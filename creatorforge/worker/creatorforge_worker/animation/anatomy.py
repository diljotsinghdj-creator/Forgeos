"""Creatures with skeletons that fit their anatomy, driven by how they actually move through the scene.

A creature is a prop (stick.Prop, kind "shape", data["kind"] = species): it moves with the same keys, steps, world
state and camera as any prop, and this module draws it from its motion every frame:

* quadruped   four legs, each a two-bone IK chain plus a foot segment, planted on the ground during stance and
              swung forward in the air; the footfall pattern blends from walk (lateral sequence) to trot (diagonal
              pairs) to gallop by speed (Froude number), with body bob and pitch, a neck and head that bob against the
              body, and a tail on a spring (wags, drags behind at speed). Hind legs bend the right way (hock back),
              front legs the other. Airborne (jumping) poses stretch the legs.
* bird        wings with two segments that flap (the outer one lags) when flying, fold when perched; hopping legs.
* fish        a body wave along a spine with the tail fin sweeping (seen edge-on as it turns); fins move.
* whale       cetaceans: the vertical body wave and fluke beat (they really swim up-and-down).
* serpent     snakes, eels and sea serpents: the body follows the path the head took (sampled from the prop's own
              motion history), with travelling humps.
* dragon      a quadruped with membrane wings (flap in flight, half-folded on the ground), a long neck and tail,
              spines, and fire breath.
* butterfly   fast flapping wings, fluttering flight.

Acts on a timeline (p.data["acts"] = [[t0, t1, act], ...]): sit, lie, eat, roar (bark/howl), wag, shake, rear,
breathe_fire, fly, sleep. Everything is drawn with an ink outline that follows the production style."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

TAU = 2 * math.pi


@dataclass
class Spec:
    rig: str = "quad"
    L: float = 0.8            # body length (m)
    Hb: float = 0.3           # body depth
    leg: float = 0.35         # shoulder height above the ground to the body's underside
    neck: float = 0.2
    neck_ang: float = 0.7     # radians above horizontal
    head: float = 0.11
    snout: float = 0.1
    ears: str = "point"       # none | point | flop | round | big | long
    tail: float = 0.3
    tail_kind: str = "thin"   # thin | bushy | tuft | hair | stub | spiky | fan | fluke | fin
    tail_ang: float = 0.5
    col: tuple = (170, 120, 80)
    belly: tuple | None = None
    pattern: str = ""         # spots | stripes | patches
    pat_col: tuple = (40, 30, 30)
    extras: tuple = ()        # mane | antlers | horn | horns | trunk | spines | whiskers | pouch | crest | hump
    flap_hz: float = 4.0
    wingspan: float = 0.6
    wag: float = 0.0          # idle tail wag strength


SPECIES: dict[str, Spec] = {
    "dog": Spec(L=0.62, Hb=0.24, leg=0.3, neck=0.16, head=0.1, snout=0.09, ears="flop", tail=0.24, tail_ang=0.9,
                col=(190, 140, 90), belly=(225, 196, 150), wag=1.0),
    "cat": Spec(L=0.45, Hb=0.17, leg=0.2, neck=0.1, head=0.075, snout=0.03, ears="point", tail=0.38, tail_ang=1.1,
                col=(120, 120, 130), pattern="stripes", pat_col=(80, 80, 90), extras=("whiskers",)),
    "wolf": Spec(L=1.0, Hb=0.32, leg=0.45, neck=0.22, head=0.13, snout=0.13, ears="point", tail=0.42,
                 tail_kind="bushy", tail_ang=0.1, col=(120, 118, 120), belly=(200, 196, 190)),
    "fox": Spec(L=0.62, Hb=0.2, leg=0.26, neck=0.14, head=0.09, snout=0.1, ears="point", tail=0.42, tail_kind="bushy",
                tail_ang=0.25, col=(210, 110, 40), belly=(245, 236, 220)),
    "horse": Spec(L=1.7, Hb=0.62, leg=0.9, neck=0.62, neck_ang=1.0, head=0.2, snout=0.3, ears="point", tail=0.75,
                  tail_kind="hair", tail_ang=-0.6, col=(140, 90, 55), extras=("mane",)),
    "unicorn": Spec(L=1.6, Hb=0.58, leg=0.88, neck=0.6, neck_ang=1.0, head=0.19, snout=0.28, ears="point", tail=0.75,
                    tail_kind="hair", tail_ang=-0.5, col=(246, 244, 252), extras=("mane", "horn")),
    "cow": Spec(L=1.7, Hb=0.75, leg=0.72, neck=0.3, neck_ang=0.3, head=0.2, snout=0.18, ears="flop", tail=0.7,
                tail_kind="tuft", tail_ang=-1.2, col=(245, 245, 240), pattern="patches", pat_col=(40, 36, 36),
                extras=("horns",)),
    "deer": Spec(L=1.3, Hb=0.45, leg=0.8, neck=0.48, neck_ang=1.1, head=0.13, snout=0.15, ears="point", tail=0.12,
                 tail_kind="stub", tail_ang=0.8, col=(170, 110, 60), belly=(235, 220, 200), extras=("antlers",)),
    "lion": Spec(L=1.7, Hb=0.6, leg=0.62, neck=0.3, neck_ang=0.5, head=0.22, snout=0.12, ears="round", tail=0.8,
                 tail_kind="tuft", tail_ang=-0.6, col=(214, 160, 80), extras=("mane_big", "whiskers")),
    "tiger": Spec(L=1.8, Hb=0.55, leg=0.6, neck=0.28, neck_ang=0.45, head=0.2, snout=0.1, ears="round", tail=0.9,
                  tail_kind="thin", tail_ang=-0.4, col=(230, 130, 40), belly=(245, 236, 220), pattern="stripes",
                  pat_col=(30, 24, 24), extras=("whiskers",)),
    "elephant": Spec(L=2.8, Hb=1.5, leg=1.3, neck=0.15, neck_ang=0.2, head=0.55, snout=0.0, ears="big", tail=0.6,
                     tail_kind="tuft", tail_ang=-1.3, col=(140, 140, 150), extras=("trunk",)),
    "bear": Spec(L=1.6, Hb=0.75, leg=0.55, neck=0.2, neck_ang=0.3, head=0.2, snout=0.12, ears="round", tail=0.08,
                 tail_kind="stub", col=(100, 70, 50)),
    "sheep": Spec(L=1.0, Hb=0.5, leg=0.45, neck=0.12, neck_ang=0.6, head=0.12, snout=0.08, ears="flop", tail=0.1,
                  tail_kind="stub", col=(240, 238, 230), extras=("fleece",)),
    "goat": Spec(L=1.0, Hb=0.4, leg=0.5, neck=0.25, neck_ang=0.9, head=0.11, snout=0.1, ears="flop", tail=0.1,
                 tail_kind="stub", tail_ang=1.0, col=(230, 226, 214), extras=("horns", "beard")),
    "camel": Spec(L=2.2, Hb=0.75, leg=1.2, neck=0.8, neck_ang=0.4, head=0.17, snout=0.2, ears="round", tail=0.4,
                  tail_kind="tuft", tail_ang=-1.2, col=(200, 160, 100), extras=("hump",)),
    "rabbit": Spec(L=0.35, Hb=0.18, leg=0.12, neck=0.06, neck_ang=1.0, head=0.075, snout=0.03, ears="long", tail=0.05,
                   tail_kind="stub", col=(200, 186, 170)),
    "crocodile": Spec(L=2.6, Hb=0.3, leg=0.18, neck=0.1, neck_ang=0.0, head=0.13, snout=0.5, ears="none", tail=1.6,
                      tail_kind="spiky", tail_ang=0.0, col=(80, 110, 60), belly=(170, 180, 120), extras=("spines",)),
    "lizard": Spec(L=0.2, Hb=0.06, leg=0.04, neck=0.03, neck_ang=0.0, head=0.035, snout=0.04, ears="none", tail=0.25,
                   tail_kind="thin", tail_ang=0.0, col=(110, 160, 70)),
    "turtle": Spec(L=0.5, Hb=0.25, leg=0.1, neck=0.1, neck_ang=0.3, head=0.06, snout=0.02, ears="none", tail=0.06,
                   tail_kind="stub", col=(110, 140, 80), extras=("shell",)),
    "dragon": Spec(rig="dragon", L=3.0, Hb=0.9, leg=1.0, neck=1.4, neck_ang=0.9, head=0.32, snout=0.45, ears="none",
                   tail=3.0, tail_kind="spiky", tail_ang=0.1, col=(170, 50, 50), belly=(240, 190, 110),
                   extras=("horns", "spines"), flap_hz=1.2, wingspan=4.5),
    "bird": Spec(rig="bird", L=0.22, Hb=0.11, leg=0.07, head=0.05, snout=0.035, tail=0.09, tail_kind="fan",
                 col=(90, 110, 160), belly=(220, 220, 230), flap_hz=6.0, wingspan=0.36),
    "eagle": Spec(rig="bird", L=0.75, Hb=0.26, leg=0.18, head=0.1, snout=0.08, tail=0.28, tail_kind="fan",
                  col=(100, 70, 45), belly=(120, 86, 56), extras=("white_head", "hook"), flap_hz=2.2, wingspan=2.0),
    "owl": Spec(rig="bird", L=0.4, Hb=0.26, leg=0.08, head=0.13, snout=0.03, tail=0.1, tail_kind="fan",
                col=(150, 110, 70), belly=(220, 200, 160), extras=("owl_face",), flap_hz=3.0, wingspan=1.0),
    "parrot": Spec(rig="bird", L=0.3, Hb=0.11, leg=0.06, head=0.06, snout=0.05, tail=0.25, tail_kind="fan",
                   col=(40, 170, 70), belly=(240, 200, 40), extras=("hook",), flap_hz=6.0, wingspan=0.5),
    "pelican": Spec(rig="bird", L=1.0, Hb=0.3, leg=0.25, head=0.1, snout=0.38, tail=0.15, tail_kind="fan",
                    col=(240, 240, 236), belly=(230, 230, 226), extras=("pouch",), flap_hz=1.6, wingspan=2.6),
    "fish": Spec(rig="fish", L=0.35, Hb=0.12, col=(240, 140, 50), belly=(250, 220, 170), tail_kind="fin",
                 pattern="stripes", pat_col=(250, 250, 250)),
    "shark": Spec(rig="fish", L=3.0, Hb=0.7, col=(110, 130, 150), belly=(230, 234, 236), tail_kind="fin",
                  extras=("tall_fin", "teeth")),
    "whale": Spec(rig="whale", L=12.0, Hb=2.6, col=(70, 90, 120), belly=(210, 214, 220), tail_kind="fluke"),
    "dolphin": Spec(rig="whale", L=2.4, Hb=0.5, col=(120, 140, 165), belly=(225, 230, 236), tail_kind="fluke",
                    extras=("beak", "dorsal")),
    "snake": Spec(rig="serpent", L=1.6, Hb=0.07, head=0.05, col=(80, 140, 60), belly=(200, 200, 120),
                  pattern="bands", pat_col=(40, 70, 30)),
    "serpent": Spec(rig="serpent", L=12.0, Hb=0.6, head=0.4, col=(40, 120, 120), belly=(170, 220, 190),
                    extras=("spines", "horns")),
    "butterfly": Spec(rig="butterfly", L=0.05, Hb=0.015, col=(250, 150, 40), pat_col=(30, 30, 30), flap_hz=9.0,
                      wingspan=0.09),
}
SYNONYMS = {"puppy": "dog", "hound": "dog", "kitten": "cat", "pony": "horse", "stallion": "horse", "mare": "horse",
            "calf": "cow", "bull": "cow", "ox": "cow", "buffalo": "cow", "stag": "deer", "doe": "deer",
            "lioness": "lion", "cub": "bear", "bunny": "rabbit", "hare": "rabbit", "lamb": "sheep", "alligator":
            "crocodile", "gecko": "lizard", "tortoise": "turtle", "wyvern": "dragon", "hawk": "eagle",
            "falcon": "eagle", "vulture": "eagle", "sparrow": "bird", "pigeon": "bird", "crow": "bird",
            "robin": "bird", "gull": "pelican", "seagull": "pelican", "goldfish": "fish", "salmon": "fish",
            "trout": "fish", "eel": "snake", "cobra": "snake", "python": "snake", "orca": "dolphin",
            "moth": "butterfly", "dinosaur": "crocodile", "leviathan": "serpent", "parakeet": "parrot",
            "macaw": "parrot", "wolves": "wolf", "mice": "rabbit", "mouse": "rabbit"}


def species_of(text: str) -> str | None:
    for w in re.findall(r"[a-z]+", (text or "").lower())[::-1]:
        w1 = SYNONYMS.get(w, w)
        if w1 in SPECIES:
            return w1
        if w.endswith("s") and SYNONYMS.get(w[:-1], w[:-1]) in SPECIES:
            return SYNONYMS.get(w[:-1], w[:-1])
    return None


def supports(text: str) -> bool:
    return species_of(text) is not None


def size(species: str, scale: float = 1.0) -> tuple:
    """(w, h) of the creature's bounding box in metres."""
    sp = SPECIES[species]
    if sp.rig in ("fish", "whale", "serpent"):
        return sp.L * scale, sp.Hb * 1.6 * scale
    if sp.rig == "bird":
        return sp.L * 1.3 * scale, (sp.leg + sp.Hb + sp.head * 2) * scale
    if sp.rig == "butterfly":
        return sp.wingspan * scale, sp.wingspan * scale
    return (sp.L + sp.neck * 0.6 + sp.head * 2 + sp.snout) * scale, (sp.leg + sp.Hb + sp.neck + sp.head) * scale


