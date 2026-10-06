package com.creatorforge.app.generation

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File

interface VoiceProvider { suspend fun generate(token:String, voiceId:String, text:String): GenerationResult }

class ElevenLabsVoiceProvider(private val context:Context):VoiceProvider {
    private val client=OkHttpClient()
    override suspend fun generate(token:String,voiceId:String,text:String):GenerationResult=withContext(Dispatchers.IO){
        try {
            if(token.isBlank()||voiceId.isBlank()||text.isBlank()) return@withContext GenerationResult.Failure("Voice credentials/text missing")
            val body=JSONObject().put("text",text).put("model_id","eleven_multilingual_v2").toString().toRequestBody("application/json".toMediaType())
            val req=Request.Builder().url("https://api.elevenlabs.io/v1/text-to-speech/$voiceId").header("xi-api-key",token).header("Accept","audio/mpeg").post(body).build()
            client.newCall(req).execute().use { r ->
                if(!r.isSuccessful) return@withContext GenerationResult.Failure("Voice provider HTTP ${r.code}")
                val bytes=r.body?.bytes()?:return@withContext GenerationResult.Failure("Empty audio response")
                if(bytes.size<1000) return@withContext GenerationResult.Failure("Audio response too small")
                val dir=File(context.filesDir,"generated_audio").apply{mkdirs()}; val f=File(dir,"voice_${System.currentTimeMillis()}.mp3");f.writeBytes(bytes);GenerationResult.Success(f)
            }
        } catch(e:Exception){GenerationResult.Failure(e.message?:"Voice generation error")}
    }
}
