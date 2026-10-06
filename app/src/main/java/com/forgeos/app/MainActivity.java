package com.forgeos.app;

import android.app.*;
import android.os.Bundle;
import android.content.*;
import android.graphics.*;
import android.graphics.Typeface;
import android.net.Uri;
import android.util.Base64;
import java.net.*;
import javax.net.ssl.HttpsURLConnection;
import android.view.View;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

public class MainActivity extends Activity {
 private final int GOLD=Color.rgb(212,175,55);
 private LinearLayout projects,files; private TextView status,log; private Button build;
 private File active; private static final long MAX_UNPACKED=250L*1024*1024; private static final String MISSION_STATE="apex_mission_state",MISSION_TEXT="apex_mission_text";
 @Override public void onCreate(Bundle b){super.onCreate(b);setContentView(ui());restore();}
 private View ui(){
  ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.rgb(7,9,13));
  LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.VERTICAL);r.setPadding(dp(22),dp(22),dp(22),dp(30));s.addView(r);
  r.addView(txt("APEX",32,GOLD,true));r.addView(txt("Mission Control • v0.1",13,Color.LTGRAY,false));
  LinearLayout hero=panel();hero.addView(txt("COMMAND APEX",12,GOLD,true));hero.addView(txt("What do you want accomplished?",20,Color.WHITE,true));
  EditText mission=new EditText(this);mission.setHint("Describe a mission…");mission.setTextColor(Color.WHITE);mission.setHintTextColor(Color.GRAY);mission.setMinLines(3);mission.setGravity(android.view.Gravity.TOP);hero.addView(mission);
  Button launch=btn("LAUNCH MISSION");hero.addView(launch);r.addView(hero);
  LinearLayout live=panel();live.addView(txt("MISSION STATUS",12,GOLD,true));status=txt("IDLE • Awaiting mission",16,Color.WHITE,true);live.addView(status);
  live.addView(txt("Planner  •  Worker  •  Tester  •  Judge",12,Color.LTGRAY,false));r.addView(live);
  LinearLayout evidence=panel();evidence.addView(txt("EVIDENCE & RECOVERY",12,GOLD,true));log=txt("No mission evidence yet. Failures will be surfaced here before recovery.",12,Color.LTGRAY,false);evidence.addView(log);r.addView(evidence);
  LinearLayout nav=panel();nav.addView(txt("SYSTEMS",12,GOLD,true));nav.addView(txt("Missions   Agents   Projects & Memory",13,Color.WHITE,true));nav.addView(txt("CreatorForge   Growth Intelligence",13,Color.WHITE,true));nav.addView(txt("Evidence   Security & Settings",13,Color.WHITE,true));r.addView(nav);
  r.addView(txt("ENGINEERING BRIDGE",12,GOLD,true));projects=panel();projects.addView(txt("ForgeOS build engine available beneath APEX.",12,Color.LTGRAY,false));r.addView(projects);
  files=panel();files.setVisibility(View.GONE);r.addView(files);build=btn("BUILD ENGINE");build.setVisibility(View.GONE);r.addView(build);
  String savedMission=getPreferences(0).getString(MISSION_TEXT,"");String savedState=getPreferences(0).getString(MISSION_STATE,"IDLE");if(!savedMission.isEmpty())mission.setText(savedMission);if(!"IDLE".equals(savedState))status.setText(savedState+" • "+savedMission);
  launch.setOnClickListener(v->{String m=mission.getText().toString().trim();if(m.isEmpty()){status.setText("MISSION BLOCKED • Enter an objective");return;}startMission(m);});
  r.addView(txt("APEX v0.1 • Mission Control on ForgeOS",11,Color.GRAY,false));return s;
 }
 private void startMission(String mission){
  getPreferences(0).edit().putString(MISSION_TEXT,mission).putString(MISSION_STATE,"PLANNING").apply();
  status.setText("PLANNING • "+mission);append("Mission accepted. State checkpoint: PLANNING.");
  new android.os.Handler(getMainLooper()).postDelayed(()->{
   getPreferences(0).edit().putString(MISSION_STATE,"RUNNING").apply();status.setText("RUNNING • "+mission);append("Worker checkpoint: RUNNING.");
   new android.os.Handler(getMainLooper()).postDelayed(()->{
    getPreferences(0).edit().putString(MISSION_STATE,"VERIFYING").apply();status.setText("VERIFYING • "+mission);append("Tester/Judge checkpoint: VERIFYING.");
    new android.os.Handler(getMainLooper()).postDelayed(()->{
     getPreferences(0).edit().putString(MISSION_STATE,"COMPLETED").apply();status.setText("COMPLETED • "+mission);append("Evidence: local v0.1 lifecycle completed. External agent execution not yet enabled.");
    },700);
   },700);
  },700);
 }

 @Override protected void onActivityResult(int q,int result,Intent data){super.onActivityResult(q,result,data);if(q==100&&result==RESULT_OK&&data!=null&&data.getData()!=null)importZip(data.getData());}
 private void importZip(Uri uri){
  status.setText("Importing project...");build.setEnabled(false);
  new Thread(()->{try{
   File root=new File(getFilesDir(),"workspaces");if(!root.exists())root.mkdirs();
   File dst=new File(root,"project_"+System.currentTimeMillis());dst.mkdirs();
   unzip(uri,dst);File project=findProjectRoot(dst);
   if(project==null)throw new IOException("No settings.gradle(.kts) or build.gradle(.kts) found");
   active=project;getPreferences(0).edit().putString("active",active.getAbsolutePath()).apply();
   runOnUiThread(()->render("Imported and validated Android/Gradle workspace."));
  }catch(Exception e){runOnUiThread(()->{status.setText("Import failed");append("ERROR: "+e.getMessage());});}}).start();
 }
 private void unzip(Uri uri,File dst)throws Exception{
  long total=0;byte[] buf=new byte[16384];
  try(ZipInputStream z=new ZipInputStream(new BufferedInputStream(getContentResolver().openInputStream(uri)))){
   ZipEntry e;while((e=z.getNextEntry())!=null){
    String n=e.getName();if(n.contains("..")||n.startsWith("/")||n.startsWith("\\"))throw new IOException("Unsafe ZIP path blocked");
    File out=new File(dst,n);String base=dst.getCanonicalPath()+File.separator;if(!out.getCanonicalPath().startsWith(base))throw new IOException("ZIP traversal blocked");
    if(e.isDirectory()){out.mkdirs();continue;}File p=out.getParentFile();if(p!=null)p.mkdirs();
    try(OutputStream o=new BufferedOutputStream(new FileOutputStream(out))){int k;while((k=z.read(buf))>0){total+=k;if(total>MAX_UNPACKED)throw new IOException("Project exceeds 250 MB safety limit");o.write(buf,0,k);}}
   }
  }
 }
 private File findProjectRoot(File f){
  if(new File(f,"settings.gradle.kts").exists()||new File(f,"settings.gradle").exists()||new File(f,"build.gradle.kts").exists()||new File(f,"build.gradle").exists())return f;
  File[] a=f.listFiles(File::isDirectory);if(a!=null)for(File x:a){File r=findProjectRoot(x);if(r!=null)return r;}return null;
 }
 private void restore(){String p=getPreferences(0).getString("active",null);if(p!=null){File f=new File(p);if(f.isDirectory()){active=f;render("Workspace restored.");}}}
 private void render(String message){
  status.setText("Workspace ready");projects.removeAllViews();projects.addView(txt(active.getName(),16,Color.WHITE,true));
  boolean gradle=new File(active,"settings.gradle.kts").exists()||new File(active,"settings.gradle").exists();
  projects.addView(txt(gradle?"Gradle project detected":"Gradle build files detected",12,GOLD,false));
  files.removeAllViews();showFiles(active,files,0);build.setEnabled(true);append(message);
 }
 private void showFiles(File d,LinearLayout box,int depth){
  File[] a=d.listFiles();if(a==null)return;Arrays.sort(a,(x,y)->x.getName().compareToIgnoreCase(y.getName()));
  int shown=0;for(File f:a){if(shown++>=40){box.addView(txt("...more files",12,Color.GRAY,false));break;}String pad="";for(int i=0;i<depth;i++)pad+="  ";box.addView(txt(pad+(f.isDirectory()?"[DIR] ":"[FILE] ")+f.getName(),12,f.isDirectory()?GOLD:Color.LTGRAY,false));if(f.isDirectory()&&depth<1)showFiles(f,box,depth+1);}
 }
 private void requestRemoteBuild(){
  if(active==null)return;
  final EditText input=new EditText(this);input.setHint("Fine-grained GitHub token");input.setSingleLine(true);
  new AlertDialog.Builder(this).setTitle("Secure remote build").setMessage("Enter a GitHub token with Contents read/write and Actions read/write access to diljotsinghdj-creator/Forgeos. ForgeOS uses it for this build only and does not save it.").setView(input).setNegativeButton("Cancel",null).setPositiveButton("BUILD",(d,w)->{
   String token=input.getText().toString().trim();if(token.length()<20){append("Build blocked: GitHub token missing or invalid.");return;}
   build.setEnabled(false);status.setText("Submitting remote build...");new Thread(()->remoteBuild(token)).start();
  }).show();
 }
 private void remoteBuild(String token){
  String id="android-"+System.currentTimeMillis();String path="build-requests/"+id+".zip";
  try{
   byte[] zip=zipWorkspace(active);if(zip.length>90L*1024*1024)throw new IOException("Compressed project exceeds 90 MB remote request limit");
   ensureBuildRequestsBranch(token);
   String body="{\"message\":\"ForgeOS remote request "+id+"\",\"content\":\""+Base64.encodeToString(zip,Base64.NO_WRAP)+"\",\"branch\":\"build-requests\"}";
   api("PUT","https://api.github.com/repos/diljotsinghdj-creator/Forgeos/contents/"+path,token,body);
   String dispatch="{\"ref\":\"main\",\"inputs\":{\"request_path\":\""+path+"\",\"request_id\":\""+id+"\"}}";
   api("POST","https://api.github.com/repos/diljotsinghdj-creator/Forgeos/actions/workflows/remote-project-build.yml/dispatches",token,dispatch);
   runOnUiThread(()->{status.setText("Remote build submitted");append("Remote build submitted: "+id);append("Open GitHub Actions to watch live logs and retrieve the APK artifact.");build.setEnabled(true);
    new AlertDialog.Builder(this).setTitle("Build submitted").setMessage("Request "+id+" is running in isolated GitHub Actions. The project ZIP was uploaded to the dedicated build-requests branch.").setPositiveButton("OPEN ACTIONS",(d,w)->startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://github.com/diljotsinghdj-creator/Forgeos/actions/workflows/remote-project-build.yml")))).setNegativeButton("CLOSE",null).show();
   });
  }catch(Exception e){runOnUiThread(()->{status.setText("Remote build failed");append("ERROR: "+e.getMessage());build.setEnabled(true);});}
 }
 private byte[] zipWorkspace(File root)throws Exception{
  ByteArrayOutputStream b=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(b)){zipDir(root,root,z);}return b.toByteArray();
 }
 private void zipDir(File root,File f,ZipOutputStream z)throws Exception{
  File[] a=f.listFiles();if(a==null)return;for(File x:a){String rel=root.toURI().relativize(x.toURI()).getPath();if(rel.startsWith(".git/")||rel.contains("/build/")||rel.startsWith("build/"))continue;if(x.isDirectory())zipDir(root,x,z);else{z.putNextEntry(new ZipEntry(rel));try(InputStream in=new FileInputStream(x)){byte[] q=new byte[16384];int n;while((n=in.read(q))>0)z.write(q,0,n);}z.closeEntry();}}
 }
 private void ensureBuildRequestsBranch(String token)throws Exception{
  String repo="https://api.github.com/repos/diljotsinghdj-creator/Forgeos";
  try{api("GET",repo+"/git/ref/heads/build-requests",token,null);return;}catch(IOException e){
   if(!e.getMessage().startsWith("GitHub HTTP 404:"))throw e;
  }
  String main=api("GET",repo+"/git/ref/heads/main",token,null);
  String needle="\\\"sha\\\":\\\"";int p=main.indexOf(needle);if(p<0)throw new IOException("Unable to resolve main branch SHA");
  int start=p+needle.length(),end=main.indexOf('"',start);if(end<0)throw new IOException("Malformed GitHub ref response");
  String sha=main.substring(start,end);
  try{api("POST",repo+"/git/refs",token,"{\\\"ref\\\":\\\"refs/heads/build-requests\\\",\\\"sha\\\":\\\""+sha+"\\\"}");}
  catch(IOException e){
   if(!e.getMessage().startsWith("GitHub HTTP 422:"))throw e;
   // A concurrent client may have created the branch after our initial 404.
   // Never treat an arbitrary 422 as success: prove the branch now exists.
   api("GET",repo+"/git/ref/heads/build-requests",token,null);
  }
 }
 private String api(String method,String url,String token,String body)throws Exception{
  HttpsURLConnection h=(HttpsURLConnection)new URL(url).openConnection();h.setRequestMethod(method);h.setConnectTimeout(20000);h.setReadTimeout(30000);h.setRequestProperty("Authorization","Bearer "+token);h.setRequestProperty("Accept","application/vnd.github+json");h.setRequestProperty("X-GitHub-Api-Version","2022-11-28");h.setRequestProperty("User-Agent","ForgeOS-Android/0.3.1");
  if(body!=null){h.setDoOutput(true);h.setRequestProperty("Content-Type","application/json");try(OutputStream o=h.getOutputStream()){o.write(body.getBytes("UTF-8"));}}
  int code=h.getResponseCode();InputStream in=code>=200&&code<300?h.getInputStream():h.getErrorStream();StringBuilder s=new StringBuilder();if(in!=null)try(BufferedReader r=new BufferedReader(new InputStreamReader(in))){String line;while((line=r.readLine())!=null)s.append(line);}
  if(code<200||code>=300)throw new IOException("GitHub HTTP "+code+": "+s);return s.toString();
 }
 private void append(String x){if(log!=null)log.setText(log.getText()+"\n"+x);}
 private LinearLayout panel(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(18),dp(16),dp(18),dp(16));l.setBackgroundColor(Color.rgb(24,24,24));return l;}
 private TextView txt(String x,int z,int c,boolean b){TextView t=new TextView(this);t.setText(x);t.setTextSize(z);t.setTextColor(c);t.setPadding(0,dp(7),0,dp(7));if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
 private Button btn(String x){Button b=new Button(this);b.setText(x);b.setTextColor(Color.BLACK);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackgroundColor(GOLD);return b;}
 private int dp(int x){return(int)(x*getResources().getDisplayMetrics().density);}
}