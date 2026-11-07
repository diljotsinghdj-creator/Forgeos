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

/** Hook Lab: copies of a finished video with different opening lines, to find the hook that keeps people watching. */
@Composable
fun HookLabScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var picked by remember { mutableStateOf<ProductionSummary?>(null) }
    var current by remember { mutableStateOf<ProductionView?>(null) }
    val hooks = remember { mutableStateListOf("", "", "") }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var groups by remember { mutableStateOf<Map<String, List<ProductionSummary>>>(emptyMap()) }
    val client = remember { ProductionClient(StudioHub.workerUrl(context)) }

    fun refresh() = scope.launch { runCatching { client.list() }.onSuccess { l -> groups = l.filter { it.hookGroup.isNotBlank() }.groupBy { it.hookGroup } } }
    LaunchedEffect(Unit) { if (StudioHub.hasWorker(context)) refresh() }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("The first 3 seconds decide if people stay. Make 2-3 versions with different hooks, post them, and keep the winner's style.")
        if (!PodGate(onOpenSettings, "Hook Lab")) return@Column
        Section("1. PICK A FINISHED VIDEO") {
            ReadyVideoPicker(picked?.id, { p -> picked = p; scope.launch { current = runCatching { client.get(p.id) }.getOrNull() } }) { it.hookGroup.isBlank() }
        }
        current?.let { v ->
            Section("2. WRITE HOOKS", "Current opening: “${v.scenes.firstOrNull()?.narration.orEmpty()}”") {
                hooks.forEachIndexed { i, h ->
                    OutlinedTextField(h, { hooks[i] = it.take(200) }, Modifier.fillMaxWidth(), label = { Text("Hook ${'A' + i}") })
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(enabled = !busy, onClick = {
                        busy = true
                        scope.launch {
                            val script = v.scenes.joinToString(" ") { it.narration }
                            runCatching { studio { StudioHub.brain(context).hooks(script, 3) } }
                                .onSuccess { it.forEachIndexed { i, h -> if (i < hooks.size) hooks[i] = h } }.onFailure { message = it.message }
                            busy = false
                        }
                    }) { Text("✨ SUGGEST") }
                    Button(enabled = !busy && hooks.any { it.isNotBlank() }, onClick = {
                        busy = true; message = null
                        scope.launch {
                            runCatching { client.hookVariants(v.id, hooks.filter { it.isNotBlank() }) }
                                .onSuccess { n -> message = "Making $n versions - only the opening is re-recorded, so it's quick"; refresh() }
                                .onFailure { message = it.message }
                            busy = false
                        }
                    }) { Text("MAKE VERSIONS") }
                }
                Note(message)
            }
        }
        if (groups.isNotEmpty()) Section("YOUR HOOK TESTS", "Post the versions at the same time of day, then compare views in Analytics after 48 hours.") {
            groups.forEach { (_, list) ->
                list.sortedBy { it.hookVariant }.forEach { p ->
                    Text("${p.hookVariant} • ${p.title} • ${if (p.status == "READY") "ready" else "${(p.progress * 100).toInt()}%"}",
                        color = if (p.status == "READY") Color.White else UiDim, fontSize = 13.sp)
                }
                Spacer(Modifier.height(6.dp))
            }
            TextButton({ refresh() }) { Text("↻ REFRESH", color = UiGold) }
        }
    }
}
