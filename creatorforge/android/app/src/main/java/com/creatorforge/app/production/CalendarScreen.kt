package com.creatorforge.app.production

import android.Manifest
import android.content.Intent
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.Reminders
import com.creatorforge.app.studio.Channel
import com.creatorforge.app.studio.Slot
import kotlinx.coroutines.launch
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Publish Calendar: every planned post across channels, with reminders and one-tap posting. */
@Composable
fun CalendarScreen(onOpenChannels: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.channels(context) }
    var channels by remember { mutableStateOf(store.list()) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf<String?>(null) }
    val notifyPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }

    fun update(ch: Channel, s: Slot) { channels = store.upsert(ch.copy(slots = ch.slots.map { if (it.id == s.id) s else it })) }

    val posts = channels.flatMap { ch -> ch.slots.filter { it.status != "skipped" && it.status != "planned" || it.productionId.isNotBlank() }.map { ch to it } }
        .sortedWith(compareBy({ it.second.day }, { it.second.time }))
        .let { list -> list.mapIndexed { i, (ch, sl) -> Triple(ch, sl, if (i == 0 || list[i - 1].second.day != sl.day) sl.day else null) } }
    val today = LocalDate.now().toString()

    fun post(ch: Channel, s: Slot) {
        busy = s.id; message = null
        scope.launch {
            runCatching {
                val client = ProductionClient(StudioHub.workerUrl(context))
                val caption = runCatching { client.publishKit(s.productionId).asText() }
                    .getOrDefault("${s.idea.title}\n\n${s.idea.hook}\n\n#shorts")
                copyText(context, caption)
                val dest = File(context.getExternalFilesDir("Movies") ?: context.filesDir, "CreatorForge_${s.productionId}.mp4")
                if (!(dest.isFile && isMp4(dest))) client.fetch("/v1/productions/${s.productionId}/video", dest, ::isMp4)
                dest
            }.onSuccess { f ->
                openVideo(context, f, Intent.ACTION_SEND)
                message = "Caption copied - pick YouTube or TikTok, paste the caption, then mark it posted."
            }.onFailure { message = if (StudioHub.hasWorker(context)) it.message else "Downloading the video needs your pod - connect it in Settings" }
            busy = null
        }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Lead("Approved and made videos from all channels, by day. Turn on 🔔 to get a reminder at posting time.") }
        item { Note(message) }
        if (posts.isEmpty()) item {
            Section("NOTHING SCHEDULED", "Plan a week in Channels and approve some slots - they show up here.") {
                Button(onOpenChannels) { Text("OPEN CHANNELS") }
            }
        }
        items(posts, key = { it.second.id }) { (ch, s, header) ->
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                if (header != null) Text(dayLabel(header, today), color = UiGold, fontWeight = FontWeight.Bold, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp))
                Section("${s.time} • ${ch.name}", when {
                    s.posted -> "✓ Posted"
                    s.productionId.isNotBlank() -> "Video made - ready to post"
                    s.script.isNotBlank() -> "Approved & scripted - make it in Channels"
                    else -> "Approved - write and make it in Channels"
                }) {
                    Text(s.idea.title, color = if (s.posted) UiDim else Color.White, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
                    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                        Text("🔔", fontSize = 16.sp)
                        Switch(s.remind, { on ->
                            if (on) {
                                if (Build.VERSION.SDK_INT >= 33) notifyPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
                                if (Reminders.schedule(context, s.id, "${ch.name}: ${s.idea.title}", s.day, s.time)) update(ch, s.copy(remind = true))
                                else message = "That time has passed - change the slot's day or time in Channels"
                            } else { Reminders.cancel(context, s.id); update(ch, s.copy(remind = false)) }
                        }, modifier = Modifier.padding(horizontal = 6.dp))
                        Spacer(Modifier.weight(1f))
                        if (s.productionId.isNotBlank() && !s.posted) Button({ post(ch, s) }, enabled = busy == null) { Text(if (busy == s.id) "…" else "POST") }
                        TextButton({ update(ch, s.copy(posted = !s.posted)) }) { Text(if (s.posted) "UNDO" else "MARK POSTED", color = UiGold, fontSize = 12.sp) }
                    }
                }
            }
        }
        item {
            Text("Direct upload to YouTube with scheduled publishing needs a Google sign-in set up for this app - it's on the roadmap. Until then POST shares the video to the YouTube or TikTok app with the caption ready.",
                color = UiDim, fontSize = 11.sp)
        }
    }
}

private fun dayLabel(day: String, today: String): String {
    val d = runCatching { LocalDate.parse(day) }.getOrNull() ?: return day
    val t = LocalDate.parse(today)
    return when (d) {
        t -> "TODAY"
        t.plusDays(1) -> "TOMORROW"
        else -> d.format(DateTimeFormatter.ofPattern("EEEE d MMMM", Locale.getDefault())).uppercase()
    }
}
