"""Real satellite imagery of a place on given dates, as a before / after shot.

    Satellite: <place | bbox: lon0,lat0,lon1,lat1> | <date> vs <date> | swipe | fade | split | <title>
               | km: 300 | source: gibs | sentinel | layer: modis | aqua | viirs

Sources:
    gibs      NASA GIBS (Global Imagery Browse Services), keyless WMS. Daily MODIS Terra / Aqua true colour from 2000
              (Aqua from mid-2002), VIIRS SNPP from late 2015. About 250 m a pixel: a sea, a delta, a city's sprawl.
    sentinel  Copernicus Sentinel-2 L2A true colour (10 m) through the Sentinel Hub Process API. Needs client
              credentials in the pod's environment: CF_CDSE_CLIENT_ID / CF_CDSE_CLIENT_SECRET (Copernicus Data Space,
              free) or SH_CLIENT_ID / SH_CLIENT_SECRET (sentinel-hub.com). Coverage from mid-2015.

Nothing is invented or retouched. A daily picture can be cloudy, so the clearest day within a few days of each
date is used and the date actually shown is the one on screen. A date with no imagery stops the shot rather than
showing another year. The credit (NASA GIBS / Copernicus Sentinel data) is drawn on the picture.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import io
import json
import math
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .ff import MediaError

GIBS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
LAYERS = {"modis": ("MODIS_Terra_CorrectedReflectance_TrueColor", "NASA GIBS / MODIS Terra", "2000-02-24"),
          "aqua": ("MODIS_Aqua_CorrectedReflectance_TrueColor", "NASA GIBS / MODIS Aqua", "2002-07-04"),
          "viirs": ("VIIRS_SNPP_CorrectedReflectance_TrueColor", "NASA GIBS / VIIRS SNPP", "2015-11-24")}
SH = {"cdse": ("https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
               "https://sh.dataspace.copernicus.eu/api/v1/process", "CF_CDSE_CLIENT_ID", "CF_CDSE_CLIENT_SECRET"),
      "sh": ("https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token",
             "https://services.sentinel-hub.com/api/v1/process", "SH_CLIENT_ID", "SH_CLIENT_SECRET")}
S2_FROM = "2015-06-27"
EVALSCRIPT = """//VERSION=3
function setup(){return {input:["B02","B03","B04","dataMask"],output:{bands:4}}}
function evaluatePixel(s){const g=2.5;return [g*s.B04,g*s.B03,g*s.B02,s.dataMask]}"""
MODES = ("swipe", "fade", "split")
HTTP = None             # tests set a callable(url, data: bytes | None, headers: dict) -> bytes
TRIES = 5               # days tried round each date for the clearest picture


def _http(url: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 60) -> bytes:
    if HTTP is not None:
        return HTTP(url, data, headers or {})
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "creatorforge-worker", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:   # noqa: S310 - fixed https hosts above
        return r.read()


def _date(s: str) -> _dt.date | None:
    s = s.strip()
    for fmt, cut in (("%Y-%m-%d", 10), ("%Y-%m", 7), ("%Y", 4)):
        try:
            d = _dt.datetime.strptime(s[:cut], fmt).date()
        except ValueError:
            continue
        if fmt == "%Y-%m":
            d = d.replace(day=15)
        elif fmt == "%Y":
            d = d.replace(month=8, day=1)            # a bare year: late summer, the least cloud and snow in most places
        return d
    return None


def parse(spec: str) -> dict | None:
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    opts, free = {}, []
    for p in parts[1:]:
        k, sep, v = p.partition(":")
        if sep and re.fullmatch(r"[a-z]+", k.strip().lower()):
            opts[k.strip().lower()] = v.strip()
        elif p:
            free.append(p)
    plan = {"type": "satellite", "place": parts[0][:60], "mode": "swipe", "title": "", "dates": [], "source": opts.get("source", "gibs").lower(),
            "layer": opts.get("layer", "modis").lower(), "km": 300.0}
    if plan["source"] not in ("gibs", "sentinel"):
        plan["source"] = "gibs"
    if plan["layer"] not in LAYERS:
        plan["layer"] = "modis"
    try:
        plan["km"] = min(3000.0, max(5.0, float(opts.get("km", "") or (60 if plan["source"] == "sentinel" else 300))))
    except ValueError:
        pass
    bb = re.match(r"bbox\s*:\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)", parts[0], re.I)
    if bb:
        x0, y0, x1, y1 = map(float, bb.groups())
        if not (x0 < x1 and y0 < y1 and -180 <= x0 and x1 <= 180 and -85 <= y0 and y1 <= 85):
            return None
        plan["bbox"], plan["place"] = [x0, y0, x1, y1], ""
    for f in free:
        low = f.lower()
        if low in MODES:
            plan["mode"] = low
            continue
        ds = [_date(x) for x in re.split(r"\s+(?:vs\.?|→|->|to)\s+", f, flags=re.I)]
        if len(ds) >= 2 and all(ds) and not plan["dates"]:
            plan["dates"] = [d.isoformat() for d in ds[:4]]
        elif not plan["title"]:
            plan["title"] = f[:60]
    if len(plan["dates"]) < 2:
        return None
    if not plan.get("bbox"):
        from . import vox
        if not vox._geo([plan["place"]]):
            return None                              # an unknown place: never a guessed position
    if plan["mode"] != "split" and len(plan["dates"]) > 2:
        plan["dates"] = plan["dates"][:2]
    return plan


def bbox_for(plan: dict) -> list[float]:
    if plan.get("bbox"):
        return plan["bbox"]
    from . import vox
    g = vox._geo([plan["place"]])
    if not g:
        raise MediaError(f"satellite: {plan['place']!r} is not a place I can find (give bbox: lon0,lat0,lon1,lat1)")
    lon, lat, half = g[0]["lon"], g[0]["lat"], plan["km"] / 2
    dlat, dlon = half / 111.0, half / (111.0 * max(0.2, math.cos(math.radians(g[0]["lat"]))))
    return [round(lon - dlon * 16 / 9, 4), round(lat - dlat, 4), round(lon + dlon * 16 / 9, 4), round(lat + dlat, 4)]


def _size(bbox: list[float], longest: int) -> tuple[int, int]:
    """Pixel size whose shape matches the ground (degrees of longitude shrink with latitude)."""
    x0, y0, x1, y1 = bbox
    gw, gh = (x1 - x0) * math.cos(math.radians((y0 + y1) / 2)), y1 - y0
    return (longest, max(64, round(longest * gh / gw))) if gw >= gh else (max(64, round(longest * gw / gh)), longest)


def cloud(img) -> float:
    """Share of the picture that is bright and colourless (cloud, snow) or empty (no data)."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), np.float32)
    hi = (a.min(axis=2) > 200) & (a.max(axis=2) - a.min(axis=2) < 30)
    empty = a.max(axis=2) < 6
    return float((hi | empty).mean())


