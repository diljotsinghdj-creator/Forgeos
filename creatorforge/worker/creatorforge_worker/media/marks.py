"""Hand-drawn explainer marks, written as ASS vector drawings so libass renders them with the captions (no extra
video pass): a red pen circle / box / underline / arrow / cross / tick that draws itself on stroke by stroke with a
slight wobble, and speech or thought bubbles that pop in and type their words. Placed around where the explainer
layouts put the picture (centre of the frame, a little high)."""
from __future__ import annotations

import math
import random

PEN = "&H002B26D6"          # red pen (BGR of #D6262B)
INK = "&H00141414"
WHITE = "&H00FFFFFF"
KINDS = ("circle", "box", "underline", "arrow", "cross", "tick")
STEP = 1 / 12               # pen strokes advance at 12 frames a second - the hand-made stutter of explainer graphics


def _ts(t: float) -> str:
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def subject_box(w: int, h: int) -> tuple[float, float, float, float]:
    """(x0, y0, x1, y1) of the picture area the layouts use: 84% wide 4:5 on tall frames, 4:3 on wide ones."""
    if h > w:
        pw = w * 0.84
        ph = pw * 1.25
    else:
        ph = h * 0.74
        pw = ph * 4 / 3
    cx, cy = w / 2, h / 2 - h * 0.03
    return cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2


def _stroke(points: list[tuple[float, float]]) -> str:
    """An open pen line as an ASS drawing: out along the points and straight back (a zero-area shape whose outline
    is the stroke)."""
    path = points + points[-2::-1]
    head = f"m {path[0][0]:.0f} {path[0][1]:.0f} l "
    return head + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:])


def _wobble(points, rng: random.Random, amount: float) -> list[tuple[float, float]]:
    return [(x + rng.uniform(-amount, amount), y + rng.uniform(-amount, amount)) for x, y in points]


def _line(a, b, n: int = 8):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def _paths(kind: str, w: int, h: int, rng: random.Random, under_y: float | None) -> list[list[tuple[float, float]]]:
    """The pen strokes for one mark, in drawing order (each a list of points)."""
    x0, y0, x1, y1 = subject_box(w, h)
    cx, cy, bw, bh = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    wob = min(w, h) * 0.004
    if kind == "circle":
        rx, ry = bw * 0.40, bh * 0.36
        start = rng.uniform(-2.4, -1.8)
        pts = [(cx + rx * (1 + 0.03 * math.sin(3 * a)) * math.cos(start + a),
                cy + ry * (1 + 0.04 * math.cos(2 * a)) * math.sin(start + a)) for a in
               (i * 2 * math.pi * 1.12 / 40 for i in range(41))]          # a little over one turn, like a real pen
        pts = _wobble(pts, rng, wob)
        return [pts[i:i + 6] for i in range(0, 40, 5)]
    if kind == "box":
        m = min(w, h) * 0.02
        c = [(x0 - m, y0 - m), (x1 + m, y0 - m * 0.6), (x1 + m * 0.8, y1 + m), (x0 - m * 0.7, y1 + m * 0.8), (x0 - m, y0 - m * 1.4)]
        return [_wobble(_line(c[i], c[i + 1]), rng, wob) for i in range(4)]
    if kind == "underline":
        y = under_y if under_y is not None else y1 - bh * 0.06
        pts = _wobble(_line((cx - bw * 0.32, y), (cx + bw * 0.34, y + h * 0.004), 12), rng, wob)
        return [pts[i:i + 4] for i in range(0, 12, 3)]
    if kind == "arrow":
        tip = (cx - bw * 0.18, cy + bh * 0.12)
        tail = (max(w * 0.04, x0 - bw * 0.02), min(h * 0.9, y1 + bh * 0.1)) if h > w else (x0 - bw * 0.25, y1)
        shaft = _wobble(_line(tail, tip, 10), rng, wob)
        ang = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
        size = min(w, h) * 0.07
        heads = [[tip, (tip[0] - size * math.cos(ang - s), tip[1] - size * math.sin(ang - s))] for s in (0.5, -0.5)]
        return [shaft[i:i + 4] for i in range(0, 10, 3)] + [_wobble(_line(a, b, 3), rng, wob) for a, b in heads]
    if kind == "cross":
        s = min(bw, bh) * 0.34
        return [_wobble(_line((cx - s, cy - s), (cx + s, cy + s), 6), rng, wob),
                _wobble(_line((cx + s, cy - s), (cx - s, cy + s), 6), rng, wob)]
    if kind == "tick":
        s = min(bw, bh) * 0.28
        return [_wobble(_line((cx - s, cy), (cx - s * 0.3, cy + s * 0.7), 4), rng, wob),
                _wobble(_line((cx - s * 0.3, cy + s * 0.7), (cx + s, cy - s * 0.8), 6), rng, wob)]
    return []


