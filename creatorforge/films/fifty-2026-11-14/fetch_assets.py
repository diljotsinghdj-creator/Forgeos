"""Download one Pixabay photo per search (free Pixabay licence; key from the pod's environment, never printed) and
cut subjects out with BiRefNet. Records page, author and licence for every file."""
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from concepts import C

D = Path(__file__).resolve().parent
A = D / "assets"
A.mkdir(exist_ok=True)
REC = D / "data" / "assets.json"
rec = json.loads(REC.read_text()) if REC.is_file() else {}
KEY = os.environ.get("PIXABAY_KEY", "")
CUT_ROLES = {"subject", "second", "hand", "tiny", "skyline", "facade"}


def slug(q):
    return re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:48]


def pixabay(q):
    r = httpx.get("https://pixabay.com/api/", params={"key": KEY, "q": q, "image_type": "photo", "per_page": 60,
                  "safesearch": "true", "orientation": "all"}, timeout=40)
    r.raise_for_status()
    stop = {"isolated", "white", "background", "black", "on", "of", "with", "the", "a"}
    words = [w for w in re.findall(r"[a-z]+", q.lower()) if w not in stop]
    stem = lambda w: w[:-1] if w.endswith("s") and len(w) > 3 else w
    for h in r.json().get("hits", []):
        tags = " ".join(stem(t) for t in re.findall(r"[a-z]+", (h.get("tags") or "").lower()))
        hits = sum(1 for w in words if stem(w) in tags)
        if h.get("imageWidth", 0) >= 1200 and hits >= max(1, len(words) - 1):   # the photo's own tags must say what it is
            return h
    return None


def cut(src: Path, out: Path):
    from PIL import Image
    from creatorforge_worker.media import cutouts
    with Image.open(src) as im:
        rgb = im.convert("RGB")
    rgb.thumbnail((1400, 1400))
    m = cutouts._mask(rgb, None, False)
    if m is None:
        return False
    bbox = m.point(lambda v: 255 if v > 128 else 0).getbbox()
    if not bbox:
        return False
    rgba = rgb.copy()
    rgba.putalpha(m)
    rgba.crop(bbox).save(out)
    return True


if __name__ == "__main__":
    wanted = {}
    for cid, ch, title, kick, dev, assets in C:
        for role, q in assets.items():
            if isinstance(q, str) and role not in ("country", "from", "to"):
                wanted[slug(q)] = (q, role in CUT_ROLES)
    for s, (q, needs_cut) in wanted.items():
        if s in rec and (A / f"{s}.jpg").is_file() and (not needs_cut or (A / f"{s}.png").is_file()):
            continue
        try:
            h = pixabay(q)
        except Exception as e:  # noqa: BLE001
            print("ERR", q, type(e).__name__)
            continue
        if not h:
            print("MISS", q)
            continue
        img = httpx.get(h["largeImageURL"], timeout=60)
        (A / f"{s}.jpg").write_bytes(img.content)
        ok = cut(A / f"{s}.jpg", A / f"{s}.png") if needs_cut else None
        rec[s] = {"query": q, "pixabay_id": h["id"], "page": h["pageURL"], "author": h.get("user", ""), "tags": h.get("tags", ""),
                  "licence": "Pixabay Content License (free for commercial use, no attribution required)", "cut": ok}
        REC.write_text(json.dumps(rec, indent=1))
        print("ok  ", q, "|", h.get("tags", "")[:50], "| cut" if ok else "")
        time.sleep(.7)
