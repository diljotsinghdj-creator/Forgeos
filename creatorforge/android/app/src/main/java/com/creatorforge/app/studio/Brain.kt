package com.creatorforge.app.studio

import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate
import java.util.UUID

/**
 * The studio's writing brain, on the phone: ideas, grounded scripts, Director chat, scene breakdowns with
 * image/video prompts, and weekly channel plans. With a [TextModel] it uses AI; without one it falls back
 * to simple templates so the app still works offline and with no key.
 */
class Brain(private val model: TextModel?) {
    val usesAi get() = model != null

    private fun ask(system: String, user: String, check: (JSONObject) -> Any): Any {
        val m = model ?: throw AiException("No Script AI set up")
        var error = ""
        repeat(2) {
            val raw = m.complete(system, if (error.isEmpty()) user else "$user\n\nYour previous answer was invalid: $error. Return corrected JSON only.")
            try { return check(extractJson(raw)) } catch (e: AiException) { throw e } catch (e: Exception) { error = e.message ?: "invalid JSON" }
        }
        throw AiException("The AI gave an unusable answer twice ($error). Try again.")
    }

    // ---- ideas ----------------------------------------------------------------------------------
    fun ideas(trend: Trend, count: Int = 5, format: String = "short", niche: String = "", period: String = "week"): List<Idea> {
        val n = count.coerceIn(1, 10)
        if (model == null) return templateIdeas(trend, n, format)
        val user = "TOPIC: ${trend.title}\nPERIOD: trending this $period\nNICHE: ${niche.ifBlank { "general" }}\n" +
            "FORMAT: $format (${when (format) { "short" -> "<= 60 seconds"; "long" -> "6-12 minutes"; else -> "mix of both" }})\nCOUNT: $n\nSIGNALS:\n${signalsBlock(trend)}"
        @Suppress("UNCHECKED_CAST")
        return ask(IDEAS_SYSTEM, user) { d ->
            val a = d.optJSONArray("ideas") ?: JSONArray()
            val out = (0 until a.length()).mapNotNull { i -> a.optJSONObject(i)?.let { cleanIdea(it, format) } }
            require(out.isNotEmpty()) { "no usable ideas (each needs a title and a hook)" }
            out.take(n)
        } as List<Idea>
    }

    private fun cleanIdea(j: JSONObject, wanted: String): Idea? {
        val title = j.optString("title").trim().take(120)
        val hook = j.optString("hook").trim().take(140)
        if (title.isBlank() || hook.isBlank()) return null
        val f = j.optString("format").lowercase().let { if (it == "short" || it == "long") it else if (wanted == "long") "long" else "short" }
        var secs = j.optInt("seconds", 0).let { if (it > 0) it else if (f == "long") 600 else 45 }
        secs = if (f == "short") secs.coerceIn(15, 60) else secs.coerceIn(120, 900)
        return Idea(title, hook, j.optString("angle").trim().take(400), f, j.optString("why_now").trim().take(240), secs)
    }

    private fun templateIdeas(trend: Trend, n: Int, format: String): List<Idea> {
        val t = trend.title
        val pool = listOf(
            "What actually happened with $t" to "Here's what really happened with $t.",
            "$t explained in 60 seconds" to "You've seen $t everywhere. Here's why.",
            "3 things nobody tells you about $t" to "Three things about $t nobody is telling you.",
            "Why everyone is talking about $t" to "Everyone is talking about $t. This is why.",
            "$t: myth vs fact" to "Most people get $t wrong.",
            "The story behind $t" to "The story behind $t is stranger than you think.",
            "$t - what happens next?" to "What happens next with $t?",
        )
        return (0 until n).map { i ->
            val (title, hook) = pool[i % pool.size]
            val long = format == "long" || (format == "mixed" && i % 4 == 3)
            Idea(title, hook, "Use the real headlines as the backbone; keep claims to what they say.", if (long) "long" else "short",
                if (trend.sources.isEmpty()) "" else "Trending on ${trend.sources.joinToString(", ")}", if (long) 600 else 45)
        }
    }

