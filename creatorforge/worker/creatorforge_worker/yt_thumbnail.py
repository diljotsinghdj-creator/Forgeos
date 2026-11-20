"""YouTube thumbnails (1280x720 JPEG) for a long video: a real, credited photo of the person the video is about
(from Wikipedia/Commons, never AI-generated), a big claim or number, and a question. Three layouts to A/B test.
Each goes into the Asset Library (kind image) so the app can save it to the phone.

    python -m creatorforge_worker.yt_thumbnail --person "Gyanesh Kumar" --tag "ज्ञानेश कुमार" \
        --big "13.3 करोड़" --mid "नाम कटे" --question "BJP के लिए इतने ज़रूरी क्यों?" --name "Gyanesh thumbnail"

Text should be a sourced number or a question - never a crime stated as fact."""
from __future__ import annotations

import argparse
import io
from pathlib import Path

W, H = 1280, 720
YELLOW, WHITE, RED, INK = (255, 212, 0), (255, 255, 255), (214, 31, 38), (12, 13, 18)


def person_photo(name: str):
    """(PIL image, credit) for the person's Wikipedia lead photo or the first openly licensed Commons photo."""
    import httpx
    from PIL import Image

    from .providers import wiki_image
    page = wiki_image.resolve(name, "", [], "")
    pics = [p for p in (wiki_image.pictures(page) if page else wiki_image.search_by_name(name)) if not p.get("logo")]
    for pic in pics:
        try:
            r = httpx.get(pic["url"], timeout=60, follow_redirects=True, headers={"User-Agent": wiki_image.UA})
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            img.load()
        except Exception:  # noqa: BLE001 - try the next photo
            continue
        if min(img.size) >= 300:
            return img.convert("RGB"), pic["credit"]
    raise SystemExit(f"no usable openly licensed photo of {name} found on Wikipedia/Commons")


def _font(size: int, text: str):
    from PIL import ImageFont

    from .media.globe import font_file, script_of
    path = font_file(script_of(text)) or font_file("deva")
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()


def _fit(draw, text: str, size: int, max_w: int):
    """The biggest font (down from `size`) at which `text` fits in `max_w` pixels."""
    while size > 18:
        f = _font(size, text)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return _font(size, text)


