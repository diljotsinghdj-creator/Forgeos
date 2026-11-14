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

## After this pass

| # | Requirement | Now | Where | Honest limits |
|---|---|---|---|---|
| 1 | Visual reasoning | Built | `visual_reasoning.py` | Rule-based (regex concept library, word-overlap source matching). It refuses rather than guesses: a line whose sources don't share enough words is shown as an unverified allegation (this happened in testing, correctly). It cannot judge whether a source is *reliable* - that stays with the editor. |
| 2 | Performance intelligence | Built | `performance.py`, `behaviour.py` | Gesture choice comes from a fixed table plus personality; no learned acting. The critic flags weak poses but cannot judge appeal. |
| 3 | Persistent world state | Built | `worldstate.py`, `production.plan_states` | Tracks position, facing, posture, holdings, feeling, look, and every prop through continuing shots. It does not track damage or wear (a broken object), or time of day. |
| 4 | Timeline / animation editor | Built (engine + API) | `production.Editor`, `studio_service.py`, `/v1/animation/*` | Every op has undo/redo and saved versions, and edits that break staging are refused. No graphical curve editor or scrubbing UI yet: the Android app has no screen for it. Motion curves are the ease kinds on keys, not free bezier handles. |
| 5 | Asset creation | Built for parametric 2D assets | `asset_lib.py` | 19 generators. Geometry validation, rigs, compatibility, closed-mesh 3D extrusion, registry. A description it can't build becomes a labelled placeholder (lighthouse, fish and basket in the unfamiliar benchmark). Extruded 3D meshes are flat slabs, not modelled volumes. An imported image is flagged as not animation-ready. |
| 6 | Critic and revision | Built | `critic.py`, `qc.refine` | Measures what can be measured; acting quality is flagged, not scored. |
| 7 | Comedy and satire | Built | `comedy.py` | Structures are templates; comic timing is the timing profile, not tuned per gag. Satire is labelled on screen by the visual-reasoning layer. |
| 8 | Sound sync | Built | `sound.py` | Effects are synthesised (no recorded foley library). Dialogue is babble syllables timed to the bubbles: no TTS voice in this sandbox (the pod's TTS provider does narration in the real pipeline). |
| 9 | Scalability | Built | `production.render`, `scene2d.render` | Scene cache by content hash (the second render of an unchanged film takes 0 s), parallel scene processes, preview/final presets, chunked resumable renders, exact frame counts. The 3D path renders EEVEE in software here (about 5 s per 960x408 frame); a GPU pod is far faster. |
| 10 | Acceptance benchmarks | Run | `benchmarks.py`, `bench3d.py`, `REPORT.md` | See REPORT.md: measured results and what is still weak, per benchmark. |
