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
# Models already downloaded by an earlier run mean a re-run only needs room for updates. (Checked by
# folder, not by adding up file sizes - that takes minutes on RunPod's network disks.)
HAVE="no"
if [ -d "$HOME_DIR/hf/hub" ] && [ -d "$HOME_DIR/venv" ]; then HAVE="yes"; NEED_GB=10; fi
echo "  free: ${FREE_GB} GB, models already downloaded: ${HAVE}, needed: ~${NEED_GB} GB (in $HOME_DIR)"
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
  # The pod's copy is never edited by hand, so throw away anything installing changed (e.g. build metadata).
  git -C Forgeos fetch -q --depth 1 origin "$BRANCH" && git -C Forgeos checkout -q -f -B "$BRANCH" FETCH_HEAD \
    && git -C Forgeos reset -q --hard FETCH_HEAD && git -C Forgeos clean -q -fd creatorforge/worker
else
  git clone -q --depth 1 -b "$BRANCH" https://github.com/diljotsinghdj-creator/Forgeos.git
fi

say "Installing the worker (Python packages; first run takes a few minutes)"
[ -d venv ] || python3 -m venv --system-site-packages venv   # reuse the image's CUDA PyTorch when present
# shellcheck disable=SC1091
. venv/bin/activate
pip install -q --upgrade pip
pip install -q -e "Forgeos/creatorforge/worker[whisper,kokoro,diffusers]" huggingface_hub hf_transfer qrcode
PYBIN="$(command -v python)"
"$PYBIN" -c "import creatorforge_worker, torch; assert torch.cuda.is_available(), 'PyTorch cannot see the GPU'; print('PyTorch', torch.__version__, 'CUDA OK')"
python -m spacy download en_core_web_sm -q >/dev/null 2>&1 || true   # used by Kokoro's English text front-end

export HF_HOME="$HOME_DIR/hf" HF_HUB_ENABLE_HF_TRANSFER=1   # hf_transfer: parallel, many times faster downloads

# The script model downloads at the same time as the image model (separate log), to cut start-up time.
say "Installing Ollama and the script model $LLM_MODEL (in parallel - log: $HOME_DIR/ollama_setup.log)"
export OLLAMA_MODELS="$HOME_DIR/ollama" OLLAMA_KEEP_ALIVE=2m   # free VRAM soon after the script is written
(
  set -e
  command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh
  if ! curl -fs http://127.0.0.1:11434/api/tags >/dev/null; then
    nohup ollama serve > "$HOME_DIR/ollama.log" 2>&1 &
    for _ in $(seq 1 30); do curl -fs http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 1; done
  fi
  ollama pull "$LLM_MODEL"
) > ollama_setup.log 2>&1 &
OLLAMA_JOB=$!

say "Downloading image model $IMAGE_MODEL (first time ~10-25 GB; reused afterwards)"
# FLUX now needs a (free) Hugging Face login; without HF_TOKEN we fall back to SDXL, which needs none.
python - "$IMAGE_MODEL" "$HOME_DIR/image_model.txt" <<'PY'
import sys
from huggingface_hub import snapshot_download
SKIP = ["flux1-*.safetensors", "ae.safetensors", "sd_xl_*.safetensors", "*.bin", "*.onnx", "*.onnx_data",
        "*.msgpack", "*openvino*", "*.md", "*.png", "*.jpg"]
FALLBACK = "stabilityai/stable-diffusion-xl-base-1.0"
model, out = sys.argv[1], sys.argv[2]
try:
    snapshot_download(model, ignore_patterns=SKIP)
except Exception as e:  # gated repo / missing token
    if model == FALLBACK:
        raise
    print(f"  {model} needs a Hugging Face login ({type(e).__name__}); using {FALLBACK} instead.")
    print("  (For FLUX later: accept its licence on huggingface.co, then run with HF_TOKEN=... set.)")
    model = FALLBACK
    snapshot_download(model, ignore_patterns=SKIP)
open(out, "w").write(model)
PY
IMAGE_MODEL="$(cat "$HOME_DIR/image_model.txt")"
echo "  image model: $IMAGE_MODEL"

say "Waiting for the script model"
if ! wait "$OLLAMA_JOB"; then echo "Ollama setup failed - last lines of ollama_setup.log:"; tail -n 30 ollama_setup.log; exit 1; fi
tail -n 2 ollama_setup.log

