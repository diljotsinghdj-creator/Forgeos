"""Real news on screen: the articles a script cites (its Source: links), shown the way news explainers do it -
a screenshot of the actual web page for an Article: line, and the article's own lead photo (its og:image) for lines
about the events it reports. Everything is credited ("Screenshot: Al Jazeera", "Photo via Al Jazeera").

Screenshots need a headless browser (Playwright + Chromium, installed on the pod by setup); without one, Article:
lines fall back to the drawn headline card. Lead photos only need HTTP."""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .base import ProviderError

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
_URL = re.compile(r"https?://[^\s;,)]+")
_STOP = set("the a an of in on at to for and or with from by as is are was were be its it this that after over "
            "into amid says said new news india indian www com html amp story article".split())
MIN_SIDE = 480


def source_links(source: str) -> list[dict]:
    """The script's Source: line as [{"url", "label", "publisher"}] (label = the text before each link)."""
    out, last = [], 0
    for m in _URL.finditer(source or ""):
        url = m.group(0).rstrip(".")
        label = source[last:m.start()].strip(" ;,|")
        last = m.end()
        host = urlparse(url).netloc.lower().removeprefix("www.").removeprefix("m.").removeprefix("amp.")
        out.append({"url": url, "label": label.split(";")[-1].strip(), "host": host,
                    "publisher": (label.split(",")[0].split(";")[-1].strip() or host)})
    return out


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{3,}", text.lower()) if w not in _STOP}


def _slug(url: str) -> str:
    p = urlparse(url)
    return f"{p.path} {p.query}".replace("-", " ").replace("_", " ").replace("/", " ")


def _publisher_hit(publisher: str, link: dict) -> bool:
    pub = re.sub(r"[^a-z]", "", publisher.lower())
    host = re.sub(r"[^a-z]", "", link["host"].split(".")[0])
    lab = re.sub(r"[^a-z]", "", link["publisher"].lower())
    return bool(pub) and (pub[:6] in host or host[:6] in pub or pub[:8] in lab or lab[:8] in pub)


def find_link(text: str, links: list[dict], publisher: str = "", min_overlap: int = 2) -> dict | None:
    """The cited article a headline or line is about: most words shared with the link's slug and label, the named
    publisher first. None when nothing clearly matches - a wrong article is worse than none."""
    want = _words(text)
    best, best_score = None, 0.0
    for link in links:
        have = _words(_slug(link["url"])) | _words(link["label"])
        overlap = len(want & have)
        pub = publisher and _publisher_hit(publisher, link)
        score = overlap + (1.5 if pub else 0)
        if (overlap >= min_overlap or (pub and overlap >= 1)) and score > best_score:
            best, best_score = link, score
    return best


def page_meta(url: str, cache: Path, timeout: float = 20) -> dict:
    """The article's og:image / og:title (cached). {} when the page can't be read."""
    cache.mkdir(parents=True, exist_ok=True)
    meta_file = cache / f"{hashlib.sha256(url.encode()).hexdigest()[:20]}.json"
    if meta_file.is_file():
        try:
            return json.loads(meta_file.read_text())
        except ValueError:
            pass
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": UA, "Accept-Language": "en"})
        r.raise_for_status()
        html = r.text[:600_000]
    except httpx.HTTPError:
        return {}

    def tag(*names: str) -> str:
        for n in names:
            m = (re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(n)}["\'][^>]*content=["\']([^"\']+)', html, re.I)
                 or re.search(rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']{re.escape(n)}["\']', html, re.I))
            if m:
                return m.group(1).replace("&amp;", "&").strip()
        return ""
    meta = {"image": tag("og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"),
            "title": tag("og:title", "twitter:title"), "site": tag("og:site_name")}
    if meta["image"].startswith("//"):
        meta["image"] = "https:" + meta["image"]
    meta_file.write_text(json.dumps(meta))
    return meta


def lead_photo(url: str, cache: Path, timeout: float = 30) -> Path | None:
    """The article's own lead photo, downloaded - only a real photograph big enough for a full frame (no logos,
    no tiny thumbnails, no generic site banners)."""
    meta = page_meta(url, cache / "meta")
    img = meta.get("image") or ""
    if not img or re.search(r"logo|default|placeholder|favicon|sprite|icon|brand", img, re.I):
        return None
    dst = cache / f"{hashlib.sha256(img.encode()).hexdigest()[:24]}.jpg"
    if dst.is_file() and dst.stat().st_size > 10_000:
        return dst
    try:
        from PIL import Image
        r = httpx.get(img, timeout=timeout, follow_redirects=True, headers={"User-Agent": UA, "Referer": url})
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content))
        im.load()
    except (httpx.HTTPError, OSError):
        return None
    if min(im.size) < MIN_SIDE or im.width / max(1, im.height) > 3.2:
        return None                         # a thumbnail or a wide banner, not a photo of the event
    im.convert("RGB").save(dst, "JPEG", quality=92)
    return dst


