package com.creatorforge.app.production

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.security.SecureTokenStore
import com.creatorforge.app.studio.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)

/** Everything the writing side of the studio needs, living on the phone. The worker is only for making videos. */
object StudioHub {
    private fun prefs(c: Context) = c.getSharedPreferences("creatorforge_ai", 0)
    private fun dir(c: Context) = File(c.filesDir, "studio").apply { mkdirs() }

    fun preset(c: Context) = AiPresets[prefs(c).getString("preset", "gemini").orEmpty()]
    fun baseUrl(c: Context) = prefs(c).getString("base_url", null) ?: preset(c).baseUrl
    fun model(c: Context) = prefs(c).getString("model", null) ?: preset(c).model
    fun key(c: Context) = SecureTokenStore(c).load("ai").orEmpty()
    fun youtubeKey(c: Context) = SecureTokenStore(c).load("youtube").orEmpty()

    /** AI is "on" when a key is saved, or a custom server (e.g. Ollama on a PC) is set. */
    fun aiReady(c: Context) = baseUrl(c).isNotBlank() && model(c).isNotBlank() && (key(c).isNotBlank() || preset(c).id == "custom")

    /** Your Script AI (Gemini, Groq, ...), lent to the pod to plan each video's story and shots - far stronger than the
     *  pod's small local model. Only https services; the pod keeps it in memory for that one video. */
    /** Pixabay key (Settings), lent to the pod for real stock footage in fast cuts. "pexels:KEY" still works for old Pexels keys. */
    fun stockKey(c: Context): org.json.JSONObject? =
        SecureTokenStore(c).load("stock")?.trim()?.takeIf { it.isNotBlank() }?.let { k ->
            if (k.startsWith("pexels:", ignoreCase = true)) org.json.JSONObject().put("provider", "pexels").put("key", k.substringAfter(":").trim())
            else org.json.JSONObject().put("provider", "pixabay").put("key", k.removePrefix("pixabay:").removePrefix("Pixabay:").trim())
        }

    /** Checks the saved stock key with Pixabay itself (one tiny search): null when it works, else the reason. */
    fun testStockKey(c: Context): String? {
        val k = stockKey(c) ?: return "Add a key first"
        if (k.getString("provider") != "pixabay") return null
        val (code, body) = com.creatorforge.app.studio.HttpFetcher().get(
            "https://pixabay.com/api/videos/?key=${Uri.encode(k.getString("key"))}&q=city&per_page=3")
        return when {
            code == 200 && "\"hits\"" in body -> null
            code == 400 || code == 401 || "key" in body.lowercase() -> "Pixabay rejected this key - copy it again from pixabay.com/api/docs (logged in)"
            code == 429 -> "Pixabay says too many requests - wait a minute and test again"
            else -> "Pixabay answered HTTP $code"
        }
    }

    fun directorLlm(c: Context): org.json.JSONObject? {
        if (!aiReady(c) || !baseUrl(c).startsWith("https://")) return null
        return org.json.JSONObject().put("url", baseUrl(c).trimEnd('/')).put("model", model(c).removePrefix("models/")).put("key", key(c))
    }

    fun textModel(c: Context, modelName: String = model(c)): TextModel =
        if (preset(c).id == "gemini") GeminiNative(modelName, key(c)) else OpenAiCompatible(baseUrl(c), modelName, key(c))

    fun models(c: Context): List<String> =
        if (preset(c).id == "gemini") GeminiNative.listModels(key(c)) else listModels(baseUrl(c), key(c))

    fun brain(c: Context): Brain = Brain(if (aiReady(c)) textModel(c) else null)
    fun radar(c: Context) = TrendRadar(File(c.cacheDir, "trends"), { youtubeKey(c) })
    fun scripts(c: Context) = ScriptStore(dir(c))
    fun channels(c: Context) = ChannelStore(dir(c))
    fun series(c: Context) = SeriesStore(dir(c))
    fun templates(c: Context) = TemplateStore(dir(c))
    fun workerUrl(c: Context) = c.getSharedPreferences("creatorforge_provider", 0).getString("base_url", "").orEmpty()
    fun hasWorker(c: Context) = workerUrl(c).isNotBlank()

    fun save(c: Context, presetId: String, baseUrl: String, model: String) {
        prefs(c).edit().putString("preset", presetId).putString("base_url", baseUrl.trim()).putString("model", model.trim()).apply()
    }
}

