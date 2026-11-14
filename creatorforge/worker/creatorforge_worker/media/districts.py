"""District-level shapes (admin-2) for heat maps below state level: "Heatmap: Patna 58, Gaya 44, Nalanda 29 | ...".

The outlines are geoBoundaries (geoboundaries.org, open licences that differ per country). They are NOT bundled: the
worker downloads a country's districts into <data>/districts (CF_DISTRICTS) the first time, with the licence and
source the dataset states, and a video that shows them carries that credit. Without the file a district heat map is
refused by the checker rather than drawn from guessed shapes.

    python -m creatorforge_worker.media.districts IND PAK BGD     # download these countries (ISO-3 codes)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from functools import lru_cache
from pathlib import Path

API = "https://www.geoboundaries.org/api/current/gbOpen/{iso}/ADM2/"
DEFAULT = ("IND",)


def folder() -> Path:
    return Path(os.environ.get("CF_DISTRICTS") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "districts")


def available() -> list[str]:
    d = folder()
    return sorted(p.stem for p in d.glob("*.json")) if d.is_dir() else []


@lru_cache(maxsize=8)
def load(iso: str) -> dict:
    """{"credit": str, "units": [{"n": name, "r": [ring, ...]}]}"""
    return json.loads((folder() / f"{iso}.json").read_text(encoding="utf-8"))


def find(names: list[str]) -> tuple[str, list[dict], list[dict], str] | None:
    """(iso, the named districts in order, the country's other districts, credit) when at least two names are
    districts of one downloaded country."""
    from . import vox
    want = [vox._fold(n) for n in names]
    best = None
    for iso in available():
        data = load(iso)
        idx = {vox._fold(u["n"]): u for u in data["units"]}
        hit = [idx.get(w) for w in want]
        n = sum(1 for h in hit if h)
        if n >= 2 and (best is None or n > best[0]):
            got = {id(h) for h in hit if h}
            best = (n, iso, hit, [u for u in data["units"] if id(u) not in got], data.get("credit", ""))
    return (best[1], best[2], best[3], best[4]) if best else None


def _thin(geojson: dict, keep: int = 90) -> list[dict]:
    out = []
    for f in geojson.get("features", []):
        g = f.get("geometry") or {}
        polys = g.get("coordinates") or []
        if g.get("type") == "Polygon":
            polys = [polys]
        rings = [[[round(x, 3), round(y, 3)] for x, y in poly[0][:: max(1, len(poly[0]) // keep)]]
                 for poly in polys if poly and len(poly[0]) >= 4]
        name = str((f.get("properties") or {}).get("shapeName") or "").strip()
        if rings and name:
            rings.sort(key=len, reverse=True)
            out.append({"n": name, "r": rings[:3]})
    return out


def fetch(isos=DEFAULT, timeout: float = 90) -> list[str]:
    """Downloads the districts of each country that is missing; returns the countries now on disk."""
    d = folder()
    d.mkdir(parents=True, exist_ok=True)
    for iso in isos:
        out = d / f"{iso.upper()}.json"
        if out.is_file() and out.stat().st_size > 1000:
            continue
        try:
            with urllib.request.urlopen(API.format(iso=iso.upper()), timeout=timeout) as r:
                meta = json.loads(r.read())
            with urllib.request.urlopen(meta["simplifiedGeometryGeoJSON"], timeout=timeout) as r:
                units = _thin(json.loads(r.read()))
            credit = f"Districts: geoBoundaries ({meta.get('boundarySource', 'source in dataset')}; {meta.get('boundaryLicense', 'see dataset')})"
            tmp = out.with_suffix(".tmp")
            tmp.write_text(json.dumps({"credit": credit[:160], "units": units}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            tmp.replace(out)
        except Exception as e:  # noqa: BLE001 - a missing country only means its districts can't be drawn
            print(f"districts: {iso} not downloaded ({e})", file=sys.stderr)
    load.cache_clear()
    return available()


if __name__ == "__main__":
    print(fetch(tuple(a.upper() for a in sys.argv[1:]) or DEFAULT))
