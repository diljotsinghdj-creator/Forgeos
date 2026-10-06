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

            timeline.clips.forEach { clip ->
                val bitmap = BitmapFactory.decodeFile(clip.visualPath)
                    ?: return@withContext RenderResult(false, error = "Cannot decode visual for scene ${clip.order}")
                val frames = max(1, ((clip.durationMs * fps) / 1000L).toInt())
                repeat(frames) { localFrame ->
                    if (isCancelled()) return@withContext RenderResult(false, error = "Render cancelled")
                    val canvas = surface.lockCanvas(null)
                    try {
                        drawCover(canvas, bitmap, width, height)
                        if (request.burnCaptions) {
                            val localMs = (localFrame * 1000L) / fps
                            val cue = clip.captions.firstOrNull { localMs in it.startMs until it.endMs }
                            if (cue != null) drawCaption(canvas, cue, width, height)
                        }
                    } finally { surface.unlockCanvasAndPost(canvas) }
                    frameIndex++
                    if (frameIndex % fps == 0L) {
                        onProgress(RenderProgress(RenderState.RENDERING, frameIndex.toFloat() / totalFrames, "Encoding scene ${clip.order}"))
                    }
                    drain(false)
                }
                bitmap.recycle()
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

    private fun drawCover(canvas: Canvas, bitmap: android.graphics.Bitmap, width: Int, height: Int) {
        canvas.drawColor(Color.BLACK)
        val scale = max(width.toFloat() / bitmap.width, height.toFloat() / bitmap.height)
        val dw = (bitmap.width * scale).toInt(); val dh = (bitmap.height * scale).toInt()
        val left = (width - dw) / 2; val top = (height - dh) / 2
        canvas.drawBitmap(bitmap, null, Rect(left, top, left + dw, top + dh), Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG))
    }

    private fun drawCaption(canvas: Canvas, cue: CaptionCue, width: Int, height: Int) {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE; textAlign = Paint.Align.CENTER; textSize = width * 0.045f
            setShadowLayer(8f, 0f, 3f, Color.BLACK)
        }
        val bg = Paint().apply { color = 0x99000000.toInt() }
        val y = height * 0.86f
        val pad = width * 0.035f
        val measured = paint.measureText(cue.text).coerceAtMost(width * 0.9f)
        canvas.drawRoundRect(width/2f-measured/2-pad, y-paint.textSize-pad, width/2f+measured/2+pad, y+pad, 18f, 18f, bg)
        canvas.drawText(cue.text, width / 2f, y, paint)
    }
}
