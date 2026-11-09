"""Layout checks for drawn graphics: every piece of text and every shape is measured where it is placed, with the
real fonts, before (or after) a graphic is rendered.

    issues = check_card("steps", "One → Two → Three | Title", "editorial", 1920, 1080)
    # [Issue(level="error", what="text off-screen", text="...", box=(...))]

Rules (from title-safe practice and phone legibility guides):
- text stays inside the action-safe frame (4% margin) - otherwise it is cut off on screen;
- text never sits in the caption band (captions would cover it);
- text is at least 2.5% of the height (27 px at 1080p) - smaller is unreadable on a phone (warning under 3.3%);
- no two pieces of text shown at the same time overlap;
- shapes (boxes, cards, phones) stay on screen.
Graphics with a camera push-in (articles, documents, screens) are checked as first drawn, before the push."""
from __future__ import annotations

import functools
import re
import subprocess
from dataclasses import dataclass

EDGE = 0.04              # action-safe margin
MIN_ERR, MIN_WARN = 0.025, 0.033
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


@dataclass
class Issue:
    level: str                    # "error" | "warning"
    what: str
    text: str
    box: tuple

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.what} - {self.text[:50]!r} {tuple(int(v) for v in self.box)}"


def caption_band(width: int, height: int) -> tuple[float, float]:
    """Where captions sit (long-form 0.86, Shorts 0.70 of the height) with room for two lines."""
    return (height * 0.60, height * 0.745) if height > width else (height * 0.785, height * 0.905)


