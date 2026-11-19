# Pepper Was Money: script, draft 5 (four-column)

- **Channel:** Print Facts, long form, 16:9, about 8½–9 minutes (draft 4 estimated 11; the timed table runs shorter), with 9:16 cutdowns from the acts marked ✂. Non-political.
- **Engine:** 3B, "pepper as money" (owner's pick, recorded in `pick.json`).
- **What changed from draft 4:**
  - The prose plan (`SCRIPT_PLAN.md`) is converted to the four-column table, written for motion (MASTER_DIRECTIVES §10b).
  - The facts and jokes are the same, and no claim is new.
  - Lines are split so that no canvas holds longer than the pacing gate.
  - Deictic lines are added ("Look closely at this jar", "Follow the list down", "Look at the string").
  - Act 3 opens with "But there was one question left…" instead of "Back to the ransom".
  - **Chappell v Nestlé** now matches the dossier: "a British judge in the House of Lords", with [1960] AC 87 on the card. The
    draft's "In 1960" is dropped from the voiceover.
- **Structure and voice:** the Vox × Johnny Harris five beats, in the John Oliver voice: fact → receipt → simile → snap back.
- **Canvas backbone:**
  - **The walnut desk** (drawn in the studio; the AI desk plate is retired, 2026-11-19) carries the receipts: the ransom page, the rent cards, the charter and the 2022 Act.
  - **The 1596 Linschoten chart** (Library of Congress) is the map table that the ships sail across.
  - Rome, the chalkboard and the globe slide onto the same desk. Hard cuts are kept for comedy beats only.
- **Palette:** cream #F4EFE6, charcoal #1A1A1A, crimson #D93829 for evidence, and yellow #F7D046 for highlighter sweeps only. The
  film accent is Venetian ledger green #2F5D50, used on the chalkboard.
- **Callbacks:**
  - "Item five: seasoning" is planted in act 1 and paid off in act 5.
  - The "scarlet trousers" are planted in act 3 and paid off in act 5.
  - The jar → ransom match cut opens the film and closes it.
- **Evidence first (gate 3):** the first explanation comes after a real document, the Zosimus ransom list (row 2).
- **Facts:** every figure is in `dossier.json`. Estimates, reported claims and our own calculation are labelled on screen.
- **Bracket notes:**
  - `[CUT]`: a 0.2 s music cut before a punchline, the only allowed hard cut.
  - `[HOLD 0.6s]`: a pause after a reveal.
  - `frame:` names the existing key frame (`html/`) that the row is built from.
- **Status:** for approval. No video until "go"; the owner chooses the voice.

**Timing (computed):** 102 shots · narration about 7:35 at ~150 WPM (music beds, holds and act breaks bring the cut to about 8½–9 min) · average hold 4.5 s · longest 7.0 s · pacing flags: none.

## 1 · Hook and question

| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |
|---|---|---|---|
| 1 · 0:00 | Look closely at this jar. There's one like it on almost every table in India. | Close-up photo of a pepper jar on the desk; a mono tag slides under it: `TABLE PEPPER · ANY KITCHEN · TODAY`. <br>`frame: 01_jar` | Locked macro at 2.2×, then a slow pull-out to 1.6×. `[SFX: room tone]` |
| 1 · 0:06 | I had never given it a single thought. Then I found this: a list from the year 408. | **Shot 1:** the jar pull-out ends on the round lid. **Shot 2:** match cut from the lid to a round ink stain on the Zosimus ransom page, lying on the same desk. <br>`frame: 02_ransom` | Shot 1 pull-out ends · Shot 2 match cut on the circle. `[SFX: page turn]` `[HOLD 0.6s]` |
| 1 · 0:13 | Rome is surrounded. The city is starving. | A real 19th-century engraving, ALARIC (public domain; labelled an artist's imagining), taped to the desk; a red marker circle on the city; a crimson date tag: `ROME · 408 CE · UNDER SIEGE`. <br>`frame: 02a_siege` | Slow push-in 1.0× → 1.2×; the circle draws on. `[SFX: low drone]` |
| 1 · 0:16 | So it does what cities did back then. It pays the army to go away. | The list's heading highlights: the terms of the ransom. <br>`frame: 02_ransom` | Push continues 1.2× → 1.3×. Yellow sweep on the heading. |
| 1 · 0:22 | Follow the list down. Five thousand pounds of gold. Thirty thousand pounds of silver. | Each line takes a yellow highlighter sweep as it is read. <br>`frame: c02b_receipt` | Tilt down the page, one line per beat. `[SFX: coin pour]` |
| 1 · 0:28 | Four thousand silk tunics. Three thousand scarlet skins. | Two more lines take their sweeps. <br>`frame: c02b_receipt` | Tilt continues. `[SFX: cloth rustle]` |
| 1 · 0:31 | And three thousand pounds of pepper. | The last line: "pepper" takes a red ink circle. <br>`frame: c02b_receipt` | `[CUT]` 1-frame smash-zoom 1.0 → 1.32 on "pepper". Red circle draws at 12 fps. `[SFX: stamp thud]` `[HOLD 0.6s]` |
| 1 · 0:34 | Pepper. In a ransom. Listed right next to the gold. | An archive-tag caption thuds on beside the circle: `ITEM 5 · FILED UNDER: SEASONING`. <br>`frame: c02_ransom` | Tag lands at 12 fps. `[SFX: typewriter bell]` |
| 1 · 0:38 | Like a hostage-taker going "and, if it's not too much trouble, something for the soup." | The tag types a second line, letter by letter: `REQUESTED BY: THE BESIEGERS`. <br>`frame: c02_ransom` | Slow drift right as it types at 12 fps. `[HOLD 0.6s]` |
| 1 · 0:45 | That's strange. Unless, for a very long time, pepper wasn't really a spice at all. | The page slides off the desk; the title card slides on: PEPPER WAS MONEY. <br>`frame: 03_title` | Paper slide, 12-frame ease-out. `[SFX: music in]` |
| 1 · 0:51 | So I went looking. How does a spice become money? | Title holds; logo D top-right. <br>`frame: 03_title` | Slow push 1.0× → 1.08×. `[HOLD 0.6s]` |

## 2 · Map and history ✂

| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |
|---|---|---|---|
| 2 · 0:55 | I started where the pepper starts. On a map. | The map table: the 1596 Linschoten chart (Library of Congress) fills the desk. <br>`frame: 04_maptable` | Top-down; slow pull-out from the chart's cartouche to the whole sheet. |
| 2 · 0:59 | Right here, on this coast, a red pin goes in: Malabar. | A red pin pushes into the Malabar coast; card: "Malabar: the vine grows here". <br>`frame: 04_maptable` | Push-in 1.0× → 1.5× on the pin. `[SFX: pin push]` `[HOLD 0.6s]` |
| 2 · 1:04 | Black pepper is a berry from a climbing vine, Piper nigrum, native to the Western Ghats of India. | **Shot 1:** a vine photo card slides onto the chart beside the pin. **Shot 2:** close on its pencil label: *Piper nigrum* · WESTERN GHATS. <br>`frame: 04_maptable` | Shot 1 card slides in with a drop shadow · Shot 2 push-in 1.0× → 1.3×. `[SFX: pencil]` |
| 2 · 1:11 | Black, white, green. Same plant, picked and treated differently. | Three photo cards slap down in a row: BLACK · WHITE · GREEN. <br>`frame: 05_three` | Cards slap down at 12 fps, one per word. `[SFX: paper slap ×3]` |
| 2 · 1:15 | Pepper basically has one personality and three outfits. | Same three cards. <br>`frame: 05_three` | Hard stop. `[HOLD 0.6s]` |
| 2 · 1:19 | For most of history, if you wanted pepper, it came from this one coast. | Back on the chart: the pin glows crimson. <br>`frame: s1_a` | Whip-pan back to the chart. |
| 2 · 1:24 | Which meant everybody who wanted it had to come here. | A red string draws from Malabar out toward the Red Sea. <br>`frame: s1_a` | Dashed route draws at constant speed. `[SFX: string pull]` |
| 2 · 1:28 | Rome wanted it badly. Follow this ship. Roman crews waited for the summer monsoon at Berenike, | **Shot 1:** a real Roman merchant ship, the Portus relief (Torlonia collection, photo CC BY), taped to the desk; a red circle on the sail; `FOLLOW THIS SHIP`. **Shot 2:** back on the chart, the drawn ship leaves Berenike; a wind arrow points to India: `SUMMER · SOUTH-WEST MONSOON`. <br>`frame: 08a_ship` | Shot 1 push-in on the sail · Shot 2 smooth pan east with the ship. `[SFX: waves, wind]` |
| 2 · 1:35 | rode it across the Arabian Sea to Muziris, and rode the winter wind back, loaded. | The ship reaches Muziris; the wind arrows flip: `WINTER · THE WIND TURNS`. <br>`frame: s1_c` | Pan continues; arrows flip at 12 fps. |
| 2 · 1:41 | We know what Rome paid, because Pliny the Elder wrote the prices down, around 77 CE. | A marble bust on dark stone (labelled: Marcus Aurelius; no portrait of Pliny survives). Pliny's line types beside it. <br>`frame: r1_a` | Slow push 1.0× → 1.15×. `[SFX: typewriter]` |
| 2 · 1:47 | Long pepper: fifteen denarii a pound. White: seven. Black: four. | Price bars rise from zero; the black-pepper bar lights yellow. <br>`frame: 06_pliny` | Bars grow one per number. `[SFX: projector click ×3]` |
| 2 · 1:51 | And look at this line. He grumbled that Romans bought pepper by weight, "as if it were gold or silver." | **Shot 1:** the bust frame; Pliny's quote finishes typing. **Shot 2:** close on the quote; yellow highlighter sweep on "as if they were so much gold or silver". <br>`frame: r1_b` | Shot 1 slow push · Shot 2 push-in 1.0× → 1.4×, sweep at constant speed. `[SFX: marker squeak]` |
| 2 · 1:59 | You've heard pepper was "worth its weight in gold." | A MYTH? stamp hovers over the desk. <br>`frame: 07_myth` | `[CUT]` music. `[HOLD 0.6s]` |
| 2 · 2:03 | It wasn't. By Pliny's own prices, one pound of gold bought about two hundred and eighty pounds of black pepper. | **Shot 1:** a balance; one pan holds 45 gold aurei, the other is empty (label: OUR CALCULATION). **Shot 2:** peppercorns pour into the empty pan, the counter running 0 → 280 LB. <br>`frame: r2_b` | Shot 1 locked wide · Shot 2 locked; the counter runs as the corns pour. `[SFX: pour]` |
| 2 · 2:11 | That isn't "worth its weight in gold." | The MYTH stamp slams down. <br>`frame: r2_c` | Stamp at 12 fps. `[SFX: stamp thud]` |
| 2 · 2:14 | That's "worth its weight in a large, reasonably priced bag." | Same frame; the scale settles with a creak. <br>`frame: r2_c` | Scale settles over 12 frames. `[HOLD 0.6s]` |
| 2 · 2:19 | So pepper wasn't priced like gold. It was traded like gold: weighed, stored, counted. Hold on to that. | **Shot 1:** the scale settles level. **Shot 2:** three small tags pop on: WEIGHED · STORED · COUNTED. <br>`frame: r2v` | Shot 1 slow push · Shot 2 tags pop at 12 fps. `[SFX: scale creak]` |
| 2 · 2:26 | Rome bought so much that Pliny complained India took fifty million sesterces out of the empire every year. | **Shot 1:** Pliny's complaint as a quote card. **Shot 2:** a counter lights 50,000,000; tag `INDIA ALONE · PLINY, NAT. HIST. 6.26`. <br>`frame: 08_drain` | Shot 1 card slides in · Shot 2 the counter rolls. `[SFX: low hit]` |
| 2 · 2:33 | They even built warehouses just for it. The Horrea Piperataria. | Duotone Forum photo; plan card slides on: HORREA PIPERATARIA, drawing on room by room. <br>`frame: r3_b` | Slow pan across the Forum. `[SFX: paper slap]` |
| 2 · 2:37 | A government building dedicated to pepper. Imagine the job title. | Archive tag thuds on: `DEPARTMENT OF PEPPER (APPROX.)`. <br>`frame: c_r3v` | Tag lands at 12 fps. `[HOLD 0.6s]` |
| 2 · 2:42 | And then I found a receipt. A papyrus in Vienna lists one ship's cargo from Muziris: | Papyrus reconstruction (labelled) slides onto the desk. <br>`frame: 09_papyrus` | Card slides in with a drop shadow. `[SFX: paper]` |
| 2 · 2:48 | about eleven hundred and fifty talents. Historians think most of it was pepper. | A value bar beneath it, two-thirds shaded, tag `ESTIMATE`. <br>`frame: 09_papyrus` | Bar fills from zero. `[SFX: register]` |
| 2 · 2:53 | And the money flowed the other way. Roman gold coins keep turning up in the soil of Kerala. | **Shot 1:** back on the chart, the red string's arrow flips: gold goes back toward India. **Shot 2:** small gold pins pop onto the Kerala coast. <br>`frame: s1_c` | Shot 1 whip-pan to the chart · Shot 2 push-in on Kerala, pins pop at 12 fps. `[SFX: coin spin]` |

## 3 · The mechanics: how a spice becomes money ✂

| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |
|---|---|---|---|
| 3 · 3:00 | But there was one question left. Why would anyone accept pepper as payment? Think about what money needs to do. | **Shot 1:** the ransom card slides back on, `ITEM 5` circled again, with a new tag: `WHY?`. **Shot 2:** a chalkboard (film accent: Venetian ledger green), a blank three-line checklist. <br>`frame: 10_rules` | Shot 1 card slides in · Shot 2 whip-pan to the board. `[SFX: chalk]` |
| 3 · 3:08 | One: it has to last. Dried pepper keeps for years. | ✓ IT LASTS. <br>`frame: 10_rules` | Chalk tick at 12 fps. `[SFX: chalk tick]` |
| 3 · 3:12 | Two: it has to be worth a lot for its size. A sack of pepper is a fortune you can carry on your shoulder. | **Shot 1:** ✓ SMALL BUT VALUABLE. **Shot 2:** a real photo of a sack of picked pepper (CC BY); a yellow marker circle; card `PFEFFERSACK · "pepper sack"`; tag `CONTENTS: A FORTUNE (APPROX.)`. <br>`frame: 10a_sack` | Shot 1 chalk tick · Shot 2 slow push into the sack; the card slides on. |
| 3 · 3:22 | Three, the big one: other people have to want it. And everybody wanted pepper. | ✓ EVERYONE ACCEPTS IT. <br>`frame: 10_rules` | Chalk tick. `[SFX: music lift]` `[HOLD 0.6s]` |
| 3 · 3:28 | Tick all three, and it doesn't matter that it's a berry. It works as money. And in medieval Europe, it did. | **Shot 1:** the three ticks glow on the board. **Shot 2:** a single peppercorn glows on the scale beside it. <br>`frame: 10_rules` | Shot 1 hold on the ticks · Shot 2 rack from the board to the peppercorn. |
| 3 · 3:37 | In London, an old toll code says German merchants owed the king ten pounds of pepper at Christmas. | **Shot 1:** the toll text card slides on. **Shot 2:** close on "at Christmas". <br>`frame: 11_rents` | Shot 1 card slides in · Shot 2 push-in 1.0× → 1.3×. |
| 3 · 3:44 | And again at Easter. | "10 lb pepper" takes a red circle. <br>`frame: 11_rents` | 1-frame smash-zoom 1.0 → 1.32. `[SFX: stamp thud]` |
| 3 · 3:45 | The king's seasonal greetings were, apparently, "pepper, please." | Same card. <br>`frame: c11_rents` | `[HOLD 0.6s]` `[SFX: church bell, faint]` |
| 3 · 3:49 | In Genoa, in 1156, you could repay a debt in pepper or in coin. Your choice. | Timeline pin 1156 on the rents strip. <br>`frame: c11_rents` | Pan along the strip. |
| 3 · 3:56 | Like a card machine that also accepts condiments. | Cut-out sight gag thuds on: a card terminal with a pepper slot (ILLUSTRATION). <br>`frame: c11_rents` | Cut-out drops in at 12 fps. `[SFX: paper slap]` |
| 3 · 3:59 | In 1194, an English abbey's yearly rent was a thousand eels, two pounds of pepper, two of ginger… | **Shot 1:** the rent card slides on, headed `ABBEY RENT · 1194`. **Shot 2:** close on the list, building item by item. <br>`frame: c11_rents` | Shot 1 card slides in · Shot 2 one tick per item. `[SFX: tick ×3]` |
| 3 · 4:06 | …and a pair of scarlet trousers. | The trousers cut-out slaps onto the ledger; tag `LINE ITEM 4 · NO FURTHER DETAILS`. <br>`frame: c11_rents` | `[CUT]` 0.2 s. Cut-out slaps on in one frame. `[HOLD 0.6s]` |
| 3 · 4:09 | Nobody in the record explains the trousers. I checked. | Same frame. <br>`frame: c11_rents` | `[SFX: typewriter bell]` |
| 3 · 4:13 | In Kent, around 1270, a plot of land rented for half a pound of pepper a year. | Charter reconstruction (labelled) on the desk; yellow circle on the rent line. <br>`frame: 12_charter` | Push-in on the rent line. `[SFX: wax seal]` |
| 3 · 4:20 | The charter still exists. It's in Oxford. I looked it up. | Archive tag: `HELD IN OXFORD`. <br>`frame: 12_charter` | `[HOLD 0.6s]` |
| 3 · 4:25 | London's pepper dealers had organised by 1180. As the Pepperers, they became the Grocers' Company, which still exists. | **Shot 1:** a name card: PEPPERERS · 1180. **Shot 2:** the arrow draws to GROCERS' COMPANY, with a tag: `STILL EXISTS`. <br>`frame: 12_charter` | Shot 1 card slides in · Shot 2 the arrow draws on at constant speed. |
| 3 · 4:32 | In German, a rich merchant got a nickname. Pfeffersack. Pepper sack. | Kinetic type: PFEFFERSACK pops on, letter by letter. <br>`frame: 12_charter` | Letters pop at 12 fps. `[SFX: pop]` |
| 3 · 4:36 | So somebody was making a fortune moving it. I followed the money, port by port. | Back on the chart: a string begins at Calicut. <br>`frame: s2_a` | Whip-pan to the chart. `[SFX: ship creak]` |
| 3 · 4:42 | One estimate: a hundredweight of pepper cost about three ducats in Calicut, | Price tag pops at Calicut: ~3 DUCATS. <br>`frame: s2_b` | Ship sets off; dashed route draws. |
| 3 · 4:47 | and about eighty by the time it was sold on in Europe. | The ship passes the Red Sea and Alexandria; a tag pops at each stop. <br>`frame: s2_c` | Pan with the ship. `[SFX: coin tap per stop]` |
| 3 · 4:52 | Every port, every ship and every middleman took a cut, until the price was roughly twenty-five times the start. | **Shot 1:** price tags pop along the route, one per stop. **Shot 2:** card: `~25× ON THE WAY`; caption `MARKUP · PER HUNDREDWEIGHT · UNESCO ESTIMATE`. <br>`frame: 13_markup` | Shot 1 pull-out along the route · Shot 2 the card slides on. `[SFX: register]` `[HOLD 0.6s]` |
| 3 · 5:00 | It's the world's longest relay race, where every runner charges you for the baton. | The map table widens to a real map (Natural Earth; India in its official boundary): the red string runs Calicut → Aden → Cairo → Venice → Bruges; a `+ cut` tag pops at every hand-off, ~3 DUCATS at one end, ~80 at the other; tag `EVERY RUNNER CHARGES FOR THE BATON`. <br>`frame: 13a_relay` | The string draws at constant speed; tags pop at 12 fps. `[SFX: coin tap per hand-off]` |

## 4 · The stakes: what it did to the world ✂

| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |
|---|---|---|---|
| 4 · 5:06 | Venice sat at the end of that relay and got rich. | Venice glows at the end of the route. <br>`frame: c13_markup` | Push-in on Venice. |
| 4 · 5:10 | Which gave everyone else an idea. What if you skipped the relay entirely? | Same map: the old relay greys out, Venice takes a red circle and a `BYPASSED` stamp; a new red string draws from Lisbon down the coast of Africa, round the Cape, to Calicut; tag `Casa da Índia, Lisbon, c. 1500`. <br>`frame: 13b_shift` | The old line fades · the new string draws south. `[SFX: riser]` |
| 4 · 5:15 | On 20 May 1498, Vasco da Gama's ships reached the coast near Calicut, today's Kozhikode, | Globe: the ship sails Lisbon → Cape → Calicut; a date counter runs to 20 MAY 1498. <br>`frame: s3_b` | The globe turns with the ship. `[SFX: waves]` |
| 4 · 5:21 | having sailed all the way round Africa. Look at the string. It has to go the long way round. | **Shot 1:** the red string wraps around the Cape. **Shot 2:** pull-out to the whole route, Lisbon to Calicut. <br>`frame: s3_c` | Shot 1 the string draws · Shot 2 smooth pull-out on the globe. |
| 4 · 5:29 | Some histories say the pepper he brought home paid for the voyage sixty times over. | `60×?` with a REPORTED tag. <br>`frame: c_s3_c` | Tag lands. |
| 4 · 5:35 | Nobody has the original accounts, so we'll file that under "people bragging in the 1500s." | Archive tag thuds on: `STATUS: UNVERIFIED BRAG`. <br>`frame: c_s3_c` | `[SFX: stamp thud]` `[HOLD 0.6s]` |
| 4 · 5:41 | Then the race was on. A Portuguese royal monopoly. The English East India Company in 1600. The Dutch company in 1602. | **Shot 1:** timeline stamps land on 1498 · 1500. **Shot 2:** stamps land on 1600 (EIC) · 1602 (VOC). <br>`frame: 18_globe` | Pan along the timeline, one stamp per date. `[SFX: stamp ×4]` |
| 4 · 5:50 | Empires, chartered companies and fleets, organised in large part around a seasoning. | Ship icons multiply on the globe. <br>`frame: 18_globe` | Slow pull-out. `[SFX: swell]` |
| 4 · 5:55 | More ships, more routes, more pepper. And you can probably guess what happens next. | The ship icons crowd the sea lanes. <br>`frame: 18_globe` | `[HOLD 0.6s]` |
| 4 · 6:01 | By the sixteen hundreds, pepper prices in Europe were falling. | An illustrative falling line (labelled ILLUSTRATIVE) draws across the ledger. <br>`frame: 14_fall` | Line draws at constant speed. `[SFX: glitch]` |
| 4 · 6:05 | Remember rule three? Money only works while people really want it and can't easily get more. | The checklist returns; tick three flickers. <br>`frame: c14_fall` | Whip-pan to the board; the tick flickers at 12 fps. |
| 4 · 6:11 | Once pepper was everywhere, it stopped being money and went back to being a spice. | The scale: the pepper pan rises, empty. <br>`frame: c14_fall` | `[SFX: scale creak]` |
| 4 · 6:17 | The greatest demotion in culinary history. | A real 1936 watercolour of a pepper grinder (Index of American Design, NGA, CC0) and a photo of peppercorns on the desk; arrow: "former currency"; tag `FORMER CURRENCY · NOW SEASONING`. <br>`frame: 14a_demotion` | Slow push on the grinder. `[HOLD 0.6s]` |

## 5 · Synthesis

| Beat / Time | Voiceover (spoken) | Canvas layer (what's on screen) | Camera & motion cue |
|---|---|---|---|
| 5 · 6:20 | Except it left one fossil behind. Look at this line in English law. | The 2022 Act text slides onto the desk. <br>`frame: c14_fall` | Card slides in. |
| 5 · 6:25 | A "peppercorn rent" is still a valid payment. One single peppercorn. | "one peppercorn" takes a red circle. <br>`frame: c14_fall` | 1-frame smash-zoom 1.0 → 1.32. `[SFX: stamp]` `[HOLD 0.6s]` |
| 5 · 6:30 | In one famous case, a British judge in the House of Lords said a peppercorn still counts, even if the person paid doesn't like pepper. | **Shot 1:** the quote card: *Chappell v Nestlé* [1960] AC 87 · LORD SOMERVELL. **Shot 2:** close on "even if the promisee does not like pepper". <br>`frame: c14_fall` | Shot 1 card slides in · Shot 2 push-in, yellow sweep. `[CUT]` 0.2 s. |
| 5 · 6:41 | Which is the most British sentence ever spoken in a court. | An archive tag thuds onto the card: `HOUSE OF LORDS · PEPPER PREFERENCES: IRRELEVANT`. <br>`frame: c14_fall` | Tag lands at 12 fps. `[HOLD 0.6s]` |
| 5 · 6:46 | Today Vietnam grows the most pepper, about a third of the world's crop. | Producer circles grow on a real world map (Natural Earth; India in its official boundary), pinned to the growing regions (area ∝ tonnes; SOURCES DIFFER tag). <br>`frame: 15a_world` | Circles grow from zero, one per country. `[SFX: pop ×4]` |
| 5 · 6:51 | In India, the top grower isn't Kerala, where it began, but Karnataka next door. | Karnataka / Kerala card slides onto the map. <br>`frame: 15a_world` | Push-in on India. |
| 5 · 6:56 | In Kochi, a kilo trades at around seven hundred rupees. | Kochi tag: ₹695/kg (refresh before air). <br>`frame: 16_kochi` | Tag pops. `[SFX: market ambience]` |
| 5 · 7:00 | So, back to the jar on your table. How does a spice become money? | The jar returns; match cut to the ransom list. <br>`frame: 17_end` | Match cut on the circle again. |
| 5 · 7:06 | When it lasts, when it's worth a lot for its size, and when everybody agrees to want it. | The three ticks glow, one per clause: LASTS · SMALL BUT VALUABLE · EVERYONE WANTS IT. <br>`frame: 17_end` | One push per tick. `[SFX: three soft hits]` |
| 5 · 7:13 | For fifteen hundred years, people agreed on a dried berry from the Western Ghats. | The two receipt cards slide in side by side. <br>`frame: 17_end` | Slow pull-out. |
| 5 · 7:19 | Rome filed it next to the gold. An abbey filed it next to the trousers. | Ransom card `ITEM 5 · SEASONING` and rent card with the trousers, side by side. <br>`frame: 17_end` | One push per card. `[SFX: typewriter bell]` `[HOLD 0.6s]` |
| 5 · 7:25 | Which raises a question worth sitting with. | A yellow question card slides up. <br>`frame: 17_end` | Slow push. |
| 5 · 7:28 | What are we treating as money today that people will one day find just as strange? | The question types onto the yellow card; logo D. <br>`frame: 17_end` | Types at 12 fps. `[SFX: final chord, music out]` `[HOLD 0.6s]` |

---

## Guardrails this draft keeps
- **The myth:** "worth its weight in gold" is shown as a myth, with Pliny's numbers. The gold price is our calculation, and the
  frame says so.
- **Dates and figures:**
  - The ransom is dated 408, not 410.
  - The fifty million sesterces are for India alone.
  - The Billingsgate toll date is disputed, so the script says only "an old toll code".
- **Marked "reported" or "estimate" on screen:**
  - Gama's "60×", with the tag "unverified brag";
  - the Muziris pepper share;
  - the ~25× markup.

  There are no dowry or "tax" claims.
- **Sight gags:**
  - The card terminal with a pepper slot, the trousers cut-out and the relay baton are labelled ILLUSTRATION.
  - Every caption joke sits on a sourced fact.
- **People:** no living person is mocked. The bust is shown neutrally, and the frame says no portrait of Pliny survives.
- **Clips:** no copyrighted footage; only public-domain documents and labelled reconstructions.

## To check before voice (⚠)
1. **Kochi price** (₹695/kg, 22 Aug 2026): refresh in the week the film is scheduled.
2. **The 2022 Act section number** for the peppercorn rent: still snippet-only.
3. **Image licences:** the papyrus, coin and charter images are still unchecked.
4. **Producer shares:** Vietnam's ~30%, and Karnataka against Kerala. FAO and the Spices Board disagree, and the frame says so.

## New visual beats not yet in the key frames
These are in the table but not yet in `html/`. They will be built and shown to the owner before any render.
- **Row 1 · 0:38:** the tag's second line, `REQUESTED BY: THE BESIEGERS`.
- **Act 2:** the vine card's close-up label, and the three WEIGHED · STORED · COUNTED tags.
- **Act 2:** the string's arrow flipping as gold goes back to India.
- **Act 3:** the ransom card returning with a `WHY?` tag, which bridges into the chalkboard.
- **Act 3:** a sight gag of a paper silhouette carrying a sack, with the tag `CONTENTS: A FORTUNE` (ILLUSTRATION).
- **Act 3:** the relay-baton cut-outs along the markup route (ILLUSTRATION).
- **Act 5:** the tag `HOUSE OF LORDS · PEPPER PREFERENCES: IRRELEVANT` on the Chappell card.
