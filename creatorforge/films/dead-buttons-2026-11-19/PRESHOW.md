# Pre-show list: The Buttons That Do Nothing (key frames, DJ style)

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
