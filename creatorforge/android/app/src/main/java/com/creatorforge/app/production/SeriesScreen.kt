package com.creatorforge.app.production

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
import com.creatorforge.app.studio.SavedScript
import com.creatorforge.app.studio.Series
import com.creatorforge.app.studio.Styles
import kotlinx.coroutines.launch
import java.util.UUID

/** Series: recurring stories with memory - each new episode knows what happened before. */
@Composable
fun SeriesScreen(onOpenSettings: () -> Unit, onOpenGenerate: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.series(context) }
    var all by remember { mutableStateOf(store.list()) }
    var open by remember { mutableStateOf(all.firstOrNull()?.id) }
    var adding by remember { mutableStateOf(all.isEmpty()) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Lead("Multi-part stories with recurring characters. Each episode remembers the story so far and ends on a cliffhanger.") }
        item { AiBanner(onOpenSettings) }
        if (adding) item {
            var name by remember { mutableStateOf("") }
            var premise by remember { mutableStateOf("") }
            var chars by remember { mutableStateOf("") }
            var style by remember { mutableStateOf("cinematic") }
            var secs by remember { mutableStateOf("60") }
            Section("NEW SERIES") {
                OutlinedTextField(name, { name = it.take(60) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Series name") })
                OutlinedTextField(premise, { premise = it }, Modifier.fillMaxWidth(), minLines = 2, label = { Text("Premise") },
                    placeholder = { Text("Two kids find a map to a buried city under London…") })
                OutlinedTextField(chars, { chars = it }, Modifier.fillMaxWidth(), minLines = 2, label = { Text("Characters (optional)") },
                    placeholder = { Text("Maya, 12, brave, red jacket; Leo, 11, nervous, glasses") })
                Chips(Styles.presets.map { it.first to it.second }, style, small = true) { style = it }
                Chips(listOf("45" to "45s", "60" to "60s", "180" to "3 min", "600" to "10 min"), secs, small = true) { secs = it }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(enabled = name.isNotBlank() && premise.length >= 10, onClick = {
                        val s = Series(UUID.randomUUID().toString().take(12), name.trim(), premise.trim(), chars.trim(), style, secs.toInt())
                        all = store.upsert(s); open = s.id; adding = false
                    }) { Text("CREATE") }
                    if (all.isNotEmpty()) TextButton({ adding = false }) { Text("CANCEL") }
                }
            }
        } else item { OutlinedButton({ adding = true }) { Text("+ NEW SERIES") } }
        item { Note(message) }
        items(all, key = { it.id }) { s ->
            val expanded = open == s.id
            Section(s.name, "${s.episodes.size} episode${if (s.episodes.size == 1) "" else "s"} • ${Styles.name(s.style)} • ${s.seconds}s each") {
                Text(s.premise, color = Color.LightGray, fontSize = 13.sp, maxLines = if (expanded) 10 else 2)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(enabled = !busy, onClick = {
                        busy = true; message = null
                        scope.launch {
                            runCatching { studio { StudioHub.brain(context).nextEpisode(s) } }.onSuccess { ep ->
                                all = store.upsert(s.copy(episodes = s.episodes + ep)); open = s.id
                                StudioHub.scripts(context).upsert(SavedScript(UUID.randomUUID().toString().take(12), ep.title, ep.script, style = s.style,
                                    template = if (s.seconds > 60) "youtube_longform" else "shorts_cinematic", source = "Series: ${s.name}"))
                                message = "Part ${ep.number} written - also saved in Scripts"
                            }.onFailure { message = it.message }
                            busy = false
                        }
                    }) { Text(if (busy) "WRITING…" else "WRITE PART ${s.episodes.size + 1}") }
                    TextButton({ open = if (expanded) null else s.id }) { Text(if (expanded) "HIDE" else "EPISODES", color = UiGold) }
                }
                if (expanded) {
                    s.episodes.asReversed().forEach { e ->
                        Text("PART ${e.number} • ${e.title}", color = UiGold, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        Text(e.summary, color = UiDim, fontSize = 12.sp)
                        Text(e.script, color = Color.LightGray, fontSize = 13.sp, maxLines = 6)
                        Row {
                            TextButton({
                                context.getSharedPreferences("creatorforge_generate", 0).edit().putString("idea", e.script).putBoolean("script_mode", true)
                                    .putString("style", s.style).putString("template", if (s.seconds > 60) "youtube_longform" else "shorts_cinematic").putString("active", null).apply()
                                onOpenGenerate()
                            }) { Text("MAKE VIDEO", color = UiGold, fontSize = 12.sp) }
                            TextButton({ copyText(context, e.script); message = "Part ${e.number} copied" }) { Text("COPY", color = UiGold, fontSize = 12.sp) }
                        }
                    }
                    TextButton({ all = store.delete(s.id) }) { Text("DELETE SERIES", color = UiDanger, fontSize = 12.sp) }
                }
            }
        }
    }
}
