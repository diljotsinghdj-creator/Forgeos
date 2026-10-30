"""Keyframed stick figures with weight, timing and personality - the action layer on top of the walking rig.

How it moves
- A pose is joint angles on fixed-length bones (bones never stretch or break), the hip position, facing, and
  optional IK targets: planted feet, and hands that grab a ledge, a folder or a chart.
- Between keys every value eases with its own curve: ease in/out, fast-out ("snap"), overshoot ("back" - a pose
  that settles past and returns), so motion has anticipation, accent and settle instead of linear sliding.
- Jumps and falls are ballistic: between take-off and landing the hips follow real gravity (9.8 m/s^2), so airtime
  and arcs are physically right; landings squash the body and the legs bend onto the planted feet.
- Follow-through: the head and the forearms lag the body by a spring, so stops wobble and swings overlap.
- Walking and running come from the planted-foot controller in rig2d; an action starts from wherever the body
  really is and hands control back at the exact feet and hips it ended on.
- Faceless emotion: body-language states (happy bounce, angry lean with clenched fists, cowering fear, shrugging
  confusion...) that loop, so a character without a face still reads.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, fields, replace

from . import face as F
from . import rig2d
from .rig2d import Look, smooth

TAU = 2 * math.pi
G = 9.8
ANGLES = ("lean", "head", "au", "al", "bu", "bl", "lu", "ll", "mu", "ml")


def ease(kind: str, u: float, overshoot: float = 1.0) -> float:
    u = max(0.0, min(1.0, u))
    if kind == "linear":
        return u
    if kind == "in":
        return u * u * u
    if kind == "accel":                      # constant push: ends at the speed a ballistic flight starts with
        return u * u
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "snap":                       # a fast accent that slightly overshoots and settles
        return 1 - (1 - u) ** 4 * math.cos(u * 3.2)
    if kind == "settle":                     # from rest, past the pose a little, back to rest (recoveries)
        return u * u * (3 - 2 * u) + 0.3 * overshoot * math.sin(math.pi * u) ** 2 * u
    if kind == "back":                       # overshoot past the pose and come back (starts fast: pops)
        s = 1.9 * overshoot
        u -= 1
        return u * u * ((s + 1) * u + s) + 1
    return u * u * (3 - 2 * u)               # inout


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.9          # hip height (world)
    lean: float = 0.0       # spine from vertical, + forward
    head: float = 0.0       # head relative to spine, + forward (down)
    au: float = 0.08        # near arm: upper, forearm (absolute, from hanging down; + forward)
    al: float = 0.25
    bu: float = 0.05        # far arm
    bl: float = 0.2
    lu: float = 0.0         # near leg: thigh, shin (absolute, from straight down; + forward)
    ll: float = 0.0
    mu: float = 0.0         # far leg
    ml: float = 0.0
    squash: float = 1.0     # <1 squashed (landing), >1 stretched (take-off)
    f: float = 1.0          # facing
    feet: tuple | None = None   # ((x, y), (x, y)) planted ankles (near, far) - legs solved by IK
    hands: tuple | None = None  # (near point or None, far point or None) - arms solved by IK
    feet_w: tuple = (1.0, 1.0)  # how much each leg follows its foot target (eases contact in and out)
    hands_w: tuple = (1.0, 1.0)


def lerp(a, b, k):
    return a + (b - a) * k


def lerp_pt(a, b, k):
    if a is None:
        return b
    if b is None:
        return a
    return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))


@dataclass
class Act:
    t0: float
    keys: list                    # [(dt, {field: value}, ease)] - dx/dy relative to where the act starts
    name: str = ""
    resolved: list | None = None  # absolute (t, Pose, ease, ballistic)
    dx: float = 0.0
    end_f: float | None = None
    upper_free: bool = False      # the arms, head and lean may still show feelings (sitting, kneeling)
    overshoot: float = 1.0
    exaggerate: float = 1.0

    @property
    def t1(self) -> float:
        return self.t0 + max(k[0] for k in self.keys)


def _simulate(x, y, ang, vx, vy, spin, bounce, w, h, ground, seconds=6.0, friction=6.0):
    """Gravity, bounces that lose energy, friction on the ground, then rest. 120 samples a second."""
    out, dt = [(x, y, ang)], 1 / 120
    on_ground = 0
    roll = min(w, h) * 0.5
    for _ in range(int(seconds * 120)):
        vy -= G * dt
        x += vx * dt
        y += vy * dt
        ang += spin * dt
        g = ground(x)
        if y <= g:
            y = g
            if abs(vy) > 0.6:
                vy = -vy * bounce
                vx *= 0.8
                spin = -vx / max(0.05, roll) * 0.5
            else:
                vy = 0.0
                on_ground += 1
                vx -= math.copysign(min(abs(vx), friction * dt), vx)  # sliding / rolling friction
                spin = -vx / max(0.05, roll) * 0.3
                ang += spin * dt
        out.append((x, y, ang))
        if on_ground > 10 and abs(vx) < 1e-3:
            break
    return out


def _retime(keys: list, tm) -> list:
    """Applies a timing profile to an action's keys (flights and push-offs keep their physical timing)."""
    out, prev, prev_new = [], 0.0, 0.0
    for i, (dt, kv, ek) in enumerate(keys):
        d = dt - prev
        if not (kv.get("ballistic") or ek == "accel"):
            d = d / tm.tempo * (tm.anticipation if i == 0 else 1.0)
        prev_new += d
        out.append((prev_new, kv, ek))
        prev = dt
    if tm.hold > 0:
        out.append((prev_new + tm.hold, {}, "linear"))
    return out


