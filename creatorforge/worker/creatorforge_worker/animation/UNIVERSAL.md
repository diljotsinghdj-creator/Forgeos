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

DEMOS

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

