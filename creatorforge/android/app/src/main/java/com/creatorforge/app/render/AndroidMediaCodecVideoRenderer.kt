package com.creatorforge.app.render

import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import com.creatorforge.app.timeline.CaptionCue
import com.creatorforge.app.timeline.ProjectTimeline
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.math.max

/**
 * Real Android H.264/MP4 video-track renderer.
 * Draws scene stills and optional captions into a MediaCodec input Surface.
 * Audio is intentionally NOT claimed here; v1.0 must add/transcode and mux narration.
 */
class AndroidMediaCodecVideoRenderer(
    private val validator: RenderValidator = RenderValidator()
) : VideoRenderer {
    override suspend fun render(
        timeline: ProjectTimeline,
        request: RenderRequest,
        onProgress: (RenderProgress) -> Unit,
        isCancelled: () -> Boolean
    ): RenderResult = withContext(Dispatchers.IO) {
        onProgress(RenderProgress(RenderState.VALIDATING, 0f, "Validating real assets"))
        val errors = validator.validate(timeline)
        if (errors.isNotEmpty()) return@withContext RenderResult(false, error = errors.joinToString("\n"))
        if (isCancelled()) return@withContext RenderResult(false, error = "Render cancelled")

        val out = File(request.outputPath)
        out.parentFile?.mkdirs()
        if (out.exists()) out.delete()

        val width = request.quality.width
        val height = request.quality.height
        val fps = request.fps.coerceIn(24, 60)
        val format = MediaFormat.createVideoFormat(MediaFormat.MIMETYPE_VIDEO_AVC, width, height).apply {
            setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface)
            setInteger(MediaFormat.KEY_BIT_RATE, request.quality.videoBitrate)
            setInteger(MediaFormat.KEY_FRAME_RATE, fps)
            setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1)
        }
        val codec = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        var muxer: MediaMuxer? = null
        try {
            codec.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            val surface = codec.createInputSurface()
            codec.start()
            muxer = MediaMuxer(out.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
            val info = MediaCodec.BufferInfo()
            var track = -1
            var muxerStarted = false
            var frameIndex = 0L
            val totalFrames = max(1L, (timeline.durationMs * fps) / 1000L)

            fun drain(end: Boolean) {
                if (end) codec.signalEndOfInputStream()
                while (true) {
                    val index = codec.dequeueOutputBuffer(info, if (end) 10_000L else 0L)
                    when {
                        index == MediaCodec.INFO_TRY_AGAIN_LATER -> if (!end) return else continue
                        index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                            check(!muxerStarted) { "Encoder format changed twice" }
                            track = muxer.addTrack(codec.outputFormat)
                            muxer.start(); muxerStarted = true
                        }
                        index >= 0 -> {
                            val buffer = codec.getOutputBuffer(index) ?: error("Encoder output buffer missing")
                            if (info.size > 0 && muxerStarted) {
                                buffer.position(info.offset); buffer.limit(info.offset + info.size)
                                muxer.writeSampleData(track, buffer, info)
                            }
                            val eos = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                            codec.releaseOutputBuffer(index, false)
                            if (eos) return
                        }
                    }
                }
            }

            // Smart edit on the phone: slow zoom/pan per scene, crossfade into the next scene,
            // fade from/to black, bold captions. Two bitmaps (current + next) are kept decoded.
            val clips = timeline.clips.sortedBy { it.startMs }
            val fadeFrames = (fps * 0.4).toInt()
            fun decode(i: Int) = clips.getOrNull(i)?.let {
                BitmapFactory.decodeFile(it.visualPath) ?: error("Cannot decode visual for scene ${it.order}")
            }
            var current = decode(0)
            var next = decode(1)
            clips.forEachIndexed { ci, clip ->
                val frames = max(1, ((clip.durationMs * fps) / 1000L).toInt())
                val cur = current ?: error("Missing visual for scene ${clip.order}")
                repeat(frames) { localFrame ->
                    if (isCancelled()) return@withContext RenderResult(false, error = "Render cancelled")
                    val canvas = surface.lockCanvas(null)
                    try {
                        val t = localFrame.toFloat() / frames
                        drawCover(canvas, cur, width, height, zoom = 1f + 0.10f * t, pan = if (ci % 2 == 0) t else 1f - t)
                        val remaining = frames - localFrame
                        val nxt = next
                        if (nxt != null && remaining <= fadeFrames) {
                            val a = 1f - remaining.toFloat() / fadeFrames
                            drawCover(canvas, nxt, width, height, zoom = 1f, pan = if ((ci + 1) % 2 == 0) 0f else 1f, alpha = a)
                        }
                        if (request.burnCaptions) {
                            val localMs = (localFrame * 1000L) / fps
                            val cue = clip.captions.firstOrNull { localMs in it.startMs until it.endMs }
                            if (cue != null) drawCaption(canvas, cue, width, height)
                        }
                        // fade in from black at the very start, out to black at the very end
                        val global = frameIndex
                        val tail = totalFrames - global
                        val black = when {
                            global < fadeFrames -> 1f - global.toFloat() / fadeFrames
                            tail < fadeFrames -> 1f - tail.toFloat() / fadeFrames
                            else -> 0f
                        }
                        if (black > 0f) canvas.drawColor(Color.argb((black.coerceIn(0f, 1f) * 255).toInt(), 0, 0, 0))
                    } finally { surface.unlockCanvasAndPost(canvas) }
                    frameIndex++
                    if (frameIndex % fps == 0L) {
                        onProgress(RenderProgress(RenderState.RENDERING, frameIndex.toFloat() / totalFrames, "Encoding scene ${clip.order}"))
                    }
                    drain(false)
                }
                cur.recycle()
                current = next
                next = decode(ci + 2)
            }
            drain(true)
            onProgress(RenderProgress(RenderState.SUCCEEDED, 1f, "Video track encoded"))
        } catch (t: Throwable) {
            if (out.exists()) out.delete()
            return@withContext RenderResult(false, error = t.message ?: t.javaClass.simpleName)
        } finally {
            try { codec.stop() } catch (_: Throwable) {}
            try { codec.release() } catch (_: Throwable) {}
            try { muxer?.stop() } catch (_: Throwable) {}
            try { muxer?.release() } catch (_: Throwable) {}
        }
        if (!out.isFile || out.length() < 1024L) RenderResult(false, error = "MP4 output missing or empty")
        else RenderResult(true, outputPath = out.absolutePath)
    }

    private val bitmapPaint = Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG)

    /** Cover-fit with Ken Burns zoom; [pan] slides along the longer overflow axis (0..1). */
    private fun drawCover(canvas: Canvas, bitmap: android.graphics.Bitmap, width: Int, height: Int,
                          zoom: Float = 1f, pan: Float = 0.5f, alpha: Float = 1f) {
        if (alpha >= 1f) canvas.drawColor(Color.BLACK)
        val scale = max(width.toFloat() / bitmap.width, height.toFloat() / bitmap.height) * zoom
        val dw = bitmap.width * scale; val dh = bitmap.height * scale
        val left = -(dw - width) * (if (dw - width > dh - height) pan else 0.5f)
        val top = -(dh - height) * (if (dh - height >= dw - width) pan else 0.5f)
        bitmapPaint.alpha = (alpha.coerceIn(0f, 1f) * 255).toInt()
        canvas.drawBitmap(bitmap, null, android.graphics.RectF(left, top, left + dw, top + dh), bitmapPaint)
        bitmapPaint.alpha = 255
    }

    /** Bold white captions with a thick black outline, wrapped to at most two lines. */
    private fun drawCaption(canvas: Canvas, cue: CaptionCue, width: Int, height: Int) {
        val size = minOf(width, height) * if (height > width) 0.068f else 0.055f
        val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE; textAlign = Paint.Align.CENTER; textSize = size
            typeface = android.graphics.Typeface.create(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD)
        }
        val stroke = Paint(fill).apply { color = Color.BLACK; style = Paint.Style.STROKE; strokeWidth = size * 0.16f; strokeJoin = Paint.Join.ROUND }
        val maxW = width * 0.86f
        val lines = mutableListOf<String>()
        var line = ""
        for (word in cue.text.split(' ')) {
            val trial = if (line.isEmpty()) word else "$line $word"
            if (fill.measureText(trial) > maxW && line.isNotEmpty()) { lines += line; line = word } else line = trial
        }
        if (line.isNotEmpty()) lines += line
        val shown = if (lines.size > 2) listOf(lines[0], lines.drop(1).joinToString(" ")) else lines
        val baseY = height * (if (height > width) 0.72f else 0.86f)
        shown.forEachIndexed { i, l ->
            val y = baseY + i * size * 1.2f
            canvas.drawText(l, width / 2f, y, stroke)
            canvas.drawText(l, width / 2f, y, fill)
        }
    }
}
