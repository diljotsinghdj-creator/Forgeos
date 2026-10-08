"""Real stock footage for beats that don't need a specific character: Pexels or Pixabay videos (free keys,
free for commercial use). The app lends its key per production; clips are cached by URL."""
from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from .base import ProviderError


def detect(key: str) -> str:
    """Pixabay keys look like 12345678-0a1b2c...; anything else is treated as a Pexels key."""
    head, _, tail = key.partition("-")
    return "pixabay" if head.isdigit() and len(tail) >= 20 else "pexels"


def search(provider: str, key: str, query: str, portrait: bool = True, timeout: float = 20) -> list[dict]:
    """Candidate clips: [{"url", "width", "height", "duration", "credit"}], best first."""
    out: list[dict] = []
    try:
        if provider == "pixabay":
            r = httpx.get("https://pixabay.com/api/videos/", params={"key": key, "q": query, "per_page": 10,
                                                                      "safesearch": "true"}, timeout=timeout)
            r.raise_for_status()
            for h in r.json().get("hits", []):
                for size in ("large", "medium"):
                    v = (h.get("videos") or {}).get(size) or {}
                    if v.get("url") and v.get("width"):
                        out.append({"url": v["url"], "width": v["width"], "height": v["height"],
                                    "duration": float(h.get("duration") or 0), "credit": f"{h.get('user', '')} / Pixabay"})
                        break
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
                                "duration": float(v.get("duration") or 0), "credit": f"{(v.get('user') or {}).get('name', '')} / Pexels"})
    except (httpx.HTTPError, ValueError, KeyError) as e:
        raise ProviderError(f"stock video search failed: {e}") from e
    # Prefer clips in the right orientation that are long enough to cover a beat.
    out.sort(key=lambda c: ((c["height"] > c["width"]) != portrait, c["duration"] < 2.5))
    return out


def fetch(clip: dict, cache: Path, timeout: float = 120) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / f"{hashlib.sha256(clip['url'].encode()).hexdigest()[:24]}.mp4"
    if dst.is_file() and dst.stat().st_size > 10_000:
        return dst
    tmp = dst.with_suffix(".part")
    try:
        with httpx.stream("GET", clip["url"], timeout=timeout, follow_redirects=True) as r:
            r.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in r.iter_bytes(1 << 16):
                    f.write(chunk)
                    if f.tell() > 200 * 1024 * 1024:
                        raise ProviderError("stock clip larger than 200 MB")
    except httpx.HTTPError as e:
        tmp.unlink(missing_ok=True)
        raise ProviderError(f"stock clip download failed: {e}") from e
    tmp.replace(dst)
    return dst
