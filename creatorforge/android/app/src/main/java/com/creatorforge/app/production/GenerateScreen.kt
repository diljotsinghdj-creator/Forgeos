package com.creatorforge.app.production

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.MediaStore
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.File

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)

private val FALLBACK_TEMPLATES = listOf(
    Choice("shorts_cinematic", "Cinematic Short"), Choice("reels_punchy", "Punchy Reel / TikTok"),
    Choice("square_social", "Square Social Post"), Choice("explainer", "Clear Explainer"),
    Choice("youtube_longform", "YouTube Documentary")
)
private val FALLBACK_STYLES = listOf(
    Choice("hyperreal", "Hyper-realistic"), Choice("cinematic", "Cinematic film"), Choice("documentary", "Documentary"),
    Choice("animated_3d", "3D animated"), Choice("anime", "Anime"), Choice("claymation", "Claymation"),
    Choice("watercolor", "Watercolor"), Choice("comic", "Comic book")
)
private val STAGE_LABELS = mapOf(
    "director" to "AI Director • script & shots", "prompts" to "PromptForge", "images" to "Scene visuals",
    "review" to "Storyboard review", "narration" to "Narration", "clips" to "AI video clips", "captions" to "Captions", "music" to "Music", "assembly" to "Edit & render",
    "verify" to "Verify MP4"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GenerateScreen(onOpenSettings: () -> Unit = {}) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val worker = remember { context.getSharedPreferences("creatorforge_provider", 0) }
    val prefs = remember { context.getSharedPreferences("creatorforge_generate", 0) }
    val client = remember { ProductionClient(worker.getString("base_url", "").orEmpty()) }

    var caps by remember { mutableStateOf<Capabilities?>(null) }
    var capsError by remember { mutableStateOf<String?>(null) }
    var idea by remember { mutableStateOf(prefs.getString("idea", "").orEmpty()) }
    var duration by remember { mutableIntStateOf(prefs.getInt("duration", 45)) }
    var aspect by remember { mutableStateOf(prefs.getString("aspect", "9:16").orEmpty()) }
    var template by remember { mutableStateOf(prefs.getString("template", "shorts_cinematic").orEmpty()) }
    var voice by remember { mutableStateOf(prefs.getString("voice", "").orEmpty()) }
    var pacing by remember { mutableStateOf(prefs.getString("pacing", "medium").orEmpty()) }
    var music by remember { mutableStateOf(prefs.getBoolean("music", true)) }
    var captions by remember { mutableStateOf(prefs.getBoolean("captions", true)) }
    var director by remember { mutableStateOf(false) }
    var style by remember { mutableStateOf(prefs.getString("style", "").orEmpty()) }
    var customLook by remember { mutableStateOf(style.isNotBlank() && FALLBACK_STYLES.none { it.id == style }) }
    var mood by remember { mutableStateOf(prefs.getString("mood", "").orEmpty()) }
    var camera by remember { mutableStateOf(prefs.getString("camera", "").orEmpty()) }
    var characters by remember { mutableStateOf(prefs.getString("characters", "").orEmpty()) }
    var videoScope by remember { mutableStateOf(prefs.getString("video_scope", null) ?: if (prefs.getBoolean("ai_video", false)) "all" else "off") }
    val aiVideo = videoScope != "off"
    var review by remember { mutableStateOf(prefs.getBoolean("review", false)) }
    var editing by remember { mutableStateOf<SceneView?>(null) }
    var autoEdit by remember { mutableStateOf(prefs.getBoolean("auto_edit", true)) }
    var library by remember { mutableStateOf<List<LibraryCharacter>>(emptyList()) }
    var picked by remember { mutableStateOf(prefs.getStringSet("character_ids", emptySet())!!.toSet()) }
    var scriptMode by remember { mutableStateOf(prefs.getBoolean("script_mode", false)) }
    var sfx by remember { mutableStateOf(prefs.getBoolean("sfx", true)) }
    var musicAsset by remember { mutableStateOf(prefs.getString("music_asset", "").orEmpty()) }
    var assets by remember { mutableStateOf<List<LibraryAsset>>(emptyList()) }
    var pickingFor by remember { mutableStateOf<Int?>(null) }
    var editingTimeline by remember { mutableStateOf(false) }

    var activeId by remember { mutableStateOf(prefs.getString("active", null)) }
    var production by remember { mutableStateOf<ProductionView?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var pollKey by remember { mutableIntStateOf(0) }
    var busy by remember { mutableStateOf(false) }
    var recent by remember { mutableStateOf<List<ProductionSummary>>(emptyList()) }
    var videoFile by remember { mutableStateOf<File?>(null) }
    var storyboardVersion by remember { mutableIntStateOf(0) }

    LaunchedEffect(Unit) {
        runCatching { client.capabilities() }.onSuccess { c ->
            caps = c
            if (voice.isBlank() || c.voices.none { it.id == voice }) voice = c.voices.firstOrNull()?.id.orEmpty()
        }.onFailure { capsError = it.message }
        runCatching { client.list() }.onSuccess { recent = it }
        runCatching { client.characters() }.onSuccess { cs -> library = cs; picked = picked.filter { id -> cs.any { it.id == id } }.toSet() }
        runCatching { client.assets() }.onSuccess { a -> assets = a; if (a.none { it.id == musicAsset }) musicAsset = "" }
    }

    // Poll the active production until it reaches a terminal state, then fetch the verified MP4.
    LaunchedEffect(activeId, pollKey) {
        val id = activeId ?: return@LaunchedEffect
        videoFile = null
        while (true) {
            val p = runCatching { client.get(id) }.onFailure { error = it.message }.getOrNull()
            if (p != null) {
                production = p
                error = null
                syncStoryboard(context, client, p) { storyboardVersion++ }
                if (p.status == "READY") {
                    val dest = File(context.getExternalFilesDir("Movies") ?: context.filesDir, "CreatorForge_${p.id}.mp4")
                    videoFile = if (dest.isFile && isMp4(dest)) dest else
                        runCatching { client.fetch("/v1/productions/${p.id}/video", dest, ::isMp4) }
                            .onFailure { error = it.message }.getOrNull()
                }
                if (p.terminal || p.inReview) break
            }
            delay(2000)
        }
        runCatching { client.list() }.onSuccess { recent = it }
    }

    fun setActive(id: String?) {
        activeId = id
        production = null
        prefs.edit().putString("active", id).apply()
    }

    fun act(block: suspend () -> ProductionView) {
        busy = true
        notice = null
        scope.launch {
            runCatching { block() }.onSuccess { p ->
                production = p
                error = null
                if (activeId != p.id) { activeId = p.id; prefs.edit().putString("active", p.id).apply() }
                if (!p.terminal) pollKey++ // (re)start polling after create / retry / regenerate
            }.onFailure { error = it.message }
            busy = false
        }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
        item { Column {
            Text("GENERATE VIDEO", color = Gold, fontSize = 30.sp)
            Text("One idea in. One verified MP4 out.", color = Color.LightGray)
            caps?.let { c ->
                if (!c.productionReady) Text("Worker not fully configured:\n" + c.problems.joinToString("\n"), color = Danger, fontSize = 12.sp)
            }
        } }
        capsError?.let { err ->
            item {
                Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("CONNECT YOUR WORKER", color = Gold, fontSize = 12.sp)
                    Text(err, color = Danger, fontSize = 13.sp)
                    Text("CreatorForge's AI runs on a computer you control (the worker); this phone is the studio controller. " +
                        "To try it right now without AI models, on a computer on the same Wi-Fi run:", color = Color.LightGray, fontSize = 13.sp)
                    Text("cd creatorforge/worker\npip install -e .\npython run_demo.py", color = Color.White, fontSize = 13.sp,
                        fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
                    Text("Then enter the address it prints (http://192.168.x.x:8765) in Settings and tap TEST CONNECTION.",
                        color = Color.LightGray, fontSize = 13.sp)
                    Button(onOpenSettings) { Text("OPEN SETTINGS") }
                }}
            }
        }

        production?.let { p ->
            item {
                ProductionCard(p, videoFile, busy,
                    onCancel = { act { client.cancel(p.id) } },
                    onRetry = { act { client.retry(p.id) } },
                    onApprove = { act { client.approve(p.id) } },
                    onEditTimeline = { editingTimeline = true },
                    onNew = { setActive(null) },
                    onPlay = { f -> openVideo(context, f, Intent.ACTION_VIEW) },
                    onShare = { f -> openVideo(context, f, Intent.ACTION_SEND) },
                    onSave = { f -> notice = saveToGallery(context, f) },
                    onDownload = { pollKey++ })
            }
            if (p.scenes.isNotEmpty()) item {
                key(storyboardVersion) { Storyboard(context, p, busy || !(p.terminal || p.inReview),
                    onEdit = { s -> editing = s },
                    onUseAsset = { i -> scope.launch { runCatching { client.assets() }.onSuccess { assets = it } }; pickingFor = i },
                    onRegenerate = { i ->
                        storyboardFile(context, p.id, i).delete()
                        act { client.regenerateScene(p.id, i) }
                    }) }
            }
        }
        if (production == null && activeId != null) item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Loading production…", color = Color.LightGray, modifier = Modifier.padding(top = 12.dp))
                OutlinedButton({ setActive(null) }) { Text("NEW VIDEO") }
            }
        }
        if (editingTimeline) production?.let { p ->
            item {
                TimelineEditor(p, onDismiss = { editingTimeline = false }) { body ->
                    editingTimeline = false
                    act { client.editTimeline(p.id, body) }
                }
            }
        }
        pickingFor?.let { i ->
            item {
                AssetPicker(assets, i + 1, onDismiss = { pickingFor = null }) { a ->
                    val pid = production?.id ?: return@AssetPicker
                    pickingFor = null
                    storyboardFile(context, pid, i).delete()
                    act { client.useAsset(pid, i, a.id) }
                }
            }
        }
        editing?.let { s ->
            item {
                SceneEditor(s, onDismiss = { editing = null }) { narration, visual ->
                    val pid = production?.id ?: return@SceneEditor
                    editing = null
                    if (visual != s.visual) storyboardFile(context, pid, s.index).delete()
                    act { client.editScene(pid, s.index, narration, visual) }
                }
            }
        }
        error?.let { item { Text(it, color = Danger) } }
        notice?.let { item { Text(it, color = Gold) } }

        if (production == null && activeId == null) {
            item {
                Column {
                    ChipRow(listOf("idea" to "From an idea", "script" to "From my script"), if (scriptMode) "script" else "idea") { scriptMode = it == "script" }
                    OutlinedTextField(idea, { idea = it }, Modifier.fillMaxWidth(), minLines = if (scriptMode) 8 else 4,
                        label = { Text(if (scriptMode) "Your script - narrated word for word" else "Your idea") },
                        placeholder = { Text(if (scriptMode) "Paste the exact narration. CreatorForge splits it into scenes and builds visuals, captions and the edit around your words."
                            else "A 45-second cinematic short explaining how humanoid robots could change warehouses") })
                }
            }
            item { Column {
                if (scriptMode) Text("Length follows your script (about ${(idea.split(Regex("\\s+")).count { it.isNotBlank() } / 2.5).toInt()}s).",
                    color = Color.Gray, fontSize = 12.sp)
                else {
                    Label("LENGTH")
                    ChipRow(listOf(15, 30, 45, 60, 90, 180).map { "$it" to "${it}s" }, "$duration") { duration = it.toInt() }
                }
                Label("FORMAT")
                ChipRow(listOf("9:16" to "9:16 Shorts", "16:9" to "16:9 YouTube", "1:1" to "1:1 Square"), aspect) { aspect = it }
                Label("TEMPLATE")
                ChipRow((caps?.templates ?: FALLBACK_TEMPLATES).map { it.id to it.name }, template) { template = it }
                caps?.voices?.takeIf { it.isNotEmpty() }?.let { vs ->
                    Label("VOICE"); ChipRow(vs.map { it.id to it.name }, voice) { voice = it }
                }
                if (library.isNotEmpty()) {
                    Label("CHARACTERS (LIBRARY)")
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        library.forEach { ch ->
                            FilterChip(selected = ch.id in picked, onClick = { picked = if (ch.id in picked) picked - ch.id else picked + ch.id },
                                label = { Text(ch.name) })
                        }
                    }
                }
                Label("PACING")
                ChipRow(listOf("slow" to "Slow", "medium" to "Medium", "fast" to "Fast"), pacing) { pacing = it }
                Label("REALISTIC AI VIDEO")
                if (caps?.aiVideo == false) Text("No video model on this worker - scenes use AI images with camera motion.", color = Color.Gray, fontSize = 12.sp)
                else {
                    ChipRow(listOf("off" to "Off", "hook" to "Hook only (cheap)", "all" to "Every scene"), videoScope) { videoScope = it }
                    Text(when (videoScope) {
                        "hook" -> "The opening shot is animated with AI video; the rest use AI images + camera motion."
                        "all" -> "Every scene animated - most realistic, several minutes of GPU per scene."
                        else -> "AI images with camera motion - fastest and cheapest."
                    }, color = Color.Gray, fontSize = 12.sp)
                }
                Row { Switch(autoEdit, { autoEdit = it }); Text(" Auto Edit (AI picks transitions, emphasis, pauses)", Modifier.padding(top = 12.dp)) }
                Row { Switch(review, { review = it }); Text(" Review storyboard before render", Modifier.padding(top = 12.dp)) }
                val tracks = assets.filter { it.kind == "music" }
                if (music && tracks.isNotEmpty()) {
                    Label("MUSIC")
                    ChipRow(listOf("" to "Auto") + tracks.map { it.id to it.name }, musicAsset) { musicAsset = it }
                }
                Row { Switch(sfx, { sfx = it }); Text(" Sound effects (whooshes, hits, pops)", Modifier.padding(top = 12.dp)) }
                Row { Switch(music, { music = it }); Text(" Music", Modifier.padding(top = 12.dp, end = 16.dp)); Switch(captions, { captions = it }); Text(" Captions", Modifier.padding(top = 12.dp)) }
                TextButton({ director = !director }) { Text(if (director) "▾ Director Mode" else "▸ Director Mode", color = Gold) }
                if (director) {
                    val presets = caps?.styles?.takeIf { it.isNotEmpty() } ?: FALLBACK_STYLES
                    Label("LOOK")
                    ChipRow(listOf("" to "Template") + presets.map { it.id to it.name } + listOf("__custom" to "Custom…"),
                        if (customLook) "__custom" else style) { choice ->
                        customLook = choice == "__custom"
                        style = if (customLook) "" else choice
                    }
                    if (customLook) OutlinedTextField(style, { style = it }, Modifier.fillMaxWidth(), label = { Text("Describe the look") })
                    OutlinedTextField(mood, { mood = it }, Modifier.fillMaxWidth(), label = { Text("Mood") })
                    OutlinedTextField(camera, { camera = it }, Modifier.fillMaxWidth(), label = { Text("Camera direction") })
                    OutlinedTextField(characters, { characters = it }, Modifier.fillMaxWidth(), minLines = 2,
                        label = { Text("Characters - one per line: Name: description") })
                }
            } }
            item {
                Button(enabled = idea.trim().length >= 5 && !busy, modifier = Modifier.fillMaxWidth().height(56.dp), onClick = {
                    prefs.edit().putString("idea", idea).putInt("duration", duration).putString("aspect", aspect)
                        .putString("template", template).putString("voice", voice).putString("pacing", pacing)
                        .putBoolean("music", music).putBoolean("captions", captions).putString("style", style)
                        .putString("mood", mood).putString("camera", camera).putString("characters", characters)
                        .putString("video_scope", videoScope).putBoolean("review", review)
                        .putBoolean("auto_edit", autoEdit).putStringSet("character_ids", picked)
                        .putBoolean("script_mode", scriptMode).putBoolean("sfx", sfx).putString("music_asset", musicAsset).apply()
                    val chars = characters.lines().mapNotNull { l ->
                        val i = l.indexOf(':'); if (i > 0) l.substring(0, i).trim() to l.substring(i + 1).trim() else null
                    }.filter { it.first.isNotBlank() && it.second.isNotBlank() }
                    fun request(text: String) = ProductionRequest(if (scriptMode) "" else text, duration, aspect, template, voice, pacing,
                        style.trim(), mood.trim(), camera.trim(), chars, music, captions, aiVideo, review, autoEdit, picked.toList(),
                        script = if (scriptMode) text else "", musicAssetId = if (music) musicAsset else "", sfx = sfx,
                        aiVideoScenes = if (videoScope == "hook") "hook" else "all")
                    val pieces = batchPieces(idea)
                    if (pieces.size <= 1) act { client.create(request(idea.trim())) }
                    else {
                        busy = true
                        scope.launch {
                            var ok = 0
                            pieces.forEachIndexed { i, text ->
                                notice = "Queuing ${i + 1} of ${pieces.size}…"
                                runCatching { client.create(request(text)) }.onSuccess { ok++ }.onFailure { error = "Video ${i + 1}: ${it.message}" }
                            }
                            notice = "Queued $ok of ${pieces.size} videos. The worker makes them one after another - leave the pod running and check Library."
                            runCatching { client.list() }.onSuccess { recent = it }
                            busy = false
                        }
                    }
                }) {
                    val n = batchPieces(idea).size
                    Text(if (busy) "STARTING…" else if (n > 1) "GENERATE $n VIDEOS" else "GENERATE VIDEO", fontSize = 18.sp)
                }
                Text("Batch: put a line with --- between ideas or scripts to queue many videos with the same settings.",
                    color = Color.Gray, fontSize = 12.sp)
            }
            if (recent.isNotEmpty()) {
                item { Label("RECENT PRODUCTIONS") }
                recent.take(10).forEach { r ->
                    item {
                        OutlinedButton({ setActive(r.id) }, Modifier.fillMaxWidth()) {
                            Text("${r.title.take(40)}  •  ${r.status}${if (r.status == "RUNNING") " ${(r.progress * 100).toInt()}%" else ""}")
                        }
                    }
                }
            }
        }
    }
}

