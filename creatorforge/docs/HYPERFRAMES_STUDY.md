# What we can learn from HyperFrames

**What was studied:** `heygen-com/hyperframes`, the main branch, cloned on 2026-11-10. Licence: Apache-2.0, so its
code and components may be adapted with attribution. The study covered:
- its main skill and craft guides: motion, look, story, explainer, data, film, review, sound, captions, character;
- its library of about 210 blocks and 240 components.

## Verdict

HyperFrames and CreatorForge are built the same way: HTML pages rendered frame by frame in headless Chromium, then
encoded to MP4. **We keep our engine.** Ours already has the evidence checks, research dossier, director, Vox and
Johnny Harris scenes, 3D, maps, satellite imagery and 420 tests.

What HyperFrames adds is **craft knowledge measured from finished films**, plus some **reference components**. Both
can be adopted without switching engines.

## What we already do (no change needed)

| HyperFrames rule | Ours |
|---|---|
| Rendering is a function of timeline time (seek-safe, no clocks or random) | `window.frame(t)`; seeded randomness |
| Stepped 8–12 fps "stop-motion" animation, quantising time before evaluating | Our 12 fps `tracks` vs per-frame `TICKS` |
| Every claim traces to a source; illustrative numbers are marked | The dossier, the badges, the `writer.check` editorial review |
| Reveal each element when the voice names it | Captions snapped to the narration; motion keyed to cues |
| Real imagery for real places; credit it on screen | `Fly`, `Satellite`, `Photo`, with credits |
| An empty first frame is a fault | `quality.first_frame` |
| Avoid more than 3 s with nothing changing | `quality.freezes` (partly) |

## Worth adopting, by priority

### P1: craft rules for the director and the scene engine

1. **Ease by role**, instead of one ease for everything:
   - arrivals land on a long tail (`expo.out` / `power4.out`);
   - camera moves and colour floods ease both ways (`power2.inOut`);
   - exits and zoom-throughs accelerate (`power3.in`).

   The same `power2.out` at 0.5 s everywhere is what makes a film look generated.
2. **Exits are 40–50% shorter than entrances.** The next element starts when the previous is 30–50% done. Staggers:
   letters 1 frame apart, words 60–120 ms, list items 40–80 ms.
3. **A landed title is dead still.** The motion moves to the next element, the camera or the background. No
   breathing, floating or creeping scale on titles.
4. **Vary title entrances within a film**, never a fade and slide-up every time:
   - per-word blur-in (6 px → 0 in 0.13 s, 0.067 s apart);
   - grey-to-ink per word;
   - a whole-line blur-in;
   - per-letter for names;
   - title behind the subject (we have this);
   - a slot-machine roll on one word.
5. **Reading holds:** a line the viewer must read holds 0.5 s plus 0.3 s a word; the film's last line at least 2 s.
   → Add this check to `writer.check` and the visual QC.
6. **Transitions with a cause**, 3–5 kinds per film, each caused by something on screen:
   - zoom through an object;
   - an object grows into the next world;
   - a colour flood;
   - a whip;
   - an iris from a point;
   - a dip cut (darken about 40% for 3 frames before a hard cut);
   - a blur swap.

   At most a third of the seams are hard cuts. → Extend our `transitions` set with dip cut, iris and object-becomes-world.
7. **Cut at the fastest frame of a move**, matching direction and speed on both sides (velocity-matched cuts).
8. **Shapes of information:** pick the *shape* first, then the picture, so similar lines get different pictures.
   The shapes: a number that lands; **a myth turned over** (wrong idea struck through, right one printed over it);
   before/after; many into few; a network that densifies; one chosen of many; steps; a circled screenshot; a quote
   poster; a chapter card. → Add **"myth turned over"** as a director pattern. It is the signature move for
   Dragon Psychology's re-checked-studies pillar.
