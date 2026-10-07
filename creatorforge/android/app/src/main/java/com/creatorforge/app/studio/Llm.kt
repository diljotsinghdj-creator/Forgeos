package com.creatorforge.app.studio

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class AiException(message: String) : Exception(message)

/** Sends one system + user message and returns the model's text. */
fun interface TextModel {
    fun complete(system: String, user: String): String
}

/** A free or paid AI service the phone can call directly. All speak the OpenAI chat format. */
data class AiPreset(val id: String, val name: String, val baseUrl: String, val model: String, val keyUrl: String, val note: String)

object AiPresets {
    val all = listOf(
        AiPreset("gemini", "Google Gemini (free tier)", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-flash-latest",
            "https://aistudio.google.com/apikey", "Free key with your Google account. Generous daily limit."),
        AiPreset("groq", "Groq (free tier)", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile",
            "https://console.groq.com/keys", "Free key, very fast open models (Llama)."),
        AiPreset("mistral", "Mistral (free tier)", "https://api.mistral.ai/v1", "mistral-small-latest",
            "https://console.mistral.ai/api-keys", "Free 'Experiment' plan - sign up, verify your phone, create a key."),
        AiPreset("cerebras", "Cerebras (free tier)", "https://api.cerebras.ai/v1", "llama-3.3-70b",
            "https://cloud.cerebras.ai", "Free key, extremely fast Llama models."),
        AiPreset("openrouter", "OpenRouter (free models)", "https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct:free",
            "https://openrouter.ai/keys", "One key for many models; ':free' models cost nothing."),
        AiPreset("custom", "Custom / my own server", "", "", "", "Any OpenAI-compatible address, e.g. Ollama on a PC: http://192.168.x.x:11434/v1"),
    )
    operator fun get(id: String) = all.firstOrNull { it.id == id } ?: all[0]
}

class OpenAiCompatible(baseUrl: String, private val model: String, private val key: String) : TextModel {
    private val base = baseUrl.trim().trimEnd('/')
    private val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(120, TimeUnit.SECONDS).build()

    override fun complete(system: String, user: String): String {
        if (base.isBlank() || model.isBlank()) throw AiException("Set up Script AI in Settings first")
        val body = JSONObject().put("model", model).put("temperature", 0.8)
            .put("messages", JSONArray().put(JSONObject().put("role", "system").put("content", system))
                .put(JSONObject().put("role", "user").put("content", user)))
        val req = Request.Builder().url("$base/chat/completions")
            .post(body.toString().toRequestBody("application/json".toMediaType()))
            .apply { if (key.isNotBlank()) header("Authorization", "Bearer $key") }.build()
        val text = try {
            client.newCall(req).execute().use { r ->
                val t = r.body?.string().orEmpty()
                when {
                    r.code == 401 || r.code == 403 -> throw AiException("The AI service rejected the key - check it in Settings")
                    r.code == 429 -> throw AiException("The free AI limit was reached for now - wait a minute and try again")
                    r.code == 404 -> throw AiException("The AI service doesn't know the model '$model' - pick another model name in Settings")
                    r.code == 400 && "API key" in t -> throw AiException("The AI service rejected the key - check it in Settings")
                    !r.isSuccessful -> throw AiException("AI service error ${r.code}: ${t.take(200)}")
                }
                t
            }
        } catch (e: AiException) {
            throw e
        } catch (e: Exception) {
            throw AiException("Can't reach the AI service: ${e.message ?: e.javaClass.simpleName}")
        }
        return try {
            JSONObject(text).getJSONArray("choices").getJSONObject(0).getJSONObject("message").getString("content")
        } catch (e: Exception) {
            throw AiException("The AI service sent an unexpected answer: ${text.take(200)}")
        }
    }
}

/**
 * Google Gemini through its own REST API (generateContent with an AI Studio key). More dependable than the
 * OpenAI-compatible route, and its errors are passed through so the user sees Google's exact reason.
 */
class GeminiNative(private val model: String, private val key: String) : TextModel {
    private val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(120, TimeUnit.SECONDS).build()

    override fun complete(system: String, user: String): String {
        if (key.isBlank()) throw AiException("Add your Gemini key in Settings")
        val m = model.trim().removePrefix("models/").ifBlank { "gemini-flash-latest" }
        val body = JSONObject()
            .put("systemInstruction", JSONObject().put("parts", JSONArray().put(JSONObject().put("text", system))))
            .put("contents", JSONArray().put(JSONObject().put("role", "user").put("parts", JSONArray().put(JSONObject().put("text", user)))))
            .put("generationConfig", JSONObject().put("temperature", 0.8))
        val req = Request.Builder().url("$GEMINI/models/$m:generateContent").header("x-goog-api-key", key.trim())
            .post(body.toString().toRequestBody("application/json".toMediaType())).build()
        val text = try {
            client.newCall(req).execute().use { r ->
                val t = r.body?.string().orEmpty()
                if (!r.isSuccessful) throw AiException(geminiError(r.code, t, m))
                t
            }
        } catch (e: AiException) { throw e } catch (e: Exception) { throw AiException("Can't reach Google Gemini: ${e.message ?: e.javaClass.simpleName}") }
        val j = JSONObject(text)
        val cand = j.optJSONArray("candidates")?.optJSONObject(0)
            ?: throw AiException("Gemini returned no answer" + (j.optJSONObject("promptFeedback")?.optString("blockReason")?.let { " (blocked: $it)" } ?: ""))
        val parts = cand.optJSONObject("content")?.optJSONArray("parts") ?: throw AiException("Gemini returned an empty answer (${cand.optString("finishReason")})")
        return (0 until parts.length()).joinToString("") { parts.getJSONObject(it).optString("text") }
    }