    // ---- scripts --------------------------------------------------------------------------------
    fun script(trend: Trend, idea: Idea, seconds: Int = idea.seconds): Script {
        val secs = seconds.coerceIn(15, 900)
        val words = Math.round(secs * WORDS_PER_SECOND).toInt()
        if (model == null) return templateScript(trend, idea, secs)
        val user = "IDEA: ${idea.title}\nHOOK: ${idea.hook}\nANGLE: ${idea.angle}\nTOPIC: ${trend.title}\n" +
            "TARGET: about $words words ($secs seconds of narration)\nSOURCES:\n${signalsBlock(trend)}"
        return ask(SCRIPT_SYSTEM, user) { d ->
            val text = d.optString("script").replace(Regex("\\s+"), " ").trim()
            val count = text.split(" ").count { it.isNotBlank() }
            require(count >= maxOf(15, words / 3)) { "script is too short ($count words, need about $words)" }
            val used = (0 until (d.optJSONArray("facts_used")?.length() ?: 0)).mapNotNull { d.getJSONArray("facts_used").optInt(it, 0).takeIf { n -> n in 1..trend.signals.size } }
            Script(d.optString("title").ifBlank { idea.title }.take(100), text.take(20000), d.optString("description").trim().take(1500),
                hashtags(d.optJSONArray("hashtags")), secs, used.map { trend.signals[it - 1].let { s -> s.title to s.url } }, VERIFY)
        } as Script
    }

    private fun templateScript(trend: Trend, idea: Idea, secs: Int): Script {
        val facts = (listOf(trend.title) + trend.headlines).distinct().take(maxOf(2, secs / 10))
        val body = facts.drop(1).joinToString(" ") { "Reports say: ${it.trimEnd('.')}." }
        val text = "${idea.hook} ${if (body.isBlank()) "Here is what we know about ${trend.title}." else body} " +
            "That's the story so far. Follow for more."
        return Script(idea.title, text, "${idea.title}. ${trend.headlines.firstOrNull().orEmpty()}".trim(),
            listOf("#shorts") + RadarWords.tags(trend.title), secs, trend.signals.take(3).map { it.title to it.url },
            "Template script (no Script AI set up) - add a free key in Settings for a real script. $VERIFY")
    }

    // ---- Director chat --------------------------------------------------------------------------
    fun chat(messages: List<Pair<String, String>>, draft: Draft): ChatReply {
        val convo = messages.filter { it.second.isNotBlank() }.takeLast(20)
        require(convo.isNotEmpty() && convo.last().first == "user") { "say something first" }
        if (model == null) {
            val last = convo.last().second.trim()
            val d = draft.copy(title = draft.title.ifBlank { last.take(60) }, idea = if (draft.idea.isBlank()) last else "${draft.idea}\n$last")
            return ChatReply("Saved to your draft. Without Script AI I can't write for you yet - add a free key in Settings (Script AI) and I'll plan, write and polish it with you.",
                true, d, listOf("How do I get a free key?"))
        }
        val transcript = convo.joinToString("\n") { (r, c) -> "${if (r == "user") "CREATOR" else "DIRECTOR"}: ${c.trim().take(4000)}" }
        val user = "CURRENT DRAFT: ${draft.toJson()}\n\nCONVERSATION:\n$transcript\n\nReply as DIRECTOR."
        return ask(CHAT_SYSTEM, user) { d ->
            val reply = d.optString("reply").trim()
            require(reply.isNotBlank()) { "missing reply" }
            val nd = cleanDraft(d.optJSONObject("draft"), draft)
            val sugg = strings(d.optJSONArray("suggestions")).map { it.trim().take(60) }.filter { it.isNotBlank() }.take(3)
            ChatReply(reply.take(2000), d.optBoolean("ready") && !nd.isEmpty, nd, sugg)
        } as ChatReply
    }

    private fun cleanDraft(j: JSONObject?, old: Draft): Draft {
        if (j == null) return old
        fun s(k: String, cur: String) = j.optString(k).trim().ifBlank { cur }
        val dur = j.optInt("duration_s", old.durationS).coerceIn(10, 900)
        val template = s("template", old.template).let { t -> if (Styles.templates.any { it.first == t }) t else if (dur > 90) "youtube_longform" else "shorts_cinematic" }
        val style = s("style", old.style).let { st -> if (Styles.presets.any { it.first == st }) st else "cinematic" }
        val ai = s("ai_video", old.aiVideo).let { if (it in setOf("off", "hook", "all")) it else "off" }
        return Draft(s("title", old.title).take(100), s("idea", old.idea).take(3000), s("hook", old.hook).take(160),
            s("script", old.script).take(20000), dur, template, style, ai)
    }

