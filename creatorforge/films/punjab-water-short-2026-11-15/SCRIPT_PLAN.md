# [SCRIPT_PLAN] Punjab's Water Overdraft: Print Facts Short (draft 1, 2026-11-15)

- **Channel:** Print Facts.
- **Format:** YouTube Short, 9:16, about 58 s.
- **Engine:** 2A, "the bank account" (picked by the owner).
- **Status:** script for approval. No visuals or video until the owner approves, and video only after "go".
- **Number series:** every number is from the 2025 national groundwater assessment (Ministry of Jal Shakti / CGWB),
  unless the line says otherwise. Sources are in `dossier.json`.

## Visual DNA (this Short only)
- **Palette:** ledger paper (#F3EEDF), bank-ink navy (#1F2A44), overdraft red (#C8312B), with the signature yellow #FFDD33 on the key number.
- **Texture:** a passbook and a bank statement on a desk, stamped and highlighted; satellite and relief for the land.
- **Type:** a typewriter mono for figures, condensed sans for headlines, and handwriting for the investigator's notes.
- **Opening shot:** a real document. It is new for this channel: none of the last three openers was a bank-statement page.
- **Not reused:** the bowl, reverse autopsy, historical echo, Trojan horse and scale shock engines; the Delhi haze look.

## Beats (line → visual code → sound)

| # | Time | Narration (Kokoro stand-in, or the owner's voice) | Visual (code) | Sound |
|---|---|---|---|---|
| 1 | 0.0–3.5 | This is Punjab's water bank statement. And it's in the red. | `[25D-DOC]` The CGWB assessment page as a bank statement. The highlighter sweeps "Punjab … 156%" and a red OVERDRAWN stamp lands. | stamp thud |
| 2 | 3.5–8.0 | Every year, rain and rivers let Punjab safely draw about 16.8 billion cubic metres of groundwater. It draws 26.3. | `[2D-BAR]` Two passbook columns, DEPOSITS 16.80 and WITHDRAWALS 26.27 (BCM), drawn from zero. The withdrawal bar runs off the page. | pen scratch, cash-register tick |
| 3 | 8.0–11.5 | That's 156 percent of what it can safely take. The highest of any state. | `[GLOW]` 156% lit in yellow. A small ranked strip: Punjab 156, Rajasthan 147, Haryana 137. | low hit |
| 4 | 11.5–15.5 | 111 of its 153 blocks are overdrawn. | `[3D-MAP]` + `[3D-PIN]` Punjab relief; the over-exploited blocks turn red one by one (12 fps), counter 111/153. | ticking |
| 5 | 15.5–20.5 | NASA's GRACE satellites saw it from orbit. Between 2002 and 2008, north-west India lost 109 cubic kilometres of groundwater. | `[ORBIT]` Satellite view of NW India with the study area outlined, and a "109 km³" tag. Nature 2009 is on screen. | radio-static whoosh |
| 6 | 20.5–24.5 | Most of it goes on one crop. A kilo of paddy can take around 3,000 litres of water. | `[2D-UNIT]` One rice sack with water buckets popping in beside it; label "~3,000 L per kg of paddy (ICAR estimate; ranges 1,500–4,500)". | water drops |
| 7 | 24.5–30.0 | So why keep withdrawing? Since 1997, power for farm pumps has been free. And the government buys almost every grain of paddy at a fixed price. | `[25D-NODE]` A chalk chain: FREE POWER (1997) → PUMP RUNS → PADDY → GOVT BUYS AT MSP → MORE PADDY. | chalk on board |
| 8 | 30.0–34.5 | For a farmer, it's the safest bet. Maize often sells below its support price. Paddy doesn't. | `[25D-CARD]` A farmer's ledger card (no person): "paddy: assured buyer" vs "maize: sold below MSP". A side-label reads "the farmers' side". | paper slide |
| 9 | 34.5–39.5 | The overdraft is shrinking, slowly: from 164 percent in 2023 to 156 now, as canals water more fields. | `[2D-LINE]` 2017 165.8 → 2020 164.4 → 2022 166.0 → 2023 163.8 → 2024 156.9 → 2025 156.4, drawn left to right; the dip is highlighted. | rising tone |
| 10 | 39.5–44.5 | But a 2019 draft government report warned Punjab could turn into a desert within 25 years at this pace. | `[25D-DOC]` A newspaper clipping of the draft-report warning, labelled DRAFT · CGWB NORTH-WESTERN REGION · 2019, AS REPORTED. | paper rustle |
| 11 | 44.5–50.5 | For decades, the water sat about half a metre deeper every year. Every new pump has to dig further. | `[3D-MODEL]` A cutaway of a tubewell: the water table steps down year by year and the pipe extends. Label "~0.5 m/yr, CGWB, to 2017". | drill hum |
| 12 | 50.5–58.0 | A bank lets you run an overdraft. An aquifer doesn't. So what should Punjab grow instead? | End card: the passbook closes, CLOSING BALANCE: ? in yellow, then a question card. | single bell |

**Word count:** about 160, at about 2.8 words a second.

**Pacing check:**
- every still holds 4.5 s or less;
- the builds (beats 2, 5, 7, 9–12) hold 7.5 s or less;
- the mean is 4.8 s.

Beat 12 (7.5 s, the end card) is the only one over the 7 s building limit. I will trim it to 7.0 s in the edit.

## Fairness and wording rules applied
- The farmers' reasons (beats 7–8) are shown before the warning (beat 10). Nobody is blamed by name.
- "Desert in 25 years" is attributed to a 2019 **draft** report as the press reported it. It is never stated as fact.
- "Half a metre a year" is dated to CGWB data through 2017, not presented as today's rate.
- The GRACE figure is for north-west India (Punjab, Haryana, Rajasthan, Delhi), not Punjab alone. The on-screen label says so.
- No real farmer's face; only objects, documents, maps and satellite imagery.

## Open checks before any render ([ACCESS / SYSTEM BLOCKER])
cgwb.gov.in, eparlib.sansad.in, eparlib.nic.in and pib.gov.in refuse connections from this container. Every number
was confirmed only from search-result snippets of those official pages. Before the video, either:
- the owner allows those hosts in the session's network settings so I can read the PDFs; or
- the owner accepts "snippet-confirmed" for this Short. The PRESHOW will say so.
