---
name: dragonpsych-style
description: The house style for Dragon Psychology, the channel on the psychology of everything (biases, behaviour, scams, studies), in the Vox x Johnny Harris grammar. Load it before using any skill that makes or changes a picture, a 3D or physics scene, a diagram, a chart, a caption, an edit or an export for a Dragon Psychology video or Short (threejs-*, ffmpeg-skill, vox-method, collage-explainer, dataviz, physics or drawing tools), and whenever someone says "[DRAGONPSYCH]", "Dragon Psychology style" or "on brand" for that channel. It overrides those tools' own defaults where they differ.
---

# Dragon Psychology house style (Vox x Johnny Harris, for the mind)

Every other skill is a tool; this file decides how a Dragon Psychology video looks and sounds. Shared craft
(grain, 12 fps steps, captions, loudness, pacing, the seven-point test) is the same as `printfacts-style`; read that
file for those, then apply the differences below. The owner's hard rules (CLAUDE.md, MASTER_DIRECTIVES) win over both.

## What makes it Dragon Psychology, not Print Facts
- **Subject:** the hidden mental mechanics of everyday life. The evidence is **the study**, not the archive document.
- **The promise: "we check the science."**
  - Every claim is shown on screen with its study card: authors, year, journal and sample size.
  - Studies that failed to replicate say so on screen, with a REPLICATION stamp.
  - "The study everyone quotes is wrong" is a recurring hook.
- **Palette (owner, 2026-11-16):**
  - clinical slate #141824;
  - lab-paper off-white #F0F4F8;
  - electric cobalt #2B6CB0;
  - experimental amber/coral **#ED8936**, the signal colour for key numbers, the highlighter and the current caption word.

  There's no yellow on this channel. Real photos go black and white or cobalt duotone.
- **Voice:** a John Oliver satirical layer inside the documentary structure. The brain is treated as an incompetent middle manager making terrible decisions. Targets are irrationality, pop-psychology scams, wellness grifts and self-sabotaging biases. The comedy visuals follow MASTER_DIRECTIVES §10.
- **Motifs:** peer-reviewed study PDFs, experimental diagrams, brain-region schematics, behavioural charts, and vintage psychology-textbook cut-outs.
- **No mascot, faceless.** People appear as plain stick figures or black-and-white cut-out silhouettes.
  - Real people only in credited photos, framed neutrally.
  - A negative trait (manipulator, liar) is never put on a real, identifiable person.
- **Narrator:** the channel's own voice. Wise, a little dry, warm, never preachy. Speaks to "you", and as "I" when investigating a study.

## The Vox x Johnny Harris grammar, for the mind
- **Vox (explain):**
  - one mental model per beat, built as it's named;
  - a big number in amber #ED8936;
  - real-object charts;
  - highlighter sweeps over the key line of a paper.
- **Johnny Harris (prove):**
  - the **study desk**: printed papers, abstracts highlighted, sticky notes, red marker on the result table;
  - **experiment reconstructions** with stick figures or real physics (the Galton board, scales, dominoes);
  - "I went back to the original paper…" as the discovery beat;
  - following the evidence, including where it fails.
- **Signature devices:**
  - perspective split screens (what you think versus what happens);
  - framing diagrams;
  - perceptual illusions the viewer experiences (`[SIMULATE]`);
  - human-scale comparisons;
  - the brain-as-machine cutaway (labelled simplified);
  - physics metaphors for biases (loss-aversion scale, bottleneck, sand pile).
- **Logo:** none yet. Dragon Psychology has no logo until the owner designs or picks one. Don't put Print Facts' logo D on Dragon Psychology work.

