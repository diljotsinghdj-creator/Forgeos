# Production workflow: from research to a production blueprint

This turns a researched topic into a professional production blueprint, which every department works from:
`blueprint.json` (machine-checked) and `blueprint.md` (rendered). It is not a storyboard of pretty frames. For every
scene it answers nine questions:
1. What the narration says.
2. What the viewer must understand.
3. Which visual communicates it best.
4. Whether that is footage, photography, animation or graphics.
5. How it moves.
6. What text appears.
7. What sound goes with it.
8. How it exits.
9. How long it holds.

Contents: 1. Stages and gates · 2. The project folder · 3. Stage by stage · 4. The scene card · 5. Timing ·
6. Department sheets · 7. Revision loops

---

## 1. Stages and gates

| # | Stage | Output | Gate before moving on |
|---|---|---|---|
| 0 | House check | notes on what's been seen | Read MASTER_DIRECTIVES, BRAIN_LOG, SEEN.json (CreatorForge) |
| 1 | Question | `question.md` | One question, a surprising answer, a reason to care now (vox_editorial_methodology.md) |
| 2 | Research | `dossier.md` + `sources.csv` | Every claim has an id, a source and a status |
| 3 | Pitch | three engines | **The owner's pick is recorded** (gate 1). Nothing below starts without it |
| 4 | Structure | chapter map | Each chapter has a job and an open loop (vox_storytelling_methodology.md) |
| 5 | Script | `script.md` | Reads aloud; hook within 5 s; banned phrases absent; every figure has a claim id |
| 6 | Visual identity | `dna` block | Film-level decisions done; swap test against the last three films passed |
| 7 | Blueprint | `blueprint.json` | `blueprint_check.py` passes; `--compare` against recent films passes |
| 8 | Assets | asset register | Every evidence shot has a sourced, licensed asset or a stated need (vox_asset_sourcing.md) |
| 9 | Narration | audio + measured timings | Timings come from real audio; the blueprint is re-timed to them |
| 10 | Graphics, animation, edit, sound | the cut | Only after the owner says "go" |
| 11 | QC | `qc_scorecard.json` | documentary_quality_control.md; every weak area revised |
| 12 | Packaging | `packaging.md` | vox_thumbnail_and_packaging.md |

## 2. The project folder

```
<film-slug>/
  question.md          central question, answer, why now, audience
  dossier.md           claims: id · statement · source · status (verified/reported/estimate/disputed/allegation/opinion)
  sources.csv          source register
  pitch.md             three engines, each with its hook, opening frame and arc; the owner's pick
  script.md            the documentary script, chapter by chapter, with [VISUAL] [AUDIO] [NARRATOR] beats
  blueprint.json       the production blueprint (assets/templates/blueprint.json)
  blueprint.md         rendered with scripts/render_blueprint.py
  assets.csv           asset register: id, scene, source, author, licence, link, date, rights, modifications
  qc_scorecard.json    assets/templates/qc_scorecard.json
  packaging.md         titles, thumbnail brief, description, chapters
```

## 3. Stage by stage

**Stage 1. Question.** Write the question a curious, smart viewer would type into a search bar. Write the one-line
answer with its surprise ("it isn't X, it's Y"). Write why now. If you can't, it's a topic, not a film yet.

**Stage 2. Research.** Build the dossier before the script. Each claim gets an id (c1, c2…), the plainest wording,
the best source (primary first) and a status. Allegations are attributed, and the other side is recorded. Also note
**visual leads**: archives, datasets, footage and documents that could appear on screen. Visual research is part of
research.

**Stage 3. Pitch.** Three engines, never the last film's, each with a different hook mechanism and opening frame. Stop
and wait for the pick.

**Stage 4. Structure.** Build the chapter map from vox_storytelling_methodology.md: hook, the question stated, context
the viewer needs, escalation in steps, the turn, the answer, the implication. Every chapter gets a job, and ends on
an open loop.

**Stage 5. Script.** Write for the ear (vox_narration.md). Write the visual beat first, then the line. Mark every fact
with its claim id. End with the retention and mistake audit: the weakest 10%, any 20 s stretch without a new kind of
picture, and a sharper rewrite.

**Stage 6. Visual identity.** Follow visual_decision_engine.md §2: the subject profile, native material, lead and
support, palette from the subject, texture, typography, motion language, transition family, signature device and
sound palette. Do the swap test.

**Stage 7. Blueprint.** Split the script into shots, one idea per shot. For each, fill a scene card (§4) using
visual_decision_engine.md §3. Run:
```
python3 scripts/visual_decide.py beats.json --domain <domains> --avoid <recent leads>   # first pass
python3 scripts/blueprint_check.py blueprint.json [--compare last.json ...]             # gate
python3 scripts/render_blueprint.py blueprint.json                                       # blueprint.md
```
Fix every error. Read the warnings and fix them or write down why not.

**Stages 8–12** follow the department references. Nothing is drawn, voiced with paid credits or rendered until the
owner says "go" (CreatorForge hard rule).

## 4. The scene card

| Field | What a professional answer looks like |
|---|---|
| narration | The exact words over this shot. One idea. |
| viewer_understands | "That the border was drawn by a committee that never visited", not "context" |
| purpose | hook / inform / context / prove / emotion / turn / payoff / transition |
| claim_ids | Every figure, date and name maps to the dossier |
| visual_mode | One mode from the vocabulary |
| visual | Subject, framing, layers, highlight, colour roles: specific enough to brief an animator |
| why_this_visual | Why it beats the named alternatives for *this* line |
| motion | Build order synced to words; the camera move and its reason |
| on_screen_text | Labels, the key number, the highlight phrase, the source line |
| badge | REPORTED / ALLEGATION / ILLUSTRATIVE / RECREATION… when not plain fact |
| asset_ids / asset_needed | What is in hand, or exactly what must be found and where to look |
| sound | music state, SFX sync points, ambience, silence |
| effects | Named effects (each at most 3 times a film) |
| transition_out | Family and cause |
| start / end | From measured narration; still ≤ 4.5 s, building ≤ 7 s, mean ≤ 5 s |

## 5. Timing

- Before audio exists, estimate at about 2.8 spoken words per second (the measured median of recent Vox explainers,
  case_studies/TRANSCRIPT_STUDY.md), and mark the timings as estimates.
- After narration is recorded, re-time every scene to the real audio. A line that runs over its cap splits into two
  shots; never stretch a shot to fit.
- Leave room: a beat of silence after a reveal (0.5–1.5 s), and a longer breath at chapter turns.

## 6. Department sheets (generated by render_blueprint.py)

- **Asset pull list:** every scene's assets in hand and needed. Sourcing works from this.
- **Music and sound cue sheet:** where each cue enters, changes and drops; SFX sync; silences.
- **Edit list:** in/out/hold per shot and the transition family. The editor's first assembly.

## 7. Revision loops

- A fact-check change rewrites the line, then the scene card, then the timing.
- A QC score below the bar in any category sends the film back to the stage that owns it.
- An owner correction becomes a BRAIN_LOG patch (CreatorForge), and if it's about craft, a learning-log entry here
  (learning_protocol.md).
