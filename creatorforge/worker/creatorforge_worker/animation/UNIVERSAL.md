# Universal studio - one engine, any genre, many looks

The studio no longer assumes a genre. The engine stages a story once: skeletons, IK, physics, expressions, lip sync,
world state, camera and QC. **Production styles** decide how it is drawn, the **world library** decides where it
happens, and **anatomy rigs** decide how non-human characters move. Everything is a field in the production
document. The automatic director fills these fields in, and the user can override every one of them.

> The reference video mentioned in the brief did not reach this session (no file was attached or uploaded). The
> graphic-novel mode was built from the written description: 2.5D parallax, illustrated characters, stylised
> shadows, atmospheric depth, comic effects, selective colour and a realistic-to-stylised slider.

## What was added

| Part | Module | What it does |
|---|---|---|
| Production styles | `cinematic.py` | Presets: `stick`, `cartoon`, `western`, `graphic_novel`, `motion_comic`, `noir`, `anime`, `explainer`, `painterly`. A `stylization` slider (0 realistic-leaning to 1 fully stylised) scales ink, halftone, posterising and shadow hardness. Every field can be overridden (`key_hue` for selective colour, `letterbox`, `grain`...). |
| Illustrated bodies | `cinematic.draw_figure` | Tapered limbs, torso, clothes, hands, shoes, hair, a face on every head, drawn on the **same skeleton** as the stick figures, so all motion carries over unchanged. Variants: `human`, `robot`, `alien`, `monster`; children (height, head, girth), elderly (hunch, cane); costumes: helmet, crown, cape, sword, staff. |
| Character shading | `cinematic.shade` | Per character: a cel shadow on the side away from the key light, a rim light, and halftone dots in the shadow. |
| Picture grade | `cinematic.grade` | Ink edges over the whole picture, contrast, saturation, split toning, luminance posterising, selective colour, grain, vignette, paper texture, letterbox, motion-comic panel border. |
| Comic effects | `cinematic.comic_fx` | `impact` bursts, `sfx` lettering, `speedlines`, motion-comic `caption` boxes; automatic speed lines behind fast movers. |
| World library | `worlds.py` | 14 worlds with variants: city (day/night), ancient (pyramids/Rome), castle (fantasy kingdom), forest (day/night), ocean, underwater, mountains, desert, savanna, space, microscopic, mind-space, interior (home/school/office), village. Depth haze, and living parts animated every frame: waves, stars, drifting cells, swaying weed and grass, banners, fireflies, falling leaves, light shafts, sparkles. |
| Anatomy rigs | `anatomy.py` | 32 species on 7 rigs: quadruped (IK legs that bend the right way; walk/trot/gallop chosen by the Froude number; planted feet; body bob and pitch; spring tail), bird (two-segment flapping wings, folded when perched, hopping), fish (body wave, tail fin foreshortening), whale (vertical fluke beat), serpent (body follows the head's path), dragon (quadruped plus membrane wings, fire breath), butterfly. Acts: sit, lie, eat, roar, wag, rear, fly, sleep, breathe_fire. |
| Dancing | `motions.dance` | On the beat, feet planted: knee bounce, body sway, arm moves (`groove`, `cheer`, `sway`). |
| Formats | `production.quality_for` | `format: {"aspect": "16:9" \| "9:16" \| "1:1" \| "4:5" \| "4k", "fps": 24 \| 30 \| 60}`; portrait frames scale characters by width. |
| Director | `studio.make` | Chooses the style from genre cues (`cinematic.choose`) and the world per line from the places named (`studio.WORLD_WORDS`), carried forward like weather. Faces are drawn in illustrated styles, except real people, who stay faceless and labelled. Every decision is reported in `notes["decisions"]`; `style=`, `world=` and `format=` override them. |
| Camera | `camera.direct` | Creatures that move, act or are named are subjects: framed with the cast, or on their own in shots with no people. |

## Document fields (all optional, all editable)

```json
{"style": {"name": "graphic_novel", "stylization": 0.8, "key_hue": 0},
 "format": {"aspect": "9:16", "fps": 30},
 "scenes": [{"style": "noir",
             "layers": {"world": "forest:night", "weather": [[0, 99, "rain", 0.8]]},
             "cast": [{"name": "Bolt", "species": "robot"},
                      {"name": "Ser Ana", "helmet": [150,150,160], "cape": [140,30,40], "holds": "sword"}],
             "creatures": [{"name": "Ember", "species": "dragon", "x": 12, "y": 4, "scale": 0.7}],
             "steps": [{"do": "move", "what": "Ember", "to": 3, "y": 2, "dur": 2.5},
                       {"do": "animal", "what": "Ember", "act": "breathe_fire", "dur": 1.4},
                       {"do": "fx", "kind": "impact", "text": "FWOOSH!", "at": "Ember"},
                       {"who": "Bolt", "do": "dance", "beats": 8}]}]}
```

A scene's own `style` wins over the document's, so styles can change from scene to scene: Film 4 cuts from
painterly to selective-colour noir and back.

## Demonstration films (rendered, inspected, fixed, re-rendered)
`python -m creatorforge_worker.animation.universal <dir>` renders all five; each writes `<name>.doc.json` (the
editable project), `<name>.mp4`, `<name>_android.mp4` and `<name>.report.json`. All five are rendered at 1280x720,
24 fps, final quality, on 4 CPU cores.

| Film | Genre / style | Length | Frames (all present) | A/V offset | Render (3 workers) |
|---|---|---|---|---|---|
| 1 The Courier | historical adventure / graphic novel | 46.5 s | 1116 | -0.006 s | 738 s |
| 2 Walkies | cartoon comedy / cartoon | 41.3 s | 991 | -0.004 s | 359 s |
| 3 The Body's Defenders | science explainer / explainer (automatic) | 38.3 s | 920 | 0.000 s | 304 s |
| 4 The Letter | drama / painterly + selective-colour noir | 54.0 s | 1297 | -0.021 s | 803 s |
| 5 Wild Worlds | wildlife and fantasy / painterly + anime | 33.5 s | 804 | -0.021 s | 321 s |

All five: 1280x720, 24 fps, H.264, no frozen, black or flickering frames (`qc.check_video`), delivery check
passed (`qc.check_delivery`), subtitles of the voiced films at most 13.5 characters a second with no issues.

What each film shows:
1. **The Courier** (historical adventure, graphic novel). Ancient Egypt, an invented courier and story (it says so on
   screen). Dialogue bubbles; a scroll picked up from a table; a desert run with a jump over a rock; a jackal (wolf rig)
   that growls ("GRRR!"); a falcon overhead; dusk at a temple with a cheering crowd; motion-comic caption boxes.
2. **Walkies** (cartoon comedy). Bolt the robot, Mia the child and Biscuit the dog in a city. Biscuit chases a cat at
   a gallop, and Bolt runs after them with speed lines, then a pratfall ("CLANK!"). The dog and cat sit together, Mia
   does a double take and a facepalm, Bolt dances on the beat ("TA-DA!").
3. **The Body's Defenders** (science explainer, made automatically from a seven-sentence script). The director chose
   the explainer style (6 science cues), the classroom and the microscopic worlds, and one presenter (Dr. Lena).
   - The virus enters and copies itself, a white cell surrounds it, and antibodies stick to it. Every one is labelled
     "illustration, not to scale" in the notes.
   - The voice-over is espeak-ng, with subtitles.
4. **The Letter** (drama). Painterly present at dusk; a remembered argument in selective-colour noir (only the red
   jacket keeps its colour); a rainy night reconciliation with a comforting touch and changing feelings. Style changes
   between scenes with dissolves.
5. **Wild Worlds** (wildlife and fantasy, voiced). An elephant and calf walk on the savanna (a lion rests and roars);
   a whale, a dolphin and fish swim; wolves trot in and gallop after a deer in a forest (gait chosen by speed); a dragon flies to a
   castle, hovers, breathes fire ("FWOOSH!") and lands while a unicorn rears and runs.

### Delivery formats (measured from the files)
The same styled scene (cartoon, city, four characters and two animals), rendered at final quality:

| Format | Size | fps | Frames missing | A/V offset | Render time |
|---|---|---|---|---|---|
| 16:9 1080p30 | 1920x1080 | 30 | 0 | 0.000 s | 421 s |
| 9:16 Shorts | 1080x1920 | 30 | 0 | 0.000 s | 451 s |
| 1:1 | 1080x1080 | 24 | 0 | -0.005 s | 183 s |
| 16:9 1080p60 | 1920x1080 | 60 | 0 | 0.000 s | 790 s |
| 4K | 3840x2160 | 24 | 0 | -0.005 s | 352 s |

`python -m creatorforge_worker.animation.universal <dir> formats` reproduces this table.

### Tests
Full worker suite: **250 passed** (35 min), including the new universal-studio tests (styles, selective colour,
worlds, anatomy rigs and gaits, a styled portrait production with creatures, the director's style and world choice,
and the science script).

### What review found and fixed
| Found by watching | Fix |
|---|---|
| The whole-picture ink pass traced eyes and buttons, which looked like goggles | Characters are masked out of the picture ink; they keep their own outlines |
| Speech-bubble text was inked and posterised | Bubbles and symbols are drawn on their own layer after the grade |
| Posterising per channel striped the skies | Posterising acts on brightness only |
| A falcon dragged the camera into the sky; a dragon was never framed | Creatures are subjects only when the shot can hold them with the people; creature-only shots frame the movers first |
| Elephant and deer cropped in creature-only shots | Movers first, then whoever fits; ground near the bottom |
| "Dr. Lena" became two people; "Antibodies" became a person; "class about" and "virus so" became objects; abstract nouns became placeholder boards | Sentence split respects titles; common nouns at sentence start are not names; noun phrases stop at prepositions and conjunctions; abstract nouns and places are not props; science assets (virus, cell, antibody, bacteria, atom, molecule) act out the line |
| Science props followed the presenter back to the classroom | A new world is a new shot |
| The forward roll snapped both arms (a known 3.0 defect) | The hands release at the tuck and reach the floor through a point in front; QC clean at 24 and 30 fps |
| Deer and wolves accelerated to 22 m/s (QC prop jump) | Linear moves at a believable speed |
| An empty title box sat in every frame's corner | No title, no box |
| A letter's text ran off the top of the frame | Shown as a caption box |

### Known limits of these films
- Portrait 9:16 re-frames a scene staged for 16:9. A wide line-up can lose a character at the edge, so portrait
  scenes should be staged closer (or per format).
- The science props (virus, cells) are not camera subjects, so the virus group can sit at the frame edge.
- The temple crowd scene in Film 1 is a wide shot, so its speech bubbles are small.
- Voices are espeak-ng (robotic).
- Illustrated people are flat cartoon figures, not semi-realistic painting.

## Supported, experimental and unsupported

Each "supported" item runs in the engine, passes the tests named, and appears in a rendered film.

| Capability (from the brief) | Status | Evidence / limits |
|---|---|---|
| Genres: comedy, history, science, drama, wildlife, fantasy | supported | The five demo films; `cinematic.choose` picks a style from genre cues; worlds for each setting |
| Genres: horror, thriller, mystery | supported (style and worlds) | `noir` preset, night worlds, rain; no horror-specific creatures beyond the monster variant |
| Music videos | experimental | `dance` on a bpm grid; no beat detection from an audio track yet |
| Advertising and product explainers | experimental | `explainer` and `cartoon` styles; products need imported images or library assets |
| Graphic novel / motion comic / 2.5D parallax | supported | `graphic_novel`, `motion_comic`; parallax worlds; Film 1 |
| Selective colour | supported | `key_hue`; test `test_selective_colour_keeps_only_the_key_hue`; Film 4 |
| Realistic to stylised slider | supported | `stylization` 0..1; test `test_every_production_style_renders_and_looks_different` |
| "Semi-realistic illustrated characters" | partial | Illustrated bodies are flat-shaded cartoon figures on a stick skeleton, not painted semi-realistic people. Producing those needs an image model or an artist-made character kit. |
| Anime-inspired / western cartoon | partial | Colour, line and speed-line looks; the characters are not drawn in a specific anime or cartoon anatomy |
| Realistic cinematic animation | unsupported in 2D | `painterly` is the softest look; realistic rendering needs the 3D path (Blender) or an image/video model |
| Hybrid live action and animation | supported (from 2.0) | Footage scenes, photo backdrops (Film A) |
| Humans of all ages | supported | height, head, girth, hunch, cane, hair, clothes; Film 4 (child, adult, elderly) |
| Robots, aliens, monsters | supported | `species` on the human skeleton; Film 2 (robot) |
| Animals: domestic, wildlife, birds, reptiles, marine | supported | 32 species on anatomy rigs; test `test_creature_rigs_plant_their_feet_and_change_gait_with_speed`; Films 1, 2 and 5 |
| Fantasy creatures | supported | dragon (wings, fire), unicorn, sea serpent; Film 5 |
| Mythical humanoids (centaur, mermaid...) | unsupported | No rig yet |
| Walking, running, jumping, dancing | supported | stick engine plus `dance` |
| Facial animation and lip sync | supported (2D) | 38 expressions and visemes (from 2.0) on illustrated heads |
| Character interaction, object manipulation | supported | pick up, give, throw, catch, comfort (from 2.0/3.0) |
| Crowds | supported | Crowd lanes (from 2.0); Film 1 |
| Environmental reactions, weather, time of day | supported | Rain, snow, wind, storms, dawn to night on every world |
| Physics | supported | Ballistic jumps, thrown props with bounce and roll; anatomy gaits by Froude number |
| Script -> analysis -> storyboard -> characters -> world -> animation -> voice -> edit -> video | supported | Film 3 is made from a plain script with no hand edits; test `test_a_science_script_gets_one_presenter_and_its_entities_act_it_out` |
| English, Hindi, Hinglish | supported | espeak-ng voices (robotic); Hinglish from 2.0 |
| Other languages | experimental | Any espeak-ng language for the voice; subtitles need the font to cover the script |
| 24/30/60 fps, 16:9, 9:16, 1:1, 1080p, 4K | supported | `format`; measured in the format test (see below) |
| Style changes inside one production | supported | Per-scene `style`; Film 4, Film 5 |
| Editable timelines, reusable characters and worlds | supported | Production documents and the editor (from 2.0); worlds and species are named presets |
| Automated quality inspection | supported | QC motion checks, delivery checks, subtitles, critic (from 2.0/3.0) |
| Character consistency across scenes | supported | World state carries position, costume, held objects and feelings; looks are declared per character |

