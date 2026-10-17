"""Full-frame explainer cards on paper, drawn with ASS over FFmpeg:

    Chapter: Part 1 | The subscription trap     a chapter title card - a highlighter kicker, a big title, a pen underline
    Quote: Move your money to a safe account | Lloyds Bank, 2026
                                                 a document with the quote typed out and a highlighter sweeping across it
    Steps: Free trial → Card saved → Auto-renew → Forgotten
                                                 how the trap works: cards appear one by one, arrows draw between them,
                                                 the last step lands in the highlight colour
    Timeline: 1890 Born → 1925 Sells the tower → 1947 Dies in prison | Lustig's life
                                                 a line draws across, each date drops in with its label; the last lands
                                                 in the highlight colour
    Icons: 3 of 4 | people | used a possible dark pattern
                                                 a grid of icons pops in one by one, then the counted ones fill in
                                                 (icons: people, coins, homes, phones, cards, locks, letters)
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import ff

PAPER = {"editorial": "0xF2ECDF", "investigative": "0xE9E0CC"}
MARK = {"editorial": "&H002BD6F7", "investigative": "&H00414BD2"}   # yellow highlighter / red-orange marker
PEN = {"editorial": "&H002B26D6", "investigative": "&H002E10C8"}
INK = "&H00141414"


def _ts(t: float) -> str:
    return f"0:{int(t // 60):02d}:{t % 60:05.2f}"


def _wrap(text: str, per: int, most: int) -> list[str]:
    out, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > per:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out[:most]


def _esc(t: str) -> str:
    return t.replace("\\", "").replace("{", "(").replace("}", ")")


def _head(width: int, height: int, font: str) -> list[str]:
    return ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "WrapStyle: 2", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
            "MarginR, MarginV, Encoding",
            f"Style: T,{font},40,{INK},{INK},{INK},&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
            f"Style: Q,DejaVu Serif,40,{INK},&HFF141414,{INK},&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]


def _font() -> str:
    from .captions import EXPLAINER_FONT, _have_font
    return EXPLAINER_FONT if _have_font(EXPLAINER_FONT) else "DejaVu Sans"


def chapter_lines(spec: str, theme: str, width: int, height: int, seconds: float) -> list[str]:
    kicker, _, title = spec.partition("|")
    if not title.strip():
        kicker, title = "", kicker
    end = _ts(seconds)
    tall = height > width
    big = int(min(width, height) * (0.095 if tall else 0.085))
    rows = _wrap(title.strip().upper(), 12 if tall else 18, 3)
    out = []
    cy = height * 0.45
    if kicker.strip():
        out.append(f"Dialogue: 2,{_ts(0.05)},{end},T,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{cy - big * (len(rows) * 0.62 + 0.9):.0f})"
                   f"\\fs{int(big * 0.42)}\\bord{int(big * 0.14)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fad(150,0)"
                   f"\\fscx15\\t(0,220,\\fscx100)}}{_esc(kicker.strip().upper())}")
    for i, row in enumerate(rows):
        y = cy + (i - (len(rows) - 1) / 2) * big * 1.12
        out.append(f"Dialogue: 3,{_ts(0.2 + i * 0.12)},{end},T,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{y + big * 0.25:.0f})"
                   f"\\move({width / 2:.0f},{y + big * 0.25:.0f},{width / 2:.0f},{y:.0f},0,220)\\fs{big}\\fad(180,0)}}"
                   f"{_esc(row)}")
    # a pen underline drawn under the title, left to right
    uy = cy + (len(rows) - 1) / 2 * big * 1.12 + big * 0.85      # just under the last title line
    x0, x1 = width * (0.22 if not tall else 0.15), width * (0.78 if not tall else 0.85)
    pts = [(x0 + (x1 - x0) * k / 10, uy + (3 if k % 2 else -3)) for k in range(11)]
    path = pts + pts[-2::-1]
    shape = f"m {path[0][0]:.0f} {path[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:])
    out.append(f"Dialogue: 4,{_ts(0.55)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{x0:.0f},{height})"
               f"\\t(0,350,\\clip(0,0,{x1 + 10:.0f},{height}))\\p1\\bord{max(4, int(big * 0.07))}\\1a&HFF&"
               f"\\3c{PEN[theme]}&\\blur0.6}}{shape}")
    return out


def quote_lines(spec: str, theme: str, width: int, height: int, seconds: float) -> list[str]:
    quote, _, source = spec.partition("|")
    quote = quote.strip().strip('"“”')
    end = _ts(seconds)
    tall = height > width
    size = int(min(width, height) * (0.058 if tall else 0.068))
    rows = _wrap(f"“{quote}”", 22 if tall else 30, 5)
    cw = min(width * 0.86, max(len(r) for r in rows) * size * 0.56 + size * 2.4)
    ch = len(rows) * size * 1.45 + size * (3.2 if source.strip() else 2.2)
    cx, cy = width / 2, height * (0.44 if tall else 0.48)
    L, T = cx - cw / 2, cy - ch / 2
    card = f"m {L:.0f} {T:.0f} l {L + cw:.0f} {T:.0f} l {L + cw:.0f} {T + ch:.0f} l {L:.0f} {T + ch:.0f}"
    sh = f"m {L + 14:.0f} {T + 18:.0f} l {L + cw + 14:.0f} {T + 18:.0f} l {L + cw + 14:.0f} {T + ch + 18:.0f} l {L + 14:.0f} {T + ch + 18:.0f}"
    out = [f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HB0&\\blur12}}{sh}",
           f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFAFCFD&}}{card}"]
    x = L + size * 1.2
    # each line is typed, then a highlighter sweeps across it (behind the ink)
    per_row = min(0.9, max(0.35, (seconds - 1.2) / max(1, len(rows)) * 0.8))
    for i, row in enumerate(rows):
        y = T + size * 1.1 + i * size * 1.45
        t0 = 0.3 + i * per_row
        words = row.split()
        per = max(4, int(per_row * 70 / max(1, len(words))))
        typed = " ".join(f"{{\\k{per}}}{_esc(w)}" for w in words)
        out.append(f"Dialogue: 4,{_ts(t0)},{end},Q,,0,0,0,,{{\\an7\\pos({x:.0f},{y:.0f})\\fs{size}}}{typed}")
        rw = len(row) * size * 0.5
        hl = f"m {x - 6:.0f} {y + size * 0.05:.0f} l {x + rw + 6:.0f} {y + size * 0.05:.0f} l {x + rw + 6:.0f} {y + size * 1.2:.0f} l {x - 6:.0f} {y + size * 1.2:.0f}"
        out.append(f"Dialogue: 3,{_ts(t0 + per_row * 0.6)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{x - 6:.0f},{height})"
                   f"\\t(0,{int(per_row * 600)},\\clip(0,0,{x + rw + 8:.0f},{height}))\\p1\\bord0\\shad0\\1c{MARK[theme]}&"
                   f"\\1a&H30&}}{hl}")
    if source.strip():
        out.append(f"Dialogue: 4,{_ts(0.4)},{end},T,,0,0,0,,{{\\an1\\pos({x:.0f},{T + ch - size * 0.7:.0f})\\fs{int(size * 0.55)}"
                   f"\\fad(200,0)}}— {_esc(source.strip().upper())}")
    return out


def steps_lines(spec: str, theme: str, width: int, height: int, seconds: float) -> list[str]:
    head, _, title = spec.partition("|")
    steps = [x.strip() for x in head.replace("->", "→").split("→") if x.strip()][:5]
    if len(steps) < 2:
        return []
    end = _ts(seconds)
    tall = height > width
    n = len(steps)
    size = int(min(width, height) * (0.05 if tall else 0.052))
    if tall:
        # Shorts captions sit at ~66-70% of the height: the whole diagram fits between the title and 62%.
        bw, bh = width * 0.72, size * 2.2
        top, bottom = height * 0.15 + bh / 2, height * 0.62 - bh / 2
        gap = min((bottom - top) / max(1, n - 1), bh * 1.9)
        mid = (top + bottom) / 2
        centres = [(width / 2, mid - gap * (n - 1) / 2 + i * gap) for i in range(n)]
    else:
        gap = width * 0.86 / n
        bw, bh = gap * 0.78, size * 3.2
        centres = [(width * 0.07 + gap * (i + 0.5), height * 0.5) for i in range(n)]
    per = min(0.6, max(0.3, (seconds - 0.8) / n))
    out = []
    if title.strip():
        out.append(f"Dialogue: 6,{_ts(0.1)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * (0.08 if tall else 0.12):.0f})"
                   f"\\fs{int(size * (1.15 if tall else 0.9))}\\bord{int(size * 0.3)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fad(150,0)}}"
                   f"{_esc(title.strip().upper())}")
    for i, ((cx, cy), text) in enumerate(zip(centres, steps)):
        t0 = 0.25 + i * per
        last = i == n - 1
        L, T, R, B = cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2
        box = f"m {L:.0f} {T:.0f} l {R:.0f} {T:.0f} l {R:.0f} {B:.0f} l {L:.0f} {B:.0f}"
        fill = MARK[theme] if last else "&H00FAFCFD&"
        pop = f"\\org({cx:.0f},{cy:.0f})\\fscx70\\fscy70\\t(0,140,\\fscx104\\fscy104)\\t(140,200,\\fscx100\\fscy100)"
        out.append(f"Dialogue: 2,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0){pop}\\p1\\bord{max(3, size // 12)}\\shad0"
                   f"\\1c{fill.rstrip('&')}&\\3c{INK}&}}{box}")
        rows = _wrap(text.upper(), 14 if tall else max(8, int(bw / (size * 0.62))), 2)
        out.append(f"Dialogue: 3,{_ts(t0 + 0.08)},{end},T,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f})\\fs{size}\\fad(100,0)}}"
                   + "\\N".join(_esc(r) for r in rows))
        out.append(f"Dialogue: 3,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos({L + 8:.0f},{T - size * 0.95:.0f})\\fs{int(size * 0.7)}"
                   f"\\fad(100,0)}}{i + 1}")
        if i < n - 1:
            (nx, ny) = centres[i + 1]
            if tall:
                a, b = (cx, B + 6), (nx, ny - bh / 2 - 6)
            else:
                a, b = (R + 6, cy), (nx - bw / 2 - 6, ny)
            shaft = f"m {a[0]:.0f} {a[1]:.0f} l {b[0]:.0f} {b[1]:.0f} l {a[0]:.0f} {a[1]:.0f}"
            hs = size * 0.45
            head_ = (f"m {b[0] - hs:.0f} {b[1] - hs:.0f} l {b[0]:.0f} {b[1]:.0f} l {b[0] - hs:.0f} {b[1] + hs:.0f} "
                     f"l {b[0]:.0f} {b[1]:.0f}") if not tall else \
                    (f"m {b[0] - hs:.0f} {b[1] - hs:.0f} l {b[0]:.0f} {b[1]:.0f} l {b[0] + hs:.0f} {b[1] - hs:.0f} "
                     f"l {b[0]:.0f} {b[1]:.0f}")
            clip = (f"\\clip(0,0,{a[0]:.0f},{height})\\t(0,{int(per * 500)},\\clip(0,0,{b[0] + hs:.0f},{height}))" if not tall
                    else f"\\clip(0,0,{width},{a[1]:.0f})\\t(0,{int(per * 500)},\\clip(0,0,{width},{b[1] + 4:.0f}))")
            out.append(f"Dialogue: 1,{_ts(t0 + per * 0.45)},{end},T,,0,0,0,,{{\\an7\\pos(0,0){clip}\\p1\\bord{max(3, size // 10)}"
                       f"\\1a&HFF&\\3c{PEN[theme]}&}}{shaft} {head_}")
    return out


def timeline_lines(spec: str, theme: str, width: int, height: int, seconds: float) -> list[str]:
    head, _, title = spec.partition("|")
    items = []
    for part in [x.strip() for x in re.split(r"→|->|;", head) if x.strip()][:6]:
        m = re.match(r"^((?:c\.\s*)?\d{3,4}s?|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{4})\s*[:,-]?\s*(.*)$", part)
        items.append((m.group(1), m.group(2)) if m else ("", part))
    if len(items) < 2:
        return []
    end = _ts(seconds)
    tall = height > width
    n = len(items)
    size = int(min(width, height) * (0.05 if tall else 0.056))
    per = min(0.7, max(0.3, (seconds - 1.0) / n))
    out = []
    if title.strip():
        out.append(f"Dialogue: 6,{_ts(0.1)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * (0.08 if tall else 0.1):.0f})"
                   f"\\fs{int(size * 1.2)}\\bord{int(size * 0.3)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fad(150,0)}}"
                   f"{_esc(title.strip().upper())}")
    lw = max(4, size // 7)
    if tall:   # a vertical line down the left, dates and labels to its right; ends above the captions
        x = width * 0.2
        top, bottom = height * 0.17, height * 0.62
        ys = [top + (bottom - top) * i / max(1, n - 1) for i in range(n)]
        line = f"m {x - lw / 2:.0f} {top:.0f} l {x + lw / 2:.0f} {top:.0f} l {x + lw / 2:.0f} {bottom:.0f} l {x - lw / 2:.0f} {bottom:.0f}"
        grow = f"\\clip(0,0,{width},{top:.0f})\\t(150,{int((0.15 + per * n) * 1000)},\\clip(0,0,{width},{bottom + 4:.0f}))"
    else:      # a horizontal line across the middle, dates above, labels below
        y = height * 0.5
        left, right = width * 0.1, width * 0.9
        xs = [left + (right - left) * (i + 0.5) / n for i in range(n)]
        line = f"m {left:.0f} {y - lw / 2:.0f} l {right:.0f} {y - lw / 2:.0f} l {right:.0f} {y + lw / 2:.0f} l {left:.0f} {y + lw / 2:.0f}"
        grow = f"\\clip(0,0,{left:.0f},{height})\\t(150,{int((0.15 + per * n) * 1000)},\\clip(0,0,{right + 4:.0f},{height}))"
    out.append(f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0){grow}\\p1\\bord0\\shad0\\1c{INK}&}}{line}")
    for i, (date, label) in enumerate(items):
        t0 = 0.25 + i * per
        last = i == n - 1
        px, py = (x, ys[i]) if tall else (xs[i], y)
        r = size * 0.42
        dot = (f"m {px - r:.0f} {py:.0f} b {px - r:.0f} {py - r * 1.33:.0f} {px + r:.0f} {py - r * 1.33:.0f} {px + r:.0f} {py:.0f} "
               f"b {px + r:.0f} {py + r * 1.33:.0f} {px - r:.0f} {py + r * 1.33:.0f} {px - r:.0f} {py:.0f}")
        pop = f"\\org({px:.0f},{py:.0f})\\fscx40\\fscy40\\t(0,140,\\fscx115\\fscy115)\\t(140,220,\\fscx100\\fscy100)"
        fill = MARK[theme] if last else "&H00FAFCFD&"
        out.append(f"Dialogue: 3,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0){pop}\\p1\\bord{max(3, lw - 1)}\\shad0"
                   f"\\1c{fill.rstrip('&')}&\\3c{INK}&}}{dot}")
        box = f"\\bord{int(size * 0.28)}\\3c{MARK[theme]}&" if last else "\\bord0"
        rows = _wrap(label.upper(), 18 if tall else max(8, int((right - left) / n / (size * 0.6))), 2)
        if tall:
            out.append(f"Dialogue: 4,{_ts(t0 + 0.05)},{end},T,,0,0,0,,{{\\an4\\pos({px + size * 1.1:.0f},{py - size * 0.55:.0f})"
                       f"\\fs{int(size * 1.1)}{box}\\fad(100,0)}}{_esc(date)}")
            if rows:
                out.append(f"Dialogue: 4,{_ts(t0 + 0.12)},{end},T,,0,0,0,,{{\\an7\\pos({px + size * 1.1:.0f},{py + size * 0.25:.0f})"
                           f"\\fs{int(size * 0.85)}\\fad(120,0)}}" + "\\N".join(_esc(r_) for r_ in rows))
        else:
            out.append(f"Dialogue: 4,{_ts(t0 + 0.05)},{end},T,,0,0,0,,{{\\an2\\pos({px:.0f},{py - size * 0.9:.0f})"
                       f"\\fs{int(size * 1.1)}{box}\\fad(100,0)}}{_esc(date)}")
            if rows:
                out.append(f"Dialogue: 4,{_ts(t0 + 0.12)},{end},T,,0,0,0,,{{\\an8\\pos({px:.0f},{py + size * 0.9:.0f})"
                           f"\\fs{int(size * 0.72)}\\fad(120,0)}}" + "\\N".join(_esc(r_) for r_ in rows))
    return out


def _icon(kind: str, cx: float, cy: float, s: float) -> str:
    """One icon as an ASS drawing, about s pixels tall, centred on (cx, cy)."""
    def circle(x, y, r):
        k = r * 1.33
        return (f"m {x - r:.0f} {y:.0f} b {x - r:.0f} {y - k:.0f} {x + r:.0f} {y - k:.0f} {x + r:.0f} {y:.0f} "
                f"b {x + r:.0f} {y + k:.0f} {x - r:.0f} {y + k:.0f} {x - r:.0f} {y:.0f}")

    def rect(x0, y0, x1, y1):
        return f"m {x0:.0f} {y0:.0f} l {x1:.0f} {y0:.0f} l {x1:.0f} {y1:.0f} l {x0:.0f} {y1:.0f}"
    h = s / 2
    if kind == "coin":
        return circle(cx, cy, h * 0.9)
    if kind == "home":
        return (f"m {cx:.0f} {cy - h:.0f} l {cx + h:.0f} {cy - h * 0.1:.0f} l {cx + h * 0.72:.0f} {cy - h * 0.1:.0f} "
                f"l {cx + h * 0.72:.0f} {cy + h:.0f} l {cx - h * 0.72:.0f} {cy + h:.0f} l {cx - h * 0.72:.0f} {cy - h * 0.1:.0f} "
                f"l {cx - h:.0f} {cy - h * 0.1:.0f}")
    if kind == "phone":
        return rect(cx - h * 0.5, cy - h, cx + h * 0.5, cy + h)
    if kind == "card":
        return rect(cx - h, cy - h * 0.62, cx + h, cy + h * 0.62)
    if kind == "letter":
        return (rect(cx - h, cy - h * 0.66, cx + h, cy + h * 0.66))
    if kind == "lock":
        return (rect(cx - h * 0.7, cy - h * 0.1, cx + h * 0.7, cy + h) + " " +
                f"m {cx - h * 0.5:.0f} {cy - h * 0.1:.0f} l {cx - h * 0.5:.0f} {cy - h * 0.55:.0f} "
                f"b {cx - h * 0.5:.0f} {cy - h * 1.15:.0f} {cx + h * 0.5:.0f} {cy - h * 1.15:.0f} {cx + h * 0.5:.0f} {cy - h * 0.55:.0f} "
                f"l {cx + h * 0.5:.0f} {cy - h * 0.1:.0f} l {cx + h * 0.28:.0f} {cy - h * 0.1:.0f} l {cx + h * 0.28:.0f} {cy - h * 0.55:.0f} "
                f"b {cx + h * 0.28:.0f} {cy - h * 0.85:.0f} {cx - h * 0.28:.0f} {cy - h * 0.85:.0f} {cx - h * 0.28:.0f} {cy - h * 0.55:.0f} "
                f"l {cx - h * 0.28:.0f} {cy - h * 0.1:.0f}")
    # a person: a head and rounded shoulders
    return (circle(cx, cy - h * 0.55, h * 0.36) + " " +
            f"m {cx - h * 0.72:.0f} {cy + h:.0f} l {cx - h * 0.72:.0f} {cy + h * 0.25:.0f} "
            f"b {cx - h * 0.72:.0f} {cy - h * 0.12:.0f} {cx + h * 0.72:.0f} {cy - h * 0.12:.0f} {cx + h * 0.72:.0f} {cy + h * 0.25:.0f} "
            f"l {cx + h * 0.72:.0f} {cy + h:.0f}")


_ICON_WORDS = {"coin": "coin|money|pound|dollar|cash|penny", "home": "home|house|household|famil",
               "phone": "phone|app|mobile|screen|site|website", "card": "card|account|payment|subscri",
               "lock": "lock|secur|password|safe", "letter": "letter|email|mail|message|text"}


def icons_lines(spec: str, theme: str, width: int, height: int, seconds: float) -> list[str]:
    parts = [x.strip() for x in spec.split("|")]
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(?:of|in|out of|/)\s*(\d+)$", parts[0], re.I) or \
        re.match(r"^(\d+(?:\.\d+)?)\s*(%)$", parts[0])
    if not m:
        return []
    if m.group(2) == "%":
        k, n = round(float(m.group(1)) / 10), 10
    else:
        k, n = round(float(m.group(1))), int(m.group(2))
        if n > 100:
            k, n = round(k * 100 / n), 100
    if not (1 <= n <= 100 and 0 <= k <= n):
        return []
    noun = parts[1] if len(parts) > 1 else "people"
    label = parts[2] if len(parts) > 2 else ""
    kind = next((key for key, pat in _ICON_WORDS.items() if re.search(pat, noun, re.I)), "person")
    end = _ts(seconds)
    tall = height > width
    cols = n if n <= 5 else (5 if n <= 10 and tall else 10 if n > 10 else n)
    if n > 10 and tall:
        cols = 10 if n > 50 else 5
    rows = -(-n // cols)
    area_w = width * (0.84 if tall else 0.86)
    area_top, area_bottom = (height * 0.2, height * 0.56) if tall else (height * 0.22, height * 0.7)
    cell = min(area_w / cols, (area_bottom - area_top) / rows)
    s = cell * 0.78
    x0 = width / 2 - cell * cols / 2
    y0 = (area_top + area_bottom) / 2 - cell * rows / 2
    size = int(min(width, height) * (0.05 if tall else 0.045))
    appear = min(1.2, max(0.4, seconds * 0.35))
    out = []
    big = f"{m.group(1)}{'%' if m.group(2) == '%' else ' IN ' + m.group(2)}"
    out.append(f"Dialogue: 6,{_ts(0.1)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * (0.07 if tall else 0.06):.0f})"
               f"\\fs{int(size * 1.6)}\\bord{int(size * 0.35)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fad(150,0)}}{_esc(big.upper())}")
    for i in range(n):
        r_, c_ = divmod(i, cols)
        cx, cy = x0 + cell * (c_ + 0.5), y0 + cell * (r_ + 0.5)
        t0 = 0.2 + appear * i / max(1, n)
        pop = f"\\org({cx:.0f},{cy:.0f})\\fscx30\\fscy30\\t(0,120,\\fscx110\\fscy110)\\t(120,180,\\fscx100\\fscy100)"
        lit = i < k
        fill = (f"\\1c&H00C9C4BC&\\t({int((0.35 + appear + 0.05 * i / max(1, k)) * 1000 - t0 * 1000)},"
                f"{int((0.55 + appear + 0.05 * i / max(1, k)) * 1000 - t0 * 1000)},\\1c{MARK[theme]}&)") if lit else "\\1c&H00C9C4BC&"
        out.append(f"Dialogue: 2,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0){pop}\\p1\\bord{max(2, int(s / 22))}\\shad0"
                   f"\\3c{INK}&{fill}}}{_icon(kind, cx, cy, s)}")
    if label:
        rows_ = _wrap(label.upper(), 20 if tall else 34, 2)
        out.append(f"Dialogue: 6,{_ts(0.5 + appear)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{y0 + cell * rows + size * 0.6:.0f})"
                   f"\\fs{size}\\fad(150,0)}}" + "\\N".join(_esc(x) for x in rows_))
    return out


def _rect(L: float, T: float, R: float, B: float, r: float = 0.0) -> str:
    if r <= 0:
        return f"m {L:.0f} {T:.0f} l {R:.0f} {T:.0f} l {R:.0f} {B:.0f} l {L:.0f} {B:.0f}"
    return (f"m {L + r:.0f} {T:.0f} l {R - r:.0f} {T:.0f} b {R:.0f} {T:.0f} {R:.0f} {T:.0f} {R:.0f} {T + r:.0f} "
            f"l {R:.0f} {B - r:.0f} b {R:.0f} {B:.0f} {R:.0f} {B:.0f} {R - r:.0f} {B:.0f} "
            f"l {L + r:.0f} {B:.0f} b {L:.0f} {B:.0f} {L:.0f} {B:.0f} {L:.0f} {B - r:.0f} "
            f"l {L:.0f} {T + r:.0f} b {L:.0f} {T:.0f} {L:.0f} {T:.0f} {L + r:.0f} {T:.0f}")


def _ring(cx: float, cy: float, rx: float, ry: float) -> str:
    """A hand-drawn pen loop around a point (slightly more than one turn, a little wobbly)."""
    import math
    pts = []
    for k in range(0, 41):
        a = -math.pi * 0.6 + k / 40 * math.pi * 2.15
        wob = 1 + 0.04 * math.sin(k * 1.7)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    path = pts + pts[-2::-1]
    return f"m {path[0][0]:.0f} {path[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:])


def screen_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A recreated app/web page (always fictional and labelled): rows appear, the camera pushes in on the starred
    row, and a red pen circles it. "Screen: Your plan | Premium £12.99 · Keep my plan · *small:Cancel" """
    title, _, body = spec.partition("|")
    if not body.strip():
        title, body = "", title
    rows = [x.strip() for x in re.split(r"·|•|;", body) if x.strip()][:7]
    if not rows:
        return []
    tall = height > width
    end = _ts(seconds)
    if tall:   # a phone, ending above the captions
        fw, fh = width * 0.56, height * 0.5
        L, T = width / 2 - fw / 2, height * 0.12
        pad = fw * 0.07
        size = int(fw * 0.062)
    else:      # a browser window
        fw, fh = width * 0.58, height * 0.8
        L, T = width / 2 - fw / 2, height * 0.08
        pad = fw * 0.05
        size = int(fh * 0.068)              # readable on a TV: widescreen screens use bigger type
    R, B = L + fw, T + fh
    out = [f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HB8&\\blur14}}"
           f"{_rect(L + 14, T + 20, R + 14, B + 20, size * 0.8)}",
           f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(6, int(size * 0.35)) if tall else 2}\\shad0"
           f"\\1c&HFFFFFF&\\3c&H202020&}}{_rect(L, T, R, B, size * (1.2 if tall else 0.4))}"]
    y = T + pad * (1.6 if tall else 0.5)
    if not tall:   # browser chrome: three dots and an address bar
        bar = size * 1.5
        out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HEDEAE6&}}"
                   f"{_rect(L + 2, T + 2, R - 2, T + bar)}")
        for i, c in enumerate(("&H5F5FEC&", "&H2EBDF5&", "&H5BC95B&")):
            cx = L + size * (0.9 + i * 0.75)
            out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{c}}}"
                       f"{_rect(cx - size * 0.22, T + bar / 2 - size * 0.22, cx + size * 0.22, T + bar / 2 + size * 0.22, size * 0.22)}")
        out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFFFFFF&}}"
                   f"{_rect(L + size * 3.2, T + bar * 0.2, R - size * 1.5, T + bar * 0.8, bar * 0.3)}")
        out.append(f"Dialogue: 5,{_ts(0)},{end},T,,0,0,0,,{{\\an4\\pos({L + size * 3.6:.0f},{T + bar / 2:.0f})\\fs{int(size * 0.55)}"
                   f"\\1c&H808080&}}example-app.com")
        y = T + bar + pad
    if title.strip():
        out.append(f"Dialogue: 5,{_ts(0.1)},{end},T,,0,0,0,,{{\\an7\\pos({L + pad:.0f},{y:.0f})\\fs{int(size * 1.15)}\\fad(120,0)}}"
                   f"{_esc(title.strip())}")
        y += size * 2.2
    target = None
    room = (B - pad) - y
    step = min(size * 2.3, room / max(1, len(rows)))
    per = min(0.35, max(0.12, seconds * 0.3 / len(rows)))
    primary = True
    for i, row in enumerate(rows):
        star = row.startswith("*")
        text = row.lstrip("*").strip()
        small = text.lower().startswith("small:")
        text = text.split(":", 1)[1].strip() if small else text
        t0 = 0.2 + i * per
        cy = y + step * 0.5
        if small:   # the trick: tiny grey words, no button
            fs = int(size * 0.62)
            out.append(f"Dialogue: 6,{_ts(t0)},{end},T,,0,0,0,,{{\\an5\\pos({(L + R) / 2:.0f},{cy:.0f})\\fs{fs}\\1c&H9A9A9A&"
                       f"\\fad(100,0)}}{_esc(text)}")
            box = (len(text) * fs * 0.56 / 2 + fs * 0.6, fs * 0.9)
        else:
            col = MARK[theme] if primary else "&H00EFEFEF&"
            primary = False
            bh = min(step * 0.78, size * 1.9)
            out.append(f"Dialogue: 5,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{col}\\fad(100,0)}}"
                       f"{_rect(L + pad, cy - bh / 2, R - pad, cy + bh / 2, bh * 0.3)}")
            out.append(f"Dialogue: 6,{_ts(t0)},{end},T,,0,0,0,,{{\\an5\\pos({(L + R) / 2:.0f},{cy:.0f})\\fs{int(size * 0.85)}"
                       f"\\fad(100,0)}}{_esc(text)}")
            box = ((R - L) / 2 - pad, bh * 0.5)
        if star:
            target = ((L + R) / 2, cy, box)
        y += step
    out.append(f"Dialogue: 7,{_ts(0)},{end},T,,0,0,0,,{{\\an9\\pos({R - pad * 0.4:.0f},{B + size * 0.4:.0f})\\fs{int(size * 0.5)}"
               f"\\1c&H606060&}}ILLUSTRATION")
    zoom = None
    if target:
        cx, cy, (rx, ry) = target
        t_zoom = min(0.25 + len(rows) * per + 0.25, seconds * 0.45)
        t_ring = t_zoom + 0.7
        out.append(f"Dialogue: 8,{_ts(t_ring)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{cx - rx * 1.4:.0f},{height})"
                   f"\\t(0,350,\\clip(0,0,{cx + rx * 1.4:.0f},{height}))\\p1\\bord{max(4, int(size * 0.16))}\\1a&HFF&"
                   f"\\3c{PEN[theme]}&\\blur0.6}}{_ring(cx, cy, rx * 1.06, ry * 1.5)}")
        zoom = (cx, cy, 2.2 if tall else 1.45, t_zoom)
    return out, {"zoom": zoom}