class Actor:
    """A stick figure: walks with planted feet (rig2d), acts with keyframes, feels with its whole body."""

    def __init__(self, look: Look | None = None, x: float = 0.0, z: float = 1.0, facing: float = 1.0,
                 faceless: bool = True, seed: int = 0, world=None):
        self.look = look or Look()
        self.loco = rig2d.Character(self.look, x=x, facing=facing, seed=seed)
        self.loco.facing = facing
        self.loco.turns = [(0.0, facing)]
        self.z, self.faceless, self.seed, self.world = z, faceless, seed, world
        if world is not None:
            self.loco.ground = world.ground
            self.loco.highest = world.highest
            self.loco.foothold = world.foothold
            self.loco.pace = world.pace
        L = self.loco
        self.H = L.H
        self.l_thigh, self.l_shin, self.l_up, self.l_fore = L.l_thigh, L.l_shin, L.l_up, L.l_fore
        self.l_torso, self.l_neck, self.r_head, self.ankle = L.l_torso, L.l_neck, L.r_head, L.ankle
        self.acts: list[Act] = []
        self.feels: list[tuple] = []          # (t0, t1, emotion)
        self.holds: list[tuple] = []          # (t0, t1, prop, hand)
        self.symbols: list[tuple] = []        # (t0, t1, "?" | "!" | "..." | "♥" | "#")
        self.postures: list[tuple] = []       # (t0, t1, lean, crouch)
        self.reaches: list[tuple] = []        # (t0, t1, (near, far)) hand targets while walking
        self._end_x = x
        self.timing = None                    # a timing.Timing profile (comedy, drama...) for keyframed actions
        self.depth: list[tuple] = []          # (t0, t1, dz): stepping toward (dz < 0) or away from the camera
        self.looks: list[tuple] = []          # (t0, t1, target): where the head turns (an actor or an (x, y) point)
        self._spring = {}
        self._act = None
        self.hip = (x, L._hip_y)
        self.speed = 0.0

    # ---- directing (build time) ---------------------------------------------------------------------------
    def walk(self, t, to_x, speed=1.3):
        end = self.loco.walk(t, to_x, speed)
        self._end_x = to_x
        return end

    def run(self, t, to_x, speed=3.8):
        end = self.loco.run(t, to_x, speed)
        self._end_x = to_x
        return end

    def act(self, t: float, keys: list, name: str = "", dx: float = 0.0, end_f: float | None = None,
            upper_free: bool = False) -> float:
        """A keyframed action from time t. keys: [(dt, {...}, ease)]; dx = where the hips end up, relative."""
        tm = self.timing
        if tm is not None and keys:
            keys = _retime(keys, tm)
        a = Act(t, keys, name, dx=dx, end_f=end_f, upper_free=upper_free,
                overshoot=tm.overshoot if tm else 1.0, exaggerate=tm.exaggerate if tm else 1.0)
        self.acts.append(a)
        if dx:
            self.loco.moves.append((a.t1, a.t1 + 1e-3, self._end_x, self._end_x + dx * self._facing_at_build(t), "handoff"))
            self._end_x += dx * self._facing_at_build(t)
            self.loco._end_x = self._end_x            # the next walk starts where the action left the body
        if end_f is not None:
            self.loco.turns.append((a.t1, end_f))
        return a.t1

    def _facing_at_build(self, t: float) -> float:
        """Which way the actor will face at time t, from the moves and turns directed so far."""
        f = self.loco.facing
        for tt, ff in self.loco.turns:
            if tt <= t:
                f = ff
        last = None
        for t0, t1, x0, x1, m in self.loco.moves:
            if t0 <= t and x1 != x0 and m != "handoff":
                last = (t0, 1.0 if x1 > x0 else -1.0)
        if last and not any(last[0] < tt <= t for tt, _ in self.loco.turns):
            f = last[1]
        return f

    def feel(self, t0: float, t1: float, emotion: str) -> float:
        self.feels.append((t0, t1, emotion))
        return t1

    def say_symbol(self, t0, t1, sym):
        self.symbols.append((t0, t1, sym))
        return t1

    def posture(self, t0, t1, lean=0.0, crouch=0.0):
        self.postures.append((t0, t1, lean, crouch))
        return t1

    def reach(self, t0, t1, near=None, far=None):
        self.reaches.append((t0, t1, (near, far)))
        return t1

    def gesture(self, t, name, dur=1.5):
        return self.loco.gesture(t, name, dur)

    def turn(self, t, facing):
        self.loco.turn(t, facing)
        return t

    def hold(self, t0, t1, prop, hand="near"):
        self.holds.append((t0, t1, prop, hand))
        prop.carriers.append((t0, t1, self, hand))
        return t1

    def hips_x(self, t):
        a = self._current_act(t)
        if a and a.resolved:
            return self._eval(a, t).x
        return self.loco.hips_x(t)

    # ---- evaluation ----------------------------------------------------------------------------------------
    def _current_act(self, t):
        for a in self.acts:
            if a.t0 <= t <= a.t1:
                return a
        return None

    def _loco_pose(self, t) -> Pose:
        P = self.loco.pose(t)
        f = 1.0 if P["facing"] >= 0 else -1.0

        def ang(a, b):        # absolute angle of segment a->b, measured from straight down, + forward
            return math.atan2(f * (b[0] - a[0]), -(b[1] - a[1]))
        hip, neck, head = P["hip"], P["neck"], P["head"]
        (h0, k0, a0, _), (h1, k1, a1, _) = P["legs"]
        (s0, e0, w0), (s1, e1, w1) = P["arms"]
        lean = math.atan2(f * (neck[0] - hip[0]), neck[1] - hip[1])
        return Pose(x=hip[0], y=hip[1], lean=lean, head=0.0, au=ang(s0, e0), al=ang(e0, w0), bu=ang(s1, e1),
                    bl=ang(e1, w1), lu=ang(h0, k0), ll=ang(k0, a0), mu=ang(h1, k1), ml=ang(k1, a1), f=f,
                    feet=(a0, a1))

    def _resolve(self, a: Act, start: Pose):
        """Turns relative keys into absolute poses from where the body actually is."""
        out = [(a.t0, start, "linear", False)]
        cur = start
        g0 = self.world.ground(start.x) if self.world else 0.0
        for dt, kv, ek in a.keys:
            kv = dict(kv)
            p = replace(cur)
            ball = kv.pop("ballistic", False)
            if "dx" in kv:
                p.x = start.x + start.f * kv.pop("dx")
            if "dy" in kv:
                p.y = start.y + kv.pop("dy")
            if "y" in kv:
                p.y = g0 + kv.pop("y")
            if "feet" in kv:
                fx = kv.pop("feet")
                if fx == "keep":
                    p.feet = start.feet
                elif fx is None:
                    p.feet = None
                else:
                    pts = []
                    for i, d in enumerate(fx):     # per foot: None (free), "keep" (where it was), "prev", (dx, height)
                        if d is None:
                            pts.append(None)
                        elif d == "keep":
                            pts.append(start.feet[i] if start.feet else None)
                        elif d == "prev":          # stays where the previous key put it
                            pts.append(cur.feet[i] if cur.feet else None)
                        else:
                            X = start.x + start.f * d[0]
                            Y = (d[1] if len(d) > 1 else 0.0) + g0
                            pts.append((X, Y + self.ankle))
                    p.feet = tuple(pts)
            if "hands" in kv:
                hs = kv.pop("hands")
                p.hands = None if hs is None else tuple(
                    None if h is None else (h if callable(h) else (start.x + start.f * h[0], g0 + h[1])) for h in hs)
            for k, v in kv.items():
                if a.exaggerate != 1.0 and k in ("au", "al", "bu", "bl", "lean", "head"):
                    v = getattr(start, k) + (v - getattr(start, k)) * a.exaggerate   # pushed further for comedy
                setattr(p, k, v)
            if not ball:                                # each key pose clears the floor (the in-betweens then do too)
                self._t = getattr(self, "_t", 0.0)
                p.y -= min(0.0, self._below_floor(p))
            out.append((a.t0 + dt, p, ek, ball))
            cur = p
        a.resolved = out
        a.foot_paths = [self._foot_path(pa, pb) for (_, pa, _, _), (_, pb, _, _) in zip(out, out[1:])]
        a.hand_paths = [self._hand_path(pa, pb) for (_, pa, _, _), (_, pb, _, _) in zip(out, out[1:])]
        # in-betweens that would dip into the floor (a body rotating through a roll): a smooth lift - the upper envelope
        # of what is needed, with bounded curvature, so the hips arc over instead of being shoved up and dropped
        a.lift_grid = None
        hz, T = 120, out[-1][0] - out[0][0]
        n = int(T * hz) + 1
        need = []
        for k in range(n):
            tt = a.t0 + k / hz
            q, qa = self._eval(a, tt), self._eval(a, max(a.t0, tt - 0.06))     # as step() will pose it
            turn = qa.lean - q.lean
            q.au, q.al, q.bu, q.bl = qa.au + turn, qa.al + turn, qa.bu + turn, qa.bl + turn
            need.append(max(0.0, -self._below_floor(q)))
        if max(need or [0.0]) > 0.002:
            c, w = 30.0, int(0.35 * hz)                 # |lift''| <= 60 m/s^2
            env = []
            for k in range(n):
                best = 0.0
                for m in range(max(0, k - w), min(n, k + w + 1)):
                    if need[m] > best:
                        best = max(best, need[m] - c * ((k - m) / hz) ** 2)
                env.append(best)
            a.lift_grid = (a.t0, hz, env)

    def _free_ankles(self, p: Pose):
        """Where the ankles hang in this pose with no foot targets (the floor still stops them)."""
        q = replace(p, feet=None, hands=None)
        self._t = getattr(self, "_t", 0.0)
        return [leg[2] for leg in self.joints(q)["legs"]]

    def _hand_path(self, pa: Pose, pb: Pose):
        """Like _foot_path for hands placed at fixed points: a hand let go of (or put down on) a spot travels between
        the spot and where the free arm will be, instead of blending joint angles (which can flip the long way round).
        Hands following moving targets (callables) keep the weight blend."""
        ha = pa.hands or (None, None)
        hb = pb.hands or (None, None)
        if any(callable(x) for x in ha + hb) or all(x is None for x in ha + hb):
            return None
        if all((x is None) == (y is None) for x, y in zip(ha, hb)):
            return None                                 # placed both ends (or free both ends): nothing to route
        def free(p):
            q = replace(p, feet=None, hands=None)
            self._t = getattr(self, "_t", 0.0)
            return [arm[2] for arm in self.joints(q)["arms"]]
        fa = free(pa) if any(x is None for x in ha) else None
        fb = free(pb) if any(x is None for x in hb) else None
        ends = []
        for i in range(2):
            x, y = ha[i], hb[i]
            if x is None and y is None:
                ends.append(None)
            else:
                ends.append((x if x is not None else fa[i], y if y is not None else fb[i]))
        return ends

    def _foot_path(self, pa: Pose, pb: Pose):
        """Both ends of each foot's path through a segment. A foot that is placed at one end and free at the
        other travels between the spot and where the free pose holds it, so the path is known and can be lifted
        clear of the floor, instead of falling out of a blend of joint angles (which skates along the floor)."""
        fa = pa.feet or (None, None)
        fb = pb.feet or (None, None)
        if all(x is None for x in fa + fb):
            return None
        free_a = self._free_ankles(pa) if any(x is None for x in fa) else None
        free_b = self._free_ankles(pb) if any(x is None for x in fb) else None
        ends = []
        for i in range(2):
            x, y = fa[i], fb[i]
            if x is None and y is None:
                ends.append(None)
            else:
                ends.append((x if x is not None else free_a[i], y if y is not None else free_b[i],
                             x is not None, y is not None))
        return ends

    def _eval(self, a: Act, t: float) -> Pose:
        R = a.resolved
        if t <= R[0][0]:
            return R[0][1]
        for si, ((ta, pa, _, _), (tb, pb, ek, ball)) in enumerate(zip(R, R[1:])):
            if ta <= t <= tb:
                u = (t - ta) / max(1e-6, tb - ta)
                k = ease(ek, u, a.overshoot)
                p = Pose(**{fl.name: getattr(pa, fl.name) for fl in fields(Pose)})
                for n in ANGLES + ("squash",):
                    setattr(p, n, lerp(getattr(pa, n), getattr(pb, n), k))
                if ball:                            # real gravity between take-off and landing
                    T = tb - ta
                    s = u * T
                    vy = (pb.y - pa.y) / T + 0.5 * G * T
                    p.x = lerp(pa.x, pb.x, u)
                    p.y = pa.y + vy * s - 0.5 * G * s * s
                else:
                    p.x, p.y = lerp(pa.x, pb.x, k), lerp(pa.y, pb.y, k)

                p.f = pb.f if u > 0.5 else pa.f
                G_ = getattr(a, "lift_grid", None)
                if G_:
                    g0_, hz_, env_ = G_
                    x_ = (t - g0_) * hz_
                    j_ = max(0, min(len(env_) - 2, int(x_)))
                    p.y += lerp(env_[j_], env_[j_ + 1], max(0.0, min(1.0, x_ - j_)))
                pts, ws = [], []
                for end in (a.foot_paths[si] or (None, None)):
                    if end is None:
                        pts.append(None); ws.append(0.0)
                        continue
                    x, y, placed_a, placed_b = end
                    if placed_a and placed_b and math.dist(x, y) < 0.02:
                        pts.append(x if u < 0.5 else y); ws.append(1.0)   # planted: it does not move at all
                        continue
                    kk = u if ball else k
                    if not ball and placed_a != placed_b:       # lifting off / setting down: start and end gently
                        kk = ease("inout", u)
                    q = lerp_pt(x, y, kk)
                    if not ball and y[1] > x[1] + 0.05:         # stepping up onto something: up first, then over
                        q = (lerp(x[0], y[0], ease("in", kk)), lerp(x[1], y[1], ease("out", kk)))
                    if not ball:                                # a step arcs over the floor
                        q = (q[0], q[1] + min(0.12, 0.35 * abs(y[0] - x[0])) * math.sin(math.pi * kk))
                    pts.append(q); ws.append(1.0)
                p.feet = tuple(pts) if any(q is not None for q in pts) else None
                p.feet_w = tuple(ws)
                hp = a.hand_paths[si] if getattr(a, "hand_paths", None) else None
                if hp:                                    # routed: an arc around the shoulder, through the front
                    kh = ease("inout", u)
                    sh = (p.x + p.f * math.sin(p.lean) * self.l_torso * 0.86 * p.squash,
                          p.y + math.cos(p.lean) * self.l_torso * 0.86 * p.squash)
                    pts = []
                    for e in hp:
                        if e is None:
                            pts.append(None)
                            continue
                        (ax, ay), (bx, by) = e
                        ov = getattr(a, "hand_from", {}).get(si)
                        if ov is not None and ov[len(pts)] is not None:   # from where the hand really was
                            ax, ay = ov[len(pts)]
                        ta = math.atan2(ay - sh[1], p.f * (ax - sh[0]))
                        tb = math.atan2(by - sh[1], p.f * (bx - sh[0]))
                        da, db = math.hypot(ax - sh[0], ay - sh[1]), math.hypot(bx - sh[0], by - sh[1])
                        th, dd = lerp(ta, tb, kh), lerp(da, db, kh)
                        pts.append((sh[0] + p.f * math.cos(th) * dd, sh[1] + math.sin(th) * dd))
                    p.hands, p.hands_w = tuple(pts), tuple(0.0 if q is None else 1.0 for q in pts)
                    return p
                ha = pa.hands or (None, None)
                hb = pb.hands or (None, None)
                pts, ws = [], []
                for x, y in zip(ha, hb):
                    x = x(t) if callable(x) else x
                    y = y(t) if callable(y) else y
                    if x is not None and y is not None:
                        q = lerp_pt(x, y, k)
                        g = self._floor(q[0])
                        if x[1] < g + 0.12 and y[1] < g + 0.12 and abs(y[0] - x[0]) > 0.03:
                            q = (q[0], q[1] + min(0.1, 0.4 * abs(y[0] - x[0])) * math.sin(math.pi * k))  # a hand
                            # moved from one spot on the floor to another is lifted, not slid
                        pts.append(q); ws.append(1.0)
                    elif y is not None:
                        pts.append(y); ws.append(k)
                    elif x is not None:
                        pts.append(x); ws.append(1 - k)
                    else:
                        pts.append(None); ws.append(0.0)
                p.hands, p.hands_w = (tuple(pts) if any(q is not None for q in pts) else None), tuple(ws)
                return p
        return R[-1][1]

    def step(self, t: float, dt: float):
        a = self._current_act(t)
        if a is not None:
            if a.resolved is None:
                start = self._last_pose if hasattr(self, "_last_pose") else self._loco_pose(t)
                self._resolve(a, start)
            # follow-through: arms trail the body a little, the head a little less
            si = next((k for k, ((ta, *_), (tb, *_)) in enumerate(zip(a.resolved, a.resolved[1:])) if ta <= t <= tb), None)
            if si is not None and getattr(a, "hand_paths", None) and a.hand_paths[si]:
                a.hand_from = getattr(a, "hand_from", {})
                if si not in a.hand_from:              # a routed hand starts from where it is now (lag included)
                    pj = getattr(self, "_prev_J", None)
                    a.hand_from[si] = [None if (e is None or pj is None) else pj["arms"][k][2]
                                       for k, e in enumerate(a.hand_paths[si])]
            p = self._eval(a, t)
            pa = self._eval(a, max(a.t0, t - 0.06))
            turn = pa.lean - p.lean                       # the arms lag the body's pose, not its rotation
            p.au, p.al, p.bu, p.bl = pa.au + turn, pa.al + turn, pa.bu + turn, pa.bl + turn
            if a.upper_free:                          # seated: feelings move the arms, head and lean only
                q = self._feelings(t, replace(p))
                p.au, p.al, p.bu, p.bl, p.head = q.au, q.al, q.bu, q.bl, q.head
                p.lean += max(-0.25, min(0.25, q.lean - p.lean))
            self._act = a
        else:
            if self._act is not None:                   # hand control back exactly where the action ended
                end = self._eval(self._act, self._act.t1)
                self._handback(end, t)
                self._blend_from = (end, t)               # and blend from that pose for a moment
                self._act = None
            self.loco.step(t, dt)
            p = self._loco_pose(t)
            p = self._feelings(t, p)
            for t0, t1, lean, crouch in self.postures:            # lean into a push, crouch to sneak
                if t0 <= t <= t1:
                    w = min(smooth((t - t0) / 0.3), smooth((t1 - t) / 0.3))
                    p.lean = lerp(p.lean, lean, w)
                    p.y -= crouch * self.H * w
            for t0, t1, hs in self.reaches:                        # hands on an object while walking
                if t0 <= t <= t1:
                    w = min(smooth((t - t0) / 0.25), smooth((t1 - t) / 0.25))
                    p.hands = tuple(h(t) if callable(h) else h for h in hs)
                    p.hands_w = tuple(w if h is not None else 0.0 for h in hs)
            bf = getattr(self, "_blend_from", None)
            if bf is not None and t - bf[1] < 0.3:                 # motion blending out of an action
                k = smooth((t - bf[1]) / 0.3)
                e = bf[0]
                for n in ("au", "al", "bu", "bl", "lean", "head", "squash"):
                    ev, pv = getattr(e, n), getattr(p, n)
                    if n != "squash":                       # a full turn ago is the same angle: no extra spin
                        ev += round((pv - ev) / TAU) * TAU
                    setattr(p, n, lerp(ev, pv, k))
                p.y = lerp(e.y, p.y, k)
                p.x = lerp(e.x, p.x, k)
        p = self._gaze(t, p)
        prev = getattr(self, "_last_pose", None)
        if prev is not None and dt > 0:              # no limb whips round faster than a human can swing it
            cap = 25.0 * dt                            # measured against the torso: a roll turns limbs with it
            for n in ("au", "al", "bu", "bl", "lu", "ll", "mu", "ml"):
                v, pv = getattr(p, n) + p.lean, getattr(prev, n) + prev.lean
                d = (v - pv + math.pi) % TAU - math.pi
                if abs(d) > cap:
                    setattr(p, n, pv + math.copysign(cap, d) - p.lean)
        p = self._springs(p, dt)
        need = -min(0.0, self._below_floor(p))        # a roll or a fall never pushes the head or hands through the floor
        lift = max(need, getattr(self, "_lift", 0.0) - 1.2 * dt)   # ...and lets go gently, not with a drop
        self._lift = lift
        p.y += lift
        self._last_pose = p
        self.pose_now = p
        self._prev_J = None
        self._prev_J = self.joints(p)                 # where the knees and elbows were (IK keeps continuity)
        self.hip = (p.x, p.y)
        self.speed = self.loco.speed if a is None else 0.0
        self._t = t

    def z_at(self, t: float) -> float:
        """Depth at time t: the actor's lane plus any step toward or away from the camera (eased in and out)."""
        z = self.z
        for t0, t1, dz in self.depth:
            if t0 <= t <= t1:
                z += dz * min(smooth((t - t0) / 0.4), smooth((t1 - t) / 0.4))
        return z

    def look_at(self, t0: float, t1: float, target) -> float:
        """Attention: from t0 to t1 the head turns to `target` (another actor, a prop, or an (x, y) point)."""
        self.looks.append((t0, t1, target))
        return t1

    def _gaze(self, t: float, p: Pose) -> Pose:
        """Tilts the head toward whatever the actor is looking at (eased in and out over a quarter second)."""
        for t0, t1, target in self.looks:
            if not (t0 <= t <= t1):
                continue
            if isinstance(target, tuple):
                tx, ty = target
            elif hasattr(target, "pose_now") and hasattr(target, "joints"):
                tx, ty = target.joints(target.pose_now)["head"]
            elif hasattr(target, "pos"):
                tx, ty = target.pos(t)[:2]
                ty += getattr(target, "h", 0.0) * 0.5
            else:
                continue
            w = min(smooth((t - t0) / 0.25), smooth((t1 - t) / 0.25))
            ny = p.y + math.cos(p.lean) * self.l_torso
            ahead = p.f * (tx - p.x)
            elev = math.atan2(ty - ny, max(0.15, abs(ahead)))
            want = max(-0.65, min(0.7, -0.75 * elev - 0.6 * p.lean))      # chin up to look up, down to look down
            p.head = lerp(p.head, want, w)
        return p

    def busy(self, t0: float, t1: float, moving_only: bool = False) -> bool:
        """Is anything already directed for this actor between t0 and t1?"""
        if any(a.t0 < t1 and a.t1 > t0 for a in self.acts):
            return True
        if any(m0 < t1 and m1 > t0 and m != "handoff" for m0, m1, _, _, m in self.loco.moves):
            return True
        return False if moving_only else any(f0 < t1 and f1 > t0 for f0, f1, _ in self.feels)

    def _handback(self, end: Pose, t: float):
        L = self.loco
        if end.feet and all(q is not None for q in end.feet):
            (nx, ny), (fx, fy) = end.feet
            L._feet[0].x, L._feet[0].y = nx, ny - self.ankle
            L._feet[1].x, L._feet[1].y = fx, fy - self.ankle
        else:
            L._feet[0].x, L._feet[1].x = end.x + end.f * 0.08 * self.H, end.x - end.f * 0.06 * self.H
            for ft in L._feet:
                ft.y = L.ground(ft.x)
        for ft in L._feet:
            ft.swing = None
        L._hip_y = end.y
        L.facing = end.f
        L._face_vis = end.f

    def _feelings(self, t: float, p: Pose) -> Pose:
        """Faceless emotion: the whole body shows it (layered over standing, eased in and out)."""
        for t0, t1, emo in self.feels:
            if not (t0 <= t <= t1):
                continue
            w = min(smooth((t - t0) / 0.35), smooth((t1 - t) / 0.35))
            u = t - t0
            q = replace(p)
            s = math.sin
            if emo in ("happy", "excited"):
                bounce = abs(s(u * (7.5 if emo == "excited" else 5.0))) * (0.07 if emo == "excited" else 0.03) * self.H
                q.y = p.y - 0.04 * self.H + bounce
                q.lean = -0.08
                q.head = -0.25
                if emo == "excited":
                    q.au, q.al = 2.6 + 0.3 * s(u * 15), 2.9
                    q.bu, q.bl = 2.6 + 0.3 * s(u * 15 + 2), 2.9
                else:
                    q.au, q.al = 0.35 + 0.25 * s(u * 5), 0.9
                    q.bu, q.bl = 0.25 - 0.2 * s(u * 5), 0.7
            elif emo == "angry":
                q.lean, q.head = 0.28, 0.25
                q.y = p.y - 0.05 * self.H
                tense = 0.04 * s(u * 37)
                q.au, q.al = -0.35 + tense, 0.6
                q.bu, q.bl = -0.3 - tense, 0.55
            elif emo in ("fear", "scared"):
                q.lean, q.head = -0.15, 0.45
                q.y = p.y - 0.14 * self.H
                tr = 0.05 * s(u * 45)
                q.au, q.al = 1.2 + tr, 2.7
                q.bu, q.bl = 1.1 - tr, 2.6
                q.x = p.x - p.f * 0.008 * self.H * s(u * 22)        # a tremble, not a shake
            elif emo == "confused":
                q.head = -0.4 + 0.12 * s(u * 1.7)
                q.lean = 0.0
                q.au, q.al = 2.4, 2.75 + 0.15 * s(u * 14)     # scratching the head
                q.bu, q.bl = 0.5, 2.2
            elif emo == "curious":
                q.lean, q.head = 0.38, 0.3 + 0.1 * s(u * 2)
                q.y = p.y + 0.02 * self.H
                q.au, q.al = 0.4, 2.6
                q.bu, q.bl = -0.25, 0.3
            elif emo == "sarcastic":
                q.lean, q.head = -0.12, -0.3
                c = 0.3 * max(0.0, s(u * 4.0)) ** 8
                q.au, q.al = 0.9, 1.4 - c                      # a slow, mocking clap
                q.bu, q.bl = 0.9, 1.4 + c
            elif emo == "frustrated":
                q.lean, q.head = 0.2, 0.5
                q.au, q.al = 0.9, 2.6                          # facepalm
                q.bu, q.bl = -0.4 + 0.2 * s(u * 3), 0.2
            elif emo == "confident":
                q.lean, q.head = -0.12, -0.18
                q.au, q.al = 0.7, -0.6                         # hands on hips
                q.bu, q.bl = 0.7, -0.6
                q.y = p.y + 0.01 * self.H
            elif emo == "embarrassed":
                q.lean, q.head = 0.12, 0.55
                q.y = p.y - 0.03 * self.H
                q.au, q.al = -0.5, -1.1                        # hands behind the back
                q.bu, q.bl = -0.45, -1.0
                q.x = p.x + p.f * 0.01 * self.H * s(u * 3)
            elif emo == "sad":
                q.lean, q.head = 0.18, 0.7
                q.y = p.y - 0.03 * self.H
                q.au, q.al = -0.02, 0.05
                q.bu, q.bl = -0.03, 0.04
            elif emo == "surprised":
                k = min(1.0, u / 0.25)
                q.lean, q.head = -0.25, -0.35
                q.au, q.al = 1.9, 1.1
                q.bu, q.bl = 1.8, 1.0
                q.x = p.x - p.f * 0.06 * self.H * ease("snap", k)
            elif emo == "laugh":
                q.lean = 0.35 + 0.15 * s(u * 16)
                q.head = 0.2
                q.au, q.al = 0.25, 1.95
                q.bu, q.bl = 0.3, 1.9
                q.y = p.y - 0.03 * self.H + 0.015 * self.H * abs(s(u * 16))
            for n in ANGLES:
                setattr(p, n, lerp(getattr(p, n), getattr(q, n), w))
            p.x, p.y = lerp(p.x, q.x, w), lerp(p.y, q.y, w)
        return p

    def _springs(self, p: Pose, dt: float) -> Pose:
        """Head and forearms follow the body through a spring: overlap on swings, a wobble on hard stops."""
        for n, k, damp in (("head", 260.0, 16.0), ("al", 320.0, 18.0), ("bl", 320.0, 18.0)):
            target = getattr(p, n)
            x, v = self._spring.get(n, (target, 0.0))
            x += round((target - x) / TAU) * TAU          # a full turn in the keys is the same angle: no whip
            for _ in range(2):
                h = dt / 2
                a = k * (target - x) - damp * v
                v += a * h
                x += v * h
            self._spring[n] = (x, v)
            setattr(p, n, x)
        return p

    def _floor(self, x):
        return self.world.ground(x) if self.world else 0.0

    def _below_floor(self, p: Pose) -> float:
        """How far the lowest of head, hands and knees sits under the floor (negative = through it)."""
        J = self.joints(p)
        g = self._floor(p.x)                  # the floor under the body: a ledge beside it is a wall, not a floor
        low = [J["head"][1] - self.r_head - g]
        low += [w[1] - 0.01 - g for _, _, w in J["arms"]]
        low += [k[1] - 0.015 - g for _, k, _, _ in J["legs"]]
        return min(low)

    # ---- drawing -------------------------------------------------------------------------------------------
    def joints(self, p: Pose) -> dict:
        f, H, sq = p.f, self.H, p.squash
        hip = (p.x, p.y)
        neck = (hip[0] + f * math.sin(p.lean) * self.l_torso * sq, hip[1] + math.cos(p.lean) * self.l_torso * sq)
        hd = p.lean + p.head
        head = (neck[0] + f * math.sin(hd) * (self.l_neck + self.r_head),
                neck[1] + math.cos(hd) * (self.l_neck + self.r_head))
        sh = (hip[0] + f * math.sin(p.lean) * self.l_torso * 0.86 * sq, hip[1] + math.cos(p.lean) * self.l_torso * 0.86 * sq)

        def seg(a, ang, L):
            return a[0] + f * math.sin(ang) * L, a[1] - math.cos(ang) * L
        def ang(a, b):
            return math.atan2(f * (b[0] - a[0]), -(b[1] - a[1]))

        def reach(root, target, l1, l2, bend, near=None):
            d = math.hypot(target[0] - root[0], target[1] - root[1])
            if d > (l1 + l2) * 0.999:              # out of reach: the limb straightens toward it
                target = (root[0] + (target[0] - root[0]) / d * (l1 + l2) * 0.999,
                          root[1] + (target[1] - root[1]) / d * (l1 + l2) * 0.999)
            mid = rig2d._ik(root, target, l1, l2, bend)
            if near is not None:                   # of the two ways to bend, the one closest to the pose: no flips
                alt = rig2d._ik(root, target, l1, l2, -bend)
                if math.dist(alt, near) < math.dist(mid, near) - 1e-6:
                    mid = alt
            return ang(root, mid), ang(mid, target)

        def blend(a1, a2, w):                      # shortest way round
            d = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
            return a1 + d * w
        arms = []
        for i, (u, l) in enumerate(((p.au, p.al), (p.bu, p.bl))):
            target = p.hands[i] if p.hands else None
            if callable(target):
                target = target(self._t)
            w = p.hands_w[i] if p.hands else 0.0
            if target is not None and w > 0:
                prevJ = getattr(self, "_prev_J", None)
                iu, il = reach(sh, target, self.l_up, self.l_fore, -f, prevJ["arms"][i][1] if prevJ else None)
                u, l = blend(u, iu, w), blend(l, il, w)
            el = seg(sh, u, self.l_up)
            arms.append((sh, el, seg(el, l, self.l_fore)))
        legs = []
        for i, (u, l) in enumerate(((p.lu, p.ll), (p.mu, p.ml))):
            fw = p.feet_w[i] if isinstance(p.feet_w, tuple) else p.feet_w
            if p.feet and p.feet[i] is not None and fw > 0:
                prevJ = getattr(self, "_prev_J", None)
                iu, il = reach(hip, p.feet[i], self.l_thigh, self.l_shin, f, prevJ["legs"][i][1] if prevJ else None)
                u, l = blend(u, iu, fw), blend(l, il, fw)
            kn = seg(hip, u, self.l_thigh)
            ank = seg(kn, l, self.l_shin)
            floor = self._floor(ank[0]) + self.ankle
            if ank[1] < floor - 1e-4:                # a swinging foot meets the floor instead of passing through it
                u, l = reach(hip, (ank[0], floor), self.l_thigh, self.l_shin, f)
                kn = seg(hip, u, self.l_thigh)
                ank = seg(kn, l, self.l_shin)
            toe = (ank[0] + f * 0.075 * H, ank[1] - self.ankle * 0.6)
            legs.append((hip, kn, ank, toe))
        return {"hip": hip, "neck": neck, "head": head, "arms": arms, "legs": legs}

    def draw(self, d, S, scale, t):
        p = self.pose_now
        J = self.joints(p)
        L = self.look
        col = L.body or L.ink
        far = tuple(int(c + (235 - c) * 0.32) for c in col)
        w = max(3, int(scale * 0.034 * self.H * L.line))

        def line(pts, c, ww=w):
            q = [S(*x) for x in pts]
            d.line(q, fill=c, width=ww, joint="curve")
            for x, y in q:
                d.ellipse([x - ww / 2, y - ww / 2, x + ww / 2, y + ww / 2], fill=c)
        h, k, a, toe = J["legs"][1]
        line([h, k, a, toe], far)
        line(J["arms"][1], far)
        line([J["hip"], J["neck"]], col, int(w * 1.05))
        line([J["neck"], J["head"]], col)
        cx, cy = S(*J["head"])
        r = self.r_head * scale
        if self.faceless:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        else:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=L.skin, outline=col, width=int(w * 0.8))
            F.draw(d, cx, cy, r, self.loco._face(t), p.f, t, ink=L.ink, lw=w * 0.6)
        h, k, a, toe = J["legs"][0]
        line([h, k, a, toe], col)
        line(J["arms"][0], col)
        for t0, t1, sym in self.symbols:
            if t0 <= t <= t1:
                pop = ease("back", min(1.0, (t - t0) / 0.3))
                sx, sy = cx + p.f * r * 0.9, cy - r * (1.6 + 0.4 * pop)
                from PIL import ImageFont
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(8, int(r * 1.6 * pop)))
                d.text((sx, sy), sym, font=fnt, fill=col, anchor="mm")
        self._joints = J

    def hand_pos(self, which="near"):
        J = getattr(self, "_joints", None) or self.joints(self.pose_now)
        return J["arms"][0 if which == "near" else 1][2]


