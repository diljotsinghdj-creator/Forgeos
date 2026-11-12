# The visual decision engine

How a film chooses what goes on screen: first for the whole film (its visual identity), then for every line (its shot).
The goal is the opposite of a template. Two films on different subjects should share a standard of craft and almost
nothing else on screen.

Contents: 1. The principle · 2. Film-level decisions (subject profile → DNA) · 3. Line-level decisions (need → mode) ·
4. The vocabulary of visual modes · 5. Domain starting points · 6. Rotation and sameness · 7. Worked contrasts ·
8. When the engine says no

---

## 1. The principle

**Show the viewer the thing itself, then explain it.** The camera goes to the subject's own material before it goes to
a graphic about the subject. A border dispute is made of terrain, fences, treaties and satellite passes. A price shock
is made of receipts, shelves and price series. A virus is made of microscopy, case curves and hospital corridors. The
first question for any film is therefore not "what template?" but **"what is this subject physically made of, and
what of it can we put in front of the viewer?"** That answer is the film's *native material*, and it drives everything
below.

Three tests every visual must pass (they come from the studied craft and from our own gates):
1. **Job test.** It does one job the narration can't do alone: locate, measure, compare, prove, sequence, reveal a
   mechanism, or make the viewer feel the stakes. Decoration fails.
2. **Mute test.** With the sound off, the frame still carries the key fact of the line (the number, the place, the
   name, the direction of change).
3. **Swap test.** If this frame could be dropped into a different film on a different subject unchanged, it is too
   generic. Make it specific, or cut it.

## 2. Film-level decisions: from subject profile to Video DNA

Do these in order, before any scene is planned. Record them in `blueprint.json` (`subject_profile`, `dna`).

1. **Name the domains** (one to three): geography, economics, history, technology, science, politics, culture,
   psychology, human-interest, investigative. Most strong films are hybrids, such as history plus geography or
   economics plus human-interest.
