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
| `[SCRIPT_PLAN]` | 30-cue script: line → visual (with its asset code, see the taxonomy) → sound, Visual DNA blueprint, skill per beat |
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

## Visual asset taxonomy (owner, 2026-11-15)

Every beat in a `[SCRIPT_PLAN]` carries one asset code from this list (a beat may pair two, e.g. `[3D-MAP]+[3D-PIN]`).
Status says what the studio can render today.

### 1. 2D statistical and infographic charts (flat vector + grid texture)
For hard numbers, trends, comparisons and quick proof points.

| Code | Visual | Studio status |
|---|---|---|
| `[2D-LINE]` | trim-path line (optional translucent area fill) drawing left to right over graph paper | ready (vox charts) |
| `[2D-BAR]` | bars that wipe or scale on cue; the outlier switches to the accent colour | ready (object bars, `[GLOW]` 3D bars) |
| `[2D-UNIT]` | pictogram grid: icons pop in at 12 fps to make a huge number countable | ready (`films/taxonomy-2026-11-15/taxonomy.py` `unit_grid`) |
| `[2D-BUBBLE]` | proportional circles side by side, or a radial fill for a share | ready (size compare, object pie) |
| `[2D-BOX]` | box plot / range strip: averages, medians, outliers across groups | ready (`taxonomy.py` `box_plot`) |
| `[2D-TIME]` | scrubbing horizontal timeline; year counter ticks, events pop up | ready (photo timeline) |

### 2. 2.5D motion graphics (flat layers in 3D camera space)
For storytelling, history, documents and systems.

| Code | Visual | Studio status |
|---|---|---|
| `[25D-PARALLAX]` | archival photo split into foreground / midground / background, camera pushes in | ready (Depth Anything parallax, `[3D_STAGE]`) |
| `[25D-DOC]` | scanned document in 3D space, highlighter sweep on the key line, the rest blurs | ready (court doc, highlighter) |
| `[25D-NODE]` | infinite-canvas web of portraits, icons and boxes linked by animated curves | ready (`taxonomy.py` `node_canvas`; also the evidence board) |
| `[25D-CARD]` | textured index cards or folders sliding / fanning out as numbered steps | ready (card on desk, polaroids, clothesline) |

### 3. True 3D and spatial (terrain, globes, low-poly models)
For geography, geopolitics, scale, infrastructure and movement.

| Code | Visual | Studio status |
|---|---|---|
| `[3D-MAP]` | tilted real-terrain relief (DEM), camera swoops low, borders hug the ground | ready (`[RELIEF]`); satellite draped on the terrain to add |
| `[3D-PRISM]` | regions extruded into columns by a value (population, GDP) | ready (extruded map) |
| `[3D-PIN]` | pins, flags and leader-line callouts anchored to coordinates, facing the camera | ready (relief pins, cutaway labels) |
| `[3D-MODEL]` | isometric / low-poly cutaway of infrastructure (ships, pipelines, dams) | ready (`[CUTAWAY]`, isometric scenes) |
| `[3D-GLOBE]` | rotating Earth with paths or ranges; morph between sphere and flat map | ready (`taxonomy.py` `globe`: spin + sphere-to-flat morph) |

### 4. Global style rules (all visuals)
- **Frame rate:** smooth 24/30 fps camera moves; chart reveals and icon pops stepped at 12 fps.
- **Texture:** paper grain, halftone dots and light film noise over clean vectors and 3D renders.
- **Colour hierarchy:** about 80 % muted archival neutrals (off-white paper, warm beige, charcoal ink) and 20 % one
  high-contrast accent. The signature yellow #FFDD33 stays the signal colour; the film's own accent (e.g. burnt red)
  rotates per film.
- These sit alongside the existing rules: pacing gate, evidence first, India's official boundary, numbers sourced,
  illustrative layers labelled.

**Every look in this playbook, old and new, must pass the seven-point Vox × Johnny Harris test (STYLE_REFERENCES.md): one sourced idea, real evidence, map/document/chart, the investigator's hand-made layer, camera feel, a source line, restraint.**

### 5. New looks from the 2026-11-15 reference study (to build on the owner's "build")
Details and rules in STYLE_REFERENCES.md. Status for all: **to build**.

