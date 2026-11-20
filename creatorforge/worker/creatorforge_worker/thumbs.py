"""9:16 "face-off" thumbnails: real, openly licensed photos of the people on one side, the map of India with the other
side on the other, big Hinglish words, and the photo credits printed small along the bottom.

Photos come from Wikipedia/Wikimedia Commons (the page's lead portrait first; only free licences), cut out of their
background when the cut-out model is on the pod, else framed in a circle. Never AI-made faces. Run on the pod:

  python -m creatorforge_worker.thumbs --left "Narendra Modi" "Amit Shah" "Gyanesh Kumar" --right "Rahul Gandhi" \
      --top "CHUNAV AYOG KA SACH" --headline "Chunav Ayukt Kaun Chunta Hai?" --bottom "CJI BAHAR! 2 vs 1"

The finished PNG is added to the Asset Library (app: Library -> Assets -> image) and its credits are printed."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

W, H = 1080, 1920
RED, YELLOW, WHITE, NAVY = (210, 20, 30), (255, 214, 0), (255, 255, 255), (12, 18, 44)
SAFFRON, GREEN = (255, 153, 51), (19, 136, 8)


def photo(name: str, cache: Path) -> tuple[object, str]:
    """(PIL image, credit) for the person's freely licensed Wikipedia portrait, or (None, "") when there is none."""
    import httpx
    from PIL import Image

    from .providers import wiki_image
    page = wiki_image.resolve(name, "India", ["politics", "election", "minister", "commissioner", "congress", "bjp",
                                              "lok sabha", "government"])
    if not page:
        return None, ""
    for pic in wiki_image.pictures(page, more=True)[:4]:
        if pic.get("logo"):
            continue
        try:
            r = httpx.get(pic["url"], timeout=60, follow_redirects=True, headers={"User-Agent": wiki_image.UA})
            r.raise_for_status()
            im = Image.open(io.BytesIO(r.content))
            im.load()
        except Exception:  # noqa: BLE001 - try the next photo
            continue
        if min(im.size) < 300:
            continue
        cache.mkdir(parents=True, exist_ok=True)
        src = cache / f"{name.replace(' ', '_')}.jpg"
        im.convert("RGB").save(src, quality=95)
        return im.convert("RGB"), f"{name}: {pic['credit']}"
    return None, ""


def _cut(im, cache: Path, data_dir: Path):
    """The person without the background (RGBA), or None when the cut-out model isn't on this machine."""
    from .media import layout
    model = data_dir / "models" / "isnet-general-use.onnx"
    if not model.is_file():
        return None
    import hashlib
    cache.mkdir(parents=True, exist_ok=True)
    src = cache / f"src_{hashlib.sha256(im.tobytes()).hexdigest()[:16]}.png"
    im.save(src)
    cut = layout.cutout(src, cache, model)
    if cut is None:
        return None
    from PIL import Image
    with Image.open(cut) as c:
        return c.convert("RGBA")


