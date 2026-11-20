"""Faces: a library of expressions as numbers (brows, eyes, pupils, mouth, extras), blended smoothly from one to the
next, with blinking and lip-sync on top. Drawn in the character's own colours, in a three-quarter view (the face sits
toward the way the character looks)."""
from __future__ import annotations

import math
from dataclasses import dataclass, fields, replace


@dataclass
class Face:
    brow_tilt: float = 0.0     # + inner ends up (sad, worried) / - inner ends down (angry)
    brow_raise: float = 0.0    # + raised (surprise) / - lowered (focus, anger)
    eye_open: float = 1.0      # 0 closed .. 1 normal .. 1.5 wide
    eye_smile: float = 0.0     # 0 round eyes .. 1 happy arcs (^ ^)
    pupil_size: float = 1.0
    look_x: float = 0.0        # pupils -1..1 (toward the face direction is +)
    look_y: float = 0.0        # -1 down .. 1 up
    smile: float = 0.0         # -1 frown .. 1 smile
    mouth_open: float = 0.0
    mouth_width: float = 1.0
    mouth_round: float = 0.0
    smirk: float = 0.0         # one corner up
    teeth: float = 0.0         # clenched teeth showing
    blush: float = 0.0
    tears: float = 0.0
    sweat: float = 0.0
    vein: float = 0.0          # anger mark
    head_tilt: float = 0.0     # degrees
    shake: float = 0.0         # trembling (fear) / laughing bounce
    sleepy: float = 0.0        # floating z's


