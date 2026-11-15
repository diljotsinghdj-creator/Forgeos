"""Compact candidate sheets: 8 Pixabay hits per search, 10 searches per sheet, numbered, picked by eye."""
import io, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent
KEY = os.environ.get("PIXABAY_KEY", "")
OUT = Path(os.environ.get("SHEETS", "/tmp"))
CD = D / "data" / "cands"; CD.mkdir(parents=True, exist_ok=True)
def slug(q): return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:48]
def search(q, n=8):
    r = httpx.get("https://pixabay.com/api/", params={"key": KEY, "q": q, "image_type": "photo", "per_page": 40, "safesearch": "true"}, timeout=40)
    r.raise_for_status()
    return [h for h in r.json().get("hits", []) if h.get("imageWidth", 0) >= 1200][:n]
def thumb(h):
    im = Image.open(io.BytesIO(httpx.get(h["previewURL"], timeout=30).content)).convert("RGB"); im.thumbnail((140, 96)); return im
def row(q):
    hits = search(q); (CD / f"{slug(q)}.json").write_text(json.dumps(hits))
    with ThreadPoolExecutor(8) as ex: ims = list(ex.map(thumb, hits))
    return q, ims
if __name__ == "__main__":
    qs = [q for q in sys.argv[2:]]
    name = sys.argv[1]
    with ThreadPoolExecutor(4) as ex: rows = list(ex.map(row, qs))
    sh = Image.new("RGB", (190 + 8 * 146, len(rows) * 104), "white"); d = ImageDraw.Draw(sh)
    for r, (q, ims) in enumerate(rows):
        y = r * 104; d.text((4, y + 40), q[:30], fill="red")
        for i, im in enumerate(ims):
            x = 190 + i * 146; sh.paste(im, (x, y + 4)); d.rectangle((x, y + 4, x + 12, y + 16), fill="black"); d.text((x + 3, y + 5), str(i), fill="yellow")
    sh.save(OUT / f"{name}.jpg", quality=80); print(name, [len(i) for _, i in rows])
