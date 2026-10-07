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
import com.creatorforge.app.studio.Channel
import com.creatorforge.app.studio.Niches
import com.creatorforge.app.studio.ProductionBodies
import com.creatorforge.app.studio.Regions
import com.creatorforge.app.studio.SavedScript
import com.creatorforge.app.studio.Slot
import com.creatorforge.app.studio.SourceException
import com.creatorforge.app.studio.Styles
import com.creatorforge.app.studio.Trend
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.UUID

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)
private val Ok = Color(0xFF81C784)

/** Channel Autopilot on the phone: weekly plans from trends, approve, write scripts. Only "MAKE" uses the pod. */
@Composable
fun ChannelsScreen(onOpenSettings: () -> Unit = {}) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.channels(context) }
    var channels by remember { mutableStateOf(store.list()) }
    var voices by remember { mutableStateOf<List<Choice>>(emptyList()) }
    var open by remember { mutableStateOf(channels.singleOrNull()?.id) }
    var editing by remember { mutableStateOf<Channel?>(null) }
    var adding by remember { mutableStateOf(false) }
    var slotEditing by remember { mutableStateOf<Pair<String, Slot>?>(null) }
    var busy by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }

    fun put(c: Channel) { channels = store.upsert(c) }
    fun setSlot(c: Channel, s: Slot) = c.copy(slots = c.slots.map { if (it.id == s.id) s else it }).also { put(it) }

    fun op(label: String, block: suspend () -> Unit) {
        busy = label; error = null; notice = null
        scope.launch { runCatching { block() }.onFailure { error = it.message }; busy = null }
    }

    LaunchedEffect(Unit) {
        if (StudioHub.hasWorker(context)) runCatching { ProductionClient(StudioHub.workerUrl(context)).capabilities() }.onSuccess { voices = it.voices }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("CHANNELS", color = Gold, fontSize = 28.sp, fontWeight = FontWeight.Bold)
                    Text("Weekly plans from what's trending in your niche. No pod needed to plan.", color = Color.LightGray, fontSize = 13.sp)
                }
                Button({ adding = true }) { Text("+ CHANNEL") }
            }
        }
        item { AiBanner(onOpenSettings) }
        error?.let { e -> item {
            Column {
                Text(e, color = Danger)
                if ("Settings" in e || "key" in e || "pod" in e) TextButton(onOpenSettings) { Text("OPEN SETTINGS", color = Gold) }
            }
        } }
        notice?.let { n -> item { Text(n, color = Gold) } }
        if (channels.isEmpty()) item {
            Text("No channels yet. Add one per faceless channel - for example \"Dark History\" (History, documentary look, 7 Shorts a week).",
                color = Dim, fontSize = 13.sp)
        }

        items(channels, key = { it.id }) { ch ->
            val expanded = open == ch.id
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1A1A1A))) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(ch.name, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                            Text("${Niches[ch.niche].name}${if (ch.niche == "custom") ": ${ch.keyword}" else ""} • ${ch.perWeek}/week • ${ch.format} • ${Styles.name(ch.style)}",
                                color = Dim, fontSize = 12.sp)
                        }
                        TextButton({ open = if (expanded) null else ch.id }) { Text(if (expanded) "HIDE" else "OPEN", color = Gold) }
                    }
                    if (expanded) {
                        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Button(enabled = busy == null, onClick = {
                                op("plan:${ch.id}") {
                                    val trends = studio {
                                        val radar = StudioHub.radar(context)
                                        val week = try { radar.scan("week", ch.niche, ch.region, ch.keyword).items } catch (e: SourceException) { emptyList<Trend>() }
                                        if (week.size >= 3) week else week + (try { radar.scan("year", ch.niche, ch.region, ch.keyword).items } catch (e: SourceException) { emptyList() })
                                    }
                                    val slots = studio { StudioHub.brain(context).plan(ch, trends) }
                                    put(ch.copy(slots = slots, plannedAt = System.currentTimeMillis()))
                                    notice = "New weekly plan for ${ch.name} - approve the slots you like"
                                }
                            }) { Text(if (busy == "plan:${ch.id}") "PLANNING…" else if (ch.slots.isEmpty()) "PLAN MY WEEK" else "RE-PLAN WEEK") }
                            OutlinedButton({ editing = ch }) { Text("EDIT") }
                            TextButton({ channels = store.delete(ch.id) }) { Text("DELETE", color = Danger) }
                        }
                        if (busy == "plan:${ch.id}") Text("Scanning this week's trends and writing ideas…", color = Dim, fontSize = 12.sp)

                        if (ch.slots.isNotEmpty()) {
                            val pending = ch.slots.filter { it.productionId.isBlank() && it.status != "skipped" }
                            val approved = pending.filter { it.status == "approved" }
                            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                OutlinedButton(enabled = busy == null && pending.any { it.status == "planned" }, onClick = {
                                    put(ch.copy(slots = ch.slots.map { if (it.status == "planned" && it.productionId.isBlank()) it.copy(status = "approved") else it }))
                                }) { Text("APPROVE ALL", fontSize = 12.sp) }
                                OutlinedButton(enabled = busy == null && approved.any { it.script.isBlank() }, onClick = {
                                    op("scripts") {
                                        var c = ch
                                        val todo = approved.filter { it.script.isBlank() }
                                        todo.forEachIndexed { i, s ->
                                            notice = "Writing script ${i + 1} of ${todo.size}…"
                                            val sc = studio { StudioHub.brain(context).script(s.trend, s.idea) }
                                            c = setSlot(c, s.copy(script = sc.text))
                                            StudioHub.scripts(context).upsert(SavedScript(UUID.randomUUID().toString().take(12), sc.title.ifBlank { s.idea.title }, sc.text,
                                                s.idea.hook, sc.description, sc.hashtags, ch.style, if (s.idea.format == "long") "youtube_longform" else "shorts_cinematic",
                                                source = "${ch.name} • ${s.day}"))
                                        }
                                        notice = "Wrote ${todo.size} script${if (todo.size == 1) "" else "s"} - also saved in Director → Scripts"
                                    }
                                }) { Text("WRITE SCRIPTS", fontSize = 12.sp) }
                                Button(enabled = busy == null && approved.isNotEmpty(), onClick = {
                                    if (!StudioHub.hasWorker(context)) { error = "Making videos needs your pod - set the Video worker in Settings when it's on."; return@Button }
                                    op("make") {
                                        val client = ProductionClient(StudioHub.workerUrl(context))
                                        var c = ch
                                        var n = 0
                                        for (s in approved) {
                                            val p = client.createJson(ProductionBodies.forChannel(ch, s, studioDefaults(context)))
                                            c = setSlot(c, s.copy(productionId = p.id, status = "queued")); n++
                                        }
                                        notice = "Queued $n video${if (n == 1) "" else "s"} - follow them in Library → Production Line"
                                    }
                                }) { Text("MAKE ${approved.size} (POD)", fontSize = 12.sp) }
                            }
                            ch.slots.forEach { s -> SlotRow(s, busy == null,
                                onStatus = { st -> setSlot(ch, s.copy(status = st)) },
                                onEdit = { slotEditing = ch.id to s }) }
                        }
                    }
                }
            }
        }
    }

    if (adding || editing != null) ChannelEditor(editing, voices, onDismiss = { adding = false; editing = null }) { c ->
        adding = false; editing = null
        put(c); open = c.id
    }
    slotEditing?.let { (cid, s) ->
        SlotEditor(s, onDismiss = { slotEditing = null }) { updated ->
            slotEditing = null
            channels.firstOrNull { it.id == cid }?.let { setSlot(it, updated) }
        }
    }
}

