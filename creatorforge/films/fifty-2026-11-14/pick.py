"""Candidate sheets: the top Pixabay hits for a search, numbered, so a person picks each photo by eye.
python pick.py "query" ...  -> data/cands/<slug>.json + scratch sheet;  python pick.py --take slug=query:index ..."""
import io, json, os, re, sys
from pathlib import Path
import httpx
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent
KEY = os.environ.get("PIXABAY_KEY", "")
OUT = Path(os.environ.get("SHEETS", "/tmp"))
(D / "data" / "cands").mkdir(parents=True, exist_ok=True)
def slug(q): return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:48]
def search(q, n=12):
    r = httpx.get("https://pixabay.com/api/", params={"key": KEY, "q": q, "image_type": "photo", "per_page": 40, "safesearch": "true"}, timeout=40)
    r.raise_for_status()
    return [h for h in r.json().get("hits", []) if h.get("imageWidth", 0) >= 1200][:n]
if __name__ == "__main__":
    for q in sys.argv[1:]:
        hits = search(q)
        (D / "data" / "cands" / f"{slug(q)}.json").write_text(json.dumps(hits))
        sh = Image.new("RGB", (6 * 200, 2 * 170), "white"); d = ImageDraw.Draw(sh)
        for i, h in enumerate(hits):
            im = Image.open(io.BytesIO(httpx.get(h["previewURL"], timeout=30).content)).convert("RGB"); im.thumbnail((190, 150))
            sh.paste(im, ((i % 6) * 200 + 5, (i // 6) * 170 + 5)); d.rectangle(((i % 6) * 200, (i // 6) * 170, (i % 6) * 200 + 22, (i // 6) * 170 + 16), fill="black")
            d.text(((i % 6) * 200 + 4, (i // 6) * 170 + 2), str(i), fill="yellow")
        sh.save(OUT / f"c_{slug(q)}.jpg", quality=80)
        print(q, len(hits))
