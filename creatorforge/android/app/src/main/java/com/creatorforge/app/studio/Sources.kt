package com.creatorforge.app.studio

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.net.URLEncoder
import java.time.LocalDate
import java.time.ZoneOffset
import java.util.concurrent.TimeUnit

class SourceException(message: String) : Exception(message)

/** Fetches a URL and returns (HTTP status, body). Swappable for tests. */
fun interface Fetcher {
    fun get(url: String): Pair<Int, String>
}

class HttpFetcher : HeaderFetcher {
    private val client = OkHttpClient.Builder().connectTimeout(12, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).build()
    override fun get(url: String): Pair<Int, String> = get(url, emptyMap())
    override fun get(url: String, headers: Map<String, String>): Pair<Int, String> = try {
        val b = Request.Builder().url(url).header("User-Agent", USER_AGENT).header("Accept", "*/*")
        headers.forEach { (k, v) -> b.header(k, v) }
        client.newCall(b.build()).execute().use { r -> r.code to (r.body?.string().orEmpty()) }
    } catch (e: Exception) {
        throw SourceException("unreachable: ${e.message ?: e.javaClass.simpleName}")
    }

    /** Raw bytes (for downloading stock photos). */
    fun bytes(url: String): ByteArray = try {
        client.newCall(Request.Builder().url(url).header("User-Agent", USER_AGENT).build()).execute().use { r ->
            if (!r.isSuccessful) throw SourceException("download failed (HTTP ${r.code})")
            r.body?.bytes() ?: ByteArray(0)
        }
    } catch (e: SourceException) { throw e } catch (e: Exception) { throw SourceException("download failed: ${e.message}") }

    companion object {
        const val USER_AGENT = "CreatorForge-TrendRadar/1.0 (Android; +https://github.com/diljotsinghdj-creator/Forgeos)"
    }
}

/** The free public feeds the Trend Radar reads. */
object Sources {
    val labels = linkedMapOf("wikipedia" to "Wikipedia", "google_trends" to "Google Trends", "news" to "News", "reddit" to "Reddit",
        "hackernews" to "Hacker News", "youtube" to "YouTube")
    val weights = mapOf("google_trends" to 1.2, "youtube" to 1.2, "wikipedia" to 1.0, "reddit" to 0.9, "news" to 0.8, "hackernews" to 0.7)
    val days = mapOf("week" to 7, "month" to 30, "year" to 365)

    private fun enc(s: String) = URLEncoder.encode(s, "UTF-8").replace("+", "%20")

    private fun json(f: Fetcher, url: String): JSONObject {
        val (code, body) = f.get(url)
        if (code >= 400 && "googleapis.com/youtube" in url) throw SourceException(YouTubeStats.explain(code, body))
        if (code >= 400) throw SourceException("HTTP $code")
        return try { JSONObject(body) } catch (e: Exception) { throw SourceException("unexpected response (not JSON)") }
    }

    private fun xml(f: Fetcher, url: String): String {
        val (code, body) = f.get(url)
        if (code >= 400) throw SourceException("HTTP $code")
        if ("<rss" !in body && "<feed" !in body && "<item" !in body) throw SourceException("unexpected response (not RSS)")
        return body
    }

    // ---- tiny RSS reader (feeds are simple; avoids platform XML parsers so this runs anywhere) ----
    internal fun items(xml: String): List<String> = Regex("<item\\b[^>]*>([\\s\\S]*?)</item>").findAll(xml).map { it.groupValues[1] }.toList()

    internal fun tag(block: String, name: String): String {
        val m = Regex("<(?:[\\w-]+:)?$name\\b[^>]*>([\\s\\S]*?)</(?:[\\w-]+:)?$name>").find(block) ?: return ""
        return unescape(m.groupValues[1].replace(Regex("^\\s*<!\\[CDATA\\[|]]>\\s*$"), "")).trim()
    }

