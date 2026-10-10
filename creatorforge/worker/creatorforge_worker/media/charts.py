"""Animated number graphics for explainer videos, drawn with FFmpeg only: a counter that rolls up to a figure, bars
that grow side by side, or a percentage bar that fills. Written in scripts as a "Chart:" line (or picked up from a
"Text:" line with an arrow or "vs" in the editorial looks), e.g.

    Chart: £12 → £720 | a year of forgotten subscriptions      (counter)
    Chart: 48% vs 22% | heavy users, everyone else             (bars)
    Chart: 76% | of 642 sites used a possible dark pattern      (filling percentage bar)
    Chart: £1bn → £3bn → £8bn | reported losses | 2015, 2020, 2025   (line graph that draws itself)
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import ff

_NUM = re.compile(r"([£$€]?)\s?(\d[\d,]*(?:\.\d+)?)\s?(%|bn|m|k|billion|million)?", re.I)
THEMES = {
    # paper, ink, accent, second bar colour, graph-paper grid
    "editorial": ("0xF2EBDD", "0x111111", "0xF5C818", "0x111111", False),
    "investigative": ("0xEFE8D8", "0x1A1A1A", "0xC8102E", "0x555555", True),
}
_BOLD = next((p for p in (Path("/usr/share/fonts/truetype/creatorforge/ArchivoBlack-Regular.ttf"),
                          Path.home() / ".fonts" / "ArchivoBlack-Regular.ttf",
                          Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) if p.is_file()),
             Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))


def _numbers(text: str) -> list[tuple[str, float, str, str]]:
    out = []
    for m in _NUM.finditer(text):
        raw = m.group(2).replace(",", "")
        try:
            out.append((m.group(1) or "", float(raw), (m.group(3) or ""), m.group(0)))
        except ValueError:
            pass
    return out


def parse(spec: str) -> dict | None:
    """Turns a chart line into a drawing plan, or None when it isn't a chart."""
    head, _, tail = spec.partition("|")
    tail, _, ticks = tail.partition("|")
    labels = [x.strip() for x in tail.split(",") if x.strip()]
    nums = _numbers(head)
    if not nums:
        return None
    if len(re.findall(r"→|->", head)) >= 2 and len(nums) >= 3:
        nums = nums[:8]
        return {"kind": "line", "values": [n[1] for n in nums], "prefix": nums[-1][0] or nums[0][0],
                "suffix": nums[-1][2] or nums[0][2], "label": tail.strip(),
                "ticks": ([x.strip() for x in ticks.split(",")] + [""] * len(nums))[:len(nums)]}
    title = head
    for *_, raw in nums:
        title = title.replace(raw, " ")
    title = re.sub(r"(→|->|\bvs\.?\b|=|×|\bx\b)", " ", title, flags=re.I)
    title = " ".join(title.split()).strip(" :·-,")
    if ("→" in head or "->" in head or "=" in head) and len(nums) >= 2:
        (p0, a, s0, _), (p1, b, s1, _) = nums[0], nums[-1]
        formula = head.split("=")[0].strip() if "=" in head else ""   # "£12 × 6 = £72" -> counts up, shows "£12 × 6"
        return {"kind": "counter", "from": a, "to": b, "prefix": p1 or p0, "suffix": s1 or s0,
                "label": (labels[0] if labels else (formula or title))}
    if re.search(r"\bvs\.?\b", head, re.I) and len(nums) >= 2:
        nums = nums[:4]
        return {"kind": "bars", "values": [n[1] for n in nums], "prefix": nums[0][0], "suffix": nums[0][2],
                "labels": (labels + [""] * len(nums))[:len(nums)], "title": title}
    p, v, s, _ = nums[0]
    if s == "%" and v <= 100:
        return {"kind": "progress", "value": v, "label": (labels[0] if labels else title)}
    return {"kind": "counter", "from": 0.0, "to": v, "prefix": p, "suffix": s, "label": (labels[0] if labels else title)}


