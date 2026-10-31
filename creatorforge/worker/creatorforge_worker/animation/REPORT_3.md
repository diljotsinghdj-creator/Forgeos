# Stickman Universe 3.0 - hardening, three films, review, readiness

Everything below was run, rendered and inspected; numbers come from the tools that produced them
(`audit.py`, `production.render` reports, `perf.py`, `qc`, `critic`). Machine: 4 CPU cores, no GPU.

## 1. Verified feature inventory (executable audit)
`python -m creatorforge_worker.animation.audit <dir>` exercises each component and writes `AUDIT.md` with evidence.

| Component | Status | Why (evidence summarised) |
|---|---|---|
| Script-to-animation engine | partial | Unseen scripts stage cleanly with the right cast, places and actions. A third test script lost "up the stairs" and "helps him pick it up". Rule-based English only. |
| 2D stickman renderer | functional | Exact frame counts, audio in sync, requested size and aspect. |
| 2.5D depth | functional | Far lanes are drawn smaller and higher; parallax layers. No camera orbit: that is the 3D path's job. |
| Genuine 3D engine | functional | Blender 5.2 with rigged characters; four 3D films rendered (Demos D and E, the benchmark, Film C). Software EEVEE only here. |
| Rigging and expressions | functional | 2D: 38 expressions with blending and visemes from speech. 3D faces are simple. |
| Locomotion and physics | partial | Stress A, B, E and the 3D scenes are clean. One defect class remains: a single-frame foot skid at a jump's touchdown (8-38 mm) in C, D and Film B, plus the known arm snap in the roll. |
| Scene generation and world building | functional | 19 asset generators validate; objects persist across shots; light and weather render. No painted backgrounds or water. |
| AI animation director | partial | Story-level plan (arc, emotion tracks, pacing, checks). Rule-based, no language model. |
| Timeline and editing | partial | Web editor with undo/redo and versions, driven end to end in a browser. No drag-on-canvas posing, curve editor or Android screen. |
| Documentary integration | partial -> see 5 | Rules hold: allegations are never acted out and unsourced figures are flagged. Provenance is now tracked and reported, but the supplied media's rights are not verified. |
| Rendering and export | functional | Scene cache, incremental re-render, failure isolation, atomic scene files, resumable 3D, exact transitions, Android copy. |

## 2. The three films
FILMS_TABLE

### Film A - "Referee kaun chunta hai?" (Hinglish political documentary)
FILM_A_NOTES

### Film B - "Bus Stop" (original stickman story)
FILM_B_NOTES

### Film C - "The Ball on the Wall" (90-second 3D)
FILM_C_NOTES

## 3. Adversarial review: what a demanding reviewer found, and what happened
Each item was found by watching the rendered film (dense contact sheets), confirmed, fixed in the engine or the
document, and re-rendered; most engine fixes have a regression test.

| Found | Where | Root cause | Fixed |
|---|---|---|---|
| Statistic card renders as an empty box | Film A (and the earlier Test 1) | visual reasoning put the number in a field the card does not draw | yes, plus a test |
| Raj sits on air beside the bench, then stands inside it | Film B | sat at the wrong spot; got up where the standable seat is | yes |
| A bus that left comes back in the next shot | Film B | the scene ended mid-departure, and the world state kept the bus mid-street | yes (the departure completes before the cut) |
| The "BUS" label floats with no post | Film B | a text label used as a sign | replaced with a sign asset |
| The fetched ball whips out of Ivy's hand backwards | Film B | she faced away from her throw | yes, plus an engine fix: flights start from the hand at the release frame |
| Flights cached from staging-time guesses | engine | a move step asked for a position before playback | estimates are never cached or logged |
| A second throw re-opens the thrower's earlier hold | engine | release logic matched any earlier hold | yes, plus a test |
| The ball rolls off the wall top | Film C | landed at 6.7 m/s on a 1.6 m wall | a dead lob onto the wall; the pick-up is staged where the ball really rests (measured) |
| People walk "through" the wall | Film C | one walking line in 2D staging | story restaged so nobody crosses it |
| The 3D camera pulls back to tiny figures | Test 4 / Film C | generic follow camera | shot list with cuts; eye-level framing |
| Presenter static through narration; the critic calls voice-over dead air | Film A | no presenter performance; the critic ignored voice | presenter gestures with the voice; the critic hears voice-over |
| Illustrations pile up over a face | psychology test | world state carried overlays | overlays stay in their scene |
| A film came out 17 s long instead of 104 s | Test 1 | transition offsets drifted past the inputs | joins use real scene lengths |
| Unchanged film "re-render" took 23 s | perf | re-joined and re-encoded everything | the join is cached |

## 4. Performance (measured; marked where the machine was busy)
PERF_TABLE

## 5. Commercial readiness - an honest assessment
READINESS

## 6. Regression tests
TESTS_LINE

## 7. Known limitations
LIMITS

## 8. Prioritised roadmap for unresolved defects
ROADMAP