    companion object {
        const val GEMINI = "https://generativelanguage.googleapis.com/v1beta"

        fun listModels(key: String): List<String> {
            val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(30, TimeUnit.SECONDS).build()
            val req = Request.Builder().url("$GEMINI/models?pageSize=200").header("x-goog-api-key", key.trim()).build()
            val text = try {
                client.newCall(req).execute().use { r ->
                    val t = r.body?.string().orEmpty()
                    if (!r.isSuccessful) throw AiException(geminiError(r.code, t, ""))
                    t
                }
            } catch (e: AiException) { throw e } catch (e: Exception) { throw AiException("Can't reach Google Gemini: ${e.message}") }
            val arr = JSONObject(text).optJSONArray("models") ?: return emptyList()
            return (0 until arr.length()).map { arr.getJSONObject(it) }
                .filter { m -> (0 until (m.optJSONArray("supportedGenerationMethods")?.length() ?: 0)).any { m.getJSONArray("supportedGenerationMethods").optString(it) == "generateContent" } }
                .map { it.optString("name").removePrefix("models/") }
        }

        /** Google's error, in plain words, with the fix. */
        fun geminiError(code: Int, body: String, model: String): String {
            val msg = runCatching { JSONObject(body).getJSONObject("error").optString("message") }.getOrDefault(body.take(200))
            val b = body.lowercase()
            return when {
                "api key not valid" in b || "api_key_invalid" in b -> "Google says the key isn't valid. Make a new one at aistudio.google.com/apikey (it starts with AIza) and paste it again."
                "has not been used in project" in b || "service_disabled" in b || "is disabled" in b ->
                    "The Gemini API is switched off for this key's Google Cloud project. Easiest fix: make the key at aistudio.google.com/apikey instead."
                "user location is not supported" in b || "failed_precondition" in b && "location" in b -> "Google doesn't offer the free Gemini API in this region. Use Groq instead (free)."
                code == 429 || "resource_exhausted" in b -> "The free Gemini limit is used up for now - wait a minute (or until tomorrow) and try again."
                code == 404 -> "Google doesn't offer the model '$model' to this key. Tap SHOW MODELS MY KEY CAN USE and pick one."
                code == 403 -> "Google refused the request: $msg"
                else -> "Gemini error $code: $msg"
            }
        }
    }
}

/** Asks the service which models this key can use (OpenAI-style GET /models). Names come back without "models/". */
fun listModels(baseUrl: String, key: String): List<String> {
    val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(30, TimeUnit.SECONDS).build()
    val req = Request.Builder().url(baseUrl.trim().trimEnd('/') + "/models").apply { if (key.isNotBlank()) header("Authorization", "Bearer $key") }.build()
    val text = try {
        client.newCall(req).execute().use { r ->
            val t = r.body?.string().orEmpty()
            if (r.code == 401 || r.code == 403 || (r.code == 400 && "API key" in t)) throw AiException("The AI service rejected the key - check it in Settings")
            if (!r.isSuccessful) throw AiException("Couldn't list models (HTTP ${r.code})")
            t
        }
    } catch (e: AiException) { throw e } catch (e: Exception) { throw AiException("Can't reach the AI service: ${e.message}") }
    val data = runCatching { JSONObject(text).getJSONArray("data") }.getOrNull() ?: return emptyList()
    return (0 until data.length()).map { data.getJSONObject(it).optString("id").removePrefix("models/") }.filter { it.isNotBlank() }
}

/** Picks the best everyday text model from a list: a fast "flash" chat model, newest first; never image/audio/embedding models. */
fun pickTextModel(models: List<String>): String? {
    val text = models.filter { m -> listOf("embed", "image", "imagen", "tts", "audio", "vision", "live", "veo", "aqa", "learnlm", "guard", "whisper").none { it in m.lowercase() } }
    fun version(m: String) = Regex("(\\d+(?:\\.\\d+)?)").find(m)?.value?.toDoubleOrNull() ?: 0.0
    val ranked = text.sortedWith(compareByDescending<String> { "latest" in it }.thenByDescending { version(it) })
    return ranked.firstOrNull { "flash" in it && "lite" !in it && "preview" !in it && "exp" !in it }
        ?: ranked.firstOrNull { "flash" in it } ?: ranked.firstOrNull { "llama-3.3-70b" in it } ?: ranked.firstOrNull()
}

/** Pulls the first JSON object out of a model answer (models sometimes wrap it in ``` fences or prose). */
fun extractJson(raw: String): JSONObject {
    val text = raw.replace(Regex("```(?:json)?"), "")
    val start = text.indexOf('{')
    val end = text.lastIndexOf('}')
    if (start < 0 || end <= start) throw IllegalArgumentException("no JSON object in the answer")
    return JSONObject(text.substring(start, end + 1))
}
