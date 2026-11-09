# Documentary engine: production spec, honest status, build order

This is the working document for the master directive (a Vox / Johnny Harris-level documentary system with an
original identity). It has four parts: the visual language we build to, what the engine does **today** (checked
against the code, not hoped for), what is missing, and the order the gaps get built in. A feature is only marked
**works** when code for it exists and a test or a rendered frame has shown it working.

Status words: **works** (built, tested) · **partial** (built, with the stated limit) · **pod-only** (built, but
needs a tool or network this sandbox does not have, so it is only proven on the RunPod worker) · **missing**.

---

## 1. The visual language (what we are building to)

Studied from the two references (technique only; no logos, intros, footage, music, faces or voices are copied).

| Discipline | The reference technique | Our rule |
|---|---|---|
| Typography | A heavy serif for headlines, a condensed sans for numbers, a clean sans for labels, mono for sources, marker handwriting for notes | Five roles, one face each per video (`vox.LOOKS`): head, big, label (Inter), source (JetBrains Mono), hand |
| Hierarchy | One idea per frame; headline in a black box; number biggest; source smallest, bottom | `boxText` headline, `Anton`-role figure, mono source line; nothing else competes |
| Colour | Paper neutrals + black ink + ONE accent; red reserved for the marker | Look sets paper, sea, land, marker; one accent per video |
| Backgrounds | Paper, grid paper, kraft, desk, atlas sea; never flat digital white | Baked paper + grain bitmaps per tone; card-on-desk layout |
| Composition | Big subject, off-centre text, layers that overlap | Layers back / mid / hero / front / side, with parallax |
| Camera | Always moving a little: push, pull, drift, push to the detail | Four moves rotated per shot; 12 fps stutter on drawn elements |
| Rhythm | Cut on the word; a new picture every 2-4 s; hold on a key fact | Beats cut on word timestamps; music beats aligned to cuts |
| Transitions | Motivated: blur-whip between graphics, match cut on a shape, map zoom into footage | `render.TRANSITIONS`; map-to-footage is **missing** (section 4) |
| Maps | Atlas styling, hand marker over it, routes that draw, zoom from globe to street | globe -> fly -> pinmap/route/heatmap chain |
| Evidence | The real document on screen, the line highlighted, source named | article / document / clipping / newscard / pinboard |
| Texture | Halftone photos, sticker edge, shadow, grain, dust, gate weave, light leaks | `cutouts.print_look`, `sticker_edge`, film layer |
| Sound | Whoosh on moves, hit on reveals, riser into a twist, paper and pen foley, music ducked under voice | `sfx.py` roles; ambient beds are **missing** |

**Our own identity ("Print Facts")**: printed-paper collage, period-aware looks (seven: archive, newsprint, kraft,
chart, field, sepia, engraving), no video shares a look or shot order with a recent one (`variety.py`), real
material first (photo, map, document), drawn illustration second, icon last, never an AI face of a real person.

---

## 2. What works today, discipline by discipline

Checked on rendered frames and by tests (`tests/test_vox_look.py`, `test_vox_director.py`, `test_edit_tools.py`).

### 2.1 Infographics (`media/vox.py`, `media/motion.py`, `media/charts.py`)

| Capability | Status | Where |
|---|---|---|
| Bar charts (object bars, figures on bars) | works | `Stack`, `Stand`, `Chart`, `Bars3d` |
| Line graphs | works | `Trend` |
| Pie / share | works | `Slice`, `Pie`, `Squares` |
| Population pyramid | works | `Pyramid` (values count up) |
| Comparative statistics, before/after | works | `Compare`, `Chart a vs b`, `Stand` |
| Timelines | works | `Timeline`, `Photoline`, `Calendar` |
| Election results | works | `Seats` (parliament arc), state `Heatmap` |
| Polling | works | `Polltrack` (line with a margin-of-error band) |
| Financial | works | `Candles` (open/high/low/close), `Area` (stacked), `Trend`, `Receipt` |
| Demographics | works | `Pyramid`, `Squares`, `Heatmap` |
| Flow diagrams | works | `Flowchart` (arrows draw in order, a token travels) |
| Network / relationship maps | works | `Linkmap` |
| Organisational structures | works | `Orgchart` (two levels) |
| Data tables | works | `Table` (row by row, one row picked out) |
| Animated counters | works | `Chart`, `Pyramid`, `Bars3d` |
| Entry animation, labels, layering, camera | works | every scene |
| Exit animation | works | every Vox scene: layers leave front-first (rise / fall / side / shrink) |
| Colour transitions inside a graphic | partial | `Heatmap`, `Sizemap`, `Borders` animate colour; bar charts pop to their colour |
| Sync with narration | works | beat lengths come from word timestamps |