def _esc(text: str) -> str:
    """Literal text for drawtext inside a filter script."""
    return (text.replace("\\", "\\\\\\\\").replace("'", "’").replace(":", "\\:").replace("%", "\\\\%")
            .replace(",", "\\,"))


def _fmt(v: float) -> str:
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"


def _text(txt: str, size: int, color: str, y: str, extra: str = "", x: str = "(w-tw)/2") -> str:
    font = f"fontfile='{_BOLD}'" if _BOLD.is_file() else "font='DejaVu Sans'"
    return f"drawtext={font}:fontsize={size}:fontcolor={color}:x={x}:y={y}:text='{txt}'{extra}"


def _wrap(text: str, size: int, room: int, lines: int = 2) -> list[str]:
    """Splits a label into at most `lines` lines that fit `room` pixels at font `size` (DejaVu Bold ~0.62 em/char)."""
    per = max(6, int(room / (size * (0.74 if "Archivo" in _BOLD.name else 0.62))))   # Archivo Black runs wider
    out, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > per:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][: per - 1].rstrip() + "…"
    return [o[:per] for o in out]


def _label(text: str, size: int, color: str, y: int, room: int, extra: str = "", x: str = "(w-tw)/2",
           lines: int = 2) -> list[str]:
    return [_text(_esc(line), size, color, f"{y + k * int(size * 1.25)}", extra, x=x)
            for k, line in enumerate(_wrap(text, size, room, lines))]


