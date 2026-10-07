package com.creatorforge.app.production

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okio.source
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

data class Choice(val id: String, val name: String)

data class Capabilities(val templates: List<Choice>, val voices: List<Choice>, val productionReady: Boolean, val problems: List<String>, val aiVideo: Boolean,
                        val styles: List<Choice> = emptyList())

data class StageView(val name: String, val state: String, val done: Int, val total: Int, val error: String?)

data class SceneView(
    val index: Int, val narration: String, val visual: String, val imageState: String, val voiceState: String,
    val clipState: String, val hasImage: Boolean, val error: String?,
    val narrationS: Double? = null, val durationOverride: Double? = null, val transition: String = "", val overlay: String = "",
    val imageSource: String = "", val clipSource: String = "", val voiceSource: String = ""
)

data class ProductionView(
    val id: String, val status: String, val message: String, val error: String?, val progress: Float,
    val title: String, val hook: String, val cta: String, val stages: List<StageView>, val scenes: List<SceneView>,
    val providers: Map<String, String>, val verification: String?
) {
    val terminal get() = status in setOf("READY", "FAILED", "CANCELLED")
    val inReview get() = status == "REVIEW"
}

data class ProductionSummary(val id: String, val title: String, val status: String, val progress: Float, val message: String = "")

data class ProductionRequest(
    val idea: String, val durationS: Int, val aspect: String, val template: String, val voice: String,
    val pacing: String, val style: String, val mood: String, val camera: String,
    val characters: List<Pair<String, String>>, val music: Boolean, val captions: Boolean,
    val aiVideo: Boolean, val review: Boolean, val autoEdit: Boolean, val characterIds: List<String>,
    val script: String = "", val musicAssetId: String = "", val sfx: Boolean = true, val aiVideoScenes: String = "all"
)

data class LibraryVoice(val id: String, val name: String, val provider: String, val voice: String, val speed: Double, val builtin: Boolean)

data class LibraryAsset(val id: String, val kind: String, val name: String, val source: String, val fileUrl: String, val durationS: Double?)

data class LibraryCharacter(val id: String, val name: String, val description: String)

data class LibraryVideo(val id: String, val title: String, val aspect: String, val durationS: Double, val videoPath: String, val thumbnailPath: String)

data class PublishKit(val titles: List<String>, val description: String, val hashtags: List<String>, val pinnedComment: String, val thumbnailText: String) {
    fun asText() = "${titles.firstOrNull().orEmpty()}\n\n$description\n\n${hashtags.joinToString(" ")}"
}

class WorkerException(message: String) : Exception(message)

/** Client for the worker's one-button production API. */
class ProductionClient(baseUrl: String) {
    private val base = baseUrl.trim().trimEnd('/')
    private val client = OkHttpClient.Builder().connectTimeout(10, TimeUnit.SECONDS).readTimeout(60, TimeUnit.SECONDS).build()
    private val download = OkHttpClient.Builder().connectTimeout(10, TimeUnit.SECONDS).readTimeout(300, TimeUnit.SECONDS).build()
    private val json = "application/json".toMediaType()

    private fun call(method: String, path: String, body: JSONObject? = null): String {
        if (base.isBlank()) throw WorkerException("Set your worker URL in Settings first")
        val req = Request.Builder().workerAuth().url("$base$path")
            .method(method, body?.toString()?.toRequestBody(json) ?: if (method == "POST") "{}".toRequestBody(json) else null)
            .build()
        try {
            client.newCall(req).execute().use { r ->
                val text = r.body?.string().orEmpty()
                if (r.code == 401) throw WorkerException("Worker rejected the token - check Settings")
                if (!r.isSuccessful) {
                    val detail = runCatching { JSONObject(text).opt("detail")?.toString() }.getOrNull() ?: text.take(240)
                    throw WorkerException("Worker HTTP ${r.code}: $detail")
                }
                return text
            }
        } catch (e: WorkerException) {
            throw e
        } catch (e: Exception) {
            throw WorkerException("Worker unreachable: ${e.message ?: e.javaClass.simpleName}")
        }
    }

