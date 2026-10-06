package com.forgeos.app;

import android.content.Context;
import org.json.JSONObject;
import java.io.*;
import java.util.UUID;
import java.security.MessageDigest;

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
  JSONObject j=new JSONObject(s.toString());
  String stored=j.optString("integrity","");
  if(stored.length()==0)throw new IOException("Mission integrity metadata missing");
  j.remove("integrity");
  String actual=sha256(j.toString().getBytes("UTF-8"));
  if(!stored.equals(actual))throw new IOException("Mission integrity verification failed");
  j.put("integrity",stored); return j;
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
 public synchronized String claimLease(String id)throws Exception{
  JSONObject j=read(id); String s=j.optString("state",""); long now=System.currentTimeMillis();
  if(State.COMPLETE.name().equals(s)||State.VERIFIED.name().equals(s))return null;
  if(State.RUNNING.name().equals(s)&&j.optLong("leaseUntil",0)>now)return null;
  String lease=UUID.randomUUID().toString();j.put("state",State.RUNNING.name());j.put("lease",lease);j.put("leaseUntil",now+5L*60*1000);j.put("updatedAt",now);write(id,j);return lease;
 }
 public synchronized boolean renewLease(String id,String lease)throws Exception{
  JSONObject j=read(id);if(lease==null||!lease.equals(j.optString("lease","")))return false;
  if(!State.RUNNING.name().equals(j.optString("state","")))return false;
  long now=System.currentTimeMillis();j.put("leaseUntil",now+5L*60*1000);j.put("updatedAt",now);write(id,j);return true;
 }
 public synchronized void checkpoint(String id,State state,String note)throws Exception{
  JSONObject j=read(id);j.put("state",state.name());j.put("note",note==null?"":note);if(state!=State.RUNNING){j.remove("lease");j.remove("leaseUntil");}
  j.put("attempt",j.optInt("attempt",0)+1);j.put("updatedAt",System.currentTimeMillis());write(id,j);
 }
 private File file(String id){return new File(dir,id.replaceAll("[^A-Za-z0-9._-]","_")+".json");}
 private String sha256(byte[] b)throws Exception{byte[] h=MessageDigest.getInstance("SHA-256").digest(b);StringBuilder s=new StringBuilder();for(byte x:h)s.append(String.format(java.util.Locale.US,"%02x",x&255));return s.toString();}
 private void write(String id,JSONObject j)throws Exception{
  j.remove("integrity"); j.put("integrity",sha256(j.toString().getBytes("UTF-8")));
  File f=file(id),tmp=new File(f.getPath()+".tmp");
  try(FileOutputStream o=new FileOutputStream(tmp)){o.write(j.toString().getBytes("UTF-8"));o.getFD().sync();}
  if(f.exists()&&!f.delete())throw new IOException("Cannot replace mission");if(!tmp.renameTo(f))throw new IOException("Cannot commit mission checkpoint");
 }
}