"""Real archive photographs for history lines (the way a video essay uses period photos and clippings): Wikimedia
Commons, keeping only public-domain and openly licensed files (PD, CC0, CC BY, CC BY-SA) and recording the credit.
No key needed. Used for lines the writer marks "Archive:"; the match check still has to agree the photo shows the
line, and the channel's faceless rule still applies."""
from __future__ import annotations

import html
import re

import httpx

from .base import ProviderError
from .stock_video import UA

API = "https://commons.wikimedia.org/w/api.php"
_OK = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by(-sa)?( \d\.\d)?|cc-by(-sa)?(-\d\.\d)?|no restrictions)", re.I)


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def search(query: str, timeout: float = 20, limit: int = 8) -> list[dict]:
    """Photos for the query, best first: [{url, width, height, credit, title}]. Empty on no result."""
    try:
        r = httpx.get(API, timeout=timeout, headers={"User-Agent": UA}, params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": limit,
            "gsrsearch": f"{query} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": 2000})
        r.raise_for_status()
        pages = (r.json().get("query") or {}).get("pages") or {}
    except (httpx.HTTPError, ValueError) as e:
        raise ProviderError(f"archive photo search failed: {e}") from e
    out = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = _plain((meta.get("LicenseShortName") or {}).get("value", ""))
        if not _OK.match(licence) or info.get("mime") not in ("image/jpeg", "image/png", "image/tiff"):
            continue
        if min(int(info.get("width") or 0), int(info.get("height") or 0)) < 500:
            continue
        artist = _plain((meta.get("Artist") or {}).get("value", "")) or "unknown photographer"
        title = re.sub(r"^File:|\.\w+$", "", p.get("title", ""))
        taken = _plain((meta.get("DateTimeOriginal") or meta.get("DateTime") or {}).get("value", ""))
        year = next((int(y) for y in re.findall(r"\b(1[89]\d\d|20\d\d)\b", taken)), 0)   # when it was taken
        out.append({"url": info.get("thumburl") or info.get("url"), "width": int(info.get("width") or 0),
                    "height": int(info.get("height") or 0), "title": title, "year": year,
                    "credit": f"{artist[:60]} / Wikimedia Commons ({licence})"})
    return out
