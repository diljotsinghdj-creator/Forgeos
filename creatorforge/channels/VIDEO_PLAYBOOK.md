# Video playbook: the prompts and commands for a Vox-style film (2026-11-15)

The owner asked: "what prompts and commands do you need when I want to create a Vox-style video? Use all your
skills, everything I taught you, the GitHub repos." This is the answer. Every session follows it. It sits on top of
MASTER_DIRECTIVES, PRODUCTION_CONSTITUTION, VOX_PRODUCTION_SYSTEM, SHOWRUNNER and BRAIN_LOG; the hard rules there
still win.

## The short version (what the owner types)

| Step | The owner types | What happens | Gate |
|---|---|---|---|
| 1 | `[PRINTFACTS]` or `[DRAGONPSYCH]` + **topic** + length + format | channel locked | channel lock |
| 2 | (nothing; wait) | research dossier: every fact with a source and a status | evidence first |
| 3 | **pick 1, 2 or 3** | three narrative engines pitched, owner picks one | gate 1: no pick, no script |
| 4 | `[SCRIPT_PLAN]` | beat-by-beat script, a visual for every line, the Visual DNA | gate 2: SEEN.json |
| 5 | `[STYLE_SHIFT]` (optional) | three new looks if the first doesn't land | |
| 6 | `[VISUALS]` | key frames only, as contact sheets | owner sees the look |
| 7 | **approve** or notes ("redo 4, 9") | fix only what was named | |
| 8 | **go** | narration, music, SFX, edit, render | "no video until go" |
| 9 | (nothing; wait) | PRESHOW.md first, then the video | gate 5 |
| 10 | notes, or **publish pack** | fixes; then title, thumbnail, description, chapters, cutdowns | |

Nothing is rendered as video before **go**. No AI images and no ElevenLabs without asking.

## Step 1: the brief (copy, fill in, send)

```
[PRINTFACTS]            (or [DRAGONPSYCH])
Topic: <one line>
Angle / question: <what the viewer should understand at the end>
Length: <60 s | 3 min | 8-12 min>   Format: <16:9 | 9:16 | both>
Region: <India | US | world>        Narration: <my ElevenLabs voice | Kokoro stand-in>
Must include: <a document, a map, a person's real photo, a number...>
Avoid: <anything>
References: <links / screenshots, optional>
```

What the studio needs from the owner and can't get alone: the topic, the angle, permission for paid tools, and the
owner's own narration if it's their voice. Everything else it finds.

## Director commands (all of them)

### Existing (PRODUCTION_CONSTITUTION, VOX_PRODUCTION_SYSTEM)

| Command | What it does |
|---|---|
| `[PRINTFACTS]` / `[DRAGONPSYCH]` | lock the channel |
| `[SCRIPT_PLAN]` | 30-cue script: line → visual → sound, Visual DNA blueprint, skill per beat |
| `[STYLE_SHIFT]` | three new visual directions (type, palette, texture, motion) |
| `[SIMULATE]` | one self-contained HTML motion scene for a beat ("viewer brain trap" for Dragon Psychology) |
| `[3D_STAGE]` | three-layer parallax desk or map stage |
| `[SFX_LOG]` | timed foley, room tone and music cue sheet |

### New (this playbook)

