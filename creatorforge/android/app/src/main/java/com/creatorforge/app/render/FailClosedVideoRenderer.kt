package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline

/**
 * v0.8 safety implementation. It deliberately refuses to invent an MP4.
 * Replace with AndroidMediaCodecRenderer only after device/runtime validation.
 */
class FailClosedVideoRenderer(
    private val validator: RenderValidator = RenderValidator()
) : VideoRenderer {
    override suspend fun render(
        timeline: ProjectTimeline,
        request: RenderRequest,
        onProgress: (RenderProgress) -> Unit,
        isCancelled: () -> Boolean
    ): RenderResult {
        onProgress(RenderProgress(RenderState.VALIDATING, 0f, "Validating real media assets"))
        if (isCancelled()) {
            onProgress(RenderProgress(RenderState.CANCELLED, 0f, "Cancelled"))
            return RenderResult(false, error = "Render cancelled")
        }
        val errors = validator.validate(timeline)
        if (errors.isNotEmpty()) {
            val message = errors.joinToString("\n")
            onProgress(RenderProgress(RenderState.FAILED, 0f, message))
            return RenderResult(false, error = message)
        }
        val message = "No device-validated MP4 encoder is attached. Refusing fake export."
        onProgress(RenderProgress(RenderState.FAILED, 0f, message))
        return RenderResult(false, error = message)
    }
}
