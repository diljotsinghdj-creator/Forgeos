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

data class ProductionSummary(val id: String, val title: String, val status: String, val progress: Float, val message: String = "",
                             val variantOf: String = "", val hookGroup: String = "", val hookVariant: String = "", val language: String = "",
                             val cancelling: Boolean = false)

data class ClipItem(val index: Int, val title: String, val hook: String, val start: Double, val end: Double, val durationS: Double)
data class ClipJob(val id: String, val status: String, val message: String, val error: String, val title: String, val clips: List<ClipItem>)
data class ReviewItem(val id: String, val title: String, val path: String, val status: String, val comments: List<Pair<String, String>>)
data class Account(val id: String, val name: String, val role: String, val credits: Int, val used: Int, val key: String = "")

data class ProductionRequest(
    val idea: String, val durationS: Int, val aspect: String, val template: String, val voice: String,
    val pacing: String, val style: String, val mood: String, val camera: String,
    val characters: List<Pair<String, String>>, val music: Boolean, val captions: Boolean,
    val aiVideo: Boolean, val review: Boolean, val autoEdit: Boolean, val characterIds: List<String>,
    val script: String = "", val musicAssetId: String = "", val sfx: Boolean = true, val aiVideoScenes: String = "all",
    val videoQuality: String = "fast", val faces: String = "show", val fastCuts: Boolean = true,
    val voiceSpeed: Double = 1.1
)

data class LibraryVoice(val id: String, val name: String, val provider: String, val voice: String, val speed: Double, val builtin: Boolean,
                        val style: String = "")

data class LibraryAsset(val id: String, val kind: String, val name: String, val source: String, val fileUrl: String, val durationS: Double?)

data class LibraryCharacter(val id: String, val name: String, val description: String)

data class LibraryVideo(val id: String, val title: String, val aspect: String, val durationS: Double, val videoPath: String, val thumbnailPath: String)

data class PublishKit(val titles: List<String>, val description: String, val hashtags: List<String>, val pinnedComment: String, val thumbnailText: String) {
    fun asText() = "${titles.firstOrNull().orEmpty()}\n\n$description\n\n${hashtags.joinToString(" ")}"
}

class WorkerException(message: String) : Exception(message)

const val WARMING_UP = "Your pod is on but CreatorForge isn't answering yet - it may still be setting up (about 10-15 min after a start). Try again shortly."
const val UNREACHABLE = "Can't reach your pod - is it running? (Settings → Pod Power, or RunPod → Start)"

/** Client for the worker's one-button production API. */
class ProductionClient(baseUrl: String) {
    companion object {
        /** Supplies the app's Script AI for planning (set once at startup). */
        @Volatile var directorLlm: (() -> JSONObject?)? = null
        /** Supplies the Pexels/Pixabay key so the pod can use real stock footage. */
        @Volatile var stockKey: (() -> JSONObject?)? = null
    }

    private val base = baseUrl.trim().trimEnd('/')
    private val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(90, TimeUnit.SECONDS).retryOnConnectionFailure(true).build()
    private val download = OkHttpClient.Builder().connectTimeout(10, TimeUnit.SECONDS).readTimeout(300, TimeUnit.SECONDS).build()
    private val json = "application/json".toMediaType()

