"""Photographs and footage from Pixabay, Unsplash, Pexels and Openverse, chosen like a picture editor would, kept in
a library, and accounted for in a ledger.

For a scene's visual need (subject, place, era, purpose, photo or video):
  1. the library is searched first (an asset already licensed and used well is reused, with the reuse recorded);
  2. otherwise several phrasings are searched across the sources (the subject, the subject in its place, the place,
     the purpose's own words: "aerial", "street", "landscape"...);
  3. every candidate is scored on its metadata: subject relevance, geographic match, period match, resolution for
     the output frame, aspect ratio (how much a crop loses);
  4. the best few are downloaded and scored on their pixels: exposure, contrast, sharpness, where the interest sits
     in the frame, colour against the film's palette, and continuity with the previous scene's picture;
  5. the best one above the bar is entered in the ledger, with every field a publication check needs.
A candidate that shows the right kind of thing but not the specific place or event can still be used, but only as
ILLUSTRATIVE: the shot then carries that tag, and the ledger says why.

Ledger fields: asset id, original filename, source site, original asset URL and page URL, creator, download date,
licence, attribution requirement, rights to check (people, brands, private property), intended documentary, scene,
categories (subject, location, type, quality, licence) and the modification history (crops, cut-outs, depth layers,
grades) appended as the shot is made.
"""
from __future__ import annotations

import csv
import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

LICENCES = {
    "Pixabay Content License": "Commercial use allowed, no attribution required. Not allowed: selling or redistributing the "
                               "file unaltered; uses that suggest endorsement. Identifiable people, logos, brands and private "
                               "property may carry rights of their own.",
    "Unsplash License": "Commercial use allowed, no attribution required (credit is appreciated). Not allowed: selling "
                        "unaltered copies; compiling photos into a competing service. People, brands and property may need "
                        "their own releases. API terms: the download must be reported to Unsplash.",
    "Pexels License": "Commercial use allowed, no attribution required. Not allowed: selling unaltered copies; implying "
                      "endorsement by people shown. People, brands and property may need their own releases.",
}
RIGHTS_WORDS = {"people": ("person", "people", "man", "woman", "men", "women", "child", "children", "girl", "boy", "portrait",
                           "face", "crowd", "worker", "family", "farmer", "student"),
                "brand": ("logo", "brand", "trademark", "sign", "billboard", "advert"),
                "property": ("interior", "house", "home", "artwork", "mural", "sculpture")}
OLD_WORDS = ("vintage", "old", "historic", "historical", "retro", "archive", "antique", "black and white", "monochrome", "sepia", "1950s",
             "1960s", "1970s", "soviet")
PURPOSE_WORDS = {"location": ["landscape", "aerial view"], "establishing": ["aerial", "skyline", "wide view"],
                 "street": ["street", "city street"], "industrial": ["factory", "industry"], "nature": ["nature", "landscape"],
                 "human": ["people", "daily life"], "object": [], "abstract": [], "transport": ["transport"], "event": []}


def default_ledger() -> Path:
    return Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "assets" / "ledger.json"


class Ledger:
    _lock = threading.Lock()

    def __init__(self, path: Path):
        self.path = Path(path)

    def all(self) -> list[dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def _save(self, rows: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.path)

    def get(self, aid: str) -> dict | None:
        return next((r for r in self.all() if r.get("id") == aid), None)

    def add(self, rec: dict) -> dict:
        with self._lock:
            rows = self.all()
            same = next((r for r in rows if r.get("url") == rec.get("url")), None)
            if same:
                same.setdefault("uses", []).append({"film": rec.get("film"), "scene": rec.get("scene"), "date": date.today().isoformat()})
                self._save(rows)
                return same
            n = 1 + max([int(re.sub(r"\D", "", r["id"]) or 0) for r in rows] or [0])
            rec = {"id": f"{'V' if rec.get('type') == 'video' else 'P'}{n:04d}", **rec,
                   "uses": [{"film": rec.get("film"), "scene": rec.get("scene"), "date": date.today().isoformat()}], "modifications": []}
            rows.append(rec)
            self._save(rows)
            return rec

    def modified(self, aid: str, note: str) -> None:
        with self._lock:
            rows = self.all()
            for r in rows:
                if r.get("id") == aid and note not in r.setdefault("modifications", []):
                    r["modifications"].append(note)
            self._save(rows)

    def find(self, terms: list[str], kind: str, place: str = "") -> list[dict]:
        """Library assets that already match: every subject term in their tags (and the place, when one is asked)."""
        out = []
        for r in self.all():
            text = (r.get("about", "") + " " + " ".join(r.get("categories", {}).get("subject", []))).lower()
            if r.get("type") != kind or not Path(r.get("file", "")).is_file():
                continue
            if all(t.lower() in text for t in terms) and (not place or place.lower() in text):
                out.append(r)
        return out

    def export(self, film: str, out: Path) -> Path:
        cols = ["id", "type", "scene", "original_filename", "site", "url", "page", "creator", "downloaded", "licence", "attribution",
                "rights_check", "illustrative", "modifications"]
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in self.all():
                for u in r.get("uses", []):
                    if u.get("film") == film:
                        w.writerow([r.get("id"), r.get("type"), u.get("scene"), r.get("original_filename"), r.get("site"), r.get("url"),
                                    r.get("page"), r.get("creator"), r.get("downloaded"), r.get("licence"), r.get("attribution"),
                                    "; ".join(r.get("rights_check", [])), r.get("illustrative_reason", ""), "; ".join(r.get("modifications", []))])
        return out


@dataclass
class Need:
    scene: str
    film: str
    subject: str                       # "fishing boat", "cotton field", "container port"
    kind: str = "photo"                # photo | video
    place: str = ""                    # "Moynaq", "Uzbekistan"
    era: int | None = None             # the year the shot should look like (None = today)
    purpose: str = "location"          # location | establishing | street | industrial | nature | human | object | abstract | transport | event
    specific: bool = False             # the line is about this very place / event: a generic picture is only ILLUSTRATIVE
    queries: list[str] = field(default_factory=list)
    orientation: str = "landscape"
    min_side: int = 1080


def queries(n: Need) -> list[str]:
    q = list(n.queries)
    if n.place:
        q += [f"{n.subject} {n.place}", n.place + " " + (PURPOSE_WORDS.get(n.purpose) or [""])[0]]
    q.append(n.subject)
    for w in PURPOSE_WORDS.get(n.purpose, []):
        q.append(f"{n.subject} {w}")
    if n.era and n.era < 1990:
        q.insert(0, f"vintage {n.subject}")
    out = []
    for x in q:
        x = re.sub(r"\s+", " ", x).strip()
        if x and x.lower() not in [o.lower() for o in out]:
            out.append(x)
    return out[:8]


def _terms(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) > 2 and w not in ("the", "and", "with", "view")]