def render(plan: dict, theme: str, width: int, height: int, seconds: float, out: Path, work: Path) -> Path:
    paper, ink, accent, second, grid = THEMES.get(theme, THEMES["editorial"])
    seconds = max(1.0, seconds)
    anim = round(min(1.2, seconds * 0.6), 2)
    ramp = f"min(1\\,t/{anim})"
    fade = f":alpha='min(1\\,t/0.25)'"
    inputs = [f"color=c={paper}:s={width}x{height}:d={seconds:.2f}:r=30"]
    chain = ["noise=alls=6:allf=t+u"]
    if grid:
        step = max(24, height // 28)
        chain.append(f"drawgrid=w={step}:h={step}:t=1:c=0x7FA3C8@0.35")
    title = plan.get("title") or ""
    if title:
        chain += _label(title.upper(), int(height * 0.038), ink, int(height * 0.12), int(width * 0.84), fade)
    overlays: list[str] = []
    kind = plan["kind"]
    # Tall (Shorts) frames carry captions at ~70% of the height: lift the graphic so the two never overlap.
    up = 0.10 if height > width else 0.0
    if kind == "counter":
        a, b = plan["from"], plan["to"]
        pre, suf = _esc(plan["prefix"]), _esc(plan["suffix"])
        if float(a).is_integer() and float(b).is_integer() and abs(b) < 1e9:
            number = f"%{{eif\\:{a:.0f}+({b:.0f}-{a:.0f})*{ramp}\\:d}}"
        else:
            number = _esc(_fmt(b))
        chain.append(_text(pre + number + suf, int(height * 0.12), ink, f"{int(height * (0.40 - up))}"))
        chain.append(f"drawbox=x={int(width * 0.2)}:y={int(height * (0.545 - up))}:w={int(width * 0.6)}:h={max(6, height // 90)}"
                     f":color={accent}:t=fill:enable='gte(t\\,{anim * 0.8:.2f})'")
        if plan.get("label"):
            chain += _label(plan["label"], int(height * 0.034), ink, int(height * (0.60 - up)), int(width * 0.84), fade,
                            lines=3 if height > width else 2)
    elif kind == "bars":
        vals = plan["values"]
        n = len(vals)
        top = max(vals) or 1.0
        left, right = int(width * 0.14), int(width * 0.86)
        slot = (right - left) // n
        bw = int(slot * 0.62)
        base, max_h = int(height * (0.72 - up)), int(height * (0.42 - up / 2))
        for i, v in enumerate(vals):
            bh = max(4, int(max_h * v / top))
            x = left + i * slot + (slot - bw) // 2
            inputs.append(f"color=c={accent if i == 0 else second}:s={bw}x{bh}:d={seconds:.2f}:r=30")
            overlays.append(f"overlay=x={x}:y='{base}-{bh}*{ramp}':eval=frame")
        after = [f"drawbox=x={left}:y={base}:w={right - left}:h={max_h // 8 + 8}:color={paper}:t=fill",
                 f"drawbox=x={left - 10}:y={base}:w={right - left + 20}:h={max(4, height // 160)}:color={ink}:t=fill"]
        for i, v in enumerate(vals):
            cx = left + i * slot + slot // 2
            bh = max(4, int(max_h * v / top))
            value = _esc(plan["prefix"] + _fmt(v) + plan["suffix"])
            after.append(_text(value, int(height * 0.045), ink, f"{base - bh - int(height * 0.06)}",
                               f":enable='gte(t\\,{anim:.2f})'", x=f"{cx}-tw/2"))
            if plan["labels"][i]:
                size = min(int(height * 0.028), int(slot / 7))
                after += _label(plan["labels"][i], size, ink, base + int(height * 0.025), int(slot * 0.92), fade,
                                x=f"{cx}-tw/2")
    elif kind == "progress":
        v = plan["value"]
        x0, y0, tw, th = int(width * 0.14), int(height * (0.52 - up)), int(width * 0.72), int(height * 0.05)
        fw = max(4, int(tw * v / 100))
        inputs.append(f"color=c={accent}:s={fw}x{th}:d={seconds:.2f}:r=30")
        overlays.append(f"overlay=x='{x0}-{fw}*(1-{ramp})':y={y0}:eval=frame")
        after = [f"drawbox=x=0:y={y0}:w={x0}:h={th}:color={paper}:t=fill",
                 f"drawbox=x={x0}:y={y0}:w={tw}:h={th}:color={ink}:t={max(3, height // 240)}"]
        number = (f"%{{eif\\:{v:.0f}*{ramp}\\:d}}" if float(v).is_integer() else _esc(_fmt(v))) + "\\\\%"
        after.append(_text(number, int(height * 0.11), ink, f"{int(height * (0.33 - up))}"))
        if plan.get("label"):
            after += _label(plan["label"], int(height * 0.032), ink, int(height * (0.62 - up)), int(width * 0.84), fade,
                            lines=3 if height > width else 2)
    if kind == "line":
        chain.append(f"subtitles=filename='{_line_ass(plan, theme, width, height, anim, seconds, work)}'")
        if plan.get("label"):
            chain += _label(plan["label"], int(height * 0.034), ink, int(height * (0.555 if height > width else 0.80)),
                            int(width * 0.84), fade, lines=2)
    if kind in ("counter", "line"):
        graph = "[0:v]" + ",".join(chain) + ",format=yuv420p[v]"
    else:
        graph = "[0:v]" + ",".join(chain) + "[b0]"
        last = "b0"
        for i, o in enumerate(overlays):
            graph += f";[{last}][{i + 1}:v]{o}[b{i + 1}]"
            last = f"b{i + 1}"
        graph += f";[{last}]" + ",".join(after) + ",format=yuv420p[v]"
    work.mkdir(parents=True, exist_ok=True)
    script = work / f"chart_{hashlib.sha256(graph.encode()).hexdigest()[:12]}.txt"
    script.write_text(graph, encoding="utf-8")
    args = []
    for src in inputs:
        args += ["-f", "lavfi", "-i", src]
    ff.run([*args, "-filter_complex_script", str(script), "-map", "[v]", "-t", f"{seconds:.2f}", "-r", "30",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(out)])
    return out


def _line_ass(plan: dict, theme: str, width: int, height: int, anim: float, seconds: float, work: Path) -> Path:
    """The line graph as an ASS drawing: axis, a line revealed left to right, dots and values that land as the line
    reaches them, and the period labels underneath."""
    _, ink, accent, second, _ = THEMES.get(theme, THEMES["editorial"])
    bgr = lambda c: f"&H00{c[6:8]}{c[4:6]}{c[2:4]}"  # noqa: E731 - 0xRRGGBB -> ASS &H00BBGGRR
    line_c = bgr(accent if theme == "investigative" else "0x111111")
    dot_c, ink_c = bgr(accent), bgr(ink)
    tall = height > width
    x0, x1 = width * 0.12, width * 0.88
    y_top, y_base = height * (0.17 if tall else 0.20), height * (0.47 if tall else 0.68)
    vals = plan["values"]
    lo, hi = min(0.0, min(vals)), max(vals) or 1.0
    pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y_base - (y_base - y_top) * (v - lo) / ((hi - lo) or 1.0))
           for i, v in enumerate(vals)]
    thick = max(5, int(min(width, height) * 0.008))
    size = int(height * (0.03 if tall else 0.04))
    font = "Archivo Black" if "Archivo" in _BOLD.name else "DejaVu Sans"
    ts = lambda t: f"0:00:{t:05.2f}"  # noqa: E731
    end = ts(seconds)
    path = pts + pts[-2::-1]
    shape = f"m {path[0][0]:.0f} {path[0][1]:.0f} l " + " ".join(f"{x:.0f} {y:.0f}" for x, y in path[1:])
    axis = f"m {x0 - 10:.0f} {y_base:.0f} l {x1 + 10:.0f} {y_base:.0f} l {x0 - 10:.0f} {y_base:.0f}"
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
             "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
             "MarginR, MarginV, Encoding",
             f"Style: D,{font},{size},{ink_c},{ink_c},{ink_c},&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1", "",
             "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
             f"Dialogue: 0,{ts(0)},{end},D,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(2, thick // 3)}\\1a&HFF&\\3c{ink_c}&}}{axis}",
             # the line draws itself: a clip window sweeps from the left edge to the right over the animation time
             f"Dialogue: 1,{ts(0)},{end},D,,0,0,0,,{{\\an7\\pos(0,0)\\clip(0,0,{x0 - thick:.0f},{height})"
             f"\\t(0,{int(anim * 1000)},\\clip(0,0,{x1 + thick * 2:.0f},{height}))\\p1\\bord{thick}\\1a&HFF&"
             f"\\3c{line_c}&\\blur0.6}}{shape}"]
    for i, ((x, y), v) in enumerate(zip(pts, vals)):
        at = anim * i / (len(vals) - 1)
        r = thick * 2.0
        dot = (f"m {x - r:.0f} {y:.0f} b {x - r:.0f} {y - r:.0f} {x + r:.0f} {y - r:.0f} {x + r:.0f} {y:.0f} "
               f"b {x + r:.0f} {y + r:.0f} {x - r:.0f} {y + r:.0f} {x - r:.0f} {y:.0f}")
        lines.append(f"Dialogue: 2,{ts(at)},{end},D,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord0\\1c{dot_c}&}}{dot}")
        if i in (0, len(vals) - 1) or len(vals) <= 5:
            value = f"{plan['prefix']}{_fmt(v)}{plan['suffix']}"
            lines.append(f"Dialogue: 3,{ts(at)},{end},D,,0,0,0,,{{\\an2\\pos({x:.0f},{y - r * 2:.0f})\\fad(120,0)}}{value}")
        if plan["ticks"][i]:
            lines.append(f"Dialogue: 3,{ts(0.1)},{end},D,,0,0,0,,{{\\an8\\pos({x:.0f},{y_base + size * 0.5:.0f})"
                         f"\\fs{int(size * 0.8)}}}{plan['ticks'][i]}")
    work.mkdir(parents=True, exist_ok=True)
    out = work / f"line_{hashlib.sha256(chr(10).join(lines).encode()).hexdigest()[:12]}.ass"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
