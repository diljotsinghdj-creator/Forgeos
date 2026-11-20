#!/usr/bin/env bash
# Storybook stickman sample: "Marcus" tells the story of garum, Rome's fish sauce (16:9, Hindi, about 1.5 min).
#   bash pod_storybook_sample.sh          (on the pod)      optional: export CF_VOICE=<your voice id>
set -euo pipefail
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/samples/storybook_garum_hindi.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o storybook.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
python - <<'PY'
import json, os, urllib.request
body = {"script": open("storybook.txt", encoding="utf-8").read(), "aspect": "16:9", "template": "youtube_longform",
        "style": "storybook_stickman", "faces": "show", "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", ""),
        "characters": [{"name": "Marcus", "description": "a Roman stickman merchant: plain white round head, simple dot eyes, "
                        "bushy black eyebrows, short curly black hair, thin black stick arms and legs, cream tunic with two "
                        "dark red stripes, brown leather belt and sandals"}]}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print("Production", json.load(urllib.request.urlopen(req))["id"], "started - it appears in the app's Library.")
PY
