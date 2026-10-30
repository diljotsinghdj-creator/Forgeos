"""Asset creation: new things for a script that needs them, generated as parts, checked, rigged and registered.

An asset is a list of parts in metres (origin at its bottom centre, y up), each a polygon, circle, rectangle or
line with a fill, a draw order and an optional rig:

    spin   wheels: rotate about their centre by the distance travelled (they roll, they don't skid)
    swing  legs, tails, arms of a lamp: swing about a pivot - legs in a gait driven by distance travelled, so they
           stop when the animal stops
    sway   tree canopies, flags: a slow idle swing about a pivot
    flap   wings
    bob    boats: ride up and down

    generate("a small red car")    -> asset dict from a parametric generator (house, shop, tower, car, bus, bicycle,
                                      tree, bush, dog, cat, cow, horse, bird, boat, lamp, chair, table, rock, sign)
    validate(asset)                -> [Issue]: degenerate or self-intersecting shapes, parts outside the bounds,
                                      floating parts, no ground contact, wheels that would wobble, legs that swing
                                      through the floor, an implausible size next to a 1.75 m person, poor contrast,
                                      and a test render that must put ink on the canvas
    compatible(asset, use)         -> (ok, reasons) for carry / sit / stand_on / ride / walk / 3d
    to_mesh(asset) / write_obj     -> an extruded 3D mesh, checked to be closed (every edge shared by two faces)
    import_image(path)             -> a single-image asset, honestly marked: it can move as a whole but has no
                                      separable parts, so it is not animation-ready
    Library                        -> registry (JSON on disk, or in memory): register() refuses anything that
                                      fails validation; ids are content hashes; prop_spec(id) gives a scene prop

An image generator's picture is not an animation-ready asset: it has no parts, pivots or depth. That is why the
generators here build assets from parts, and why imported images are flagged."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

PAPER = (240, 242, 246)
PERSON_H = 1.75

COLOURS = {"red": (204, 64, 58), "blue": (60, 110, 200), "green": (70, 150, 80), "yellow": (240, 200, 60),
           "orange": (236, 140, 50), "white": (236, 236, 232), "black": (50, 50, 56), "grey": (140, 142, 150),
           "gray": (140, 142, 150), "brown": (140, 96, 60), "purple": (130, 80, 170), "pink": (230, 130, 170),
           "silver": (186, 190, 198), "gold": (210, 170, 60)}

# plausible heights in metres (what a viewer expects next to a 1.75 m person)
SIZES = {"house": (3.0, 9.0), "shop": (3.0, 7.0), "tower": (8.0, 60.0), "car": (1.2, 2.0), "bus": (2.6, 4.2),
         "bicycle": (0.8, 1.2), "tree": (2.5, 15.0), "bush": (0.4, 1.6), "dog": (0.3, 1.0), "cat": (0.2, 0.45),
         "cow": (1.2, 1.8), "horse": (1.3, 2.0), "bird": (0.08, 0.6), "boat": (0.3, 3.0), "lamp": (2.5, 6.0),
         "chair": (0.7, 1.1), "table": (0.6, 0.9), "rock": (0.1, 2.0), "sign": (0.8, 3.0)}
SYNONYMS = {"home": "house", "hut": "house", "cottage": "house", "store": "shop", "stall": "shop", "office": "tower",
            "building": "tower", "skyscraper": "tower", "taxi": "car", "jeep": "car", "van": "car", "auto": "car",
            "lorry": "bus", "truck": "bus", "coach": "bus", "bike": "bicycle", "cycle": "bicycle", "puppy": "dog",
            "kitten": "cat", "buffalo": "cow", "ox": "cow", "pony": "horse", "donkey": "horse", "crow": "bird",
            "pigeon": "bird", "sparrow": "bird", "parrot": "bird", "ship": "boat", "canoe": "boat",
            "streetlight": "lamp", "lamppost": "lamp", "lantern": "lamp", "stool": "chair", "desk": "table",
            "boulder": "rock", "stone": "rock", "shrub": "bush", "plant": "bush", "signpost": "sign",
            "billboard": "sign", "palm": "tree", "oak": "tree", "banyan": "tree"}


# ---- parts -------------------------------------------------------------------------------------------------------------
def darker(c, k=0.62):
    return tuple(int(v * k) for v in c)


def poly(pid, pts, fill, z=0, rig=None, line=None):
    return {"id": pid, "shape": "poly", "pts": [[round(x, 4), round(y, 4)] for x, y in pts], "fill": list(fill),
            "line": list(line or darker(fill)), "z": z, **({"rig": rig} if rig else {})}


def rect(pid, x0, y0, x1, y1, fill, z=0, rig=None):
    return poly(pid, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, z, rig)


def circle(pid, cx, cy, r, fill, z=0, rig=None):
    return {"id": pid, "shape": "circle", "c": [round(cx, 4), round(cy, 4)], "r": round(r, 4), "fill": list(fill),
            "line": list(darker(fill)), "z": z, **({"rig": rig} if rig else {})}


def line(pid, pts, colour, width, z=0, rig=None):
    return {"id": pid, "shape": "line", "pts": [[round(x, 4), round(y, 4)] for x, y in pts], "fill": list(colour),
            "width": width, "z": z, **({"rig": rig} if rig else {})}


def ellipse_pts(cx, cy, rx, ry, n=18):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _asset(kind, name, parts, w, h, **meta):
    return {"kind": kind, "name": name, "w": round(w, 3), "h": round(h, 3), "parts": parts,
            "grounded": meta.pop("grounded", True), "loose": meta.pop("loose", []), **meta}


# ---- generators --------------------------------------------------------------------------------------------------------
def _wheel(pid, cx, r, z=5):
    spin = {"type": "spin", "pivot": [cx, r]}
    return [circle(pid, cx, r, r, (46, 46, 52), z, spin), circle(pid + "_hub", cx, r, r * 0.42, (190, 192, 200), z + 1, spin),
            line(pid + "_spoke", [(cx - r * 0.8, r), (cx + r * 0.8, r)], (120, 122, 130), r * 0.1, z + 2, spin)]


def g_house(c, s, **_):
    w, h = 5.2 * s, 5.0 * s
    wall = c or (226, 196, 150)
    p = [rect("wall", -w / 2, 0, w / 2, h * 0.6, wall),
         poly("roof", [(-w * 0.58, h * 0.58), (w * 0.58, h * 0.58), (0, h)], (170, 70, 56), 1),
         rect("door", -w * 0.1, 0, w * 0.1, h * 0.36, (120, 80, 50), 2),
         rect("win_l", -w * 0.38, h * 0.26, -w * 0.2, h * 0.45, (170, 210, 236), 2),
         rect("win_r", w * 0.2, h * 0.26, w * 0.38, h * 0.45, (170, 210, 236), 2)]
    return _asset("house", "house", p, w * 1.16, h, uses=["stand_near", "enter"])


def g_shop(c, s, **_):
    w, h = 4.4 * s, 3.8 * s
    p = [rect("wall", -w / 2, 0, w / 2, h * 0.86, c or (236, 226, 200)),
         rect("board", -w / 2, h * 0.86, w / 2, h, (60, 110, 200), 1),
         poly("awning", [(-w / 2, h * 0.72), (w / 2, h * 0.72), (w * 0.56, h * 0.58), (-w * 0.56, h * 0.58)],
              (220, 80, 70), 2),
         rect("counter", -w * 0.42, 0, w * 0.42, h * 0.32, (150, 104, 66), 3)]
    return _asset("shop", "shop", p, w * 1.12, h, uses=["stand_near"])


def g_tower(c, s, **_):
    w, h = 5.0 * s, 16.0 * s
    p = [rect("body", -w / 2, 0, w / 2, h, c or (170, 178, 192))]
    rows, cols = 7, 3
    for r_ in range(rows):
        for k in range(cols):
            x0 = -w / 2 + w * (0.12 + 0.3 * k)
            y0 = h * (0.08 + 0.13 * r_)
            p.append(rect(f"win{r_}_{k}", x0, y0, x0 + w * 0.18, y0 + h * 0.07, (190, 220, 240), 1))
    return _asset("tower", "tower", p, w, h, uses=["background"])


def g_car(c, s, **_):
    L, r = 4.0 * s, 0.33 * s
    body = c or (204, 64, 58)
    p = [poly("body", [(-L / 2, r * 0.9), (L / 2, r * 0.9), (L / 2, r * 2.7), (L * 0.28, r * 2.9),
                       (-L * 0.42, r * 2.9), (-L / 2, r * 2.4)], body, 1),
         poly("cabin", [(-L * 0.3, r * 2.85), (L * 0.2, r * 2.85), (L * 0.08, r * 4.3), (-L * 0.22, r * 4.3)], body, 0),
         poly("glass", [(-L * 0.26, r * 2.95), (L * 0.15, r * 2.95), (L * 0.05, r * 4.05), (-L * 0.19, r * 4.05)],
              (176, 214, 236), 2)]
    p += _wheel("wheel_f", L * 0.3, r) + _wheel("wheel_r", -L * 0.3, r)
    return _asset("car", "car", p, L, r * 4.3, uses=["ride", "background"], mass=1200)


def g_bus(c, s, **_):
    L, r = 10.0 * s, 0.5 * s
    body = c or (240, 200, 60)
    p = [rect("body", -L / 2, r * 0.8, L / 2, r * 6.4, body, 1)]
    for k in range(6):
        x0 = -L / 2 + L * (0.06 + 0.15 * k)
        p.append(rect(f"win{k}", x0, r * 3.8, x0 + L * 0.11, r * 5.8, (176, 214, 236), 2))
    p.append(rect("door", L * 0.38, r * 1.0, L * 0.47, r * 5.6, (120, 160, 190), 2))
    p += _wheel("wheel_f", L * 0.32, r) + _wheel("wheel_r", -L * 0.3, r)
    return _asset("bus", "bus", p, L, r * 6.4, uses=["ride", "background"], mass=11000)


def g_bicycle(c, s, **_):
    r = 0.34 * s
    fr = c or (60, 110, 200)
    p = _wheel("wheel_r", -0.55 * s, r) + _wheel("wheel_f", 0.55 * s, r)
    p += [line("frame", [(-0.55 * s, r), (-0.1 * s, r * 2.6), (0.45 * s, r * 2.6), (0.55 * s, r)], fr, 0.05 * s, 6),
          line("down", [(-0.1 * s, r * 2.6), (0.05 * s, r), (-0.55 * s, r)], fr, 0.05 * s, 6),
          line("bar", [(0.45 * s, r * 2.6), (0.4 * s, r * 3.1), (0.25 * s, r * 3.1)], (50, 50, 56), 0.04 * s, 7),
          rect("seat", -0.22 * s, r * 2.7, 0.0, r * 2.9, (50, 50, 56), 7)]
    return _asset("bicycle", "bicycle", p, 1.8 * s, r * 3.1, uses=["ride", "carry"], mass=12)


def g_tree(c, s, **_):
    h = 5.0 * s
    leaf = c or (70, 150, 80)
    sway = {"type": "sway", "pivot": [0, h * 0.4], "amp": 0.03, "rate": 0.5}
    p = [poly("trunk", [(-h * 0.05, 0), (h * 0.05, 0), (h * 0.035, h * 0.55), (-h * 0.035, h * 0.55)], (120, 84, 54))]
    for i, (dx, dy, rr) in enumerate([(0, 0.72, 0.26), (-0.17, 0.6, 0.18), (0.17, 0.62, 0.19), (0.02, 0.86, 0.17)]):
        p.append(circle(f"canopy{i}", dx * h, dy * h, rr * h, leaf, 1 + i, sway))
    return _asset("tree", "tree", p, h * 0.72, h * 1.03, uses=["background", "stand_near"])


def g_bush(c, s, **_):
    h = 0.9 * s
    leaf = c or (80, 160, 90)
    p = [circle(f"b{i}", dx * h, h * 0.42, h * 0.42, leaf, i) for i, dx in enumerate((-0.45, 0.0, 0.45))]
    return _asset("bush", "bush", p, h * 1.74, h * 0.84, uses=["background"])


def _quadruped(kind, c, s, body_l, body_h, leg, head_r, tail, colour):
    col = c or colour
    hip_y = leg
    legs = []
    for i, (lx, ph) in enumerate([(body_l * 0.36, 0.0), (body_l * 0.3, math.pi), (-body_l * 0.32, math.pi),
                                  (-body_l * 0.38, 0.0)]):
        rig = {"type": "swing", "pivot": [lx, hip_y], "amp": 0.45, "stride": leg * 1.6, "phase": ph, "gait": True}
        legs.append(rect(f"leg{i}", lx - leg * 0.09, 0, lx + leg * 0.09, hip_y + body_h * 0.2,
                         darker(col, 0.85) if i in (1, 2) else col, 0 if i in (1, 2) else 3, rig))
    hx, hy = body_l * 0.55, hip_y + body_h * 0.9
    p = legs + [poly("body", ellipse_pts(0, hip_y + body_h / 2, body_l / 2, body_h / 2), col, 2),
                circle("head", hx, hy, head_r, col, 4),
                circle("eye", hx + head_r * 0.35, hy + head_r * 0.2, head_r * 0.13, (30, 30, 34), 5)]
    if tail:
        p.append(line("tail", [(-body_l / 2, hip_y + body_h * 0.7), (-body_l / 2 - tail, hip_y + body_h * 1.1)],
                      darker(col), max(0.015, body_h * 0.1), 1,
                      {"type": "swing", "pivot": [-body_l / 2, hip_y + body_h * 0.7], "amp": 0.35, "rate": 1.6}))
    return _asset(kind, kind, p, body_l + 2 * max(head_r, tail or 0) + head_r, hy + head_r, uses=["walk"],
                  stride=leg * 1.6)


def g_dog(c, s, **_):
    return _quadruped("dog", c, s, 0.7 * s, 0.28 * s, 0.32 * s, 0.13 * s, 0.22 * s, (190, 140, 90))


def g_cat(c, s, **_):
    return _quadruped("cat", c, s, 0.36 * s, 0.14 * s, 0.14 * s, 0.075 * s, 0.24 * s, (120, 120, 128))


def g_cow(c, s, **_):
    return _quadruped("cow", c, s, 1.9 * s, 0.75 * s, 0.7 * s, 0.26 * s, 0.4 * s, (236, 236, 228))


def g_horse(c, s, **_):
    return _quadruped("horse", c, s, 1.8 * s, 0.6 * s, 0.85 * s, 0.24 * s, 0.5 * s, (140, 96, 60))


def g_bird(c, s, **_):
    col = c or (60, 60, 70)
    r = 0.09 * s
    p = [poly("body", ellipse_pts(0, r * 2, r * 1.5, r), col, 1), circle("head", r * 1.5, r * 2.7, r * 0.6, col, 2),
         poly("beak", [(r * 2.0, r * 2.8), (r * 2.6, r * 2.65), (r * 2.0, r * 2.5)], (236, 160, 50), 3),
         poly("wing", [(-r * 0.4, r * 2.2), (r * 0.6, r * 2.2), (-r * 0.6, r * 3.8)], darker(col, 0.8), 4,
              {"type": "flap", "pivot": [0.0, r * 2.2], "amp": 0.8, "rate": 6.0}),
         line("legs", [(-r * 0.2, 0), (0, r * 1.1), (r * 0.2, 0)], (200, 140, 60), r * 0.15, 0)]
    return _asset("bird", "bird", p, r * 5.4, r * 3.8, uses=["background"])


def g_boat(c, s, **_):
    L = 2.6 * s
    col = c or (150, 96, 60)
    p = [poly("hull", [(-L / 2, L * 0.16), (L / 2, L * 0.16), (L * 0.36, 0), (-L * 0.36, 0)], col, 1,
              {"type": "bob", "amp": 0.03 * s, "rate": 0.7})]
    return _asset("boat", "boat", p, L, L * 0.16, uses=["ride"], grounded=True)


def g_lamp(c, s, **_):
    h = 4.0 * s
    p = [rect("base", -0.16 * s, 0, 0.16 * s, 0.12 * s, (60, 62, 70)),
         rect("post", -0.05 * s, 0.12 * s, 0.05 * s, h * 0.95, c or (70, 72, 82), 1),
         poly("head", [(-0.25 * s, h * 0.92), (0.25 * s, h * 0.92), (0.12 * s, h), (-0.12 * s, h)], (60, 62, 70), 2),
         circle("light", 0, h * 0.9, 0.11 * s, (255, 226, 140), 3)]
    return _asset("lamp", "lamp", p, 0.5 * s, h, uses=["background", "stand_near"])


def g_chair(c, s, **_):
    col = c or (150, 98, 60)
    p = [rect("seat", -0.22 * s, 0.42 * s, 0.22 * s, 0.47 * s, col, 1),
         rect("leg_f", 0.16 * s, 0, 0.21 * s, 0.42 * s, darker(col, 0.8)),
         rect("leg_b", -0.21 * s, 0, -0.16 * s, 0.42 * s, darker(col, 0.8)),
         rect("back", -0.22 * s, 0.47 * s, -0.16 * s, 0.92 * s, col, 1)]
    return _asset("chair", "chair", p, 0.44 * s, 0.92 * s, uses=["sit", "carry"], seat=round(0.47 * s, 3), mass=5)


def g_table(c, s, **_):
    col = c or (160, 110, 70)
    w = 1.4 * s
    p = [rect("top", -w / 2, 0.72 * s, w / 2, 0.78 * s, col, 1),
         rect("leg_l", -w * 0.44, 0, -w * 0.4, 0.72 * s, darker(col, 0.8)),
         rect("leg_r", w * 0.4, 0, w * 0.44, 0.72 * s, darker(col, 0.8))]
    return _asset("table", "table", p, w, 0.78 * s, uses=["stand_on", "put_on"], top=round(0.78 * s, 3), mass=25)


def g_rock(c, s, **_):
    r = 0.4 * s
    pts = [(-r, 0), (r, 0), (r * 0.9, r * 0.5), (r * 0.4, r * 0.85), (-r * 0.3, r * 0.8), (-r * 0.85, r * 0.45)]
    return _asset("rock", "rock", [poly("rock", pts, c or (150, 146, 140))], 2 * r, r * 0.85,
                  uses=["stand_on", "sit"], top=round(r * 0.8, 3), seat=round(r * 0.8, 3), mass=round(600 * r ** 3))


def g_sign(c, s, text="", **_):
    h = 2.0 * s
    p = [rect("post", -0.04 * s, 0, 0.04 * s, h * 0.7, (110, 80, 50)),
         rect("board", -0.6 * s, h * 0.62, 0.6 * s, h, c or (236, 230, 210), 1)]
    return _asset("sign", "sign", p, 1.2 * s, h, uses=["background"], text=text)


GENERATORS = {k[2:]: v for k, v in globals().items() if k.startswith("g_")}


def parse(description: str) -> dict:
    """'a small red car', 'two tall trees', 'a puppy' -> {kind, colour, scale, text}."""
    low = description.lower()
    words = re.findall(r"[a-z]+", low)
    kind = next((w for w in words if w in GENERATORS), None) or \
        next((SYNONYMS[w] for w in words if w in SYNONYMS), None) or \
        next((SYNONYMS.get(w[:-1], w[:-1]) for w in words if w.endswith("s") and
              (w[:-1] in GENERATORS or w[:-1] in SYNONYMS)), None)
    colour = next((COLOURS[w] for w in words if w in COLOURS), None)
    scale = 1.0
    for w, k in (("tiny", 0.5), ("small", 0.75), ("little", 0.75), ("big", 1.3), ("large", 1.3), ("tall", 1.4),
                 ("huge", 1.8), ("giant", 2.2)):
        if w in words:
            scale = k
    if kind in ("puppy", "kitten") or "puppy" in words or "kitten" in words:
        scale *= 0.6
    text = re.search(r"['\"]([^'\"]+)['\"]", description)
    return {"kind": kind, "colour": colour, "scale": scale, "text": text.group(1) if text else ""}


def generate(description: str) -> dict:
    """A new asset from a short description. Raises ValueError for something no generator can build (the caller
    then falls back to a labelled placeholder rather than inventing a shape)."""
    q = parse(description)
    if not q["kind"]:
        raise ValueError(f"no generator for {description!r} (known: {', '.join(sorted(GENERATORS))})")
    a = GENERATORS[q["kind"]](q["colour"], q["scale"], text=q["text"])
    a["name"] = description.strip()
    a["source"] = "procedural:" + q["kind"]
    return a


def placeholder(description: str, w=0.8, h=0.8) -> dict:
    """An honest stand-in for something we cannot generate: a labelled box."""
    a = _asset("placeholder", description, [rect("box", -w / 2, 0, w / 2, h, (226, 226, 232))], w, h,
               text=description, uses=["background"])
    a["source"] = "placeholder"
    return a


# ---- the rig at time t --------------------------------------------------------------------------------------------------
def _rot(pt, piv, ang):
    c, s = math.cos(ang), math.sin(ang)
    x, y = pt[0] - piv[0], pt[1] - piv[1]
    return (piv[0] + c * x - s * y, piv[1] + s * x + c * y)


def rig_angle(part: dict, t: float, dist: float, speed: float) -> tuple[float, float]:
    """(rotation in radians, vertical offset) of a part at time t, having travelled `dist` metres at `speed`."""
    rig = part.get("rig")
    if not rig:
        return 0.0, 0.0
    k = rig["type"]
    if k == "spin":
        r = part["r"] if part["shape"] == "circle" else rig["pivot"][1]
        return -dist / max(r, 1e-3), 0.0                      # rolling: no skid
    if k == "swing" and rig.get("gait"):
        on = min(1.0, abs(speed) / 0.4)
        return rig["amp"] * on * math.sin(2 * math.pi * abs(dist) / rig["stride"] + rig.get("phase", 0.0)), 0.0
    if k in ("swing", "sway", "flap"):
        return rig["amp"] * math.sin(2 * math.pi * rig.get("rate", 1.0) * t + rig.get("phase", 0.0)), 0.0
    if k == "bob":
        return 0.02 * math.sin(2 * math.pi * rig["rate"] * t * 0.7), rig["amp"] * math.sin(2 * math.pi * rig["rate"] * t)
    return 0.0, 0.0


def posed(asset: dict, t: float = 0.0, dist: float = 0.0, speed: float = 0.0, flip: float = 1.0) -> list[dict]:
    """The parts at time t in asset coordinates (rigs applied, mirrored if flip < 0), sorted by draw order."""
    out = []
    for part in sorted(asset["parts"], key=lambda p: p.get("z", 0)):
        ang, dy = rig_angle(part, t, dist * flip, speed)
        piv = part.get("rig", {}).get("pivot", [0.0, 0.0])
        q = dict(part)
        if part["shape"] == "circle":
            cx, cy = _rot(part["c"], piv, ang)
            q["c"] = [flip * cx, cy + dy]
            q["ang"] = ang * flip
        else:
            q["pts"] = [[flip * x, y + dy] for x, y in (_rot(p, piv, ang) for p in part["pts"])]
        out.append(q)
    return out


# ---- validation ---------------------------------------------------------------------------------------------------------
@dataclass
class Issue:
    check: str
    part: str
    detail: str
    severity: str = "error"


def _area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _segments_cross(p1, p2, p3, p4):
    d1, d2 = _cross(p3, p4, p1), _cross(p3, p4, p2)
    d3, d4 = _cross(p1, p2, p3), _cross(p1, p2, p4)
    return d1 * d2 < -1e-12 and d3 * d4 < -1e-12


def self_intersects(pts) -> bool:
    n = len(pts)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _segments_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                return True
    return False


def bbox(part: dict, pad: float = 0.0):
    if part["shape"] == "circle":
        (cx, cy), r = part["c"], part["r"]
        return cx - r - pad, cy - r - pad, cx + r + pad, cy + r + pad
    xs, ys = [p[0] for p in part["pts"]], [p[1] for p in part["pts"]]
    w = part.get("width", 0) / 2
    return min(xs) - w - pad, min(ys) - w - pad, max(xs) + w + pad, max(ys) + w + pad


def _touch(a, b, tol):
    return a[0] <= b[2] + tol and b[0] <= a[2] + tol and a[1] <= b[3] + tol and b[1] <= a[3] + tol


def _lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def contrast(a, b) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def validate(asset: dict, paper=PAPER, render_test: bool = True) -> list[Issue]:
    out = []
    parts = asset.get("parts", [])
    if not parts:
        return [Issue("empty", "", "no parts")]
    W, H = asset["w"], asset["h"]
    tol = 0.02 * max(W, H)
    ids = [p["id"] for p in parts]
    for dup in {i for i in ids if ids.count(i) > 1}:
        out.append(Issue("duplicate_id", dup, "two parts share an id"))
    for p in parts:
        s = p["shape"]
        if s == "poly":
            if len(p["pts"]) < 3:
                out.append(Issue("degenerate", p["id"], "a polygon needs three points"))
                continue
            if abs(_area(p["pts"])) < 1e-6:
                out.append(Issue("degenerate", p["id"], "zero area"))
            if self_intersects(p["pts"]):
                out.append(Issue("self_intersection", p["id"], "the outline crosses itself"))
        elif s == "circle" and p["r"] <= 0:
            out.append(Issue("degenerate", p["id"], "radius must be positive"))
        elif s == "line" and (len(p["pts"]) < 2 or p.get("width", 0) <= 0):
            out.append(Issue("degenerate", p["id"], "a line needs two points and a width"))
        x0, y0, x1, y1 = bbox(p)
        if x0 < -W / 2 - tol or x1 > W / 2 + tol or y0 < -tol or y1 > H + tol:
            out.append(Issue("out_of_bounds", p["id"], f"part spans x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}; "
                             f"asset is {W:.2f} x {H:.2f}"))
        rig = p.get("rig")
        if rig:
            piv = rig.get("pivot")
            if rig["type"] != "bob":                  # the joint is on the part, or where it attaches to another
                pt = (piv[0], piv[1], piv[0], piv[1]) if piv else None
                on = pt and (_touch(bbox(p, tol), pt, 0) or any(
                    _touch(bbox(q, tol), pt, 0) and _touch(bbox(q), bbox(p), tol) for q in parts if q is not p))
                if not on:
                    out.append(Issue("pivot_outside", p["id"], f"pivot {piv} is not on the part or its attachment"))
            if rig["type"] == "spin":
                c = p["c"] if s == "circle" else None
                if c and math.dist(c, piv) > 1e-3:
                    out.append(Issue("wobble", p["id"], "a spinning circle must spin about its own centre"))
            if rig["type"] in ("swing", "sway", "flap") and asset.get("grounded", True):
                for ang in (-rig["amp"], -rig["amp"] / 2, rig["amp"] / 2, rig["amp"]):
                    pts = [p["c"]] if s == "circle" else p["pts"]
                    low = min(_rot(q, piv, ang)[1] for q in pts) - (p["r"] if s == "circle" else 0)
                    if low < -tol:
                        out.append(Issue("swings_through_floor", p["id"], f"reaches y={low:.2f} at {ang:+.2f} rad"))
                        break
    # floating parts: every part must touch another unless declared loose
    if len(parts) > 1:
        boxes = {p["id"]: bbox(p) for p in parts}
        for p in parts:
            if p["id"] in asset.get("loose", []):
                continue
            if not any(_touch(boxes[p["id"]], boxes[q["id"]], tol) for q in parts if q is not p):
                out.append(Issue("floating_part", p["id"], "does not touch any other part"))
    if asset.get("grounded", True):
        low = min(bbox(p)[1] for p in parts)
        if low > tol:
            out.append(Issue("no_ground_contact", "", f"lowest point is {low:.2f} m above the ground"))
    rng = SIZES.get(asset["kind"])
    if rng and not (rng[0] * 0.8 <= H <= rng[1] * 1.25):
        out.append(Issue("implausible_size", "", f"a {asset['kind']} {H:.2f} m tall next to a {PERSON_H} m person "
                         f"(expected {rng[0]}-{rng[1]} m)", "warn"))
    big = max(parts, key=lambda p: abs(_area(p["pts"])) if p["shape"] == "poly" else math.pi * p.get("r", 0) ** 2)
    if contrast(big["fill"], paper) < 1.25 and contrast(big.get("line", big["fill"]), paper) < 1.8:
        out.append(Issue("low_contrast", big["id"], "the main shape barely shows against the background", "warn"))
    if render_test:
        ink = render_png(asset, None, 160)
        if ink < 0.01:
            out.append(Issue("render_empty", "", f"test render covers {ink:.1%} of the canvas"))
    return out


def errors(issues) -> list:
    return [i for i in issues if i.severity == "error"]


# ---- compatibility ------------------------------------------------------------------------------------------------------
def compatible(asset: dict, use: str) -> tuple[bool, list[str]]:
    why = []
    rigs = [p.get("rig", {}).get("type") for p in asset["parts"]]
    if use == "carry":
        if asset.get("mass", 50) > 25:
            why.append(f"too heavy to carry ({asset.get('mass', '?')} kg)")
        if asset["w"] > 1.9 or asset["h"] > 1.2:
            why.append(f"too big to carry ({asset['w']:.1f} x {asset['h']:.1f} m)")
    elif use == "sit":
        seat = asset.get("seat")
        if seat is None or not 0.25 <= seat <= 0.65:
            why.append("no seat at a sitting height (0.25-0.65 m)")
    elif use in ("stand_on", "put_on"):
        top = asset.get("top")
        if top is None:
            why.append("no flat top")
        elif use == "stand_on" and top > 1.2:
            why.append(f"top at {top:.2f} m is too high to step onto")
    elif use == "ride":
        if "spin" not in rigs and asset["kind"] != "boat":
            why.append("no wheels")
    elif use == "walk":
        legs = [p for p in asset["parts"] if p.get("rig", {}).get("gait")]
        if len(legs) < 2:
            why.append("needs at least two rigged legs")
        elif not all(bbox(p)[1] <= 0.02 * asset["h"] for p in legs):
            why.append("legs do not reach the ground")
    elif use == "3d":
        try:
            m = to_mesh(asset)
            if m["open_edges"]:
                why.append(f"mesh has {m['open_edges']} open edges")
        except ValueError as e:
            why.append(str(e))
    elif use != "background":
        why.append(f"unknown use {use!r}")
    if use not in ("3d", "background") and use not in asset.get("uses", []) and not why:
        why.append(f"not designed for {use} (designed for: {', '.join(asset.get('uses', [])) or 'nothing'})")
    return not why, why


# ---- 3D -----------------------------------------------------------------------------------------------------------------
def to_mesh(asset: dict, depth: float | None = None) -> dict:
    """Extrudes every part into a closed prism (lines become thin boxes); depth layers follow draw order so parts
    don't z-fight. Returns {"verts", "faces", "open_edges", "parts"}. A mesh is valid when every edge is shared by
    exactly two faces."""
    depth = depth or max(0.05, min(asset["w"], asset["h"]) * 0.35)
    verts, faces, names = [], [], []
    for p in sorted(asset["parts"], key=lambda q: q.get("z", 0)):
        if p["shape"] == "circle":
            pts = ellipse_pts(p["c"][0], p["c"][1], p["r"], p["r"], 20)
        elif p["shape"] == "poly":
            pts = [tuple(q) for q in p["pts"]]
        elif p["shape"] == "line":
            (ax, ay), (bx, by) = p["pts"][0], p["pts"][-1]
            n = math.hypot(bx - ax, by - ay) or 1
            nx, ny = -(by - ay) / n * p["width"] / 2, (bx - ax) / n * p["width"] / 2
            pts = [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)]
        else:
            raise ValueError(f"cannot extrude a {p['shape']} part")
        if len(pts) < 3 or abs(_area(pts)) < 1e-9:
            raise ValueError(f"part {p['id']} is degenerate")
        if _area(pts) < 0:
            pts = pts[::-1]
        d = depth * (1 - 0.04 * p.get("z", 0))
        base = len(verts)
        n = len(pts)
        verts += [(x, -d / 2, y) for x, y in pts] + [(x, d / 2, y) for x, y in pts]
        faces.append(tuple(base + i for i in range(n)))                       # front
        faces.append(tuple(base + n + i for i in reversed(range(n))))         # back
        for i in range(n):
            j = (i + 1) % n
            faces.append((base + i, base + n + i, base + n + j, base + j))
        names.append(p["id"])
    edges = {}
    for f in faces:
        for i in range(len(f)):
            e = tuple(sorted((f[i], f[(i + 1) % len(f)])))
            edges[e] = edges.get(e, 0) + 1
    return {"verts": verts, "faces": faces, "open_edges": sum(1 for c in edges.values() if c != 2), "parts": names}


def write_obj(asset: dict, path: Path) -> Path:
    m = to_mesh(asset)
    lines = [f"# {asset['name']} ({asset['kind']}) - extruded by CreatorForge"]
    lines += [f"v {x:.4f} {y:.4f} {z:.4f}" for x, y, z in m["verts"]]
    lines += ["f " + " ".join(str(i + 1) for i in f) for f in m["faces"]]
    Path(path).write_text("\n".join(lines) + "\n")
    return Path(path)


# ---- images -------------------------------------------------------------------------------------------------------------
def import_image(path: str | Path, kind: str = "image", height: float = 1.0) -> dict:
    """A picture as an asset. It is checked (it opens, it has a transparent background or is flagged), but it is
    one rigid piece: it can slide, scale and turn as a whole and nothing more."""
    from PIL import Image
    im = Image.open(path)
    im.load()
    w = height * im.width / im.height
    notes = ["single image: no separable parts, no pivots, no depth - not animation-ready; it moves only as a whole"]
    alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    if alpha:
        a = im.convert("RGBA").getchannel("A")
        clear = sum(1 for v in a.getdata() if v < 16) / (im.width * im.height)
        if clear < 0.05:
            notes.append("has an alpha channel but almost nothing is transparent: shows as a rectangle")
    else:
        notes.append("no transparency: shows as a rectangle with its background")
    return {"kind": kind, "name": Path(path).stem, "w": round(w, 3), "h": height, "image": str(path),
            "parts": [{"id": "image", "shape": "poly", "pts": [[-w / 2, 0], [w / 2, 0], [w / 2, height], [-w / 2, height]],
                       "fill": [200, 200, 200], "line": [120, 120, 120], "z": 0}],
            "grounded": True, "animation_ready": False, "notes": notes, "source": "image:" + Path(path).name,
            "uses": ["background"]}


# ---- drawing -------------------------------------------------------------------------------------------------------------
def draw_parts(d, parts, S, scale, ox, oy):
    """Draws posed parts onto a PIL ImageDraw; S maps world metres to pixels; (ox, oy) is the asset's bottom centre."""
    lw = max(1, int(scale * 0.018))
    for p in parts:
        fill, ln = tuple(p["fill"]), tuple(p.get("line", p["fill"]))
        if p["shape"] == "circle":
            cx, cy = S(ox + p["c"][0], oy + p["c"][1])
            r = p["r"] * scale
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=ln, width=lw)
        elif p["shape"] == "line":
            d.line([S(ox + x, oy + y) for x, y in p["pts"]], fill=fill, width=max(1, int(p["width"] * scale)),
                   joint="curve")
        else:
            d.polygon([S(ox + x, oy + y) for x, y in p["pts"]], fill=fill, outline=ln, width=lw)


