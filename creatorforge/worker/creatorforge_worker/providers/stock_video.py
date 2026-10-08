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

FREE_SOURCES = ("nasa", "wikimedia")
UA = "CreatorForge/1.0 (video worker; https://github.com/diljotsinghdj-creator/Forgeos)"
_STOP = {"the", "and", "with", "from", "into", "over", "for", "of", "a", "an", "in", "on", "at", "to", "by"}
# Free licences that allow commercial use and editing (credit goes in the publish kit).
_FREE_LICENCE = re.compile(r"public domain|\bpd\b|cc0|cc[ -]by(?![ -]?n[cd])(?:[ -]sa)?(?![ -]?n[cd])", re.I)


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


def _wikimedia(query: str, timeout: float) -> list[dict]:
    r = httpx.get("https://commons.wikimedia.org/w/api.php", timeout=timeout, headers={"User-Agent": UA}, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:video {query}",
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
        if int(info.get("height") or 0) < 480 or float(info.get("duration") or 0) < 2:
            continue
        # A transcoded copy near 1080p downloads far faster than the original master.
        ders = [d for d in info.get("derivatives") or [] if d.get("src") and 480 <= int(d.get("height") or 0) <= 1080]
        ders.sort(key=lambda d: -int(d.get("height") or 0))
        src = ders[0] if ders else info
        url = src.get("src") or info.get("url")
        if not url or int(info.get("size") or 0) > 200 * 1024 * 1024 and not ders:
            continue
        artist = val("Artist")[:60] or "unknown author"
        out.append({"url": url, "width": int(src.get("width") or info.get("width") or 0),
                    "height": int(src.get("height") or info.get("height") or 0),
                    "duration": float(info.get("duration") or 0),
                    "credit": f"{artist} / Wikimedia Commons ({licence})", "trim": True})
        if len(out) >= 3:
            break
    return out


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
