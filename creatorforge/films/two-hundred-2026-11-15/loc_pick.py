"""Library of Congress candidates: for each key, the first 6 image results with rights, as a numbered contact sheet."""
import io, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent; CD = D / "data" / "loc_cands"; CD.mkdir(parents=True, exist_ok=True)
OUT = Path(os.environ.get("SHEETS", "/tmp"))
Q = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
def search(q):
    for t in range(4):
        try:
            r = httpx.get("https://www.loc.gov/search/", params={"q": q, "fo": "json", "c": 12, "fa": "online-format:image"}, timeout=90, follow_redirects=True)
            if "json" in r.headers.get("content-type", ""):
                out = []
                for it in r.json().get("results", []):
                    im = [u for u in (it.get("image_url") or []) if u]
                    if not im: continue
                    out.append({"id": it.get("id"), "title": it.get("title", "")[:90], "date": it.get("date", ""), "thumb": im[0].split("#")[0], "big": im[-1].split("#")[0]})
                return out[:6]
        except Exception: pass
        time.sleep(6)
    return []
def thumb(u):
    try:
        im = Image.open(io.BytesIO(httpx.get(u, timeout=60, follow_redirects=True).content)).convert("RGB"); im.thumbnail((180, 150)); return im
    except Exception: return Image.new("RGB", (180, 150), "#888")
rows = []
for k, q in Q.items():
    res = search(q); (CD / f"{k}.json").write_text(json.dumps(res)); time.sleep(2)
    with ThreadPoolExecutor(6) as ex: ims = list(ex.map(thumb, [r["thumb"] for r in res]))
    rows.append((k, q, res, ims)); print(k, len(res), flush=True)
sh = Image.new("RGB", (200 + 6 * 190, len(rows) * 186), "white"); d = ImageDraw.Draw(sh)
for i, (k, q, res, ims) in enumerate(rows):
    y = i * 186; d.text((4, y + 60), k, fill="red"); d.text((4, y + 80), q[:28], fill="black")
    for j, (r, im) in enumerate(zip(res, ims)):
        x = 200 + j * 190; sh.paste(im, (x, y + 4)); d.rectangle((x, y + 4, x + 14, y + 18), fill="black"); d.text((x + 3, y + 5), str(j), fill="yellow")
        d.text((x, y + 158), (r["date"] or "")[:10], fill="blue"); d.text((x, y + 170), r["title"][:30], fill="black")
sh.save(OUT / f"loc_{sys.argv[2] if len(sys.argv) > 2 else 'a'}.jpg", quality=80)
