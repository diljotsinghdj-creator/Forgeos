package com.creatorforge.app.production

import androidx.compose.foundation.background
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
import com.creatorforge.app.studio.ChannelStats
import com.creatorforge.app.studio.HttpFetcher
import com.creatorforge.app.studio.YouTubeStats
import kotlinx.coroutines.launch

/** Analytics: public YouTube numbers for each channel, what's working, and that lesson fed back into planning. */
@Composable
fun AnalyticsScreen(onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val store = remember { StudioHub.channels(context) }
    var channels by remember { mutableStateOf(store.list()) }
    var selected by remember { mutableStateOf(channels.firstOrNull()?.id) }
    var stats by remember { mutableStateOf<ChannelStats?>(null) }
    var insights by remember { mutableStateOf<List<String>>(emptyList()) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val ch = channels.firstOrNull { it.id == selected }
    var handle by remember(selected) { mutableStateOf(ch?.youtube.orEmpty()) }

    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Lead("See which videos win, and let CreatorForge plan more of what works. Uses your free YouTube API key - no sign-in.")
        if (StudioHub.youtubeKey(context).isBlank()) Section("ADD YOUR YOUTUBE KEY", "Settings → YouTube trends. It's free (Google Cloud → YouTube Data API v3).") {
            Button(onOpenSettings) { Text("OPEN SETTINGS") }
        }
        if (channels.isEmpty()) { Section("NO CHANNELS YET", "Add a channel in Channels first.") {}; return@Column }
        Chips(channels.map { it.id to it.name }, selected ?: "") { selected = it; stats = null; insights = emptyList() }
        ch?.let { c ->
            Section("YOUTUBE CHANNEL") {
                OutlinedTextField(handle, { handle = it }, Modifier.fillMaxWidth(), singleLine = true, label = { Text("Handle, e.g. @darkhistory") })
                Button(enabled = !busy && handle.isNotBlank(), onClick = {
                    busy = true; error = null
                    scope.launch {
                        runCatching {
                            val s = studio { YouTubeStats.fetch(HttpFetcher(), handle, StudioHub.youtubeKey(context)) }
                            val tips = studio { StudioHub.brain(context).insights(s) }
                            s to tips
                        }.onSuccess { (s, tips) ->
                            stats = s; insights = tips
                            channels = store.upsert(c.copy(youtube = handle.trim(), insights = tips.joinToString(" ")))
                        }.onFailure { error = it.message }
                        busy = false
                    }
                }) { Text(if (busy) "READING…" else "ANALYSE") }
                Note(error, true)
            }
            val s = stats
            if (s != null) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Stat("Subscribers", s.subscribers, Modifier.weight(1f))
                    Stat("Total views", s.totalViews, Modifier.weight(1f))
                    Stat("Videos read", s.videos.size.toLong(), Modifier.weight(1f))
                }
                Section("WHAT'S WORKING", "Saved to ${c.name} - weekly plans now lean on this") {
                    insights.forEach { Text("• $it", color = Color.White, fontSize = 13.sp) }
                }
                Section("TOP VIDEOS") {
                    val max = s.videos.maxOfOrNull { it.views }?.coerceAtLeast(1) ?: 1
                    s.videos.sortedByDescending { it.views }.take(10).forEach { v ->
                        Text(v.title, color = Color.White, fontSize = 13.sp, maxLines = 1)
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(Modifier.weight(1f).height(6.dp).clip(RoundedCornerShape(3.dp)).background(Color(0xFF2A2A2A))) {
                                Box(Modifier.fillMaxWidth((v.views.toFloat() / max).coerceIn(0.02f, 1f)).fillMaxHeight().background(UiGold))
                            }
                            Text("  ${compactNum(v.views)} • ${if (v.isShort) "Short" else "${v.seconds / 60}m"}", color = UiDim, fontSize = 11.sp)
                        }
                    }
                }
            } else if (c.insights.isNotBlank()) {
                Section("LAST INSIGHTS") { Text(c.insights, color = Color.LightGray, fontSize = 13.sp) }
            }
            Text("Watch time and retention need a YouTube sign-in (coming with direct upload). TikTok doesn't offer public stats to apps.", color = UiDim, fontSize = 11.sp)
        }
    }
}

@Composable
private fun Stat(label: String, value: Long, modifier: Modifier) {
    Column(modifier.clip(RoundedCornerShape(12.dp)).background(UiCard).padding(12.dp)) {
        Text(compactNum(value), color = UiGold, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text(label, color = UiDim, fontSize = 11.sp)
    }
}

internal fun compactNum(n: Long): String = when {
    n >= 1_000_000 -> "%.1fM".format(n / 1e6)
    n >= 1_000 -> "%.1fK".format(n / 1e3)
    else -> n.toString()
}
