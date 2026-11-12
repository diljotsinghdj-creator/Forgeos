# CreatorForge house rules (how this skill plugs into the owner's studio)

This skill teaches the craft. The owner's standing instructions decide what may be done, and when. Where the two
differ, the owner's rules win. The full, current rules are in the repo; read them, because they change:
- `creatorforge/channels/MASTER_DIRECTIVES.md`: the channels, style, anti-clone rules, workflow, hard rules;
- `creatorforge/channels/BRAIN_LOG.md`: lessons from corrections, and retired mechanics;
- `creatorforge/channels/SEEN.json`: everything the owner has already seen;
- `creatorforge/channels/SHOWRUNNER.md`: engines, beats, banned phrases;
- `creatorforge/docs/PRODUCTION_KNOWLEDGE_BASE.md`: the studio engine's techniques and their build status.

## The essentials that change how this skill runs

| Rule | Effect on this skill |
|---|---|
| **No video until the owner says "go"** | Stop at the blueprint. No render, no paid narration, no image generation without the word |
| **No images without asking** | Storyboard frames, style frames and mock-ups count as images. Blueprints are words |
| **ElevenLabs only with permission** | Estimate timings at about 2.6 words/s until real audio is approved |
| **Pitch three engines, wait for the pick** (gate 1) | The blueprint records `pick` with three pitched engines and the owner's words |
| **Seen means used** (gate 2) | Before designing, list what the owner has seen on this topic and in the last three pieces (engine, look, voice, opening shot, hooks, shots) and change all variable elements |
| **Evidence first** (gate 3, Print Facts) | The first real document, photo or footage comes before the first explanatory graphic, or an `evidence_waiver` the owner has been told about |
| **Pacing** (gate 4) | Still ≤ 4.5 s, building ≤ 7 s, last shot +1.5 s, mean ≤ 5 s. The validator's house profile enforces this |
| **Pre-show list** (gate 5) | Any render writes PRESHOW.md and it goes to the owner first |
| **English, faceless, no mascot** | Both channels |
| **Signature yellow #FFDD33** | Highlighter, key numbers, signal, in every film. The film's accent keeps clear of it |
| **Badges** | REPORTED, ALLEGATION, PARTY CLAIM, ILLUSTRATIVE, RECREATION on anything that isn't plain fact |
| **People** | No AI faces of real people, no cartoons over real faces, no private individuals |
| **No flags or emblems as decoration**; platform and party logos only when named | Applies to every frame |
| **Psychology** (Dragon Psychology) | Describe tactics, never diagnose viewers. Dark psychology is framed as recognising and defending |
| **Legal** | Attribute allegations; right of reply before political films; UK defamation law applies |

## The two channels through this skill

- **Print Facts** (investigative documentaries): lead with evidence. Natural leads are documents, satellite, maps,
  archive and official records. Vox clarity explains; investigation proves.
- **Dragon Psychology** (psychology, scams, biases): the lead is illustration and visual metaphor, interface
  recreations, simple re-staged experiments and charts from studies. No character, no mascot. The look carries the
  identity.

## Handing the blueprint to the studio engine

The studio's screenplay format (`creatorforge/worker`) has its own graphic line syntax and its own gates
(`studio/gates.py`). When a blueprint is approved, translate each scene card into a screenplay scene. Where the engine
can't draw a mode the blueprint needs, say so and list it as a build requirement. Don't swap in a generic stand-in
(BRAIN_LOG 2026-11-11).
