"""Real photos for beats that video libraries couldn't fill: Unsplash (free key, moody high-quality photos), Pixabay
(the same key as its videos) and Openverse (no key; only licences that allow commercial use and editing). A photo gets
the same slow camera move as an AI still. Credits go into the post description."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

import httpx

from .base import ProviderError
from .stock_video import UA, relevant

FREE_SOURCES = ("openverse",)
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
        out.append({"url": f"{raw}&w=2160&q=85&fm=jpg&fit=max", "width": int(p.get("width") or 0),
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
             "credit": f"{h.get('user', '')} / Pixabay"} for h in r.json().get("hits", []) if h.get("largeImageURL")]


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
                    "credit": f"{who} / {p.get('source') or 'Openverse'} ({label})"})
    return out


def search(provider: str, key: str, query: str, portrait: bool = True, timeout: float = 20) -> list[dict]:
    if provider == "mock":
        return [{"url": f"mock://{query}", "width": 1080, "height": 1920, "credit": "test photo"}]
    try:
        if provider == "unsplash":
            found = _unsplash(key, query, portrait, timeout)
        elif provider == "pixabay":
            found = _pixabay(key, query, portrait, timeout)
        elif provider == "openverse":
            found = _openverse(query, timeout)
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
    """Downloads and checks the photo; returns a JPEG in the cache."""
    from PIL import Image
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / f"{hashlib.sha256(photo['url'].encode()).hexdigest()[:24]}.jpg"
    if dst.is_file() and dst.stat().st_size > 10_000:
        return dst
    if photo["url"].startswith("mock://"):
        Image.new("RGB", (1080, 1920), (40, 60, 90)).save(dst, quality=90)
        return dst
    try:
        r = httpx.get(photo["url"], timeout=timeout, follow_redirects=True, headers={"User-Agent": UA})
        r.raise_for_status()
        if len(r.content) > 40 * 1024 * 1024:
            raise ProviderError("stock photo larger than 40 MB")
        im = Image.open(io.BytesIO(r.content))
        im.load()
    except (httpx.HTTPError, OSError, ValueError) as e:
        raise ProviderError(f"stock photo download failed: {e}") from e
    im = im.convert("RGB")
    if max(im.size) > 2400:
        im.thumbnail((2400, 2400))
    tmp = dst.with_suffix(".part.jpg")
    im.save(tmp, quality=92)
    tmp.replace(dst)
    if photo.get("track"):
        try:   # best effort: Unsplash counts the download for the photographer
            httpx.get(photo["track"], timeout=10, headers={"Authorization": f"Client-ID {photo.get('key', '')}"})
        except httpx.HTTPError:
            pass
    return dst
