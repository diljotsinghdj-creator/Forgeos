package com.creatorforge.app.production

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
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
import kotlinx.coroutines.launch
import org.json.JSONObject

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)
private val Dim = Color(0xFF9E9E9E)
private val Card2 = Color(0xFF1D1D1D)

private val PERIODS = listOf("week" to "This week", "month" to "This month", "year" to "This year")
private val FALLBACK_NICHES = listOf(
    Choice("all", "Everything"), Choice("tech", "Tech & Gadgets"), Choice("ai", "AI"), Choice("money", "Money & Finance"),
    Choice("business", "Business & Side Hustles"), Choice("crypto", "Crypto"), Choice("science", "Science & Space"),
    Choice("history", "History"), Choice("mystery", "Mystery & True Crime"), Choice("facts", "Facts & Curiosities"),
    Choice("motivation", "Motivation & Self-improvement"), Choice("health", "Health & Fitness"), Choice("gaming", "Gaming"),
    Choice("entertainment", "Movies, TV & Music"), Choice("sports", "Sports"), Choice("custom", "My keyword")
)
private val FALLBACK_REGIONS = listOf(Choice("GB", "UK"), Choice("US", "US"), Choice("IN", "India"), Choice("CA", "Canada"), Choice("AU", "Australia"))

/** Trend Radar: what is trending this week, month or year, turned into ideas, scripts and videos in a few taps. */
@Composable
fun TrendsScreen(onOpenSettings: () -> Unit = {}, onOpenGenerate: () -> Unit = {}) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val worker = remember { context.getSharedPreferences("creatorforge_provider", 0) }
    val prefs = remember { context.getSharedPreferences("creatorforge_trends", 0) }
    val client = remember { ProductionClient(worker.getString("base_url", "").orEmpty()) }

    var period by remember { mutableStateOf(prefs.getString("period", "week").orEmpty()) }
    var niche by remember { mutableStateOf(prefs.getString("niche", "all").orEmpty()) }
    var region by remember { mutableStateOf(prefs.getString("region", "GB").orEmpty()) }
    var keyword by remember { mutableStateOf(prefs.getString("keyword", "").orEmpty()) }
    var niches by remember { mutableStateOf(FALLBACK_NICHES) }
    var regions by remember { mutableStateOf(FALLBACK_REGIONS) }
    var youtube by remember { mutableStateOf(true) }

    var scan by remember { mutableStateOf<TrendScan?>(null) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var notice by remember { mutableStateOf<String?>(null) }
    var open by remember { mutableStateOf<String?>(null) }
    val ideas = remember { mutableStateMapOf<String, List<TrendIdea>>() }
    val picked = remember { mutableStateMapOf<String, Boolean>() } // "trendId|ideaIndex"
    val scripts = remember { mutableStateMapOf<String, TrendScript>() } // "trendId|ideaIndex"
    var working by remember { mutableStateOf<String?>(null) } // what is busy right now (key)

    fun load(refresh: Boolean) {
        if (niche == "custom" && keyword.trim().length < 2) { error = "Type a keyword first"; return }
        prefs.edit().putString("period", period).putString("niche", niche).putString("region", region).putString("keyword", keyword).apply()
        loading = true; error = null; notice = null
        scope.launch {
            runCatching { client.trends(period, niche, region, if (niche == "custom") keyword.trim() else "", refresh) }
                .onSuccess { scan = it; open = null }
                .onFailure { error = it.message }
            loading = false
        }
    }

    LaunchedEffect(Unit) {
        runCatching { client.trendOptions() }.onSuccess { (n, r, yt) -> if (n.isNotEmpty()) niches = n; if (r.isNotEmpty()) regions = r; youtube = yt }
        load(false)
    }

    fun sendToGenerate(script: TrendScript) {
        val g = context.getSharedPreferences("creatorforge_generate", 0)
        val long = script.seconds() > 60
        val current = g.getString("template", "shorts_cinematic").orEmpty()
        val template = if (long) "youtube_longform" else if (current == "reels_punchy") current else "shorts_cinematic"
        g.edit().putString("idea", script.script).putBoolean("script_mode", true).putString("template", template)
            .putString("aspect", if (long) "16:9" else "9:16").apply()
        onOpenGenerate()
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            Text("TREND RADAR", color = Gold, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Text("What people are watching and searching - turned into videos.", color = Color.LightGray)
        }
        item { Chips(PERIODS, period) { period = it; load(false) } }
        item { Chips(niches.map { it.id to it.name }, niche) { niche = it; if (it != "custom") load(false) } }
        item { Chips(regions.map { it.id to it.name }, region, small = true) { region = it; load(false) } }
        if (niche == "custom") item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(keyword, { keyword = it }, Modifier.weight(1f), singleLine = true, label = { Text("Keyword or topic") },
                    placeholder = { Text("e.g. electric cars, Roman empire, budgeting") })
                Spacer(Modifier.width(8.dp))
                Button(onClick = { load(false) }, enabled = !loading) { Text("SCAN") }
            }
        }
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(scan?.let { s -> "${s.items.size} topics • " + if (s.cached) "saved scan" else "fresh scan" } ?: "", color = Dim, fontSize = 12.sp,
                    modifier = Modifier.weight(1f))
                TextButton(onClick = { load(true) }, enabled = !loading) { Text(if (loading) "SCANNING…" else "↻ REFRESH", color = Gold) }
            }
            if (loading) LinearProgressIndicator(Modifier.fillMaxWidth(), color = Gold)
            scan?.let { s ->
                Text(s.sources.joinToString("  ") { (if (it.ok) "✓ " else "✗ ") + it.name + if (it.ok) " ${it.count}" else "" },
                    color = Dim, fontSize = 11.sp)
                s.sources.filter { !it.ok && it.error.isNotBlank() }.forEach { Text("${it.name}: ${it.error}", color = Dim, fontSize = 11.sp) }
            }
        }
        error?.let { e ->
            item {
                Card(colors = CardDefaults.cardColors(containerColor = Card2)) {
                    Column(Modifier.padding(14.dp)) {
                        Text(e, color = Danger)
                        if ("Settings" in e || "unreachable" in e) TextButton(onClick = onOpenSettings) { Text("OPEN SETTINGS", color = Gold) }
                    }
                }
            }
        }
        notice?.let { n -> item { Text(n, color = Gold) } }

        items(scan?.items.orEmpty(), key = { it.id }) { t ->
            val expanded = open == t.id
            Card(colors = CardDefaults.cardColors(containerColor = Card2), modifier = Modifier.fillMaxWidth().clickable { open = if (expanded) null else t.id }) {
                Column(Modifier.padding(14.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(heatLabel(t.heat), fontSize = 12.sp, color = Gold, modifier = Modifier.width(70.dp))
                        Box(Modifier.weight(1f).height(6.dp).clip(RoundedCornerShape(3.dp)).background(Color(0xFF2A2A2A))) {
                            Box(Modifier.fillMaxWidth(t.heat.coerceIn(4, 100) / 100f).fillMaxHeight().background(Gold))
                        }
                    }
                    Spacer(Modifier.height(6.dp))
                    Text(t.title, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                    Text(t.sources.joinToString(" • ") + metricText(t.metrics), color = Dim, fontSize = 12.sp)
                    t.headlines.take(if (expanded) 6 else 2).forEach { Text("“$it”", color = Color.LightGray, fontSize = 13.sp, maxLines = if (expanded) 3 else 1) }

                    if (expanded) {
                        Spacer(Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            listOf("short" to "5 SHORTS IDEAS", "long" to "3 LONG IDEAS").forEach { (fmt, label) ->
                                OutlinedButton(enabled = working == null, onClick = {
                                    working = "${t.id}|ideas"; error = null
                                    scope.launch {
                                        runCatching { client.trendIdeas(t.id, if (fmt == "short") 5 else 3, fmt, niche, period) }
                                            .onSuccess { ideas[t.id] = it; it.indices.forEach { i -> picked["${t.id}|$i"] = true } }
                                            .onFailure { error = it.message }
                                        working = null
                                    }
                                }) { Text(label, fontSize = 12.sp) }
                            }
                        }
                        if (working == "${t.id}|ideas") Text("The AI Director is reading the sources…", color = Dim, fontSize = 12.sp)
                        TextButton(onClick = { t.signals.firstOrNull { it.url.isNotBlank() }?.let { openUrl(context, it.url) } }) {
                            Text("OPEN TOP SOURCE", color = Gold, fontSize = 12.sp)
                        }

                        ideas[t.id]?.let { list ->
                            list.forEachIndexed { i, idea ->
                                val key = "${t.id}|$i"
                                Column(Modifier.fillMaxWidth().padding(vertical = 6.dp).clip(RoundedCornerShape(10.dp)).background(Color(0xFF111111)).padding(10.dp)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Checkbox(picked[key] == true, { picked[key] = it })
                                        Column(Modifier.weight(1f)) {
                                            Text(idea.title, color = Color.White, fontWeight = FontWeight.SemiBold)
                                            Text("${if (idea.format == "long") "Long-form 16:9" else "Short 9:16"} • ${idea.seconds}s", color = Dim, fontSize = 11.sp)
                                        }
                                    }
                                    Text("Hook: ${idea.hook}", color = Gold, fontSize = 13.sp)
                                    if (idea.angle.isNotBlank()) Text(idea.angle, color = Color.LightGray, fontSize = 13.sp)
                                    if (idea.whyNow.isNotBlank()) Text("Why now: ${idea.whyNow}", color = Dim, fontSize = 12.sp)
                                    val sc = scripts[key]
                                    if (sc == null) {
                                        TextButton(enabled = working == null, onClick = {
                                            working = key; error = null
                                            scope.launch {
                                                runCatching { client.trendScript(t.id, idea) }.onSuccess { scripts[key] = it }.onFailure { error = it.message }
                                                working = null
                                            }
                                        }) { Text(if (working == key) "WRITING SCRIPT…" else "WRITE SCRIPT", color = Gold) }
                                    } else {
                                        Spacer(Modifier.height(6.dp))
                                        Text(sc.script, color = Color.White, fontSize = 13.sp)
                                        if (sc.hashtags.isNotEmpty()) Text(sc.hashtags.joinToString(" "), color = Gold, fontSize = 12.sp)
                                        sc.sources.forEach { (title, url) ->
                                            Text("Source: $title", color = Dim, fontSize = 11.sp, maxLines = 1,
                                                modifier = Modifier.clickable(enabled = url.isNotBlank()) { openUrl(context, url) })
                                        }
                                        if (sc.verify.isNotBlank()) Text(sc.verify, color = Dim, fontSize = 11.sp)
                                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                            TextButton(onClick = { sendToGenerate(sc) }) { Text("OPEN IN GENERATE", color = Gold, fontSize = 12.sp) }
                                            TextButton(onClick = {
                                                copy(context, "${sc.title}\n\n${sc.script}\n\n${sc.description}\n\n${sc.hashtags.joinToString(" ")}")
                                                notice = "Script, description and hashtags copied"
                                            }) { Text("COPY", color = Gold, fontSize = 12.sp) }
                                        }
                                    }
                                }
                            }
                            val chosen = list.indices.filter { picked["${t.id}|$it"] == true }
                            Button(enabled = chosen.isNotEmpty() && working == null, modifier = Modifier.fillMaxWidth().height(52.dp), onClick = {
                                working = "${t.id}|produce"; error = null
                                scope.launch {
                                    runCatching {
                                        client.trendProduce(t.id, chosen.map { list[it] to (scripts["${t.id}|$it"]?.script ?: "") }, studioDefaults(context))
                                    }.onSuccess { n ->
                                        notice = "Queued $n video${if (n == 1) "" else "s"} about “${t.title}”. They render one after another - follow them in Generate or Library."
                                    }.onFailure { error = it.message }
                                    working = null
                                }
                            }) { Text(if (working == "${t.id}|produce") "QUEUING…" else "MAKE ${chosen.size} VIDEO${if (chosen.size == 1) "" else "S"}") }
                            Text("Uses your voice, look and AI-video choice from Generate. Ideas with a written script are narrated word for word.",
                                color = Dim, fontSize = 11.sp)
                        }
                    }
                }
            }
        }
        if (scan != null && scan!!.items.isEmpty()) item { Text("Nothing trending found for this filter. Try another niche or period.", color = Dim) }
        if (!youtube) item {
            Text("Tip: add a free YouTube Data API key on the worker (CF_YOUTUBE_API_KEY) to include YouTube's most-watched videos.",
                color = Dim, fontSize = 11.sp)
        }
    }
}

