package com.creatorforge.app.studio

import org.json.JSONObject
import java.io.File
import java.security.MessageDigest
import java.time.LocalDate
import java.time.ZoneOffset
import java.util.concurrent.Callable
import java.util.concurrent.Executors

/**
 * Trend Radar, running on the phone: reads free public feeds, groups the signals into topics and ranks them.
 * No worker or pod needed.
 */
class TrendRadar(
    private val cacheDir: File,
    private val youtubeKey: () -> String = { "" },
    private val fetcher: Fetcher = HttpFetcher(),
    private val today: () -> LocalDate = { LocalDate.now(ZoneOffset.UTC) },
) {
    init { cacheDir.mkdirs() }

    fun scan(period: String = "week", niche: String = "all", region: String = "GB", query: String = "", refresh: Boolean = false): TrendScan {
        require(period in PERIODS) { "period must be week, month or year" }
        require(Niches.exists(niche)) { "unknown niche '$niche'" }
        val q = if (niche == "custom") query.trim().replace(Regex("\\s+"), " ").take(80) else ""
        require(niche != "custom" || q.length >= 2) { "Type a keyword first" }
        val file = cacheFile(period, niche, region, q)
        if (!refresh && file.isFile) {
            runCatching { TrendScan.from(JSONObject(file.readText()), cached = true) }.getOrNull()
                ?.takeIf { System.currentTimeMillis() - it.fetchedAt < TTL.getValue(period) }?.let { return it }
        }
        val scan = collect(period, Niches[niche], region, q)
        val tmp = File(file.path + ".tmp")
        tmp.writeText(scan.toJson().toString())
        tmp.renameTo(file)
        return scan
    }

    /** Finds a topic in recent scans (newest first). */
    fun find(id: String): Trend? = cacheDir.listFiles { f -> f.name.endsWith(".json") }.orEmpty().sortedByDescending { it.lastModified() }
        .firstNotNullOfOrNull { f -> runCatching { TrendScan.from(JSONObject(f.readText()), true).items.firstOrNull { it.id == id } }.getOrNull() }

    private fun cacheFile(period: String, niche: String, region: String, q: String) =
        File(cacheDir, "${period}_${niche}_${region}_${if (q.isBlank()) "all" else sha(q.lowercase()).take(8)}.json")

    private fun wanted(niche: Niche, query: String): List<String> {
        val names = mutableListOf("news", "reddit", "hackernews", "youtube")
        if (niche.id == "all" || niche.keywords.isNotEmpty() || query.isNotBlank()) names.add(0, "google_trends")
        if (niche.wikipedia || query.isNotBlank()) names.add(0, "wikipedia")
        return names
    }

    private fun run(name: String, period: String, niche: Niche, region: String, query: String): List<Signal> {
        val d = today()
        return when (name) {
            "wikipedia" -> Sources.wikipedia(fetcher, period, region, d)
            "google_trends" -> Sources.googleTrends(fetcher, period, region)
            "news" -> Sources.news(fetcher, period, niche, region, query)
            "reddit" -> Sources.reddit(fetcher, period, niche, query)
            "hackernews" -> Sources.hackerNews(fetcher, period, niche, query, d)
            else -> Sources.youtube(fetcher, period, niche, region, query, d, youtubeKey())
        }
    }

    private fun collect(period: String, niche: Niche, region: String, query: String): TrendScan {
        val names = wanted(niche, query)
        val pool = Executors.newFixedThreadPool(names.size)
        val status = mutableListOf<SourceStatus>()
        val lists = LinkedHashMap<String, List<Signal>>()
        try {
            val futures = names.associateWith { n -> pool.submit(Callable { run(n, period, niche, region, query) }) }
            for ((n, fut) in futures) {
                val label = Sources.labels.getValue(n)
                val sigs = try { fut.get() } catch (e: Exception) {
                    val cause = e.cause ?: e
                    status += SourceStatus(n, label, false, 0, (cause as? SourceException)?.message ?: "failed: ${cause.javaClass.simpleName}")
                    continue
                }
                val kept = filter(n, sigs, niche, query)
                lists[n] = kept
                status += SourceStatus(n, label, true, kept.size, "")
            }
        } finally {
            pool.shutdown()
        }
        if (lists.values.all { it.isEmpty() }) {
            throw SourceException("No trend source returned anything (" + status.joinToString("; ") { "${it.name}: ${it.error.ifBlank { "nothing found" }}" } + ")")
        }
        val clusters = cluster(lists)
        val top = clusters.maxOfOrNull { it.score() } ?: 0.0
        val items = clusters.sortedByDescending { it.score() }.take(60).map { it.toTrend(top, period) }
        return TrendScan(period, niche.id, region, query, System.currentTimeMillis(), status, items)
    }

    private fun filter(name: String, sigs: List<Signal>, niche: Niche, query: String): List<Signal> {
        if (name !in ENTITY_SOURCES) return sigs
        val words = if (query.isNotBlank()) tokens(query) else niche.keywords.toSet()
        if (words.isEmpty()) return sigs
        return sigs.filter { s -> val t = "${s.title} ${s.snippet}".lowercase(); words.any { w -> Regex("\\b" + Regex.escape(w)).containsMatchIn(t) } }
    }

    internal class Cluster(val anchor: Signal, score: Double) {
        val key = tokens(anchor.title)
        val signals = mutableListOf(anchor to score)

        fun matches(sig: Signal, toks: Set<String>): Boolean {
            if (key.isEmpty() || toks.isEmpty()) return false
            val common = key intersect toks
            if ((key.size == 1 && anchor.source in ENTITY_SOURCES) || (toks.size == 1 && sig.source in ENTITY_SOURCES)) {
                return common.any { it.length >= 4 } // a one-word entity ("Oasis") matches headlines that name it
            }
            return common.size >= 2 && common.size.toDouble() / minOf(key.size, toks.size) >= 0.6
        }

        fun score(): Double {
            val best = HashMap<String, Double>()
            for ((s, v) in signals) best[s.source] = maxOf(best[s.source] ?: 0.0, v)
            // agreement across sources counts a lot, extra mentions in one source a little
            return best.values.sum() + 0.15 * (signals.sumOf { it.second } - best.values.sum())
        }

        fun toTrend(maxScore: Double, period: String): Trend {
            val ordered = signals.sortedByDescending { it.second }
            // Prefer Wikipedia's properly written name; otherwise capitalise lower-case search terms ("comet atlas").
            val wiki = signals.firstOrNull { it.first.source == "wikipedia" }?.first?.title
            val raw = (wiki ?: anchor.title).trim()
            val title = if (raw == raw.lowercase()) raw.split(" ").joinToString(" ") { w -> w.replaceFirstChar { it.uppercase() } } else raw
            val metrics = LinkedHashMap<String, Long>()
            for ((s, _) in signals) if (s.metric > 0 && s.metricLabel.isNotBlank()) metrics[s.metricLabel] = (metrics[s.metricLabel] ?: 0) + s.metric
            val score = score()
            return Trend(sha(title.lowercase()).take(12), title, if (maxScore > 0) Math.round(100 * score / maxScore).toInt() else 0,
                Math.round(score * 1000) / 1000.0,
                signals.map { it.first.source }.distinct().sortedByDescending { Sources.weights[it] ?: 0.0 }.map { Sources.labels.getValue(it) },
                metrics, ordered.map { it.first.title }.filter { it != title }.distinct().take(6), ordered.take(10).map { it.first }, period == "year")
        }
    }

    companion object {
        val PERIODS = listOf("week", "month", "year")
        private val TTL = mapOf("week" to 2 * 3600_000L, "month" to 12 * 3600_000L, "year" to 48 * 3600_000L)
        private val ENTITY_SOURCES = setOf("google_trends", "wikipedia")
        private val STOP = ("a an the and or but of to in on at for from by with without into over under about after before is are was were be been " +
            "being has have had do does did will would can could should may might must this that these those it its i you he she they we them his her " +
            "their our your my me us not no yes so as if than then there here what which who whom whose when where why how all any each more most other " +
            "some such only own same too very just new says say said vs via amid up out off one two three first last year years week weeks month months " +
            "day days today now 2024 2025 2026 2027 get got make makes made video watch people man woman").split(" ").toSet()

        fun tokens(title: String): Set<String> = Regex("[a-z0-9]+").findAll(title.lowercase().replace("'s", "")).map { it.value }
            .filter { it !in STOP && (it.length >= 3 || it in setOf("ai", "uk", "us", "f1")) }
            .map { if (it.length > 4 && it.endsWith("s") && !it.endsWith("ss")) it.dropLast(1) else it }.toSet()

        internal fun cluster(lists: Map<String, List<Signal>>): List<Cluster> {
            val scored = lists.flatMap { (name, sigs) ->
                val n = maxOf(sigs.size, 1)
                sigs.mapIndexed { rank, s -> s to (Sources.weights[name] ?: 0.5) * (1 - 0.8 * rank / n) }
            }.sortedWith(compareBy<Pair<Signal, Double>>({ it.first.source !in ENTITY_SOURCES }, { -it.second }))
            val clusters = mutableListOf<Cluster>()
            for ((s, v) in scored) {
                val toks = tokens(s.title)
                val home = clusters.firstOrNull { it.matches(s, toks) }
                if (home != null) home.signals += s to v else if (toks.isNotEmpty()) clusters += Cluster(s, v)
            }
            return clusters
        }

        fun sha(s: String): String = MessageDigest.getInstance("SHA-1").digest(s.toByteArray()).joinToString("") { "%02x".format(it) }
    }
}
