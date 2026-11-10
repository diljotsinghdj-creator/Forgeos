# Production knowledge base

This knowledge base records the method the studio works by. It is a study of techniques, not of anyone's finished
work: no scene, script, graphic, logo or artwork is reproduced. Every entry says what the technique is for, when it is
the right choice, how the engine does it (the screenplay line or option), and its status. **works** means built and
tested. **pod-only** means built, but it needs a model, a key or network that only the pod has. **not built** means
just that.

## 1. The combined method

Explanatory clarity and visual investigation are one discipline, not two styles to alternate between.

1. **One question carries the film.** Every scene either sharpens it, answers part of it, or complicates it. A scene
   that does none of the three is cut. (`writer.check` requires a central question and a hook.)
2. **Show the evidence, then explain it.** A real place, document or photograph first, so the viewer trusts it.
   Then a graphic takes over to explain it. (`Photo ... | then: pin / number`, document then map.)
3. **The viewer must get it with the sound off.** A line with a figure or a date puts it on screen (the mute test).
4. **Reveal in the order the story reasons.** Labels, bars and arrows appear when the narration reaches them, not
   all at once. Graphics build, hold, then leave.
5. **The camera points.** A push picks out what matters; stillness lets evidence be read; a pull gives context.
   Moving everything all the time means nothing points. (Art direction camera policy; `camera: still` on evidence.)
6. **Texture is honesty.** Paper, print, grain and handwriting say "this was made by people looking at sources". The
   source line, badges and credits say which sources.
7. **Every film looks like itself.** Techniques are reused; treatments are not. (Art direction plus studio history.)

## 2. Decision table (`studio/decide.py`)

| Narration needs | Preferred treatments, best first |
|---|---|
| A real person or event | verified photograph · footage · document · combination |
| A geographical explanation | animated map · photo-to-map · photograph |
| A statistical claim | custom infographic · photo-to-figure |
| A historical event | archive photograph · labelled reconstruction · map |
| A financial mechanism | financial flow diagram · document |
| An institution | organisational graphic |
| An abstract concept | illustration or visual metaphor |
| A specific document | the document, annotated |
| A location introduction | photograph · footage · map |
| A sequence of events | timeline |
| A physical process | 2D or 3D process animation |
| A human consequence | photograph · footage |

Each option is scored on five things: whether it shows the line's key facts, how authentic it is for this claim,
whether it suits the need, whether it repeats the last shot, and whether the material can be had. Every decision
is written to `writing/visual_decisions.md` with all its options. Stock footage is never chosen by default, and
neither is animation.

## 3. Techniques

### Photography (`Photo:` / `Photos:` / `Photo3d:`)

| # | Technique | Line / option | Status |
|---|---|---|---|
| 1 | Full-screen photograph | `Photo: src` | works |
| 2-5 | Push, pull, horizontal and vertical moves | `push`, `pull`, `pan-left/right`, `tilt-up/down` | works |
| 6-7 | Multi-layer parallax, foreground and background | `depth: layers` (default): depth bands; the far layer filled only inside the nearer ones | works (estimated depth: pod-only) |
| 8 | Animated subject cut-outs | the nearer layer is the subject (BiRefNet, else ISNet, else GrabCut; never a guessed cut of a person) | works (BiRefNet: pod-only download) |
| 9 | Depth-map animation | Depth Anything V2 bands; `Photo3d` mesh | pod-only for the model; the subject-plane fallback works |
| 10 | Animated photographic collage | `Photos: a, b, c \| collage` | works |
| 11 | Split-screen comparison | `Photos: a, b \| split \| labels: 1960, today` | works |
| - | Before / after on the same frame | `Photos: a, b \| swipe` (a wipe with a handle) or `\| fade` (a dissolve), dates as labels | works |
| 12 | Photo to map | `then: pin <place>` (the photo becomes a card pinned on the map) | works |
| 13 | Photo to infographic | `then: number <figure> <caption>` (the photo greys out under the figure) | works |
| 14-16 | Annotations, highlighted detail, moving labels and arrows | `annotate: circle / arrow / box / label`, `detail \| at: x,y,w,h` (a spotlight) | works |
| 17 | Animated frames and borders | `frame: print / taped / polaroid` | works |
| 18 | Perspective transformation | `Photo3d: src \| tilt-left / tilt-right` (a print turning in real 3D) | works |
| 19 | Multi-image composition | `Photos:` collage / split | works |
| 20 | Photo sequence with transitions | `Photos: a, b, c \| sequence` | works |
| - | Camera projection, 3D camera mapping | `Photo3d: src \| dolly / orbit` (the photo on a mesh shaped by its depth) | works |
| - | Light sweep, colour grade | `light: sweep`, `grade: mono / warm / cool / archive` | works |

