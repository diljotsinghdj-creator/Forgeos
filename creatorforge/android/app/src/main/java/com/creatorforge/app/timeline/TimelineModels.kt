package com.creatorforge.app.timeline

data class TimelineClip(
    val sceneId: String,
    val order: Int,
    val startMs: Long,
    val durationMs: Long,
    val visualPath: String?,
    val audioPath: String?,
    val captions: List<CaptionCue>
) { val endMs: Long get() = startMs + durationMs }

data class CaptionCue(val startMs: Long, val endMs: Long, val text: String)

data class ProjectTimeline(val clips: List<TimelineClip>) {
    val durationMs: Long get() = clips.maxOfOrNull { it.endMs } ?: 0L
}
