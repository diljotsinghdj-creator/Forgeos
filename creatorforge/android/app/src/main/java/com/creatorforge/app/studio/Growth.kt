package com.creatorforge.app.studio

import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder

/** A channel's look and sound: applied by the worker when it renders. */
data class Brand(
    val logoAssetId: String = "", val logoName: String = "", val logoPosition: String = "top-right",
    val captionColor: String = "#FFFFFF", val highlightColor: String = "#FFD400",
    val introText: String = "", val outroText: String = ""
) {
    fun toJson(): JSONObject = JSONObject().put("logo_asset_id", logoAssetId).put("logo_name", logoName).put("logo_position", logoPosition)
        .put("caption_color", captionColor).put("highlight_color", highlightColor).put("intro_text", introText).put("outro_text", outroText)

    /** What the worker's /v1/productions accepts as `brand`. */
    fun forWorker(): JSONObject = JSONObject().apply {
        put("caption_color", captionColor); put("highlight_color", highlightColor)
        if (logoAssetId.isNotBlank()) { put("logo_asset_id", logoAssetId); put("logo_position", logoPosition) }
        if (introText.isNotBlank()) put("intro_text", introText)
        if (outroText.isNotBlank()) put("outro_text", outroText)
    }

    companion object {
        fun from(j: JSONObject?): Brand = if (j == null) Brand() else Brand(j.optString("logo_asset_id"), j.optString("logo_name"),
            j.optString("logo_position", "top-right"), j.optString("caption_color", "#FFFFFF"), j.optString("highlight_color", "#FFD400"),
            j.optString("intro_text"), j.optString("outro_text"))
    }
}

// ---- Series --------------------------------------------------------------------------------------

data class Episode(val number: Int, val title: String, val summary: String, val script: String) {
    fun toJson(): JSONObject = JSONObject().put("number", number).put("title", title).put("summary", summary).put("script", script)
    companion object { fun from(j: JSONObject) = Episode(j.optInt("number"), j.optString("title"), j.optString("summary"), j.optString("script")) }
}

data class Series(
    val id: String, val name: String, val premise: String, val characters: String = "", val style: String = "cinematic",
    val seconds: Int = 60, val episodes: List<Episode> = emptyList(), val createdAt: Long = System.currentTimeMillis()
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("name", name).put("premise", premise).put("characters", characters)
        .put("style", style).put("seconds", seconds).put("created_at", createdAt)
        .put("episodes", JSONArray().apply { episodes.forEach { put(it.toJson()) } })
    companion object {
        fun from(j: JSONObject): Series {
            val e = j.optJSONArray("episodes") ?: JSONArray()
            return Series(j.getString("id"), j.optString("name"), j.optString("premise"), j.optString("characters"), j.optString("style", "cinematic"),
                j.optInt("seconds", 60), (0 until e.length()).map { Episode.from(e.getJSONObject(it)) }, j.optLong("created_at"))
        }
    }
}

// ---- Safety --------------------------------------------------------------------------------------

data class SafetyIssue(val level: String, val text: String, val fix: String) // level: high | medium | low

object SafetyRules {
    /** Checks that need no AI: phrases that commonly get videos limited, demonetised or into legal trouble. */
    fun scan(script: String): List<SafetyIssue> {
        val t = script.lowercase()
        val out = mutableListOf<SafetyIssue>()
        fun hit(words: List<String>) = words.firstOrNull { Regex("\\b" + Regex.escape(it) + "\\b").containsMatchIn(t) }
        hit(listOf("cure", "cures", "treats", "heal cancer", "detox", "miracle"))?.let {
            out += SafetyIssue("high", "Health claim (\"$it\")", "Say \"some studies suggest\" and add \"this isn't medical advice\".")
        }
        hit(listOf("guaranteed", "risk-free", "get rich", "double your money", "can't lose", "100% profit"))?.let {
            out += SafetyIssue("high", "Money promise (\"$it\")", "Remove promises; add \"not financial advice\".")
        }
        hit(listOf("murderer", "fraudster", "criminal", "scammer", "rapist", "paedophile", "pedophile"))?.let {
            out += SafetyIssue("high", "Calling someone \"$it\"", "Only if a court said so - otherwise say \"accused of\" or \"charged with\".")
        }
        hit(listOf("suicide", "self-harm", "kill yourself"))?.let {
            out += SafetyIssue("medium", "Sensitive topic (\"$it\")", "Keep it non-graphic and add a helpline in the description.")
        }
        hit(listOf("gore", "beheaded", "graphic", "blood everywhere"))?.let {
            out += SafetyIssue("medium", "Graphic wording (\"$it\")", "Tone it down to keep ads on the video.")
        }
        if (Regex("\\b(19|20)\\d{2}\\b|\\b\\d+(\\.\\d+)?\\s?(%|percent|million|billion)").containsMatchIn(t)) {
            out += SafetyIssue("low", "Dates, numbers or statistics", "Check each one against a source before posting.")
        }
        if (Regex("\"[^\"]{12,}\"").containsMatchIn(script)) {
            out += SafetyIssue("low", "A direct quote", "Make sure the person really said it, word for word.")
        }
        return out
    }

