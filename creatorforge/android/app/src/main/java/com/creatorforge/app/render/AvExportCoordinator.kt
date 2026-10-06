package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline
import java.io.File

/** v1.0 acceptance coordinator. It cannot return success without real H.264 video,
 * real AAC narration, a muxed MP4, and post-mux A/V track verification. */
class AvExportCoordinator(
    private val videoRenderer: VideoRenderer,
    private val audioComposer: AacNarrationComposer,
    private val muxer: Mp4TrackMuxer = Mp4TrackMuxer()
) {
    suspend fun export(
        timeline: ProjectTimeline,
        request: RenderRequest,
        onProgress: (RenderProgress) -> Unit,
        isCancelled: () -> Boolean = { false }
    ): RenderResult {
        val finalFile = File(request.outputPath)
        val work = File(finalFile.parentFile ?: File("."), ".creatorforge_${request.projectId}").apply { mkdirs() }
        val silentVideo = File(work, "video.mp4")
        val narration = File(work, "narration.m4a")
        try {
            val vr = videoRenderer.render(timeline, request.copy(outputPath = silentVideo.absolutePath), onProgress, isCancelled)
            if (!vr.success) return vr
            if (isCancelled()) return RenderResult(false, error = "Render cancelled")
            onProgress(RenderProgress(RenderState.RENDERING, .82f, "Composing narration"))
            val ar = audioComposer.compose(timeline, narration, isCancelled)
            if (!ar.success) return RenderResult(false, error = ar.error ?: "Narration composition failed")
            onProgress(RenderProgress(RenderState.RENDERING, .94f, "Muxing audio + video"))
            muxer.mux(silentVideo, narration, finalFile)
            onProgress(RenderProgress(RenderState.SUCCEEDED, 1f, "Verified H.264/AAC MP4"))
            return RenderResult(true, finalFile.absolutePath)
        } catch (t: Throwable) {
            if (finalFile.exists()) finalFile.delete()
            return RenderResult(false, error = t.message ?: t.javaClass.simpleName)
        } finally {
            silentVideo.delete(); narration.delete(); work.delete()
        }
    }
}
