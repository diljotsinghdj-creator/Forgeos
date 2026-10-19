"""A real picture of something the narration names - a person, party, institution, company or landmark - found by
name on Wikipedia, the way a news explainer cuts to the party symbol or the politician when they are mentioned.

resolve("BJP", context="India") -> {"title": "Bharatiya Janata Party", ...}
pictures("Bharatiya Janata Party") -> the article's lead image (its symbol/logo), then free photos from Commons.

Only openly licensed files are used, except logos/symbols/flags/emblems, which are shown to identify who is being
discussed (credited, like a news broadcast does). A name that doesn't clearly resolve to one page about it - a
different person with the same first name, a disambiguation page - gets nothing, and the line keeps its picture."""
from __future__ import annotations

import html
import re

import httpx

from .base import ProviderError
from .stock_video import UA

WP = "https://en.wikipedia.org/w/api.php"
_FREE = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by(-sa)?( \d\.\d)?|cc-by(-sa)?(-\d\.\d)?|no restrictions|gfdl|"
                   r"attribution|gódl|godl)", re.I)
_LOGO = re.compile(r"logo|symbol|flag|emblem|seal|wordmark|insignia|coat of arms|election[_ ]symbol", re.I)
_SMALL = {"of", "the", "and", "for", "in", "on", "at", "a", "an", "to", "de", "&"}


def _get(params: dict, timeout: float = 20) -> dict:
    try:
        r = httpx.get(WP, timeout=timeout, headers={"User-Agent": UA}, params={"format": "json", **params})
        r.raise_for_status()
        return r.json()
    except (httpx.HTTPError, ValueError) as e:
        raise ProviderError(f"wikipedia lookup failed: {e}") from e


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def _initials(title: str) -> str:
    return "".join(w[0] for w in re.findall(r"[A-Za-z][\w'-]*", re.sub(r"\(.*?\)", "", title))
                   if w.lower() not in _SMALL).upper()


def names_match(name: str, title: str) -> bool:
    """Is this Wikipedia page about the name? "BJP" ~ "Bharatiya Janata Party", "Modi" ~ "Narendra Modi",
    "Supreme Court" ~ "Supreme Court of India"; "Leah" !~ "Leah Williamson" is still a match by name, which is why
    single words also need the topic check in resolve()."""
    t = title.lower()
    if re.fullmatch(r"[A-Z0-9-]{2,7}", name):
        # an acronym is the page whose initials it is ("ED" = Enforcement Directorate), or a page titled with that
        # exact acronym - never a person who merely has the same letters as a name ("ED" is not Ed Sheeran)
        if name in re.findall(r"\b[A-Z0-9-]{2,7}\b", title):
            return True
        if title.split()[0].strip(".,").lower() == name.lower():
            return False                      # "Ed Davey", "Sir Elton...": a word that only looks like the acronym
        ini, n = _initials(title), name.replace("-", "")
        return ini == n or (len(n) >= 3 and ini.endswith(n))   # "U.S. Securities and Exchange Commission" = SEC
    words = [w for w in re.findall(r"[a-z0-9']+", name.lower()) if w not in _SMALL]
    return bool(words) and all(re.search(rf"\b{re.escape(w)}", t) for w in words)


_NATIONS = {"india": ("india", "indian"), "united states": ("united states", "u.s.", "american", "america"),
            "united kingdom": ("united kingdom", "british", "britain", "england", "english", "uk"),
            "pakistan": ("pakistan",), "bangladesh": ("bangladesh",), "china": ("china", "chinese"),
            "canada": ("canada", "canadian"), "australia": ("australia", "australian"), "france": ("france", "french"),
            "germany": ("germany", "german"), "japan": ("japan", "japanese"), "russia": ("russia", "russian"),
            "ireland": ("ireland", "irish"), "nigeria": ("nigeria",), "south africa": ("south africa",),
            "brazil": ("brazil",), "israel": ("israel",), "turkey": ("turkey", "turkish"), "hungary": ("hungary",)}
_ALIAS = {"britain": "united kingdom", "england": "united kingdom", "scotland": "united kingdom", "wales": "united kingdom",
          "america": "united states"}


