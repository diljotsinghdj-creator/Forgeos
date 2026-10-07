package com.creatorforge.app.studio

import org.json.JSONArray
import org.json.JSONObject

/** One mention of a topic in one source (a Wikipedia page, a headline, a Reddit post...). */
data class Signal(
    val source: String, val title: String, val url: String = "", val metric: Long = 0, val metricLabel: String = "",
    val publisher: String = "", val snippet: String = ""
) {
    fun toJson(): JSONObject = JSONObject().put("source", source).put("title", title).put("url", url).put("metric", metric)
        .put("metric_label", metricLabel).put("publisher", publisher).put("snippet", snippet)

    companion object {
        fun from(j: JSONObject) = Signal(j.optString("source"), j.optString("title"), j.optString("url"), j.optLong("metric"),
            j.optString("metric_label"), j.optString("publisher"), j.optString("snippet"))
    }
}

/** A trending topic: signals from several sources grouped together and ranked. */
data class Trend(
    val id: String, val title: String, val heat: Int, val score: Double, val sources: List<String>,
    val metrics: Map<String, Long>, val headlines: List<String>, val signals: List<Signal>, val evergreen: Boolean = false
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("title", title).put("heat", heat).put("score", score)
        .put("sources", JSONArray(sources)).put("metrics", JSONObject(metrics as Map<*, *>)).put("headlines", JSONArray(headlines))
        .put("signals", JSONArray().apply { signals.forEach { put(it.toJson()) } }).put("evergreen", evergreen)

    companion object {
        fun from(j: JSONObject): Trend {
            val m = j.optJSONObject("metrics") ?: JSONObject()
            val s = j.optJSONArray("signals") ?: JSONArray()
            return Trend(j.getString("id"), j.optString("title"), j.optInt("heat"), j.optDouble("score", 0.0),
                strings(j.optJSONArray("sources")), m.keys().asSequence().associateWith { m.optLong(it) },
                strings(j.optJSONArray("headlines")), (0 until s.length()).map { Signal.from(s.getJSONObject(it)) }, j.optBoolean("evergreen"))
        }

        /** A topic the user typed themselves (no live signals). */
        fun manual(title: String) = Trend("manual-" + title.lowercase().hashCode().toUInt().toString(16), title.trim(), 0, 0.0,
            emptyList(), emptyMap(), emptyList(), emptyList())
    }
}

data class SourceStatus(val id: String, val name: String, val ok: Boolean, val count: Int, val error: String)

data class TrendScan(
    val period: String, val niche: String, val region: String, val query: String, val fetchedAt: Long,
    val sources: List<SourceStatus>, val items: List<Trend>, val cached: Boolean = false
) {
    fun toJson(): JSONObject = JSONObject().put("period", period).put("niche", niche).put("region", region).put("query", query)
        .put("fetched_at", fetchedAt)
        .put("sources", JSONArray().apply { sources.forEach { put(JSONObject().put("id", it.id).put("name", it.name).put("ok", it.ok).put("count", it.count).put("error", it.error)) } })
        .put("items", JSONArray().apply { items.forEach { put(it.toJson()) } })

    companion object {
        fun from(j: JSONObject, cached: Boolean): TrendScan {
            val s = j.optJSONArray("sources") ?: JSONArray()
            val i = j.optJSONArray("items") ?: JSONArray()
            return TrendScan(j.optString("period"), j.optString("niche"), j.optString("region"), j.optString("query"), j.optLong("fetched_at"),
                (0 until s.length()).map { s.getJSONObject(it).let { o -> SourceStatus(o.optString("id"), o.optString("name"), o.optBoolean("ok"), o.optInt("count"), o.optString("error")) } },
                (0 until i.length()).map { Trend.from(i.getJSONObject(it)) }, cached)
        }
    }
}

data class Idea(val title: String, val hook: String, val angle: String, val format: String, val whyNow: String, val seconds: Int) {
    fun toJson(): JSONObject = JSONObject().put("title", title).put("hook", hook).put("angle", angle).put("format", format)
        .put("why_now", whyNow).put("seconds", seconds)

    companion object {
        fun from(j: JSONObject) = Idea(j.optString("title"), j.optString("hook"), j.optString("angle"), j.optString("format", "short"),
            j.optString("why_now"), j.optInt("seconds", 45))
    }
}

data class Script(
    val title: String, val text: String, val description: String, val hashtags: List<String>, val seconds: Int,
    val sources: List<Pair<String, String>>, val verify: String
)

/** One scene of a breakdown: what is said, what is seen, and ready-to-paste prompts for image and video tools. */
data class Scene(
    val narration: String, val visual: String, val shot: String, val camera: String, val mood: String,
    val imagePrompt: String, val videoPrompt: String, val negative: String
) {
    fun toJson(): JSONObject = JSONObject().put("narration", narration).put("visual", visual).put("shot", shot).put("camera", camera)
        .put("mood", mood).put("image_prompt", imagePrompt).put("video_prompt", videoPrompt).put("negative", negative)

    companion object {
        fun from(j: JSONObject) = Scene(j.optString("narration"), j.optString("visual"), j.optString("shot"), j.optString("camera"),
            j.optString("mood"), j.optString("image_prompt"), j.optString("video_prompt"), j.optString("negative"))
    }
}

