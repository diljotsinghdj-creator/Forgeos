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
**191.5 s**, 16 scenes (15 animated plus real footage).
- **Measured:**
  - 15/15 animated scenes motion-clean and 0 continuity issues.
  - Frames 4519/4519; audio/video in sync (-0.021 s).
  - Subtitles at most 18.1 chars/s, 0 issues.
  - Sourcing audit: 0 unsourced lines. Every factual line cites the Constitution, the 2023 judgment, the 2023 Act,
    ECI or Scroll.in.
- **Content:** Hinglish narration throughout: the Hindi voice reads Devanagari with English terms, with Roman
  subtitles. Real media, credited on screen: the ECI photo, the Scroll.in screenshot (pushed into, then dissolving
  into real footage) and the Print Facts clip. Charts build bar by bar; the balance metaphor is labelled; the
  timeline and flow diagrams animate.
  - The petitioners' allegation appears as a sourced evidence chain labelled "Allegation - as reported", never
    acted out.
  - Both sides are given by two characters, labelled "positions paraphrased".
- **Review fixes:**
  - an empty statistic card (now "73 years" with its source);
  - a static presenter (now gestures with the voice);
  - subtitles over the charts' sources;
  - a source list that flashed by.
- **Still weak:**
  - The espeak-ng voice is intelligible but robotic.
  - Diagram labels are small at 480p.
  - In polling day the VOTES box sits partly under the subtitles.
  - One framing edge in the two-views scene.
  - Two rights items must be cleared before publishing: the Scroll.in screenshot and the Print Facts clip
    (`provenance_issues`).

### Film B - "Bus Stop" (original stickman story)
**183.5 s**, 11 scenes, one continuous street from dawn to night.
- **Measured:** 10/11 scenes motion-clean; the one defect is a 38 mm single-frame touchdown skid on Raj's hop off
  the bench. 0 continuity issues; frames 4407/4407; audio/video in sync.
- **Story:** Raj runs for the bus and sits. Ivy's dog Biscuit sends him onto the bench, followed by introductions,
  a rule-of-three phone gag and a game of fetch with a real projectile ball.
  - **The first bus:** it pulls up too far away; they run, it leaves, then a double take and a slow burn.
  - **Rain:** Raj, Ivy, Biscuit and a crowd shelter under the shop awning; Biscuit shakes himself dry over
    everyone; a quiet conversation about the missed interview.
  - **Ending:** the rain stops at dusk, the second bus comes, Raj trips in the rush, Ivy helps him up and the bus
    leaves without them. They decide to walk; night falls.
- **Review fixes:**
  - Raj sat on air beside the bench, then stood inside it;
  - a departed bus reappeared;
  - the bus-stop label floated with no post;
  - the fetch ball whipped backwards out of Ivy's hand (an engine fix: flights start from the hand at release);
  - two bench skids.
- **Still weak:**
  - The camera checker reports characters at the frame edge in 5 multi-character scenes (crowd shots and running).
  - In "Waiting" the phone gag is partly off-frame.
  - The critic flags 10 staging notes and 7 dead-air spots (no narrator; pauses between lines).
  - The dog is a rigid generated asset.

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
**Verdict: not yet ready to publish unattended. Ready for supervised production of short explainers.**

| Criterion | Evidence | Assessment |
|---|---|---|
| Output quality | Three complete films, inspected frame by frame | Coherent stories, correct sourcing, clean motion in almost all scenes. Visual polish is that of a simple stick-figure channel: flat paper sets, a robotic voice, small diagram text, imperfect framing in crowd scenes. Acceptable for an explainer channel's drafts; below a polished animation channel. |
| Production time | Preview: about 0.8x real time for a 72 s film on 4 cores (busy). Final 1080p: about 26 s per film second (busy machine). 3D: about 5 s per 960x408 frame | A 3-minute preview takes about 3 minutes; a 3-minute 1080p final roughly 1-1.5 hours on this CPU. 3D: about 3 hours per 90 s. A GPU pod is needed for 3D at scale. |
| Hardware | 4 cores; peak about 0.4 GB (main) + 0.7 GB (scene renderers) | 2D runs on any modest server. 3D wants a GPU. |
| Reliability | Scene isolation, atomic files, resumable chunks and 3D frames; three worker restarts during this pass lost no finished work | Good: every interrupted render resumed. |
| Editing flexibility | Editor page plus API, undo/redo, versions; incremental re-render of one edited scene | Good for structural edits; weak for hand-animating poses (numeric). |
| Licensing compliance | Provenance tracked per item; rights issues listed per film | The tooling works; the supplied media's rights are not verified, so Film A cannot be published as is. |
| Reproducibility | Deterministic staging, content-hash caches, documents in git | Strong: the same document gives the same film. |
| Long-form | 3-minute films rendered; scene cache and isolation scale linearly | Plausible for 10+ minutes; not demonstrated beyond about 4.5 minutes. |
| Installation | Python + ffmpeg + espeak-ng; Blender in a separate venv for 3D | Moderate; the 3D environment is the hard part. |

## 6. Regression tests
TESTS_LINE

## 7. Known limitations
- **Voice:** espeak-ng only here. The pod's TTS (better voices) is not reachable from this sandbox.
- **Director:** rule-based English parsing, with no language model. Complex sentences and unknown verbs fall back,
  and are reported.
- **Motion:** the touchdown skid (8-38 mm, single frame) and the roll's arm snap remain.
- **Camera:** framing edges in multi-character and crowd scenes even after three director passes.
- **Environments:** paper tones, scenery assets, lighting and weather. No painted backgrounds, water, interiors
  with walls, or depth occlusion (a cat "hides" beside a chair, not behind it).
- **3D:** stick rigs with simple faces; text symbols (BONK, "Got it!") are not drawn in 3D; no audio track on
  Film C; software rendering only.
- **Editor:** no drag posing, no curve editor, no Android screen.
- **Rights:** the user-supplied photos and footage have unverified rights.

## 8. Prioritised roadmap for unresolved defects
1. **Rights:** clear the rights for the Scroll.in screenshot and the Print Facts clip, or replace them (blocks
   publishing Film A).
2. **Narration:** route narration to the pod's TTS provider (the same document fields); the biggest single quality
   gain for Films A and the explainers.
3. **Crowd framing:** make the camera director fit groups (a widest-shot fallback with a minimum on-screen size;
   rule-of-thirds placement) until the framing check passes; add it as a regression test with Film B's crowd
   scenes.
4. **Touchdown skid:** add a vertical-approach key before contact in `jump`/`climb`, and tighten the QC limit back
   once fixed.
5. **Readable diagrams:** minimum font size relative to the output height for diagrams and relations.
6. **3D:** draw symbols (BONK, "Got it!") as camera-facing text; add sound to 3D films from the stick recording
   (sound.events); a GPU render profile.
7. **Environments:** backdrops (painted or photographic) per place; water; walled interiors; depth occlusion
   ("behind").
8. **Editor:** drag-on-canvas posing and keyframe curves; an Android screen for the editor.
9. **Director:** an optional language-model pass for sentence understanding (with the rule engine kept as a
   validator and fallback).
10. **Roll arm snap:** re-key the hand release in `trip_roll`.
