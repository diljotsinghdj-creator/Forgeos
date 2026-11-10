# The documentary studio

`creatorforge_worker/studio` turns a topic into a researched, written, narrated, animated, edited and reviewed
documentary, with every deliverable a channel needs. It is the "autonomous documentary filmmaker" of the master
directive, built on the engine described in `DOCUMENTARY_ENGINE_SPEC.md`.

```
python -m creatorforge_worker.studio films/<id>/screenplay.json films/<id>/dossier.json <out_dir> [1920x1080] [fps]
```

## The workflow (and where each step lives)

| # | Step | Module | Stops the film when |
|---|---|---|---|
| 1-3 | Research, verification | `research.py` (search provider + model), `dossier.py` | a claim has no URL, "verified" rests on one source, "disputed" has no other side |
| 4-6 | Story, structure, script | `writer.write()` (model) or a hand-written screenplay | - |
| 7 | Editorial review | `writer.check()` | a figure said or shown is not in the scene's cited evidence; a reported / estimated / disputed / alleged claim is stated as fact; a claim is unverified; a graphic can't be drawn; the film doesn't open on a hook or end on an ending |
| 8-10 | Narration, timing | `voice.py` (Kokoro, one file per scene) | - |
| 11-12 | Storyboard, art direction | `produce.py`, `artdirection.py` | - |
| 13-20 | Visuals, sync | the engine (`media/vox.py`, `media/scene3d.py`, `media/motion.py`), `produce.py` | - |
| 21-22 | Sound, music | `media/sfx.py`, `media/ambience.py`, `score.py` | - |
| 23 | Captions | `produce.captions()` (cut on the narrator's own breaths) | - |
| 24-28 | Visual and factual QC, watch-through | `produce.py` + `media/quality.py` | reported in `qc/report.md` |
| 29 | Export | `produce.py` | a deliverable is missing (listed in `README.md`) |

## What makes each film different

* `artdirection.direct()` writes a fifteen-part treatment (identity, narrative approach, visual concept, palette,
  typography, cinematography, maps, infographics, animation, footage, sound, rhythm, opening, climax, ending).
* Each axis has several treatments. The genre narrows them, and the studio history (`<data>/studio_history.json`)
  rules out whatever the last films used. No treatment comes back until the others have had their turn.
* The renderer applies the treatment: the look and accent, the camera policy per kind of shot (still on evidence,
  drift, push or pull), drawn graphics at 12 fps or the full frame rate, the breath after each line, and the music
  treatment (drone, pulse or sparse).
* The screenplay chooses the graphics line by line, and the engine rotates layouts per graphic type.

## Truthfulness rules built in

* No figure reaches the screen or the narration unless the scene cites a claim that lists it.
* A claim's status decides how it may be said: `verified` as fact; `reported`, `estimate`, `disputed`, `allegation`,
  `opinion` and `interpretation` only with attribution or a qualifier. `unverified` claims cannot be used.
* Graphics say how they were made. Map outlines and elevation data are credited on screen, and exaggerated terrain
  shows its factor (`HEIGHT ×N`). Badges (`REPORTED`, `ESTIMATE`, `DISPUTED`...) mark evidence that is not
  established fact.
* Measured graphics are checked against the sources. The Aral Sea's historic outline (Natural Earth) measures
  67,500 km² against the sourced 68,000 km². Today's outlines measure 6,800 km², about 10%, matching NASA.

## Voices

The studio narrates with Kokoro through `kokoro-onnx`: natural voices, CPU only, Apache-2.0. Setup downloads the two
model files into `<data>/models/kokoro`. FFmpeg's flite is the fallback, and it is robotic. The pipeline's voices
(ElevenLabs, Gemini, Chatterbox) can replace Kokoro through the same `voice.synth()`. The pronunciation guide changes
only what the voice reads, never the captions.

## Research providers

`research.research()` needs a search API key in the pod environment: `CF_BRAVE_KEY` (Brave Search) or
`CF_TAVILY_KEY` (Tavily). A claim survives only if its quotation is found in the text of the result it cites. Its
status comes from the number of independent hosts, not from the model's say-so. Without a key, the dossier is
written by hand in the same format, as the Aral Sea film's was.

## The first film: `films/aral-sea`

*The Sea That Was Switched Off.* It has 27 claims from 52 sources, and 32 scenes in six acts. Every figure is checked
by the editorial review, and the review caught four unsupported figures in the first draft. Its research could not
open the source pages from the sandbox, so every quotation is the search engine's summary, marked `[summary]`. The
dossier's method note says so.
