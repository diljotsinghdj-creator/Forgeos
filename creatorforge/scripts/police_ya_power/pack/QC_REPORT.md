# QC report

| Check | Pass | Detail |
|---|---|---|
| Runtime under 20 min | PASS | estimated 12:41.44 |
| Every line has a visual | PASS | 90/90 lines |
| Every factual line sourced | PASS | 67/67 factual lines carry a source |
| Hinglish subtitles track Devanagari narration | PASS | word-count mismatches: none |
| Dates checked against sources | PASS | years used: 1996, 2006, 2014, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026 (each tied to a source in the evidence report) |
| ElevenLabs parts within v3 limit | PASS | 4 parts ≤ ~2,900 chars |
| Animatic renders, H.264 yuv420p (Android-safe) | PASS | h264 High 1920x1080 yuv420p, 761.7s |
| No black frames ≥0.5 s | PASS | none detected |
| Animatic length matches script timing | PASS | 761.7s vs 761.4s |

## Not checkable here (do on the pod / before upload)

- Final audio consistency and loudness: needs the recorded ElevenLabs voice (target -14 LUFS, -1 dBTP).
- Subtitle timing word-for-word against the real voice: `voiceover_sync` re-times; spot-check 5 random cues.
- Android playback of the FINAL film: copy to a phone, play in Files/Photos and YouTube app preview.
- Archive licences: every 'ARCHIVE (licence needed)' row in 03_VISUAL_MATCHING.md.