# ---- world, platforms, props ---------------------------------------------------------------------------------
class World:
    """The ground: flat floor at 0, boxes to stand on (platforms), slopes (ramps) and staircases."""

    def __init__(self):
        self.platforms: list[tuple] = []        # (x0, x1, top)
        self.ramps: list[tuple] = []            # (x0, x1, y0, y1): a straight slope

    def ground(self, x: float) -> float:
        h = [top for x0, x1, top in self.platforms if x0 <= x <= x1]
        h += [y0 + (y1 - y0) * (x - x0) / (x1 - x0) for x0, x1, y0, y1 in self.ramps if x0 <= x <= x1]
        return max(h or [0.0])

    def stairs(self, x0: float, steps: int, rise: float = 0.17, run: float = 0.3, direction: float = 1.0,
               landing: float = 1.2) -> float:
        """A staircase going up from x0 in `direction`, with a landing at the top. Returns the far end's x."""
        for i in range(steps):
            a, b = x0 + direction * i * run, x0 + direction * (i + 1) * run
            far = b + direction * (landing if i == steps - 1 else 0.0)
            self.platforms.append((min(a, far) if direction > 0 else min(b, far), max(a, far), rise * (i + 1)))
        return x0 + direction * (steps * run + landing)

    def pace(self, x: float, mode: str = "walk") -> float:
        """Top speed over the ground at x: stairs one step at a time (~0.55 m/s walking, 1.6 running), slopes slower
        the steeper they are, flat ground unlimited."""
        g = [self.ground(x + 0.05 * k) for k in range(-6, 7)]
        jumps = sum(1 for a, b in zip(g, g[1:]) if abs(b - a) > 0.05)
        if jumps:
            return 1.6 if mode == "run" else 0.55
        slope = abs(g[-1] - g[0]) / 0.6
        if slope > 0.02:
            return (3.0 if mode == "run" else 1.25) / (1 + 2.5 * slope)
        return 99.0

    def highest(self, xa: float, xb: float) -> float:
        """The highest ground between two points (what a swinging foot has to clear)."""
        lo, hi = min(xa, xb), max(xa, xb)
        pts = [lo, hi] + [q for x0, x1, _ in self.platforms for q in (x0, x1) if lo <= q <= hi]
        pts += [q for x0, x1, _, _ in self.ramps for q in (x0, x1) if lo <= q <= hi]
        return max(self.ground(q) for q in pts)

    def foothold(self, x: float, f: float, toe: float, heel: float, frm: float | None = None) -> float:
        """Moves a landing spot so the whole foot is on one level (no toe stubbed into a riser, no heel hanging over
        an edge) and, on stairs, so a step goes up or down one stair at a time. Prefers stepping a little short."""
        if frm is not None:                        # one stair per step: shorten the stride until it is
            g0 = self.ground(frm)
            while abs(self.ground(x) - g0) > 0.22 and f * (x - frm) > 0.12:
                x -= f * 0.02

        def flat(c):                               # level under heel and toe (a slope may tilt the foot a little)
            g = self.ground(c)
            on_ramp = any(x0 <= c <= x1 for x0, x1, _, _ in self.ramps)
            tol = 0.25 if on_ramp else 0.0
            toe_, heel_ = toe + 0.05, heel + 0.03         # room to lift the toe without catching the riser
            return (abs(self.ground(c + f * toe_) - g) < 0.004 + tol * toe_
                    and abs(self.ground(c - f * heel_) - g) < 0.004 + tol * heel_)
        if not self.platforms or flat(x):
            return x
        for k in range(1, 12):
            for cand in (x - f * 0.03 * k, x + f * 0.03 * k):
                if flat(cand) and (frm is None or abs(self.ground(cand) - self.ground(frm)) <= 0.22):
                    return cand
        return x


