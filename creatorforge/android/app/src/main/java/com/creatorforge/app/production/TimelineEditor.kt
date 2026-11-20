package com.creatorforge.app.production

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONArray
import org.json.JSONObject

private val Gold = Color(0xFFD4AF37)
private val TRANSITIONS = listOf("cut", "fade", "dissolve", "dip", "flash", "slide", "wipe", "whip", "zoom", "reveal")

private data class Row(
    val index: Int, val narration: String, val narrationS: Double, val duration: Double?,
    val transition: String, val transitionChanged: Boolean, val overlay: String
)

/** Timeline editor: reorder / remove scenes, set lengths and transitions, edit hook, callouts and CTA. */
@Composable
fun TimelineEditor(p: ProductionView, onDismiss: () -> Unit, onSave: (JSONObject) -> Unit) {
    var rows by remember(p.id) {
        mutableStateOf(p.scenes.map { s ->
            Row(s.index, s.narration, s.narrationS ?: 0.0, s.durationOverride, s.transition, false, s.overlay)
        })
    }
    var hook by remember(p.id) { mutableStateOf(p.hook) }
    var cta by remember(p.id) { mutableStateOf(p.cta) }

    fun update(i: Int, f: (Row) -> Row) { rows = rows.toMutableList().also { it[i] = f(it[i]) } }
    fun move(i: Int, d: Int) {
        val j = i + d
        if (j in rows.indices) rows = rows.toMutableList().also { val t = it[i]; it[i] = it[j]; it[j] = t }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Edit timeline") },
        text = {
            LazyColumn(Modifier.heightIn(max = 560.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                item {
                    OutlinedTextField(hook, { hook = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Hook (opening title)") })
                    OutlinedTextField(cta, { cta = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Call to action (end)") })
                }
                itemsIndexed(rows, key = { _, r -> r.index }) { i, r ->
                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(10.dp)) {
                            Text("${i + 1}. ${r.narration.take(70)}${if (r.narration.length > 70) "…" else ""}", fontSize = 13.sp, color = Color.White)
                            val shown = r.duration ?: (r.narrationS + 0.35)
                            Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                                TextButton({ update(i) { it.copy(duration = maxOf(it.narrationS + 0.1, shown - 0.5)) } }) { Text("−") }
                                Text("%.1fs".format(shown) + if (r.duration == null) " auto" else "", color = Gold, fontSize = 13.sp)
                                TextButton({ update(i) { it.copy(duration = minOf(60.0, shown + 0.5)) } }) { Text("+") }
                                if (r.duration != null) TextButton({ update(i) { it.copy(duration = null) } }) { Text("AUTO") }
                            }
                            if (i > 0) TextButton({
                                val next = TRANSITIONS[(TRANSITIONS.indexOf(r.transition) + 1).mod(TRANSITIONS.size)]
                                update(i) { it.copy(transition = next, transitionChanged = true) }
                            }) { Text("Transition in: ${r.transition.ifBlank { "template" }}  (tap to change)", fontSize = 12.sp) }
                            if (i > 0) OutlinedTextField(r.overlay, { v -> update(i) { it.copy(overlay = v) } }, Modifier.fillMaxWidth(),
                                singleLine = true, label = { Text("On-screen callout (optional)") })
                            Row {
                                TextButton({ move(i, -1) }, enabled = i > 0) { Text("UP") }
                                TextButton({ move(i, 1) }, enabled = i < rows.size - 1) { Text("DOWN") }
                                TextButton({ rows = rows.filterIndexed { k, _ -> k != i } }, enabled = rows.size > 1) { Text("REMOVE") }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button({
                val scenes = JSONArray()
                rows.forEach { r ->
                    val o = JSONObject().put("index", r.index).put("overlay", r.overlay)
                        .put("duration_s", r.duration ?: JSONObject.NULL)
                    if (r.transitionChanged) o.put("transition", r.transition)
                    scenes.put(o)
                }
                onSave(JSONObject().put("hook", hook).put("cta", cta).put("scenes", scenes))
            }) { Text("SAVE") }
        },
        dismissButton = { TextButton(onDismiss) { Text("CANCEL") } }
    )
}

/** Picks an Asset Library file (image, clip or voice-over) for one scene. */
@Composable
fun AssetPicker(assets: List<LibraryAsset>, sceneNumber: Int, onDismiss: () -> Unit, onPick: (LibraryAsset) -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Use an asset in scene $sceneNumber") },
        text = {
            val usable = assets.filter { it.kind in setOf("image", "video", "audio") }
            if (usable.isEmpty()) Text("No images, clips or voice-overs in your Asset Library yet. Import them from the Library tab.")
            else LazyColumn(Modifier.heightIn(max = 420.dp)) {
                itemsIndexed(usable, key = { _, a -> a.id }) { _, a ->
                    TextButton({ onPick(a) }, Modifier.fillMaxWidth()) {
                        Text("${when (a.kind) { "image" -> "🖼"; "video" -> "🎞"; else -> "🎙" }}  ${a.name}" +
                            if (a.kind == "audio") "  (replaces narration)" else "", color = Color.White)
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = { TextButton(onDismiss) { Text("CLOSE") } }
    )
}
