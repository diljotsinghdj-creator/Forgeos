#!/usr/bin/env bash
# Ramlila Kal Kya Hoga - make the Short on the pod and put the ElevenLabs voice-over on it, line for line.
#
#   bash pod_ramlila_short.sh /workspace/creatorforge/ramlila_vo.mp3
#
# 1. Renders the timed script (17 lines, real pictures) as a 9:16 Short: Investigative desk, faceless, fast cuts.
# 2. Waits for it (progress every 20 s).
# 3. Stretches each line's video onto your voice-over and swaps in your audio at -14 LUFS
#    (python -m creatorforge_worker.voiceover_sync), then adds the result to the Asset Library.
# Optional, for real stock photos: export PIXABAY_KEY=... in the terminal first (never paste keys into chat).
set -euo pipefail
VO="${1:?give the path of your ElevenLabs MP3, e.g. /workspace/creatorforge/ramlila_vo.mp3}"
[ -f "$VO" ] || { echo "No file at $VO - upload the MP3 to the pod first"; exit 1; }
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/india_2026/shorts/03_Ramlila_Kal_Kya_Hoga_ElevenLabs_Timed.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o ramlila_short.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }

JOB=$(python - <<'PY'
import json, os, urllib.request
body = {"script": open("ramlila_short.txt", encoding="utf-8").read(), "aspect": "9:16",
        "template": "shorts_cinematic", "style": "investigative", "faces": "faceless", "fast_cuts": True,
        "voice_speed": 1.1, "captions": True, "music": False}
if os.environ.get("PIXABAY_KEY"):
    body["stock"] = {"key": os.environ["PIXABAY_KEY"], "provider": "pixabay"}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print(json.load(urllib.request.urlopen(req))["id"])
PY
)
echo "Production $JOB started - it also appears in the app's Library."

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
    FAILED*|CANCELLED*) echo "Stopped. Check: tail -n 50 /workspace/creatorforge/worker.log"; exit 1 ;;
  esac
  sleep 20
done

python -m creatorforge_worker.voiceover_sync "$JOB" "$VO" --name "Ramlila Kal Kya Hoga - ElevenLabs" \
  --out /workspace/creatorforge/Ramlila_Kal_Kya_Hoga_final.mp4
echo "Final video: /workspace/creatorforge/Ramlila_Kal_Kya_Hoga_final.mp4"
