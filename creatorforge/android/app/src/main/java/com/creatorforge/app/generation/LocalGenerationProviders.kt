package com.creatorforge.app.generation

import android.content.Context
import com.creatorforge.app.model.AspectRatio
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.net.URI
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

interface ImageGenerationProvider { suspend fun generate(prompt:String, ratio:AspectRatio):GenerationResult }
interface LocalVoiceEngine { suspend fun generate(text:String):GenerationResult }

data class LocalProviderConfig(val baseUrl:String){
    fun normalized()=baseUrl.trim().trimEnd('/')
    fun validationError():String? = try {
        val u=URI(normalized())
        when { normalized().isBlank()->"Worker URL is empty"; u.scheme !in listOf("http","https")->"Worker URL must use http or https"; u.host.isNullOrBlank()->"Worker URL has no host"; else->null }
    } catch(_:Exception){ "Worker URL is invalid" }
}

data class WorkerHealth(val ok:Boolean,val message:String,val version:String?=null)

class LocalWorkerClient(private val config:LocalProviderConfig){
    private val client=OkHttpClient.Builder().connectTimeout(5,TimeUnit.SECONDS).readTimeout(8,TimeUnit.SECONDS).callTimeout(10,TimeUnit.SECONDS).build()
    suspend fun health():WorkerHealth=withContext(Dispatchers.IO){
        config.validationError()?.let{return@withContext WorkerHealth(false,it)}
        try { client.newCall(Request.Builder().url("${config.normalized()}/health").get().build()).execute().use { r ->
            if(!r.isSuccessful)return@withContext WorkerHealth(false,"Worker health HTTP ${r.code}")
            val body=r.body?.string().orEmpty(); val j=runCatching{JSONObject(body)}.getOrNull()
            if(j?.optBoolean("ok",false)!=true) WorkerHealth(false,"Worker did not report ready") else WorkerHealth(true,"Worker online",j.optString("version").ifBlank{null})
        }} catch(e:Exception){WorkerHealth(false,"Worker unavailable: ${e.message?:"connection error"}")}
    }
}

private fun sha256(bytes:ByteArray)=MessageDigest.getInstance("SHA-256").digest(bytes).joinToString(""){"%02x".format(it)}

class SelfHostedImageProvider(private val context:Context, private val config:LocalProviderConfig):ImageGenerationProvider {
 private val client=OkHttpClient.Builder().connectTimeout(10,TimeUnit.SECONDS).readTimeout(180,TimeUnit.SECONDS).callTimeout(190,TimeUnit.SECONDS).build()
 override suspend fun generate(prompt:String,ratio:AspectRatio):GenerationResult=withContext(Dispatchers.IO){
  config.validationError()?.let{return@withContext GenerationResult.Failure(it)}
  if(prompt.isBlank())return@withContext GenerationResult.Failure("Scene prompt is empty")
  try{
   val aspect=when(ratio){AspectRatio.VERTICAL_9_16->"9:16";AspectRatio.LANDSCAPE_16_9->"16:9";AspectRatio.SQUARE_1_1->"1:1"}
   val body=JSONObject().put("prompt",prompt).put("aspect_ratio",aspect).toString().toRequestBody("application/json".toMediaType())
   client.newCall(Request.Builder().url("${config.normalized()}/v1/images/generate").post(body).build()).execute().use { r ->
    if(!r.isSuccessful){val detail=r.body?.string()?.take(240).orEmpty();return@withContext GenerationResult.Failure("Local image provider HTTP ${r.code}${if(detail.isBlank())"" else ": $detail"}")}
    val bytes=r.body?.bytes()?:return@withContext GenerationResult.Failure("Empty local image response")
    val png=bytes.size>8&&bytes.copyOfRange(0,8).contentEquals(byteArrayOf(0x89.toByte(),0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A)); val jpg=bytes.size>3&&bytes[0]==0xFF.toByte()&&bytes[1]==0xD8.toByte()&&bytes[2]==0xFF.toByte()
    if(bytes.size<10_000||(!png&&!jpg))return@withContext GenerationResult.Failure("Local provider returned an unverified image")
    val dir=File(context.filesDir,"generated_images").apply{mkdirs()};val f=File(dir,"local_${System.currentTimeMillis()}_${sha256(bytes).take(12)}.${if(png)"png" else "jpg"}");f.writeBytes(bytes);GenerationResult.Success(f)
   }
  }catch(e:Exception){GenerationResult.Failure("Local provider unavailable: ${e.message?:"connection error"}")}
 }
}

