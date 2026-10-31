package com.creatorforge.app.production

import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
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
import com.creatorforge.app.studio.Brand
import com.creatorforge.app.studio.Channel
import kotlinx.coroutines.launch

private val SWATCHES = listOf("#FFFFFF", "#FFD400", "#D4AF37", "#FF3B30", "#FF9500", "#34C759", "#00E5FF", "#FF2D55", "#AF52DE")

/** Brand kits: each channel gets its own caption colours, logo watermark and intro/outro lines. */
@Composable
fun BrandKitScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.channels(context) }
    var channels by remember { mutableStateOf(store.list()) }
    var selected by remember { mutableStateOf(channels.firstOrNull()?.id) }
    var message by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val ch = channels.firstOrNull { it.id == selected }

    fun save(c: Channel) { channels = store.upsert(c) }

    val logoPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        val c = ch ?: return@rememberLauncherForActivityResult
        if (uri == null) return@rememberLauncherForActivityResult
        if (!StudioHub.hasWorker(context)) { message = "Uploading a logo needs your pod - connect it in Settings"; return@rememberLauncherForActivityResult }
        val name = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { if (it.moveToFirst()) it.getString(0) else null } ?: "logo.png"
        busy = true
        scope.launch {
            runCatching { ProductionClient(StudioHub.workerUrl(context)).uploadAsset("image", name) { context.contentResolver.openInputStream(uri)!! } }
                .onSuccess { id -> save(c.copy(brand = c.brand.copy(logoAssetId = id, logoName = name))); message = "Logo saved to the pod's Asset Library" }
                .onFailure { message = it.message }
            busy = false
        }
    }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("Every video a channel makes uses its kit: caption colours, a logo in the corner, and a branded intro and outro.")
        if (channels.isEmpty()) { Section("NO CHANNELS YET", "Create a channel in Channels (or from a template), then style it here.") {}; return@Column }
        Chips(channels.map { it.id to it.name }, selected ?: "") { selected = it }
        ch?.let { c ->
            val b = c.brand
            Section("PREVIEW") { BrandPreview(c.name, b) }
            Section("CAPTION COLOUR") { Swatches(b.captionColor) { save(c.copy(brand = b.copy(captionColor = it))) } }
            Section("HIGHLIGHT COLOUR", "Key words, the hook and the call to action") { Swatches(b.highlightColor) { save(c.copy(brand = b.copy(highlightColor = it))) } }
            Section("LOGO WATERMARK", if (b.logoAssetId.isBlank()) "Optional - a PNG with a transparent background looks best" else "Using ${b.logoName.ifBlank { "your logo" }}") {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button({ logoPicker.launch("image/*") }, enabled = !busy) { Text(if (busy) "UPLOADING…" else if (b.logoAssetId.isBlank()) "ADD LOGO" else "CHANGE") }
                    if (b.logoAssetId.isNotBlank()) TextButton({ save(c.copy(brand = b.copy(logoAssetId = "", logoName = ""))) }) { Text("REMOVE", color = UiDanger) }
                }
                if (b.logoAssetId.isNotBlank()) Chips(listOf("top-left" to "Top left", "top-right" to "Top right", "bottom-left" to "Bottom left", "bottom-right" to "Bottom right"),
                    b.logoPosition, small = true) { save(c.copy(brand = b.copy(logoPosition = it))) }
            }
            Section("INTRO & OUTRO", "Shown at the start and end of every video") {
                var intro by remember(c.id) { mutableStateOf(b.introText) }
                var outro by remember(c.id) { mutableStateOf(b.outroText) }
                OutlinedTextField(intro, { intro = it.take(40) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Intro (e.g. channel name)") })
                OutlinedTextField(outro, { outro = it.take(50) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Outro (e.g. Follow for part 2)") })
                Button({ save(c.copy(brand = b.copy(introText = intro.trim(), outroText = outro.trim()))); message = "Saved" }) { Text("SAVE") }
            }
            Note(message)
        }
    }
}

@Composable
private fun Swatches(current: String, onPick: (String) -> Unit) {
    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        SWATCHES.forEach { hex ->
            val on = hex.equals(current, true)
            Box(Modifier.size(30.dp).clip(RoundedCornerShape(50)).background(Color(android.graphics.Color.parseColor(hex)))
                .border(if (on) 3.dp else 1.dp, if (on) UiGold else Color(0xFF444444), RoundedCornerShape(50))
                .clickable { onPick(hex) })
        }
    }
}

@Composable
private fun BrandPreview(name: String, b: Brand) {
    Box(Modifier.fillMaxWidth().height(160.dp).clip(RoundedCornerShape(12.dp)).background(Color(0xFF263238))) {
        if (b.introText.isNotBlank()) Text(b.introText.uppercase(), color = Color(android.graphics.Color.parseColor(b.highlightColor)), fontWeight = FontWeight.Black,
            fontSize = 13.sp, modifier = Modifier.align(Alignment.TopCenter).padding(8.dp))
        if (b.logoAssetId.isNotBlank()) Text("LOGO", color = Color.White, fontSize = 10.sp, modifier = Modifier.align(when (b.logoPosition) {
            "top-left" -> Alignment.TopStart; "bottom-left" -> Alignment.BottomStart; "bottom-right" -> Alignment.BottomEnd; else -> Alignment.TopEnd
        }).padding(8.dp).background(Color(0x66000000)).padding(4.dp))
        Row(Modifier.align(Alignment.Center)) {
            Text("This is how ", color = Color(android.graphics.Color.parseColor(b.captionColor)), fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Text("captions", color = Color(android.graphics.Color.parseColor(b.highlightColor)), fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Text(" look", color = Color(android.graphics.Color.parseColor(b.captionColor)), fontWeight = FontWeight.Bold, fontSize = 18.sp)
        }
        if (b.outroText.isNotBlank()) Text(b.outroText, color = Color(android.graphics.Color.parseColor(b.highlightColor)), fontSize = 12.sp,
            modifier = Modifier.align(Alignment.BottomCenter).padding(8.dp))
    }
}
