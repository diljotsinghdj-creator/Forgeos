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

### Added 2026-11-14 (round 2), all keyless unless marked

| Provider | Source | Licence | Reached via |
|---|---|---|---|
| `usgov` | US government films: FedFlix, NARA uploads, CBS WWI, Army films | public domain (US government work) | Internet Archive |
| `voa` | Voice of America news reports | public domain (US government work), only items marked PD | Internet Archive |
| `voanews` | Voice of America news reports | public domain | Wikimedia Commons (file source = voanews.com) |
| `eso`, `esahubble`, `esawebb`, `noirlab` | observatory footage and animations | CC BY 4.0, credit exactly as the page gives it | the observatories' own sites |
| `kremlin` | Kremlin.ru: Putin addresses and events | CC BY 4.0 | Commons (kremlin.ru) |
| `whitehouse` | White House videos | public domain | Commons (whitehouse.gov) |
| `cspan` | House/Senate floor footage only | free to use (C-SPAN's own shows are not) | Commons (c-span.org) |
| `openbeelden` | Dutch archive (Beeld en Geluid) | CC BY-SA, read per file | Commons (openbeelden.nl) |
| `europarl` | European Parliament | per file | Commons |
| `agenciabrasil` | Agência Brasil | CC BY | Commons |
| `pib` | Press Information Bureau, India | GODL-India | Commons (pib.gov.in) |
| `nps` | US National Park Service: nature, wildlife | public domain | Commons (nps.gov) |
| `noaa` | NOAA: storms, satellites, oceans | public domain | Commons (noaa.gov) |
| `dareful` | Dareful: nature, ocean, sky, snow, city, travel b-roll (1080p MP4 on Mux) | CC BY 4.0, credit "Video courtesy of Dareful" | Dareful search; **its paid Shutterstock adverts are skipped**, only dareful.com clip pages are read |
| `dvids` *key* | US military public affairs | public domain | DVIDS API (`DVIDS_KEY`) |

For every source reached through Commons, the licence is still read from each file. A non-free file never gets
through, whatever its publisher.

Observatory clips often carry music: **we use the picture only**, never their soundtrack.

**Keys still needed (free, kept in the pod's environment only):** `EUROPEANA_KEY`, `DVIDS_KEY`, plus Pixabay/Pexels.
Until a key is set, that source is skipped.

**Not reachable from here, so handled by hand:**
- The Open Beelden site itself (the connection is reset), so we go through its Commons mirror instead.
- Kremlin.ru directly (does not resolve from the pod), so we go through Commons.
- houselive.gov (connection reset).
- NOAA Photo Library (403; not circumvented).
- The NPS API, Coverr and NARA's catalog API (free keys, not wired yet).
- The EU Audiovisual Service (a JavaScript-only site; manual pulls).

**Not automated:** Mixkit (checked by hand, see below), Pond5 Public Domain, Videvo/Videezy (no API, or a mix of free and paid clips) and
Google Earth Studio (a manual tool, with Google's attribution rules).

## Topic routing (`stock_video.topic_sources`)

The always-on set (NASA, SVS, Wikimedia, plus any keyed library) is searched for every line. The line's subject then
adds libraries, most specific first. They only join the search when the studio's picture check is on.

| Subject words | Extra libraries |
|---|---|
| space, galaxy, star, black hole, telescope, Mars | ESA/Hubble, ESO, ESA/Webb, NOIRLab, SVS |
| climate, flood, storm, monsoon, glacier, wildfire | SVS, NOAA, US gov films, LoC |
| forest, wildlife, animals, mountains | NPS, NOAA, Dareful |
| ocean, sky, sunset, snow, city, travel, aerial, calm, alone, quiet | Dareful |
| US president, Congress, Senate, Washington | White House, C-SPAN floor, VOA |
| Russia, Kremlin, Putin, Soviet | Kremlin.ru, VOA, Europeana |
| Europe, EU, Brussels, Netherlands | European Parliament, Open Beelden, Europeana |
| Brazil, Amazon, Latin America | Agência Brasil, VOA |
| India, Modi, Lok Sabha, ministry | PIB, VOA |
| war, army, military, nuclear | US gov films, DVIDS, LoC, Open Beelden |
| history, a year from 1800 to 1979, newsreel | US gov films, LoC, Open Beelden, Europeana |
| mind, brain, emotion, fear, children, school | Prelinger, Wellcome |
| medicine, disease, hospital, pandemic | Wellcome, US gov films |

## Mixkit (by hand, one clip at a time)

Modern, polished b-roll: nature, cities, hands, offices, abstract. It is a good fit for Dragon Psychology texture.
Checked 2026-11-14 against Mixkit's own licence pages and User Terms:

- **Two video licences, named on each clip page.**
  - **Stock Video Free License:** YouTube, commercial and monetised use allowed; credit not required (we credit
    anyway). Allowed.
  - **Stock Video Restricted License:** personal projects only. It says it can "never" appear in "a monetized YouTube
    video". **Refused.** Example: "Scientist looks at 3D brain model" (5665) is Restricted.
- **No automatic search.** The User Terms forbid "scripts or bots to mass download Items" and using the site "in any
  way not expressly permitted". So the studio never searches or crawls Mixkit.
- **The checker.** A person picks a clip page, then `providers/mixkit.py: check(url)` reads that one page. It returns
  the 1080p file only when the page names the Free licence; otherwise it gives the reason.
- **People in Mixkit clips are models, not real subjects.** Never use them to stand in for a real person or a real
  event in Print Facts.

## The usual "free stock footage" sites (checked 2026-11-14)

| Site | Status from the pod | Verdict |
|---|---|---|
| Pexels, Pixabay | bot check on the website; official free APIs (keys) | **use via API** (already wired) |
| Coverr | own licence, free commercial use; API needs a free key; has premium and AI clips too | **use, free clips only**, key needed |
| Dareful | CC BY 4.0, commercial allowed; robots allow it; no terms against searching | **wired in** (`dareful`): nature, sea, sky, cities, travel; credit "Video courtesy of Dareful" |
| Free Nature Stock | says attribution required | **use by hand**, with credit |
| SplitShire | now an AI image/video generator with paid plans; its "community videos" are user-made AI clips (even "Retro Footage" and "Crowd Footage"); no licence page, only general site terms | **dropped**: paid, no clear licence, and AI clips must never pass as real footage |
| Ignite Motion | free motion backgrounds | low value (abstract loops) |
| Videvo, Mazwai | now redirect to Magnific (Freepik's AI platform) | **dropped**: the free libraries are gone or paid |
| Freepik videos | now Magnific (freepik.com redirects there); free clips need attribution and an account, with download limits; Premium and the API are paid; the terms forbid downloads "through any robots, spiders or ... tool"; robots.txt blocks /download/ and /search | **dropped**: no automation allowed, and it pushes towards paid |
| Motion Places | "Pro License" | **dropped** (paid) |
| Vecteezy | free clips need attribution, Pro is paid | per clip only, risky; low priority |
| Videezy | bot check; mix of free (attribution) and Pro | per clip only; not automated |
| Vimeo Stock | redirects to the paid editor | **dropped** |
| Life of Vids, Stockio | connection reset from the pod | unverified |
| Clip Canvas | broken certificate | unverified; not used |
| Vidsplay | no licence text found | unverified; not used |

Bot checks are never worked around.

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
