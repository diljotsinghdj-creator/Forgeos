"""Animals with their own gaits. The camel paces (both legs on one side move together, as camels really walk), with
the same planted-foot rule as people: a hoof stays where it touched the ground until the body has passed over it."""
from __future__ import annotations

import math

from .rig2d import _ik, _trapezoid, smooth


class Camel:
    def __init__(self, x: float = 0.0, z: float = 1.0, facing: float = 1.0, color=(196, 150, 96), seed: int = 3):
        self.x, self.z, self.facing, self.color, self.seed = x, z, facing, color, seed
        self.moves: list[tuple] = []
        self._end_x = x
        self.l_up, self.l_low = 0.62, 0.66
        self.leg_y = 1.33
        # hooves: front-near, front-far, hind-near, hind-far (pace pairs: near legs together, far legs together)
        self._hooves = [[x + 0.55, 0.0, None], [x + 0.62, 0.0, None], [x - 0.6, 0.0, None], [x - 0.53, 0.0, None]]
        self._sx = {0: 0.55, 1: 0.62, 2: -0.6, 3: -0.53}
        self.f = facing

    def walk(self, t: float, to_x: float, speed: float = 1.1) -> float:
        dur = abs(to_x - self._end_x) / speed + 0.6
        self.moves.append((t, t + dur, self._end_x, to_x))
        self._end_x = to_x
        return t + dur

    def body_x(self, t: float) -> float:
        x = self.x
        for t0, t1, x0, x1 in self.moves:
            if t >= t0:
                x = _trapezoid(t, t0, t1, x0, x1)
        return x

    def step(self, t: float, dt: float):
        bx = self.body_x(t)
        v = (self.body_x(t + 0.02) - self.body_x(t - 0.02)) / 0.04
        if abs(v) > 0.05:
            self.f = 1.0 if v > 0 else -1.0
        f = self.f
        S = 0.95
        pairs = ((0, 2), (1, 3))
        for h in self._hooves:
            if h[2]:
                t0, dur, xa, xb = h[2]
                k = (t - t0) / dur
                if k >= 1:
                    h[0], h[1], h[2] = xb, 0.0, None
                else:
                    h[0] = xa + (xb - xa) * smooth(k)
                    h[1] = 0.16 * math.sin(math.pi * k)
        if abs(v) > 0.05:
            for pi, (a, b) in enumerate(pairs):
                other = pairs[1 - pi]
                if self._hooves[a][2] or any(self._hooves[o][2] for o in other):
                    continue
                home = bx + f * self._sx[a]
                if f * (home - self._hooves[a][0]) > 0.5 * S:
                    dur = max(0.3, min(0.6, 0.85 * S / max(abs(v), 0.3)))
                    nb = self.body_x(t + dur)
                    for leg in (a, b):
                        self._hooves[leg][2] = (t, dur, self._hooves[leg][0], nb + f * self._sx[leg] + f * 0.45 * S)
                    break
        self.bx = bx
        self.speed = abs(v)
        self._t = t

    def draw(self, d, to_screen, scale: float, t: float, ink=(70, 45, 25)):
        f, bx, S = self.f, self.bx, to_screen
        bob = 0.03 * math.sin(t * 2 * math.pi * 1.6) * min(1.0, self.speed)
        body_y = self.leg_y + 0.25 + bob
        col = self.color
        dark = tuple(int(c * 0.78) for c in col)
        lw = max(2, int(scale * 0.03))

        def leg(i, shade):
            hx = bx + f * self._sx[i] * 0.92
            top = (hx, self.leg_y + bob)
            hoof = (self._hooves[i][0], self._hooves[i][1] + 0.05)
            front = i in (0, 1)
            knee = _ik(top, hoof, self.l_up, self.l_low, -f if front else f)
            pts = [S(*top), S(*knee), S(*hoof)]
            w = int(scale * 0.15)
            d.line(pts, fill=shade, width=w, joint="curve")
            hx2, hy2 = S(*hoof)
            d.ellipse([hx2 - w * 0.7, hy2 - w * 0.4, hx2 + w * 0.7, hy2 + w * 0.35], fill=dark)
            kx, ky = S(*knee)
            d.ellipse([kx - w * 0.6, ky - w * 0.6, kx + w * 0.6, ky + w * 0.6], fill=shade)
        leg(1, dark)
        leg(3, dark)
        # tail
        tail_base = (bx - f * 0.85, body_y + 0.15)
        sw = 0.12 * math.sin(t * 2.3 + self.seed)
        d.line([S(*tail_base), S(bx - f * (1.0 + sw * 0.3), body_y - 0.35)], fill=dark, width=lw * 2)
        # body with hump
        pts = []
        for k in range(41):
            a = math.pi * 2 * k / 40
            x = math.cos(a) * 0.95
            y = math.sin(a) * 0.42
            if y > 0:
                y += 0.38 * math.exp(-((x + 0.05 * f) ** 2) / 0.12)          # the hump
            pts.append(S(bx + f * x, body_y + y))
        d.polygon(pts, fill=col, outline=ink)
        # neck and head
        nb = (bx + f * 0.75, body_y + 0.1)
        bend = 0.05 * math.sin(t * 2 * math.pi * 0.8 + 1)
        nm = (bx + f * 1.25, body_y + 0.15 + bend)
        hd = (bx + f * 1.45, body_y + 0.85 + bend)
        neck = [S(nb[0], nb[1] + 0.25), S(nm[0] + f * 0.12, nm[1] + 0.1), S(hd[0] + f * 0.05, hd[1]),
                S(hd[0] - f * 0.12, hd[1] - 0.05), S(nm[0] - f * 0.1, nm[1] - 0.12), S(nb[0], nb[1] - 0.25)]
        d.polygon(neck, fill=col, outline=ink)
        head = [S(hd[0] - f * 0.15, hd[1] + 0.12), S(hd[0] + f * 0.3, hd[1] + 0.06), S(hd[0] + f * 0.45, hd[1] - 0.08),
                S(hd[0] + f * 0.4, hd[1] - 0.16), S(hd[0] - f * 0.1, hd[1] - 0.14)]
        d.polygon(head, fill=col, outline=ink)
        ex, ey = S(hd[0] + f * 0.08, hd[1] + 0.03)
        er = scale * 0.035
        blink = (t + self.seed) % 3.7 < 0.15
        if blink:
            d.line([(ex - er, ey), (ex + er, ey)], fill=(30, 20, 15), width=max(1, lw // 2))
        else:
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(30, 20, 15))
        ear = S(hd[0] - f * 0.12, hd[1] + 0.2)
        d.ellipse([ear[0] - er * 1.4, ear[1] - er * 2, ear[0] + er * 1.4, ear[1] + er * 0.5], fill=dark)
        leg(0, col)
        leg(2, col)
        # saddle blanket
        sx, sy = S(bx, body_y + 0.45)
        w = scale * 0.42
        d.rounded_rectangle([sx - w, sy - scale * 0.1, sx + w, sy + scale * 0.32], radius=scale * 0.06,
                            fill=(170, 40, 50), outline=(110, 25, 30))
        d.line([(sx - w, sy + scale * 0.18), (sx + w, sy + scale * 0.18)], fill=(235, 190, 70), width=lw)


class Bird:
    """A small bird flapping across the sky (wing beats, a gentle bob)."""

    def __init__(self, x: float, y: float, vx: float = 1.6, seed: int = 0):
        self.x0, self.y, self.vx, self.seed = x, y, vx, seed

    def draw(self, d, to_screen, scale, t, ink=(40, 35, 45)):
        x = self.x0 + self.vx * t
        y = self.y + 0.15 * math.sin(t * 2 + self.seed)
        flap = math.sin(t * 2 * math.pi * 3.2 + self.seed)
        cx, cy = to_screen(x, y)
        s = scale * 0.18
        d.line([(cx - s, cy - s * 0.6 * flap), (cx, cy), (cx + s, cy - s * 0.6 * flap)], fill=ink,
               width=max(2, int(s * 0.18)), joint="curve")
