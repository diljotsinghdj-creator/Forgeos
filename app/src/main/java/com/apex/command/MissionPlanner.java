package com.apex.command;

public final class MissionPlanner {
 private MissionPlanner(){}
 public static String build(String objective,String identity,String platform,String audience,String tone){
  if(objective==null||objective.trim().isEmpty())throw new IllegalArgumentException("objective required");
  return "APEX MISSION ARTIFACT\n"+
   "Objective: "+safe(objective,"Untitled")+"\n"+
   "Identity: "+safe(identity,"Default")+"\n"+
   "Platform: "+safe(platform,"Unspecified")+"\n"+
   "Audience: "+safe(audience,"General")+"\n"+
   "Tone: "+safe(tone,"Clear and engaging")+"\n\n"+
   "EXECUTION BRIEF\n"+
   "1. Define the single outcome and success evidence.\n"+
   "2. Produce the smallest publishable deliverable for the selected platform.\n"+
   "3. Verify identity, audience and tone constraints before release.\n"+
   "4. Record failures explicitly; never report completion without an artifact.\n";
 }
 private static String safe(String s,String fallback){if(s==null||s.trim().isEmpty())return fallback;return s.trim();}
}