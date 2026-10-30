# Stickman Universe - architectural gap analysis

Inspected the worker and the animation package before building. Status per requirement:

| # | Requirement | Before this pass | What exists / what was missing |
|---|---|---|---|
| 1 | Visual reasoning | Incomplete | `storyboard.py` mapped a few concepts (price card, equal fall, march, ballot box, worry cloud) by keyword. No notion of *representation mode* (literal / metaphor / diagram / satire / reenactment / evidence), no rule against inventing scenes for allegations. |
| 2 | Performance intelligence | Incomplete | Pieces exist: faces (38 expressions, blending, blinks, visemes), body feelings, gaze (`look_at`), reactions (`behaviour.Ensemble`), timing profiles, speech bubbles. Missing: one director that turns a *line of dialogue* into a coordinated performance (anticipation, gesture choice by personality and content, gaze shifts, emotional transitions, listener reactions, no repeated gestures). |
| 3 | Persistent world state | Absent | Each scene was staged from scratch; nothing carried who holds what, where people stand, or what they feel from one scene to the next, and nothing checked continuity. |
| 4 | Timeline / animation editor | Incomplete | `runner.edit_timeline` edits the *video* pipeline (scene order, lengths, transitions, captions). Nothing edits *animation*: poses, keys, curves, camera, expressions, lip sync, assets; no undo/redo or versions. |
| 5 | Asset creation | Absent | Fixed drawing kinds in `props_draw.py`; characters only. No generator, validator, rig check or registry for new buildings, vehicles, animals or objects. |
| 6 | Critic and revision | Incomplete | `qc.py` measures technical motion defects (stretch, skid, floor, teleport, snap, jerk, frozen, overlap, prop jumps, framing) and file defects, and auto-corrects overlaps. Missing: acting/staging/repetition/continuity/camera-distraction/interpretation review, and the split between auto-fixable and "needs a human". |
| 7 | Comedy and satire | Incomplete | A comedy timing profile and physical gags (trip, pain hop, knockback). No comedic *structures*: double take, slow burn, deadpan hold, rule of three, reaction shot, button. |
| 8 | Sound sync | Incomplete | `media/sfx_builtin.py` synthesises edit SFX (whooshes, hits) for the video pipeline. Animation scenes were silent: no footsteps, impacts, catches, bounces, ambience or dialogue cues tied to what the characters do. |
| 9 | Scalability | Incomplete | Chunked, resumable renders and motion blur exist. Missing: scene-level rendering with a content-hash cache, parallel scene rendering, preview vs final quality presets, resource-aware settings. |
| 10 | Acceptance benchmarks | Absent | Stress tests A-G are 15-40 s each. No 60 s / 90 s / 3 min / 5 min productions with storyboard, assets, technical, continuity and limitations reports. |

Build order (foundations first): world state -> visual reasoning -> performance director -> sound sync -> critic ->
comedy -> production document with editing and history -> asset creation -> scene cache and parallel/preview
rendering -> benchmarks.
