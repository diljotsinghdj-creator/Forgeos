#!/usr/bin/env bash
# YouTube thumbnails for "Gyanesh Kumar Ka Poora Sach" (1280x720): his real, credited Wikipedia/Commons photo,
# never an AI face. Three layouts to A/B test; all three go into the app's Library -> Asset Library -> Image.
#   curl -fsSL <raw url of this file> -o thumb.sh && bash thumb.sh
set -euo pipefail
cd /workspace/creatorforge
. venv/bin/activate
set -a; . ./worker.env; set +a
BR="https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/worker/creatorforge_worker"
PKG=$(python -c "import creatorforge_worker, os; print(os.path.dirname(creatorforge_worker.__file__))")
curl -fsSL "$BR/yt_thumbnail.py?nocache=$(date +%s)" -o "$PKG/yt_thumbnail.py"
python -m creatorforge_worker.yt_thumbnail --person "Gyanesh Kumar" --tag "ज्ञानेश कुमार" \
  --big "13.3 करोड़" --mid "नाम कटे" --question "BJP के लिए इतने ज़रूरी क्यों?" \
  --alt "इस्तीफ़ा|क्यों नहीं?|ज्ञानेश कुमार का पूरा सच" \
  --alt "BJP KE LIYE|ITNE ZAROORI KYUN?|Gyanesh Kumar Ka Poora Sach" \
  --name "Gyanesh thumbnail" --out /workspace/creatorforge/thumbnails
