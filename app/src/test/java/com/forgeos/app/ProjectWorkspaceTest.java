package com.forgeos.app;

import static org.junit.Assert.*;
import java.io.*;
import java.nio.file.*;
import org.junit.*;

public class ProjectWorkspaceTest {
 private Path tmp;
 @Before public void setup()throws Exception{tmp=Files.createTempDirectory("forgeos-test");}
 @After public void cleanup()throws Exception{delete(tmp.toFile());}
 @Test public void detectsWrappedAndroidRoot()throws Exception{
  File root=tmp.resolve("wrapper/project").toFile();new File(root,"app/src/main").mkdirs();
  touch(new File(root,"settings.gradle.kts"));touch(new File(root,"app/build.gradle.kts"));touch(new File(root,"app/src/main/AndroidManifest.xml"));
  assertEquals(root.getCanonicalFile(),ProjectWorkspace.findRoot(tmp.toFile()).getCanonicalFile());
 }
 @Test public void rejectsNestedModuleWithoutProjectRoot()throws Exception{
  File module=tmp.resolve("random/app").toFile();module.mkdirs();touch(new File(module,"build.gradle.kts"));
  assertNull(ProjectWorkspace.findRoot(tmp.toFile()));
 }
 @Test public void ignoresBuildAndGitDecoys()throws Exception{
  File decoy=tmp.resolve("build/fake").toFile();decoy.mkdirs();touch(new File(decoy,"settings.gradle"));
  File real=tmp.resolve("src/project").toFile();new File(real,"app/src/main").mkdirs();touch(new File(real,"settings.gradle"));touch(new File(real,"app/build.gradle"));touch(new File(real,"app/src/main/AndroidManifest.xml"));
  assertEquals(real.getCanonicalFile(),ProjectWorkspace.findRoot(tmp.toFile()).getCanonicalFile());
 }
 @Test public void depthBombIsBounded()throws Exception{
  File d=tmp.toFile();for(int i=0;i<12;i++){d=new File(d,"d"+i);d.mkdir();}touch(new File(d,"settings.gradle"));
  assertNull(ProjectWorkspace.findRoot(tmp.toFile()));
 }
 private static void touch(File f)throws Exception{File p=f.getParentFile();if(p!=null)p.mkdirs();try(FileOutputStream o=new FileOutputStream(f)){o.write(1);}}
 private static void delete(File f){File[] a=f.listFiles();if(a!=null)for(File x:a)delete(x);f.delete();}
}
