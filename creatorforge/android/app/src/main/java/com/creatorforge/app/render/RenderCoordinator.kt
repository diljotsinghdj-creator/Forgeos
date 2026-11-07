package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline
import java.io.File

class RenderCoordinator(private val renderer: VideoRenderer) {
    suspend fun export(
        timeline: ProjectTimeline,
        request: RenderRequest,
        onProgress: (RenderProgress) -> Unit,
        isCancelled: () -> Boolean = { false }
    ): RenderResult {
        val result = renderer.render(timeline, request, onProgress, isCancelled)
        if (!result.success) return result
        val path = result.outputPath ?: return RenderResult(false, error = "Renderer returned no output path")
        val file = File(path)
        if (!file.isFile || file.length() < 1024L) return RenderResult(false, error = "Renderer output is missing or empty")
        return result
    }
}