    suspend fun capabilities(): Capabilities = withContext(Dispatchers.IO) {
        val c = JSONObject(call("GET", "/v1/capabilities"))
        val health = JSONObject(call("GET", "/health"))
        val providers = health.optJSONObject("providers") ?: JSONObject()
        val problems = providers.keys().asSequence().mapNotNull { k ->
            providers.optJSONObject(k)?.takeIf { !it.optBoolean("ready") }?.let { "$k: ${it.optString("error")}" }
        }.toList()
        Capabilities(
            choices(c.optJSONArray("templates")), choices(c.optJSONArray("voices")),
            health.optBoolean("production_ready"), problems,
            (0 until (c.optJSONArray("motion")?.length() ?: 0)).any { c.getJSONArray("motion").optString(it) == "ai_video" },
            choices(c.optJSONArray("styles"))
        )
    }

    private fun choices(a: JSONArray?): List<Choice> =
        (0 until (a?.length() ?: 0)).map { i -> a!!.getJSONObject(i).let { Choice(it.getString("id"), it.optString("name", it.getString("id"))) } }

    suspend fun create(r: ProductionRequest): ProductionView = withContext(Dispatchers.IO) {
        val body = JSONObject().put("idea", r.idea).put("duration_s", r.durationS).put("aspect", r.aspect)
            .put("template", r.template).put("voice", r.voice).put("pacing", r.pacing).put("style", r.style)
            .put("mood", r.mood).put("camera", r.camera).put("music", r.music).put("captions", r.captions)
            .put("motion", if (r.aiVideo) "ai_video" else "stills").put("review", r.review).put("ai_video_scenes", r.aiVideoScenes)
            .put("auto_edit", r.autoEdit).put("character_ids", JSONArray(r.characterIds))
            .put("script", r.script).put("music_asset_id", r.musicAssetId).put("sfx", r.sfx)
            .put("characters", JSONArray().apply { r.characters.forEach { (n, d) -> put(JSONObject().put("name", n).put("description", d)) } })
        parse(call("POST", "/v1/productions", body))
    }

    suspend fun get(id: String) = withContext(Dispatchers.IO) { parse(call("GET", "/v1/productions/$id")) }
    suspend fun cancel(id: String) = withContext(Dispatchers.IO) { parse(call("DELETE", "/v1/productions/$id")) }
    suspend fun retry(id: String) = withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions/$id/retry")) }
    suspend fun regenerateScene(id: String, index: Int) =
        withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions/$id/scenes/$index/regenerate")) }
    suspend fun editScene(id: String, index: Int, narration: String, visual: String) = withContext(Dispatchers.IO) {
        parse(call("PATCH", "/v1/productions/$id/scenes/$index", JSONObject().put("narration", narration).put("visual", visual)))
    }
    suspend fun redraw(id: String, scenes: List<Int>) = withContext(Dispatchers.IO) {
        parse(call("POST", "/v1/productions/$id/redraw", JSONObject().put("scenes", JSONArray(scenes))))
    }
    suspend fun approve(id: String) = withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions/$id/approve")) }

