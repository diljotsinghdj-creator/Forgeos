package com.forgeos.app;

import java.util.*;

/** Selects an available execution adapter without coupling core mission state to GitHub. */
public final class BuildAdapterRegistry {
 private final List<BuildAdapter> adapters=new ArrayList<>();
 public BuildAdapterRegistry add(BuildAdapter a){if(a!=null)adapters.add(a);return this;}
 public BuildAdapter firstAvailable(){
  for(BuildAdapter a:adapters)try{if(a.isAvailable())return a;}catch(RuntimeException ignored){}
  return null;
 }
 public List<String> ids(){List<String>x=new ArrayList<>();for(BuildAdapter a:adapters)x.add(a.id());return Collections.unmodifiableList(x);}
}