def mark_events(spec: str, start: float, end: float, w: int, h: int, color: str = PEN,
                under_y: float | None = None) -> list[str]:
    """ASS Dialogue lines for 'circle', 'arrow', 'box, arrow' ...: each stroke appears in turn (~0.4 s per mark,
    stepped like hand animation) and stays until `end`."""
    out = []
    rng = random.Random(f"{spec}|{start:.2f}")
    width = max(4, int(min(w, h) * 0.0065))
    t = start
    for kind in [k.strip().lower() for k in spec.replace("+", ",").split(",") if k.strip().lower() in KINDS][:3]:
        strokes = _paths(kind, w, h, rng, under_y)
        per = max(STEP, round(0.42 / max(1, len(strokes)) / STEP) * STEP)
        for path in strokes:
            if t >= end - 0.1:
                break
            fx = f"{{\\an7\\pos(0,0)\\p1\\bord{width}\\shad0\\1a&HFF&\\3c{color}&\\blur0.6}}"
            out.append(f"Dialogue: 3,{_ts(t)},{_ts(end)},Mark,,0,0,0,,{fx}{_stroke(path)}")
            t += per
        t += STEP * 2
    return out


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> str:
    k = 0.5523
    return (f"m {cx - rx:.0f} {cy:.0f} b {cx - rx:.0f} {cy - ry * k:.0f} {cx - rx * k:.0f} {cy - ry:.0f} {cx:.0f} {cy - ry:.0f} "
            f"b {cx + rx * k:.0f} {cy - ry:.0f} {cx + rx:.0f} {cy - ry * k:.0f} {cx + rx:.0f} {cy:.0f} "
            f"b {cx + rx:.0f} {cy + ry * k:.0f} {cx + rx * k:.0f} {cy + ry:.0f} {cx:.0f} {cy + ry:.0f} "
            f"b {cx - rx * k:.0f} {cy + ry:.0f} {cx - rx:.0f} {cy + ry * k:.0f} {cx - rx:.0f} {cy:.0f}")


