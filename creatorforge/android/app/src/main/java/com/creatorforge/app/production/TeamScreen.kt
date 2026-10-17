package com.creatorforge.app.production

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

/** Team & Clients: approval links clients open in any browser, and keys for teammates on your pod. */
@Composable
fun TeamScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val client = remember { ProductionClient(StudioHub.workerUrl(context)) }
    var picked by remember { mutableStateOf<ProductionSummary?>(null) }
    var reviews by remember { mutableStateOf<List<ReviewItem>>(emptyList()) }
    var accounts by remember { mutableStateOf<List<Account>?>(null) }
    var newKey by remember { mutableStateOf<Account?>(null) }
    var message by remember { mutableStateOf<String?>(null) }

    fun refresh() = scope.launch {
        runCatching { client.reviews() }.onSuccess { reviews = it }
        accounts = runCatching { client.accounts() }.getOrNull() // null = this login isn't the owner
    }
    LaunchedEffect(Unit) { if (StudioHub.hasWorker(context)) refresh() }

    fun shareText(text: String) = context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
        .putExtra(Intent.EXTRA_TEXT, text), null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("Send a client a link: they watch the video in their browser and tap Approve or Request changes. No app or account needed.")
        if (!PodGate(onOpenSettings, "Client approvals")) return@Column
        Section("SEND FOR APPROVAL") {
            ReadyVideoPicker(picked?.id, { picked = it })
            Button(enabled = picked != null, onClick = {
                scope.launch {
                    runCatching { client.reviewLink(picked!!.id) }.onSuccess { url ->
                        shareText("Please review “${picked!!.title}”: $url"); refresh()
                    }.onFailure { message = it.message }
                }
            }) { Text("SHARE REVIEW LINK") }
            Text("The link works while your pod is on. With the permanent RunPod address it never changes.", color = UiDim, fontSize = 11.sp)
        }
        if (reviews.isNotEmpty()) Section("APPROVALS") {
            reviews.forEach { r ->
                Text(r.title, color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                Text(when (r.status) { "approved" -> "✓ Approved"; "changes" -> "✎ Changes requested"; else -> "… Waiting" },
                    color = when (r.status) { "approved" -> UiOk; "changes" -> UiDanger; else -> UiDim }, fontSize = 12.sp)
                r.comments.filter { it.second.isNotBlank() }.forEach { (_, c) -> Text("“$c”", color = Color.LightGray, fontSize = 12.sp) }
                TextButton({ shareText("Please review “${r.title}”: ${r.path}") }) { Text("SHARE AGAIN", color = UiGold, fontSize = 12.sp) }
            }
            TextButton({ refresh() }) { Text("↻ REFRESH", color = UiGold) }
        }
        accounts?.let { list ->
            Section("TEAMMATES & CLIENT LOGINS", "Give someone their own key for your pod. Creators make videos with credits; clients can only review.") {
                var name by remember { mutableStateOf("") }
                var role by remember { mutableStateOf("creator") }
                var credits by remember { mutableStateOf("20") }
                OutlinedTextField(name, { name = it.take(60) }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Name") })
                Chips(listOf("creator" to "Creator", "client" to "Client"), role, small = true) { role = it }
                if (role == "creator") OutlinedTextField(credits, { credits = it.filter(Char::isDigit).take(5) }, singleLine = true, label = { Text("Credits (1 ≈ 30s of video)") })
                Button(enabled = name.trim().length >= 2, onClick = {
                    scope.launch {
                        runCatching { client.createAccount(name.trim(), role, credits.toIntOrNull() ?: 0) }
                            .onSuccess { newKey = it; name = ""; refresh() }.onFailure { message = it.message }
                    }
                }) { Text("CREATE LOGIN") }
                newKey?.let { a ->
                    Text("Key for ${a.name} (shown once):", color = UiGold, fontSize = 12.sp)
                    Text(a.key, color = Color.White, fontSize = 12.sp)
                    TextButton({ shareText("Your CreatorForge login\nWorker URL: ${StudioHub.workerUrl(context)}\nToken: ${a.key}") }) { Text("SEND IT TO THEM", color = UiGold) }
                }
                list.forEach { a ->
                    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text("${a.name} • ${a.role}", color = Color.White, fontSize = 13.sp)
                            Text("${a.credits} credits left • ${a.used} used", color = UiDim, fontSize = 11.sp)
                        }
                        if (a.role == "creator") TextButton({ scope.launch { runCatching { client.addCredits(a.id, 20) }.onSuccess { refresh() } } }) { Text("+20", color = UiGold) }
                        TextButton({ scope.launch { runCatching { client.deleteAccount(a.id) }.onSuccess { refresh() } } }) { Text("REMOVE", color = UiDanger, fontSize = 12.sp) }
                    }
                }
            }
        }
        Note(message, true)
    }
}