/** Splits a batch on lines containing only dashes; every piece becomes its own production. */
private fun batchPieces(text: String): List<String> =
    text.split(Regex("\\n\\s*-{3,}\\s*(\\n|$)")).map { it.trim() }.filter { it.length >= 5 }

@Composable
private fun Label(t: String) { Spacer(Modifier.height(8.dp)); Text(t, color = Gold, fontSize = 12.sp) }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChipRow(options: List<Pair<String, String>>, selected: String, onSelect: (String) -> Unit) {
    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        options.forEach { (id, label) -> FilterChip(selected = id == selected, onClick = { onSelect(id) }, label = { Text(label) }) }
    }
}

@Composable
private fun ProductionCard(
    p: ProductionView, video: File?, busy: Boolean, onCancel: () -> Unit, onRetry: () -> Unit, onApprove: () -> Unit,
    onEditTimeline: () -> Unit, onNew: () -> Unit,
    onPlay: (File) -> Unit, onShare: (File) -> Unit, onSave: (File) -> Unit, onDownload: () -> Unit
) {
    Card { Column(Modifier.padding(16.dp)) {
        Text(p.title.ifBlank { "New production" }, color = Gold, fontSize = 20.sp)
        if (p.hook.isNotBlank()) Text("Hook: ${p.hook}", color = Color.LightGray, fontSize = 13.sp)
        Text("${p.status} • ${p.message}", color = when (p.status) { "READY", "REVIEW" -> Gold; "FAILED" -> Danger; else -> Color.White })
        Spacer(Modifier.height(8.dp))
        LinearProgressIndicator(progress = { p.progress }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        p.stages.forEach { s ->
            val mark = when (s.state) { "READY" -> "✓"; "SKIPPED" -> "–"; "RUNNING" -> "●"; "FAILED" -> "✗"; "WAITING" -> "⏸"; else -> "○" }
            val count = if (s.total > 0 && s.state == "RUNNING") " ${s.done}/${s.total}" else ""
            Text("$mark ${STAGE_LABELS[s.name] ?: s.name}$count", fontSize = 13.sp,
                color = when (s.state) { "READY" -> Gold; "FAILED" -> Danger; "RUNNING" -> Color.White; else -> Color.Gray })
            s.error?.let { Text("   $it", color = Danger, fontSize = 11.sp) }
        }
        p.verification?.let { Spacer(Modifier.height(6.dp)); Text("Verified: $it", color = Gold, fontSize = 12.sp) }
        if (p.providers.isNotEmpty()) Text(p.providers.entries.joinToString(" • ") { "${it.key}: ${it.value}" }, color = Color.Gray, fontSize = 11.sp)
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (p.inReview) Button(onApprove, enabled = !busy) { Text("APPROVE & RENDER") }
            if (!p.terminal) OutlinedButton(onCancel, enabled = !busy) { Text("CANCEL") }
            if (p.status == "FAILED" || p.status == "CANCELLED") Button(onRetry, enabled = !busy) { Text("RETRY / RESUME") }
            if (p.terminal) OutlinedButton(onNew) { Text("NEW VIDEO") }
        }
        if ((p.terminal || p.inReview) && p.scenes.isNotEmpty() && p.scenes.all { it.narrationS != null }) {
            OutlinedButton(onEditTimeline, enabled = !busy) { Text("EDIT TIMELINE") }
        }
        if (p.status == "READY") {
            if (video == null) OutlinedButton(onDownload) { Text("DOWNLOAD MP4") }
            else Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button({ onPlay(video) }) { Text("PLAY") }
                OutlinedButton({ onShare(video) }) { Text("SHARE") }
                OutlinedButton({ onSave(video) }) { Text("SAVE") }
            }
        }
    } }
}

