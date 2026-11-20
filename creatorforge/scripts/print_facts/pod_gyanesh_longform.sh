#!/usr/bin/env bash
# Gyanesh Kumar Ka Poora Sach - make the ~17 min Hinglish long-form on the pod, in one production.
#
#   bash pod_gyanesh.sh                                   # CreatorForge Hindi voice
#   bash pod_gyanesh.sh /workspace/vo_hi/gyanesh_full.mp3 # + your ElevenLabs voice-over, synced line by line
#
# 16:9, YouTube Documentary, Investigative desk, faceless, fast cuts, captions on, music off.
# Optional: export CF_VOICE=<Hindi voice id from the app>  and  export PIXABAY_KEY=...  (never paste keys into chat).
set -euo pipefail
VO="${1:-}"
if [ -n "$VO" ] && [ ! -f "$VO" ]; then echo "No file at $VO - upload the MP3 to the pod first"; exit 1; fi
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/print_facts/long_form/07_Gyanesh_Kumar_Poora_Sach_FINAL_Hinglish.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o gyanesh_full.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }

JOB=$(python - <<'PY'
import json, os, urllib.request
body = {"script": open("gyanesh_full.txt", encoding="utf-8").read(), "aspect": "16:9",
        "template": "youtube_longform", "style": "investigative", "faces": "faceless", "fast_cuts": True,
        "voice_speed": 1.0, "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", "")}
if os.environ.get("PIXABAY_KEY"):
    body["stock"] = {"key": os.environ["PIXABAY_KEY"], "provider": "pixabay"}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
try:
    print(json.load(urllib.request.urlopen(req))["id"])
except urllib.error.HTTPError as e:
    raise SystemExit("Refused: " + e.read().decode()[:300] + "\n(If it says 'too long', the worker is old - run the update command.)")
PY
)
echo "Production $JOB started - it also appears in the app's Library. A 17 min film takes a while (often 30-90 min)."

while true; do
  STATE=$(python - "$JOB" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(os.environ["API"] + "/v1/productions/" + sys.argv[1],
                             headers={"Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
j = json.load(urllib.request.urlopen(req))
print(j["status"], f"{100 * (j.get('progress') or 0):.0f}%", (j.get("message") or "")[:70])
PY
)
  echo "$(date +%H:%M:%S)  $STATE"
  case "$STATE" in
    READY*) break ;;
    FAILED*|CANCELLED*) echo "Stopped. Retry resumes where it failed: in the app tap Retry. Log: tail -n 50 /workspace/creatorforge/worker.log"; exit 1 ;;
  esac
  sleep 30
done

if [ -n "$VO" ]; then
  python -m creatorforge_worker.voiceover_sync "$JOB" "$VO" --name "Gyanesh Kumar - ElevenLabs" \
    --out /workspace/creatorforge/Gyanesh_Kumar_final.mp4
  echo "Final video: /workspace/creatorforge/Gyanesh_Kumar_final.mp4"
else
  echo "Done - download it from the app's Library (production $JOB)."
fi
