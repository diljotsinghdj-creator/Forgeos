"""Reusable worlds: painted parallax environments with atmospheric depth and living details, for any genre.

    worlds.build(scene, "forest", seed=3, variant="night")      -> notes (what was built)
    worlds.WORLDS                                                -> name: (builder, description)

Every world is layers at real depths (far layers move slower, are drawn smaller, and fade into the sky colour: aerial
perspective), a ground the characters stand on at z = 1, optional foreground layers that pass in front of the cast,
and "animated" painters drawn every frame for what must move: water, stars, drifting cells, swaying weed, flags,
fireflies, light shafts. Weather and time of day (scene2d's light/weather layers) work on top of every world.

Worlds: city, ancient, castle (fantasy kingdom), forest, ocean (coast), underwater, mountains, desert, savanna,
space, microscopic, mind (abstract), interior (home | school | office), village."""
from __future__ import annotations

import math
import random

from .scene2d import Layer, _ridge, mixc

SPAN = (-45.0, 65.0)


def _haze(col, z, haze, k=14.0, most=0.82):
    return mixc(col, haze, min(most, (z - 1) / k)) if z > 1 else col


def _sky(sc, top, bottom, sun=None):
    sc.sky = (top, bottom)
    sc.sun = sun
    sc.__dict__.pop("_sky_img", None)


def _clouds(sc, rng, col=(255, 255, 255), alpha=150, z=40.0, n=14, band=(6.0, 14.0)):
    def paint(d, w, h, left, scale, gy):
        for _ in range(n):
            x = rng.uniform(0, w)
            y = gy - rng.uniform(*band) * scale
            r = scale * rng.uniform(1.6, 3.4)
            for k in range(6):
                ox, oy = rng.uniform(-1.6, 1.6) * r, rng.uniform(-0.25, 0.2) * r
                rr = r * rng.uniform(0.45, 0.8)
                d.ellipse([x + ox - rr * 1.6, y + oy - rr * 0.7, x + ox + rr * 1.6, y + oy + rr * 0.6],
                          fill=col + (alpha,))
    sc.layers.append(Layer(z, paint, (SPAN[0] * 3, SPAN[1] * 3)))


def _hills(sc, rng, z, base, amp, col, haze, step=1.8, rough=0.55, extra=None):
    pts = _ridge(rng, SPAN[0] * 2.5, SPAN[1] * 2.5, step, base, amp, rough)
    c = _haze(col, z, haze)

    def paint(d, w, h, left, scale, gy):
        poly = [((x - left) * scale, gy - y * scale) for x, y in pts]
        d.polygon([(0, h)] + [(max(-60, min(w + 60, x)), y) for x, y in poly] + [(w, h)], fill=c)
        if extra:
            extra(d, w, h, left, scale, gy, pts, c)
    sc.layers.append(Layer(z, paint, (SPAN[0] * 2.5, SPAN[1] * 2.5)))
    return pts


def _tree(d, x, gy, scale, kind, col, trunk, rng, size=1.0):
    s = scale * size
    if kind == "conifer":
        d.rectangle([x - s * 0.07, gy - s * 0.6, x + s * 0.07, gy], fill=trunk)
        for k in range(4):
            y0 = gy - s * (0.45 + k * 0.55)
            wv = s * (0.95 - k * 0.2)
            d.polygon([(x - wv, y0), (x + wv, y0), (x, y0 - s * 1.0)], fill=mixc(col, (0, 0, 0), 0.08 * k))
    elif kind == "palm":
        d.line([(x, gy), (x + s * 0.25, gy - s * 1.6), (x + s * 0.2, gy - s * 2.6)], fill=trunk, width=max(2, int(s * 0.12)))
        tx, ty = x + s * 0.2, gy - s * 2.6
        for k in range(7):
            a = math.pi * (0.95 + 1.1 * k / 6)
            d.line([(tx, ty), (tx + math.cos(a) * s * 1.1, ty + math.sin(a) * s * 0.45 + s * 0.35)], fill=col,
                   width=max(2, int(s * 0.14)))
    elif kind == "acacia":
        d.line([(x, gy), (x - s * 0.1, gy - s * 1.2), (x + s * 0.2, gy - s * 1.9)], fill=trunk, width=max(2, int(s * 0.1)))
        d.line([(x - s * 0.1, gy - s * 1.2), (x - s * 0.6, gy - s * 1.85)], fill=trunk, width=max(2, int(s * 0.07)))
        d.ellipse([x - s * 1.5, gy - s * 2.25, x + s * 1.3, gy - s * 1.75], fill=col)
    elif kind == "dead":
        d.line([(x, gy), (x, gy - s * 1.8)], fill=trunk, width=max(2, int(s * 0.1)))
        for k in range(4):
            y = gy - s * (0.8 + 0.3 * k)
            sd = 1 if k % 2 else -1
            d.line([(x, y), (x + sd * s * 0.6, y - s * 0.45)], fill=trunk, width=max(2, int(s * 0.05)))
    else:                                              # broadleaf
        d.rectangle([x - s * 0.09, gy - s * 1.3, x + s * 0.09, gy], fill=trunk)
        for k in range(6):
            bx = x + rng.uniform(-0.55, 0.55) * s
            by = gy - s * rng.uniform(1.45, 2.3)
            r = s * rng.uniform(0.45, 0.7)
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=mixc(col, (255, 255, 230), rng.uniform(0, 0.12)))


def _trees(sc, rng, z, kind, col, trunk, haze, every=2.4, size=(0.8, 1.3), floor=None):
    c, tc = _haze(col, z, haze), _haze(trunk, z, haze)

    def paint(d, w, h, left, scale, gy):
        if floor:
            d.rectangle([0, gy - scale * 0.1, w, h], fill=_haze(floor, z, haze))
        x = SPAN[0]
        while x < SPAN[1]:
            _tree(d, (x - left) * scale, gy, scale, kind, c, tc, rng, rng.uniform(*size))
            x += every * rng.uniform(0.6, 1.4)
    sc.layers.append(Layer(z, paint, SPAN))


