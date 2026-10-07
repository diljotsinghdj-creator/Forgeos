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
import com.creatorforge.app.studio.SafetyIssue
import com.creatorforge.app.studio.SafetyRules
import kotlinx.coroutines.launch

/** Safety Check: catches wording that gets videos limited, demonetised or into legal trouble - before you post. */
@Composable
fun SafetyScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val saved = remember { StudioHub.scripts(context).list() }
    var text by remember { mutableStateOf("") }
    var issues by remember { mutableStateOf<List<SafetyIssue>?>(null) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val ticks = remember { mutableStateMapOf<Int, Boolean>() }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("Paste a script or pick a saved one. Rules catch risky phrases; with Script AI on, a careful reviewer reads it too.")
        if (saved.isNotEmpty()) Section("FROM YOUR SCRIPTS") {
            Chips(saved.take(12).map { it.id to it.title.take(24) }, "", small = true) { id -> text = saved.first { it.id == id }.script; issues = null }
        }
        OutlinedTextField(text, { text = it; issues = null }, Modifier.fillMaxWidth(), minLines = 6, label = { Text("Script") })
        Button(enabled = text.isNotBlank() && !busy, onClick = {
            busy = true; error = null
            scope.launch {
                runCatching { studio { StudioHub.brain(context).safety(text) } }.onSuccess { issues = it }.onFailure { error = it.message; issues = SafetyRules.scan(text) }
                busy = false
            }
        }) { Text(if (busy) "CHECKING…" else "CHECK") }
        Note(error, true)
        issues?.let { list ->
            if (list.isEmpty()) Section("✓ LOOKS SAFE", "Nothing risky found. Still run through the checklist below.") {}
            list.forEach { i ->
                Section(when (i.level) { "high" -> "⛔ FIX BEFORE POSTING"; "medium" -> "⚠ WORTH CHANGING"; else -> "ℹ DOUBLE-CHECK" }) {
                    Text(i.text, color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                    if (i.fix.isNotBlank()) Text(i.fix, color = Color.LightGray, fontSize = 13.sp)
                }
            }
        }
        Section("BEFORE YOU POST") {
            SafetyRules.checklist.forEachIndexed { n, item ->
                Row { Checkbox(ticks[n] == true, { ticks[n] = it }); Text(item, color = Color.LightGray, fontSize = 13.sp, modifier = Modifier.padding(top = 12.dp)) }
            }
        }
        Text("This is guidance, not legal advice.", color = UiDim, fontSize = 11.sp)
    }
}