def _photo_panel(photo, w: int, h: int):
    """The photo cropped to w x h, keeping the top (the face) of a portrait, fading into the background on the left."""
    from PIL import Image, ImageEnhance
    s = max(w / photo.width, h / photo.height)
    p = photo.resize((max(w, round(photo.width * s)), max(h, round(photo.height * s))), Image.LANCZOS)
    x0 = (p.width - w) // 2
    y0 = min((p.height - h) // 2, round(p.height * 0.06))       # portraits: keep the head in frame
    p = p.crop((x0, y0, x0 + w, y0 + h))
    p = ImageEnhance.Contrast(ImageEnhance.Color(p).enhance(0.85)).enhance(1.12)
    mask = Image.new("L", (w, h), 255)
    fade = round(w * 0.38)
    for x in range(fade):
        mask.paste(round(255 * (x / fade) ** 1.6), (x, 0, x + 1, h))
    return p, mask


def render(photo, credit: str, tag: str, big: str, mid: str, question: str, layout: str = "A"):
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new("RGB", (W, H), INK)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-300, 120, 600, 900), fill=(90, 8, 12))
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(160)), 0.7)

    pw = 640 if layout != "C" else 560
    panel, mask = _photo_panel(photo, pw, H)
    img.paste(panel, (W - pw, 0), mask)
    d = ImageDraw.Draw(img)
    left = 52
    text_w = W - pw - left + 150                  # text may run a little over the faded photo edge

    # tag: who it is about, a red label
    tf = _font(40, tag)
    tw = d.textlength(tag, font=tf)
    d.rectangle((left - 14, 44, left + tw + 14, 104), fill=RED)
    d.text((left, 74), tag, font=tf, fill=WHITE, anchor="lm")

    y = 132
    for text, colour, size in ((big, YELLOW, 168), (mid, WHITE, 118)):
        if not text:
            continue
        f = _fit(d, text, size, text_w)
        d.text((left, y), text, font=f, fill=colour, stroke_width=4, stroke_fill=(0, 0, 0))
        top, bottom = d.textbbox((left, y), text, font=f, stroke_width=4)[1::2]
        y = bottom + 18

    # the question on a white band at the bottom
    qf = _fit(d, question, 60, W - 2 * left - 20)
    qh = d.textbbox((0, 0), question, font=qf)[3] + 34
    band_top = H - qh - 40
    d.rectangle((left - 14, band_top, left + d.textlength(question, font=qf) + 22, band_top + qh), fill=WHITE)
    d.text((left + 4, band_top + qh // 2), question, font=qf, fill=INK, anchor="lm")

    # photo credit, small, on the photo (the licence requires it)
    cf = _font(15, credit)
    cred = "Photo: " + credit[:90]
    d.text((W - 12, H - 10), cred, font=cf, fill=(200, 200, 200), anchor="rs", stroke_width=2, stroke_fill=(0, 0, 0))
    return img


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--person", required=True, help="the person's name as on Wikipedia (their photo is used)")
    ap.add_argument("--tag", default="", help="small red label (default: the person's name)")
    ap.add_argument("--big", required=True, help="the big yellow words (a sourced number works best)")
    ap.add_argument("--mid", default="", help="the white words under it")
    ap.add_argument("--question", required=True, help="the question on the white band")
    ap.add_argument("--alt", action="append", default=[],
                    help="another layout: 'big|mid|question' (repeatable); each becomes its own thumbnail")
    ap.add_argument("--photo", help="use this photo file instead of looking it up (you must have the right to use it)")
    ap.add_argument("--credit", default="", help="credit line for --photo")
    ap.add_argument("--out", default="thumbnails", help="folder for the JPEGs")
    ap.add_argument("--name", default="", help="Asset Library name (default: '<person> thumbnail')")
    ap.add_argument("--no-library", action="store_true")
    a = ap.parse_args(argv)

    from PIL import Image, features
    if not features.check("raqm"):
        print("warning: Pillow has no complex text layout (raqm): Hindi letters may not join up correctly")
    if a.photo:
        photo, credit = Image.open(a.photo).convert("RGB"), a.credit or "own photo"
    else:
        photo, credit = person_photo(a.person)
    print("photo credit:", credit)
    variants = [(a.big, a.mid, a.question)] + [tuple((v.split("|") + ["", ""])[:3]) for v in a.alt]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lib = None
    if not a.no_library:
        from .api import _check_asset
        from .config import Config
        from .library import Library
        cfg = Config.from_env()
        lib = Library(cfg.data_dir / "library", cfg.allow_mock)
    for k, (big, mid, q) in enumerate(variants):
        layout = "ABC"[k % 3]
        img = render(photo, credit, a.tag or a.person, big, mid, q or a.question, layout)
        f = out / f"thumbnail_{layout}{'' if k < 3 else k}.jpg"
        img.save(f, "JPEG", quality=92, optimize=True)
        print(f"{f}  ({f.stat().st_size // 1024} KB)  {big} / {mid} / {q or a.question}")
        if lib is not None:
            tmp = f.with_suffix(".upload.jpg")
            tmp.write_bytes(f.read_bytes())
            name = f"{a.name or a.person + ' thumbnail'} {layout}"
            asset = lib.assets.add("image", name, tmp, ".jpg", lambda p: _check_asset("image", p))
            print(f"   In the app: Library -> Assets -> Image -> '{name}' (asset {asset['id']})")
    print("Credit to add to the YouTube description:", "Photo: " + credit)


if __name__ == "__main__":
    main()
