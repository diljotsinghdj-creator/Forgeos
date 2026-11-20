# Visual DNA Blueprint: "In Event of Moon Disaster" (Print Facts, 60 s sample)

Checked against `SEEN.json` before locking. The last six looks were declassified, intel, water, atlas-red, museum
and light-table. The last three openings were document, illustration and kinetic type. The last engine was
reverse-autopsy, and the last voice bf_alice. Nothing below repeats them.

| Dimension | This film |
|---|---|
| **1. Typography and kinetic system** | **Instrument Serif** (roman and italic) speaks for the speech, in elegiac display type. **Space Grotesk 700** carries labels and dates. **DM Mono** carries mission metadata, the memo's own typewriter lines and source chips. Reveals are a *typewriter strike* (characters land with a hammer jitter and a tiny ink bleed) and a *carbon lift* (a top sheet peels to show the text beneath). Numbers tick on a mission-elapsed-time counter. |
| **2. Colour and surface** | Core: **space ink #0B0D12**, **onionskin #F2EEE3**, **regolith grey #8D8A84**. Accent: **abort red #C8372D**. The owner's **signal yellow #FFDD33** sits on top, for highlighter sweeps on the document only. Surfaces are translucent onionskin (type from the back shows through, mirrored and faint), blue-violet carbon paper and a 16 mm film gate with sprocket holes and edge code. |
| **3. Camera and physics** | *Weightless drift*: paper floats with a slow rotation and no gravity (≤0.4° a second), as if in a spacecraft cabin. Footage sits in a 16 mm gate with a 2 px gate weave. A slow 60 fps optical push on documents; paper elements step at 12 fps. No whip-pans: this film is quiet and elegiac. |
| **4. Signature motif** | **The carbon copy.** History is the top copy; underneath lies the carbon of the speech that was never read. Across the film the top sheet (NASA footage and photos) lifts at a corner to show the carbon beneath, and at the end it settles back. |

**Opening:** footage (NASA's 1969 TV pictures of the first steps): not one of the last three openings.
**Engine:** trojan-horse (the owner delegated the pick; see `pick.json`).
**Evidence first (gate 3):** real NASA footage at 0 s, then the real memo at 4 s, before any explanation.
**Voice:** a Kokoro narrator other than bf_alice (to choose at the video stage; never an imitation of Nixon).

## Storyboard (`[SCRIPT_PLAN]`)

Each frame below is a key frame. At the video stage, frames longer than the pacing gate allows (a still at most
4.5 s, a building shot at most 7 s) split into the sub-shots listed, for about 14 shots in all with an average
under 5 s.

| # | Time | Key frame | Sub-shots at video stage | Sound |
|---|---|---|---|---|
| F1 | 0–4 s | NASA TV picture of the first steps in a 16 mm gate; chip "JULY 1969 · SEA OF TRANQUILITY" | 1 | `[SFX: projector gate start]` `[SFX: low sub-pulse]` |
| F2 | 4–9 s | The memo on onionskin; yellow sweep over To / From / Date; National Archives chip | 2 (wide, then push to the header) | `[SFX: paper slide]` `[SFX: marker stroke]` |
| F3 | 9–12 s | "IN EVENT OF MOON DISASTER:" typewriter strike, abort-red rule | 1 | `[SFX: typewriter strikes]` |
| F4 | 12–21 s | Aldrin (NASA photo AS11-40-5903), the speech's first line in serif italic | 2 (photo, then the quote builds) | the score drops to the pad alone |
| F5 | 21–32 s | Page 2 as a procedure card: 1 the call, 2 the cut-off, 3 the burial at sea | 3 (one per step) | `[SFX: rotary phone dial]`, `[SFX: radio squelch cut]`, silence |
| F6 | 32–38 s | Signature motif: the top copy lifts to show the carbon of the speech | 1 (building) | `[SFX: paper peel]` |
| F7 | 38–48 s | The two timelines: the real mission clock against the dashed "if" branch | 2 (track draws, then the branch fades) | `[SFX: mechanical shutter]` on 21 Jul |
| F8 | 48–60 s | Earth over the lunar limb (AS11-44-6549); the last line; "never read" | 2 to 3 | the score resolves to the tonic, then fades out |

**Score:** cut-fitted (`studio/score_bars.py`), minor mode, every cut on a downbeat, a silent bar before F8;
`sync_check` must pass (no off-beat cut, no jump above +6 dB).