def gibs_url(layer: str, bbox: list[float], day: str, w: int, h: int) -> str:
    q = {"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.1.1", "LAYERS": LAYERS[layer][0], "SRS": "EPSG:4326",
         "BBOX": ",".join(f"{v:.4f}" for v in bbox), "WIDTH": w, "HEIGHT": h, "FORMAT": "image/jpeg", "TIME": day, "STYLES": ""}
    return GIBS + "?" + urllib.parse.urlencode(q)


def _sh_keys() -> tuple[str, str, str, str] | None:
    for name in ("cdse", "sh"):
        tok, proc, ki, ks = SH[name]
        if os.environ.get(ki) and os.environ.get(ks):
            return tok, proc, os.environ[ki], os.environ[ks]
    return None


def sentinel_ready() -> bool:
    return _sh_keys() is not None


def _sh_token(tok: str, cid: str, secret: str) -> str:
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}).encode()
    data = json.loads(_http(tok, body, {"Content-Type": "application/x-www-form-urlencoded"}))
    if not data.get("access_token"):
        raise MediaError("satellite: Sentinel Hub refused the client credentials")
    return data["access_token"]


def sentinel_body(bbox: list[float], day: _dt.date, w: int, h: int, window: int = 20) -> dict:
    t0, t1 = day - _dt.timedelta(days=window), day + _dt.timedelta(days=window)
    return {"input": {"bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
                      "data": [{"type": "sentinel-2-l2a", "dataFilter": {"timeRange": {"from": f"{t0}T00:00:00Z", "to": f"{t1}T23:59:59Z"},
                                                                        "maxCloudCoverage": 30, "mosaickingOrder": "leastCC"}}]},
            "output": {"width": w, "height": h, "responses": [{"identifier": "default", "format": {"type": "image/jpeg"}}]},
            "evalscript": EVALSCRIPT}


