#!/usr/bin/env bash
# Israel 2026 HINGLISH: Woh Chunav Jisne Kuch Tay Nahin Kiya - render all six parts on the pod and join them into one film.
#
#   bash pod_israel_hinglish.sh                      # CreatorForge narration
#   bash pod_israel_hinglish.sh /workspace/vo_hi     # + your ElevenLabs MP3s: R1.mp3 ... R6.mp3 in that folder
#
# Each part: 16:9, YouTube Documentary template, Investigative desk, faceless, captions on, music off (add music in
# the edit), voice speed 1.0, your Hindi voice (export CF_VOICE=<voice id from the app>, else the pod default). Part 4 (Gaza / West Bank, R3) renders with fast cuts OFF.
# Optional real stock: export PIXABAY_KEY=... in the terminal first (never paste keys into chat).
# Output: /workspace/creatorforge/israel_2026_hinglish/Israel_2026_Hinglish_full.mp4 (+ each part). Every part also appears in the app's Library.
set -euo pipefail
VO_DIR="${1:-}"
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
OUT=/workspace/creatorforge/israel_2026_hinglish
mkdir -p "$OUT"
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/israel_2026/hinglish/render"
PARTS=(R1_Cold_Open_aur_Part_1 R2_Part_2_aur_3 R3_Part_4_Gaza_aur_West_Bank R4_Part_5_Kingmakers
       R5_Part_6_Paisa_Missiles_Washington R6_Part_7_aur_8)

start() {   # $1 script file, $2 fast cuts (1/0)
  python - "$1" "$2" <<'PY'
import json, os, sys, urllib.request
body = {"script": open(sys.argv[1], encoding="utf-8").read(), "aspect": "16:9", "template": "youtube_longform",
        "style": "investigative", "faces": "faceless", "fast_cuts": sys.argv[2] == "1",
        "voice_speed": 1.0, "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", "")}
if os.environ.get("PIXABAY_KEY"):
    body["stock"] = {"key": os.environ["PIXABAY_KEY"], "provider": "pixabay"}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print(json.load(urllib.request.urlopen(req))["id"])
PY
}
state() {
  python - "$1" <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request(os.environ["API"] + "/v1/productions/" + sys.argv[1],
                             headers={"Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
j = json.load(urllib.request.urlopen(req))
print(j["status"], f"{100 * (j.get('progress') or 0):.0f}%", (j.get("message") or "")[:60])
PY
}

: > "$OUT/concat.txt"
n=0
for P in "${PARTS[@]}"; do
  n=$((n + 1))
  curl -fsSL "$RAW/$P.txt?nocache=$(date +%s)" -o "$OUT/$P.txt"
  FAST=1; [ "$n" = 3 ] && FAST=0
  JOB=$(start "$OUT/$P.txt" "$FAST")
  echo "Part $n/6 ($P): production $JOB started"
  while true; do
    S=$(state "$JOB"); echo "$(date +%H:%M:%S)  part $n  $S"
    case "$S" in READY*) break ;; FAILED*|CANCELLED*) echo "Part $n stopped. Check: tail -n 50 /workspace/creatorforge/worker.log"; exit 1 ;; esac
    sleep 30
  done
  DEST="$OUT/$(printf '%02d' $n)_$P.mp4"
  if [ -n "$VO_DIR" ] && [ -f "$VO_DIR/R$n.mp3" ]; then
    python -m creatorforge_worker.voiceover_sync "$JOB" "$VO_DIR/R$n.mp3" --name "Israel 2026 Hinglish part $n - ElevenLabs" --out "$DEST"
  else
    FILE=$(python -c "import json,sys;j=json.load(open('data/productions/$JOB/job.json'));print(j['result']['file'])")
    cp "data/productions/$JOB/$FILE" "$DEST"
  fi
  echo "file '$DEST'" >> "$OUT/concat.txt"
  echo "Part $n ready: $DEST"
done

# Join: re-encode so parts with slightly different audio settings join cleanly.
ffmpeg -y -loglevel error -f concat -safe 0 -i "$OUT/concat.txt" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart "$OUT/Israel_2026_Hinglish_full.mp4"
echo "Full film: $OUT/Israel_2026_Hinglish_full.mp4  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/Israel_2026_Hinglish_full.mp4" | cut -d. -f1) s)"
