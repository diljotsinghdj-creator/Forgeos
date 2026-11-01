"""Read-only check of the pod and its latest production (prints no tokens or keys).

    curl -fsSL <raw url of this file> -o diag.py && /workspace/creatorforge/venv/bin/python diag.py
"""
import glob
import json
import os
import subprocess
import urllib.request

os.chdir("/workspace/creatorforge")
for src in ("/workspace/creatorforge/Forgeos", "/workspace/creatorforge/worker", "/workspace/creatorforge"):
    out = subprocess.run(["git", "-C", src, "log", "-1", "--format=%h %ci"], capture_output=True, text=True).stdout.strip()
    if out:
        print("worker commit:", out, f"({src})")
        break
else:
    print("worker commit: unknown")
print("ffmpeg:", (subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True).stdout.splitlines() or ["?"])[0][:40])
print("free stock / real photos (CF_FREE_STOCK):", os.environ.get("CF_FREE_STOCK", "(default on)"))

jobs = sorted(glob.glob("data/productions/*/job.json"), key=os.path.getmtime)
if not jobs:
    print("no productions yet")
else:
    j = json.load(open(jobs[-1]))
    s, p = j.get("spec", {}), j.get("plan") or {}
    scenes = p.get("scenes", [])
    beats = [b for sc in scenes for b in (sc.get("beats") or [])]
    print("job", j.get("id"), j.get("status"), "| faces:", s.get("faces"), "| style:", s.get("style"),
          "| template:", s.get("template"), "| aspect:", s.get("aspect"))
    print("script chars:", len(s.get("script") or ""), "| scenes:", len(scenes), "| beats:", len(beats))
    print("writer beats (script's own pictures):", sum(1 for b in beats if b.get("writer")),
          "| named beats (real-photo lines):", sum(1 for b in beats if b.get("named")))
    print("real-photo lookups:", {k: len((v or {}).get("pics") or []) for k, v in (j.get("named_cache") or {}).items()})
    print("first 5 scene visuals:", [str(sc.get("visual", ""))[:45] for sc in scenes[:5]])
    print("providers:", {k: v for k, v in (j.get("providers") or {}).items() if k in ("images", "director", "llm", "voice")})

try:
    r = urllib.request.urlopen(urllib.request.Request(
        "https://en.wikipedia.org/w/api.php?action=query&titles=Rahul_Gandhi&format=json",
        headers={"User-Agent": "CreatorForge-check"}), timeout=10)
    print("wikipedia reachable:", r.status)
except Exception as e:  # noqa: BLE001
    print("wikipedia: FAILED", e)
