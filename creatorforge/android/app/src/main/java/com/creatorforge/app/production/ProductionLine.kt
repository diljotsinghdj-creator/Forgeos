package com.creatorforge.app.production

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)

/** Production Line: every queued, rendering, review and failed video on the worker, live. */
@Composable
fun ProductionLine(client: ProductionClient, onFinished: () -> Unit = {}) {
    val scope = rememberCoroutineScope()
    var jobs by remember { mutableStateOf<List<ProductionSummary>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var showFailed by remember { mutableStateOf(false) }
    var tick by remember { mutableIntStateOf(0) }

    LaunchedEffect(tick) {
        var lastActive = -1
        while (true) {
            runCatching { client.list() }.onSuccess { list ->
                jobs = list; error = null
                val active = list.count { it.status !in setOf("READY", "FAILED", "CANCELLED") }
                if (lastActive > 0 && active < lastActive) onFinished() // a video finished: refresh the library below
                lastActive = active
            }.onFailure { error = it.message }
            delay(if (jobs.any { it.status in setOf("QUEUED", "RUNNING") }) 3000 else 15000)
        }
    }

    val active = jobs.filter { it.status in setOf("QUEUED", "RUNNING", "REVIEW") }
    val failed = jobs.filter { it.status == "FAILED" }
    if (active.isEmpty() && failed.isEmpty() && error == null) return

    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1D1D1D))) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("PRODUCTION LINE", color = Gold, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                val running = active.count { it.status == "RUNNING" }
                val queued = active.count { it.status == "QUEUED" }
                Text("$running rendering • $queued waiting", color = Dim, fontSize = 12.sp)
            }
            error?.let { Text(it, color = Danger, fontSize = 12.sp) }
            active.forEach { j -> JobRow(j, onCancel = {
                scope.launch { runCatching { client.cancel(j.id) }.onFailure { error = it.message }; tick++ }
            }) }
            if (failed.isNotEmpty()) {
                TextButton(onClick = { showFailed = !showFailed }) {
                    Text("${failed.size} failed ${if (showFailed) "▲" else "▼"}", color = Danger, fontSize = 12.sp)
                }
                if (showFailed) failed.take(10).forEach { j -> JobRow(j, onRetry = {
                    scope.launch { runCatching { client.retry(j.id) }.onFailure { error = it.message }; tick++ }
                }) }
            }
            if (active.size > 1) Text("The worker renders one video at a time. Keep the pod running until the line is empty.",
                color = Dim, fontSize = 11.sp)
        }
    }
}

@Composable
private fun JobRow(j: ProductionSummary, onCancel: (() -> Unit)? = null, onRetry: (() -> Unit)? = null) {
    Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(Color(0xFF111111)).padding(10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text(j.title.ifBlank { j.id }, color = Color.White, maxLines = 1, fontSize = 14.sp)
                Text(when (j.status) {
                    "QUEUED" -> "Waiting in line"
                    "REVIEW" -> "Storyboard ready - open it in Generate to approve"
                    else -> j.message.ifBlank { j.status }
                }, color = if (j.status == "FAILED") Danger else Dim, fontSize = 11.sp, maxLines = 2)
            }
            Text("${(j.progress * 100).toInt()}%", color = Gold, fontSize = 12.sp)
            onCancel?.let { if (j.status != "REVIEW") TextButton(onClick = it) { Text("CANCEL", color = Danger, fontSize = 11.sp) } }
            onRetry?.let { TextButton(onClick = it) { Text("RETRY", color = Gold, fontSize = 11.sp) } }
        }
        LinearProgressIndicator(progress = { j.progress.coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth(), color = Gold)
    }
}
