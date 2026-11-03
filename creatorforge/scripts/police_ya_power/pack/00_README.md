# POLICE YA POWER? - production pack

Hinglish investigative documentary, YouTube 16:9. **Estimated runtime 12:41.44** (90 narrated
sentences). The suggested 19:00 was not padded to: every chapter ends when its evidence ends.

| Ch | Title | Starts |
|---|---|---|
| 0 | COLD OPEN | 00:00.00 |
| 1 | WHO HOLDS THE LATHI? | 01:03.52 |
| 2 | THE WRESTLERS | 02:02.38 |
| 3 | JAMIA: THE LIBRARY | 04:02.48 |
| 4 | DELHI 2020: THE CASE FILES | 05:31.69 |
| 5 | KHANAURI: THE BORDER | 07:16.96 |
| 6 | CUSTODY: ACROSS PARTIES | 08:37.80 |
| 7 | 2006: THE PROMISE | 10:55.33 |

## What is in this ZIP
| # | Deliverable | File(s) |
|---|---|---|
| 1 | Final narration (Devanagari + Roman Hinglish + English) | 01_FINAL_NARRATION.md |
| 2 | Timecoded storyboard (all requested columns) | 02_STORYBOARD_TIMECODED.csv / .md |
| 3 | Sentence-by-sentence visual matching | 03_VISUAL_MATCHING.md |
| 4 | Verified source links + archive shot list to license | 04_SOURCES_AND_FOOTAGE.md |
| 5 | Animation assets (10 PNG) + instructions | 05_ANIMATION_ASSETS/ |
| 6 | ElevenLabs narration (v3 parts, v2 parts, pronunciation) | 06_ELEVENLABS/ |
| 7 | Music & sound-design plan + mastering chain | 07_MUSIC_AND_SOUND_PLAN.md |
| 8 | Subtitles: Hinglish, English, Hindi (Devanagari) | 08_SUBTITLES/*.srt |
| 9 | YouTube title, description, tags, pinned comment | 09_YOUTUBE_METADATA.md |
| 10 | Three 16:9 thumbnails (rendered) + concepts | 10_THUMBNAILS/ |
| 11 | Evidence & legal-verification report (+ corrections to the original pack) | 11_EVIDENCE_AND_LEGAL_REPORT.md |
| 12 | CreatorForge script + pod render script; silent animatic MP4 | 12_CREATORFORGE/, 12_ANIMATIC/ |
| QC | Automated checks | QC_REPORT.md |

## Honest limits - read before publishing
- **No finished film is in this ZIP.** No MP4 was rendered.
- **No archive footage or news photos were downloaded or licensed** (this workspace cannot reach news sites, and agency
  material needs a licence). 04_SOURCES_AND_FOOTAGE.md lists every shot to license; until then, the storyboard's
  original graphic for that line is the fallback.
- **The ElevenLabs voice-over has not been recorded** - it needs your ElevenLabs account. Timings and subtitles
  are estimates until it exists; `pod_police_ya_power.sh <your.mp3>` re-times every cut to the real voice.
- **4K**: CreatorForge renders 1080p; the pod script makes a 4K master by upscaling (lanczos). It is not native 4K.
- Legal review by a media lawyer is still needed; open items are listed in section 4 of the evidence report.

## Make the film (on the pod)
1. Record the voice: 06_ELEVENLABS/README_ELEVENLABS.md. Upload the MP3 to /workspace/vo_hi/police_ya_power.mp3.
2. `bash pod_police_ya_power.sh /workspace/vo_hi/police_ya_power.mp3`
3. Replace the archive placeholders with licensed clips in your editor using 02_STORYBOARD_TIMECODED.csv, add music
   per 07, master to -14 LUFS, upload the three SRTs.
