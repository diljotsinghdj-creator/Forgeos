package com.creatorforge.app.production

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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

/** Media Library (finished, verified videos) and Character Library, both stored on the worker. */
@Composable
fun LibraryScreen() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember {
        ProductionClient(context.getSharedPreferences("creatorforge_provider", 0).getString("base_url", "").orEmpty())
    }
    var videos by remember { mutableStateOf<List<LibraryVideo>>(emptyList()) }
    var characters by remember { mutableStateOf<List<LibraryCharacter>>(emptyList()) }
    var thumbs by remember { mutableStateOf<Map<String, File>>(emptyMap()) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf<String?>(null) }
    var editing by remember { mutableStateOf<LibraryCharacter?>(null) }
    var adding by remember { mutableStateOf(false) }
    var refresh by remember { mutableIntStateOf(0) }

    LaunchedEffect(refresh) {
        runCatching { client.videos() }.onSuccess { videos = it }.onFailure { message = it.message }
        runCatching { client.characters() }.onSuccess { characters = it }
        val dir = File(context.cacheDir, "thumbs").apply { mkdirs() }
        videos.forEach { v ->
            val f = File(dir, "${v.id}.png")
            if (f.isFile || runCatching { client.fetch(v.thumbnailPath, f, ::isImage) }.isSuccess) thumbs = thumbs + (v.id to f)
        }
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
                Text("Finished videos and reusable characters on your worker", color = Color.LightGray)
                message?.let { Text(it, color = if (it.startsWith("Saved")) Gold else Danger, fontSize = 12.sp) }
            }
        }
        item { Text("VIDEOS", color = Gold, fontSize = 12.sp) }
        if (videos.isEmpty()) item { Text("No finished videos yet.", color = Color.Gray) }
        items(videos, key = { it.id }) { v ->
            Card(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    thumbs[v.id]?.let { AsyncImage(model = it, contentDescription = v.title, modifier = Modifier.size(72.dp, 96.dp)) }
                    Column(Modifier.weight(1f)) {
                        Text(v.title, color = Color.White)
                        Text("${v.aspect} • ${"%.0f".format(v.durationS)}s", color = Color.Gray, fontSize = 12.sp)
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            TextButton({ withVideo(v) { openVideo(context, it, Intent.ACTION_VIEW) } }, enabled = busy == null) {
                                Text(if (busy == v.id) "LOADING…" else "PLAY")
                            }
                            TextButton({ withVideo(v) { openVideo(context, it, Intent.ACTION_SEND) } }, enabled = busy == null) { Text("SHARE") }
                            TextButton({ withVideo(v) { message = saveToGallery(context, it) } }, enabled = busy == null) { Text("SAVE") }
                        }
                    }
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("CHARACTERS", color = Gold, fontSize = 12.sp, modifier = Modifier.padding(top = 14.dp))
                TextButton({ adding = true }) { Text("+ ADD CHARACTER") }
            }
        }
        if (characters.isEmpty()) item {
            Text("Save recurring characters once; pick them on the Generate screen and every scene that names them keeps the same look.",
                color = Color.Gray, fontSize = 12.sp)
        }
        items(characters, key = { it.id }) { c ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(12.dp)) {
                    Text(c.name, color = Gold)
                    Text(c.description, color = Color.LightGray, fontSize = 13.sp)
                    Row {
                        TextButton({ editing = c }) { Text("EDIT") }
                        TextButton({
                            scope.launch {
                                runCatching { client.deleteCharacter(c.id) }.onFailure { message = it.message }
                                refresh++
                            }
                        }) { Text("DELETE", color = Danger) }
                    }
                }
            }
        }
    }

    if (adding || editing != null) {
        val c = editing
        CharacterEditor(c, onDismiss = { adding = false; editing = null }) { name, description ->
            scope.launch {
                runCatching { client.saveCharacter(c?.id, name, description) }
                    .onSuccess { adding = false; editing = null; refresh++ }
                    .onFailure { message = it.message }
            }
        }
    }
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
