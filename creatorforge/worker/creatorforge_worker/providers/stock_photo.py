"""Real photos: Unsplash and Pixabay (free keys), and with no key Openverse, Wikimedia Commons, the NASA image library
and the Library of Congress. Only material whose licence or rights statement allows commercial use is returned:
public domain, CC0, CC BY and CC BY-SA (share-alike flagged), NASA media (not copyrighted unless marked), and Library
of Congress items marked "no known restrictions". Every result carries its page, author, licence and attribution
for the asset ledger and the credits."""
from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from .base import ProviderError
from .stock_video import UA, relevant

FREE_SOURCES = ("openverse", "wikimedia", "nasa", "loc")
ARCHIVES = ("wikimedia", "nasa", "loc")         # real archives: people, places and events as they were
_OK_LICENCES = {"cc0", "pdm", "by", "by-sa"}


def _unsplash(key: str, query: str, portrait: bool, timeout: float) -> list[dict]:
    r = httpx.get("https://api.unsplash.com/search/photos", timeout=timeout,
                  headers={"Authorization": f"Client-ID {key}", "Accept-Version": "v1"},
                  params={"query": query, "per_page": 10, "content_filter": "high",
                          "orientation": "portrait" if portrait else "landscape"})
    r.raise_for_status()
    out = []
    for p in r.json().get("results", []):
        raw = (p.get("urls") or {}).get("raw")
        if not raw:
            continue
        name = (p.get("user") or {}).get("name") or "an Unsplash photographer"
        about = " ".join([str(p.get("alt_description") or ""), str(p.get("description") or ""),
                          " ".join(str(t.get("title", "")) for t in p.get("tags") or [] if isinstance(t, dict))])
        out.append({"url": f"{raw}&w=2160&q=85&fm=jpg&fit=max", "width": int(p.get("width") or 0), "about": about,
                    "id": str(p.get("id", "")), "page": (p.get("links") or {}).get("html", ""), "creator": name, "site": "unsplash",
                    "licence": "Unsplash License", "attribution": "not required; credit the photographer and Unsplash",
                    "created": str(p.get("created_at") or "")[:10], "location": str(((p.get("location") or {}).get("name")) or ""),
                    "height": int(p.get("height") or 0), "credit": f"Photo by {name} on Unsplash",
                    # Unsplash's API terms: tell them when a photo is used.
                    "track": (p.get("links") or {}).get("download_location", ""), "key": key})
    return out


def _pixabay(key: str, query: str, portrait: bool, timeout: float) -> list[dict]:
    r = httpx.get("https://pixabay.com/api/", timeout=timeout, params={
        "key": key, "q": query, "image_type": "photo", "per_page": 10, "safesearch": "true",
        "orientation": "vertical" if portrait else "horizontal"})
    r.raise_for_status()
    return [{"url": h["largeImageURL"], "width": int(h.get("imageWidth") or 0), "height": int(h.get("imageHeight") or 0),
             "credit": f"{h.get('user', '')} / Pixabay", "about": str(h.get("tags") or ""), "id": str(h.get("id", "")),
             "page": h.get("pageURL", ""), "creator": str(h.get("user", "")), "site": "pixabay", "licence": "Pixabay Content License",
             "attribution": "not required"}
            for h in r.json().get("hits", []) if h.get("largeImageURL")]


def _pexels(key: str, query: str, portrait: bool, timeout: float) -> list[dict]:
    r = httpx.get("https://api.pexels.com/v1/search", timeout=timeout, headers={"Authorization": key},
                  params={"query": query, "per_page": 10, "orientation": "portrait" if portrait else "landscape"})
    r.raise_for_status()
    return [{"url": (p.get("src") or {}).get("original"), "width": int(p.get("width") or 0),
             "height": int(p.get("height") or 0), "credit": f"{p.get('photographer') or 'a Pexels photographer'} / Pexels",
             "about": str(p.get("alt") or ""), "id": str(p.get("id", "")), "page": p.get("url", ""),
             "creator": str(p.get("photographer") or ""), "site": "pexels", "licence": "Pexels License", "attribution": "not required"} for p in r.json().get("photos", []) if (p.get("src") or {}).get("original")]