def _wrap(text: str, per: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > per:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines[:4]


def bubble_events(text: str, start: float, end: float, w: int, h: int, think: bool = False,
                  font: str = "DejaVu Sans") -> list[str]:
    """A speech bubble (or a thought cloud) above the picture that pops in, then types its words one by one."""
    from .captions import _esc
    x0, y0, x1, y1 = subject_box(w, h)
    size = int(min(w, h) * (0.052 if h > w else 0.05))
    lines = _wrap(text.strip(), 16 if h > w else 22)
    if not lines:
        return []
    tw = max(len(s) for s in lines) * size * 0.62
    th = len(lines) * size * 1.25
    bw, bh = tw + size * 1.6, th + size * 1.2
    cx = min(max((x0 + x1) / 2 + (x1 - x0) * 0.12, bw / 2 + w * 0.04), w - bw / 2 - w * 0.04)
    cy = max(y0 + bh * 0.2, bh / 2 + h * 0.13)          # high on the picture, below the callout area
    org = f"\\org({cx:.0f},{cy:.0f})"
    pop = f"\\fscx55\\fscy55\\t(0,140,\\fscx104\\fscy104)\\t(140,200,\\fscx100\\fscy100)"
    if think:
        blobs = [_ellipse(cx + dx * bw, cy + dy * bh, bw * rx, bh * ry) for dx, dy, rx, ry in
                 ((-0.28, 0.05, 0.30, 0.42), (0.0, -0.18, 0.34, 0.40), (0.28, 0.02, 0.30, 0.42), (0.02, 0.2, 0.38, 0.34))]
        trail = [_ellipse(cx - bw * 0.25 + i * bw * 0.04, cy + bh * (0.62 + i * 0.28), size * (0.32 - i * 0.1),
                          size * (0.32 - i * 0.1)) for i in range(2)]
        shape = " ".join(blobs + trail)
    else:
        r = size * 0.6
        L, T, R, B = cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2
        shape = (f"m {L + r:.0f} {T:.0f} l {R - r:.0f} {T:.0f} b {R:.0f} {T:.0f} {R:.0f} {T:.0f} {R:.0f} {T + r:.0f} "
                 f"l {R:.0f} {B - r:.0f} b {R:.0f} {B:.0f} {R:.0f} {B:.0f} {R - r:.0f} {B:.0f} "
                 f"l {cx - bw * 0.05:.0f} {B:.0f} l {cx - bw * 0.22:.0f} {B + size * 0.9:.0f} l {cx - bw * 0.2:.0f} {B:.0f} "
                 f"l {L + r:.0f} {B:.0f} b {L:.0f} {B:.0f} {L:.0f} {B:.0f} {L:.0f} {B - r:.0f} "
                 f"l {L:.0f} {T + r:.0f} b {L:.0f} {T:.0f} {L:.0f} {T:.0f} {L + r:.0f} {T:.0f}")
    bord = max(3, int(size * 0.09))
    out = [  # outline layer, then a white fill on top that hides the inner overlaps of the cloud's circles
        f"Dialogue: 4,{_ts(start)},{_ts(end)},Mark,,0,0,0,,{{\\an7\\pos(0,0){org}{pop}\\p1\\bord{bord}\\shad0"
        f"\\1c{WHITE}&\\3c{INK}&}}{shape}",
        f"Dialogue: 5,{_ts(start)},{_ts(end)},Mark,,0,0,0,,{{\\an7\\pos(0,0){org}{pop}\\p1\\bord0\\shad0"
        f"\\1c{WHITE}&}}{shape}",
    ]
    words = " ".join(lines).split()
    per = max(6, int(min(0.16, max(0.06, (end - start - 0.5) * 0.5 / max(1, len(words)))) * 100))
    typed, n = [], 0
    for li, line in enumerate(lines):
        for word in line.split():
            typed.append(f"{{\\k{per if n else 22}}}{_esc(word)} ")
            n += 1
        if li < len(lines) - 1:
            typed.append("\\N")
    out.append(f"Dialogue: 6,{_ts(start + 0.05)},{_ts(end)},BubbleText,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f})"
               f"\\fn{font}\\fs{size}}}{''.join(typed).strip()}")
    return out


def place_events(text: str, start: float, end: float, w: int, h: int, font: str = "DejaVu Sans",
                 pin: str = PEN) -> list[str]:
    """A documentary location stamp, lower left: a red map pin drops in, then 'PARIS · 1925' types out on a white
    label (karaoke timing: the letters appear one by one)."""
    from .captions import _esc
    size = int(min(w, h) * (0.05 if w > h else 0.04))
    x, y = w * 0.06, h * (0.62 if h > w else 0.80)
    r = size * 0.45
    pin_shape = (f"m {x:.0f} {y + r * 1.9:.0f} l {x - r * 0.9:.0f} {y + r * 0.2:.0f} b {x - r * 1.4:.0f} {y - r * 1.2:.0f} "
                 f"{x + r * 1.4:.0f} {y - r * 1.2:.0f} {x + r * 0.9:.0f} {y + r * 0.2:.0f} l {x:.0f} {y + r * 1.9:.0f}")
    letters = list(text.strip().upper())
    per = max(3, int(min(6.0, 70 / max(1, len(letters)))))
    typed = "".join(f"{{\\k{per}}}{_esc(ch) if ch != ' ' else ' '}" for ch in letters)
    return [f"Dialogue: 6,{_ts(start)},{_ts(end)},Mark,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(2, size // 12)}\\shad0"
            f"\\1c{pin}&\\3c&HFFFFFF&\\fad(80,200)\\org({x:.0f},{y + r * 1.9:.0f})\\fscy30\\t(0,150,\\fscy110)"
            f"\\t(150,220,\\fscy100)}}{pin_shape}",
            f"Dialogue: 6,{_ts(start + 0.15)},{_ts(end)},BubbleText,,0,0,0,,{{\\an4\\pos({x + r * 1.8:.0f},{y + r * 0.2:.0f})"
            f"\\fn{font}\\fs{size}\\bord{max(6, size // 4)}\\3c&HFFFFFF&\\4c&HFFFFFF&\\fad(0,200)}}{typed}"]


def cite_events(text: str, start: float, end: float, w: int, h: int, font: str = "DejaVu Sans") -> list[str]:
    """The small on-screen source credit explainers carry: 'SOURCE: FTC, 2025' in the bottom-left corner."""
    from .captions import _esc
    size = max(18, int(min(w, h) * (0.028 if w > h else 0.022)))
    label = text.strip()
    if not label.lower().startswith(("source", "sources", "data")):
        label = f"Source: {label}"
    return [f"Dialogue: 6,{_ts(start)},{_ts(end)},Mark,,0,0,0,,{{\\an1\\pos({w * 0.035:.0f},{h * 0.975:.0f})\\fn{font}"
            f"\\fs{size}\\1c&H00222222&\\1a&H30&\\bord{max(3, size // 5)}\\3c&H00F2ECDF&\\3a&H40&\\fad(200,200)}}"
            f"{_esc(label.upper())}"]
