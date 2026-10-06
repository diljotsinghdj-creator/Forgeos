# CreatorForge Worker

The self-hosted half of CreatorForge. It runs every heavy step on hardware you control.
Your phone sends one request and gets back a finished, checked MP4. No step requires a
subscription or credit-based service.

```
idea → AI Director (script, hook, shot list, CTA) → PromptForge → scene images
     → [optional storyboard review: edit any scene, then approve] → narration
     → [optional AI video clips: image-to-video per scene] → captions (Whisper)
     → music (your library) → assembly (motion, transitions, overlays)
     → render (H.264/AAC MP4) → verify (codecs, resolution, duration, full decode)
```

Each stage saves its output. A crash, cancel or failure resumes from the first unfinished
stage. Finished images and narration are cached by content, so they are never paid for twice.

## Try it in 2 minutes (demo mode, no AI models)

You need Python 3.10+ and FFmpeg on a computer that's on the same Wi-Fi as your phone.

```bash
pip install -e .
python run_demo.py
```

In the app, open **Settings**, set **Worker URL** to the address it prints
(`http://192.168.x.x:8765`), and tap **Test connection**. Then go to **Generate** and tap
**Generate video**. Demo mode uses placeholder AI: coloured images, a tone instead of a voice,
and a canned script. Everything else is real: the stage tracking, storyboard, review/edit,
editing, captions, render, verification, download and library. If the phone can't connect,
allow port 8765 through the computer's firewall.

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
| `CF_VIDEO_PROVIDER`, `CF_VIDEO_MODEL`, `CF_VIDEO_URL` | Optional AI video clips. `diffusers` runs image-to-video on the worker's own CUDA GPU (default model `Lightricks/LTX-Video`; Wan 2.x I2V models also work). `http` calls your own server at `POST {url}/v1/video/i2v` with JSON `image_base64, prompt, seconds, width, height, seed` and expects MP4 bytes back. Productions ask for clips with `"motion": "ai_video"` |
| `CF_PIPER_MODEL` / `CF_KOKORO_VOICE` | Sets up one default narrator |
| `CF_VOICES` | Voice profiles as JSON: `[{"id":"deep","name":"Deep male","provider":"piper","voice":"/models/x.onnx","speed":0.95}, {"id":"warm","name":"Warm female","provider":"kokoro","voice":"af_heart"}]` |
| `CF_ASR_PROVIDER=whisper`, `CF_WHISPER_MODEL`, `CF_WHISPER_DEVICE` | Whisper caption timing. When unset, captions are timed from the script and the measured narration length, and the production records `captions: estimated` |
| `CF_MUSIC_DIR` | Folder of music tracks. A track is picked when its filename matches the scene's mood (for example `epic_cinematic_1.mp3`) |
| `CF_MUSIC_PROVIDER`, `CF_MUSIC_MODEL`, `CF_MUSIC_URL` | Optional AI-generated score instead of the library. `stable-audio` runs Stable Audio Open on the worker GPU and makes a bed of up to 47s, which loops under longer videos. `http` calls your own server at `POST {url}/v1/music/generate` with JSON `prompt, seconds, seed` and expects audio bytes back. Check the model licence |
| `CF_SFX_DIR` | Optional sound-effects folder. Files are matched to roles by name: `whoosh`/`swoosh` (moving transitions), `hit`/`impact`/`boom` (hard cuts, the hook), `pop`/`click`/`ding` (callouts, CTA). Sound-effect assets you upload are used as well |
| `CF_ALLOW_MOCK=1` | **Tests only.** Turns on placeholder providers (`mock`). Every production records the providers that made it |

Check the licence of each model you install: some popular voice and music models are not
licensed for commercial use.

## API

