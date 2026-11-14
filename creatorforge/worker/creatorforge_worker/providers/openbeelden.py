"""Open Beelden (Open Images, Netherlands Institute for Sound and Vision): ~11,000 openly licensed films, mostly
Dutch newsreels and archive footage from 1900 on, plus documentaries and amateur-free institutional film.

The site's search pages are unreliable from cloud servers, but its OAI-PMH catalogue feed (the channel archives
publish for exactly this) carries everything needed per film: title, description, date, place, licence, the
attribution line and direct HD MP4 links. So the studio keeps a small local index of that catalogue (metadata only,
no video) and searches it; a film is downloaded only when a shot uses it.

Licences kept: Public Domain Mark, CC0, CC BY, CC BY-SA. Anything NC or ND is dropped at harvest time.
Titles and descriptions are Dutch, so English search words are also looked up in Dutch (DUTCH below).
"""
from __future__ import annotations

import gzip
import json
import re
import time
from pathlib import Path

import httpx

UA = "CreatorForge-footage-check/1.0"
FEED = "https://www.openbeelden.nl/feeds/oai/"
INDEX = Path(__file__).with_name("openbeelden_index.jsonl.gz")
_OPEN = re.compile(r"publicdomain/(mark|zero)|licenses/by(-sa)?/", re.I)

# common documentary words -> Dutch equivalents found in the catalogue's titles, subjects and descriptions
DUTCH = {
    "flood": "overstroming watersnood", "floods": "overstroming watersnood", "dike": "dijk", "dam": "dam", "sea": "zee",
    "water": "water", "storm": "storm", "war": "oorlog", "army": "leger", "soldier": "soldaat soldaten", "soldiers": "soldaten",
    "bomb": "bom bombardement", "election": "verkiezingen verkiezing", "elections": "verkiezingen", "vote": "stemmen",
    "parliament": "parlement kamer", "government": "regering", "minister": "minister", "queen": "koningin",
    "king": "koning", "protest": "demonstratie protest", "strike": "staking", "crowd": "menigte publiek",
    "children": "kinderen", "child": "kind kinderen", "school": "school", "family": "gezin familie", "women": "vrouwen",
    "work": "werk arbeid", "factory": "fabriek", "farm": "boerderij landbouw", "harbour": "haven", "port": "haven",
    "ship": "schip schepen", "train": "trein", "car": "auto", "bicycle": "fiets", "city": "stad", "street": "straat",
    "market": "markt", "trade": "handel", "money": "geld", "bank": "bank", "hospital": "ziekenhuis", "doctor": "dokter arts",
    "health": "gezondheid", "disease": "ziekte", "food": "voedsel eten", "hunger": "honger", "refugees": "vluchtelingen",
    "colony": "kolonie", "colonial": "koloniaal", "indonesia": "indonesie indie", "fire": "brand", "snow": "sneeuw",
    "ice": "ijs", "winter": "winter", "summer": "zomer", "sport": "sport", "football": "voetbal", "church": "kerk",
    "airport": "vliegveld luchthaven", "plane": "vliegtuig", "aircraft": "vliegtuig", "television": "televisie",
    "radio": "radio", "newsreel": "polygoon journaal", "history": "geschiedenis", "europe": "europa", "germany": "duitsland",
    "russia": "rusland", "america": "amerika", "india": "india",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zà-ÿ0-9]{3,}", (text or "").lower())


def _record(xml: str) -> dict | None:
    tag = lambda t: [re.sub(r"\s+", " ", x).strip() for x in re.findall(rf"<oi:{t}[^>]*>(.*?)</oi:{t}>", xml, re.S)]
    lic = (tag("license") or [""])[0]
    if not _OPEN.search(lic) or re.search(r"-nc|-nd", lic, re.I):
        return None
    mp4 = [m for m in re.findall(r'<oi:medium format="hd">(https://[^<]+?\.mp4)</oi:medium>', xml)]
    mp4 = mp4 or re.findall(r'<oi:medium format="[^"]*">(https://[^<]+?\.mp4)</oi:medium>', xml)
    if not mp4:
        return None
    ident = (re.findall(r"<identifier>oai:openimages\.eu:(\d+)</identifier>", xml) or [""])[0]
    return {"id": ident, "title": (tag("title") or [""])[0][:200], "date": (tag("date") or [""])[0][:10],
            "about": " ".join(tag("description") + tag("abstract"))[:600], "subjects": tag("subject")[:12],
            "places": tag("spatial")[:6], "licence": lic, "mp4": mp4[0],
            "attribution": (tag("attributionName") or ["Beeld en Geluid"])[0][:200]}


def harvest(out: Path = INDEX, pause: float = 3.0, tries: int = 8, log=print) -> int:
    """Walk the whole OAI feed politely (one page at a time, a pause between pages, patient retries on the site's
    frequent connection resets) and write the open-licence films to a gzipped JSON-lines index."""
    params, rows, page = {"verb": "ListRecords", "metadataPrefix": "oai_oi"}, [], 0
    while True:
        for i in range(tries):
            try:
                r = httpx.get(FEED, params=params, headers={"User-Agent": UA}, timeout=90)
                r.raise_for_status()
                break
            except Exception as e:                       # noqa: BLE001 - the site resets often; back off and retry
                log(f"page {page}: retry {i + 1} ({type(e).__name__})")
                time.sleep(pause * (i + 2))
        else:
            raise RuntimeError(f"Open Beelden feed unreachable at page {page}; {len(rows)} films kept so far")
        rows += [x for x in (_record(rec) for rec in re.findall(r"(?s)<record>.*?</record>", r.text)) if x]
        page += 1
        token = re.search(r"<resumptionToken[^>]*>([^<]+)</resumptionToken>", r.text)
        log(f"page {page}: {len(rows)} open films")
        if not token:
            break
        params = {"verb": "ListRecords", "resumptionToken": token.group(1)}
        time.sleep(pause)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


_cache: list[dict] | None = None


def _index() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = []
        if INDEX.is_file():
            with gzip.open(INDEX, "rt", encoding="utf-8") as f:
                _cache = [json.loads(line) for line in f if line.strip()]
    return _cache


def search(query: str, limit: int = 3) -> list[dict]:
    """Films whose title, subjects, places or description match the query (English words also tried in Dutch).
    Every query word must match, in English or in Dutch; titles and subjects count more than descriptions."""
    want = []
    for w in _words(query):
        if w in {"the", "and", "with", "from", "for", "into", "over"}:
            continue
        want.append({w, *DUTCH.get(w, "").split()})
    if not want:
        return []
    scored = []
    for row in _index():
        head = set(_words(" ".join([row["title"], *row["subjects"], *row["places"]])))
        body = set(_words(row["about"]))
        score, ok = 0, True
        for alts in want:
            if alts & head:
                score += 2
            elif alts & body:
                score += 1
            else:
                ok = False
                break
        if ok:
            scored.append((score, row))
    scored.sort(key=lambda s: -s[0])
    out = []
    for _, row in scored[:limit]:
        year = row["date"][:4]
        out.append({"url": row["mp4"], "width": 1280, "height": 720, "duration": 0.0, "trim": True, "site": "openbeelden",
                    "credit": f"{row['attribution']} / Open Beelden" + (f", {year}" if year else ""),
                    "creator": row["attribution"], "licence": row["licence"], "id": row["id"],
                    "page": f"https://www.openbeelden.nl/media/{row['id']}", "about": f"{row['title']} {row['about'][:200]}",
                    "archive": True, "attribution": "not required" if "publicdomain" in row["licence"] else f"required: {row['attribution']}"})
    return out
