# CreatorForge: instructions for every session

Read **`creatorforge/channels/MASTER_DIRECTIVES.md`** first. It holds the owner's standing instructions:
- the two channels (Print Facts and Dragon Psychology);
- the Vox × Johnny Harris style;
- the anti-clone rules;
- the production workflow;
- the hard rules.

Also read **`creatorforge/channels/VOX_PRODUCTION_SYSTEM.md`**: the owner's production system for both channels
(visual archetypes that rotate every episode, the collage vocabulary, paper physics and optical finish, the Artifact
sandbox rules, and the [STYLE_SHIFT] [SIMULATE] [3D_STAGE] [SFX_LOG] [SCRIPT_PLAN] shortcuts).

Then read **`creatorforge/channels/BRAIN_LOG.md`**: lessons from the owner's corrections, and the mechanics already
used.

The essentials, in case nothing else is read:
- **No video is produced until the owner says "go".**
- **Keys and tokens never go in chat;** they live in the pod's environment.
- **Pitch three narrative engines before writing any script.** Never repeat the previous film's engine, hook or
  metaphor.
- **Every fact is in the research dossier with a source and a status.** Allegations are attributed and the other
  side is shown.
- **All videos are in English** (both channels), faceless, no mascot.
- **No images are created without asking the owner first.** ElevenLabs only with the owner's permission.
- **Signature colour:** yellow #FFDD33 in every film (highlighter, key numbers, signal), the owner's pick; each
  film's own accent still changes.

**The owner's five gates** (2026-11-11, enforced by `studio/gates.py` for both channels and every sample with
`"sample_for"`). A gate stops the studio; it is never worked around:
1. **No pick, no script:** pitch three engines and record the owner's pick (`"pick"`) before writing or drawing.
2. **Seen means used:** `creatorforge/channels/SEEN.json` holds everything the owner has seen. Never repeat the last
   piece's engine, look or stand-in voice, an opening shot from the last three, or a hook or shot already shown on the topic.
3. **Evidence first (Print Facts):** a real document, photo or footage comes before the first explanation, or an
   `"evidence_waiver"` the owner has been told about.
4. **Pacing:** a still shot holds at most 4.5 s, a building shot at most 7 s, and the average hold is at most 5 s.
5. **Pre-show list:** every render writes `PRESHOW.md`. Send it to the owner with the video, before any summary of your own.

The studio's memory of past looks and variations lives in `creatorforge/channels/studio_history/`. Never render
channel work with a throwaway history.

**Code:** the worker is in `creatorforge/worker` (tests: `python -m pytest -q`); the Android app is in
`creatorforge/android`.