    val checklist = listOf(
        "Music: only use tracks you made, generated, or that are licensed for YouTube/TikTok.",
        "No logos, brands or famous faces used in a way that suggests they endorse you.",
        "AI-made realistic people or events: tick YouTube's \"altered or synthetic content\" box.",
        "Facts: check names, dates and numbers against at least one reliable source.",
        "Kids: don't mark as \"made for kids\" unless it really is - it turns off comments and some ads.",
    )
}

// ---- Templates -----------------------------------------------------------------------------------

/** A ready-made channel recipe: niche, look, rhythm, tone and brand colours. Shareable as a short code. */
data class ChannelTemplate(
    val id: String, val name: String, val niche: String, val style: String, val format: String, val perWeek: Int,
    val tone: String, val audience: String, val captionColor: String, val highlightColor: String, val note: String
) {
    fun toJson(): JSONObject = JSONObject().put("id", id).put("name", name).put("niche", niche).put("style", style).put("format", format)
        .put("per_week", perWeek).put("tone", tone).put("audience", audience).put("caption_color", captionColor)
        .put("highlight_color", highlightColor).put("note", note)

    fun toChannel(id: String) = Channel(id, name, niche, region = "GB", format = format, perWeek = perWeek, style = style, tone = tone, audience = audience)
    fun brand() = Brand(captionColor = captionColor, highlightColor = highlightColor, introText = name.uppercase())

    /** "CFT1:" + base64 JSON - paste it into a chat or a note to share. */
    fun shareCode(): String = "CFT1:" + java.util.Base64.getEncoder().encodeToString(toJson().toString().toByteArray())

    companion object {
        fun from(j: JSONObject) = ChannelTemplate(j.optString("id"), j.optString("name"), j.optString("niche", "facts"), j.optString("style", "cinematic"),
            j.optString("format", "shorts"), j.optInt("per_week", 7), j.optString("tone"), j.optString("audience"),
            j.optString("caption_color", "#FFFFFF"), j.optString("highlight_color", "#FFD400"), j.optString("note"))

        fun fromShareCode(code: String): ChannelTemplate {
            val c = code.trim()
            require(c.startsWith("CFT1:")) { "That isn't a CreatorForge template code" }
            val t = from(JSONObject(String(java.util.Base64.getDecoder().decode(c.removePrefix("CFT1:")))))
            require(t.name.isNotBlank() && Niches.exists(t.niche)) { "The template code is damaged" }
            return t
        }

        val starters = listOf(
            ChannelTemplate("dark_history", "Dark History", "history", "documentary", "mixed", 7, "calm, ominous, storytelling", "history lovers 18-45", "#FFFFFF", "#C0392B", "Forgotten events, told like a mystery."),
            ChannelTemplate("unsolved", "Unsolved Files", "mystery", "cinematic", "shorts", 7, "suspenseful, careful with facts", "true-crime fans", "#FFFFFF", "#FF3B30", "Cold cases and strange disappearances."),
            ChannelTemplate("money_minute", "Money Minute", "money", "hyperreal", "shorts", 10, "clear, punchy, practical", "young adults starting out", "#FFFFFF", "#34C759", "One money habit per Short. Not financial advice."),
            ChannelTemplate("space_facts", "Cosmic Facts", "science", "cinematic", "shorts", 7, "awe, wonder", "curious teens and adults", "#FFFFFF", "#00E5FF", "Mind-blowing space facts."),
            ChannelTemplate("ai_daily", "AI Daily", "ai", "hyperreal", "shorts", 14, "fast, newsy, excited", "tech-curious people", "#FFFFFF", "#FFD400", "Today's AI news in 45 seconds."),
            ChannelTemplate("stoic", "Stoic Mind", "motivation", "cinematic", "shorts", 7, "deep, calm, wise", "self-improvers", "#F5F5F5", "#D4AF37", "Stoic lessons for modern life."),
            ChannelTemplate("did_you_know", "Did You Know?", "facts", "animated_3d", "shorts", 14, "playful, surprising", "everyone", "#FFFFFF", "#FF9500", "Quick weird facts."),
            ChannelTemplate("anime_tales", "Anime Tales", "entertainment", "anime", "shorts", 5, "emotional storytelling", "anime fans", "#FFFFFF", "#FF2D55", "Original short stories in anime style."),
            ChannelTemplate("history_docs", "History Deep Dives", "history", "documentary", "long", 2, "authoritative documentary narration", "documentary watchers", "#FFFFFF", "#D4AF37", "10-minute documentaries."),
            ChannelTemplate("side_hustle", "Side Hustle Lab", "business", "hyperreal", "shorts", 7, "motivating, realistic", "people wanting extra income", "#FFFFFF", "#34C759", "Honest side-hustle breakdowns."),
        )
    }
}

// ---- Analytics (public YouTube stats, API key only) ------------------------------------------------

data class VideoStat(val id: String, val title: String, val published: String, val views: Long, val likes: Long, val comments: Long, val seconds: Int) {
    val isShort get() = seconds in 1..61
}

