package com.apex.command;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.view.View;
import android.widget.*;

public class MainActivity extends Activity {
 private final int GOLD=Color.rgb(212,175,55);
 private static final String MISSION_STATE="apex_mission_state",MISSION_TEXT="apex_mission_text",MISSION_ATTEMPT="apex_mission_attempt";
 private TextView status,log; private Button launch; private Handler handler;
 @Override public void onCreate(Bundle b){super.onCreate(b);handler=new Handler(getMainLooper());setContentView(ui());}
 @Override protected void onDestroy(){handler.removeCallbacksAndMessages(null);super.onDestroy();}
 private View ui(){
  ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.rgb(7,9,13));
  LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.VERTICAL);r.setPadding(dp(22),dp(22),dp(22),dp(30));s.addView(r);
  r.addView(txt("APEX",32,GOLD,true));r.addView(txt("Mission Control • v0.1",13,Color.LTGRAY,false));
  LinearLayout hero=panel();hero.addView(txt("COMMAND APEX",12,GOLD,true));hero.addView(txt("What do you want accomplished?",20,Color.WHITE,true));
  EditText mission=new EditText(this);mission.setHint("Describe a mission…");mission.setTextColor(Color.WHITE);mission.setHintTextColor(Color.GRAY);mission.setMinLines(3);mission.setGravity(Gravity.TOP);hero.addView(mission);
  launch=btn("LAUNCH MISSION");hero.addView(launch);r.addView(hero);
  LinearLayout live=panel();live.addView(txt("MISSION STATUS",12,GOLD,true));status=txt("IDLE • Awaiting mission",16,Color.WHITE,true);live.addView(status);
  live.addView(txt("Planner  •  Worker  •  Tester  •  Judge",12,Color.LTGRAY,false));r.addView(live);
  LinearLayout evidence=panel();evidence.addView(txt("EVIDENCE & RECOVERY",12,GOLD,true));log=txt("No mission evidence yet. Failures will be surfaced here before recovery.",12,Color.LTGRAY,false);evidence.addView(log);r.addView(evidence);
  LinearLayout nav=panel();nav.addView(txt("SYSTEMS",12,GOLD,true));nav.addView(txt("Missions   Agents   Projects & Memory",13,Color.WHITE,true));nav.addView(txt("CreatorForge   Growth Intelligence",13,Color.WHITE,true));nav.addView(txt("Evidence   Security & Settings",13,Color.WHITE,true));r.addView(nav);
  r.addView(txt("ENGINEERING BRIDGE",12,GOLD,true));LinearLayout bridge=panel();bridge.addView(txt("Android builds run in the separate ForgeOS app (com.forgeos.app).",12,Color.LTGRAY,false));r.addView(bridge);
  String savedMission=getPreferences(0).getString(MISSION_TEXT,"");String savedState=getPreferences(0).getString(MISSION_STATE,"IDLE");
  if(!savedMission.isEmpty())mission.setText(savedMission);
  if(!"IDLE".equals(savedState)&&!"COMPLETED".equals(savedState)){
   // The simulated worker does not survive process death; resume it from the saved checkpoint instead of showing a stuck state.
   int attempt=getPreferences(0).getInt(MISSION_ATTEMPT,1);append("Resumed interrupted mission from checkpoint "+savedState+".");runWorker(savedMission,Math.max(attempt,2));
  }else if(!"IDLE".equals(savedState))status.setText(savedState+" • "+savedMission);
  launch.setOnClickListener(v->{String m=mission.getText().toString().trim();if(m.isEmpty()){status.setText("MISSION BLOCKED • Enter an objective");return;}startMission(m);});
  r.addView(txt("APEX v0.1 • Mission Control",11,Color.GRAY,false));return s;
 }
 private void checkpoint(String mission,String state,int attempt,String evidence){
  getPreferences(0).edit().putString(MISSION_TEXT,mission).putString(MISSION_STATE,state).putInt(MISSION_ATTEMPT,attempt).apply();
  status.setText(state+" • "+mission);append("["+state+"] attempt "+attempt+" • "+evidence);
  launch.setEnabled("COMPLETED".equals(state));
 }
 private void startMission(String mission){
  handler.removeCallbacksAndMessages(null);log.setText("Mission launched.");
  checkpoint(mission,"PLANNING",1,"Planner created a deterministic local execution plan.");
  handler.postDelayed(()->runWorker(mission,1),500);
 }
 private void runWorker(String mission,int attempt){
  checkpoint(mission,"RUNNING",attempt,"Worker started.");
  handler.postDelayed(()->{
   if(attempt==1){
    checkpoint(mission,"RECOVERING",attempt,"Controlled worker fault injected; checkpoint preserved. Recovery policy approved one retry.");
    handler.postDelayed(()->runWorker(mission,attempt+1),650);
   }else{
    checkpoint(mission,"VERIFYING",attempt,"Worker completed on retry; Tester/Judge validating terminal evidence.");
    handler.postDelayed(()->checkpoint(mission,"COMPLETED",attempt,"Verified local worker recovery path: failure → recovery → retry → verification → completion. External AI/tool execution remains disabled."),650);
   }
  },650);
 }
 private void append(String x){if(log!=null)log.setText(log.getText()+"\n"+x);}
 private LinearLayout panel(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(18),dp(16),dp(18),dp(16));l.setBackgroundColor(Color.rgb(20,23,30));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(6),0,dp(10));l.setLayoutParams(p);return l;}
 private TextView txt(String x,int z,int c,boolean b){TextView t=new TextView(this);t.setText(x);t.setTextSize(z);t.setTextColor(c);t.setPadding(0,dp(7),0,dp(7));if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
 private Button btn(String x){Button b=new Button(this);b.setText(x);b.setTextColor(Color.BLACK);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackgroundColor(GOLD);return b;}
 private int dp(int x){return(int)(x*getResources().getDisplayMetrics().density);}
}
