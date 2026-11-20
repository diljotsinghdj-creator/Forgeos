"""Find real photos for the collage look (Pixabay first; its key stays in the environment and is never printed).
usage: python3 -I find_real2.py "query one" "query two" ...     -> assets/cand/<slug>/NN.jpg, cand.json and SHEET_<n>.jpg to pick from by eye."""
import json, os, re, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
C = D / "assets" / "cand"; C.mkdir(parents=True, exist_ok=True)
KEY = os.environ.get("PIXABAY_KEY", "")
UA = {"User-Agent": "documentary-photo-search/1.0"}
slug = lambda q: re.sub(r"[^a-z0-9]+", "_", q.lower()).strip("_")


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()


def search(q, n=8, kind="photo"):
    d = json.loads(get("https://pixabay.com/api/?" + urllib.parse.urlencode({"key": KEY, "q": q, "image_type": kind, "per_page": max(3, n), "safesearch": "true", "order": "popular"})))
    out = []
    for i, h in enumerate(d.get("hits", [])[:n]):
        f = C / slug(q) / f"{i:02d}.jpg"; f.parent.mkdir(exist_ok=True)
        try:
            if not f.is_file():
                f.write_bytes(get(h["webformatURL"]))
            out.append({"i": i, "file": str(f.relative_to(D)), "id": h["id"], "page": h["pageURL"], "author": h.get("user", ""), "tags": h.get("tags", ""), "large": h.get("largeImageURL", ""), "w": h.get("imageWidth"), "h": h.get("imageHeight")})
        except Exception as e:
            print("  skip", q, i, type(e).__name__)
    return out


def openverse(q, n=8):
    """Public-domain and CC0 images (Openverse); CC BY allowed with --by."""
    lic = "cc0,pdm,by" if "--by" in sys.argv else "cc0,pdm"
    d = json.loads(get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q": q, "license": lic, "page_size": max(3, n)})))
    out = []
    for i, h in enumerate(d.get("results", [])[:n]):
        f = C / slug(q) / f"{i:02d}.jpg"; f.parent.mkdir(exist_ok=True)
        try:
            if not f.is_file():
                f.write_bytes(get(h["thumbnail"]))
            out.append({"i": i, "file": str(f.relative_to(D)), "id": h["id"], "page": h.get("foreign_landing_url", ""), "author": h.get("creator") or h.get("source", ""), "tags": h.get("title", ""),
                        "large": h.get("url", ""), "w": h.get("width"), "h": h.get("height"), "licence": (h.get("license", "") + " " + (h.get("license_version") or "")).strip(), "source": h.get("source", "")})
        except Exception as e:
            print("  skip", q, i, type(e).__name__)
    return out


if __name__ == "__main__":
    book = json.loads((C / "cand.json").read_text()) if (C / "cand.json").is_file() else {}
    qs = [a for a in sys.argv[1:] if not a.startswith("--")]
    kind = "all" if "--all" in sys.argv else "photo"
    for q in qs:
        book[slug(q)] = {"query": q, "hits": openverse(q) if "--ov" in sys.argv else search(q, 8, kind)}; print(q, "->", len(book[slug(q)]["hits"]))
    (C / "cand.json").write_text(json.dumps(book, indent=1))
    W, H, per = 240, 170, 6
    for k in range(0, len(qs), per):
        part = qs[k:k + per]; S = Image.new("RGB", (8 * W, len(part) * (H + 22)), (20, 24, 36)); d = ImageDraw.Draw(S)
        for r, q in enumerate(part):
            d.text((6, r * (H + 22) + 4), q, fill=(240, 244, 248))
            for h in book[slug(q)]["hits"]:
                im = Image.open(D / h["file"]).convert("RGB"); im.thumbnail((W - 6, H - 6)); S.paste(im, (h["i"] * W + 3, r * (H + 22) + 20)); d.text((h["i"] * W + 8, r * (H + 22) + 22), str(h["i"]), fill=(237, 137, 54))
        n = len(list(C.glob("SHEET_*.jpg"))) + 1; S.save(C / f"SHEET_{n:02d}.jpg", quality=80); print(C / f"SHEET_{n:02d}.jpg")