def _openverse(query: str, timeout: float) -> list[dict]:
    r = httpx.get("https://api.openverse.org/v1/images/", timeout=timeout, headers={"User-Agent": UA},
                  params={"q": query, "license_type": "commercial,modification", "page_size": 20, "mature": "false"})
    r.raise_for_status()
    out = []
    for p in r.json().get("results", []):
        lic = str(p.get("license") or "").lower()
        tags = " ".join(str(t.get("name", "")) for t in p.get("tags") or [] if isinstance(t, dict))
        if lic not in _OK_LICENCES or not p.get("url") or not relevant(query, f"{p.get('title', '')} {tags}"):
            continue
        version = f" {p['license_version']}" if p.get("license_version") else ""
        label = "Public domain" if lic in ("cc0", "pdm") else f"CC {lic.upper()}{version}"
        who = (p.get("creator") or "unknown author")[:60]
        out.append({"url": p["url"], "width": int(p.get("width") or 0), "height": int(p.get("height") or 0),
                    "credit": f"{who} / {p.get('source') or 'Openverse'} ({label})", "about": f"{p.get('title', '')} {tags}",
                    "id": str(p.get("id", "")), "page": p.get("foreign_landing_url", ""), "creator": who, "site": "openverse",
                    "licence": label, "attribution": "not required" if lic in ("cc0", "pdm") else
                    f"required: {who}, {p.get('title', '')}, {label}" + (", share alike" if lic == "by-sa" else "")})
    return out


def _clean(x) -> str:
    import html as _html
    import re as _re
    return _html.unescape(_re.sub(r"<[^>]+>", "", str(x or ""))).strip()