ARCHIVES = ("wikimedia", "nasa", "loc", "archive", "smithsonian", "europeana", "flickr")


def meta_score(c: dict, n: Need, frame: tuple[int, int]) -> dict:
    about = (str(c.get("about", "")) + " " + str(c.get("location", ""))).lower()
    sub = _terms(n.subject)
    rel = sum(1 for t in sub if t in about) / max(1, len(sub))
    geo = bool(n.place) and n.place.lower() in about
    old = any(w in about for w in OLD_WORDS)
    era = 1.0 if not n.era or n.era >= 1990 else (1.0 if old else 0.25)
    w, h = int(c.get("width") or 0), int(c.get("height") or 0)
    res = min(1.0, min(w, h) / max(1, n.min_side)) if w and h else 0.5
    ar, fr = (w / h if w and h else 1.6), frame[0] / frame[1]
    crop = min(ar / fr, fr / ar)
    # real archives first (MASTER_DIRECTIVES §5): for a specific person, place or event, an archive record of it beats
    # an equally relevant stock picture; stock is never the default
    arch = c.get("site") in ARCHIVES
    total = 0.4 * rel + (0.2 if geo else 0.0) + 0.15 * era + 0.15 * res + 0.1 * crop + (0.1 if arch and n.specific and rel >= 0.5 else 0.0)
    return {"relevance": round(rel, 2), "geography": geo, "period": round(era, 2), "resolution": round(res, 2), "crop_kept": round(crop, 2),
            "archive": arch, "meta": round(total, 3)}


def pixel_score(path: Path, palette: dict | None = None, prev: Path | None = None) -> dict:
    """Exposure, contrast, sharpness, composition (interest away from dead centre and edges), palette fit, continuity."""
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(path).convert("RGB")
    im.thumbnail((640, 640))
    a = np.asarray(im, np.float32)
    y = a.mean(axis=2)
    expo = 1 - min(1.0, abs(y.mean() - 120) / 120)
    contrast = min(1.0, y.std() / 55)
    edges = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES), np.float32)
    sharp = min(1.0, edges.var() / 900)
    hh, ww = edges.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    wsum = edges.sum() or 1
    cx, cy = (xx * edges).sum() / wsum / ww, (yy * edges).sum() / wsum / hh
    # interest on the thirds reads as composed; hard against an edge reads as accidental
    comp = 1 - min(1.0, min(abs(cx - 1 / 3), abs(cx - 2 / 3), abs(cx - .5) + .08) * 3) * .5 - (0.3 if min(cx, cy, 1 - cx, 1 - cy) < .12 else 0)
    fit = 0.5
    if palette and palette.get("paper"):
        warm = (a[..., 0].mean() - a[..., 2].mean()) / 255
        pw = palette["paper"]
        want = (int(pw[1:3], 16) - int(pw[5:7], 16)) / 255
        fit = 1 - min(1.0, abs(warm - want) * 3)
    cont = 0.5
    if prev and Path(prev).is_file():
        b = np.asarray(Image.open(prev).convert("RGB").resize(im.size), np.float32)
        h1, _ = np.histogram(a, bins=24, range=(0, 255))
        h2, _ = np.histogram(b, bins=24, range=(0, 255))
        cont = float(np.minimum(h1 / h1.sum(), h2 / h2.sum()).sum())
    total = .22 * expo + .2 * contrast + .2 * sharp + .18 * max(0, comp) + .1 * fit + .1 * cont
    return {"exposure": round(expo, 2), "contrast": round(contrast, 2), "sharpness": round(sharp, 2), "composition": round(max(0, comp), 2),
            "palette": round(fit, 2), "continuity": round(cont, 2), "pixels": round(total, 3)}


