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
import coil.compose.AsyncImage
import com.creatorforge.app.data.ProjectStore
import com.creatorforge.app.generation.GenerationResult
import com.creatorforge.app.generation.*
import com.creatorforge.app.model.*
import com.creatorforge.app.security.SecureTokenStore
import com.creatorforge.app.timeline.TimelineEngine
import com.creatorforge.app.render.*
import com.creatorforge.app.production.GenerateScreen
import com.creatorforge.app.production.LibraryScreen
import com.creatorforge.app.production.TrendsScreen
import com.creatorforge.app.production.DirectorScreen
import com.creatorforge.app.production.ChannelsScreen
import com.creatorforge.app.production.WorkerAuth
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID

private val Gold=Color(0xFFD4AF37); private val Black=Color(0xFF090909); private val Panel=Color(0xFF151515)
object PendingRoute{@Volatile var value:String?=null}
class MainActivity:ComponentActivity(){
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState);takeLink(intent);setContent{CreatorForge()}}
 override fun onNewIntent(intent:android.content.Intent){super.onNewIntent(intent);takeLink(intent)}
 private fun takeLink(i:android.content.Intent?){i?.data?.takeIf{it.scheme=="creatorforge"}?.let{com.creatorforge.app.production.WorkerConnect.pending=it.toString()};i?.getStringExtra("route")?.let{PendingRoute.value=it}}
}

@Composable fun CreatorForge(){
 val context=androidx.compose.ui.platform.LocalContext.current; val store=remember{ProjectStore(context)}; val secure=remember{SecureTokenStore(context).also{WorkerAuth.token=it.load("worker").orEmpty()}}
 val nav=remember{context.getSharedPreferences("creatorforge_nav",0)}
 var projects by remember{mutableStateOf(store.load())}
 var route by remember{mutableStateOf(nav.getString("route","trends")!!.let{if(it in AVAILABLE)it else "trends"})}
 fun go(r:String){route=r;nav.edit().putString("route",r).apply()}
 fun persist(next:List<CreatorProject>){projects=next;store.save(next)}
 var connectNote by remember{mutableStateOf<String?>(null)}; var settingsKey by remember{mutableIntStateOf(0)}
 val lifecycle=androidx.lifecycle.compose.LocalLifecycleOwner.current
 DisposableEffect(lifecycle){val obs=androidx.lifecycle.LifecycleEventObserver{_,e->if(e==androidx.lifecycle.Lifecycle.Event.ON_RESUME){PendingRoute.value?.let{r->PendingRoute.value=null;if(r in AVAILABLE)go(r)};com.creatorforge.app.production.WorkerConnect.pending?.let{link->com.creatorforge.app.production.WorkerConnect.pending=null;connectNote=com.creatorforge.app.production.WorkerConnect.apply(context,link);settingsKey++;go("settings")}}};lifecycle.lifecycle.addObserver(obs);onDispose{lifecycle.lifecycle.removeObserver(obs)}}
 MaterialTheme(colorScheme=darkColorScheme(primary=Gold,background=Black,surface=Panel)){
  AppShell(route,AVAILABLE,::go){
   val settings={go("settings")}; val generate={go("generate")}
   key(route){when(route){
    "trends"->TrendsScreen(onOpenSettings=settings,onOpenGenerate=generate,onOpenScripts={go("scripts")})
    "director"->DirectorScreen(onOpenGenerate=generate,onOpenSettings=settings,onOpenScripts={go("scripts")})
    "scripts"->com.creatorforge.app.production.ScriptsPanel(generate,settings)
    "thumbnails"->com.creatorforge.app.production.ThumbnailScreen(settings)
    "generate"->GenerateScreen(onOpenSettings=settings)
    "library"->LibraryScreen()
    "phone"->PhoneStudio(projects,secure,::persist)
    "channels"->ChannelsScreen(onOpenSettings=settings)
    "series"->com.creatorforge.app.production.SeriesScreen(settings,generate)
    "hooks"->com.creatorforge.app.production.HookLabScreen(settings)
    "clipper"->com.creatorforge.app.production.ClipperScreen(settings)
    "dubbing"->com.creatorforge.app.production.DubbingScreen(settings)
    "calendar"->com.creatorforge.app.production.CalendarScreen{go("channels")}
    "analytics"->com.creatorforge.app.production.AnalyticsScreen(settings)
    "templates"->com.creatorforge.app.production.TemplatesScreen{go("channels")}
    "brand"->com.creatorforge.app.production.BrandKitScreen(settings)
    "safety"->com.creatorforge.app.production.SafetyScreen(settings)
    "team"->com.creatorforge.app.production.TeamScreen(settings)
    "cloud"->com.creatorforge.app.production.CloudScreen(settings)
    else->key(settingsKey){Settings(secure,connectNote){msg->connectNote=msg;settingsKey++}}
   }}
  }
 }
}

