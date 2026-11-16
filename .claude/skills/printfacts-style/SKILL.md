---
name: printfacts-style
description: The house style every visual, 3D scene, edit, caption and export in this repo must follow - Vox x Johnny Harris for Print Facts and Dragon Psychology. Load it before using any other skill that makes or changes a picture, a 3D scene, a chart, a map, a caption, an edit or an export (threejs-*, ffmpeg-skill, vox-method, collage-explainer, dataviz), and whenever someone asks for "Vox style", "Johnny Harris style", "our style" or "on brand". It overrides those skills' own defaults where they differ.
---

# Print Facts house style (Vox x Johnny Harris)

Every other skill is a tool. This file decides how the result looks and sounds. When a tool skill's default
differs from this file, this file wins. The owner's hard rules (CLAUDE.md, MASTER_DIRECTIVES) still win over both.

## The seven-point test (every frame)
1. **One sourced idea:** one claim per frame, and it's in the dossier.
2. **Real evidence:** a document, photo, map, satellite image or footage. Not a stock mood shot alone.
3. **A map, document or chart** carries the idea.
4. **The investigator's hand-made layer:** marker circle, arrow, highlighter, sticky note, tape, pins and red string.
5. **Camera feel:** a slow push or drift, never a dead still longer than 4.5 s.
6. **A source line** on screen (bottom, small mono caps).
7. **Restraint:** one accent colour plus signature yellow, and nothing decorative that says nothing.

## Fixed brand layer
- **Signature yellow #FFDD33:** on the key number, the highlighter, and the current caption word, in every film.
- **Accent:** one per film, chosen in its Visual DNA. It changes every film.
- **Logo D** ("PRINT [FACTS]" + tick, FACTS on a yellow highlighter swipe) top-right, small. A corner mark, never an intro.
- **Type:**
  - Anton for headlines;
  - IBM Plex Mono for labels and sources;
  - Instrument Serif italic for quotes;
  - Caveat for handwriting.

  All of them live in `creatorforge/worker/creatorforge_worker/media/vendor/fonts`.
- **Texture:**
  - paper grain (feTurbulence, about 0.26 opacity, multiply);
  - a soft vignette;
  - halftone dots on collage photos.
- **Motion:**
  - camera at 24/30 fps;
  - reveals, pops, counters and icon grids stepped at 12 fps;
  - lines and strings draw on (stroke-dashoffset).
- **Captions:**
  - word timings from `media/wordtimes.py`;
  - 4-word groups on a dark rounded box;
  - Anton, white, current word #FFDD33.
- **Pacing:** still shots at most 4.5 s, building shots at most 7 s, mean at most 5 s (gate 4).

## Johnny Harris layer
- **Narrator:** speaks as "I", an investigator (faceless; no presenter on camera).
- **The map table:** an old chart or real map on a desk, with pins, red string and handwritten price or date tags. It returns through the film.
- **Discovery beats:** "And then I found this." The evidence appears as it's found.
- **A personal way in** at the start, paid off at the end.

## How each tool skill is used here
| Skill | Use it for | House overrides |
|---|---|---|
| `threejs-*` (r186, `vendor/three186`) | relief maps, globes, routes, cutaways, physics, glow bars | Bloom only on the one lit thing (strength at most 0.6). Paper-grain and vignette HTML overlay on top. Labels are HTML cards in house type, not 3D text. Accent + yellow only. Heights exaggeration stated in the source line. Camera moves slow; no spinning showcase. |
| `ffmpeg-skill` | cuts, 9:16 refits, silence trim, loudness, final checks | Loudness −14 LUFS integrated, true peak −1 dBTP. Captions burned with our spec (`printfacts-style/captions.py`: exact word timing, house look, then −14 LUFS), never the tool's default yellow box or emoji. Shorts: 1080×1920, words inside the safe band (y 220–1560). |
| `wordtimes.py` (faster-whisper) | caption timing | Pass the script line as `prompt` so names and numbers match the script. |
| `vox-method` | the production blueprint | Use as written; its Visual DNA must name the accent colour and the map-table or evidence device. |
| `collage-explainer` | collage look | **AI image and video models only with the owner's explicit permission for that film.** Default to real photos (Pixabay, archives) with BiRefNet cut-outs, halftone, white sticker edge, torn paper, colour disc. |
| `dataviz` | charts | Bars from zero, the one key value in yellow, the rest neutral grey. Source line always. Illustrative data labelled. |

## Never
- Copy Vox's or Johnny Harris's logos, intros, music, graphics or footage.
- Draw on faces, or show AI faces of real people.
- Show numbers that aren't in the dossier.
- Draw India without its official boundary.
- Use a glossy stock look with no evidence.
- Use rainbow palettes, or emoji in captions.

## Before showing anything
Run the seven-point test on each frame and fix failures first. Then send PRESHOW.md before the video (gate 5).
