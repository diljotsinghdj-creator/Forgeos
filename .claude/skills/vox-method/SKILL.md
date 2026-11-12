---
name: vox-method
description: Documentary production method distilled from a study of Vox's publicly observable craft (editorial choices, script architecture, visual language, motion graphics, maps, data graphics, editing, sound, packaging), turned into our own original production system with a visual decision engine and a machine-checked production blueprint. Use this whenever the task is to plan, pitch, research, script, storyboard, visually plan, edit, review or package a documentary, video essay or explainer, for Print Facts, Dragon Psychology or any faceless channel; whenever someone asks for "Vox style", "Vox quality", "Johnny Harris style" or "documentary quality"; whenever a topic needs to be turned into a scene-by-scene production plan; and whenever a Vox video is to be analysed and its lessons added to the knowledge base. Prefer it over generic storyboarding even if the user never says "Vox".
---

# Vox method: elite documentary production, in our own identity

This skill is a production capability, not a style filter. It encodes what a professional explainer-documentary studio
does at every stage, so a researched topic becomes a **production blueprint** that every department can work from.
That blueprint is a scene-by-scene plan of narration, viewer takeaway, visual, motion, text, sound, transition and
hold.

**What it is built from.** A study of Vox's publicly observable craft (references/sources.md and case_studies/), kept
in three labelled layers:
- **[V] verified:** a source states it;
- **[I] interpreted:** an informed inference;
- **[O] ours:** our original technique.

We learn the craft and never copy the product: no Vox logos, branding, footage, music, scripts or finished
compositions, and no claim of affiliation.

## Before anything else

1. **In the CreatorForge repo,** read `references/creatorforge_house_rules.md`. The owner's rules override this skill.
   They include: no video, render, paid narration or image without the owner's say-so; three engines pitched and a
   pick recorded before any script; nothing the owner has already seen gets reused.
2. **Never claim what wasn't done.** A blueprint is a plan; say "planned" until something is rendered and checked.
   Don't describe frames of a video you didn't watch.

## The pipeline: what to read at each stage

| Stage | Do | Read |
|---|---|---|
| 1. Question | One question, a surprising answer, why now; the five story tests | `vox_editorial_methodology.md` |
| 2. Research | Dossier (claim id, source, status) **and** visual leads (archives, data, documents, places) | `vox_editorial_methodology.md` §6, `vox_asset_sourcing.md` §5 |
| 2b. Psychology (Dragon Psychology) | Every psychological claim also gets a **replication status** (robust / mixed / failed / single study); famous classics are checked first | `psychology_of_everything.md` |
| 3. Pitch | Three engines, three hooks, three opening frames; never the last film's; say which engines are blocked and why. **Stop for the pick** | `vox_storytelling_methodology.md` §3–4, `creatorforge_house_rules.md` (engine pool) |
| 4. Structure | Architecture chosen by claim type; chapters with jobs and open loops; the turn at 60–75% | `vox_storytelling_methodology.md` §4–6 |
| 5. Script | Two-column beats (visual first); written for the ear; claim ids on every fact; retention audit | `vox_storytelling_methodology.md`, `vox_narration.md` |
| 6. Visual identity | Subject profile → native material → lead and support → palette from subject → texture, type, motion, transitions, signature device, sound palette; swap test | `visual_decision_engine.md` §2, `vox_visual_language.md` §5 |
| 7. Blueprint | A scene card per shot; `visual_decide.py` for the first pass; `blueprint_check.py` until clean; `render_blueprint.py` | `production_workflow.md`, `visual_decision_engine.md` §3–4 |
| 8. Department detail | Maps, data graphics, motion, editing, sound for the shots that need them | `vox_maps_and_geography.md`, `vox_infographics.md`, `vox_motion_graphics.md`, `vox_documentary_editing.md`, `vox_sound_design.md` |
| 9. QC | Score the rubric with evidence; revise weak areas; `qc_check.py` | `documentary_quality_control.md` |
| 10. Packaging | Titles, thumbnail brief, description with sources, chapters | `vox_thumbnail_and_packaging.md` |