E = Face
EXPRESSIONS: dict[str, Face] = {
    "neutral": E(),
    "happy": E(smile=0.7, eye_smile=0.25, brow_raise=0.1),
    "excited": E(smile=0.95, mouth_open=0.45, eye_open=1.25, brow_raise=0.45, pupil_size=1.15),
    "joyful": E(smile=1.0, mouth_open=0.3, eye_smile=0.9, brow_raise=0.25, blush=0.4),
    "laughing": E(smile=1.0, mouth_open=0.8, eye_smile=1.0, brow_raise=0.3, head_tilt=-10, shake=0.6, blush=0.3),
    "sad": E(smile=-0.6, brow_tilt=0.7, eye_open=0.75, look_y=-0.5, head_tilt=6),
    "crying": E(smile=-0.9, mouth_open=0.35, brow_tilt=0.95, eye_open=0.35, tears=1.0, head_tilt=8, shake=0.15),
    "heartbroken": E(smile=-0.8, brow_tilt=0.9, eye_open=0.6, look_y=-0.8, tears=0.5, head_tilt=12),
    "angry": E(smile=-0.55, brow_tilt=-0.85, brow_raise=-0.3, eye_open=0.85, pupil_size=0.8, teeth=0.6, vein=0.6),
    "furious": E(smile=-0.8, mouth_open=0.55, brow_tilt=-1.0, brow_raise=-0.45, eye_open=1.05, pupil_size=0.65,
                 teeth=1.0, vein=1.0, shake=0.3),
    "frustrated": E(smile=-0.45, brow_tilt=-0.5, eye_open=0.7, teeth=0.4, look_y=-0.3, head_tilt=-5),
    "confused": E(smile=-0.15, smirk=-0.4, brow_tilt=0.3, brow_raise=0.15, look_x=-0.4, look_y=0.4, head_tilt=14),
    "curious": E(smile=0.15, brow_raise=0.4, eye_open=1.15, pupil_size=1.1, head_tilt=10, look_x=0.4),
    "suspicious": E(smile=-0.2, smirk=0.3, brow_tilt=-0.4, eye_open=0.45, look_x=0.9),
    "shocked": E(mouth_open=0.9, mouth_round=0.7, mouth_width=0.8, eye_open=1.5, pupil_size=0.6, brow_raise=0.9),
    "surprised": E(mouth_open=0.55, mouth_round=0.8, mouth_width=0.75, eye_open=1.35, brow_raise=0.7, smile=0.1),
    "frightened": E(smile=-0.5, mouth_open=0.45, brow_tilt=0.8, brow_raise=0.6, eye_open=1.4, pupil_size=0.55,
                    shake=0.5, sweat=0.8),
    "nervous": E(smile=-0.1, smirk=0.25, brow_tilt=0.55, eye_open=1.05, look_x=-0.6, sweat=1.0, teeth=0.4),
    "anxious": E(smile=-0.3, brow_tilt=0.7, eye_open=1.1, look_x=-0.3, look_y=-0.2, sweat=0.6, shake=0.15),
    "embarrassed": E(smile=0.2, smirk=0.3, brow_tilt=0.5, eye_open=0.7, look_y=-0.7, look_x=-0.6, blush=1.0,
                     head_tilt=8),
    "sarcastic": E(smirk=0.8, brow_raise=0.2, brow_tilt=-0.2, eye_open=0.6, look_x=-0.5, look_y=0.4),
    "smug": E(smile=0.45, smirk=0.6, eye_open=0.55, brow_raise=0.15, head_tilt=-8),
    "mischievous": E(smile=0.65, smirk=0.5, brow_tilt=-0.5, eye_open=0.65, look_x=0.6, teeth=0.5),
    "disgusted": E(smile=-0.6, smirk=-0.5, brow_tilt=-0.4, brow_raise=-0.1, eye_open=0.55, head_tilt=-10,
                   look_x=-0.5),
    "disappointed": E(smile=-0.45, brow_tilt=0.45, eye_open=0.6, look_y=-0.4, head_tilt=4),
    "bored": E(smile=-0.15, eye_open=0.45, look_x=-0.5, look_y=0.2, head_tilt=10),
    "thoughtful": E(smile=-0.05, smirk=0.2, brow_tilt=0.2, brow_raise=0.15, look_x=0.5, look_y=0.8, head_tilt=8),
    "focused": E(smile=-0.1, brow_tilt=-0.3, brow_raise=-0.2, eye_open=0.8, pupil_size=0.9),
    "intelligent": E(smile=0.3, smirk=0.3, brow_raise=0.2, eye_open=0.9),
    "tired": E(smile=-0.2, eye_open=0.4, brow_tilt=0.3, look_y=-0.3, head_tilt=10),
    "sleepy": E(eye_open=0.12, mouth_open=0.15, mouth_round=0.6, head_tilt=16, sleepy=1.0),
    "exhausted": E(smile=-0.3, mouth_open=0.4, eye_open=0.35, brow_tilt=0.5, sweat=0.7, head_tilt=12, look_y=-0.5),
    "proud": E(smile=0.6, eye_open=0.75, brow_raise=0.25, head_tilt=-12, look_y=0.3),
    "confident": E(smile=0.55, smirk=0.2, eye_open=0.9, brow_raise=0.1, brow_tilt=-0.1),
    "determined": E(smile=-0.1, brow_tilt=-0.6, brow_raise=-0.2, eye_open=0.95, teeth=0.3, pupil_size=0.9),
    "worried": E(smile=-0.4, brow_tilt=0.75, eye_open=1.0, look_x=0.4, sweat=0.4),
    "panicked": E(smile=-0.6, mouth_open=0.7, mouth_round=0.4, brow_tilt=0.9, brow_raise=0.7, eye_open=1.5,
                  pupil_size=0.5, sweat=1.0, shake=0.6),
    "terrified": E(smile=-0.7, mouth_open=0.85, brow_tilt=1.0, brow_raise=0.9, eye_open=1.55, pupil_size=0.45,
                   sweat=1.0, shake=0.9, tears=0.3),
}
ALIASES = {"joy": "joyful", "laugh": "laughing", "cry": "crying", "anger": "angry", "mad": "angry", "shock": "shocked",
           "surprise": "surprised", "fear": "frightened", "scared": "frightened", "afraid": "frightened",
           "think": "thoughtful", "thinking": "thoughtful", "smart": "intelligent", "calm": "neutral",
           "disgust": "disgusted", "panic": "panicked"}


def expression(name: str) -> Face:
    n = (name or "neutral").strip().lower()
    return EXPRESSIONS.get(ALIASES.get(n, n), EXPRESSIONS["neutral"])


def blend(a: Face, b: Face, k: float) -> Face:
    k = max(0.0, min(1.0, k))
    return Face(**{f.name: getattr(a, f.name) + (getattr(b, f.name) - getattr(a, f.name)) * k for f in fields(Face)})


def mix(*parts: tuple[Face, float]) -> Face:
    """A weighted combination ("worried" 0.6 + "angry" 0.4)."""
    total = sum(w for _, w in parts) or 1.0
    return Face(**{f.name: sum(getattr(p, f.name) * w for p, w in parts) / total for f in fields(Face)})


