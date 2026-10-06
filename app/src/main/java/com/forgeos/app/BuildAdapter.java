package com.forgeos.app;

/** External build systems are adapters; ForgeOS core must not depend on any one provider. */
public interface BuildAdapter {
 String id();
 boolean isAvailable();
 BuildResult submit(String missionId, java.io.File workspace) throws Exception;
 final class BuildResult {
  public final boolean accepted; public final String reference; public final String message;
  public BuildResult(boolean a,String r,String m){accepted=a;reference=r;message=m;}
 }
}