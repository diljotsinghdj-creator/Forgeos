package com.creatorforge.app.studio

import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** A JSON list on the phone's storage, written atomically. */
open class JsonListStore<T>(private val file: File, private val read: (JSONObject) -> T, private val write: (T) -> JSONObject, private val id: (T) -> String) {
    @Synchronized fun list(): List<T> = if (!file.isFile) emptyList() else runCatching {
        val a = JSONArray(file.readText()); (0 until a.length()).map { read(a.getJSONObject(it)) }
    }.getOrDefault(emptyList())

    @Synchronized fun save(items: List<T>) {
        file.parentFile?.mkdirs()
        val tmp = File(file.path + ".tmp")
        tmp.writeText(JSONArray().apply { items.forEach { put(write(it)) } }.toString())
        if (!tmp.renameTo(file)) { file.delete(); tmp.renameTo(file) }
    }

    @Synchronized fun upsert(item: T): List<T> {
        val items = list().toMutableList()
        val i = items.indexOfFirst { id(it) == id(item) }
        if (i >= 0) items[i] = item else items.add(0, item)
        save(items)
        return items
    }

    @Synchronized fun delete(itemId: String): List<T> = list().filter { id(it) != itemId }.also { save(it) }
}

class ScriptStore(dir: File) : JsonListStore<SavedScript>(File(dir, "scripts.json"), SavedScript::from, SavedScript::toJson, SavedScript::id)
class ChannelStore(dir: File) : JsonListStore<Channel>(File(dir, "channels.json"), Channel::from, Channel::toJson, Channel::id)

/** Builds the worker's /v1/productions body. The worker is only needed for this last step: making the video. */
object ProductionBodies {
    fun fromIdea(trend: Trend, idea: Idea, script: String, base: JSONObject): JSONObject {
        val body = JSONObject(base.toString())
        if (script.isNotBlank()) return body.put("script", script).put("idea", idea.title.ifBlank { trend.title }.take(200))
        val facts = (listOf(trend.title) + trend.headlines).filter { it.isNotBlank() }.take(6).joinToString("\n") { "- $it" }
        body.put("idea", ("${idea.title.ifBlank { trend.title }}\nHook: ${idea.hook}\nAngle: ${idea.angle}" +
            if (facts.isNotBlank() && trend.signals.isNotEmpty()) "\nUse only these real facts from this week's sources:\n$facts" else "").take(3900))
        if (!body.has("duration_s")) body.put("duration_s", idea.seconds.coerceIn(10, 900))
        if (!body.has("template")) body.put("template", if (idea.seconds <= 60) "shorts_cinematic" else "youtube_longform")
        return body.put("script", "")
    }

    fun fromDraft(d: Draft, base: JSONObject): JSONObject {
        val body = JSONObject(base.toString()).put("template", d.template).put("style", d.style)
            .put("motion", if (d.aiVideo == "off") "stills" else "ai_video").put("ai_video_scenes", if (d.aiVideo == "all") "all" else "hook")
        return if (d.script.isNotBlank()) body.put("script", d.script).put("idea", d.title)
        else body.put("idea", if (d.hook.isNotBlank()) "${d.idea.ifBlank { d.title }}\nHook: ${d.hook}" else d.idea.ifBlank { d.title })
            .put("duration_s", d.durationS).put("script", "")
    }

    fun forChannel(ch: Channel, slot: Slot, base: JSONObject): JSONObject {
        val b = JSONObject(base.toString()).put("style", ch.style).put("motion", if (ch.aiVideo == "off") "stills" else "ai_video")
            .put("ai_video_scenes", if (ch.aiVideo == "all") "all" else "hook")
        if (ch.voice.isNotBlank()) b.put("voice", ch.voice)
        b.remove("template"); b.remove("duration_s")
        return fromIdea(slot.trend, slot.idea, slot.script, b)
    }
}