    // ---- scene breakdown + prompts ---------------------------------------------------------------
    /** Splits a script (or an idea) into scenes with ready-to-paste image and video prompts. */
    fun scenes(text: String, isScript: Boolean, style: String, template: String, seconds: Int = 45): List<Scene> {
        val look = Styles.prompt(style)
        if (model == null || isScript && text.split(Regex("\\s+")).size < 8) {
            val parts = if (isScript) groupSentences(text, template) else listOf(text)
            return parts.map { p -> forge(p, p.trimEnd('.'), "medium", "slow push in", "", "", look) }
        }
        val n = if (isScript) groupSentences(text, template).size
        else Math.round(seconds / (Styles.sceneSeconds[template] ?: 5.0)).toInt().coerceIn(3, 40)
        val user = (if (isScript) "SCRIPT (final - keep these exact words, already split):\n" +
            groupSentences(text, template).mapIndexed { i, s -> "${i + 1}. $s" }.joinToString("\n")
        else "IDEA: $text\nLENGTH: about $seconds seconds") + "\nSCENE_COUNT: $n\nLOOK: ${Styles.name(style)}"
        @Suppress("UNCHECKED_CAST")
        return ask(SCENES_SYSTEM, user) { d ->
            val a = d.optJSONArray("scenes") ?: JSONArray()
            val fixed = if (isScript) groupSentences(text, template) else null
            val out = (0 until a.length()).mapNotNull { i ->
                val s = a.optJSONObject(i) ?: return@mapNotNull null
                val narration = fixed?.getOrNull(i) ?: s.optString("narration").trim()
                val visual = s.optString("visual").trim()
                if (narration.isBlank() || visual.isBlank()) null
                else forge(narration, visual, s.optString("shot"), s.optString("camera"), s.optString("mood"), s.optString("motion"), look)
            }
            require(out.size >= minOf(n, 2)) { "expected $n scenes, got ${out.size}" }
            out
        } as List<Scene>
    }

    private fun forge(narration: String, visual: String, shot: String, camera: String, mood: String, motion: String, look: String): Scene {
        val v = visual.trimEnd('.')
        val framing = listOfNotNull(shot.takeIf { it.isNotBlank() }?.let { "$it shot" }, camera.ifBlank { null }, mood.takeIf { it.isNotBlank() }?.let { "$it mood" })
        val image = (listOf(v) + listOfNotNull(framing.joinToString(", ").ifBlank { null }) + look).joinToString(". ")
        val video = "${motion.ifBlank { "subtle natural movement in the scene: $v" }}. Camera: ${camera.ifBlank { "slow cinematic camera move" }}. $v. $look. " +
            "Smooth realistic motion, natural physics, consistent identity, stable details"
        return Scene(narration, visual, shot, camera, mood, image, video, Styles.NEGATIVE)
    }

    // ---- thumbnail text --------------------------------------------------------------------------
    /** Short, punchy thumbnail texts: (line1, line2, highlight word). */
    fun thumbnailIdeas(topic: String, count: Int = 5): List<Triple<String, String, String>> {
        val t = topic.trim().ifBlank { "this" }
        if (model == null) {
            val w = t.split(Regex("\\s+")).take(3).joinToString(" ")
            return listOf(Triple("NOBODY", "SAW THIS COMING", "NOBODY"), Triple(w, "EXPLAINED", "EXPLAINED"), Triple("THE TRUTH", "ABOUT $w", "TRUTH"),
                Triple("DON'T", "MAKE THIS MISTAKE", "DON'T"), Triple("$w", "IN 60 SECONDS", "60")).take(count)
        }
        @Suppress("UNCHECKED_CAST")
        return ask(THUMB_SYSTEM, "TOPIC: $t\nCOUNT: $count") { d ->
            val a = d.optJSONArray("ideas") ?: JSONArray()
            val out = (0 until a.length()).mapNotNull { i -> a.optJSONObject(i)?.let {
                val l1 = it.optString("line1").trim().take(24); val l2 = it.optString("line2").trim().take(28)
                if (l1.isBlank()) null else Triple(l1, l2, it.optString("highlight").trim().take(20))
            } }
            require(out.isNotEmpty()) { "no thumbnail ideas" }
            out.take(count)
        } as List<Triple<String, String, String>>
    }