def rights(about: str) -> list[str]:
    t = (about or "").lower()
    return [k for k, ws in RIGHTS_WORDS.items() if any(re.search(rf"\b{w}\b", t) for w in ws)]


def select(n: Need, sources: list[tuple[str, str]], cache: Path, ledger: Ledger, palette: dict | None = None,
           prev: Path | None = None, frame: tuple[int, int] = (1920, 1080), keep: int = 4, bar: float = 0.5) -> tuple[dict | None, dict]:
    """(ledger record or None, the decision report: what was searched, every candidate's scores, why one won)."""
    from ..providers import stock_photo, stock_video
    report: dict = {"need": n.__dict__, "library": [], "queries": [], "candidates": [], "chosen": None, "reason": ""}
    # the library first: an asset of this very place, else (for a specific line) a fitting one used as ILLUSTRATIVE
    lib = ledger.find(_terms(n.subject)[:2], n.kind, n.place) if n.place else []
    exact = bool(lib)
    lib = lib or ledger.find(_terms(n.subject)[:2], n.kind)
    if lib:
        rec = ledger.add({**lib[0], "film": n.film, "scene": n.scene})
        rec = dict(rec, illustrative=n.specific and not exact)
        report.update(library=[r["id"] for r in lib], chosen=rec["id"], reason="reused from the asset library"
                      + ("; ILLUSTRATIVE: it does not show the specific place" if rec["illustrative"] else ""))
        return rec, report
    mod = stock_video if n.kind == "video" else stock_photo
    found, seen = [], set()
    for q in queries(n):
        report["queries"].append(q)
        for prov, key in sources:
            try:
                hits = mod.search(prov, key, q, portrait=n.orientation == "portrait")
            except Exception:  # noqa: BLE001 - one source failing is not the end of the search
                continue
            for h in hits:
                if h.get("url") and h["url"] not in seen:
                    seen.add(h["url"])
                    found.append({**h, "query": q, **meta_score(h, n, frame)})
    found.sort(key=lambda c: -c["meta"])
    best = None
    for c in found[:keep]:
        try:
            f = (stock_video.fetch if n.kind == "video" else stock_photo.fetch)(c, cache)
        except Exception as e:  # noqa: BLE001
            c["error"] = str(e)[:80]
            continue
        c["file"] = str(f)
        if n.kind == "photo":
            c.update(pixel_score(f, palette, prev))
        c["score"] = round(.6 * c["meta"] + .4 * c.get("pixels", .5), 3)
        if best is None or c["score"] > best["score"]:
            best = c
    report["candidates"] = [{k: c.get(k) for k in ("url", "page", "site", "query", "meta", "pixels", "score", "relevance", "geography",
                                                    "period", "resolution", "crop_kept", "error")} for c in found[:12]]
    if best is None or best["score"] < bar or best["relevance"] < 0.5:
        report["reason"] = "no candidate good enough: " + ("nothing found" if not found else f"best scored {best['score'] if best else 0}")
        return None, report
    illustrative = n.specific and not best["geography"]
    lic = best.get("licence") or ""
    rec = ledger.add({
        "type": n.kind, "file": best["file"], "url": best["url"], "page": best.get("page", ""), "site": best.get("site", ""),
        "original_filename": Path(urlparse(best["url"]).path).name or best.get("id", ""), "creator": best.get("creator", ""),
        "credit": best.get("credit", ""), "downloaded": date.today().isoformat(), "licence": lic,
        "licence_terms": LICENCES.get(lic, "check the licence on the asset page before publishing"),
        "attribution": best.get("attribution", "check"), "about": best.get("about", ""), "rights_check": rights(best.get("about", "")),
        "illustrative_reason": (f"generic {n.subject}; not shown to be {n.place}" if illustrative else ""), "film": n.film, "scene": n.scene,
        "categories": {"subject": _terms(n.subject), "location": [n.place] if best["geography"] else [], "type": n.kind,
                       "quality": "high" if best.get("pixels", .5) >= .6 and best["resolution"] >= 1 else "usable", "licence": lic},
        "scores": {k: best.get(k) for k in ("meta", "pixels", "score")}})
    if best.get("track") and best.get("key"):
        try:   # Unsplash API terms: report the download
            import httpx
            httpx.get(best["track"], headers={"Authorization": f"Client-ID {best['key']}"}, timeout=10)
        except Exception:  # noqa: BLE001
            pass
    report.update(chosen=rec["id"], reason=f"highest score {best['score']} ({best['site']}, query '{best['query']}')"
                  + ("; ILLUSTRATIVE: it does not show the specific place" if illustrative else ""))
    rec["illustrative"] = illustrative
    return rec, report
