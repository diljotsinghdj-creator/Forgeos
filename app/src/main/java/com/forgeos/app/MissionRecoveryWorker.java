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
   JSONObject j=s.read(id);
   String state=j.optString("state","");
   if(MissionStore.State.COMPLETE.name().equals(state)||MissionStore.State.VERIFIED.name().equals(state))return Result.success();
   MissionCommandRunner.Outcome outcome=new MissionCommandRunner(getApplicationContext()).resume(j);
   if(outcome==MissionCommandRunner.Outcome.COMPLETE){s.checkpoint(id,MissionStore.State.COMPLETE,"Recovered mission completed");return Result.success();}
   if(outcome==MissionCommandRunner.Outcome.RETRYABLE){s.checkpoint(id,MissionStore.State.CHECKPOINTED,"Recovery deferred for retry");return getRunAttemptCount()<3?Result.retry():Result.failure();}
   if(outcome==MissionCommandRunner.Outcome.NEEDS_SECURE_REBIND){s.checkpoint(id,MissionStore.State.BLOCKED,"Recovered safely; privileged adapter requires secure rebind");return Result.success();}
   s.checkpoint(id,MissionStore.State.FAILED,"Mission could not be reconstructed safely");return Result.failure();
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