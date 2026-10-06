package com.forgeos.app;

import android.content.Context;
import org.json.JSONObject;
import java.io.File;

/** Reconstructs non-secret mission intent after process death. */
public final class MissionCommandRunner {
 public enum Outcome { COMPLETE, NEEDS_SECURE_REBIND, RETRYABLE, FAILED }
 private final Context app;
 public MissionCommandRunner(Context c){app=c.getApplicationContext();}
 public Outcome resume(JSONObject m)throws Exception{
  String type=m.optString("commandType","GENERIC");
  if("BUILD_ANDROID".equals(type))return resumeBuild(m);
  return Outcome.NEEDS_SECURE_REBIND;
 }
 private Outcome resumeBuild(JSONObject m)throws Exception{
  String p=m.optString("workspacePath","");
  if(p.length()==0)return Outcome.FAILED;
  File workspace=new File(p);
  if(!workspace.isDirectory())return Outcome.FAILED;
  String adapter=m.optString("adapterId","");
  // GitHub token is intentionally never serialized. A privileged remote build cannot
  // be replayed after process death without fresh authorization.
  if("github-actions".equals(adapter))return Outcome.NEEDS_SECURE_REBIND;
  return Outcome.NEEDS_SECURE_REBIND;
 }
}