"""A rigged 2D stickman (skeleton, two-bone leg IK, arm gestures) that walks, runs, jumps, talks and emotes.

Walking is physical rather than a looped drawing: each foot is planted at a point on the ground and stays there while
the body passes over it; it lifts only once it trails behind, swings ahead and lands where the body will be. The legs
bend (IK) to reach the planted feet, so the hips dip at double support and rise over the standing leg - weight shift
without any foot sliding. Arms counter-swing with the opposite leg. Starts and stops ease, and a stop ends with a
small settling step so the character stands on both feet."""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field

from . import face as F
from . import speech


@dataclass
class Look:
    """How a character looks. Heights in metres; colours RGB."""
    name: str = "Stick"
    height: float = 1.75
    head: float = 1.0              # head size (children ~1.35, cartoon heroes ~1.15)
    ink: tuple = (22, 22, 28)      # lines
    body: tuple = None             # limb colour (None = ink)
    skin: tuple = (255, 255, 255)  # head fill
    line: float = 1.0              # line weight
    hair: str = "none"             # none | short | spiky | long | ponytail | bun | curly
    hair_color: tuple = (40, 30, 25)
    glasses: bool = False
    tie: tuple = None              # tie colour
    cap: tuple = None              # cap colour
    beard: bool = False
    mustache: bool = False
    skirt: tuple = None            # skirt/dress colour
    shirt: tuple = None            # a shirt over the torso line
    cane: bool = False             # walking stick (elderly)
    hunch: float = 0.0             # forward stoop 0..1 (elderly)
    bow: tuple = None              # hair bow colour


@dataclass
class _Foot:
    x: float
    y: float = 0.0
    swing: tuple | None = None     # (t0, dur, x_from, x_to, lift)
    pitch: float = 0.0
    landed: float = -9.0


