package com.creatorforge.app.timeline

import com.creatorforge.app.captions.CaptionEngine
import com.creatorforge.app.model.CreatorProject

object TimelineEngine {
    fun build(project: CreatorProject): ProjectTimeline {
        var cursor = 0L
        val clips = project.scenes.sortedBy { it.order }.map { scene ->
            val duration = scene.durationSeconds.coerceAtLeast(1) * 1000L
            TimelineClip(scene.id, scene.order, cursor, duration, scene.visualAssetPath, scene.audioAssetPath,
                CaptionEngine.fromNarration(scene.narration, duration)).also { cursor += duration }
        }
        return ProjectTimeline(clips)
    }
}
