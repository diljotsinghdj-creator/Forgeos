# Music & sound-design plan

Mix targets: dialogue -16 LUFS integrated (YouTube normalises to -14), true peak -1 dBTP; music bed -28 to -24 LUFS under voice with 4-6 dB side-chain ducking; SFX peaks -12 dBFS. Room tone under every graphic so the film never drops to digital silence except the three marked silences.

All music must be licensed (Epidemic Sound, Artlist, Musicbed or YouTube Audio Library). Never use commercial film scores or news-channel stings. Archive clips keep their natural sound at -20 LUFS.

| Chapter | In | Music cue | SFX palette | Notes |
|---|---|---|---|---|
| 0. COLD OPEN | 00:00.00 | low drone + single heartbeat kick, no melody | none | slow push-in; transitions: hard cut |
| 1. WHO HOLDS THE LATHI? | 01:03.52 | sparse low piano ostinato, 72 bpm | soft UI ticks | locked-off, diagram builds; transitions: match cut |
| 2. THE WRESTLERS | 02:02.38 | tense strings pulse, low | crowd bed under archive | slow parallax on photos; transitions: photo-flip |
| 3. JAMIA: THE LIBRARY | 04:02.48 | cold ambient pad, ticking clock | library room tone | slow zoom on stills, freeze frames; transitions: dip to black 6 frames |
| 4. DELHI 2020: THE CASE FILES | 05:31.69 | low brass drone, no percussion | paper rustle, typewriter | top-down desk camera over files; transitions: file-slide |
| 5. KHANAURI: THE BORDER | 07:16.96 | low taiko pulse building, then cut to silence | wind, distant chants | aerial-style map moves, handheld archive; transitions: smash cut |
| 6. CUSTODY: ACROSS PARTIES | 08:37.80 | solo cello, sparse | low room tone, cell-door clank once | slow data builds; stills held; transitions: cross-dissolve 12 frames |
| 7. 2006: THE PROMISE | 10:55.33 | piano motif returns, warmer, then strings rise for the close | page turns, then silence | slow push on documents; final wide; transitions: dissolve |

## Line-specific cues

- **00:00.00** (line 1): distant crowd, a tear-gas shell pop
- **00:32.54** (line 5): four paper flips, room tone
- **00:42.38** (line 6): title hit, then drop to silence
- **02:39.61** (line 19): archive natural sound only
- **03:56.54** (line 28): one bus door hiss
- **04:23.25** (line 32): CCTV hum, tape click
- **07:31.95** (line 54): drone whine, canister thuds
- **07:50.34** (line 56): hard cut to silence
- **12:20.47** (line 89): strings resolve, then silence

## Mastering chain (Audition / Resolve Fairlight / ffmpeg)

1. Voice: high-pass 80 Hz → de-ess 6-8 kHz → gentle compressor 3:1 → EQ +2 dB at 3 kHz → limiter -1 dBTP.
2. Music: low-shelf -3 dB under 200 Hz while voice speaks; side-chain duck 5 dB, attack 20 ms, release 400 ms.
3. Final bus: loudness normalise to -14 LUFS, true peak -1 dBTP. ffmpeg check: `ffmpeg -i final.mp4 -af loudnorm=print_format=summary -f null -`.