def document_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A page of a real document (its other lines blurred to grey bars): the camera pushes in on the quoted
    sentence, typed in, and a highlighter sweeps across it. "Document: the exact words | source, year" """
    quote, _, source = spec.partition("|")
    quote = quote.strip().strip('"“”')
    if not quote:
        return []
    tall = height > width
    end = _ts(seconds)
    pw, ph = (width * 0.84, height * 0.5) if tall else (width * 0.5, height * 0.86)
    L, T = width / 2 - pw / 2, height * (0.12 if tall else 0.07)
    R, B = L + pw, T + ph
    size = int(pw * 0.034)
    out = [f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HB0&\\blur14}}"
           f"{_rect(L + 12, T + 18, R + 12, B + 18)}",
           f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFAFCFD&}}{_rect(L, T, R, B)}"]
    m = pw * 0.09
    gap = size * 1.75
    rows = _wrap(f"“{quote}”", 34, 4)
    n_lines = int((ph - m * 2) / gap)
    at = max(3, n_lines // 2 - len(rows) // 2)
    import random
    rnd = random.Random(quote)
    out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HB9B9B9&}}"
               f"{_rect(L + m, T + m, L + m + pw * 0.45, T + m + size * 1.2)}")
    qy = []
    for k in range(2, n_lines):
        y = T + m + k * gap
        if at <= k < at + len(rows):
            qy.append(y)
            continue
        if k == n_lines - 1 and source.strip():
            continue
        w = (pw - 2 * m) * (0.55 + 0.45 * rnd.random() if k % 5 else 0.4)
        out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HD5D5D5&\\blur1.5}}"
                   f"{_rect(L + m, y + size * 0.25, L + m + w, y + size * 0.85)}")
    t_zoom, per_row = 0.35, min(0.8, max(0.3, (seconds - 1.4) / max(1, len(rows)) * 0.7))
    for i, (row, y) in enumerate(zip(rows, qy)):
        t0 = t_zoom + 0.5 + i * per_row
        words = row.split()
        per = max(4, int(per_row * 70 / max(1, len(words))))
        out.append(f"Dialogue: 5,{_ts(t0)},{end},Q,,0,0,0,,{{\\an7\\pos({L + m:.0f},{y:.0f})\\fs{size}}}"
                   + " ".join(f"{{\\k{per}}}{_esc(w)}" for w in words))
        rw = min(pw - 2 * m, len(row) * size * 0.5)
        out.append(f"Dialogue: 4,{_ts(t0 + per_row * 0.6)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{L + m - 4:.0f},{height})"
                   f"\\t(0,{int(per_row * 600)},\\clip(0,0,{L + m + rw + 6:.0f},{height}))\\p1\\bord0\\shad0\\1c{MARK[theme]}&"
                   f"\\1a&H30&}}{_rect(L + m - 4, y + size * 0.05, L + m + rw + 6, y + size * 1.2)}")
    if source.strip():
        out.append(f"Dialogue: 5,{_ts(0.2)},{end},T,,0,0,0,,{{\\an1\\pos({L + m:.0f},{B - m * 0.6:.0f})\\fs{int(size * 0.8)}}}"
                   f"— {_esc(source.strip().upper())}")
    if not qy:
        return []
    cy = (qy[0] + qy[-1]) / 2 + size * 0.6
    return out, {"zoom": (L + m + min(pw - 2 * m, max(len(r) for r in rows) * size * 0.5) / 2, cy,
                          min(2.2, (width * 0.8) / min(pw - 2 * m, max(len(r) for r in rows) * size * 0.5 + size)), t_zoom)}


def statement_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """One big line on a dark screen, word by word - the pause before (or after) the reveal. *Word* = highlighted."""
    text = spec.strip()
    if not text:
        return []
    tall = height > width
    end = _ts(seconds)
    big = int(min(width, height) * (0.105 if tall else 0.09))
    rows = _wrap(text.upper(), 11 if tall else 20, 4)
    cy = height * (0.38 if tall else 0.48)
    out = []
    words_seen = 0
    total_words = max(1, len(text.split()))
    per = min(0.35, max(0.12, (seconds * 0.45) / total_words))
    for i, row in enumerate(rows):
        y = cy + (i - (len(rows) - 1) / 2) * big * 1.15
        parts = []
        for w in row.split():
            hi = w.startswith("*") or w.endswith("*")
            w = w.strip("*")
            t = int((0.15 + words_seen * per) * 1000)
            col = MARK[theme] if hi else "&H00F4F4F4&"
            parts.append(f"{{\\alpha&HFF&\\1c{col}\\t({t},{t + 120},\\alpha&H00&)}}{_esc(w)}")
            words_seen += 1
        out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{y:.0f})\\fs{big}\\bord0\\shad0}}"
                   + " ".join(parts))
    return out, {"bg": "0x111111", "plain": True}


def article_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """The source on screen, the way Johnny Harris flashes the article he is quoting: a plain page with the
    publisher's name as text (never its logo), the real headline, blurred body text; the camera pushes in and a
    highlighter sweeps the headline. "Article: the exact headline | Publisher, date" """
    headline, _, source = spec.partition("|")
    headline = headline.strip().strip('"“”')
    if not headline:
        return []
    tall = height > width
    end = _ts(seconds)
    pw, ph = (width * 0.86, height * 0.5) if tall else (width * 0.56, height * 0.84)
    L, T = width / 2 - pw / 2, height * (0.12 if tall else 0.08)
    R, B = L + pw, T + ph
    m = pw * 0.07
    size = int(pw * (0.058 if tall else 0.05))
    out = [f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HB0&\\blur14}}"
           f"{_rect(L + 12, T + 18, R + 12, B + 18)}",
           f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFFFFFF&}}{_rect(L, T, R, B)}"]
    pub, _, date = source.partition(",")
    bar = size * 1.6
    out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H202020&}}{_rect(L, T, R, T + bar)}")
    if pub.strip():
        out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an4\\pos({L + m:.0f},{T + bar / 2:.0f})\\fs{int(size * 0.62)}"
                   f"\\1c&HFFFFFF&}}{_esc(pub.strip().upper())}")
    y = T + bar + m * 0.8
    if date.strip():
        out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos({L + m:.0f},{y:.0f})\\fs{int(size * 0.5)}\\1c&H707070&}}"
                   f"{_esc(date.strip())}")
        y += size * 1.1
    rows = _wrap(headline, 22 if tall else 30, 4)
    t_zoom = 0.3
    hy = []
    for i, row in enumerate(rows):
        out.append(f"Dialogue: 5,{_ts(0)},{end},Q,,0,0,0,,{{\\an7\\pos({L + m:.0f},{y:.0f})\\fs{size}\\b1}}{_esc(row)}")
        rw = min(pw - 2 * m, len(row) * size * 0.52)
        t0 = t_zoom + 0.6 + i * 0.35
        out.append(f"Dialogue: 4,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{L + m - 4:.0f},{height})"
                   f"\\t(0,330,\\clip(0,0,{L + m + rw + 6:.0f},{height}))\\p1\\bord0\\shad0\\1c{MARK[theme]}&\\1a&H30&}}"
                   f"{_rect(L + m - 4, y + size * 0.1, L + m + rw + 6, y + size * 1.25)}")
        hy.append(y)
        y += size * 1.3
    y += size * 0.6
    out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HC8C8C8&}}"
               f"{_rect(L + m, y, L + m + pw * 0.3, y + size * 0.4)}")
    y += size * 1.2
    import random
    rnd = random.Random(headline)
    while y < B - m:
        w = (pw - 2 * m) * (0.6 + 0.4 * rnd.random())
        out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HDCDCDC&\\blur1.5}}"
                   f"{_rect(L + m, y, L + m + w, y + size * 0.42)}")
        y += size * 0.85
    out.append(f"Dialogue: 7,{_ts(0.2)},{end},T,,0,0,0,,{{\\an9\\pos({R - m * 0.3:.0f},{T - size * 0.3:.0f})\\fs{int(size * 0.55)}"
               f"\\bord{int(size * 0.18)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&}}SOURCE")
    cy = (hy[0] + hy[-1]) / 2 + size * 0.6
    hw = min(pw - 2 * m, max(len(r) for r in rows) * size * 0.52)
    z = min(1.6 if tall else 1.35, width * 0.92 / (hw + size))
    return out, {"zoom": (L + m + hw / 2, cy, z, t_zoom)}


def _phone(width: int, height: int, size_k: float = 0.062):
    """A phone frame for Shorts (or a centred phone on widescreen); returns (L, T, R, B, pad, size, lines)."""
    tall = height > width
    fh = height * (0.5 if tall else 0.8)
    fw = fh * 0.52 if not tall else width * 0.6
    L, T = width / 2 - fw / 2, height * (0.12 if tall else 0.1)
    R, B = L + fw, T + fh
    size = int(fw * size_k)
    lines = [f"Dialogue: 1,{_ts(0)},9:59:59.00,T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HB8&\\blur14}}"
             f"{_rect(L + 14, T + 20, R + 14, B + 20, size * 1.2)}",
             f"Dialogue: 2,{_ts(0)},9:59:59.00,T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(6, int(size * 0.35))}\\shad0"
             f"\\1c&HF7F4F2&\\3c&H202020&}}{_rect(L, T, R, B, size * 1.2)}"]
    return L, T, R, B, fw * 0.07, size, lines


def chat_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A recreated (fictional, labelled) text conversation: bubbles pop in one by one, the other side's after a
    'typing' dots bubble. "Chat: Unknown number | them: Hi, is this Sam? · me: Wrong number · them: Oh, sorry!" """
    head, _, body = spec.partition("|")
    if not body.strip():
        head, body = "", head
    msgs = []
    for part in [x.strip() for x in re.split(r"·|•", body) if x.strip()][:7]:
        who, _, text = part.partition(":")
        mine = who.strip().lower() in ("me", "you", "sam", "i")
        msgs.append((mine, text.strip() if text.strip() else part))
    if not msgs:
        return []
    L, T, R, B, pad, size, out = _phone(width, height)
    end = _ts(seconds)
    bar = size * 2.4
    out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFFFFFF&}}{_rect(L + 4, T + size, R - 4, T + size + bar)}")
    if head.strip():
        out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an5\\pos({(L + R) / 2:.0f},{T + size + bar / 2:.0f})\\fs{int(size * 0.85)}}}"
                   f"{_esc(head.strip())}")
    y = T + size + bar + pad
    per = min(0.9, max(0.35, (seconds - 0.6) / len(msgs)))
    t = 0.25
    mine_col, their_col = MARK[theme], "&H00E4E1DE&"
    for mine, text in msgs:
        rows = _wrap(text, 20, 4)
        bh = len(rows) * size * 1.25 + size * 0.8
        bw = min((R - L) * 0.72, max(len(r) for r in rows) * size * 0.56 + size * 1.2)
        if y + bh > B - pad:
            break
        x0 = R - pad - bw if mine else L + pad
        if not mine:      # the other person is typing...
            dots = " ".join(_rect(L + pad + size * (0.7 + i * 0.7), y + size * 0.55, L + pad + size * (1.1 + i * 0.7),
                                  y + size * 0.95, size * 0.2) for i in range(3))
            out.append(f"Dialogue: 5,{_ts(t)},{_ts(t + per * 0.4)},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0"
                       f"\\1c&H00E4E1DE&}}{_rect(L + pad, y, L + pad + size * 3.2, y + size * 1.5, size * 0.7)}")
            out.append(f"Dialogue: 6,{_ts(t)},{_ts(t + per * 0.4)},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0"
                       f"\\1c&H808080&\\t(0,200,\\1c&HC0C0C0&)\\t(200,400,\\1c&H808080&)}}{dots}")
            t += per * 0.4
        pop = f"\\org({x0 + bw / 2:.0f},{y + bh / 2:.0f})\\fscx70\\fscy70\\t(0,120,\\fscx103\\fscy103)\\t(120,180,\\fscx100\\fscy100)"
        out.append(f"Dialogue: 5,{_ts(t)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{mine_col if mine else their_col}}}"
                   f"{_rect(x0, y, x0 + bw, y + bh, size * 0.7)}")
        out.append(f"Dialogue: 6,{_ts(t)},{end},T,,0,0,0,,{{\\an7\\pos({x0 + size * 0.6:.0f},{y + size * 0.4:.0f})\\fs{size}"
                   f"\\fad(80,0)}}" + "\\N".join(_esc(r) for r in rows))
        t += per * 0.6
        y += bh + size * 0.7
    out.append(f"Dialogue: 7,{_ts(0)},{end},T,,0,0,0,,{{\\an9\\pos({R:.0f},{B + size * 0.5:.0f})\\fs{int(size * 0.55)}"
               f"\\1c&H606060&}}ILLUSTRATION")
    return out, {}


