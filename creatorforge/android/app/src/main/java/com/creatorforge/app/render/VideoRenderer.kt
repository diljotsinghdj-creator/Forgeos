package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline

/** Contract for a renderer that must create a genuine playable MP4. */
interface VideoRenderer {
    suspend fun render(
        timeline: ProjectTimeline,
        request: RenderRequest,
        onProgress: (RenderProgress) -> Unit,
        isCancelled: () -> Boolean = { false }
    ): RenderResult
}
