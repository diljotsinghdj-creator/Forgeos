"""Animation quality control: Generate -> Inspect -> Detect -> Correct -> Re-render -> Validate.

`record` plays a staged (not yet rendered) scene and keeps every joint of every character and where every prop is,
frame by frame. `inspect` measures the defects an animator looks for:

    stretch      a bone changing length (broken joint)            > 1 mm
    skid         a planted foot sliding                           > 6 mm in a frame
    floor        a foot, hand or head below the ground            > 1 cm
    teleport     the hips jumping                                 > 9 m/s
    snap         a limb flicking round relative to the body       > 1.1 rad in a frame (30 fps)
    jerk         the hips' acceleration                           > 120 m/s^2 (a landing is ~30)
    frozen       a visible character not moving at all           >= 3 s
    overlap      two characters' bodies passing through each other (torsos closer than 12 cm)
    prop_jump    a prop teleporting                               > 0.8 m in a frame (a hard throw is ~0.6)
    framing      a focal character's head outside the safe area (after the camera is set)

`check_video` inspects the rendered file: frame count, frozen stretches, black frames and flicker.
`refine` runs the loop that can be automated: stage -> record -> inspect -> direct the camera (camera.direct) ->
check framing -> widen and re-direct if needed -> restage for rendering. Motion defects are reported with times
so they can be fixed in the choreography; they are not papered over."""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .stick import Actor

LIMITS = dict(stretch=1e-3, skid=0.006, floor=0.01, teleport=9.0, snap=1.1, jerk=120.0, frozen=3.0, overlap=0.12,
              prop_jump=0.8)


@dataclass
class Defect:
    kind: str
    who: str
    t0: float
    t1: float
    worst: float


@dataclass
class Report:
    seconds: float
    fps: int
    metrics: dict = field(default_factory=dict)          # kind -> worst value over the scene
    defects: list = field(default_factory=list)          # Defect spans

    @property
    def clean(self) -> bool:
        return not self.defects

    def summary(self) -> str:
        if self.clean:
            return f"clean ({self.seconds:.1f} s checked at {self.fps} fps)"
        kinds = {}
        for d in self.defects:
            kinds[d.kind] = kinds.get(d.kind, 0) + 1
        return ", ".join(f"{k} x{n}" for k, n in sorted(kinds.items()))

    def to_json(self) -> str:
        return json.dumps(dict(seconds=self.seconds, fps=self.fps, metrics=self.metrics,
                               defects=[asdict(d) for d in self.defects]), indent=1)


@dataclass
class Recording:
    fps: int
    times: list
    actors: list                 # the Actor objects (for lengths and the world)
    joints: dict                 # actor index -> [joints dict per frame]
    props: dict                  # prop index -> [(x, y, angle) per frame]
    prop_objs: list
    acting: dict                 # actor index -> [name of the action playing or "" per frame]
    feeling: dict                # actor index -> [bool per frame]


def record(sc, seconds: float, fps: int | None = None) -> Recording:
    fps = fps or sc.fps
    actors = [a for a in sc.actors if isinstance(a, Actor)]
    props = [a for a in sc.actors if not isinstance(a, Actor) and hasattr(a, "pos")]
    R = Recording(fps, [], actors, {i: [] for i in range(len(actors))}, {i: [] for i in range(len(props))}, props,
                  {i: [] for i in range(len(actors))}, {i: [] for i in range(len(actors))})
    for n in range(int(seconds * fps)):
        t = n / fps
        for a in sc.actors:
            a.step(t, 1 / fps)
        R.times.append(t)
        for i, a in enumerate(actors):
            R.joints[i].append(a.joints(a.pose_now))
            act = a._current_act(t)
            R.acting[i].append(act.name if act else "")
            R.feeling[i].append(any(f0 <= t <= f1 for f0, f1, _ in a.feels))
        for i, p in enumerate(props):
            R.props[i].append(tuple(p.pos(t)))
    return R


def _rel(J, i, arm=False):
    """A limb's angle to the torso, in the character's own frame (so turning around is not a flick)."""
    f = J.get("f", 1.0)
    a, b = (J["arms"][i][0], J["arms"][i][1]) if arm else (J["legs"][i][0], J["legs"][i][1])
    th = math.atan2(f * (b[0] - a[0]), b[1] - a[1])
    tor = math.atan2(f * (J["neck"][0] - J["hip"][0]), J["neck"][1] - J["hip"][1])
    return (th - tor + math.pi) % (2 * math.pi) - math.pi


def _seg_dist(p1, p2, q1, q2):
    def d(p, a, b):
        ax, ay = b[0] - a[0], b[1] - a[1]
        L = ax * ax + ay * ay
        u = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L))
        return math.dist(p, (a[0] + ax * u, a[1] + ay * u))
    return min(d(p1, q1, q2), d(p2, q1, q2), d(q1, p1, p2), d(q2, p1, p2))