## How each tool skill is used here
| Skill | Use it for | Dragon Psychology overrides |
|---|---|---|
| `threejs-*` (r186) | brain cutaways, physics metaphors, illusion scenes | The channel palette only; the subject in amber, structure in cobalt. Paper-grain overlay. Labelled "simplified" or "metaphor, not anatomy". |
| physics (Rapier) | biases as mechanisms | The block weights or ratios shown come from the study (e.g. λ ≈ 2.25), and the frame says so. |
| `ffmpeg-skill` | cuts, 9:16 Shorts, loudness | Same as printfacts-style: −14 LUFS, house captions via `printfacts-style/captions.py`. |
| `vox-method` | the production blueprint | Its Visual DNA names the study desk and the experiment device. |
| `collage-explainer` | collage scenes | Real photos in black and white only, never of identifiable people as the "bad" example. **AI image and video models are allowed wherever required** (owner, 2026-11-19; MASTER_DIRECTIVES §8b): labelled ILLUSTRATION, logged with model and prompt, never a real person's face, never passed off as evidence. |
| `dataviz` | effect sizes and replication results | Show the effect size with its uncertainty where the paper gives it. Original vs replication side by side. Bars from zero. |

## Never
- Pop-psychology claims without a study card.
- Diagnosing the viewer or anyone else, or medical advice. Say "talk to a professional" where it matters.
- Manipulation tactics framed as how-to. Always frame them as how to spot and resist them.
- Mocking marks on real faces, or AI faces.
- Rainbow colours or emoji.

## Writing the script for motion (owner, 2026-11-17)
These rules add to the voice (MASTER_DIRECTIVES §10). They don't replace it. Every script is written so that the narration drives
the camera.

1. **Format:** every script is a four-column table:
   `| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |`
2. **Point at the screen (deictic writing):** write as if a finger is tracing the frame. Use phrases like "Look closely at…",
   "Follow this line…" and "Right here, in the corner…". Never an abstract essay.
3. **The zoom-out hook (first 30–45 s):** open on one tangible detail, such as a border kink, an object or one sentence in a
   document. Hold the mystery, then pull out to the stakes.
4. **The micro-loop (each ~30 s block):** artifact (the map, photo or document) → anomaly (highlight what's strange) →
   curiosity gap (ask why) → spatial pivot (the camera moves to the next clue).
5. **Cadence:** alternate 4–7-word punchlines, for impact freezes and highlighter sweeps, with 15–20-word explanations, for slow
   pans and routes drawing on. The John Oliver line ("fact → receipt → simile → snap back") sits inside this rhythm, and the snap
   back is the short line.
6. **No clunky transitions:** never "Now let's look at", "Secondly" or "In conclusion". Bridge with cause: "But there was one
   problem…", "And that's when everything shifted…".
7. **Camera physics on every row:**
   - the move (`slow push-in 1.0× → 1.4×`, `smooth pan east`, `whip-pan to the timeline`);
   - the tactile action (`highlighter sweep`, `dashed route draws at constant speed`, `paper cut-out drops in, 12-frame ease-out`);
   - `[HOLD 0.6s]` after every major reveal.
8. **The tabletop is the backbone:** keep the base canvas (the desk, paper or map) on screen and slide clippings, photos and
   callouts onto it with drop shadows. Don't hard-cut to unrelated B-roll.
   - **The one exception is comedy:** a 1-frame smash-zoom or a hard music cut before a punchline is a deliberate beat.
   - **The canvas changes per film** (gate 2, SEEN.json); the continuity rule applies within a film.
9. **Colour:** the channel palette stays.
   - **Signal colour:** one per moment: amber #ED8936. No yellow.
   - **Background:** slate #141824 or lab-paper #F0F4F8, with cobalt #2B6CB0 for structure.

## "DJ style" (owner, 2026-11-19)
When the owner says **"DJ style"**, use the John Oliver script (MASTER_DIRECTIVES §10, written for motion as in §10b) **and** the
Vox × Johnny Harris visuals and editing in this house style: animated maps, motion graphics, archival overlays, kinetic
typography. It's a style shortcut. Every gate still applies, and it doesn't choose the voice.
