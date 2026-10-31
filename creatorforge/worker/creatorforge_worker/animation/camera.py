"""A camera director for the 2D stage. From a recorded performance (qc.record) it decides, moment by moment:

* who matters - characters doing something (an action > moving > feeling) and props in flight or in hand;
* the shot size - wide with lead room for action, full figure for walking and staging, medium (closer, from the
  hips up) for emotional beats with one or two people;
* where to point - the subject box centred, with room ahead of a moving subject (lead room), heads kept in the
  safe area and the ground line kept in frame when it can be;
* how to move - a critically damped follow (no overshoot) whose stiffness depends on the style (action reacts
  quickly, drama drifts), a pan-speed limit, a dead zone so small shifts don't move the camera, and a cut instead
  of a whip pan when the subject jumps across the stage. In a side-on 2D stage the screen direction never flips.

Returns CamKeys (linear between dense keys) for Scene.cams."""
from __future__ import annotations

import math

from .scene2d import CamKey
from .stick import Actor

STYLE = {                      # spring frequency (1/s), max pan (frame widths / s), activity weights
    "action": dict(omega=4.5, pan=1.2, wide=1.5),
    "comedy": dict(omega=3.0, pan=0.8, wide=1.2),
    "explainer": dict(omega=2.2, pan=0.6, wide=1.1),
    "satire": dict(omega=2.2, pan=0.6, wide=1.1),
    "drama": dict(omega=1.4, pan=0.4, wide=1.0),
}
BIG = ("jump", "climb", "trip_roll", "knockback", "kick", "throw", "pain_hop", "crawl")


def _activity(R, i, n, win):
    """How much character i is doing around frame n."""
    lo, hi = max(0, n - win), min(len(R.times) - 1, n + win)
    act = any(R.acting[i][k] for k in (lo, n, hi))
    big = any(R.acting[i][k] in BIG for k in (lo, n, hi))
    J0, J1 = R.joints[i][lo], R.joints[i][hi]
    move = abs(J1["hip"][0] - J0["hip"][0]) / max(1e-6, R.times[hi] - R.times[lo])
    feel = R.feeling[i][n]
    return (3.0 if big else 2.0 if act else 0.0) + min(2.0, move) + (1.2 if feel else 0.0), move, big, feel