class SelfHostedVoiceEngine(private val context:Context,private val config:LocalProviderConfig):LocalVoiceEngine{
 private val client=OkHttpClient.Builder().connectTimeout(10,TimeUnit.SECONDS).readTimeout(180,TimeUnit.SECONDS).callTimeout(190,TimeUnit.SECONDS).build()
 override suspend fun generate(text:String):GenerationResult=withContext(Dispatchers.IO){
  config.validationError()?.let{return@withContext GenerationResult.Failure(it)};if(text.isBlank())return@withContext GenerationResult.Failure("Narration text is empty")
  try{val body=JSONObject().put("text",text).put("format","wav").toString().toRequestBody("application/json".toMediaType());client.newCall(Request.Builder().url("${config.normalized()}/v1/voice/generate").post(body).build()).execute().use { r->if(!r.isSuccessful)return@withContext GenerationResult.Failure("Local voice provider HTTP ${r.code}: ${r.body?.string()?.take(240).orEmpty()}");val bytes=r.body?.bytes()?:return@withContext GenerationResult.Failure("Empty voice response");val wav=bytes.size>=44&&String(bytes.copyOfRange(0,4))=="RIFF"&&String(bytes.copyOfRange(8,12))=="WAVE";if(!wav)return@withContext GenerationResult.Failure("Unverified WAV response");val dir=File(context.filesDir,"generated_audio").apply{mkdirs()};val f=File(dir,"local_${System.currentTimeMillis()}_${sha256(bytes).take(12)}.wav");f.writeBytes(bytes);GenerationResult.Success(f)}
  }catch(e:Exception){GenerationResult.Failure("Local voice unavailable: ${e.message?:"connection error"}")}}
}


enum class VideoJobState { QUEUED, GENERATING, READY, FAILED, CANCELLED }
data class VideoJob(val id:String,val state:VideoJobState,val progress:Int=0,val message:String?=null,val resultUrl:String?=null)

class SelfHostedVideoProvider(private val config:LocalProviderConfig){
 private val client=OkHttpClient.Builder().connectTimeout(10,TimeUnit.SECONDS).readTimeout(30,TimeUnit.SECONDS).callTimeout(35,TimeUnit.SECONDS).build()
 suspend fun submit(prompt:String,ratio:AspectRatio,durationSeconds:Int):Result<VideoJob> = withContext(Dispatchers.IO){
  config.validationError()?.let{return@withContext Result.failure(IllegalArgumentException(it))}
  if(prompt.isBlank()) return@withContext Result.failure(IllegalArgumentException("Video prompt is empty"))
  runCatching {
   val aspect=when(ratio){AspectRatio.VERTICAL_9_16->"9:16";AspectRatio.LANDSCAPE_16_9->"16:9";AspectRatio.SQUARE_1_1->"1:1"}
   val body=JSONObject().put("prompt",prompt).put("aspect_ratio",aspect).put("duration_seconds",durationSeconds.coerceIn(1,30)).toString().toRequestBody("application/json".toMediaType())
   client.newCall(Request.Builder().url("${config.normalized()}/v1/video/jobs").post(body).build()).execute().use { r->
    if(!r.isSuccessful) error("Video submit HTTP ${r.code}: ${r.body?.string()?.take(240).orEmpty()}")
    parseVideoJob(r.body?.string().orEmpty())
   }
  }
 }
 suspend fun status(id:String):Result<VideoJob> = withContext(Dispatchers.IO){runCatching{
  client.newCall(Request.Builder().url("${config.normalized()}/v1/video/jobs/$id").get().build()).execute().use{r->
   if(!r.isSuccessful) error("Video status HTTP ${r.code}: ${r.body?.string()?.take(240).orEmpty()}")
   parseVideoJob(r.body?.string().orEmpty())
  }
 }}
 suspend fun cancel(id:String):Result<Unit> = withContext(Dispatchers.IO){runCatching{
  client.newCall(Request.Builder().url("${config.normalized()}/v1/video/jobs/$id").delete().build()).execute().use{r->
   if(r.code !in listOf(200,202,204,409)) error("Video cancel HTTP ${r.code}")
  }
 }}
 private fun parseVideoJob(raw:String):VideoJob{
  val j=JSONObject(raw); val id=j.optString("id")
  if(id.isBlank()) error("Worker returned video job without id")
  val state=runCatching{VideoJobState.valueOf(j.optString("state","QUEUED").uppercase())}.getOrElse{error("Unknown video job state")}
  return VideoJob(id,state,j.optInt("progress",0).coerceIn(0,100),j.optString("message").ifBlank{null},j.optString("result_url").ifBlank{null})
 }
}