    // ---- series ---------------------------------------------------------------------------------
    /** Writes the next episode with the story so far in mind. */
    fun nextEpisode(series: Series): Episode {
        val n = series.episodes.size + 1
        val words = Math.round(series.seconds * WORDS_PER_SECOND).toInt()
        if (model == null) {
            val prev = series.episodes.lastOrNull()
            val text = "Part $n of ${series.name}. " + (prev?.let { "Last time: ${it.summary} " } ?: "") +
                "${series.premise.trimEnd('.')}. What happens next will surprise you. Follow so you don't miss part ${n + 1}."
            return Episode(n, "${series.name} - Part $n", "Part $n continues: ${series.premise.take(80)}", text)
        }
        val story = series.episodes.takeLast(8).joinToString("\n") { "Part ${it.number}: ${it.summary}" }.ifBlank { "(this is the first episode)" }
        val user = "SERIES: ${series.name}\nPREMISE: ${series.premise}\nCHARACTERS: ${series.characters.ifBlank { "(invent consistent ones)" }}\n" +
            "STORY SO FAR:\n$story\nWRITE: part $n, about $words words (${series.seconds} seconds)"
        return ask(SERIES_SYSTEM, user) { d ->
            val text = d.optString("script").replace(Regex("\\s+"), " ").trim()
            require(text.split(" ").size >= maxOf(15, words / 3)) { "episode script too short" }
            Episode(n, d.optString("title").ifBlank { "${series.name} - Part $n" }.take(100), d.optString("summary").trim().take(400), text.take(20000))
        } as Episode
    }

    // ---- safety ---------------------------------------------------------------------------------
    /** Rule checks always run; with AI, a careful reviewer adds anything the rules can't see. */
    fun safety(script: String): List<SafetyIssue> {
        val rules = SafetyRules.scan(script)
        if (model == null || script.isBlank()) return rules
        @Suppress("UNCHECKED_CAST")
        val ai = runCatching {
            ask(SAFETY_SYSTEM, "SCRIPT:\n${script.take(12000)}") { d ->
                val a = d.optJSONArray("issues") ?: JSONArray()
                (0 until a.length()).mapNotNull { i -> a.optJSONObject(i)?.let {
                    val lvl = it.optString("level").lowercase().let { l -> if (l in setOf("high", "medium", "low")) l else "medium" }
                    it.optString("issue").trim().takeIf { t -> t.isNotBlank() }?.let { t -> SafetyIssue(lvl, t.take(200), it.optString("fix").trim().take(240)) }
                } }
            } as List<SafetyIssue>
        }.getOrDefault(emptyList())
        return (rules + ai).distinctBy { it.text.lowercase() }.sortedBy { listOf("high", "medium", "low").indexOf(it.level) }
    }

    // ---- analytics insights ------------------------------------------------------------------------
    fun insights(stats: ChannelStats): List<String> {
        val base = YouTubeStats.patterns(stats)
        if (model == null || stats.videos.size < 4) return base
        val list = stats.videos.sortedByDescending { it.views }.take(40)
            .joinToString("\n") { "${it.views} views | ${if (it.isShort) "Short" else "${it.seconds / 60} min"} | ${it.title}" }
        @Suppress("UNCHECKED_CAST")
        return runCatching {
            ask(INSIGHTS_SYSTEM, "CHANNEL: ${stats.title}\nVIDEOS (views | length | title):\n$list") { d ->
                strings(d.optJSONArray("insights")).map { it.trim().take(240) }.filter { it.isNotBlank() }.take(6).also { require(it.isNotEmpty()) { "no insights" } }
            } as List<String>
        }.getOrDefault(base)
    }

