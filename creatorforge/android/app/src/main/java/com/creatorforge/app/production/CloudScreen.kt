package com.creatorforge.app.production

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONObject

/** Cloud Studio: your balance and costs on the connected studio - your own pod, or a hosted CreatorForge. */
@Composable
fun CloudScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    var me by remember { mutableStateOf<JSONObject?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(Unit) {
        if (StudioHub.hasWorker(context)) runCatching { ProductionClient(StudioHub.workerUrl(context)).me() }.onSuccess { me = it }.onFailure { error = it.message }
    }
    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("CreatorForge can run on your own pod (you pay the GPU by the hour) or on a hosted studio where you pay with credits.")
        if (!PodGate(onOpenSettings, "Cloud Studio")) return@Column
        Note(error, true)
        me?.let { m ->
            if (m.optString("role") == "owner") Section("YOU OWN THIS STUDIO", "Unlimited use - you pay the GPU directly. ${m.optInt("accounts")} other login(s) on it.") {
                Text("Hand out logins with credits in Team & Clients to share or sell access.", color = Color.LightGray, fontSize = 13.sp)
            } else Section("YOUR BALANCE") {
                Text("${m.optInt("credits")} credits", color = UiGold, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                Text("${m.optInt("used")} used so far • signed in as ${m.optString("name")} (${m.optString("role")})", color = UiDim, fontSize = 12.sp)
            }
        }
        Section("WHAT THINGS COST", "1 credit = up to 30 seconds of video with stills and camera motion") {
            listOf("60-second Short (stills)" to "2", "60-second Short, AI-animated hook" to "4", "60-second Short, every scene AI-animated" to "8",
                "10-minute video (stills)" to "20", "Dub into one language" to "half the video", "Hook test (per version)" to "¼ of the video",
                "Shorts Clipper" to "1 per Short").forEach { (what, cost) ->
                Row { Text(what, color = Color.White, fontSize = 13.sp, modifier = Modifier.weight(1f)); Text(cost, color = UiGold, fontSize = 13.sp) }
            }
        }
        Section("HOSTED VERSION", "For selling CreatorForge to others") {
            Text("The studio already supports logins, credits and private work per user. To run it as a business you'd host the worker on always-on GPUs and add a payment provider that tops up credits. Writing tools stay free on the phone.",
                color = Color.LightGray, fontSize = 13.sp)
        }
    }
}