def blink(t: float, seed: int = 0) -> float:
    """Eyelid factor 0..1 (1 open): a blink every 2.5-4.5 s, 0.16 s long."""
    period = 2.5 + (seed % 7) * 0.3
    ph = (t + seed * 0.37) % period
    if ph > 0.16:
        return 1.0
    return abs(ph - 0.08) / 0.08


def speaking(face: Face, mouth: tuple[float, float, float], weight: float = 1.0) -> Face:
    """The expression with the speech mouth on top (the smile stays, so a happy line is said smiling)."""
    o, w, r = mouth
    if weight <= 0:
        return face
    return replace(face, mouth_open=face.mouth_open * (1 - weight) + o * weight,
                   mouth_width=face.mouth_width * (1 - weight) + w * weight,
                   mouth_round=face.mouth_round * (1 - weight) + r * weight, teeth=face.teeth * (1 - weight))


def _rot(px, py, cx, cy, ang):
    s, c = math.sin(ang), math.cos(ang)
    dx, dy = px - cx, py - cy
    return cx + dx * c - dy * s, cy + dx * s + dy * c


def _quad(p0, p1, p2, n=14):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def draw(d, cx: float, cy: float, r: float, face: Face, facing: float, t: float, ink=(20, 20, 24),
         skin=(255, 255, 255), lw: float = 4.0, eye_white=(255, 255, 255)) -> None:
    """Draws the face on the head centred at (cx, cy) radius r (screen pixels, y down). facing -1..1."""
    ang = math.radians(face.head_tilt) * (1 if facing >= 0 else -1)
    off = r * 0.22 * facing                       # features toward where the character looks (3/4 view)

    def P(x, y):
        return _rot(cx + off + x, cy + y, cx, cy, ang)
    # eyes
    ex, ey = r * 0.36, -r * 0.12
    er = r * 0.17
    for side in (-1, 1):
        x = side * ex * (0.82 if side * facing < 0 else 1.0)   # the far eye a little closer (perspective)
        open_ = max(0.0, face.eye_open)
        cxe, cye = P(x, ey)
        if face.eye_smile > 0.5:
            pts = [P(x + er * math.cos(a), ey + er * 0.35 - er * 0.9 * math.sin(a)) for a in
                   [math.pi * i / 10 for i in range(11)]]
            d.line(pts, fill=ink, width=int(lw * 0.9), joint="curve")
            continue
        h = er * min(1.6, open_) * (1 - face.eye_smile * 0.6)
        if h < er * 0.12:
            d.line([P(x - er, ey), P(x + er, ey)], fill=ink, width=int(lw * 0.9))
            continue
        d.ellipse([cxe - er * 1.05, cye - h * 1.05, cxe + er * 1.05, cye + h * 1.05], fill=eye_white, outline=ink,
                  width=max(1, int(lw * 0.55)))
        pr = er * 0.55 * face.pupil_size
        px = cxe + face.look_x * facing * er * 0.45
        py = cye - face.look_y * h * 0.4
        pr = min(pr, h * 0.95)
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=ink)
        d.ellipse([px - pr * 0.35 + pr * 0.25, py - pr * 0.6, px + pr * 0.2, py - pr * 0.1], fill=(255, 255, 255))
        if face.eye_smile > 0:                  # lower lids pushed up by the smile
            d.chord([cxe - er * 1.1, cye + h * (1 - face.eye_smile) - er, cxe + er * 1.1, cye + h * 1.1 + er * 0.6],
                    200, 340, fill=skin)
    # brows
    by = ey - er * 1.55 - face.brow_raise * r * 0.16
    for side in (-1, 1):
        x = side * ex * (0.82 if side * facing < 0 else 1.0)
        inner = (x - side * er * 0.95, by - face.brow_tilt * r * 0.1)
        outer = (x + side * er * 1.0, by + face.brow_tilt * r * 0.08)
        d.line([P(*inner), P(*outer)], fill=ink, width=int(lw * 1.15))
    # mouth
    my = r * 0.42
    mw = r * 0.34 * face.mouth_width * (1 - face.mouth_round * 0.35)
    o = face.mouth_open
    left, right = (-mw, my - face.smile * r * 0.06 + face.smirk * -0.0), (mw, my - face.smile * r * 0.06 - face.smirk * r * 0.12)
    mid_up = (0, my + face.smile * r * 0.16)
    if o < 0.06 and face.teeth < 0.3:
        d.line([P(*p) for p in _quad(left, mid_up, right)], fill=ink, width=int(lw * 0.95), joint="curve")
    else:
        cy0 = my - face.smile * r * 0.06
        drop = max(o, face.teeth * 0.18) * r * 0.42
        top_c = cy0 - o * r * 0.14 + max(0.0, face.smile) * r * 0.12 - max(0.0, -face.smile) * r * 0.1
        bot_c = max(top_c + r * 0.12 * max(o, 0.25), cy0 + drop * (1.0 + 0.6 * face.smile) + max(0.0, face.smile) * r * 0.2)
        top = _quad(left, (0, top_c), right)
        bottom = _quad(right, (0, bot_c), left)
        if face.mouth_round > 0.5 and o > 0.1:
            rw, rh = mw * 0.75, max(drop * 0.6, r * 0.06)
            c = P(0, my + rh * 0.4)
            d.ellipse([c[0] - rw, c[1] - rh, c[0] + rw, c[1] + rh], fill=(70, 20, 30), outline=ink, width=int(lw * 0.8))
        else:
            poly = [P(*p) for p in top + bottom]
            d.polygon(poly, fill=(70, 20, 30) if o > 0.12 else (245, 245, 245), outline=ink)
            d.line(poly + [poly[0]], fill=ink, width=int(lw * 0.8), joint="curve")
            if face.teeth > 0.3 and o < 0.5:
                ty = (top_c + bot_c) / 2
                d.line([P(-mw * 0.7, ty), P(mw * 0.7, ty)], fill=(200, 200, 200), width=max(1, int(lw * 0.5)))
            elif o > 0.35 and bot_c - top_c > r * 0.18:     # tongue, inside the mouth
                tc = P(0, bot_c - (bot_c - top_c) * 0.28)
                tw, th = mw * 0.42, (bot_c - top_c) * 0.2
                d.ellipse([tc[0] - tw, tc[1] - th, tc[0] + tw, tc[1] + th], fill=(205, 80, 90))
    # extras
    if face.blush > 0.05:
        a = int(110 * face.blush)
        for side in (-1, 1):
            c = P(side * ex * 1.15, r * 0.2)
            d.ellipse([c[0] - r * 0.16, c[1] - r * 0.07, c[0] + r * 0.16, c[1] + r * 0.07], fill=(255, 120, 140, a))
    if face.tears > 0.05:
        for side in (-1, 1):
            x = side * ex * (0.82 if side * facing < 0 else 1.0)
            run = (t * 1.6 + side * 0.3) % 1.0
            c = P(x + side * er * 0.4, ey + er + run * r * 0.55 * face.tears)
            s = r * 0.07
            d.ellipse([c[0] - s * 0.7, c[1] - s, c[0] + s * 0.7, c[1] + s], fill=(90, 170, 255))
    if face.sweat > 0.05:
        c = P(r * 0.8 * (1 if facing >= 0 else -1) * -1, -r * 0.55 + ((t * 0.7) % 1) * r * 0.3)
        s = r * 0.1 * face.sweat
        d.polygon([(c[0], c[1] - s * 1.6), (c[0] - s, c[1]), (c[0] + s, c[1])], fill=(120, 190, 255))
        d.ellipse([c[0] - s, c[1] - s, c[0] + s, c[1] + s], fill=(120, 190, 255))
    if face.vein > 0.05:
        c = P(-r * 0.55 * (1 if facing >= 0 else -1), -r * 0.62)
        s = r * 0.13 * face.vein
        for a in (0.3, 1.87, 3.44, 5.01):
            d.line([(c[0] + math.cos(a) * s * 0.3, c[1] + math.sin(a) * s * 0.3),
                    (c[0] + math.cos(a) * s, c[1] + math.sin(a) * s)], fill=(220, 30, 40), width=int(lw * 0.8))
    if face.sleepy > 0.05:
        for k in range(3):
            ph = (t * 0.5 + k / 3) % 1
            zx, zy = cx + r * (0.9 + ph * 0.8), cy - r * (0.9 + ph * 1.3)
            s = r * (0.12 + ph * 0.12)
            d.line([(zx, zy), (zx + s, zy), (zx, zy + s), (zx + s, zy + s)], fill=ink, width=max(1, int(lw * 0.6)))