def search_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """Typing into a plain search bar (no logo), then results appear as blurred lines with readable titles.
    "Search: how to cancel a subscription | Cancel in 10 steps · Why can't I cancel?" """
    query, _, body = spec.partition("|")
    query = query.strip()
    if not query:
        return []
    tall = height > width
    end = _ts(seconds)
    size = int(min(width, height) * (0.05 if tall else 0.045))
    L, R = width * 0.08, width * 0.92
    y = height * (0.2 if tall else 0.26)
    bh = size * 2.2
    out = [f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord3\\shad0\\1c&HFFFFFF&\\3c&HC8C8C8&}}"
           f"{_rect(L, y, R, y + bh, bh / 2)}"]
    # magnifier icon
    cx, cy, r = L + bh * 0.55, y + bh / 2, size * 0.42
    out.append(f"Dialogue: 3,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(3, size // 9)}\\1a&HFF&\\3c&H707070&}}"
               f"m {cx - r:.0f} {cy:.0f} b {cx - r:.0f} {cy - r * 1.33:.0f} {cx + r:.0f} {cy - r * 1.33:.0f} {cx + r:.0f} {cy:.0f} "
               f"b {cx + r:.0f} {cy + r * 1.33:.0f} {cx - r:.0f} {cy + r * 1.33:.0f} {cx - r:.0f} {cy:.0f}")
    typing = min(1.6, max(0.6, seconds * 0.4))
    per = max(2, int(typing * 100 / max(1, len(query))))
    typed = "".join(f"{{\\alpha&HFF&\\t({int(0.2 * 1000 + i * per * 10)},{int(0.2 * 1000 + i * per * 10) + 1},\\alpha&H00&)}}{_esc(c)}"
                    for i, c in enumerate(query))
    out.append(f"Dialogue: 4,{_ts(0)},{end},T,,0,0,0,,{{\\an4\\pos({L + bh * 1.2:.0f},{y + bh / 2:.0f})\\fs{size}\\1c&H202020&}}{typed}")
    caret_end = 0.2 + typing
    out.append(f"Dialogue: 5,{_ts(0)},{_ts(caret_end + 0.3)},T,,0,0,0,,{{\\an4\\pos({L + bh * 1.2 + len(query) * size * 0.52:.0f},"
               f"{y + bh / 2:.0f})\\fs{size}\\1c&H202020&\\t(0,400,\\alpha&HFF&)\\t(400,800,\\alpha&H00&)}}|")
    titles = [x.strip() for x in re.split(r"·|•", body) if x.strip()][:4]
    ry = y + bh + size * 1.2
    import random
    rnd = random.Random(query)
    for i in range(4):
        t0 = caret_end + 0.25 + i * 0.18
        if i < len(titles):
            out.append(f"Dialogue: 4,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos({L:.0f},{ry:.0f})\\fs{int(size * 0.85)}\\1c&H8B4A1A&"
                       f"\\fad(120,0)}}{_esc(titles[i])}")
        else:
            out.append(f"Dialogue: 4,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HC9A27A&\\fad(120,0)}}"
                       f"{_rect(L, ry + size * 0.2, L + (R - L) * (0.4 + 0.3 * rnd.random()), ry + size * 0.75)}")
        for k in range(2):
            out.append(f"Dialogue: 3,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HDADADA&\\blur1.5\\fad(120,0)}}"
                       f"{_rect(L, ry + size * (1.2 + k * 0.7), L + (R - L) * (0.6 + 0.35 * rnd.random()), ry + size * (1.55 + k * 0.7))}")
        ry += size * 3.0
        if ry > height * (0.62 if tall else 0.92):
            break
    return out, {}


