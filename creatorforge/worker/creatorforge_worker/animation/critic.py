"""The animation critic: reviews a recorded scene the way a supervising animator would, and says which notes it can
fix itself and which need a person.

    review(R, sc, plan=None, video=None) -> Review

Notes (each measured, with the time and the character):
    technical        everything qc.inspect finds (stretch, skid, floor, teleport, snap, jerk, frozen, overlap...)
    repetition       the same gesture or action used again and again by one character
    weak_pose        an emotional beat whose silhouette barely changes from standing neutral (it won't read)
    staging          two characters talking with their backs to each other; characters bunched on top of each other
    dead_air         nobody moving or speaking for too long
    reaction_timing  a reaction faster than a person can react (it looks mechanical)
    camera           panning faster than the eye can follow; zoom pumping in and out
    interpretation   an action the plan asked for that never happens on screen
    render           missing frames, frozen or black stretches, flicker in the finished file

Auto-fixable (applied by `revise`): characters talking back to back are turned to face each other, the camera is
re-directed with a calmer style, repeated gestures are varied. Everything about acting quality (weak poses, dead
air, interpretation) is flagged for review, with a suggestion - the critic does not pretend to judge appeal."""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, field

from . import qc


@dataclass
class Note:
    category: str
    severity: str            # "error" | "warn" | "info"
    t: float
    who: str
    detail: str
    suggestion: str = ""
    auto: bool = False       # can revise() fix it?


@dataclass
class Review:
    notes: list = field(default_factory=list)

    def counts(self) -> dict:
        return dict(Counter(n.category for n in self.notes))

    def for_review(self) -> list:
        return [n for n in self.notes if not n.auto]

    def to_dict(self) -> dict:
        return {"counts": self.counts(), "notes": [asdict(n) for n in self.notes]}


