# Pre-show list: The Buttons That Do Nothing (key frames, DJ style)

## Second pass, 2026-11-19: more real, less AI (your rule: "more real pictures, animation, motion graphics etc and less ai")
Contact sheets `sheets/V2_1`–`V2_5` (all 26 frames, in order); motion sheet `sheets/M_2` (8 builds at t = 0.2 / 0.45 / 0.7 / 1.0).
The V1 sheets are the old pass, kept for comparison. Still no video, voice or music.

### What changed
- **The panel is no longer AI.** K1 is retired. `panel.py` builds the panel in the studio: plates with white sticker edges,
  rivets, screws, sockets, worn paint chips and halftone, on a **real brushed-steel photo** (TextureX.com, CC BY 2.0), toned
  slate. Same socket layout, so every studio-drawn device, lamp and the trap button still sit where they did.
- **K2 (office) → real photo:** "Office cubicle, circa 2001" (IN 30 MINUTES Guides, CC BY 2.0), cobalt duotone, captioned
  NOT THE WSJ'S OFFICE (13).
- **K4 (windowsill) → real photo:** a houseplant on a windowsill (rawpixel, CC0), black and white, labelled
  "PHOTO: A WINDOWSILL TODAY, NOT THE 1976 HOME" (21).
- **K3 (the middle manager) stays:** it's a metaphor, so no photo can show it. It's labelled AI ILLUSTRATION · METAPHOR (18).
- **New real photos in the sockets and on the cards:**
  - a lift panel with door controls (12, 24);
  - the "close door" placebo lift photo, reused (23);
  - the inside of a real traffic-signal cabinet, as "the real crossing version" of our cam timer (16);
  - a real lottery ticket, captioned NOT LANGER'S 1975 ONES, replacing the silhouette tickets (15);
  - the walk button, lift and thermostat photos pinned beside their devices in the recap (24);
  - the real Midtown street map (NYC Open Data) on the panel's screen (04, 05, 24).
- **Investigator layer:** every photo is taped down. Amber hand-drawn circles and arrows mark the walk sign's face (06) and the
  dead button (08).
- **Camera feel:** a slow push-in on every panel shot, and cut-out parallax on the photo prints.
- **Study cards:** Langer 1975 now gives the lottery N = 53 (14). Stefan & David show d = 0.62 with its 95% CI of 0.49–0.75 as a
  small interval chart (19). Glass & Singer say "N: NOT IN OUR SOURCES (TO CHECK)" (20).
- **QA fixes from the sheets:**
  - the EXHIBIT B tag no longer runs off the frame (25);
  - the REPLICATION stamp no longer covers the Stefan & David TO CHECK tag (19);
  - the cabinet photo now covers the "BACK OF THE PANEL" text (16);
  - the closing frame is dimmer, so its line reads cleanly (26).

### Counts
| | Before (V1) | After (V2) | Target (§8c) |
|---|---|---|---|
| Frames | 26 | 26 | |
| Frames with an AI plate | 26 (K1 under 24; K2, K3, K4) | **1** (18, K3, metaphor) | ≤ ~1 in 8 |
| Frames with real material (photos, real maps, charts from real data) | 10 (38%) | **17 (65%)**: 04 05 06 07 08 09 10 11 12 13 15 16 19 21 22 23 24 | ≥ 60% |
| Motion builds | 4 shown on M_1 | **11** | ≥ 8 |

The 11 motion builds are:
1. the lamps lighting on the narration's timer (01–03);
2. the camera pull-out from the button to the panel, then the devices dropping in (04);
3. the kinetic title, word by word, with the highlighter wipe (05);
4. cut-out parallax on the photo prints (06, 11, 12, 13, 15, 16, 23), plus a push-in on the real windowsill (21);
5. the Manhattan map dots greying out (07);
6. the NYC unit chart filling as the count runs 3,250 → 2,500+ (07);
7. the lottery bars growing from zero (15);
8. the reveal door swinging open and the wires drawing (16);
9. the meta-analysis interval drawing on, and the 17 / 10,825 count-ups (19);
10. the court card counting up to ~10,000, then 855 and its pace bar (22);
11. the amber circles and arrows drawing on (06, 08).

