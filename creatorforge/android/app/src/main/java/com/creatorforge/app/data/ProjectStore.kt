package com.creatorforge.app.data

import android.content.Context
import com.creatorforge.app.model.*
import org.json.JSONArray
import org.json.JSONObject

class ProjectStore(context: Context) {
    private val prefs = context.getSharedPreferences("creatorforge_v04_projects", Context.MODE_PRIVATE)
    fun save(projects: List<CreatorProject>) = prefs.edit().putString("projects", encode(projects).toString()).apply()
    fun load(): List<CreatorProject> = runCatching {
        val raw = prefs.getString("projects", "[]") ?: "[]"; val arr = JSONArray(raw)
        (0 until arr.length()).map { i ->
            val p = arr.getJSONObject(i); val scenes = p.optJSONArray("scenes") ?: JSONArray()
            CreatorProject(
                p.getString("id"), p.getString("title"), ProjectType.valueOf(p.getString("type")),
                AspectRatio.valueOf(p.getString("ratio")), p.getString("prompt"),
                (0 until scenes.length()).map { j -> val s=scenes.getJSONObject(j); Scene(s.getString("id"),s.getInt("order"),s.getString("title"),s.getString("narration"),s.getString("visualPrompt"),s.getInt("duration"),SceneStatus.valueOf(s.optString("status","PLANNED")),s.optString("visualAssetPath").ifBlank{null},s.optString("audioAssetPath").ifBlank{null}) }
            )
        }
    }.getOrDefault(emptyList())
    private fun encode(projects: List<CreatorProject>) = JSONArray().apply { projects.forEach { p -> put(JSONObject().apply {
        put("id",p.id); put("title",p.title); put("type",p.type.name); put("ratio",p.aspectRatio.name); put("prompt",p.prompt)
        put("scenes",JSONArray().apply { p.scenes.forEach { s -> put(JSONObject().apply { put("id",s.id);put("order",s.order);put("title",s.title);put("narration",s.narration);put("visualPrompt",s.visualPrompt);put("duration",s.durationSeconds);put("status",s.status.name);put("visualAssetPath",s.visualAssetPath ?: "");put("audioAssetPath",s.audioAssetPath ?: "") }) } })
    }) } }
}