def inspect(R: Recording, limits: dict | None = None) -> Report:
    L = dict(LIMITS, **(limits or {}))
    dt = 1 / R.fps
    rep = Report(len(R.times) / R.fps, R.fps)
    worst = {k: 0.0 for k in L}
    raw = []                                          # (kind, who, t, value)

    def flag(kind, who, t, v):
        worst[kind] = max(worst[kind], v)
        raw.append((kind, who, t, v))
    for i, a in enumerate(R.actors):
        who = a.look.name or f"actor{i}"
        F = R.joints[i]
        floor = a._floor
        vel_prev = None
        for n, J in enumerate(F):
            t = R.times[n]
            for sh, el, wr in J["arms"]:
                e = max(abs(math.dist(sh, el) - a.l_up), abs(math.dist(el, wr) - a.l_fore))
                if e > L["stretch"]:
                    flag("stretch", who, t, e)
            for hip, kn, ank, _ in J["legs"]:
                e = max(abs(math.dist(hip, kn) - a.l_thigh), abs(math.dist(kn, ank) - a.l_shin))
                if e > L["stretch"]:
                    flag("stretch", who, t, e)
                u = floor(ank[0]) + a.ankle - ank[1]
                if u > L["floor"]:
                    flag("floor", who, t, u)
            hx, hy = J["head"]
            u = floor(J["hip"][0]) - (hy - a.r_head)
            if u > L["floor"]:
                flag("floor", who, t, u)
            if n == 0:
                continue
            P = F[n - 1]
            for k in range(2):
                p0, p1 = P["legs"][k][2], J["legs"][k][2]
                g0, g1 = floor(p0[0]) + a.ankle, floor(p1[0]) + a.ankle
                if abs(p0[1] - g0) < 0.002 and abs(p1[1] - g1) < 0.002:
                    s = abs(p1[0] - p0[0])
                    if s > L["skid"]:
                        flag("skid", who, t, s)
                for arm in (False, True):
                    d = abs((_rel(J, k, arm) - _rel(P, k, arm) + math.pi) % (2 * math.pi) - math.pi) / (30 * dt)
                    if d > L["snap"]:
                        flag("snap", who, t, d)
            v = (J["hip"][0] - P["hip"][0]) / dt, (J["hip"][1] - P["hip"][1]) / dt
            sp = math.hypot(*v)
            if sp > L["teleport"]:
                flag("teleport", who, t, sp)
            if vel_prev is not None:
                acc = math.hypot(v[0] - vel_prev[0], v[1] - vel_prev[1]) / dt
                if acc > L["jerk"]:
                    flag("jerk", who, t, acc)
            vel_prev = v
            w = int(L["frozen"] / dt)                  # frozen: nothing moved more than 3 mm over the last 3 s
            if n >= w:
                span = F[n - w:n + 1]
                pts = [[J_["head"] for J_ in span], [J_["hip"] for J_ in span]] + \
                      [[J_["arms"][k][2] for J_ in span] for k in range(2)]
                rng = max(max(math.dist(p, q) for q in pts_[::6]) for pts_ in pts for p in pts_[::6])
                if rng < 0.003:
                    flag("frozen", who, t, L["frozen"])
    # characters passing through each other
    for i in range(len(R.actors)):
        for j in range(i + 1, len(R.actors)):
            a, b = R.actors[i], R.actors[j]
            for n in range(len(R.times)):
                if abs(a.z_at(R.times[n]) - b.z_at(R.times[n])) > 0.04:
                    continue                          # in different lanes: one passes in front of the other
                A, B = R.joints[i][n], R.joints[j][n]
                d = _seg_dist(A["hip"], A["neck"], B["hip"], B["neck"])
                if d < L["overlap"]:
                    flag("overlap", f"{a.look.name}+{b.look.name}", R.times[n], L["overlap"] - d)
    for i, p in enumerate(R.prop_objs):
        P = R.props[i]
        for n in range(1, len(P)):
            d = math.dist(P[n][:2], P[n - 1][:2])
            if d > L["prop_jump"]:
                flag("prop_jump", getattr(p, "label", "") or p.kind, R.times[n], d)
    rep.metrics = {k: round(v, 4) for k, v in worst.items()}
    rep.defects = _spans(raw, dt)
    return rep


def _spans(raw, dt):
    out = []
    for kind, who, t, v in sorted(raw, key=lambda r: (r[0], r[1], r[2])):
        if out and out[-1].kind == kind and out[-1].who == who and t - out[-1].t1 <= 2.5 * dt:
            out[-1].t1 = t
            out[-1].worst = max(out[-1].worst, round(v, 4))
        else:
            out.append(Defect(kind, who, round(t, 3), round(t, 3), round(v, 4)))
    return out