### New credits (all found through Openverse, logged in `data/photo_credits.json`, credited on screen)
- **Panel surface:** "Texture Brushed Silver Steel Metal…" by TextureX.com, CC BY 2.0.
- **Lift panel:** "Ambiguous door control" by nSeika, CC BY 2.0.
- **Signal cabinet:** "Signal Cabinet Replacement" by Greenville, NC, Public Domain Mark.
- **Office:** "Office cubicle, circa 2001" by IN 30 MINUTES Guides, CC BY 2.0.
- **Windowsill:** "Free cute houseplant window image" by rawpixel, CC0 1.0.
- **Lottery ticket:** "Indiana Mega Millions Lottery Ticket" by danxoneil, CC BY 2.0.

### Not found or not used
- **A real accessible pedestrian signal close-up:** the APS photos on Openverse are ribbon-cutting shots with identifiable
  people, and the Wikimedia original was rate-limited earlier. The button in 22 stays drawn.
- **A real lift fire-service key switch:** none on Openverse, so the key in 23 stays drawn.
- **An empty modern open-plan office:** none on Openverse, so the 2001 cubicle is used instead.
- **Photos of the real 1970s settings** (Langer's office lottery, the Connecticut home): none exist. Both frames say what the
  picture is not.
- **No new AI images were made,** and ElevenLabs was not used.

## First pass (V1), as shown earlier

This shows 26 key frames for Dragon Psychology, covering all five beats of `SCRIPT_TABLE.md` draft 1 in script order. The
contact sheets are `sheets/V1_1`–`V1_5`. The motion sheet `sheets/M_1` shows four frames (the trap opening, the panel pull-out,
the NYC count and the trap reveal) at t = 0.2 / 0.45 / 0.7 / 1.0. There is no video, voice or music: no video until "go".

## What you're about to see
- **Hook (the trap):**
  - **01–03:** the big amber button on its panel plate, "Press it. In your head." Lamp 1 lights at +3.5 s, lamp 2 at +4.0 s,
    and lamp 3 just after "NOW". Then the tags INPUT RECEIVED and EXHIBIT A · YOUR FEELING.
  - **04:** the pull-out to the full panel. The studio-drawn devices drop into their sockets: crosswalk box, lift panel with
    ◀▶ / ▶◀, map screen with its tuning dial, round thermostat, four toggles and the button. Then wires and amber "?" marks.
  - **05:** the title plate.
- **Map and history:**
  - **06:** two real photos (a New York "WAIT FOR WALK SIGNAL" sign and a Chicago walk button), with the NYT 2004 headline card.
  - **07:** the count card, 3,250 → **2,500+** (amber) → ~750, as a unit chart (1 square = 50). It sits beside a **real map of
    Midtown Manhattan streets** (NYC Open Data) on the panel's screen. Intersection dots light, then grey out.
  - **08:** the "MECHANICAL PLACEBOS" quote card (NYT 2004), with a real photo of a deactivated push button and the
    "TAKE ONE PRESS AS NEEDED" gag.
  - **09:** London, with a UK locator map, a real pelican-crossing photo (the WAIT box) and the TfL and DfT cards.
  - **10:** Sydney, with an Australia locator map, a real central-Sydney street photo, the Transport for NSW card and
    "BUTTON STATUS: ON LEAVE".
  - **11:** the lift, with a real lift-panel photo, the ADA 1990 card and the §407.3.5 receipt ("3 seconds minimum").
  - **12:** PLACEBO? | DELAYED?, with the NEII 2016 paraphrase against the ABC7 quote.
  - **13:** the office plate K2, the WSJ 2003 card, a real "PRESS FOR COOLER TEMPERATURE" photo and the ACHR **51 of 70**
    dot grid, labelled INFORMAL WEB POLL.
- **Mechanics:**
  - **14:** the Langer 1975 study card, its definition and the four skill cues.
  - **15:** the lottery, as bars from zero: $1.96 handed vs **$8.67** picked, N = 26 / 27, with silhouette tickets.
  - **16 [TRAP REVEAL]:** the panel swings open. There is no wire to the button, a cam timer is wired to the lamps, and the timer
    tape reads +3.5 s / +4.0 s / "NOW".
  - **17:** the sandwich gag, labelled ILLUSTRATION.
  - **18:** the middle manager (K3, METAPHOR), with the APPROVED notes.
- **Stakes:**
  - **19:** Langer's N = 53, then Klusowski, Small & Simmons 2021 (17 experiments, N = 10,825) with a REPLICATION stamp, then
    Stefan & David 2013 (d = 0.62).
  - **20:** Glass & Singer 1972, with bars showing direction only and the AFTER-EFFECTS NOT REPLICATED stamp.
  - **21:** the windowsill (K4) for Langer & Rodin 1976 (N = 91), the 1977 follow-up, the caveats card and "Rx: 1 FERN".
  - **22:** the NYC court card (20 Oct 2020), **95%+** over the real Midtown street map, the remedial order (~10,000), **855** in
    2024, and a drawn accessible button.
  - **23:** fire-service mode (ASME A17.1 Phase II) on the lift panel, with the fire key.
- **Synthesis:**
  - **24:** the panel recap with every device tagged, and "Before you press, ask what it's wired to."
  - **25:** one more press, and no lamp: EXHIBIT B · ALSO YOUR FEELING.
  - **26:** everything dims. A generic pause icon glows amber in the lower-left corner with its wire: "That one was always
    connected. To you."

## House rules followed
- **Palette:** slate, lab-paper and cobalt, with amber as the only signal colour. No yellow and no logo. Real photos are black
  and white or cobalt duotone.
- **Real first** (your rule, MASTER_DIRECTIVES §8c):
  - **Real photos:** 11, all licensed (CC0, public domain or CC BY), found through Openverse and logged in
    `data/photo_credits.json` with title, author, licence and URL. Each is credited on screen and in the source line.
  - **Real maps:** Midtown Manhattan streets from NYC Open Data (street centerline), and the UK and Australia from Natural Earth.
  - **AI plates:** only four. K1, the panel, is the canvas; K2, the office, is a backdrop only; K3, the manager, is a metaphor;
    K4, the windowsill, is a reconstruction. Each is labelled AI ILLUSTRATION on screen and in the source line. Each now has a
    `no_real_because` note in `data/ai_ledger.json`.
- **Studio-drawn:** every device, lamp, number, chart, label and the timer mechanism.
- **People:** stick figures and silhouettes only, with no faces. The pedestrians in the real photos are small, from behind, and
  never the "bad" example.
- **Source line:** every frame has one, giving the study, outlet and year, or saying ILLUSTRATION or RECONSTRUCTION.

## Things to know
- **TO CHECK items,** marked on screen or in the source line:
  - the NYT 2004 wording (3,250 / "more than 2,500" / "mechanical placebos"); ~750 is that difference;
  - Langer's $8.67 vs $1.96 against the original table;
  - the NEII 2016 paraphrase;
  - the WSJ date and the ACHR page;
  - Glass & Singer's task details and the non-replication citation;
  - Langer & Rodin's staff-cared plants;
  - the remedial order's ~10,000 (reports differ: 9,000 more, or 10,000 in total);
  - the date of the Sydney covers;
  - Stefan & David's journal and d.
- **The Manhattan dots are illustrative.** The streets are real, but each dot is an intersection coloured at the city's share
  (750 of 3,250). They are not real button locations, and the frame says so.
- **Some photos are not from the city in the line.** The walk button in 06 is from Chicago and the deactivated button in 08 has
  no stated location. Both captions say so.
- **No Sydney button photo was found,** so 10 uses a central-Sydney street.
- **Wikimedia Commons rate-limited this session,** so its accessible-signal photo couldn't be downloaded. The button in 22 is
  drawn.
- **Glass & Singer bars:** they show direction only, with no values.
- **The photos and map data are gitignored:** `assets/` and `maps/` are not in git. `real_assets.py` rebuilds the finished
  photos from `assets/real/raw`.

## Still to decide
- **Changes** to frames or script.
- **Go** for the video, and the **voice**: the stand-in, or your ElevenLabs voice (with your permission). No video until you
  say go.
