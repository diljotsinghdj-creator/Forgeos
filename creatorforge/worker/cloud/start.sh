#!/usr/bin/env bash
# Disconnect-proof launcher: downloads the setup and runs it in the background, so closing the
# browser tab or losing signal never interrupts it. Progress: tail -f /workspace/creatorforge/setup.log
set -e
mkdir -p /workspace/creatorforge
cd /workspace/creatorforge
curl -fsSL "https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/${CF_BRANCH:-claude/forgeos-visibility-47vgwp}/creatorforge/worker/cloud/setup_gpu.sh" -o setup_gpu.sh
pkill -f "bash setup_gpu.sh" 2>/dev/null || true
rm -f connection.txt
nohup setsid bash setup_gpu.sh > setup.log 2>&1 < /dev/null &
echo "Setup is running in the background (safe to close this tab)."
echo "Watching progress - press Ctrl+C to stop watching (setup keeps going):"
sleep 2
tail -n +1 -f setup.log
