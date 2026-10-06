#!/usr/bin/env bash
# CreatorForge worker on a rented NVIDIA GPU (RunPod, Vast.ai, or any Ubuntu box with CUDA).
# Run as root in the machine's terminal:
#   curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/worker/cloud/setup_gpu.sh | bash
# Re-running is safe and fast: code is updated, downloaded models are reused.
set -euo pipefail

BRANCH="${CF_BRANCH:-claude/forgeos-visibility-47vgwp}"
HOME_DIR="${CF_HOME:-/workspace/creatorforge}"   # /workspace survives pod restarts on RunPod volumes
PORT="${CF_PORT:-8765}"
LLM_MODEL="${CF_LLM_MODEL:-qwen2.5:7b-instruct}"
IMAGE_MODEL="${CF_IMAGE_MODEL:-black-forest-labs/FLUX.1-schnell}"
IDLE_MINUTES="${CF_IDLE_MINUTES:-30}"   # stop the pod after this many minutes with no video work (0 = never)
VIDEO="${CF_VIDEO:-fast}"   # fast = Wan 2.2 TI2V-5B (720p, 24 GB GPU) | max = Wan 2.2 I2V-A14B (80 GB GPU, ~200 GB disk) | off
case "$VIDEO" in
  fast) VIDEO_MODEL="Wan-AI/Wan2.2-TI2V-5B-Diffusers" ;;
  max)  VIDEO_MODEL="Wan-AI/Wan2.2-I2V-A14B-Diffusers" ;;
  off)  VIDEO_MODEL="" ;;
  *) echo "CF_VIDEO must be fast, max or off"; exit 1 ;;
esac

say() { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
mkdir -p "$HOME_DIR"/{data,hf,ollama,music,sfx}
cd "$HOME_DIR"

say "Checking GPU"
if ! command -v nvidia-smi >/dev/null || ! nvidia-smi >/dev/null 2>&1; then
  echo "No NVIDIA GPU found. Pick a GPU machine (RTX 4090 / L4 / A5000 / RTX 3090, 24 GB VRAM recommended)."; exit 1
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

say "Checking disk space"
FREE_GB=$(df -BG --output=avail "$HOME_DIR" | tail -1 | tr -dc '0-9')
NEED_GB=$([ "$VIDEO" = "max" ] && echo 180 || ([ "$VIDEO" = "off" ] && echo 50 || echo 80))
echo "  free: ${FREE_GB} GB, needed for models: ~${NEED_GB} GB (in $HOME_DIR)"
if [ "${FREE_GB:-0}" -lt "$NEED_GB" ]; then
  echo "Not enough disk. Stop the pod, edit it and raise the disk / volume size to at least ${NEED_GB} GB"
  echo "(or run with CF_HOME pointing at a bigger disk). Then run this command again."
  exit 1
fi

say "Installing system packages (ffmpeg, espeak-ng, fonts)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ffmpeg espeak-ng git curl fonts-dejavu-core python3-venv >/dev/null

say "Fetching CreatorForge ($BRANCH)"
if [ -d Forgeos/.git ]; then
  git -C Forgeos fetch -q --depth 1 origin "$BRANCH" && git -C Forgeos checkout -q -B "$BRANCH" FETCH_HEAD
else
  git clone -q --depth 1 -b "$BRANCH" https://github.com/diljotsinghdj-creator/Forgeos.git
fi

say "Installing the worker (Python packages; first run takes a few minutes)"
[ -d venv ] || python3 -m venv --system-site-packages venv   # reuse the image's CUDA PyTorch when present
# shellcheck disable=SC1091
. venv/bin/activate
pip install -q --upgrade pip
pip install -q -e "Forgeos/creatorforge/worker[whisper,kokoro,diffusers]" huggingface_hub
python -c "import torch; assert torch.cuda.is_available(), 'PyTorch cannot see the GPU'; print('PyTorch', torch.__version__, 'CUDA OK')"
python -m spacy download en_core_web_sm -q >/dev/null 2>&1 || true   # used by Kokoro's English text front-end

export HF_HOME="$HOME_DIR/hf"
say "Downloading image model $IMAGE_MODEL (first time ~25 GB; reused afterwards)"
python - <<PY
from huggingface_hub import snapshot_download
# diffusers needs the per-component folders, not the duplicate single-file checkpoints
snapshot_download("$IMAGE_MODEL", ignore_patterns=["flux1-*.safetensors", "ae.safetensors", "*.md", "*.png", "*.jpg"])
PY
if [ -n "$VIDEO_MODEL" ]; then
  say "Downloading realistic video model $VIDEO_MODEL (first time 20-60 GB; reused afterwards)"
  python -c "from huggingface_hub import snapshot_download; snapshot_download('$VIDEO_MODEL', ignore_patterns=['*.md', 'assets/*', 'examples/*'])"
fi

say "Installing Ollama and the script model $LLM_MODEL"
command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh
export OLLAMA_MODELS="$HOME_DIR/ollama" OLLAMA_KEEP_ALIVE=2m   # free VRAM soon after the script is written
if ! curl -fs http://127.0.0.1:11434/api/tags >/dev/null; then
  nohup ollama serve > ollama.log 2>&1 &
  for _ in $(seq 1 30); do curl -fs http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 1; done
fi
ollama pull "$LLM_MODEL"

say "Configuring the worker"
[ -s token ] || python -c "import secrets; print(secrets.token_urlsafe(24))" > token
TOKEN="$(cat token)"
cat > worker.env <<ENV
CF_DATA_DIR=$HOME_DIR/data
CF_PORT=$PORT
CF_WORKER_TOKEN=$TOKEN
HF_HOME=$HOME_DIR/hf
CF_LLM_URL=http://127.0.0.1:11434/v1
CF_LLM_MODEL=$LLM_MODEL
CF_IMAGE_PROVIDER=diffusers
CF_IMAGE_MODEL=$IMAGE_MODEL
CF_VOICES='[{"id":"warm","name":"Warm (US female)","provider":"kokoro","voice":"af_heart"},{"id":"deep","name":"Deep (US male)","provider":"kokoro","voice":"am_michael"},{"id":"british_f","name":"British female","provider":"kokoro","voice":"bf_emma","lang":"b"},{"id":"british_m","name":"British male","provider":"kokoro","voice":"bm_george","lang":"b"}]'
CF_ASR_PROVIDER=whisper
CF_WHISPER_MODEL=small
CF_WHISPER_DEVICE=cuda
CF_MUSIC_DIR=$HOME_DIR/music
CF_SFX_DIR=$HOME_DIR/sfx
ENV
if [ -n "$VIDEO_MODEL" ]; then printf 'CF_VIDEO_PROVIDER=diffusers\nCF_VIDEO_MODEL=%s\n' "$VIDEO_MODEL" >> worker.env; fi

say "Starting the worker on port $PORT"
pkill -f "bin/creatorforge-worker" 2>/dev/null || true
nohup bash -c "set -a; . '$HOME_DIR/worker.env'; set +a; exec '$HOME_DIR/venv/bin/creatorforge-worker'" > worker.log 2>&1 &
for _ in $(seq 1 60); do curl -fs "http://127.0.0.1:$PORT/health" >/dev/null && break; sleep 1; done
curl -fs "http://127.0.0.1:$PORT/health" >/dev/null || { echo "Worker did not start - see $HOME_DIR/worker.log"; tail -n 40 worker.log; exit 1; }
python - <<PY
import json, urllib.request
h = json.load(urllib.request.urlopen("http://127.0.0.1:$PORT/health"))
for k, v in h["providers"].items():
    print(f"  {k:9} {'OK  ' if v['ready'] else 'MISSING'} {v.get('id') or v.get('error')}")
print("  production_ready:", h["production_ready"])
PY

say "Money guard: auto-stop after $IDLE_MINUTES idle minutes"
cat > idle_guard.sh <<'GUARD'
#!/usr/bin/env bash
# Stops this pod when no production has been queued or running for IDLE_MINUTES, so a forgotten
# pod never keeps billing. Finished videos and models stay on the volume.
PORT="$1"; IDLE_MINUTES="$2"; TOKEN="$3"
last_busy=$(date +%s)
while sleep 60; do
  busy=$(curl -fs -H "Authorization: Bearer $TOKEN" "http://127.0.0.1:$PORT/v1/productions" |
         python3 -c "import json,sys; print(any(j['status'] in ('QUEUED','RUNNING') for j in json.load(sys.stdin)))" 2>/dev/null)
  [ "$busy" = "True" ] && last_busy=$(date +%s)
  # touching this file (any request from the app) also counts as activity
  [ -f "$HOME_DIR_ACTIVITY" ] && [ "$(stat -c %Y "$HOME_DIR_ACTIVITY")" -gt "$last_busy" ] && last_busy=$(stat -c %Y "$HOME_DIR_ACTIVITY")
  idle=$(( ( $(date +%s) - last_busy ) / 60 ))
  if [ "$idle" -ge "$IDLE_MINUTES" ]; then
    echo "$(date) idle ${idle} min - stopping pod"
    if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then runpodctl stop pod "$RUNPOD_POD_ID"; fi
    sleep 120
  fi
done
GUARD
chmod +x idle_guard.sh
pkill -f idle_guard.sh 2>/dev/null || true
if [ "$IDLE_MINUTES" != "0" ]; then
  if command -v runpodctl >/dev/null && [ -n "${RUNPOD_POD_ID:-}" ]; then
    HOME_DIR_ACTIVITY="$HOME_DIR/data/last_request" nohup ./idle_guard.sh "$PORT" "$IDLE_MINUTES" "$TOKEN" > idle_guard.log 2>&1 &
    GUARD_MSG="Auto-stop is ON: the pod stops itself after $IDLE_MINUTES minutes without video work."
  else
    GUARD_MSG="Auto-stop is NOT available here - remember to stop the machine yourself."
  fi
else
  GUARD_MSG="Auto-stop is OFF (CF_IDLE_MINUTES=0) - remember to stop the pod yourself."
fi

say "Opening a secure public link (no port settings needed)"
# A free Cloudflare quick tunnel gives an https:// address that reaches this worker from anywhere.
if [ ! -x "$HOME_DIR/cloudflared" ]; then
  curl -fsSL -o "$HOME_DIR/cloudflared" https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x "$HOME_DIR/cloudflared"
fi
pkill -f "cloudflared tunnel" 2>/dev/null || true
nohup "$HOME_DIR/cloudflared" tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" > tunnel.log 2>&1 &
URL=""
for _ in $(seq 1 45); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' tunnel.log | head -1 || true)
  [ -n "$URL" ] && break
  sleep 1
done
ALT=""
if [ -n "${RUNPOD_POD_ID:-}" ]; then ALT="https://${RUNPOD_POD_ID}-${PORT}.proxy.runpod.net (only if port $PORT is exposed)"; fi
if [ -z "$URL" ]; then
  echo "Could not open the Cloudflare link (see $HOME_DIR/tunnel.log)."
  URL="${ALT:-http://$(curl -fs https://api.ipify.org || hostname -I | awk '{print $1}'):$PORT}"
fi
cat <<DONE

================================================================
 CreatorForge worker is running.

 In the app -> Settings:
   Worker URL:   $URL
   Worker token: $TOKEN

 Tap SAVE, SAVE TOKEN, then TEST CONNECTION.
 (The link changes each time you run this command - paste the new one.)
${ALT:+ Alternative URL: $ALT}
 The first video loads models into memory and is slow (several
 minutes). Turn on "AI video clips" in Generate for realistic motion:
 each scene takes a few minutes to animate on a 24 GB GPU.

 Logs:   tail -f $HOME_DIR/worker.log
 Music:  put royalty-free tracks in $HOME_DIR/music (name them by mood)
 SFX:    put whoosh/impact/pop files in $HOME_DIR/sfx
 $GUARD_MSG
 Still: STOP THE POD when you're done - you pay while it runs.
================================================================
DONE
