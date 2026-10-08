package com.creatorforge.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.generation.*
import com.creatorforge.app.security.SecureTokenStore
import com.creatorforge.app.production.GenerateScreen
import com.creatorforge.app.production.LibraryScreen
import com.creatorforge.app.production.TrendsScreen
import com.creatorforge.app.production.DirectorScreen
import com.creatorforge.app.production.ChannelsScreen
import com.creatorforge.app.production.WorkerAuth
import kotlinx.coroutines.launch

private val Gold=Color(0xFFD4AF37); private val Black=Color(0xFF090909); private val Panel=Color(0xFF151515)
object PendingRoute{@Volatile var value:String?=null}
class MainActivity:ComponentActivity(){
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);takeLink(intent);setContent{CreatorForge()}}
 override fun onNewIntent(intent:android.content.Intent){super.onNewIntent(intent);takeLink(intent)}
 private fun takeLink(i:android.content.Intent?){i?.data?.takeIf{it.scheme=="creatorforge"}?.let{com.creatorforge.app.production.WorkerConnect.pending=it.toString()};i?.getStringExtra("route")?.let{PendingRoute.value=it}}
}

@Composable fun CreatorForge(){
 val context=androidx.compose.ui.platform.LocalContext.current
 remember{val app=context.applicationContext;com.creatorforge.app.production.ProductionClient.directorLlm={com.creatorforge.app.production.StudioHub.directorLlm(app)};com.creatorforge.app.production.ProductionClient.stockKey={com.creatorforge.app.production.StudioHub.stockKey(app)};0}; val secure=remember{SecureTokenStore(context).also{WorkerAuth.token=it.load("worker").orEmpty()}}
 val nav=remember{context.getSharedPreferences("creatorforge_nav",0)}
 var advanced by remember{mutableStateOf(nav.getBoolean("advanced",false))}
 val available=menuFor(advanced)
 var tab by remember{mutableIntStateOf(0)}
 var route by remember{mutableStateOf(nav.getString("route","trends")!!.let{r->Dests.moved[r]?.first?:r}.let{if(it in available)it else "trends"})}
 fun go(r:String){val (page,t)=Dests.moved[r]?:(r to 0);tab=t;route=if(page in menuFor(true))page else "trends";nav.edit().putString("route",route).apply()}
 var connectNote by remember{mutableStateOf<String?>(null)}; var settingsKey by remember{mutableIntStateOf(0)}
 val lifecycle=androidx.lifecycle.compose.LocalLifecycleOwner.current
 DisposableEffect(lifecycle){val obs=androidx.lifecycle.LifecycleEventObserver{_,e->if(e==androidx.lifecycle.Lifecycle.Event.ON_RESUME){PendingRoute.value?.let{r->PendingRoute.value=null;go(r)};com.creatorforge.app.production.WorkerConnect.pending?.let{link->com.creatorforge.app.production.WorkerConnect.pending=null;connectNote=com.creatorforge.app.production.WorkerConnect.apply(context,link);settingsKey++;go("settings")}}};lifecycle.lifecycle.addObserver(obs);onDispose{lifecycle.lifecycle.removeObserver(obs)}}
 MaterialTheme(colorScheme=darkColorScheme(primary=Gold,background=Black,surface=Panel)){
  AppShell(route,available,::go){
   val settings={go("settings")}; val generate={go("generate")}
   key(route){when(route){
    "trends"->TrendsScreen(onOpenSettings=settings,onOpenGenerate=generate,onOpenScripts={go("scripts")})
    "director"->DirectorScreen(onOpenGenerate=generate,onOpenSettings=settings,onOpenScripts={go("scripts")})
    "scripts"->TabbedPage(listOf("📝 Scripts","🪝 Hook Lab","🛡 Safety check"),tab,{tab=it}){t->when(t){
     1->com.creatorforge.app.production.HookLabScreen(settings)
     2->com.creatorforge.app.production.SafetyScreen(settings)
     else->com.creatorforge.app.production.ScriptsPanel(generate,settings)}}
    "thumbnails"->com.creatorforge.app.production.ThumbnailScreen(settings)
    "generate"->GenerateScreen(onOpenSettings=settings)
    "library"->LibraryScreen()
    "channels"->TabbedPage(listOf("📅 Channels","🗓 Calendar","🧩 Templates"),tab,{tab=it}){t->when(t){
     1->com.creatorforge.app.production.CalendarScreen{tab=0}
     2->com.creatorforge.app.production.TemplatesScreen{tab=0}
     else->ChannelsScreen(onOpenSettings=settings)}}
    "series"->com.creatorforge.app.production.SeriesScreen(settings,generate)
    "clipper"->com.creatorforge.app.production.ClipperScreen(settings)
    "dubbing"->com.creatorforge.app.production.DubbingScreen(settings)
    "analytics"->com.creatorforge.app.production.AnalyticsScreen(settings)
    "brand"->com.creatorforge.app.production.BrandKitScreen(settings)
    "team"->com.creatorforge.app.production.TeamScreen(settings)
    "cloud"->com.creatorforge.app.production.CloudScreen(settings)
    else->key(settingsKey){Settings(secure,connectNote,advanced,{on->advanced=on;nav.edit().putBoolean("advanced",on).apply()}){msg->connectNote=msg;settingsKey++}}
   }}
  }
 }
}

