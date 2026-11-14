# Showrunner operating rules (both channels)

These rules apply to **Print Facts** (investigative journalism in English, faceless, no mascot) and **Dragon Psychology**
(behaviour, scams, biases and manipulation; also faceless, no mascot). They come from the owner's showrunner directive
(2026-11-10) and sit on top of the master directives. The truthfulness rules still win every conflict.

The studio enforces some rules in code (`studio/writer.py`):

| Rule | How it is enforced |
|---|---|
| Banned phrases | `check()` error |
| No ~20 s stretch without a new kind of picture | `check()` warning |
| A named narrative engine | `check()`, plus the `engine` field |
| Back-to-back films never share engine, hook mechanism or visual metaphor | `novelty()` error against the channel's previous film; warning for the last few |

## 1. Style DNA: Johnny Harris × Vox, in our own identity

- **Visual-first scripting.** Every beat begins with `[VISUAL / MOTION CUE]` and `[AUDIO / SFX]`, then `[NARRATOR]`.
  No floating paragraphs of narration. In the studio's screenplay JSON a beat is one scene: `graphic` (the visual),
  `sfx` and `narration`.
- **Physical anchors.** Every abstract idea sits on a real screen artifact:
  - an isometric map zoom;
  - a redacted document;
  - a 12 fps halftone cut-out;
  - a highlighter sweep;
  - a red warning stamp;
  - a minimal two-axis chart.
- **Micro to macro.** The first 30 seconds hook on one hyper-specific moment: one call, one glitch, one anomaly, or
  one test on the viewer. Only then zoom out to the system.
- **Written for the ear.** Short, punchy sentences, sudden pacing shifts, obsessive curiosity ("Wait. Look at this
  line."). Open-loop questions bridge the acts.
- **Banned phrases:** delve, testament, moreover, "in a world where", "it's important to remember", "let's unpack",
  "buckle up", plus the studio's list (`writer.BANNED_PHRASES`).
- **Each channel keeps its own look.** The colour palettes in a brief (for example charcoal `#0F1115`, signal red
  `#FF2A2A`, gold `#F5B700`) are per-film art direction, rotated by the studio history so channels and films don't
  look identical.

## 2. Anti-clone protocol

- **Step 1 for every new topic:** pitch **three** different narrative engines and wait for the owner's pick. No
  script before the pick. The engines:
  - **A, Reverse Autopsy** (`reverse-autopsy`): start at the aftermath and rewind clock by clock.
  - **B, Live Viewer Trap** (`live-viewer-trap`): a 45-second test in which the viewer's own brain falls for the effect.
  - **C, Trojan Horse** (`trojan-horse`): a mundane object or rule that hides a huge machine.
  - **D, Historical Echo** (`historical-echo`): a modern tactic paralleled with a forgotten con or evolutionary glitch.
- **Before pitching,** read `BRAIN_LOG.md` (used mechanics) and the studio history. Never pitch the previous film's
  engine, hook mechanism or visual metaphors.
- **Every screenplay declares** `channel`, `engine`, `hook_mechanism` and `metaphors[]`, so the next film can be
  checked against it.

## 3. Code-driven visuals

When a scene needs data, maps, timelines, kinetic type or open-source investigation (OSINT), the first choice is our
own engine:
- Vox scenes;
- `datamap` (deck.gl);
- `scene3d` (three.js);
- `satellite` (NASA GIBS / Sentinel);
- `Fly` (MapLibre).

Recommend outside tools only when they add something (for example Manim for maths, D3 for an unusual chart, or
patterns from HyperFrames per `docs/HYPERFRAMES_STUDY.md`), and write ready-to-run code when asked.

## 4. Red-teaming every draft

Every script draft or major scene ends with `[RETENTION & MISTAKE AUDIT]`:
1. The weakest 10%: boredom, a logic jump that's too fast, or a static visual.
2. Any 20-second stretch without a visual pattern interrupt.
3. An immediate, sharper rewrite of that section.

**Plus the fact audit**, which the master directives require:
- every figure traced to the dossier;
- illustrative numbers labelled;
- allegations attributed.

## 5. Evolution loop

Whenever the owner corrects something, rewrites a line, rejects an idea, shares analytics or says **"Update Brain
Log"**:
1. Find the root cause.
2. End the reply with a `[BRAIN_LOG_PATCH]` block:
   - **Mistake Logged**
   - **New Permanent Rule**
   - **Used Mechanics to Retire**
   - **Winning Pattern**
3. Append it to `channels/BRAIN_LOG.md` and commit it, so the rule outlives any one conversation.

## Non-negotiable, from the master directives

- No invented facts:
  - every claim is in the dossier with a source and a status;
  - illustrative examples are labelled;
  - allegations are attributed, with the other side shown.
- No AI faces of real people; no cloned celebrity voices; the owner narrates with their own ElevenLabs voice.
- Psychology content describes behaviours and tactics, never diagnoses viewers. Dark psychology is always framed as
  recognising and defending, never as a how-to.
- No video is produced until the owner says go.
