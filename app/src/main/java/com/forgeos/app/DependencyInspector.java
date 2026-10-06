package com.forgeos.app;

import java.io.*;
import java.util.regex.*;
import org.json.*;

/** Static, offline dependency inventory. Does not resolve or execute dependencies. */
public final class DependencyInspector {
 private static final long MAX=2L*1024*1024;
 private static final Pattern COORD=Pattern.compile("[\"']([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):([^\\"']+)[\"']");
 public JSONArray inspect(File root)throws Exception{
  JSONArray out=new JSONArray(); inspectFile(new File(root,"build.gradle"),out);inspectFile(new File(root,"build.gradle.kts"),out);
  File app=new File(root,"app");inspectFile(new File(app,"build.gradle"),out);inspectFile(new File(app,"build.gradle.kts"),out);
  return out;
 }
 private void inspectFile(File f,JSONArray out)throws Exception{
  if(!f.isFile())return;if(f.length()>MAX)throw new IOException("Dependency config too large: "+f.getName());
  StringBuilder s=new StringBuilder();try(BufferedReader r=new BufferedReader(new FileReader(f))){String x;while((x=r.readLine())!=null)s.append(x).append('\n');}
  Matcher m=COORD.matcher(s);while(m.find()){JSONObject d=new JSONObject();d.put("group",m.group(1));d.put("artifact",m.group(2));d.put("version",m.group(3));d.put("source",f.getPath());d.put("dynamic",m.group(3).contains("+")||m.group(3).equalsIgnoreCase("latest.release")||m.group(3).equalsIgnoreCase("latest.integration"));out.put(d);}
 }
}