def smooth(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def _warped(t: float, warp) -> float:
    ts, xs, _ = warp
    if t <= ts[0]:
        return xs[0]
    if t >= ts[-1]:
        return xs[-1]
    i = bisect.bisect_right(ts, t) - 1
    u = (t - ts[i]) / max(1e-9, ts[i + 1] - ts[i])
    return xs[i] + (xs[i + 1] - xs[i]) * u


def _trapezoid(t: float, t0: float, t1: float, x0: float, x1: float) -> float:
    """Position along a move with eased start and stop (accelerate, cruise, decelerate)."""
    T = max(1e-3, t1 - t0)
    if t <= t0:
        return x0
    if t >= t1:
        return x1
    ta = min(0.45, T / 3)
    vmax = (x1 - x0) / (T - ta)
    u = t - t0
    if u < ta:
        return x0 + 0.5 * vmax * u * u / ta
    if u > T - ta:
        r = T - u
        return x1 - 0.5 * vmax * r * r / ta
    return x0 + 0.5 * vmax * ta + vmax * (u - ta)


# arm poses: (upper arm angle from hanging down, + = forward; elbow bend, + = forearm forward/up), near and far arm
def _g(name: str, t: float):
    s = math.sin
    if name == "wave":
        return (2.55, 0.35 + 0.45 * s(t * 2 * math.pi * 2.6)), None, 0.0
    if name == "point":
        return (1.5, 0.04), None, -0.05
    if name in ("talk", "explain"):
        return ((0.55 + 0.18 * s(t * 5.2), 1.35 + 0.3 * s(t * 8.1)),
                (0.35 + 0.12 * s(t * 4.1 + 1), 1.0 + 0.25 * s(t * 6.3 + 2)), 0.0)
    if name == "clap":
        c = 0.28 * s(t * 2 * math.pi * 3)
        return (0.95, 1.25 + c), (0.95, 1.25 - c), 0.02
    if name == "laugh":
        return (0.2, 1.9 + 0.15 * s(t * 18)), (0.25, 1.95 + 0.15 * s(t * 18 + 1)), 0.08 * s(t * 9)
    if name in ("angry", "fists"):
        return (-0.12 + 0.05 * s(t * 20), 0.6), (-0.1, 0.55), 0.1
    if name == "shake_fist":
        return (2.1, 1.3 + 0.35 * s(t * 14)), (-0.1, 0.5), 0.08
    if name == "shrug":
        return (0.32, 2.15), (0.32, 2.15), 0.0
    if name == "facepalm":
        return (0.85, 2.45), None, 0.06
    if name == "think":
        return (0.45, 2.6), (0.42, 1.65), 0.0
    if name == "phone":
        return (0.55, 2.05), (0.15, 0.5), 0.06
    if name == "cheer":
        return (2.95, 0.15 + 0.25 * s(t * 12)), (2.95, 0.15 + 0.25 * s(t * 12 + 3)), -0.06
    if name == "surprise":
        return (1.95, 1.05), (1.85, 1.0), -0.08
    if name == "cross_arms":
        return (0.55, 2.25), (0.6, 2.15), -0.02
    if name == "scratch_head":
        return (2.35, 2.5 + 0.18 * s(t * 16)), None, 0.0
    if name == "cover_face":
        return (0.95, 2.35), (0.9, 2.3), 0.12
    if name == "hands_up":
        return (2.75, 0.3), (2.7, 0.3), 0.0
    if name == "carry":
        return (0.95, 1.2), (0.85, 1.15), 0.04
    if name == "beckon":
        return (1.3, 1.2 + 0.5 * s(t * 9)), None, 0.0
    return None, None, 0.0


GESTURES = ("wave", "point", "talk", "explain", "clap", "laugh", "angry", "shake_fist", "shrug", "facepalm", "think",
            "phone", "cheer", "surprise", "cross_arms", "scratch_head", "cover_face", "hands_up", "beckon", "carry")


@dataclass
class Character:
    look: Look = field(default_factory=Look)
    x: float = 0.0
    z: float = 1.0                         # depth (1 = the main ground line)
    facing: float = 1.0
    seed: int = 0

    def __post_init__(self):
        H = self.look.height
        self.H = H
        self.r_head = 0.105 * H * self.look.head
        self.l_neck, self.l_torso = 0.04 * H, 0.26 * H
        self.l_up, self.l_fore = 0.165 * H, 0.155 * H
        self.l_thigh, self.l_shin = 0.255 * H, 0.25 * H
        self.ankle = 0.022 * H
        self.moves: list[tuple] = []        # (t0, t1, x0, x1, mode)
        self.warps: dict = {}               # move index -> (times, xs, speed caps) for terrain-paced moves
        self.pace = None                    # x, mode -> top speed there (set by a world with stairs/slopes)
        self.faces: list[tuple] = [(0.0, "neutral", 0.01)]
        self.lines: list[tuple] = []        # (t0, t1, visemes)
        self.gestures: list[tuple] = []     # (t0, t1, name)
        self.turns: list[tuple] = [(0.0, self.facing)]
        self.jumps: list[tuple] = []        # (t0, height, forward)
        self.nods: list[tuple] = []         # (t0, t1, kind)
        self.props: list[tuple] = []        # (t0, t1, kind)
        self._end_x = self.x
        self.ground = lambda x: 0.0               # ground height under x (platforms: a box, a photo, a stage)
        self.highest = lambda xa, xb: max(self.ground(xa), self.ground(xb))   # highest ground between two x
        self.foothold = lambda x, f, toe, heel, frm=None: x   # where a foot can land flat (stairs: off an edge)
        self._feet = [_Foot(self.x + 0.09 * H), _Foot(self.x - 0.09 * H)]
        self._still = 0.0
        self._hip_y = self.l_thigh + self.l_shin + self.ankle
        self._face_vis = self.facing
        self._last_t = None
        self._jump_land = None

    # ---- directing -------------------------------------------------------------------------------------------
    def walk(self, t: float, to_x: float, speed: float = 1.25, mode: str = "walk") -> float:
        x0 = self._end_x
        if self.pace is not None and abs(to_x - x0) > 0.05:
            caps = [self.pace(x0 + (to_x - x0) * k / 40, mode) for k in range(41)]
            if min(caps) < speed:                 # stairs or a slope on the way: slow down for them
                dur = self._paced(t, x0, to_x, speed, mode)
                self._end_x = to_x
                return t + dur
        dur = abs(to_x - x0) / speed + 0.45
        self.moves.append((t, t + dur, x0, to_x, mode))
        self._end_x = to_x
        return t + dur

    def _paced(self, t: float, x0: float, x1: float, speed: float, mode: str) -> float:
        """A move whose speed follows the terrain (slower on stairs and steep slopes), braking and accelerating
        at a human rate. Stores a time -> position table for hips_x."""
        d = abs(x1 - x0)
        n = max(2, int(d / 0.02))
        s = 1.0 if x1 >= x0 else -1.0
        xs = [x0 + s * d * i / n for i in range(n + 1)]
        cap = [min(speed, self.pace(x, mode)) for x in xs]
        acc = 3.5 if mode == "run" else 1.4
        h = d / n
        v = list(cap)
        v[0] = v[-1] = 0.0
        for i in range(n - 1, -1, -1):
            v[i] = min(v[i], math.sqrt(v[i + 1] ** 2 + 2 * acc * h))
        for i in range(1, n + 1):
            v[i] = min(v[i], math.sqrt(v[i - 1] ** 2 + 2 * acc * h))
        ts = [0.0]
        for i in range(n):
            ts.append(ts[-1] + h / max(0.04, (v[i] + v[i + 1]) / 2))
        T = ts[-1]
        self.warps[len(self.moves)] = ([t + q for q in ts], xs, cap)
        self.moves.append((t, t + T, x0, x1, mode))
        return T

    def run(self, t: float, to_x: float, speed: float = 3.6) -> float:
        return self.walk(t, to_x, speed, "run")

    def express(self, t: float, name: str, blend: float = 0.3):
        self.faces.append((t, name, blend))
        return self

    def say(self, t: float, text: str, wav_out, lang: str = "en", voice: str = "", expr: str | None = None,
            gesture: str | None = "talk", rate: int = 160, pitch: int = 50) -> tuple[float, object]:
        """Speaks the line from time t (lip-synced); returns (end time, wav path)."""
        track = speech.say(text, wav_out, lang, voice, rate=rate, pitch=pitch)
        end = t + track[-1][0]
        self.lines.append((t, end, [(t + a, v) for a, v in track]))
        if expr:
            self.express(t, expr, 0.25)
        if gesture:
            self.gestures.append((t, end, gesture))
        return end, wav_out

    def gesture(self, t: float, name: str, dur: float = 1.5):
        self.gestures.append((t, t + dur, name))
        return t + dur

    def turn(self, t: float, facing: float):
        self.turns.append((t, 1.0 if facing >= 0 else -1.0))
        return self

    def jump(self, t: float, height: float = 0.45, forward: float = 0.0) -> float:
        self.jumps.append((t, height * self.H, forward))
        if forward:
            self.moves.append((t + 0.28, t + 0.28 + 0.62, self._end_x, self._end_x + forward, "jump"))
            self._end_x += forward
        return t + 1.2

    def nod(self, t: float, dur: float = 0.8, kind: str = "yes"):
        self.nods.append((t, t + dur, kind))
        return t + dur

    def hold(self, t0: float, t1: float, prop: str):
        self.props.append((t0, t1, prop))
        return self

    # ---- evaluation --------------------------------------------------------------------------------------------
    def hips_x(self, t: float) -> float:
        x = self.x
        for i, (t0, t1, x0, x1, _) in enumerate(self.moves):
            if t >= t0:
                x = _warped(t, self.warps[i]) if i in self.warps else _trapezoid(t, t0, t1, x0, x1)
        return x

    def mode(self, t: float) -> str:
        for t0, t1, _, _, m in self.moves:
            if t0 <= t <= t1:
                return m
        return "idle"

    def _jump_off(self, t: float) -> tuple[float, float, bool]:
        """(hip offset, crouch, airborne) for a jump: anticipate 0.28 s, fly 0.62 s, land 0.3 s."""
        for t0, h, _ in self.jumps:
            u = t - t0
            if 0 <= u < 0.28:
                return 0.0, 0.11 * self.H * smooth(u / 0.28), False
            if 0.28 <= u < 0.9:
                k = (u - 0.28) / 0.62
                return h * 4 * k * (1 - k), 0.0, True
            if 0.9 <= u < 1.2:
                return 0.0, 0.13 * self.H * math.sin(math.pi * (u - 0.9) / 0.3) * (1 - (u - 0.9) / 0.3 * 0.3), False
        return 0.0, 0.0, False

    def _facing_at(self, t: float, v: float) -> float:
        for t0, t1, x0, x1, m in self.moves:            # moving: face the way the move goes, from its first instant
            if t0 <= t <= t1 and x1 != x0 and m not in ("jump", "handoff"):
                return 1.0 if x1 > x0 else -1.0
        if abs(v) > 0.08:
            return 1.0 if v > 0 else -1.0
        f = self.facing
        for tt, ff in self.turns:
            if tt <= t:
                f = ff
        for t0, t1, x0, x1, m in self.moves:
            if t1 <= t and x1 != x0 and m != "handoff":       # an action's hand-off is not a walk direction
                last_move_dir = 1.0 if x1 > x0 else -1.0
                if not any(t1 < tt <= t for tt, _ in self.turns):
                    f = last_move_dir
        return f

    def step(self, t: float, dt: float):
        """Advances the feet and body to time t (frames are evaluated in order)."""
        H = self.H
        hx = self.hips_x(t)
        v = (self.hips_x(t + 0.02) - self.hips_x(t - 0.02)) / 0.04
        speed = abs(v)
        f = self._facing_at(t, v)
        self.f = f
        self._face_vis += (f - self._face_vis) * min(1.0, dt * 9)
        mode = self.mode(t)
        run = mode == "run"
        joff, crouch, air = self._jump_off(t)
        if air:
            self._jump_land = True
            for k, ft in enumerate(self._feet):
                ft.swing = None
            self._carry = True
        elif self._jump_land:
            self._jump_land = None
            self._carry = False
            self._feet[0].x, self._feet[1].x = hx + f * 0.1 * H, hx - f * 0.08 * H
            for ft in self._feet:
                ft.y, ft.swing = self.ground(ft.x), None
        # step length grows with speed (about 0.39 x height at a brisk 1.4 m/s); one step takes S / speed
        # plan steps from the move's cruise speed, not this instant's (the first step of a start is then a proper step,
        # not a shuffle the accelerating body outruns)
        plan = speed
        for i, (t0, t1, x0, x1, _m) in enumerate(self.moves):
            if t0 <= t <= t1:
                if i in self.warps:                     # paced over terrain: the local cruise speed
                    ts_, xs_, cap_ = self.warps[i]
                    k = min(len(xs_) - 1, max(0, int(abs(hx - xs_[0]) / max(1e-6, abs(xs_[-1] - xs_[0])) * (len(xs_) - 1))))
                    plan = max(speed, 0.75 * cap_[k])
                    continue
                T = max(1e-3, t1 - t0)
                plan = max(speed, 0.75 * abs(x1 - x0) / max(1e-3, T - min(0.45, T / 3)))
        S = H * ((0.5 + 0.18 * min(1, plan / 4)) if run else (0.2 + 0.14 * min(1.0, plan / 1.4)))
        P = S / max(plan, 0.25)
        # finish swings (a landed foot remembers when it touched down)
        for ft in self._feet:
            if ft.swing:
                t0, dur, xa, xb, lift = ft.swing
                k = (t - t0) / dur
                if k >= 1:
                    ft.x, ft.y, ft.swing, ft.pitch = xb, self.ground(xb), None, 0.0
                    ft.landed = t
                else:
                    e = smooth(k)
                    ft.x = xa + (xb - xa) * e
                    ga, gb = self.ground(xa), self.ground(xb)
                    toe = 0.08 * H * (1 if xb >= xa else -1)
                    top = self.highest(xa, xb + toe)                   # the toe reaches the next step first
                    if top > max(ga, gb) + 0.005 or gb > ga + 0.02:    # a step up (or over something): rise first
                        ey = 1 - (1 - k) ** 4
                        clear = max(0.0, top - max(ga, gb))
                        ft.y = ga + (gb - ga) * ey + (lift + clear) * math.sin(math.pi * k) ** 0.7
                    elif gb < ga - 0.02:                       # a step down: travel out over the edge, then drop
                        ey = k ** 2.2
                        ft.y = ga + (gb - ga) * ey + lift * math.sin(math.pi * k)
                    else:
                        ft.y = ga + (gb - ga) * e + lift * math.sin(math.pi * k)
                    if k < 0.9:                                # the whole foot, heel to toe, stays over the steps
                        under = self.highest(ft.x - 0.03 * H * (1 if xb >= xa else -1), ft.x + toe)
                        ft.y = max(ft.y, under + 0.015 * math.sin(math.pi * k))
                    ft.pitch = 0.5 * math.sin(math.pi * k) * (1 if k < 0.5 else -0.4)
        if not air and speed > 0.05 and mode in ("walk", "run"):
            self._still = 0.0
            order = sorted(range(2), key=lambda k: f * self._feet[k].x)     # the foot furthest behind steps first
            together = abs(self._feet[0].x - self._feet[1].x) < 0.12 * H
            for i in (order if together else order[:1]):   # only the rear one, unless the feet are side by side
                ft = self._feet[i]
                other = self._feet[1 - i]
                if ft.swing:
                    continue
                behind = f * (hx - ft.x)
                if run:
                    # running: lift at toe-off, whatever the other foot does (there is a flight phase)
                    ready = behind > 0.3 * S and (other.swing is None or (t - other.swing[0]) / other.swing[1] > 0.4)
                    dur = max(0.16, min(0.36, 1.3 * P))
                    ahead = 0.25 * S
                else:
                    # walking: the back foot lifts once the front foot has carried weight for ~20% of a step
                    # (double support), swings for 80% of a step and lands half a step ahead of the hips
                    ready = (other.swing is None and behind > 0.12 * S and (
                        t - other.landed >= 0.2 * P
                        or behind > 0.8 * S)          # catch-up: never let the body leave both feet behind
                        or behind > 1.0 * S and (other.swing is None or (t - other.swing[0]) / other.swing[1] > 0.6))
                    dur = max(0.24, min(0.55, 0.8 * P))
                    ahead = 0.45 * S
                if ready:
                    land = self.hips_x(t + dur) + f * ahead
                    land = self.foothold(land, f, 0.075 * H, 0.03 * H, other.x)   # one stair past the planted foot
                    ft.swing = (t, dur, ft.x, land, (0.16 if run else 0.07) * H)
                    break
        elif not air:
            self._still += dt
            a, b = self._feet
            if self._still > 0.12 and not a.swing and not b.swing:
                spread = abs(a.x - b.x)
                centred = min(a.x, b.x) - 0.05 * H <= hx <= max(a.x, b.x) + 0.05 * H
                if spread > 0.21 * H or not centred:
                    far = max(self._feet, key=lambda q: abs(q.x - hx))
                    near = a if far is b else b
                    side = -1.0 if near.x >= hx else 1.0
                    far.swing = (t, 0.34, far.x, hx + side * 0.085 * H, 0.05 * H)
        # hips: as high as the planted legs reach (bending at double support), lowered by crouch, raised in a jump
        leg = self.l_thigh + self.l_shin
        base = max([ft.y for ft in self._feet if ft.swing is None] or [self.ground(hx)])
        # the hips follow the terrain under and just ahead of the body (stairs, slopes) - smoothly - and never
        # higher than the planted legs can reach
        span = 0.22 * H
        terrain = sum(self.ground(hx + f * span * (k / 4 - 0.1)) for k in range(5)) / 5
        target = terrain + leg * 0.985 + self.ankle
        cap = 1e9
        if not air:
            for ft in self._feet:
                if ft.swing is None:
                    dx = hx - ft.x
                    cap = min(cap, ft.y + self.ankle + math.sqrt(max(0.0, (leg * 0.995) ** 2 - dx * dx)))
        if not air:                                       # a foot about to land lower: sink in time to meet it
            for ft in self._feet:
                if ft.swing:
                    t0s, durs, _, xb, _ = ft.swing
                    left = max(0.0, t0s + durs - t)
                    dxl = self.hips_x(t0s + durs) - xb
                    meet = self.ground(xb) + self.ankle + math.sqrt(max(0.0, (leg * 0.995) ** 2 - dxl * dxl))
                    target = min(target, meet + 0.9 * left)
        target = min(target, cap)
        target -= crouch + (0.04 * H if run else 0.0)
        if self.look.hunch:
            target -= 0.03 * H * self.look.hunch
        target = max(target, base + 0.72 * leg)          # a safety floor: hips never sink below a deep crouch
        if target > self._hip_y:                          # rising (a step up, standing up): the stance leg pushes
            self._hip_y += min((target - self._hip_y) * min(1.0, dt * 12), 1.1 * dt)
        else:                                             # sinking: eased, unless the legs can't reach
            self._hip_y = max(target, self._hip_y - min((self._hip_y - target) * min(1.0, dt * 14), 1.3 * dt))
        self._hip_y = min(self._hip_y, cap - crouch)
        self.hip = (hx, self._hip_y + joff)
        if air:
            for k, ft in enumerate(self._feet):
                ft.x = hx + f * (0.08 if k == 0 else -0.06) * H
                ft.y = self.hip[1] - leg * 0.86 - self.ankle
        self.speed, self.run_mode, self.air = speed, run, air
        self._t = t

    def pose(self, t: float) -> dict:
        """Joint positions (world metres, y up) and the face, for drawing."""
        H, f = self.H, self.f
        hx, hy = self.hip
        lean = 0.0
        if self.run_mode:
            lean = 0.22
        elif self.speed > 0.05:
            lean = 0.06 * min(1, self.speed / 1.4)
        lean += 0.28 * self.look.hunch
        g_near, g_far, g_lean, gw = None, None, 0.0, 0.0
        gname = None
        for t0, t1, name in self.gestures:
            if t0 <= t <= t1:
                w = min(smooth((t - t0) / 0.25), smooth((t1 - t) / 0.25))
                n, fa, ln = _g(name, t - t0)
                if w > gw:
                    g_near, g_far, g_lean, gw, gname = n, fa, ln, w, name
        lean += g_lean * gw
        breath = 0.006 * H * math.sin(t * 2 * math.pi / 3.4 + self.seed)
        neck = (hx + f * math.sin(lean) * self.l_torso, hy + math.cos(lean) * self.l_torso + breath)
        if gname == "shrug":
            neck = (neck[0], neck[1] + 0.012 * H * gw)
        sh = (hx + f * math.sin(lean) * self.l_torso * 0.88, hy + math.cos(lean) * self.l_torso * 0.88 + breath)
        # face
        fc = self._face(t)
        nod = 0.0
        for t0, t1, kind in self.nods:
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                nod = (0.25 if kind == "yes" else 0.0) * math.sin(k * math.pi * 4) * (1 - k)
                if kind == "no":
                    fc = F.Face(**{**fc.__dict__, "look_x": math.sin(k * math.pi * 4) * (1 - k) * 1.2})
        shake = fc.shake * (0.012 * H) * math.sin(t * 40 + self.seed)
        tilt = math.radians(fc.head_tilt) * 0.0
        head = (neck[0] + f * math.sin(lean + tilt) * (self.l_neck + self.r_head) + shake,
                neck[1] + math.cos(lean) * (self.l_neck + self.r_head) - nod * 0.05 * H)
        if gname == "phone":
            fc = F.blend(fc, F.Face(**{**fc.__dict__, "look_y": -0.8, "look_x": 0.5}), gw)
        # legs (IK)
        legs = []
        for ft in self._feet:
            ank = (ft.x, ft.y + self.ankle)
            knee = _ik(self.hip, ank, self.l_thigh, self.l_shin, f)
            toe = (ank[0] + f * 0.085 * H * math.cos(ft.pitch), ank[1] - self.ankle + 0.085 * H * math.sin(ft.pitch) * 0.6)
            legs.append((self.hip, knee, ank, toe))
        # arms
        a_near, a_far = self._arm_swing()
        if self.run_mode:
            a_near, a_far = (a_near[0] * 1.4, 1.5), (a_far[0] * 1.4, 1.5)
        if self.look.cane:
            a_far = (0.35, 0.25)
        arms = []
        for i, (base, gpose) in enumerate(((a_near, g_near), (a_far, g_far))):
            a1, a2 = base
            if gpose is not None:
                a1, a2 = a1 + (gpose[0] - a1) * gw, a2 + (gpose[1] - a2) * gw
            elbow = (sh[0] + f * math.sin(a1) * self.l_up, sh[1] - math.cos(a1) * self.l_up)
            hand = (elbow[0] + f * math.sin(a1 + a2) * self.l_fore, elbow[1] - math.cos(a1 + a2) * self.l_fore)
            arms.append((sh, elbow, hand))
        props = [p for t0, t1, p in self.props if t0 <= t <= t1]
        if gname == "phone" and gw > 0.5 and "phone" not in props:
            props.append("phone")
        return {"hip": self.hip, "neck": neck, "head": head, "legs": legs, "arms": arms, "face": fc,
                "facing": max(-1.0, min(1.0, self._face_vis)), "lean": lean, "props": props}

    def _arm_swing(self):
        hx = self.hip[0]
        S = 0.35 * self.H
        a, b = self._feet          # feet[0] is the near leg; the near arm swings with the far leg
        k_near = max(-1.0, min(1.0, self.f * (b.x - hx) / S)) if self.speed > 0.05 else 0.0
        k_far = max(-1.0, min(1.0, self.f * (a.x - hx) / S)) if self.speed > 0.05 else 0.0
        amp = 0.5 * min(1.0, self.speed / 1.3)
        base = 0.06 + 0.02 * math.sin(self._t * 1.9 + self.seed)
        return ((base + amp * k_near, 0.22 + 0.35 * max(0, k_near) * amp),
                (base * 0.6 + amp * k_far, 0.2 + 0.35 * max(0, k_far) * amp))

    def _face(self, t: float) -> F.Face:
        cur = F.expression("neutral")
        for i, (t0, name, bl) in enumerate(self.faces):
            if t >= t0:
                prev = cur
                cur = F.blend(prev, F.expression(name), (t - t0) / max(bl, 1e-3))
        mouth = None
        for t0, t1, track in self.lines:
            if t0 - 0.05 <= t <= t1 + 0.1:
                mouth = speech.mouth_at(track, t)
        if mouth:
            cur = F.speaking(cur, mouth)
        b = F.blink(t, self.seed)
        if b < 1:
            cur = F.Face(**{**cur.__dict__, "eye_open": cur.eye_open * b, "eye_smile": cur.eye_smile * b})
        return cur


def _ik(hip, ankle, l1, l2, f):
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = max(1e-6, min(math.hypot(dx, dy), (l1 + l2) * 0.9999))
    a = math.atan2(dy, dx)
    c = max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    b = math.acos(c)
    ang = a + b * (1 if f > 0 else -1)          # knee bends toward the facing direction
    return hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang)