/** Runs blocking studio work off the main thread. */
suspend fun <T> studio(block: () -> T): T = withContext(Dispatchers.IO) { block() }

/** A small banner shown in writing screens while no Script AI is set up. */
@Composable
fun AiBanner(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    if (StudioHub.aiReady(context)) return
    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1F1A0A))) {
        Column(Modifier.padding(12.dp)) {
            Text("Script AI is off - you're getting simple template text.", color = Gold, fontSize = 13.sp)
            Text("Add a free Google Gemini or Groq key in Settings for real ideas, scripts and chat. No pod needed.", color = Color.LightGray, fontSize = 12.sp)
            TextButton(onOpenSettings) { Text("SET UP SCRIPT AI", color = Gold) }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AiSettingsCard(secure: SecureTokenStore) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var preset by remember { mutableStateOf(StudioHub.preset(context).id) }
    var baseUrl by remember { mutableStateOf(StudioHub.baseUrl(context)) }
    var model by remember { mutableStateOf(StudioHub.model(context)) }
    var key by remember { mutableStateOf("") }
    var hasKey by remember { mutableStateOf(secure.has("ai")) }
    var ytKey by remember { mutableStateOf("") }
    var hasYt by remember { mutableStateOf(secure.has("youtube")) }
    var ytStatus by remember { mutableStateOf<String?>(null) }
    var status by remember { mutableStateOf<String?>(null) }
    var testing by remember { mutableStateOf(false) }
    val p = AiPresets[preset]

    Card { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("SCRIPT AI (runs from your phone - no pod)", color = Gold)
        Text("Used by Trends, Director, Scripts and Channels for ideas, scripts, scenes and prompts.", color = Color.LightGray, fontSize = 12.sp)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            AiPresets.all.forEach { a ->
                FilterChip(selected = a.id == preset, onClick = { preset = a.id; baseUrl = a.baseUrl; model = a.model }, label = { Text(a.name, fontSize = 12.sp) })
            }
        }
        Text(p.note, color = Dim, fontSize = 12.sp)
        if (p.keyUrl.isNotBlank()) TextButton({
            runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(p.keyUrl)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        }) { Text("GET A FREE KEY ↗", color = Gold) }
        if (preset == "custom") OutlinedTextField(baseUrl, { baseUrl = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Server address (…/v1)") })
        OutlinedTextField(model, { model = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Model") })
        var models by remember { mutableStateOf<List<String>>(emptyList()) }
        TextButton({
            scope.launch {
                if (key.isNotBlank()) { secure.save("ai", key.trim()); key = ""; hasKey = true }
                StudioHub.save(context, preset, baseUrl, model)
                runCatching { studio { StudioHub.models(context) } }
                    .onSuccess { list -> models = list.filter { pickTextModel(listOf(it)) != null }.take(30); if (models.isEmpty()) status = "✗ No models found for this key" }
                    .onFailure { status = "✗ ${it.message}" }
            }
        }) { Text("SHOW MODELS MY KEY CAN USE", color = Gold, fontSize = 12.sp) }
        if (models.isNotEmpty()) Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            models.forEach { m -> FilterChip(selected = m == model, onClick = { model = m }, label = { Text(m, fontSize = 11.sp) }) }
        }
        OutlinedTextField(key, { key = it }, Modifier.fillMaxWidth(), singleLine = true, visualTransformation = PasswordVisualTransformation(),
            label = { Text(if (hasKey) "API key saved - paste to replace" else "API key") })
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                StudioHub.save(context, preset, baseUrl, model)
                if (key.isNotBlank()) { secure.save("ai", key.trim()); key = ""; hasKey = true }
                testing = true; status = null
                scope.launch {
                    val result = runCatching {
                        studio {
                            require(StudioHub.aiReady(context)) { "Add a key first" }
                            val base = StudioHub.baseUrl(context)
                            try {
                                StudioHub.textModel(context).complete("Reply with the single word OK.", "Say OK")
                                StudioHub.model(context) to false
                            } catch (e: AiException) {
                                val m = e.message ?: ""
                                if ("doesn't know the model" !in m && "doesn't offer the model" !in m) throw e
                                // The model was retired or renamed: ask the service what this key can use and switch to it.
                                val pick = pickTextModel(StudioHub.models(context)) ?: throw e
                                StudioHub.textModel(context, pick).complete("Reply with the single word OK.", "Say OK")
                                StudioHub.save(context, preset, base, pick)
                                pick to true
                            }
                        }
                    }
                    status = result.fold({ (m, switched) ->
                        model = m
                        if (switched) "✓ Script AI works - switched to $m" else "✓ Script AI works ($m)"
                    }, { "✗ ${it.message}" })
                    testing = false
                }
            }, enabled = !testing) { Text(if (testing) "TESTING…" else "SAVE & TEST") }
            if (hasKey) TextButton({ secure.clear("ai"); hasKey = false; status = "Key removed - templates will be used" }) { Text("REMOVE KEY", color = Danger) }
        }
        status?.let { Text(it, color = if (it.startsWith("✓")) Gold else Danger, fontSize = 12.sp) }
        HorizontalDivider(Modifier.padding(vertical = 6.dp))
        Text("Real stock footage (free, optional)", color = Gold, fontSize = 13.sp)
        Text("Your videos already mix in real footage from NASA (space, science, Earth) and Wikimedia Commons (history, " +
            "real events, animals) - no key needed; their credits go into the post description. " +
            "Add a free Pixabay key for everyday clips - crowds, cities, hands, nature - free for commercial use. " +
            "Get it: sign up at pixabay.com, then open pixabay.com/api/docs - your key is shown there.", color = Dim, fontSize = 12.sp)
        TextButton({ openUrl(context, "https://pixabay.com/api/docs/") }) { Text("GET A FREE PIXABAY KEY ↗", color = Gold, fontSize = 12.sp) }
        var stock by remember { mutableStateOf("") }
        var hasStock by remember { mutableStateOf(secure.has("stock")) }
        var stockStatus by remember { mutableStateOf<String?>(null) }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(stock, { stock = it }, Modifier.weight(1f), singleLine = true, visualTransformation = PasswordVisualTransformation(),
                label = { Text(if (hasStock) "Saved - paste to replace" else "Pixabay API key") })
            Button({ if (stock.isNotBlank()) { secure.save("stock", stock.trim().trim('"', ' ')); stock = ""; hasStock = true }
                scope.launch {
                    stockStatus = "Testing…"
                    stockStatus = runCatching { studio { StudioHub.testStockKey(context) } }
                        .fold({ it?.let { e -> "✗ $e" } ?: "✓ Pixabay key works - stock clips will be mixed into your videos" }, { "✗ ${it.message}" })
                }
            }, enabled = stock.isNotBlank() || hasStock) { Text(if (stock.isBlank() && hasStock) "TEST" else "SAVE & TEST") }
        }
        stockStatus?.let { Text(it, color = if (it.startsWith("✓")) Gold else if (it.startsWith("✗")) Danger else Dim, fontSize = 12.sp) }
        if (hasStock) TextButton({ secure.clear("stock"); hasStock = false; stockStatus = null }) { Text("REMOVE STOCK KEY", color = Danger) }
        HorizontalDivider(Modifier.padding(vertical = 6.dp))
        Text("YouTube trends (optional)", color = Gold, fontSize = 13.sp)
        Text("A free YouTube Data API key adds YouTube's most-watched videos to Trends.", color = Dim, fontSize = 12.sp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(ytKey, { ytKey = it }, Modifier.weight(1f), singleLine = true, visualTransformation = PasswordVisualTransformation(),
                label = { Text(if (hasYt) "Saved - paste to replace" else "YouTube API key") })
            Button({ if (ytKey.isNotBlank()) { secure.save("youtube", ytKey.trim().trim('"', ' ')); ytKey = ""; hasYt = true }
                scope.launch {
                    ytStatus = "Testing…"
                    ytStatus = runCatching { studio { YouTubeStats.test(HttpFetcher(), StudioHub.youtubeKey(context)) } }
                        .fold({ it?.let { e -> "✗ $e" } ?: "✓ YouTube key works" }, { "✗ ${it.message}" })
                }
            }, enabled = ytKey.isNotBlank() || hasYt) { Text(if (ytKey.isBlank() && hasYt) "TEST" else "SAVE & TEST") }
        }
        ytStatus?.let { Text(it, color = if (it.startsWith("✓")) Gold else if (it.startsWith("✗")) Danger else Dim, fontSize = 12.sp) }
        if (hasYt) TextButton({ secure.clear("youtube"); hasYt = false; ytStatus = "YouTube key removed" }) { Text("REMOVE YOUTUBE KEY", color = Danger) }
    } }
}
