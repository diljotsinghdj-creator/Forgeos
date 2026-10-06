# CreatorForge Worker

The self-hosted half of CreatorForge. It runs every heavy step on hardware you control.
Your phone sends one request and gets back a finished, checked MP4. No step requires a
subscription or credit-based service.

```
idea → AI Director (script, hook, shot list, CTA) → PromptForge → scene images → narration
     → captions (Whisper) → music (your library) → assembly (motion, transitions, overlays)
     → render (H.264/AAC MP4) → verify (codecs, resolution, duration, full decode)
```

Each stage saves its output. A crash, cancel or failure resumes from the first unfinished
stage. Finished images and narration are cached by content, so they are never paid for twice.

## Run

```bash
pip install -e ".[whisper]" piper-tts       # or: docker build -t creatorforge-worker .
export CF_WORKER_TOKEN=change-me            # phone sends: Authorization: Bearer change-me
export CF_LLM_URL=http://localhost:11434/v1 CF_LLM_MODEL=qwen2.5:14b   # Ollama
export CF_IMAGE_PROVIDER=a1111 CF_IMAGE_URL=http://localhost:7860      # Forge / A1111 / SD.Next
export CF_PIPER_MODEL=/models/en_US-ryan-high.onnx
export CF_ASR_PROVIDER=whisper
export CF_MUSIC_DIR=/music                  # optional royalty-free tracks; name them by mood
creatorforge-worker                          # listens on :8765
```

Open `GET /health` and check that `production_ready` is `true`. It lists any backend that is
missing.

## Configuration

| Variable | Purpose |
|---|---|
| `CF_DATA_DIR` | Where productions and the asset cache are stored (default `./creatorforge-data`) |
| `CF_WORKER_TOKEN` | When set, every request except `/health` must send this bearer token |
| `CF_LLM_URL`, `CF_LLM_MODEL`, `CF_LLM_API_KEY` | Any OpenAI-compatible chat endpoint: Ollama, llama.cpp, vLLM, LM Studio, or a hosted API if you choose |
| `CF_IMAGE_PROVIDER` | `a1111` (HTTP to SD WebUI / Forge) or `diffusers` (in-process, needs a GPU) |
| `CF_IMAGE_URL`, `CF_IMAGE_MODEL`, `CF_IMAGE_STEPS` | Provider settings. The `diffusers` default is `black-forest-labs/FLUX.1-schnell` |
| `CF_PIPER_MODEL` / `CF_KOKORO_VOICE` | Sets up one default narrator |
| `CF_VOICES` | Voice profiles as JSON: `[{"id":"deep","name":"Deep male","provider":"piper","voice":"/models/x.onnx","speed":0.95}, {"id":"warm","name":"Warm female","provider":"kokoro","voice":"af_heart"}]` |
| `CF_ASR_PROVIDER=whisper`, `CF_WHISPER_MODEL`, `CF_WHISPER_DEVICE` | Whisper caption timing. When unset, captions are timed from the script and the measured narration length, and the production records `captions: estimated` |
| `CF_MUSIC_DIR` | Folder of music tracks. A track is picked when its filename matches the scene's mood (for example `epic_cinematic_1.mp3`) |
| `CF_ALLOW_MOCK=1` | **Tests only.** Turns on placeholder providers (`mock`). Every production records the providers that made it |

Check the licence of each model you install: some popular voice and music models are not
licensed for commercial use.

## API

| Method | Path | |
|---|---|---|
| GET | `/health` | Readiness, plus the status of each provider |
| GET | `/v1/capabilities` | Templates, aspect ratios, pacing options, voice profiles |
| POST | `/v1/productions` | **One-button production.** Body: `{"idea", "duration_s", "template", "aspect", "voice", "pacing", "style", "mood", "camera", "characters":[{"name","description"}], "music", "captions"}`. Returns `202` with the production |
| GET | `/v1/productions` / `/{id}` | Status, stages, per-scene states, progress, errors, providers used |
| DELETE | `/v1/productions/{id}` | Cancel. Finished assets are kept |
| POST | `/v1/productions/{id}/retry[?from_stage=images]` | Resume from the failed stage, or redo from a chosen stage |
| POST | `/v1/productions/{id}/scenes/{n}/regenerate` | Generate a new visual for one scene and re-render. Nothing else is regenerated |
| GET | `/v1/productions/{id}/video` | The verified MP4. Only available once the production is `READY` |
| GET | `/v1/productions/{id}/scenes/{n}/image` | Storyboard image for scene `n` |
| POST | `/v1/images/generate`, `/v1/voice/generate` | Single-asset endpoints used by the RC10 app |

Templates: `shorts_cinematic`, `reels_punchy`, `square_social`, `explainer`, `youtube_longform`.

## Tests

```bash
pip install -e ".[test]" && pytest
```

The end-to-end tests use the placeholder providers. They render real MP4s with FFmpeg and run
the same verification used in production.
