"""Real-picture layer (owner, 2026-11-19: "more real pictures, animation, motion graphics etc and less ai").
Finishes the licensed / public-domain photos in assets/real/raw/ for Dragon Psychology: black and white on the channel's
slate-to-lab-paper ramp (or cobalt duotone), grain added later by the page. Credits: data/photo_credits.json.
Run with `python3 -I real.py` (the raws are downloaded files)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

D = Path(__file__).resolve().parent
RAW, OUT = D / "assets" / "real" / "raw", D / "assets" / "real"
SL, PAPER, CO = (20, 24, 36), (240, 244, 248), (43, 108, 176)


def ramp(stops):
    """256-entry RGB lookup through the given (position, colour) stops."""
    lut = []
    for i in range(256):
        t = i / 255
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = (t - p0) / (p1 - p0 or 1)
                lut.append(tuple(round(c0[j] + (c1[j] - c0[j]) * k) for j in range(3)))
                break
    return lut


BW = ramp([(0, SL), (1, PAPER)])
DUO = ramp([(0, SL), (.55, CO), (1, PAPER)])


def finish(name, mode="bw", contrast=1.0, crop=None, max_w=2400, out=None, gamma=1.0):
    src = next(RAW.glob(name + ".*"))
    im = Image.open(src).convert("RGB")
    if crop:  # crop as fractions (l, t, r, b)
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    if contrast != 1.0:
        g = g.point(lambda v: max(0, min(255, round((v - 128) * contrast + 128))))
    if gamma != 1.0:
        g = g.point(lambda v: round(255 * (v / 255) ** gamma))
    lut = BW if mode == "bw" else DUO
    rgb = Image.merge("RGB", [g.point([c[j] for c in lut]) for j in range(3)])
    rgb.save(OUT / f"{out or name}.jpg", quality=90)
    return rgb


def disc(name, out):
    """A round cut-out (the penny) on transparency, black and white."""
    im = finish(name, "bw", 1.1, out=out + "_sq")
    s = min(im.size); im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse((s * .035, s * .035, s * .965, s * .965), fill=255)
    im = im.convert("RGBA"); im.putalpha(m.filter(ImageFilter.GaussianBlur(1)))
    im.save(OUT / f"{out}.png"); (OUT / f"{out}_sq.jpg").unlink()


if __name__ == "__main__":
    finish("himes_chart_1843", "bw", 1.1, out="millerite_chart")
    finish("himes_chart_1843", "bw", 1.15, crop=(.6, .0, 1.0, .27), out="millerite_detail")
    finish("phone_model500", "duo", 1.1)
    finish("phone_bakelite", "bw", 1.05)
    finish("archive_boxes", "bw", 1.05)
    finish("archive_shelf", "bw", 1.0)
    finish("books_stack", "bw", 1.05)
    finish("books_two", "bw", 1.0)
    finish("pegboard", "bw", 1.15)
    finish("gauge", "bw", 1.1)
    finish("padlock", "bw", 1.05)
    finish("night_house", "duo", 1.2, gamma=1.9)
    finish("bentley", "bw", 1.05, crop=(.36, .12, 1.0, .97), gamma=.7)
    disc("penny", "penny")
    print("ok")
