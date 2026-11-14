# Motion graphics

How graphics move so that they explain. Read this for any scene whose visual_mode is explain-role (map, chart,
diagram, timeline, process, 3D, collage, kinetic type) and when setting the film's `motion_language`.

Labels: [V] a source states it (see sources.md, case_studies/) · [I] informed interpretation · [O] our production rule.

Contents: 1. What the studied craft shows · 2. The core rule: build on the word · 3. Technique specs ·
4. Camera grammar · 5. Layering, masking, parallax · 6. Texture and frame rate · 7. Transitions that carry
information · 8. Callouts and tracking · 9. Failure modes

---

## 1. What the studied craft shows

- [V] After Effects is the core build tool for maps and animation, with Premiere for the final edit and Photoshop for
  textures (P8, P9, P27).
- [V] An art director gives visual notes on a producer's animation and keeps it within a shared style guide of
  "tools, templates and rules", while producers develop their own style inside it (P9, P25). [I] This is the 20/80
  model: a fixed system plus a per-film voice.
- [V] Google Earth Studio provides 3D map moves (zooms, slow orbits). The frames are brought into After Effects,
  linked to a master map and annotated, e.g. a zoom into a specific building annotated to show how money moved (P23).
- [V] Handmade materials: some videos were built entirely from construction paper (P8). [V] A third-party breakdown
  (not Vox's own account) attributes part of the look to graphics animated at 12 fps inside a 24 fps edit, which gives
  a slight stutter (P28).
- [V] Animation is used carefully on serious subjects: the art director warns against misleading positivity, since
  animation rarely shows graphic real images (P8).
- [V] The "explained in N moments" format organises chapters with a recurring visual device (P15).
- [V] In a data interactive, the base map took about a day; the extra time went into the last 10 percent, chiefly
  making the animated change between two states (work and home) readable (P26).
  [I] The transferable lesson: the transition between two states of a graphic is where the understanding happens,
  so budget for it.
- [V] Transitions carry no information, so they are used rarely and only for pacing (P16).
- [V] One anchor motif per film: the art director picks one visual idea (flying text for a film about AI writing)
  and builds the whole film on it. Where sources are scarce, a period style can be quoted (protest posters for a
  Black Panther story). Too much polish reads like an ad, not journalism (P8).
- [V] A recurring device can be 2.5D, not 3D: a wall of monitors built with corner pinning, key moments opening
  inside a screen then going full screen, other clips used only as texture, and art-directed CRT jitter (P15).
- [V] Archival documents and timelines are animated so the film doesn't feel like an archive dump; 3D or game-engine
  renders can stage what was never filmed (P12, one former producer's own channel).
- [V] Third-party emulation details (not Vox's own account): lower thirds revealed by a jagged, frame-skipping mask
  with the text a few frames late; a held photo sits on a background cycling two or three textures a second; photos
  and clippings get a slight edge-only chromatic split and blur for a lens feel (P28).

- [V-auto] **From four full-video analyses (case_studies/TRANSCRIPT_STUDY.md and the four watch-based case studies):**
  - **no full-screen chapter cards in any of them.** Chapters are marked by a recurring device instead: a growing
    isometric object that gains a wall per chapter; a running paper timeline with portrait badges; a route map and
    travel milestones; a menu "puzzle" that keeps being reassembled;
  - charts build as the values are named, and highlight bars recolour the key bar;
  - document text gets translucent highlighter wipes;
  - lines are traced directly onto real terrain footage;
  - exploded 3D cutaways show inside an object;
  - clicks and pops are synced to each build.

## 2. The core rule: build on the word [O]

Every element of a graphic arrives at the moment the narration names it, and not before.
- Script the build order from the narration. Underline each noun or number that should trigger an element; each
  becomes a keyframe.
- **Hierarchy of arrival:** the frame (axes, map base, outline) arrives first and quietly. The subject arrives on its
  word. Labels follow within about 6–8 frames. Emphasis (yellow highlight, circle, glow) comes last, on the key word.
- **One new idea per build.** If a chart needs two ideas, it gets two builds with a hold between them, or two shots.
- **Leave on purpose:** elements that the next idea no longer needs fade or push out *before* the new idea arrives,
  not with it.
- **Hold to read:** after a build completes, hold at least about 1 s plus reading time (a 5-word label ≈ 1 s) before
  the next change.

## 3. Technique specs [O] (each one names when to use it)

| Technique | Use when | Spec |
|---|---|---|
| **Kinetic typography** | A definition, a phrase the viewer must remember, a quote | Max ~7 words on screen; the key word in the signal colour; words land on the syllable; never full sentences of narration |
| **Animated map** | Place, route, spread, borders | maps_and_geography.md |
| **Line chart drawn on** | Change over time | Axis first, then the line draws left to right as the narration walks the years; label events on the line, not in a legend |
| **Bar / column chart** | Compare a few quantities | Bars grow from the baseline; sort by value unless order means something; label the values directly |
| **Unit chart** | Share of whole, counts people should feel | One unit = one recognisable thing (a person, a coin, a house); fill in the signal colour as the share is spoken |
| **Big number** | One figure carries the line | The number has a body: a unit, an object or a comparison beside it; count-ups only when the rise itself is the point |
| **Timeline** | Sequence, causation through time | A spine that the camera travels along; one event per beat; past events dim as you move on |
| **Explanatory diagram** | Mechanism, cause and effect | Arrows carry verbs; parts appear in causal order; a cutaway shows inside |
| **Flowchart** | Process with steps or decisions | Left-to-right or top-to-bottom, one step per beat, the active step highlighted |
| **Network graph** | Who connects to whom | Start with one node; add edges as the narration names relationships; a final pull-out shows the whole web |
| **2D illustration / collage** | Abstract ideas, scenes we can't film, history without footage | A consistent drawn or cut-out language for the film; cut-outs move at a stepped frame rate over a smooth camera |
| **3D** | Scale, inside of objects, terrain, space | A camera move that reveals scale (start close, pull back); keep 3D purposeful, never as a stand-in for a flat fact |
| **Split screen** | Compare two things, before/after | Same scale and framing on both sides; a divider in the base colour; labels top-left of each half |
| **Photo animation** | Archive or evidence stills | Gentle push (3–8% over the hold) to the detail the narration names; parallax only when layers are clean |

## 4. Camera grammar [O]

Graphics live under a virtual camera, and its moves must mean something.
- **Push in** = "look at this": move to the detail the narration names. Ease in and out.
- **Pull out** = "now see the whole": context, scale, the system around the detail.
- **Pan / track** = "next": moving along a timeline, a route, a row of items.
- **Still** = "read this": documents and dense evidence hold still so they can be read.
- **Orbit** = "this is a real place in 3D": terrain, buildings, models. Slow (10–20° per shot).
- **Don't** move everything all the time. If every shot drifts, no move points at anything.
- One camera grammar per film, set in `dna.motion_language` (e.g. "slow eased pushes, hard cuts on turns" or
  "locked frames, elements slide in on a grid").

## 5. Layering, masking, parallax [O]

- **Layer order:** background texture → base (map, paper, photo) → data layer → annotation → labels → badge and
  source line. Annotation never covers the evidence it points at.
- **Masking reveals:** wipe-on lines, highlighter sweeps, map borders drawn by a mask following the path, and photos
  revealed through a torn edge. The mask moves at the narration's speed.
- **Parallax:** split a still into 2–4 depth planes only where the cut-out is clean. The far plane moves 20–40% as
  much as the near plane. Never invent a face or fill a hole outside the moved layer (CreatorForge rule).
- **Depth cues for flat graphics:** a soft drop shadow (2–6 px, low opacity) under paper-like elements and a slight
  scale-up on arrival give hierarchy without 3D.

## 6. Texture and frame rate [O]

- Pick the film's texture from its material (dna.texture): paper, newsprint, halftone, grain, clean vector, glass UI.
  Apply it consistently, at low strength, over graphics, not over evidence.
- A stepped frame rate (animating on twos, ~12 fps) reads as handmade and works for cut-outs and collage. Smooth
  24/25/30 fps reads as precise and suits data and 3D. Choose one per film, or a deliberate split: stepped elements
  over a smooth camera.
- Don't copy the studied look's texture. Derive ours from each film's subject (visual_decision_engine.md §2).

## 7. Transitions that carry information [O]

A transition earns its place if it says how two shots relate. Families (pick one per film; vary film to film):

| Family | Says | Example use |
|---|---|---|
| match_cut / graphic_match | "this is the same thing as" | the pill becomes the price bar |
| push_through / zoom_through | "inside this is" | zoom through a document into the map it describes |
| map_fly | "now go here" | globe to city to street |
| morph | "this turned into" | one chart's bars become the next chart's units |
| mask_wipe / paper_tear | "a new era or side" | between periods or between two sides of a dispute |
| whip | "meanwhile, elsewhere" | parallel events |
| dip / hold_black | "stop and feel it" | after a human consequence |
| cut | "next idea" | the default, with a cause |
| j_cut / l_cut | sound leads or trails the picture | a chapter turn led by its ambience |

## 8. Callouts and tracking [O]

- Callouts (circle, arrow, box, underline) are drawn on, as if by hand, at the word. The stroke runs 8–14 frames.
- A label tracks its subject: if the photo pushes in, the label stays pinned to the subject, not to the frame.
- One callout colour per film for "look here" (CreatorForge: the signature yellow), one for "evidence against" (the
  film's accent).
- A source line sits bottom-left in small type on every evidence and data shot (e.g. "Source: <org>, <year>").

## 9. Failure modes (and the fix)

| Failure | Fix |
|---|---|
| Everything animates at once | Build on the word (§2) |
| A counter or number where the subject should be drawn | Draw the subject (the planets, the ships, the people) and attach the number |
| Decorative motion (spinning icons, constant drift) | Remove; give the camera one job per shot |
| Text-heavy frames | Max ~7 words of narration-echo; the rest is said, not shown |
| A transition with no meaning | Replace with a cut, or a family that says the relationship |
| The same chart style every film | The palette, texture and motion language come from the subject |
