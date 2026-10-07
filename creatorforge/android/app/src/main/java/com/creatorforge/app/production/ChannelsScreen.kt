package com.creatorforge.app.production

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
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
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)
private val Ok = Color(0xFF81C784)

private val NICHE_CHOICES = listOf(
    "all" to "Everything", "tech" to "Tech", "ai" to "AI", "money" to "Money", "business" to "Business", "crypto" to "Crypto",
    "science" to "Science", "history" to "History", "mystery" to "Mystery", "facts" to "Facts", "motivation" to "Motivation",
    "health" to "Health", "gaming" to "Gaming", "entertainment" to "Movies & TV", "sports" to "Sports", "custom" to "My keyword"
)
private val STYLE_CHOICES = listOf(
    "cinematic" to "Cinematic", "hyperreal" to "Hyper-real", "documentary" to "Documentary", "animated_3d" to "3D animated",
    "anime" to "Anime", "claymation" to "Claymation", "watercolor" to "Watercolor", "comic" to "Comic"
)

/** Channel Autopilot: one card per channel, a dated weekly plan built from trends, approve and make. */
@Composable
fun ChannelsScreen(onOpenSettings: () -> Unit = {}) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember { ProductionClient(context.getSharedPreferences("creatorforge_provider", 0).getString("base_url", "").orEmpty()) }
    var channels by remember { mutableStateOf<List<Channel>>(emptyList()) }
    var voices by remember { mutableStateOf<List<Choice>>(emptyList()) }
    var open by remember { mutableStateOf<String?>(null) }
    var editing by remember { mutableStateOf<Channel?>(null) }
    var adding by remember { mutableStateOf(false) }
    var slotEditing by remember { mutableStateOf<Pair<String, PlanSlot>?>(null) }
    var busy by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }

    fun replace(c: Channel) { channels = channels.map { if (it.id == c.id) c else it } }

    fun op(label: String, block: suspend () -> Unit) {
        busy = label; error = null; notice = null
        scope.launch { runCatching { block() }.onFailure { error = it.message }; busy = null }
    }

    LaunchedEffect(Unit) {
        runCatching { client.channels() }.onSuccess { channels = it; if (it.size == 1) open = it[0].id }.onFailure { error = it.message }
        runCatching { client.capabilities() }.onSuccess { voices = it.voices }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("CHANNELS", color = Gold, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text("Autopilot plans each week from what's trending in your niche.", color = Color.LightGray, fontSize = 13.sp)
                }
                Button({ adding = true }) { Text("+ CHANNEL") }
            }
        }
        error?.let { e -> item {
            Column {
                Text(e, color = Danger)
                if ("Settings" in e || "unreachable" in e) TextButton(onOpenSettings) { Text("OPEN SETTINGS", color = Gold) }
            }
        } }
        notice?.let { n -> item { Text(n, color = Gold) } }
        if (channels.isEmpty() && error == null) item {
            Text("No channels yet. Add one per faceless channel you run - for example \"Dark History\" (History, documentary look, deep voice, 7 Shorts a week).",
                color = Dim, fontSize = 13.sp)
        }

        items(channels, key = { it.id }) { ch ->
            val expanded = open == ch.id
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A1A))) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(ch.name, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                            Text("${NICHE_CHOICES.firstOrNull { it.first == ch.niche }?.second ?: ch.niche} • ${ch.perWeek}/week • ${ch.format} • " +
                                (STYLE_CHOICES.firstOrNull { it.first == ch.raw.optString("style") }?.second ?: ch.raw.optString("style")),
                                color = Dim, fontSize = 12.sp)
                        }
                        TextButton({ open = if (expanded) null else ch.id }) { Text(if (expanded) "HIDE" else "OPEN", color = Gold) }
                    }
                    if (expanded) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("Autopilot", color = Color.White)
                                Text("Queue approved videos the day before they're due, while the worker is on", color = Dim, fontSize = 11.sp)
                            }
                            Switch(ch.autoProduce, { on -> op("auto") { replace(client.saveChannel(ch.id, JSONObject().put("auto_produce", on))) } })
                        }
                        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Button({ op("plan:${ch.id}") { replace(client.planChannel(ch.id)); notice = "New weekly plan for ${ch.name} - approve the slots you like" } },
                                enabled = busy == null) { Text(if (busy == "plan:${ch.id}") "PLANNING…" else if (ch.slots.isEmpty()) "PLAN MY WEEK" else "RE-PLAN WEEK") }
                            OutlinedButton({ editing = ch }) { Text("EDIT") }
                            TextButton({ op("del") { client.deleteChannel(ch.id); channels = channels - ch } }) { Text("DELETE", color = Danger) }
                        }
                        if (busy == "plan:${ch.id}") Text("Scanning this week's trends and writing ideas…", color = Dim, fontSize = 12.sp)

                        if (ch.slots.isNotEmpty()) {
                            val open2 = ch.slots.filter { it.productionId.isBlank() && it.status != "skipped" }
                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                OutlinedButton(enabled = busy == null && open2.any { it.status == "planned" }, onClick = {
                                    op("approveall") { var c = ch; open2.filter { it.status == "planned" }.forEach { s -> c = client.editSlot(ch.id, s.id, JSONObject().put("status", "approved")) }; replace(c) }
                                }) { Text("APPROVE ALL", fontSize = 12.sp) }
                                val approved = open2.count { it.status == "approved" }
                                Button(enabled = busy == null && approved > 0, onClick = {
                                    op("make") { val (n, c) = client.producePlan(ch.id); replace(c); notice = "Queued $n video${if (n == 1) "" else "s"} - follow them in Library → Production Line" }
                                }) { Text("MAKE $approved NOW", fontSize = 12.sp) }
                            }
                            ch.slots.forEach { s -> SlotRow(s, busy == null,
                                onStatus = { st -> op("slot") { replace(client.editSlot(ch.id, s.id, JSONObject().put("status", st))) } },
                                onEdit = { slotEditing = ch.id to s }) }
                        }
                    }
                }
            }
        }
    }

    if (adding || editing != null) ChannelEditor(editing, voices, onDismiss = { adding = false; editing = null }) { body ->
        val id = editing?.id
        adding = false; editing = null
        op("save") {
            val c = client.saveChannel(id, body)
            channels = if (id == null) channels + c else channels.map { if (it.id == id) c else it }
            open = c.id
        }
    }
    slotEditing?.let { (cid, s) ->
        SlotEditor(s, onDismiss = { slotEditing = null }) { body ->
            slotEditing = null
            op("slot") { replace(client.editSlot(cid, s.id, body)) }
        }
    }
}