private fun TrendScript.seconds(): Int = (script.split(Regex("\\s+")).count { it.isNotBlank() } / 2.5).toInt()

private fun heatLabel(heat: Int) = when {
    heat >= 75 -> "🔥 HOT $heat"
    heat >= 40 -> "↗ RISING $heat"
    else -> "• $heat"
}

private fun metricText(m: Map<String, Long>): String {
    val top = m.maxByOrNull { it.value } ?: return ""
    return " • ${compact(top.value)} ${top.key}"
}

private fun compact(n: Long): String = when {
    n >= 1_000_000_000 -> "%.1fB".format(n / 1e9)
    n >= 1_000_000 -> "%.1fM".format(n / 1e6)
    n >= 1_000 -> "%.1fK".format(n / 1e3)
    else -> n.toString()
}

private fun openUrl(context: Context, url: String) {
    runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
}

private fun copy(context: Context, text: String) {
    (context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager).setPrimaryClip(ClipData.newPlainText("CreatorForge script", text))
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Chips(options: List<Pair<String, String>>, selected: String, small: Boolean = false, onSelect: (String) -> Unit) {
    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        options.forEach { (id, label) ->
            FilterChip(selected = id == selected, onClick = { onSelect(id) },
                label = { Text(label, fontSize = if (small) 11.sp else 13.sp) },
                colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Gold, selectedLabelColor = Color.Black))
        }
    }
}

/** The look, voice and AI-video choice from the Generate tab, reused by Trends, the Director and Autopilot. */
internal fun studioDefaults(context: Context): JSONObject {
    val g = context.getSharedPreferences("creatorforge_generate", 0)
    val scopeVideo = g.getString("video_scope", "off").orEmpty()
    return JSONObject().put("voice", g.getString("voice", "").orEmpty()).put("style", g.getString("style", "").orEmpty())
        .put("pacing", g.getString("pacing", "medium").orEmpty()).put("music", g.getBoolean("music", true))
        .put("captions", g.getBoolean("captions", true)).put("sfx", g.getBoolean("sfx", true))
        .put("auto_edit", g.getBoolean("auto_edit", true))
        .put("motion", if (scopeVideo == "off") "stills" else "ai_video").put("ai_video_scenes", if (scopeVideo == "all") "all" else "hook")
}
