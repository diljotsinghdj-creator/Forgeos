package com.creatorforge.app.production

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.provider.MediaStore
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import com.creatorforge.app.render.ThumbSpec
import com.creatorforge.app.render.ThumbnailRenderer
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import android.graphics.Color as AColor

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)

private val GRADIENTS = listOf(
    "Night" to ("#0F2027" to "#2C5364"), "Fire" to ("#1A1A2E" to "#E94560"), "Gold" to ("#232526" to "#B8860B"),
    "Toxic" to ("#0B3D0B" to "#7CFC00"), "Royal" to ("#1F1C2C" to "#6A3093"), "Blood" to ("#000000" to "#8B0000"),
)
private val COLORS = listOf("White" to "#FFFFFF", "Yellow" to "#FFD400", "Red" to "#FF3B30", "Green" to "#34C759", "Cyan" to "#00E5FF", "Orange" to "#FF9500")

/** Thumbnail maker on the phone: photo or gradient, huge outlined text, one highlighted word, badge, emoji. */
@Composable
fun ThumbnailScreen(onOpenSettings: () -> Unit = {}) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var format by remember { mutableStateOf("16:9") }
    var background by remember { mutableStateOf<Bitmap?>(null) }
    var gradient by remember { mutableStateOf("Fire") }
    var line1 by remember { mutableStateOf("NOBODY") }
    var line2 by remember { mutableStateOf("SAW THIS COMING") }
    var highlight by remember { mutableStateOf("NOBODY") }
    var textColor by remember { mutableStateOf("White") }
    var hiColor by remember { mutableStateOf("Yellow") }
    var position by remember { mutableStateOf("bottom") }
    var darken by remember { mutableFloatStateOf(0.45f) }
    var badge by remember { mutableStateOf("") }
    var emoji by remember { mutableStateOf("") }
    var topic by remember { mutableStateOf("") }
    var ideas by remember { mutableStateOf<List<Triple<String, String, String>>>(emptyList()) }
    var preview by remember { mutableStateOf<Bitmap?>(null) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri: Uri? ->
        if (uri != null) scope.launch { background = withContext(Dispatchers.IO) { decode(context, uri) }; if (background == null) message = "Couldn't open that picture" }
    }

    fun spec(scale: Float = 1f): ThumbSpec {
        val (w, h) = if (format == "16:9") 1280 to 720 else 1080 to 1920
        val g = GRADIENTS.first { it.first == gradient }.second
        return ThumbSpec((w * scale).toInt(), (h * scale).toInt(), background, AColor.parseColor(g.first) to AColor.parseColor(g.second),
            line1, line2, highlight, AColor.parseColor(COLORS.first { it.first == textColor }.second),
            AColor.parseColor(COLORS.first { it.first == hiColor }.second), position, darken, badge, emoji)
    }

    // Live preview at half size, re-drawn off the main thread whenever something changes.
    LaunchedEffect(format, background, gradient, line1, line2, highlight, textColor, hiColor, position, darken, badge, emoji) {
        preview = withContext(Dispatchers.Default) { ThumbnailRenderer.render(spec(0.5f)) }
    }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("THUMBNAILS", color = Gold, fontSize = 26.sp, fontWeight = FontWeight.Bold)
        Text("Big readable text on your picture - saved straight to the gallery.", color = Color.LightGray, fontSize = 13.sp)
        preview?.let { Image(it.asImageBitmap(), "Thumbnail preview", Modifier.fillMaxWidth().heightIn(max = 420.dp), contentScale = ContentScale.Fit) }
        Chips(listOf("16:9" to "YouTube 16:9", "9:16" to "Shorts 9:16"), format) { format = it }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton({ picker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) }) { Text("PICK PHOTO") }
            if (background != null) TextButton({ background = null }) { Text("USE GRADIENT", color = Gold) }
        }
        if (background == null) Chips(GRADIENTS.map { it.first to it.first }, gradient, small = true) { gradient = it }

        OutlinedTextField(line1, { line1 = it.take(24) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Line 1") })
        OutlinedTextField(line2, { line2 = it.take(28) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Line 2 (optional)") })
        OutlinedTextField(highlight, { highlight = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Word(s) to colour") })
        Text("Text colour", color = Gold, fontSize = 12.sp); Chips(COLORS.map { it.first to it.first }, textColor, small = true) { textColor = it }
        Text("Highlight colour", color = Gold, fontSize = 12.sp); Chips(COLORS.map { it.first to it.first }, hiColor, small = true) { hiColor = it }
        Text("Text position", color = Gold, fontSize = 12.sp)
        Chips(listOf("top" to "Top", "center" to "Middle", "bottom" to "Bottom"), position, small = true) { position = it }
        Text("Shade ${(darken * 100).toInt()}%", color = Gold, fontSize = 12.sp)
        Slider(darken, { darken = it }, valueRange = 0f..0.9f)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(badge, { badge = it.take(14) }, Modifier.weight(1f), singleLine = true, label = { Text("Badge (e.g. PART 2)") })
            OutlinedTextField(emoji, { emoji = it.take(4) }, Modifier.width(110.dp), singleLine = true, label = { Text("Emoji") })
        }

        HorizontalDivider()
        Text("Need words? Ask the AI", color = Gold, fontSize = 13.sp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(topic, { topic = it }, Modifier.weight(1f), singleLine = true, label = { Text("Video topic") })
            Button(enabled = !busy && topic.isNotBlank(), onClick = {
                busy = true; message = null
                scope.launch {
                    runCatching { studio { StudioHub.brain(context).thumbnailIdeas(topic) } }.onSuccess { ideas = it }.onFailure { message = it.message }
                    busy = false
                }
            }) { Text(if (busy) "…" else "IDEAS") }
        }
        if (!StudioHub.aiReady(context)) Text("Script AI is off, so these are templates - add your Gemini key in Settings.", color = Dim, fontSize = 11.sp)
        ideas.forEach { (a, b, hi) ->
            Text("• $a ${b}".trim() + if (hi.isNotBlank()) "   ($hi)" else "", color = Color.White, fontSize = 14.sp,
                modifier = Modifier.fillMaxWidth().clickable { line1 = a; line2 = b; highlight = hi }.padding(vertical = 6.dp))
        }
        if (ideas.isNotEmpty()) Text("Tap an idea to use it.", color = Dim, fontSize = 11.sp)

        HorizontalDivider()
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(enabled = !busy, onClick = {
                busy = true
                scope.launch {
                    message = withContext(Dispatchers.IO) { saveThumbnail(context, ThumbnailRenderer.render(spec())) }
                    busy = false
                }
            }) { Text("SAVE TO GALLERY") }
            OutlinedButton(enabled = !busy, onClick = {
                scope.launch {
                    val f = withContext(Dispatchers.IO) {
                        File(context.getExternalFilesDir(null) ?: context.filesDir, "thumbnail.png").also { f ->
                            f.outputStream().use { ThumbnailRenderer.render(spec()).compress(Bitmap.CompressFormat.PNG, 100, it) }
                        }
                    }
                    val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", f)
                    context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("image/png").putExtra(Intent.EXTRA_STREAM, uri)
                        .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION), null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                }
            }) { Text("SHARE") }
        }
        message?.let { Text(it, color = if (it.startsWith("Saved")) Gold else Danger, fontSize = 12.sp) }
        Spacer(Modifier.height(24.dp))
    }
}

/** Decodes a picked photo, downsampled so huge camera images don't run the phone out of memory. */
private fun decode(context: Context, uri: Uri): Bitmap? = runCatching {
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, bounds) }
    var sample = 1
    while (maxOf(bounds.outWidth, bounds.outHeight) / sample > 2400) sample *= 2
    context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inSampleSize = sample }) }
}.getOrNull()

private fun saveThumbnail(context: Context, bmp: Bitmap): String = runCatching {
    val name = "CreatorForge_thumb_${System.currentTimeMillis()}.jpg"
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, name)
            put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg")
            put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/CreatorForge")
        }
        val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values) ?: error("gallery refused the file")
        context.contentResolver.openOutputStream(uri)!!.use { bmp.compress(Bitmap.CompressFormat.JPEG, 95, it) }
        "Saved to Pictures/CreatorForge"
    } else {
        val f = File(context.getExternalFilesDir("Pictures") ?: context.filesDir, name)
        f.outputStream().use { bmp.compress(Bitmap.CompressFormat.JPEG, 95, it) }
        "Saved in app storage (use SHARE on this Android version)"
    }
}.getOrElse { "Save failed: ${it.message}" }