def prop(name: str, species: str, x: float, y: float = 0.0, z: float = 1.0, scale: float = 1.0, facing: float = 1.0,
         colour=None):
    """A creature as a scene prop: move it with prop.move / production "move" steps."""
    from .stick import Prop
    w, h = size(species, scale)
    p = Prop("shape", x, y, w, h, z=z, label=name, data={"kind": species, "parts": [], "flip": facing,
                                                         "scale": scale, "creature": True})
    if colour:
        p.data["colour"] = list(colour)
    p.name = name
    p.no_shadow = True
    return p


def act(p, t0: float, t1: float, what: str):
    p.data.setdefault("acts", []).append([t0, t1, what])


def _acts(p, t):
    out = {}
    for t0, t1, a in p.data.get("acts", []):
        if t0 <= t <= t1:
            k = min(1.0, (t - t0) / 0.35, (t1 - t) / 0.35)
            out[a] = max(out.get(a, 0.0), k * k * (3 - 2 * k))
    return out


# ---- drawing helpers (screen pixels) ----------------------------------------------------------------------------
def _cap(d, a, b, w0, w1, fill):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    d.polygon([(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
               (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)], fill=fill)
    for (x, y), w in ((a, w0), (b, w1)):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)


def _limb(d, pts, ws, fill, ink, o):
    for i in range(len(pts) - 1):
        _cap(d, pts[i], pts[i + 1], ws[i] + 2 * o, ws[i + 1] + 2 * o, ink)
    for i in range(len(pts) - 1):
        _cap(d, pts[i], pts[i + 1], ws[i], ws[i + 1], fill)