def render_png(asset: dict, out: Path | None = None, px: int = 320, t: float = 0.0, dist: float = 0.0,
               speed: float = 0.0) -> float:
    """Renders the asset alone (a thumbnail, and the render test). Returns the fraction of the canvas inked."""
    from PIL import Image, ImageDraw
    W, H = asset["w"], asset["h"]
    scale = px * 0.86 / max(W, H)
    img = Image.new("RGB", (px, px), PAPER)
    d = ImageDraw.Draw(img)
    gy = px * 0.93

    def S(x, y):
        return px / 2 + x * scale, gy - y * scale
    if asset.get("image") and Path(asset["image"]).exists():
        pic = Image.open(asset["image"]).convert("RGBA").resize((max(1, int(W * scale)), max(1, int(H * scale))))
        img.paste(pic, (int(px / 2 - W * scale / 2), int(gy - H * scale)), pic)
    else:
        draw_parts(d, posed(asset, t, dist, speed), S, scale, 0.0, 0.0)
    if out:
        img.save(out)
    bg = PAPER
    data = img.getdata()
    return sum(1 for c in data if abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2]) > 24) / len(data)


# ---- the library --------------------------------------------------------------------------------------------------------
def asset_id(asset: dict) -> str:
    body = json.dumps({k: v for k, v in asset.items() if k not in ("id", "registered")}, sort_keys=True)
    return f"{asset['kind']}-" + hashlib.sha256(body.encode()).hexdigest()[:10]


