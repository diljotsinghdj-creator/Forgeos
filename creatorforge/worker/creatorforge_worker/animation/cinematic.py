"""Production styles: how the same staged scene is drawn - stickman, cartoon, graphic novel, motion comic, noir with
selective colour, anime-inspired, explainer or soft "painterly" - one engine, one skeleton, many looks.

A style changes the drawing, never the animation: every character is still posed by the stick engine (bones, IK,
physics, expressions, lip sync), so all motion, continuity and QC work in every style, and styles can change from
scene to scene in one production.

    style = cinematic.get("graphic_novel", stylization=0.8, overrides={"key_hue": 0})

* bodies       "stick" (lines), "volume" (illustrated: tapered limbs, torso, clothes, hands, shoes, hair and a face
               on every head) or species variants on the same skeleton: robot, alien, monster.
* shading      per character: a cel shadow on the side away from the key light, a rim light on the lit edge, and
               halftone dots in the shadow when stylised.
* ink          outlines on the characters, and inked edges on the whole picture (backgrounds included).
* grade        contrast, saturation, split toning (cool shadows, warm highlights), posterised tones, film grain,
               vignette, letterbox bars, and selective colour: the picture in black and white except one hue.
* comic FX     impact bursts, sound-effect lettering, speed lines, narration caption boxes, panel borders; speed
               lines are added automatically behind anyone moving fast.

`stylization` (0..1) runs from realistic-leaning (soft shading, no posterising, light ink) to fully stylised (hard
cel shadows, halftone, heavy ink, few tones). Every field can be overridden in the production document."""
from __future__ import annotations

import colorsys
import math
import zlib
from dataclasses import dataclass, field, replace

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


@dataclass
class Style:
    name: str = "stick"
    body: str = "stick"            # stick | volume
    stylization: float = 0.7       # 0 realistic-leaning .. 1 fully stylised
    outline: float = 1.0           # character ink weight (x the base)
    shade: float = 0.0             # strength of the cel shadow on characters (0 = none)
    rim: float = 0.0               # rim light on the lit edge
    halftone: float = 0.0          # dots in the character shadows
    light: tuple = (-0.6, -1.0)    # direction toward the key light (screen x, y; y up is negative)
    shadow_tint: tuple = (40, 50, 90)
    ink_edges: float = 0.0         # inked edges over the whole picture
    posterize: int = 0             # tones per channel (0 = off)
    contrast: float = 1.0
    saturation: float = 1.0
    split: float = 0.0             # cool shadows / warm highlights
    key_hue: float | None = None   # selective colour: the hue kept (degrees); everything else goes grey
    key_tol: float = 22.0
    grain: float = 0.0
    vignette: float = 0.0
    letterbox: float = 0.0         # target aspect for bars (2.39), 0 = none
    panel: bool = False            # motion-comic panel border and gutter
    speedlines: bool = False       # automatic speed lines behind fast movers
    paper: float = 0.0             # paper texture strength
    font: str = FONT
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in self.__dataclass_fields__ if k != "extra"}
        d["extra"] = dict(self.extra)
        return d


PRESETS: dict[str, dict] = {
    "stick": {},
    "cartoon": dict(body="volume", outline=1.25, shade=0.35, rim=0.0, saturation=1.2, contrast=1.05),
    "western": dict(body="volume", outline=1.4, shade=0.3, saturation=1.25, contrast=1.08, speedlines=True),
    "graphic_novel": dict(body="volume", outline=1.3, shade=0.8, rim=0.5, halftone=0.7, ink_edges=0.75, posterize=9,
                          contrast=1.22, saturation=0.82, split=0.35, grain=0.018, vignette=0.45, letterbox=2.0,
                          paper=0.25, font=SERIF),
    "motion_comic": dict(body="volume", outline=1.35, shade=0.75, rim=0.4, halftone=0.85, ink_edges=0.7, posterize=8,
                         contrast=1.15, saturation=0.95, split=0.2, grain=0.012, vignette=0.2, panel=True,
                         speedlines=True, paper=0.35, font=SERIF),
    "noir": dict(body="volume", outline=1.3, shade=0.9, rim=0.7, halftone=0.6, ink_edges=0.85, posterize=7,
                 contrast=1.4, saturation=1.0, key_hue=0.0, grain=0.03, vignette=0.65, letterbox=2.39, font=SERIF),
    "anime": dict(body="volume", outline=0.75, shade=0.7, rim=0.6, halftone=0.0, ink_edges=0.25, posterize=0,
                  contrast=1.08, saturation=1.25, split=0.15, speedlines=True, vignette=0.15),
    "explainer": dict(body="volume", outline=0.9, shade=0.2, saturation=1.05, contrast=1.0),
    "painterly": dict(body="volume", outline=0.45, shade=0.45, rim=0.3, ink_edges=0.0, contrast=1.06,
                      saturation=0.92, split=0.25, grain=0.01, vignette=0.35),
}
# what the slider changes: a value at stylization 0 and at 1 (the preset's own value is the 0.7 point)
SLIDER = {"outline": (0.45, 1.25), "halftone": (0.0, 1.25), "ink_edges": (0.15, 1.2), "posterize_scale": (0.0, 1.0)}


