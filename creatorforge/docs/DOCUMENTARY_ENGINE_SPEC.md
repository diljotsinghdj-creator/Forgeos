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

### 2.1 Infographics (`media/vox.py`, `media/motion.py`, `media/charts.py`)

| Capability | Status | Where |
|---|---|---|
| Bar charts (object bars, figures on bars) | works | `Stack`, `Stand`, `Chart` |
| Line graphs | works | `Trend` |
| Pie / share | works | `Slice`, `Pie`, `Squares` |
| Population pyramid | works (new) | `Pyramid` |
| Comparative statistics, before/after | works | `Compare`, `Chart a vs b`, `Stand` |
| Timelines | works | `Timeline`, `Photoline`, `Calendar` |
| Election results | works | `Seats` (parliament arc) |
| Polling | partial | shown with `Slice` / `Stack`; no poll-tracker (line with margin band) yet |
| Financial | partial | `Trend`, `BigNumber`, `Receipt`; no candlestick or stacked area |
| Demographics | works | `Pyramid`, `Squares` (1 in N people) |
| Flow diagrams | works (new) | `Flowchart` |
| Network / relationship maps | works (new) | `Linkmap` |
| Organisational structures | works (new) | `Orgchart` |
| Animated counters | works | `Chart` counter, `Pyramid` values |
| Entry animation, labels, layering, camera | works | every scene |
| **Exit animation** | **missing** | scenes end on a hold; the cut is a transition, not an animated exit |
| Colour transitions inside a graphic | partial | `Heatmap` fills animate; others pop to final colour |
| Sync with narration | works | beat lengths come from word timestamps |

### 2.2 Cartography (`globe.py`, `flyover.py`, `maps.py`, `vox.py`)

| Capability | Status | Where / limit |
|---|---|---|
| World and country maps | works | `Pinmap`, `Map`, `Shade`, `Heatmap` |
| Globe to country zoom | works | `Globe` |
| Country to city, tilt and rotate | pod-only | `Fly` (MapLibre + OSM tiles: needs network) |
| Street level, satellite, terrain | pod-only | `Fly ... | satellite` / `| terrain` |
| State / regional boundaries | partial | Indian states are pins, not shapes: no sub-national polygons bundled |
| Routes: flight, shipping, migration, trade | partial | `Route` draws and animates a vehicle; sea routes cut across land (no sea-lane routing) |
| Country heat map with scale | works (new) | `Heatmap` |
| Sub-national density / heat | missing | needs state/district shapes |
| Historical borders | missing | needs a dated border dataset |
| Animated border change | missing | |
| Military movement arrows, front lines | missing | |
| Transport networks | missing | |
| Labels by zoom level | pod-only | MapLibre does this in `Fly` |
| Map to footage / map to infographic transitions | missing | only the generic transitions today |

### 2.3 Motion graphics

| Capability | Status |
|---|---|
| Kinetic typography, word emphasis, highlighter, typewriter | works (`kinetic.py`, `Statement`, `rich`, `typeIn`) |
| Marker circle, arrow, underline, hatching, callouts | works (`marker:`, `pen`, `marks.py`) |
| Parallax, push, pull, drift, focus push | works |
| Split screen | works (`Split`, `Tornsplit`, `Compare`) |
| Wipes, reveals, blur-whip | works (xfade set) |
| 3D camera into a still | pod-only (`depth3d.py`, needs the depth model) |
| Shape morphing | missing |
| Particles | missing |
| Motion blur on moving elements | missing (only the blur transition) |
| Picture-in-picture | missing as a named tool (the framed-footage layout is close) |
| Animated light / shadow | partial (light leak, drop shadows; no moving light) |

### 2.4 Narration to visuals (`infographic.py`, `vox_director.py`, `literal.py`)

Works: for every line the director extracts facts (numbers, places, people, parties, publishers, quotes, denials,
false claims), proposes candidates, ranks real material first, rejects a graphic that fails the mute test (the key
fact must be on screen), varies objects, adds the named person and platform logos, and picks a camera and layout.
Partial: the transition into the next scene is chosen by style map, not yet by what the two shots share.

