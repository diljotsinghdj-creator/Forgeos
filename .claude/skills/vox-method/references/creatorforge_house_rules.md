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
| **ElevenLabs only with permission** | Estimate timings at about 2.8 words/s (measured Vox median) until real audio is approved |
| **Pitch three engines, wait for the pick** (gate 1) | The blueprint records `pick` with three pitched engines and the owner's words |
| **Seen means used** (gate 2) | Before designing, list what the owner has seen on this topic and in the last three pieces (engine, look, voice, opening shot, hooks, shots) and change all variable elements |
| **Evidence first** (gate 3, Print Facts) | The first real document, photo or footage comes before the first explanatory graphic, or an `evidence_waiver` the owner has been told about |
| **Pacing** (gate 4) | Still ≤ 4.5 s, building ≤ 7 s, last shot +1.5 s, mean ≤ 5 s. The validator's house profile enforces this |
| **Pre-show list** (gate 5) | Any render writes PRESHOW.md and it goes to the owner first |
| **English, faceless, no mascot** | Both channels |
| **Signature yellow #FFDD33** | Highlighter, key numbers, signal, in every film. The film's accent keeps clear of it. The yellow highlighter is the channel's signal, **not an "effect"** for the three-uses-per-film limit; list it in `effects` only when used as a distinct device (e.g. a full-frame wipe) |
| **Badges** | REPORTED, ALLEGATION, PARTY CLAIM, ILLUSTRATIVE, RECREATION on anything that isn't plain fact |
| **People** | No AI faces of real people, no cartoons over real faces, no private individuals |
| **No flags or emblems as decoration**; platform and party logos only when named | Applies to every frame |
| **Psychology** (Dragon Psychology) | Describe tactics, never diagnose viewers. Dark psychology is framed as recognising and defending |
| **Legal** | Attribute allegations; right of reply before political films; UK defamation law applies |

## The two channels through this skill

- **Print Facts** (investigative documentaries): lead with evidence. Natural leads are documents, satellite, maps,
  archive and official records. Vox clarity explains; investigation proves.
- **Dragon Psychology** (the psychology of everything, in the owner's words on 2026-11-12; earlier brief: psychology, scams,
  biases). Read `psychology_of_everything.md` for its evidence standard (replication status) and visual language: the lead is illustration and visual metaphor, interface
  recreations, simple re-staged experiments and charts from studies. No character, no mascot. The look carries the
  identity.

## Comparing with recent films

- Build comparison stubs: `python3 scripts/history_stubs.py --repo <repo root> --out compare_stubs`. It uses the
  saved blueprints first, then the studio's variation ledger and SEEN.json, mapped onto this skill's vocabulary
  (approximate). Then run `blueprint_check.py blueprint.json --compare compare_stubs/1_*.json compare_stubs/2_*.json
  compare_stubs/3_*.json`.
- **When a blueprint is shown to the owner,** save a copy to `creatorforge/channels/blueprints/<film-id>.json` and log
  it in SEEN.json as a storyboard (gate 2: seen means used). Later comparisons then run against the real blueprint,
  not an approximation.
- Pacing classes match the studio's gate 4: annotated documents and photos, quote cards and on-screen type are
  *still* shots (4.5 s max). Where this skill and `studio/gates.py` ever disagree, the studio's stricter rule wins.

## When the engine pool runs dry

The owner's four engines, minus the last film's and those the brain log retires for samples, can leave only one or
two engines that are truly free. Tests on 2026-11-12 showed all three films landing on the same engine. When this
happens:
- say so in the pitch, and name which engines are blocked and why;
- still pitch **three of the four house engines** (gate 1 in `studio/gates.py` rejects any other name), with the
  blocked ones honestly flagged;
- a new engine (forensic, controlled comparison, object biography…, from `vox_storytelling_methodology.md` §4) may
  be offered only **in addition to** the three, clearly marked as a suggestion, never as one of them. It joins the
  house list only if the owner says yes (BRAIN_LOG 2026-11-10: Claude's suggestions stay suggestions). Gate 1
  stopped a sample on 2026-11-12 for exactly this.

## Handing the blueprint to the studio engine

The studio's screenplay format (`creatorforge/worker`) has its own graphic line syntax and its own gates
(`studio/gates.py`). When a blueprint is approved, translate each scene card into a screenplay scene. Where the engine
can't draw a mode the blueprint needs, say so and list it as a build requirement. Don't swap in a generic stand-in
(BRAIN_LOG 2026-11-11).

## The owner's Vox production system (2026-11-12, both channels)

Read `creatorforge/channels/VOX_PRODUCTION_SYSTEM.md` before any film, script or Artifact. In this skill's terms:
- **Visual identity:** the owner's archetypes (A–E or a fresh hybrid) are the starting point for `dna`. Name the
  "Episode Visual Theme"; never the last episode's archetype.
- **[STYLE_SHIFT]** = three visual concepts before building, alongside the three engine pitches (gate 1).
- **Scripts:** at least two of the three handles (Geography, Numbers, Time). One reusable master canvas (30-cue
  rule). Focal points on the centre or the thirds for match cuts. ~150 WPM, one beat every 3.5–4.5 s.
- **Motion:** rigid paper physics (4–6 frame overshoot, then still), 12 fps stepped hand-drawn accents, smooth
  camera, and the optical finish (chromatic edge split, print offset, vignette, grain swaps every 8–12 frames).
- **Receipts:** a bottom-left monospace source citation on every data visual.
- **Sound:** [SFX_LOG] under every script or visual (low-passed foley 2 frames early, room tone at −35 dB, an
  analog noise floor in music drops).
- **Artifacts:** fully self-contained vanilla code, with the top-right Play/Replay and Hide UI bar.
- **Where it meets the hard rules:** real people only from real credited photos (no invented likeness); films keep
  #FFDD33 as the signal and real evidence first. See the notes at the end of the system file.