def _hull_area(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    h = lo[:-1] + hi[:-1]
    return abs(sum(h[i][0] * h[(i + 1) % len(h)][1] - h[(i + 1) % len(h)][0] * h[i][1] for i in range(len(h)))) / 2


def _silhouette(J):
    pts = [J["head"], J["neck"], J["hip"]] + [w[2] for w in J["arms"]] + [w[1] for w in J["arms"]] + \
          [l_[2] for l_ in J["legs"]] + [l_[1] for l_ in J["legs"]]
    return _hull_area([(round(x, 3), round(y, 3)) for x, y in pts])


def review(R, sc, plan=None, video: dict | None = None) -> Review:
    rv = Review()
    rep = qc.inspect(R)
    for d in rep.defects:
        rv.notes.append(Note("technical", "error", d.t0, d.who, f"{d.kind} (worst {d.worst})",
                             "fixed by the QC loop" if d.kind == "overlap" else "fix the choreography at this time",
                             d.kind == "overlap"))
    names = [a.look.name for a in R.actors]
    T = R.times[-1] if R.times else 0.0
    for i, a in enumerate(R.actors):
        # repetition: the same gesture more than twice in 20 s
        g = Counter(n for g0, g1, n in a.loco.gestures if n not in ("carry", "talk"))
        for name, c in g.items():
            if c > 2:
                rv.notes.append(Note("repetition", "warn", 0.0, a.look.name, f"gesture '{name}' used {c} times",
                                     "vary it (performance.perform never repeats back to back)", True))
        acts = Counter(x.name for x in a.acts)
        for name, c in acts.items():
            if c > 3 and name not in ("throw", "catch", "pick_up"):
                rv.notes.append(Note("repetition", "info", 0.0, a.look.name, f"action '{name}' {c} times",
                                     "intentional for a running gag? otherwise vary it"))
        # weak poses during emotional beats
        neutral = _silhouette(R.joints[i][0])
        for f0, f1, emo in a.feels:
            if emo in ("happy", "curious", "confident"):
                continue
            n = min(len(R.times) - 1, int((f0 + min(0.8, (f1 - f0) / 2)) * R.fps))
            if R.acting[i][n]:
                continue
            area = _silhouette(R.joints[i][n])
            if neutral and area < neutral * 1.15:
                rv.notes.append(Note("weak_pose", "warn", f0, a.look.name, f"'{emo}' reads weakly (silhouette "
                                     f"{area / neutral:.2f}x neutral)", "push the pose: raise exaggeration, add a "
                                     "gesture, or frame closer"))
        # reaction timing
        for l0, l1, target in a.looks:
            pass
    # staging: talking back to back; bunching
    for i, a in enumerate(R.actors):
        for t0, t1, text in a.bubbles:
            n = min(len(R.times) - 1, int((t0 + 0.3) * R.fps))
            others = [j for j in range(len(R.actors)) if j != i and abs(R.joints[j][n]["hip"][0] - R.joints[i][n]["hip"][0]) < 4]
            if not others:
                continue
            j = min(others, key=lambda j: abs(R.joints[j][n]["hip"][0] - R.joints[i][n]["hip"][0]))
            dx = R.joints[j][n]["hip"][0] - R.joints[i][n]["hip"][0]
            fa = R.joints[i][n].get("f", 1.0)
            if dx * fa < 0:
                rv.notes.append(Note("staging", "warn", t0, a.look.name, f"speaks with their back to {names[j]}",
                                     "turn to face the listener", True))
    for n in range(0, len(R.times), max(1, R.fps // 2)):
        xs = sorted((R.joints[i][n]["hip"][0], names[i]) for i in range(len(R.actors)))
        for (x0, a0), (x1, a1) in zip(xs, xs[1:]):
            if x1 - x0 < 0.35 and not any(R.acting[k][n] for k in range(len(R.actors))):
                rv.notes.append(Note("staging", "info", R.times[n], f"{a0}+{a1}", "standing on top of each other",
                                     "space them at least half a metre apart"))
                break
    # dead air: nobody moves more than 2 cm and nobody speaks for 2.5 s
    win = int(2.5 * R.fps)
    voice = [(t0, t0 + 3.0) for t0, _ in getattr(sc, "narration", [])]     # voice-over counts as sound
    voice = [(a_, a_ + d) for a_, d in ((t0, getattr(sc, "voiced", {}).get(round(t0 - 0.15, 3), 3.0))
                                        for t0, _ in getattr(sc, "narration", []))] or voice
    speaking = [any(t0 <= t <= t1 for a in R.actors for t0, t1, _ in a.bubbles) or
                any(v0 <= t <= v1 for v0, v1 in voice) for t in R.times]
    n = win
    while n < len(R.times):
        quiet = not any(speaking[n - win:n + 1])
        still = all(max(math.dist(R.joints[i][k]["hip"], R.joints[i][n - win]["hip"]) for k in range(n - win, n + 1, 5))
                    < 0.02 and not any(R.acting[i][n - win:n + 1]) for i in range(len(R.actors)))
        if quiet and still:
            rv.notes.append(Note("dead_air", "warn", R.times[n - win], "", "2.5 s with nobody moving or speaking",
                                 "cut it shorter, or give someone a reaction"))
            n += win
        else:
            n += R.fps // 2
    # camera: pan speed and zoom pumping
    cams = sorted(getattr(sc, "cams", []), key=lambda k: k.t)
    width = sc.width / sc.ppm
    zdir = []
    for a_, b_ in zip(cams, cams[1:]):
        dt_ = max(1e-3, b_.t - a_.t)
        if dt_ > 0.05:
            pan = abs(b_.x - a_.x) / dt_ / (width / max(a_.zoom, 1.0))
            if pan > 1.2:
                rv.notes.append(Note("camera", "warn", a_.t, "", f"pans {pan:.1f} frame widths a second",
                                     "slow it down or cut", True))
            if abs(b_.zoom - a_.zoom) > 0.02:
                zdir.append((a_.t, 1 if b_.zoom > a_.zoom else -1))
    flips = [t for (t, d), (_, e) in zip(zdir, zdir[1:]) if d != e]
    for k in range(len(flips) - 2):
        if flips[k + 2] - flips[k] < 4.0:
            rv.notes.append(Note("camera", "warn", flips[k], "", "zoom pumping in and out", "hold the shot size", True))
            break
    # interpretation: planned actions that never appear
    if plan is not None:
        for b in plan.beats:
            t0 = b.narration_window[0] - plan.beats[0].narration_window[0]
            t1 = b.narration_window[1] - plan.beats[0].narration_window[0]
            for act in b.actions:
                a = next((x for x in R.actors if x.look.name == act["who"]), None)
                if a is None:
                    continue
                seen = any(t0 - 0.5 <= x.t0 <= t1 + 1.0 for x in a.acts) or \
                    any(t0 - 0.5 <= g0 <= t1 + 1.0 for g0, _, _ in a.loco.gestures) or \
                    any(t0 - 0.5 <= m[0] <= t1 + 1.0 for m in a.loco.moves) or \
                    any(t0 - 0.5 <= f0 <= t1 + 1.0 for f0, _, _ in a.bubbles)
                if not seen and act["verb"] not in ("price_up", "equal_fall"):
                    rv.notes.append(Note("interpretation", "warn", t0, act["who"], f"'{act['verb']}' planned but not "
                                         f"shown during: {b.narration[:60]}", "check the beat's staging"))
    if video:
        if video.get("missing"):
            rv.notes.append(Note("render", "error", 0.0, "", f"{video['missing']} frames missing", "re-render"))
        for a_, b_ in video.get("frozen", []):
            rv.notes.append(Note("render", "warn", a_, "", f"frozen picture {a_:.1f}-{b_:.1f} s", "check the scene"))
        for a_, b_ in video.get("black", []):
            rv.notes.append(Note("render", "error", a_, "", f"black {a_:.1f}-{b_:.1f} s", "re-render"))
        if video.get("flicker_frames"):
            rv.notes.append(Note("render", "warn", 0.0, "", f"{video['flicker_frames']} flicker frames", "check"))
    return rv


def revise(sc, R, rv: Review, style: str = "explainer") -> list[str]:
    """Applies the notes that can be fixed reliably. Returns what was done (the caller re-stages and re-reviews)."""
    from . import camera
    done = []
    by = {a.look.name: a for a in R.actors}
    for n in rv.notes:
        if not n.auto:
            continue
        if n.category == "staging" and n.who in by:
            a = by[n.who]
            f = a._facing_at_build(n.t)
            a.turn(max(0.0, n.t - 0.35), -f)
            done.append(f"{n.who} turns to face the listener at {n.t:.1f} s")
        elif n.category == "camera":
            calmer = {"action": "comedy", "comedy": "explainer", "explainer": "drama"}.get(style, "drama")
            sc.cams = camera.direct(R, sc, style=calmer)
            done.append(f"camera re-directed in a calmer style ({calmer})")
            style = calmer
    return done
