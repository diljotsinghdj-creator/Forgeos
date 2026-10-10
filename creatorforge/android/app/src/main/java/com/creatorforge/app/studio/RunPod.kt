package com.creatorforge.app.studio

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** A pod as RunPod reports it. */
data class PodInfo(val id: String, val name: String, val status: String, val gpu: String, val costPerHour: Double, val uptimeS: Long) {
    val running get() = status == "RUNNING"
    /** The permanent address of the CreatorForge worker on this pod (needs HTTP port 8765 exposed). */
    val workerUrl get() = "https://$id-8765.proxy.runpod.net"
}

/** Starts and stops the GPU pod from the phone with the user's RunPod API key (GraphQL API). */
class RunPodApi(private val key: String, private val post: (String) -> Pair<Int, String> = defaultPost(key)) {

    private fun gql(query: String): JSONObject {
        if (key.isBlank()) throw SourceException("Add your RunPod API key in Settings first")
        val (code, body) = post(JSONObject().put("query", query).toString())
        if (code == 401 || code == 403) throw SourceException("RunPod rejected the API key - make a new one at runpod.io → Settings → API Keys")
        if (code >= 400) throw SourceException("RunPod said HTTP $code")
        val j = JSONObject(body)
        j.optJSONArray("errors")?.optJSONObject(0)?.optString("message")?.takeIf { it.isNotBlank() }?.let { throw SourceException(friendly(it)) }
        return j.optJSONObject("data") ?: JSONObject()
    }

    fun pods(): List<PodInfo> {
        val arr = gql("query { myself { pods { id name desiredStatus costPerHr machine { gpuDisplayName } runtime { uptimeInSeconds } } } }")
            .optJSONObject("myself")?.optJSONArray("pods") ?: return emptyList()
        return (0 until arr.length()).map { arr.getJSONObject(it) }.map { p ->
            PodInfo(p.getString("id"), p.optString("name"), p.optString("desiredStatus"), p.optJSONObject("machine")?.optString("gpuDisplayName").orEmpty(),
                p.optDouble("costPerHr", 0.0), p.optJSONObject("runtime")?.optLong("uptimeInSeconds") ?: 0L)
        }
    }

    fun start(id: String) {
        gql("mutation { podResume(input: { podId: \"${id.filter { it.isLetterOrDigit() }}\", gpuCount: 1 }) { id desiredStatus } }")
    }

    fun stop(id: String) {
        gql("mutation { podStop(input: { podId: \"${id.filter { it.isLetterOrDigit() }}\" }) { id desiredStatus } }")
    }

    companion object {
        /** The one-time "Container Start Command": keeps RunPod's own services and starts CreatorForge on every boot. */
        const val START_COMMAND = "bash -c \"(/start.sh &) ; sleep 15 ; curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/worker/cloud/start.sh | bash ; sleep infinity\""

        fun friendly(msg: String): String = when {
            "not enough free gpu" in msg.lowercase() || "no longer any instances" in msg.lowercase() || "no available" in msg.lowercase() ->
                "That GPU is busy right now. Try again in a few minutes, or migrate the pod on runpod.io."
            "balance" in msg.lowercase() || "insufficient" in msg.lowercase() -> "Your RunPod balance is too low - add credit on runpod.io."
            else -> "RunPod: $msg"
        }

        private fun defaultPost(key: String): (String) -> Pair<Int, String> {
            val client = OkHttpClient.Builder().connectTimeout(15, TimeUnit.SECONDS).readTimeout(60, TimeUnit.SECONDS).build()
            return { body ->
                try {
                    client.newCall(Request.Builder().url("https://api.runpod.io/graphql").header("Authorization", "Bearer $key")
                        .post(body.toRequestBody("application/json".toMediaType())).build()).execute().use { r -> r.code to (r.body?.string().orEmpty()) }
                } catch (e: Exception) {
                    throw SourceException("Can't reach RunPod: ${e.message ?: e.javaClass.simpleName}")
                }
            }
        }
    }
}
