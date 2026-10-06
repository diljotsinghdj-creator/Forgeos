package com.creatorforge.app.production

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

data class Choice(val id: String, val name: String)

data class Capabilities(val templates: List<Choice>, val voices: List<Choice>, val productionReady: Boolean, val problems: List<String>)

data class StageView(val name: String, val state: String, val done: Int, val total: Int, val error: String?)

data class SceneView(val index: Int, val narration: String, val imageState: String, val voiceState: String, val hasImage: Boolean, val error: String?)

data class ProductionView(
    val id: String, val status: String, val message: String, val error: String?, val progress: Float,
    val title: String, val hook: String, val stages: List<StageView>, val scenes: List<SceneView>,
    val providers: Map<String, String>, val verification: String?
) {
    val terminal get() = status in setOf("READY", "FAILED", "CANCELLED")
}

data class ProductionSummary(val id: String, val title: String, val status: String, val progress: Float)

data class ProductionRequest(
    val idea: String, val durationS: Int, val aspect: String, val template: String, val voice: String,
    val pacing: String, val style: String, val mood: String, val camera: String,
    val characters: List<Pair<String, String>>, val music: Boolean, val captions: Boolean
)

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
            health.optBoolean("production_ready"), problems
        )
    }

    private fun choices(a: JSONArray?): List<Choice> =
        (0 until (a?.length() ?: 0)).map { i -> a!!.getJSONObject(i).let { Choice(it.getString("id"), it.optString("name", it.getString("id"))) } }

    suspend fun create(r: ProductionRequest): ProductionView = withContext(Dispatchers.IO) {
        val body = JSONObject().put("idea", r.idea).put("duration_s", r.durationS).put("aspect", r.aspect)
            .put("template", r.template).put("voice", r.voice).put("pacing", r.pacing).put("style", r.style)
            .put("mood", r.mood).put("camera", r.camera).put("music", r.music).put("captions", r.captions)
            .put("characters", JSONArray().apply { r.characters.forEach { (n, d) -> put(JSONObject().put("name", n).put("description", d)) } })
        parse(call("POST", "/v1/productions", body))
    }

    suspend fun get(id: String) = withContext(Dispatchers.IO) { parse(call("GET", "/v1/productions/$id")) }
    suspend fun cancel(id: String) = withContext(Dispatchers.IO) { parse(call("DELETE", "/v1/productions/$id")) }
    suspend fun retry(id: String) = withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions/$id/retry")) }
    suspend fun regenerateScene(id: String, index: Int) =
        withContext(Dispatchers.IO) { parse(call("POST", "/v1/productions/$id/scenes/$index/regenerate")) }

    suspend fun list(): List<ProductionSummary> = withContext(Dispatchers.IO) {
        val a = JSONArray(call("GET", "/v1/productions"))
        (0 until a.length()).map { i ->
            a.getJSONObject(i).let { ProductionSummary(it.getString("id"), it.optString("title"), it.optString("status"), it.optDouble("progress", 0.0).toFloat()) }
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

    private fun parse(raw: String): ProductionView {
        val j = JSONObject(raw)
        val plan = j.optJSONObject("plan")
        val shots = plan?.optJSONArray("scenes")
        val stagesJ = j.optJSONObject("stages") ?: JSONObject()
        val order = listOf("director", "prompts", "images", "narration", "captions", "music", "assembly", "verify")
        val stages = order.filter { stagesJ.has(it) }.map { n ->
            val s = stagesJ.getJSONObject(n)
            StageView(n, s.optString("state"), s.optInt("done"), s.optInt("total"), s.optString("error").takeIf { it.isNotBlank() && it != "null" })
        }
        val scenesJ = j.optJSONArray("scenes") ?: JSONArray()
        val scenes = (0 until scenesJ.length()).map { i ->
            val s = scenesJ.getJSONObject(i)
            SceneView(s.optInt("index", i), shots?.optJSONObject(i)?.optString("narration").orEmpty(),
                s.optString("image_state"), s.optString("voice_state"),
                s.optString("image").let { it.isNotBlank() && it != "null" },
                s.optString("error").takeIf { it.isNotBlank() && it != "null" })
        }
        val prov = j.optJSONObject("providers") ?: JSONObject()
        val v = j.optJSONObject("result")?.optJSONObject("verification")
        return ProductionView(
            j.getString("id"), j.optString("status"), j.optString("message"),
            j.optString("error").takeIf { it.isNotBlank() && it != "null" }, j.optDouble("progress", 0.0).toFloat(),
            plan?.optString("title").orEmpty().ifBlank { j.optJSONObject("spec")?.optString("idea").orEmpty().take(60) },
            plan?.optString("hook").orEmpty(), stages, scenes,
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