### 2.2 Cartography (`globe.py`, `flyover.py`, `maps.py`, `searoute.py`, `history.py`, `vox.py`)

| Capability | Status | Where / limit |
|---|---|---|
| World and country maps | works | `Pinmap`, `Map`, `Shade`, `Heatmap` |
| Globe to country zoom | works | `Globe` |
| Country to city, tilt and rotate | pod-only | `Fly` (MapLibre + tiles: needs network) |
| Street level, satellite, terrain | pod-only | `Fly ... | satellite` / `| terrain` |
| State / regional boundaries | works | every country (Natural Earth admin-1), by English or local name |
| Shipping routes | works | `Route ... | ship` follows the sea lanes through canals and straits (`searoute.py`) |
| Flight, road, rail routes | works | `Route` (arcs), `Railmap` (networks through stations) |
| Migration, military, trade movement | works | `Arrows` (broad curved arrows, each named) |
| Country and state heat maps with a scale | works | `Heatmap`; in 3D: `Prism` |
| Geographic comparison | works | `Sizemap` (same scale, one shape morphs into the other, area ratio) |
| Historical borders and border change | pod-only | `Borders` needs the dated maps downloaded by setup (`history.py`, GPL data, credited on screen); proven here with the 1914 file |
| District-level heat maps | pod-only | `districts.py` downloads geoBoundaries per country at setup (credited on screen); proven here with a fixture |
| Real terrain in 3D | works | `Terrain3d` (open elevation tiles, cached; needs the network once per place) |
| Labels by zoom level | pod-only | MapLibre does this in `Fly` |
| Map to footage / map to infographic transition | works | the `dive` cut (motivated transitions) |

### 2.3 Motion graphics

| Capability | Status |
|---|---|
| Kinetic typography, word emphasis, highlighter, typewriter | works |
| Marker circle, arrow, underline, hatching, callouts | works |
| Parallax, push, pull, drift, focus push | works |
| Split screen | works (`Split`, `Tornsplit`, `Compare`) |
| Wipes, reveals, blur-whip, dive, page, push, drop, squeeze | works |
| Motion blur on travelling elements | works (`slide`, `drop`) |
| Particles | works (`| fx:` dust, embers, snow, rain, confetti, sparks) |
| Shape morphing | works (`Morph`: countries, states and plain shapes in a chain; `Sizemap` at true scale) |
| Picture-in-picture | works (`| inset:` a framed picture; `| with:` a person beside the graphic) |
| 3D camera movement | works in the 3D scenes (orbiting perspective camera) |
| 3D camera into a still photo | pod-only (`depth3d.py`, needs the depth model) |
| Animated light and shadow | works in 3D scenes (sun with soft shadows, a light sweep on `Title3d`) |

### 2.4 Narration to visuals (`infographic.py`, `vox_director.py`, `literal.py`)

Works: for every line the director extracts facts, proposes candidates, ranks real material first, rejects a graphic
that fails the mute test, varies objects, adds the named person and platform logos, and picks camera, layout and
exit. The cut into the next shot now comes from what the two shots are (`pipeline.motivated_transition`).
The rule-based director picks from narration alone: Sizemap, Heatmap / Prism (three or more places each with its
number), Bars3d, Arrows (a movement between places), Linkmap (three or more names and a word about ties), Interview
(a named person speaking in the line), Borders (an old year, a place, a word about borders) and Terrain3d (a named
peak or pass). Kinds that need structured data a sentence does not carry (Pyramid, Orgchart, Table, Polltrack, Area,
Candles, Flowchart, Railmap, Towers3d, Explode) and Courtdoc (it must quote the court's own words, which Hindi
narration does not give in English) are chosen by the script AI or written by hand, never guessed.

### 2.5 Archival and investigative

Works: clippings, real article screenshots, documents with highlighting, court documents (`Courtdoc`), data tables,
interviews with lower third and typed pull quote, receipts, social posts, comments, chat, search, evidence board,
photo timeline, source lines, attribution checks, and an on-screen standing for any graphic (`| badge:` verified,
official data, court record, reported, alleged, claim, denied, response, opinion, estimate).
Pod-only: real archive photographs and footage (need the photo sources).

