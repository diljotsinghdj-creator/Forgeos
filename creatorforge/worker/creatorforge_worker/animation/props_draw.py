"""How props look: crates, folders that open, bar charts whose bars grow, flow diagrams whose boxes can be moved,
framed real photographs with an animated highlight, signs, statistic cards and labels. Positions are the prop's
bottom centre in metres; sizes in metres."""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageFont

from .stick import ease

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
INK = (28, 28, 34)


@lru_cache(maxsize=64)
def font(size: int, bold: bool = True):
    return ImageFont.truetype(BOLD if bold else REG, max(6, int(size)))


@lru_cache(maxsize=16)
def _image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def _text(d, xy, text, size, fill=INK, bold=True, anchor="mm", maxw=None):
    f = font(size, bold)
    while maxw and d.textlength(text, font=f) > maxw and size > 8:
        size *= 0.9
        f = font(size, bold)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def draw(p, d, S, scale, t):
    x, y, ang = p.pos(t)
    k = p.kind
    x0, y0 = S(x - p.w / 2, y + p.h)
    x1, y1 = S(x + p.w / 2, y)
    lw = max(2, int(scale * 0.02))
    if k == "crate":
        d.rectangle([x0, y0, x1, y1], fill=(196, 150, 96), outline=(110, 75, 40), width=lw)
        for i in range(1, 3):
            yy = y0 + (y1 - y0) * i / 3
            d.line([(x0, yy), (x1, yy)], fill=(150, 108, 64), width=lw)
        d.line([(x0, y0), (x1, y1)], fill=(150, 108, 64), width=lw)
        if p.label:
            _text(d, ((x0 + x1) / 2, (y0 + y1) / 2), p.label, (y1 - y0) * 0.2, (90, 55, 25), maxw=(x1 - x0) * 0.9)
    elif k == "folder":
        open_ = p.value("open", t)
        d.rounded_rectangle([x0, y0, x1, y1], radius=lw * 2, fill=(222, 182, 106), outline=(150, 112, 52), width=lw)
        tab = (x1 - x0) * 0.35
        if open_ < 0.05:
            d.rounded_rectangle([x0, y0 - (y1 - y0) * 0.12, x0 + tab, y0 + lw * 2], radius=lw * 2, fill=(222, 182, 106),
                                outline=(150, 112, 52), width=lw)
            if p.label:
                _text(d, ((x0 + x1) / 2, (y0 + y1) / 2), p.label, (y1 - y0) * 0.17, (90, 50, 20), maxw=(x1 - x0) * 0.86)
        else:                                       # the cover swings up and back
            lift = (y1 - y0) * (1.0 + 0.2 * open_) * open_
            cover = [(x0, y0), (x1, y0), (x1 - (x1 - x0) * 0.08 * open_, y0 - lift), (x0 + (x1 - x0) * 0.08 * open_, y0 - lift)]
            d.rectangle([x0 + lw * 2, y0 + lw * 2, x1 - lw * 2, y1 - lw * 2], fill=(250, 248, 240))
            for i in range(4):
                yy = y0 + (y1 - y0) * (0.2 + 0.17 * i)
                d.line([(x0 + (x1 - x0) * 0.12, yy), (x1 - (x1 - x0) * 0.12, yy)], fill=(180, 180, 190), width=lw)
            d.polygon(cover, fill=(232, 196, 120), outline=(150, 112, 52))
            if p.label and open_ > 0.3:
                _text(d, ((x0 + x1) / 2, y0 - lift * 0.5), p.label, (y1 - y0) * 0.15, (90, 50, 20), maxw=(x1 - x0) * 0.8)
    elif k == "chart":
        d.rectangle([x0, y0, x1, y1], fill=(250, 250, 246), outline=INK, width=lw)
        title = p.data.get("title", "")
        if title:
            _text(d, ((x0 + x1) / 2, y0 + (y1 - y0) * 0.09), title, (y1 - y0) * 0.075, INK, maxw=(x1 - x0) * 0.92)
        bars = p.data.get("bars", [])
        n = max(1, len(bars))
        base = y1 - (y1 - y0) * 0.14
        top = y0 + (y1 - y0) * 0.2
        bw = (x1 - x0) * 0.7 / n
        vmax = p.data.get("max", 1.0)
        for i, (lab, col) in enumerate(bars):
            v = p.value(f"v{i}", t)
            cx = x0 + (x1 - x0) * (0.15 + 0.7 * (i + 0.5) / n)
            hb = (base - top) * max(0.0, v) / vmax
            d.rectangle([cx - bw * 0.36, base - hb, cx + bw * 0.36, base], fill=col)
            if v > 0.02:
                _text(d, (cx, base - hb - (y1 - y0) * 0.05), p.data.get("fmt", "{:.0f}").format(v), (y1 - y0) * 0.065, INK)
            _text(d, (cx, base + (y1 - y0) * 0.065), lab, (y1 - y0) * 0.05, INK, bold=False, maxw=bw * 1.1)
        d.line([(x0 + (x1 - x0) * 0.08, base), (x1 - (x1 - x0) * 0.08, base)], fill=INK, width=lw)
        if p.data.get("source"):
            _text(d, (x1 - lw * 3, y1 - lw * 3), p.data["source"], (y1 - y0) * 0.035, (110, 110, 120), bold=False,
                  anchor="rd")
    elif k == "diagram":
        labels = p.data.get("boxes", [])
        n = max(1, len(labels))
        bw, bh = p.w / n * 0.78, p.h * 0.55
        reveal = p.value("reveal", t, 1.0)
        centres = []
        for i, lab in enumerate(labels):
            ox = p.value(f"bx{i}", t, (i + 0.5) / n * p.w - p.w / 2)
            oy = p.value(f"by{i}", t, p.h * 0.5)
            pop = ease("back", max(0.0, min(1.0, reveal * n - i)))
            if pop <= 0:
                continue
            cx, cy = x + ox, y + oy
            ax0, ay0 = S(cx - bw / 2 * pop, cy + bh / 2 * pop)
            ax1, ay1 = S(cx + bw / 2 * pop, cy - bh / 2 * pop)
            col = p.data.get("colors", [(70, 130, 220)] * n)[i]
            d.rounded_rectangle([ax0, ay0, ax1, ay1], radius=lw * 3, fill=col, outline=INK, width=lw)
            _text(d, ((ax0 + ax1) / 2, (ay0 + ay1) / 2), lab, (ay1 - ay0) * 0.3, (255, 255, 255), maxw=(ax1 - ax0) * 0.9)
            centres.append((ox, cx, cy, ax0, ax1, (ay0 + ay1) / 2))
        centres.sort()
        for a, b in zip(centres, centres[1:]):            # arrows follow the boxes' current order
            sx, sy = a[4] + lw * 2, a[5]
            ex, ey = b[3] - lw * 2, b[5]
            if ex - sx > lw * 4:
                d.line([(sx, sy), (ex, ey)], fill=INK, width=lw)
                d.polygon([(ex, ey), (ex - lw * 4, ey - lw * 3), (ex - lw * 4, ey + lw * 3)], fill=INK)
    elif k == "photo":
        img = _image(p.data["image"])
        w, h = int(x1 - x0), int(y1 - y0)
        if w > 4 and h > 4:
            pad = max(4, int(min(w, h) * 0.025))
            d.rectangle([x0 - pad + lw * 2, y0 - pad + lw * 2, x1 + pad + lw * 2, y1 + pad + lw * 2], fill=(0, 0, 0, 70))
            d.rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], fill=(252, 252, 250))
            d._image.paste(img.resize((w, h), Image.LANCZOS), (int(x0), int(y0)))
            hl = p.data.get("highlight")
            if hl:
                k2 = p.value("hl", t)
                if k2 > 0:
                    hx0, hy0, hx1, hy1 = hl
                    ex = x0 + w * (hx0 + (hx1 - hx0) * k2)
                    d.rectangle([x0 + w * hx0, y0 + h * hy0, ex, y0 + h * hy1], fill=(255, 225, 40, 85),
                                outline=(240, 180, 0), width=lw)
            if p.data.get("credit"):
                _text(d, (x1, y1 + pad * 2.4), p.data["credit"], max(10, pad * 2.2), (70, 70, 78), bold=False, anchor="ra")
    elif k == "sign":
        d.rounded_rectangle([x0, y0, x1, y1], radius=lw * 3, fill=p.color, outline=INK, width=lw)
        _text(d, ((x0 + x1) / 2, (y0 + y1) / 2), p.label, (y1 - y0) * 0.42, p.data.get("ink", (255, 255, 255)),
              maxw=(x1 - x0) * 0.9)
    elif k == "stat":
        pop = ease("back", p.value("pop", t, 1.0))
        if pop > 0.01:
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            hw, hh = (x1 - x0) / 2 * pop, (y1 - y0) / 2 * pop
            d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], radius=lw * 4, fill=(255, 255, 255, 235),
                                outline=(210, 30, 40), width=lw * 2)
            _text(d, (cx, cy - hh * 0.25), p.label, hh * 0.75, (210, 30, 40), maxw=hw * 1.8)
            _text(d, (cx, cy + hh * 0.45), p.data.get("sub", ""), hh * 0.24, INK, bold=False, maxw=hw * 1.85)
            if p.data.get("source"):
                _text(d, (cx + hw - lw * 3, cy + hh + lw * 6), p.data["source"], hh * 0.2, (90, 90, 100), bold=False,
                      anchor="ra")
    elif k == "gift":
        pop = p.value("pop", t)                        # 0 closed .. 1 burst open
        shake = p.value("shake", t)
        jx = (scale * 0.02) * math.sin(t * 60) * shake
        bx0, bx1 = x0 + jx, x1 + jx
        lid_h = (y1 - y0) * 0.22
        d.rectangle([bx0, y0 + lid_h, bx1, y1], fill=(70, 120, 210), outline=INK, width=lw)
        d.rectangle([(bx0 + bx1) / 2 - lw * 3, y0 + lid_h, (bx0 + bx1) / 2 + lw * 3, y1], fill=(250, 200, 60))
        lift = pop * (y1 - y0) * 2.2
        tilt = pop * 0.7
        cx = (bx0 + bx1) / 2 + pop * (x1 - x0) * 0.9
        ly = y0 - lift
        w2 = (x1 - x0) * 0.56
        pts = [(-w2, 0), (w2, 0), (w2, lid_h), (-w2, lid_h)]
        pts = [(cx + px * math.cos(tilt) - py * math.sin(tilt), ly + px * math.sin(tilt) + py * math.cos(tilt)) for px, py in pts]
        d.polygon(pts, fill=(80, 135, 225), outline=INK)
        if pop < 0.05 and p.label:
            _text(d, ((bx0 + bx1) / 2, (y0 + lid_h + y1) / 2), p.label, (y1 - y0) * 0.45, (255, 255, 255))
        if pop > 0.05:                                # a spring with a flag springs out
            top = y0 + lid_h - (y1 - y0) * 1.6 * ease("back", min(1.0, pop * 1.4))
            mx = (bx0 + bx1) / 2
            zz = [(mx + ((-1) ** i) * (x1 - x0) * 0.12, y0 + lid_h - (y0 + lid_h - top) * i / 8) for i in range(9)]
            d.line(zz, fill=(90, 90, 100), width=lw)
            d.rectangle([mx - (x1 - x0) * 0.55, top - (y1 - y0) * 0.5, mx + (x1 - x0) * 0.55, top], fill=(230, 60, 70),
                        outline=INK, width=lw)
            _text(d, (mx, top - (y1 - y0) * 0.25), p.data.get("burst", "!"), (y1 - y0) * 0.38, (255, 255, 255))
            for i in range(10):                         # confetti
                a = i * 0.63
                r = (x1 - x0) * (0.4 + 1.6 * pop)
                fx, fy = mx + math.cos(a) * r, top - (y1 - y0) * 0.3 + math.sin(a) * r * 0.6 + pop * (y1 - y0) * 0.8
                d.rectangle([fx, fy, fx + lw * 3, fy + lw * 2], fill=[(240, 80, 90), (250, 200, 60), (80, 160, 240)][i % 3])
    elif k == "table":
        top = lw * 4
        d.rectangle([x0, y0, x1, y0 + top], fill=(120, 74, 44), outline=(70, 42, 22), width=lw)
        d.rectangle([x0 + (x1 - x0) * 0.05, y0 + top, x0 + (x1 - x0) * 0.95, y1], fill=(98, 60, 36))
        d.rectangle([x0 + (x1 - x0) * 0.08, y0 + top * 2, x0 + (x1 - x0) * 0.92, y1 - top], outline=(140, 92, 56),
                    width=lw)
    elif k == "label":
        _text(d, ((x0 + x1) / 2, (y0 + y1) / 2), p.label, (y1 - y0) * 0.8, p.color, maxw=(x1 - x0))