def _portrait(im, size: int, cut=None):
    """Head-and-shoulders in a size x size tile with a round mask (or the cut-out standing on the tile's bottom)."""
    from PIL import Image, ImageDraw
    if cut is not None:
        w, h = cut.size
        cut = cut.crop((0, 0, w, min(h, int(w * 1.15))))           # head and shoulders
        scale = size * 0.98 / cut.width
        cut = cut.resize((int(cut.width * scale), int(cut.height * scale)), Image.LANCZOS)
        tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        tile.alpha_composite(cut, ((size - cut.width) // 2, max(0, size - cut.height)))
        return tile
    w, h = im.size
    side = min(w, h)
    top = int(h * 0.04) if h > w else 0                        # portraits: keep the head, not the chin, in frame
    sq = im.crop(((w - side) // 2, top, (w - side) // 2 + side, top + side)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile.paste(sq, (0, 0), mask)
    return tile


def india_map(width: int, height: int):
    """India (official boundary) filled in the tricolour, white outline, on a transparent card."""
    from PIL import Image, ImageDraw

    from .media import maps
    rings = maps._find("India")["rings"]
    pts = [p for r in rings for p in r]
    lons, lats = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1 = min(lons), max(lons)
    y0, y1 = maps._merc(0, min(lats))[1], maps._merc(0, max(lats))[1]
    xs0, xs1 = maps._merc(x0, 0)[0], maps._merc(x1, 0)[0]
    k = min((width - 20) / (xs1 - xs0), (height - 20) / (y1 - y0))
    ox = (width - (xs1 - xs0) * k) / 2
    oy = (height - (y1 - y0) * k) / 2

    def xy(lon, lat):
        mx, my = maps._merc(lon, lat)
        return ox + (mx - xs0) * k, height - (oy + (my - y0) * k)
    mask = Image.new("L", (width, height), 0)
    for r in rings:
        ImageDraw.Draw(mask).polygon([xy(*p) for p in r], fill=255)
    flag = Image.new("RGBA", (width, height))
    d = ImageDraw.Draw(flag)
    for y in range(height):
        d.line([(0, y), (width, y)], fill=SAFFRON if y < height / 3 else WHITE if y < 2 * height / 3 else GREEN)
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    glow.putalpha(mask.point(lambda v: 90 if v else 0))
    from PIL import ImageFilter
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
    out.paste(flag, (0, 0), mask)
    edge = ImageDraw.Draw(out)
    for r in rings:
        edge.line([xy(*p) for p in r] + [xy(*r[0])], fill=WHITE, width=5, joint="curve")
    return out


def face_off(left: list[str], right: list[str], top: str, headline: str, bottom: str, left_label: str,
             right_label: str, out: Path, data_dir: Path) -> list[str]:
    """Draws the thumbnail to `out`; returns the photo credits (to print and paste in the description)."""
    from PIL import Image, ImageDraw, ImageFilter

    from .media.globe import font_file
    cache = data_dir / "cache" / "thumbs"
    latin = font_file("latin")

    def font(size):
        from PIL import ImageFont
        try:
            return ImageFont.truetype(latin, size)
        except OSError:
            return ImageFont.load_default()

    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(NAVY[0] * (1 - t)), int(NAVY[1] * (1 - t)), int(NAVY[2] * (1 - t) + 6)))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((300, 700, 780, 1300), fill=170)
    img.paste((150, 10, 20), mask=glow.filter(ImageFilter.GaussianBlur(150)))
    d = ImageDraw.Draw(img)

    def text(cx, y, s, size, fill, stroke=0, sfill=(0, 0, 0), maxw=W - 60):
        f = font(size)
        while d.textlength(s, font=f) > maxw and size > 20:
            size -= 4
            f = font(size)
        d.text((cx - d.textlength(s, font=f) / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

    d.rectangle((0, 110, W, 230), fill=RED)
    text(W / 2, 128, top.upper(), 78, WHITE)
    words = headline.split()
    half = (len(words) + 1) // 2
    text(W / 2, 265, " ".join(words[:half]), 104, WHITE, 6)
    text(W / 2, 390, " ".join(words[half:]), 104, YELLOW, 6)

    credits = []
    # left: the people on one side, stacked, each with a name tag
    col_x, tile = 40, 260
    text(col_x + 225, 535, left_label.upper(), 54, SAFFRON, 3)
    for i, name in enumerate(left[:3]):
        im, credit = photo(name, cache)
        y = 620 + i * 320
        ImageDraw.Draw(img).ellipse((col_x + 95 - 8, y - 8, col_x + 95 + tile + 8, y + tile + 8), fill=SAFFRON)
        if im is not None:
            credits.append(credit)
            p = _portrait(im, tile, _cut(im, cache, data_dir))
            ring = Image.new("RGBA", (tile, tile), (30, 34, 60, 255))
            m = Image.new("L", (tile, tile), 0)
            ImageDraw.Draw(m).ellipse((0, 0, tile - 1, tile - 1), fill=255)
            img.paste(ring, (col_x + 95, y), m)
            img.alpha_composite(p, (col_x + 95, y))
        d = ImageDraw.Draw(img)
        label = name.upper().replace("NARENDRA ", "PM ")
        d.rounded_rectangle((col_x + 20, y + tile - 26, col_x + 430, y + tile + 30), 14, fill=(0, 0, 0))
        text(col_x + 225, y + tile - 22, label, 40, WHITE, maxw=390)

    # right: India, the other side standing in it
    mp = india_map(520, 820)
    img.alpha_composite(mp, (W - 540, 600))
    d = ImageDraw.Draw(img)
    text(W - 270, 535, right_label.upper(), 54, (120, 200, 255), 3)
    for i, name in enumerate(right[:2]):
        im, credit = photo(name, cache)
        size = 250 if len(right) == 1 else 200
        x, y = W - 280 - size // 2 + (0 if len(right) == 1 else (-105 + 210 * i)), 880 + (0 if len(right) == 1 else 70 * i)
        ImageDraw.Draw(img).ellipse((x - 8, y - 8, x + size + 8, y + size + 8), fill=(120, 200, 255))
        if im is not None:
            credits.append(credit)
            p = _portrait(im, size, _cut(im, cache, data_dir))
            m = Image.new("L", (size, size), 0)
            ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
            img.paste(Image.new("RGBA", (size, size), (30, 34, 60, 255)), (x, y), m)
            img.alpha_composite(p, (x, y))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x + size // 2 - 200, y + size - 30, x + size // 2 + 200, y + size + 32), 14, fill=(0, 0, 0))
        text(x + size // 2, y + size - 26, name.upper(), 44, WHITE, maxw=380)
    text(W - 280, 1450, "+ OPPOSITION", 46, WHITE, 3)

    # VS in the middle
    d.ellipse((W / 2 - 85, 905, W / 2 + 85, 1075), fill=RED, outline=WHITE, width=6)
    text(W / 2, 935, "VS", 96, WHITE)

    d.rounded_rectangle((60, 1600, W - 60, 1760), 30, fill=YELLOW)
    text(W / 2, 1618, bottom.upper(), 110, (20, 20, 20), maxw=W - 160)
    note = "Photos: Wikimedia Commons (see description) · Map: official boundary, not to scale"
    text(W / 2, 1800, "PRINT FACTS", 54, (200, 200, 210))
    text(W / 2, 1872, note, 22, (150, 150, 165))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out)
    return credits


def main(argv: list[str] | None = None) -> None:
    from .config import Config
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--left", nargs="+", required=True)
    ap.add_argument("--right", nargs="+", required=True)
    ap.add_argument("--top", default="CHUNAV AYOG KA SACH")
    ap.add_argument("--headline", default="Chunav Ayukt Kaun Chunta Hai?")
    ap.add_argument("--bottom", default="CJI BAHAR! 2 vs 1")
    ap.add_argument("--left-label", default="SARKAR + CEC")
    ap.add_argument("--right-label", default="VIPAKSH")
    ap.add_argument("--name", default="Thumbnail 9x16")
    a = ap.parse_args(argv)
    cfg = Config.from_env()
    out = cfg.data_dir / "cache" / "thumbs" / "thumbnail.png"
    credits = face_off(a.left, a.right, a.top, a.headline, a.bottom, a.left_label, a.right_label, out, cfg.data_dir)
    from .library import Library
    from .media import verify
    tmp = out.with_name("thumbnail.upload.png")
    tmp.write_bytes(out.read_bytes())
    asset = Library(cfg.data_dir / "library", cfg.allow_mock).assets.add("image", a.name, tmp, ".png", verify.image)
    print(json.dumps({"asset": asset["id"], "file": str(out), "credits": credits}, ensure_ascii=False, indent=1))
    print("\nIn the app: Library -> Assets -> image -> '" + a.name + "'. Paste the credits into the description.")


if __name__ == "__main__":
    main()
