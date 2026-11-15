"""Download chosen LoC candidates at up to 2000 px (IIIF where possible), record title, date, rights; optional crop."""
import io, json, re, sys, time
from pathlib import Path
import httpx
from PIL import Image
D = Path(__file__).resolve().parent; A = D / "assets"; A.mkdir(exist_ok=True)
REC = D / "data" / "loc.json"; rec = json.loads(REC.read_text()) if REC.is_file() else {}
SEL = json.loads(sys.argv[1])
def rights(item_id):
    for t in range(3):
        try:
            r = httpx.get(item_id.rstrip("/") + "/", params={"fo": "json"}, timeout=90, follow_redirects=True)
            if "json" in r.headers.get("content-type", ""):
                it = r.json().get("item", {})
                return it.get("rights_advisory") or it.get("rights") or ""
        except Exception: pass
        time.sleep(4)
    return ""
for key, (cand, idx, crop) in SEL.items():
    c = json.loads((D / "data" / "loc_cands" / f"{cand}.json").read_text())[idx]
    url = re.sub(r"_\d+px", "", c["big"]); img = None
    m = re.search(r"service/(.+?)([a-z])?\.(jpg|gif|tif)", url)
    if m:
        base = m.group(1).replace("/", ":")
        for suf in ("v", "u", "r", ""):
            try:
                r = httpx.get(f"https://tile.loc.gov/image-services/iiif/service:{base}{suf}/full/2000,/0/default.jpg", timeout=120)
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    img = Image.open(io.BytesIO(r.content)).convert("RGB"); break
            except Exception: pass
    if img is None:
        img = Image.open(io.BytesIO(httpx.get(url, timeout=120, follow_redirects=True).content)).convert("RGB")
    if crop:
        w, h = img.size; img = img.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    img.save(A / f"{key}.jpg", quality=92)
    rec[key] = {"title": c["title"], "date": c["date"], "url": c["id"], "rights": rights(c["id"]), "size": img.size}
    REC.write_text(json.dumps(rec, indent=1)); print("ok", key, img.size, rec[key]["rights"][:60], flush=True)