| Code | Visual | Best beat |
|---|---|---|
| `[25D-PORTRAIT-BOARD]` | framed public-domain portrait on a chalkboard of notes | introducing a person in history or science |
| `[25D-PORTRAIT-DOC]` | the person's photo over their own letter | "who was this", in their own words |
| `[25D-DOC-BOARD]` | portrait + year badge + satellite panel on a green grid board | who / when / where opener |
| `[3D-FLAG-RIBBON]` | paper or archival flag cut-out pinned beside a portrait and a dated document (no glossy waving cloth) | a nation's leader or symbol (neutral only) |
| `[3D-MAP-FILL]` | satellite region filled with photo texture, arrow, typewriter labels | what grows or lives in a region |
| `[3D-MAP-EVENT]` | vehicle icons, tracers and date on a satellite place | a historical event at a place |
| `[2D-BAR-PHOTO]` | bars sliced from one photo, or standing over a landscape photo | a statistic about a place or thing |
| `[25D-HUD]` | instrument readouts over a real photo | measuring: climate, disasters, science |
| `[25D-CHALK-NODE]` | chalk network of photo cards on a dark board | investigations, organisations |
| `[25D-STRIPS]` | a statue or monument profile sliced into archive photo strips | one idea through many images |
| `[25D-MONUMENT-CARD]` | monument cut-out, half-sun, pattern strip, paragraph | a building or site in its context |
| `[25D-STRIP-MONUMENT]` | monument built from sky and skyline strips, reflection | reveal of a landmark |
| `[25D-PANORAMA]` | B&W city layers blending, halftone, one colour | a city across time |
| `[25D-PORTAL]` | an object whose glass shows another landscape | travel, discovery, "a way in" |
| `[25D-SPOT-STICKER]` | B&W cut-out, white torn edge, scratch discs, one spot colour | a single device or object (phones, scams) |
| `[2D-DOODLE]` | scribbles, sparks, drawn diagrams around objects (never faces) | energy, shock, a simple mechanism |
| `[V-OBJECT-MAP]` | 9:16: object over a country silhouette, stacked phrase | Shorts: a thing and where it comes from |
| `[V-DEPTH-CROWD]` | 9:16: one sharp figure among many, blurred one in front | Shorts: standing out, conformity (animals) |

Mapping additions: introducing a historical person → `[25D-PORTRAIT-DOC]` or `[25D-PORTRAIT-BOARD]`;
"who, when, where" → `[25D-DOC-BOARD]`; an event at a place → `[3D-MAP-EVENT]`; a statistic about a place →
`[2D-BAR-PHOTO]`; anything measured → `[25D-HUD]`; Shorts → `[V-...]` first.

## Mapping guide: which visual for which beat

| Script beat | First choice | Also good | Avoid |
|---|---|---|---|
| A single headline number | `[2D-BAR]` (outlier lit) or `[GLOW]` counter | `[2D-UNIT]` if the number is countable | a table |
| A trend over time | `[2D-LINE]` | `[2D-TIME]` with events | bars for 20+ points |
| Comparing sizes or shares | `[2D-BUBBLE]` | `[2D-BAR]`, `[3D-PRISM]` for places | pies with more than 4 slices |
| A huge abstract number (people, money) | `[2D-UNIT]` | `[2D-BUBBLE]` scale shock | a bare number with no anchor |
| Spread / inequality / outliers in groups | `[2D-BOX]` | `[2D-BAR]` sorted | averages alone |
| A sequence of dated events | `[2D-TIME]` | `[25D-CARD]` for 3-5 steps | a bulleted list |
| A historical quote, law, report or court record | `[25D-DOC]` | `[25D-PARALLAX]` for the archive photo of the moment | paraphrase without the document |
| An archival photo moment | `[25D-PARALLAX]` | collage cut-out on paper | a flat still over 4.5 s |
| Who is connected to whom / cause and effect | `[25D-NODE]` | evidence board | arrows on a plain slide |
| A step-by-step argument or process | `[25D-CARD]` | `[DRAW]` stroke-by-stroke | five bullets at once |
| A place, border or terrain | `[3D-MAP]` + `[3D-PIN]` | `[ORBIT]` satellite, halftone route map | a flat locator map only |
| Movement (trade, migration, smoke, armies) | `[3D-MAP]` route or `[3D-GLOBE]` paths | halftone route map | a static arrow |
| A value by region | `[3D-PRISM]` | choropleth | prisms where heights can't be compared |
| How a machine, building or system works | `[3D-MODEL]` cutaway | `[PHYSICS]` for the mechanism | stock footage only |
| Global reach (cables, flights, ranges) | `[3D-GLOBE]` | world route map | a cropped flat map hiding distance |
| A behaviour or bias (Dragon Psychology) | `[PHYSICS]` metaphor or `[DRAW]` | `[SIMULATE]` viewer test | a real person shown as the "bad" example |
| Before vs after | `[ORBIT]` slider | split collage | two separate shots far apart |

Rules of use: one code per beat is the default; never the same code three beats running; Print Facts opens on
`[25D-DOC]`, `[ORBIT]` or real footage (evidence first).

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