def pie_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A donut that fills to the share, the number counting up in the middle. "Pie: 61% | of losses refunded" """
    head, _, label = spec.partition("|")
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", head)
    if not m:
        return []
    v = max(0.0, min(100.0, float(m.group(1))))
    import math
    tall = height > width
    end = _ts(seconds)
    cx, cy = width / 2, height * (0.36 if tall else 0.45)
    r = min(width, height) * (0.3 if tall else 0.28)
    ring = r * 0.34
    out = []

    def arc(frac: float, r_out: float, r_in: float) -> str:
        n = max(2, int(80 * frac))
        a0 = -math.pi / 2
        pts_o = [(cx + r_out * math.cos(a0 + 2 * math.pi * frac * i / n), cy + r_out * math.sin(a0 + 2 * math.pi * frac * i / n)) for i in range(n + 1)]
        pts_i = [(cx + r_in * math.cos(a0 + 2 * math.pi * frac * i / n), cy + r_in * math.sin(a0 + 2 * math.pi * frac * i / n)) for i in range(n, -1, -1)]
        pts = pts_o + pts_i
        return f"m {pts[0][0]:.0f} {pts[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in pts[1:])
    out.append(f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H00D6D2CC&}}{arc(0.9999, r, r - ring)}")
    anim = min(1.2, seconds * 0.5)
    steps = 24
    for i in range(1, steps + 1):      # the filled arc grows in steps (stepped, like hand-made animation)
        frac = v / 100 * i / steps
        t0, t1 = 0.2 + anim * (i - 1) / steps, 0.2 + anim * i / steps
        out.append(f"Dialogue: 2,{_ts(t0)},{_ts(t1 if i < steps else seconds)},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0"
                   f"\\1c{MARK[theme]}}}{arc(max(frac, 0.005), r, r - ring)}")
        shown = round(v * i / steps) if float(v).is_integer() else round(v * i / steps, 1)
        out.append(f"Dialogue: 3,{_ts(t0)},{_ts(t1 if i < steps else seconds)},T,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f})"
                   f"\\fs{int(r * 0.42)}}}{shown}%")
    if label.strip():
        out.append(f"Dialogue: 4,{_ts(0.4)},{end},T,,0,0,0,,{{\\an8\\pos({cx:.0f},{cy + r + r * 0.18:.0f})\\fs{int(r * 0.17)}"
                   f"\\fad(200,0)}}" + "\\N".join(_esc(x) for x in _wrap(label.strip().upper(), 22 if tall else 34, 2)))
    return out, {}


def squares_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """Proportional squares: each value's area to scale, side by side, so the difference is felt.
    "Squares: £4.2m vs £85,000 | fines, one claim" """
    head, _, labels = spec.partition("|")
    nums = []
    for m in re.finditer(r"([£$€]?)\s*(\d[\d,]*(?:\.\d+)?)\s*(bn|billion|m|million|k|thousand)?", head, re.I):
        v = float(m.group(2).replace(",", ""))
        unit = (m.group(3) or "").lower()
        v *= {"bn": 1e9, "billion": 1e9, "m": 1e6, "million": 1e6, "k": 1e3, "thousand": 1e3}.get(unit, 1)
        nums.append((m.group(0).strip(), v))
    nums = [n for n in nums if n[1] > 0][:3]
    if len(nums) < 2:
        return []
    names = [x.strip() for x in labels.split(",")] if labels.strip() else []
    tall = height > width
    end = _ts(seconds)
    top = max(v for _, v in nums)
    side_max = min(width * (0.62 if tall else 0.36), height * (0.36 if tall else 0.58))
    sizes = [max(6.0, side_max * (v / top) ** 0.5) for _, v in nums]
    out = []
    size = int(min(width, height) * 0.045)
    if tall:   # stacked, biggest first, all above the captions
        y = height * 0.12
        for i, ((txt, _), s_) in enumerate(zip(nums, sizes)):
            x0 = width / 2 - s_ / 2
            t0 = 0.25 + i * 0.45
            out.append(f"Dialogue: 2,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{MARK[theme] if i == 0 else INK}"
                       f"\\clip(0,{y + s_:.0f},{width},{y + s_:.0f})\\t(0,350,\\clip(0,{y:.0f},{width},{y + s_:.0f}))}}{_rect(x0, y, x0 + s_, y + s_)}")
            lab = txt + (f"  {names[i]}" if i < len(names) and names[i] else "")
            out.append(f"Dialogue: 3,{_ts(t0 + 0.3)},{end},T,,0,0,0,,{{\\an4\\pos({x0 + s_ + size * 0.5:.0f},{y + s_ / 2:.0f})"
                       f"\\fs{size}\\fad(150,0)}}{_esc(lab.upper())}" if s_ < width * 0.4 else
                       f"Dialogue: 3,{_ts(t0 + 0.3)},{end},T,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{y + s_ / 2:.0f})\\fs{size}"
                       f"\\fad(150,0)}}{_esc(lab.upper())}")
            y += s_ + size * 1.4
    else:      # side by side on a shared baseline
        base = height * 0.78
        gap = width * 0.06
        total_w = sum(sizes) + gap * (len(sizes) - 1)
        x = width / 2 - total_w / 2
        for i, ((txt, _), s_) in enumerate(zip(nums, sizes)):
            t0 = 0.25 + i * 0.45
            out.append(f"Dialogue: 2,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{MARK[theme] if i == 0 else INK}"
                       f"\\clip(0,{base:.0f},{width},{base:.0f})\\t(0,350,\\clip(0,{base - s_:.0f},{width},{base:.0f}))}}"
                       f"{_rect(x, base - s_, x + s_, base)}")
            out.append(f"Dialogue: 3,{_ts(t0 + 0.3)},{end},T,,0,0,0,,{{\\an8\\pos({x + s_ / 2:.0f},{base + size * 0.4:.0f})\\fs{size}"
                       f"\\fad(150,0)}}{_esc(txt.upper())}" + (f"\\N{_esc(names[i].upper())}" if i < len(names) and names[i] else ""))
            x += s_ + gap
    return out, {}


def timer_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A countdown that runs out (fast), a ring emptying around it. "Timer: 09:59 → 00:00 | Offer ends" """
    head, _, label = spec.partition("|")
    times = re.findall(r"(\d{1,2}):(\d{2})", head)
    if not times:
        return []
    start = int(times[0][0]) * 60 + int(times[0][1])
    stop = int(times[-1][0]) * 60 + int(times[-1][1]) if len(times) > 1 else 0
    import math
    tall = height > width
    end = _ts(seconds)
    cx, cy = width / 2, height * (0.36 if tall else 0.45)
    r = min(width, height) * 0.28
    run = max(1.0, seconds * 0.7)
    steps = 30
    out = []
    for i in range(steps + 1):
        frac = i / steps
        now = round(start + (stop - start) * frac)
        t0 = 0.15 + run * i / steps
        t1 = 0.15 + run * (i + 1) / steps if i < steps else seconds
        left = 1 - frac
        n = max(2, int(80 * left))
        a0 = -math.pi / 2
        pts = [(cx + r * math.cos(a0 + 2 * math.pi * left * k / n), cy + r * math.sin(a0 + 2 * math.pi * left * k / n)) for k in range(n + 1)]
        if left > 0.005:
            path = pts + pts[-2::-1]
            out.append(f"Dialogue: 2,{_ts(t0)},{_ts(t1)},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(6, int(r * 0.09))}\\1a&HFF&"
                       f"\\3c{MARK[theme] if left > 0.25 else PEN[theme]}}}m {path[0][0]:.0f} {path[0][1]:.0f} l "
                       + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:]))
        col = INK if left > 0.25 else PEN[theme]
        out.append(f"Dialogue: 3,{_ts(t0)},{_ts(t1)},T,,0,0,0,,{{\\an5\\pos({cx:.0f},{cy:.0f})\\fs{int(r * 0.5)}\\1c{col}}}"
                   f"{now // 60:02d}:{now % 60:02d}")
    if label.strip():
        out.append(f"Dialogue: 4,{_ts(0.2)},{end},T,,0,0,0,,{{\\an8\\pos({cx:.0f},{cy + r * 1.25:.0f})\\fs{int(r * 0.2)}"
                   f"\\bord{int(r * 0.05)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&}}{_esc(label.strip().upper())}")
    return out, {}


