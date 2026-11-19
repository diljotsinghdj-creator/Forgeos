# Restoring the bank films in a fresh container (2026-11-19)

Rendered frames, photos and AI images are gitignored. This is how they were rebuilt, so the next session doesn't have to work it out again.

## Setup
- `pip install playwright httpx` (Python bindings only). Chromium is already at `/opt/pw-browsers/chromium`; never run `playwright install`.
- Scripts use `/home/user/forgeos/...` (fixed from the old `/home/user/Forgeos`). Old html in non-bank films still says `Forgeos`; `ln -sfn /home/user/forgeos /home/user/Forgeos` covers those.
- `shoot_http.py` always logs one 404: the browser's favicon request. It is harmless.

## The Night the World Didn't End (`prophecy-2026-11-19`)
- AI picks A1, B3, C1, D1 and E2 are re-fetched by generation ID from the ElevenLabs flow `pQGk0bAw8kXDdsfofcfS` ("Dragon Psychology · The Night the World Didn't End · AI plates"). Use `creative_get_generations`, which spends no credits, then download `full_res_url`. They go in `assets/ai/<label>.jpg`. Never generate them again.
- Then run `python3 frames.py && python3 ai_frames.py && python3 shoot_http.py`. The result is 25 frames.

## Pepper Was Money (`pepper-money-2026-11-15`)
- **Photos:**
  - All 13 photos are listed in `data/assets.json`; match each one's `page` to its entry in `data/cands/*.json`.
  - The logged `pixabay.com/get/...` links expire. Use the same Pixabay ID from the logged `previewURL`, with `_640` swapped for `_1280`.
- **Chart:** `assets/chart.jpg` is the Linschoten chart, from the `loc-chart` entry in `data/loc.json` (`loc_cands/malabar.json[0]`, pct:100).
- **Cut-outs:** use `cutout.py` with **BiRefNet-lite**. The full BiRefNet-general model keeps the scale's lid, which doesn't match the sheets.
- **Order:** run `frames.py`, `rome.py`, `rome_vox.py`, `ships.py`, then `comedy.py` last, from inside the folder; it edits the other pages.
- **Shoot:** run `shoot_http.py`. That gives 45 stills. The 17 motion builds are shot at t = 0.20, 0.45, 0.70 and 1.00 (`name@t`).

## Why India Is Mocked Online (`india-mocked-2026-11-17`)
- **Faces:**
  - H keys come from `data/handsome_final.json`, by Pixabay ID through the free API (`PIXABAY_KEY` from the pod environment).
  - O keys come from the Flickr URLs in `data/ov_curated.json`.
- **Portraits:** from `data/portraits_cands.json`: macaulay = C, gandhi = E, chawla = J, williams = L.
- **Chart:** `chart.jpg` is the same LOC Linschoten chart as Pepper, at 2000 px wide.
- **CSOH receipts:** `csoh_title.png` and `csoh_kf.png` are crops of the live report at `csohate.org/2025/01/09/x-anti-indian-racism/`.
- **Maps:**
  - `bluemarble_world.jpg` comes from `taxonomy-2026-11-15/maps/`.
  - `ganga_bm.jpg` is NASA GIBS Blue Marble at 2400×1440.
- **Terrain box:** India terrain is `terrain.heights("india", (67.0, 5.5, 98.5, 37.5), 6)`. The original box wasn't recorded; this one was chosen on 2026-11-19, so `relief_a/b/c` sit slightly differently from sheet `M_4_new`.
- **Build:** run `frames.py`, `faces.py`, `motion.py`, then `shoot_http.py`. That gives 37 frames.
