package com.creatorforge.app.production

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.studio.Draft
import com.creatorforge.app.studio.ProductionBodies
import com.creatorforge.app.studio.SavedScript
import com.creatorforge.app.studio.Styles
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)

private val STARTERS = listOf(
    "Give me 5 faceless Shorts ideas about money habits",
    "A 60-second story about a lighthouse keeper, anime style",
    "A 10-minute documentary about the fall of Rome",
    "Write a script: why we dream"
)

/** Director: chat (typing or voice). Runs on the phone; only MAKE IT uses the pod. */
@Composable
fun DirectorScreen(onOpenGenerate: () -> Unit = {}, onOpenSettings: () -> Unit = {}, onOpenScripts: () -> Unit = {}) {
    DirectorChat(onOpenGenerate, onOpenSettings, onOpenScripts)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DirectorChat(onOpenGenerate: () -> Unit, onOpenSettings: () -> Unit, onOpenScripts: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val prefs = remember { context.getSharedPreferences("creatorforge_director", 0) }

    val messages = remember { mutableStateListOf<Pair<String, String>>().apply { addAll(loadChat(prefs.getString("chat", null))) } }
    var draft by remember { mutableStateOf(Draft.from(prefs.getString("draft", null)?.let { runCatching { JSONObject(it) }.getOrNull() })) }
    var ready by remember { mutableStateOf(prefs.getBoolean("ready", false)) }
    var suggestions by remember { mutableStateOf<List<String>>(emptyList()) }
    var input by remember { mutableStateOf("") }
    var thinking by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    val list = rememberLazyListState()

    fun save() {
        prefs.edit().putString("chat", JSONArray().apply { messages.forEach { (r, c) -> put(JSONObject().put("r", r).put("c", c)) } }.toString())
            .putString("draft", draft.toJson().toString()).putBoolean("ready", ready).apply()
    }

    fun send(text: String) {
        val t = text.trim()
        if (t.isEmpty() || thinking) return
        messages.add("user" to t); input = ""; error = null; notice = null; thinking = true; suggestions = emptyList()
        save()
        scope.launch {
            runCatching { studio { StudioHub.brain(context).chat(messages.toList(), draft) } }.onSuccess { turn ->
                messages.add("assistant" to turn.reply); draft = turn.draft; ready = turn.ready; suggestions = turn.suggestions
            }.onFailure { error = it.message }
            thinking = false
            save()
            list.animateScrollToItem(messages.size)
        }
    }

    fun toLibrary(): SavedScript {
        val s = SavedScript(UUID.randomUUID().toString().take(12), draft.title.ifBlank { "Untitled" }, draft.script.ifBlank { draft.idea },
            draft.hook, style = draft.style, template = draft.template, source = "Director chat")
        StudioHub.scripts(context).upsert(s)
        return s
    }

    val voice = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { r ->
        if (r.resultCode == Activity.RESULT_OK) {
            val heard = r.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull().orEmpty()
            if (heard.isNotBlank()) send(heard)
        }
    }

    fun listen() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            .putExtra(RecognizerIntent.EXTRA_PROMPT, "Tell your Director about the video")
        try { voice.launch(intent) } catch (e: ActivityNotFoundException) { error = "No speech recogniser on this phone - install the Google app or type instead" }
    }

    Column(Modifier.fillMaxSize()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Talk it through. Tap 🎤 to speak.", color = Color.LightGray, fontSize = 13.sp, modifier = Modifier.weight(1f))
            if (messages.isNotEmpty()) TextButton({ messages.clear(); draft = Draft(); ready = false; suggestions = emptyList(); save() }) {
                Text("NEW CHAT", color = Gold, fontSize = 12.sp)
            }
        }
        LazyColumn(Modifier.weight(1f).fillMaxWidth(), state = list, verticalArrangement = Arrangement.spacedBy(8.dp),
            contentPadding = PaddingValues(vertical = 10.dp)) {
            item { AiBanner(onOpenSettings) }
            if (messages.isEmpty()) {
                item { Text("Try one of these, or say anything:", color = Dim, fontSize = 13.sp) }
                itemsIndexed(STARTERS) { _, s -> OutlinedButton({ send(s) }, modifier = Modifier.fillMaxWidth()) { Text(s, fontSize = 13.sp) } }
            }
            itemsIndexed(messages) { _, (role, text) ->
                val mine = role == "user"
                Row(Modifier.fillMaxWidth(), horizontalArrangement = if (mine) Arrangement.End else Arrangement.Start) {
                    Text(text, color = if (mine) Color.Black else Color.White, fontSize = 14.sp,
                        modifier = Modifier.widthIn(max = 300.dp).clip(RoundedCornerShape(14.dp))
                            .background(if (mine) Gold else Color(0xFF222222)).padding(12.dp))
                }
            }
            if (thinking) item { Text("Director is thinking…", color = Dim, fontSize = 12.sp) }
            error?.let { e -> item {
                Column {
                    Text(e, color = Danger, fontSize = 13.sp)
                    if ("Settings" in e || "key" in e) TextButton(onOpenSettings) { Text("OPEN SETTINGS", color = Gold) }
                }
            } }
            if (!draft.isEmpty) item { DraftCard(draft, ready, thinking,
                onMake = {
                    if (!StudioHub.hasWorker(context)) {
                        toLibrary(); notice = "Saved to Scripts. Making the video needs your pod (Settings → Video worker)."
                        return@DraftCard
                    }
                    thinking = true
                    scope.launch {
                        runCatching { ProductionClient(StudioHub.workerUrl(context)).createJson(ProductionBodies.fromDraft(draft, studioDefaults(context))) }
                            .onSuccess { p ->
                                context.getSharedPreferences("creatorforge_generate", 0).edit().putString("active", p.id).apply()
                                notice = "“${draft.title.ifBlank { "Your video" }}” is in production. Follow it in Generate."
                            }.onFailure { error = it.message }
                        thinking = false
                    }
                },
                onSave = { toLibrary(); notice = "Saved to Scripts" },
                onScenes = { toLibrary(); onOpenScripts() },
                onEdit = {
                    context.getSharedPreferences("creatorforge_generate", 0).edit()
                        .putString("idea", draft.script.ifBlank { draft.idea }).putBoolean("script_mode", draft.script.isNotBlank())
                        .putInt("duration", draft.durationS).putString("template", draft.template)
                        .putString("style", draft.style).putString("active", null).apply()
                    onOpenGenerate()
                }) }
            notice?.let { n -> item { Text(n, color = Gold) } }
        }
        if (suggestions.isNotEmpty()) Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            suggestions.forEach { s -> AssistChip(onClick = { send(s) }, label = { Text(s, fontSize = 12.sp) }) }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(input, { input = it }, Modifier.weight(1f), placeholder = { Text("Describe your video…") }, maxLines = 4)
            Spacer(Modifier.width(6.dp))
            FilledIconButton(onClick = { listen() }, enabled = !thinking) { Text("🎤") }
            Spacer(Modifier.width(4.dp))
            Button({ send(input) }, enabled = input.isNotBlank() && !thinking) { Text("SEND") }
        }
    }
}

