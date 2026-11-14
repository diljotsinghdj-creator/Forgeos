"""Sentinel-2 true colour at 10 m with no account and no key: the public Sentinel-2 archive on AWS (Registry of Open
Data, bucket `sentinel-cogs`, cloud-optimised GeoTIFFs maintained by Element 84).

    fetch(bbox, day, width, height, cache) -> {"file", "date", "credit", "cloud"}

How a picture is found: the bbox's centre gives the 100 km Sentinel-2 tile (MGRS); the archive is listed for the
months around the date; each scene's own metadata gives its cloud cover and how much of the tile it covers; the least
cloudy scene within `window` days wins, the nearest date breaking ties. Only the window over the bbox is read from the
true-colour image (TCI.tif), over HTTP, so a 60 km crop downloads a few megabytes, not the 100 km tile.

Nothing is retouched: the picture is the scene's own true-colour product, resized. The credit says whose data it is.
Needs rasterio and mgrs (`pip install rasterio mgrs`).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import urllib.request
from pathlib import Path

from .ff import MediaError

BUCKET = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
PREFIX = "sentinel-s2-l2a-cogs"
HTTP = None        # tests set a callable(url) -> bytes
READ = None        # tests set a callable(tci_url, bbox, width, height) -> PIL image


def ready() -> bool:
    if READ is not None:
        return True
    try:
        import mgrs  # noqa: F401
        import rasterio  # noqa: F401
    except ImportError:
        return False
    return True


def _get(url: str, timeout: int = 30) -> bytes:
    if HTTP is not None:
        return HTTP(url)
    req = urllib.request.Request(url, headers={"User-Agent": "creatorforge-worker"})
    with urllib.request.urlopen(req, timeout=timeout) as r:      # noqa: S310 - the public AWS bucket only
        return r.read()


def tile_of(lon: float, lat: float) -> tuple[str, str, str]:
    """('41', 'T', 'NM') for the Sentinel-2 tile containing the point."""
    import mgrs
    code = mgrs.MGRS().toMGRS(lat, lon, MGRSPrecision=0)
    m = re.match(r"(\d{1,2})([C-X])([A-Z]{2})", code)
    if not m:
        raise MediaError(f"satellite: no Sentinel-2 tile for {lat:.3f}, {lon:.3f}")
    return str(int(m.group(1))), m.group(2), m.group(3)


def scenes(tile: tuple[str, str, str], day: _dt.date, window: int = 20) -> list[dict]:
    """Every scene of the tile within `window` days: [{"prefix", "date", "cloud", "nodata"}]."""
    months = sorted({(d.year, d.month) for d in (day - _dt.timedelta(days=window), day, day + _dt.timedelta(days=window))})
    out = []
    for y, mo in months:
        pre = f"{PREFIX}/{tile[0]}/{tile[1]}/{tile[2]}/{y}/{mo}/"
        xml = _get(f"{BUCKET}/?list-type=2&prefix={pre}&delimiter=/").decode("utf-8", "replace")
        for p in re.findall(r"<Prefix>([^<]+_L2A/)</Prefix>", xml):
            m = re.search(r"_(\d{8})_\d+_L2A/$", p)
            if not m:
                continue
            d = _dt.datetime.strptime(m.group(1), "%Y%m%d").date()
            if abs((d - day).days) > window:
                continue
            name = p.rstrip("/").rsplit("/", 1)[-1]
            try:
                props = json.loads(_get(f"{BUCKET}/{p}{name}.json"))["properties"]
            except Exception:  # noqa: BLE001 - a scene without metadata is skipped, never guessed
                continue
            out.append({"prefix": p, "date": d, "cloud": float(props.get("eo:cloud_cover", 100)),
                        "nodata": float(props.get("s2:nodata_pixel_percentage", 0))})
    return out


def _read(tci_url: str, bbox: list[float], width: int, height: int):
    if READ is not None:
        return READ(tci_url, bbox, width, height)
    import numpy as np
    import rasterio
    from PIL import Image
    from rasterio.enums import Resampling
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open("/vsicurl/" + tci_url) as src:
            b = transform_bounds("EPSG:4326", src.crs, *bbox)
            win = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
            data = src.read([1, 2, 3], window=win, out_shape=(3, height, width), boundless=True, fill_value=0,
                            resampling=Resampling.average)
    return Image.fromarray(np.transpose(data, (1, 2, 0)).astype("uint8"), "RGB")


def fetch(bbox: list[float], day: _dt.date, width: int, height: int, cache: Path, window: int = 20,
          max_cloud: float = 30.0) -> dict:
    if not ready():
        raise MediaError("satellite: the AWS Sentinel-2 source needs rasterio and mgrs (pip install rasterio mgrs)")
    cache.mkdir(parents=True, exist_ok=True)
    lon, lat = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    tile = tile_of(lon, lat)
    found = [s for s in scenes(tile, day, window) if s["nodata"] < 40]
    if not found:
        raise MediaError(f"satellite: no Sentinel-2 scene of tile {''.join(tile)} within {window} days of {day}")
    found.sort(key=lambda s: (round(s["cloud"] / 5), abs((s["date"] - day).days)))
    best = found[0]
    if best["cloud"] > max_cloud:
        raise MediaError(f"satellite: the clearest Sentinel-2 scene near {day} is {best['cloud']:.0f}% cloud")
    key = hashlib.sha1(json.dumps([best["prefix"], bbox, width, height]).encode()).hexdigest()[:16]
    f = cache / f"s2aws_{key}.jpg"
    if not f.is_file():
        _read(f"{BUCKET}/{best['prefix']}TCI.tif", bbox, width, height).save(f, quality=93)
    return {"file": f, "date": best["date"].isoformat(), "cloud": best["cloud"],
            "credit": f"Contains modified Copernicus Sentinel data {best['date'].year} (AWS Open Data)"}
