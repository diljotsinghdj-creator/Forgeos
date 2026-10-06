package com.forgeos.app;

import java.io.*;
import java.util.*;
import java.util.regex.*;
import org.json.*;

/** Static fail-closed supply-chain scan. Never executes imported Gradle code. */
public final class SupplyChainScanner {
 private static final long MAX=2L*1024*1024;
 public JSONObject scan(File root)throws Exception{
  JSONArray findings=new JSONArray(); scanGradle(root,findings); scanWrapper(root,findings); scanBinaries(root,root,findings,new long[]{0});
  JSONObject o=new JSONObject();o.put("schema","forgeos.supply-chain.v1");o.put("findings",findings);
  int high=0,medium=0;for(int i=0;i<findings.length();i++){String s=findings.getJSONObject(i).getString("severity");if("HIGH".equals(s))high++;else if("MEDIUM".equals(s))medium++;}
  o.put("high",high);o.put("medium",medium);o.put("pass",high==0);return o;
 }
 private void scanGradle(File root,JSONArray f)throws Exception{
  List<File> xs=Arrays.asList(new File(root,"settings.gradle"),new File(root,"settings.gradle.kts"),new File(root,"build.gradle"),new File(root,"build.gradle.kts"),new File(root,"app/build.gradle"),new File(root,"app/build.gradle.kts"));
  for(File x:xs)if(x.isFile()){
   String s=read(x);
   if(Pattern.compile("http://",Pattern.CASE_INSENSITIVE).matcher(s).find())add(f,"HIGH","INSECURE_REPOSITORY","HTTP repository/configuration detected",x);
   if(Pattern.compile("(latest\\.(release|integration)|[0-9]+\\.\\+|SNAPSHOT)",Pattern.CASE_INSENSITIVE).matcher(s).find())add(f,"MEDIUM","NONDETERMINISTIC_DEPENDENCY","Dynamic or snapshot dependency detected",x);
   if(Pattern.compile("(exec\\s*\\{|commandLine\\s*\\(|Runtime\\.getRuntime|ProcessBuilder)",Pattern.CASE_INSENSITIVE).matcher(s).find())add(f,"HIGH","EXECUTABLE_BUILD_HOOK","Build script can launch external processes",x);
   if(Pattern.compile("(flatDir\\s*\\{|files\\s*\\(|fileTree\\s*\\()",Pattern.CASE_INSENSITIVE).matcher(s).find())add(f,"MEDIUM","LOCAL_BINARY_DEPENDENCY","Local binary dependency source detected",x);
  }
 }
 private void scanWrapper(File root,JSONArray f)throws Exception{
  File p=new File(root,"gradle/wrapper/gradle-wrapper.properties");
  File jar=new File(root,"gradle/wrapper/gradle-wrapper.jar");
  if(!p.isFile())add(f,"MEDIUM","WRAPPER_METADATA_MISSING","Gradle wrapper properties missing",root);
  else {String s=read(p);if(s.contains("http://"))add(f,"HIGH","INSECURE_WRAPPER_URL","Gradle wrapper uses insecure HTTP",p);if(!s.contains("distributionSha256Sum"))add(f,"MEDIUM","WRAPPER_CHECKSUM_MISSING","Gradle distribution checksum is not pinned",p);}
  if(p.isFile()&&!jar.isFile())add(f,"MEDIUM","WRAPPER_JAR_MISSING","Gradle wrapper JAR missing",root);
 }
 private void scanBinaries(File root,File d,JSONArray f,long[] n)throws Exception{
  File[] xs=d.listFiles();if(xs==null)return;for(File x:xs){String rel=root.toURI().relativize(x.toURI()).getPath();if(rel.startsWith(".git/")||rel.startsWith(".forgeos/")||rel.contains("/build/"))continue;if(x.isDirectory())scanBinaries(root,x,f,n);else if((x.getName().endsWith(".jar")||x.getName().endsWith(".aar"))&&++n[0]<=100)add(f,"MEDIUM","BUNDLED_BINARY","Bundled JAR/AAR requires provenance review",x);}
 }
 private String read(File f)throws Exception{if(f.length()>MAX)throw new IOException("Config too large for supply-chain scan: "+f.getName());StringBuilder s=new StringBuilder();try(BufferedReader r=new BufferedReader(new FileReader(f))){String x;while((x=r.readLine())!=null)s.append(x).append('\n');}return s.toString();}
 private void add(JSONArray a,String sev,String code,String msg,File file)throws Exception{JSONObject x=new JSONObject();x.put("severity",sev);x.put("code",code);x.put("message",msg);x.put("path",file.getPath());a.put(x);}
}