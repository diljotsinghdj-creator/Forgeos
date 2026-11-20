# Restoring the bank films in a fresh container (2026-11-19)

Rendered frames, photos and AI images are gitignored. This is how they were rebuilt, so the next session doesn't have to work it out again.

## Setup
- `pip install playwright httpx` (Python bindings only). Chromium is already at `/opt/pw-browsers/chromium`; never run `playwright install`.
- Scripts use `/home/user/forgeos/...` (fixed from the old `/home/user/Forgeos`). Old html in non-bank films still says `Forgeos`; `ln -sfn /home/user/forgeos /home/user/Forgeos` covers those.
- `shoot_http.py` always logs one 404: the browser's favicon request. It is harmless.

## The Night the World Didn't End (`prophecy-2026-11-19`)
- AI picks A1, B3, C1, D1 and E2 are re-fetched by generation ID from the ElevenLabs flow `pQGk0bAw8kXDdsfofcfS` ("Dragon Psychology · The Night the World Didn't End · AI plates"). Use `creative_get_generations`, which spends no credits, then download `full_res_url`. They go in `assets/ai/<label>.jpg`. Never generate them again.
- Round 2 plates F1–F6 come from the same flow (generation IDs in `data/ai_ledger.json`). Save the raws in `assets/ai_raw/`, then finish every used plate (A1, B3, C1, D1, E2, F1–F6) with `python3 -I ../../channels/design_kits/ai_finish.py assets/ai_raw/X assets/ai/X.jpg --channel dp`.
- **Real photos (2026-11-19 rework):** run `python3 -I real.py`, which re-fetches the credited photos in `data/photo_credits.json`. Only A1, D1 and F4 remain as AI plates.
- Then run `python3 frames.py && python3 ai_frames.py && python3 shoot_http.py`. The result is 28 frames.

## Pepper Was Money (`pepper-money-2026-11-15`)
- **Photos:**
  - All 13 photos are listed in `data/assets.json`; match each one's `page` to its entry in `data/cands/*.json`.
  - The logged `pixabay.com/get/...` links expire. Use the same Pixabay ID from the logged `previewURL`, with `_640` swapped for `_1280`.
- **Chart:** `assets/chart.jpg` is the Linschoten chart, from the `loc-chart` entry in `data/loc.json` (`loc_cands/malabar.json[0]`, pct:100).
- **Cut-outs:** use `cutout.py` with **BiRefNet-lite**. The full BiRefNet-general model keeps the scale's lid, which doesn't match the sheets.
- **AI plates P1–P6:** re-fetch them by generation ID from flow `UKqrgruhJAMbRscLiUYe` (`data/ai_ledger.json`) into `assets/ai_raw/`. Finish each with `ai_finish.py --channel pf` into `assets/ai/`.
- **Real photos (2026-11-19 rework):** `data/photo_credits_2.json` lists every replacement (all AI plates retired). Fetch them into `assets/real2/`.
- **Order:** from inside the folder, run `frames.py`, `rome.py`, `rome_vox.py`, `ships.py`, `comedy.py` (it edits the other pages), `ai_frames.py`, `real_frames.py`, then `motion_maps.py`. If the scripts differ, follow the order noted at the top of `real_frames.py`.
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
- **AI plates AI1–AI6:** re-fetch them by generation ID from flow `TqEmfXfQP7ZvL79XUAW5` (`data/ai_ledger.json`) into `assets/ai_raw/`. Finish each with `ai_finish.py --channel pf` into `assets/ai/`.
- **Paths:** the scripts expect the repo at `/home/user/forgeos`. If it's cloned as `/home/user/Forgeos`, add a symlink: `ln -s /home/user/Forgeos /home/user/forgeos`.
- **Real photos (2026-11-19 rework):** `data/photo_credits_2.json` lists the replacements for every AI plate (all retired). Fetch them into `assets/real2/`.
- **Build:** run `frames.py`, `faces.py`, `motion.py`, `ai_frames.py`, then `shoot_http.py`. That gives 42 frames.