def receipt_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """A printed receipt that rolls out line by line; the * line gets circled, the last line is the total.
    "Receipt: Basket £24.00 · Delivery £3.99 · *Service fee £2.50 · Total £30.49" """
    head, _, body = spec.partition("|")
    if not body.strip():
        head, body = "", head
    rows = [x.strip() for x in re.split(r"·|•|;", body) if x.strip()][:8]
    if not rows:
        return []
    tall = height > width
    end = _ts(seconds)
    pw = width * (0.62 if tall else 0.3)
    L, R = width / 2 - pw / 2, width / 2 + pw / 2
    T = height * (0.1 if tall else 0.08)
    size = int(pw * 0.075)
    step = size * 1.7
    H_ = step * (len(rows) + (2 if head.strip() else 1)) + size * 2
    B = min(T + H_, height * (0.62 if tall else 0.92))
    roll = min(1.0, seconds * 0.4)
    paper = f"m {L:.0f} {T:.0f} l {R:.0f} {T:.0f} l {R:.0f} {B:.0f} " + " ".join(
        f"l {R - (R - L) * k / 24:.0f} {B + (size * 0.4 if k % 2 else 0):.0f}" for k in range(25))
    out = [f"Dialogue: 1,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&HC0&\\blur10"
           f"\\clip(0,0,{width},{T:.0f})\\t(0,{int(roll * 1000)},\\clip(0,0,{width},{height}))}}{paper}",
           f"Dialogue: 2,{_ts(0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&HFDFDFB&"
           f"\\clip(0,0,{width},{T:.0f})\\t(0,{int(roll * 1000)},\\clip(0,0,{width},{height}))}}{paper}"]
    y = T + size
    if head.strip():
        out.append(f"Dialogue: 3,{_ts(0.1)},{end},Q,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{y:.0f})\\fs{size}\\b1}}{_esc(head.strip().upper())}")
        y += step
    target = None
    per = roll / max(1, len(rows))
    for i, row in enumerate(rows):
        star = row.startswith("*")
        row = row.lstrip("*").strip()
        m = re.search(r"([£$€]\s?\d[\d,.]*|\d[\d,.]*\s?%)\s*$", row)
        name, price = (row[:m.start()].strip(), m.group(1)) if m else (row, "")
        last = i == len(rows) - 1
        t0 = 0.15 + i * per
        style = "\\b1" if last else ""
        if last:
            out.append(f"Dialogue: 3,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H404040&}}"
                       f"{_rect(L + size, y - size * 0.35, R - size, y - size * 0.3)}")
        out.append(f"Dialogue: 4,{_ts(t0)},{end},Q,,0,0,0,,{{\\an7\\pos({L + size:.0f},{y:.0f})\\fs{size}{style}\\fad(80,0)}}{_esc(name.upper())}")
        if price:
            out.append(f"Dialogue: 4,{_ts(t0)},{end},Q,,0,0,0,,{{\\an9\\pos({R - size:.0f},{y:.0f})\\fs{size}{style}\\fad(80,0)}}{_esc(price)}")
        if star:
            target = (width / 2, y + size * 0.6, (R - L) / 2 - size * 0.4, size * 0.8)
        if last and len(rows) > 1:
            out.append(f"Dialogue: 3,{_ts(t0 + 0.2)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{MARK[theme]}\\1a&H40&}}"
                       f"{_rect(L + size * 0.6, y - size * 0.1, R - size * 0.6, y + size * 1.3)}")
        y += step
    if target:
        cx, cy, rx, ry = target
        tr = roll + 0.35
        out.append(f"Dialogue: 8,{_ts(tr)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{cx - rx * 1.2:.0f},{height})"
                   f"\\t(0,350,\\clip(0,0,{cx + rx * 1.2:.0f},{height}))\\p1\\bord{max(4, int(size * 0.16))}\\1a&HFF&"
                   f"\\3c{PEN[theme]}&\\blur0.6}}{_ring(cx, cy, rx * 1.06, ry * 1.4)}")
    return out, {}


