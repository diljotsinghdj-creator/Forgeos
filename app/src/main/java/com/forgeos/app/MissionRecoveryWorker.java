package com.forgeos.app;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.*;
import org.json.JSONObject;

/** OS-managed recovery worker. Never stores credentials; it only reconciles durable mission state. */
public final class MissionRecoveryWorker extends Worker {
 public static final String KEY_MISSION_ID="mission_id";
 public MissionRecoveryWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
 @NonNull @Override public Result doWork(){
  String id=getInputData().getString(KEY_MISSION_ID);
  if(id==null||id.length()==0)return Result.failure();
  try{
   MissionStore s=new MissionStore(getApplicationContext());
   JSONObject current=s.read(id);
   String state=current.optString("state","");
   if(MissionStore.State.COMPLETE.name().equals(state)||MissionStore.State.VERIFIED.name().equals(state))return Result.success();

   // Recovery must participate in the same lease protocol as live execution.
   // Never replay work or write a terminal checkpoint without ownership.
   String lease=s.claimLease(id);
   if(lease==null)return Result.success();
   JSONObject owned=s.read(id);
   if(!lease.equals(owned.optString("lease","")))return Result.success();

   MissionCommandRunner.Outcome outcome=new MissionCommandRunner(getApplicationContext()).resume(owned);
   if(outcome==MissionCommandRunner.Outcome.COMPLETE){
    return s.checkpointOwned(id,lease,MissionStore.State.COMPLETE,"Recovered mission completed")?Result.success():Result.retry();
   }
   if(outcome==MissionCommandRunner.Outcome.RETRYABLE){
    boolean saved=s.checkpointOwned(id,lease,MissionStore.State.CHECKPOINTED,"Recovery deferred for retry");
    return saved&&getRunAttemptCount()<3?Result.retry():Result.failure();
   }
   if(outcome==MissionCommandRunner.Outcome.NEEDS_SECURE_REBIND){
    return s.checkpointOwned(id,lease,MissionStore.State.BLOCKED,"Recovered safely; privileged adapter requires secure rebind")?Result.success():Result.retry();
   }
   return s.checkpointOwned(id,lease,MissionStore.State.FAILED,"Mission could not be reconstructed safely")?Result.failure():Result.retry();
  }catch(java.io.FileNotFoundException e){return Result.failure();}
   catch(Exception e){return getRunAttemptCount()<3?Result.retry():Result.failure();}
 }
 public static void schedule(Context c,String missionId){
  Data d=new Data.Builder().putString(KEY_MISSION_ID,missionId).build();
  OneTimeWorkRequest w=new OneTimeWorkRequest.Builder(MissionRecoveryWorker.class)
   .setInputData(d)
   .setBackoffCriteria(BackoffPolicy.EXPONENTIAL,java.time.Duration.ofSeconds(30))
   .build();
  WorkManager.getInstance(c.getApplicationContext()).enqueueUniqueWork("forgeos-recovery-"+missionId,ExistingWorkPolicy.KEEP,w);
 }
}
