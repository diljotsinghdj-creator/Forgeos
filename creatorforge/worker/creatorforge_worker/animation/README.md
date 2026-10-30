# CreatorForge animation

Original characters, procedural motion and rendering, all free and offline.

| Part | File | What it does |
|---|---|---|
| Speech + lip-sync | `speech.py` | espeak-ng speaks a line (English, Hindi and ~100 more) and reports every phoneme with its time. Each phoneme becomes a mouth shape (viseme), eased 40–90 ms. For someone else's audio, `estimate_visemes` times mouth shapes from the text and length. |
| Faces | `face.py` | 38 expressions as numbers (brows, eyelids, pupils, mouth, smirk, teeth, blush, tears, sweat, anger mark, sleepy z's), blending and mixing, automatic blinking, speech mouth on top of the expression. |
| 2D rig | `rig2d.py` | Skeleton with two-bone leg IK. Feet are planted in world space and lift only once the body has passed over them (measured slide: 0.0 mm). Double support ~20% of a step, hips ride the legs' reach (weight shift), arms counter-swing. Walk, run (flight phase), jump (anticipation, flight, landing squash), settling step on stops, 19 gestures, looks (hair, glasses, tie, cap, beard, skirt, shirt, cane, stoop), children (bigger head), elderly. |
| Animals | `creatures.py` | Camel with a pacing gait (same-side legs together) and planted hooves; flapping birds. |
| Scenes | `scene2d.py` | Camera with eased moves, zoom and shake; parallax depth layers painted once as wide strips; haze by depth; shadows; desert, park and paper-studio environments; 2× supersampled frames; H.264 master (CRF 12) + Android copy (Main 4.0, AAC, fast start). |
| Script → animation | `script.py` | A sentence ("A stickman receives shocking news on his phone.") becomes a plan: who, where, actions in order, the feeling, quoted speech. Then it's acted, framed and rendered. In a video script, an `Animate:` line plays such a scene on that line. |
| Stick engine | `stick.py` | Keyframed acting on fixed-length bones (bones never stretch: tested). Per-foot and per-hand targets with IK; every keyed foot travels an explicit path that arcs over the floor, so feet never skate (planted-foot skid measured 0–1 mm per frame across all four demos). Flights are real gravity (−9.8 m/s²) with the push-off ending at exactly the take-off speed. Follow-through, spring-damped head and forearms, a floor that hands, head and feet can't pass through, faceless body language (sad, excited, angry, confused, embarrassed, laugh, confident…), walking with hands on an object, props carried, pushed, dragged and keyed, platforms to stand on. |
| Moves | `motions.py` | jump (and onto/off ledges), climb (chest-high mantle, or jump-catch-hang-pull-up when the ledge is out of reach), trip + forward roll (curled, limbs turn with the body), knockback and get-up, pick up, put down, point, push, drag, kick, pain hop, tap. |
| Props + sets | `props_draw.py`, `stick_demos.py` | Crates, folders, charts, flow diagrams, real photos (credited, highlightable), signs, statistic cards with sources; a parliament chamber and a documents wall. |
| 3D | `blender3d.py` | Real 3D in Blender (`bpy`): one skinned mesh per character on an armature; IK legs and arms with pole targets; a face of 19 blend shapes (shape keys); stickman and cartoon styles; park environment; sun and fill lights with shadows; tracking camera with depth of field; EEVEE (default) or Cycles. Motion comes from the same planted-foot controller, and turns are real body rotations. |

## Demos

```
python -m creatorforge_worker.animation.demos A|B|C out_dir      # 2D, 2.5D
python -m creatorforge_worker.animation.script "A girl gets great news and dances." out.mp4 [--portrait]
python -m creatorforge_worker.animation.stick_demos 1|2|3|4 out_dir   # stick engine demos
python -m creatorforge_worker.animation.blender3d D|E|5 out_dir  # needs: pip install bpy (Blender as a module)
```

Demo 5 drives the 3D rig with the stick engine (`Char3D.pose_actor`): the same jump physics, roll and body
language, with knee and elbow pole targets following the solved joints, and one continuous 2.35:1 camera.
Demo 4 uses crops of real images from a CreatorForge video (`assets/`), each labelled with its source on screen.

For 3D without a display, Blender needs EGL (`apt-get install libegl1 libgl1 libegl-mesa0 libgl1-mesa-dri`) and
`EGL_PLATFORM=surfaceless`. `CF_3D_ENGINE=cycles` switches to path tracing. `CF_PREVIEW=1` renders 5 low-res stills.

## Not done yet (honest list)

- 3D characters are built from primitives (capsules and spheres), not sculpted models. They are clean and
  consistent, but not feature-film detailed. Hands have no fingers.
- 3D turns pivot the feet in place rather than stepping around.
- The script planner is rule-based: it understands common actions and feelings, not arbitrary prose.
- Environments: desert, park and studio (2D); park (3D). Cities, interiors, mountains and beaches, plus dogs, cats
  and horses, are not built yet.
- espeak-ng voices are robotic. For a finished film, record or generate the voice elsewhere and use
  `estimate_visemes` for the mouth, or wire the Google voice in.
- Sitting is not implemented. Climbing, carrying, pushing and dragging are (stick engine), but a foot can't yet
  collide with a wall face, only with floors and platform tops.
- The stick torso is one rigid bone; a curled roll is suggested by shortening it (squash), not by bending a spine.
- 2D keyframed moves are hand-tuned poses; there is no physics solver for falls or collisions between characters.
- The 3D stickman's feet don't pitch through a roll, and Demo 5 is rendered with EEVEE at 1280×544, not a film
  renderer at 4K.
