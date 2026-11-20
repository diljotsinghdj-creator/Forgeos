"""NASA GIBS imagery (public domain): Blue Marble NG for orbit views, MODIS Terra true colour for routes and
before/after pairs (clearest of nearby days), VIIRS Black Marble 2016 for night lights."""
import datetime as dt, io, json, sys
from pathlib import Path
import httpx, numpy as np
from PIL import Image
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
from concepts import C
D = Path(__file__).resolve().parent
M = D / "maps"
URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
log = {}


def get(layer, bbox, day, w=2048):
    lon0, lat0, lon1, lat1 = bbox
    h = int(w * (lat1 - lat0) / (lon1 - lon0))
    q = {"SERVICE": "WMS", "REQUEST": "GetMap", "VERSION": "1.1.1", "LAYERS": layer, "SRS": "EPSG:4326", "BBOX": ",".join(map(str, bbox)),
         "WIDTH": w, "HEIGHT": h, "FORMAT": "image/jpeg", "TIME": day}
    return Image.open(io.BytesIO(httpx.get(URL, params=q, timeout=120).content)).convert("RGB")


def score(im):
    a = np.asarray(im).astype(int)
    white = ((a.min(2) > 200)).mean()          # cloud
    black = (a.sum(2) < 30).mean()             # swath gaps
    return white + 5 * black


def best(bbox, day, span=24, step=3):
    d0 = dt.date.fromisoformat(day)
    best = None
    for k in range(0, span, step):
        for sgn in (1, -1):
            d = d0 + dt.timedelta(days=sgn * k)
            try:
                im = get("MODIS_Terra_CorrectedReflectance_TrueColor", bbox, d.isoformat())
            except Exception:
                continue
            s = score(im)
            if best is None or s < best[0]:
                best = (s, im, d.isoformat())
            if s < .01:
                return best
    return best


for c in C:
    cid, dev, a = c[0], c[4], c[5]
    try:
        if dev == "satellite":
            get("BlueMarble_NextGeneration", a["bbox"], "2004-08-01").save(M / f"{cid}.jpg", quality=92); log[cid] = {"layer": "BlueMarble_NextGeneration"}
        elif dev == "satroute":
            s, im, d = best(a["bbox"], a["date"]); im.save(M / f"{cid}.jpg", quality=92); log[cid] = {"layer": "MODIS Terra", "date": d, "score": round(s, 4)}
        elif dev == "beforeafter":
            for tag, day in zip(("a", "b"), a["dates"]):
                s, im, d = best(a["bbox"], day); im.save(M / f"{cid}_{tag}.jpg", quality=92); log[f"{cid}_{tag}"] = {"layer": "MODIS Terra", "date": d, "score": round(s, 4)}
        elif dev == "nightlights":
            get("VIIRS_Black_Marble", a["bbox"], "2016-01-01").save(M / f"{cid}.jpg", quality=92); log[cid] = {"layer": "VIIRS Black Marble 2016"}
        else:
            continue
        print("ok", cid, log.get(cid) or log.get(cid + "_b"), flush=True)
    except Exception as e:  # noqa: BLE001
        print("ERR", cid, type(e).__name__, e, flush=True)
    (D / "data" / "sat.json").write_text(json.dumps(log, indent=1))