Load only the files the current stage needs. Each reference opens with what the studied craft shows, then gives
actionable rules and failure modes.

## The visual decision engine (the heart of the skill)

Never apply one visual formula. For every film, and then for every line:
1. **Film level:** what is this subject physically made of? Its native material decides the lead technique, the
   palette, the texture and the motion language, rotated against recent films.
2. **Line level:** what must the viewer understand, and what kind of need is it (a place, a quantity, a comparison,
   a mechanism, a real event, a document claim, an abstract idea…)? Rank modes by fit to the need, native to the
   subject, real evidence over explanation, and rotation; then decide and write why, naming the rejected
   alternative.
3. **Three tests on every frame:** the job test (it does work the words can't), the mute test (it carries the fact
   with sound off) and the swap test (it couldn't be dropped into another film unchanged).

Details and the full need → mode table: `references/visual_decision_engine.md`.

## The deliverable: a production blueprint

`blueprint.json` (copy `assets/templates/blueprint.json`) plus `blueprint.md` rendered from it. It holds the film
card (question, answer, engine, pick, hook), the Video DNA, the chapter map, and one scene card per shot with:
- narration, viewer_understands, purpose and claim_ids;
- visual_mode, visual, why_this_visual and alternatives;
- motion, on_screen_text and badge;
- asset_ids or asset_needed;
- sound (music / sfx / ambience / silence), effects, transition_out (family and cause), start and end.

```bash
S=<this skill's directory>
python3 $S/scripts/visual_decide.py beats.json --domain <domains> --avoid <recent leads>   # first-pass ranking
python3 $S/scripts/blueprint_check.py blueprint.json                                       # house rules (CreatorForge)
python3 $S/scripts/blueprint_check.py blueprint.json --profile generic                     # craft rules only
python3 $S/scripts/history_stubs.py --repo <repo> --out compare_stubs                       # recent films to compare with
python3 $S/scripts/blueprint_check.py blueprint.json --compare compare_stubs/*.json         # sameness vs recent films
python3 $S/scripts/render_blueprint.py blueprint.json                                      # blueprint.md + department sheets
python3 $S/scripts/qc_check.py qc_scorecard.json                                           # QC gate
```

Fix every error. Read every warning, and either fix it or write down why it stands. The checker enforces, among
other things:
- pacing caps;
- a pattern interrupt at least every 20 s;
- evidence before explanation (Print Facts);
- stock at most 25% of runtime;
- a mix of at least five visual modes, with no mode over 60% of runtime;
- the banned phrases;
- a claim id for every spoken figure;
- badges on recreations;
- the signature yellow;
- a recorded pick;
- sameness against earlier blueprints.

## Non-negotiables, and why

- **Evidence first, then explanation.** A real document, photo or footage earns trust; the graphic then explains it.
  Every studied category showed the test or evidence leading.
- **Every shot has a job.** Decoration is what turns a documentary into a slideshow.
- **Every fact traces to the dossier.** One invented number costs the channel its credibility. Illustrative numbers
  wear an ILLUSTRATIVE badge.
- **Each film gets its own look from its subject.** Sameness reads as automation to viewers.
- **Sourcing is visible:** a source line on screen and timestamped sources in the description.
- **Licence before use.** Downloadable is not licensed.

## Case studies and continuous learning

- `case_studies/INDEX.md` lists every analysed video, with its evidence basis. `case_studies/PATTERNS.md` holds the
  cross-video syntheses.
- To analyse a new video, follow `references/learning_protocol.md`:
  1. Fill `assets/templates/case_study.md` (thirteen points, labelled [V]/[I]/[O], timestamps only from a transcript
     or chapter list).
  2. Run `python3 scripts/case_study_check.py case_studies/`.
  3. Fold genuinely new lessons into the right reference file.
  4. Add an entry to `references/learning_log.md`.
- The first study pass could not view frames or read full transcripts (`learning_log.md`), so shot-level rules are
  mostly [O]. Where a later session can watch the videos, verifying those rules is the highest-value research.

## Regression tests

`bash tests/run_tests.sh`: a good blueprint passes, a slideshow fails for the right reasons, a clone is caught, and
the renderer and decision ranker work.
