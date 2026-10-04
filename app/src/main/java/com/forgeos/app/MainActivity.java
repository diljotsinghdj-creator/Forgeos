package com.forgeos.app;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.View;
import android.widget.*;

public class MainActivity extends Activity {
 private final int GOLD=Color.rgb(212,175,55);
 private LinearLayout projects; private TextView status;
 @Override public void onCreate(Bundle b){super.onCreate(b);setContentView(ui());}
 private View ui(){
  ScrollView s=new ScrollView(this);s.setBackgroundColor(Color.rgb(9,9,9));
  LinearLayout r=new LinearLayout(this);r.setOrientation(LinearLayout.VERTICAL);r.setPadding(dp(22),dp(28),dp(22),dp(28));s.addView(r);
  r.addView(txt("FORGEOS",30,GOLD,true));r.addView(txt("Android Development Workspace",14,Color.LTGRAY,false));
  LinearLayout c=panel();c.addView(txt("BUILD CONTROL",12,GOLD,true));status=txt("Ready - cloud build pipeline configured",16,Color.WHITE,true);c.addView(status);c.addView(txt("Import an Android project ZIP. This bootstrap build validates the ForgeOS shell before build execution is connected.",13,Color.LTGRAY,false));r.addView(c);
  Button i=btn("IMPORT PROJECT ZIP");i.setOnClickListener(v->{Intent x=new Intent(Intent.ACTION_OPEN_DOCUMENT);x.setType("application/zip");x.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(x,100);});r.addView(i);
  Button build=btn("BUILD APK");build.setEnabled(false);r.addView(build);
  r.addView(txt("PROJECTS",12,GOLD,true));projects=panel();projects.addView(txt("No project imported yet",15,Color.LTGRAY,false));r.addView(projects);
  r.addView(txt("ForgeOS v0.1 - Bootstrap Build",11,Color.GRAY,false));return s;
 }
 @Override protected void onActivityResult(int q,int result,Intent data){super.onActivityResult(q,result,data);if(q==100&&result==RESULT_OK&&data!=null){Uri u=data.getData();if(u!=null){projects.removeAllViews();projects.addView(txt("Imported: "+u.getLastPathSegment(),15,Color.WHITE,true));status.setText("Project selected - workspace engine next");}}}
 private LinearLayout panel(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(18),dp(18),dp(18),dp(18));l.setBackgroundColor(Color.rgb(24,24,24));return l;}
 private TextView txt(String x,int z,int c,boolean b){TextView t=new TextView(this);t.setText(x);t.setTextSize(z);t.setTextColor(c);t.setPadding(0,dp(8),0,dp(8));if(b)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
 private Button btn(String x){Button b=new Button(this);b.setText(x);b.setTextColor(Color.BLACK);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setBackgroundColor(GOLD);return b;}
 private int dp(int x){return(int)(x*getResources().getDisplayMetrics().density);}
}