class Library:
    """A registry of validated assets. root=None keeps it in memory."""
    STOCK = ["house", "shop", "tower", "car", "bus", "bicycle", "tree", "bush", "dog", "cat", "cow", "horse", "bird",
             "boat", "lamp", "chair", "table", "rock", "sign"]
    _default = None

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else None
        self.items: dict[str, dict] = {}
        if self.root and (self.root / "index.json").exists():
            for aid in json.loads((self.root / "index.json").read_text()):
                self.items[aid] = json.loads((self.root / f"{aid}.json").read_text())

    @classmethod
    def default(cls) -> "Library":
        """The stock library (every generator at its default size) plus anything registered under $CF_ASSET_LIB."""
        if cls._default is None:
            lib = cls(os.environ.get("CF_ASSET_LIB") or None)
            for k in cls.STOCK:
                a = GENERATORS[k](None, 1.0)
                a["source"] = "procedural:" + k
                lib.register(a, render_test=False, aid=k)
            cls._default = lib
        return cls._default

    def register(self, asset: dict, render_test: bool = True, aid: str | None = None) -> str:
        """Validates and stores an asset; refuses one with errors (raises ValueError listing them)."""
        issues = validate(asset, render_test=render_test)
        bad = errors(issues)
        if bad:
            raise ValueError("asset failed validation: " + "; ".join(f"{i.check} {i.part} {i.detail}" for i in bad))
        a = copy.deepcopy(asset)
        a["id"] = aid or asset_id(a)
        a["warnings"] = [asdict(i) for i in issues]
        self.items[a["id"]] = a
        if self.root and aid is None:
            self.root.mkdir(parents=True, exist_ok=True)
            (self.root / f"{a['id']}.json").write_text(json.dumps(a, indent=1))
            ids = [k for k, v in self.items.items() if (self.root / f"{k}.json").exists()]
            (self.root / "index.json").write_text(json.dumps(sorted(ids)))
        return a["id"]

    def get(self, aid: str) -> dict:
        if aid not in self.items:
            raise KeyError(f"no asset {aid!r}")
        return self.items[aid]

    def find(self, kind: str | None = None, use: str | None = None) -> list[dict]:
        return [a for a in self.items.values() if (kind is None or a["kind"] == kind) and
                (use is None or compatible(a, use)[0])]

    def obtain(self, description: str) -> tuple[str, str]:
        """An asset for a description: an exact stock kind, else a newly generated (and registered) one, else a
        labelled placeholder. Returns (id, how)."""
        q = parse(description)
        if q["kind"] and q["colour"] is None and q["scale"] == 1.0 and q["kind"] in self.items:
            return q["kind"], "library"
        try:
            return self.register(generate(description)), "generated"
        except ValueError:
            return self.register(placeholder(description), render_test=False), "placeholder"

    def prop_spec(self, aid: str) -> dict:
        """What a scene needs to place it: a 'shape' prop whose data carries the parts."""
        a = self.get(aid)
        spec = {"kind": "shape", "w": a["w"], "h": a["h"],
                "data": {"asset": aid, "parts": a["parts"], "image": a.get("image"), "text": a.get("text", "")}}
        return spec
