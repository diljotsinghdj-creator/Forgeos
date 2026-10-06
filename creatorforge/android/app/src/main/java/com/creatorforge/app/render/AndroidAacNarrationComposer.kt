package com.creatorforge.app.render

import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import com.creatorforge.app.timeline.ProjectTimeline
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min

/**
 * Android narration composer for CreatorForge.
 * Decodes each scene narration asset with MediaCodec, converts it to 44.1 kHz
 * mono PCM, trims/pads it to the scene duration, AAC-encodes the continuous
 * project timeline, and writes an M4A/MP4 audio-only file.
 */
class AndroidAacNarrationComposer(
    private val sampleRate: Int = 44_100,
    private val bitRate: Int = 128_000
) : AacNarrationComposer {

    override suspend fun compose(
        timeline: ProjectTimeline,
        outputFile: File,
        isCancelled: () -> Boolean
    ): AudioComposeResult {
        if (timeline.clips.isEmpty()) return AudioComposeResult(false, error = "Timeline is empty")
        val missing = timeline.clips.firstOrNull { it.audioPath.isNullOrBlank() || !File(it.audioPath!!).isFile }
        if (missing != null) return AudioComposeResult(false, error = "Missing narration for scene ${missing.sceneId}")

        outputFile.parentFile?.mkdirs()
        if (outputFile.exists()) outputFile.delete()

        val encoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_AUDIO_AAC)
        val format = MediaFormat.createAudioFormat(MediaFormat.MIMETYPE_AUDIO_AAC, sampleRate, 1).apply {
            setInteger(MediaFormat.KEY_AAC_PROFILE, MediaCodecInfo.CodecProfileLevel.AACObjectLC)
            setInteger(MediaFormat.KEY_BIT_RATE, bitRate)
            setInteger(MediaFormat.KEY_MAX_INPUT_SIZE, 16 * 1024)
        }
        var muxer: MediaMuxer? = null
        try {
            encoder.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            encoder.start()
            muxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
            var muxTrack = -1
            var muxStarted = false
            var submittedSamples = 0L
            val info = MediaCodec.BufferInfo()

            fun drain(end: Boolean) {
                while (true) {
                    val index = encoder.dequeueOutputBuffer(info, if (end) 10_000 else 0)
                    when {
                        index == MediaCodec.INFO_TRY_AGAIN_LATER -> return
                        index == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                            check(!muxStarted) { "AAC output format changed twice" }
                            muxTrack = requireNotNull(muxer).addTrack(encoder.outputFormat)
                            requireNotNull(muxer).start(); muxStarted = true
                        }
                        index >= 0 -> {
                            val out = encoder.getOutputBuffer(index) ?: error("Missing AAC output buffer")
                            if (info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG != 0) info.size = 0
                            if (info.size > 0) {
                                check(muxStarted) { "AAC muxer not started" }
                                out.position(info.offset); out.limit(info.offset + info.size)
                                requireNotNull(muxer).writeSampleData(muxTrack, out, info)
                            }
                            val eos = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                            encoder.releaseOutputBuffer(index, false)
                            if (eos) return
                        }
                    }
                }
            }

            fun submit(samples: ShortArray, eos: Boolean = false) {
                var offset = 0
                while (offset < samples.size || eos) {
                    if (isCancelled()) throw InterruptedException("Export cancelled")
                    val index = encoder.dequeueInputBuffer(10_000)
                    if (index < 0) { drain(false); continue }
                    val input = encoder.getInputBuffer(index) ?: error("Missing AAC input buffer")
                    input.clear()
                    input.order(ByteOrder.LITTLE_ENDIAN)
                    val capacitySamples = input.remaining() / 2
                    val count = if (eos && offset >= samples.size) 0 else min(capacitySamples, samples.size - offset)
                    for (i in 0 until count) input.putShort(samples[offset + i])
                    val ptsUs = submittedSamples * 1_000_000L / sampleRate
                    val flags = if (eos && offset + count >= samples.size) MediaCodec.BUFFER_FLAG_END_OF_STREAM else 0
                    encoder.queueInputBuffer(index, 0, count * 2, ptsUs, flags)
                    submittedSamples += count
                    offset += count
                    drain(false)
                    if (flags != 0) return
                }
            }

            for (clip in timeline.clips.sortedBy { it.startMs }) {
                if (isCancelled()) throw InterruptedException("Export cancelled")
                val targetStart = clip.startMs * sampleRate / 1000L
                if (submittedSamples < targetStart) submit(ShortArray((targetStart - submittedSamples).toInt()))

                val decoded = decodeToMono(File(clip.audioPath!!), isCancelled)
                val converted = resample(decoded.samples, decoded.sampleRate, sampleRate)
                val targetCount = max(1L, clip.durationMs * sampleRate / 1000L).toInt()
                if (converted.size >= targetCount) {
                    submit(converted.copyOf(targetCount))
                } else {
                    submit(converted)
                    submit(ShortArray(targetCount - converted.size))
                }
            }

            val totalTarget = timeline.durationMs * sampleRate / 1000L
            if (submittedSamples < totalTarget) submit(ShortArray((totalTarget - submittedSamples).toInt()))
            submit(ShortArray(0), eos = true)
            drain(true)

            if (muxStarted) { muxer.stop(); muxer.release(); muxer = null }
            encoder.stop(); encoder.release()
            require(outputFile.isFile && outputFile.length() > 512) { "AAC narration output missing" }
            verifyAudio(outputFile)
            return AudioComposeResult(true, outputFile)
        } catch (t: Throwable) {
            try { muxer?.release() } catch (_: Throwable) {}
            try { encoder.stop() } catch (_: Throwable) {}
            try { encoder.release() } catch (_: Throwable) {}
            outputFile.delete()
            return AudioComposeResult(false, error = t.message ?: t.javaClass.simpleName)
        }
    }

    private data class DecodedPcm(val samples: ShortArray, val sampleRate: Int)

    private fun decodeToMono(file: File, isCancelled: () -> Boolean): DecodedPcm {
        val extractor = MediaExtractor()
        extractor.setDataSource(file.absolutePath)
        var track = -1
        for (i in 0 until extractor.trackCount) {
            if (extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME).orEmpty().startsWith("audio/")) { track = i; break }
        }
        require(track >= 0) { "Narration has no audio track: ${file.name}" }
        extractor.selectTrack(track)
        val inputFormat = extractor.getTrackFormat(track)
        val mime = inputFormat.getString(MediaFormat.KEY_MIME) ?: error("Narration MIME missing")
        val decoder = MediaCodec.createDecoderByType(mime)
        decoder.configure(inputFormat, null, null, 0); decoder.start()
        val output = ArrayList<Short>()
        val info = MediaCodec.BufferInfo()
        var inputDone = false; var outputDone = false
        var actualRate = inputFormat.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        var channels = inputFormat.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
        try {
            while (!outputDone) {
                if (isCancelled()) throw InterruptedException("Export cancelled")
                if (!inputDone) {
                    val ix = decoder.dequeueInputBuffer(10_000)
                    if (ix >= 0) {
                        val buf = decoder.getInputBuffer(ix) ?: error("Missing decoder input")
                        val size = extractor.readSampleData(buf, 0)
                        if (size < 0) {
                            decoder.queueInputBuffer(ix, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM); inputDone = true
                        } else {
                            decoder.queueInputBuffer(ix, 0, size, extractor.sampleTime, extractor.sampleFlags); extractor.advance()
                        }
                    }
                }
                when (val ox = decoder.dequeueOutputBuffer(info, 10_000)) {
                    MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                        val f = decoder.outputFormat
                        actualRate = f.getInteger(MediaFormat.KEY_SAMPLE_RATE)
                        channels = f.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
                    }
                    MediaCodec.INFO_TRY_AGAIN_LATER -> Unit
                    else -> if (ox >= 0) {
                        val buf = decoder.getOutputBuffer(ox)
                        if (buf != null && info.size > 0) {
                            buf.position(info.offset); buf.limit(info.offset + info.size); buf.order(ByteOrder.LITTLE_ENDIAN)
                            val frame = ShortArray(info.size / 2) { buf.short }
                            var p = 0
                            while (p + channels <= frame.size) {
                                var sum = 0L
                                for (c in 0 until channels) sum += frame[p + c]
                                output.add((sum / channels).toInt().coerceIn(Short.MIN_VALUE.toInt(), Short.MAX_VALUE.toInt()).toShort())
                                p += channels
                            }
                        }
                        outputDone = info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0
                        decoder.releaseOutputBuffer(ox, false)
                    }
                }
            }
        } finally { decoder.stop(); decoder.release(); extractor.release() }
        return DecodedPcm(ShortArray(output.size) { output[it] }, actualRate)
    }

    private fun resample(input: ShortArray, fromRate: Int, toRate: Int): ShortArray {
        if (input.isEmpty() || fromRate == toRate) return input
        val outSize = max(1, (input.size.toLong() * toRate / fromRate).toInt())
        val out = ShortArray(outSize)
        val ratio = fromRate.toDouble() / toRate
        for (i in out.indices) {
            val pos = i * ratio
            val a = floor(pos).toInt().coerceIn(0, input.lastIndex)
            val b = min(a + 1, input.lastIndex)
            val frac = pos - a
            out[i] = (input[a] * (1.0 - frac) + input[b] * frac).toInt().coerceIn(Short.MIN_VALUE.toInt(), Short.MAX_VALUE.toInt()).toShort()
        }
        return out
    }

    private fun verifyAudio(file: File) {
        val extractor = MediaExtractor()
        try {
            extractor.setDataSource(file.absolutePath)
            var audio = false
            for (i in 0 until extractor.trackCount) {
                audio = audio || extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME).orEmpty().startsWith("audio/")
            }
            require(audio) { "Composed narration has no audio track" }
        } finally { extractor.release() }
    }
}