def fetch(plan: dict, cache: Path, longest: int = 2048) -> list[dict]:
    """[{"file", "date", "credit"}] for each date of the plan; raises MediaError when a date has no usable picture."""
    from PIL import Image
    cache.mkdir(parents=True, exist_ok=True)
    bbox = bbox_for(plan)
    out = []
    token = None
    for ds in plan["dates"]:
        want = _dt.date.fromisoformat(ds)
        if plan["source"] == "sentinel":
            keys = _sh_keys()
            if keys is None:
                raise MediaError("satellite: Sentinel-2 needs CF_CDSE_CLIENT_ID / CF_CDSE_CLIENT_SECRET (or SH_CLIENT_ID / "
                                 "SH_CLIENT_SECRET) in the pod's environment; use source: gibs without them")
            if ds < S2_FROM:
                raise MediaError(f"satellite: Sentinel-2 starts in mid-2015, not {ds}; use source: gibs for older dates")
            w, h = _size(bbox, min(longest, 2500))
            key = hashlib.sha1(json.dumps(["s2", bbox, ds, w, h]).encode()).hexdigest()[:16]
            f = cache / f"s2_{key}.jpg"
            if not f.is_file():
                token = token or _sh_token(keys[0], keys[2], keys[3])
                raw = _http(keys[1], json.dumps(sentinel_body(bbox, want, w, h)).encode(),
                            {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "Accept": "image/jpeg"})
                im = Image.open(io.BytesIO(raw)).convert("RGB")
                if cloud(im) > 0.6:
                    raise MediaError(f"satellite: no clear Sentinel-2 picture within 20 days of {ds}")
                im.save(f, quality=93)
            out.append({"file": f, "date": ds, "credit": f"Contains modified Copernicus Sentinel data {want.year}"})
            continue
        layer, credit, start = plan["layer"], LAYERS[plan["layer"]][1], LAYERS[plan["layer"]][2]
        if ds < start:
            raise MediaError(f"satellite: {layer.upper()} imagery starts on {start}, not {ds}")
        w, h = _size(bbox, longest)
        best = None
        for k in range(TRIES):
            day = want + _dt.timedelta(days=(k + 1) // 2 * (1 if k % 2 else -1))      # the date, then a day after, a day before...
            key = hashlib.sha1(json.dumps(["gibs", layer, bbox, day.isoformat(), w, h]).encode()).hexdigest()[:16]
            f = cache / f"gibs_{key}.jpg"
            if not f.is_file():
                try:
                    raw = _http(gibs_url(layer, bbox, day.isoformat(), w, h))
                    im = Image.open(io.BytesIO(raw)).convert("RGB")
                except Exception:  # noqa: BLE001 - one missing day is not the end; the next is tried
                    continue
                im.save(f, quality=93)
            c = cloud(Image.open(f))
            if best is None or c < best[0]:
                best = (c, f, day)
            if c < 0.08:
                break
        if best is None or best[0] > 0.6:
            raise MediaError(f"satellite: no clear {layer.upper()} picture within {TRIES // 2} days of {ds}")
        out.append({"file": best[1], "date": best[2].isoformat(), "credit": f"{credit}, {best[2].isoformat()}"})
    return out


def label(day: str, asked: str) -> str:
    """The on-screen date: the year alone when the asked date was a bare year or month, else the day."""
    d = _dt.date.fromisoformat(day)
    return str(d.year) if len(asked) <= 7 else d.strftime("%-d %b %Y")


def prepare(spec: str, work: Path, width: int = 1920, height: int = 1080) -> tuple[str, str, dict]:
    """The Satellite line -> (a Photos line with the downloaded files, the imagery credit, the plan)."""
    plan = parse(spec)
    if plan is None:
        raise MediaError(f"satellite: needs a place and two dates ('Aral Sea | 2000 vs 2020'), got {spec!r}")
    asked = []
    for f in [p.strip() for p in spec.split("|")[1:]]:
        bits = re.split(r"\s+(?:vs\.?|→|->|to)\s+", f, flags=re.I)
        if len(bits) >= 2 and all(_date(b) for b in bits):
            asked = [b.strip() for b in bits]
            break
    shots = fetch(plan, Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "satellite", max(width, height))
    plan["shots"] = [{"file": str(s["file"]), "date": s["date"]} for s in shots]
    labels = [label(s["date"], asked[i] if i < len(asked) else s["date"]) for i, s in enumerate(shots)]
    line = ", ".join(str(s["file"]) for s in shots) + f" | {plan['mode']}" + (f" | {plan['title']}" if plan["title"] else "") + \
        " | labels: " + ", ".join(labels)
    credit = "; ".join(dict.fromkeys(re.sub(r", \d{4}-\d\d-\d\d$", "", s["credit"]) for s in shots))
    return line, credit, plan