def _wikimedia(query: str, timeout: float) -> list[dict]:
    """Wikimedia Commons photographs (no key): public domain, CC0, CC BY and CC BY-SA only."""
    import re as _re
    from .stock_video import _FREE_LICENCE
    r = httpx.get("https://commons.wikimedia.org/w/api.php", timeout=timeout, headers={"User-Agent": UA}, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {query}",
        "gsrnamespace": 6, "gsrlimit": 20, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 2400})
    r.raise_for_status()
    pages = sorted(((r.json().get("query") or {}).get("pages") or {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        val = lambda k: _clean((meta.get(k) or {}).get("value", ""))
        licence = val("LicenseShortName")
        if not _FREE_LICENCE.search(licence) or val("NonFree"):
            continue
        title = p.get("title", "").removeprefix("File:").rsplit(".", 1)[0]
        about = f"{title} {val('ImageDescription')[:400]} {val('Categories')}"
        if not relevant(query, about):
            continue
        who = val("Artist")[:60] or "unknown author"
        pd = bool(_re.search(r"public domain|\bpd\b|cc0", licence, _re.I))
        sa = "sa" in licence.lower().replace("usa", "")
        out.append({"url": info.get("thumburl") or info.get("url"), "width": int(info.get("thumbwidth") or info.get("width") or 0),
                    "height": int(info.get("thumbheight") or info.get("height") or 0), "about": about,
                    "credit": f"{who} / Wikimedia Commons ({licence})", "id": str(p.get("pageid", "")),
                    "page": info.get("descriptionurl", ""), "creator": who, "site": "wikimedia", "licence": licence,
                    "attribution": "not required" if pd else f"required: {who}, {title}, {licence}" + (", share alike" if sa else ""),
                    "archive": True})
    return out


def _nasa(query: str, timeout: float) -> list[dict]:
    """The NASA image library (no key). NASA media is generally not copyrighted; items whose text names another
    rights holder or a copyright are skipped."""
    import re as _re
    from urllib.parse import quote as _q
    r = httpx.get("https://images-api.nasa.gov/search", timeout=timeout, headers={"User-Agent": UA},
                  params={"q": query, "media_type": "image", "page_size": 20})
    r.raise_for_status()
    out = []
    for it in (r.json().get("collection") or {}).get("items", []):
        d = (it.get("data") or [{}])[0]
        about = f"{d.get('title', '')} {_clean(d.get('description', ''))[:500]} {' '.join(d.get('keywords') or [])}"
        if not d.get("nasa_id") or not relevant(query, about) or _re.search(r"©|copyright|courtesy of (?!nasa)", about, _re.I):
            continue
        try:
            a = httpx.get(f"https://images-api.nasa.gov/asset/{_q(d['nasa_id'])}", timeout=timeout, headers={"User-Agent": UA})
            hrefs = [x.get("href", "") for x in (a.json().get("collection") or {}).get("items", [])]
        except (httpx.HTTPError, ValueError):
            continue
        pick = next((h for tag in ("~large.jpg", "~orig.jpg", "~medium.jpg") for h in hrefs if h.lower().endswith(tag)), "")
        if not pick:
            continue
        who = d.get("photographer") or d.get("center") or "NASA"
        out.append({"url": pick.replace("http://", "https://"), "width": 0, "height": 0, "about": about,
                    "credit": f"{who} / NASA", "id": d["nasa_id"], "page": f"https://images.nasa.gov/details/{_q(d['nasa_id'])}",
                    "creator": who, "site": "nasa", "licence": "NASA media (not copyrighted unless noted)",
                    "attribution": "NASA (credit requested)", "archive": True, "date": str(d.get("date_created", ""))[:10]})
        if len(out) >= 4:
            break
    return out


def _loc(query: str, timeout: float) -> list[dict]:
    """Library of Congress photographs (no key), only items whose rights statement says there are no known
    restrictions on publication."""
    import re as _re
    r = httpx.get("https://www.loc.gov/photos/", timeout=timeout, headers={"User-Agent": UA},
                  params={"q": query, "fo": "json", "c": 25})
    r.raise_for_status()
    out = []
    for it in r.json().get("results", []):
        item = it.get("item") or {}
        rights = " ".join(str(x) for x in [it.get("rights_advisory"), item.get("rights_advisory"), it.get("rights"),
                                           item.get("rights")] if x)
        if not _re.search(r"no known restrictions|public domain", rights, _re.I):
            continue
        about = f"{it.get('title', '')} {' '.join(it.get('subject') or [])} {_clean(' '.join(it.get('description') or []))[:300]}"
        if not relevant(query, about):
            continue
        imgs = [u for u in it.get("image_url") or [] if isinstance(u, str)]
        if not imgs:
            continue
        url = imgs[-1].split("#")[0]
        if url.startswith("//"):
            url = "https:" + url
        who = ", ".join((it.get("contributor") or [])[:1]) or "Library of Congress"
        out.append({"url": url, "width": 0, "height": 0, "about": about, "credit": f"{who} / Library of Congress",
                    "id": str(it.get("id", ""))[-40:], "page": it.get("url") or it.get("id", ""), "creator": who, "site": "loc",
                    "licence": "No known restrictions on publication (Library of Congress)",
                    "attribution": "Library of Congress, Prints & Photographs Division (credit requested)", "archive": True,
                    "date": str(it.get("date", ""))[:10]})
        if len(out) >= 5:
            break
    return out


def search(provider: str, key: str, query: str, portrait: bool = True, timeout: float = 20) -> list[dict]:
    if provider == "mock":
        return [{"url": f"mock://{query}", "width": 1080, "height": 1920, "credit": "test photo"}]
    try:
        if provider == "unsplash":
            found = _unsplash(key, query, portrait, timeout)
        elif provider == "pixabay":
            found = _pixabay(key, query, portrait, timeout)
        elif provider == "pexels":
            found = _pexels(key, query, portrait, timeout)
        elif provider == "openverse":
            found = _openverse(query, timeout)
        elif provider == "wikimedia":
            found = _wikimedia(query, timeout)
        elif provider == "nasa":
            found = _nasa(query, timeout)
        elif provider == "loc":
            found = _loc(query, timeout)
        else:
            return []
    except (httpx.HTTPError, ValueError, KeyError) as e:
        raise ProviderError(f"stock photo search failed: {e}") from e
    # Big enough to fill the frame after the slow zoom (short side ~900 px or more), right orientation first.
    found = [f for f in found if min(f["width"], f["height"]) >= 900 or not f["width"]]
    found.sort(key=lambda f: (f["height"] > f["width"]) != portrait)
    return found


def search_any(sources: list[tuple[str, str]], query: str, portrait: bool = True) -> list[dict]:
    for provider, key in sources:
        try:
            found = search(provider, key, query, portrait)
        except ProviderError:
            continue
        if found:
            return found
    return []


def fetch(photo: dict, cache: Path, timeout: float = 60) -> Path:
    """Downloads the photo and re-encodes it with FFmpeg (which also proves it is a real image); returns a JPEG."""
    from ..media import ff
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / f"{hashlib.sha256(photo['url'].encode()).hexdigest()[:24]}.jpg"
    if dst.is_file() and dst.stat().st_size > 10_000:
        return dst
    raw = dst.with_suffix(".download")
    out = dst.with_suffix(".part.jpg")
    try:
        if photo["url"].startswith("mock://"):
            ff.run(["-f", "lavfi", "-i", "color=c=0x283c5a:s=1080x1920", "-frames:v", "1", str(out)])
        else:
            r = httpx.get(photo["url"], timeout=timeout, follow_redirects=True, headers={"User-Agent": UA})
            r.raise_for_status()
            if len(r.content) > 40 * 1024 * 1024:
                raise ProviderError("stock photo larger than 40 MB")
            raw.write_bytes(r.content)
            # Longest side at most 2400 px; plenty for the slow zoom on a 1080x1920 frame.
            ff.run(["-i", str(raw), "-frames:v", "1", "-vf",
                    "scale='if(gt(iw,ih),min(2400,iw),-2)':'if(gt(iw,ih),-2,min(2400,ih))'", "-q:v", "2", str(out)])
    except (httpx.HTTPError, OSError, ff.MediaError) as e:
        out.unlink(missing_ok=True)
        raise ProviderError(f"stock photo download failed: {e}") from e
    finally:
        raw.unlink(missing_ok=True)
    out.replace(dst)
    if photo.get("track"):
        try:   # best effort: Unsplash counts the download for the photographer
            httpx.get(photo["track"], timeout=10, headers={"Authorization": f"Client-ID {photo.get('key', '')}"})
        except httpx.HTTPError:
            pass
    return dst