Nothing is invented. The fill behind a layer exists only so that a small parallax move never opens a hole. A stock
picture standing in for a specific place or event is tagged **ILLUSTRATIVE** on screen (`assets.select` decides
this). Every change to an asset is written to its modification history in the ledger.

### Footage (`Footage:`)

Moving footage is played frame by frame inside the same page as the graphics, so annotations, titles and badges sit
on the footage. Options: `in:` and `speed:` (slow motion). Freeze, speed ramps and slow motion in the edit come from
`Playback:`. Stock footage is for atmosphere and context. A generic clip on a specific line is ILLUSTRATIVE.
**works**; the footage itself is pod-only, since this sandbox can't reach the stock sites.

### Stock media workflow (`studio/assets.py`)

1. **Search** with several phrasings: the subject, the subject in its place, the place, the purpose's words, and
   "vintage" for old periods. Sources are Unsplash, Pixabay and Pexels (keys in the pod's environment), plus
   Openverse with commercial-use licences only.
2. **Score the metadata:** relevance, geographic match, period match, resolution, and how much a crop loses.
3. **Score the pixels** of the best few: exposure, contrast, sharpness, composition, fit with the film's palette,
   and continuity with the previous shot.
4. **Keep it in the library and the ledger:** asset ID, original filename, site, asset URL and page URL, creator,
   download date, licence and its terms, attribution, rights to check (people, brands, property), film, scene,
   categories, scores, uses and modification history. The ledger is exported per film to `research/assets.csv`.
   Unsplash downloads are reported to Unsplash, as its API terms require.
5. **Before publication:** every asset with a rights flag is listed for a human check.

### Infographics, maps, 3D and motion

These are covered in `DOCUMENTARY_ENGINE_SPEC.md`, which lists about 45 graphic types: charts, maps, diagrams,
documents and 3D. Isometric (orthographic) views of the 3D scenes come from `| isometric`. Each graphic is composed
from the line's own data, with layouts rotated per type and treatments from the film's art direction. None is a
fixed template.

### Compositing and other techniques (15.5)

| Technique | How | Status |
|---|---|---|
| Green-screen compositing, chroma keying | `Key: fg \| background: bg \| color: 00FF00` (FFmpeg chromakey and despill) | works |
| Rotoscoping | stills: BiRefNet / ISNet masks. Footage: `Footage: clip \| cutout` cuts the subject out of every frame onto the paper (SAM 2 video tracking from one box, else BiRefNet frame by frame); `subject: x,y,w,h` names it | works (SAM 2: pod-only) |
| Motion tracking | `Footage: clip \| follow: <note>`: a ring and a note stay on the tracked subject (SAM 2 / BiRefNet masks); footage pan tracking for marks (`render.Clip.track`) | works (SAM 2: pod-only) |
| Camera projection, 3D camera mapping | `Photo3d` | works |
| Depth-map animation | `Photo` depth layers, `Photo3d` | works (model on the pod) |
| Fill behind a moved layer | LaMa inpainting, else OpenCV; only inside the nearer layer, so nothing new is shown | works (LaMa: pod-only) |
| Data maps in 3D | `Flowmap: A → B 120, ...` (arcs as wide as their numbers, lights travelling along them), `Columns: place 1.4, ...` (3D columns standing on the map), `Dots: place 37, ...` (circles by area). deck.gl, Natural Earth land, the camera tilting slowly | works |
| Hand-drawn ink | Every marker stroke (circles, arrows, strike-throughs, map routes, annotations) is a perfect-freehand pen stroke, tapered like a real marker; photo boxes are Rough.js sketches. All of them draw on cue and then "boil" (re-posed 6 times a second, seeded, so renders match). A look can switch the boil off | works |
| Myth turned over | `Myth: <wrong idea> \| <what is true> \| <stamp>`: the wrong line struck through in marker, a stamp, the true line printed over it. Only when the dossier shows it is a myth | works |
| Counter | `Counter: <from> → <to> \| <unit> \| <caption>`: a real figure counting in fixed digit slots (no jitter), 1.2–1.6 s, then holding | works |
| Staircase | `Staircase: step; step; step \| title`: isometric steps lighting one by one as the story climbs (an escalation, a process) | works |
| Balance scale | `Scale: weight, weight \| other side \| verdict`: weights drop on one pan, the beam tips, the other side is thrown off, a verdict stamp | works |
| Text QA in every scene | Each scene measures its own text once everything has landed: text under 2.6% of the frame's short side, and text cut off at the edge, go to the QC report with a 360-px phone contact sheet | works |
| Effect timing | Every effect's loudest moment lands one frame after its picture (a whoosh's swell on the cut); two takes of a sound never play back to back | works |
| Pod self-test | `python -m creatorforge_worker.selftest --network` reports every model, key and service as works / missing / failed (key values never shown) | works |
| Title entrances | Chart titles enter one of three ways (slide, blur-in, wipe), chosen per scene so a film doesn't repeat one, then land dead still | works |
| Reading holds | The editorial review warns when on-screen words can't be read in the time the line is up (0.5 s + 0.3 s a word) | works |
| Matte painting, digital set extension | **not built, deliberately:** it would add detail that was not there to a documentary picture; allowed only as a labelled reconstruction | - |
| Animated cut-paper compositions | the Vox scenes' cut-outs, paper and print looks | works |
| Isometric illustration | `\| isometric` on the 3D scenes | works |
| Architectural visualisation | `Towers3d` (massing to scale); detailed building models are not built | partial |
| 3D object breakdowns, exploded views | `Explode` | works |
| Screen recording, interface recreation | the `screen`, `article`, `search`, `chat`, `social` and `comments` scenes; a recreation is labelled as one | works |
| Newspaper reconstruction, document animation | `Clipping`, `Newscard`, `Courtdoc`, `Document` | works |
| Visual evidence boards | `Pinboard`, `Linkmap` | works |
| Animated historical photographs | `Photo` with `grade: archive`, depth layers and annotations; no colourisation | works |
| Satellite imagery | `Satellite: <place> \| 2000 vs 2020 \| swipe / fade / split`: the same ground on two dates (NASA GIBS MODIS / VIIRS, keyless; Sentinel-2 10 m with Copernicus keys). The clearest day within two days of each date is used and its year is on screen; a date with no imagery stops the shot. Also `Fly ... \| satellite` (tiles) | works (imagery: pod-only) |
| Photogrammetry | not practical here (needs many photos of one subject and a reconstruction toolchain) | not built |
| Environmental sound, colour grading, film grain | `ambience.py`; per-film grade (`warm / cool / bleach / neutral`); the film layer | works |
| Music | ACE-Step composes an instrumental bed per act from its mood (pod, `CF_ACESTEP=1`), else the synthesised score; a licensed track (`music_track`) has any singing removed by Demucs | pod-only for ACE-Step and Demucs |
| Sound effects | Real recorded effects from Freesound, CC0 and CC-BY only, credited in `audio/sfx_credits.txt` (`FREESOUND_KEY`); the built-in set otherwise | pod-only (key) |
| Loudness | FFmpeg EBU R128 plus an independent BS.1770 measurement (pyloudnorm) in the QC report | works |

## 4. How a reference is studied (15.7)

When a reference film is analysed, these questions are recorded in the film's notes, never its frames:

* What does each shot let the viewer understand that the narration alone does not?
* What enters when, and what the camera is pointing at.
* How a photograph is used: as evidence, as atmosphere, or as the start of a graphic.
* How a map is entered and left: from a photo, into a figure, from the globe.
* Where the cut lands relative to the spoken word, and what the sound does at that moment.

The answers become reasons in this knowledge base, and new options in the engine when a technique is missing. They
are never a copied sequence.
