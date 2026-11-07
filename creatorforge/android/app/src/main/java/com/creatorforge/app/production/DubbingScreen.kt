package com.creatorforge.app.production

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

/** Languages the pod has voices for (see the setup's voice list). */
private val LANGUAGES = listOf(
    Triple("Spanish", "es_f", "🇪🇸"), Triple("French", "fr_f", "🇫🇷"), Triple("Hindi", "hi_f", "🇮🇳"),
    Triple("Italian", "it_f", "🇮🇹"), Triple("Portuguese", "pt_f", "🇧🇷"),
)

/** Dubbing: the phone translates each line (Gemini), the pod re-voices it and reuses every picture. */
@Composable
fun DubbingScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember { ProductionClient(StudioHub.workerUrl(context)) }
    var picked by remember { mutableStateOf<ProductionSummary?>(null) }
    val languages = remember { mutableStateMapOf<String, Boolean>() }
    var busy by remember { mutableStateOf<String?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("One video, many audiences. The pictures stay; the voice and captions are made in each language. Costs about half a new video.")
        AiBanner(onOpenSettings)
        if (!PodGate(onOpenSettings, "Dubbing")) return@Column
        Section("1. PICK A FINISHED VIDEO") { ReadyVideoPicker(picked?.id, { picked = it }) { it.language.isBlank() } }
        Section("2. LANGUAGES") {
            LANGUAGES.forEach { (name, _, flag) ->
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Checkbox(languages[name] == true, { languages[name] = it })
                    Text("$flag  $name", color = Color.White)
                }
            }
            Text("Voices come from the pod (Spanish, French, Hindi, Italian, Portuguese). Run the latest start command if one is missing.", color = UiDim, fontSize = 11.sp)
        }
        val chosen = LANGUAGES.filter { languages[it.first] == true }
        Button(enabled = picked != null && chosen.isNotEmpty() && busy == null, modifier = Modifier.fillMaxWidth().height(52.dp), onClick = {
            val p = picked ?: return@Button
            error = null; message = null
            scope.launch {
                runCatching {
                    val lines = client.get(p.id).scenes.map { it.narration }
                    var n = 0
                    for ((name, voice, _) in chosen) {
                        busy = "Translating into $name…"
                        val translated = studio { StudioHub.brain(context).translate(lines, name) }
                        busy = "Sending $name to the pod…"
                        client.dub(p.id, name, voice, translated); n++
                    }
                    n
                }.onSuccess { message = "Dubbing into $it language${if (it == 1) "" else "s"} - follow them in Library → Production Line" }
                    .onFailure { error = it.message }
                busy = null
            }
        }) { Text(busy ?: "DUB ${chosen.size} LANGUAGE${if (chosen.size == 1) "" else "S"}") }
        Note(message); Note(error, true)
    }
}
