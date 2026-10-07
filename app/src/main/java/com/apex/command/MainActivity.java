package com.apex.command;

import android.app.*;
import android.os.Bundle;
import android.content.*;
import android.graphics.*;
import android.graphics.Typeface;
import android.view.View;
import android.widget.*;
import java.util.*;

public class MainActivity extends Activity {
 private final int GOLD=Color.rgb(212,175,55);
 private TextView status,log,identityView; private EditText mission;
 private static final String STATE="mission_state",TEXT="mission_text",ATTEMPT="mission_attempt",IDS="identities",ACTIVE="active_identity";
 @Override public void onCreate(Bundle b){super.onCreate(b);setContentView(ui());}
 private View ui(){
  ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.rgb(7,9,13));
  LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.VERTICAL);r.setPadding(dp(22),dp(22),dp(22),dp(30));s.addView(r);
  r.addView(txt("APEX",32,GOLD,true));r.addView(txt("Brand-agnostic Mission Control",13,Color.LTGRAY,false));
  LinearLayout id=panel();id.addView(txt("ACTIVE SOCIAL IDENTITY",12,GOLD,true));identityView=txt(activeIdentity(),17,Color.WHITE,true);id.addView(identityView);
  Button manage=btn("MANAGE IDENTITIES");manage.setOnClickListener(v->identityDialog());id.addView(manage);r.addView(id);
  LinearLayout hero=panel();hero.addView(txt("COMMAND APEX",12,GOLD,true));hero.addView(txt("What do you want accomplished?",20,Color.WHITE,true));
  mission=new EditText(this);mission.setHint("Describe a mission…");mission.setTextColor(Color.WHITE);mission.setHintTextColor(Color.GRAY);mission.setMinLines(3);mission.setGravity(android.view.Gravity.TOP);hero.addView(mission);
  Button launch=btn("LAUNCH MISSION");launch.setOnClickListener(v->launch());hero.addView(launch);r.addView(hero);
  LinearLayout live=panel();live.addView(txt("MISSION STATUS",12,GOLD,true));status=txt(saved(STATE,"IDLE")+" • "+saved(TEXT,"Awaiting mission"),16,Color.WHITE,true);live.addView(status);r.addView(live);
  LinearLayout ev=panel();ev.addView(txt("EVIDENCE",12,GOLD,true));log=txt("APEX records only work it actually performs. Unsupported external execution is BLOCKED, never reported as completed.",12,Color.LTGRAY,false);ev.addView(log);r.addView(ev);
  String m=saved(TEXT,"");if(!m.isEmpty())mission.setText(m);
  r.addView(txt("APEX • independent Android identity com.apex.command",11,Color.GRAY,false));return s;
 }
 private void launch(){
  String m=mission.getText().toString().trim();if(m.isEmpty()){checkpoint("", "BLOCKED",0,"Objective is empty.");return;}
  checkpoint(m,"PLANNING",1,"Objective bound to identity: "+activeIdentity());
  ArrayList<String> plan=plan(m);
  if(plan.isEmpty()){checkpoint(m,"BLOCKED",1,"No locally executable capability matched. APEX refused to fabricate completion.");return;}
  checkpoint(m,"RUNNING",1,"Plan: "+join(plan));
  String out=executeLocal(m,plan);
  checkpoint(m,"VERIFYING",1,"Tester checking produced artifact.");
  if(out==null||out.trim().length()<20){checkpoint(m,"FAILED",1,"Output evidence missing or too small.");return;}
  getPreferences(0).edit().putString("last_output",out).apply();
  checkpoint(m,"COMPLETED",1,"Verified local output produced ("+out.length()+" chars).");
  new AlertDialog.Builder(this).setTitle("APEX OUTPUT").setMessage(out).setPositiveButton("COPY",(d,w)->((android.content.ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("APEX output",out))).setNegativeButton("CLOSE",null).show();
 }
 private ArrayList<String> plan(String m){ArrayList<String> p=new ArrayList<>();String q=m.toLowerCase(Locale.ROOT);
  if(q.contains("script")||q.contains("video")||q.contains("post")||q.contains("caption")||q.contains("content")){p.add("content-brief");p.add("script-outline");p.add("publishing-pack");}
  return p;
 }
 private String executeLocal(String m,ArrayList<String> p){
  String id=activeIdentity();StringBuilder b=new StringBuilder();
  b.append("IDENTITY: ").append(id).append("\nOBJECTIVE: ").append(m).append("\n\n");
  b.append("CONTENT BRIEF\nAudience: configured channel audience\nGoal: clear single-message retention arc\nFormat: hook → context → payoff → CTA\n\n");
  b.append("SCRIPT OUTLINE\n0-3s: Pattern-interrupt hook tied directly to the objective.\n3-10s: Establish the problem and stakes.\n10-22s: Deliver three concise proof/value beats.\n22-27s: Resolve the opening promise.\n27-30s: One specific CTA.\n\n");
  b.append("PUBLISHING PACK\nTitle: ").append(trim(m,62)).append("\nCaption: ").append(trim(m,110)).append(" — built for ").append(id).append(".\n");
  b.append("Verification: generated locally by APEX; no external media, AI model, upload, or publishing action was claimed.");
  return b.toString();
 }
 private void identityDialog(){
  final EditText e=new EditText(this);e.setHint("Identity/channel name");e.setSingleLine(true);
  new AlertDialog.Builder(this).setTitle("Add social identity").setMessage("APEX identities are configurable and are not tied to any brand or platform.").setView(e).setPositiveButton("ADD",(d,w)->{
   String n=e.getText().toString().trim();if(n.isEmpty())return;LinkedHashSet<String> x=identities();x.add(n);saveIds(x);setActive(n);
  }).setNeutralButton("SELECT",(d,w)->selectIdentity()).setNegativeButton("CANCEL",null).show();
 }
 private void selectIdentity(){final String[] a=identities().toArray(new String[0]);new AlertDialog.Builder(this).setTitle("Select identity").setItems(a,(d,i)->setActive(a[i])).show();}
 private LinkedHashSet<String> identities(){LinkedHashSet<String>x=new LinkedHashSet<>();String raw=saved(IDS,"Default Channel");for(String n:raw.split("\\|"))if(!n.trim().isEmpty())x.add(n.trim());if(x.isEmpty())x.add("Default Channel");return x;}
 private void saveIds(LinkedHashSet<String>x){getPreferences(0).edit().putString(IDS,join(new ArrayList<>(x))).apply();}
 private void setActive(String n){getPreferences(0).edit().putString(ACTIVE,n).apply();if(identityView!=null)identityView.setText(n);append("Identity selected: "+n);}
 private String activeIdentity(){return saved(ACTIVE,"Default Channel");}
 private void checkpoint(String m,String st,int a,String e){getPreferences(0).edit().putString(TEXT,m).putString(STATE,st).putInt(ATTEMPT,a).apply();if(status!=null)status.setText(st+" • "+(m.isEmpty()?"No mission":m));append("["+st+"] "+e);}
 private String saved(String k,String d){return getPreferences(0).getString(k,d);}
 private void append(String x){if(log!=null)log.setText(log.getText()+"\n"+x);}
 private String join(ArrayList<String>x){StringBuilder b=new StringBuilder();for(int i=0;i<x.size();i++){if(i>0)b.append(" | ");b.append(x.get(i));}return b.toString();}
 private String trim(String s,int n){return s.length()<=n?s:s.substring(0,n-1)+"…";}
 private LinearLayout panel(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(18),dp(16),dp(18),dp(16));l.setBackgroundColor(Color.rgb(24,24,24));return l;}
 private TextView txt(String x,int z,int c,boolean b){TextView t=new TextView(this);t.setText(x);t.setTextSize(z);t.setTextColor(c);t.setPadding(0,dp(7),0,dp(7));if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
 private Button btn(String x){Button b=new Button(this);b.setText(x);b.setTextColor(Color.BLACK);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackgroundColor(GOLD);return b;}
 private int dp(int x){return(int)(x*getResources().getDisplayMetrics().density);}
}