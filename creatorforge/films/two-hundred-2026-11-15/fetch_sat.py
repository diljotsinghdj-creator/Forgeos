"""NASA GIBS imagery for every map-based frame (public domain). Blue Marble NG for still views, MODIS Terra true colour
(clearest nearby day, gaps filled from Aqua) for dated views, VIIRS Black Marble for night lights."""
import datetime as dt, io, json, sys, time
from pathlib import Path
import httpx, numpy as np
from PIL import Image
from concepts import C
D = Path(__file__).resolve().parent; M = D / "maps"
URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
LOG = D / "data" / "sat.json"; log = json.loads(LOG.read_text()) if LOG.is_file() else {}
def get(layer, bbox, day, w=2048, h=None):
    lon0, lat0, lon1, lat1 = bbox
    h = h or max(64, int(w * (lat1 - lat0) / (lon1 - lon0)))
    q = {"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.1.1", "LAYERS": layer, "SRS": "EPSG:4326", "BBOX": ",".join(map(str, bbox)), "WIDTH": w, "HEIGHT": h, "FORMAT": "image/jpeg", "TIME": day}
    for t in range(4):
        try:
            return np.asarray(Image.open(io.BytesIO(httpx.get(URL, params=q, timeout=200).content)).convert("RGB")).copy()
        except Exception:
            time.sleep(4)
    raise RuntimeError("gibs failed")
def fill(day, bbox, **kw):
    t = get("MODIS_Terra_CorrectedReflectance_TrueColor", bbox, day, **kw)
    if (t.sum(2) < 30).mean() > .001:
        a = get("MODIS_Aqua_CorrectedReflectance_TrueColor", bbox, day, **kw); m = t.sum(2) < 30; t[m] = a[m]
    return t
def score(a): return (a.min(2) > 200).mean() + 5 * (a.sum(2) < 30).mean()
def best(bbox, day, span=20, step=2, **kw):
    d0 = dt.date.fromisoformat(day); b = None
    for k in range(0, span, step):
        for s in (1, -1):
            d = (d0 + dt.timedelta(days=s * k)).isoformat()
            try: im = fill(d, bbox, **kw)
            except Exception: continue
            sc = score(im)
            if b is None or sc < b[0]: b = (sc, im, d)
            if sc < .01: return b
    return b
def save(name, arr, meta):
    Image.fromarray(arr).save(M / f"{name}.jpg", quality=90); log[name] = meta; LOG.write_text(json.dumps(log, indent=1)); print("ok", name, meta, flush=True)
BM = "BlueMarble_NextGeneration"
for c in C:
    cid, dev, a = c[0], c[4], c[5]
    if any((M / f"{cid}{s}.jpg").is_file() for s in ("", "_a")):
        continue
    try:
        if dev in ("satellite", "map_fill", "map_event"):
            save(cid, get(BM, a["bbox"], "2004-08-01"), {"layer": "Blue Marble NG"})
        elif dev == "satroute":
            sc, im, d = best(a["bbox"], a["date"]); save(cid, im, {"layer": "MODIS Terra/Aqua", "date": d})
        elif dev == "beforeafter":
            for tag, day in zip(("a", "b"), a["dates"]):
                sc, im, d = best(a["bbox"], day, span=14); save(f"{cid}_{tag}", im, {"layer": "MODIS Terra/Aqua", "date": d})
        elif dev == "nightlights":
            save(cid, get("VIIRS_Black_Marble", a["bbox"], "2016-01-01"), {"layer": "VIIRS Black Marble 2016"})
        elif dev == "hud":
            save(cid, fill(a["date"], a["bbox"]), {"layer": "MODIS Terra/Aqua", "date": a["date"]})
        elif dev in ("portal", "doc_board") and a.get("sat"):
            lon0, lat0, lon1, lat1 = a["sat"]
            if dev == "portal":
                cx, cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2; half = max(lon1 - lon0, lat1 - lat0) / 2
                bbox = (cx - half, cy - half, cx + half, cy + half); save(cid, get(BM, bbox, "2004-08-01", w=1024, h=1024), {"layer": "Blue Marble NG"})
            else:
                save(cid, get(BM, a["sat"], "2004-08-01", w=1200, h=1700), {"layer": "Blue Marble NG"})
    except Exception as e:
        print("ERR", cid, e, flush=True)
