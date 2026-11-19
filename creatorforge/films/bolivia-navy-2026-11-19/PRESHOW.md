# Pre-show list: Why Does Landlocked Bolivia Have a Navy? (key frames, draft 1)

This sheet shows 26 key frames for Print Facts, covering all five beats of `SCRIPT_TABLE.md` draft 1 (engine A, Reverse
Autopsy). Every frame is a still with an animation timeline. Sheet `M_1` shows four of them at four moments. Contact sheets
`V1_1`–`V1_5` show all 26. There is no video, voice or music. **No video until you say "go".**

## What you're about to see
- **Hook (01–05):**
  - the navy boat on Titicaca (AI plate B1), "THIS IS A NAVY.", and an altitude readout that climbs to 3,810 m;
  - the receipt: Article II of the 1904 treaty on aged paper, with a highlight on "dominio absoluto y perpetuo de Chile" and a
    red circle on "perpetuo";
  - the light table: a relief map of the Andes, with a real photo of the lake next to the boat clipping;
  - "Bolivia's coast: 0 km", the loose Litoral paper strip, and the title.
- **The rewind (06–12):** the crimson date stamp runs ◀◀ JAN 1963 → 20 OCT 1904 → 4 APR 1884 → 14 FEB 1879 → 1878. It shows:
  - FLUVIAL Y LACUSTRE, with MAR crossed out;
  - the signature block;
  - the truce, with tape across the strip;
  - the Antofagasta landing, with the strip lifting;
  - the 10-centavo ledger, with a real photo of the Humberstone nitrate works;
  - both sides of the 1874 tax argument;
  - the auction stamp, with the date stamp frozen crimson.
- **Forward (13–19):** the stamp switches to ▶ and ▶▶. It shows:
  - Topáter and Abaroa (AI plate B2, told straight, no joke);
  - the strip peeling off the coast, with ~400 km / ~120,000 km² and the "same date" cards;
  - the Arica–La Paz railway drawing on and the £300,000 card;
  - "the treaty uses forever twice";
  - the house-and-hallway gag;
  - the ~76% Arica bar, over a real 2008 photo of Arica port and a real historic FCALP locomotive photo;
  - Chile's position card and Bolivia's position card.
- **Stakes (20–24):**
  - the rivers draw on, with the navy's roles, a real photo of the Strait of Tiquina, and the swim-ring gag;
  - Día del Mar (AI plate B5), with the empty chair "RSVP: NO";
  - Article 267 of the 2009 constitution, answering the 1904 "perpetuo";
  - Boliviamar, over a real CC0 photo of the coast at Ilo;
  - the ICJ 12–3 card, with grey bars and the "coffee sometime" tag.
- **Synthesis (25–26):** the full table with pins, red string and the row of receipts, plus "OUR READING". The callback "Most
  navies measure depth…" sits over a real Titicaca photo, with 3,810 m and 0 km of coast.

## House rules followed
- **Palette:**
  - cream, charcoal, crimson for evidence only (stamp, pins, string, circles), yellow for highlighter only;
  - Pacific teal #2C7A8C only for water (sea, lake, rivers, the strip's coast edge, the MAR tag, the Boliviamar bracket);
  - logo D top-right on every frame.
- **Real first** (§8c, owner 2026-11-19):
  - 6 real licensed photos are used, credited on screen and in `data/photo_credits.json`;
  - 3 AI plates are still used, only where no real image was found (B1 boat, B2 Topáter, B5 Día del Mar). Each is labelled AI
    ILLUSTRATION, and the reason is in `no_real_because` in `data/ai_ledger.json`;
  - B3, B4 and B6 were replaced by real photos.
- **Maps** are drawn from real geodata:
  - Natural Earth 1:50m countries, coastline, lakes and rivers (public domain);
  - relief from Terrarium elevation tiles (SRTM), height ×6, stated in every source line;
  - the animated maps are 04, 09, 14, 15, 20 and 25 (pins drop, routes and rivers draw, the strip lifts and peels).
- **No flags, emblems or faces.** No real person is drawn. Abaroa gets a plain text card.
- **Fairness:**
  - the 1874 tax gets both sides;
  - there is a card for Chile's position and a card for Bolivia's;
  - the ICJ finding for Chile is stated plainly, and both governments' reactions are attributed;
  - "OUR READING" is labelled as opinion.
- **Numbers come only from `dossier.json`.** Every frame has a source line.

## Things to know
- **The treaty is a reconstruction, not a scan.** Frame 02 is labelled "RECONSTRUCTION · TEXT OF THE 1904 TREATY, ART. II ·
  SCAN TO BE SOURCED".
  - As it stands, gate 3 (evidence first) is not met by a real document. Either a scan clears (Diario Oficial 27 Mar 1905, or
    FRUS 1905 page images) or you give an `evidence_waiver`.
  - The other typeset pages (07 signatures, 16 articles, 22 Art. 267, 24 ICJ summary) are also studio settings, labelled as
    such.
  - The other articles are blank bars, not invented text.
- **The Litoral strip is schematic:** a band along the real coast between about 21°S and 25°S, labelled "APPROX. 1879 BORDER,
  SCHEMATIC". It is not a surveyed historical boundary. Tarapacá is a label only, with no drawn boundary.
- **Marked TO CHECK on screen:**
  - the treaty wording against the scan;
  - the 1963/1966 navy dates;
  - the quintal unit;
  - the 1874 article number;
  - ~400 km / ~120,000 km² (Bolivian government figures);
  - the 1913 date;
  - ~76% Arica cargo (refresh before air);
  - ~5,000 personnel and training abroad;
  - Boliviamar "still mostly sand";
  - the ICJ 12–3 wording and paragraph 176 (the ICJ PDF has not been read).
- **Altitude:** the readout uses the dossier's ~3,810 m (Britannica). The voiceover says "about three thousand eight hundred".
- **Photo gaps:**
  - Wikimedia Commons refused every download with HTTP 429 (rate limit) all session; I backed off and did not work around it.
    Not fetched: the PD 1890 map of the nitrate works (British Library), Commons photos of Tiquina and Titicaca, and a Commons
    check for a licensed photo of the navy.
  - No licensed photo of the navy's boats was found, so B1 stays in the hook.
  - The FCALP locomotive photo is marked Public Domain on Flickr, but its date and original photographer are to check.
- **Downloads are gitignored:** `maps/` (geodata and tiles) and `assets/` are both ignored. Rebuild with `python3 -I geo.py &&
  python3 -I relief.py`. The real photos in `assets/real/` would need a commit rule if you want them kept.

## Still to decide
- **Changes** to the frames or the script.
- **The treaty receipt:** a scan, or an evidence waiver.
- **Go** for the video, and the **voice**: your ElevenLabs voice (with your permission) or a stand-in.