def _ground(sc, col, line=None, detail=None, z=1.0, front_strip=None):
    def paint(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=col)
        if front_strip:
            d.rectangle([0, gy - scale * 0.05, w, gy + scale * front_strip[0]], fill=front_strip[1])
        if line:
            d.line([(0, gy - scale * 0.04), (w, gy - scale * 0.04)], fill=line, width=max(2, int(scale * 0.01)))
        if detail:
            detail(d, w, h, left, scale, gy)
    sc.layers.append(Layer(z, paint, SPAN))


# ---- animated painters: fn(d, W, H, to_screen_z, t, cam_x) at supersampled resolution ---------------------------
def _visible(to_screen_z, z, W, cx):
    S, scale = to_screen_z(z)
    half = W / 2 / scale
    return S, scale, cx - half - 1, cx + half + 1


def _waves(z_list, sea_y=0.0, col=(255, 255, 255), amp=0.06, speed=1.2):
    def fn(d, W, H, to_screen_z, t, cx):
        for z in z_list:
            S, scale, x0, x1 = _visible(to_screen_z, z, W, cx)
            step = max(0.15, 0.6 / z)
            for row in range(3):
                pts = []
                x = x0
                yb = sea_y + 0.05 * row * z
                while x <= x1:
                    y = yb + amp * z * math.sin(x * 1.3 / z + t * speed * (1 + 0.2 * row) + row)
                    pts.append(S(x, y))
                    x += step
                d.line(pts, fill=col + (int(150 / (1 + row)),), width=max(1, int(scale * 0.02)))
            for k in range(12):                       # sparkles
                ph = (k * 0.618 + t * 0.35) % 1
                x = x0 + (x1 - x0) * ((k * 0.377) % 1)
                y = sea_y + 0.08 * z * ((k * 0.53) % 1)
                a = int(220 * math.sin(math.pi * ph))
                px, py = S(x, y)
                r = scale * 0.04
                d.ellipse([px - r * 2, py - r * 0.4, px + r * 2, py + r * 0.4], fill=(255, 255, 240, a))
    return fn


def _stars(n=260, seed=2):
    rng = random.Random(seed)
    stars = [(rng.random(), rng.random() * 0.7, rng.random() * 6.28, rng.uniform(0.5, 1.6)) for _ in range(n)]

    def fn(d, W, H, to_screen_z, t, cx):
        drift = (cx * 0.004) % 1
        for x, y, ph, s in stars:
            a = int(140 + 115 * math.sin(t * 1.7 + ph))
            px, py = ((x - drift) % 1) * W, y * H
            r = s * H / 1080 * 2
            d.ellipse([px - r, py - r, px + r, py + r], fill=(255, 255, 250, a))
    return fn


