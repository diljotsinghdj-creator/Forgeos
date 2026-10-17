package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline
import java.io.File

/** Boundary for narration composition. Implementations MUST produce AAC audio
 * aligned to timeline time. MP3 source files are not accepted as final output.
 */
interface AacNarrationComposer {
    suspend fun compose(
        timeline: ProjectTimeline,
        outputFile: File,
        isCancelled: () -> Boolean = { false }
    ): AudioComposeResult
}

data class AudioComposeResult(
    val success: Boolean,
    val outputFile: File? = null,
    val error: String? = null
)

class FailClosedAacNarrationComposer : AacNarrationComposer {
    override suspend fun compose(timeline: ProjectTimeline, outputFile: File, isCancelled: () -> Boolean): AudioComposeResult =
        AudioComposeResult(false, error = "AAC narration composer is not runtime-verified; v1.0 export blocked")
}
