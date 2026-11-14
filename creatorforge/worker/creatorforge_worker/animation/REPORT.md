# Stickman Universe 2.0 - stress tests, before/after, performance, limitations

Every number below was measured on the rendered files (`benchmarks.py`, `perf.py`, `qc.check_video`,
`qc.check_delivery`, `critic.review`). The checks measure technique; they do not measure whether a film is good.
Each film was also watched as dense contact sheets (one frame every 1-5 s), and what that found is listed
under "looked at". Machine: 4 CPU cores, no GPU, so the 3D work uses Blender EEVEE in software.

## The five stress tests

| | Test | Length | Scenes | Motion QC | Continuity | Frames | A/V sync | Subtitles | Sourcing audit |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Political documentary, Hinglish narration | 108.1 s | 8 (7 animated + real footage) | 8/8 clean | 0 issues | 2562/2562 | ok (-0.021 s) | 12, max 18.1 chars/s, 0 issues | 0 unsourced |
| 2 | Cartoon comedy | 72.2 s | 6 | 5/6 clean (1 roll-arm snap) | 0 | 1733/1733 | ok (-0.016 s) | 1 | - |
| 3 | Psychology explainer, narrated | 174.3 s | 16 | 16/16 clean | 0 | 4183/4183 | ok (-0.004 s) | 18, max 16.1 chars/s, 0 issues | 0 unsourced |
| 4 | Cinematic 3D at dusk | TEST4_SECONDS | 1 continuous shot | clean (stick-engine QC before filming) | - | TEST4_FRAMES | no audio | - | - |
| 5a | Universal script: "Flour" (never seen before) | 23.9 s | 5 | 5/5 clean | 0 | exact | ok | 5, 0 issues | - |
| 5b | Universal script: "The Pelican" | 32.3 s | 5 | 5/5 clean | 0 | exact | ok | 5, 0 issues | - |

Each test has: the MP4 and an Android copy (H.264 Main 4.0, AAC 48 kHz), the source document (`doc.json`, which
opens in the editor), a storyboard sheet (one frame per scene), `assets.json` and `report.json` (per-scene QC,
camera passes and framing, critic notes, continuity, sourcing, subtitles, delivery checks, timings).

### Test 1 - political documentary (Hinglish)
How India's election commissioners are chosen, with sources: Constitution Art. 324, *Anoop Baranwal v. Union of
India* (2 Mar 2023), the CEC and ECs Act 2023 s.6/s.7, Scroll.in (18 Feb 2025, real screenshot), real footage
(Print Facts report), real photos credited on screen. The narration is the Hindi espeak-ng voice reading Devanagari
with English terms, and the subtitles are Roman Hinglish. Charts build bar by bar; the balance metaphor is labelled
"Illustration"; both sides are given by two characters, labelled "positions paraphrased". The camera pushes into
the headline and dissolves into the footage.
- **Looked at, and fixed:** before the fixes, the presenter stood still through long lines, the "73 years" line had
  no picture, the subtitles covered the charts' source lines, and the source list flashed by too fast to read.
  After the fixes: the presenter gestures while the voice speaks, the figure becomes a sourced statistic card,
  charts sit above the subtitles, and the list stays 7 s.
- **Still weak:** 108 s, not 90. The voice is a formant synthesiser: clear, but robotic, especially in Hindi.
  The two-sides scene still has one framing edge (Mira at 13.7-16.2 s).

### Test 2 - expressive cartoon comedy
"The Last Samosa": three characters (Raj, Ivy, a dog from the asset library). It has a double take, a polite
standoff in dialogue, a rule of three (reach, "ahem", reach, "AHEM", give up, pratfall), a slow burn, a gift put
back, the dog stealing the samosa, double takes, and a button. Physical comedy uses the stick engine's physics
(trip and roll, take). The world interaction is the table, the samosa on it, the dog and the scenery.
- **Before/after:** see `before_after_dialogue.png`. Before (commit 6ba8420) the camera framed the listener and
  cut the speaker off at the frame edge in 5 of 6 scenes. After: speakers lead the shot, the listener stays in a
  two-shot, and 3 brief (< 0.6 s) edges remain.
- **Still weak:** the roll's arm snap (one measured defect, documented since the first pass). 72 s, not 60. The
  dog's legs are rigid rectangles swinging from the hip.

### Test 3 - psychology explainer
"The Worry Loop": anxiety as a labelled worry cloud with an anxious grade, pacing loops, the body's response,
avoidance, slow breathing (keyed breath poses with a calm grade), naming the worry, weighing fear against facts
(a balance), a friend's comfort and dialogue, a small step, problem vs worry, grounding (looking at the room),
night-time worry, self-kindness, and where to get help. All of it is general and hedged; there are no statistics.
- **Looked at, and fixed:** with the first world-state rules, every sign and the balance were carried into each
  later shot and piled up over Noor's face. The QC and continuity checks did not catch it. Illustrations now stay
  in their scene unless they are listed again.
- **Still weak:** the last third is mostly Noor standing and talking. The critic flags 4 dead-air spots, 1 weak
  pose, 3 staging notes and 2 brief technical defects that the overlap dodge resolves. The night scene is a paper
  tint, not the new lighting.