    // ---- translation for dubbing -------------------------------------------------------------------
    fun translate(lines: List<String>, language: String): List<String> {
        val m = model ?: throw AiException("Dubbing needs Script AI to translate - add your Gemini key in Settings")
        if (lines.isEmpty()) return emptyList()
        val user = "LANGUAGE: $language\nLINES:\n" + lines.mapIndexed { i, l -> "${i + 1}. $l" }.joinToString("\n")
        @Suppress("UNCHECKED_CAST")
        return ask(TRANSLATE_SYSTEM, user) { d ->
            val out = strings(d.optJSONArray("lines")).map { it.trim() }
            require(out.size == lines.size && out.all { it.isNotBlank() }) { "expected ${lines.size} translated lines, got ${out.size}" }
            out
        } as List<String>
    }

    // ---- hooks -----------------------------------------------------------------------------------
    fun hooks(script: String, count: Int = 3): List<String> {
        val first = sentences(script).firstOrNull().orEmpty()
        if (model == null) {
            val topic = first.trimEnd('.', '!', '?').take(60)
            return listOf("Nobody talks about this: $topic.", "You won't believe what happened next.", "Here's the truth about $topic.").take(count)
        }
        @Suppress("UNCHECKED_CAST")
        return ask(HOOKS_SYSTEM, "CURRENT OPENING: $first\nSCRIPT:\n${script.take(6000)}\nCOUNT: $count") { d ->
            strings(d.optJSONArray("hooks")).map { it.trim().take(200) }.filter { it.isNotBlank() }.take(count).also { require(it.isNotEmpty()) { "no hooks" } }
        } as List<String>
    }

    // ---- channel plans ----------------------------------------------------------------------------
    fun plan(channel: Channel, trends: List<Trend>, start: LocalDate = LocalDate.now().plusDays(1)): List<Slot> {
        val n = channel.perWeek.coerceIn(1, 21)
        val formats = (0 until n).map { i -> when (channel.format) { "long" -> "long"; "mixed" -> if (i % 4 == 3) "long" else "short"; else -> "short" } }
        val note = listOf(Niches[channel.niche].name, channel.tone.takeIf { it.isNotBlank() }?.let { "tone: $it" },
            channel.audience.takeIf { it.isNotBlank() }?.let { "audience: $it" },
            channel.insights.takeIf { it.isNotBlank() }?.let { "what works on this channel: ${it.take(600)}" }).filterNotNull().joinToString("; ")
        val pool = trends.ifEmpty { listOf(Trend.manual("Evergreen " + channel.keyword.ifBlank { Niches[channel.niche].name })) }
        val per = if (n > 3) 2 else 1
        val picked = mutableListOf<Pair<Trend, Idea>>()
        var t = 0
        while (picked.size < n && t < pool.size + 3) {
            val trend = pool[t % pool.size]
            val need = minOf(per, n - picked.size)
            val f = formats.subList(picked.size, picked.size + need).let { if (it.toSet().size == 1) it[0] else "mixed" }
            for (idea in ideas(trend, need, f, note, "week")) {
                if (picked.size >= n) break
                val want = formats[picked.size]
                picked += trend to (if (idea.format == want) idea else idea.copy(format = want, seconds = if (want == "short") 45 else 600))
            }
            t++
        }
        return picked.mapIndexed { i, (trend, idea) ->
            Slot(UUID.randomUUID().toString().take(10), start.plusDays((i * 7L) / maxOf(picked.size, 1)).toString(), channel.postTime,
                "planned", idea, trend.copy(signals = trend.signals.take(8), headlines = trend.headlines.take(6)))
        }
    }

