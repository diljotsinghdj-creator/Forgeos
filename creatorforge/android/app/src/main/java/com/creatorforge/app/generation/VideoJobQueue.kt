package com.creatorforge.app.generation

import android.content.Context
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

data class QueuedVideoJob(
 val localId:String=UUID.randomUUID().toString(),
 val remoteId:String?=null,
 val prompt:String,
 val state:VideoJobState=VideoJobState.QUEUED,
 val progress:Int=0,
 val message:String?=null,
 val resultUrl:String?=null
)

class VideoJobQueue(context:Context){
 private val prefs=context.getSharedPreferences("creatorforge_video_queue",Context.MODE_PRIVATE)
 private val _jobs=MutableStateFlow(load())
 val jobs: StateFlow<List<QueuedVideoJob>> = _jobs.asStateFlow()

 fun enqueue(prompt:String):QueuedVideoJob {
  require(prompt.isNotBlank()){"Video prompt is empty"}
  val j=QueuedVideoJob(prompt=prompt.trim()); update(_jobs.value+j); return j
 }
 fun applyRemote(localId:String, remote:VideoJob){
  update(_jobs.value.map{if(it.localId==localId) it.copy(remoteId=remote.id,state=remote.state,progress=remote.progress.coerceIn(0,100),message=remote.message,resultUrl=remote.resultUrl) else it})
 }
 fun fail(localId:String,message:String){ update(_jobs.value.map{if(it.localId==localId) it.copy(state=VideoJobState.FAILED,message=message.take(240)) else it}) }
 fun cancelLocal(localId:String){ update(_jobs.value.map{if(it.localId==localId) it.copy(state=VideoJobState.CANCELLED,message="Cancelled") else it}) }
 fun retry(localId:String){ update(_jobs.value.map{if(it.localId==localId && it.state==VideoJobState.FAILED) it.copy(remoteId=null,state=VideoJobState.QUEUED,progress=0,message=null,resultUrl=null) else it}) }
 fun removeTerminal(localId:String){ update(_jobs.value.filterNot{it.localId==localId && it.state in setOf(VideoJobState.READY,VideoJobState.FAILED,VideoJobState.CANCELLED)}) }

 private fun update(v:List<QueuedVideoJob>){_jobs.value=v; save(v)}
 private fun save(v:List<QueuedVideoJob>){
  val a=JSONArray()
  v.forEach{j->a.put(JSONObject().put("localId",j.localId).put("remoteId",j.remoteId).put("prompt",j.prompt).put("state",j.state.name).put("progress",j.progress).put("message",j.message).put("resultUrl",j.resultUrl))}
  prefs.edit().putString("jobs",a.toString()).apply()
 }
 private fun load():List<QueuedVideoJob> = runCatching{
  val a=JSONArray(prefs.getString("jobs","[]")); (0 until a.length()).mapNotNull{i->
   runCatching{val o=a.getJSONObject(i); QueuedVideoJob(o.getString("localId"),o.optString("remoteId").ifBlank{null},o.getString("prompt"),VideoJobState.valueOf(o.getString("state")),o.optInt("progress",0).coerceIn(0,100),o.optString("message").ifBlank{null},o.optString("resultUrl").ifBlank{null})}.getOrNull()
  }
 }.getOrDefault(emptyList())
}
