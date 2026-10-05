package com.forgeos.app.build
import android.content.Context
import com.forgeos.app.model.*
import org.json.JSONArray
import org.json.JSONObject
class BuildJournal(private val context: Context) {
 private val prefs=context.getSharedPreferences("forgeos_jobs",Context.MODE_PRIVATE)
 fun load():List<BuildJob> = runCatching { val a=JSONArray(prefs.getString("jobs","[]")); (0 until a.length()).map { i -> a.getJSONObject(i).let { o -> BuildJob(o.getString("id"),o.getString("projectId"),o.getString("task"),JobState.valueOf(o.getString("state")),o.getLong("createdAt"),o.getLong("updatedAt"),if(o.has("exitCode"))o.getInt("exitCode") else null,o.optString("logPath").ifBlank{null},o.optString("apkPath").ifBlank{null},o.optString("error").ifBlank{null}) } } }.getOrDefault(emptyList())
 fun upsert(job:BuildJob){ val list=load().filterNot{it.id==job.id}+job; val a=JSONArray(); list.takeLast(50).forEach { j -> a.put(JSONObject().put("id",j.id).put("projectId",j.projectId).put("task",j.task).put("state",j.state.name).put("createdAt",j.createdAt).put("updatedAt",j.updatedAt).apply { j.exitCode?.let{put("exitCode",it)}; j.logPath?.let{put("logPath",it)}; j.apkPath?.let{put("apkPath",it)}; j.error?.let{put("error",it)} }) }; prefs.edit().putString("jobs",a.toString()).commit() }
 fun recoverInterrupted(){ load().filter{it.state==JobState.RUNNING}.forEach { upsert(it.copy(state=JobState.INTERRUPTED,updatedAt=System.currentTimeMillis(),error="Build interrupted by process/device shutdown; safe to retry.")) } }
}