@Composable
private fun Storyboard(context: Context, p: ProductionView, locked: Boolean, onEdit: (SceneView) -> Unit,
                       onUseAsset: (Int) -> Unit, onRegenerate: (Int) -> Unit) {
    Column {
        Label("STORYBOARD")
        p.scenes.forEach { s ->
            Card(Modifier.fillMaxWidth().padding(vertical = 4.dp)) { Column(Modifier.padding(12.dp)) {
                Text("Scene ${s.index + 1} • visual ${s.imageState} • voice ${s.voiceState}" +
                    if (s.clipState.isNotBlank() && s.clipState != "PLANNED" && s.clipState != "null") " • clip ${s.clipState}" else "",
                    color = Gold, fontSize = 12.sp)
                val f = storyboardFile(context, p.id, s.index)
                if (f.isFile) AsyncImage(model = f, contentDescription = "Scene ${s.index + 1}", modifier = Modifier.fillMaxWidth().height(200.dp))
                if (s.narration.isNotBlank()) Text("“${s.narration}”", color = Color.LightGray, fontSize = 13.sp)
                s.error?.let { Text(it, color = Danger, fontSize = 11.sp) }
                if (s.visual.isNotBlank()) Text("Visual: ${s.visual}", color = Color.Gray, fontSize = 12.sp)
                Row(Modifier.horizontalScroll(rememberScrollState())) {
                    if (s.hasImage) TextButton({ onRegenerate(s.index) }, enabled = !locked) { Text("REGENERATE VISUAL") }
                    TextButton({ onEdit(s) }, enabled = !locked) { Text("EDIT SCENE") }
                    TextButton({ onUseAsset(s.index) }, enabled = !locked) { Text("USE ASSET") }
                }
            } }
        }
    }
}