9. **Data rules:**
   - one number at a time, the biggest thing on screen;
   - `tabular-nums` so a count-up doesn't jitter;
   - a count-up runs 1.2–1.6 s, then holds;
   - build a chart in reading order (axis, reference line, data, one annotation on the mark);
   - highlight one series and grey the rest;
   - no legends, no pie charts, no KPI-card grids.

### P1: review pass

10. **A harsh review after every render**, ranked P0 (breaks the read), P1 (weakens it), P2 (polish), one line each:
    `t=4.2s · where · problem → exact change · what stays`. Never a score out of 10.
11. **The "pictures alone" test:** with the words covered, do the beat frames still tell the story?
12. **The phone test:** every line meant to be read must be readable at 360 px wide.
13. **Measurable warnings to add to `quality.py`:**
    - `line_unread`: text on screen too briefly to read;
    - `dead_stretch`: more than 3 s with nothing changing (extend `freezes`);
    - `text_below_floor`: text under 2.6% of the frame's short side.

### P2: sound

14. **Few, exact sound effects**, each caused by something on screen: whoosh on cuts, a pop when a number lands, one
    riser into impact per film. Rotate 2–3 takes of a repeated sound.
15. **Place an effect's peak one frame after its picture.** A hit that must land on a beat starts 40–190 ms early.
16. **Music under voice at about 0.14 volume.** True peak at −1 dBTP or below; mix at −16 to −14 LUFS. We target −14
    already; add the true-peak check.

### P2: characters (stickman scenes; the owner dropped the mascot on 2026-11-10)

17. **Acting rules:**
    - mood changes go anticipation → squash → new face → settle; never a snap;
    - offset the parts (head leads, arms follow) and never move both arms or both eyes in unison;
    - contact sells it: feet on the ground, eyes on what they look at.
18. **Hand-drawn "boil":** redraw outlines about 12 times a second with jitter seeded by `floor(t*12)`, so the line
    lives while the character holds still. → Add to our marker strokes.
19. **A rig is parameters over time:** mood changes are keyed states (`[[t0,"normal"],[t1,"scared"]]`) the rig eases
    between.

## Components worth studying for reference (adapt, never mount as-is)

| Component | Use for us |
|---|---|
| `vox-annotate`, `marker-highlight`, `hw-callout-circle`, `hw-underline`, `hw-arrow` | Seek-safe marker strokes: a dash tween from the path's length, explicit endpoints |
| `hw-boil` | Seeded hand-drawn jitter, and a pen-velocity ease for strokes |
| `stop-motion-cadence` | The stepped-time law with squash on landing and 2–3-frame sparkles |
| `strikethrough-replace` | The "myth turned over" shape |
| `count-up`, `number-wheel` | Count-ups with tabular figures |
| `before-after-wipe`, `torn-paper-rip`, `paper-collage-reveal`, `halftone-dissolve` | Transitions in our paper look |
| `cut-the-curve`, `whip-pan-cut`, `match-cut` | Velocity-matched cuts |
| `pendulum-swing` | Basis for the balance-scale scene (Dragon Psychology scam video) |
| `flowchart`, `decline-chart`, `chart-story` | Compare against our flowchart and trend scenes |

Credit HyperFrames (Apache-2.0) in `CREDITS` for any code adapted from it.

## Not adopted

- **Switching to the HyperFrames engine:** it would duplicate ours and drop our evidence and studio layers.
- **HeyGen avatars, voices and the paid "Pro" features:** the user narrates with their own ElevenLabs voice. No AI
  presenters of real people.
- **Telemetry commands**: `npx hyperframes events` and `usage`.
- **"Reverse any video" / style copying:** our rule is to study techniques, never rebuild someone else's finished film.

## Build order

1. Director patterns: "myth turned over"; ease-by-role in the scene engine; the reading-hold check.
2. Review pass in the studio QC, plus the `line_unread`, `dead_stretch` and `text_below_floor` warnings.
3. New transitions: dip cut, iris, object-becomes-world, velocity-matched cut.
4. Hand-drawn boil on markers.
5. The four new scenes for the scam video (counter, two-track brain, isometric staircase, balance scale), built to
   these rules.
