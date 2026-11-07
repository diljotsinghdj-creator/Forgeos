package com.creatorforge.app.render

import android.media.MediaExtractor
import android.media.MediaFormat
import android.media.MediaMuxer
import java.io.File
import java.nio.ByteBuffer

/**
 * Final fail-closed MP4 mux step. Accepts a rendered H.264 MP4 and an AAC/M4A
 * narration track, copies both into one MPEG-4 container, and refuses to report
 * success unless both a video and audio track are present in the result.
 */
class Mp4TrackMuxer {
    fun mux(videoFile: File, audioFile: File, outputFile: File): File {
        require(videoFile.isFile && videoFile.length() > 1024) { "Video input missing" }
        require(audioFile.isFile && audioFile.length() > 512) { "AAC narration input missing" }
        outputFile.parentFile?.mkdirs()
        if (outputFile.exists()) outputFile.delete()

        val videoExtractor = MediaExtractor()
        val audioExtractor = MediaExtractor()
        var muxer: MediaMuxer? = null
        try {
            videoExtractor.setDataSource(videoFile.absolutePath)
            audioExtractor.setDataSource(audioFile.absolutePath)
            val videoIndex = findTrack(videoExtractor, "video/")
            val audioIndex = findTrack(audioExtractor, "audio/")
            require(videoIndex >= 0) { "No video track" }
            require(audioIndex >= 0) { "No audio track" }
            videoExtractor.selectTrack(videoIndex)
            audioExtractor.selectTrack(audioIndex)

            muxer = MediaMuxer(outputFile.absolutePath, MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4)
            val outVideo = muxer.addTrack(videoExtractor.getTrackFormat(videoIndex))
            val outAudio = muxer.addTrack(audioExtractor.getTrackFormat(audioIndex))
            muxer.start()
            copyTrack(videoExtractor, muxer, outVideo)
            copyTrack(audioExtractor, muxer, outAudio)
            muxer.stop()
            muxer.release(); muxer = null
        } catch (t: Throwable) {
            try { muxer?.release() } catch (_: Throwable) {}
            if (outputFile.exists()) outputFile.delete()
            throw t
        } finally {
            videoExtractor.release(); audioExtractor.release()
        }
        require(outputFile.isFile && outputFile.length() > 2048) { "Final MP4 missing or empty" }
        verifyAv(outputFile)
        return outputFile
    }

    private fun copyTrack(extractor: MediaExtractor, muxer: MediaMuxer, track: Int) {
        val buffer = ByteBuffer.allocateDirect(2 * 1024 * 1024)
        val info = android.media.MediaCodec.BufferInfo()
        while (true) {
            val size = extractor.readSampleData(buffer, 0)
            if (size < 0) break
            info.offset = 0; info.size = size
            info.presentationTimeUs = extractor.sampleTime
            info.flags = extractor.sampleFlags
            muxer.writeSampleData(track, buffer, info)
            extractor.advance()
        }
    }

    private fun findTrack(extractor: MediaExtractor, prefix: String): Int {
        for (i in 0 until extractor.trackCount) {
            val mime = extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME) ?: continue
            if (mime.startsWith(prefix)) return i
        }
        return -1
    }

    fun verifyAv(file: File) {
        val extractor = MediaExtractor()
        try {
            extractor.setDataSource(file.absolutePath)
            var video = false; var audio = false
            for (i in 0 until extractor.trackCount) {
                val mime = extractor.getTrackFormat(i).getString(MediaFormat.KEY_MIME).orEmpty()
                video = video || mime.startsWith("video/")
                audio = audio || mime.startsWith("audio/")
            }
            require(video) { "Final MP4 has no video track" }
            require(audio) { "Final MP4 has no audio track" }
        } finally { extractor.release() }
    }
}
