package com.creatorforge.app.production

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.security.SecureTokenStore
import com.creatorforge.app.studio.PodInfo
import com.creatorforge.app.studio.RunPodApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/** Start and stop the GPU pod from the phone, and wait until CreatorForge on it is ready. */
@Composable
fun PodPowerCard() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val secure = remember { SecureTokenStore(context) }
    var hasKey by remember { mutableStateOf(secure.has("runpod")) }
    var key by remember { mutableStateOf("") }
    var pods by remember { mutableStateOf<List<PodInfo>>(emptyList()) }
    var status by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var showSetup by remember { mutableStateOf(false) }

    fun api() = RunPodApi(secure.load("runpod").orEmpty())
    fun refresh() = scope.launch { runCatching { studio { api().pods() } }.onSuccess { pods = it }.onFailure { status = "✗ ${it.message}" } }

    /** After a start: wait for the pod, then for CreatorForge on it, up to ~15 minutes. */
    fun waitForWorker(pod: PodInfo) = scope.launch {
        val prefs = context.getSharedPreferences("creatorforge_provider", 0)
        if (prefs.getString("base_url", "").isNullOrBlank() || prefs.getString("base_url", "")!!.contains("proxy.runpod.net")) {
            prefs.edit().putString("base_url", pod.workerUrl).apply()
        }
        for (i in 0 until 90) {
            val h = runCatching { com.creatorforge.app.generation.LocalWorkerClient(com.creatorforge.app.generation.LocalProviderConfig(StudioHub.workerUrl(context))).health() }.getOrNull()
            if (h?.ok == true) { status = "✓ CreatorForge is ready on the pod"; refresh(); return@launch }
            if (h != null && "TOKEN" in h.message) { status = "✗ The pod is ready but its password doesn't match the app. Do step 3 of ONE-TIME SETUP below, or scan the pod's QR."; return@launch }
            status = if (i < 6) "Starting the pod…" else "Pod is on - CreatorForge is loading (${i * 10 / 60} min)…"
            delay(10_000)
        }
        status = "The pod is on but CreatorForge didn't answer. Check the one-time setup below (start command + port 8765)."
    }

    LaunchedEffect(Unit) { if (hasKey) refresh() }

    Card { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("POD POWER", color = UiGold)
        Text("Start and stop your RunPod GPU from here - no website, no terminal.", color = Color.LightGray, fontSize = 12.sp)
        if (!hasKey) {
            Text("RunPod → Settings → API Keys → Create API Key (Read/Write). Paste it here:", color = UiDim, fontSize = 12.sp)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(key, { key = it }, Modifier.weight(1f), singleLine = true, visualTransformation = PasswordVisualTransformation(), label = { Text("RunPod API key") })
                Button({ secure.save("runpod", key.trim()); key = ""; hasKey = true; refresh() }, enabled = key.isNotBlank()) { Text("SAVE") }
            }
        } else {
            pods.forEach { p ->
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("${p.name.ifBlank { p.id }} • ${p.gpu}", color = Color.White, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Text((if (p.running) "● Running" else "○ Stopped") + if (p.costPerHour > 0) " • $%.2f/hr".format(p.costPerHour) else "",
                            color = if (p.running) UiOk else UiDim, fontSize = 12.sp)
                    }
                    if (p.running) OutlinedButton({
                        busy = true
                        scope.launch { runCatching { studio { api().stop(p.id) } }.onSuccess { status = "Stopping - you stop paying for the GPU"; delay(3000); refresh() }.onFailure { status = "✗ ${it.message}" }; busy = false }
                    }, enabled = !busy) { Text("■ STOP") }
                    else Button({
                        busy = true
                        scope.launch {
                            runCatching { studio { api().start(p.id) } }.onSuccess { waitForWorker(p) }.onFailure { status = "✗ ${it.message}" }
                            busy = false
                        }
                    }, enabled = !busy) { Text("▶ START") }
                }
            }
            if (pods.isEmpty()) Text("No pods on this RunPod account yet - create one on runpod.io first.", color = UiDim, fontSize = 12.sp)
            Row {
                TextButton({ refresh() }) { Text("↻ REFRESH", color = UiGold, fontSize = 12.sp) }
                TextButton({ showSetup = !showSetup }) { Text(if (showSetup) "HIDE SETUP" else "ONE-TIME SETUP", color = UiGold, fontSize = 12.sp) }
                TextButton({ secure.clear("runpod"); hasKey = false; pods = emptyList() }) { Text("REMOVE KEY", color = UiDanger, fontSize = 12.sp) }
            }
        }
        status?.let { Text(it, color = if (it.startsWith("✗")) UiDanger else UiGold, fontSize = 12.sp) }
        if (showSetup || (hasKey && pods.isNotEmpty() && status == null)) {
            HorizontalDivider()
            Text("ONE-TIME POD SETUP (so CreatorForge starts by itself)", color = UiGold, fontSize = 12.sp)
            Text("On runpod.io: your pod → ⋮ → Edit Pod.\n1. Container Start Command: paste the line below.\n2. Expose HTTP Ports: add 8765.\n" +
                "3. Environment Variables: add CF_WORKER_TOKEN with the pod password below (so the password never changes, even after a restart wipes the pod).\n" +
                "4. Save. From then on, ▶ START here is all you need.", color = Color.LightGray, fontSize = 12.sp)
            OutlinedButton({ copyText(context, RunPodApi.START_COMMAND); status = "Start command copied - paste it into Container Start Command" }) { Text("COPY START COMMAND") }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton({ copyText(context, "CF_WORKER_TOKEN"); status = "Copied the name - paste it as the variable's KEY" }) { Text("COPY NAME") }
                OutlinedButton({ copyText(context, podPassword(secure)); status = "Pod password copied - paste it as the VALUE of CF_WORKER_TOKEN. The app already uses it." }) { Text("COPY PASSWORD") }
            }
            Text("The app made this password and already uses it, so after this you never type or scan a token again.", color = UiDim, fontSize = 11.sp)
        }
    } }
}

/** The app's pod password: the saved worker token, or a new random one that the app starts using right away. */
internal fun podPassword(secure: SecureTokenStore): String {
    secure.load("worker")?.takeIf { it.isNotBlank() }?.let { return it }
    val bytes = ByteArray(24).also { java.security.SecureRandom().nextBytes(it) }
    val token = android.util.Base64.encodeToString(bytes, android.util.Base64.URL_SAFE or android.util.Base64.NO_WRAP or android.util.Base64.NO_PADDING)
    secure.save("worker", token)
    WorkerAuth.token = token
    return token
}
