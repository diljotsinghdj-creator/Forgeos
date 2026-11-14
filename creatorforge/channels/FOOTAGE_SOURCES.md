# Free footage, photo and audio sources (both channels)

Owner's rule: **free only.** If a source costs money now or later, it is dropped. Every clip carries a credit line
(top-left, small, on screen while the clip plays) and a row in the film's `assets/credits.json`.

## The licence test (applies to every source)

| Allowed | Not allowed |
|---|---|
| Public domain, Public Domain Mark, CC0 | Any **NC** (non-commercial): the channels are monetised |
| CC BY (credit on screen + in the description) | Any **ND** (no derivatives): we cut, crop and grade |
| CC BY-SA (credit; our film is not relicensed, but keep SA clips to short excerpts and note them) | "Educational use only", "subject to restrictions", "© … all rights reserved" on the title card |
| GODL-India (Indian government works, credit the ministry) | Home movies / private individuals (owner's rule) |

A licence field is not the last word: **read the title card.** In the test pull, two "public domain" films carried
their own notices (Encyclopaedia Britannica 1949 "Copyright MCMXLIX"; the 1945 OWI film "subject to published
restrictions"). Such clips go to the owner as *needs a check*, never straight into a film.

## Video: wired into the worker (`providers/stock_video.py`), keyless unless marked

| Source | What it is good for | Licence handling in code | Fit |
|---|---|---|---|
| **NASA Images** (`nasa`) | launches, Earth from orbit, space | public domain | both |
| **NASA SVS** (`svs`) *new* | climate and data visualisations: sea level, floods, ice, fires, CO2 | public domain; credit "NASA's Scientific Visualization Studio" | Print Facts (climate, disasters), Dragon (awe, scale) |
| **Wikimedia Commons** (`wikimedia`) | parliaments, events, explainer animations | regex keeps PD / CC0 / CC BY / CC BY-SA only | both |
| **Prelinger Archives** (`archive`) | 1930s–70s US educational films: emotions, children, school, crowds, campaigns | now reads each film's `licenseurl`; skips `-nc` / `-nd` and home movies | Dragon (mental-hygiene films are a gift), Print Facts history |
| **Library of Congress films** (`loc`) *new* | 1890s–1920s actualities: floods, elections, crowds, cities | kept only if published before 1930 or "no known restrictions" | Print Facts history openers |
| **Wellcome Collection** (`wellcome`) *new* | medicine, mind, health history | keeps CC BY / CC0 / PDM only (most of the collection is NC: dropped) | Dragon Psychology |
| **Europeana** (`europeana`) *new, key* | European archives, newsreels | `reusability=open`, then drops NC/ND/InC | Print Facts (Europe, Russia) |
| **Pixabay / Pexels** (key) | modern b-roll: people, cities, hands, phones | their own free licence (no attribution needed, credit anyway) | Dragon b-roll, Print Facts texture |

Keys (Europeana, Pixabay, Pexels, DVIDS) are **free personal keys** that live only in the pod's environment
(`EUROPEANA_KEY`, etc.). They never go in chat or in a file. Without a key, that source is skipped silently.

Not wired yet (probed): **DVIDS** (US military, public domain, free key: 403 without one); **EU Audiovisual Service**
(EU institutions, free reuse with credit; no clean API yet, manual pulls only).

## Photos (`providers/stock_photo.py`, already wired)

Openverse, Wikimedia Commons, NASA, Library of Congress, Smithsonian Open Access (CC0), Europeana.
Plus by hand, with credit: **PIB / GODL-India** (Indian ministers and events), **Kremlin.ru** (CC BY 4.0),
**White House / US government** (public domain), **UN Photo** (only items marked free to use).
Real people only from these credited photos; never AI faces.

## Audio

- **Our own score** (`studio/score_bars.py`): synthesised, nothing licensed, fitted to the cuts. First choice.
- **Freesound**: CC0 and CC BY only (free key). No NC sounds.
- **Musopen**: public-domain recordings of classical works (check each recording's own licence).
- **Kokoro** voices for narration (Apache 2.0). ElevenLabs only with the owner's permission.

## Credit line format

On screen, top-left, 18 px mono, 70 % white, while the clip plays:
`NASA SVS` · `LIBRARY OF CONGRESS, 1900` · `PRELINGER ARCHIVES` · `WELLCOME COLLECTION, CC BY` · `WIKIMEDIA COMMONS / <author>, CC BY-SA 4.0`

In `credits.json`: `site, id, page, creator, licence, attribution` (all filled by the provider) plus the time
range used.

## How clips are used (planned montage mode, not built yet)

Old film is texture and evidence, not wallpaper. Rules for the coming montage mode:
- 0.8–1.5 s per clip in a montage, cut on the score's beats (`score_bars.plan`); a single clip under gate 4 (≤4.5 s still, ≤7 s moving).
- **Skip the first 20 s** of every archive film (title cards, distributor logos: the test pull hit them often).
- Archive film is framed as archive (paper frame, date chip, grain kept), never passed off as present-day.
- Print Facts: footage never stands in for an allegation it does not show. A 1912 campaign clip can open a story
  about elections; it can't illustrate a specific 2026 claim.

## Test pull, 2026-11-14

Queries: Print Facts "sea level", "flood", "parliament", "election"; Dragon Psychology "brain", "children",
"crowd", "emotion". 35 clips found, 25 frames pulled. Strong: SVS flood maps, LoC 1900 Galveston, Prelinger
"Act Your Age" / "Toward Emotional Maturity", Wikimedia brain animation (CC BY). Weak: SVS matched "children" to
Hubble; Wellcome matched "election" to a medical film (relevance needs the clip's own text, which is thin).
