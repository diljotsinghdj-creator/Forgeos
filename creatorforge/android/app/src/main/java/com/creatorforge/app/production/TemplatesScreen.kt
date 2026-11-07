package com.creatorforge.app.production

import android.content.Intent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.studio.ChannelTemplate
import com.creatorforge.app.studio.Niches
import com.creatorforge.app.studio.Styles
import java.util.UUID

/** Templates: ready-made channel recipes. One tap creates a channel with its look, rhythm, tone and brand colours. */
@Composable
fun TemplatesScreen(onOpenChannels: () -> Unit) {
    val context = LocalContext.current
    val store = remember { StudioHub.templates(context) }
    var mine by remember { mutableStateOf(store.list()) }
    var code by remember { mutableStateOf("") }
    var message by remember { mutableStateOf<String?>(null) }

    fun use(t: ChannelTemplate) {
        val id = UUID.randomUUID().toString().take(12)
        StudioHub.channels(context).upsert(t.toChannel(id).copy(brand = t.brand()))
        message = "Created the “${t.name}” channel - open Channels to plan its first week"
    }

    fun share(t: ChannelTemplate) {
        context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain")
            .putExtra(Intent.EXTRA_TEXT, "CreatorForge channel template “${t.name}”:\n${t.shareCode()}"), null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), contentPadding = PaddingValues(bottom = 24.dp)) {
        item { Lead("Start a channel in one tap, or share your own recipe as a code. (An online marketplace comes with the hosted version.)") }
        item {
            Section("IMPORT A CODE") {
                OutlinedTextField(code, { code = it }, Modifier.fillMaxWidth(), label = { Text("Paste a CFT1:… code") }, maxLines = 3)
                Button(enabled = code.isNotBlank(), onClick = {
                    runCatching { ChannelTemplate.fromShareCode(code.substringAfter("\n").ifBlank { code }.trim().let { if ("CFT1:" in it) it.substring(it.indexOf("CFT1:")) else it }) }
                        .onSuccess { t -> mine = store.upsert(t.copy(id = UUID.randomUUID().toString().take(12))); code = ""; message = "Imported “${t.name}”" }
                        .onFailure { message = it.message }
                }) { Text("IMPORT") }
            }
        }
        item {
            Section("SAVE A CHANNEL AS A TEMPLATE") {
                val channels = remember { StudioHub.channels(context).list() }
                if (channels.isEmpty()) Text("No channels yet.", color = UiDim, fontSize = 12.sp)
                channels.forEach { c ->
                    TextButton({
                        val t = ChannelTemplate(UUID.randomUUID().toString().take(12), c.name, c.niche, c.style, c.format, c.perWeek, c.tone, c.audience,
                            c.brand.captionColor, c.brand.highlightColor, "My template")
                        mine = store.upsert(t); message = "Saved “${c.name}” as a template"
                    }) { Text("+ ${c.name}", color = UiGold) }
                }
            }
        }
        item { Note(message) }
        if (mine.isNotEmpty()) item { Text("MY TEMPLATES", color = UiDim, fontSize = 12.sp) }
        items(mine, key = { "m" + it.id }) { t -> TemplateCard(t, { use(t) }, { share(t) }) { mine = store.delete(t.id) } }
        item { Text("STARTER PACK", color = UiDim, fontSize = 12.sp) }
        items(ChannelTemplate.starters, key = { it.id }) { t -> TemplateCard(t, { use(t) }, { share(t) }, null) }
        item { TextButton(onOpenChannels) { Text("OPEN CHANNELS →", color = UiGold) } }
    }
}

@Composable
private fun TemplateCard(t: ChannelTemplate, onUse: () -> Unit, onShare: () -> Unit, onDelete: (() -> Unit)?) {
    Section(t.name, "${Niches[t.niche].name} • ${Styles.name(t.style)} • ${t.perWeek}/week • ${t.format}") {
        if (t.note.isNotBlank()) Text(t.note, color = Color.LightGray, fontSize = 13.sp)
        Text("Tone: ${t.tone}", color = UiDim, fontSize = 12.sp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onUse) { Text("USE") }
            OutlinedButton(onShare) { Text("SHARE CODE") }
            onDelete?.let { TextButton(it) { Text("DELETE", color = UiDanger) } }
        }
    }
}