data class ChannelStats(val channelId: String, val title: String, val subscribers: Long, val totalViews: Long, val videos: List<VideoStat>)

object YouTubeStats {
    private const val API = "https://www.googleapis.com/youtube/v3"
    private fun enc(s: String) = URLEncoder.encode(s, "UTF-8")

    private fun json(f: Fetcher, url: String): JSONObject {
        val (code, body) = f.get(url)
        if (code == 403 && "quota" in body.lowercase()) throw SourceException("YouTube's daily free limit is used up - try again tomorrow")
        if (code >= 400) throw SourceException("YouTube said HTTP $code - check the YouTube key in Settings")
        return JSONObject(body)
    }

    /** ISO-8601 duration (PT1M5S) to seconds. */
    fun seconds(iso: String): Int {
        val m = Regex("P(?:(\\d+)D)?T?(?:(\\d+)H)?(?:(\\d+)M)?(?:(\\d+)S)?").matchEntire(iso) ?: return 0
        val (d, h, mi, s) = m.destructured
        return (d.toIntOrNull() ?: 0) * 86400 + (h.toIntOrNull() ?: 0) * 3600 + (mi.toIntOrNull() ?: 0) * 60 + (s.toIntOrNull() ?: 0)
    }

    /** handle: "@name", a channel id "UC…", or a channel URL. Reads the latest [max] uploads. */
    fun fetch(f: Fetcher, handleOrId: String, key: String, max: Int = 50): ChannelStats {
        if (key.isBlank()) throw SourceException("Add your free YouTube API key in Settings first")
        val h = handleOrId.trim().substringAfterLast("youtube.com/").removePrefix("channel/").trim('/')
        require(h.isNotBlank()) { "Type your channel handle, e.g. @darkhistory" }
        val q = if (h.startsWith("UC") && h.length >= 20) "id=${enc(h)}" else "forHandle=${enc(if (h.startsWith("@")) h else "@$h")}"
        val ch = json(f, "$API/channels?part=snippet,statistics,contentDetails&$q&key=$key").optJSONArray("items")?.optJSONObject(0)
            ?: throw SourceException("No YouTube channel found for \"$handleOrId\"")
        val uploads = ch.getJSONObject("contentDetails").getJSONObject("relatedPlaylists").getString("uploads")
        val items = json(f, "$API/playlistItems?part=contentDetails&maxResults=${max.coerceIn(1, 50)}&playlistId=$uploads&key=$key").optJSONArray("items") ?: JSONArray()
        val ids = (0 until items.length()).map { items.getJSONObject(it).getJSONObject("contentDetails").getString("videoId") }
        val videos = if (ids.isEmpty()) emptyList() else {
            val v = json(f, "$API/videos?part=snippet,statistics,contentDetails&id=${ids.joinToString(",")}&key=$key").optJSONArray("items") ?: JSONArray()
            (0 until v.length()).map { v.getJSONObject(it) }.map { o ->
                val st = o.optJSONObject("statistics") ?: JSONObject()
                VideoStat(o.getString("id"), o.getJSONObject("snippet").optString("title"), o.getJSONObject("snippet").optString("publishedAt").take(10),
                    st.optString("viewCount").toLongOrNull() ?: 0, st.optString("likeCount").toLongOrNull() ?: 0, st.optString("commentCount").toLongOrNull() ?: 0,
                    seconds(o.optJSONObject("contentDetails")?.optString("duration").orEmpty()))
            }
        }
        val s = ch.optJSONObject("statistics") ?: JSONObject()
        return ChannelStats(ch.getString("id"), ch.getJSONObject("snippet").optString("title"), s.optString("subscriberCount").toLongOrNull() ?: 0,
            s.optString("viewCount").toLongOrNull() ?: 0, videos)
    }

    /** Simple patterns without AI: which kinds of titles and formats get more views on this channel. */
    fun patterns(stats: ChannelStats): List<String> {
        val v = stats.videos.filter { it.views > 0 }
        if (v.size < 4) return listOf("Post a few more videos - patterns need at least 4 with views.")
        fun avg(list: List<VideoStat>) = if (list.isEmpty()) 0.0 else list.map { it.views }.average()
        val out = mutableListOf<String>()
        fun compare(label: String, yes: List<VideoStat>, no: List<VideoStat>) {
            if (yes.size >= 2 && no.size >= 2) {
                val a = avg(yes); val b = avg(no)
                if (b > 0 && (a / b >= 1.3 || b / a >= 1.3)) out += if (a > b) "$label get %.1f× the views.".format(a / b) else "$label get %.1f× fewer views.".format(b / a)
            }
        }
        compare("Titles with a number", v.filter { Regex("\\d").containsMatchIn(it.title) }, v.filter { !Regex("\\d").containsMatchIn(it.title) })
        compare("Question titles", v.filter { "?" in it.title }, v.filter { "?" !in it.title })
        compare("Shorts", v.filter { it.isShort }, v.filter { !it.isShort })
        val top = v.sortedByDescending { it.views }.take(3).joinToString("; ") { "\"${it.title}\"" }
        out += "Top videos: $top"
        return out
    }
}