| Command | What it does | Tool behind it |
|---|---|---|
| `[VISUALS]` | key frames of every beat as contact sheets, no video | the whole studio |
| `[RELIEF] <place>, <route>` | real-terrain 3D relief map, one area lit, a glowing route | Terrarium elevation tiles + three.js bloom (`films/vox-tools-2026-11-15/relief.py`) |
| `[ORBIT] <place>, <date or two dates>` | real satellite view, or a before/after slider | NASA GIBS (MODIS, Blue Marble, VIIRS night lights) |
| `[PHYSICS] <dominoes | tower | galton | custom>` | real rigid-body physics as a metaphor | Rapier (Apache-2.0) + three.js |
| `[CUTAWAY] <object>` | labelled blueprint cutaway, one part glowing | three.js + bloom |
| `[GLOW] <the fact>` | dark 3D chart or object, only the key fact lit | three.js UnrealBloomPass |
| `[DRAW] <idea>` | stroke-by-stroke ink drawing with a pen at the tip | `drawing.py` |
| `[ARCHIVE] <subject>` | search NARA, Library of Congress, Internet Archive, Wikimedia, Open Beelden, NASA | providers |
| `[FOOTAGE] <subject>` | free B-roll candidates (Pixabay, NASA, Commons, archives) on a numbered sheet | providers + pick-by-eye |
| `[PICK] <numbers>` | owner chooses photos or clips from a numbered sheet | `pick.py` / `take.py` |
| `[BEAT]` | time cuts and number pops to the music beat | librosa (to add) |
| `[REDO] <frame numbers>` | rebuild only those frames | |
| `[CHECK]` | QA pass: facts, overlaps, pacing, licences, repeats, India boundary | QC + gates |
| `[PUBLISH_PACK]` | titles, thumbnail options, description with sources, chapters, 9:16 cutdowns | studio SEO + thumbnail |

## What the studio uses, beat by beat

| Need | Tool (all free) |
|---|---|
| Facts | research dossier: source + status for every claim; allegations attributed, other side shown |
| Evidence first (Print Facts) | real document, photo or footage before the first explanation (NARA, LoC, court records, gazettes) |
| Maps | official India boundary always; halftone route maps, satellite (GIBS), relief (Terrarium), globes, night lights, before/after |
| Collage | Pixabay photos picked by eye, BiRefNet cut-outs, torn paper, halftone, sun discs, giant hands, stamps, polaroids, ransom letters, evidence board |
| Numbers | glowing sourced counter, bars from zero, the one fact lit (`[GLOW]`) |
| Metaphor | real physics (`[PHYSICS]`), cutaways, isometric scenes, live drawing |
| Archive | NARA, Library of Congress, Internet Archive, Wikimedia, Open Beelden, NASA, ESO/ESA |
| Motion | 12 fps paper physics, motivated transitions, match cuts, camera push, 60 fps (RIFE) for live footage, depth parallax (Depth Anything) |
| Voice | the owner's ElevenLabs voice (with permission) or a Kokoro stand-in, never a cloned celebrity |
| Captions | WhisperX word-by-word, signature yellow #FFDD33 highlight |
| Music & sound | ACE-Step or free licensed music, Freesound foley, `[SFX_LOG]` mix, cuts on the beat |
| Finish | grain, vignette, one accent colour + signature yellow, pacing gate (still ≤ 4.5 s, build ≤ 7 s, mean ≤ 5 s) |

Not used, by the owner's rules: AI faces or AI images of real people, mascots, paid tools, the owner's RunPod
tokens, anything that clones another creator's film.

## Prompts that get the best result

- **Topic prompt:** "[PRINTFACTS] Topic: why Delhi's air gets worst in November. Angle: what actually burns, and
  who decides. 3 min, 16:9 + a 60 s 9:16 cut. Must include: satellite fire data, a real government document."
- **Narrowing prompt:** "Engine 2, but open on the document, not the map."
- **Look prompt:** "[STYLE_SHIFT] darker, more archival, less collage" or "make it look like reference X" (send it).
- **Frame notes:** "Frame 7: number too small. Frame 12: wrong photo. Frame 15: swap to [RELIEF]."
- **Beat prompt:** "[PHYSICS] dominoes for the bank-run beat" / "[DRAW] the sunk-cost idea for beat 4".
- **Final:** "go" (only then is the video rendered), then "[PUBLISH_PACK]".

## Where things live

- A film: `creatorforge/films/<slug>/` with pick.json, dossier.json, lines.json, VISUAL_DNA.md, PRESHOW.md, SFX_LOG.md, sheets/.
- Memory of looks used: `SEEN.json` and `studio_history/`. Lessons: `BRAIN_LOG.md`.
- The app (Android) talks to the worker on a GPU pod the owner starts (`worker/cloud/README.md`).