    private fun call(method: String, path: String, body: JSONObject? = null): String {
        if (base.isBlank()) throw WorkerException("Not connected to your pod - start it and tap Settings → SCAN QR (writing tools work without it)")
        // RunPod's proxy drops or 502s requests now and then (weak signal, pod busy loading a model). Reads are
        // retried quietly; writes only when the request never reached the pod, so nothing is created twice.
        var last: WorkerException? = null
        for (attempt in 0 until 3) {
            if (attempt > 0) Thread.sleep(1500L * attempt)
            val req = Request.Builder().workerAuth().url("$base$path")
                .method(method, body?.toString()?.toRequestBody(json) ?: if (method == "POST") "{}".toRequestBody(json) else null)
                .build()
            try {
                client.newCall(req).execute().use { r ->
                    val text = r.body?.string().orEmpty()
                    if (r.code == 401) throw WorkerException("Worker rejected the token - check Settings (scan the pod's QR again)")
                    if (r.code in 502..504) {
                        last = WorkerException(WARMING_UP)
                        if (method == "GET") return@use null else throw last!!
                    }
                    if (!r.isSuccessful) {
                        val detail = runCatching { JSONObject(text).opt("detail")?.toString() }.getOrNull() ?: text.take(240)
                        throw WorkerException("Worker HTTP ${r.code}: $detail")
                    }
                    text
                }?.let { return it }
            } catch (e: WorkerException) {
                throw e
            } catch (e: java.net.ConnectException) {
                last = WorkerException(UNREACHABLE)
            } catch (e: java.net.UnknownHostException) {
                last = WorkerException("No internet connection (or the pod address is wrong)")
            } catch (e: Exception) {
                last = WorkerException("Connection to your pod dropped (${e.message ?: e.javaClass.simpleName}) - try again")
                if (method != "GET") throw last!!
            }
        }
        throw last ?: WorkerException(UNREACHABLE)
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
            .put("video_quality", r.videoQuality).put("faces", r.faces).put("fast_cuts", r.fastCuts).put("voice_speed", r.voiceSpeed).put("auto_edit", r.autoEdit).put("character_ids", JSONArray(r.characterIds))
            .put("script", r.script).put("music_asset_id", r.musicAssetId).put("sfx", r.sfx)
            .put("characters", JSONArray().apply { r.characters.forEach { (n, d) -> put(JSONObject().put("name", n).put("description", d)) } })
        parse(call("POST", "/v1/productions", withDirector(body)))
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
            a.getJSONObject(i).let {
                val ht = it.optJSONObject("hook_test")
                ProductionSummary(it.getString("id"), it.optString("title"), it.optString("status"), it.optDouble("progress", 0.0).toFloat(), it.optString("message"),
                    it.optString("variant_of").takeIf { v -> v != "null" }.orEmpty(), ht?.optString("group").orEmpty(), ht?.optString("variant").orEmpty(),
                    it.optString("language").takeIf { v -> v != "null" }.orEmpty(), it.optBoolean("cancelling"))
            }
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
                    it.optDouble("speed", 1.0), it.optBoolean("builtin"), it.optString("style"))
            }
        }
    }

    suspend fun saveVoice(id: String?, name: String, provider: String, voice: String, speed: Double, style: String = ""): Unit = withContext(Dispatchers.IO) {
        val body = JSONObject().put("name", name).put("provider", provider).put("voice", voice).put("speed", speed).put("style", style)
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
    suspend fun uploadAsset(kind: String, name: String, open: () -> java.io.InputStream): String = withContext(Dispatchers.IO) {
        if (base.isBlank()) throw WorkerException("Not connected to your pod - start it and tap Settings → SCAN QR (writing tools work without it)")
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
            runCatching { JSONObject(r.body?.string().orEmpty()).optString("id") }.getOrDefault("")
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

    // ---- dubbing, Hook Lab, Shorts Clipper ----
    suspend fun dub(id: String, language: String, voice: String, narrations: List<String>): ProductionView = withContext(Dispatchers.IO) {
        parse(call("POST", "/v1/productions/$id/dub", JSONObject().put("language", language).put("voice", voice).put("narrations", JSONArray(narrations))))
    }

    suspend fun hookVariants(id: String, hooks: List<String>): Int = withContext(Dispatchers.IO) {
        JSONObject(call("POST", "/v1/productions/$id/hook-variants", JSONObject().put("hooks", JSONArray(hooks)))).optJSONArray("productions")?.length() ?: 0
    }

    private fun parseClipJob(j: JSONObject): ClipJob {
        val a = j.optJSONArray("clips") ?: JSONArray()
        return ClipJob(j.getString("id"), j.optString("status"), j.optString("message"), j.optString("error").takeIf { it != "null" }.orEmpty(),
            j.optJSONObject("source")?.optString("title").orEmpty(),
            (0 until a.length()).map { a.getJSONObject(it).let { c -> ClipItem(c.optInt("index"), c.optString("title"), c.optString("hook"),
                c.optDouble("start"), c.optDouble("end"), c.optDouble("duration_s")) } })
    }

    suspend fun createClips(productionId: String?, assetId: String?, count: Int, seconds: Int, brand: JSONObject?): ClipJob = withContext(Dispatchers.IO) {
        val body = JSONObject().put("count", count).put("seconds", seconds)
        productionId?.let { body.put("production_id", it) }; assetId?.let { body.put("asset_id", it) }; brand?.let { body.put("brand", it) }
        parseClipJob(JSONObject(call("POST", "/v1/clips", body)))
    }
    suspend fun clipJob(id: String): ClipJob = withContext(Dispatchers.IO) { parseClipJob(JSONObject(call("GET", "/v1/clips/$id"))) }
    suspend fun clipJobs(): List<ClipJob> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/clips")); (0 until a.length()).map { parseClipJob(a.getJSONObject(it)) }
    }

    // ---- team & accounts ----
    suspend fun reviewLink(id: String): String = withContext(Dispatchers.IO) { base + JSONObject(call("POST", "/v1/productions/$id/review-link")).getString("path") }
    suspend fun reviews(): List<ReviewItem> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/reviews"))
        (0 until a.length()).map { a.getJSONObject(it).let { r ->
            val c = r.optJSONArray("comments") ?: JSONArray()
            ReviewItem(r.getString("id"), r.optString("title"), base + r.optString("path"), r.optString("status"),
                (0 until c.length()).map { i -> c.getJSONObject(i).let { x -> x.optString("decision") to x.optString("comment") } })
        } }
    }
    private fun parseAccount(j: JSONObject) = Account(j.getString("id"), j.optString("name"), j.optString("role"), j.optInt("credits"), j.optInt("used"), j.optString("key"))
    suspend fun me(): JSONObject = withContext(Dispatchers.IO) { JSONObject(call("GET", "/v1/me")) }
    suspend fun accounts(): List<Account> = withContext(Dispatchers.IO) { JSONArray(call("GET", "/v1/accounts")).let { a -> (0 until a.length()).map { parseAccount(a.getJSONObject(it)) } } }
    suspend fun createAccount(name: String, role: String, credits: Int): Account = withContext(Dispatchers.IO) {
        parseAccount(JSONObject(call("POST", "/v1/accounts", JSONObject().put("name", name).put("role", role).put("credits", credits))))
    }
    suspend fun addCredits(id: String, n: Int): Account = withContext(Dispatchers.IO) { parseAccount(JSONObject(call("PATCH", "/v1/accounts/$id", JSONObject().put("add_credits", n)))) }
    suspend fun deleteAccount(id: String): Unit = withContext(Dispatchers.IO) { call("DELETE", "/v1/accounts/$id") }

    /** Queues a production from a ready-made request body (built on the phone by the studio). */
    suspend fun createJson(body: JSONObject): ProductionView = withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions", withDirector(body))) }

    private fun withDirector(body: JSONObject): JSONObject {
        directorLlm?.invoke()?.let { if (!body.has("director_llm")) body.put("director_llm", it) }
        stockKey?.invoke()?.let { if (!body.has("stock")) body.put("stock", it) }
        return body
    }

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
