package com.forgeos.app;

import android.content.Context;
import java.util.concurrent.*;

/** Process-local continuous mission executor backed by durable MissionStore checkpoints. */
public final class ContinuousEngine {
 private static volatile ContinuousEngine INSTANCE;
 private final MissionStore store;
 private final Context appContext;
 private final ExecutorService executor=Executors.newSingleThreadExecutor();
 private ContinuousEngine(Context c){
  appContext=c.getApplicationContext();
  store=new MissionStore(appContext);
  recoverInterrupted();
 }
 private void recoverInterrupted(){
  executor.submit(()->{
   try{
    for(org.json.JSONObject j:store.recoverable()){
     String id=j.getString("id");
     store.checkpoint(id,MissionStore.State.BLOCKED,"Recovered after process restart; execution payload requires explicit safe rebind");
    }
   }catch(Exception ignored){}
  });
 }
 private Context storeContext(){return appContext;}
 public static ContinuousEngine get(Context c){
  if(INSTANCE==null)synchronized(ContinuousEngine.class){if(INSTANCE==null)INSTANCE=new ContinuousEngine(c);}
  return INSTANCE;
 }
 public String submit(String objective, MissionTask task)throws Exception{return submit(objective,"GENERIC",null,null,task);}
 public String submit(String objective,String commandType,String workspacePath,String adapterId,MissionTask task)throws Exception{
  final String id=store.create(objective,commandType,workspacePath,adapterId);
  executor.submit(()->run(id,task));
  return id;
 }
 private void run(String id,MissionTask task){
  String lease=null;
  try{
   lease=store.claimLease(id);if(lease==null)return;
   if(!store.checkpointOwned(id,lease,MissionStore.State.RUNNING,"Mission worker started"))return;
   task.run(new MissionContext(id,lease,store));
   if(!store.checkpointOwned(id,lease,MissionStore.State.COMPLETE,"Mission verified and complete"))return;
  }catch(Throwable t){
   try{
    if(lease!=null)store.checkpointOwned(id,lease,MissionStore.State.FAILED,t.getClass().getSimpleName()+": "+String.valueOf(t.getMessage()));
   }catch(Exception ignored){}
  }
 }
 public interface MissionTask { void run(MissionContext context)throws Exception; }
 public static final class MissionContext {
  public final String id; private final String lease; private final MissionStore store;
  MissionContext(String id,String lease,MissionStore s){this.id=id;this.lease=lease;store=s;}
  public void checkpoint(String note)throws Exception{
   if(!store.checkpointOwned(id,lease,MissionStore.State.RUNNING,note))throw new IllegalStateException("Mission lease lost");
  }
  public void block(String note)throws Exception{
   if(!store.checkpointOwned(id,lease,MissionStore.State.BLOCKED,note))throw new IllegalStateException("Mission lease lost");
  }
 }
}