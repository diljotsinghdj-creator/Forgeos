package com.forgeos.app;

import android.content.Context;
import org.json.JSONObject;
import java.io.*;
import java.util.UUID;

/** Durable on-device mission state. No network or GitHub dependency. */
public final class MissionStore {
 public enum State { QUEUED, RUNNING, CHECKPOINTED, BLOCKED, VERIFIED, COMPLETE, FAILED }
 private final File dir;
 public MissionStore(Context c){ dir=new File(c.getFilesDir(),"missions"); if(!dir.exists())dir.mkdirs(); }
 public synchronized String create(String objective)throws Exception{return create(objective,"GENERIC",null,null);}
 public synchronized String create(String objective,String commandType,String workspacePath,String adapterId)throws Exception{
  String id="mission-"+UUID.randomUUID(); JSONObject j=new JSONObject();
  j.put("id",id);j.put("objective",objective);j.put("commandType",commandType==null?"GENERIC":commandType);
  if(workspacePath!=null)j.put("workspacePath",workspacePath);
  if(adapterId!=null)j.put("adapterId",adapterId);
  j.put("state",State.QUEUED.name());
  j.put("attempt",0);j.put("createdAt",System.currentTimeMillis());j.put("updatedAt",System.currentTimeMillis());
  write(id,j); return id;
 }
 public synchronized JSONObject read(String id)throws Exception{
  File f=file(id); if(!f.isFile())throw new FileNotFoundException(id);
  StringBuilder s=new StringBuilder(); try(BufferedReader r=new BufferedReader(new FileReader(f))){String x;while((x=r.readLine())!=null)s.append(x);}
  return new JSONObject(s.toString());
 }
 public synchronized java.util.List<JSONObject> recoverable()throws Exception{
  java.util.List<JSONObject> out=new java.util.ArrayList<>(); File[] fs=dir.listFiles();
  if(fs==null)return out;
  for(File f:fs)if(f.isFile()&&f.getName().endsWith(".json")){
   try{
    String id=f.getName().substring(0,f.getName().length()-5); JSONObject j=read(id);
    String s=j.optString("state","");
    if(State.QUEUED.name().equals(s)||State.RUNNING.name().equals(s)||State.CHECKPOINTED.name().equals(s))out.add(j);
   }catch(Exception ignored){}
  }
  return out;
 }
 public synchronized void checkpoint(String id,State state,String note)throws Exception{
  JSONObject j=read(id);j.put("state",state.name());j.put("note",note==null?"":note);
  j.put("attempt",j.optInt("attempt",0)+1);j.put("updatedAt",System.currentTimeMillis());write(id,j);
 }
 private File file(String id){return new File(dir,id.replaceAll("[^A-Za-z0-9._-]","_")+".json");}
 private void write(String id,JSONObject j)throws Exception{
  File f=file(id),tmp=new File(f.getPath()+".tmp");
  try(FileOutputStream o=new FileOutputStream(tmp)){o.write(j.toString().getBytes("UTF-8"));o.getFD().sync();}
  if(f.exists()&&!f.delete())throw new IOException("Cannot replace mission");if(!tmp.renameTo(f))throw new IOException("Cannot commit mission checkpoint");
 }
}