def _ell(d, c, rx, ry, ang, fill, ink=None, o=0, n=28):
    pts = []
    ca, sa = math.cos(ang), math.sin(ang)
    for k in range(n):
        a = TAU * k / n
        x, y = math.cos(a) * rx, math.sin(a) * ry
        pts.append((c[0] + x * ca - y * sa, c[1] + x * sa + y * ca))
    if ink is not None and o > 0:
        big = [(c[0] + (x - c[0]) * (1 + o / max(rx, 1)), c[1] + (y - c[1]) * (1 + o / max(ry, 1))) for x, y in pts]
        d.polygon(big, fill=ink)
    d.polygon(pts, fill=fill)
    return pts


def _dark(c, k=0.72):
    return tuple(int(v * k) for v in c[:3])


def _ik(root, target, l1, l2, bend):
    """Middle joint of a two-bone chain (screen coords); bend +1/-1 picks the side."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    dist = min(math.hypot(dx, dy), (l1 + l2) * 0.999) or 1e-6
    a = math.atan2(dy, dx)
    c = max(-1.0, min(1.0, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    ang = a + bend * math.acos(c)
    return root[0] + math.cos(ang) * l1, root[1] + math.sin(ang) * l1


def _eye(d, c, r, t, seed=0.0, blink=True, col=(20, 20, 24)):
    shut = blink and (t * 0.31 + seed) % 1.0 < 0.035
    if shut:
        d.line([(c[0] - r, c[1]), (c[0] + r, c[1])], fill=col, width=max(1, int(r * 0.5)))
        return
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(250, 250, 245))
    d.ellipse([c[0] - r * 0.6, c[1] - r * 0.6, c[0] + r * 0.6, c[1] + r * 0.6], fill=col)
    d.ellipse([c[0] - r * 0.15, c[1] - r * 0.45, c[0] + r * 0.15, c[1] - r * 0.15], fill=(255, 255, 255))


# ---- the rigs ---------------------------------------------------------------------------------------------------
GAITS = {  # footfall offsets (LH, LF, RH, RF), duty factor
    "walk": ((0.0, 0.25, 0.5, 0.75), 0.65),
    "trot": ((0.0, 0.5, 0.5, 0.0), 0.45),
    "gallop": ((0.0, 0.55, 0.1, 0.65), 0.35),
}


def _gait(speed, leg):
    fr = speed * speed / (9.8 * max(0.05, leg))     # Froude number: how animals choose their gait
    if fr < 0.4:                                     # walk-trot near 0.5, trot-gallop near 2.5 (Alexander)
        return "walk", 0.0
    if fr < 2.2:
        return "trot", min(1.0, (fr - 0.4) / 0.3)
    return "gallop", min(1.0, (fr - 2.2) / 0.6)


def _offsets(speed, leg):
    g, k = _gait(speed, leg)
    order = ["walk", "trot", "gallop"]
    i = order.index(g)
    prev = order[max(0, i - 1)]
    a, b = GAITS[prev], GAITS[g]
    offs = []
    for x0, x1 in zip(a[0], b[0]):                  # blend round the circle
        dd = (x1 - x0 + 0.5) % 1 - 0.5
        offs.append((x0 + dd * k) % 1)
    duty = a[1] + (b[1] - a[1]) * k
    return offs, duty, g


def foot_offset(u: float, duty: float, C: float, lift_h: float) -> tuple:
    """A foot's (offset ahead of its hip/shoulder, height) at gait phase u. In stance (u < duty) the offset falls by
    exactly the distance the body travels, so the foot stays planted on the ground; in swing it arcs forward."""
    if u < duty:
        return C * duty * (0.5 - u / duty), 0.0
    s_ = (u - duty) / (1 - duty)
    return C * duty * (-0.5 + s_), lift_h * math.sin(math.pi * s_)


def _quad(d, S, scale, sp, x, y, f, dist, speed, vy, t, acts, ink, o, colour, seed, wings=False, flying=False):
    leg, L, Hb = sp.leg, sp.L, sp.Hb
    mv = min(1.0, abs(speed) / 0.35)
    offs, duty, gait = _offsets(abs(speed), leg)
    C = leg * 2.7 + L * 0.3                         # distance per gait cycle
    ph = dist / C
    sit, lie, eat, roar, rear = (acts.get(k, 0.0) for k in ("sit", "lie", "eat", "roar", "rear"))
    sleep = acts.get("sleep", 0.0)
    lie = max(lie, sleep)
    air = (not flying) and abs(vy) > 0.6
    bob = 0.0
    if mv > 0 and not air:
        bob = (0.04 if gait != "gallop" else 0.09) * leg * (0.5 - 0.5 * math.cos(TAU * 2 * ph)) * mv
    pitch = (0.07 * math.sin(TAU * ph) * mv if gait == "gallop" else 0.0) + rear * 0.6
    breathe = 0.012 * Hb * math.sin(t * 2.2 + seed)
    body_y = y + leg + Hb * 0.5 - bob + breathe - lie * (leg + Hb * 0.05) - sit * leg * 0.15
    if flying:
        body_y = y + Hb * 0.5
    cx = x
    half = L * 0.4
    hip_drop = sit * (leg * 0.75)
    sh_w = (cx + f * half * math.cos(pitch), body_y + half * math.sin(pitch))
    hp_w = (cx - f * half * math.cos(pitch), body_y - half * math.sin(pitch) - hip_drop)
    P = S
    sh, hp = P(*sh_w), P(*hp_w)
    col = tuple(colour or sp.col)
    far = _dark(col, 0.74)
    leg_w = [Hb * 0.42 * scale, Hb * 0.22 * scale, Hb * 0.16 * scale]
    if "trunk" in sp.extras:
        leg_w = [Hb * 0.36 * scale, Hb * 0.32 * scale, Hb * 0.33 * scale]

    def foot_target(i, root_w, front):
        rel, lift = foot_offset((ph + offs[i]) % 1, duty, C, leg * (0.22 if front else 0.18))
        rest = 0.04 * L if front else -0.02 * L
        rel = rest * (1 - mv) + rel * mv
        lift *= mv
        if air or flying:                             # stretched out in the air / tucked in flight
            k = 1.0 if not flying else 0.5
            rel = (leg * 0.55 if front else -leg * 0.6) * (1 if vy > 0 or flying else 0.4) * k
            lift = leg * (0.3 if flying else 0.12)
        gy = y if not flying else body_y - Hb * 0.5 - leg * 0.8
        fx = root_w[0] + f * rel
        fy = gy + lift
        if lie > 0:                                   # legs fold under the body
            fx, fy = fx * (1 - lie) + (root_w[0] + f * (leg * 0.5 if front else -leg * 0.3)) * lie, \
                fy * (1 - lie) + (y + 0.02) * lie
        if not front and sit > 0:                     # haunches down, hind feet forward
            fx, fy = fx * (1 - sit) + (root_w[0] + f * leg * 0.35) * sit, fy
        if front and eat > 0:
            fx = fx + f * 0.05 * leg * eat
        if front and rear > 0:
            fx, fy = fx * (1 - rear) + (root_w[0] + f * leg * 0.25) * rear, fy * (1 - rear) + (root_w[1] - leg * 0.35) * rear
        return fx, fy

    def draw_leg(i, front, dim):
        root_w = (sh_w if front else hp_w)
        root_w = (root_w[0], root_w[1] - Hb * 0.25)
        foot = foot_target(i, root_w, front)
        r, ft = P(*root_w), P(*foot)
        l1, l2, l3 = leg * 0.5 * scale, leg * 0.42 * scale, leg * 0.2 * scale
        if front:                                     # elbow back, then the pastern
            wrist = (ft[0], ft[1] - l3 * 0.85)
            mid = _ik(r, wrist, l1, l2, 1 if f > 0 else -1)
        else:                                         # stifle forward, hock back
            wrist = (ft[0] - f * l3 * 0.45, ft[1] - l3 * 0.8)
            mid = _ik(r, wrist, l1, l2, -1 if f > 0 else 1)
        c = far if dim else col
        _limb(d, [r, mid, wrist, ft], leg_w + [leg_w[-1] * 0.9], c, ink, o)
        pw = leg_w[-1] * 0.75
        d.ellipse([ft[0] - pw * 0.6 + f * pw * 0.3, ft[1] - pw * 0.45, ft[0] + pw * 0.6 + f * pw * 0.3, ft[1] + pw * 0.2],
                  fill=_dark(c, 0.55) if "horse" not in sp.extras else (40, 34, 30))
    # far legs behind
    draw_leg(2, False, True)
    draw_leg(3, True, True)
    if wings:
        _dragon_wing(d, S, scale, sp, sh_w, f, t, flying, ink, o, _dark(col, 0.62), far=True)
    # tail
    base = (hp_w[0] - f * Hb * 0.25, hp_w[1] + Hb * 0.2)
    _tail(d, S, scale, sp, base, f, t, speed, acts, ink, o, col, seed)
    # body
    bw = Hb * scale
    _limb(d, [hp, sh], [bw * 0.92, bw * 1.0], col, ink, o)
    if "hump" in sp.extras:
        hx, hy = P(cx, body_y + Hb * 0.45)
        _ell(d, (hx, hy), Hb * 0.45 * scale, Hb * 0.35 * scale, 0, col, ink, o)
        _ell(d, (hx, hy + Hb * 0.12 * scale), Hb * 0.44 * scale, Hb * 0.3 * scale, 0, col)
        _limb(d, [hp, sh], [bw * 0.92, bw * 1.0], col, None, 0) if False else None
    if "fleece" in sp.extras:
        for k in range(9):
            u = k / 8
            px = hp[0] + (sh[0] - hp[0]) * u
            py = hp[1] + (sh[1] - hp[1]) * u
            for dy in (-0.32, 0.0, 0.3):
                r_ = bw * 0.24
                d.ellipse([px - r_, py + dy * bw - r_, px + r_, py + dy * bw + r_], fill=(250, 248, 240), outline=_dark(col, 0.8))
    if "shell" in sp.extras:
        cx_, cy_ = P(cx, body_y + Hb * 0.1)
        d.chord([cx_ - L * 0.55 * scale, cy_ - Hb * 1.0 * scale, cx_ + L * 0.55 * scale, cy_ + Hb * 0.9 * scale], 180,
                360, fill=(120, 100, 60), outline=ink, width=max(1, int(o)))
        for k in (-1, 0, 1):
            d.line([(cx_ + k * L * 0.2 * scale, cy_ - Hb * 0.8 * scale), (cx_ + k * L * 0.25 * scale, cy_)], fill=ink,
                   width=max(1, int(o)))
    if sp.belly:                                      # a lighter underside, inside the body outline
        bc = tuple(int(a * 0.55 + b * 0.45) for a, b in zip(sp.belly, col))
        bl = [(hp[0] + (sh[0] - hp[0]) * 0.22, hp[1] + bw * 0.28), (sh[0] - (sh[0] - hp[0]) * 0.12, sh[1] + bw * 0.26)]
        _cap(d, bl[0], bl[1], bw * 0.3, bw * 0.36, bc)
    _pattern(d, sp, hp, sh, bw, seed)
    if "spines" in sp.extras:
        for k in range(9):
            u = 0.05 + 0.9 * k / 8
            px = hp[0] + (sh[0] - hp[0]) * u
            py = hp[1] + (sh[1] - hp[1]) * u - bw * 0.48
            s_ = bw * 0.28
            d.polygon([(px - s_ * 0.5, py + s_ * 0.3), (px + f * s_ * 0.3, py - s_), (px + s_ * 0.5, py + s_ * 0.3)],
                      fill=_dark(col, 0.6), outline=ink)
    # near legs
    draw_leg(0, False, False)
    draw_leg(1, True, False)
    # neck and head
    look = 0.0 if mv > 0.2 else 0.18 * math.sin(t * 0.45 + seed * 3)
    nb = -0.06 * math.sin(TAU * 2 * ph) * mv
    na = sp.neck_ang + nb + look - eat * (sp.neck_ang + 1.0) + roar * 0.3 + rear * 0.3 - lie * 0.2
    if sleep:
        na = -0.2
    n0w = (sh_w[0] + f * Hb * 0.15, sh_w[1] + Hb * 0.25)
    n1w = (n0w[0] + f * math.cos(na) * sp.neck, n0w[1] + math.sin(na) * sp.neck)
    if eat > 0:
        n1w = (n1w[0], max(y + sp.head * 1.1, n1w[1]))
    n0, n1 = P(*n0w), P(*n1w)
    if "mane_big" in sp.extras:                       # the mane sits behind the head
        hr = sp.head * scale
        hcx, hcy = P(*n1w)
        for k in range(14):
            a = TAU * k / 14
            d.ellipse([hcx + math.cos(a) * hr * 1.1 - hr * 0.55, hcy + math.sin(a) * hr * 1.1 - hr * 0.55,
                       hcx + math.cos(a) * hr * 1.1 + hr * 0.55, hcy + math.sin(a) * hr * 1.1 + hr * 0.55],
                      fill=(150, 90, 40), outline=ink)
    if sp.neck > 0.05:
        _limb(d, [n0, n1], [Hb * 0.55 * scale, sp.head * 1.3 * scale], col, ink, o)
        if "mane" in sp.extras:
            for k in range(7):
                u = k / 6
                px, py = n0[0] + (n1[0] - n0[0]) * u, n0[1] + (n1[1] - n0[1]) * u
                sw = math.sin(t * 3 + k) * Hb * 0.04 * scale - f * min(abs(speed), 8) * 0.012 * scale
                d.polygon([(px - f * Hb * 0.25 * scale, py - Hb * 0.05 * scale),
                           (px - f * Hb * 0.5 * scale + sw, py + Hb * 0.2 * scale),
                           (px - f * Hb * 0.15 * scale, py + Hb * 0.12 * scale)], fill=(70, 40, 25))
    _head(d, S, scale, sp, n1w, f, t, acts, ink, o, col, seed, speed)
    if wings:
        _dragon_wing(d, S, scale, sp, sh_w, f, t, flying, ink, o, _dark(col, 0.85), far=False)
    if acts.get("breathe_fire", 0.0) > 0:
        _fire(d, S, scale, sp, n1w, f, t, acts["breathe_fire"])
    return body_y


def _pattern(d, sp, hp, sh, bw, seed):
    if not sp.pattern:
        return
    pc = tuple(sp.pat_col)
    import random
    rng = random.Random(seed + 7)
    if sp.pattern in ("spots", "patches"):
        for k in range(6 if sp.pattern == "patches" else 12):
            u = rng.uniform(0.15, 0.85)
            v = rng.uniform(-0.25, 0.2)
            px = hp[0] + (sh[0] - hp[0]) * u
            py = hp[1] + (sh[1] - hp[1]) * u + v * bw
            r = bw * (rng.uniform(0.12, 0.22) if sp.pattern == "patches" else 0.06)
            d.ellipse([px - r * 1.3, py - r, px + r * 1.3, py + r], fill=pc)
    elif sp.pattern == "stripes":
        for k in range(8):
            u = 0.12 + 0.76 * k / 7
            px = hp[0] + (sh[0] - hp[0]) * u
            py = hp[1] + (sh[1] - hp[1]) * u
            d.line([(px, py - bw * 0.46), (px - bw * 0.08, py - bw * 0.05)], fill=pc, width=max(2, int(bw * 0.07)))


def _head(d, S, scale, sp, hw, f, t, acts, ink, o, col, seed, speed):
    hr = sp.head * scale
    hc = S(*hw)
    roar = max(acts.get("roar", 0.0), 0.0)
    if sp.ears in ("point", "round", "long", "big"):   # far ear first
        _ear(d, sp, hc, hr, f, t, ink, o, _dark(col), far=True)
    _ell(d, hc, hr * 1.05, hr * 0.92, 0, col, ink, o)
    if sp.snout > 0:
        tip = (hc[0] + f * (hr * 0.6 + sp.snout * scale), hc[1] + hr * 0.25)
        _limb(d, [(hc[0] + f * hr * 0.3, hc[1] + hr * 0.05), tip], [hr * 1.1, hr * 0.6], col, ink, o)
        d.ellipse([tip[0] - hr * 0.16, tip[1] - hr * 0.22, tip[0] + hr * 0.16, tip[1] + hr * 0.02], fill=(30, 26, 26))
        mo = roar * hr * 0.55 + acts.get("eat", 0.0) * hr * 0.15 * (0.5 + 0.5 * math.sin(t * 12))
        if mo > 1:
            d.polygon([(tip[0] - f * sp.snout * scale * 0.9, tip[1] + hr * 0.12), (tip[0], tip[1] + hr * 0.12),
                       (tip[0] - f * sp.snout * scale * 0.1, tip[1] + hr * 0.12 + mo)], fill=(110, 30, 40), outline=ink)
            if "teeth" in sp.extras or sp.rig == "dragon" or sp.L > 1.4:
                for k in range(3):
                    tx = tip[0] - f * (k + 0.5) * sp.snout * scale * 0.25
                    d.polygon([(tx - hr * 0.05, tip[1] + hr * 0.12), (tx + hr * 0.05, tip[1] + hr * 0.12),
                               (tx, tip[1] + hr * 0.3)], fill=(250, 250, 240))
        else:
            d.line([(tip[0] - f * sp.snout * scale * 0.7, tip[1] + hr * 0.12), (tip[0], tip[1] + hr * 0.1)],
                   fill=ink, width=max(1, int(o)))
    if "trunk" in sp.extras:
        pts = [(hc[0] + f * hr * 0.7, hc[1] + hr * 0.1)]
        sw = math.sin(t * 1.3 + seed) * 0.25 + roar * 1.4
        a = math.pi / 2 - f * 0.3
        for k in range(6):
            a += f * (0.12 + sw * 0.12)
            pts.append((pts[-1][0] + math.cos(a) * hr * 0.32 * f * (1 if f > 0 else -1) * (1 if f > 0 else -1),
                        pts[-1][1] + math.sin(a) * hr * 0.32))
        _limb(d, pts, [hr * (0.42 - 0.04 * k) for k in range(len(pts))], col, ink, o)
        tusk = (hc[0] + f * hr * 0.75, hc[1] + hr * 0.45)
        d.line([tusk, (tusk[0] + f * hr * 0.5, tusk[1] + hr * 0.2), (tusk[0] + f * hr * 0.75, tusk[1] - hr * 0.05)],
               fill=(250, 246, 230), width=max(2, int(hr * 0.12)))
    eye = (hc[0] + f * hr * 0.35, hc[1] - hr * 0.18)
    if acts.get("sleep", 0.0) > 0.5:
        d.arc([eye[0] - hr * 0.18, eye[1] - hr * 0.1, eye[0] + hr * 0.18, eye[1] + hr * 0.15], 20, 160, fill=ink,
              width=max(1, int(o)))
    else:
        _eye(d, eye, hr * 0.17, t, seed)
    if sp.ears in ("point", "round", "flop", "long", "big"):
        _ear(d, sp, hc, hr, f, t, ink, o, col, far=False)
    if "horn" in sp.extras:
        b = (hc[0] + f * hr * 0.3, hc[1] - hr * 0.8)
        d.polygon([(b[0] - hr * 0.12, b[1]), (b[0] + f * hr * 0.5, b[1] - hr * 1.3), (b[0] + hr * 0.12, b[1])],
                  fill=(240, 210, 120), outline=ink)
    if "horns" in sp.extras:
        for k in (0, 1):
            b = (hc[0] - f * hr * (0.1 + 0.3 * k), hc[1] - hr * 0.75)
            d.polygon([(b[0] - hr * 0.1, b[1]), (b[0] - f * hr * 0.55, b[1] - hr * 0.75), (b[0] + hr * 0.12, b[1])],
                      fill=(236, 226, 200) if k == 0 else (200, 190, 170), outline=ink)
    if "antlers" in sp.extras:
        b = (hc[0] - f * hr * 0.1, hc[1] - hr * 0.8)
        w_ = max(2, int(hr * 0.12))
        top = (b[0] - f * hr * 0.6, b[1] - hr * 2.0)
        d.line([b, top], fill=(150, 110, 70), width=w_)
        for k in range(3):
            q = (b[0] + (top[0] - b[0]) * (0.35 + 0.25 * k), b[1] + (top[1] - b[1]) * (0.35 + 0.25 * k))
            d.line([q, (q[0] + f * hr * 0.45, q[1] - hr * 0.5)], fill=(150, 110, 70), width=w_)
    if "whiskers" in sp.extras:
        wx, wy = hc[0] + f * (hr * 0.75 + sp.snout * scale), hc[1] + hr * 0.25
        for k in (-1, 0, 1):
            d.line([(wx, wy), (wx + f * hr * 0.8, wy + k * hr * 0.2)], fill=(240, 240, 240), width=1)
    if "beard" in sp.extras:
        bx, by = hc[0] + f * (hr * 0.4 + sp.snout * scale * 0.6), hc[1] + hr * 0.6
        d.polygon([(bx - hr * 0.15, by), (bx + hr * 0.15, by), (bx, by + hr * 0.6)], fill=(210, 206, 196))


def _ear(d, sp, hc, hr, f, t, ink, o, col, far):
    off = -f * hr * (0.15 if not far else 0.4)
    bx, by = hc[0] + off, hc[1] - hr * 0.6
    tw = math.sin(t * 0.7 + (3 if far else 0)) * hr * 0.05
    if sp.ears == "point":
        d.polygon([(bx - hr * 0.3, by + hr * 0.15), (bx - f * hr * 0.05 + tw, by - hr * 0.75), (bx + hr * 0.3, by + hr * 0.15)],
                  fill=col, outline=ink)
    elif sp.ears == "round":
        d.ellipse([bx - hr * 0.28, by - hr * 0.35, bx + hr * 0.28, by + hr * 0.15], fill=col, outline=ink)
    elif sp.ears == "long":
        _ell(d, (bx - f * hr * 0.1 + tw, by - hr * 0.9), hr * 0.22, hr * 0.85, -f * 0.15, col, ink, o)
    elif sp.ears == "flop" and not far:
        d.polygon([(bx - f * hr * 0.2, by + hr * 0.05), (bx + f * hr * 0.25, by), (bx + f * hr * 0.05 + tw, by + hr * 0.95),
                   (bx - f * hr * 0.25, by + hr * 0.8)], fill=_dark(col, 0.78), outline=ink)
    elif sp.ears == "big" and not far:
        flap = math.sin(t * 1.6) * hr * 0.08
        d.polygon([(bx + f * hr * 0.1, by + hr * 0.1), (bx - f * hr * 0.9 + flap, by - hr * 0.2),
                   (bx - f * hr * 1.05 + flap, by + hr * 0.9), (bx - f * hr * 0.2, by + hr * 1.2)],
                  fill=_dark(col, 0.85), outline=ink)


def _tail(d, S, scale, sp, base, f, t, speed, acts, ink, o, col, seed):
    if sp.tail <= 0:
        return
    wag = max(sp.wag * 0.6, acts.get("wag", 0.0) * 1.0)
    drag = min(1.0, abs(speed) / 4.0)
    n = 6
    pts = [S(*base)]
    a = sp.tail_ang * (1 - drag * 0.7) - drag * 0.1
    seg = sp.tail * scale / n
    for k in range(n):
        u = (k + 1) / n
        sw = (wag * 0.5 * math.sin(t * 11 - k * 0.6) + 0.12 * math.sin(t * 1.7 + seed - k * 0.5)) * u
        ang = a + sw
        px, py = pts[-1]
        pts.append((px - f * math.cos(ang) * seg, py - math.sin(ang) * seg))
        a += (-0.12 if sp.tail_kind in ("hair", "tuft") else 0.05)
    w0 = sp.Hb * scale * {"bushy": 0.35, "hair": 0.3, "spiky": 0.45, "thin": 0.13, "tuft": 0.08, "stub": 0.25}.get(sp.tail_kind, 0.12)
    ws = [w0 * (1 - 0.6 * k / n) if sp.tail_kind not in ("bushy",) else w0 * (0.6 + 0.6 * math.sin(math.pi * k / n))
          for k in range(n + 1)]
    c = col if sp.tail_kind != "hair" else (70, 40, 25)
    _limb(d, pts, ws, c, ink, o)
    if sp.tail_kind == "bushy":
        tip = pts[-1]
        d.ellipse([tip[0] - w0 * 0.4, tip[1] - w0 * 0.4, tip[0] + w0 * 0.4, tip[1] + w0 * 0.4], fill=(250, 250, 245))
    if sp.tail_kind == "tuft":
        tip = pts[-1]
        r = w0 * 1.6
        d.ellipse([tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r * 1.4], fill=(60, 40, 30))
    if sp.tail_kind == "spiky":
        for k in range(1, n):
            px, py = pts[k]
            s_ = ws[k] * 0.8
            d.polygon([(px - s_ * 0.4, py - ws[k] * 0.4), (px, py - ws[k] * 0.4 - s_), (px + s_ * 0.4, py - ws[k] * 0.4)],
                      fill=_dark(col, 0.6))


def _dragon_wing(d, S, scale, sp, sh_w, f, t, flying, ink, o, col, far):
    span = sp.wingspan * scale * (0.85 if far else 1.0)
    if flying:
        th = math.sin(TAU * sp.flap_hz * t) * 0.9 + 0.25
    else:                                             # folded along the back, breathing a little
        span *= 0.55
        th = 0.55 + 0.05 * math.sin(t * 1.2)
    root = S(sh_w[0] - f * sp.Hb * 0.2, sh_w[1] + sp.Hb * 0.35)
    elbow = (root[0] - f * math.cos(th) * span * 0.35, root[1] - math.sin(th) * span * 0.35)
    lag = th * 1.25 - 0.2 if flying else th + 0.4
    wrist = (elbow[0] - f * math.cos(lag) * span * 0.35, elbow[1] - math.sin(lag) * span * 0.35)
    tips = []
    for k in range(4):
        a = lag - 0.35 - k * 0.45
        tips.append((wrist[0] - f * math.cos(a) * span * (0.5 - k * 0.06), wrist[1] - math.sin(a) * span * (0.5 - k * 0.06)))
    back = (root[0] - f * sp.L * scale * 0.55, root[1] + sp.Hb * scale * 0.1)
    memb = [root, elbow, wrist] + tips + [back]
    d.polygon(memb, fill=_dark(col, 0.9) if far else (min(255, col[0] + 30), min(255, col[1] + 20), col[2]), outline=ink)
    for tp in tips:
        d.line([wrist, tp], fill=ink, width=max(1, int(o)))
    d.line([root, elbow, wrist], fill=ink, width=max(2, int(o * 2)))


def _fire(d, S, scale, sp, hw, f, t, k):
    import random
    rng = random.Random(int(t * 30))
    hc = S(*hw)
    mouth = (hc[0] + f * (sp.head + sp.snout) * scale * 1.1, hc[1] + sp.head * scale * 0.3)
    for i in range(60):
        u = rng.random()
        dist = u * 5.0 * scale * k
        spread = (rng.random() - 0.5) * u * 1.2 * scale
        x, y = mouth[0] + f * dist, mouth[1] + spread + u * u * 0.6 * scale
        r = (0.08 + u * 0.4) * scale
        core = 1 - u
        col = (255, int(60 + 190 * core * core), int(10 + 120 * core ** 3), int(255 * (1 - 0.65 * u)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def _bird(d, S, scale, sp, x, y, f, dist, speed, vy, t, acts, ink, o, colour, seed, flying):
    col = tuple(colour or sp.col)
    L, Hb = sp.L, sp.Hb
    by = y + (sp.leg + Hb * 0.5 if not flying else Hb * 0.5)
    hop = 0.0
    if not flying and abs(speed) > 0.05:
        hop = abs(math.sin(dist / (L * 1.2) * math.pi)) * sp.leg * 0.6
    by += hop
    pitch = max(-0.5, min(0.5, math.atan2(vy, max(0.5, abs(speed))))) if flying else 0.12 * math.sin(t * 2 + seed)
    c = S(x, by)
    bl, bh = L * 0.5 * scale, Hb * 0.5 * scale
    if not flying:
        for k, dk in ((0, 0.0), (1, 0.5)):           # two thin legs
            ph = (dist / (L * 1.2) + dk) % 1
            fx = x + f * (0.02 * L + 0.05 * L * math.sin(TAU * ph) * min(1, abs(speed) * 4))
            top, ft = S(x - f * L * 0.05, by - Hb * 0.3), S(fx, y + hop * 0)
            mid = _ik(top, ft, sp.leg * 0.55 * scale, sp.leg * 0.55 * scale, -1 if f > 0 else 1)
            d.line([top, mid, ft], fill=(230, 150, 50) if k == 0 else (190, 120, 40), width=max(1, int(scale * Hb * 0.06)))
    flap = math.sin(TAU * sp.flap_hz * t + seed)
    span = sp.wingspan * 0.5 * scale

    def wing(dim):
        cc = _dark(col, 0.7) if dim else _dark(col, 0.9)
        root = (c[0] - f * bl * 0.1, c[1] - bh * 0.4)
        if flying:
            glide = vy < -0.3 and abs(speed) > 1.0
            th = 0.25 if glide else flap * 0.95 + 0.15
            lag = th * 1.3 - 0.15 if not glide else 0.2
        else:
            th, lag = -0.25, -0.15
        if not flying:                                # folded on the body
            _ell(d, (c[0] - f * bl * 0.15, c[1] - bh * 0.05), bl * 0.75, bh * 0.6, -f * 0.12, cc, ink, o)
            return
        elbow = (root[0] - f * math.cos(th) * span * 0.45 * 0.3, root[1] - math.sin(th) * span * 0.45)
        tip = (elbow[0] - f * math.cos(lag) * span * 0.2, elbow[1] - math.sin(lag) * span * 0.6)
        trail = [(tip[0] - f * span * 0.25, tip[1] + span * 0.08), (elbow[0] - f * span * 0.35, elbow[1] + span * 0.15),
                 (root[0] - f * bl * 0.6, root[1] + bh * 0.4)]
        d.polygon([root, elbow, tip] + trail, fill=cc, outline=ink)
        for k in range(4):                             # feather tips on the trailing edge
            u = k / 4
            px = tip[0] + (trail[1][0] - tip[0]) * u
            py = tip[1] + (trail[1][1] - tip[1]) * u
            d.line([(px, py), (px - f * span * 0.08, py + span * 0.1)], fill=ink, width=max(1, int(o)))
    if flying:
        wing(True)
    tail_base = (c[0] - f * bl * 0.85, c[1])
    tail_tip = (tail_base[0] - f * sp.tail * scale, tail_base[1] + sp.tail * scale * (0.15 + 0.1 * math.sin(t * 3)))
    d.polygon([tail_base, (tail_tip[0], tail_tip[1] - sp.tail * scale * 0.25), (tail_tip[0], tail_tip[1] + sp.tail * scale * 0.2)],
              fill=_dark(col, 0.8), outline=ink)
    _ell(d, c, bl, bh, -f * pitch, col, ink, o)
    if sp.belly:
        _ell(d, (c[0] + f * bl * 0.15, c[1] + bh * 0.35), bl * 0.6, bh * 0.5, -f * pitch, tuple(sp.belly))
    hr = sp.head * scale
    hc = (c[0] + f * bl * 0.95, c[1] - bh * 0.6 - (0.0 if flying else hr * 0.3 + hr * 0.15 * math.sin(t * 3 + seed)))
    hcol = (250, 250, 250) if "white_head" in sp.extras else col
    if "owl_face" in sp.extras:
        hc = (c[0] + f * bl * 0.3, c[1] - bh * 1.2)
    _ell(d, hc, hr, hr, 0, hcol, ink, o)
    bk = sp.snout * scale
    if "pouch" in sp.extras:
        d.polygon([(hc[0] + f * hr * 0.6, hc[1] - hr * 0.1), (hc[0] + f * (hr + bk), hc[1] + hr * 0.1),
                   (hc[0] + f * hr * 0.6, hc[1] + hr * 0.25)], fill=(240, 170, 60), outline=ink)
        d.chord([hc[0] + f * hr * 0.2 - (bk if f < 0 else 0), hc[1], hc[0] + f * hr * 0.2 + (bk if f > 0 else 0), hc[1] + hr * 1.3],
                0, 180, fill=(250, 200, 120), outline=ink)
    elif "hook" in sp.extras:
        d.polygon([(hc[0] + f * hr * 0.7, hc[1] - hr * 0.35), (hc[0] + f * (hr + bk), hc[1] - hr * 0.1),
                   (hc[0] + f * (hr + bk * 0.8), hc[1] + hr * 0.4), (hc[0] + f * hr * 0.7, hc[1] + hr * 0.25)],
                  fill=(240, 200, 60), outline=ink)
    else:
        d.polygon([(hc[0] + f * hr * 0.7, hc[1] - hr * 0.25), (hc[0] + f * (hr + bk), hc[1] + hr * 0.05),
                   (hc[0] + f * hr * 0.7, hc[1] + hr * 0.3)], fill=(240, 180, 50), outline=ink)
    if "owl_face" in sp.extras:
        for k in (-1, 1):
            e = (hc[0] + k * hr * 0.42, hc[1] - hr * 0.1)
            d.ellipse([e[0] - hr * 0.38, e[1] - hr * 0.38, e[0] + hr * 0.38, e[1] + hr * 0.38], fill=(250, 240, 210))
            _eye(d, e, hr * 0.25, t, seed + k)
    else:
        _eye(d, (hc[0] + f * hr * 0.35, hc[1] - hr * 0.2), hr * 0.24, t, seed)
    if flying:
        wing(False)
    else:
        wing(False)


def _fish(d, S, scale, sp, x, y, f, dist, speed, t, ink, o, colour, seed, whale=False):
    col = tuple(colour or sp.col)
    L, Hb = sp.L, sp.Hb
    n = 12
    beat = 2.2 + min(3.0, abs(speed) / max(0.2, L) * 1.2)
    ph = t * beat * TAU + seed
    spine = []
    for k in range(n + 1):
        u = k / n                                    # 0 head .. 1 tail
        amp = (0.02 + 0.10 * u * u) * Hb * (1.6 if whale else 0.6)
        sx = x + f * L * (0.5 - u)
        sy = y + amp * math.sin(ph - u * 4.0)
        spine.append((sx, sy))
    prof = [Hb * 0.5 * math.sin(math.pi * min(1.0, (k / n) * 1.05 + 0.08)) ** 0.7 for k in range(n + 1)]
    top = [S(sx, sy + w) for (sx, sy), w in zip(spine, prof)]
    bot = [S(sx, sy - w * (0.95 if not whale else 0.8)) for (sx, sy), w in zip(spine, prof)]
    tail = S(*spine[-1])
    if whale:                                        # fluke: seen side-on it tilts with the beat
        a = math.cos(ph - 4.0) * 0.9
        fl = Hb * 0.9 * scale
        d.polygon([tail, (tail[0] - f * fl * 0.9, tail[1] - fl * 0.25 - math.sin(a) * fl * 0.6),
                   (tail[0] - f * fl * 0.5, tail[1]), (tail[0] - f * fl * 0.9, tail[1] + fl * 0.25 - math.sin(a) * fl * 0.6)],
                  fill=_dark(col, 0.85), outline=ink)
    else:                                            # a vertical fin sweeping side to side: its width foreshortens
        sw = abs(math.cos(ph - 4.0)) * 0.6 + 0.4
        fl = Hb * 0.9 * scale
        d.polygon([tail, (tail[0] - f * fl * 0.8 * sw, tail[1] - fl * 0.6), (tail[0] - f * fl * 0.45 * sw, tail[1]),
                   (tail[0] - f * fl * 0.8 * sw, tail[1] + fl * 0.6 * (0.6 if "tall_fin" in sp.extras else 1.0))],
                  fill=_dark(col, 0.85), outline=ink)
    body = top + bot[::-1]
    if o > 0:
        d.polygon(body, fill=ink)
        d.line(body + [body[0]], fill=ink, width=int(o * 2))
    d.polygon(body, fill=col)
    if sp.belly:
        bel = [S(sx, sy - w * 0.15) for (sx, sy), w in zip(spine, prof)] + bot[::-1]
        d.polygon(bel, fill=tuple(sp.belly))
    if sp.pattern == "stripes":
        for k in (3, 6, 9):
            d.line([top[k], bot[k]], fill=tuple(sp.pat_col), width=max(2, int(Hb * scale * 0.12)))
    fin_k = 4 if "tall_fin" not in sp.extras else 5
    ftop = top[fin_k]
    if not whale or "dorsal" in sp.extras:
        hgt = Hb * scale * (0.8 if "tall_fin" in sp.extras else 0.4)
        d.polygon([ftop, (ftop[0] - f * hgt * 0.6, ftop[1] - hgt), top[fin_k + 2]], fill=_dark(col, 0.85), outline=ink)
    pec = S(spine[3][0], spine[3][1] - Hb * 0.15)
    pa = math.sin(ph * 0.7) * 0.5
    d.polygon([pec, (pec[0] - f * Hb * scale * 0.5, pec[1] + Hb * scale * (0.25 + 0.15 * pa)),
               (pec[0] - f * Hb * scale * 0.2, pec[1] + Hb * scale * 0.05)], fill=_dark(col, 0.8), outline=ink)
    head = S(*spine[1])
    e = (head[0] + f * Hb * scale * 0.05, head[1] - Hb * scale * 0.12)
    _eye(d, e, Hb * scale * (0.07 if whale else 0.12), t, seed)
    mouth = S(*spine[0])
    d.line([(mouth[0] - f * Hb * scale * 0.25, mouth[1] + Hb * scale * 0.08), (mouth[0], mouth[1] + Hb * scale * 0.05)],
           fill=ink, width=max(1, int(o)))
    if "teeth" in sp.extras:
        for k in range(4):
            tx = mouth[0] - f * Hb * scale * (0.05 + 0.05 * k)
            d.polygon([(tx - 2, mouth[1] + Hb * scale * 0.08), (tx + 2, mouth[1] + Hb * scale * 0.08),
                       (tx, mouth[1] + Hb * scale * 0.14)], fill=(250, 250, 250))


def _serpent(d, S, scale, sp, p, t, f, ink, o, colour, seed):
    col = tuple(colour or sp.col)
    n = 26
    seg = sp.L / n
    pts = [p.pos(t)[:2]]
    tt, back = t, 0.0
    while len(pts) <= n and tt > -30:                # walk back along where the head has been
        tt -= 0.02
        q = p.pos(max(0.0, tt))[:2] if tt > 0 else (pts[-1][0] - f * seg, pts[-1][1])
        dd = math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1])
        back += dd
        if back >= seg:
            pts.append(q)
            back = 0.0
        if tt <= 0:
            while len(pts) <= n:
                pts.append((pts[-1][0] - f * seg, pts[-1][1]))
    spine = []
    for k, (sx, sy) in enumerate(pts):
        u = k / n
        hump = sp.Hb * (1.6 if sp.L > 4 else 0.8) * math.sin(t * 2.4 - u * 9 + seed) * (0.3 + 0.7 * u) * (1 - 0.3 * u)
        spine.append((sx, sy + max(0.0, hump) + sp.Hb * 0.5))
    ws = [sp.Hb * scale * (1.0 - 0.75 * (k / n) ** 1.5) for k in range(n + 1)]
    scr = [S(*q) for q in spine]
    _limb(d, scr[::-1], ws[::-1], col, ink, o)
    if sp.pattern == "bands":
        for k in range(2, n, 3):
            a, b = scr[k], scr[k + 1]
            d.line([a, b], fill=tuple(sp.pat_col), width=max(2, int(ws[k] * 0.9)))
    if sp.belly:
        for k in range(n):
            d.line([(scr[k][0], scr[k][1] + ws[k] * 0.3), (scr[k + 1][0], scr[k + 1][1] + ws[k + 1] * 0.3)],
                   fill=tuple(sp.belly), width=max(1, int(ws[k] * 0.3)))
    if "spines" in sp.extras:
        for k in range(1, n, 2):
            x_, y_ = scr[k]
            s_ = ws[k] * 0.6
            d.polygon([(x_ - s_ * 0.4, y_ - ws[k] * 0.45), (x_, y_ - ws[k] * 0.45 - s_), (x_ + s_ * 0.4, y_ - ws[k] * 0.45)],
                      fill=_dark(col, 0.6))
    h = scr[0]
    hr = sp.head * scale
    _ell(d, (h[0] + f * hr * 0.3, h[1]), hr * 1.3, hr * 0.8, 0, col, ink, o)
    _eye(d, (h[0] + f * hr * 0.6, h[1] - hr * 0.25), hr * 0.22, t, seed)
    if "horns" in sp.extras:
        d.polygon([(h[0] - f * hr * 0.2, h[1] - hr * 0.6), (h[0] - f * hr * 1.1, h[1] - hr * 1.4), (h[0], h[1] - hr * 0.7)],
                  fill=(236, 226, 200), outline=ink)
    if (t * 0.8 + seed) % 1 < 0.15:                 # the tongue flicks
        tip = (h[0] + f * hr * 2.2, h[1] + hr * 0.1)
        d.line([(h[0] + f * hr * 1.5, h[1] + hr * 0.1), tip], fill=(220, 40, 60), width=max(1, int(hr * 0.1)))


def _butterfly(d, S, scale, sp, x, y, f, t, ink, o, colour, seed):
    col = tuple(colour or sp.col)
    c = S(x, y + 0.05 * math.sin(t * 7 + seed))
    k = abs(math.cos(TAU * sp.flap_hz * t + seed))   # wings seen edge-on as they close
    s = sp.wingspan * scale
    for sgn, cc in ((1, col), (-1, _dark(col, 0.8))):
        d.ellipse([c[0] - s * 0.5, c[1] - s * 0.55 * k * (1 if sgn > 0 else 0.8), c[0] + s * 0.1, c[1]], fill=cc, outline=ink)
        d.ellipse([c[0] - s * 0.35, c[1], c[0] + s * 0.05, c[1] + s * 0.35 * k], fill=cc, outline=ink)
    d.line([(c[0] - s * 0.3, c[1]), (c[0] + s * 0.15, c[1])], fill=(30, 30, 30), width=max(2, int(s * 0.06)))


def draw(p, d, S, scale, t, style=None) -> bool:
    """Draws prop p as its creature. False if its species has no creature rig (the caller draws it as before)."""
    species = p.data.get("kind") if p.data.get("kind") in SPECIES else species_of(p.label or "")
    if species is None:
        return False
    base = SPECIES[species]
    sc_ = p.data.get("scale")
    if not sc_:                                       # a library asset: match its size
        w0, _ = size(species)
        sc_ = max(0.2, min(5.0, p.w / w0)) if p.w else 1.0
    sp = Spec(**{**base.__dict__, "L": base.L * sc_, "Hb": base.Hb * sc_, "leg": base.leg * sc_,
                 "neck": base.neck * sc_, "head": base.head * sc_, "snout": base.snout * sc_, "tail": base.tail * sc_,
                 "wingspan": base.wingspan * sc_})
    x, y, _ = p.pos(t)
    x_prev, y_prev, _ = p.pos(max(0.0, t - 0.04))
    x_next, y_next, _ = p.pos(t + 0.04)
    speed = (x_next - x_prev) / 0.08
    vy = (y_next - y_prev) / 0.08
    flip = p.data.get("flip", 1.0)
    for ft, fv in p.data.get("flips", []):
        if ft <= t:
            flip = fv
    if abs(speed) > 0.05:                             # it faces where it goes
        flip = 1.0 if speed > 0 else -1.0
    x0 = p.pos(0.0)[0]
    dist = abs(x - x0) if True else 0.0
    dist = _travelled(p, t)
    acts = _acts(p, t)
    ink = (22, 22, 28)
    o = max(1.0, scale * 0.012 * (style.outline if style is not None and style.body != "stick" else 0.7))
    seed = (sum(map(ord, p.name if hasattr(p, "name") else species)) % 97) / 10.0
    colour = p.data.get("colour")
    flying = acts.get("fly", 0.0) > 0.5 or (sp.rig in ("bird", "dragon", "butterfly") and
                                            (abs(vy) > 0.05 or (y > 0.25 and abs(speed) > 0.2) or
                                             (sp.rig in ("dragon", "butterfly") and y > 0.3)))   # hovers
    if sp.rig in ("quad", "dragon"):
        gy = y
        _shadow(d, S, scale, x, 0.0 if flying else gy, sp.L * 0.55, flying, y)
        _quad(d, S, scale, sp, x, y, flip, dist, speed, vy, t, acts, ink, o, colour, seed,
              wings=sp.rig == "dragon", flying=flying and sp.rig == "dragon")
    elif sp.rig == "bird":
        if not flying:
            _shadow(d, S, scale, x, y, sp.L * 0.4, False, y)
        _bird(d, S, scale, sp, x, y, flip, dist, speed, vy, t, acts, ink, o, colour, seed, flying)
    elif sp.rig in ("fish", "whale"):
        _fish(d, S, scale, sp, x, y + sp.Hb * 0.6, flip, dist, speed, t, ink, o, colour, seed, whale=sp.rig == "whale")
    elif sp.rig == "serpent":
        _serpent(d, S, scale, sp, p, t, flip, ink, o, colour, seed)
    elif sp.rig == "butterfly":
        _butterfly(d, S, scale, sp, x, y, flip, t, ink, o, colour, seed)
    return True


def _travelled(p, t, step=0.05):
    """Distance the prop has covered by t (along x and y): the gait phase. Cached per frame time."""
    cache = p.data.setdefault("_trav", {})
    if t in cache:
        return cache[t]
    # integrate from the nearest cached earlier time
    known = [k for k in cache if k <= t]
    t0 = max(known) if known else 0.0
    acc = cache.get(t0, 0.0)
    x0, y0, _ = p.pos(t0)
    tt = t0
    while tt < t:
        tn = min(t, tt + step)
        x1, y1, _ = p.pos(tn)
        acc += math.hypot(x1 - x0, (y1 - y0) * 0.3)
        x0, y0, tt = x1, y1, tn
    cache[t] = acc
    if len(cache) > 400:
        for k in sorted(cache)[:200]:
            if k != t:
                cache.pop(k)
    return acc


def _shadow(d, S, scale, x, gy, half, flying, y):
    k = 1.0 if not flying else max(0.25, 1 - y / 6)
    sx, sy = S(x, gy)
    w = half * scale * k
    d.ellipse([sx - w, sy - w * 0.1, sx + w, sy + w * 0.1], fill=(0, 0, 0, int(60 * k)))
