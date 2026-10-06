package com.creatorforge.app.device

import android.content.Context
import android.graphics.*
import android.media.MediaMetadataRetriever
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import com.creatorforge.app.model.AspectRatio
import com.creatorforge.app.model.CreatorProject
import com.creatorforge.app.model.SceneStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import java.io.File
import java.util.UUID
import kotlin.coroutines.resume
import kotlin.math.ceil

/**
 * Worker-free production: narration from Android's built-in text-to-speech (free, offline) and
 * styled title-card visuals drawn on the phone. The Studio tab then renders the MP4 on-device.
 */
class DeviceStudio(private val context: Context) {
    private var tts: TextToSpeech? = null

    private suspend fun engine(): TextToSpeech = tts ?: withContext(Dispatchers.Main) {
        // TextToSpeech binds a service and reports readiness on the main thread.
        var created: TextToSpeech? = null
        val ok = suspendCancellableCoroutine { cont ->
            created = TextToSpeech(context.applicationContext) { status -> if (cont.isActive) cont.resume(status == TextToSpeech.SUCCESS) }
        }
        val engine = created!!
        if (!ok) { engine.shutdown(); throw IllegalStateException("This phone has no text-to-speech engine available") }
        tts = engine
        engine
    }

    fun close() { tts?.shutdown(); tts = null }

    /** Synthesizes [text] to a WAV file and returns its length in seconds. */
    suspend fun narrate(text: String, out: File): Double {
        val engine = engine()
        val id = UUID.randomUUID().toString()
        val ok = suspendCancellableCoroutine { cont ->
            engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {}
                override fun onDone(utteranceId: String?) { if (utteranceId == id && cont.isActive) cont.resume(true) }
                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) { if (utteranceId == id && cont.isActive) cont.resume(false) }
                override fun onError(utteranceId: String?, errorCode: Int) { if (utteranceId == id && cont.isActive) cont.resume(false) }
            })
            if (engine.synthesizeToFile(text, Bundle(), out, id) != TextToSpeech.SUCCESS && cont.isActive) cont.resume(false)
        }
        if (!ok || !out.isFile || out.length() < 1000) throw IllegalStateException("Device voice failed for: ${text.take(40)}")
        val ms = MediaMetadataRetriever().run {
            try { setDataSource(out.absolutePath); extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull() ?: 0L }
            finally { release() }
        }
        if (ms <= 200) throw IllegalStateException("Device voice produced empty audio")
        return ms / 1000.0
    }

    /** Draws a title card: brand gradient, scene headline, small scene counter. */
    fun titleCard(headline: String, index: Int, total: Int, ratio: AspectRatio, out: File) {
        val (w, h) = when (ratio) { AspectRatio.VERTICAL_9_16 -> 1080 to 1920; AspectRatio.LANDSCAPE_16_9 -> 1920 to 1080; AspectRatio.SQUARE_1_1 -> 1080 to 1080 }
        val palettes = listOf(
            intArrayOf(0xFF0B0B0F.toInt(), 0xFF3A2A05.toInt()), intArrayOf(0xFF05101F.toInt(), 0xFF123E6B.toInt()),
            intArrayOf(0xFF140512.toInt(), 0xFF5A1446.toInt()), intArrayOf(0xFF04140C.toInt(), 0xFF145A3A.toInt()),
            intArrayOf(0xFF1A0A02.toInt(), 0xFF6B3412.toInt())
        )
        val bmp = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bmp)
        val colors = palettes[index % palettes.size]
        canvas.drawRect(0f, 0f, w.toFloat(), h.toFloat(), Paint().apply {
            shader = LinearGradient(0f, 0f, w.toFloat(), h.toFloat(), colors[0], colors[1], Shader.TileMode.CLAMP)
        })
        val gold = Color.rgb(212, 175, 55)
        canvas.drawRect(w * 0.08f, h * 0.30f, w * 0.08f + w * 0.12f, h * 0.30f + h * 0.006f, Paint().apply { color = gold })
        val paint = TextPaint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE; typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            textSize = (minOf(w, h) * 0.085f); setShadowLayer(12f, 0f, 4f, Color.BLACK)
        }
        val width = (w * 0.84f).toInt()
        var layout = StaticLayout.Builder.obtain(headline, 0, headline.length, paint, width).setAlignment(Layout.Alignment.ALIGN_NORMAL).build()
        while (layout.height > h * 0.38f && paint.textSize > 30f) {
            paint.textSize *= 0.9f
            layout = StaticLayout.Builder.obtain(headline, 0, headline.length, paint, width).setAlignment(Layout.Alignment.ALIGN_NORMAL).build()
        }
        canvas.save(); canvas.translate(w * 0.08f, h * 0.30f + h * 0.03f); layout.draw(canvas); canvas.restore()
        canvas.drawText("${index + 1} / $total", w * 0.08f, h * 0.27f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = gold; textSize = minOf(w, h) * 0.035f })
        out.outputStream().use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bmp.recycle()
    }

    /** Fills every scene with a device-voice narration and a title card, sizing scenes to the real voice length. */
    suspend fun makeProject(project: CreatorProject, onProgress: (String) -> Unit): CreatorProject = withContext(Dispatchers.IO) {
        val dir = File(context.filesDir, "device_assets/${project.id}").apply { mkdirs() }
        val scenes = project.scenes.sortedBy { it.order }
        val updated = scenes.mapIndexed { i, s ->
            onProgress("Scene ${i + 1}/${scenes.size}: voice + title card")
            val wav = File(dir, "scene_${i + 1}.wav")
            val seconds = narrate(s.narration, wav)
            val png = File(dir, "scene_${i + 1}.png")
            titleCard(headline(s.narration), i, scenes.size, project.aspectRatio, png)
            s.copy(status = SceneStatus.READY, visualAssetPath = png.absolutePath, audioAssetPath = wav.absolutePath,
                durationSeconds = ceil(seconds + 0.4).toInt().coerceAtLeast(2))
        }
        project.copy(scenes = updated)
    }

    /** The first clause of the narration, so the card reads like a headline while captions carry the full line. */
    private fun headline(narration: String): String {
        val clause = narration.split(Regex("(?<=[,;:—–])\\s+")).first().trim()
        val words = clause.split(' ')
        return if (words.size <= 12) clause else words.take(12).joinToString(" ") + "…"
    }
}
