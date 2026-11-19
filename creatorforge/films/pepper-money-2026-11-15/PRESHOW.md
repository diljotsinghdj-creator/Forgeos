# Pre-show list: Pepper Was Money (key frames, draft 4, 16:9)

These are 30 still key frames in story order, covering all five beats of SCRIPT_PLAN.md draft 4. That draft keeps the Vox × Johnny Harris
structure and puts the narration in a John Oliver satirical voice. There is no video, voice or music yet; video comes only after "go".

## What changed since draft 3
- **The new Print Facts palette:**
  - cream #F4EFE6, charcoal #1A1A1A, crimson #D93829 and highlighter yellow #F7D046 on every frame;
  - film accent: green #2F5D50 (the "three rules of money" board).
- **The comedy layer, which only targets documents and official language:**
  - sarcastic captions styled as archive tags:
    - "ITEM 5 · FILED UNDER: SEASONING";
    - "DEPARTMENT OF PEPPER (APPROX.)";
    - "STATUS: UNVERIFIED BRAG";
    - "EVERY RUNNER CHARGES FOR THE BATON";
    - "MOST BRITISH SENTENCE EVER SPOKEN IN COURT".
  - a smash-zoom receipt: the ransom list jumps from scale 1 to 1.32 on the pepper line, with a red circle;
  - the scarlet-trousers sight gag: a cut-out with a 4 px white border and a hard shadow, labelled ILLUSTRATION. Sources: the Ramsey Abbey rent of 1194 lists scarlet trousers.
- **Layout fixes** after my own review:
  - the trousers tag no longer covers the timeline;
  - the markup tag no longer covers the 25× box;
  - the 25× box no longer runs off the frame;
  - the map-table line now has a dark backing so it reads.

## What you're about to see
- **The cold open:** the pepper on your table, the 408 ransom list, the smash-zoom receipt and the title.
- **Johnny Harris layer:**
  - the investigator's map table: the real 1596 Linschoten chart (Library of Congress, public domain by age), with pins and string placed by hand;
  - the monsoon ships;
  - the papyrus and Kent charter discovery cards;
  - Gama's globe route round Africa.
- **Vox layer:**
  - chapter cards;
  - Pliny's prices as bars from zero;
  - the MYTH stamp and the 1 : 280 balance;
  - the 50 million sesterces;
  - the three rules of money;
  - the rent timeline;
  - the peppercorn-rent law;
  - the producer circles today;
  - the Kochi price.
- **Logo D** is in the top-right corner of every frame.

## Reconstructions and illustrations, labelled on the frame
- **The Muziris papyrus and the Kent charter** are studio reconstructions, each labelled with the original's reference. I haven't checked image licences for the real ones yet.
- **The 408 ransom page** is set in the studio from the translations of Zosimus.
- **The trousers cut-out** is drawn in the studio, labelled ILLUSTRATION.
- **The falling-price line** in chapter 7 is an illustrative trend, labelled as such, not a price series.
- **The warehouse plan** is a typical Roman layout, not this building's survey. The Forum photo shows the general area, not the exact spot.

## Numbers
- **Source of every figure:** `dossier.json`. Every figure is confirmed only from search-result snippets; the source pages can't be reached from this machine.
- **Our own calculation:** the gold price (about 1,125 denarii a pound), labelled on the frame.
- **Estimates, labelled on the frame:** the Muziris cargo's pepper share and the 25× markup.
- **Gama's "60 times the cost":** the frame and the script say it is an unverified brag.
- **Production figures:** FAO and the Spices Board disagree on India's output, and the frame says so.
- **Kochi price:** from 22 Aug 2026, the latest indexed; it needs refreshing before air.

## Photos and people
- **Photos:** Pixabay (peppercorns, white peppercorns, green pepper, gold bars, ginger, brass scale, spice sacks, Roman Forum, Marcus Aurelius bust).
- **No brands:** a pepper grinder showing a brand name was swapped out.
- **The bust:** shown neutrally, with nothing drawn on the face. No portrait of Pliny survives, and the frame says so.
- **No AI images.**

## Still to decide before the video
- **Go** or changes.
- **Voice:** the Kokoro stand-in (am_onyx), or your ElevenLabs voice with your permission.

## Added 2026-11-19: six AI plates (sheet `AI_PLATES_1`)
- **What you'll see:**
  - **The cream desk (P1)** now sits under every desk frame, noted in the source line. To keep it readable, desk pages use dark type, crimson handwriting, a cream logo patch and a source band.
  - **02a_siege:** Rome surrounded, 408.
  - **08a_ship:** the monsoon ship, Berenike → Muziris.
  - **10a_sack:** "a fortune you can carry on your shoulder".
  - **13a_relay:** the relay race, ~3 → ~80 ducats (UNESCO). No middle prices were invented.
  - **14a_demotion:** "the greatest demotion in culinary history".
- **House rules:**
  - Each plate is labelled AI ILLUSTRATION and logged in `data/ai_ledger.json`.
  - No faces or real people. Runners and the merchant are faceless and illustrative.
  - No AI chart, number or map. Every word is set by the studio.
  - Each plate is finished with `channels/design_kits/ai_finish.py --channel pf`.
- **One plate was redone:** the first relay take dressed a runner as a pharaoh, which is wrong for the 1400s. About 1,333 credits in all.
- **Still to fix:** the title card's subtitle sits on a pan of the scale. I'll fix it at the video stage.

## Updated 2026-11-19 (pass 5): more real pictures and motion, no AI (sheets `V5_1`–`V5_6`, motion sheet `M_5`)
Owner: "we need more real pictures, animation, motion graphics etc and less ai" (MASTER_DIRECTIVES §8c). Then: "strictly Vox x
Johnny Harris style". Every frame was put through the house seven-point test, and the frames that failed it were fixed.

