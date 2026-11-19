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

And read **`creatorforge/channels/PRODUCTION_CONSTITUTION.md`** (2026-11-14): the owner's constitution for every
video. It covers the channel lock, the four Vox and Johnny Harris pillars, a unique **Visual DNA Blueprint** per
video, beat-by-beat skill use, zero-defect QA, the `[ACCESS / SYSTEM BLOCKER]` alert, and the director commands.

Read **`creatorforge/channels/VIDEO_PLAYBOOK.md`** (2026-11-15): the owner's prompts and director commands for a
Vox-style film, step by step, and which tool serves each beat.

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
  **Exception (owner, 2026-11-19): on Dragon Psychology, AI visuals may be used wherever required** (MASTER_DIRECTIVES §8b): labelled as illustration, never a real person's face, never passed off as evidence.
- **Channel palettes (owner, 2026-11-16):**
  - **Print Facts:** cream #F4EFE6, charcoal #1A1A1A, crimson #D93829 and highlighter yellow #F7D046.
  - **Dragon Psychology:** slate #141824, lab-paper #F0F4F8, cobalt #2B6CB0 and amber #ED8936.
  - Each film may add one accent of its own.
- **Scripts:** Vox × Johnny Harris structure and visuals, written in a John Oliver satirical voice (MASTER_DIRECTIVES §10), as a four-column table that writes for motion (§10b).
- **"DJ style"** (owner, 2026-11-19) means the John Oliver script plus Vox × Johnny Harris visuals and editing, together (§10c). It is a style shortcut, not a skip of any gate.

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

**House style for every tool:** before using any skill that makes or changes a picture, 3D scene, chart, map, caption, edit or export (`threejs-*`, `ffmpeg-skill`, `vox-method`, `collage-explainer`, `dataviz`), load the channel's house style: **`.claude/skills/printfacts-style`** for Print Facts, **`.claude/skills/dragonpsych-style`** for Dragon Psychology. Their Vox × Johnny Harris rules override those tools' own defaults. Captions use `printfacts-style/captions.py`.

**Code:** the worker is in `creatorforge/worker` (tests: `python -m pytest -q`); the Android app is in
`creatorforge/android`.