def direct(R, sc, style: str = "explainer", margin: float = 1.0, every: int = 2) -> list:
    """sc.focus (optional): [(t0, t1, [names])] - who the narration is about at each moment; they are always
    framed (with whoever they are dealing with), however busy anyone else is. sc.show (optional):
    [(t0, t1, x0, x1, y0, y1)] - world boxes (a diagram, a document) that must be in the shot while shown."""
    S = STYLE.get(style, STYLE["explainer"])
    hints = getattr(sc, "focus", None) or []
    W_m, H_m = sc.width / sc.ppm, sc.height / sc.ppm
    ground_y = (sc.ground - 0.5) * H_m           # world y of the screen centre at cy=0, zoom 1 (relative)
    win = int(0.6 * R.fps)
    targets = []
    for n, t in enumerate(R.times):
        acts = [(_activity(R, i, n, win), i) for i, a in enumerate(R.actors) if getattr(a, "z", 1.0) == 1.0]
        named_now = next((names for h0, h1, names in hints if h0 <= t <= h1), None) or []
        beasts = []                                       # creatures that move, act or are named: subjects too
        for k, p in enumerate(R.prop_objs):
            if not (getattr(p, "data", {}) or {}).get("creature") or getattr(p, "z", 1.0) != 1.0:
                continue
            x, y, _ = R.props[k][n]
            px_, py_, _ = R.props[k][max(0, n - win)]
            nx_, ny_, _ = R.props[k][min(len(R.times) - 1, n + win)]
            moving = math.dist((px_, py_), (nx_, ny_)) > 0.15
            acting = any(a0 <= t <= a1 for a0, a1, _ in p.data.get("acts", []))
            if moving or acting or any(getattr(p, "name", "").startswith(nm) for nm in named_now):
                beasts.append((x, y, p))
        if not acts:
            if beasts:                                    # a creature-only shot: frame the creatures
                xs = [b[0] - b[2].w / 2 for b in beasts] + [b[0] + b[2].w / 2 for b in beasts]
                ys = [b[1] for b in beasts] + [b[1] + b[2].h for b in beasts]
                bw, bh = max(xs) - min(xs) + 2.0 * margin, max(ys) - min(ys) + 1.0 * margin
                zoom = max(1.0, min(1.9, W_m / bw, H_m / bh))
                hh = H_m / (2 * zoom)
                yc = max(max(ys) + 0.4 * margin - hh, min(min(ys) - 0.25 + hh, 0.0 - 0.3 + hh))
                targets.append(((min(xs) + max(xs)) / 2, yc - ground_y, zoom))
            else:
                targets.append((0.0, 0.0, 1.0))
            continue
        talking = [i for _, i in acts if any(b0 - 0.6 <= t <= b1 + 0.3 for b0, b1, _ in
                                             getattr(R.actors[i], "bubbles", []))]
        if talking:                                       # a conversation: the speaker and whoever they talk to
            sx = [R.joints[i][n]["hip"][0] for i in talking]
            acts = [((s_[0] + (2.5 if i in talking else 2.0 if min(abs(R.joints[i][n]["hip"][0] - x) for x in sx)
                                < 4.0 else 0.0),) + s_[1:], i) for s_, i in acts]
        named = next((names for h0, h1, names in hints if h0 <= t <= h1), None)
        if named:                                         # the narration's subject leads the frame...
            lead = [i for _, i in acts if any(R.actors[i].look.name.startswith(nm) for nm in named)]
            lx = [R.joints[i][n]["hip"][0] for i in lead]

            def boost(i):
                if i in lead:
                    return 6.0
                near = lx and min(abs(R.joints[i][n]["hip"][0] - x) for x in lx) < 4.0
                return 6.0 if near else 0.0               # ...with whoever they are dealing with (a two-shot)
            acts = [((s[0] + boost(i),) + s[1:], i) for s, i in acts]
        top = max(s[0] for s, _ in acts)
        focus = [(s, i) for s, i in acts if s[0] >= max(0.5, 0.45 * top)] or [max(acts)]
        fx_ = [R.joints[i][n]["hip"][0] for _, i in focus]
        focus += [(s, i) for s, i in acts if (s, i) not in focus and                 # someone right beside the
                  min(abs(R.joints[i][n]["hip"][0] - x) for x in fx_) < 2.6]    # subject is in the shot, not half cut
        xs, ys, lead = [], [], 0.0
        any_big = any(s[2] for s, _ in focus)
        moving = [s[1] for s, _ in focus]
        feeling = any(s[3] for s, _ in focus) and not any_big and max(moving) < 0.3
        for s, i in focus:
            J = R.joints[i][n]
            pts = [J["head"], J["hip"]] + [l[2] for l in J["legs"]] + [w[2] for w in J["arms"]]
            xs += [p[0] for p in pts]
            ys += [p[1] for p in pts] + [J["head"][1] + R.actors[i].r_head]
            if s[1] > 0.3:                                # room ahead of a moving subject
                nxt = R.joints[i][min(len(R.times) - 1, n + win)]["hip"][0]
                lead += math.copysign(min(1.2, 0.5 * s[1]), nxt - J["hip"][0]) / len(focus)
        for k, p in enumerate(R.prop_objs):              # a thrown or carried prop is part of the action
            x, y, _ = R.props[k][n]
            near = any(abs(x - R.joints[i][n]["hip"][0]) < 3.0 for _, i in focus)
            prev = R.props[k][max(0, n - 3)]
            if near and math.dist((x, y), prev[:2]) > 0.02:
                xs.append(x)
                ys.append(y + getattr(p, "h", 0.2))
        for x, y, p in beasts:                            # a creature in the action joins the shot - if the
            nx = xs + [x - p.w / 2, x + p.w / 2]          # shot can hold it without losing the people
            ny = ys + [y, y + p.h]
            if max(nx) - min(nx) + 1.8 * margin <= W_m * 0.98 and max(ny) - min(ny) + 0.9 * margin <= H_m * 0.98:
                xs, ys = nx, ny
                feeling = False
        for r0, r1, bx0, bx1, by0, by1 in getattr(sc, "show", []):   # a visual on screen: frame it with the cast
            if r0 <= t <= r1:
                xs += [bx0, bx1]
                ys += [by0, by1]
                feeling = False
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if feeling and len(focus) <= 2:                   # medium shot: hips up
            pad_x, pad_top, pad_bot = 0.6 * margin, 0.35 * margin, -0.15
            y0 = min(J["hip"][1] for J in (R.joints[i][n] for _, i in focus)) - 0.25
        elif any_big:                                     # wide: the whole move and where it goes
            pad_x, pad_top, pad_bot = S["wide"] * margin, 0.6 * margin, 0.25
        else:
            pad_x, pad_top, pad_bot = 0.9 * margin, 0.45 * margin, 0.2
        bw = (x1 - x0) + 2 * pad_x + abs(lead)
        bh = (y1 - y0) + pad_top + pad_bot
        zoom = max(1.0, min(1.65 if feeling else 1.9, min(W_m / bw, H_m / bh)))
        cx = (x0 + x1) / 2 + lead / 2
        hh = H_m / (2 * zoom)
        lo, hi = y0 - pad_bot, y1 + pad_top
        if hi - lo > 2 * hh:                              # can't fit it all: the heads matter most
            yc = hi - hh
        elif feeling and len(focus) <= 2:
            yc = (lo + hi) / 2
        else:                                             # the floor near the bottom of the frame, not a slab
            floor = min(R.actors[i]._floor(R.joints[i][n]["hip"][0]) for _, i in focus)
            yc = max(hi - hh, min(lo + hh, floor - 0.3 + hh))
        cy = yc - ground_y                                # Scene.cy: metres the view is raised
        targets.append((cx, cy, zoom))
    # follow: dead zone, critically damped spring, pan limit, cuts for big jumps
    keys = []
    x, y, z = targets[0]
    vx = vy = vz = 0.0
    dt = 1 / R.fps
    w = S["omega"]
    still = 0.0
    for n, (tx, ty, tz) in enumerate(targets):
        half = W_m / (2 * z)
        if n and math.dist(targets[n][:2], targets[n - 1][:2]) < 0.01 and abs(vx) < 0.05:
            still += dt                                   # a held shot: creep in slowly so the picture lives
        else:
            still = 0.0
        if still > 1.2:
            tz = min(1.9, tz * (1.0 + min(0.09, 0.018 * (still - 1.2))))
        if abs(tx - x) > 1.6 * half:                     # the subject is somewhere else entirely: cut
            x, y, z, vx, vy, vz = tx, ty, tz, 0.0, 0.0, 0.0
            keys.append(CamKey(max(0.0, R.times[n] - 1e-3), keys[-1].x if keys else x,
                               keys[-1].y if keys else y, keys[-1].zoom if keys else z, ease="linear"))
            keys.append(CamKey(R.times[n], x, y, z, ease="linear"))
            continue
        if abs(tx - x) < 0.12 * half:                    # dead zone: hold still for small shifts
            tx = x
        for val, tgt, vel, name in ((x, tx, vx, "x"), (y, ty, vy, "y"), (z, tz, vz, "z")):
            a = w * w * (tgt - val) - 2 * w * vel
            vel += a * dt
            if name == "x":
                vel = max(-S["pan"] * 2 * half, min(S["pan"] * 2 * half, vel))
                vx, x = vel, val + vel * dt
            elif name == "y":
                vy, y = vel, val + vel * dt
            else:
                vz, z = vel, max(1.0, min(1.9, val + vel * dt))
        if n % every == 0:
            keys.append(CamKey(R.times[n], x, y, z, ease="linear"))
    return keys
