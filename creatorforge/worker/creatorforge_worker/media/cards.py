"""Full-frame explainer cards on paper, drawn with ASS over FFmpeg:

    Chapter: Part 1 | The subscription trap     a chapter title card - a highlighter kicker, a big title, a pen underline
    Quote: Move your money to a safe account | Lloyds Bank, 2026
                                                 a document with the quote typed out and a highlighter sweeping across it
    Steps: Free trial → Card saved → Auto-renew → Forgotten
                                                 how the trap works: cards appear one by one, arrows draw between them,
                                                 the last step lands in the highlight colour
"""
from __future__ import annotations

import hashlib
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
        bw, bh = width * 0.72, size * 2.4
        gap = min(height * 0.7 / n, bh * 1.9)
        centres = [(width / 2, height * 0.45 - gap * (n - 1) / 2 + i * gap) for i in range(n)]
    else:
        gap = width * 0.86 / n
        bw, bh = gap * 0.78, size * 3.2
        centres = [(width * 0.07 + gap * (i + 0.5), height * 0.5) for i in range(n)]
    per = min(0.6, max(0.3, (seconds - 0.8) / n))
    out = []
    if title.strip():
        out.append(f"Dialogue: 6,{_ts(0.1)},{end},T,,0,0,0,,{{\\an8\\pos({width / 2:.0f},{height * (0.08 if tall else 0.12):.0f})"
                   f"\\fs{int(size * 0.9)}\\bord{int(size * 0.3)}\\3c{MARK[theme]}&\\4c{MARK[theme]}&\\fad(150,0)}}"
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
        out.append(f"Dialogue: 3,{_ts(t0)},{end},T,,0,0,0,,{{\\an7\\pos({L + 8:.0f},{T - size * 0.9:.0f})\\fs{int(size * 0.55)}"
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


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path) -> Path:
    theme = theme if theme in PAPER else "editorial"
    seconds = max(1.5, seconds)
    body = {"chapter": chapter_lines, "quote": quote_lines, "steps": steps_lines}[kind](spec, theme, width, height, seconds)
    text = "\n".join(_head(width, height, _font()) + body) + "\n"
    work.mkdir(parents=True, exist_ok=True)
    ass = work / f"card_{hashlib.sha256(text.encode()).hexdigest()[:12]}.ass"
    ass.write_text(text, encoding="utf-8")
    grid = ",drawgrid=w={0}:h={0}:t=1:c=0x7FA3C8@0.3".format(max(24, height // 28)) if theme == "investigative" else ""
    ff.run(["-f", "lavfi", "-i", f"color=c={PAPER[theme]}:s={width}x{height}:d={seconds:.2f}:r=30",
            "-vf", f"noise=alls=7:allf=t+u{grid},subtitles=filename='{ass}',vignette=angle=PI/7,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out
