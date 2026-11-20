# Brief: turning a bank film's approved script and key frames into the finished video

The owner said **go** on 2026-11-20: all bank films, free Kokoro voice. Work only inside your film's folder. Do not commit or push.
Do not generate images, audio or video with any AI service (no ElevenLabs). Do not change the approved wording of the script.

## The engine
`python3 creatorforge/channels/design_kits/film_video.py <film_dir> [--check | --probe | --voice-only | --shots A:B] [--workers N] [--port P]`
(run it from the repo root, `/home/user/Forgeos`). Read its docstring first. It reads `<film_dir>/video/shots.json` and makes
`<film_dir>/video/<slug>.mp4`: Kokoro voice per shot, the page's own animation timeline stepped at 12 fps, a CSS camera at 24 fps,
score by act, SFX from animation events, burned captions, −14 LUFS. Clips are cached per shot, so a re-run only re-renders shots
whose spec changed.

## Your job
1. **Read:** the film's `SCRIPT_TABLE.md` (approved), `PRESHOW.md`, `frames.py` and the other page builders (to learn each
   page's `data-anim="kind start end"` cues and where pieces sit), and look at the contact sheets in `sheets/`. Rebuild the pages
   if `html/` is stale (see `creatorforge/films/RESTORE.md` for the build order). Assets are already in `assets/`.
2. **Write `video/shots.json`:**
   - One shot per script row, in order, with `beat` 1–5. `vo` is the row's Voiceover exactly as approved, minus markup (⚠,
     backticks, bracket notes, *(silence)*). Use `"say"` for a spoken respelling where Kokoro would misread (currency, units,
     foreign names, years, "12–3"), and a film-level `"guide"` for names. Never change what the viewer hears in meaning.
   - `page`: the key frame that row's Canvas column describes. Consecutive rows on one page **continue its timeline**: give each
     row the `t` slice in which the pieces it talks about appear (`t` must not go backwards while you stay on a page).
   - `cam` `[z0,cx0,cy0,z1,cx1,cy1]`: follow the row's Camera column: push-ins, pull-outs, pans to the thing the line points at
     (centre = piece position / 1920, / 1080). Every shot needs a different set-up from the one before it. Smash-zoom = a new
     shot that starts already at 1.3–1.5×.
   - `[CUT]` in the script → `"cut": true`. `[HOLD 0.6s]` → `"post": 0.6`. Silent beats → `"vo": ""` with `"hold"` seconds.
   - If a row has no fitting page, reuse the nearest fitting page with a new camera, or add a simple page with the film's own
     helpers (same house style, numbers only from `dossier.json`, source line, no AI).
3. **Gate 4 (pacing) is enforced by the engine** and is never worked around: a still shot ≤ 4.5 s, a building shot ≤ 7 s, mean
   ≤ 5 s. When a line runs long, split the row into two shots at a clause boundary (two `vo` halves, two camera set-ups).
4. **Run in this order:** `--check`; `--probe` (copy its `"reload_pages"` list into shots.json); `--voice-only` (fix gate-4
   failures); `--shots 0:8` and look at frames you extract from `video/clips/*.mp4` with ffmpeg (Read tool) to confirm the
   camera lands where you meant; then the full render with `--workers 1` and your port.
5. **QC the finished film (zero-defect):** extract one frame every ~15 s into contact sheets and look at all of them; check
   that the camera never crops the piece being discussed, that the right page is up for each line, that captions are legible,
   that no page shows empty (timeline too early) or everything at once too soon. Listen-check by numbers: `ffprobe` duration,
   `ffmpeg -af ebur128` loudness (−14 LUFS ±0.7). Fix and re-render until clean.
6. **Write up:** add a dated "Video" section to `PRESHOW.md` (running time, voice, what the viewer sees act by act, every
   on-screen TO CHECK item still open, gate results). `SFX_LOG.md` is written by the engine. Delete `video/work/` when done; keep
   `video/clips/` and the MP4.

## House rules that still bind
Load the channel's house style skill (`.claude/skills/printfacts-style` or `dragonpsych-style`). Faceless, English, no mascot.
Numbers only from the dossier. AI plates only those already in the frames. Real people only in credited photos, nothing drawn on
faces. If something blocks you, say so in your final report rather than working around a gate.

## Final report (under 250 words)
The MP4's path, running time and file size; shots count and mean hold; anything that looks weak and why; open TO CHECK items.
