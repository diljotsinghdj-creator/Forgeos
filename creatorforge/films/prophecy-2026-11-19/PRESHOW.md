# Pre-show list: The Night the World Didn't End (key frames, DJ style)

The first round showed 24 key frames for Dragon Psychology, covering all five beats of `SCRIPT_TABLE.md` draft 1. Each frame is also shown
at four moments of its animation (sheets `M_1`–`M_3`). There is no video, voice or music: video only after "go".

## Updated 2026-11-19 (round 5): more real pictures and motion, less AI (sheets `V5_1`–`V5_4`, motion sheet `M_5`)
Your rule: "we need more real pictures, animation, motion graphics etc and less ai" (MASTER_DIRECTIVES §8c).

- **Counts:**

  | | Before | Now |
  |---|---|---|
  | Frames | 30 | 28 |
  | Frames with an AI plate | 15 (10 plates, plus the AI desk under 5 slate frames) | 3 (1 in 9) |
  | Frames carrying real material | 1 (the map) | 17 (61%) |
  | Motion builds on the motion sheet | the drawn builds only | 12 |

- **What replaced each AI plate:**
  - **F1 (desk):** the drawn slate is back under every slate frame.
  - **C1:** `07_millerites` now uses the **real 1843 Millerite chart** ("A Chronological Chart of the Visions of Daniel & John", J. V. Himes, Boston; public domain). It shows the full sheet and a close-up of its sums, which end in 1843, with an amber circle. The line now reads "1843 passed; the date moved to 22 October 1844". That fact is added to the dossier.
  - **E2:** `15_box` now uses a **real photo of the Bentley Historical Library** (Dwight Burdette, CC BY 3.0), with the sign circled, and a real archive photo (Toronto Archives, CC BY 2.0). The archive photo is labelled "not the Bentley, not the Festinger box". The pages are still drawn and labelled as reconstructions.
  - **F2:** `11b_phones` now uses **real 1950s desk phones** (a Western Union Model 500 and a Bakelite set, both CC BY 2.0), labelled "not the group's own".
  - **F5:** `22b_textbooks` now uses **a real stack of books** (CC BY 2.0, no titles shown), with kinetic type: "DOUBLED / DOWN ON." drops in letter by letter.
  - **F3:** dropped. The drawn `13_carlsmith` now has a **real peg board** ("not the 1959 apparatus") and the $1 and $20 bars grow from a zero line. They still show the direction of the effect only.
  - **F6:** dropped. The drawn `06_membership` is back, with a **real padlock** photo on the card.
  - **B3:** `24_end` is a **real night sky over a house** ("not Oak Park, not 1954") under the drawn cracked clock and saucer.
- **AI kept (3), only where nothing real exists:**
  - **A1:** the 1954 living room nobody photographed. It is now a labelled print on the drawn grid, not a backdrop.
  - **D1:** the antelope sight gag.
  - **F4:** the valve-in-your-head metaphor.
- **Other real material added:**
  - Natural Earth locator maps on `01_clock` and `02_house`.
  - The 1843 chart pinned at 1844 on the timeline.
  - A real coin on `03_metal` and a real pressure gauge as the dissonance dial on `12_valve`.
  - The Bentley photo on `16_kelly`, and archive boxes on `21_otherside`.
  - `20_replications` counts up the Vaidis 2024 figures: 39 labs, 19 countries, 4,898 people. The dossier doesn't list the 19 countries, so there's no world map.
- **Motion (sheet `M_5`):**
  - the house plan drawing on;
  - the metal items and the coin dropping in;
  - the timeline wipe;
  - a slow camera push on the chart;
  - the Great Lakes route, drawn in story order (Minneapolis → Oak Park → East Lansing → Ann Arbor);
  - the valve and gauge;
  - the peg board and the bars growing from zero;
  - the two clocks, whose hands now spin;
  - the archive (the pages drop in, the arrow draws on);
  - the count-up;
  - the book spines growing;
  - the "doubled down" kinetic type.
- **The investigator layer:** amber circles and arrows sit on the chart, the coin, the gauge and the library sign; the photos are taped prints. Amber stays the only signal colour, and the chart is shown in black and white, so there's no yellow.
- **Real photos** are black and white or cobalt duotone (`real.py`). No faces of the group or the researchers are shown anywhere. The banner with people in the Bentley photo is cropped out.
- **Credits** are on screen in each frame's source line and listed in `data/photo_credits.json`:
  - J. V. Himes chart (PD, Commons);
  - Dwight Burdette (CC BY 3.0, Commons);
  - Phillip Pessar, nreijmersdal, sillygwailo, Digital Game Museum, Wonderlane, Horia Varlan, Eric M Martin, wwarby, matthiasxc, andypowe11 and Robin Mulligan (all CC BY 2.0, Flickr via Openverse).
  - Retired plates are marked in `data/ai_ledger.json`.
  - No new AI images were made, and no ElevenLabs credits were spent.
