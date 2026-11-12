# Complete mixed-media Vox production system (owner, 2026-11-12, both channels)

The owner's standing system for **Print Facts and Dragon Psychology**, given on 2026-11-12. It replaces the earlier
"Master Vox motion and sandbox system" of the same day. The master text below is the owner's final and most complete
version, verbatim. The section after it keeps the details that appear only in the earlier versions sent in the same
message. Where this system meets an older rule, see the notes at the end.

---

## 1. Sandbox and security rules (strict, never violate)

- ZERO EXTERNAL NETWORK CALLS IN ARTIFACTS: Never use fetch(), XMLHttpRequest, WebSockets, or external API URLs inside generated Artifacts. Hardcode all numbers, study citations, and datasets directly inside the script.
- ZERO EXTERNAL CDNS OR FONTS: Never include <script src="https://...">, <link href="https://fonts.googleapis.com/...">, or external JS/CSS libraries. Write 100% self-contained vanilla HTML, CSS, and JavaScript using native system font stacks.
- ZERO REMOTE IMAGES: Never use <img src="https://..."> URLs. Draw all maps, portraits, monuments, silhouettes, icons, arrows, torn-paper edges, masking tape, and grain textures using pure inline <svg> or CSS gradients/data-URIs.
- SAFE STATE: Keep all state in JS variables. Never use document.cookie or blocked auto-downloads.

## 2. Episode-to-episode visual variation engine (no two videos alike)

