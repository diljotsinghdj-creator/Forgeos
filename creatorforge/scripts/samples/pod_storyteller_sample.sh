#!/usr/bin/env bash
# Storyteller sample: "Dastango" presents a 45 s Hindi Short in the 3D-animated look, the same character in every scene.
#   bash pod_storyteller_sample.sh            (on the pod, in /workspace/creatorforge)
# Optional: export CF_VOICE=<voice id from the app, e.g. your ElevenLabs voice>
set -euo pipefail
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
export API="http://127.0.0.1:${CF_PORT:-8765}"
RAW="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/scripts/samples/storyteller_constitution_short.txt"
curl -fsSL "$RAW?nocache=$(date +%s)" -o storyteller.txt
curl -fsS "$API/health" > /dev/null || { echo "The worker is not running - run the update command first"; exit 1; }
JOB=$(python - <<'PY'
import json, os, urllib.request
body = {"script": open("storyteller.txt", encoding="utf-8").read(), "aspect": "9:16", "template": "shorts_cinematic",
        "style": "animated_3d", "faces": "show", "captions": True, "music": False, "voice": os.environ.get("CF_VOICE", ""),
        "characters": [{"name": "Dastango", "description":
            "an original elderly Indian storyteller character: long neat grey beard and moustache, round black glasses, "
            "kind smiling eyes, bushy grey eyebrows, maroon Nehru jacket over a cream kurta, brown leather satchel, "
            "always carrying an old leather-bound book; 3D animated feature film style"}]}
req = urllib.request.Request(os.environ["API"] + "/v1/productions", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ.get("CF_WORKER_TOKEN", "")})
print(json.load(urllib.request.urlopen(req))["id"])
PY
)
echo "Production $JOB started - it also appears in the app's Library (a few minutes on the GPU)."