def screenshot(url: str, cache: Path, width: int = 1280, height: int = 1500, timeout_ms: int = 25_000) -> Path | None:
    """A screenshot of the real article page (top of the page: masthead, headline, lead photo), with cookie and
    subscription pop-ups dismissed where possible. None when no browser is installed or the page won't load."""
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / f"shot_{hashlib.sha256(f'{url}{width}x{height}'.encode()).hexdigest()[:20]}.png"
    if dst.is_file() and dst.stat().st_size > 20_000:
        return dst
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            try:
                page = browser.new_page(viewport={"width": width, "height": height}, user_agent=UA,
                                        device_scale_factor=1.5, locale="en-IN")
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(2500)
                for label in ("Accept", "Accept all", "I agree", "Agree", "Got it", "OK", "Allow", "Continue",
                              "Close", "No thanks", "Not now", "Maybe later"):
                    try:
                        page.get_by_role("button", name=re.compile(rf"^\s*{label}\s*$", re.I)).first.click(timeout=600)
                    except Exception:  # noqa: BLE001 - no such pop-up
                        pass
                page.add_style_tag(content="[class*='cookie'],[id*='cookie'],[class*='consent'],[id*='consent'],"
                                           "[class*='paywall'],[class*='modal'],[class*='popup'],[class*='newsletter']"
                                           "{display:none!important} body{overflow:auto!important}")
                page.wait_for_timeout(500)
                page.screenshot(path=str(dst), full_page=False)
            finally:
                browser.close()
    except Exception:  # noqa: BLE001 - blocked, timed out, no browser binary: fall back to the drawn card
        return None
    return dst if dst.is_file() and dst.stat().st_size > 20_000 else None


def framed(shot: Path, out: Path, w: int, h: int, label: str) -> Path:
    """The screenshot as a finished frame: the page held up over a blurred copy of itself, with a SOURCE tag."""
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
    with Image.open(shot) as im:
        page = im.convert("RGB")
    cover = max(w / page.width, h / page.height)
    bg = page.resize((int(page.width * cover) + 1, int(page.height * cover) + 1), Image.LANCZOS)
    bg = bg.crop(((bg.width - w) // 2, 0, (bg.width - w) // 2 + w, h))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(max(10, w // 50)))).enhance(0.35)
    tall = h > w
    fit = min(w * (0.9 if tall else 0.62) / page.width, h * 0.88 / page.height)
    fg = page.resize((int(page.width * fit), int(page.height * fit)), Image.LANCZOS)
    x, y = (w - fg.width) // 2, int(h * 0.07)
    shadow = Image.new("L", (fg.width + 40, fg.height + 40), 0)
    ImageDraw.Draw(shadow).rectangle((20, 20, fg.width + 20, fg.height + 20), fill=170)
    bg.paste((0, 0, 0), (x - 8, y - 4), shadow.filter(ImageFilter.GaussianBlur(14)))
    bg.paste(fg, (x, y))
    d = ImageDraw.Draw(bg)
    size = max(18, int(min(w, h) * 0.032))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    tag = f"SOURCE: {label.upper()}"[:60]
    tw = d.textlength(tag, font=font)
    tx, ty = w - tw - size * 1.6, y + fg.height + size * 0.8
    if ty + size * 1.8 > h:
        ty = y - size * 2.2 if y > size * 2.4 else h - size * 2
    d.rectangle((tx - size * 0.5, ty - size * 0.35, tx + tw + size * 0.5, ty + size * 1.35), fill=(200, 16, 46))
    d.text((tx, ty), tag, font=font, fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out, "PNG")
    return out


def frame_photo(src: Path, out: Path, w: int, h: int) -> Path:
    """A news photo framed for the video: whole, over a blurred copy of itself (never stretched past 1.5x)."""
    from PIL import Image, ImageEnhance, ImageFilter
    with Image.open(src) as im:
        photo = im.convert("RGB")
    cover = max(w / photo.width, h / photo.height)
    full = photo.resize((int(photo.width * cover) + 1, int(photo.height * cover) + 1), Image.LANCZOS)
    full = full.crop(((full.width - w) // 2, (full.height - h) // 2, (full.width - w) // 2 + w, (full.height - h) // 2 + h))
    fit = min(w * 0.96 / photo.width, h * 0.96 / photo.height, 1.5)
    if photo.width * fit >= w * 0.9 and photo.height * fit >= h * 0.9:
        out_img = full
    else:
        out_img = ImageEnhance.Brightness(full.filter(ImageFilter.GaussianBlur(max(8, w // 60)))).enhance(0.4)
        fg = photo.resize((int(photo.width * fit), int(photo.height * fit)), Image.LANCZOS)
        out_img.paste(fg, ((w - fg.width) // 2, (h - fg.height) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    out_img.save(out, "JPEG", quality=92)
    return out


def still_clip(frame: Path, out: Path, w: int, h: int, seconds: float) -> Path:
    """A slow push-in on a still (the screenshot), as a clip the render cuts in like any other graphic."""
    from ..media import ff
    frames = max(1, int(seconds * 30))
    ff.run(["-loop", "1", "-i", str(frame), "-vf",
            f"scale={w * 2}:{h * 2},zoompan=z='min(1+0.10*on/{frames},1.10)':x='iw/2-(iw/zoom/2)':y='ih*0.1-(ih*0.1/zoom)'"
            f":d={frames}:s={w}x{h}:fps=30,format=yuv420p", "-t", f"{seconds:.2f}", "-r", "30",
            "-c:v", "libx264", "-preset", "veryfast", "-an", str(out)])
    return out


def host_label(link: dict) -> str:
    return link.get("publisher") or link["host"]


def check_photo(path: Path) -> None:
    if not path.is_file():
        raise ProviderError("news photo missing")
