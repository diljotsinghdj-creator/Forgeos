# Sound design and music

Music, effects, ambience, silence and the mix. Read this when setting the film's `sound_palette` and when filling
each scene's `sound`.

Labels: [V] source-backed (sources.md P#, case_studies/) · [I] interpretation · [O] our rule.

**Evidence note.** This is the thinnest area of the research. No source found names Vox's music library, composers,
SFX workflow or mix standard (sources.md §I). What we have is [V] below. Everything else is our craft standard [O],
to be checked against real audio when access allows.

---

## 1. What the studied craft shows

- [V] The music's emotional tone tracks the explanation, and visual changes are cut on the beat (P3).
- [V] One music-led producer composed some of her own music on a hardware synthesiser (P27).
- [V] Music rights are a live risk: a music-analysis video was taken down by Content ID over a few seconds of fair-used
  audio (PATTERNS sci/culture §4, from the producer's own post), and the producer has said Content ID cannot judge fair
  use, which cost her videos their monetisation (P32).
- [V] Audio is most of the work in music-led films: one producer spends about 70% of her time editing audio, and builds
  a playlist while outlining to choose the songs a film will feature (P27).
- [V] Stock music is mostly too much (too sad, too happy, too cheesy); most of a former producer's music time goes
  on finding subtle tracks and reviewing stems, and a serious stretch is undercut with lighter imagery so it doesn't
  turn pretentious (P13).
- [V] A riser followed by a bass hit carries the viewer out of one music bed into the next scene (P13).
- [V] The team kept short internal tutorials on craft such as editing music, as part of a script and editing
  curriculum (P42).
- [V] Music-analysis pieces treat sound as data and evidence: lyric mentions logged and sorted by year with audio
  per entry (why-rappers-love-grey-poupon-2016); a performer-scholar plays the instrument on camera
  (banjo-black-american-folk-music-2022).

- [V-auto] **From four full-video analyses (case_studies/TRANSCRIPT_STUDY.md and the four watch-based case studies):**
  - beds are light percussion, mallets, pizzicato or acoustic guitar, and the music changes register with each act:
    mystery, explanation, harm, human cost (piano), resolution;
  - clicks and pops sync to graphic builds; paper rustle and pen strokes sit under document highlights;
  - **the subject's own sounds are mixed forward** (a dessert shell cracking, engine rumble, wood cracking);
  - music dips under interviews;
  - a sting or drop into silence comes before the title;
  - endings resolve on a contemplative pad or a clean chord, then a silent tail.

## 2. The sound palette, per film [O]

Each film declares (`dna.sound_palette`):
- **Music: at least two cues,** usually three to five for 8–15 minutes. A cue change marks a chapter turn or the film's
  turn. Each cue has a role: curiosity (light, pulsing), investigation (low, steady), weight (sparse, sustained),
  resolution (open, warm).
- **An SFX family matched to the native material:** paper and pen for documents; UI clicks and haptics for
  interfaces; water, metal and engines for infrastructure; radio static for history; tonal swells for science.
- **Ambience beds** for every real place shown: room tone, street, wind, sea.
- **Planned silences:** where the music drops out entirely, and why.

## 3. Music [O]

- **Licensing first:** use licensed library music, commissioned music, or our own compositions; keep the licence in
  the asset register. Never commercial tracks without a licence. Fair use is not a production plan (P32).
- **Enter late.** Let the hook's first line land on near-silence or ambience; bring the music in on the question.
- **Change on turns:** a new cue at the film's turn; a drop to silence before the biggest reveal; a resolution cue for
  the ending.
- **Duck under narration** by about 12–18 dB; let it swell 3–6 dB in gaps and on visual-only beats.
- **Edit music to picture:** cut on downbeats, end cues on a phrase end or a hard button, never fade mid-phrase
  without a reason.
- **Avoid emotional overreach:** the music never tells the viewer to feel more than the evidence supports (after
  P8, which says the same of visuals: no misleading positivity on serious subjects).

## 4. Sound effects [O]

- **Sync SFX to builds:** a soft tick or pop when a label lands, a pen stroke under a hand-drawn circle, a paper
  slide when a document enters, a whoosh only under a real camera move.
- **Restraint:** at most one prominent SFX per second of action; the family stays consistent through the film.
- **Diegetic sound for evidence:** footage keeps its natural sound (lowered under narration) because it signals
  "this is real".
- **No cartoon effects on serious subjects.**

## 5. Ambience and silence [O]

- Every place shot gets an ambience bed (location sound or licensed ambience), J-cut 0.5–1 s before the picture.
- **Silence is a tool:** 0.5–1.5 s of near-silence (ambience only) after a human-consequence line or a reveal.
  Once or twice a film, a full drop to room tone.

## 6. Mixing and loudness [O]

| Element | Target |
|---|---|
| Integrated loudness (YouTube delivery) | about −14 LUFS integrated; true peak ≤ −1 dBTP (CreatorForge's fixed audio target) |
| Narration | the anchor: consistent level, light compression, de-essed, around −16 to −18 LUFS short-term under music |
| Music under narration | 12–18 dB below the voice |
| SFX | felt, not heard: ~6–10 dB below the voice |
| Ambience | just audible |

Check on a phone speaker and on headphones. Loudness measured with ffmpeg's `loudnorm` / `ebur128` filters.

## 7. Sound in the blueprint [O]

Each scene's `sound` object: `{"music": "<cue id + state: enter | continue | swell | drop | change>", "sfx": "<sync
points>", "ambience": "<bed>", "silence": true|false}`. `render_blueprint.py` turns these into the cue sheet.

## 8. Failure modes

| Failure | Fix |
|---|---|
| One wall-to-wall track | At least two cues; changes on turns; silences |
| Whooshes on every cut | SFX only on real motion and builds |
| Music fighting the narration | Duck 12–18 dB; choose cues with no melody in the voice range |
| Uncleared music | Licensed or original only; register every cue |
