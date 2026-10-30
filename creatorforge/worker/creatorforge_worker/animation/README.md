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
| 3D | `blender3d.py` | Real 3D in Blender (`bpy`): one skinned mesh per character on an armature; IK legs and arms with pole targets; a face of 19 blend shapes (shape keys); stickman and cartoon styles; park environment; sun and fill lights with shadows; tracking camera with depth of field; EEVEE (default) or Cycles. Motion comes from the same planted-foot controller, and turns are real body rotations. |

## Demos

```
python -m creatorforge_worker.animation.demos A|B|C out_dir      # 2D, 2.5D
python -m creatorforge_worker.animation.script "A girl gets great news and dances." out.mp4 [--portrait]
python -m creatorforge_worker.animation.blender3d D|E out_dir    # needs: pip install bpy (Blender as a module)
```

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
- Sitting, climbing and holding objects other than a phone or cane are not implemented.