    suspend fun list(): List<ProductionSummary> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/productions"))
        (0 until a.length()).map { i ->
            a.getJSONObject(i).let { ProductionSummary(it.getString("id"), it.optString("title"), it.optString("status"), it.optDouble("progress", 0.0).toFloat(), it.optString("message")) }
        }
    }

    suspend fun characters(): List<LibraryCharacter> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/library/characters"))
        (0 until a.length()).map { i -> a.getJSONObject(i).let { LibraryCharacter(it.getString("id"), it.optString("name"), it.optString("description")) } }
    }

    suspend fun saveCharacter(id: String?, name: String, description: String): Unit = withContext(Dispatchers.IO) {
        val body = JSONObject().put("name", name).put("description", description)
        if (id == null) call("POST", "/v1/library/characters", body) else call("PUT", "/v1/library/characters/$id", body)
    }

    suspend fun deleteCharacter(id: String): Unit = withContext(Dispatchers.IO) { call("DELETE", "/v1/library/characters/$id") }

    // ---- voice profiles ----
    suspend fun voices(): List<LibraryVoice> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/library/voices"))
        (0 until a.length()).map { i ->
            a.getJSONObject(i).let {
                LibraryVoice(it.getString("id"), it.optString("name"), it.optString("provider"), it.optString("voice"),
                    it.optDouble("speed", 1.0), it.optBoolean("builtin"))
            }
        }
    }

    suspend fun saveVoice(id: String?, name: String, provider: String, voice: String, speed: Double): Unit = withContext(Dispatchers.IO) {
        val body = JSONObject().put("name", name).put("provider", provider).put("voice", voice).put("speed", speed)
        if (id == null) call("POST", "/v1/library/voices", body) else call("PUT", "/v1/library/voices/$id", body)
    }

    suspend fun deleteVoice(id: String): Unit = withContext(Dispatchers.IO) { call("DELETE", "/v1/library/voices/$id") }

    /** Downloads a short spoken sample of a voice profile as WAV. */
    suspend fun previewVoice(id: String, dest: File): File = withContext(Dispatchers.IO) {
        val req = Request.Builder().workerAuth().url("$base/v1/library/voices/$id/preview")
            .post(JSONObject().toString().toRequestBody(json)).build()
        download.newCall(req).execute().use { r ->
            if (!r.isSuccessful) throw WorkerException("Preview failed (HTTP ${r.code}): ${r.body?.string()?.take(200).orEmpty()}")
            dest.outputStream().use { out -> r.body!!.byteStream().copyTo(out) }
        }
        dest
    }

    // ---- asset library ----
    suspend fun assets(kind: String? = null, generated: Boolean = false): List<LibraryAsset> = withContext(Dispatchers.IO) {
        val q = listOfNotNull(kind?.let { "kind=$it" }, if (generated) "generated=true" else null).joinToString("&")
        val a = JSONArray(call("GET", "/v1/library/assets" + if (q.isBlank()) "" else "?$q"))
        (0 until a.length()).map { i ->
            a.getJSONObject(i).let {
                LibraryAsset(it.getString("id"), it.optString("kind"), it.optString("name"), it.optString("source"),
                    it.optString("file_url"), if (it.has("duration_s")) it.optDouble("duration_s") else null)
            }
        }
    }

    /** Streams a file picked on the phone to the worker's Asset Library. */
    suspend fun uploadAsset(kind: String, name: String, open: () -> java.io.InputStream): Unit = withContext(Dispatchers.IO) {
        if (base.isBlank()) throw WorkerException("Set your worker URL in Settings first")
        val body = object : okhttp3.RequestBody() {
            override fun contentType() = "application/octet-stream".toMediaType()
            override fun writeTo(sink: okio.BufferedSink) { open().use { input -> sink.writeAll(input.source()) } }
        }
        val url = "$base/v1/library/assets?kind=$kind&name=" + java.net.URLEncoder.encode(name, "UTF-8")
        download.newCall(Request.Builder().workerAuth().url(url).post(body).build()).execute().use { r ->
            if (!r.isSuccessful) {
                val text = r.body?.string().orEmpty()
                throw WorkerException(runCatching { JSONObject(text).optString("detail") }.getOrNull()?.ifBlank { null } ?: "Upload failed (HTTP ${r.code})")
            }
        }
    }

    suspend fun deleteAsset(id: String): Unit = withContext(Dispatchers.IO) { call("DELETE", "/v1/library/assets/$id") }
    suspend fun renameAsset(id: String, name: String): Unit = withContext(Dispatchers.IO) {
        call("PATCH", "/v1/library/assets/$id", JSONObject().put("name", name))
    }

    suspend fun useAsset(id: String, index: Int, assetId: String) = withContext(Dispatchers.IO) {
        parse(call("PATCH", "/v1/productions/$id/scenes/$index", JSONObject().put("asset_id", assetId)))
    }

    // ---- production management ----
    suspend fun editTimeline(id: String, body: JSONObject) = withContext(Dispatchers.IO) {
        parse(call("PATCH", "/v1/productions/$id/timeline", body))
    }
    suspend fun renameProduction(id: String, title: String): Unit = withContext(Dispatchers.IO) {
        call("PATCH", "/v1/productions/$id", JSONObject().put("title", title))
    }
    suspend fun deleteProduction(id: String): Unit = withContext(Dispatchers.IO) { call("DELETE", "/v1/productions/$id?purge=true") }

    suspend fun videos(): List<LibraryVideo> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/library/videos"))
        (0 until a.length()).map { i ->
            a.getJSONObject(i).let {
                LibraryVideo(it.getString("id"), it.optString("title"), it.optString("aspect"), it.optDouble("duration_s"),
                    it.optString("video_url"), it.optString("thumbnail_url"))
            }
        }
    }

    /** Downloads a file and only keeps it if it passes [check]. */
    suspend fun fetch(path: String, dest: File, check: (File) -> Boolean): File = withContext(Dispatchers.IO) {
        val tmp = File(dest.parentFile, dest.name + ".part")
        try {
            download.newCall(Request.Builder().workerAuth().url("$base$path").get().build()).execute().use { r ->
                if (!r.isSuccessful) throw WorkerException("Download HTTP ${r.code}")
                val body = r.body ?: throw WorkerException("Empty download")
                tmp.outputStream().use { out -> body.byteStream().copyTo(out) }
            }
            if (!check(tmp)) throw WorkerException("Downloaded file failed verification")
            if (dest.exists()) dest.delete()
            if (!tmp.renameTo(dest)) throw WorkerException("Could not save ${dest.name}")
            dest
        } catch (e: WorkerException) {
            tmp.delete(); throw e
        } catch (e: Exception) {
            tmp.delete(); throw WorkerException("Download failed: ${e.message}")
        }
    }

    suspend fun publishKit(id: String, refresh: Boolean = false): PublishKit = withContext(Dispatchers.IO) {
        val j = JSONObject(call("POST", "/v1/productions/$id/publish-kit?refresh=$refresh"))
        PublishKit(strings(j.optJSONArray("titles")), j.optString("description"), strings(j.optJSONArray("hashtags")),
            j.optString("pinned_comment"), j.optString("thumbnail_text"))
    }

    private fun strings(a: JSONArray?) = (0 until (a?.length() ?: 0)).map { a!!.optString(it) }

    /** Queues a production from a ready-made request body (built on the phone by the studio). */
    suspend fun createJson(body: JSONObject): ProductionView = withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions", body)) }

    private fun parse(raw: String): ProductionView {
        val j = JSONObject(raw)
        val plan = j.optJSONObject("plan")
        val shots = plan?.optJSONArray("scenes")
        val stagesJ = j.optJSONObject("stages") ?: JSONObject()
        val order = listOf("director", "prompts", "images", "review", "narration", "clips", "captions", "music", "assembly", "verify")
        val stages = order.filter { stagesJ.has(it) }.map { n ->
            val s = stagesJ.getJSONObject(n)
            StageView(n, s.optString("state"), s.optInt("done"), s.optInt("total"), s.optString("error").takeIf { it.isNotBlank() && it != "null" })
        }
        val scenesJ = j.optJSONArray("scenes") ?: JSONArray()
        val scenes = (0 until scenesJ.length()).map { i ->
            val s = scenesJ.getJSONObject(i)
            val shot = shots?.optJSONObject(i)
            SceneView(s.optInt("index", i), shot?.optString("narration").orEmpty(), shot?.optString("visual").orEmpty(),
                s.optString("image_state"), s.optString("voice_state"), s.optString("clip_state"),
                s.optString("image").let { it.isNotBlank() && it != "null" },
                s.optString("error").takeIf { it.isNotBlank() && it != "null" },
                if (s.isNull("narration_s") || !s.has("narration_s")) null else s.optDouble("narration_s"),
                if (s.isNull("duration_override") || !s.has("duration_override")) null else s.optDouble("duration_override"),
                shot?.optString("transition").orEmpty(), shot?.optString("overlay").orEmpty(),
                s.optString("image_source"), s.optString("clip_source"), s.optString("voice_source"))
        }
        val prov = j.optJSONObject("providers") ?: JSONObject()
        val v = j.optJSONObject("result")?.optJSONObject("verification")
        return ProductionView(
            j.getString("id"), j.optString("status"), j.optString("message"),
            j.optString("error").takeIf { it.isNotBlank() && it != "null" }, j.optDouble("progress", 0.0).toFloat(),
            j.optString("title").takeIf { it.isNotBlank() && it != "null" }
                ?: plan?.optString("title").orEmpty().ifBlank { j.optJSONObject("spec")?.optString("idea").orEmpty().take(60) },
            plan?.optString("hook").orEmpty(), plan?.optString("cta").orEmpty(), stages, scenes,
            prov.keys().asSequence().associateWith { prov.optString(it) },
            v?.let { "${it.optInt("width")}x${it.optInt("height")} • ${"%.1f".format(it.optDouble("duration_s"))}s • H.264/AAC • decode ${it.optString("decode_check")}" }
        )
    }
}

fun isMp4(f: File): Boolean = f.length() > 10_000 && f.inputStream().use { s ->
    val b = ByteArray(8); s.read(b) == 8 && String(b, 4, 4, Charsets.US_ASCII) == "ftyp"
}

fun isImage(f: File): Boolean = f.length() > 1_000 && f.inputStream().use { s ->
    val b = ByteArray(4); s.read(b) == 4 && ((b[0] == 0x89.toByte() && b[1] == 0x50.toByte()) || (b[0] == 0xFF.toByte() && b[1] == 0xD8.toByte()))
}