@Composable
private fun SlotRow(s: PlanSlot, enabled: Boolean, onStatus: (String) -> Unit, onEdit: () -> Unit) {
    val day = runCatching { LocalDate.parse(s.day).format(DateTimeFormatter.ofPattern("EEE d MMM", Locale.getDefault())) }.getOrDefault(s.day)
    val (label, color) = when {
        s.productionId.isNotBlank() -> "IN PRODUCTION" to Gold
        s.status == "approved" -> "APPROVED" to Ok
        s.status == "skipped" -> "SKIPPED" to Dim
        else -> "PLANNED" to Color.White
    }
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(Color(0xFF101010)).padding(10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("$day • ${s.time} • ${if (s.format == "long") "Long 16:9" else "Short 9:16"}", color = Dim, fontSize = 11.sp, modifier = Modifier.weight(1f))
            Text(label, color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }
        Text(s.title, color = if (s.status == "skipped") Dim else Color.White, fontWeight = FontWeight.SemiBold)
        if (s.hook.isNotBlank()) Text("Hook: ${s.hook}", color = Gold, fontSize = 12.sp)
        if (s.trendTitle.isNotBlank()) Text("Trend: ${s.trendTitle}", color = Dim, fontSize = 11.sp)
        if (s.productionId.isBlank()) Row {
            if (s.status != "approved") TextButton({ onStatus("approved") }, enabled = enabled) { Text("✓ APPROVE", color = Ok, fontSize = 12.sp) }
            if (s.status != "skipped") TextButton({ onStatus("skipped") }, enabled = enabled) { Text("SKIP", color = Dim, fontSize = 12.sp) }
            if (s.status != "planned") TextButton({ onStatus("planned") }, enabled = enabled) { Text("UNDO", color = Dim, fontSize = 12.sp) }
            TextButton(onEdit, enabled = enabled) { Text("✎ EDIT", color = Gold, fontSize = 12.sp) }
        }
    }
}