def _shade(c, k):
    return tuple(int(v + (200 - v) * k) for v in c[:3])


def draw(d, ch: Character, P: dict, to_screen, scale: float, t: float) -> None:
    """Draws the posed character. to_screen(x, y) -> pixels; scale = pixels per metre."""
    L = ch.look
    lw = max(2, int(scale * 0.018 * ch.H * L.line))
    ink = L.ink
    body = L.body or ink
    far = _shade(body, 0.38)
    f = P["facing"]
    S = to_screen

    def seg(pts, col, w=lw):
        q = [S(*p) for p in pts]
        d.line(q, fill=col, width=w, joint="curve")
        for x, y in (q[0], q[-1]):
            d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)
    # far limbs first
    hip, knee, ank, toe = P["legs"][1]
    seg([hip, knee, ank, toe], far)
    sh, el, hd = P["arms"][1]
    seg([sh, el, hd], far)
    if L.cane:
        hx, hy = S(*hd)
        gx, gy = S(hd[0] + f * 0.04 * ch.H, 0)
        d.line([(hx, hy), (gx, gy)], fill=(110, 70, 40), width=max(2, int(lw * 0.8)))
    # torso
    if L.skirt:
        hx, hy = P["hip"]
        w = 0.13 * ch.H
        pts = [(hx - w * 0.35, hy + 0.08 * ch.H), (hx + w * 0.35, hy + 0.08 * ch.H), (hx + w, hy - 0.15 * ch.H),
               (hx - w, hy - 0.15 * ch.H)]
        d.polygon([S(*p) for p in pts], fill=L.skirt, outline=ink)
    if L.shirt:
        hx, hy = P["hip"]
        nx, ny = P["neck"]
        w = 0.06 * ch.H
        pts = [(hx - w, hy + 0.02 * ch.H), (hx + w, hy + 0.02 * ch.H), (nx + w * 1.15, ny - 0.03 * ch.H),
               (nx - w * 1.15, ny - 0.03 * ch.H)]
        d.polygon([S(*p) for p in pts], fill=L.shirt, outline=ink)
    seg([P["hip"], P["neck"]], body, int(lw * 1.1))
    if L.tie:
        nx, ny = P["neck"]
        pts = [(nx, ny - 0.02 * ch.H), (nx + 0.018 * ch.H, ny - 0.12 * ch.H), (nx, ny - 0.15 * ch.H),
               (nx - 0.018 * ch.H, ny - 0.12 * ch.H)]
        d.polygon([S(*p) for p in pts], fill=L.tie)
    seg([P["neck"], P["head"]], body)
    # head
    cx, cy = S(*P["head"])
    r = ch.r_head * scale
    if L.hair in ("long", "ponytail") or L.bow:
        _hair_back(d, L, cx, cy, r, f, t)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=L.skin, outline=ink, width=int(lw * 0.95))
    _hair_front(d, L, cx, cy, r, f, lw)
    F.draw(d, cx, cy, r, P["face"], f, t, ink=ink, skin=L.skin, lw=lw * 0.75)
    if L.glasses:
        off = r * 0.22 * f
        for side in (-1, 1):
            gx = cx + off + side * r * 0.36 * (0.82 if side * f < 0 else 1)
            d.ellipse([gx - r * 0.22, cy - r * 0.32, gx + r * 0.22, cy + r * 0.08], outline=ink, width=int(lw * 0.5))
        d.line([(cx + off - r * 0.14, cy - r * 0.15), (cx + off + r * 0.14, cy - r * 0.15)], fill=ink,
               width=int(lw * 0.5))
    if L.mustache:
        off = r * 0.22 * f
        d.chord([cx + off - r * 0.3, cy + r * 0.18, cx + off + r * 0.3, cy + r * 0.42], 180, 360, fill=L.hair_color)
    if L.beard:
        off = r * 0.22 * f
        d.chord([cx + off - r * 0.7, cy + r * 0.05, cx + off + r * 0.7, cy + r * 1.12], 15, 165, fill=L.hair_color)
        fc = P["face"]
        my = cy + r * 0.42
        d.ellipse([cx + off - r * 0.2, my - r * 0.05, cx + off + r * 0.2, my + r * (0.06 + fc.mouth_open * 0.3)],
                  fill=(70, 20, 30) if fc.mouth_open > 0.12 else L.hair_color)
    if L.cap:
        d.chord([cx - r * 1.02, cy - r * 1.05, cx + r * 1.02, cy + r * 0.55], 180, 360, fill=L.cap, outline=ink)
        d.line([(cx + f * r * 0.2, cy - r * 0.28), (cx + f * r * 1.45, cy - r * 0.2)], fill=L.cap, width=int(lw * 1.4))
    # near limbs
    hip, knee, ank, toe = P["legs"][0]
    seg([hip, knee, ank, toe], body)
    sh, el, hd = P["arms"][0]
    seg([sh, el, hd], body)
    if "phone" in P["props"]:
        x, y = S(*hd)
        w, h = r * 0.42, r * 0.75
        d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y + h * 0.1], radius=r * 0.08, fill=(30, 30, 36),
                            outline=(15, 15, 18))
        glow = 140 + int(80 * (0.5 + 0.5 * math.sin(t * 5)))
        d.rectangle([x - w / 2 + 3, y - h + 4, x + w / 2 - 3, y + h * 0.1 - 6], fill=(glow // 2, int(glow / 1.4), glow))


def _hair_back(d, L, cx, cy, r, f, t):
    col = L.hair_color
    if L.hair == "long":
        # hair falls behind the head and down the back, never over the face
        bx = cx - f * r * 0.55
        d.rounded_rectangle([bx - r * 0.75, cy - r * 0.7, bx + r * 0.75, cy + r * 1.55], radius=r * 0.55, fill=col)
    if L.hair == "ponytail":
        sway = math.sin(t * 3) * r * 0.1
        bx = cx - f * r * 1.05
        d.ellipse([bx - r * 0.38 + sway, cy - r * 0.35, bx + r * 0.38 + sway, cy + r * 0.9], fill=col)
    if L.bow:
        bx, by = cx - f * r * 0.75, cy - r * 0.8
        d.polygon([(bx, by), (bx - r * 0.35, by - r * 0.25), (bx - r * 0.35, by + r * 0.25)], fill=L.bow)
        d.polygon([(bx, by), (bx + r * 0.35, by - r * 0.25), (bx + r * 0.35, by + r * 0.25)], fill=L.bow)


def _hair_front(d, L, cx, cy, r, f, lw):
    col = L.hair_color
    if L.hair in ("short", "long", "ponytail") and not L.cap:
        d.chord([cx - r * 1.04, cy - r * 1.06, cx + r * 1.04, cy + r * 0.45], 185, 355, fill=col)
        if L.hair != "short":
            d.chord([cx - r * 1.0 - f * r * 0.3, cy - r * 1.0, cx + r * 0.6 - f * r * 0.3, cy - r * 0.05], 200, 330,
                    fill=col)
    elif L.hair == "spiky":
        pts = []
        for i in range(9):
            a = math.pi * (1.05 + 0.9 * i / 8)
            rr = r * (1.38 if i % 2 else 1.0)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr - r * 0.05))
        d.polygon(pts + [(cx + r * 0.95, cy - r * 0.15), (cx - r * 0.95, cy - r * 0.15)], fill=col)
    elif L.hair == "bun":
        d.ellipse([cx - r * 0.42 - f * r * 0.3, cy - r * 1.55, cx + r * 0.42 - f * r * 0.3, cy - r * 0.75], fill=col)
        d.chord([cx - r * 1.04, cy - r * 1.06, cx + r * 1.04, cy + r * 0.3], 190, 350, fill=col)
    elif L.hair == "curly":
        for i in range(8):
            a = math.pi * (1.0 + i / 7)
            x, y = cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95
            d.ellipse([x - r * 0.3, y - r * 0.3, x + r * 0.3, y + r * 0.3], fill=col)
