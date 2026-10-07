package com.creatorforge.app.studio

import org.json.JSONObject
import java.net.URLEncoder

/** Free stock photos for phone-made videos: Pexels (free key) or Pixabay (free key). Returns image URLs. */
object StockPhotos {
    data class Photo(val url: String, val credit: String)

    /** The 2-3 most telling words of a line, used as the search. */
    fun query(line: String): String = TrendRadar.tokens(line).sortedByDescending { it.length }.take(3).joinToString(" ").ifBlank { line.take(40) }

    private fun enc(s: String) = URLEncoder.encode(s, "UTF-8")

    fun pexels(f: Fetcher, key: String, q: String, orientation: String): List<Photo> {
        val (code, body) = (f as? HeaderFetcher)?.get("https://api.pexels.com/v1/search?query=${enc(q)}&per_page=5&orientation=$orientation", mapOf("Authorization" to key))
            ?: f.get("https://api.pexels.com/v1/search?query=${enc(q)}&per_page=5&orientation=$orientation")
        if (code >= 400) throw SourceException("Pexels said HTTP $code - check the key")
        val photos = JSONObject(body).optJSONArray("photos") ?: return emptyList()
        return (0 until photos.length()).mapNotNull { i ->
            val p = photos.getJSONObject(i)
            val src = p.optJSONObject("src") ?: return@mapNotNull null
            val url = src.optString(if (orientation == "portrait") "portrait" else "large2x").ifBlank { src.optString("large") }
            if (url.isBlank()) null else Photo(url, "Photo: ${p.optString("photographer")} / Pexels")
        }
    }

    fun pixabay(f: Fetcher, key: String, q: String, orientation: String): List<Photo> {
        val o = if (orientation == "portrait") "vertical" else "horizontal"
        val (code, body) = f.get("https://pixabay.com/api/?key=${enc(key)}&q=${enc(q)}&image_type=photo&orientation=$o&safesearch=true&per_page=5")
        if (code >= 400) throw SourceException("Pixabay said HTTP $code - check the key")
        val hits = JSONObject(body).optJSONArray("hits") ?: return emptyList()
        return (0 until hits.length()).mapNotNull { i ->
            val h = hits.getJSONObject(i)
            h.optString("largeImageURL").takeIf { it.isNotBlank() }?.let { Photo(it, "Photo: ${h.optString("user")} / Pixabay") }
        }
    }

    /** "pexels:KEY" or "pixabay:KEY" (a bare key is treated as Pexels). */
    fun search(f: Fetcher, setting: String, line: String, orientation: String): List<Photo> {
        val (provider, key) = if (':' in setting) setting.substringBefore(':') to setting.substringAfter(':') else "pexels" to setting
        if (key.isBlank()) return emptyList()
        val q = query(line)
        return if (provider == "pixabay") pixabay(f, key, q, orientation) else pexels(f, key, q, orientation)
    }
}

/** A fetcher that can send headers (Pexels wants the key in a header). */
interface HeaderFetcher : Fetcher {
    fun get(url: String, headers: Map<String, String>): Pair<Int, String>
}
