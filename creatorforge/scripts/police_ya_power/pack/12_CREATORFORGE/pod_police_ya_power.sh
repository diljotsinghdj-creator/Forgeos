#!/usr/bin/env bash
# POLICE YA POWER? - render the documentary on the pod (16:9), then a 4K master.
#   bash pod_police_ya_power.sh                                   # CreatorForge voice (scratch)
#   bash pod_police_ya_power.sh /workspace/vo_hi/police_ya_power.mp3   # + your ElevenLabs voice-over, synced line by line
# Keys live in worker.env / the app's encrypted settings - never paste them into chat.
set -euo pipefail
VO="${1:-}"
if [ -n "$VO" ] && [ ! -f "$VO" ]; then echo "No file at $VO - upload the MP3 to the pod first"; exit 1; fi
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/police_ya_power/police_ya_power_creatorforge.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o police_ya_power.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
JOB=$(python - <<'PY'
import json, os, urllib.request
body = {"script": open("police_ya_power.txt", encoding="utf-8").read(), "aspect": "16:9",
        "template": "youtube_longform", "style": "investigative", "faces": "faceless", "fast_cuts": False,
        "voice_speed": 1.0, "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", "")}
if os.environ.get("PIXABAY_KEY"):
    body["stock"] = {"key": os.environ["PIXABAY_KEY"], "provider": "pixabay"}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print(json.load(urllib.request.urlopen(req))["id"])
PY
)
echo "Production $JOB started - also in the app's Library."
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
  case "$STATE" in READY*) break ;; FAILED*|CANCELLED*) echo "Stopped - tap Retry in the app"; exit 1 ;; esac
  sleep 30
done
OUT=/workspace/creatorforge/POLICE_YA_POWER_1080p.mp4
if [ -n "$VO" ]; then
  python -m creatorforge_worker.voiceover_sync "$JOB" "$VO" --name "Police Ya Power - ElevenLabs" --out "$OUT"
else
  python - "$JOB" "$OUT" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(os.environ["API"] + "/v1/productions/" + sys.argv[1] + "/video",
                             headers={"Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
open(sys.argv[2], "wb").write(urllib.request.urlopen(req).read())
PY
fi
# 4K master: an upscale of the 1080p render (lanczos + light sharpen), loudness to YouTube's -14 LUFS.
ffmpeg -nostdin -y -i "$OUT" -vf "scale=3840:2160:flags=lanczos,unsharp=5:5:0.4" -c:v libx264 -preset slow -crf 16 \
  -pix_fmt yuv420p -af "loudnorm=I=-14:TP=-1:LRA=9" -c:a aac -b:a 320k -movflags +faststart \
  /workspace/creatorforge/POLICE_YA_POWER_4K.mp4
echo "Done: /workspace/creatorforge/POLICE_YA_POWER_4K.mp4 (upscaled 4K master) and $OUT"