def _drifters(kind, n, seed, area=(-14, 14, 0.4, 5.0), z=(1.4, 4.0), col=(255, 255, 255), speed=0.3, size=0.4):
    rng = random.Random(seed)
    items = [(rng.uniform(*area[:2]), rng.uniform(*area[2:]), rng.uniform(*z), rng.random() * 6.28,
              rng.uniform(0.6, 1.4)) for _ in range(n)]

    def fn(d, W, H, to_screen_z, t, cx):
        for x, y, zz, ph, s in sorted(items, key=lambda q: -q[2]):
            S, scale = to_screen_z(zz)
            if kind == "bubble":
                yy = area[2] + ((y - area[2] + t * speed * s) % (area[3] - area[2]))
                xx = cx + x + 0.15 * math.sin(t * 2 + ph)
            else:
                yy = y + 0.3 * math.sin(t * 0.4 * s + ph)
                xx = cx * 0.0 + x + t * speed * 0.3 * math.sin(ph) + 0.4 * math.sin(t * 0.3 + ph)
            px, py = S(xx, yy)
            r = scale * size * s
            if kind == "cell":
                d.ellipse([px - r * 1.3, py - r, px + r * 1.3, py + r], fill=col + (150,), outline=mixc(col, (0, 0, 0), 0.4) + (200,),
                          width=max(2, int(r * 0.08)))
                d.ellipse([px - r * 0.35 + r * 0.2 * math.sin(t + ph), py - r * 0.3, px + r * 0.35 + r * 0.2 * math.sin(t + ph),
                           py + r * 0.3], fill=mixc(col, (90, 30, 90), 0.5) + (210,))
            elif kind == "bubble":
                d.ellipse([px - r * 0.3, py - r * 0.3, px + r * 0.3, py + r * 0.3], outline=(230, 250, 255, 190),
                          width=max(1, int(r * 0.06)))
            elif kind == "firefly":
                a = int(255 * max(0.0, math.sin(t * 2.3 + ph)))
                d.ellipse([px - r * 0.12, py - r * 0.12, px + r * 0.12, py + r * 0.12], fill=(255, 240, 120, a))
                d.ellipse([px - r * 0.4, py - r * 0.4, px + r * 0.4, py + r * 0.4], fill=(255, 240, 120, a // 5))
            elif kind == "sparkle":
                a = int(255 * max(0.0, math.sin(t * 3.1 + ph)))
                for ang in (0, math.pi / 2):
                    dx, dy = math.cos(ang) * r * 0.5, math.sin(ang) * r * 0.5
                    d.line([(px - dx, py - dy), (px + dx, py + dy)], fill=col + (a,), width=max(1, int(r * 0.08)))
            elif kind == "shape":                      # mind-space: slowly turning outlines
                n_ = 3 + int(ph * 10) % 4
                pts = [(px + math.cos(t * 0.3 * s + ph + k * math.tau / n_) * r,
                        py + math.sin(t * 0.3 * s + ph + k * math.tau / n_) * r) for k in range(n_)]
                d.polygon(pts, outline=col + (170,))
                d.line(pts + [pts[0]], fill=col + (170,), width=max(2, int(r * 0.06)))
            elif kind == "leaf":
                yy = area[3] - ((t * speed * s + y) % (area[3] - area[2]))
                xx = x + 0.6 * math.sin(t * 1.3 + ph) + t * 0.2
                px, py = S(xx, yy)
                d.ellipse([px - r * 0.25, py - r * 0.12, px + r * 0.25, py + r * 0.12], fill=col + (220,))
    return fn


def _rays(src_x=0.25, col=(255, 245, 200), n=5, strength=40):
    def fn(d, W, H, to_screen_z, t, cx):
        for k in range(n):
            a = int(strength * (0.6 + 0.4 * math.sin(t * 0.5 + k * 1.7)))
            x0 = W * (src_x + 0.11 * k)
            d.polygon([(x0, 0), (x0 + W * 0.05, 0), (x0 + W * 0.22 + W * 0.04 * k, H), (x0 + W * 0.1 + W * 0.04 * k, H)],
                      fill=col + (a,))
    return fn


def _sway(items, seed=5, col=(40, 120, 70), height=(0.8, 1.8), z=1.25, width=0.05):
    rng = random.Random(seed)
    stalks = [(rng.uniform(-30, 50), rng.uniform(*height), rng.random() * 6.28) for _ in range(items)]

    def fn(d, W, H, to_screen_z, t, cx):
        S, scale = to_screen_z(z)
        for x, hgt, ph in stalks:
            if abs(x - cx) > W / scale:
                continue
            pts = []
            for k in range(8):
                u = k / 7
                pts.append(S(x + 0.18 * u * u * math.sin(t * 1.1 + ph + u * 2), u * hgt))
            d.line(pts, fill=col, width=max(2, int(scale * width)), joint="curve")
    return fn


def _flags(xs, z, top, col=(200, 40, 40)):
    def fn(d, W, H, to_screen_z, t, cx):
        S, scale = to_screen_z(z)
        for x, y in [(x, top) for x in xs]:
            pts = []
            for k in range(7):
                u = k / 6
                pts.append(S(x + u * 0.9, y + 0.08 * math.sin(t * 4 - u * 3) * u))
            low = [(px, py + scale * 0.45) for px, py in reversed(pts)]
            d.polygon(pts + low, fill=col)
    return fn


# ---- the worlds -------------------------------------------------------------------------------------------------
def city(sc, rng, variant=""):
    night = variant == "night"
    _sky(sc, (16, 22, 48) if night else (92, 140, 205), (60, 60, 96) if night else (226, 222, 214),
         None if night else (0.82, 0.18, 0.03, (255, 236, 200)))
    haze = sc.sky[1]
    if not night:
        _clouds(sc, rng, alpha=120)
    for z, hmin, hmax, col in ((22, 6, 18, (110, 120, 150)), (9, 4, 12, (96, 104, 128)), (3.6, 3, 7, (120, 110, 104))):
        c = _haze(col, z, haze, 22)

        def paint(d, w, h, left, scale, gy, c=c, hmin=hmin, hmax=hmax, z=z):
            x = 0
            while x < w:
                bw = scale * rng.uniform(1.5, 3.4)
                bh = scale * rng.uniform(hmin, hmax)
                d.rectangle([x, gy - bh, x + bw, gy], fill=c)
                if rng.random() < 0.3:              # a roof feature
                    d.rectangle([x + bw * 0.4, gy - bh - scale * 0.6, x + bw * 0.46, gy - bh], fill=c)
                lit = (255, 214, 120) if night else mixc(c, (230, 240, 255), 0.35)
                for wy in range(int(gy - bh + scale * 0.4), int(gy - scale * 0.3), max(3, int(scale * 0.6))):
                    for wx in range(int(x + scale * 0.25), int(x + bw - scale * 0.3), max(3, int(scale * 0.5))):
                        if not night or rng.random() < 0.45:
                            d.rectangle([wx, wy, wx + scale * 0.2, wy + scale * 0.28], fill=lit)
                x += bw + scale * rng.uniform(0.05, 0.4)
        sc.layers.append(Layer(z, paint, SPAN))

    def street(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(70, 72, 80))
        d.rectangle([0, gy - scale * 0.04, w, gy + scale * 0.35], fill=(150, 148, 144))
        for k in range(int(w / (scale * 1.4))):
            x = k * scale * 1.4
            d.line([(x, gy - scale * 0.04), (x, gy + scale * 0.35)], fill=(120, 118, 114), width=2)
        for k in range(int(w / (scale * 2.5)) + 1):
            x = k * scale * 2.5
            d.rectangle([x, gy + scale * 0.9, x + scale * 1.2, gy + scale * 0.97], fill=(230, 220, 160))
        x = SPAN[0]
        while x < SPAN[1]:                            # street lamps
            px = (x - left) * scale
            d.rectangle([px - scale * 0.035, gy - scale * 3.2, px + scale * 0.035, gy], fill=(40, 44, 52))
            d.line([(px, gy - scale * 3.2), (px + scale * 0.45, gy - scale * 3.3)], fill=(40, 44, 52), width=max(2, int(scale * 0.04)))
            d.ellipse([px + scale * 0.3, gy - scale * 3.35, px + scale * 0.6, gy - scale * 3.18],
                      fill=(255, 236, 170) if night else (230, 230, 220))
            x += 9.0
    sc.layers.append(Layer(1.0, street, SPAN))
    if night:
        sc.animated.append(_stars(80, 4))
    return "modern city: three skyline depths, street, lamps" + (", lit windows at night" if night else "")


def ancient(sc, rng, variant=""):
    _sky(sc, (88, 130, 190), (250, 214, 160), (0.72, 0.3, 0.05, (255, 220, 160)))
    haze = sc.sky[1]
    _hills(sc, rng, 18, 1.0, 1.2, (170, 140, 120), haze, 3.0)
    pyr = variant != "rome"

    def monuments(d, w, h, left, scale, gy):
        if pyr:
            for x, s in ((-10, 9), (6, 13), (22, 7)):
                px = (x - left) * scale
                c = _haze((214, 176, 120), 9, haze)
                d.polygon([(px - s * scale * 0.8, gy), (px + s * scale * 0.8, gy), (px, gy - s * scale * 0.62)], fill=c)
                d.polygon([(px, gy - s * scale * 0.62), (px + s * scale * 0.8, gy), (px + s * scale * 0.2, gy)],
                          fill=mixc(c, (120, 80, 60), 0.25))
        else:
            for x in (-12, 4, 18):                    # an arena and aqueduct arches
                px = (x - left) * scale
                c = _haze((196, 170, 136), 9, haze, 30)
                for k in range(8):
                    ax_ = px + k * scale * 1.2
                    d.rectangle([ax_, gy - scale * 4.2, ax_ + scale * 1.2, gy], fill=c)
                    d.chord([ax_ + scale * 0.2, gy - scale * 3.4, ax_ + scale * 1.0, gy - scale * 2.0], 180, 360,
                            fill=mixc(c, haze, 0.6))
                    d.rectangle([ax_ + scale * 0.2, gy - scale * 2.7, ax_ + scale * 1.0, gy], fill=mixc(c, haze, 0.6))
    sc.layers.append(Layer(9.0, monuments, SPAN))

    def temple(d, w, h, left, scale, gy):
        for x in (-6.0, 12.0, 30.0):
            px = (x - left) * scale
            c = _haze((232, 214, 182), 3.2, haze)
            sh = mixc(c, (110, 80, 60), 0.3)
            d.rectangle([px - scale * 3.2, gy - scale * 0.5, px + scale * 3.2, gy], fill=sh)
            for k in range(7):
                cx_ = px - scale * 2.7 + k * scale * 0.9
                d.rectangle([cx_ - scale * 0.16, gy - scale * 3.4, cx_ + scale * 0.16, gy - scale * 0.5], fill=c)
                d.rectangle([cx_ - scale * 0.05, gy - scale * 3.4, cx_ + scale * 0.03, gy - scale * 0.5], fill=sh)
            d.rectangle([px - scale * 3.3, gy - scale * 3.8, px + scale * 3.3, gy - scale * 3.4], fill=c)
            d.polygon([(px - scale * 3.3, gy - scale * 3.8), (px + scale * 3.3, gy - scale * 3.8), (px, gy - scale * 4.7)],
                      fill=mixc(c, (255, 240, 210), 0.2))
        x = SPAN[0]
        while x < SPAN[1]:
            _tree(d, (x - left) * scale, gy, scale, "palm", _haze((70, 110, 60), 3.2, haze), _haze((120, 90, 60), 3.2, haze), rng)
            x += rng.uniform(5, 9)
    sc.layers.append(Layer(3.2, temple, SPAN))
    _ground(sc, (222, 190, 140), front_strip=(0.3, (206, 172, 124)))
    sc.animated.append(_drifters("leaf", 14, 6, (-14, 14, 0.2, 2.0), (1.2, 2.5), (230, 200, 150), 0.5, 0.25))
    return "ancient civilisation: " + ("pyramids" if pyr else "arches and an aqueduct") + ", a columned temple, palms, drifting dust"


def castle(sc, rng, variant=""):
    dusk = variant != "day"
    _sky(sc, (70, 60, 130) if dusk else (110, 160, 225), (250, 176, 150) if dusk else (220, 236, 250),
         (0.2, 0.42, 0.05, (255, 200, 150)) if dusk else None)
    haze = sc.sky[1]
    _clouds(sc, rng, (255, 220, 230) if dusk else (255, 255, 255), 110)

    def isles(d, w, h, left, scale, gy):           # floating islands
        for x, y, s in ((-14, 7.0, 2.2), (9, 9.0, 3.0), (26, 6.0, 1.6)):
            px, py = (x - left) * scale, gy - y * scale
            c = _haze((120, 110, 140), 16, haze)
            d.polygon([(px - s * scale, py), (px + s * scale, py), (px + s * scale * 0.2, py + s * scale * 1.2)], fill=c)
            d.ellipse([px - s * scale * 1.05, py - s * scale * 0.25, px + s * scale * 1.05, py + s * scale * 0.2],
                      fill=_haze((110, 150, 100), 16, haze))
    sc.layers.append(Layer(16.0, isles, (SPAN[0] * 2, SPAN[1] * 2)))
    pts = _hills(sc, rng, 7.0, 1.5, 1.4, (90, 110, 120), haze, 2.2)

    def keep(d, w, h, left, scale, gy):
        px = (4.0 - left) * scale
        c = _haze((150, 140, 160), 5, haze)
        base = gy - 1.6 * scale
        d.rectangle([px - scale * 3, base - scale * 2.5, px + scale * 3, base], fill=c)
        for k in range(13):
            d.rectangle([px - scale * 3 + k * scale * 0.5, base - scale * 2.8, px - scale * 2.75 + k * scale * 0.5,
                         base - scale * 2.5], fill=c)
        for tx, th in ((-3.2, 4.6), (3.2, 4.6), (0.0, 6.2)):
            x0 = px + tx * scale
            d.rectangle([x0 - scale * 0.6, base - th * scale, x0 + scale * 0.6, base], fill=mixc(c, (255, 255, 255), 0.08))
            d.polygon([(x0 - scale * 0.8, base - th * scale), (x0 + scale * 0.8, base - th * scale),
                       (x0, base - (th + 1.6) * scale)], fill=_haze((110, 60, 90), 5, haze))
            for wy in (1.5, 3.0):
                d.rectangle([x0 - scale * 0.12, base - (th - wy) * scale - scale * 0.4, x0 + scale * 0.12,
                             base - (th - wy) * scale], fill=(255, 210, 120) if dusk else (60, 50, 70))
    sc.layers.append(Layer(5.0, keep, SPAN))
    sc.animated.append(_flags([4.0 - 3.2, 4.0 + 3.2, 4.0], 5.0, 1.6 + 4.6 + 1.6, (200, 40, 60)))
    _trees(sc, rng, 2.6, "conifer", (50, 90, 70), (70, 50, 40), haze, 3.0)
    _ground(sc, (98, 140, 80), front_strip=(0.3, (150, 130, 100)))
    sc.animated.append(_drifters("sparkle", 30, 7, (-12, 12, 0.5, 4.0), (1.1, 3.0), (255, 230, 150), 0.0, 0.35))
    return "fantasy kingdom: floating islands, a castle on a hill with waving banners, pines, magic sparkles"


def forest(sc, rng, variant=""):
    night = variant == "night"
    _sky(sc, (20, 30, 50) if night else (120, 170, 200), (40, 60, 70) if night else (210, 230, 210))
    haze = sc.sky[1]
    _trees(sc, rng, 14, "conifer", (60, 100, 90), (60, 60, 50), haze, 1.0, (1.4, 2.2))
    _trees(sc, rng, 6.0, "conifer", (40, 90, 60), (70, 55, 40), haze, 1.6, (1.2, 1.8))
    _trees(sc, rng, 2.8, "broadleaf", (50, 110, 55), (80, 60, 40), haze, 2.6, (1.0, 1.4), floor=(70, 110, 60))

    def floor(d, w, h, left, scale, gy):
        for k in range(int(w / (scale * 0.25))):
            x = k * scale * 0.25 + rng.uniform(0, scale * 0.2)
            y = gy + rng.uniform(0.1, 1.5) * scale
            d.ellipse([x - scale * 0.12, y - scale * 0.04, x + scale * 0.12, y + scale * 0.04],
                      fill=mixc((70, 110, 50), (140, 120, 70), rng.random()))
    _ground(sc, (84, 120, 62), detail=floor, front_strip=(0.25, (120, 100, 70)))

    def ferns(d, w, h, left, scale, gy):
        x = SPAN[0]
        while x < SPAN[1]:
            px = (x - left) * scale
            for k in range(9):
                a = math.pi * (1.15 + 0.7 * k / 8)
                L_ = scale * rng.uniform(0.35, 0.6)
                ex, ey = px + math.cos(a) * L_, h + math.sin(a) * L_
                d.line([(px, h), (ex, ey)], fill=(28, 60, 36), width=max(2, int(scale * 0.02)))
                for j in range(1, 6):                 # leaflets along the frond
                    u = j / 6
                    qx, qy = px + (ex - px) * u, h + (ey - h) * u
                    rr = scale * 0.05 * (1.2 - u)
                    d.ellipse([qx - rr * 1.6, qy - rr, qx + rr * 1.6, qy + rr], fill=(34, 76, 44))
            x += rng.uniform(5, 9)
    sc.front.append(Layer(0.6, ferns, SPAN))
    if night:
        sc.animated.append(_drifters("firefly", 40, 3, (-12, 12, 0.3, 2.5), (1.1, 3.0), (255, 240, 120), 0.0, 0.5))
    else:
        sc.animated.append(_rays(0.15, (255, 250, 210), 5, 34))
        sc.animated.append(_drifters("leaf", 18, 9, (-12, 12, 0.2, 4.0), (1.1, 2.5), (170, 140, 60), 0.35, 0.3))
    return "forest: three depths of trees, ferns in front, " + ("fireflies at night" if night else "light shafts and falling leaves")


def ocean(sc, rng, variant=""):
    _sky(sc, (80, 150, 220), (230, 236, 240), (0.75, 0.25, 0.04, (255, 244, 210)))
    haze = sc.sky[1]
    _clouds(sc, rng, alpha=140)

    def sea(d, w, h, left, scale, gy):
        top = gy - 0.02 * scale
        for k in range(30):
            y = top + (h - top) * k / 30
            d.rectangle([0, y, w, y + (h - top) / 30 + 1], fill=mixc((70, 130, 170), (30, 90, 140), k / 30))
        for x, s in ((-20, 1.0), (14, 0.7)):         # far sails
            px = (x - left) * scale
            d.polygon([(px, top - s * scale * 2.4), (px, top - s * scale * 0.2), (px + s * scale * 1.2, top - s * scale * 0.3)],
                      fill=(250, 250, 245))
            d.polygon([(px - s * scale, top - s * scale * 0.2), (px + s * scale * 1.4, top - s * scale * 0.2),
                       (px + s * scale * 1.0, top + s * scale * 0.2), (px - s * scale * 0.7, top + s * scale * 0.2)],
                      fill=(110, 70, 50))
    sc.layers.append(Layer(12.0, sea, (SPAN[0] * 2, SPAN[1] * 2)))

    def beach(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(236, 214, 170))
        d.rectangle([0, gy - scale * 0.04, w, gy + scale * 0.06], fill=(214, 190, 150))
        x = SPAN[0]
        while x < SPAN[1]:
            px = (x - left) * scale
            d.ellipse([px - scale * 0.1, gy + scale * 0.5, px + scale * 0.1, gy + scale * 0.56], fill=(250, 240, 220))
            x += rng.uniform(2, 5)
    sc.layers.append(Layer(1.0, beach, SPAN))
    sc.animated.append(_waves([8.0, 4.0, 2.2], sea_y=0.0, amp=0.03))
    return "coast: open sea with animated waves and sparkles, sailing boats, a beach"


def underwater(sc, rng, variant=""):
    _sky(sc, (20, 70, 120), (40, 140, 170))
    haze = sc.sky[1]

    def rocks(d, w, h, left, scale, gy, pts, c):
        pass
    _hills(sc, rng, 10, 0.6, 1.4, (40, 90, 110), haze, 2.0)
    _hills(sc, rng, 4.0, 0.3, 0.8, (90, 110, 100), haze, 1.4)

    def coral(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(206, 192, 150))
        x = SPAN[0]
        while x < SPAN[1]:
            px = (x - left) * scale
            col = rng.choice([(240, 120, 110), (250, 170, 90), (200, 100, 170)])
            for k in range(5):
                a = math.pi * (1.2 + 0.6 * k / 4)
                d.line([(px, gy), (px + math.cos(a) * scale * 0.5, gy + math.sin(a) * scale * 0.7)], fill=col,
                       width=max(3, int(scale * 0.07)))
            x += rng.uniform(3, 6)
    sc.layers.append(Layer(1.0, coral, SPAN))
    sc.animated.append(_rays(0.1, (200, 240, 255), 6, 30))
    sc.animated.append(_sway(26, 3, (40, 130, 80), (0.8, 2.2), 1.4))
    sc.animated.append(_drifters("bubble", 40, 2, (-10, 10, 0.0, 6.0), (1.0, 2.5), (230, 250, 255), 0.6, 0.35))
    return "underwater: blue depth haze, rocks, coral, swaying weed, light shafts, rising bubbles"


def mountains(sc, rng, variant=""):
    _sky(sc, (90, 140, 210), (220, 232, 246), (0.25, 0.2, 0.04, (255, 250, 230)))
    haze = sc.sky[1]
    _clouds(sc, rng, alpha=120)

    def snow(d, w, h, left, scale, gy, pts, c):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if y0 > 10.5:
                d.polygon([((x0 - left) * scale, gy - y0 * scale), ((x1 - left) * scale, gy - y1 * scale),
                           ((x1 - left) * scale, gy - (y1 - 0.9) * scale), ((x0 - left) * scale, gy - (y0 - 1.2) * scale)],
                          fill=(246, 248, 252))
    _hills(sc, rng, 20, 9.5, 5.0, (110, 120, 150), haze, 3.5, 1.2, snow)
    _hills(sc, rng, 8.0, 2.5, 2.0, (80, 110, 100), haze, 2.0)
    _trees(sc, rng, 3.0, "conifer", (40, 90, 60), (60, 50, 40), haze, 1.6, (0.8, 1.3), floor=(110, 150, 90))
    _ground(sc, (130, 170, 100), front_strip=(0.25, (160, 150, 120)))
    return "mountains: snow-capped peaks, foothills, pines, alpine meadow"


def savanna(sc, rng, variant=""):
    _sky(sc, (110, 150, 200), (250, 214, 160), (0.8, 0.4, 0.06, (255, 210, 140)))
    haze = sc.sky[1]
    _hills(sc, rng, 16, 1.0, 1.0, (160, 130, 120), haze, 3.0)
    _trees(sc, rng, 6.0, "acacia", (90, 110, 60), (90, 70, 50), haze, 7.0, (1.4, 2.0))
    _trees(sc, rng, 2.6, "acacia", (80, 104, 50), (80, 60, 40), haze, 9.0, (1.0, 1.4), floor=(200, 170, 100))

    def grass(d, w, h, left, scale, gy):
        for k in range(int(w / (scale * 0.08))):
            x = k * scale * 0.08 + rng.uniform(0, scale * 0.06)
            y = gy + rng.uniform(0, 1.6) * scale
            d.line([(x, y), (x + scale * 0.04, y - scale * 0.16)], fill=mixc((190, 160, 80), (150, 120, 60), rng.random()),
                   width=max(2, int(scale * 0.012)))
    _ground(sc, (214, 182, 112), detail=grass)
    sc.animated.append(_sway(320, 8, (186, 156, 84), (0.12, 0.28), 1.6, 0.01))
    return "savanna: distant hills, acacias at two depths, golden grass that sways in front"


def space(sc, rng, variant=""):
    _sky(sc, (4, 6, 20), (26, 20, 60))

    def nebula(d, w, h, left, scale, gy):
        for _ in range(16):
            x, y = rng.uniform(0, w), gy - rng.uniform(4, 16) * scale
            r = rng.uniform(2, 5) * scale
            d.ellipse([x - r * 1.6, y - r, x + r * 1.6, y + r], fill=rng.choice([(120, 60, 160), (40, 90, 170), (170, 60, 110)]) + (40,))
        px, py = (8 - left) * scale, gy - 9 * scale
        R = 5.0 * scale
        d.ellipse([px - R * 1.9, py - R * 0.35, px + R * 1.9, py + R * 0.35], outline=(220, 200, 160), width=max(3, int(scale * 0.12)))
        d.ellipse([px - R, py - R, px + R, py + R], fill=(200, 140, 90))
        d.chord([px - R, py - R, px + R, py + R], 100, 280, fill=(150, 96, 70))
        d.arc([px - R * 1.9, py - R * 0.35, px + R * 1.9, py + R * 0.35], 0, 180, fill=(220, 200, 160), width=max(3, int(scale * 0.12)))
    sc.layers.append(Layer(30.0, nebula, (SPAN[0] * 3, SPAN[1] * 3)))
    sc.animated.insert(0, _stars(320, 5))

    def moon(d, w, h, left, scale, gy, pts, c):
        for _ in range(int(w / scale / 3)):
            x, y = rng.uniform(0, w), gy - rng.uniform(-0.2, 0.5) * scale
            r = rng.uniform(0.3, 0.9) * scale
            d.ellipse([x - r, y - r * 0.3, x + r, y + r * 0.3], fill=mixc(c, (0, 0, 0), 0.2))
    _hills(sc, rng, 5.0, 0.6, 0.7, (130, 130, 140), (26, 20, 60), 1.4, 0.4, moon)

    def surface(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(170, 168, 174))
        for _ in range(int(w / scale)):
            x, y = rng.uniform(0, w), gy + rng.uniform(0.1, 1.6) * scale
            r = rng.uniform(0.1, 0.45) * scale
            d.ellipse([x - r, y - r * 0.3, x + r, y + r * 0.3], fill=(140, 138, 146))
            d.arc([x - r, y - r * 0.3, x + r, y + r * 0.3], 180, 360, fill=(200, 200, 206), width=2)
    sc.layers.append(Layer(1.0, surface, SPAN))
    return "space: twinkling stars, nebula, a ringed planet, a cratered moon surface"


def microscopic(sc, rng, variant=""):
    _sky(sc, (110, 30, 70), (230, 140, 150))
    haze = sc.sky[1]

    def tissue(d, w, h, left, scale, gy):
        for _ in range(int(w / scale * 0.8)):
            x, y = rng.uniform(0, w), gy - rng.uniform(0, 10) * scale
            r = rng.uniform(0.8, 2.0) * scale
            d.ellipse([x - r * 1.3, y - r, x + r * 1.3, y + r], fill=(210, 110, 130), outline=(170, 70, 100), width=max(2, int(scale * 0.08)))
    sc.layers.append(Layer(9.0, tissue, (SPAN[0] * 2, SPAN[1] * 2)))
    sc.animated.append(_drifters("cell", 14, 4, (-12, 12, 0.6, 5.0), (2.0, 4.5), (240, 90, 90), 0.4, 0.55))

    def membrane(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(200, 90, 120))
        for k in range(int(w / (scale * 0.5))):
            x = k * scale * 0.5
            d.ellipse([x, gy - scale * 0.15, x + scale * 0.5, gy + scale * 0.15], fill=(230, 150, 160), outline=(170, 70, 100), width=2)
    sc.layers.append(Layer(1.0, membrane, SPAN))
    sc.animated.append(_drifters("cell", 8, 11, (-8, 8, 0.4, 3.5), (1.15, 1.6), (250, 230, 120), 0.3, 0.25))
    return "microscopic: tissue walls, drifting red cells and yellow particles, a membrane floor (not to scale)"


def mind(sc, rng, variant=""):
    _sky(sc, (30, 16, 60), (110, 70, 160))

    def grid(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(40, 24, 80))
        for k in range(int(w / (scale * 1.0)) + 1):
            x = k * scale * 1.0
            d.line([(x, gy), (x + (x - w / 2) * 0.8, h)], fill=(150, 110, 230), width=2)
        for k in range(8):
            y = gy + (h - gy) * (k / 8) ** 1.6
            d.line([(0, y), (w, y)], fill=(150, 110, 230), width=2)
    sc.layers.append(Layer(1.0, grid, SPAN))
    sc.animated.append(_drifters("shape", 22, 5, (-12, 12, 1.0, 6.5), (1.5, 6.0), (210, 180, 255), 0.0, 0.7))
    sc.animated.append(_drifters("sparkle", 30, 9, (-12, 12, 0.5, 5.0), (1.2, 4.0), (255, 255, 255), 0.0, 0.3))
    return "mind-space: an abstract purple void, a glowing grid floor, slowly turning shapes and sparks"


def interior(sc, rng, variant="home"):
    _sky(sc, (230, 220, 200), (220, 206, 186))
    wall = {"home": (226, 200, 168), "school": (200, 216, 196), "office": (210, 214, 222)}.get(variant, (226, 200, 168))

    def room(d, w, h, left, scale, gy):
        d.rectangle([0, 0, w, gy], fill=wall)
        d.rectangle([0, gy - scale * 0.25, w, gy], fill=mixc(wall, (90, 70, 50), 0.4))
        x = SPAN[0]
        k = 0
        while x < SPAN[1]:
            px = (x - left) * scale
            if k % 3 == 0:                            # a window with sky
                d.rectangle([px - scale * 0.9, gy - scale * 2.6, px + scale * 0.9, gy - scale * 1.1], fill=(120, 80, 50))
                d.rectangle([px - scale * 0.8, gy - scale * 2.5, px + scale * 0.8, gy - scale * 1.2], fill=(170, 210, 240))
                d.line([(px, gy - scale * 2.5), (px, gy - scale * 1.2)], fill=(120, 80, 50), width=max(2, int(scale * 0.05)))
            elif variant == "school" and k % 3 == 1:
                d.rectangle([px - scale * 1.8, gy - scale * 2.6, px + scale * 1.8, gy - scale * 1.0], fill=(40, 70, 60),
                            outline=(140, 100, 60), width=max(3, int(scale * 0.08)))
                d.text((px - scale * 1.4, gy - scale * 2.3), "E = mc²   a² + b² = c²", fill=(240, 240, 230))
            elif variant == "office" and k % 3 == 1:
                d.rectangle([px - scale * 1.2, gy - scale * 2.4, px + scale * 1.2, gy - scale * 1.2], fill=(250, 250, 250),
                            outline=(80, 80, 90), width=3)
                for b in range(5):
                    bh = scale * rng.uniform(0.2, 0.9)
                    d.rectangle([px - scale * 1.0 + b * scale * 0.42, gy - scale * 1.3 - bh, px - scale * 0.75 + b * scale * 0.42,
                                 gy - scale * 1.3], fill=(70, 120, 200))
            else:                                     # a framed picture and a shelf
                d.rectangle([px - scale * 0.5, gy - scale * 2.4, px + scale * 0.5, gy - scale * 1.6], fill=(150, 110, 70))
                d.rectangle([px - scale * 0.42, gy - scale * 2.32, px + scale * 0.42, gy - scale * 1.68], fill=(120, 160, 140))
                d.rectangle([px - scale * 1.0, gy - scale * 1.25, px + scale * 1.0, gy - scale * 1.18], fill=(120, 86, 56))
                for b in range(6):
                    d.rectangle([px - scale * 0.9 + b * scale * 0.22, gy - scale * 1.55, px - scale * 0.75 + b * scale * 0.22,
                                 gy - scale * 1.25], fill=rng.choice([(170, 60, 60), (60, 90, 150), (200, 170, 70)]))
            x += 4.0
            k += 1
    sc.layers.append(Layer(1.25, room, SPAN))

    def floor(d, w, h, left, scale, gy):
        d.rectangle([0, gy - scale * 0.04, w, h], fill=(170, 124, 84))
        for k in range(int(w / (scale * 0.8)) + 1):
            x = k * scale * 0.8
            d.line([(x, gy), (x + (x - w / 2) * 0.5, h)], fill=(140, 100, 66), width=2)
    sc.layers.append(Layer(1.0, floor, SPAN))
    return f"interior ({variant}): walls with windows, " + {"school": "a blackboard", "office": "charts"}.get(variant, "pictures and shelves") + ", wooden floor"


def village(sc, rng, variant=""):
    _sky(sc, (110, 160, 220), (240, 226, 196), (0.8, 0.25, 0.04, (255, 236, 190)))
    haze = sc.sky[1]
    _clouds(sc, rng, alpha=130)
    _hills(sc, rng, 14, 1.4, 1.2, (110, 140, 110), haze, 2.6)

    def huts(d, w, h, left, scale, gy):
        x = SPAN[0]
        while x < SPAN[1]:
            px = (x - left) * scale
            c = _haze((210, 170, 120), 3.4, haze)
            d.rectangle([px - scale * 1.1, gy - scale * 1.6, px + scale * 1.1, gy], fill=c)
            d.polygon([(px - scale * 1.5, gy - scale * 1.5), (px + scale * 1.5, gy - scale * 1.5), (px, gy - scale * 2.8)],
                      fill=_haze((150, 110, 60), 3.4, haze))
            d.rectangle([px - scale * 0.25, gy - scale * 0.9, px + scale * 0.25, gy], fill=_haze((90, 60, 40), 3.4, haze))
            x += rng.uniform(6, 10)
    sc.layers.append(Layer(3.4, huts, SPAN))
    _ground(sc, (190, 160, 100), front_strip=(0.3, (170, 140, 90)))
    sc.animated.append(_sway(260, 12, (120, 150, 60), (0.12, 0.26), 1.6, 0.01))
    return "village: hills, huts with thatched roofs, a dirt path, swaying grass"


def _desert(sc, rng, variant=""):
    from . import scene2d
    scene2d.desert(sc, rng.randint(0, 99))
    return "desert: violet mountains, dunes, rippled sand, rocks and scrub"


WORLDS = {
    "city": (city, "modern city street; variant night"),
    "ancient": (ancient, "ancient civilisation (pyramids); variant rome (arches)"),
    "castle": (castle, "fantasy kingdom; variant day"),
    "forest": (forest, "forest; variant night"),
    "ocean": (ocean, "coast with waves"),
    "underwater": (underwater, "under the sea"),
    "mountains": (mountains, "snowy mountains"),
    "desert": (_desert, "desert"),
    "savanna": (savanna, "savanna for wildlife"),
    "space": (space, "space and a moon surface"),
    "microscopic": (microscopic, "inside the body (illustrative, not to scale)"),
    "mind": (mind, "abstract psychological space"),
    "interior": (interior, "rooms; variant home | school | office"),
    "village": (village, "a village"),
}
ALIASES = {"street": "city", "town": "city", "egypt": "ancient", "rome": "ancient:rome", "kingdom": "castle",
           "fantasy": "castle", "woods": "forest", "jungle": "forest", "beach": "ocean", "sea": "ocean",
           "coast": "ocean", "reef": "underwater", "alps": "mountains", "himalaya": "mountains", "safari": "savanna",
           "planet": "space", "moon": "space", "cell": "microscopic", "body": "microscopic", "dream": "mind",
           "home": "interior:home", "house": "interior:home", "classroom": "interior:school",
           "school": "interior:school", "office": "interior:office", "countryside": "village"}


def build(sc, name: str, seed: int = 3, variant: str = "") -> str:
    """Builds world `name` (or an alias, "name:variant") into the scene, replacing its layers. Returns a note."""
    name = ALIASES.get(name, name)
    if ":" in name:
        name, v = name.split(":", 1)
        variant = variant or v
    if name not in WORLDS:
        raise ValueError(f"unknown world {name!r}; choose from {sorted(WORLDS)}")
    sc.layers, sc.front = [], []
    sc.animated, sc.animated_front = [], []
    rng = random.Random(seed)
    note = WORLDS[name][0](sc, rng, variant)
    for i, L in enumerate(sc.layers + sc.front):      # each layer paints the same picture whenever it is (re)painted
        L.paint = _reseeded(L.paint, rng, seed * 1000 + i)
    sc.world_name = name
    return note


def _reseeded(paint, rng, s):
    def p(*a):
        rng.seed(s)
        paint(*a)
    return p
