# The bank: 20 finished films before the first upload (owner, 2026-11-17)

The owner's plan is to build a bank of scripts, visuals and finished videos first. Once there are **20 good ones**, posting starts
on a YouTube schedule. Until then nothing is uploaded.

## Rules for the bank
- **What counts toward the 20:** a film counts only when its script, visuals and final video have all been approved by the owner.
- **Every script is in the John Oliver voice, and every video is in the Vox style** (owner, 2026-11-17; MASTER_DIRECTIVES §10). A
  film enters the bank only if it passes both tests below. Scripts and videos made before these rules count only after a rewrite.
  - **Script test (John Oliver voice):**
    1. The film keeps the five beats: hook and question, map and history, mechanics, stakes, synthesis.
    2. The lines run fact, then receipt (a real document or number on screen), then simile, then snap back.
    3. The tone is deadpan, with at least two callbacks.
    4. There is a hard music cut, with 0.2 s of silence, before each punchline.
    5. The satire targets systems, documents and official language, never a party or a named person's character.
    6. There are none of John Oliver's catchphrases or bits.
    7. Every fact is in the research dossier with its source and status, and the other side is shown.
  - **Video test (Vox style):** the channel's house style skill (`printfacts-style` or `dragonpsych-style`) is loaded before any
    visual work, and the video has:
    - the channel palette, plus at most one film accent;
    - paper, cut-out and texture collage;
    - real maps and archive material (evidence first for Print Facts);
    - charts that start from zero;
    - chapter cards;
    - comedy visuals: cut-out sight gags, archive-tag captions, and smash-zoom receipts with a highlighter and red circle;
    - captions from `captions.py`;
    - pacing within the limits: a still holds at most 4.5 s, a building shot at most 7 s, and the average at most 5 s;
    - loudness at -14 LUFS;
    - a PRESHOW sent to the owner first.
- **The gates still apply to every film in the bank**, however long it waits: pick, SEEN, evidence first, pacing and PRESHOW.
- **No two films in a row share an engine, a hook or an opening look.** The bank is the order viewers will see.
- **Facts are refreshed before scheduling:**
  - Each film keeps a "refresh before air" list: prices, ranks, counts and anything dated.
  - Each item is checked again in the week the film is scheduled, not on the day it was made.
- **Scheduling comes later.** Uploading by API needs the owner to connect their YouTube channel. Until then, the owner uploads by
  hand from the finished files.

## Work plan (owner, 2026-11-19)
- **Until Friday:** write scripts on Opus 5.5 (pitch three engines, owner's pick, dossier, four-column John Oliver table). No video.
- **Friday, before the 21:00 weekly reset:** render the videos for every script the owner has approved, using what's left of the week's usage. Each film still needs the owner's **go** and a **voice** choice, and its PRESHOW goes to the owner first.
- Rendering is mostly local CPU (Playwright frames, ffmpeg). The model's usage goes into building and checking the code, so separate sessions can run films in parallel.

## Bank status
| # | Film | Channel | Format | Script | Visuals | Video | Refresh before air | Status |
|---|------|---------|--------|--------|---------|-------|--------------------|--------|
| 1 | Pepper Was Money (`films/pepper-money-2026-11-15`) | Print Facts | long, 16:9, ~9 min | draft 5, four-column `SCRIPT_TABLE.md` (2026-11-19), John Oliver voice; pacing checked (101 shots, avg 4.5 s) | 30 key frames and 17 motion builds; 7 new beats listed in the table | not made | Kochi price; UNESCO and other counts; 2022 Act section | script for owner's approval; then go and a voice |
| 2 | Why India is mocked online (working title "Disgust Pays") | Print Facts | long, 16:9, ~9 min | draft 3.1, four-column `SCRIPT_TABLE.md` (2026-11-19): report corrections in, script test passed (7/7), jokes aimed at the feed, 6 AI plates marked; 1 wording ⚠ (TRAI slide title) | 20 key frames and motion sheets (`films/india-mocked-2026-11-17`); 17_sowhat to restage | not made | IMF rank; CSOH, NCRI and FBI figures; UPI; IQAir; UNESCO | pick: the owner's own draft (`pick.json`); script for owner's approval; then go and a voice |

| 3 | The Night the World Didn't End (`films/prophecy-2026-11-19`) | Dragon Psychology | long, 16:9 | draft 1, four-column, John Oliver voice | 24 key frames and motion sheets (DJ style, 2026-11-19) | not made | Kelly rebuttal status; Festinger & Carlsmith scores | engine A (countdown) picked by the owner 2026-11-19; script draft 1 done |

| 4 | Why does landlocked Bolivia have a navy? (`films/bolivia-navy-2026-11-19`) | Print Facts | long, 16:9, ~9½ min | draft 1, four-column `SCRIPT_TABLE.md` (2026-11-19), John Oliver voice, pacing checked (130 shots, mean 4.25 s); 14 ⚠ items | 26 key frames + motion sheet (2026-11-19): real relief, 6 animated maps, 6 real photos, 3 AI plates; gate 3 needs a treaty scan or the owner's waiver | not made | ICJ 2018 vote; Day of the Sea; navy size; Arica cargo share | engine A (Reverse Autopsy) picked by the owner 2026-11-19 |
| 5 | The buttons that do nothing (`films/dead-buttons-2026-11-19`) | Dragon Psychology | long, 16:9, ~10½ min | draft 1, four-column `SCRIPT_TABLE.md` (2026-11-19), John Oliver voice, viewer trap set at 0:00, revealed at 5:00; pacing checked (130 rows, mean 4.7 s); 9 ⚠ items | 26 key frames + motion sheet (2026-11-19): 11 real photos, real Manhattan street map, 4 AI plates | not made | NYC button count; NYC accessible-signal order; Sydney hours | engine A (Live Viewer Trap) picked by the owner 2026-11-19 |

Older work waiting on the owner (not counted until approved in the current style):
- US midterms: awaits go;
- the Delhi film: awaits go.

**Count toward 20: 0 approved.**
