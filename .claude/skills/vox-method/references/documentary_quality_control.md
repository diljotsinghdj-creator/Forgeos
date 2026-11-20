# Documentary quality control

How a film is judged against professional documentary standards, at the blueprint stage and again at every cut. A
weak area is never waved through: it goes back to the stage that owns it.

Gate: `python3 scripts/qc_check.py qc_scorecard.json`. Every category is scored 1–10 with written evidence. The
critical categories (research depth, accuracy and honesty, information clarity, rights and sourcing) need 9+; all
others need 8+. Anything below the bar is listed in `weak_areas` with the specific revision.

---

## 1. When QC runs

| Stage | What is scored | Who scores |
|---|---|---|
| Blueprint | Every category, from the blueprint and script (graphics, animation, editing and sound scored on their plan) | The producer, then an independent reviewer (a fresh agent with only the blueprint and this file) |
| Rough cut | All categories on the actual cut | Producer + reviewer |
| Final | All categories + technical checks (§4) | Producer + reviewer; then the owner (CreatorForge PRESHOW.md first) |

An independent reviewer matters: the person who made a thing can't see its gaps. Give the reviewer the blueprint and
this file, not your opinion of the film.

## 2. The rubric (what a 6, an 8 and a 10 look like)

| Category | 6: competent | 8: professional | 10: elite |
|---|---|---|---|
| **Research depth** | Secondary sources; key claims sourced | Primary sources for key claims; other side shown | Original document or data work; experts consulted; what's unknown stated |
| **Accuracy and honesty** | No known errors | Every figure has a claim id; badges on anything not plain fact | Uncertainty shown visually; recreations labelled; nothing implied beyond the evidence |
| **Storytelling** | Clear topic and order | One question, a hook in 5 s, chapters with open loops, a turn | Every chapter changes what the viewer thinks; the ending reframes or returns with new meaning |
| **Information clarity** | Understandable with effort | Passes the mute test; one idea per shot; terms shown as defined | A newcomer can retell the mechanism after one watch |
| **Visual explanation** | Visuals relate to the words | Every shot has a job; evidence before explanation; native material | The visuals carry the argument; the swap test fails for every key frame |
| **Graphic design** | Readable | Clear hierarchy, consistent type and colour roles, phone-legible | A look derived from the subject that is unmistakably this film's |
| **Animation** | Things move | Builds on the word, purposeful camera, good easing | Transitions between states are where understanding happens |
| **Editing** | No dead air | Holds within caps; varied rhythm; cuts with a cause | The rhythm tracks the argument: acceleration, turn, release |
| **Narration** | Clear | Written for the ear, good pace, stress on new information | A distinct, curious, trustworthy voice; silences used |
| **Sound design** | Music present | Several cues changing on turns; SFX synced; loudness on target | Sound carries meaning (ambience as evidence, silence as weight) |
| **Audience engagement** | Hook present | Promise paid off; open loops close; no slack stretch | Hard to stop watching; viewers come away wanting to share it |
| **Originality** | Not a copy | Passes the swap test against our last three films | A device or approach no other channel owns |
| **Rights and sourcing** | Assets have sources | Every asset licensed and registered; credits on screen | A companion source list with timestamps; nothing questionable |

## 3. The review procedure

1. Run the machine checks: `blueprint_check.py` (and `--compare` the last films), and CreatorForge's own gates
   for renders.
2. Read the script aloud at speed. Mark stumbles, slack and jargon.
3. Walk the blueprint shot by shot and ask the nine questions (production_workflow.md intro). Mark any shot that
   can't answer one.
4. Do the **mute pass** (picture only) and the **blind pass** (sound only): each should carry the argument alone,
   imperfectly.
5. Do the **swap test** on the hook, the midpoint proof and the payoff frames.
6. Do the **fact pass:** every figure against the dossier; every allegation attributed with the other side; every
   badge present.
7. Do the **retention pass:** mark the weakest 10%, and any 20 s without a new kind of picture.
8. Score the rubric with written evidence; list weak areas with revisions; run `qc_check.py`.
9. Revise, then rescore only the categories touched, plus any that the revision might have affected.

## 4. Technical checks (render stage)

- Resolution and frame rate as specified; `ffprobe` confirms duration and streams.
- Loudness about −14 LUFS integrated, true peak ≤ −1 dBTP.
- No text in the bottom ~12% at chapter markers or in the end-screen zone.
- Captions: accurate, synced, max two lines, ~42 characters a line.
- Frame check: watch every frame at speed and step through any build; fix overlaps, cut-off words and flashes
  (BRAIN_LOG 2026-11-11).
- CreatorForge: PRESHOW.md written and sent before any summary (gate 5).

## 5. Common weak areas and where they go back to

| Weakness | Back to |
|---|---|
| A slack middle | Structure (vox_storytelling_methodology.md §4–5) |
| Generic visuals | Visual identity and decision engine |
| Number soup | Script (one number per sentence) and infographics |
| An unearned ending | Structure: what question did the film actually answer? |
| A thin evidence layer | Research and asset sourcing |
| Sameness with earlier films | DNA (visual_decision_engine.md §6) |