@Composable
private fun SlotEditor(s: PlanSlot, onDismiss: () -> Unit, onSave: (JSONObject) -> Unit) {
    var title by remember { mutableStateOf(s.title) }
    var hook by remember { mutableStateOf(s.hook) }
    var angle by remember { mutableStateOf(s.angle) }
    var script by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Edit slot") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(title, { title = it }, label = { Text("Title") })
                OutlinedTextField(hook, { hook = it }, label = { Text("Hook") })
                OutlinedTextField(angle, { angle = it }, label = { Text("Angle") }, minLines = 2)
                OutlinedTextField(script, { script = it }, label = { Text("Exact script (optional)") }, minLines = 3,
                    placeholder = { Text("Leave empty and the Director writes it") })
            }
        },
        confirmButton = { Button({ onSave(JSONObject().put("title", title).put("hook", hook).put("angle", angle).put("script", script)) }, enabled = title.isNotBlank()) { Text("SAVE") } },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } })
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChannelEditor(ch: Channel?, voices: List<Choice>, onDismiss: () -> Unit, onSave: (JSONObject) -> Unit) {
    val r = ch?.raw
    var name by remember { mutableStateOf(r?.optString("name").orEmpty()) }
    var niche by remember { mutableStateOf(r?.optString("niche") ?: "facts") }
    var keyword by remember { mutableStateOf(r?.optString("keyword").orEmpty()) }
    var region by remember { mutableStateOf(r?.optString("region") ?: "GB") }
    var format by remember { mutableStateOf(r?.optString("format") ?: "shorts") }
    var perWeek by remember { mutableFloatStateOf((r?.optInt("per_week", 7) ?: 7).toFloat()) }
    var style by remember { mutableStateOf(r?.optString("style") ?: "cinematic") }
    var voice by remember { mutableStateOf(r?.optString("voice") ?: voices.firstOrNull()?.id.orEmpty()) }
    var aiVideo by remember { mutableStateOf(r?.optString("ai_video") ?: "off") }
    var tone by remember { mutableStateOf(r?.optString("tone").orEmpty()) }
    var audience by remember { mutableStateOf(r?.optString("audience").orEmpty()) }
    var postTime by remember { mutableStateOf(r?.optString("post_time") ?: "18:00") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text(if (ch == null) "New channel" else "Edit ${ch.name}") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedTextField(name, { name = it }, label = { Text("Channel name") }, singleLine = true)
                Text("Niche", color = Gold, fontSize = 12.sp); Pick(NICHE_CHOICES, niche) { niche = it }
                if (niche == "custom") OutlinedTextField(keyword, { keyword = it }, label = { Text("Keyword") }, singleLine = true)
                Text("Country", color = Gold, fontSize = 12.sp); Pick(listOf("GB" to "UK", "US" to "US", "IN" to "India", "CA" to "Canada", "AU" to "Australia"), region) { region = it }
                Text("Format", color = Gold, fontSize = 12.sp); Pick(listOf("shorts" to "Shorts", "long" to "Long-form", "mixed" to "Mixed"), format) { format = it }
                Text("${perWeek.toInt()} videos a week", color = Gold, fontSize = 12.sp)
                Slider(perWeek, { perWeek = it }, valueRange = 1f..21f, steps = 19)
                Text("Look", color = Gold, fontSize = 12.sp); Pick(STYLE_CHOICES, style) { style = it }
                if (voices.isNotEmpty()) { Text("Voice", color = Gold, fontSize = 12.sp); Pick(voices.map { it.id to it.name }, voice) { voice = it } }
                Text("AI video", color = Gold, fontSize = 12.sp); Pick(listOf("off" to "Off (cheapest)", "hook" to "Hook only", "all" to "Every scene"), aiVideo) { aiVideo = it }
                OutlinedTextField(tone, { tone = it }, label = { Text("Tone (e.g. calm, mysterious)") }, singleLine = true)
                OutlinedTextField(audience, { audience = it }, label = { Text("Audience (e.g. UK students)") }, singleLine = true)
                OutlinedTextField(postTime, { postTime = it.take(5) }, label = { Text("Posting time (HH:MM)") }, singleLine = true)
            }
        },
        confirmButton = {
            Button({
                onSave(JSONObject().put("name", name.trim()).put("niche", niche).put("keyword", keyword.trim()).put("region", region)
                    .put("format", format).put("per_week", perWeek.toInt()).put("style", style).put("voice", voice).put("ai_video", aiVideo)
                    .put("tone", tone.trim()).put("audience", audience.trim()).put("post_time", postTime.trim()))
            }, enabled = name.trim().length >= 2 && (niche != "custom" || keyword.trim().length >= 2)) { Text("SAVE") }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } })
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Pick(options: List<Pair<String, String>>, selected: String, onSelect: (String) -> Unit) {
    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(4.dp)) {
        options.forEach { (id, label) -> FilterChip(selected = id == selected, onClick = { onSelect(id) }, label = { Text(label, fontSize = 12.sp) }) }
    }
}
