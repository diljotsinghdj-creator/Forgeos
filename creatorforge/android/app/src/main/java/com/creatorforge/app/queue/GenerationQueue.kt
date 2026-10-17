package com.creatorforge.app.queue

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

enum class QueueState { QUEUED, RUNNING, SUCCEEDED, FAILED }
data class GenerationJob(val id:String, val projectId:String, val sceneId:String, val state:QueueState, val error:String?=null)

class GenerationQueue(context: Context) {
    private val prefs=context.getSharedPreferences("creatorforge_generation_queue",Context.MODE_PRIVATE)
    fun load():List<GenerationJob> = runCatching {
        val a=JSONArray(prefs.getString("jobs","[]")); (0 until a.length()).map { i -> val o=a.getJSONObject(i)
            GenerationJob(o.getString("id"),o.getString("projectId"),o.getString("sceneId"),QueueState.valueOf(o.getString("state")),o.optString("error").ifBlank{null}) }
    }.getOrDefault(emptyList())
    fun save(jobs:List<GenerationJob>) { val a=JSONArray(); jobs.forEach { j->a.put(JSONObject().put("id",j.id).put("projectId",j.projectId).put("sceneId",j.sceneId).put("state",j.state.name).put("error",j.error?:"")) }; prefs.edit().putString("jobs",a.toString()).apply() }
    fun recoverInterrupted():List<GenerationJob> = load().map { if(it.state==QueueState.RUNNING) it.copy(state=QueueState.FAILED,error="Generation interrupted") else it }.also(::save)
}
