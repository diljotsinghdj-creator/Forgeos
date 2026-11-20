# Asset sourcing and rights

Where every picture and sound comes from, and how we prove we may use it. Read this when filling `asset_ids` /
`asset_needed` and before anything is downloaded.

Labels: [V] source-backed (sources.md P#, case_studies/) · [I] interpretation · [O] our rule.

---

## 1. What the studied craft shows

- [V] Footage sources are listed with timestamps in a video's description, plus further reading
  (from-spy-to-president-putin-2017).
- [V] Archive footage from public archives (an archive.org clip is credited in one description) (same case study).
- [V] Maps start from existing cartography; historical maps were traced from old books (P22).
- [V] Satellite and 3D map imagery from Google Earth Studio, annotated (P23). [O] Check Google's attribution and
  licence terms for any Earth Studio export; prefer open satellite data where the terms are unclear.
- [V] Rights risk for music and clips is real: Content ID demonetisation, and takedowns, even for fair use (P32;
  PATTERNS sci/culture §4).
- [V] Archive research happens during research, not after the script: the visuals that prove each fact are found
  alongside the facts (P16). Sources include public-domain archives, old magazines and instrument manuals, gathered
  on a mood board tool in pre-production (P27).
- [V] Data often sits behind research papers or in think-tank databases; ask the researchers for it (P9, P26).
- [V] Companion packages share the data and sources: a playlist and an interactive, a card stack, a resource list
  (PATTERNS sci/culture §7, politics §6).

## 2. Source order (CreatorForge MASTER_DIRECTIVES §5) [O]

1. **Real archives and public-domain or open collections:** Wikimedia Commons (check each file's licence), NASA
   (generally public domain; check logos and third-party content), Library of Congress (check rights statements),
   Internet Archive (check each item), national archives, USGS/ESA satellite data (Landsat, Sentinel: open, with
   attribution), Natural Earth and OpenStreetMap (attribution required).
2. **Primary documents:** court records, government reports, filings, papers. Usually free to show as evidence;
   cite them.
3. **Licensed stock:** Pixabay, Unsplash, Openverse (check each licence; some forbid trademarks and identifiable
   people in certain uses).
4. **Our own graphics:** drawn, animated or rendered by us.
5. **News footage and third-party clips:** only with a licence, or under a fair-use/fair-dealing analysis written
   down (short, transformative, commented on, credited). Note: UK fair dealing is narrower than US fair use.

Stock is never the default (≤ 25% of runtime, ILLUSTRATIVE when standing in for a specific place).

## 3. The asset register (`assets.csv`) [O]

Columns: `id, scene_ids, kind, title, source_url, author, licence, licence_url, date_accessed, rights_flags
(people/trademarks/third-party), how_used, modifications, credit_line, status (candidate | cleared | rejected)`.

Every asset is registered **before** it is used in a cut. "Downloadable" is not a licence.

## 4. People, logos, symbols [O, CreatorForge hard rules]

- No AI-generated faces of real people. No cartoons over real faces.
- Private individuals: no names, handles or faces; blur in screenshots.
- No national flags or emblems as decoration. Official, unaltered platform or party logos only when the narration
  names them.
- Recreations of interfaces are badged RECREATION.

## 5. Finding visual leads during research [O]

Visual research runs alongside fact research. For each chapter, list:
- the primary documents that could be shown (and where to get clean scans);
- archives that might hold photos or footage (search terms, collection names);
- datasets that could become graphics (owner, licence, format);
- places that need maps or satellite passes (coordinates, dates);
- what doesn't exist (so the blueprint plans a graphic or a labelled recreation instead).

## 6. Credits and the description [O]

- On screen: a source line on every evidence and data shot.
- Description: a sources section with timestamps (`0:42 Library of Congress, …`), further reading, and the data
  files we built (companion drop).
- Corrections line if ever needed (vox_editorial_methodology.md §7).
