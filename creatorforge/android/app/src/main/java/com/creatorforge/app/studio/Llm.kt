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
        AiPreset("gemini", "Google Gemini (free tier)", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash",
            "https://aistudio.google.com/apikey", "Free key with your Google account. Generous daily limit."),
        AiPreset("groq", "Groq (free tier)", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile",
            "https://console.groq.com/keys", "Free key, very fast open models (Llama)."),
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

/** Pulls the first JSON object out of a model answer (models sometimes wrap it in ``` fences or prose). */
fun extractJson(raw: String): JSONObject {
    val text = raw.replace(Regex("```(?:json)?"), "")
    val start = text.indexOf('{')
    val end = text.lastIndexOf('}')
    if (start < 0 || end <= start) throw IllegalArgumentException("no JSON object in the answer")
    return JSONObject(text.substring(start, end + 1))
}