say "Configuring the worker"
# A token set as a pod environment variable survives restarts even without a volume disk, so the app stays connected.
if [ -n "${CF_WORKER_TOKEN:-}" ]; then printf '%s\n' "$CF_WORKER_TOKEN" > token; fi
[ -s token ] || python -c "import secrets; print(secrets.token_urlsafe(24))" > token
TOKEN="$(cat token)"
cat > worker.env <<ENV
CF_DATA_DIR=$HOME_DIR/data
CF_PORT=$PORT
CF_WORKER_TOKEN=$TOKEN
HF_HOME=$HOME_DIR/hf
HF_HUB_ENABLE_HF_TRANSFER=1
CF_VIDEO_QUALITY=${CF_VIDEO_QUALITY:-fast}
CF_LLM_URL=http://127.0.0.1:11434/v1
CF_LLM_MODEL=$LLM_MODEL
CF_IMAGE_PROVIDER=diffusers
CF_IMAGE_MODEL=$IMAGE_MODEL
CF_VOICES='[{"id":"warm","name":"Warm (US female)","provider":"kokoro","voice":"af_heart","lang":"a"},{"id":"deep_doc","name":"Deep documentary narrator ★ human-like","provider":"chatterbox","voice":"kokoro:am_onyx","style":"documentary"},{"id":"storyteller_uk","name":"British storyteller ★ human-like","provider":"chatterbox","voice":"kokoro:bm_george","style":"documentary"},{"id":"warm_human","name":"Warm female ★ human-like","provider":"chatterbox","voice":"kokoro:af_heart","style":"natural"},{"id":"calm_human","name":"Calm female ★ human-like","provider":"chatterbox","voice":"kokoro:af_bella","style":"calm"},{"id":"host_human","name":"Energetic host ★ human-like","provider":"chatterbox","voice":"kokoro:am_puck","style":"energetic"},{"id":"natural_human","name":"Natural ★ human-like","provider":"chatterbox","voice":"default","style":"natural"},{"id":"deep","name":"Deep (US male)","provider":"kokoro","voice":"am_michael","lang":"a"},{"id":"onyx","name":"Low & deep (US male)","provider":"kokoro","voice":"am_onyx","lang":"a"},{"id":"fenrir","name":"Bold (US male)","provider":"kokoro","voice":"am_fenrir","lang":"a"},{"id":"puck","name":"Upbeat (US male)","provider":"kokoro","voice":"am_puck","lang":"a"},{"id":"bella","name":"Bright (US female)","provider":"kokoro","voice":"af_bella","lang":"a"},{"id":"nicole","name":"Soft whisper (US female)","provider":"kokoro","voice":"af_nicole","lang":"a"},{"id":"sarah","name":"Clear (US female)","provider":"kokoro","voice":"af_sarah","lang":"a"},{"id":"british_f","name":"British female","provider":"kokoro","voice":"bf_emma","lang":"b"},{"id":"british_isabella","name":"Elegant (British female)","provider":"kokoro","voice":"bf_isabella","lang":"b"},{"id":"british_m","name":"British male","provider":"kokoro","voice":"bm_george","lang":"b"},{"id":"fable","name":"Storyteller (British male)","provider":"kokoro","voice":"bm_fable","lang":"b"},{"id":"es_f","name":"Spanish (female)","provider":"kokoro","voice":"ef_dora","lang":"e"},{"id":"fr_f","name":"French (female)","provider":"kokoro","voice":"ff_siwis","lang":"f"},{"id":"hi_f","name":"Hindi (female)","provider":"kokoro","voice":"hf_alpha","lang":"h"},{"id":"it_f","name":"Italian (female)","provider":"kokoro","voice":"if_sara","lang":"i"},{"id":"pt_f","name":"Portuguese BR (female)","provider":"kokoro","voice":"pf_dora","lang":"p"}]'
CF_ASR_PROVIDER=whisper
CF_WHISPER_MODEL=small
CF_WHISPER_DEVICE=cuda
CF_MUSIC_DIR=$HOME_DIR/music
CF_SFX_DIR=$HOME_DIR/sfx
ENV
if [ -n "$VIDEO_MODEL" ]; then printf 'CF_VIDEO_PROVIDER=diffusers\nCF_VIDEO_MODEL=%s\n' "$VIDEO_MODEL" >> worker.env; fi
if [ -n "${CF_YOUTUBE_API_KEY:-}" ]; then printf 'CF_YOUTUBE_API_KEY=%s\n' "$CF_YOUTUBE_API_KEY" >> worker.env; fi

say "Starting the worker on port $PORT"
pkill -f "creatorforge_worker" 2>/dev/null || true
pkill -f "bin/creatorforge-worker" 2>/dev/null || true
# Wait for the old worker to let go of the port, otherwise its last /health answer fools the check below.
for _ in $(seq 1 30); do curl -fs "http://127.0.0.1:$PORT/health" >/dev/null || break; sleep 1; done
pkill -9 -f "creatorforge_worker" 2>/dev/null || true
nohup bash -c "set -a; . '$HOME_DIR/worker.env'; set +a; exec '$PYBIN' -m creatorforge_worker" > worker.log 2>&1 &
for _ in $(seq 1 60); do curl -fs "http://127.0.0.1:$PORT/health" >/dev/null && break; sleep 1; done
curl -fs "http://127.0.0.1:$PORT/health" >/dev/null || { echo "Worker did not start - last lines of $HOME_DIR/worker.log:"; tail -n 40 worker.log; exit 1; }
python - <<PY || echo "  (couldn't read provider status - check $HOME_DIR/worker.log)"
import json, time, urllib.request
for attempt in range(30):
    try:
        h = json.load(urllib.request.urlopen("http://127.0.0.1:$PORT/health")); break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("worker not answering on port $PORT")
