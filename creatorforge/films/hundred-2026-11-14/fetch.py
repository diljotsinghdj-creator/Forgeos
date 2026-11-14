"""Find one public-domain or CC0 image per theme and record where it came from.
Sources: Library of Congress (published before 1930, or 'no known restrictions'), NASA (public domain),
Art Institute of Chicago (is_public_domain, CC0), Cleveland Museum of Art (CC0)."""
import json
import re
import sys
import time
from pathlib import Path

import httpx

from topics import DP, PF

D = Path(__file__).resolve().parent
UA = {"User-Agent": "CreatorForge-research/1.0"}
OUT = D / "data" / "records.json"
rec = json.loads(OUT.read_text()) if OUT.is_file() else {}
used = {r["source_id"] for r in rec.values()}


def get(url, **kw):
    for i in range(3):
        try:
            r = httpx.get(url, headers=UA, timeout=60, follow_redirects=True, **kw)
            if r.status_code == 200:
                return r
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2 * (i + 1))
    return None


def loc(q):
    r = get("https://www.loc.gov/photos/", params={"q": q, "fo": "json", "c": 40})
    for x in (r.json().get("results", []) if r else []):
        year = re.search(r"(1[789]\d\d|19\d\d|20\d\d)", str(x.get("date") or ""))
        rights = " ".join(map(str, x.get("rights") or [])) if isinstance(x.get("rights"), list) else str(x.get("rights") or "")
        ok = (year and int(year.group(1)) < 1930) or "no known restrictions" in rights.lower()
        imgs = [u.split("#")[0] for u in (x.get("image_url") or []) if u.split("#")[0].endswith(".jpg")]
        if not ok or not imgs or x.get("id") in used:
            continue
        big = imgs[-1].split("#")[0]
        yield {"source": "Library of Congress", "source_id": x.get("id"), "url": big, "title": str(x.get("title", ""))[:200],
               "date": str(x.get("date") or ""), "maker": ", ".join(map(str, x.get("contributor") or []))[:120],
               "licence": "Public domain (published before 1930)" if year and int(year.group(1)) < 1930 else "No known restrictions on publication",
               "page": x.get("id")}


def nasa(q):
    r = get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "image"})
    for it in (r.json()["collection"]["items"] if r else [])[:20]:
        d = it["data"][0]
        if d["nasa_id"] in used:
            continue
        yield {"source": "NASA", "source_id": d["nasa_id"], "url": f"https://images-assets.nasa.gov/image/{d['nasa_id']}/{d['nasa_id']}~large.jpg",
               "title": d.get("title", "")[:200], "date": d.get("date_created", "")[:10], "maker": d.get("center", "NASA"),
               "licence": "Public domain (NASA media policy)", "page": f"https://images.nasa.gov/details/{d['nasa_id']}"}


def aic(q):
    r = get("https://api.artic.edu/api/v1/artworks/search", params={"q": q, "limit": 30, "query[term][is_public_domain]": "true",
            "fields": "id,title,image_id,is_public_domain,artist_display,date_display,thumbnail"})
    for x in (r.json().get("data", []) if r else []):
        if not x.get("is_public_domain") or not x.get("image_id") or f"aic-{x['id']}" in used:
            continue
        if (x.get("thumbnail") or {}).get("width", 0) < 843:
            continue
        yield {"source": "Art Institute of Chicago", "source_id": f"aic-{x['id']}", "url": f"https://www.artic.edu/iiif/2/{x['image_id']}/full/843,/0/default.jpg",
               "title": x.get("title", "")[:200], "date": x.get("date_display", ""), "maker": (x.get("artist_display") or "").split("\n")[0][:120],
               "licence": "CC0 (public domain)", "page": f"https://www.artic.edu/artworks/{x['id']}"}


def cma(q):
    r = get("https://openaccess-api.clevelandart.org/api/artworks/", params={"q": q, "cc0": 1, "has_image": 1, "limit": 30})
    for x in (r.json().get("data", []) if r else []):
        web = ((x.get("images") or {}).get("web") or {})
        if x.get("share_license_status") != "CC0" or not web.get("url") or f"cma-{x['id']}" in used or int(web.get("width") or 0) < 800:
            continue
        yield {"source": "Cleveland Museum of Art", "source_id": f"cma-{x['id']}", "url": web["url"], "title": x.get("title", "")[:200],
               "date": x.get("creation_date", ""), "maker": ", ".join(c.get("description", "") for c in (x.get("creators") or []))[:120],
               "licence": "CC0 (public domain)", "page": x.get("url", "")}


FIND = {"loc": loc, "nasa": nasa, "aic": aic, "cma": cma}
if __name__ == "__main__":
    only = set(sys.argv[1:])
    for ch, rows in (("print-facts", PF), ("dragon-psychology", DP)):
        for tid, title, kick, src, q in rows:
            if (only and tid not in only) or (not only and tid in rec):
                continue
            pick = None
            for cand in FIND[src](q):
                img = get(cand["url"])
                if img is None or len(img.content) < 30000 or not img.headers.get("content-type", "").startswith("image"):
                    continue
                (D / "img" / f"{tid}.jpg").write_bytes(img.content)
                pick = cand
                break
            if pick:
                rec[tid] = {**pick, "channel": ch, "theme": title, "kicker": kick, "query": q}
                used.add(pick["source_id"])
                print("ok  ", tid, "|", pick["source"], "|", pick["title"][:60])
            else:
                print("MISS", tid, q)
            OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
            time.sleep(.4)