@Composable
private fun SlotRow(s: Slot, enabled: Boolean, onStatus: (String) -> Unit, onEdit: () -> Unit) {
    val day = runCatching { LocalDate.parse(s.day).format(DateTimeFormatter.ofPattern("EEE d MMM", Locale.getDefault())) }.getOrDefault(s.day)
    val (label, color) = when {
        s.productionId.isNotBlank() -> "IN PRODUCTION" to Gold
        s.status == "approved" -> (if (s.script.isNotBlank()) "APPROVED • SCRIPTED" else "APPROVED") to Ok
        s.status == "skipped" -> "SKIPPED" to Dim
        else -> "PLANNED" to Color.White
    }
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(Color(0xFF101010)).padding(10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("$day • ${s.time} • ${if (s.idea.format == "long") "Long 16:9" else "Short 9:16"}", color = Dim, fontSize = 11.sp, modifier = Modifier.weight(1f))
            Text(label, color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }
        Text(s.idea.title, color = if (s.status == "skipped") Dim else Color.White, fontWeight = FontWeight.SemiBold)
        if (s.idea.hook.isNotBlank()) Text("Hook: ${s.idea.hook}", color = Gold, fontSize = 12.sp)
        if (s.trend.title.isNotBlank()) Text("Trend: ${s.trend.title}", color = Dim, fontSize = 11.sp)
        if (s.script.isNotBlank()) Text(s.script, color = Color.LightGray, fontSize = 12.sp, maxLines = 3)
        if (s.productionId.isBlank()) Row {
            if (s.status != "approved") TextButton({ onStatus("approved") }, enabled = enabled) { Text("✓ APPROVE", color = Ok, fontSize = 12.sp) }
            if (s.status != "skipped") TextButton({ onStatus("skipped") }, enabled = enabled) { Text("SKIP", color = Dim, fontSize = 12.sp) }
            if (s.status != "planned") TextButton({ onStatus("planned") }, enabled = enabled) { Text("UNDO", color = Dim, fontSize = 12.sp) }
            TextButton(onEdit, enabled = enabled) { Text("✎ EDIT", color = Gold, fontSize = 12.sp) }
        }
    }
}

