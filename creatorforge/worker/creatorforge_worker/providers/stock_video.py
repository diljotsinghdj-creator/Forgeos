"""Real stock footage for beats that don't need a specific character: Pixabay videos (free key, free for
commercial use; old Pexels keys also work), then two keyless sources - the NASA Image and Video Library (space,
science, Earth; public domain) and Wikimedia Commons (history, real events, animals; free licences, credited).
The app lends its key per production; clips are cached by URL."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path
from urllib.parse import quote

import httpx

from .base import ProviderError

FREE_SOURCES = ("nasa", "svs", "wikimedia")
# Prelinger (1930s-80s films, mostly black and white, often 480p): only for history lines (Archive:)
ARCHIVE_SOURCES = ("archive", "loc", "wellcome")
MIN_CLIP_SIDE = 720       # a smaller clip is blown up into visible pixels on a 1080p frame
UA = "CreatorForge/1.0 (video worker; https://github.com/diljotsinghdj-creator/Forgeos)"
_STOP = {"the", "and", "with", "from", "into", "over", "for", "of", "a", "an", "in", "on", "at", "to", "by"}
# Free licences that allow commercial use and editing (credit goes in the publish kit).
_FREE_LICENCE = re.compile(r"public domain|\bpd\b|cc0|godl|cc[ -]by(?![ -]?n[cd])(?:[ -]sa)?(?![ -]?n[cd])", re.I)


def _words(query: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2 and w not in _STOP]


def relevant(query: str, text: str) -> bool:
    """Keyless libraries rank loosely, so a clip must actually be about the search: every word (all but one for
    3+ word searches) appears in its title, description or keywords. Prefix match, so "wave" finds "waves"."""
    want = _words(query)
    if not want:
        return False
    have = set(re.findall(r"[a-z0-9]+", text.lower()))
    hits = sum(1 for w in want if any(h.startswith(w) or w.startswith(h) and len(h) > 3 for h in have))
    return hits >= (len(want) - 1 if len(want) >= 3 else len(want))


def _https(url: str) -> str:
    url = url.replace("http://", "https://", 1)
    return quote(url, safe=":/%?&=~._-")


def _nasa(query: str, timeout: float) -> list[dict]:
    r = httpx.get("https://images-api.nasa.gov/search", params={"q": query, "media_type": "video", "page_size": 20},
                  timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    out = []
    for item in (r.json().get("collection") or {}).get("items", [])[:20]:
        d = (item.get("data") or [{}])[0]
        about = " ".join([d.get("title", ""), d.get("description", "")[:400], " ".join(d.get("keywords") or [])])
        if not d.get("nasa_id") or not relevant(query, about):
            continue
        a = httpx.get(f"https://images-api.nasa.gov/asset/{quote(d['nasa_id'])}", timeout=timeout, headers={"User-Agent": UA})
        if a.status_code != 200:
            continue
        files = [f.get("href", "") for f in (a.json().get("collection") or {}).get("items", [])]
        # ~large is about 1080p; ~orig can be a multi-GB master, ~mobile is too soft.
        for size in ("~large.mp4", "~medium.mp4"):
            pick = next((f for f in files if f.endswith(size)), None)
            if pick:
                out.append({"url": _https(pick), "width": 1920, "height": 1080, "duration": 0.0,
                            "credit": "NASA", "trim": True})
                break
        if len(out) >= 3:
            break
    return out


# Publishers whose free videos are mirrored on Wikimedia Commons, found by the source link on each file page.
# The licence is still read from each file, so a file that is not free never gets through.
PUBLISHERS = {
    "kremlin": ("kremlin.ru", "Kremlin.ru"),                       # CC BY 4.0
    "whitehouse": ("whitehouse.gov", "The White House"),            # public domain
    "cspan": ("c-span.org", "C-SPAN (House/Senate floor)"),         # floor feeds only; C-SPAN's own shows are not free
    "openbeelden": ("openbeelden.nl", "Open Beelden / Beeld en Geluid"),  # CC BY-SA
    "europarl": ("europarl.europa.eu", "European Parliament"),
    "agenciabrasil": ("agenciabrasil.ebc.com.br", "Agência Brasil"),     # CC BY
    "pib": ("pib.gov.in", "Press Information Bureau, Govt. of India"),  # GODL-India
    "nps": ("nps.gov", "US National Park Service"),                 # public domain
    "noaa": ("noaa.gov", "NOAA"),                                   # public domain
    "voanews": ("voanews.com", "Voice of America"),                 # public domain
}


def _wikimedia(query: str, timeout: float, publisher: str = "") -> list[dict]:
    domain, label = PUBLISHERS.get(publisher, ("", ""))
    narrow = f' insource:"{domain}"' if domain else ""
    r = httpx.get("https://commons.wikimedia.org/w/api.php", timeout=timeout, headers={"User-Agent": UA}, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:video {query}{narrow}",
        "gsrnamespace": 6, "gsrlimit": 20, "prop": "videoinfo",
        "viprop": "url|size|mime|extmetadata|derivatives"})
    r.raise_for_status()
    pages = sorted(((r.json().get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("videoinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        val = lambda k: html.unescape(re.sub(r"<[^>]+>", "", str((meta.get(k) or {}).get("value", "")))).strip()
        licence = val("LicenseShortName")
        if not _FREE_LICENCE.search(licence) or val("NonFree"):
            continue
        title = p.get("title", "").removeprefix("File:").rsplit(".", 1)[0]
        if not relevant(query, f"{title} {val('ImageDescription')[:400]} {val('Categories')}"):
            continue
        if min(int(info.get("height") or 0), int(info.get("width") or 0)) < MIN_CLIP_SIDE or float(info.get("duration") or 0) < 2:
            continue
        # A transcoded copy near 1080p downloads far faster than the original master.
        ders = [d for d in info.get("derivatives") or [] if d.get("src") and 480 <= int(d.get("height") or 0) <= 1080]
        ders.sort(key=lambda d: -int(d.get("height") or 0))
        src = ders[0] if ders else info
        url = src.get("src") or info.get("url")
        if not url or int(info.get("size") or 0) > 200 * 1024 * 1024 and not ders:
            continue
        artist = val("Artist")[:60] or label or "unknown author"
        out.append({"url": url, "width": int(src.get("width") or info.get("width") or 0),
                    "height": int(src.get("height") or info.get("height") or 0),
                    "duration": float(info.get("duration") or 0),
                    "credit": f"{label or artist} / Wikimedia Commons ({licence})", "trim": True, "site": publisher or "wikimedia",
                    "creator": artist, "licence": licence, "page": info.get("descriptionurl", ""), "id": str(p.get("pageid", "")),
                    "about": f"{title} {val('ImageDescription')[:200]}", "archive": True,
                    "attribution": "not required" if re.search(r"public domain|\bpd\b|cc0", licence, re.I) else f"required: {artist}, {title}, {licence}"})
        if len(out) >= 3:
            break
    return out


# Internet Archive collections: (search filter, credit, creator, site, licence when the item has no licence field)
IA_COLLECTIONS = {
    "archive": ("collection:(prelinger)", "Prelinger Archives / Internet Archive", "Prelinger Archives", "Public domain (Prelinger Archives, no licence field)"),
    # US government films (FedFlix, NARA's own uploads, CBS WWI, Army films): works of the US government are public domain
    "usgov": ("collection:(FedFlix OR usgovfilms OR us-national-archives-youtube)", "US National Archives / Internet Archive",
              "US government (via FedFlix / NARA)", "Public domain (US government work)"),
    # Voice of America news reports: US government work; only items the uploader marked public domain
    "voa": ('(creator:("Voice of America") OR subject:(VOA)) AND licenseurl:(*publicdomain*)', "Voice of America (VOA)",
            "Voice of America", "Public domain (US government work)"),
}


def _archive(query: str, timeout: float, which: str = "archive") -> list[dict]:
    """Films on the Internet Archive. Default: Prelinger (thousands of public-domain 1930s-80s educational films,
    ads and newsreels). `which` picks another collection from IA_COLLECTIONS. The archive asks for a credit."""
    flt, credit, creator, default_lic = IA_COLLECTIONS[which]
    q = " AND ".join(f"({w})" for w in _words(query)[:4])
    if not q:
        return []
    r = httpx.get("https://archive.org/advancedsearch.php", timeout=timeout, headers={"User-Agent": UA}, params={
        "q": f"{q} AND {flt} AND mediatype:(movies)", "fl[]": ["identifier", "title", "description",
        "subject", "licenseurl"], "rows": 15, "output": "json"})
    r.raise_for_status()
    out = []
    for doc in (r.json().get("response") or {}).get("docs", []):
        about = " ".join(str(doc.get(k) or "") for k in ("title", "description", "subject"))[:1500]
        ident = str(doc.get("identifier") or "")
        if any(o["about"][:60] == about[:60] for o in out):
            continue
        lic_url = str(doc.get("licenseurl") or "")
        if not ident or not relevant(query, about) or _PRIVATE.search(about) or re.search(r"-nc|-nd", lic_url):
            continue                     # each film's own licence: non-commercial or no-derivatives films are skipped
        m = httpx.get(f"https://archive.org/metadata/{quote(ident)}", timeout=timeout, headers={"User-Agent": UA})
        if m.status_code != 200:
            continue
        files = [f for f in m.json().get("files") or [] if str(f.get("name", "")).lower().endswith(".mp4")]
        # The h.264 derivative keeps the film's resolution at a sane size; the 512kb copy is a last resort.
        files.sort(key=lambda f: (str(f.get("format", "")) not in ("h.264", "MPEG4", "h.264 HD"),
                                  "512kb" in str(f.get("name", "")).lower(), int(f.get("size") or 0)))
        files = [f for f in files if 0 < int(f.get("size") or 0) <= 200 * 1024 * 1024]
        if files:
            f = files[0]
            out.append({"url": f"https://archive.org/download/{quote(ident)}/{quote(str(f['name']))}",
                        "width": int(f.get("width") or 640), "height": int(f.get("height") or 480),
                        "duration": float(f.get("length") or 0) if str(f.get("length", "")).replace(".", "", 1).isdigit() else 0.0,
                        "credit": credit, "trim": True, "site": which,
                        "creator": creator, "licence": "Public domain mark" if "publicdomain" in lic_url else default_lic, "id": ident,
                        "page": f"https://archive.org/details/{quote(ident)}", "about": about[:300], "archive": True,
                        "attribution": f"{credit} (credit requested)"})
        if len(out) >= 2:
            break
    return out


def _svs(query: str, timeout: float) -> list[dict]:
    """NASA's Scientific Visualization Studio: data visualisations of Earth, climate and space (public domain, NASA
    media policy; credit NASA's Scientific Visualization Studio)."""
    r = httpx.get("https://svs.gsfc.nasa.gov/api/search/", params={"search": query, "limit": 12}, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    out = []
    for hit in r.json().get("results", [])[:12]:
        if not relevant(query, f"{hit.get('title', '')} {hit.get('description', '')}"):
            continue
        it = httpx.get(f"https://svs.gsfc.nasa.gov/api/{hit['id']}", timeout=timeout, headers={"User-Agent": UA})
        if it.status_code != 200:
            continue
        cands = []
        for g in it.json().get("media_groups") or []:
            for m in g.get("items") or []:
                inst = (m or {}).get("instance") or {}
                url = inst.get("url") or ""
                if url.endswith(".mp4") and int(inst.get("width") or 0) >= MIN_CLIP_SIDE and int(inst.get("filesize") or 0) < 300 * 1024 * 1024:
                    cands.append((abs(int(inst.get("width") or 0) - 1920), url, inst))
        if cands:
            cands.sort(key=lambda c: c[0])
            _, url, inst = cands[0]
            out.append({"url": _https(url), "width": int(inst.get("width") or 1920), "height": int(inst.get("height") or 1080),
                        "duration": 0.0, "credit": "NASA's Scientific Visualization Studio", "trim": True, "site": "svs",
                        "creator": "NASA SVS", "licence": "Public domain (NASA media policy)", "id": str(hit["id"]),
                        "page": f"https://svs.gsfc.nasa.gov/{hit['id']}", "about": str(hit.get("title", ""))[:300],
                        "attribution": "NASA's Scientific Visualization Studio (credit requested)"})
        if len(out) >= 3:
            break
    return out


def _loc(query: str, timeout: float) -> list[dict]:
    """Library of Congress films: only those published before 1930 (public domain in the US by age) or marked
    'no known restrictions'. Early actualities, newsreels and events."""
    r = httpx.get("https://www.loc.gov/film-and-videos/", params={"q": query, "fo": "json", "c": 25}, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    out = []
    for x in r.json().get("results", []):
        year = re.search(r"(1[89]\d\d|20\d\d)", str(x.get("date") or ""))
        rights = " ".join(map(str, x.get("rights") or [])) if isinstance(x.get("rights"), list) else str(x.get("rights") or "")
        free = (year and int(year.group(1)) < 1930) or "no known restrictions" in rights.lower()
        if not free or x.get("access_restricted") or not relevant(query, f"{x.get('title', '')} {' '.join(map(str, x.get('description') or []))} {' '.join(map(str, x.get('subject') or []))}"):
            continue
        for res in x.get("resources") or []:
            if res.get("video") and int(res.get("height") or 0) >= 480:
                out.append({"url": res["video"], "width": int(res.get("width") or 1440), "height": int(res.get("height") or 1080),
                            "duration": float(res.get("duration") or 0), "credit": "Library of Congress", "trim": True, "site": "loc",
                            "creator": "Library of Congress", "id": str(x.get("id", "")), "page": str(x.get("id", "")),
                            "licence": f"Public domain ({year.group(1)}, published before 1930)" if year and int(year.group(1)) < 1930 else "No known restrictions",
                            "about": str(x.get("title", ""))[:300], "archive": True, "attribution": "Library of Congress (credit requested)"})
                break
        if len(out) >= 3:
            break
    return out


_OPEN_WELLCOME = {"cc-by", "cc-0", "pdm"}
# home movies show private individuals, whom the channels never feature (owner's rule); skip them at the source
_PRIVATE = re.compile(r"home movie", re.I)


def _wellcome(query: str, timeout: float) -> list[dict]:
    """Wellcome Collection films (medicine, mind, health history). Only CC BY, CC0 or public-domain items: most of
    its films are CC BY-NC or in copyright, which a monetised channel cannot use."""
    r = httpx.get("https://api.wellcomecollection.org/catalogue/v2/works", timeout=timeout, headers={"User-Agent": UA},
                  params={"query": query, "workType": "g", "pageSize": 30, "include": "items"})
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        lic, manifest = set(), None
        for it in w.get("items") or []:
            for loc in it.get("locations") or []:
                if loc.get("license"):
                    lic.add(loc["license"].get("id"))
                if (loc.get("locationType") or {}).get("id") == "iiif-presentation":
                    manifest = loc.get("url")
        if not lic or not lic <= _OPEN_WELLCOME or not manifest or _PRIVATE.search(str(w.get("title", ""))) or not relevant(query, f"{w.get('title', '')} {w.get('description', '')}"):
            continue
        m = httpx.get(manifest, timeout=timeout, headers={"User-Agent": UA})
        mp4 = re.findall(r'https://[^"]+?\.mp4', m.text) if m.status_code == 200 else []
        if mp4:
            out.append({"url": mp4[0], "width": 720, "height": 576, "duration": 0.0, "credit": "Wellcome Collection", "trim": True,
                        "site": "wellcome", "creator": "Wellcome Collection", "licence": "/".join(sorted(lic)).upper(), "id": w.get("id", ""),
                        "page": f"https://wellcomecollection.org/works/{w.get('id', '')}", "about": str(w.get("title", ""))[:300], "archive": True,
                        "attribution": "not required" if lic <= {"cc-0", "pdm"} else f"required: {w.get('title', '')}, Wellcome Collection, CC BY"})
        if len(out) >= 2:
            break
    return out


def _europeana(query: str, key: str, timeout: float) -> list[dict]:
    """Europeana (European archives): openly reusable videos only (reusability=open). Needs a free personal key in
    the pod's environment (EUROPEANA_KEY); never put a key in a script or a chat."""
    if not key:
        return []
    r = httpx.get("https://api.europeana.eu/record/v2/search.json", timeout=timeout, headers={"User-Agent": UA},
                  params={"query": query, "media": "true", "type": "VIDEO", "reusability": "open", "rows": 15, "wskey": key})
    r.raise_for_status()
    out = []
    for it in r.json().get("items", []):
        url = (it.get("edmIsShownBy") or [""])[0]
        rights = (it.get("rights") or [""])[0]
        if not url or re.search(r"-nc|-nd|/InC", rights) or not relevant(query, " ".join(it.get("title") or []) + " " + " ".join(it.get("dcDescription") or [])):
            continue
        if not re.search(r"\.(mp4|webm|mov)(\?|$)", url, re.I):
            continue
        out.append({"url": url, "width": 1280, "height": 720, "duration": 0.0, "credit": f"{(it.get('dataProvider') or ['Europeana'])[0]} / Europeana",
                    "trim": True, "site": "europeana", "creator": (it.get("dataProvider") or [""])[0], "licence": rights, "id": it.get("id", ""),
                    "page": (it.get("guid") or ""), "about": " ".join(it.get("title") or [])[:300], "archive": True,
                    "attribution": f"required: {(it.get('dataProvider') or [''])[0]}, {rights}"})
        if len(out) >= 3:
            break
    return out


# Observatory video archives on the same platform: (search page, video page prefix, CDN pattern hint, credit fallback)
OBSERVATORIES = {
    "eso": ("https://www.eso.org/public/videos/list/1/?search={q}", "https://www.eso.org/public/videos/{id}/", "ESO"),
    "esahubble": ("https://esahubble.org/videos/?search={q}", "https://esahubble.org/videos/{id}/", "ESA/Hubble"),
    "esawebb": ("https://esawebb.org/videos/?search={q}", "https://esawebb.org/videos/{id}/", "ESA/Webb"),
    "noirlab": ("https://noirlab.edu/public/videos/?search={q}", "https://noirlab.edu/public/videos/{id}/", "NOIRLab/NSF/AURA"),
}


def _observatory(query: str, timeout: float, which: str) -> list[dict]:
    """Space footage and animations from ESO, ESA/Hubble, ESA/Webb and NOIRLab: CC BY 4.0, credit as each page says."""
    search, page, fallback = OBSERVATORIES[which]
    r = httpx.get(search.format(q=quote(query)), timeout=timeout, headers={"User-Agent": UA}, follow_redirects=True)
    r.raise_for_status()
    ids = []
    for i in re.findall(r'href="/(?:public/)?videos/([a-z]+\d{3,}[a-z]?)/"', r.text):
        if i not in ids:
            ids.append(i)
    out = []
    for vid in ids[:8]:
        p = httpx.get(page.format(id=vid), timeout=timeout, headers={"User-Agent": UA}, follow_redirects=True)
        if p.status_code != 200:
            continue
        title = html.unescape(re.sub(r"\s*\|.*$", "", (re.search(r"<title>(.*?)</title>", p.text, re.S) or [None, ""])[1].strip()))
        # the observatory's own search already matched its full record (our page text is thin); the studio's picture
        # check still judges each clip before it is used
        mp4 = [u for u in re.findall(r'https://[^"\'\s<>]+?\.mp4', p.text) if re.search(r"hd_1080p?\d*_screen|hd_1080_screen", u)]
        if not mp4:
            continue
        cm = (re.search(r'Credit:</strong>\s*<div class="credit">(.*?)</div>', p.text, re.S)
              or re.search(r"Credit:</[^>]+>\s*(?:</th>)?\s*<td[^>]*>(.*?)</td>", p.text, re.S))
        credit = html.unescape(re.sub(r"<[^>]+>", " ", cm.group(1))).split("Directed by")[0].strip() if cm else fallback
        credit = re.split(r"\s*(?:Music|Acknowledge?ments?|Directed by)\s*:", re.sub(r"\s+", " ", credit))[0]
        credit = re.sub(r"\s*/\s*", "/", credit).strip()[:120] or fallback      # picture only: their music is never used
        out.append({"url": mp4[0], "width": 1920, "height": 1080, "duration": 0.0, "credit": f"{credit} (CC BY 4.0)", "trim": True,
                    "site": which, "creator": credit, "licence": "CC BY 4.0", "id": vid, "page": page.format(id=vid),
                    "about": title[:300], "attribution": f"required: {credit}, CC BY 4.0"})
        if len(out) >= 2:
            break
    return out


def _dvids(query: str, key: str, timeout: float) -> list[dict]:
    """DVIDS (US military public affairs): public domain, free personal key (DVIDS_KEY in the pod's environment)."""
    if not key:
        return []
    r = httpx.get("https://api.dvidshub.net/search", timeout=timeout, headers={"User-Agent": UA},
                  params={"api_key": key, "q": query, "type": "video", "max_results": 10})
    r.raise_for_status()
    out = []
    for hit in r.json().get("results", []):
        if not relevant(query, f"{hit.get('title', '')} {hit.get('description', '')}"):
            continue
        a = httpx.get("https://api.dvidshub.net/asset", timeout=timeout, headers={"User-Agent": UA},
                      params={"api_key": key, "id": hit.get("id", "")})
        if a.status_code != 200:
            continue
        files = [f for f in ((a.json().get("results") or {}).get("files") or []) if str(f.get("src", "")).endswith(".mp4")]
        files = [f for f in files if int(f.get("height") or 0) >= 720] or files
        if files:
            f = sorted(files, key=lambda f: abs(int(f.get("height") or 0) - 1080))[0]
            out.append({"url": f["src"], "width": int(f.get("width") or 1920), "height": int(f.get("height") or 1080),
                        "duration": 0.0, "credit": "DVIDS / US Department of Defense", "trim": True, "site": "dvids",
                        "creator": "DVIDS", "licence": "Public domain (US government work)", "id": str(hit.get("id", "")),
                        "page": str(hit.get("url", "")), "about": str(hit.get("title", ""))[:300], "archive": True,
                        "attribution": "DVIDS (credit requested)"})
        if len(out) >= 2:
            break
    return out


# Topic routing: which extra libraries a line's subject should search, beyond the always-on free set.
TOPICS = [
    (r"\b(space|planet|galax\w*|star|stars|universe|cosmos|nebula|black hole|telescope|moon|mars|astronom\w*)\b",
     ["esahubble", "eso", "esawebb", "noirlab", "svs"]),
    (r"\b(climate|sea level|flood\w*|drought|storm|hurricane|cyclone|monsoon|ocean|glacier|ice|wildfire|fire|heat ?wave|weather|earth)\b",
     ["svs", "noaa", "usgov", "loc"]),
    (r"\b(forest|wildlife|animal\w*|bear|bird\w*|river|mountain|national park|landscape|nature)\b", ["nps", "noaa"]),
    (r"\b(white house|president|congress|senate|house of representatives|washington|biden|trump|usa?|united states|america\w*)\b",
     ["whitehouse", "cspan", "voa", "voanews", "usgov"]),
    (r"\b(russia\w*|kremlin|putin|moscow|soviet)\b", ["kremlin", "voa", "voanews", "europeana"]),
    (r"\b(europe\w*|eu|brussels|european parliament|netherlands|dutch|germany|france)\b", ["europarl", "openbeelden", "europeana"]),
    (r"\b(brazil\w*|lula|bolsonaro|amazon|latin america)\b", ["agenciabrasil", "voa"]),
    (r"\b(india\w*|delhi|modi|lok sabha|parliament of india|ministry|government of india)\b", ["pib", "voa", "voanews"]),
    (r"\b(war|army|military|soldier\w*|troops|navy|world war|ww[i12]+|cold war|nuclear)\b", ["usgov", "dvids", "loc", "openbeelden"]),
    (r"\b(19[0-7]\d|18\d\d|history|historic\w*|newsreel|old film|vintage|archive)\b", ["usgov", "loc", "openbeelden", "europeana"]),
    (r"\b(mind|brain|emotion\w*|feeling\w*|anxiety|fear|anger|psycholog\w*|mental|habit\w*|child\w*|teen\w*|school|family|behaviou?r)\b",
     ["archive", "wellcome"]),
    (r"\b(medicine|medical|disease|doctor|hospital|health|virus|pandemic)\b", ["wellcome", "usgov"]),
]
KEYED = {"europeana": "EUROPEANA_KEY", "dvids": "DVIDS_KEY"}


def topic_sources(text: str) -> list[tuple[str, str]]:
    """Extra (provider, key) pairs for a line's subject, most specific first; keyed libraries only when the pod has
    their free key in its environment. Never the same provider twice."""
    import os
    out: list[str] = []
    for pattern, names in TOPICS:
        if re.search(pattern, text or "", re.I):
            out += [n for n in names if n not in out]
    return [(n, os.environ.get(KEYED[n], "") if n in KEYED else "") for n in out
            if n not in KEYED or os.environ.get(KEYED[n])]


def search_any(sources: list[tuple[str, str]], query: str, portrait: bool = True) -> list[dict]:
    """First source with a matching clip wins (keyed library first, then the keyless ones). A source that is
    down or rate-limited is skipped."""
    for provider, key in sources:
        try:
            found = search(provider, key, query, portrait)
        except ProviderError:
            continue
        if found:
            return found
    return []


def detect(key: str) -> str:
    """Pixabay is the default (Pexels no longer issues new keys). Old Pexels keys - long, letters and digits only,
    no dash - are still recognised."""
    head, _, tail = key.partition("-")
    if head.isdigit() and tail:
        return "pixabay"
    return "pexels" if len(key) >= 40 and key.isalnum() else "pixabay"


def search(provider: str, key: str, query: str, portrait: bool = True, timeout: float = 20) -> list[dict]:
    """Candidate clips: [{"url", "width", "height", "duration", "credit"}], best first."""
    out: list[dict] = []
    if provider == "mock":
        return [{"url": f"mock://{query}", "width": 1080, "height": 1920, "duration": 4.0, "credit": "test"}]
    try:
        if provider == "nasa":
            return _nasa(query, timeout)
        if provider == "wikimedia":
            return _wikimedia(query, timeout)
        if provider == "archive":
            return _archive(query, timeout)
        if provider in IA_COLLECTIONS and provider != "archive":
            return _archive(query, timeout, provider)
        if provider in PUBLISHERS:
            return _wikimedia(query, timeout, provider)
        if provider in OBSERVATORIES:
            return _observatory(query, timeout, provider)
        if provider == "dvids":
            import os
            return _dvids(query, key or os.environ.get("DVIDS_KEY", ""), timeout)
        if provider == "svs":
            return _svs(query, timeout)
        if provider == "loc":
            return _loc(query, timeout)
        if provider == "wellcome":
            return _wellcome(query, timeout)
        if provider == "europeana":
            import os
            return _europeana(query, key or os.environ.get("EUROPEANA_KEY", ""), timeout)
        if provider == "pixabay":
            r = httpx.get("https://pixabay.com/api/videos/", params={"key": key, "q": query, "per_page": 10,
                                                                      "safesearch": "true"}, timeout=timeout)
            r.raise_for_status()
            for h in r.json().get("hits", []):
                for size in ("large", "medium"):
                    v = (h.get("videos") or {}).get(size) or {}
                    if v.get("url") and v.get("width"):
                        out.append({"url": v["url"], "width": v["width"], "height": v["height"],
                                    "duration": float(h.get("duration") or 0), "credit": f"{h.get('user', '')} / Pixabay",
                                    "about": str(h.get("tags") or ""), "id": str(h.get("id", "")), "page": h.get("pageURL", ""),
                                    "creator": str(h.get("user", "")), "site": "pixabay", "licence": "Pixabay Content License",
                                    "attribution": "not required"})
                        break
        elif provider != "pexels" or not key:
            return []                      # a photo-only source (Unsplash, Openverse, the Library of Congress)
        else:
            r = httpx.get("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=timeout,
                          params={"query": query, "per_page": 10, "orientation": "portrait" if portrait else "landscape"})
            r.raise_for_status()
            for v in r.json().get("videos", []):
                files = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("height")]
                # Big enough for 1080p, but not a 4K file that is slow to download and decode.
                files.sort(key=lambda f: abs(int(f["height"]) - 1920) if portrait else abs(int(f["width"]) - 1920))
                if files:
                    f = files[0]
                    out.append({"url": f["link"], "width": f["width"], "height": f["height"],
                                "duration": float(v.get("duration") or 0), "credit": f"{(v.get('user') or {}).get('name', '')} / Pexels",
                                # Pexels has no tags; its page address describes the clip ("/video/protesters-marching-...")
                                "about": re.sub(r"[-/_\d]+", " ", str(v.get("url") or "").split("/video/")[-1]),
                                "id": str(v.get("id", "")), "page": v.get("url", ""), "creator": str((v.get("user") or {}).get("name", "")),
                                "site": "pexels", "licence": "Pexels License", "attribution": "not required"})
    except (httpx.HTTPError, ValueError, KeyError) as e:
        raise ProviderError(f"stock video search failed: {e}") from e
    # Big enough for a sharp 1080p frame (a 480p film blown up 4x is the "pixelated old picture")
    out = [c for c in out if min(int(c.get("width") or 0), int(c.get("height") or 0)) >= MIN_CLIP_SIDE
           or provider in ("mock", "archive")]
    # Prefer clips in the right orientation that are long enough to cover a beat.
    out.sort(key=lambda c: ((c["height"] > c["width"]) != portrait, c["duration"] < 2.5))
    return out


def fetch(clip: dict, cache: Path, timeout: float = 120) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(clip["url"].encode()).hexdigest()[:24]
    dst = cache / f"{name}.mp4"
    if dst.is_file() and dst.stat().st_size > 10_000:
        return dst
    tmp = cache / f"{name}.part"
    if clip["url"].startswith("mock://"):
        from ..media import ff
        ff.run(["-f", "lavfi", "-i", "testsrc2=s=540x960:d=4:r=24", "-pix_fmt", "yuv420p", "-c:v", "libx264",
                "-preset", "ultrafast", "-f", "mp4", str(tmp)])
        tmp.replace(dst)
        return dst
    try:
        with httpx.stream("GET", clip["url"], timeout=timeout, follow_redirects=True, headers={"User-Agent": UA}) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_bytes(1 << 16):
                    f.write(chunk)
                    if f.tell() > 200 * 1024 * 1024:
                        raise ProviderError("stock clip larger than 200 MB")
    except (httpx.HTTPError, ProviderError) as e:
        tmp.unlink(missing_ok=True)
        raise ProviderError(f"stock clip download failed: {e}") from e
    if clip.get("trim"):
        _trim(tmp, dst)
        tmp.unlink(missing_ok=True)
    else:
        tmp.replace(dst)
    return dst


def _trim(src: Path, dst: Path) -> None:
    """Archive footage (NASA, Wikimedia) often opens on a title card or slate and can be minutes long: keep a short
    piece from about a third of the way in, as plain H.264 (Wikimedia serves WebM)."""
    from ..media import ff
    try:
        total = ff.duration(src)
    except Exception:  # noqa: BLE001 - unreadable download
        total = 0.0
    if total <= 0:
        raise ProviderError("stock clip is not a readable video")
    start = 0.0 if total <= 8 else min(total * 0.3, 30.0, total - 8)
    out = dst.with_suffix(".tmp.mp4")
    try:
        ff.run(["-ss", f"{start:.2f}", "-i", str(src), "-t", "8", "-an", "-vf", "scale=-2:'min(1080,ih)'",
                "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
    except Exception as e:  # noqa: BLE001
        out.unlink(missing_ok=True)
        raise ProviderError(f"stock clip could not be cut: {e}") from e
    out.replace(dst)