@functools.lru_cache(maxsize=32)
def _font_file(family: str) -> str:
    try:
        return subprocess.run(["fc-match", "-f", "%{file}", family], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


@functools.lru_cache(maxsize=256)
def _pil_font(family: str, size: int):
    from PIL import ImageFont
    path = _font_file(family)
    try:
        return ImageFont.truetype(path, max(4, size)) if path else ImageFont.load_default()
    except OSError:
        return ImageFont.load_default()


def text_width(s: str, family: str, size: float) -> float:
    fam = "Noto Sans Devanagari" if _DEVANAGARI.search(s) else family
    f = _pil_font(fam, int(round(size)))
    try:
        return float(f.getlength(s))
    except AttributeError:
        return len(s) * size * 0.55


_TAG = re.compile(r"\{[^}]*\}")
_TS = re.compile(r"(\d+):(\d\d):(\d\d)\.(\d\d)")


def _secs(ts: str) -> float:
    m = _TS.match(ts.strip())
    return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 100 if m else 0.0


def _last(tags: str, name: str, default=None):
    """The last value of an override tag outside \\t(...) animations (the state a piece settles in)."""
    flat = re.sub(r"\\t\([^)]*\)", "", tags)
    found = re.findall(rf"\\{name}([-\d.]+)", flat)
    return float(found[-1]) if found else default


def parse_ass(lines: list[str], fonts: dict[str, str], base_size: float = 40) -> list[dict]:
    """Every Dialogue line as a measured item: {"kind": "text"|"shape", "box": (L, T, R, B), "t0", "t1",
    "text", "size"}."""
    out = []
    for ln in lines:
        if not ln.startswith("Dialogue:"):
            continue
        parts = ln.split(",", 9)
        if len(parts) < 10:
            continue
        style, body = parts[3].strip(), parts[9]
        t0, t1 = _secs(parts[1]), _secs(parts[2])
        tags = "".join(re.findall(r"\{([^}]*)\}", body))
        pos = re.search(r"\\pos\(([-\d.]+),([-\d.]+)\)", tags)
        x, y = (float(pos[1]), float(pos[2])) if pos else (0.0, 0.0)
        an = int(_last(tags, "an", 5 if style == "T" else 7))
        clip = re.search(r"\\clip\(", tags)
        if re.search(r"\\p[1-9]", tags):
            nums = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", _TAG.sub("", body))]
            xs, ys = nums[0::2], nums[1::2]
            if xs and ys and not clip:
                out.append({"kind": "shape", "box": (x + min(xs), y + min(ys), x + max(xs), y + max(ys)),
                            "t0": t0, "t1": t1, "text": "(shape)", "size": 0})
            continue
        text = _TAG.sub("", body).replace("\\h", " ")
        rows = [r for r in text.split("\\N") if r.strip()]
        if not rows:
            continue
        size = _last(tags, "fs", base_size)
        sx = (_last(tags, "fscx", 100) if "\\t(" not in tags else 100) / 100
        sy = (_last(tags, "fscy", 100) if "\\t(" not in tags else 100) / 100
        bord = _last(tags, "bord", 0) or 0
        fam = fonts.get(style, fonts.get("T", "DejaVu Sans"))
        w = max(text_width(r, fam, size) for r in rows) * sx + 2 * bord
        h = len(rows) * size * 1.2 * sy + 2 * bord
        hor, ver = (an - 1) % 3, (an - 1) // 3          # 0 left / 1 centre / 2 right; 0 bottom / 1 middle / 2 top
        L = x - (0, w / 2, w)[hor]
        T = y - (h, h / 2, 0)[ver]
        out.append({"kind": "text", "box": (L, T, L + w, T + h), "t0": t0, "t1": t1, "text": " / ".join(rows),
                    "size": size * sy})
    return out


def check_items(items: list[dict], width: int, height: int, captions: bool = True) -> list[Issue]:
    issues: list[Issue] = []
    lo, hi = caption_band(width, height)
    ex, ey = width * EDGE, height * EDGE
    for it in items:
        L, T, R, B = it["box"]
        if it["kind"] == "shape":
            if L < -2 or T < -2 or R > width + 2 or B > height + 2:
                if (R - L) < width * 0.98 and (B - T) < height * 0.98:      # a full-frame backdrop is fine
                    issues.append(Issue("error", "shape off-screen", it["text"], it["box"]))
            continue
        if L < ex or T < ey or R > width - ex or B > height - ey:
            issues.append(Issue("error", "text off-screen or at the edge", it["text"], it["box"]))
        if captions and B > lo and T < hi:
            issues.append(Issue("error", "text in the caption band", it["text"], it["box"]))
        side = min(width, height)        # a Short is read full-width on a phone: size is judged on the short side
        if len(it["text"].strip()) <= 1:
            continue                      # a typing cursor or a bullet
        if it["size"] < side * MIN_ERR:
            issues.append(Issue("error", f"text too small ({it['size']:.0f}px)", it["text"], it["box"]))
        elif it["size"] < side * MIN_WARN:
            issues.append(Issue("warning", f"text small ({it['size']:.0f}px)", it["text"], it["box"]))
    texts = [i for i in items if i["kind"] == "text" and len(i["text"].strip()) > 1]
    for a in range(len(texts)):
        for b in range(a + 1, len(texts)):
            p, q = texts[a], texts[b]
            if p["t1"] <= q["t0"] or q["t1"] <= p["t0"]:
                continue
            L, T = max(p["box"][0], q["box"][0]), max(p["box"][1], q["box"][1])
            R, B = min(p["box"][2], q["box"][2]), min(p["box"][3], q["box"][3])
            if R <= L or B <= T:
                continue
            small = min((p["box"][2] - p["box"][0]) * (p["box"][3] - p["box"][1]),
                        (q["box"][2] - q["box"][0]) * (q["box"][3] - q["box"][1])) or 1
            if (R - L) * (B - T) / small > 0.12:
                issues.append(Issue("error", "texts overlap", f"{p['text']} ⟷ {q['text']}", (L, T, R, B)))
    return issues


def check_card(kind: str, spec: str, theme: str, width: int, height: int, seconds: float = 5.0,
               captions: bool = True, fit: bool = True) -> list[Issue]:
    """Lays out a drawn card (cards.py) and checks it, without rendering any video."""
    from . import cards
    fn = {"chapter": cards.chapter_lines, "quote": cards.quote_lines, "steps": cards.steps_lines,
          "timeline": cards.timeline_lines, "icons": cards.icons_lines, "screen": cards.screen_lines,
          "document": cards.document_lines, "statement": cards.statement_lines, "article": cards.article_lines,
          "chat": cards.chat_lines, "search": cards.search_lines, "pie": cards.pie_lines,
          "squares": cards.squares_lines, "timer": cards.timer_lines, "receipt": cards.receipt_lines}[kind]
    body = fn(spec, theme, width, height, seconds)
    if isinstance(body, tuple):
        body = body[0]
    if not body:
        return [Issue("error", "nothing drawn (bad syntax?)", spec, (0, 0, 0, 0))]
    fonts = {"T": cards._font(), "Q": "DejaVu Serif"}
    if fit:
        body, _ = fit_lines(body, width, height, fonts, captions)
    return check_items(parse_ass(body, fonts), width, height, captions)


# ---- automatic fitting -------------------------------------------------------------------------------------------
_NUM = r"-?\d+(?:\.\d+)?"


def _backdrop(it: dict, width: int, height: int) -> bool:
    L, T, R, B = it["box"]
    return (R - L) >= width * 0.97 and (B - T) >= height * 0.97


def _map_line(ln: str, fx, fy, s: float) -> str:
    """Applies x' = fx(x), y' = fy(y) and size*s to one Dialogue line (positions, clips, moves, drawings, sizes)."""
    head, body = ln.split(",", 9)[:9], ln.split(",", 9)[9]
    drawing = bool(re.search(r"\\p[1-9]", body))

    def tags(m):
        t = m.group(0)
        t = re.sub(rf"\\(pos|org)\(({_NUM}),({_NUM})\)", lambda q: f"\\{q[1]}({fx(float(q[2])):.0f},{fy(float(q[3])):.0f})", t)
        t = re.sub(rf"\\move\(({_NUM}),({_NUM}),({_NUM}),({_NUM})",
                   lambda q: f"\\move({fx(float(q[1])):.0f},{fy(float(q[2])):.0f},{fx(float(q[3])):.0f},{fy(float(q[4])):.0f}", t)
        t = re.sub(rf"\\(i?clip)\(({_NUM}),({_NUM}),({_NUM}),({_NUM})\)",
                   lambda q: f"\\{q[1]}({fx(float(q[2])):.0f},{fy(float(q[3])):.0f},{fx(float(q[4])):.0f},{fy(float(q[5])):.0f})", t)
        t = re.sub(rf"\\(fs|bord|shad)({_NUM})", lambda q: f"\\{q[1]}{max(0.0, float(q[2]) * s):.1f}".replace(".0", ""), t)
        return t
    if drawing:
        # drawing coordinates are relative to \pos: scale them (the position itself moves with fx/fy)
        parts = re.split(r"(\{[^}]*\})", body)
        out = []
        for part in parts:
            if part.startswith("{"):
                out.append(tags(re.match(r".*", part, re.S)))
            else:
                out.append(re.sub(_NUM, lambda q: f"{float(q[0]) * s:.0f}", part))
        body = "".join(out)
    else:
        body = re.sub(r"\{[^}]*\}", tags, body)
    return ",".join(head) + "," + body


def _region(width: int, height: int, captions: bool) -> tuple[float, float, float, float]:
    lo, _ = caption_band(width, height)
    bottom = (lo - height * 0.012) if captions else height * (1 - EDGE - 0.01)
    return width * (EDGE + 0.01), height * (EDGE + 0.01), width * (1 - EDGE - 0.01), bottom


def fit_lines(lines: list[str], width: int, height: int, fonts: dict[str, str], captions: bool = True,
              zoom: tuple | None = None) -> tuple[list[str], tuple | None]:
    """Shrinks over-wide text lines, then scales and moves the whole graphic into the safe region (inside the
    edges, above the captions). Returns the fitted lines and the moved camera-zoom target."""
    lines = list(lines)
    L0, T0, R0, B0 = _region(width, height, captions)
    # 1. a single line too wide for the screen: smaller type for that line
    for i, ln in enumerate(lines):
        its = parse_ass([ln], fonts)
        if not its or its[0]["kind"] != "text":
            continue
        L, T, R, B = its[0]["box"]
        if (R - L) > (R0 - L0):
            k = (R0 - L0) / (R - L) * 0.98
            cx = (L + R) / 2
            lines[i] = _map_line(ln, lambda x, k=k, cx=cx: cx + (x - cx) * k, lambda y: y, k)
    # 2. the whole graphic into the region
    items = [it for it in parse_ass(lines, fonts)]
    keep = [it for it in items if not _backdrop(it, width, height)]
    if not keep:
        return lines, zoom
    L = min(it["box"][0] for it in keep); T = min(it["box"][1] for it in keep)
    R = max(it["box"][2] for it in keep); B = max(it["box"][3] for it in keep)
    if L >= L0 and T >= T0 and R <= R0 and B <= B0:
        return lines, zoom
    s = min(1.0, (R0 - L0) / max(1.0, R - L), (B0 - T0) / max(1.0, B - T))
    cx, cy = (L + R) / 2, (T + B) / 2
    # keep the graphic where it was when it already fits on that axis, otherwise centre it in the region
    nx = min(max(cx, L0 + (R - L) * s / 2), R0 - (R - L) * s / 2)
    ny = min(max(cy, T0 + (B - T) * s / 2), B0 - (B - T) * s / 2)
    fx = lambda x: nx + (x - cx) * s          # noqa: E731
    fy = lambda y: ny + (y - cy) * s          # noqa: E731
    out = []
    for ln in lines:
        its = parse_ass([ln], fonts) if ln.startswith("Dialogue:") else []
        if ln.startswith("Dialogue:") and not (its and _backdrop(its[0], width, height)):
            ln = _map_line(ln, fx, fy, s)
        out.append(ln)
    if zoom:
        zx, zy, z, t0 = zoom
        zoom = (fx(zx), fy(zy), z, t0)
    return out, zoom
