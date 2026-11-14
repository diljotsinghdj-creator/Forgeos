#!/usr/bin/env bash
# BJP IT CELL KA SACH - render the documentary on the pod (16:9), then a 4K master.
#   bash pod_bjp_it_cell.sh                                   # CreatorForge voice (scratch)
#   bash pod_bjp_it_cell.sh /workspace/vo_hi/bjp_it_cell.mp3   # + your ElevenLabs voice-over, synced line by line
#   bash pod_bjp_it_cell.sh latest                              # ... the newest audio uploaded in the app's Library
# Real HD footage on the script's Stock: lines needs the free Pixabay key as a pod environment variable PIXABAY_KEY.
# Keys live in worker.env / the app's encrypted settings - never paste them into chat.
set -euo pipefail
VO="${1:-}"
# VO can be a file on the pod, or "latest" / part of a name: an MP3 uploaded in the app (Library -> Asset Library)
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/bjp_it_cell/PASTE_IN_CREATORFORGE.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o bjp_it_cell.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
JOB=$(python - <<'PY'
import json, os, urllib.request
# Cinematic film: full modern scenes (the desk/collage looks put cut-outs on plain paper). The pod's own Hindi
# voice is only a guide track for timing when your ElevenLabs MP3 is given - it is replaced line by line.
body = {"script": open("bjp_it_cell.txt", encoding="utf-8").read(), "aspect": "16:9",
        "template": "youtube_longform", "style": "cinematic", "faces": "faceless", "fast_cuts": True,
        "auto_edit": True, "sfx": True, "voice_speed": 1.0, "captions": True, "music": False,
        "voice": os.environ.get("CF_VOICE", "hindi_m_human")}
if not os.environ.get("PIXABAY_KEY"):
    import sys
    print("No PIXABAY_KEY: the 20 real-footage lines use AI pictures instead (add the free key as a pod variable)",
          file=sys.stderr)
else:
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
OUT=/workspace/creatorforge/BJP_IT_CELL_1080p.mp4
if [ -n "$VO" ]; then
  python -m creatorforge_worker.voiceover_sync "$JOB" "$VO" --name "BJP IT Cell - ElevenLabs" --out "$OUT"
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
  /workspace/creatorforge/BJP_IT_CELL_4K.mp4
echo "Done: /workspace/creatorforge/BJP_IT_CELL_4K.mp4 (upscaled 4K master) and $OUT"
