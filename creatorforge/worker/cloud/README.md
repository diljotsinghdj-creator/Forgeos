# Run the CreatorForge worker on a rented GPU (from your phone)

You rent a GPU machine by the hour, start it, paste one command, and copy two values into the
app. There's no subscription, and you pay only while the machine is running.

## 1. Create the machine (RunPod example, works in a phone browser)

1. Sign up at runpod.io and add a little credit.
2. **Pods → Deploy**. Pick a **24 GB GPU**: RTX 4090, L4, RTX A5000 or RTX 3090.
3. Template: **RunPod PyTorch** (any 2.x).
4. Make sure the pod has **at least 100 GB of disk** (Volume or Container disk; it's usually
   under **Edit**, **Customize** or **Edit Template**). The setup checks this and tells you if
   there isn't enough. You **don't** need to expose any ports: the setup opens a free secure
   `https://…trycloudflare.com` link on its own.
5. **Deploy**, wait until it says *Running*, then **Connect → Start Web Terminal → Connect to Web Terminal**.

## 2. Paste this one command

```bash
curl -fsSL https://raw.githubusercontent.com/diljotsinghdj-creator/Forgeos/claude/forgeos-visibility-47vgwp/creatorforge/worker/cloud/start.sh | bash
```

The setup runs in the background on the pod, so closing the tab or losing signal doesn't stop
it. To watch progress again later: `tail -f /workspace/creatorforge/setup.log`. When it's done,
`cat /workspace/creatorforge/connection.txt` shows the URL and token.

The first run downloads about 60 GB of open models and takes 15–30 minutes:

| Job | Model |
|---|---|
| Script writing | Qwen 2.5 7B, via Ollama |
| Images | FLUX.1-schnell (Apache-2.0) |
| Realistic AI video | **Wan 2.2** TI2V-5B (Apache-2.0, 720p) |
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

For realistic moving shots, turn on **AI video clips** in Generate and pick a look under
**Director Mode → Style** (Hyper-realistic, Cinematic, 3D animated, Anime and so on). Animating
takes a few minutes per scene on a 24 GB GPU, so a 45-second video can take 20–40 minutes. Start
with 15–30 seconds.

## Every time after that

- **Start** the pod in RunPod, open the web terminal, and paste the same command. It takes about a
  minute because everything is already downloaded.
- **Stop** the pod when you're done. Stopped pods only cost a small amount for the stored disk.

## Options (put them before `bash` in the command, e.g. `... | CF_ENABLE_VIDEO=1 bash`)

| Variable | Effect |
|---|---|
| `CF_VIDEO=max` | Uses **Wan 2.2 I2V-A14B**, the most realistic motion. Needs an **80 GB GPU** (A100 / H100) and a 200 GB volume |
| `CF_VIDEO=off` | Skips the video model (stills with camera motion only) |
| `CF_LLM_MODEL=qwen2.5:14b-instruct` | A stronger script writer (needs more VRAM) |
| `CF_IMAGE_MODEL=...` | A different diffusers image model. Check its licence |

Music and sound effects: upload them from the app (**Library → Asset Library**), or copy files
into `/workspace/creatorforge/music` and `/workspace/creatorforge/sfx`.

## If something goes wrong

- `tail -n 50 /workspace/creatorforge/worker.log` shows the worker's errors.
- **TEST CONNECTION says OFFLINE:** check the pod is running, then run the command again and paste the
  new link it prints (the trycloudflare link changes on every run).
- **The model download asks for a login:** create a free Hugging Face token, then run
  `export HF_TOKEN=...` before the command.