/** Sidebar pages; Team & Cloud only appear when Settings → Advanced is on. */
fun menuFor(advanced:Boolean)=Dests.all.filter{advanced||it.section!="ADVANCED"}.map{it.id}.toSet()

@Composable fun Settings(secure:SecureTokenStore,connectNote:String?=null,advanced:Boolean=false,onAdvanced:(Boolean)->Unit={},onConnected:(String)->Unit={}){
 val context=androidx.compose.ui.platform.LocalContext.current;val prefs=remember{context.getSharedPreferences("creatorforge_provider",0)};val scope=rememberCoroutineScope()
 var url by remember{mutableStateOf(prefs.getString("base_url","").orEmpty())};var savedUrl by remember{mutableStateOf(url)};var health by remember{mutableStateOf("Not tested")};var checking by remember{mutableStateOf(false)};var token by remember{mutableStateOf("")};var hasToken by remember{mutableStateOf(secure.has("worker"))}
 Column(Modifier.verticalScroll(rememberScrollState())){Text("Writing runs on your phone • the pod only makes videos",color=Color.LightGray,fontSize=13.sp);Spacer(Modifier.height(10.dp));com.creatorforge.app.production.AiSettingsCard(secure);Spacer(Modifier.height(12.dp));com.creatorforge.app.production.PodPowerCard();Spacer(Modifier.height(12.dp));connectNote?.let{Text(it,color=Gold)};com.creatorforge.app.production.WorkerQuickConnect{msg->onConnected(msg)};Spacer(Modifier.height(12.dp));if(advanced)Card{Column(Modifier.padding(16.dp)){Text("VIDEO WORKER - MANUAL SETUP",color=Gold);Text("Your GPU pod or PC. Trends, Director, Scripts and Channels work without it.");Spacer(Modifier.height(10.dp));OutlinedTextField(url,{url=it},Modifier.fillMaxWidth(),label={Text("Worker URL (http://… or https://…)")},singleLine=true);Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){Button(enabled=url.startsWith("http://")||url.startsWith("https://"),onClick={savedUrl=url.trim().trimEnd('/');prefs.edit().putString("base_url",savedUrl).apply();health="Saved • test connection next"}){Text("SAVE")};OutlinedButton(enabled=savedUrl.isNotBlank()&&!checking,onClick={checking=true;health="Checking…";scope.launch{val h=LocalWorkerClient(LocalProviderConfig(savedUrl)).health();health=if(h.ok)"ONLINE • token OK${h.version?.let{" • v$it"}?:""}" else if(h.message.startsWith("pod is"))"PROBLEM • ${h.message}" else "OFFLINE • ${h.message}";checking=false}}){Text(if(checking)"TESTING…" else "TEST CONNECTION")}};Text(if(savedUrl.isBlank())"Not configured" else "Configured: $savedUrl",color=if(savedUrl.isBlank())Color.Gray else Gold);Text(health,color=if(health.startsWith("ONLINE"))Gold else Color.LightGray);Spacer(Modifier.height(10.dp));OutlinedTextField(token,{token=it},Modifier.fillMaxWidth(),label={Text(if(hasToken)"Worker token (saved • enter to replace)" else "Worker token (CF_WORKER_TOKEN)")},singleLine=true,visualTransformation=androidx.compose.ui.text.input.PasswordVisualTransformation());Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){Button(enabled=token.isNotBlank(),onClick={secure.save("worker",token.trim());WorkerAuth.token=token.trim();token="";hasToken=true;health="Token saved (encrypted) • test connection next"}){Text("SAVE TOKEN")};if(hasToken)OutlinedButton(onClick={secure.clear("worker");WorkerAuth.token="";hasToken=false;health="Token removed"}){Text("REMOVE TOKEN")}};Text("Use https:// when the worker is reachable outside your home network.",color=Color.Gray,fontSize=12.sp)}};Spacer(Modifier.height(12.dp));Card{Row(Modifier.padding(16.dp),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically){Column(Modifier.weight(1f)){Text("ADVANCED",color=Gold);Text("Manual pod address & token, Team & Clients, Cloud Studio",color=Color.LightGray,fontSize=12.sp)};Switch(advanced,onAdvanced)}};Spacer(Modifier.height(12.dp));Text("CreatorForge ${com.creatorforge.app.BuildConfig.VERSION_NAME} • your studio, no credits required.",color=Gold);TextButton({com.creatorforge.app.production.openUrl(context,"https://github.com/diljotsinghdj-creator/Forgeos/actions/workflows/creatorforge.yml")}){Text("GET THE LATEST BUILD ↗",color=Gold)};Spacer(Modifier.height(24.dp))}
}