@Composable
private fun SlotEditor(s: Slot, onDismiss: () -> Unit, onSave: (Slot) -> Unit) {
    var title by remember { mutableStateOf(s.idea.title) }
    var hook by remember { mutableStateOf(s.idea.hook) }
    var angle by remember { mutableStateOf(s.idea.angle) }
    var script by remember { mutableStateOf(s.script) }
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
        confirmButton = { Button({ onSave(s.copy(idea = s.idea.copy(title = title.trim(), hook = hook.trim(), angle = angle.trim()), script = script.trim())) },
            enabled = title.isNotBlank()) { Text("SAVE") } },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } })
}

@Composable
private fun ChannelEditor(ch: Channel?, voices: List<Choice>, onDismiss: () -> Unit, onSave: (Channel) -> Unit) {
    var name by remember { mutableStateOf(ch?.name.orEmpty()) }
    var niche by remember { mutableStateOf(ch?.niche ?: "facts") }
    var keyword by remember { mutableStateOf(ch?.keyword.orEmpty()) }
    var region by remember { mutableStateOf(ch?.region ?: "GB") }
    var format by remember { mutableStateOf(ch?.format ?: "shorts") }
    var perWeek by remember { mutableFloatStateOf((ch?.perWeek ?: 7).toFloat()) }
    var style by remember { mutableStateOf(ch?.style ?: "cinematic") }
    var voice by remember { mutableStateOf(ch?.voice ?: voices.firstOrNull()?.id.orEmpty()) }
    var aiVideo by remember { mutableStateOf(ch?.aiVideo ?: "off") }
    var tone by remember { mutableStateOf(ch?.tone.orEmpty()) }
    var audience by remember { mutableStateOf(ch?.audience.orEmpty()) }
    var postTime by remember { mutableStateOf(ch?.postTime ?: "18:00") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text(if (ch == null) "New channel" else "Edit ${ch.name}") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                OutlinedTextField(name, { name = it }, label = { Text("Channel name") }, singleLine = true)
                Text("Niche", color = Gold, fontSize = 12.sp); Chips(Niches.all.map { it.id to it.name }, niche, small = true) { niche = it }
                if (niche == "custom") OutlinedTextField(keyword, { keyword = it }, label = { Text("Keyword") }, singleLine = true)
                Text("Country", color = Gold, fontSize = 12.sp); Chips(Regions.all.map { it.id to it.name }, region, small = true) { region = it }
                Text("Format", color = Gold, fontSize = 12.sp); Chips(listOf("shorts" to "Shorts", "long" to "Long-form", "mixed" to "Mixed"), format, small = true) { format = it }
                Text("${perWeek.toInt()} videos a week", color = Gold, fontSize = 12.sp)
                Slider(perWeek, { perWeek = it }, valueRange = 1f..21f, steps = 19)
                Text("Look", color = Gold, fontSize = 12.sp); Chips(Styles.presets.map { it.first to it.second }, style, small = true) { style = it }
                Text("Voice", color = Gold, fontSize = 12.sp)
                if (voices.isNotEmpty()) Chips(voices.map { it.id to it.name }, voice, small = true) { voice = it }
                else OutlinedTextField(voice, { voice = it }, label = { Text("Voice id (e.g. warm, deep) - optional") }, singleLine = true)
                Text("AI video", color = Gold, fontSize = 12.sp); Chips(listOf("off" to "Off (cheapest)", "hook" to "Hook only", "all" to "Every scene"), aiVideo, small = true) { aiVideo = it }
                OutlinedTextField(tone, { tone = it }, label = { Text("Tone (e.g. calm, mysterious)") }, singleLine = true)
                OutlinedTextField(audience, { audience = it }, label = { Text("Audience (e.g. UK students)") }, singleLine = true)
                OutlinedTextField(postTime, { postTime = it.take(5) }, label = { Text("Posting time (HH:MM)") }, singleLine = true)
            }
        },
        confirmButton = {
            Button({
                onSave((ch ?: Channel(UUID.randomUUID().toString().take(12), name.trim())).copy(name = name.trim(), niche = niche, keyword = keyword.trim(),
                    region = region, format = format, perWeek = perWeek.toInt(), style = style, voice = voice.trim(), aiVideo = aiVideo,
                    tone = tone.trim(), audience = audience.trim(), postTime = postTime.trim()))
            }, enabled = name.trim().length >= 2 && (niche != "custom" || keyword.trim().length >= 2)) { Text("SAVE") }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } })
}