Every new video, script, or Artifact MUST adopt a distinct visual identity, typographic pairing, and layout metaphor tailored to the topic—never recycle the exact same look back-to-back. Rotate across these archetypes (or invent a fresh hybrid) and state the chosen "Episode Visual Theme" at the top of every response:
- ARCHETYPE A [CLASSIC EDITORIAL PAPER]: Warm cream paper (#F4F1EA), charcoal ink (#1C1C1C), Vox yellow multiply highlighter (#F4D03F), heavy Georgia serif headlines + monospace citations. Best for: Behavioral psychology & social experiments.
- ARCHETYPE B [DARK INTELLIGENCE / GEOPOLITICS]: Deep midnight slate (#14181F), crisp bone text (#EDEAE2), radar cyan (#38BDF8) + tactical crimson (#EF4444), condensed bold sans-serif headers + technical monospace coordinates, glowing topographic contours & radar sweeps. Best for: World politics, espionage, conflict & power dynamics.
- ARCHETYPE C [DECLASSIFIED ARCHIVE / COLD WAR]: Aged manila folder (#E5DEC9), typewriter courier ink (#22201E), stamped red ink (#B91C1C) + carbon-copy blue (#1D4ED8), Courier headers, peeling redaction bars, and staple/coffee-ring artifacts. Best for: History, cover-ups & historical turning points.
- ARCHETYPE D [SWISS DATA / MODERN TECH]: Stark gallery off-white (#F8F9FA), pure architectural black (#0F172A), international signal orange (#F97316) + cobalt (#2563EB), clean Helvetica/geometric sans typography, strict grid-line animations, and isometric vector diagrams. Best for: Economics, AI, algorithms & modern systems.
- ARCHETYPE E [NOIR / COGNITIVE SHADOW]: Textured warm charcoal (#1C1917), muted parchment (#D6D3D1), amber spotlight (#F59E0B) + dusty rose (#E11D48), high-contrast italic serif pull-quotes, halftone duotone cutouts, and spotlight vignette reveals. Best for: Dark psychology, manipulation, media & subconscious bias.

## 3. Iconic mixed-media collage and object vocabulary

Combine multiple physical print textures and bespoke editorial props in every scene:
- SCISSOR-CUT PORTRAITS & OFFSET BACKINGS: Render public figures as high-contrast halftone SVG/cutout silhouettes wrapped in an irregular 6-12px cream paper scissor border (#F4F1EA), paired with an offset solid accent backing (#F4D03F or #D9534F shifted 8px down/right) and 12fps head-bob animation for audio quotes.
- ANONYMOUS / BLIND SILHOUETTES: Render unnamed subjects as construction-paper silhouettes (#1C1C1C or #7A7770) or halftone portraits with torn black/yellow redaction tape across the eyes.
- HINGED POP-UP MONUMENTS & X-RAY BLUEPRINTS: Anchor landmarks flat at their base horizon to flip upright like a pop-up book (rotateX 90deg -> -4deg -> 0deg), or wipe away outer walls to reveal architectural blueprint cross-sections underneath.
- WAVEFORM & WORD-BY-WORD TRANSCRIPT CARDS: For spoken audio clips, pair a spinning cassette/reel-to-reel SVG and live waveform bar with a paper transcript card where a #F4D03F multiply highlight jumps word-by-word.
- DETECTIVE BOARDS, STATIONERY & RUBBER STAMPS: Connect tilted index cards using translucent masking-tape corner strips, metallic pushpins, taut dashed red-string lines, rolling slot-machine odometers, tear-off calendar pages, split-screen newspaper mastheads, and slamming distressed ink stamps (CLASSIFIED / DENIED / YEAR).

## 4. Rigid paper physics and filmed optical finish

- Stage Spec: Responsive 16:9 (1920x1080 / 1280x720) stage with warm directional desk shadows (rgba(45, 38, 25, 0.22)).
- Rigid Paper Physics: Elements move like stiff cardboard—entering with a 4-6 frame overshoot pop (0 -> 1.03 -> 1) or slide, then locking completely still. Apply 12fps stepped motion (steps(2)) to hand-drawn SVG arrows, circles, and underlines while keeping camera zooms at smooth 24/60fps.
- Optical Lens Realism: Apply subtle micro-chromatic aberration edge split (1px channel offset near frame edges), slight 2px print-registration color offset, soft radial vignette, and cycling multi-frame background paper/grunge texture swaps (every 8-12 frames).
- Jagged Masks & Receipts: Reveal lower-thirds via irregular stepped clip-path increments, trim labels 3-4 frames early, and always include a bottom-left monospace citation ("Source: Study / Archive, Year").
- Recording Controls: Every Artifact must include a top-right floating control bar with "Play / Replay" and "Hide UI (Clean Screen)" buttons (plus Spacebar replay shortcut).

## 5. Script architecture and director shortcut commands

- Pre-Production Rules: Frame every script around at least two of three handles (Geography, Numbers, Time). Consolidate beats onto one reusable Master Canvas (30-Cue Rule) and align focal points on center/rule-of-thirds anchors for B-roll match-cuts.
- [STYLE_SHIFT]: Pitch 3 distinct visual, typographic, and collage concepts for the topic before generating code.
- [SIMULATE]: Build an interactive 10-second first-person "Viewer Brain Trap" experiment tailored to the episode's archetype that tricks the viewer live first, then reveals the psychological mechanism.
- [3D_STAGE]: Stack 3 CSS 3D perspective layers (perspective: 1200px; background at translateZ(-200px), mid-ground collage at translateZ(0px), foreground cutout/arrow at translateZ(80px)) with virtual camera dolly and rack-focus blur.
- [SFX_LOG]: Output a timestamped Foley, Room-Tone & Music Cue table below any visual or script (low-passed <800Hz foley synced -2 frames early, stereo office/projector room-tone at -35dB, and analog vinyl noise floor during music dropouts).
- [SCRIPT_PLAN]: Build a 30-cue visual skeleton script mapping spoken lines (~150 WPM, 1 visual beat every 3.5-4.5s) to reusable master canvases, match-cut focal points, and DIY overhead desk prop cues.

---

## Also in the owner's message (earlier versions, details not repeated above)

- **Brand palette:** Canvas #F4F1EA, Card #E8E2D5, Ink #1C1C1C (never pure black), Slate #7A7770, Accent Gold / Vox Yellow #F4D03F (always mix-blend-mode: multiply), Alert Coral #D9534F, Psych Teal #2E86AB.
- **EXPORT_SPEC:** 1920x1080 (Full HD 16:9), 60fps smooth camera moves, 12fps stepped hand-drawn overlays.
- **Jagged mask reveals:** reveal lower-third banners with irregular, stepped polygon/clip-path increments (every 2-3 frames).
- **[SFX_LOG] detail:** low-passed <800Hz marker/paper foley synced -2 frames early, rotary/shutter ticks, stereo office/projector room-tone beds at -35dB, and vinyl crackle/analog noise floor during music dropouts.
- **Fonts in Artifacts:** system editorial stacks (Georgia, 'Times New Roman', -apple-system, 'SF Mono', Menlo, Consolas, 'Courier New', monospace).
- **Vox visual defaults when nothing else is asked:** 1280x720 stage, paper #F4F1EA, ink #1C1C1C, yellow #F4D03F (multiply), coral #D9534F, 12 fps stepped SVG accents, the top-right Play/Replay + Hide UI bar.

---

## Notes where this meets earlier rules (Claude's, for the owner to confirm)

These keep the owner's earlier hard rules standing until the owner says otherwise (MASTER_DIRECTIVES order:
truthfulness and safety first).

1. **Sandbox rules apply to Artifacts.** Rendered films keep real evidence (archive photos, documents, footage) first,
   as gate 3 requires. Drawn SVG maps and props are for Artifacts and for explanation shots.
2. **Real people:** scissor-cut portraits of public figures are made from real, credited photographs turned halftone,
   never an invented or AI likeness (hard rule). The 12 fps head-bob plays only under that person's own real audio,
   and is never used to put words in their mouth. Unnamed private people stay as silhouettes, or with their eyes taped.
3. **Yellow:** films keep the signature #FFDD33 (owner, 2026-11-11). Artifacts use #F4D03F. Archetypes B to E bring
   their own accents. In a film the signal stays #FFDD33 and the archetype supplies the accent.
4. **Narration speed:** script plans use the owner's ~150 WPM. The measured Vox median of ~167 WPM
   (vox-method TRANSCRIPT_STUDY) is a reference only.
5. **"Episode Visual Theme" at the top of every response** applies to responses that produce a video, script or
   Artifact.

## What the studio does with this system (built 2026-11-12)

- **Archetypes:** the art direction gives every film one of A–E as its "Episode Visual Theme". It fits the genre
  (Dragon Psychology counts as psychology), is never the last film's, and the one used longest ago goes first. The
  owner can pick one with `"art": {"archetype": "C"}` in the screenplay. It is written at the top of art_direction.md,
  in PRESHOW.md and in the studio history. B and E are dark in this system; the film renderer draws ink on light
  paper, so films use a light variant of their palette until it has a dark-ink mode (PRESHOW says so). The film's
  accent hue still comes from the subject (variation plan); #FFDD33 stays the signal.
- **Optical finish:** every studio film gets a 1 px colour-plate offset, a soft radial vignette, and paper grain
  swapped every 10 frames. The chromatic split is across the whole frame, not only near the edges.
- **[SFX_LOG]:** every render writes SFX_LOG.md next to PRESHOW.md, and the mix follows it: foley low-passed at
  800 Hz and 2 frames early, a stereo room tone at −35 dB under everything, and an analog noise floor at −42 dB where
  the music drops out.
- **Not built yet:** redaction tape, the waveform transcript card with word-by-word highlight, pop-up monuments and
  the CSS 3D stage in films. Stamps, red-string boards, halftone cut-outs from real photos and torn paper already exist.
