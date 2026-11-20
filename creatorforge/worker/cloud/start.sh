#!/usr/bin/env bash
# Disconnect-proof launcher: downloads the setup and runs it in the background, so closing the
# browser tab or losing signal never interrupts it. Progress: tail -f /workspace/creatorforge/setup.log
set -e
mkdir -p /workspace/creatorforge
cd /workspace/creatorforge
BRANCH="${CF_BRANCH:-claude/forgeos-visibility-47vgwp}"
# Pin to the branch's latest commit so a CDN-cached old copy is never used.
SHA=$(curl -fsSL "https://api.github.com/repos/diljotsinghdj-creator/Forgeos/commits/$BRANCH" | grep -m1 '"sha"' | cut -d'"' -f4 || true)
REF="${SHA:-$BRANCH}"
curl -fsSL "https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/$REF/creatorforge/worker/cloud/setup_gpu.sh?nocache=$(date +%s)" -o setup_gpu.sh
echo "Using setup from ${SHA:0:7}${SHA:+ (latest)}"
pkill -f "bash setup_gpu.sh" 2>/dev/null || true
rm -f connection.txt
nohup setsid bash setup_gpu.sh > setup.log 2>&1 < /dev/null &
echo "Setup is running in the background (safe to close this tab)."
echo "Watching progress - press Ctrl+C to stop watching (setup keeps going):"
sleep 2
tail -n +1 -f setup.log
