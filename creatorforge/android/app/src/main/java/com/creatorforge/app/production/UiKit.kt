package com.creatorforge.app.production

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

internal val UiGold = Color(0xFFD4AF37)
internal val UiDanger = Color(0xFFE57373)
internal val UiDim = Color(0xFF9E9E9E)
internal val UiCard = Color(0xFF1A1A1A)
internal val UiOk = Color(0xFF81C784)

/** A titled card - the building block of every screen, so pages look the same everywhere. */
@Composable
fun Section(title: String, subtitle: String = "", content: @Composable ColumnScope.() -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = UiCard), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, color = UiGold, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            if (subtitle.isNotBlank()) Text(subtitle, color = UiDim, fontSize = 12.sp)
            content()
        }
    }
}

@Composable
fun Lead(text: String) = Text(text, color = Color.LightGray, fontSize = 13.sp)

@Composable
fun Note(text: String?, error: Boolean = false) {
    if (!text.isNullOrBlank()) Text(text, color = if (error) UiDanger else UiGold, fontSize = 13.sp)
}

/** Shown on pages that need the pod when none is connected. Returns true when the pod is linked. */
@Composable
fun PodGate(onOpenSettings: () -> Unit, what: String): Boolean {
    val context = LocalContext.current
    if (StudioHub.hasWorker(context)) return true
    Section("START YOUR POD", "$what runs on your GPU pod. Settings → Pod Power starts it with one tap (or scan its QR code once).") {
        Button(onOpenSettings) { Text("OPEN SETTINGS") }
    }
    return false
}

/** Lists finished videos on the pod; tap one to pick it. */
@Composable
fun ReadyVideoPicker(selected: String?, onPick: (ProductionSummary) -> Unit, filter: (ProductionSummary) -> Boolean = { true }) {
    val context = LocalContext.current
    var items by remember { mutableStateOf<List<ProductionSummary>?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(Unit) {
        runCatching { ProductionClient(StudioHub.workerUrl(context)).list() }
            .onSuccess { items = it.filter { p -> p.status == "READY" && filter(p) } }.onFailure { error = it.message }
    }
    Note(error, true)
    when {
        items == null && error == null -> LinearProgressIndicator(Modifier.fillMaxWidth())
        items?.isEmpty() == true -> Text("No finished videos yet - make one in Generate first.", color = UiDim, fontSize = 13.sp)
        else -> items?.take(30)?.forEach { p ->
            val on = p.id == selected
            OutlinedButton({ onPick(p) }, modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.outlinedButtonColors(containerColor = if (on) Color(0xFF2A2412) else Color.Transparent)) {
                Text((if (on) "✓ " else "") + p.title.ifBlank { p.id }, color = if (on) UiGold else Color.White, maxLines = 1, fontSize = 13.sp)
            }
        }
    }
}