@Composable
private fun SceneEditor(scene: SceneView, onDismiss: () -> Unit, onSave: (String, String) -> Unit) {
    var narration by remember(scene) { mutableStateOf(scene.narration) }
    var visual by remember(scene) { mutableStateOf(scene.visual) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Edit scene ${scene.index + 1}") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(narration, { narration = it }, Modifier.fillMaxWidth(), minLines = 3, label = { Text("Narration") })
                OutlinedTextField(visual, { visual = it }, Modifier.fillMaxWidth(), minLines = 3, label = { Text("Visual") })
                Text("Only what you change is regenerated. Approve afterwards to render.", fontSize = 12.sp, color = Color.Gray)
            }
        },
        confirmButton = { Button({ onSave(narration.trim(), visual.trim()) }, enabled = narration.isNotBlank() && visual.isNotBlank()) { Text("SAVE") } },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } }
    )
}

private fun storyboardFile(context: Context, id: String, index: Int) =
    File(File(context.cacheDir, "storyboard").apply { mkdirs() }, "${id}_$index.png")

private suspend fun syncStoryboard(context: Context, client: ProductionClient, p: ProductionView, changed: () -> Unit) {
    var any = false
    p.scenes.filter { it.hasImage && it.imageState == "READY" }.forEach { s ->
        val f = storyboardFile(context, p.id, s.index)
        if (!f.isFile && runCatching { client.fetch("/v1/productions/${p.id}/scenes/${s.index}/image", f, ::isImage) }.isSuccess) any = true
    }
    if (any) changed()
}

internal fun openVideo(context: Context, file: File, action: String) {
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
    val intent = Intent(action).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    if (action == Intent.ACTION_SEND) intent.setType("video/mp4").putExtra(Intent.EXTRA_STREAM, uri)
    else intent.setDataAndType(uri, "video/mp4")
    context.startActivity(Intent.createChooser(intent, null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
}

/** Copies the MP4 into the shared Movies/CreatorForge folder. Returns an error message or null. */
internal fun saveToGallery(context: Context, file: File): String? {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return "Kept in app storage: ${file.absolutePath} (use SHARE to export on this Android version)"
    return runCatching {
        val values = ContentValues().apply {
            put(MediaStore.Video.Media.DISPLAY_NAME, file.name)
            put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
            put(MediaStore.Video.Media.RELATIVE_PATH, "Movies/CreatorForge")
        }
        val uri = context.contentResolver.insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values) ?: error("MediaStore refused the file")
        context.contentResolver.openOutputStream(uri)!!.use { out -> file.inputStream().use { it.copyTo(out) } }
        "Saved to Movies/CreatorForge"
    }.getOrElse { "Save failed: ${it.message}" }
}