@Composable
private fun DraftCard(d: Draft, ready: Boolean, busy: Boolean, onMake: () -> Unit, onSave: () -> Unit, onScenes: () -> Unit, onEdit: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A1A))) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(if (ready) "DRAFT • READY" else "DRAFT", color = Gold, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Text(d.title.ifBlank { "Untitled" }, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
            if (d.hook.isNotBlank()) Text("Hook: ${d.hook}", color = Gold, fontSize = 13.sp)
            val length = if (d.script.isNotBlank()) "${(d.script.split(Regex("\\s+")).size / 2.5).toInt()}s script" else "${d.durationS}s"
            Text("$length • ${Styles.templates.firstOrNull { it.first == d.template }?.second ?: d.template} • ${Styles.name(d.style)} • AI video: ${d.aiVideo}",
                color = Dim, fontSize = 12.sp)
            if (d.script.isNotBlank()) Text(d.script, color = Color.LightGray, fontSize = 13.sp, maxLines = 8)
            else if (d.idea.isNotBlank()) Text(d.idea, color = Color.LightGray, fontSize = 13.sp, maxLines = 5)
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedButton(onScenes, enabled = !busy) { Text("SCENES & PROMPTS", fontSize = 12.sp) }
                OutlinedButton(onSave, enabled = !busy) { Text("SAVE", fontSize = 12.sp) }
                Button(onMake, enabled = !busy) { Text("MAKE IT (POD)", fontSize = 12.sp) }
                TextButton(onEdit, enabled = !busy) { Text("EDIT IN GENERATE", color = Gold, fontSize = 12.sp) }
            }
        }
    }
}

private fun loadChat(raw: String?): List<Pair<String, String>> = runCatching {
    val a = JSONArray(raw ?: return emptyList())
    (0 until a.length()).map { a.getJSONObject(it).let { m -> m.getString("r") to m.getString("c") } }
}.getOrDefault(emptyList())
