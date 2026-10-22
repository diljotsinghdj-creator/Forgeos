package com.creatorforge.app.generation

import android.content.Context
import com.creatorforge.app.model.AspectRatio
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

sealed class GenerationResult {
    data class Success(val file: File): GenerationResult()
    data class Failure(val message: String): GenerationResult()
}

class ReplicateImageProvider(private val context: Context) {
    private val client = OkHttpClient.Builder().connectTimeout(20, TimeUnit.SECONDS).readTimeout(90, TimeUnit.SECONDS).build()
    suspend fun generate(token: String, prompt: String, ratio: AspectRatio): GenerationResult = withContext(Dispatchers.IO) {
        try {
            val aspect = when(ratio){ AspectRatio.VERTICAL_9_16 -> "9:16"; AspectRatio.LANDSCAPE_16_9 -> "16:9"; AspectRatio.SQUARE_1_1 -> "1:1" }
            val payload = JSONObject().put("input", JSONObject().put("prompt", prompt).put("aspect_ratio", aspect).put("output_format", "png"))
            val create = Request.Builder().url("https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions")
                .header("Authorization", "Bearer $token").header("Content-Type", "application/json")
                .post(payload.toString().toRequestBody("application/json".toMediaType())).build()
            val first = client.newCall(create).execute(); val body = first.body?.string().orEmpty()
            if (!first.isSuccessful) return@withContext GenerationResult.Failure("Provider HTTP ${first.code}")
            var json = JSONObject(body); val getUrl = json.optJSONObject("urls")?.optString("get").orEmpty()
            repeat(60) {
                when(json.optString("status")) {
                    "succeeded" -> {
                        val output = json.opt("output")
                        val url = when(output){ is org.json.JSONArray -> output.optString(0); is String -> output; else -> "" }
                        if (url.isBlank()) return@withContext GenerationResult.Failure("Provider returned no image URL")
                        val download = client.newCall(Request.Builder().url(url).get().build()).execute()
                        val bytes = download.body?.bytes() ?: return@withContext GenerationResult.Failure("Empty image response")
                        if (!download.isSuccessful || bytes.size < 10_000) return@withContext GenerationResult.Failure("Invalid image response")
                        val sigOk = bytes.take(8).toByteArray().contentEquals(byteArrayOf(0x89.toByte(),0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A)) || (bytes.size>3 && bytes[0]==0xFF.toByte() && bytes[1]==0xD8.toByte() && bytes[2]==0xFF.toByte())
                        if (!sigOk) return@withContext GenerationResult.Failure("Downloaded asset is not a verified image")
                        val dir = File(context.filesDir,"generated_images").apply{mkdirs()}; val file=File(dir,"cf_${System.currentTimeMillis()}.png"); file.writeBytes(bytes)
                        return@withContext GenerationResult.Success(file)
                    }
                    "failed", "canceled" -> return@withContext GenerationResult.Failure(json.optString("error","Generation failed"))
                }
                if (getUrl.isBlank()) return@withContext GenerationResult.Failure("Provider supplied no status URL")
                delay(1500)
                val poll = client.newCall(Request.Builder().url(getUrl).header("Authorization","Bearer $token").get().build()).execute()
                if (!poll.isSuccessful) return@withContext GenerationResult.Failure("Status HTTP ${poll.code}")
                json = JSONObject(poll.body?.string().orEmpty())
            }
            GenerationResult.Failure("Generation timed out")
        } catch(e: Exception){ GenerationResult.Failure(e.message ?: "Generation error") }
    }
}
