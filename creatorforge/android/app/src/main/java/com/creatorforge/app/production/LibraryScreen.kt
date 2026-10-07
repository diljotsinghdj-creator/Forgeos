package com.creatorforge.app.production

import android.content.Intent
import android.media.MediaPlayer
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.launch
import java.io.File

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val IMPORT_KINDS = listOf("image" to "image/*", "video" to "video/*", "audio" to "audio/*", "music" to "audio/*", "sfx" to "audio/*")

/** Media Library, Voice Profiles, Asset Library and Character Library - all stored on the worker. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibraryScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember {
        ProductionClient(context.getSharedPreferences("creatorforge_provider", 0).getString("base_url", "").orEmpty())
    }
    var videos by remember { mutableStateOf<List<LibraryVideo>>(emptyList()) }
    var characters by remember { mutableStateOf<List<LibraryCharacter>>(emptyList()) }
    var voices by remember { mutableStateOf<List<LibraryVoice>>(emptyList()) }
    var assets by remember { mutableStateOf<List<LibraryAsset>>(emptyList()) }
    var thumbs by remember { mutableStateOf<Map<String, File>>(emptyMap()) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf<String?>(null) }
    var editing by remember { mutableStateOf<LibraryCharacter?>(null) }
    var adding by remember { mutableStateOf(false) }
    var voiceEditing by remember { mutableStateOf<LibraryVoice?>(null) }
    var voiceAdding by remember { mutableStateOf(false) }
    var renaming by remember { mutableStateOf<Pair<String, String>?>(null) } // (kind:id, current name)
    var assetFilter by remember { mutableStateOf("") }
    var importKind by remember { mutableStateOf("image") }
    var refresh by remember { mutableIntStateOf(0) }
    var player by remember { mutableStateOf<MediaPlayer?>(null) }
    DisposableEffect(Unit) { onDispose { player?.release() } }

    LaunchedEffect(refresh) {
        runCatching { client.videos() }.onSuccess { videos = it }.onFailure { message = it.message }
        runCatching { client.characters() }.onSuccess { characters = it }
        runCatching { client.voices() }.onSuccess { voices = it }
        runCatching { client.assets() }.onSuccess { assets = it }
        val dir = File(context.cacheDir, "thumbs").apply { mkdirs() }
        videos.forEach { v ->
            val f = File(dir, "${v.id}.png")
            if (f.isFile || runCatching { client.fetch(v.thumbnailPath, f, ::isImage) }.isSuccess) thumbs = thumbs + (v.id to f)
        }
    }

    fun launchOp(label: String, block: suspend () -> Unit) {
        busy = label
        scope.launch {
            runCatching { block() }.onFailure { message = it.message }
            busy = null
            refresh++
        }
    }

    val importer = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri == null) return@rememberLauncherForActivityResult
        val name = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
            if (c.moveToFirst()) c.getString(0) else null
        } ?: "import"
        val kind = importKind
        launchOp("upload") {
            client.uploadAsset(kind, name) { context.contentResolver.openInputStream(uri) ?: error("Cannot read $name") }
            message = "Saved '$name' to the Asset Library"
        }
    }

    fun play(file: File) {
        player?.release()
        player = MediaPlayer().apply { setDataSource(file.absolutePath); prepare(); start() }
    }

    fun withVideo(v: LibraryVideo, action: (File) -> Unit) {
        val dest = File(context.getExternalFilesDir("Movies") ?: context.filesDir, "CreatorForge_${v.id}.mp4")
        if (dest.isFile && isMp4(dest)) return action(dest)
        busy = v.id
        scope.launch {
            runCatching { client.fetch(v.videoPath, dest, ::isMp4) }.onSuccess(action).onFailure { message = it.message }
            busy = null
        }
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp), contentPadding = PaddingValues(bottom = 32.dp)) {
        item {
            Column {
                Text("Videos, voices, assets and characters on your worker", color = Color.LightGray)
                message?.let { Text(it, color = if (it.startsWith("Sav") || it.startsWith("✓")) Gold else Danger, fontSize = 12.sp) }
                if (busy == "upload") LinearProgressIndicator(Modifier.fillMaxWidth())
            }
        }

        item { ProductionLine(client) { refresh++ } }

        // ---- videos ----
        item {
            Row {
                Section("VIDEOS")
                if (videos.isNotEmpty()) TextButton({
                    launchOp("saveall") {
                        val dir = context.getExternalFilesDir("Movies") ?: context.filesDir
                        videos.forEachIndexed { i, v ->
                            message = "Saving ${i + 1} of ${videos.size}…"
                            val dest = File(dir, "CreatorForge_${v.id}.mp4")
                            if (!(dest.isFile && isMp4(dest))) client.fetch(v.videoPath, dest, ::isMp4)
                            saveToGallery(context, dest)
                        }
                        message = "Saved all ${videos.size} videos to Movies/CreatorForge"
                    }
                }, enabled = busy == null) { Text(if (busy == "saveall") "SAVING…" else "SAVE ALL TO GALLERY") }
            }
        }
        if (videos.isEmpty()) item { Text("No finished videos yet.", color = Color.Gray) }
        items(videos, key = { "v" + it.id }) { v ->
            Card(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    thumbs[v.id]?.let { AsyncImage(model = it, contentDescription = v.title, modifier = Modifier.size(72.dp, 96.dp)) }
                    Column(Modifier.weight(1f)) {
                        Text(v.title, color = Color.White)
                        Text("${v.aspect} • ${"%.0f".format(v.durationS)}s", color = Color.Gray, fontSize = 12.sp)
                        Row(Modifier.horizontalScroll(rememberScrollState())) {
                            TextButton({ withVideo(v) { openVideo(context, it, Intent.ACTION_VIEW) } }, enabled = busy == null) {
                                Text(if (busy == v.id) "LOADING…" else "PLAY")
                            }
                            TextButton({ withVideo(v) { openVideo(context, it, Intent.ACTION_SEND) } }, enabled = busy == null) { Text("SHARE") }
                            TextButton({ withVideo(v) { message = saveToGallery(context, it) } }, enabled = busy == null) { Text("SAVE") }
                            TextButton({ renaming = "video:${v.id}" to v.title }) { Text("RENAME") }
                            TextButton({ launchOp("delete") { client.deleteProduction(v.id) } }) { Text("DELETE", color = Danger) }
                        }
                    }
                }
            }
        }

        // ---- voice profiles ----
        item {
            Row { Section("VOICE PROFILES"); TextButton({ voiceAdding = true }) { Text("+ ADD VOICE") } }
        }
        if (voices.isEmpty()) item { Text("No voices yet. Add a Piper or Kokoro voice installed on your worker.", color = Color.Gray, fontSize = 12.sp) }
        items(voices, key = { "voice" + it.id }) { v ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(v.name + if (v.builtin) "  • built-in" else "", color = Gold)
                    Text(if (v.provider == "chatterbox") "★ human-like • ${v.style.ifBlank { "natural" }}" + if (v.voice.startsWith("asset:")) " • your recording" else ""
                         else "${v.provider} • ${v.voice.substringAfterLast('/').ifBlank { "default" }} • speed ${v.speed}", color = Color.LightGray, fontSize = 12.sp)
                    Row {
                        TextButton({
                            launchOp("preview") {
                                val f = client.previewVoice(v.id, File(context.cacheDir, "preview_${v.id}.wav"))
                                play(f)
                            }
                        }, enabled = busy == null) { Text(if (busy == "preview") "LOADING…" else "PREVIEW") }
                        if (!v.builtin) {
                            TextButton({ voiceEditing = v }) { Text("EDIT") }
                            TextButton({ launchOp("delete") { client.deleteVoice(v.id) } }) { Text("DELETE", color = Danger) }
                        }
                    }
                }
            }
        }

        // ---- asset library ----
        item {
            Column {
                Section("ASSET LIBRARY")
                Text("Import your own images, clips, voice-overs, music and sound effects. Use them in any scene from the storyboard.",
                    color = Color.Gray, fontSize = 12.sp)
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    IMPORT_KINDS.forEach { (kind, mime) ->
                        OutlinedButton({ importKind = kind; importer.launch(arrayOf(mime)) }, enabled = busy == null) {
                            Text("+ ${kind.uppercase()}")
                        }
                    }
                }
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    (listOf("" to "All") + IMPORT_KINDS.map { it.first to it.first.replaceFirstChar(Char::uppercase) }).forEach { (k, label) ->
                        FilterChip(selected = assetFilter == k, onClick = { assetFilter = k }, label = { Text(label) })
                    }
                }
            }
        }
        val shown = assets.filter { assetFilter.isBlank() || it.kind == assetFilter }
        if (shown.isEmpty()) item { Text("Nothing here yet.", color = Color.Gray) }
        items(shown, key = { "a" + it.id }) { a ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(a.name, color = Color.White)
                    Text(a.kind + (a.durationS?.let { " • %.1fs".format(it) } ?: ""), color = Color.Gray, fontSize = 12.sp)
                    Row {
                        TextButton({ renaming = "asset:${a.id}" to a.name }) { Text("RENAME") }
                        TextButton({ launchOp("delete") { client.deleteAsset(a.id) } }) { Text("DELETE", color = Danger) }
                    }
                }
            }
        }

        // ---- characters ----
        item {
            Row { Section("CHARACTERS"); TextButton({ adding = true }) { Text("+ ADD CHARACTER") } }
        }
        if (characters.isEmpty()) item {
            Text("Save recurring characters once; pick them on the Generate screen and every scene that names them keeps the same look.",
                color = Color.Gray, fontSize = 12.sp)
        }
        items(characters, key = { "c" + it.id }) { c ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(c.name, color = Gold)
                    Text(c.description, color = Color.LightGray, fontSize = 13.sp)
                    Row {
                        TextButton({ editing = c }) { Text("EDIT") }
                        TextButton({ launchOp("delete") { client.deleteCharacter(c.id) } }) { Text("DELETE", color = Danger) }
                    }
                }
            }
        }
    }

    if (adding || editing != null) {
        val c = editing
        CharacterEditor(c, onDismiss = { adding = false; editing = null }) { name, description ->
            adding = false; editing = null
            launchOp("save") { client.saveCharacter(c?.id, name, description) }
        }
    }
    if (voiceAdding || voiceEditing != null) {
        val v = voiceEditing
        VoiceEditor(v, onDismiss = { voiceAdding = false; voiceEditing = null }) { d ->
            voiceAdding = false; voiceEditing = null
            launchOp("save") {
                val voice = d.sample?.let { uri ->
                    val ext = when (context.contentResolver.getType(uri).orEmpty()) {
                        "audio/mpeg" -> ".mp3"; "audio/ogg", "audio/opus" -> ".ogg"; "audio/wav", "audio/x-wav" -> ".wav"
                        "audio/aac" -> ".aac"; "audio/flac" -> ".flac"; else -> ".m4a"
                    }
                    "asset:" + client.uploadAsset("audio", "Voice sample - ${d.name}$ext") { context.contentResolver.openInputStream(uri)!! }
                } ?: d.voice
                client.saveVoice(v?.id, d.name, d.provider, voice, d.speed, d.style)
            }
        }
    }
    renaming?.let { (target, current) ->
        RenameDialog(current, onDismiss = { renaming = null }) { name ->
            renaming = null
            val (kind, id) = target.split(":", limit = 2)
            launchOp("rename") { if (kind == "video") client.renameProduction(id, name) else client.renameAsset(id, name) }
        }
    }
}

@Composable
private fun Section(t: String) { Text(t, color = Gold, fontSize = 12.sp, modifier = Modifier.padding(top = 14.dp)) }

@Composable
private fun RenameDialog(current: String, onDismiss: () -> Unit, onSave: (String) -> Unit) {
    var name by remember(current) { mutableStateOf(current) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Rename") },
        text = { OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), singleLine = true) },
        confirmButton = { Button({ onSave(name.trim()) }, enabled = name.isNotBlank()) { Text("SAVE") } },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } }
    )
}

private val HUMAN_BASES = listOf(
    "kokoro:am_onyx" to "Deep male", "kokoro:bm_george" to "British male", "kokoro:am_puck" to "Upbeat male",
    "kokoro:af_heart" to "Warm female", "kokoro:af_bella" to "Calm female", "default" to "Natural", "mine" to "🎙 My recording"
)
private val HUMAN_STYLES = listOf("documentary" to "Documentary", "natural" to "Natural", "calm" to "Calm", "energetic" to "Energetic")

/** Result of the voice editor. [sample] is a recording to upload first (its asset id becomes the voice). */
data class VoiceDraft(val name: String, val provider: String, val voice: String, val speed: Double, val style: String, val sample: android.net.Uri?)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VoiceEditor(v: LibraryVoice?, onDismiss: () -> Unit, onSave: (VoiceDraft) -> Unit) {
    var name by remember(v) { mutableStateOf(v?.name.orEmpty()) }
    var provider by remember(v) { mutableStateOf(v?.provider ?: "chatterbox") }
    var voice by remember(v) { mutableStateOf(v?.voice ?: "kokoro:am_onyx") }
    var speed by remember(v) { mutableFloatStateOf((v?.speed ?: 1.0).toFloat()) }
    var style by remember(v) { mutableStateOf(v?.style?.ifBlank { null } ?: "documentary") }
    var base by remember(v) { mutableStateOf(if (v?.voice?.startsWith("asset:") == true) "mine" else v?.voice?.takeIf { it.startsWith("kokoro:") || it == "default" } ?: "kokoro:am_onyx") }
    var sample by remember { mutableStateOf<android.net.Uri?>(null) }
    var consent by remember(v) { mutableStateOf(v?.voice?.startsWith("asset:") == true) }
    val pick = androidx.activity.compose.rememberLauncherForActivityResult(androidx.activity.result.contract.ActivityResultContracts.GetContent()) { u ->
        if (u != null) sample = u
    }
    val ready = name.isNotBlank() && when (provider) {
        "chatterbox" -> base != "mine" || (consent && (sample != null || v?.voice?.startsWith("asset:") == true))
        else -> voice.isNotBlank()
    }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (v == null) "New voice profile" else "Edit ${v.name}") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Name (e.g. Deep documentary)") })
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf("chatterbox" to "★ Human-like", "kokoro" to "Kokoro", "piper" to "Piper").forEach { (id, label) ->
                        FilterChip(selected = provider == id, onClick = { provider = id }, label = { Text(label) })
                    }
                }
                if (provider == "chatterbox") {
                    Text("Natural pauses, breathing and emotion. Runs on your pod.", color = Color.LightGray, fontSize = 12.sp)
                    Text("VOICE", color = Gold, fontSize = 11.sp)
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        HUMAN_BASES.forEach { (id, label) -> FilterChip(selected = base == id, onClick = { base = id }, label = { Text(label, fontSize = 12.sp) }) }
                    }
                    if (base == "mine") {
                        Text("Upload 10-30 seconds of clear speech, no music (your phone's voice recorder is fine).", color = Color.LightGray, fontSize = 12.sp)
                        OutlinedButton({ pick.launch("audio/*") }) { Text(if (sample != null) "✓ RECORDING PICKED - CHANGE" else "PICK RECORDING") }
                        Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                            Checkbox(consent, { consent = it })
                            Text("This is my own voice, or I have the speaker's permission. (Copying celebrities or other people without consent isn't allowed.)",
                                color = Color.LightGray, fontSize = 11.sp)
                        }
                    }
                    Text("DELIVERY", color = Gold, fontSize = 11.sp)
                    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        HUMAN_STYLES.forEach { (id, label) -> FilterChip(selected = style == id, onClick = { style = id }, label = { Text(label, fontSize = 12.sp) }) }
                    }
                } else {
                    OutlinedTextField(voice, { voice = it }, Modifier.fillMaxWidth(), singleLine = true,
                        label = { Text(if (provider == "piper") "Model path on worker (.onnx)" else "Kokoro voice id (e.g. af_heart, am_onyx, bm_fable)") })
                    Text("Speed ${"%.2f".format(speed)}x", color = Color.LightGray, fontSize = 12.sp)
                    Slider(speed, { speed = it }, valueRange = 0.5f..2f)
                }
            }
        },
        confirmButton = {
            Button({
                onSave(if (provider == "chatterbox")
                    VoiceDraft(name.trim(), provider, if (base == "mine") (v?.voice?.takeIf { sample == null && it.startsWith("asset:") } ?: "") else base,
                        1.0, style, if (base == "mine") sample else null)
                else VoiceDraft(name.trim(), provider, voice.trim(), speed.toDouble(), "", null))
            }, enabled = ready) { Text("SAVE") }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } }
    )
}

@Composable
private fun CharacterEditor(c: LibraryCharacter?, onDismiss: () -> Unit, onSave: (String, String) -> Unit) {
    var name by remember(c) { mutableStateOf(c?.name.orEmpty()) }
    var description by remember(c) { mutableStateOf(c?.description.orEmpty()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (c == null) "New character" else "Edit ${c.name}") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Name (used in scripts)") })
                OutlinedTextField(description, { description = it }, Modifier.fillMaxWidth(), minLines = 3,
                    label = { Text("Look: face, hair, clothing, colors, distinctive details") })
            }
        },
        confirmButton = {
            Button({ onSave(name.trim(), description.trim()) }, enabled = name.isNotBlank() && description.trim().length >= 5) { Text("SAVE") }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } }
    )
}
