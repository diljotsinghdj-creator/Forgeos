package com.forgeos.app;

import android.util.Base64;
import java.io.*;
import java.net.*;
import javax.net.ssl.HttpsURLConnection;
import java.util.zip.*;

/** Optional GitHub execution adapter. ForgeOS mission state remains local and provider-independent. */
public final class GitHubBuildAdapter implements BuildAdapter {
 private final String token;
 public GitHubBuildAdapter(String token){this.token=token==null?"":token.trim();}
 public String id(){return "github-actions";}
 public boolean isAvailable(){return token.length()>=20;}
 public BuildResult submit(String missionId,File workspace)throws Exception{
  if(!isAvailable())return new BuildResult(false,null,"GitHub adapter unavailable");
  String requestId="android-"+System.currentTimeMillis();
  String path="build-requests/"+requestId+".zip";
  byte[] zip=zipWorkspace(workspace);
  if(zip.length>90L*1024*1024)throw new IOException("Compressed project exceeds 90 MB remote request limit");
  String body="{\"message\":\"ForgeOS mission "+missionId+"\",\"content\":\""+Base64.encodeToString(zip,Base64.NO_WRAP)+"\",\"branch\":\"build-requests\"}";
  api("PUT","https://api.github.com/repos/diljotsinghdj-creator/Forgeos/contents/"+path,body);
  String dispatch="{\"ref\":\"main\",\"inputs\":{\"request_path\":\""+path+"\",\"request_id\":\""+requestId+"\"}}";
  api("POST","https://api.github.com/repos/diljotsinghdj-creator/Forgeos/actions/workflows/remote-project-build.yml/dispatches",dispatch);
  return new BuildResult(true,requestId,"Remote build submitted");
 }
 private byte[] zipWorkspace(File root)throws Exception{
  ByteArrayOutputStream b=new ByteArrayOutputStream();try(ZipOutputStream z=new ZipOutputStream(b)){zipDir(root,root,z);}return b.toByteArray();
 }
 private void zipDir(File root,File f,ZipOutputStream z)throws Exception{
  File[] a=f.listFiles();if(a==null)return;for(File x:a){String rel=root.toURI().relativize(x.toURI()).getPath();if(rel.startsWith(".git/")||rel.contains("/build/")||rel.startsWith("build/"))continue;if(x.isDirectory())zipDir(root,x,z);else{z.putNextEntry(new ZipEntry(rel));try(InputStream in=new FileInputStream(x)){byte[] q=new byte[16384];int n;while((n=in.read(q))>0)z.write(q,0,n);}z.closeEntry();}}
 }
 private String api(String method,String url,String body)throws Exception{
  HttpsURLConnection h=(HttpsURLConnection)new URL(url).openConnection();h.setRequestMethod(method);h.setConnectTimeout(20000);h.setReadTimeout(30000);h.setRequestProperty("Authorization","Bearer "+token);h.setRequestProperty("Accept","application/vnd.github+json");h.setRequestProperty("X-GitHub-Api-Version","2022-11-28");h.setRequestProperty("User-Agent","ForgeOS-Android/0.4.0");
  if(body!=null){h.setDoOutput(true);h.setRequestProperty("Content-Type","application/json");try(OutputStream o=h.getOutputStream()){o.write(body.getBytes("UTF-8"));}}
  int code=h.getResponseCode();InputStream in=code>=200&&code<300?h.getInputStream():h.getErrorStream();StringBuilder s=new StringBuilder();if(in!=null)try(BufferedReader r=new BufferedReader(new InputStreamReader(in))){String line;while((line=r.readLine())!=null)s.append(line);}
  if(code<200||code>=300)throw new IOException("GitHub HTTP "+code+": "+s);return s.toString();
 }
}