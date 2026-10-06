# Run the CreatorForge worker on a rented GPU (from your phone)

You rent a GPU machine by the hour, start it, paste one command, and copy two values into the
app. There's no subscription, and you pay only while the machine is running.

## 1. Create the machine (RunPod example, works in a phone browser)

1. Sign up at runpod.io and add a little credit.
2. **Pods → Deploy**. Pick a **24 GB GPU**: RTX 4090, L4, RTX A5000 or RTX 3090.
3. Template: **RunPod PyTorch** (any 2.x).
4. Press **Edit Template**:
   - **Volume disk: 100 GB** (models are stored here and survive restarts)
   - **Expose HTTP ports: `8765`**
5. **Deploy**, wait until it says *Running*, then **Connect → Start Web Terminal → Connect to Web Terminal**.

## 2. Paste this one command

```bash
curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/worker/cloud/setup_gpu.sh | bash
```

The first run downloads about 35 GB of open models and takes 10–20 minutes:

| Job | Model |
|---|---|
| Script writing | Qwen 2.5 7B, via Ollama |
| Images | FLUX.1-schnell (Apache-2.0) |
| Voices | Kokoro: warm US female, deep US male, British female, British male |
| Captions | Whisper |

When it finishes it prints:

```
Worker URL:   https://<pod-id>-8765.proxy.runpod.net
Worker token: <random token>
```

## 3. Connect the app

**Settings** → paste the **Worker URL** → **SAVE** → paste the **Worker token** → **SAVE TOKEN** →
**TEST CONNECTION**. It should say **ONLINE**. Then go to **Generate**.

The first video is slow because the models load into GPU memory. Later videos are much faster.

## Every time after that

- **Start** the pod in RunPod, open the web terminal, and paste the same command. It takes about a
  minute because everything is already downloaded.
- **Stop** the pod when you're done. Stopped pods only cost a small amount for the stored disk.

## Options (put them before `bash` in the command, e.g. `... | CF_ENABLE_VIDEO=1 bash`)

| Variable | Effect |
|---|---|
| `CF_ENABLE_VIDEO=1` | Also downloads LTX-Video, so **AI video clips** can be used. Pick a 48 GB GPU (A6000 / L40S) for this |
| `CF_LLM_MODEL=qwen2.5:14b-instruct` | A stronger script writer (needs more VRAM) |
| `CF_IMAGE_MODEL=...` | A different diffusers image model. Check its licence |

Music and sound effects: upload them from the app (**Library → Asset Library**), or copy files
into `/workspace/creatorforge/music` and `/workspace/creatorforge/sfx`.

## If something goes wrong

- `tail -n 50 /workspace/creatorforge/worker.log` shows the worker's errors.
- **TEST CONNECTION says OFFLINE:** check that port 8765 is exposed as an HTTP port on the pod
  and that the pod is running.
- **The model download asks for a login:** create a free Hugging Face token, then run
  `export HF_TOKEN=...` before the command.
