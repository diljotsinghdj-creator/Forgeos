package com.creatorforge.app.render

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface

/** Everything that defines a thumbnail. */
data class ThumbSpec(
    val width: Int = 1280, val height: Int = 720,
    val background: Bitmap? = null,
    val gradient: Pair<Int, Int> = Color.parseColor("#1A1A2E") to Color.parseColor("#E94560"),
    val line1: String = "", val line2: String = "", val highlight: String = "",
    val textColor: Int = Color.WHITE, val highlightColor: Int = Color.parseColor("#FFD400"),
    val position: String = "bottom", // top | center | bottom
    val darken: Float = 0.45f, val badge: String = "", val emoji: String = "",
)

/** Draws YouTube / Shorts thumbnails: centre-cropped background, legibility shade, huge outlined text. */
object ThumbnailRenderer {
    private val bold: Typeface = Typeface.create("sans-serif-black", Typeface.BOLD)

    fun render(s: ThumbSpec): Bitmap {
        val bmp = Bitmap.createBitmap(s.width, s.height, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val w = s.width.toFloat()
        val h = s.height.toFloat()
        val bg = s.background
        if (bg != null) {
            val scale = maxOf(w / bg.width, h / bg.height)
            val dw = bg.width * scale
            val dh = bg.height * scale
            c.drawBitmap(bg, null, RectF((w - dw) / 2, (h - dh) / 2, (w + dw) / 2, (h + dh) / 2), Paint(Paint.FILTER_BITMAP_FLAG))
        } else {
            c.drawRect(0f, 0f, w, h, Paint().apply { shader = LinearGradient(0f, 0f, w, h, s.gradient.first, s.gradient.second, Shader.TileMode.CLAMP) })
        }
        // Shade where the text sits so it stays readable on any picture.
        val a = (s.darken.coerceIn(0f, 1f) * 255).toInt()
        val shade = Color.argb(a, 0, 0, 0)
        val clear = Color.argb(0, 0, 0, 0)
        val shadeTop = when (s.position) { "top" -> 0f; "center" -> 0f; else -> h * 0.3f }
        val shadeBottom = when (s.position) { "top" -> h * 0.7f; else -> h }
        val fromColor = if (s.position == "bottom") clear else shade
        val toColor = if (s.position == "top") clear else shade
        c.drawRect(0f, 0f, w, h, Paint().apply { shader = LinearGradient(0f, shadeTop, 0f, shadeBottom, fromColor, toColor, Shader.TileMode.CLAMP) })

        val lines = listOf(s.line1, s.line2).map { it.trim().uppercase() }.filter { it.isNotEmpty() }
        if (lines.isNotEmpty()) {
            val margin = w * 0.06f
            val maxWidth = w - 2 * margin
            val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { typeface = bold }
            // One size for all lines: as big as fits the longest line, capped by height.
            var size = minOf(h * (if (lines.size == 1) 0.24f else 0.18f), w * 0.16f)
            paint.textSize = size
            while (lines.maxOf { paint.measureText(it) } > maxWidth && size > 12f) { size *= 0.94f; paint.textSize = size }
            val lineH = size * 1.08f
            val block = lineH * lines.size
            val top = when (s.position) { "top" -> h * 0.08f; "center" -> (h - block) / 2; else -> h - block - h * 0.08f }
            val words = s.highlight.trim().uppercase().split(Regex("\\s+")).filter { it.isNotEmpty() }.toSet()
            lines.forEachIndexed { i, line ->
                val baseline = top + lineH * (i + 1) - size * 0.16f
                var x = (w - paint.measureText(line)) / 2
                for ((k, word) in line.split(" ").withIndex()) {
                    val text = if (k == 0) word else " $word"
                    val bare = word.trim { !it.isLetterOrDigit() }
                    stroke(c, text, x, baseline, paint, size)
                    paint.style = Paint.Style.FILL
                    paint.color = if (bare in words) s.highlightColor else s.textColor
                    c.drawText(text, x, baseline, paint)
                    x += paint.measureText(text)
                }
            }
        }
        if (s.badge.isNotBlank()) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG).apply { typeface = bold; textSize = h * 0.07f; color = Color.BLACK }
            val t = s.badge.trim().uppercase()
            val pad = h * 0.025f
            val r = RectF(w * 0.04f, h * 0.05f, w * 0.04f + p.measureText(t) + 2 * pad, h * 0.05f + p.textSize + 1.6f * pad)
            c.drawRoundRect(r, pad, pad, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = s.highlightColor })
            c.drawText(t, r.left + pad, r.bottom - pad * 1.1f, p)
        }
        if (s.emoji.isNotBlank()) {
            val p = Paint(Paint.ANTI_ALIAS_FLAG).apply { textSize = h * 0.22f }
            c.drawText(s.emoji.trim(), w - p.measureText(s.emoji.trim()) - w * 0.04f, h * 0.28f, p)
        }
        return bmp
    }

    private fun stroke(c: Canvas, text: String, x: Float, y: Float, paint: Paint, size: Float) {
        paint.style = Paint.Style.STROKE
        paint.strokeJoin = Paint.Join.ROUND
        paint.strokeWidth = size * 0.14f
        paint.color = Color.BLACK
        c.drawText(text, x, y, paint)
    }
}
