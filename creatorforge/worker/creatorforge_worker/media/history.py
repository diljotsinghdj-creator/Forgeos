"""Historical borders: the world as it was in a given year, for "the map before the war" shots.

The outlines are the historical-basemaps dataset (github.com/aourednik/historical-basemaps, GPL-3.0). It is NOT
bundled with CreatorForge: the worker's setup downloads the years it needs into <data>/history (CF_HISTORY), and a
video that shows them carries the credit "Historical borders: historical-basemaps (A. Ourednik)". Without the
files a Borders: line is refused by the checker instead of drawing today's map with an old date on it.

    python -m creatorforge_worker.media.history 1880 1914 1938 1945   # download these years
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from functools import lru_cache
from pathlib import Path

CREDIT = "Historical borders: historical-basemaps (A. Ourednik), GPL-3.0"
RAW = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/world_{}.geojson"
# the years the dataset has from 1500 on (earlier ones exist; these cover the stories explainers tell)
YEARS = (1500, 1530, 1600, 1650, 1700, 1715, 1783, 1800, 1815, 1880, 1900, 1914, 1920, 1930, 1938, 1945, 1960, 1994,
         2000, 2010)
DEFAULT = (1815, 1880, 1914, 1920, 1938, 1945, 1960, 1994)


def folder() -> Path:
    return Path(os.environ.get("CF_HISTORY") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "history")


def available() -> list[int]:
    d = folder()
    return sorted(int(m.group(1)) for p in (d.glob("world_*.geojson") if d.is_dir() else [])
                  for m in [re.fullmatch(r"world_(\d{3,4})\.geojson", p.name)] if m)


def nearest(year: int) -> int | None:
    """The map in force in `year`: the latest dated map not after it (else the earliest there is)."""
    ys = available()
    if not ys:
        return None
    before = [y for y in ys if y <= year]
    return before[-1] if before else ys[0]


@lru_cache(maxsize=6)
def load(year: int) -> tuple:
    """Countries of the dated map: ({"n": name, "r": [ring, ...]}, ...) with rings thinned for drawing."""
    d = json.loads((folder() / f"world_{year}.geojson").read_text(encoding="utf-8"))
    out = []
    for f in d.get("features", []):
        g = f.get("geometry") or {}
        polys = g.get("coordinates") or []
        if g.get("type") == "Polygon":
            polys = [polys]
        rings = []
        for poly in polys:
            r = poly[0] if poly else []
            if len(r) >= 4:
                rings.append([[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 220)]])
        if rings:
            rings.sort(key=len, reverse=True)
            out.append({"n": str((f.get("properties") or {}).get("NAME") or "").strip(), "r": rings[:14]})
    return tuple(out)


def fetch(years=DEFAULT, timeout: float = 60) -> list[int]:
    """Downloads the dated maps that are missing; returns the years now on disk."""
    d = folder()
    d.mkdir(parents=True, exist_ok=True)
    for y in years:
        out = d / f"world_{y}.geojson"
        if out.is_file() and out.stat().st_size > 10_000:
            continue
        try:
            with urllib.request.urlopen(RAW.format(y), timeout=timeout) as r:
                data = r.read()
            json.loads(data)
            tmp = out.with_suffix(".tmp")
            tmp.write_bytes(data)
            tmp.replace(out)
        except Exception as e:  # noqa: BLE001 - a missing year only means that year can't be drawn
            print(f"history: {y} not downloaded ({e})", file=sys.stderr)
    return available()


if __name__ == "__main__":
    print(fetch(tuple(int(a) for a in sys.argv[1:]) or DEFAULT))
