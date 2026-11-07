package com.creatorforge.app.render

import com.creatorforge.app.timeline.ProjectTimeline
import java.io.File

class RenderValidator {
    fun validate(timeline: ProjectTimeline): List<String> {
        val errors = mutableListOf<String>()
        if (timeline.clips.isEmpty()) errors += "Timeline has no clips."
        timeline.clips.forEach { clip ->
            if (clip.durationMs <= 0) errors += "Scene ${clip.order} has invalid duration."
            val visual = clip.visualPath
            val audio = clip.audioPath
            if (visual.isNullOrBlank() || !File(visual).isFile) errors += "Scene ${clip.order} has no real visual asset."
            if (audio.isNullOrBlank() || !File(audio).isFile) errors += "Scene ${clip.order} has no real narration asset."
        }
        return errors
    }
}
