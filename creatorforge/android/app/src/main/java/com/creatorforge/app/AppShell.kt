package com.creatorforge.app

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
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
import com.creatorforge.app.production.StudioHub
import kotlinx.coroutines.launch

private val Gold = Color(0xFFD4AF37)
private val Dim = Color(0xFF9E9E9E)
private val Panel = Color(0xFF121212)

/** One place in the app. The sidebar lists them by section. */
data class Dest(val id: String, val icon: String, val label: String, val section: String)

object Dests {
    val all = listOf(
        Dest("trends", "📈", "Trends", "CREATE"),
        Dest("director", "💬", "Director", "CREATE"),
        Dest("scripts", "📝", "Scripts", "CREATE"),
        Dest("series", "📚", "Series", "CREATE"),
        Dest("thumbnails", "🖼", "Thumbnails", "CREATE"),
        Dest("generate", "🎬", "Generate", "PRODUCE"),
        Dest("library", "🗂", "Library", "PRODUCE"),
        Dest("clipper", "✂️", "Shorts Clipper", "PRODUCE"),
        Dest("dubbing", "🌍", "Dubbing", "PRODUCE"),
        Dest("channels", "📅", "Channels", "GROW"),
        Dest("analytics", "📊", "Analytics", "GROW"),
        Dest("brand", "🎨", "Brand Kits", "BRAND"),
        Dest("team", "👥", "Team & Clients", "ADVANCED"),
        Dest("cloud", "☁️", "Cloud Studio", "ADVANCED"),
        Dest("settings", "⚙", "Settings", "SETTINGS"),
    )
    /** Pages that now live as tabs inside another page: old route -> (page, tab). */
    val moved = mapOf("hooks" to ("scripts" to 1), "safety" to ("scripts" to 2), "calendar" to ("channels" to 1), "templates" to ("channels" to 2))
    operator fun get(id: String) = all.firstOrNull { it.id == id } ?: all[0]
}

/** Pill tabs across the top of a page that groups related tools (keeps the sidebar short). */
@Composable
fun TabbedPage(tabs: List<String>, selected: Int, onSelect: (Int) -> Unit, content: @Composable (Int) -> Unit) {
    Column(Modifier.fillMaxSize()) {
        Row(Modifier.horizontalScroll(rememberScrollState()).padding(bottom = 8.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            tabs.forEachIndexed { i, t -> FilterChip(selected = i == selected, onClick = { onSelect(i) }, label = { Text(t) }) }
        }
        Box(Modifier.weight(1f).fillMaxWidth()) { content(selected) }
    }
}

/** Clean shell: a slim top bar with the page name, and a sidebar with every tool grouped by what it's for. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppShell(route: String, available: Set<String>, onNavigate: (String) -> Unit, content: @Composable () -> Unit) {
    val drawer = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val dest = Dests[route]
    ModalNavigationDrawer(drawerState = drawer, drawerContent = {
        ModalDrawerSheet(drawerContainerColor = Panel, modifier = Modifier.width(290.dp)) {
            Column(Modifier.fillMaxHeight().verticalScroll(rememberScrollState()).padding(vertical = 12.dp)) {
                Column(Modifier.padding(horizontal = 20.dp, vertical = 8.dp)) {
                    Text("CREATORFORGE", color = Gold, fontSize = 22.sp, fontWeight = FontWeight.Black)
                    Text("Your faceless content studio", color = Dim, fontSize = 12.sp)
                    Spacer(Modifier.height(10.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        StatusPill(if (StudioHub.aiReady(context)) "Script AI on" else "Script AI off", StudioHub.aiReady(context))
                        StatusPill(if (StudioHub.hasWorker(context)) "Pod linked" else "No pod", StudioHub.hasWorker(context))
                    }
                }
                var last = ""
                Dests.all.filter { it.id in available }.forEach { d ->
                    if (d.section != last) {
                        last = d.section
                        Text(d.section, color = Dim, fontSize = 11.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 22.dp, top = 16.dp, bottom = 4.dp))
                    }
                    NavigationDrawerItem(
                        label = { Text(d.label, fontSize = 15.sp) }, icon = { Text(d.icon, fontSize = 18.sp) }, selected = d.id == route,
                        onClick = { onNavigate(d.id); scope.launch { drawer.close() } },
                        colors = NavigationDrawerItemDefaults.colors(selectedContainerColor = Color(0xFF2A2412), selectedTextColor = Gold, unselectedContainerColor = Color.Transparent),
                        modifier = Modifier.padding(horizontal = 10.dp).height(46.dp)
                    )
                }
            }
        }
    }) {
        Scaffold(containerColor = Color(0xFF090909), topBar = {
            TopAppBar(
                title = { Row(verticalAlignment = Alignment.CenterVertically) { Text(dest.icon, fontSize = 18.sp); Spacer(Modifier.width(8.dp)); Text(dest.label, fontWeight = FontWeight.SemiBold) } },
                navigationIcon = { IconButton({ scope.launch { drawer.open() } }) { Text("☰", fontSize = 22.sp, color = Gold) } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF090909), titleContentColor = Color.White)
            )
        }) { pad ->
            Box(Modifier.fillMaxSize().padding(pad).padding(horizontal = 16.dp, vertical = 4.dp)) { content() }
        }
    }
}

@Composable
private fun StatusPill(text: String, ok: Boolean) {
    Text(text, fontSize = 11.sp, color = if (ok) Color.Black else Color.LightGray,
        modifier = Modifier.clip(RoundedCornerShape(10.dp)).background(if (ok) Gold else Color(0xFF2A2A2A)).padding(horizontal = 8.dp, vertical = 3.dp))
}