    companion object {
        const val WORDS_PER_SECOND = 2.5
        const val VERIFY = "Check names, dates and numbers against the sources before posting."

        fun signalsBlock(t: Trend): String {
            val lines = t.signals.mapIndexed { i, s ->
                val metric = if (s.metric > 0 && s.metricLabel.isNotBlank()) " %,d %s".format(s.metric, s.metricLabel) else ""
                val snippet = if (s.snippet.isNotBlank()) " - ${s.snippet.take(240)}" else ""
                "${i + 1}. [${s.publisher.ifBlank { s.source }}$metric] ${s.title}$snippet"
            }
            return lines.ifEmpty { (t.headlines.ifEmpty { listOf(t.title) }).mapIndexed { i, h -> "${i + 1}. $h" } }.joinToString("\n")
        }

        fun hashtags(a: JSONArray?): List<String> = strings(a).map { "#" + it.replace(Regex("[^\\p{L}\\p{N}_]"), "") }
            .filter { it.length > 1 }.distinctBy { it.lowercase() }.take(12)

        private val ABBREV = Regex("(?:\\b(?:Mr|Mrs|Ms|Dr|Jr|Sr|St|vs|etc|No|Inc|Ltd)\\.|\\b(?:[A-Z]\\.){2,})$")

        fun sentences(text: String): List<String> {
            val out = mutableListOf<String>()
            for (block in text.split(Regex("\n+"))) {
                var buf = ""
                for (p in block.trim().split(Regex("(?<=[.!?…])\\s+"))) {
                    buf = if (buf.isNotEmpty()) "$buf ${p.trim()}" else p.trim()
                    if (!ABBREV.containsMatchIn(buf)) { out += buf; buf = "" }
                }
                if (buf.isNotEmpty()) out += buf
            }
            return out.map { it.replace(Regex("\\s+"), " ").trim() }.filter { s -> s.any { it.isLetterOrDigit() } }
        }

        /** Same grouping the worker uses in script mode, so the phone's scenes match the rendered video. */
        fun groupSentences(text: String, template: String): List<String> {
            val sents = sentences(text)
            if (sents.isEmpty()) return emptyList()
            val words = sents.sumOf { it.split(" ").size }
            val n = Math.round(words / WORDS_PER_SECOND / (Styles.sceneSeconds[template] ?: 5.0)).toInt().coerceIn(1, minOf(sents.size, 40))
            val target = words.toDouble() / n
            val groups = mutableListOf(mutableListOf<String>())
            var count = 0
            sents.forEachIndexed { i, s ->
                if (groups.last().isNotEmpty() && groups.size < n && (count >= target * groups.size || sents.size - i <= n - groups.size)) groups += mutableListOf<String>()
                groups.last() += s
                count += s.split(" ").size
            }
            return groups.filter { it.isNotEmpty() }.map { it.joinToString(" ") }
        }

        private const val IDEAS_SYSTEM = """You are the strategist for faceless YouTube Shorts, TikTok and long-form channels.
Given a trending topic and the real signals behind it, propose video ideas that ride the trend.
Rules:
- Hooks are at most 12 words and make the viewer need the answer. No lies, no fake quotes.
- Every angle must be supported by the SIGNALS. Do not invent facts, numbers or events.
- For short videos (<= 60s) pick one sharp angle. For long videos pick an angle with depth (story, explainer, timeline, top-list).
- Mix formats: explainer, story, "what nobody tells you", top-N list, myth vs fact, timeline, prediction (clearly labelled opinion).
- why_now: one sentence on why this is worth posting now.
Return JSON only: {"ideas":[{"title":"...","hook":"...","angle":"...","format":"short|long","why_now":"...","seconds":45}]}"""

        private const val SCRIPT_SYSTEM = """You write narration for faceless social videos.
Write a voice-over script about the IDEA using ONLY facts found in the numbered SOURCES.
Rules:
- Plain spoken English, no stage directions, no emojis, no headings, no scene labels.
- RETENTION: second 1 is the hook (curiosity gap, bold claim or tension) - never a greeting or "in this video".
- Short spoken sentences, mostly under 12 words. Open loops: tease what's coming, escalate every 2-3 sentences, payoff at the end.
- Every sentence names something the viewer can SEE, so it can be illustrated.
- 60 seconds or less: end with a LOOP - the last line flows straight back into the first line so the replay is seamless; no
  "like and subscribe" at the end. Longer videos: last sentence is a short call to action.
- If a detail is not in the SOURCES, do not state it as fact. You may give clearly labelled opinion ("I think", "it might").
- Never invent quotes, statistics, dates or names.
- Hit the target word count.
Return JSON only: {"title":"...","script":"...","description":"one-paragraph video description","hashtags":["#..."],"facts_used":[1,2]}"""

        private const val CHAT_SYSTEM = """You are the AI Director of CreatorForge, a studio for faceless YouTube Shorts, TikTok and YouTube videos.
Talk with the creator like a sharp, friendly producer. Help them turn a rough thought into a video that will perform.
Each turn:
- Answer in 1-4 short sentences. Ask at most ONE question, only when it really matters.
- Keep a DRAFT of the video up to date. Fill in sensible defaults yourself; don't make the creator choose everything.
- If the creator asks for a script, write the full narration in draft.script (spoken words only). Scripts must hold attention:
  hook in second 1 (never a greeting), short visual sentences, open loops with a payoff at the end; videos of 60s or less end with
  a line that loops back into the first line (no "like and subscribe").
- If they ask for ideas, list them in your reply and put the best one in the draft.
- Never invent facts presented as news. For real events, keep claims general or ask the creator for sources.
- Set ready=true once the draft is good enough to produce.
Templates: shorts_cinematic, reels_punchy (9:16 shorts), square_social (1:1), explainer, youtube_longform (16:9 long).
Styles: cinematic, hyperreal, documentary, animated_3d, anime, claymation, watercolor, comic.
ai_video: "off" (stills with camera motion, cheapest), "hook" (AI motion on the first scene), "all" (every scene).
Return JSON only:
{"reply":"...","ready":false,"suggestions":["up to 3 short replies the creator might tap"],
"draft":{"title":"...","idea":"one paragraph brief","hook":"...","script":"","duration_s":45,"template":"shorts_cinematic","style":"cinematic","ai_video":"off"}}"""

        private const val SERIES_SYSTEM = """You write episodes of a faceless narrated series. Keep characters, names and facts consistent with the STORY SO FAR.
Open with a one-line recap only if it helps, end on a cliffhanger and "follow for part N+1". Spoken words only, no stage directions.
Return JSON only: {"title":"...","script":"...","summary":"two sentences of what happens, for the next episode's memory"}"""

        private const val SAFETY_SYSTEM = """You review scripts for faceless YouTube/TikTok videos before they're posted. Flag only real risks:
defamation (calling real people criminals), medical or financial advice presented as fact, unverifiable claims stated as certain,
copyrighted lyrics or long quotes, hate or harassment, dangerous instructions, content unsuitable for advertisers.
Return JSON only: {"issues":[{"level":"high|medium|low","issue":"what's wrong, quoting the words","fix":"how to reword"}]} - an empty list if it's fine."""

        private const val INSIGHTS_SYSTEM = """You are a YouTube growth analyst. From the channel's videos and their views, find what works:
topics, title styles, hook patterns, length, Shorts vs long. Be concrete and practical. 3-6 short bullet points, each one an action
("Do more X", "Stop Y"). Return JSON only: {"insights":["..."]}"""

        private const val TRANSLATE_SYSTEM = """You translate voice-over lines for dubbing. Keep the meaning, tone and roughly the same length
so timing still fits. Natural spoken language, not literal. Keep names. One output line per input line, same order.
Return JSON only: {"lines":["..."]}"""

        private const val HOOKS_SYSTEM = """You write opening lines (hooks) for Shorts and TikToks. Each hook is one spoken sentence of 6-16 words
that makes the viewer need to keep watching, and it must fit the script that follows. Use different techniques: question,
shocking fact, bold claim, story start. No lies. Return JSON only: {"hooks":["..."]}"""

        private const val THUMB_SYSTEM = """You write YouTube and Shorts thumbnail text that makes people click without lying.
Each idea: line1 (1-3 words) and optional line2 (1-4 words), all short enough to read on a phone; highlight = the one word to colour.
Use curiosity, contrast, numbers or a bold claim the video actually delivers. No emojis, no hashtags.
Return JSON only: {"ideas":[{"line1":"...","line2":"...","highlight":"..."}]}"""

        private const val SCENES_SYSTEM = """You are a storyboard artist for faceless social videos. Break the video into scenes.
For each scene give the narration (if a SCRIPT is given, copy each numbered part exactly, one per scene) and ONE concrete,
filmable image: subject, setting, action, lighting. The image must literally show what that scene's narration says (its key
subject and action). Keep the same character, place and look across scenes by repeating the same descriptors. Vary shot sizes
(wide, medium, close-up). No on-screen text in images.
Return JSON only: {"scenes":[{"narration":"...","visual":"...","shot":"wide|medium|close-up|aerial|...","camera":"slow push in|pan left|static|...","mood":"...","motion":"what moves in the shot"}]}"""
    }
}

/** Small helper for no-AI hashtags. */
object RadarWords {
    fun tags(title: String): List<String> = TrendRadar.tokens(title).filter { it.length >= 4 }.take(5).map { "#$it" }
}
