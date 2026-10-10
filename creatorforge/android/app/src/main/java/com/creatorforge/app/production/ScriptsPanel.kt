package com.creatorforge.app.production

import android.content.Intent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.studio.Brain
import com.creatorforge.app.studio.SavedScript
import com.creatorforge.app.studio.Scene
import com.creatorforge.app.studio.Styles
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.util.UUID

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)

/**
 * Scripts library: everything written on the phone. Each script can be broken into scenes with ready-to-paste
 * image and video prompts (for CreatorForge, CapCut, or any image/video tool), copied, shared, or sent to the pod.
 */
@Composable
fun ScriptsPanel(onOpenGenerate: () -> Unit, onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.scripts(context) }
    var scripts by remember { mutableStateOf(store.list()) }
    var open by remember { mutableStateOf(scripts.firstOrNull()?.id) }
    var busy by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var adding by remember { mutableStateOf(false) }

    fun update(s: SavedScript) { scripts = store.upsert(s) }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(vertical = 10.dp, horizontal = 0.dp)) {
        item {
            Row {
                Text("Your scripts, scene breakdowns and prompts - saved on this phone.", color = Color.LightGray, fontSize = 13.sp, modifier = Modifier.weight(1f))
                TextButton({ adding = true }) { Text("+ PASTE", color = Gold) }
            }
        }
        item { AiBanner(onOpenSettings) }
        error?.let { e -> item { Text(e, color = Danger, fontSize = 13.sp) } }
        notice?.let { n -> item { Text(n, color = Gold, fontSize = 13.sp) } }
        if (scripts.isEmpty()) item {
            Text("Nothing saved yet. Write scripts in Trends or the Director chat, or paste your own with + PASTE.", color = Dim, fontSize = 13.sp)
        }
        items(scripts, key = { it.id }) { s ->
            val expanded = open == s.id
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A1A)), modifier = Modifier.fillMaxWidth().clickable { open = if (expanded) null else s.id }) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(s.title, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
                    Text(listOfNotNull(s.source.ifBlank { null }, "${(s.script.split(Regex("\\s+")).size / 2.5).toInt()}s",
                        Styles.name(s.style), if (s.scenes.isNotEmpty()) "${s.scenes.size} scenes" else null).joinToString(" • "), color = Dim, fontSize = 12.sp)
                    Text(s.script, color = Color.LightGray, fontSize = 13.sp, maxLines = if (expanded) 200 else 3)
                    if (expanded) {
                        if (s.hashtags.isNotEmpty()) Text(s.hashtags.joinToString(" "), color = Gold, fontSize = 12.sp)
                        Text("Look", color = Gold, fontSize = 12.sp)
                        Chips(Styles.presets.map { it.first to it.second }, s.style, small = true) { update(s.copy(style = it, scenes = emptyList())) }
                        Chips(Styles.templates, s.template, small = true) { update(s.copy(template = it, scenes = emptyList())) }
                        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Button(enabled = busy == null, onClick = {
                                busy = s.id; error = null
                                scope.launch {
                                    val isScript = Brain.sentences(s.script).size >= 2
                                    runCatching { studio { StudioHub.brain(context).scenes(s.script, isScript, s.style, s.template) } }
                                        .onSuccess { update(s.copy(scenes = it)); notice = "${it.size} scenes with image and video prompts" }
                                        .onFailure { error = it.message }
                                    busy = null
                                }
                            }) { Text(if (busy == s.id) "BREAKING DOWN…" else if (s.scenes.isEmpty()) "SCENES & PROMPTS" else "REDO SCENES") }
                            OutlinedButton({ copyText(context, exportText(s)); notice = "Copied script + all prompts" }) { Text("COPY ALL") }
                            OutlinedButton({
                                context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
                                    .putExtra(Intent.EXTRA_SUBJECT, s.title).putExtra(Intent.EXTRA_TEXT, exportText(s)), null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                            }) { Text("SHARE") }
                        }
                        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            TextButton({
                                context.getSharedPreferences("creatorforge_generate", 0).edit().putString("idea", s.script).putBoolean("script_mode", true)
                                    .putString("template", s.template).putString("style", s.style).putString("active", null).apply()
                                onOpenGenerate()
                            }) { Text("MAKE VIDEO (POD)", color = Gold, fontSize = 12.sp) }
                            TextButton({ scripts = store.delete(s.id); notice = "Deleted" }) { Text("DELETE", color = Danger, fontSize = 12.sp) }
                        }
                        s.scenes.forEachIndexed { i, sc -> SceneCard(i, sc) { what, text -> copyText(context, text); notice = "Scene ${i + 1} $what copied" } }
                    }
                }
            }
        }
    }

    if (adding) PasteDialog(onDismiss = { adding = false }) { title, text ->
        adding = false
        val s = SavedScript(UUID.randomUUID().toString().take(12), title.ifBlank { Brain.sentences(text).firstOrNull()?.take(60) ?: "My script" }, text, source = "Pasted")
        scripts = store.upsert(s); open = s.id
    }
}

@Composable
private fun SceneCard(i: Int, s: Scene, onCopy: (String, String) -> Unit) {
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(Color(0xFF101010)).padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text("SCENE ${i + 1}" + listOf(s.shot, s.camera).filter { it.isNotBlank() }.joinToString(" • ", prefix = " • ").takeIf { s.shot.isNotBlank() || s.camera.isNotBlank() }.orEmpty(),
            color = Gold, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Text("“${s.narration}”", color = Color.White, fontSize = 13.sp)
        Text("Image prompt: ${s.imagePrompt}", color = Color.LightGray, fontSize = 12.sp)
        Text("Video prompt: ${s.videoPrompt}", color = Dim, fontSize = 12.sp, maxLines = 4)
        Row {
            TextButton({ onCopy("image prompt", s.imagePrompt) }) { Text("COPY IMAGE PROMPT", color = Gold, fontSize = 11.sp) }
            TextButton({ onCopy("video prompt", s.videoPrompt) }) { Text("COPY VIDEO PROMPT", color = Gold, fontSize = 11.sp) }
        }
    }
}

@Composable
private fun PasteDialog(onDismiss: () -> Unit, onSave: (String, String) -> Unit) {
    var title by remember { mutableStateOf("") }
    var text by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Add a script") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(title, { title = it }, label = { Text("Title (optional)") }, singleLine = true)
                OutlinedTextField(text, { text = it }, label = { Text("Script or idea") }, minLines = 6)
            }
        },
        confirmButton = { Button({ onSave(title.trim(), text.trim()) }, enabled = text.trim().length >= 10) { Text("SAVE") } },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } })
}

private fun exportText(s: SavedScript): String = buildString {
    appendLine(s.title); appendLine()
    appendLine("SCRIPT"); appendLine(s.script); appendLine()
    if (s.description.isNotBlank()) { appendLine("DESCRIPTION"); appendLine(s.description); appendLine() }
    if (s.hashtags.isNotEmpty()) { appendLine(s.hashtags.joinToString(" ")); appendLine() }
    s.scenes.forEachIndexed { i, sc ->
        appendLine("SCENE ${i + 1}")
        appendLine("Voice: ${sc.narration}")
        appendLine("Image prompt: ${sc.imagePrompt}")
        appendLine("Video prompt: ${sc.videoPrompt}")
        appendLine("Negative: ${sc.negative}")
        appendLine()
    }
}