def other_country(text: str, context: str) -> bool:
    """True when the text is about a different country than the story's ("of the United States" vs India)."""
    t = f" {text.lower()} "
    home = _ALIAS.get(context.lower(), context.lower())
    if any(re.search(rf"\b{re.escape(w)}\b", t) for w in _NATIONS.get(home, (home,))):
        return False
    return any(re.search(rf"\b{re.escape(w)}\b", t) for k, ws in _NATIONS.items() if k != home for w in ws)


# Acronyms in Indian news: the institution they stand for, or None for words that are not a picturable subject.
ACRONYMS = {"ED": "Enforcement Directorate", "CBI": "Central Bureau of Investigation", "NIA": "National Investigation Agency",
            "ECI": "Election Commission of India", "EC": "Election Commission of India", "SC": "Supreme Court of India",
            "RBI": "Reserve Bank of India", "CAG": "Comptroller and Auditor General of India",
            "EVM": "Electronic voting machine", "UN": "United Nations", "RSS": "Rashtriya Swayamsevak Sangh",
            "NEET": "National Eligibility cum Entrance Test (Undergraduate)", "PMLA": "Prevention of Money Laundering Act, 2002",
            "SIR": None, "PM": None, "CM": None, "MP": None, "MPS": None, "MLA": None, "MLAS": None, "GDP": None,
            "CEO": None, "IT": None, "OK": None, "TV": None, "US": None, "UK": None, "CCTV": None, "FIR": None,
            "SG": None, "CJI": None, "HC": None}


def resolve(name: str, context: str = "", topic: list[str] | None = None) -> dict | None:
    """The one Wikipedia page the name refers to here, or None when unsure."""
    key = name.strip().upper()
    if re.fullmatch(r"[A-Z0-9-]{2,7}", name.strip()) and key in ACRONYMS:
        if ACRONYMS[key] is None:
            return None                       # "SIR", "PM", "MP": not a subject to look up
        name = ACRONYMS[key]                  # search the institution's full name
    topic = [w.lower() for w in (topic or []) if w]
    single = len(name.split()) == 1
    # "Supreme Court" in a story about India is the Supreme Court of India: search with the country first
    queries = ([f"{name} {context}"] if context else []) + [name]
    for q in queries:
        hits = (_get({"action": "query", "list": "search", "srsearch": q, "srlimit": 5, "srnamespace": 0})
                .get("query") or {}).get("search") or []
        for h in hits:
            title = h.get("title", "")
            if not names_match(name, title):
                continue
            page = next(iter(((_get({"action": "query", "titles": title, "redirects": 1,
                                     "prop": "pageimages|description|pageprops", "piprop": "name",
                                     "ppprop": "disambiguation"}).get("query") or {}).get("pages") or {}).values()), {})
            if "disambiguation" in (page.get("pageprops") or {}):
                continue
            desc = str(page.get("description") or "")
            about = f"{title} {desc} {_plain(h.get('snippet', ''))}".lower()
            if context and other_country(f"{title} {desc}", context):
                continue                          # the US Supreme Court, in a story about India
            if single and not re.fullmatch(r"[A-Z0-9-]{2,7}", name):
                # a lone first/last name must be the one this script is about ("Modi" - Prime Minister of India),
                # not someone else who shares it
                if not any(w in about for w in topic + ([context.lower()] if context else [])):
                    continue
            return {"title": page.get("title") or title, "description": desc, "image": page.get("pageimage") or ""}
    return None


def file_info(filename: str, width: int = 1600) -> dict | None:
    """URL and licence of a file (Commons or local). None when it can't be shown: non-free and not a logo."""
    pages = (_get({"action": "query", "titles": f"File:{filename}", "prop": "imageinfo",
                   "iiprop": "url|extmetadata|mime|size", "iiurlwidth": width}).get("query") or {}).get("pages") or {}
    info = (next(iter(pages.values()), {}).get("imageinfo") or [{}])[0]
    if not info.get("url"):
        return None
    meta = info.get("extmetadata") or {}
    licence = _plain((meta.get("LicenseShortName") or {}).get("value", "")) or "unknown licence"
    nonfree = str((meta.get("NonFree") or {}).get("value", "")).lower() in ("true", "1")
    logo = bool(_LOGO.search(filename)) or info.get("mime") == "image/svg+xml"
    if (nonfree or not _FREE.match(licence)) and not logo:
        return None
    artist = _plain((meta.get("Artist") or {}).get("value", ""))[:60] or "Wikimedia"
    credit = f"{artist} / Wikimedia ({licence})" if not logo else f"{filename.rsplit('.', 1)[0]} (identification)"
    return {"url": info.get("thumburl") or info["url"], "credit": credit, "logo": logo,
            "width": int(info.get("thumbwidth") or info.get("width") or 0)}