### 2.5 Archival and investigative

Works: clippings, real article screenshots, documents with highlighting, receipts, social posts, comments, chat,
search, evidence board, photo timeline, source lines, attribution checks in preflight.
Partial: fact / allegation / commentary are enforced in the script checks, but there is no on-screen badge
("ALLEGED", "COURT RECORD", "OPINION") except the ILLUSTRATION · OPINION tag.
Missing: court-document and database-table templates; interview lower-third with pull quote.

### 2.6 2D, 2.5D, 3D

| Pipeline | Status |
|---|---|
| 2D vector and character animation | works (`animation/`: rig2d, scene2d, stick) |
| 2.5D layered photo parallax | works in drawn scenes; depth-map dolly is pod-only |
| 3D globe | works |
| 3D objects (coin, card, bars) | partial: drawn frame by frame in Pillow, not a 3D engine |
| Genuine 3D (Blender: characters, title, camera, lights) | pod-only: `blender3d.py`, `intro3d.py` need Blender, which is **not installed in this sandbox**; unproven here |
| Exploded views, architecture, 3D terrain | missing |

### 2.7 Editing

Works: beat-level cuts on word timestamps, music-beat alignment, punch-in, settle, shake, jump cuts, montage of
beat clips, multi-layer compositing, 12 fps stepped graphics. Missing: speed ramps, freeze frames, true match
cuts (today "match" is a short fade), audio-reactive elements.

### 2.8 Typography

Works: titles, chapter cards, headlines, statistics, source lines, captions (word-by-word, Hindi and English),
quotes, location labels. Partial: lower thirds and end cards exist in the older card set but are not in the
Vox kit's type system. Hindi: captions and handwriting are covered; the display faces are Latin-only, so Hindi
headlines fall back to a system face (a Devanagari display face is needed).

### 2.9 Audio

Works: narration, word alignment, music with beat offset, ducking, loudness normalisation, whoosh / hit / pop /
riser / scribble placed by transition and role. Missing: ambient beds per scene, spatial audio.

### 2.10 Quality control

Works: fail-closed export verification, loudness / clipping / dead air / dark first frame, caption drift, text
fit and safe areas (`layout_qa`), picture-matches-line (CLIP), script preflight (facts, attribution, graphics
valid), video-against-video similarity (`variety`). Missing: contrast check, low-resolution asset check,
map-label check, grade consistency check.

### 2.11 Output

Works: 16:9, 9:16, 1:1 with layouts composed per aspect (not cropped), 1080p, 60 fps option.
Missing: 4K.

---

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

## 4. Build order for what is missing

1. **Exit animations** for every drawn scene, and motivated transitions (shared shape or position; map zoom into
   the next shot).
2. **Maps**: sea-lane routing; sub-national shapes (Indian states first) for state heat maps; arrows for movement
   (migration, military); border-change animation; transport lines.
3. **Evidence badges** (verified / alleged / opinion / court record) and court-document, data-table, interview
   templates.
4. **Charts**: poll tracker with margin band, stacked area, candlestick.
5. **Type**: Devanagari display face; lower third and end card in the kit.
6. **Edit**: freeze frame, speed ramp, true match cut.
7. **Motion**: particles, shape morph, motion blur on movers, picture-in-picture.
8. **Audio**: ambient beds.
9. **QC**: contrast, asset resolution, map labels, grade consistency.
10. **4K** output.
11. **3D**: prove Blender on the pod; add exploded view and terrain.

## 5. Acceptance test

A 60-90 s documentary on a non-political world topic, rendered on the pod (real photos, tiles, Blender), that
contains: a globe-to-city map move, a route, a heat map, three different infographics, kinetic type, an archival
photo sequence, a highlighted document, a 2.5D depth shot, one Blender 3D shot, motivated transitions, full sound
design, word-accurate cuts and source lines. Each discipline is scored on its own; the video is not called done
while any row above that it uses is short of **works**.