def endscreen_lines(spec: str, theme: str, width: int, height: int, seconds: float):
    """The last seconds laid out for YouTube's end-screen elements: two video slots and a round subscribe slot,
    with the channel name and a line asking what to watch next. (YouTube's own elements sit on top of these.)"""
    name, _, line = spec.partition("|")
    end = _ts(seconds)
    size = int(height * 0.05)
    out = []
    if name.strip():
        out.append(f"Dialogue: 4,{_ts(0.1)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * 0.08:.0f})\\fs{int(size * 1.3)}"
                   f"\\bord{int(size * 0.3)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fscx15\\t(0,250,\\fscx100)}}{_esc(name.strip().upper())}")
    if line.strip():
        out.append(f"Dialogue: 4,{_ts(0.4)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * 0.2:.0f})\\fs{size}\\fad(200,0)}}"
                   f"{_esc(line.strip())}")
    # YouTube end-screen video elements are 16:9; leave two clean framed slots and a subscribe circle
    vw, vh = width * 0.34, width * 0.34 * 9 / 16
    y = height * 0.36
    for i, x in enumerate((width * 0.08, width * 0.58)):
        out.append(f"Dialogue: 2,{_ts(0.2 + i * 0.15)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(4, size // 6)}\\shad0"
                   f"\\1c&H00EDE8DF&\\3c{INK}&\\fad(200,0)}}{_rect(x, y, x + vw, y + vh, size * 0.3)}")
    r = height * 0.09
    cx, cy = width / 2, y + vh + r * 1.5
    out.append(f"Dialogue: 2,{_ts(0.5)},{end},T,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(4, size // 6)}\\shad0\\1c&H00EDE8DF&"
               f"\\3c{INK}&\\fad(200,0)}}m {cx - r:.0f} {cy:.0f} b {cx - r:.0f} {cy - r * 1.33:.0f} {cx + r:.0f} {cy - r * 1.33:.0f} "
               f"{cx + r:.0f} {cy:.0f} b {cx + r:.0f} {cy + r * 1.33:.0f} {cx - r:.0f} {cy + r * 1.33:.0f} {cx - r:.0f} {cy:.0f}")
    return out, {}


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           brand: str = "") -> Path:
    theme = theme if theme in PAPER else "editorial"
    seconds = max(1.5, seconds)
    body = {"chapter": chapter_lines, "quote": quote_lines, "steps": steps_lines, "timeline": timeline_lines,
            "icons": icons_lines, "screen": screen_lines, "document": document_lines,
            "statement": statement_lines, "article": article_lines, "chat": chat_lines, "search": search_lines,
            "pie": pie_lines, "squares": squares_lines, "timer": timer_lines, "receipt": receipt_lines,
            "endscreen": endscreen_lines}[kind](spec, theme, width, height, seconds)
    opts: dict = {}
    if isinstance(body, tuple):
        body, opts = body
    if not body:
        raise ff.MediaError(f"{kind}: nothing to draw from {spec!r}")     # the line keeps its picture instead
    if brand and kind in ("chapter", "statement"):
        # the channel's name as a small recurring signature on chapter cards and statements
        col = "&H00F4F4F4&" if kind == "statement" else INK
        body.append(f"Dialogue: 9,{_ts(0.3)},{_ts(seconds)},T,,0,0,0,,{{\\an2\\pos({width / 2:.0f},"
                    f"{height * (0.64 if height > width else 0.93):.0f})\\fs{int(min(width, height) * 0.026)}\\1c{col}"
                    f"\\alpha&H40&\\fad(300,0)}}{_esc(brand.strip().upper())}")
    text = "\n".join(_head(width, height, _font()) + body) + "\n"
    work.mkdir(parents=True, exist_ok=True)
    ass = work / f"card_{hashlib.sha256(text.encode()).hexdigest()[:12]}.ass"
    ass.write_text(text, encoding="utf-8")
    zoom = opts.get("zoom")
    # a camera push-in (screens, documents) is drawn at twice the size, then cropped in, so it stays sharp
    k = 2 if zoom else 1
    grid = ",drawgrid=w={0}:h={0}:t=1:c=0x7FA3C8@0.3".format(max(24, height * k // 28)) if theme == "investigative" and not opts.get("plain") else ""
    tail = "vignette=angle=PI/7" if not opts.get("plain") else "vignette=angle=PI/5"
    vf = f"noise=alls=7:allf=t+u{grid},subtitles=filename='{ass}',{tail}"
    if zoom:
        zx, zy, z, t0 = zoom
        zx, zy = zx * k, zy * k
        ease = f"(1-cos(PI*min(1,max(0,(it-{t0:.2f})/0.7))))/2"
        zexpr = f"1+({z:.2f}-1)*{ease}"
        vf += (f",zoompan=z='{zexpr}':x='max(0,min(iw-iw/zoom,{zx:.0f}-iw/zoom/2))'"
               f":y='max(0,min(ih-ih/zoom,{zy:.0f}-ih/zoom*{0.42 if height > width else 0.5}))':d=1:s={width}x{height}:fps=30")
    vf += ",format=yuv420p"
    bg = opts.get("bg") or PAPER[theme]
    ff.run(["-f", "lavfi", "-i", f"color=c={bg}:s={width * k}x{height * k}:d={seconds:.2f}:r=30",
            "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out
