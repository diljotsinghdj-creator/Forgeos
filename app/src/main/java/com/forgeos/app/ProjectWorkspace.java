package com.forgeos.app;

import java.io.File;
import java.util.Arrays;
import java.util.Comparator;

/** Pure-Java project discovery so import validation can be regression tested off-device. */
public final class ProjectWorkspace {
 private static final int MAX_DEPTH=8;
 private ProjectWorkspace(){}
 public static File findRoot(File f){return findRoot(f,0);}
 private static File findRoot(File f,int depth){
  if(f==null||!f.isDirectory()||depth>MAX_DEPTH)return null;
  boolean settings=file(f,"settings.gradle.kts")||file(f,"settings.gradle");
  boolean topBuild=file(f,"build.gradle.kts")||file(f,"build.gradle");
  File app=new File(f,"app");
  boolean appBuild=file(app,"build.gradle.kts")||file(app,"build.gradle");
  boolean manifest=file(f,"app/src/main/AndroidManifest.xml");
  if(settings||(topBuild&&(appBuild||manifest)))return f;
  File[] dirs=f.listFiles(x->x.isDirectory()&&!ignored(x.getName()));
  if(dirs!=null){Arrays.sort(dirs,Comparator.comparing(File::getName));for(File d:dirs){File r=findRoot(d,depth+1);if(r!=null)return r;}}
  return null;
 }
 public static boolean valid(File f){return f!=null&&f.isDirectory()&&findRoot(f)!=null;}
 private static boolean file(File d,String n){return new File(d,n).isFile();}
 private static boolean ignored(String n){return n.equals("__MACOSX")||n.equals(".git")||n.equals(".gradle")||n.equals("build")||n.equals("node_modules");}
}