2. **Name the native material:** the five to ten physical things the film can show. Write them as nouns ("1950s
   shipping manifests", "the canal's lock gates", "a phone's lock screen", "the price board at a fuel station").
3. **Name the proof types available:** archives, documents, datasets, satellite passes, footage, first-person
   testimony. The lead technique must come from what can actually be proven on screen.
4. **Pick a lead technique and one support technique** (from §4). The lead is the film's largest single mode by
   screen time (in a 12–15-mode documentary that is typically 18–30%), and lead plus support together fill 30% or
   more. The support carries the counterpoint: evidence against explanation, human against system. The checker
   warns when the declared lead isn't among the top two modes, or when lead plus support fall under 30%. These
   numbers were recalibrated after the first tests, where well-mixed films put their lead at 19–26%. Under
   CreatorForge rules neither may be the lead of the last two films (`studio_history`, `SEEN.json`).
5. **Take the palette from the subject:** sample the hues of the native material (the canal's oxidised green, the
   ledger paper's buff, the warning-label orange). Assign roles: base, accent, signal. On CreatorForge the signal is
   always #FFDD33. The accent sits at least 120° round the wheel from the last film's.
   **Don't default to the complement of the last film.** The 120° rule only excludes hues; it doesn't choose one.
   Tests on 2026-11-12 showed three unrelated films all landing on green, opposite the previous film's magenta.
   Instead:
   1. List three candidate accent hues, each sampled from a different part of the native material (the object, the
      place, the document, the warning).
   2. Drop any within 120° of the last film or 60° of the two before.
   3. Of the rest, pick the one farthest from all three recent films. Write the three candidates and the reason for
      the pick in `palette.from_subject`.
6. **Set the texture and typography treatment** by the material. Archival subjects suit paper, halftone and
   typewriter. Data subjects suit clean grids and tabular figures. Science suits soft light and scientific plates.
   Interfaces suit pixel-true UI.
7. **Set the motion language:** tempo (long holds for evidence, fast builds for data), camera grammar (push to point,
   pull for context, still to let a document be read) and one transition family with a cause.
8. **Choose the signature device:** one recurring visual idea that belongs to this film only, such as a water-level
   bar, a ledger line that keeps a running total, or a map pin that never leaves the corner. It returns at every
   chapter turn. Prefer it to full-screen chapter cards: none of the four Vox films analysed frame by frame
   used chapter cards. Each marked chapters with a recurring device (a growing object, a running timeline, a route
   map, a reassembled puzzle) (case_studies, 2026-11-12).
9. **Sound palette:** more than one music cue (a change of cue marks a turn), an SFX family matched to the material
   (paper, metal, UI clicks, ambient field recordings), and planned silences.
10. **Swap test at film level.** Sketch three key frames in words (hook, the midpoint proof, the payoff). Compare them
    with the last three films' key frames. If any could be swapped, redesign before scene planning.

## 3. Line-level decisions: from need to mode

For every narration line:

1. **Write what the viewer must understand** (`viewer_understands`), in one sentence and in viewer terms.
2. **Classify the line's need.** Use the list in `scripts/visual_decide.py`: specific_place, route_or_movement,
   scale_or_size, single_number, comparison, change_over_time, share_of_whole, geographic_distribution,
   sequence_of_events, causal_mechanism, system_or_network, institution, physical_process, invisible_process,
   real_person, real_event, document_claim, quote, abstract_concept, human_consequence, interface_behaviour,
   historical_moment, hypothetical, definition, sound_or_music, emotional_beat.
3. **Rank the candidate modes.** Run `python3 scripts/visual_decide.py beats.json --domain <d...> --avoid <recent
   leads>`. The ranking applies four pressures:
   - **fit to the need:** a share-of-whole wants a unit chart, not a big number;
   - **native to the subject:** domain lift;
   - **evidence over explanation:** real material for this exact line wins when it exists;
   - **rotation:** the previous shot's mode and recent films' leads are penalised.
4. **Decide, and write the reason** in `why_this_visual`, naming at least one rejected alternative. You may overrule
   the script; the reason is what matters.
5. **Specify the frame:** subject, framing, layers, what is highlighted, the colour roles, and the text on screen.
6. **Specify the motion:** what builds, in the order the narration names it (each element arrives on its word), and
   what the camera does and why (push points, pull gives context, still lets evidence be read).
7. **Specify the sound:** the music state (enter, continue, drop, change), sync SFX on builds, ambience, silence.
8. **Specify the exit:** the transition family, and the cause of the cut (a new idea, a turn, a match, a time jump).
9. **Set the hold** from the measured narration. A still frame at most 4.5 s, a building frame at most 7 s
   (CreatorForge gate 4). Split longer lines into several shots.

### Need → mode defaults (best first)

| Need | Defaults | Notes |
|---|---|---|
| Specific place | globe dive → satellite → location footage → archival photo | Start wide enough to orient, end tight enough to recognise |
| Route or movement | animated route on a map → satellite → process animation | Draw the line at the speed of the narration |
| Scale or size | scale comparison (object beside object) → 3D model → unit chart | Compare with something the viewer has held or walked |
| Single number | big number with a unit made physical → unit chart → annotated photo | A number alone is weak; give it a body |
| Comparison | split screen → bar chart → unit chart | Same scale on both sides, always |
| Change over time | line chart drawn left to right → timeline → satellite before/after | Draw the line as the narration walks through the years |
| Share of whole | unit chart (squares, people, coins) → stacked bar | Avoid pies with more than three slices |
| Geographic distribution | choropleth / dot map → globe | Normalise per capita unless the raw count is the point |
| Sequence of events | timeline → archival footage → newspaper collage | One event per beat; the timeline is the spine |
| Causal mechanism | diagram that builds → process animation → flowchart → visual metaphor | Arrows carry verbs: "pays", "blocks", "feeds" |
| System or network | network graph → flowchart → map of flows | Reveal one node at a time |
| Institution | org diagram → official record → building exterior | Show who holds the power, not the logo |
| Physical process | process animation → 3D cutaway → real footage | Real footage first if it exists, then the cutaway |
| Invisible process | simulation → animated diagram → visual metaphor | Label the metaphor as a metaphor |
| Real person | archival photo → news footage → own words as a quote card | No AI faces, no cartoons over real faces |
| Real event | news or archival footage → photo → newspaper front page → satellite | Date and source on screen |
| Document claim | the document, annotated (highlighter, circle, redaction) | The exact line, highlighted as it is read |
| Quote | document or clip of the speaker → quote card | Attribute on screen, with date |
| Abstract concept | visual metaphor → illustration → diagram → collage | One metaphor per idea; never reuse last film's |
| Human consequence | location footage → photo → testimony | The film's emotional anchor; hold longer, cut less |
| Interface behaviour | screenshot → labelled UI recreation | Recreations are badged RECREATION |
| Historical moment | archival photo with parallax → archival footage → period newspaper → historical map | Grade the archive consistently |
| Hypothetical | illustrated scene → simulation | Badge ILLUSTRATIVE |
| Definition | kinetic type → simple diagram | Say it and show it in the same breath |
| Sound or music | notation, waveform or score, synced to the audio | The viewer hears what is drawn |
| Emotional beat | footage or photo with space and silence | Fewer graphics, slower cut, music change |

## 4. The vocabulary of visual modes

Every scene names one `visual_mode`. Each has a role and a hold type. The validator knows them all
(`scripts/blueprint_check.py`, `MODES`).

| Role | Modes | What they are for |
|---|---|---|
| **Evidence** (proves) | archival_photo, archival_footage, location_footage, news_footage, document, document_annotated, newspaper, screenshot, satellite, official_record, interview, photo_annotated | Real material. They establish trust and must be sourced in the asset register |
| **Explain** (makes sense of it) | map_2d, map_globe, map_route, chart, data_viz, unit_chart, big_number, timeline, diagram, flowchart, network, process_animation, 3d_model, simulation, scale_comparison, split_screen, illustration, collage, visual_metaphor, notation, table | Graphics that build as they are named |
| **Recreation** (rebuilds) | ui_recreation, reenactment, illustrated_scene | Must be badged RECREATION or ILLUSTRATIVE |
| **Atmosphere** | stock_footage, stock_photo, texture_plate | Seasoning only: at most 25% of runtime, ILLUSTRATIVE when standing in for a specific place |
| **Text-led** | kinetic_type, quote_card, title_card, chapter_card, end_card | Never the first frame |

## 5. Domain starting points (not templates)

These are where the thinking starts. The film's own native material always overrides them.

| Domain | Native leads to consider | Typical support | Avoid by default |
|---|---|---|---|
| Geography | globe dive, satellite, route maps, terrain, scale comparisons | location footage, archival maps | flat pin maps where terrain matters |
| Economics | price series, unit charts of money, receipts and filings, flow diagrams | human consequence footage | a counter instead of the thing being counted |
| History | archival photo with parallax, period newspapers, historical maps, timelines | documents annotated | generic "old" stock |
| Technology | screenshots and labelled UI recreations, 3D cutaways, system diagrams | archival product footage | glowing-circuit stock |
| Science | simulations, scale comparisons, process animation, scientific plates and microscopy | interviews with researchers, papers | sci-fi stock |
| Politics | official records, parliamentary/news footage, maps of results, documents | charts of votes and money | flags and emblems as decoration |
| Culture | archival performance footage, notation, collage, split-screen comparisons | interviews, reviews | uncleared clips beyond fair-use need |
| Psychology | illustrated scenes, visual metaphors, interface recreations, simple experiments recreated | charts from studies | brain-glow stock, diagnosing the viewer |
| Investigative | documents and records, satellite, route reconstruction, link networks, evidence board | interviews, footage | dramatic reenactment presented as fact |
| Human-interest | location footage, personal archive (with consent), maps of a life | documents, timelines | stock people as stand-ins |

## 6. Rotation and sameness

- Never the same lead technique more than twice in a row on a channel, and never the lead of the previous film.
- The opening shot type differs from the last three films.
- Rotate transition families film to film.
- Any single effect at most three times a film.
- One visual mode may not fill more than about 60% of a film. The lead may dominate, but never alone.
- Compare blueprints: `python3 scripts/blueprint_check.py new.json --compare last.json previous.json`.

## 7. Worked contrasts (how the same engine yields different films)

| | A border dispute | A drug price | A forgotten flood |
|---|---|---|---|
| Native material | terrain, fences, treaties, satellite passes | pharmacy receipts, patent filings, price series | newspaper archive, survey maps, flood marks on walls |
| Lead / support | satellite + route maps / treaty documents | price chart + unit chart / patent documents | archival photo with parallax / historical map overlays |
| Palette source | dry earth and survey ink | prescription white and price-tag red | river silt and sepia paper |
| Signature device | the line on the ground the film keeps redrawing | a pill that grows as the price rises | a waterline that rises across every chapter card |
| Transition family | map fly-through | graphic match on the pill | paper tear between eras |
| Sound | wind, radio static, low pulse | register beeps, clean synth | river ambience, archival radio, strings |

## 8. When the engine says no

- No real material exists for an evidence line: say so (`asset_needed`) and either find it, use a labelled
  recreation, or rewrite the line. Never imply evidence that isn't there.
- The best visual is a person's face we may not show: use their documents, their words on a quote card, or the
  place, not an AI likeness.
- The engine can't draw what the subject needs (for example a 3D cutaway the pipeline doesn't have): write it in the
  blueprint as a build requirement and say so plainly. Don't fall back to a generic stand-in.
