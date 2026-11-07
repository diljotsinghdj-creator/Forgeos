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
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.File

/** Shorts Clipper: a long video becomes several vertical Shorts with captions, cut at its best moments. */
@Composable
fun ClipperScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember { ProductionClient(StudioHub.workerUrl(context)) }
    var picked by remember { mutableStateOf<ProductionSummary?>(null) }
    var count by remember { mutableStateOf("3") }
    var seconds by remember { mutableStateOf("45") }
    var jobs by remember { mutableStateOf<List<ClipJob>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        if (!StudioHub.hasWorker(context)) return@LaunchedEffect
        while (true) {
            runCatching { client.clipJobs() }.onSuccess { jobs = it }
            delay(if (jobs.any { it.status in setOf("QUEUED", "RUNNING") }) 3000 else 20000)
        }
    }

    fun withClip(job: ClipJob, n: Int, action: (File) -> Unit) {
        val dest = File(context.getExternalFilesDir("Movies") ?: context.filesDir, "CreatorForge_short_${job.id}_$n.mp4")
        if (dest.isFile && isMp4(dest)) return action(dest)
        scope.launch { runCatching { client.fetch("/v1/clips/${job.id}/files/$n", dest, ::isMp4) }.onSuccess(action).onFailure { message = it.message } }
    }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("Turn one long video into several Shorts. The AI picks moments that stand on their own; each is reframed to 9:16 with captions.")
        if (!PodGate(onOpenSettings, "The Shorts Clipper")) return@Column
        Section("1. PICK A LONG VIDEO") { ReadyVideoPicker(picked?.id, { picked = it }) }
        Section("2. HOW MANY") {
            Chips(listOf("2" to "2 Shorts", "3" to "3 Shorts", "5" to "5 Shorts"), count, small = true) { count = it }
            Chips(listOf("30" to "~30s", "45" to "~45s", "60" to "~60s"), seconds, small = true) { seconds = it }
            Button(enabled = picked != null && !busy, onClick = {
                busy = true; message = null
                scope.launch {
                    runCatching { client.createClips(picked!!.id, null, count.toInt(), seconds.toInt(), null) }
                        .onSuccess { j -> jobs = listOf(j) + jobs; message = "Cutting Shorts from “${picked!!.title}”…" }.onFailure { message = it.message }
                    busy = false
                }
            }) { Text("MAKE SHORTS") }
            Note(message)
        }
        jobs.forEach { j ->
            Section(j.title.ifBlank { "Clip job" }, when (j.status) { "READY" -> "${j.clips.size} Shorts ready"; "FAILED" -> "Failed: ${j.error}"; else -> j.message }) {
                if (j.status in setOf("QUEUED", "RUNNING")) LinearProgressIndicator(Modifier.fillMaxWidth())
                j.clips.forEach { c ->
                    Text("${c.index}. ${c.title}", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                    Text("${"%.0f".format(c.durationS)}s • from ${"%.0f".format(c.start)}s • ${c.hook}", color = UiDim, fontSize = 12.sp)
                    Row {
                        TextButton({ withClip(j, c.index) { openVideo(context, it, android.content.Intent.ACTION_VIEW) } }) { Text("PLAY", color = UiGold, fontSize = 12.sp) }
                        TextButton({ withClip(j, c.index) { openVideo(context, it, android.content.Intent.ACTION_SEND) } }) { Text("SHARE", color = UiGold, fontSize = 12.sp) }
                        TextButton({ withClip(j, c.index) { message = saveToGallery(context, it) } }) { Text("SAVE", color = UiGold, fontSize = 12.sp) }
                    }
                }
            }
        }
    }
}
