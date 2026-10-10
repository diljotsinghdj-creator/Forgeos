package com.creatorforge.app.captions

import com.creatorforge.app.timeline.CaptionCue

object CaptionEngine {
    fun fromNarration(text: String, durationMs: Long): List<CaptionCue> {
        val words = text.trim().split(Regex("\\s+")).filter { it.isNotBlank() }
        if (words.isEmpty() || durationMs <= 0) return emptyList()
        val groups = words.chunked(6)
        return groups.mapIndexed { index, group ->
            val start = durationMs * index / groups.size
            val end = durationMs * (index + 1) / groups.size
            CaptionCue(start, end, group.joinToString(" "))
        }
    }
}
