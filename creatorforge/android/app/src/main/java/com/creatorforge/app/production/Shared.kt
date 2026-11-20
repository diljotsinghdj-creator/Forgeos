package com.creatorforge.app.production

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONObject

// Small helpers several screens share (moved here when the Trends screen was removed).

private val ChipGold = Color(0xFFD4AF37)

internal fun openUrl(context: Context, url: String) {
    runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun Chips(options: List<Pair<String, String>>, selected: String, small: Boolean = false, onSelect: (String) -> Unit) {
    Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
        options.forEach { (id, label) ->
            FilterChip(selected = id == selected, onClick = { onSelect(id) },
                label = { Text(label, fontSize = if (small) 11.sp else 13.sp) },
                colors = FilterChipDefaults.filterChipColors(selectedContainerColor = ChipGold, selectedLabelColor = Color.Black))
        }
    }
}

/** The look, voice and AI-video choice from the Generate tab, reused when the phone sends videos to the worker. */
internal fun studioDefaults(context: Context): JSONObject {
    val g = context.getSharedPreferences("creatorforge_generate", 0)
    val scopeVideo = g.getString("video_scope", "off").orEmpty()
    return JSONObject().put("voice", g.getString("voice", "").orEmpty()).put("style", g.getString("style", "").orEmpty())
        .put("pacing", g.getString("pacing", "medium").orEmpty()).put("music", g.getBoolean("music", true))
        .put("captions", g.getBoolean("captions", true)).put("sfx", g.getBoolean("sfx", true))
        .put("auto_edit", g.getBoolean("auto_edit", true))
        .put("motion", if (scopeVideo == "off") "stills" else "ai_video").put("ai_video_scenes", if (scopeVideo == "all") "all" else "hook")
}