def get(name: str = "stick", stylization: float | None = None, overrides: dict | None = None) -> Style:
    """A style by preset name, at a stylization level, with any field overridden."""
    base = PRESETS.get(name)
    if base is None:
        raise ValueError(f"unknown style {name!r}; choose from {sorted(PRESETS)}")
    st = Style(name=name, **base)
    if stylization is not None:
        s = max(0.0, min(1.0, float(stylization)))
        k = s / 0.7                                  # 1.0 at the preset's own level
        st = replace(st, stylization=s, outline=st.outline * (0.55 + 0.45 * k), halftone=min(1.0, st.halftone * k),
                     ink_edges=min(1.0, st.ink_edges * k), shade=min(1.0, st.shade * (0.6 + 0.4 * k)),
                     posterize=(0 if s < 0.35 else max(5, int(round(st.posterize * (1.6 - 0.6 * k)))))
                     if st.posterize else 0,
                     grain=st.grain * k, paper=st.paper * k)
    for k_, v in (overrides or {}).items():
        if k_ in Style.__dataclass_fields__:
            st = replace(st, **{k_: tuple(v) if isinstance(v, list) else v})
        else:
            st.extra[k_] = v
    return st


def from_doc(spec) -> Style | None:
    """A production document's "style" field: a preset name or {"name", "stylization", ...overrides}."""
    if not spec:
        return None
    if isinstance(spec, str):
        return None if spec == "stick" else get(spec)
    spec = dict(spec)
    name = spec.pop("name", "graphic_novel")
    if name == "stick" and not spec:
        return None
    return get(name, spec.pop("stylization", None), spec)


# ---- illustrated bodies on the stick skeleton --------------------------------------------------------------------
SKINS = [(241, 204, 170), (224, 172, 128), (198, 140, 98), (160, 104, 70), (118, 76, 52), (250, 220, 196)]
OUTFITS = [(70, 92, 140), (150, 60, 58), (64, 120, 92), (190, 150, 70), (96, 72, 130), (60, 60, 66), (180, 96, 60)]


def _h(name: str) -> int:
    return zlib.crc32(name.encode())


