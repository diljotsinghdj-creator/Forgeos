package com.creatorforge.app.render

enum class RenderState { IDLE, VALIDATING, RENDERING, SUCCEEDED, FAILED, CANCELLED }
enum class RenderQuality(val width: Int, val height: Int, val videoBitrate: Int) {
    HD_720(1280, 720, 5_000_000),
    FULL_HD_1080(1920, 1080, 10_000_000)
}

data class RenderRequest(
    val projectId: String,
    val outputPath: String,
    val quality: RenderQuality = RenderQuality.FULL_HD_1080,
    val fps: Int = 30,
    val burnCaptions: Boolean = true
)

data class RenderProgress(val state: RenderState, val fraction: Float = 0f, val message: String = "")
data class RenderResult(val success: Boolean, val outputPath: String? = null, val error: String? = null)