    internal fun unescape(s: String): String = s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"")
        .replace("&#39;", "'").replace("&apos;", "'").replace("&nbsp;", " ")
        .replace(Regex("&#(\\d+);")) { it.groupValues[1].toIntOrNull()?.let { c -> String(Character.toChars(c)) } ?: "" }
        .replace("&amp;", "&")

    private fun count(s: String) = s.filter { it.isDigit() }.toLongOrNull() ?: 0L

    private val wikiSkip = Regex("^(Main_Page|Special:|Wikipedia:|File:|Portal:|Help:|Category:|Template:|Talk:|User:|Search|-$|XXX|Pornhub|XHamster|Xvideos)", RegexOption.IGNORE_CASE)

    fun wikipedia(f: Fetcher, period: String, region: String, today: LocalDate): List<Signal> {
        val base = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/${Regions[region].wiki}/all-access"
        val urls = if (period == "week") (0 until 7).map { today.minusDays(2L + it) }.map { d -> "%s/%04d/%02d/%02d".format(base, d.year, d.monthValue, d.dayOfMonth) }
        else {
            var first = today.withDayOfMonth(1)
            (0 until if (period == "month") 1 else 12).map { first = first.minusMonths(1); "%s/%04d/%02d/all-days".format(base, first.year, first.monthValue) }
        }
        val views = HashMap<String, Long>()
        var errors = 0
        for (u in urls) {
            val data = try { json(f, u) } catch (e: SourceException) { errors++; continue }
            val items = data.optJSONArray("items") ?: continue
            for (i in 0 until items.length()) {
                val arts = items.getJSONObject(i).optJSONArray("articles") ?: continue
                for (k in 0 until arts.length()) {
                    val a = arts.getJSONObject(k)
                    val name = a.optString("article")
                    if (name.isNotBlank() && !wikiSkip.containsMatchIn(name)) views[name] = (views[name] ?: 0) + a.optLong("views")
                }
            }
        }
        if (errors == urls.size) throw SourceException("Wikipedia pageviews unavailable")
        return views.entries.sortedByDescending { it.value }.take(60).map { (n, v) ->
            Signal("wikipedia", n.replace('_', ' '), "https://en.wikipedia.org/wiki/" + enc(n), v, "page views")
        }
    }

    fun googleTrends(f: Fetcher, period: String, region: String): List<Signal> {
        if (period != "week") return emptyList() // the public feed only covers the last few days
        return items(xml(f, "https://trends.google.com/trending/rss?geo=$region")).mapNotNull { b ->
            val title = tag(b, "title").ifBlank { return@mapNotNull null }
            val news = Regex("<(?:[\\w-]+:)?news_item\\b[^>]*>([\\s\\S]*?)</(?:[\\w-]+:)?news_item>").find(b)?.groupValues?.get(1).orEmpty()
            Signal("google_trends", title, tag(news, "news_item_url"), count(tag(b, "approx_traffic")), "searches",
                tag(news, "news_item_source"), tag(news, "news_item_title"))
        }
    }

    fun news(f: Fetcher, period: String, niche: Niche, region: String, query: String): List<Signal> {
        val r = Regions[region]
        val q = query.ifBlank { niche.newsQuery }
        val tail = "hl=${r.hl}&gl=${r.id}&ceid=${r.ceid}"
        val url = when {
            q.isNotBlank() -> "https://news.google.com/rss/search?q=${enc("$q when:${days.getValue(period)}d")}&$tail"
            period == "week" -> "https://news.google.com/rss?$tail"
            else -> return emptyList() // top stories are only "now"; month/year need a topic
        }
        return items(xml(f, url)).mapNotNull { b ->
            var title = tag(b, "title")
            val publisher = tag(b, "source")
            if (publisher.isNotBlank() && title.endsWith(" - $publisher")) title = title.dropLast(publisher.length + 3)
            if (title.isBlank()) null else Signal("news", title, tag(b, "link"), 0, "", publisher)
        }.take(60)
    }

    fun reddit(f: Fetcher, period: String, niche: Niche, query: String): List<Signal> {
        val url = when {
            query.isNotBlank() -> "https://www.reddit.com/search.json?q=${enc(query)}&sort=top&t=$period&limit=50"
            niche.subreddits.isNotEmpty() -> "https://www.reddit.com/r/${niche.subreddits.joinToString("+")}/top.json?t=$period&limit=60"
            else -> return emptyList()
        }
        val children = json(f, url).optJSONObject("data")?.optJSONArray("children") ?: return emptyList()
        return (0 until children.length()).mapNotNull { i ->
            val d = children.getJSONObject(i).optJSONObject("data") ?: return@mapNotNull null
            if (d.optBoolean("stickied") || d.optBoolean("over_18")) return@mapNotNull null
            val title = unescape(d.optString("title")).trim().replace(Regex("^(TIL that|TIL:|TIL)\\s+", RegexOption.IGNORE_CASE), "")
            if (title.isBlank()) null else Signal("reddit", title, "https://www.reddit.com" + d.optString("permalink"), d.optLong("score"), "upvotes",
                "r/" + d.optString("subreddit"), d.optString("selftext").take(280))
        }
    }

    fun hackerNews(f: Fetcher, period: String, niche: Niche, query: String, today: LocalDate): List<Signal> {
        val q = if (query.isNotBlank()) query else niche.hnQuery ?: return emptyList()
        val since = today.minusDays(days.getValue(period).toLong()).atStartOfDay().toEpochSecond(ZoneOffset.UTC)
        val hits = json(f, "https://hn.algolia.com/api/v1/search?query=${enc(q)}&tags=story&numericFilters=created_at_i>$since,points>30&hitsPerPage=60")
            .optJSONArray("hits") ?: return emptyList()
        return (0 until hits.length()).map { hits.getJSONObject(it) }.filter { it.optString("title").isNotBlank() }
            .sortedByDescending { it.optLong("points") }.take(40).map { h ->
                Signal("hackernews", h.optString("title").trim(), h.optString("url").ifBlank { "https://news.ycombinator.com/item?id=" + h.optString("objectID") },
                    h.optLong("points"), "points", "Hacker News")
            }
    }

    fun youtube(f: Fetcher, period: String, niche: Niche, region: String, query: String, today: LocalDate, key: String): List<Signal> {
        if (key.isBlank()) throw SourceException("add a free YouTube Data API key in Settings to include YouTube")
        val api = "https://www.googleapis.com/youtube/v3"
        val q = query.ifBlank { niche.youtubeQuery }
        val items = if (period == "week" && query.isBlank()) {
            var url = "$api/videos?part=snippet,statistics&chart=mostPopular&regionCode=$region&maxResults=50&key=$key"
            if (niche.youtubeCategory.isNotBlank()) url += "&videoCategoryId=${niche.youtubeCategory}"
            json(f, url).optJSONArray("items")
        } else {
            if (q.isBlank()) return emptyList()
            val after = today.minusDays(days.getValue(period).toLong()).toString() + "T00:00:00Z"
            val found = json(f, "$api/search?part=snippet&type=video&order=viewCount&maxResults=25&regionCode=$region&publishedAfter=$after&q=${enc(q)}&key=$key")
                .optJSONArray("items")
            val ids = (0 until (found?.length() ?: 0)).mapNotNull { found!!.getJSONObject(it).optJSONObject("id")?.optString("videoId")?.takeIf { v -> v.isNotBlank() } }
            if (ids.isEmpty()) return emptyList()
            json(f, "$api/videos?part=snippet,statistics&id=${ids.joinToString(",")}&key=$key").optJSONArray("items")
        } ?: return emptyList()
        return (0 until items.length()).mapNotNull { i ->
            val it = items.getJSONObject(i)
            val sn = it.optJSONObject("snippet") ?: return@mapNotNull null
            val title = unescape(sn.optString("title")).trim()
            if (title.isBlank()) null else Signal("youtube", title, "https://www.youtube.com/watch?v=" + it.optString("id"),
                it.optJSONObject("statistics")?.optString("viewCount")?.toLongOrNull() ?: 0, "views", sn.optString("channelTitle"),
                sn.optString("description").take(280))
        }.sortedByDescending { it.metric }
    }
}