/** The Director chat's working draft. */
data class Draft(
    val title: String = "", val idea: String = "", val hook: String = "", val script: String = "", val durationS: Int = 45,
    val template: String = "shorts_cinematic", val style: String = "cinematic", val aiVideo: String = "off"
) {
    fun toJson(): JSONObject = JSONObject().put("title", title).put("idea", idea).put("hook", hook).put("script", script)
        .put("duration_s", durationS).put("template", template).put("style", style).put("ai_video", aiVideo)

    val isEmpty get() = idea.isBlank() && script.isBlank()

    companion object {
        fun from(j: JSONObject?): Draft = if (j == null) Draft() else Draft(j.optString("title"), j.optString("idea"), j.optString("hook"),
            j.optString("script"), j.optInt("duration_s", 45), j.optString("template", "shorts_cinematic"), j.optString("style", "cinematic"),
            j.optString("ai_video", "off"))
    }
}

data class ChatReply(val reply: String, val ready: Boolean, val draft: Draft, val suggestions: List<String>)

/** A saved piece of work in the Scripts library: a script and/or its scene breakdown. */
data class SavedScript(
    val id: String, val title: String, val script: String, val hook: String = "", val description: String = "",
    val hashtags: List<String> = emptyList(), val style: String = "cinematic", val template: String = "shorts_cinematic",
    val scenes: List<Scene> = emptyList(), val source: String = "", val createdAt: Long = System.currentTimeMillis()
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("title", title).put("script", script).put("hook", hook)
        .put("description", description).put("hashtags", JSONArray(hashtags)).put("style", style).put("template", template)
        .put("scenes", JSONArray().apply { scenes.forEach { put(it.toJson()) } }).put("source", source).put("created_at", createdAt)

    companion object {
        fun from(j: JSONObject): SavedScript {
            val s = j.optJSONArray("scenes") ?: JSONArray()
            return SavedScript(j.getString("id"), j.optString("title"), j.optString("script"), j.optString("hook"), j.optString("description"),
                strings(j.optJSONArray("hashtags")), j.optString("style", "cinematic"), j.optString("template", "shorts_cinematic"),
                (0 until s.length()).map { Scene.from(s.getJSONObject(it)) }, j.optString("source"), j.optLong("created_at"))
        }
    }
}

/** A faceless channel and its weekly plan, stored on the phone. */
data class Channel(
    val id: String, val name: String, val niche: String = "facts", val keyword: String = "", val region: String = "GB",
    val format: String = "shorts", val perWeek: Int = 7, val style: String = "cinematic", val voice: String = "",
    val aiVideo: String = "off", val tone: String = "", val audience: String = "", val postTime: String = "18:00",
    val slots: List<Slot> = emptyList(), val plannedAt: Long = 0
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("name", name).put("niche", niche).put("keyword", keyword).put("region", region)
        .put("format", format).put("per_week", perWeek).put("style", style).put("voice", voice).put("ai_video", aiVideo)
        .put("tone", tone).put("audience", audience).put("post_time", postTime).put("planned_at", plannedAt)
        .put("slots", JSONArray().apply { slots.forEach { put(it.toJson()) } })

    companion object {
        fun from(j: JSONObject): Channel {
            val s = j.optJSONArray("slots") ?: JSONArray()
            return Channel(j.getString("id"), j.optString("name"), j.optString("niche", "facts"), j.optString("keyword"), j.optString("region", "GB"),
                j.optString("format", "shorts"), j.optInt("per_week", 7), j.optString("style", "cinematic"), j.optString("voice"),
                j.optString("ai_video", "off"), j.optString("tone"), j.optString("audience"), j.optString("post_time", "18:00"),
                (0 until s.length()).map { Slot.from(s.getJSONObject(it)) }, j.optLong("planned_at"))
        }
    }
}

data class Slot(
    val id: String, val day: String, val time: String, val status: String, val idea: Idea, val trend: Trend,
    val script: String = "", val productionId: String = ""
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("day", day).put("time", time).put("status", status)
        .put("idea", idea.toJson()).put("trend", trend.toJson()).put("script", script).put("production_id", productionId)

    companion object {
        fun from(j: JSONObject) = Slot(j.getString("id"), j.optString("day"), j.optString("time"), j.optString("status", "planned"),
            Idea.from(j.optJSONObject("idea") ?: JSONObject()), Trend.from(j.optJSONObject("trend") ?: JSONObject().put("id", "")),
            j.optString("script"), j.optString("production_id"))
    }
}

internal fun strings(a: JSONArray?): List<String> = (0 until (a?.length() ?: 0)).map { a!!.optString(it) }