# ---- framing ------------------------------------------------------------------------------------------------------
def to_screen(sc, x, y, z, t):
    """World point -> output pixel, with the scene's camera (pan, height, zoom) at time t."""
    cx, cy, zoom = sc.camera(t)
    W, H = sc.width, sc.height
    scale = sc.ppm / z
    gy = sc.horizon * H + (sc.ground * H - sc.horizon * H) / z + cy * scale
    px, py = W / 2 + (x - cx) * scale, gy - y * scale
    return (px - W / 2) * zoom + W / 2, (py - H / 2) * zoom + H / 2


def framing(sc, R: Recording, focus: list | None = None, safe=(0.06, 0.1, 0.04)) -> list[Defect]:
    """Heads of the focal characters (default: all) outside the safe area (top, bottom, sides fractions)."""
    top, bottom, side = safe
    out = []
    names = None if focus is None else {getattr(f, "look", f).name if hasattr(f, "look") else f for f in focus}
    for i, a in enumerate(R.actors):
        if names is not None and a.look.name not in names:
            continue
        for n, J in enumerate(R.joints[i]):
            x, y = J["head"]
            px, py = to_screen(sc, x, y + a.r_head, getattr(a, "z", 1.0), R.times[n])
            fx, fy = to_screen(sc, J["hip"][0], J["hip"][1], getattr(a, "z", 1.0), R.times[n])
            visible = -0.2 * sc.width < fx < 1.2 * sc.width
            if visible and (py < top * sc.height or py > (1 - bottom) * sc.height or px < side * sc.width
                            or px > (1 - side) * sc.width):
                out.append(("framing", a.look.name, R.times[n], 1.0))
    return _spans(out, 1 / R.fps)


# ---- the rendered file ----------------------------------------------------------------------------------------------
def check_video(path: Path, expected_seconds: float, fps: int) -> dict:
    """Frame count, frozen stretches, black frames and flicker of the rendered file."""
    from ..media.quality import blacks, freezes
    path = Path(path)
    n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    frames = int((n.stdout.strip() or "0").split(",")[0])
    luma = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=64:36,signalstats,metadata=print:key="
                           "lavfi.signalstats.YAVG:file=-", "-f", "null", "-"], capture_output=True, text=True).stdout
    ys = [float(line.split("=")[1]) for line in luma.splitlines() if "YAVG" in line]
    flicker = sum(1 for a, b, c in zip(ys, ys[1:], ys[2:]) if abs(b - a) > 12 and abs(c - b) > 12 and (b - a) * (c - b) < 0)
    expected = int(round(expected_seconds * fps))
    return dict(frames=frames, expected=expected, missing=max(0, expected - frames), frozen=freezes(path),
                black=blacks(path, expected_seconds), flicker_frames=flicker)


# ---- automatic corrections ------------------------------------------------------------------------------------------
def corrections(R: Recording, rep: Report) -> list:
    """What can be fixed without re-choreographing: two bodies passing through each other -> the one that is
    moving steps a little toward the camera while they pass (a depth dodge). Returns (actor name, t0, t1, dz)."""
    fixes = []
    names = [a.look.name for a in R.actors]
    for d in rep.defects:
        if d.kind != "overlap":
            continue
        a, b = d.who.split("+")
        i, j = names.index(a), names.index(b)
        n0 = min(range(len(R.times)), key=lambda n: abs(R.times[n] - d.t0))
        n1 = min(len(R.times) - 1, n0 + max(1, int(0.3 * R.fps)))
        speed = [abs(R.joints[k][n1]["hip"][0] - R.joints[k][n0]["hip"][0]) for k in (i, j)]
        mover = a if speed[0] >= speed[1] else b
        fixes.append((mover, d.t0 - 0.5, d.t1 + 0.5, -0.07))
    return fixes


def apply(sc, fixes: list):
    by = {a.look.name: a for a in sc.actors if isinstance(a, Actor)}
    for name, t0, t1, dz in fixes:
        if name in by:
            by[name].depth.append((t0, t1, dz))


# ---- the loop ---------------------------------------------------------------------------------------------------------
def refine(build, style: str = "explainer", tries: int = 3, focus=None):
    """build() -> (scene, seconds) must stage a fresh scene each call. Returns (scene ready to render, seconds,
    motion report after corrections, framing defects, camera passes used, the corrections applied)."""
    from . import camera
    sc, seconds = build()
    R = record(sc, seconds)
    report = inspect(R)
    fixes = corrections(R, report)
    if fixes:                                          # correct, then re-stage and re-inspect
        sc, seconds = build()
        apply(sc, fixes)
        R = record(sc, seconds)
        report = inspect(R)
    margin = 1.0
    frame_defects = []
    for k in range(tries):
        sc2, seconds = build()
        apply(sc2, fixes)
        sc2.cams = camera.direct(R, sc2, style=style, margin=margin)
        frame_defects = framing(sc2, R, focus)
        if not frame_defects:
            return sc2, seconds, report, frame_defects, k + 1, fixes
        margin *= 1.3                                  # widen the shots and try again
    return sc2, seconds, report, frame_defects, tries, fixes
