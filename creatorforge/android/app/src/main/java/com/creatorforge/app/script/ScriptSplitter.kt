package com.creatorforge.app.script

import kotlin.math.ceil
import kotlin.math.max

/** One scene of a pasted script: what the narrator says and roughly how long it takes. */
data class ScriptBeat(val narration: String, val seconds: Int)

/**
 * Splits a pasted script into scenes on sentence boundaries, balancing word counts, so each scene
 * gets its own narration instead of the whole script repeated in every scene.
 */
object ScriptSplitter {
    private const val WORDS_PER_SECOND = 2.5

    fun sentences(text: String): List<String> =
        text.replace(Regex("[\\p{So}\\p{Cn}]"), " ") // emoji and other symbols are not spoken
            // Sentence ends, except after abbreviations like "U.S." or "Dr."
            .split(Regex("(?<=[.!?…])(?<![A-Z]\\.[A-Z]\\.)(?<!\\b(?:Mr|Mrs|Ms|Dr|Jr|Sr|St|vs|etc)\\.)\\s+|\\n+"))
            .map { it.replace(Regex("\\s+"), " ").trim() }
            .filter { it.any(Char::isLetterOrDigit) }

    fun split(text: String, maxScenes: Int): List<ScriptBeat> {
        val parts = sentences(text)
        if (parts.isEmpty()) return emptyList()
        val words = parts.sumOf { it.split(' ').size }
        val scenes = parts.size.coerceAtMost(maxScenes).coerceAtLeast(1)
        val target = words.toDouble() / scenes
        val groups = mutableListOf<MutableList<String>>(mutableListOf())
        var count = 0
        parts.forEachIndexed { i, s ->
            val remainingSentences = parts.size - i
            val remainingSlots = scenes - groups.size
            if (groups.last().isNotEmpty() && (count >= target * groups.size || remainingSentences <= remainingSlots) && groups.size < scenes) {
                groups.add(mutableListOf())
            }
            groups.last().add(s)
            count += s.split(' ').size
        }
        return groups.filter { it.isNotEmpty() }.map { g ->
            val narration = g.joinToString(" ")
            ScriptBeat(narration, max(3, ceil(narration.split(' ').size / WORDS_PER_SECOND).toInt()))
        }
    }

    /** A short title from the first sentence. */
    fun title(text: String): String = sentences(text).firstOrNull()?.take(60)?.trimEnd(' ', ',', '.') ?: "Untitled"
}
