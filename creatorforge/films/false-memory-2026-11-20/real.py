"""Real-picture layer for "Can I Give You a False Memory in 60 Seconds?" (real first, MASTER_DIRECTIVES 8c).
Finishes the licensed / public-domain photos in assets/real/raw/ for Dragon Psychology: black and white on the channel's
slate-to-lab-paper ramp, or cobalt duotone. Grain and halftone are added by the page. Credits: data/photo_credits.json.
Run with `python3 -I real.py` (the raws are downloaded files)."""
from pathlib import Path
from PIL import Image, ImageOps

D = Path(__file__).resolve().parent
RAW, OUT = D / "assets" / "real" / "raw", D / "assets" / "real"
SL, PAPER, CO = (20, 24, 36), (240, 244, 248), (43, 108, 176)


def ramp(stops):
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


def finish(name, mode="bw", contrast=1.0, crop=None, out=None, gamma=1.0, min_w=1920):
    src = next(RAW.glob(name + ".*"))
    im = Image.open(src).convert("RGB")
    if crop:  # fractions (l, t, r, b)
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    if im.width < min_w:  # small web sizes: one clean upscale here, so the page never stretches a JPEG
        im = im.resize((min_w, round(im.height * min_w / im.width)), Image.LANCZOS)
    g = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    if contrast != 1.0:
        g = g.point(lambda v: max(0, min(255, round((v - 128) * contrast + 128))))
    if gamma != 1.0:
        g = g.point(lambda v: round(255 * (v / 255) ** gamma))
    lut = BW if mode == "bw" else DUO
    Image.merge("RGB", [g.point([c[j] for c in lut]) for j in range(3)]).save(OUT / f"{out or name}.jpg", quality=90)


if __name__ == "__main__":
    finish("courthouse_front", "duo", 1.12)
    finish("courthouse_side", "bw", 1.1)
    finish("lecture_hall", "bw", 1.08)
    finish("mall", "bw", 1.1)
    finish("balloon_big", "bw", 1.08)
    finish("balloon_fog", "duo", 1.0)
    finish("thompson_cotton", "bw", 1.05, crop=(.13, .0, .92, 1.0), min_w=1600)
    finish("challenger_launch", "bw", 1.05)
    print("ok")
