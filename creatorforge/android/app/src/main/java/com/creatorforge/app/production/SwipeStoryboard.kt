package com.creatorforge.app.production

import android.content.Context
import androidx.compose.animation.core.Animatable
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.launch
import kotlin.math.abs

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Keep = Color(0xFF81C784)
private const val THRESHOLD = 220f

/**
 * Swipe Storyboard: one scene at a time. Swipe right (or ✓) to keep it, left (or ✗) to have it redrawn,
 * tap ✎ to change its words or picture description. At the end: redraw the rejected scenes or approve and render.
 */
@Composable
fun SwipeStoryboard(
    context: Context, p: ProductionView, busy: Boolean, version: Int,
    onRedraw: (List<Int>) -> Unit, onEdit: (SceneView) -> Unit, onApprove: () -> Unit, onListView: () -> Unit
) {
    val scope = rememberCoroutineScope()
    val scenes = p.scenes
    var index by remember(p.id) { mutableIntStateOf(0) }
    val decisions = remember(p.id) { mutableStateMapOf<Int, Boolean>() } // true = keep, false = redraw
    val offset = remember { Animatable(0f) }

    fun decide(keep: Boolean) {
        val i = index
        if (i >= scenes.size) return
        decisions[scenes[i].index] = keep
        scope.launch {
            offset.animateTo(if (keep) 1400f else -1400f)
            index = i + 1
            offset.snapTo(0f)
        }
    }

    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF151515))) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("SWIPE STORYBOARD", color = Gold, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                TextButton(onListView) { Text("LIST VIEW", color = Gold, fontSize = 12.sp) }
            }
            // progress dots: gold = keep, red = redraw, grey = not decided
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                scenes.forEachIndexed { i, s ->
                    val c = when (decisions[s.index]) { true -> Keep; false -> Danger; null -> if (i == index) Gold else Color(0xFF333333) }
                    Box(Modifier.weight(1f).height(5.dp).clip(RoundedCornerShape(3.dp)).background(c))
                }
            }

            if (index < scenes.size) {
                val s = scenes[index]
                val f = storyboardFile(context, p.id, s.index)
                Box(
                    Modifier.fillMaxWidth()
                        .graphicsLayer { translationX = offset.value; rotationZ = offset.value / 45f }
                        .pointerInput(index) {
                            detectHorizontalDragGestures(
                                onDragEnd = {
                                    when {
                                        offset.value > THRESHOLD -> decide(true)
                                        offset.value < -THRESHOLD -> decide(false)
                                        else -> scope.launch { offset.animateTo(0f) }
                                    }
                                },
                                onHorizontalDrag = { change, delta -> change.consume(); scope.launch { offset.snapTo(offset.value + delta) } }
                            )
                        }
                        .clip(RoundedCornerShape(16.dp)).background(Color(0xFF0E0E0E))
                ) {
                    Column {
                        key(version, s.index) { if (f.isFile) AsyncImage(model = f, contentDescription = "Scene ${s.index + 1}", contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxWidth().height(380.dp))
                        else Box(Modifier.fillMaxWidth().height(220.dp), contentAlignment = Alignment.Center) {
                            Text(if (s.imageState == "READY") "Loading picture…" else "Picture: ${s.imageState}", color = Color.Gray)
                        } }
                        Column(Modifier.padding(12.dp)) {
                            Text("Scene ${s.index + 1} of ${scenes.size}", color = Gold, fontSize = 12.sp)
                            Text("“${s.narration}”", color = Color.White, fontSize = 15.sp)
                            if (s.visual.isNotBlank()) Text(s.visual, color = Color.Gray, fontSize = 12.sp, maxLines = 3)
                            s.error?.let { Text(it, color = Danger, fontSize = 11.sp) }
                        }
                    }
                    val o = offset.value
                    if (abs(o) > 30) Text(if (o > 0) "KEEP" else "REDRAW", color = if (o > 0) Keep else Danger,
                        fontSize = 34.sp, fontWeight = FontWeight.Black,
                        modifier = Modifier.align(if (o > 0) Alignment.TopStart else Alignment.TopEnd).padding(18.dp)
                            .graphicsLayer { alpha = (abs(o) / THRESHOLD).coerceIn(0f, 1f) })
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                    OutlinedButton({ decide(false) }, enabled = !busy) { Text("✗ REDRAW", color = Danger) }
                    OutlinedButton({ onEdit(s) }, enabled = !busy) { Text("✎ EDIT") }
                    Button({ decide(true) }, enabled = !busy) { Text("✓ KEEP") }
                }
                if (index > 0) TextButton({ index -= 1; decisions.remove(scenes[index].index) }) { Text("↶ UNDO", color = Gold) }
                Text("Swipe right to keep, left to redraw.", color = Color.Gray, fontSize = 11.sp)
            } else {
                val redraw = decisions.filterValues { !it }.keys.sorted()
                Text("Keeping ${scenes.size - redraw.size} • redrawing ${redraw.size}", color = Color.White, fontSize = 16.sp)
                if (redraw.isNotEmpty()) {
                    Button({ onRedraw(redraw) }, enabled = !busy, modifier = Modifier.fillMaxWidth().height(52.dp)) {
                        Text("REDRAW ${redraw.size} SCENE${if (redraw.size == 1) "" else "S"}")
                    }
                    Text("New pictures are made for those scenes, then the storyboard pauses here again for you.", color = Color.Gray, fontSize = 11.sp)
                } else {
                    Button(onApprove, enabled = !busy, modifier = Modifier.fillMaxWidth().height(52.dp)) { Text("APPROVE & RENDER") }
                }
                TextButton({ index = 0; decisions.clear() }) { Text("START OVER", color = Gold) }
            }
        }
    }
}
