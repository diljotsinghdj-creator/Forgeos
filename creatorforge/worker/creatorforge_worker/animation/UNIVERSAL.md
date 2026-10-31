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