def pictures(page: dict, more: bool = True) -> list[dict]:
    """The page's lead image first (a party's symbol, a politician's portrait, a building), then a few more openly
    licensed photos of the same subject from Commons, so repeated mentions don't repeat one picture."""
    out = []
    if page.get("image"):
        lead = file_info(page["image"])
        if lead:
            out.append(lead)
    if more:
        from . import archive_photo
        try:
            for p in archive_photo.search(page["title"], limit=8)[:5]:
                if names_match(page["title"].split(" (")[0], p.get("title", "")) or page["title"].lower() in p.get("title", "").lower():
                    out.append({"url": p["url"], "credit": p["credit"], "logo": False, "width": p.get("width", 0)})
        except ProviderError:
            pass
    return out


def fetch_framed(pic: dict, cache, size: tuple[int, int], timeout: float = 60):
    """Downloads the picture and frames it for the video: a logo or symbol centred on a plain paper card, a photo
    whole over a blurred, darkened copy of itself (so a portrait photo in a 16:9 frame isn't cropped to a chin)."""
    import hashlib
    import io
    from pathlib import Path

    from PIL import Image, ImageFilter, ImageEnhance
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    w, h = size
    dst = cache / f"{hashlib.sha256((pic['url'] + f'{w}x{h}').encode()).hexdigest()[:24]}.jpg"
    if dst.is_file() and dst.stat().st_size > 5_000:
        return dst
    try:
        r = httpx.get(pic["url"], timeout=timeout, follow_redirects=True, headers={"User-Agent": UA})
        r.raise_for_status()
        if len(r.content) > 40 * 1024 * 1024:
            raise ProviderError("picture larger than 40 MB")
        src = Image.open(io.BytesIO(r.content))
        src.load()
    except (httpx.HTTPError, OSError) as e:
        raise ProviderError(f"picture download failed: {e}") from e
    if pic.get("logo") or src.mode in ("RGBA", "LA", "P"):
        rgba = src.convert("RGBA")
        card = Image.new("RGB", (w, h), (242, 236, 223))
        scale = min(w * 0.6 / rgba.width, h * 0.6 / rgba.height)
        mark = rgba.resize((max(1, int(rgba.width * scale)), max(1, int(rgba.height * scale))), Image.LANCZOS)
        card.paste(mark, ((w - mark.width) // 2, (h - mark.height) // 2), mark)
        out = card
    else:
        photo = src.convert("RGB")
        cover = max(w / photo.width, h / photo.height)
        bg = photo.resize((int(photo.width * cover) + 1, int(photo.height * cover) + 1), Image.LANCZOS)
        bg = bg.crop(((bg.width - w) // 2, (bg.height - h) // 2, (bg.width - w) // 2 + w, (bg.height - h) // 2 + h))
        bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(max(8, w // 60)))).enhance(0.45)
        fit = min(w * 0.94 / photo.width, h * 0.94 / photo.height)
        fg = photo.resize((max(1, int(photo.width * fit)), max(1, int(photo.height * fit))), Image.LANCZOS)
        if fg.width >= w * 0.9 and fg.height >= h * 0.9:
            out = photo.resize((int(photo.width * cover) + 1, int(photo.height * cover) + 1), Image.LANCZOS)
            out = out.crop(((out.width - w) // 2, (out.height - h) // 2, (out.width - w) // 2 + w, (out.height - h) // 2 + h))
        else:
            bg.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
            out = bg
    tmp = dst.with_suffix(".part.jpg")
    out.save(tmp, "JPEG", quality=92)
    tmp.replace(dst)
    return dst