for k, v in h["providers"].items():
    print(f"  {k:9} {'OK  ' if v['ready'] else 'MISSING'} {v.get('id') or v.get('error')}")
print("  production_ready:", h["production_ready"])
PY

say "Human-like narrator (Chatterbox) installs in the background (log: $HOME_DIR/chatterbox.log)"
# Chatterbox pins its own torch/diffusers versions, so it lives in a separate Python 3.11 environment and
# runs as a small local server. Until it's up, "human-like" voices fall back to their Kokoro voice.
pkill -f "chatterbox_server.py" 2>/dev/null || true
nohup bash -c "
  set -e
  pip install -q uv
  [ -x '$HOME_DIR/chatterbox_venv/bin/python' ] || uv venv -q --python 3.11 '$HOME_DIR/chatterbox_venv'
  uv pip install -q --python '$HOME_DIR/chatterbox_venv/bin/python' chatterbox-tts 'setuptools<81'
  echo 'Chatterbox installed - starting the narration server'
  export HF_HOME='$HOME_DIR/hf'
  exec '$HOME_DIR/chatterbox_venv/bin/python' '$HOME_DIR/Forgeos/creatorforge/worker/creatorforge_worker/chatterbox_server.py' 8770
" > chatterbox.log 2>&1 &

if [ -n "$VIDEO_MODEL" ]; then
  # Videos with AI images work right away; the big AI-video model finishes downloading in the background
  # (the worker would also fetch it on first use, this just gets it ready sooner).
  say "AI video model $VIDEO_MODEL is downloading in the background (log: $HOME_DIR/video_download.log)"
  pkill -f "snapshot_download('$VIDEO_MODEL'" 2>/dev/null || true
  nohup "$PYBIN" -c "from huggingface_hub import snapshot_download; snapshot_download('$VIDEO_MODEL', ignore_patterns=['*.md', 'assets/*', 'examples/*']); print('AI video model ready')" > video_download.log 2>&1 &
fi

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
# RunPod gives every pod a permanent address for exposed ports. When port $PORT is exposed it never changes,
# so the app only needs to be set up once. The Cloudflare link above changes on every start.
FIXED=""
if [ -n "${RUNPOD_POD_ID:-}" ]; then
  PROXY="https://${RUNPOD_POD_ID}-${PORT}.proxy.runpod.net"
  if curl -fs -m 15 "$PROXY/health" >/dev/null 2>&1; then FIXED="$PROXY"; fi
fi
if [ -z "$URL" ] && [ -z "$FIXED" ]; then
  echo "Could not open the Cloudflare link (see $HOME_DIR/tunnel.log)."
  URL="http://$(curl -fs https://api.ipify.org || hostname -I | awk '{print $1}'):$PORT"
fi
MAIN="${FIXED:-$URL}"
if [ -n "$FIXED" ]; then
  LINK_NOTE="This address is PERMANENT for this pod - set it up once, it keeps working after restarts."
elif [ -n "${RUNPOD_POD_ID:-}" ]; then
  LINK_NOTE="This link changes every start. For a permanent one: RunPod -> your pod -> Edit -> Expose HTTP Ports -> add $PORT, save, run this command again."
else
  LINK_NOTE="This link changes every start - scan the new QR code each time."
fi
CONNECT=$("$PYBIN" -c "import sys, urllib.parse as u; print('creatorforge://connect?url=' + u.quote(sys.argv[1], safe='') + '&token=' + u.quote(sys.argv[2], safe=''))" "$MAIN" "$TOKEN")
echo "$CONNECT" > "$HOME_DIR/connect_link.txt"
cat <<DONE | tee "$HOME_DIR/connection.txt"

================================================================
 CreatorForge worker is running.

 EASIEST: in the app -> Settings -> Video worker -> SCAN QR,
 and scan the code below. Or type these in:
   Worker URL:   $MAIN
   Worker token: $TOKEN

 $LINK_NOTE
 The first video loads models into memory and is slow (several minutes).

 Logs:   tail -f $HOME_DIR/worker.log
 Music:  put royalty-free tracks in $HOME_DIR/music (name them by mood)
 SFX:    put whoosh/impact/pop files in $HOME_DIR/sfx
 $GUARD_MSG
 Still: STOP THE POD when you're done - you pay while it runs.
================================================================
DONE
"$PYBIN" - "$CONNECT" <<'QR' || echo "(QR code unavailable - type the URL and token instead)"
import sys
import qrcode
q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_L)
q.add_data(sys.argv[1])
q.make(fit=True)
q.print_ascii(invert=True)
QR
