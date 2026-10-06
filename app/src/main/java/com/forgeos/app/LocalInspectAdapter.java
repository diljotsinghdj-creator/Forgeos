package com.forgeos.app;

import java.io.*;
import java.security.*;
import java.util.*;
import org.json.*;

/** Credential-free local ForgeOS capability. Works without GitHub/network. */
public final class LocalInspectAdapter implements BuildAdapter {
 public String id(){return "local-inspect";}
 public boolean isAvailable(){return true;}
 public BuildResult submit(String missionId,File workspace)throws Exception{
  if(workspace==null||!workspace.isDirectory())return new BuildResult(false,null,"Workspace unavailable");
  JSONObject report=inspect(workspace);
  File out=new File(workspace,".forgeos"); if(!out.exists()&&!out.mkdirs())throw new IOException("Cannot create .forgeos");
  File reportFile=new File(out,"inspection-"+missionId+".json");
  atomicWrite(reportFile,report.toString(2));
  return new BuildResult(true,reportFile.getAbsolutePath(),"Local inspection verified");
 }
 private JSONObject inspect(File root)throws Exception{
  JSONObject j=new JSONObject();j.put("schema","forgeos.local-inspection.v1");j.put("workspace",root.getCanonicalPath());
  boolean settings=new File(root,"settings.gradle.kts").isFile()||new File(root,"settings.gradle").isFile();
  boolean build=new File(root,"build.gradle.kts").isFile()||new File(root,"build.gradle").isFile();
  j.put("gradleSettings",settings);j.put("gradleBuild",build);
  if(!settings&&!build)throw new IOException("No Gradle project markers");
  JSONArray files=new JSONArray();long[] stats={0,0};walk(root,root,files,stats);
  j.put("fileCount",stats[0]);j.put("bytes",stats[1]);j.put("files",files);
  j.put("manifestSha256",sha256(files.toString().getBytes("UTF-8")));j.put("verifiedAt",System.currentTimeMillis());
  return j;
 }
 private void walk(File root,File f,JSONArray out,long[] stats)throws Exception{
  File[] list=f.listFiles();if(list==null)return;Arrays.sort(list,Comparator.comparing(File::getName));
  for(File x:list){
   String rel=root.toURI().relativize(x.toURI()).getPath();
   if(rel.startsWith(".forgeos/")||rel.startsWith(".git/")||rel.contains("/build/")||rel.startsWith("build/"))continue;
   if(x.isDirectory())walk(root,x,out,stats);else{
    JSONObject e=new JSONObject();e.put("path",rel);e.put("bytes",x.length());e.put("sha256",sha256(x));out.put(e);stats[0]++;stats[1]+=x.length();
   }
  }
 }
 private String sha256(File f)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[16384];int n;while((n=in.read(b))>0)d.update(b,0,n);}return hex(d.digest());}
 private String sha256(byte[] b)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");return hex(d.digest(b));}
 private String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format(Locale.US,"%02x",x&255));return s.toString();}
 private void atomicWrite(File f,String s)throws Exception{File t=new File(f.getPath()+".tmp");try(FileOutputStream o=new FileOutputStream(t)){o.write(s.getBytes("UTF-8"));o.getFD().sync();}if(f.exists()&&!f.delete())throw new IOException("Cannot replace report");if(!t.renameTo(f))throw new IOException("Cannot commit report");}
}