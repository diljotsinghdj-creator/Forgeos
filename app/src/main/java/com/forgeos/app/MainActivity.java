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
 private File active; private static final long MAX_UNPACKED=250L*1024*1024;
 @Override public void onCreate(Bundle b){super.onCreate(b);setContentView(ui());restore();}
 private View ui(){
  ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.rgb(9,9,9));
  LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.VERTICAL);r.setPadding(dp(22),dp(24),dp(22),dp(28));s.addView(r);
  r.addView(txt("FORGEOS",30,GOLD,true));r.addView(txt("Android Development Workspace",14,Color.LTGRAY,false));
  LinearLayout c=panel();c.addView(txt("WORKSPACE CONTROL",12,GOLD,true));status=txt("Ready",16,Color.WHITE,true);c.addView(status);c.addView(txt("Import a project ZIP. ForgeOS extracts it into an isolated private workspace, validates Android/Gradle structure and preserves it between launches.",13,Color.LTGRAY,false));r.addView(c);
  Button imp=btn("IMPORT PROJECT ZIP");imp.setOnClickListener(v->{Intent x=new Intent(Intent.ACTION_OPEN_DOCUMENT);x.setType("application/zip");x.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(x,100);});r.addView(imp);
  build=btn("BUILD APK");build.setEnabled(false);build.setOnClickListener(v->requestRemoteBuild());r.addView(build);
  r.addView(txt("PROJECT",12,GOLD,true));projects=panel();projects.addView(txt("No project imported yet",15,Color.LTGRAY,false));r.addView(projects);
  r.addView(txt("FILES",12,GOLD,true));files=panel();files.addView(txt("Workspace empty",13,Color.GRAY,false));r.addView(files);
  r.addView(txt("ACTIVITY LOG",12,GOLD,true));log=txt("ForgeOS initialized.",12,Color.LTGRAY,false);LinearLayout lp=panel();lp.addView(log);r.addView(lp);
  r.addView(txt("ForgeOS v0.4.0 - Continuous Engine",11,Color.GRAY,false));return s;
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
  final File workspace=active;
  try{
   ContinuousEngine engine=ContinuousEngine.get(this);
   String missionId=engine.submit("Build Android workspace",ctx->{
    ctx.checkpoint("Selecting execution adapter");
    BuildAdapter adapter=new BuildAdapterRegistry().add(new GitHubBuildAdapter(token)).firstAvailable();
    if(adapter==null){ctx.block("No build adapter available");throw new IOException("No build adapter available");}
    ctx.checkpoint("Submitting via "+adapter.id());
    BuildAdapter.BuildResult result=adapter.submit(ctx.id,workspace);
    if(!result.accepted)throw new IOException(result.message);
    runOnUiThread(()->{status.setText("Build mission submitted");append("Mission "+ctx.id+" -> "+result.reference+" via "+adapter.id());build.setEnabled(true);});
   });
   runOnUiThread(()->{status.setText("Mission queued");append("Durable mission queued: "+missionId);});
  }catch(Exception e){runOnUiThread(()->{status.setText("Build mission failed");append("ERROR: "+e.getMessage());build.setEnabled(true);});}
 }
 private byte[] zipWorkspace(File root)throws Exception{
  ByteArrayOutputStream b=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(b)){zipDir(root,root,z);}return b.toByteArray();
 }
 private void zipDir(File root,File f,ZipOutputStream z)throws Exception{
  File[] a=f.listFiles();if(a==null)return;for(File x:a){String rel=root.toURI().relativize(x.toURI()).getPath();if(rel.startsWith(".git/")||rel.contains("/build/")||rel.startsWith("build/"))continue;if(x.isDirectory())zipDir(root,x,z);else{z.putNextEntry(new ZipEntry(rel));try(InputStream in=new FileInputStream(x)){byte[] q=new byte[16384];int n;while((n=in.read(q))>0)z.write(q,0,n);}z.closeEntry();}}
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