### Test 4 - cinematic 3D
Four rigged 3D stick characters in a Blender park. Kit walks to a bench and sits. Ash and Ivy play catch with a
real projectile (released from the hand, g = 9.8, bounces, rolls to rest). The long throw sails over Ivy's jump;
Mo walks in, picks it up and throws it back; everyone cheers. Dynamic lighting: the sun sinks and warms, the sky
dims, the lamp posts switch on. The set includes generated library assets extruded into closed meshes (a car and
lamp posts). The camera is at eye level and follows the play.
- **Looked at, and fixed:** the first camera pulled back to a far wide shot for the long throw, with tiny figures
  and half the frame empty lawn. It now follows the action side at eye level.
- **Still weak:** EEVEE in software at 960x408 with 4 anti-aliasing samples, chosen for render time. The stick
  rig's faces are simple. The extruded car is a flat slab, not a modelled car. TEST4_NOTES

### Test 5 - universal script challenge
Two scripts the studio was not written for, straight through the director (`studio.film`), narrated in English.
- **"Flour"** (written after the director was built, run untouched first). That first run was QC-clean, yet
  "bakes" and "sneezes" became "thinks", the cat's jump, knock-over and hide did nothing, "picks up the cat" picked
  up a ball, "window" was read as wind, and nothing was reported. After general fixes (hand-work verbs, reflexes,
  animals jumping onto / knocking over / hiding by things, picking up animals, small objects on furniture,
  unanimated verbs reported): Rosa works at the table, the cat jumps up and knocks the flour off, "Achoo!", the
  cat goes to the chair, and Rosa picks it up by the window.
  - **Reported limitations:** "share" is not animated; flour and window are labelled placeholders.
  - **Not reported (gap):** "white flour covers everything" is not shown, and nothing flags it.
- **"The Pelican"**: a fisherman rows his boat in (rider and vehicle move together), a pelican (the bird
  generator) lands, grabs a fish and flees with it across a cut, Tomas chases it past the lighthouse and the
  market stalls, a girl walks in, the fish drops into her basket, and Tomas laughs and lets her keep it.
  - **Reported limitations:** fish, lighthouse and basket are labelled placeholders.
  - **Still weak:** there is no water under the boat (an environment is a paper tone plus named scenery).

## Before and after (measured)

| What | Before | After |
|---|---|---|
| Unfamiliar script, cast | "Old Tomas" and "Tomas" (two people), no pelican, no girl | Tomas (fisherman), Pelican (animal), Girl |
| Unfamiliar script, places | studio | outdoors throughout |
| Unfamiliar script, actions | explain, explain, explain, drop, give | ride, land, steal, chase, drop (pelican), laugh, give |
| Dialogue framing (comedy, after the refine loop) | 5 of 6 scenes cut a speaker | 3 brief edges (< 0.6 s) |
| Exact frame count | short by 1-9 frames per film (`-shortest` with copied video) | exact on every film |
| Transitions | a 104 s film came out 17 s long, padded audio hiding it | exact; joins use real scene lengths |
| Frozen picture during long narration | 2 x 3.6 s (political) | 0 (camera creeps in on held shots) |
| Critic dead-air flags (psychology) | 30 | 4 |

## Performance (preview 854x480 at 24 fps; final 1920x1080, 2x supersampling, motion blur; 4 CPU cores)
PERF_TABLE

## Engine bugs found by the tests (all fixed, most with regression tests)
- **Repeated throws:** a second throw re-opened the thrower's earlier hold, so the ball snapped back into the hand
  mid-flight.
- **Cached ball flights:** where a ball would land was cached from the ground if it was asked while staging.
- **Lost props:** props the director created were not registered in the world state, and an animal's grip on a
  fish was lost at a cut.
- **Frame and sync errors:** the frame-count and transition-length bugs above, and an ambience bed one sample too
  long that crashed the mix.
- **Crashes:** JSON colours crashed charts; a look-at a point given as a list crashed.
- **Overlays:** illustrations persisted across shots.

## Remaining limitations (honest)
- **Voice:** the narration voice is espeak-ng (offline, robotic). The production pipeline's TTS providers on the
  pod sound far better but are not reachable here.
- **3D:** it renders through Blender EEVEE in software. A GPU would allow higher resolution and samples. Faces in
  3D are simple; the 3D path takes stick-engine scenes and does not yet read production documents directly.
- **Environments:** paper tones, scenery assets, lighting and weather. No painted backgrounds, water or interiors
  with walls.
- **Asset library:** 19 parametric kinds. Anything else is a labelled placeholder.
- **Director:** rule-based reading of English. It handles simple narrative sentences and the verbs it knows, and
  reports the ones it doesn't know. It does not yet report clauses whose subject is an object ("flour covers
  everything").
- **Editor:** a web page served by the worker. It edits steps, poses as numbers and camera keys as numbers;
  there is no drag-on-canvas pose editing or curve editor yet, and no screen in the Android app.
- **Critic:** it measures and flags; it does not judge acting, timing or humour. Those notes are for a person.
- **Length targets:** missed in places (108 s vs 90 s, 72 s vs 60 s).