/** Every sidebar entry is built. */
val AVAILABLE=Dests.all.map{it.id}.toSet()

/** The original on-device tools (make a video entirely on this phone), grouped under one tab. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable fun PhoneStudio(projects:List<CreatorProject>,secure:SecureTokenStore,persist:(List<CreatorProject>)->Unit){
 var sub by remember{mutableIntStateOf(0)}; var list by remember{mutableStateOf(projects)}
 fun save(next:List<CreatorProject>){list=next;persist(next)}
 Column{Text("Make a simple video entirely on this phone - no pod, no internet.",color=Color.LightGray,fontSize=13.sp)
  Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(6.dp)){listOf("Create","Projects","Export").forEachIndexed{i,n->FilterChip(selected=sub==i,onClick={sub=i},label={Text(n)})}}
  Spacer(Modifier.height(8.dp))
  when(sub){0->Create{p->save(list+p);sub=1};1->Projects(list,secure,::save);else->Studio(list)}}
}
@Composable fun Header(t:String,s:String){Column{Text(t,color=Gold,fontSize=18.sp);Text(s,color=Color.LightGray);Spacer(Modifier.height(18.dp))}}
@Composable fun Home(count:Int){Column{Header("CREATORFORGE","AI filmmaking workspace");Card{Column(Modifier.padding(18.dp)){Text("RC10.3 • SCROLLABLE EXPORT STUDIO",color=Gold);Text("$count saved projects");Text("Timeline • captions • synchronized scene timing • persistent recovery queue")}}}}
@Composable fun Create(done:(CreatorProject)->Unit){var prompt by remember{mutableStateOf("")};var long by remember{mutableStateOf(false)};var square by remember{mutableStateOf(false)};Column{Header("CREATE","Paste a script - each sentence group becomes a scene");OutlinedTextField(prompt,{prompt=it},Modifier.fillMaxWidth(),label={Text("Your script (narration)")},minLines=5);Row{Switch(long,{long=it;if(it)square=false});Text(if(long)" Long-form 16:9" else " Short-form 9:16",Modifier.padding(top=12.dp))};Row{Switch(square,{square=it;if(it)long=false});Text(" Square 1:1",Modifier.padding(top=12.dp))};Button(enabled=prompt.isNotBlank(),onClick={val beats=com.creatorforge.app.script.ScriptSplitter.split(prompt,if(long)20 else 10);if(beats.isEmpty())return@Button;done(CreatorProject(UUID.randomUUID().toString(),com.creatorforge.app.script.ScriptSplitter.title(prompt),if(long)ProjectType.LONG_FORM else ProjectType.SHORT_FORM,if(square)AspectRatio.SQUARE_1_1 else if(long)AspectRatio.LANDSCAPE_16_9 else AspectRatio.VERTICAL_9_16,prompt,beats.mapIndexed{i,b->Scene(UUID.randomUUID().toString(),i+1,"Scene ${i+1}",b.narration,"Hyper-realistic cinematic photograph illustrating: ${b.narration}",b.seconds)}))}){Text("CREATE PROJECT")}}}

@Composable fun Projects(projects:List<CreatorProject>,secure:SecureTokenStore,persist:(List<CreatorProject>)->Unit){
 val context=androidx.compose.ui.platform.LocalContext.current; val prefs=remember{context.getSharedPreferences("creatorforge_provider",0)}; val scope=rememberCoroutineScope(); var busy by remember{mutableStateOf<String?>(null)}; var message by remember{mutableStateOf<String?>(null)}
 Column{Header("PROJECTS","Generate verified scene visuals");message?.let{Text(it,color=if(it.startsWith("PASS"))Gold else MaterialTheme.colorScheme.error);Spacer(Modifier.height(8.dp))};if(projects.isEmpty())Text("No projects yet.") else LazyColumn(verticalArrangement=Arrangement.spacedBy(12.dp)){items(projects,key={it.id}){p->Card{Column(Modifier.padding(16.dp)){Text(p.title,color=Gold,fontSize=20.sp);Text("${p.scenes.size} scenes");Button(enabled=busy==null,onClick={busy="device_${p.id}";message="Making on this phone…";scope.launch{val studio=com.creatorforge.app.device.DeviceStudio(context);try{val made=studio.makeProject(p){m->message=m};persist(projects.map{if(it.id==p.id)made else it});message="PASS: device voice + title cards ready for all ${made.scenes.size} scenes - open Studio and EXPORT MP4"}catch(e:Exception){message="FAILED: ${e.message}"}finally{studio.close();busy=null}}}){Text(if(busy=="device_${p.id}")"MAKING ON THIS PHONE…" else "MAKE ON THIS PHONE (NO WORKER)")};Text("Uses Android's built-in voice and styled title cards. AI images and voices still need the worker.",color=Color.Gray,fontSize=12.sp);ProjectAdmin(p,projects,persist);Spacer(Modifier.height(8.dp));p.scenes.sortedBy{it.order}.forEach{s->HorizontalDivider();Spacer(Modifier.height(8.dp));Text("${s.order}. ${s.title}",color=Gold);Text(s.visualPrompt,color=Color.LightGray);Text("STATE: ${s.status}",color=when(s.status){SceneStatus.READY->Gold;SceneStatus.FAILED->MaterialTheme.colorScheme.error;else->Color.Gray});s.visualAssetPath?.let{path->Spacer(Modifier.height(8.dp));AsyncImage(model=File(path),contentDescription="Generated scene ${s.order}",modifier=Modifier.fillMaxWidth().height(180.dp))};Button(enabled=busy==null,onClick={val base=prefs.getString("base_url","").orEmpty();if(base.isBlank()){message="FAILED: Configure local provider URL in Settings";return@Button};busy=s.id;persist(projects.map{proj->if(proj.id!=p.id)proj else proj.copy(scenes=proj.scenes.map{scene->if(scene.id==s.id)scene.copy(status=SceneStatus.GENERATING) else scene})});message="Generating scene ${s.order} locally…";scope.launch{val provider=SelfHostedImageProvider(context,LocalProviderConfig(base));when(val r=provider.generate(s.visualPrompt,p.aspectRatio)){is GenerationResult.Success->{persist(storeScene(projects,p.id,s.id,SceneStatus.READY,r.file.absolutePath));message="PASS: verified local image saved for scene ${s.order}"};is GenerationResult.Failure->{persist(storeScene(projects,p.id,s.id,SceneStatus.FAILED,null));message="FAILED: ${r.message}"}};busy=null}}){Text(if(busy==s.id)"GENERATING…" else if(s.visualAssetPath!=null)"REGENERATE LOCAL IMAGE" else "GENERATE LOCAL IMAGE")};Spacer(Modifier.height(8.dp));Button(enabled=busy==null,onClick=narration@{val base=prefs.getString("base_url","").orEmpty();if(base.isBlank()){message="FAILED: Configure local provider URL in Settings";return@narration};busy="voice_${s.id}";message="Generating narration ${s.order} locally…";scope.launch{when(val r=SelfHostedVoiceEngine(context,LocalProviderConfig(base)).generate(s.narration)){is GenerationResult.Success->{persist(storeAudio(projects,p.id,s.id,r.file.absolutePath));message="PASS: verified local WAV saved for scene ${s.order}"};is GenerationResult.Failure->{message="FAILED: ${r.message}"}};busy=null}}){Text(if(busy=="voice_${s.id}")"GENERATING VOICE…" else if(s.audioAssetPath!=null)"REGENERATE NARRATION" else "GENERATE NARRATION")};s.audioAssetPath?.let{Text("Narration: READY",color=Gold,fontSize=12.sp)};Spacer(Modifier.height(8.dp))}}}}}}
}
fun storeScene(projects:List<CreatorProject>,projectId:String,sceneId:String,status:SceneStatus,path:String?)=projects.map{p->if(p.id!=projectId)p else p.copy(scenes=p.scenes.map{s->if(s.id==sceneId)s.copy(status=status,visualAssetPath=path?:s.visualAssetPath) else s})}
fun storeAudio(projects:List<CreatorProject>,projectId:String,sceneId:String,path:String)=projects.map{p->if(p.id!=projectId)p else p.copy(scenes=p.scenes.map{s->if(s.id==sceneId)s.copy(audioAssetPath=path) else s})}

@Composable fun Settings(secure:SecureTokenStore,connectNote:String?=null,onConnected:(String)->Unit={}){
 val context=androidx.compose.ui.platform.LocalContext.current;val prefs=remember{context.getSharedPreferences("creatorforge_provider",0)};val scope=rememberCoroutineScope()
 var url by remember{mutableStateOf(prefs.getString("base_url","").orEmpty())};var savedUrl by remember{mutableStateOf(url)};var health by remember{mutableStateOf("Not tested")};var checking by remember{mutableStateOf(false)};var token by remember{mutableStateOf("")};var hasToken by remember{mutableStateOf(secure.has("worker"))}
 Column(Modifier.verticalScroll(rememberScrollState())){Text("Writing runs on your phone • the pod only makes videos",color=Color.LightGray,fontSize=13.sp);Spacer(Modifier.height(10.dp));com.creatorforge.app.production.AiSettingsCard(secure);Spacer(Modifier.height(12.dp));com.creatorforge.app.production.PodPowerCard();Spacer(Modifier.height(12.dp));connectNote?.let{Text(it,color=Gold)};com.creatorforge.app.production.WorkerQuickConnect{msg->onConnected(msg)};Spacer(Modifier.height(12.dp));Card{Column(Modifier.padding(16.dp)){Text("VIDEO WORKER (only needed to make videos)",color=Gold);Text("Your GPU pod or PC. Trends, Director, Scripts and Channels work without it.");Spacer(Modifier.height(10.dp));OutlinedTextField(url,{url=it},Modifier.fillMaxWidth(),label={Text("Worker URL (http://… or https://…)")},singleLine=true);Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){Button(enabled=url.startsWith("http://")||url.startsWith("https://"),onClick={savedUrl=url.trim().trimEnd('/');prefs.edit().putString("base_url",savedUrl).apply();health="Saved • test connection next"}){Text("SAVE")};OutlinedButton(enabled=savedUrl.isNotBlank()&&!checking,onClick={checking=true;health="Checking…";scope.launch{val h=LocalWorkerClient(LocalProviderConfig(savedUrl)).health();health=if(h.ok)"ONLINE • token OK${h.version?.let{" • v$it"}?:""}" else if(h.message.startsWith("pod is up"))"PROBLEM • ${h.message}" else "OFFLINE • ${h.message}";checking=false}}){Text(if(checking)"TESTING…" else "TEST CONNECTION")}};Text(if(savedUrl.isBlank())"Not configured" else "Configured: $savedUrl",color=if(savedUrl.isBlank())Color.Gray else Gold);Text(health,color=if(health.startsWith("ONLINE"))Gold else Color.LightGray);Spacer(Modifier.height(10.dp));OutlinedTextField(token,{token=it},Modifier.fillMaxWidth(),label={Text(if(hasToken)"Worker token (saved • enter to replace)" else "Worker token (CF_WORKER_TOKEN)")},singleLine=true,visualTransformation=androidx.compose.ui.text.input.PasswordVisualTransformation());Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){Button(enabled=token.isNotBlank(),onClick={secure.save("worker",token.trim());WorkerAuth.token=token.trim();token="";hasToken=true;health="Token saved (encrypted) • test connection next"}){Text("SAVE TOKEN")};if(hasToken)OutlinedButton(onClick={secure.clear("worker");WorkerAuth.token="";hasToken=false;health="Token removed"}){Text("REMOVE TOKEN")}};Text("Use https:// when the worker is reachable outside your home network.",color=Color.Gray,fontSize=12.sp)}};Spacer(Modifier.height(12.dp));Text("CreatorForge ${com.creatorforge.app.BuildConfig.VERSION_NAME} • your studio, no credits required.",color=Gold);TextButton({com.creatorforge.app.production.openUrl(context,"https://github.com/diljotsinghdj-creator/Forgeos/actions/workflows/creatorforge.yml")}){Text("GET THE LATEST BUILD ↗",color=Gold)};Spacer(Modifier.height(24.dp))}
}
@Composable fun Studio(projects:List<CreatorProject>){
 val context=androidx.compose.ui.platform.LocalContext.current
 val scope=rememberCoroutineScope()
 var exportMessage by remember{mutableStateOf<String?>(null)}
 var exporting by remember{mutableStateOf(false)}
 var exported by remember{mutableStateOf<File?>(null)}
 var whooshes by remember{mutableStateOf(true)}
 var selectedId by remember(projects){mutableStateOf(projects.lastOrNull()?.id)}
 val project=projects.firstOrNull{it.id==selectedId}
 Column{
  Header("STUDIO","Timeline • captions • render readiness")
  if(projects.isEmpty()){Text("Create a project first.",color=Color.LightGray);return@Column}
  if(projects.size>1){
   Text("PROJECT",color=Gold)
   projects.forEach{p->OutlinedButton(onClick={selectedId=p.id},modifier=Modifier.fillMaxWidth()){Text(if(p.id==selectedId)"◆ ${p.title}" else p.title)}}
   Spacer(Modifier.height(8.dp))
  }
  project?.let{p->
   val timeline=remember(p){TimelineEngine.build(p)}
   val ready=p.scenes.count{it.status==SceneStatus.READY && it.visualAssetPath!=null}
   val voiced=p.scenes.count{!it.audioAssetPath.isNullOrBlank() && File(it.audioAssetPath!!).isFile}
   Card{Column(Modifier.padding(16.dp)){
    Text(p.title,color=Gold,fontSize=20.sp)
    Text("${p.scenes.size} scenes • ${timeline.durationMs/1000}s timeline")
    Text("$ready/${p.scenes.size} visual assets ready",color=Color.LightGray)
    Text("$voiced/${p.scenes.size} narration assets ready",color=Color.LightGray)
    Spacer(Modifier.height(10.dp))
    LinearProgressIndicator(progress={if(p.scenes.isEmpty())0f else ready.toFloat()/p.scenes.size},modifier=Modifier.fillMaxWidth())
   }}
   Spacer(Modifier.height(12.dp))
   Text("TIMELINE",color=Gold)
   LazyColumn(modifier=Modifier.fillMaxWidth().weight(1f),verticalArrangement=Arrangement.spacedBy(8.dp),contentPadding=PaddingValues(bottom=24.dp)){
    items(timeline.clips,key={it.sceneId}){clip->
     Card(Modifier.fillMaxWidth()){Column(Modifier.padding(12.dp)){
      Text("Scene ${clip.order}  •  ${clip.startMs/1000}s–${clip.endMs/1000}s",color=Gold)
      val scene=p.scenes.firstOrNull{it.id==clip.sceneId}; Text("Visual: ${scene?.status?:SceneStatus.PLANNED}",color=if(scene?.status==SceneStatus.FAILED)MaterialTheme.colorScheme.error else Color.LightGray)
      Text("Captions: ${clip.captions.size} cues",color=Color.LightGray)
      clip.captions.take(2).forEach{cue->Text("“${cue.text}”",fontSize=12.sp,color=Color.Gray)}
     }}
    }
    item{
     Spacer(Modifier.height(4.dp))
     val exportReady=ready==p.scenes.size && voiced==p.scenes.size && p.scenes.isNotEmpty()
     Row{Switch(whooshes,{whooshes=it});Text(" Whoosh on scene changes",Modifier.padding(top=12.dp),color=Color.LightGray)}
     Button(enabled=exportReady&&!exporting,onClick={
      exporting=true;exported=null;exportMessage="Validating export…"
      scope.launch{
       val output=File(context.getExternalFilesDir(null)?:context.filesDir,"CreatorForge_${p.id.take(8)}.mp4")
       val exporter=AvExportCoordinator(AndroidMediaCodecVideoRenderer(),AndroidAacNarrationComposer(whooshes=whooshes))
       val result=exporter.export(timeline,RenderRequest(p.id,output.absolutePath,quality=RenderQuality.forAspect(p.aspectRatio)),onProgress={pr->exportMessage="${pr.message} • ${(pr.fraction*100).toInt()}%"})
       exportMessage=if(result.success)"PASS: MP4 exported and verified" else "FAILED: ${result.error}"
       if(result.success)exported=result.outputPath?.let{File(it)}?.takeIf{it.isFile}
       exporting=false
      }
     },modifier=Modifier.fillMaxWidth()){Text(if(exporting)"EXPORTING…" else "EXPORT MP4")}
     exportMessage?.let{Text(it,color=if(it.startsWith("PASS"))Gold else Color.LightGray,fontSize=12.sp)}
     exported?.let{f->
      Row(horizontalArrangement=Arrangement.spacedBy(8.dp)){
       Button(onClick={com.creatorforge.app.production.openVideo(context,f,android.content.Intent.ACTION_VIEW)}){Text("PLAY")}
       OutlinedButton(onClick={com.creatorforge.app.production.openVideo(context,f,android.content.Intent.ACTION_SEND)}){Text("SHARE")}
       OutlinedButton(onClick={exportMessage=com.creatorforge.app.production.saveToGallery(context,f)}){Text("SAVE")}
      }
     }
     Text(when{ready!=p.scenes.size->"Export locked: generate every scene visual.";voiced!=p.scenes.size->"Export locked: generate narration for every scene.";else->"Ready: ${when(p.aspectRatio){AspectRatio.VERTICAL_9_16->"1080×1920";AspectRatio.SQUARE_1_1->"1080×1080";else->"1920×1080"}} • slow zoom • crossfades • bold captions • voice + whoosh."},color=Color.Gray,fontSize=12.sp)
     Spacer(Modifier.height(24.dp))
    }
   }
  }
 }
}