- **The counts:**

  | | Before (draft 4 + AI plates) | Now |
  |---|---|---|
  | Frames in the film | 35 | 36 |
  | Frames with an AI plate in them | 18 (5 plates + the P1 desk under 13 desk/chart frames) | **0** |
  | Frames carrying real material | 26 (74%) | **32 (89%)** |
  | Motion builds | 17 timeline builds + 3 ship/globe moves | **23 timeline builds + 3 ship/globe moves = 26** (8 of them animated maps) |

  "Real material" means a licensed or public-domain photo, archive art, a real document or quote, or a map or chart from real
  data. The four frames without it are the 1 : 280 balance, the 50-million counter (it now has a real coin), and the two studio
  reconstructions (papyrus and charter), which are labelled.
- **What replaced each AI plate** (all six are marked `"retired"` in `data/ai_ledger.json`; `ai_frames.py` now builds the replacements):
  - **P1, the desk:** the drawn walnut desk again. The cream-desk legibility hack in `page()` is gone, and desk frames are back to dark styling.
  - **P2, 02a_siege:** a real 19th-century engraving captioned "ALARIC" (Public Domain Mark). It is taped to the desk, with a red circle on the city. The frame labels it as an artist's imagining, drawn 1,400 years later, not a record.
  - **P3, 08a_ship:** the Portus relief (Torlonia MT 430), a real Roman merchant ship carved in stone. It has a red circle on the sail and a Berenike → Muziris route card that draws on. The frame says it shows a ship at Rome's harbour, not one of the India run.
  - **P4, 10a_sack:** a real photo of a sack of picked pepper, with a yellow circle, the PFEFFERSACK card (Port of Hamburg FAQ, in the dossier) and the tag CONTENTS: A FORTUNE (APPROX.).
  - **P5, 13a_relay:** a new **animated map** from real geodata: Calicut → Aden → Cairo → Venice → Bruges, with "+ cut" popping at each hand-off and ~3 / ~80 ducats at the two ends. No middle prices were invented.
  - **P6, 14a_demotion:** Albert Camilli's watercolour *Pepper Grinder* (c. 1936, Index of American Design, National Gallery of Art, CC0) and a real photo of peppercorns, with the arrow "former currency".
- **New motion frames:**
  - **13b_shift** (4 · 5:10): the old relay greys out, Venice gets a red circle and a BYPASSED stamp, and the sea road Lisbon → Cape → Calicut draws on. Tag: Casa da Índia, c. 1500.
  - **15a_world** (5 · 6:46): producer circles grow from zero on the world map, pinned to the growing regions, with the Karnataka/Kerala card. It replaces the free-floating circle chart 15_today.
  - All three new maps use Natural Earth 1:50m, with India in its official boundary (DataMeet composite). Each one is a paper sheet taped to the map table, with pins, red string and handwritten tags. That is the Johnny Harris map table, returning in chapters 5, 6 and 8.
- **Fixes from the seven-point test:**
  - **07_myth:** the branded stock gold bars are swapped for a real gold aureus of Nero (The Met, CC0). This fixes a brand breach and adds real evidence.
  - **08_drain:** now has the same aureus, a red underline, and "Roman coins still turn up in Kerala". The Kottayam hoard is in the dossier; no coin count is shown.
  - **01_jar:** adds a red circle and "look closely." (deictic). The table tag now has a dark backing so it reads.
  - **05_three:** tape on the three photo cards, and "one personality, three outfits".
  - **17_end:** the ITEM 5 callback tag and a red circle.
  - **03_title:** the subtitle sits on a dark band and no longer sits on the scale pan. This was the open fix from the last pass.
  - **c02b_receipt:** the zoom no longer crops the handwritten note.
  - **s2_a–c:** the Calicut and Alexandria labels no longer sit under the ship or the chapter chip.
  - **Globe frames:** the kit's stray "GLOBE · 0%" readout is removed.
  - **Every dark frame:** the logo sits on a dark chip, so it reads over the chart.
- **Script:** `SCRIPT_TABLE.md` now points the rows at the new frames (rebuilt with `script_table.py`): 102 shots, average hold 4.5 s, longest 7.0 s, no pacing flags.
- **Dossier:** two caption and framing entries were added (the Portus relief caption; the relay bypassed, with Casa da Índia c. 1500). No new numbers.
- **Credits for the new photos** (full list in `data/photo_credits_2.json`; files in `assets/real2/`, gitignored; found via Openverse):
  - "Rome - Alaric", 19th-c. engraving, via History Maps / Flickr: Public Domain Mark.
  - "Portus relief (Torlonia MT 430) detail 016", Mark Landon, CC BY 4.0, Wikimedia Commons.
  - "Sack Of Picked Pepper Spikes", Steenbergs, CC BY 2.0, Flickr.
  - Albert Camilli, *Pepper Grinder*, c. 1936, NGA: CC0.
  - "Black Pepper IMG 4866 - 02", Hubertl, CC BY 4.0, Wikimedia Commons.
  - "Gold aureus of Nero", The Metropolitan Museum of Art: CC0.
  - Spare, not used yet: "Ostia antica-08" (ship mosaic), Patrick Denker, CC BY 2.0.
- **Still open:**
  - The bust (Marcus Aurelius) and the Kochi sacks are still Pixabay photos. The Kochi sacks show printed trade names on the burlap, which predates this pass: swap them or blur them before air.
  - Wikimedia rate-limited some downloads (429). I backed off and retried, never circumvented.
  - The Livre des merveilles pepper-harvest miniature (Marco Polo, BnF), which would be ideal, was not on Openverse under these licences.
