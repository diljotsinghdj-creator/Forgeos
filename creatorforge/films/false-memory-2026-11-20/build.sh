#!/bin/sh
# Rebuild every key frame and the contact sheets. Needs /home/user/forgeos -> the repo (fonts are served from the worker's vendor folder).
set -e
cd "$(dirname "$0")"
[ -f assets/real/thompson_cotton.jpg ] || { python3 -I fetch_real.py; python3 -I real.py; }
python3 -c "import frames_a, frames_b, frames_c"
[ $# -gt 0 ] && python3 shoot_http.py "$@" || python3 shoot_http.py $(ls html | grep "^[0-9]" | sed "s/\.html$//")   # key frames only, unless pages are named
python3 sheets.py
python3 qa_edges.py | tail -6
