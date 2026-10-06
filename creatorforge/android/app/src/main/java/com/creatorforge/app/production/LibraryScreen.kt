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
                Text("LIBRARY", color = Gold, fontSize = 30.sp)
                Text("Videos, voices, assets and characters on your worker", color = Color.LightGray)
                message?.let { Text(it, color = if (it.startsWith("Saved")) Gold else Danger, fontSize = 12.sp) }
                if (busy == "upload") LinearProgressIndicator(Modifier.fillMaxWidth())
            }
        }

        // ---- videos ----
        item { Section("VIDEOS") }
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
                    Text("${v.provider} • ${v.voice.substringAfterLast('/').ifBlank { "default" }} • speed ${v.speed}", color = Color.LightGray, fontSize = 12.sp)
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
        VoiceEditor(v, onDismiss = { voiceAdding = false; voiceEditing = null }) { name, provider, voice, speed ->
            voiceAdding = false; voiceEditing = null
            launchOp("save") { client.saveVoice(v?.id, name, provider, voice, speed) }
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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VoiceEditor(v: LibraryVoice?, onDismiss: () -> Unit, onSave: (String, String, String, Double) -> Unit) {
    var name by remember(v) { mutableStateOf(v?.name.orEmpty()) }
    var provider by remember(v) { mutableStateOf(v?.provider ?: "kokoro") }
    var voice by remember(v) { mutableStateOf(v?.voice.orEmpty()) }
    var speed by remember(v) { mutableFloatStateOf((v?.speed ?: 1.0).toFloat()) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (v == null) "New voice profile" else "Edit ${v.name}") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(name, { name = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Name (e.g. Deep documentary)") })
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    listOf("kokoro" to "Kokoro", "piper" to "Piper").forEach { (id, label) ->
                        FilterChip(selected = provider == id, onClick = { provider = id }, label = { Text(label) })
                    }
                }
                OutlinedTextField(voice, { voice = it }, Modifier.fillMaxWidth(), singleLine = true,
                    label = { Text(if (provider == "piper") "Model path on worker (.onnx)" else "Kokoro voice id (e.g. af_heart, am_michael)") })
                Text("Speed ${"%.2f".format(speed)}x", color = Color.LightGray, fontSize = 12.sp)
                Slider(speed, { speed = it }, valueRange = 0.5f..2f)
            }
        },
        confirmButton = {
            Button({ onSave(name.trim(), provider, voice.trim(), speed.toDouble()) }, enabled = name.isNotBlank() && voice.isNotBlank()) { Text("SAVE") }
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