| Method | Path | |
|---|---|---|
| GET | `/health` | Readiness, plus the status of each provider |
| GET | `/v1/capabilities` | Templates, aspect ratios, pacing options, voice profiles |
| POST | `/v1/productions` | **One-button production.** Body: `{"idea", "duration_s", "template", "aspect", "voice", "pacing", "style", "mood", "camera", "characters":[{"name","description"}], "music", "captions", "motion": "stills"\|"ai_video", "review": bool, "auto_edit": bool, "character_ids": [..], "script": "exact narration", "music_asset_id": "...", "sfx": bool}`. With `script`, the narration is used word for word (split into scenes on sentence boundaries) and the Director plans only visuals and the edit; script mode also works with no LLM configured. Returns `202` with the production |
| GET | `/v1/productions` / `/{id}` | Status, stages, per-scene states, progress, errors, providers used |
| DELETE | `/v1/productions/{id}` | Cancel. Finished assets are kept |
| POST | `/v1/productions/{id}/retry[?from_stage=images]` | Resume from the failed stage, or redo from a chosen stage |
| POST | `/v1/productions/{id}/scenes/{n}/regenerate` | Generate a new visual for one scene and re-render. Nothing else is regenerated |
| PATCH | `/v1/productions/{id}/scenes/{n}` | Edit a scene's `narration` and/or `visual`. Only the assets that depend on the change are regenerated. Moves the production to `REVIEW` |
| POST | `/v1/productions/{id}/approve` | Approve the storyboard (or your edits) and render |
| GET | `/v1/productions/{id}/video` | The verified MP4. Only available once the production is `READY` |
| GET | `/v1/productions/{id}/scenes/{n}/image` | Storyboard image for scene `n` |
| GET/POST | `/v1/library/characters` | Character Library. Saved characters are injected into the prompt of every scene that mentions them by name. Productions reference them with `character_ids`, and each production keeps a snapshot of the character as it was at submit time |
| PUT/DELETE | `/v1/library/characters/{id}` | Edit or remove a saved character |
| GET/POST | `/v1/library/voices` | Voice Profiles. Built-in voices come from `CF_VOICES`; voices saved from the app are added with `{"name","provider":"piper"\|"kokoro","voice","speed"}` |
| PUT/DELETE | `/v1/library/voices/{id}` | Edit or remove a saved voice (built-in voices are read-only) |
| POST | `/v1/library/voices/{id}/preview` | Speak a short sample (WAV) |
| GET | `/v1/library/assets[?kind=&generated=true]` | Asset Library. Uploads, plus every generated scene image, clip and narration |
| POST | `/v1/library/assets?kind=image\|video\|audio\|music\|sfx&name=` | Upload with the raw file as the body (300 MB max). Files are checked to be what they claim to be |
| PATCH/DELETE | `/v1/library/assets/{id}` | Rename or delete an asset |
| PATCH | `/v1/productions/{id}/scenes/{n}` with `{"asset_id"}` | Put an image, clip or voice-over into one scene |
| PATCH | `/v1/productions/{id}/timeline` | Timeline editor. `{"hook","cta","scenes":[{"index","duration_s","transition","overlay"}]}`: list the scenes in their new order (leave one out to remove it). A length can't be shorter than its narration. Moves the production to `REVIEW` |
| PATCH | `/v1/productions/{id}` | Rename `{"title"}` |
| DELETE | `/v1/productions/{id}?purge=true` | Delete a finished production and its files |
| GET | `/v1/library/videos` | Media Library: every finished, verified video with its thumbnail URL |
| POST | `/v1/images/generate`, `/v1/voice/generate` | Single-asset endpoints used by the RC10 app |

**Auto Edit** (`auto_edit`, on by default): the AI Director picks the transition into each scene
(`cut, fade, dissolve, dip, flash, slide, wipe, whip, zoom, reveal`), the key words that are
highlighted in the captions, and short dramatic pauses. Each production records the edit
decisions it used in `edit`. With Auto Edit off, the template's transition rhythm is used.

Templates: `shorts_cinematic`, `reels_punchy`, `square_social`, `explainer`, `youtube_longform`.

## Tests

```bash
pip install -e ".[test]" && pytest
```

The end-to-end tests use the placeholder providers. They render real MP4s with FFmpeg and run
the same verification used in production.
