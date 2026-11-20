package com.forgeos.app;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import org.json.*;

/** Offline preflight that predicts common Android/Gradle build blockers without executing project code. */
public final class BuildReadinessAnalyzer {
 private static final long MAX_TEXT=2L*1024*1024;
 public JSONObject analyze(File root)throws Exception{
  JSONObject out=new JSONObject(); JSONArray checks=new JSONArray(); JSONArray warnings=new JSONArray();
  check(checks,"workspace",root!=null&&root.isDirectory(),"Workspace exists");
  File settings=first(root,"settings.gradle.kts","settings.gradle");
  File top=first(root,"build.gradle.kts","build.gradle");
  check(checks,"gradle_root",settings!=null||top!=null,"Gradle root markers");
  File app=new File(root,"app"), appBuild=first(app,"build.gradle.kts","build.gradle");
  check(checks,"app_module",appBuild!=null,"Android app module build file");
  boolean sourceRoot=new File(app,"src/main").isDirectory();
  check(checks,"source_root",sourceRoot,"app/src/main source root");
  File manifest=new File(app,"src/main/AndroidManifest.xml");
  check(checks,"manifest",manifest.isFile(),"AndroidManifest.xml");
  if(manifest.isFile()){
   String m=read(manifest); boolean clear=m.contains("usesCleartextTraffic=\"true\"");
   if(clear)warnings.put("Manifest permits cleartext network traffic");
   boolean exported=m.contains("android:exported=");
   if(m.contains("android.intent.action.MAIN")&&!exported)warnings.put("Launcher activity may need explicit android:exported on modern Android");
  }
  if(appBuild!=null){
   String g=read(appBuild);
   Integer compile=num(g,"compileSdk\\s*(?:=)?\\s*(\\d+)");
   Integer min=num(g,"minSdk\\s*(?:=)?\\s*(\\d+)");
   Integer target=num(g,"targetSdk\\s*(?:=)?\\s*(\\d+)");
   if(compile!=null)out.put("compileSdk",compile); else warnings.put("compileSdk not statically detected");
   if(min!=null)out.put("minSdk",min);
   if(target!=null)out.put("targetSdk",target);
   if(compile!=null&&target!=null&&target>compile)warnings.put("targetSdk exceeds compileSdk");
   boolean androidPlugin=g.contains("com.android.application")||g.contains("com.android.library");
   check(checks,"android_plugin",androidPlugin,"Android Gradle plugin detected");
   if(!androidPlugin)warnings.put("Android Gradle plugin not detected in app module");
  }
  File wrapper=new File(root,"gradle/wrapper/gradle-wrapper.properties");
  if(!wrapper.isFile())warnings.put("Gradle wrapper metadata missing; reproducible build may depend on external Gradle");
  else {
   String w=read(wrapper);
   Matcher dm=Pattern.compile("distributionUrl\\s*=\\s*(.+)").matcher(w);
   if(dm.find())out.put("gradleDistribution",dm.group(1).trim());
  }
  out.put("schema","forgeos.build-readiness.v1");out.put("checks",checks);out.put("warnings",warnings);
  boolean ready=true;for(int i=0;i<checks.length();i++)if(!checks.getJSONObject(i).getBoolean("pass"))ready=false;
  out.put("ready",ready);out.put("analyzedAt",System.currentTimeMillis());return out;
 }
 private void check(JSONArray a,String id,boolean pass,String label)throws Exception{JSONObject x=new JSONObject();x.put("id",id);x.put("label",label);x.put("pass",pass);a.put(x);}
 private File first(File d,String...n){if(d==null)return null;for(String x:n){File f=new File(d,x);if(f.isFile())return f;}return null;}
 private String read(File f)throws Exception{if(f.length()>MAX_TEXT)throw new IOException("Config too large for safe static analysis: "+f.getName());StringBuilder s=new StringBuilder();try(BufferedReader r=new BufferedReader(new FileReader(f))){String x;while((x=r.readLine())!=null)s.append(x).append('\n');}return s.toString();}
 private Integer num(String s,String p){Matcher m=Pattern.compile(p).matcher(s);return m.find()?Integer.valueOf(m.group(1)):null;}
}