- **Not found:**
  - No real photo of a 1950s Chicago-area street or house fits. The candidates were Australian or Frank Lloyd Wright houses, which would mislead, so A1 stays.
  - No real lottery-ticket or spool photo was found for the peg task.
- **Build:** `python3 -I real.py && python3 frames.py && python3 ai_frames.py && python3 shoot_http.py && python3 shoot_http.py $(python3 sheets.py --list) && python3 sheets.py`.

> The sections below are the earlier rounds. Where they describe AI plates, round 5 replaces them.

## What you're about to see
- **Hook:**
  - the cobalt clock at 11:59, 20 Dec 1954, Oak Park;
  - a stick-figure house plan, with the three undercover researchers in amber;
  - "the boarding requirements" from the 1956 book: no metal, the password "I left my hat at home", a stamped-envelope passport;
  - the title, with a REPLICATION? stamp.
- **History:**
  - a timeline from small human groups to today, with the Mercier & Sperber study card ("theory, debated");
  - the "admits the mistake / digs in" split and the membership card;
  - the Millerites' 1844 "Great Disappointment";
  - a Great Lakes map (Natural Earth) pinning Minneapolis, Oak Park, East Lansing and Ann Arbor, the archive.
- **Mechanics:** midnight; the Christmas message (paraphrased); the 1956 book's double-down claim; the dissonance pressure valve; the
  Festinger & Carlsmith $1 vs $20 study; the second clock (2025).
- **Stakes:**
  - the Box 4 archive (reconstruction);
  - Kelly's study card and the split "the book says / the papers say";
  - the empty room;
  - the quote from Riecken's notes ("precipitated…", as quoted by Kelly);
  - the antelope-and-lion sight gag;
  - the failed-prophecy follow-ups and the 2024 39-lab replication ("EFFECT NOT FOUND");
  - "Before we pile on": the other side.
- **Synthesis:** "the study about doubling down got doubled down on"; the valve in your head with "UPDATE"; the end clock at 12:01
  with a tiny saucer.

## House rules followed
- **Palette:** slate, lab-paper, cobalt, with amber as the only signal colour. No yellow, no logo.
- **People:** stick figures only. No faces, no photos of real people. The group members are never mocked.
- **Documents:** the archive box, papers, book cover and broadsheet are studio reconstructions, labelled as such.
- **Allegations:** every claim against the researchers is attributed to Kelly 2025, and the other side has its own frame (21).
- **Maps and metaphors:** the map is Natural Earth data (public domain). The valve and the brain are labelled "metaphor, not anatomy".

## Things to know
- **The $1 vs $20 bars show the direction of the effect,** not the measured scores. The frame says so, and the exact scores are to
  check in the 1959 paper.
- **The Christmas message is paraphrased,** not quoted.
- **The authors' death years** are left off the frame. They're in the dossier to check.
- **The bathroom note-taking line** in the script (act 1) is a well-known detail from the book. Check the page before the voice.

## Still to decide
- **Changes** to the frames or script.
- **Go** for the video, and the **voice**: the Kokoro stand-in, your ElevenLabs voice (with your permission), or your cloned voice.

## Added 2026-11-19: AI illustrations (owner's picks A1, B3, C1, D1, E2)
- **01b_room (new frame, after the clock):** an AI paper-cut 1950s living room, stick figures and the prediction card. The three
  researchers are in amber. The AI clock is corrected to 11:59.
- **07_millerites:** the AI 1844 dawn scene of faceless silhouettes replaces my drawn broadsheet.
- **15_box:** an AI archive box, with a "BOX 4" label set on it and labelled "not the real box".
- **19_antelope:** the AI antelope-and-lion gag, with the tweed hand holding a microphone.
- **24_end:** the AI night sky with the late saucer and the lit window, under the cracked clock.
- **Labels and ledger:** every AI plate is labelled "AI ILLUSTRATION" on screen and logged in `data/ai_ledger.json`. No real person
  is depicted, and none stands in for evidence.
- **Credits:** about 3,800 ElevenLabs credits for the 20 options.

## Added 2026-11-19: round 2 of AI plates (sheet `AI_PLATES_2`, motion sheet `MOTION_AI`)
- **What you'll see:**
  - **The slate study desk (F1)** now sits under every slate frame: the clock, title, midnight, two clocks and "your head".
  - **06b_card:** the membership card, padlocked.
  - **11b_phones:** the phones ringing, labelled as the book's version, which chapter 4 disputes.
  - **13b_pegs:** the Festinger & Carlsmith peg task.
  - **22b_textbooks:** "the study about doubling down got doubled down on".
  - **23b_head:** "the same valve sits in your head", labelled metaphor, not anatomy.
- **The five earlier picks** (A1, B3, C1, D1, E2) now get the studio finish (`ai_finish.py --channel dp`). The raw files are kept.
- **House rules:**
  - Each plate is labelled AI ILLUSTRATION and logged in `data/ai_ledger.json`.
  - No faces: the head is a blank silhouette.
  - No AI chart or number.
- **Credits:** about 1,142.