### 2.6 2D, 2.5D, 3D

| Pipeline | Status |
|---|---|
| 2D vector and character animation | works (`animation/`) |
| 2.5D layered parallax | works in drawn scenes; depth-map dolly is pod-only |
| Genuine 3D: `Bars3d`, `Prism` map, `Explode`, `Title3d` | works (three.js in headless Chromium: meshes, sun, soft shadows, orbiting camera; no Blender, no GPU needed) |
| 3D globe | works |
| Blender characters and intro | pod-only (Blender is not in this sandbox) |
| 3D terrain | works (`Terrain3d`: real elevation, lit, the summit named) |
| Buildings to scale | works (`Towers3d`: stepped massing with floors and a person for scale; not a model of the building) |
| Detailed architectural models | missing (needs real building models) |

### 2.7 Editing

Works: beat-level cuts on word timestamps, music-beat alignment, punch-in, settle, shake, jump cuts, montage,
zoom-through match cut, multi-layer compositing, 12 fps stepped graphics, freeze frame, speed ramp and slow motion
on footage (`Playback:`), motivated transitions, graphics that move with the voice (`| voice`, and the bars on
`Interview`, driven by the narration's measured loudness).

### 2.8 Typography

Works: titles, chapter cards, headlines, statistics, source lines, captions, quotes, location labels, lower third
(`Interview`), end card (`Endcard`), 3D title. Hindi: display faces for headlines and figures (Rozha One, Teko,
Mukta under the Latin family names), no tracking on Devanagari, captions and handwriting as before. The 3D title
face is Latin only (a Hindi title is refused there and belongs in the 2D type scenes).

### 2.9 Audio

Works: narration, word alignment, music with beat offset, ducking, loudness normalisation, whoosh / hit / pop /
riser / scribble by transition and role, ambient beds per shot (`ambience.py`: sea, wind, city, room, paper,
projector, hum), stereo placement (a whoosh travels across with the cut; cues can sit left or right).
Missing: surround / object audio (the output is stereo).

### 2.10 Quality control

Works: fail-closed export verification; loudness, clipping, dead air, frozen or black picture, first frame; caption
drift; text fit and safe areas; picture-matches-line (CLIP); script preflight (facts, attribution, valid graphics,
places found on the map); flat-contrast frames; colour-grade jumps; frame size; audio cut off at the end; the accent
made readable as type on its paper; video-against-video similarity (`variety`).
A picture shown much larger than its own size is flagged before the render (`*.qa.json`, collected into the
quality report).

### 2.11 Output

Works: 16:9, 9:16, 1:1 with layouts composed per aspect, 1080p and 4K (`resolution: "4k"`: graphics are drawn at
2160p), 60 fps option.

## 3. Dependencies

| Need | Tool | Where it must be |
|---|---|---|
| Drawn scenes | Chromium + Playwright, svg.js (bundled) | worker (present) |
| Cut, mix, encode | FFmpeg | worker (present) |
| Photos | Pixabay / Unsplash / Openverse / Wikimedia (keys in pod env) | pod network |
| Cut-outs | ISNet ONNX, OpenCV < 5 | pod |
| City and satellite maps | MapLibre GL + tile servers | pod network |
| Depth dolly | Depth Anything V2 Small | pod |
| Genuine 3D | Blender (bpy or `blender -b`) | pod; **not in this sandbox** |
| Word timing | WhisperX | pod GPU |

---

## 4. What is still open

1. Detailed architectural models and surround audio (out of reach without model assets / a surround pipeline).
2. On the pod: prove `Fly`, satellite, depth dolly, Blender, dated borders, districts and real photographs in one
   render (the acceptance storyboard, through the real voice and word alignment).

## 5. Acceptance test

`python -m creatorforge_worker.acceptance <out_dir>` builds a 14-scene documentary (the 2021 Suez blockage, checked
figures) with the engine's own modules and spoken narration, then scores every discipline on its own. In this
sandbox it passes all eleven that can run here (maps, infographics, kinetic type, document evidence, 2.5D, genuine
3D, source citations, motivated transitions, sound design, narration sync, finished-film quality) and lists as
**pod-only**, never as passed: archive footage, the depth-map camera move, street-level and satellite maps, real
cut-out photographs and word-level alignment. The system is done when the same storyboard passes those on the pod.