def palette(look):
    """(skin, outfit, trousers, shoes, ink) for a look; a stick look's white head becomes a skin tone."""
    h = _h(look.name or "x")
    skin = tuple(look.skin[:3])
    if skin == (255, 255, 255):
        skin = SKINS[h % len(SKINS)]
    outfit = getattr(look, "shirt", None) or (look.body if look.body and sum(look.body) > 90 else None) \
        or OUTFITS[(h // 7) % len(OUTFITS)]
    pants = getattr(look, "pants", None) or tuple(int(c * 0.55) for c in outfit)
    shoes = getattr(look, "shoes", None) or (38, 32, 30)
    return skin, tuple(outfit), tuple(pants), tuple(shoes), look.ink


def _capsule(d, a, b, w0, w1, fill):
    """A tapered limb from a (width w0) to b (width w1), rounded ends; screen pixels."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    d.polygon([(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
               (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)], fill=fill)
    for (x, y), w in ((a, w0), (b, w1)):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)


def _chain(d, pts, widths, fill, ink, o):
    """A limb as joined capsules with an ink outline o pixels wide (ink pass first, then the fill)."""
    for i in range(len(pts) - 1):
        _capsule(d, pts[i], pts[i + 1], widths[i] + 2 * o, widths[i + 1] + 2 * o, ink)
    for i in range(len(pts) - 1):
        _capsule(d, pts[i], pts[i + 1], widths[i], widths[i + 1], fill)


def _poly(d, pts, fill, ink, o):
    if o > 0:
        d.polygon(pts, fill=ink)
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        inner = []
        for x, y in pts:                              # an inset copy: the ink shows as an even outline
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1
            inner.append((x - dx / L * o, y - dy / L * o))
        d.polygon(inner, fill=fill)
    else:
        d.polygon(pts, fill=fill)


def draw_figure(actor, d, S, scale, t, style: Style):
    """Draws an Actor's body in the illustrated ("volume") style from its joints; returns (cx, cy, r, ink) for the
    symbols and speech bubbles drawn on top."""
    from . import face as F
    from . import rig2d
    p = actor.pose_now
    J = actor.joints(p)
    L = actor.look
    H = actor.H
    f = J["f"]
    species = getattr(L, "species", "human") or "human"
    skin, outfit, pants, shoes, ink = palette(L)
    girth = getattr(L, "girth", 1.0) or 1.0
    thin = 0.62 if species == "alien" else 1.0
    o = max(1.0, scale * 0.0045 * H * style.outline)
    far = (lambda c: tuple(int(v * 0.72 + 30 * 0.28) for v in c))
    pt = lambda q: S(*q)
    u = scale * H                                   # pixels per body height

    def leg(i, dim):
        hip, kn, ank, toe = J["legs"][i]
        c, sc_ = (pants, shoes) if not dim else (far(pants), far(shoes))
        if species == "robot":
            c = (150, 156, 166) if not dim else (110, 114, 124)
        _chain(d, [pt(hip), pt(kn), pt(ank)], [0.085 * u * girth * thin, 0.062 * u * thin, 0.05 * u * thin], c, ink, o)
        a, tp = pt(ank), pt(toe)
        fx = (tp[0] - a[0]) * 1.5
        _capsule(d, (a[0] - fx * 0.15, a[1]), (a[0] + fx, a[1] + 0.01 * u), 0.055 * u + 2 * o, 0.04 * u + 2 * o, ink)
        _capsule(d, (a[0] - fx * 0.15, a[1]), (a[0] + fx, a[1] + 0.01 * u), 0.055 * u, 0.04 * u, sc_)
        if species == "robot":
            k = pt(kn)
            r_ = 0.03 * u
            d.ellipse([k[0] - r_, k[1] - r_, k[0] + r_, k[1] + r_], fill=(90, 94, 104), outline=ink)

    def arm(i, dim):
        sh, el, hd = J["arms"][i]
        sleeve = outfit if not dim else far(outfit)
        hand = skin if not dim else far(skin)
        if species == "robot":
            sleeve, hand = ((160, 166, 176), (120, 124, 134)) if not dim else ((116, 120, 130), (96, 98, 106))
        if species in ("alien", "monster"):
            sleeve = hand
        _chain(d, [pt(sh), pt(el), pt(hd)], [0.06 * u * girth * thin, 0.05 * u * thin, 0.044 * u * thin], sleeve, ink, o)
        h_ = pt(hd)
        r_ = 0.034 * u * (1.25 if species == "monster" else 1.0)
        d.ellipse([h_[0] - r_ - o, h_[1] - r_ - o, h_[0] + r_ + o, h_[1] + r_ + o], fill=ink)
        d.ellipse([h_[0] - r_, h_[1] - r_, h_[0] + r_, h_[1] + r_], fill=hand)
        if species == "monster":                      # claws
            for k in (-1, 0, 1):
                a = math.atan2(h_[1] - pt(el)[1], h_[0] - pt(el)[0]) + k * 0.45
                d.polygon([(h_[0] + math.cos(a + 0.2) * r_ * 0.8, h_[1] + math.sin(a + 0.2) * r_ * 0.8),
                           (h_[0] + math.cos(a) * r_ * 1.8, h_[1] + math.sin(a) * r_ * 1.8),
                           (h_[0] + math.cos(a - 0.2) * r_ * 0.8, h_[1] + math.sin(a - 0.2) * r_ * 0.8)],
                          fill=(240, 236, 220))

    cape = getattr(L, "cape", None)
    if cape:                                          # a cape hangs from the shoulders behind everything and swings
        nk_, hp_ = pt(J["neck"]), pt(J["hip"])
        sway = math.sin(t * 2.2) * 0.03 * u - f * min(0.14 * u, abs(getattr(actor, "_vx", 0.0)) * 0.04 * u)
        cw = 0.09 * u * girth
        cp = [(nk_[0] - f * cw * 0.2, nk_[1] + 0.01 * u), (nk_[0] + f * cw * 0.6, nk_[1] + 0.01 * u),
              (hp_[0] - f * 0.02 * u + sway, hp_[1] + 0.2 * u), (hp_[0] - f * 0.2 * u + sway, hp_[1] + 0.17 * u)]
        d.polygon(cp, fill=tuple(cape), outline=ink)
    # far side first
    leg(1, True)
    arm(1, True)
    # torso: shoulders to hips, a little chest toward the facing side
    hip, neck = pt(J["hip"]), pt(J["neck"])
    ax, ay = neck[0] - hip[0], neck[1] - hip[1]
    Lt = math.hypot(ax, ay) or 1
    nx, ny = -ay / Lt, ax / Lt
    ws = 0.17 * u * girth * thin * (getattr(L, "shoulders", 1.0) or 1.0)
    wh = 0.15 * u * girth * thin
    top = (neck[0] - ax / Lt * 0.035 * u, neck[1] - ay / Lt * 0.035 * u)
    hip = (hip[0] - ax / Lt * 0.05 * u, hip[1] - ay / Lt * 0.05 * u)   # the torso reaches down over the pelvis
    ax, ay = top[0] - hip[0], top[1] - hip[1]
    chest = (hip[0] + ax * 0.62 + nx * f * 0.035 * u * girth, hip[1] + ay * 0.62 + ny * f * 0.035 * u * girth)
    torso = [(top[0] + nx * ws / 2, top[1] + ny * ws / 2), (chest[0] + nx * ws * 0.56, chest[1] + ny * ws * 0.56),
             (hip[0] + nx * wh / 2, hip[1] + ny * wh / 2), (hip[0] - nx * wh / 2, hip[1] - ny * wh / 2),
             (chest[0] - nx * ws * 0.56, chest[1] - ny * ws * 0.56), (top[0] - nx * ws / 2, top[1] - ny * ws / 2)]
    body_col = {"robot": (176, 182, 192), "alien": skin, "monster": skin}.get(species, outfit)
    if L.skirt:
        sk = [(hip[0] + nx * wh * 0.55, hip[1] + ny * wh * 0.55), (hip[0] - nx * wh * 0.55, hip[1] - ny * wh * 0.55),
              (hip[0] - nx * wh * 1.1 - ax * 0.42, hip[1] - ny * wh * 1.1 - ay * 0.42),
              (hip[0] + nx * wh * 1.1 - ax * 0.42, hip[1] + ny * wh * 1.1 - ay * 0.42)]
        _poly(d, sk, tuple(L.skirt), ink, o)
    _poly(d, torso, body_col, ink, o)
    if species == "robot":                            # chest panel and lights
        cx_, cy_ = hip[0] + ax * 0.6, hip[1] + ay * 0.6
        w_ = ws * 0.32
        d.rectangle([cx_ - w_, cy_ - w_ * 0.7, cx_ + w_, cy_ + w_ * 0.7], fill=(70, 76, 90), outline=ink)
        blink = 0.5 + 0.5 * math.sin(t * 5)
        d.ellipse([cx_ - w_ * 0.4, cy_ - w_ * 0.3, cx_ + w_ * 0.1, cy_ + w_ * 0.2],
                  fill=(int(80 + 170 * blink), 230, 120))
    elif species == "human":
        if L.tie:
            dx_, dy_ = -ax / Lt, -ay / Lt                # down the torso
            tw_ = 0.016 * u
            d.polygon([(top[0] + nx * tw_, top[1] + ny * tw_), (top[0] - nx * tw_, top[1] - ny * tw_),
                       (top[0] + dx_ * Lt * 0.5 - nx * tw_ * 1.4, top[1] + dy_ * Lt * 0.5 - ny * tw_ * 1.4),
                       (top[0] + dx_ * Lt * 0.6, top[1] + dy_ * Lt * 0.6),
                       (top[0] + dx_ * Lt * 0.5 + nx * tw_ * 1.4, top[1] + dy_ * Lt * 0.5 + ny * tw_ * 1.4)],
                      fill=tuple(L.tie), outline=ink)
        # collar line
        d.line([(top[0] + nx * ws * 0.22, top[1] + ny * ws * 0.22), (top[0] + ax / Lt * -0.05 * u, top[1] + ay / Lt * -0.05 * u),
                (top[0] - nx * ws * 0.22, top[1] - ny * ws * 0.22)], fill=ink, width=max(1, int(o)))
    # neck and head
    head = pt(J["head"])
    nk = 0.05 * u * (1.4 if species == "monster" else thin)
    _capsule(d, neck, (neck[0] + (head[0] - neck[0]) * 0.55, neck[1] + (head[1] - neck[1]) * 0.55), nk + 2 * o,
             nk + 2 * o, ink)
    _capsule(d, neck, (neck[0] + (head[0] - neck[0]) * 0.55, neck[1] + (head[1] - neck[1]) * 0.55), nk, nk,
             skin if species != "robot" else (120, 124, 134))
    cx, cy = head
    r = actor.r_head * scale * (1.3 if species == "alien" else 1.0)
    fc = actor.loco._face(t)
    if species == "robot":
        w_ = r * 1.05
        d.rounded_rectangle([cx - w_ - o, cy - r * 1.05 - o, cx + w_ + o, cy + r * 0.95 + o], radius=r * 0.3, fill=ink)
        d.rounded_rectangle([cx - w_, cy - r * 1.05, cx + w_, cy + r * 0.95], radius=r * 0.3, fill=(186, 192, 202))
        vx = cx + f * r * 0.18
        d.rounded_rectangle([vx - r * 0.75, cy - r * 0.5, vx + r * 0.75, cy + r * 0.05], radius=r * 0.2, fill=(30, 36, 48))
        eye = (90, 220, 255)
        for s_ in (-1, 1):
            ex = vx + s_ * r * 0.33
            h_ = r * 0.14 * max(0.15, fc.eye_open)
            d.ellipse([ex - r * 0.15, cy - r * 0.22 - h_, ex + r * 0.15, cy - r * 0.22 + h_], fill=eye)
        mo = r * (0.04 + 0.2 * fc.mouth_open)
        d.rectangle([vx - r * 0.35, cy + r * 0.38 - mo, vx + r * 0.35, cy + r * 0.38 + mo], fill=(40, 44, 54))
        d.line([(cx, cy - r * 1.05), (cx, cy - r * 1.55)], fill=ink, width=max(2, int(o * 1.5)))
        d.ellipse([cx - r * 0.12, cy - r * 1.7, cx + r * 0.12, cy - r * 1.46], fill=(240, 90, 80))
    else:
        if species == "human" and (L.hair in ("long", "ponytail") or L.bow):
            rig2d._hair_back(d, L, cx, cy, r, f, t)
        # ear on the far side of the face, head with a slight jaw
        if species != "alien":
            ex = cx - f * r * 0.18
            d.ellipse([ex - r * 0.2 - o, cy - r * 0.18 - o, ex + r * 0.2 + o, cy + r * 0.26 + o], fill=ink)
            d.ellipse([ex - r * 0.2, cy - r * 0.18, ex + r * 0.2, cy + r * 0.26], fill=far(skin))
        hh = r * (1.18 if species == "alien" else 1.06)
        d.ellipse([cx - r - o, cy - hh - o, cx + r + o, cy + r * 0.98 + o], fill=ink)
        d.ellipse([cx - r, cy - hh, cx + r, cy + r * 0.98], fill=skin)
        if species == "monster":
            for s_ in (-1, 1):                        # horns
                bx = cx + s_ * r * 0.55
                d.polygon([(bx - r * 0.2, cy - r * 0.75), (bx + s_ * r * 0.35, cy - r * 1.6),
                           (bx + r * 0.2, cy - r * 0.8)], fill=(236, 226, 200), outline=ink)
        if species == "alien":
            off = r * 0.22 * f
            for s_ in (-1, 1):                        # big almond eyes; blink with the face
                ex = cx + off + s_ * r * 0.4
                h_ = r * 0.32 * max(0.08, fc.eye_open)
                d.ellipse([ex - r * 0.27, cy - r * 0.15 - h_, ex + r * 0.27, cy - r * 0.15 + h_], fill=(18, 18, 26))
                d.ellipse([ex - r * 0.08, cy - r * 0.25 - h_ * 0.4, ex + r * 0.02, cy - r * 0.15 - h_ * 0.4],
                          fill=(230, 240, 255))
            mo = r * (0.02 + 0.18 * fc.mouth_open)
            d.ellipse([cx + off - r * 0.14, cy + r * 0.5 - mo, cx + off + r * 0.14, cy + r * 0.5 + mo], fill=(40, 30, 40))
            for s_ in (-1, 1):                        # antennae that wobble
                wob = math.sin(t * 4 + s_) * r * 0.15
                d.line([(cx + s_ * r * 0.3, cy - hh * 0.85), (cx + s_ * r * 0.6 + wob, cy - hh * 1.55)], fill=ink,
                       width=max(2, int(o)))
                d.ellipse([cx + s_ * r * 0.6 + wob - r * 0.1, cy - hh * 1.65, cx + s_ * r * 0.6 + wob + r * 0.1,
                           cy - hh * 1.45], fill=(250, 220, 90))
        else:
            F.draw(d, cx, cy, r, fc, f, t, ink=ink, skin=skin, lw=max(2.0, o * 1.1))
            if species == "monster":
                for k in (-1, 1):                     # fangs
                    tx = cx + r * 0.22 * f + k * r * 0.18
                    d.polygon([(tx - r * 0.07, cy + r * 0.38), (tx + r * 0.07, cy + r * 0.38), (tx, cy + r * 0.62)],
                              fill=(250, 250, 240))
        if species == "human":
            rig2d._hair_front(d, L, cx, cy, r, f, o * 2)
            if L.glasses:
                off = r * 0.22 * f
                for side in (-1, 1):
                    gx = cx + off + side * r * 0.36 * (0.82 if side * f < 0 else 1)
                    d.ellipse([gx - r * 0.22, cy - r * 0.32, gx + r * 0.22, cy + r * 0.08], outline=ink,
                              width=max(1, int(o)))
            if L.beard or L.mustache:
                off = r * 0.22 * f
                if L.beard:
                    d.chord([cx + off - r * 0.72, cy + r * 0.0, cx + off + r * 0.72, cy + r * 1.1], 15, 165,
                            fill=L.hair_color)
                d.chord([cx + off - r * 0.3, cy + r * 0.18, cx + off + r * 0.3, cy + r * 0.42], 180, 360,
                        fill=L.hair_color)
                if fc.mouth_open > 0.12:
                    my = cy + r * 0.45
                    d.ellipse([cx + off - r * 0.17, my - r * 0.04, cx + off + r * 0.17, my + r * fc.mouth_open * 0.3],
                              fill=(70, 20, 30))
            if L.cap:
                d.chord([cx - r * 1.02, cy - r * 1.1, cx + r * 1.02, cy + r * 0.5], 180, 360, fill=L.cap, outline=ink)
                d.line([(cx + f * r * 0.2, cy - r * 0.3), (cx + f * r * 1.45, cy - r * 0.22)], fill=L.cap,
                       width=max(2, int(r * 0.18)))
            crown = getattr(L, "crown", None)
            if crown:
                pts = [(cx - r * 0.6, cy - r * 0.85)]
                for i in range(5):
                    pts.append((cx - r * 0.6 + r * 0.3 * i, cy - r * (1.55 if i % 2 == 0 else 1.15)))
                pts.append((cx + r * 0.6, cy - r * 0.85))
                d.polygon(pts, fill=tuple(crown), outline=ink)
            helmet = getattr(L, "helmet", None)
            if helmet:
                d.chord([cx - r * 1.08, cy - r * 1.18, cx + r * 1.08, cy + r * 0.62], 180, 360, fill=tuple(helmet),
                        outline=ink)
                d.polygon([(cx - r * 0.1, cy - r * 1.18), (cx, cy - r * 1.75), (cx + r * 0.1, cy - r * 1.18)],
                          fill=(170, 40, 40))
    # near side on top
    leg(0, False)
    arm(0, False)
    hold = getattr(L, "holds", None)
    if hold == "staff":
        h_ = pt(J["arms"][0][2])
        d.line([(h_[0], h_[1] - 0.45 * u), (h_[0], h_[1] + 0.5 * u)], fill=(110, 76, 44), width=max(3, int(0.022 * u)))
        d.ellipse([h_[0] - 0.035 * u, h_[1] - 0.52 * u, h_[0] + 0.035 * u, h_[1] - 0.45 * u], fill=(120, 210, 255))
    elif hold == "sword":
        h_, e_ = pt(J["arms"][0][2]), pt(J["arms"][0][1])
        a = math.atan2(h_[1] - e_[1], h_[0] - e_[0])
        tip = (h_[0] + math.cos(a) * 0.45 * u, h_[1] + math.sin(a) * 0.45 * u)
        d.line([h_, tip], fill=(210, 214, 222), width=max(3, int(0.018 * u)))
        d.line([(h_[0] - math.sin(a) * 0.05 * u, h_[1] + math.cos(a) * 0.05 * u),
                (h_[0] + math.sin(a) * 0.05 * u, h_[1] - math.cos(a) * 0.05 * u)], fill=(150, 110, 40),
               width=max(3, int(0.02 * u)))
    actor._joints = J
    return cx, cy, r, ink


# ---- per-character shading (cel shadow, rim light, halftone) -----------------------------------------------------
_DOTS: dict = {}


def _dots(h, w, period):
    key = (h, w, period)
    if key not in _DOTS:
        yy, xx = np.mgrid[0:h, 0:w]
        # a 45-degree screen: dot radius grows with the shadow (here: fixed coverage ~45%)
        u = ((xx + yy) % period) - period / 2
        v = ((xx - yy) % period) - period / 2
        _DOTS[key] = (u * u + v * v) < (period * 0.36) ** 2
        if len(_DOTS) > 24:
            _DOTS.pop(next(iter(_DOTS)))
    return _DOTS[key]


def shade(layer: Image.Image, style: Style, scale_px: float) -> Image.Image:
    """Cel-shades a layer holding one character: the edge facing away from the light darkens (tinted), the edge
    facing it brightens, and the shadow gets halftone dots when stylised. scale_px ~ the character's height in px."""
    box = layer.getbbox()
    if not box or style.shade <= 0:
        return layer
    pad = 4
    x0, y0, x1, y1 = max(0, box[0] - pad), max(0, box[1] - pad), min(layer.width, box[2] + pad), \
        min(layer.height, box[3] + pad)
    crop = np.asarray(layer.crop((x0, y0, x1, y1)), dtype=np.float32)
    a = crop[..., 3] > 128
    lx, ly = style.light
    n = math.hypot(lx, ly) or 1
    lx, ly = lx / n, ly / n
    k = max(2, int(scale_px * 0.045 * (0.6 + 0.6 * style.stylization)))

    def away(m, dist):                               # m sampled `dist` px away from the light
        dx, dy = int(round(-lx * dist)), int(round(-ly * dist))
        return np.roll(np.roll(m, -dy, axis=0), -dx, axis=1)

    def toward(m, dist):
        dx, dy = int(round(lx * dist)), int(round(ly * dist))
        return np.roll(np.roll(m, -dy, axis=0), -dx, axis=1)
    shadow = a & ~away(a, k)
    if style.stylization < 0.45:                     # softer: a graded band instead of a hard edge
        soft = shadow.astype(np.float32)
        img = Image.fromarray((soft * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(k * 0.6))
        sh = np.asarray(img, dtype=np.float32) / 255 * a
    else:
        sh = shadow.astype(np.float32)
    if style.halftone > 0:
        dots = _dots(a.shape[0], a.shape[1], max(4, int(scale_px * 0.016)))
        sh = sh * np.where(dots, 1.0, 1.0 - style.halftone)
    rgb = crop[..., :3]
    tint = np.array(style.shadow_tint, dtype=np.float32)
    amt = (style.shade * 0.55 * sh)[..., None]
    rgb = rgb * (1 - amt) + rgb * tint / 255 * amt * 0.7
    if style.rim > 0:
        rim = (a & ~toward(a, max(1, k // 3))).astype(np.float32)[..., None]
        rgb = rgb + (255 - rgb) * rim * style.rim * 0.45
    crop[..., :3] = np.clip(rgb, 0, 255)
    out = layer.copy()
    out.paste(Image.fromarray(crop.astype(np.uint8), "RGBA"), (x0, y0))
    return out


# ---- whole-picture grade ----------------------------------------------------------------------------------------
_VIG: dict = {}


def _vignette(w, h, amount):
    key = (w, h, round(amount, 3))
    if key not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        _VIG[key] = (1 - amount * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6)[..., None]
    return _VIG[key]


def _paper(w, h):
    key = ("paper", w, h)
    if key not in _VIG:
        rng = np.random.default_rng(3)
        n = rng.normal(0, 1, (h // 4 + 1, w // 4 + 1)).astype(np.float32)
        img = Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        _VIG[key] = (np.asarray(img, dtype=np.float32)[..., None] - 128) / 128
    return _VIG[key]


def grade(img: Image.Image, style: Style, t: float, frame_no: int = 0) -> Image.Image:
    """The whole picture: ink edges, tone, colour, selective colour, posterising, grain, vignette, paper,
    letterbox and panel border."""
    W, H = img.size
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    if style.ink_edges > 0:
        lum = img.convert("L").filter(ImageFilter.GaussianBlur(0.8))
        e = np.asarray(lum.filter(ImageFilter.FIND_EDGES), dtype=np.float32)
        thr = 26 - 10 * style.stylization
        ink = np.clip((e - thr) / 30, 0, 1) * style.ink_edges
        a = a * (1 - ink[..., None] * 0.85)
    if style.contrast != 1.0:
        a = (a - 128) * np.float32(style.contrast) + 128
    lum = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114)[..., None]
    if style.key_hue is not None:                    # selective colour: one hue survives
        hsv = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("HSV"), dtype=np.float32)
        hue = hsv[..., 0] / 255 * 360
        dh = np.abs((hue - style.key_hue + 180) % 360 - 180)
        keep = np.clip((style.key_tol - dh) / 8, 0, 1) * np.clip((hsv[..., 1] / 255 - 0.3) / 0.2, 0, 1)
        a = lum + (a - lum) * (keep[..., None] * 1.25)
    elif style.saturation != 1.0:
        a = lum + (a - lum) * style.saturation
    if style.split > 0:
        lo = np.clip(1 - lum / 128, 0, 1)
        hi = np.clip((lum - 128) / 128, 0, 1)
        a = a + style.split * (lo * np.array([-10, 4, 18], np.float32) + hi * np.array([18, 6, -14], np.float32))
    if style.posterize:                              # tonal steps on brightness only: hues stay, no colour bands
        a = np.clip(a, 0, 255)
        lm = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114)[..., None]
        step = 256 / style.posterize
        q = np.floor(lm / step) * step + step / 2
        k = 0.35 + 0.4 * style.stylization
        a = a * (1 - k) + a * (q / np.maximum(lm, 1)) * k
    if style.paper > 0:
        a = a * (1 + _paper(W, H) * 0.08 * style.paper)
    if style.grain > 0:
        rng = np.random.default_rng(frame_no + 1)
        a = a + rng.standard_normal((H, W, 1), dtype=np.float32) * np.float32(255 * style.grain)
    if style.vignette > 0:
        a = a * _vignette(W, H, style.vignette)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if style.letterbox and W / H < style.letterbox and W > H:
        bar = int((H - W / style.letterbox) / 2)
        if bar > 0:
            dd = ImageDraw.Draw(out)
            dd.rectangle([0, 0, W, bar], fill=(8, 8, 10))
            dd.rectangle([0, H - bar, W, H], fill=(8, 8, 10))
    if style.panel:
        dd = ImageDraw.Draw(out)
        g = max(4, int(min(W, H) * 0.022))
        dd.rectangle([0, 0, W, g], fill=(246, 242, 230))
        dd.rectangle([0, H - g, W, H], fill=(246, 242, 230))
        dd.rectangle([0, 0, g, H], fill=(246, 242, 230))
        dd.rectangle([W - g, 0, W, H], fill=(246, 242, 230))
        dd.rectangle([g, g, W - g, H - g], outline=(16, 16, 20), width=max(2, g // 4))
    return out


def safe_area(style: Style | None, W: int, H: int) -> tuple:
    """(top, bottom) pixels hidden by letterbox bars or the panel border: captions stay inside."""
    if style is None:
        return 0, 0
    top = 0
    if style.letterbox and W > H and W / H < style.letterbox:
        top = int((H - W / style.letterbox) / 2)
    if style.panel:
        top = max(top, int(min(W, H) * 0.022))
    return top, top


# ---- comic effects -----------------------------------------------------------------------------------------------
def _font(style, size, serif=False):
    try:
        return ImageFont.truetype(SERIF if serif else (style.font if style else FONT), max(8, int(size)))
    except OSError:
        return ImageFont.truetype(FONT, max(8, int(size)))


def _pop(u):
    u = max(0.0, min(1.0, u))
    s = 2.2
    u -= 1
    return u * u * ((s + 1) * u + s) + 1


def comic_fx(img: Image.Image, fx: list, t: float, where, style: Style | None):
    """Draws comic effects active at t. Each: {"t0", "t1", "kind": impact|sfx|speedlines|caption, "text",
    "at": actor or (x, y) world point or None, "color"}. where(at) -> screen (x, y) or None."""
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    top, _ = safe_area(style, W, H)
    for e in fx:
        t0, t1 = e["t0"], e["t1"]
        if not t0 <= t <= t1:
            continue
        u = (t - t0) / max(1e-3, t1 - t0)
        k = _pop(min(1.0, (t - t0) / 0.25))
        fade = min(1.0, (t1 - t) / 0.2)
        kind = e.get("kind", "sfx")
        pos = where(e.get("at")) if e.get("at") is not None else None
        if kind == "speedlines":
            cx, cy = pos or (W / 2, H / 2)
            rng = np.random.default_rng(int(t * 24))
            for i in range(46):
                ang = rng.uniform(0, math.tau)
                r0 = rng.uniform(0.32, 0.5) * max(W, H)
                r1 = max(W, H) * 0.9
                w_ = rng.uniform(1.5, 5) * H / 720
                d.line([(cx + math.cos(ang) * r0, cy + math.sin(ang) * r0),
                        (cx + math.cos(ang) * r1, cy + math.sin(ang) * r1)],
                       fill=(255, 255, 255, int(150 * fade)) if e.get("light", True) else (10, 10, 14, int(170 * fade)),
                       width=int(w_))
            continue
        if kind == "caption":                         # the motion-comic narration box
            size = H * 0.034
            fnt = _font(style, size, serif=True)
            words, lines, cur = e["text"].split(), [], ""
            for w_ in words:
                if d.textlength((cur + " " + w_).strip(), font=fnt) > W * 0.42 and cur:
                    lines.append(cur)
                    cur = w_
                else:
                    cur = (cur + " " + w_).strip()
            lines.append(cur)
            pad = size * 0.55
            bw = max(d.textlength(l_, font=fnt) for l_ in lines) + 2 * pad
            bh = len(lines) * size * 1.3 + 2 * pad
            x0, y0 = W * 0.04, top + H * 0.04
            al = int(255 * min(1.0, (t - t0) / 0.25, fade))
            d.rectangle([x0 + 4, y0 + 4, x0 + bw + 4, y0 + bh + 4], fill=(0, 0, 0, al // 3))
            d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=(250, 232, 160, al), outline=(20, 20, 20, al),
                        width=max(2, int(H / 360)))
            for i, l_ in enumerate(lines):
                d.text((x0 + pad, y0 + pad + i * size * 1.3), l_, font=fnt, fill=(20, 20, 20, al))
            continue
        cx, cy = pos or (W * e.get("sx", 0.5), H * e.get("sy", 0.35))
        size = H * e.get("size", 0.09) * k
        if size < 4:
            continue
        col = tuple(e.get("color", (255, 214, 40)))
        al = int(255 * fade)
        if kind == "impact":                          # a jagged burst behind the word
            pts = []
            n = 14
            rot = (zlib.crc32(e.get("text", "").encode()) % 100) / 100
            for i in range(2 * n):
                a_ = math.tau * (i + rot) / (2 * n)
                rr = size * (1.55 if i % 2 == 0 else 0.95)
                pts.append((cx + math.cos(a_) * rr * 1.25, cy + math.sin(a_) * rr))
            d.polygon(pts, fill=(255, 255, 255, al), outline=(15, 15, 15, al))
            inner = [(cx + (x - cx) * 0.8, cy + (y - cy) * 0.8) for x, y in pts]
            d.polygon(inner, fill=col + (al,))
        text = e.get("text", "")
        if text:
            fnt = _font(style, size)
            tilt = e.get("tilt", -8)
            tw = int(d.textlength(text, font=fnt)) + int(size)
            th = int(size * 1.6)
            tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            td = ImageDraw.Draw(tile)
            fill = (255, 255, 255) if kind == "impact" else col
            td.text((tw / 2, th / 2), text, font=fnt, fill=fill + (al,), anchor="mm", stroke_width=max(2, int(size / 9)),
                    stroke_fill=(15, 15, 15, al))
            tile = tile.rotate(tilt, resample=Image.BICUBIC, expand=True)
            img.alpha_composite(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2))) if img.mode == "RGBA" \
                else img.paste(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)), tile)
            d = ImageDraw.Draw(img, "RGBA")


def auto_speedlines(d, actors, t, to_screen_z, scale_out, ss=1):
    """Motion streaks behind anyone moving faster than a jog (stylised styles only)."""
    for a in actors:
        if not hasattr(a, "pose_now") or not hasattr(a, "_vx"):
            continue
        v = a._vx
        if abs(v) < 3.0:
            continue
        S, sc = to_screen_z(getattr(a, "z", 1.0))
        J = getattr(a, "_joints", None)
        if not J:
            continue
        hx, hy = S(*J["hip"])
        nx_, ny_ = S(*J["neck"])
        back = -1 if v > 0 else 1
        L = sc * min(1.6, abs(v) * 0.25)
        for i in range(6):
            y = hy + (ny_ - hy) * (i / 5.0) * 1.3
            x = hx + back * sc * 0.2
            d.line([(x, y), (x + back * L * (0.6 + 0.4 * ((i * 7) % 3) / 2), y)], fill=(255, 255, 255, 150),
                   width=max(2, int(sc * 0.012)))


# ---- choosing a style for a story -------------------------------------------------------------------------------
GENRE_STYLE = {
    "history": "graphic_novel", "mythology": "graphic_novel", "thriller": "noir", "mystery": "noir",
    "horror": "noir", "action": "motion_comic", "adventure": "graphic_novel", "fantasy": "painterly",
    "comedy": "cartoon", "children": "cartoon", "story": "cartoon", "romance": "painterly", "drama": "painterly",
    "science": "explainer", "education": "explainer", "medical": "explainer", "business": "explainer",
    "finance": "explainer", "psychology": "explainer", "wildlife": "painterly", "nature": "painterly",
    "space": "anime", "sports": "western", "music": "anime", "advertising": "cartoon", "political": "stick",
    "documentary": "stick", "news": "stick",
}
GENRE_WORDS = {
    "history": r"\b(emperor|empire|ancient|king|queen|pharaoh|roman|centur(y|ies)|dynasty|medieval|fort|"
               r"kingdom|warrior|battle of|caravan|civili[sz]ation)\b",
    "fantasy": r"\b(dragon|wizard|magic|spell|elf|fairy|unicorn|enchanted|potion|castle|sorcer)\w*",
    "science": r"\b(cell|atom|molecule|planet|gravity|energy|experiment|scientist|photosynthesis|dna|virus|"
               r"bacteria|orbit|electron|neuron)s?\b",
    "space": r"\b(astronaut|rocket|spaceship|galaxy|alien|mars|moon base|space station)s?\b",
    "thriller": r"\b(detective|crime scene|shadowy|murder|suspect|spy|heist|alley at midnight)\b",
    "horror": r"\b(ghost|haunted|monster|zombie|creature in the dark|scream)s?\b",
    "wildlife": r"\b(wolf|wolves|lion|elephant|deer|eagle|forest animals|herd|pack|savanna|wildlife|fox)\b",
    "drama": r"\b(grief|funeral|hospital|letter from|goodbye|memories|regret|forgive)\w*",
    "romance": r"\b(in love|first date|kiss|wedding|heart raced)\b",
    "sports": r"\b(match|goal|race|stadium|team|coach|finish line)\b",
    "children": r"\b(bunny|teddy|playground|kindergarten|lullaby)\b",
}


def choose(text: str, domain: str = "", override=None) -> tuple:
    """(style name, reason). An explicit override always wins; otherwise the strongest genre signal in the script,
    then the director's domain."""
    import re
    if override:
        return (override if isinstance(override, str) else override.get("name", "graphic_novel")), "chosen by the user"
    hits = {g: len(re.findall(rx, text, re.I)) for g, rx in GENRE_WORDS.items()}
    g, n = max(hits.items(), key=lambda kv: kv[1])
    if n >= 2 or (n == 1 and domain in ("story", "")):
        return GENRE_STYLE[g], f"genre looks like {g} ({n} cue{'s' if n > 1 else ''})"
    return GENRE_STYLE.get(domain, "stick"), f"from the director's domain ({domain or 'general'})"