@dataclass
class Prop:
    kind: str
    x: float
    y: float
    w: float
    h: float
    z: float = 1.0
    angle: float = 0.0
    label: str = ""
    color: tuple = (240, 200, 80)
    keys: list = field(default_factory=list)          # (t, x, y, angle, ease) - keyed moves
    carriers: list = field(default_factory=list)      # (t0, t1, actor, hand)
    follows: list = field(default_factory=list)       # (t0, t1, actor, offset) - pushed or dragged along
    data: dict = field(default_factory=dict)          # chart values, folder open amount, image...
    flights: list = field(default_factory=list)       # thrown / dropped: dicts with t0, launch, samples
    no_shadow: bool = True

    def body_x(self, t):
        return self.x

    def pos(self, t):
        """Where the object is at time t: carried in a hand, riding along with a pusher, keyed, or resting."""
        done = None
        for i, (t0, t1, actor, off) in enumerate(self.follows):
            if off is None:                       # the offset is fixed the moment the pushing starts
                base = self._unfollowed(t0)
                off = (base[0] - actor.hips_x(t0), base[1])
                self.follows[i] = (t0, t1, actor, off)
            if t0 <= t <= t1:
                return actor.hips_x(t) + off[0], off[1], 0.0
            if t > t1 and (done is None or t1 > done[0]):
                done = (t1, actor, off)
        if done is not None and not any(c[0] > done[0] for c in self.carriers) and \
                not any(k[0] > done[0] for k in self.keys):
            t1, actor, off = done
            return actor.hips_x(t1) + off[0], off[1], 0.0
        return self._unfollowed(t)

    def _unfollowed(self, t):
        for t0, t1, actor, hand in self.carriers:
            if t0 <= t <= t1 and (hasattr(actor, "_joints") or hasattr(actor, "pose_now")):
                hx, hy = actor.hand_pos(hand)
                p = (hx + self.data.get("grip_dx", 0.0) * actor.pose_now.f, hy + self.data.get("grip_dy", -self.h * 0.5),
                     self.data.get("carry_angle", 0.0) * actor.pose_now.f)
                self._last_held = p
                return p
        fl = None
        for f in self.flights:                         # the latest flight that has begun
            if t >= f["t0"]:
                fl = f
        if fl is not None and not any(fl["t0"] < c[0] <= t for c in self.carriers) and \
                not any(fl["t0"] < k[0] <= t for k in self.keys):
            return self._fly(fl, t)
        x, y, ang = self.x, self.y, self.angle
        held = getattr(self, "_last_held", None) or (self.x, self.y, self.angle)
        keys = [(k[0], held[0], held[1], held[2], k[4]) if k[1] is None else k for k in self.keys]
        for (ta, xa, ya, aa, _), (tb, xb, yb, ab, ek) in zip(keys, keys[1:]):
            if t >= tb:
                x, y, ang = xb, yb, ab
            elif ta <= t < tb:
                k = ease(ek, (t - ta) / max(1e-6, tb - ta))
                return lerp(xa, xb, k), lerp(ya, yb, k), lerp(aa, ab, k)
        if keys and t >= keys[-1][0]:
            return keys[-1][1], keys[-1][2], keys[-1][3]
        if keys and t < keys[0][0] and keys[0][1] is not None and self.keys[0][1] is not None:
            return keys[0][1], keys[0][2], keys[0][3]
        return x, y, ang

    # ---- physics -------------------------------------------------------------------------------------------
    def launch(self, t0: float, velocity, target=None, flight_time: float | None = None, bounce: float = 0.45,
               spin: float = 0.0, world=None):
        """From time t0 the object flies on gravity from wherever it is then (a hand at release, a shelf), bounces
        (losing energy each time), slides or rolls to rest. velocity: (vx, vy) m/s, or None with `target` (an (x, y)
        point or a callable t -> (x, y)) and `flight_time`, to aim it."""
        self.flights.append(dict(t0=t0, velocity=velocity, target=target, T=flight_time, bounce=bounce, spin=spin,
                                 world=world, samples=None))
        return t0 + (flight_time or 1.0)

    def _fly(self, f, t):
        if f["samples"] is None:
            start = getattr(self, "_last_held", None) or self._resting_before(f["t0"])
            x0, y0, a0 = start
            if f["velocity"] is not None:
                vx, vy = f["velocity"]
            else:
                tgt = f["target"](f["t0"] + f["T"]) if callable(f["target"]) else f["target"]
                T = f["T"]
                vx = (tgt[0] - x0) / T
                vy = (tgt[1] - y0 + 0.5 * G * T * T) / T
            f["samples"] = _simulate(x0, y0, a0, vx, vy, f["spin"], f["bounce"], self.w, self.h,
                                     (f["world"].ground if f["world"] else (lambda x: 0.0)),
                                     friction=self.data.get("friction", 6.0))
        S = f["samples"]
        u = (t - f["t0"]) * 120
        i = int(u)
        if i >= len(S) - 1:
            return S[-1]
        k = u - i
        a, b = S[i], S[i + 1]
        return lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)

    def _resting_before(self, t):
        saved, self.flights = self.flights, [f for f in self.flights if f["t0"] < t]
        try:
            return self._unfollowed(t - 1e-4) if self.flights or self.carriers or self.keys else (self.x, self.y, self.angle)
        finally:
            self.flights = saved

    def move(self, t0, t1, x, y, angle=0.0, how="inout"):
        if any(c1 <= t0 + 1e-6 for _, c1, _, _ in self.carriers) and not any(k[0] > max(c1 for _, c1, _, _ in
                                                                                    self.carriers) for k in self.keys):
            self.keys.append((t0, None, None, None, "linear"))        # from wherever the hand let go of it
        elif not self.keys:
            self.keys.append((t0, self.x, self.y, self.angle, "linear"))
        else:
            last = self.keys[-1]
            self.keys.append((t0, last[1], last[2], last[3], "linear"))
        self.keys.append((t1, x, y, angle, how))
        return t1

    def step(self, t, dt):
        self._t = t

    def value(self, name, t, default=0.0):
        """A keyed number (chart bar, folder opening): data[name] = [(t, v, ease), ...]."""
        ks = self.data.get(name)
        if not ks:
            return default
        if t <= ks[0][0]:
            return ks[0][1]
        for (ta, va, _), (tb, vb, ek) in zip(ks, ks[1:]):
            if ta <= t <= tb:
                return lerp(va, vb, ease(ek, (t - ta) / max(1e-6, tb - ta)))
        return ks[-1][1]

    def draw(self, d, S, scale, t):
        from . import props_draw
        props_draw.draw(self, d, S, scale, t)
