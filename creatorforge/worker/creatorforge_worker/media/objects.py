"""Simple 3D objects for explainers, drawn frame by frame with Pillow (no 3D engine, no GPU): a coin that spins and
lands face-on, a bank card that flips over, 3D bars that rise, a stack of coins that grows. Written as "Object:" lines:

    Object: coin | £1 | one pound coin          (spins twice, lands showing "£1", label underneath)
    Object: card | Subscription card            (a plain bank card flips from front to back; never a real brand)
    Object: bars | 12, 45, 80 | 2019, 2021, 2023 | Losses rise
    Object: stack | 12 | twelve months of £10   (coins drop onto a growing pile, counter beside it)
"""
from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

from . import ff
from .globe import _font

FPS = 30
PAPER = {"editorial": (242, 236, 223), "investigative": (233, 224, 204)}
GOLD = ((247, 214, 43), (196, 150, 20), (120, 88, 10))      # face, edge, shadow
INK = (20, 20, 20)
ACCENT = {"editorial": (247, 214, 43), "investigative": (200, 16, 46)}


def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 1 - (1 - t) ** 3


def parse(spec: str) -> dict | None:
    parts = [p.strip() for p in spec.split("|")]
    kind = parts[0].lower().split()[0] if parts and parts[0] else ""
    if kind == "coin":
        return {"kind": "coin", "face": (parts[1] if len(parts) > 1 else "")[:6], "label": parts[2] if len(parts) > 2 else ""}
    if kind == "card":
        return {"kind": "card", "label": parts[1] if len(parts) > 1 else ""}
    if kind == "bars":
        vals = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", parts[1] if len(parts) > 1 else "")][:6]
        if len(vals) < 2 or max(vals) <= 0:
            return None
        names = [x.strip() for x in (parts[2].split(",") if len(parts) > 2 else [])]
        return {"kind": "bars", "values": vals, "names": (names + [""] * len(vals))[:len(vals)],
                "title": parts[3] if len(parts) > 3 else ""}
    if kind == "stack":
        m = re.search(r"\d+", parts[1] if len(parts) > 1 else "")
        if not m:
            return None
        return {"kind": "stack", "count": max(2, min(40, int(m.group()))), "label": parts[2] if len(parts) > 2 else ""}
    return None


def render(plan: dict, theme: str, width: int, height: int, seconds: float, out: Path, work: Path) -> Path:
    from PIL import Image, ImageDraw
    seconds = max(1.5, seconds)
    frames = int(round(seconds * FPS))
    ss = 2                                            # drawn at 2x, scaled down: smooth edges
    W, H = width * ss, height * ss
    tall = height > width
    page = PAPER.get(theme, PAPER["editorial"])
    accent = ACCENT.get(theme, ACCENT["editorial"])
    big, small = _font(int(min(W, H) * 0.11)), _font(int(min(W, H) * 0.045))
    work.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-v", "error", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(FPS), "-i", "-",
                             "-vf", "noise=alls=6:allf=t+u,vignette=angle=PI/7,format=yuv420p", "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "18", str(out)],
                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    cx, cy = W / 2, H * (0.38 if tall else 0.46)
    try:
        for f in range(frames):
            t = f / FPS
            im = Image.new("RGB", (W, H), page)
            d = ImageDraw.Draw(im)
            k = plan["kind"]
            if k == "coin":
                _coin(d, cx, cy, min(W, H) * 0.26, t, seconds, plan["face"], big)
            elif k == "card":
                _card(d, cx, cy, min(W, H) * (0.62 if tall else 0.5), t, seconds, accent, small)
            elif k == "bars":
                _bars(d, W, H, t, plan, accent, small, tall)
            elif k == "stack":
                _stack(d, cx, cy, min(W, H), t, seconds, plan["count"], big)
            label = plan.get("label") or plan.get("title") or ""
            if label and t > 0.3:
                text = label.upper()
                l, tp, r, b = d.textbbox((0, 0), text, font=small)
                y = H * (0.1 if k == "bars" else (0.6 if tall else 0.84))
                pad = small.size // 3
                d.rectangle((W / 2 - (r - l) / 2 - pad, y - pad, W / 2 + (r - l) / 2 + pad, y + (b - tp) + pad), fill=accent)
                d.text((W / 2 - (r - l) / 2 - l, y - tp), text, font=small, fill=INK)
            proc.stdin.write(im.resize((width, height), Image.LANCZOS).tobytes())
        proc.stdin.close()
        proc.wait(timeout=600)
    except (BrokenPipeError, subprocess.TimeoutExpired) as e:
        proc.kill()
        raise ff.MediaError(f"object render failed: {e}") from e
    if proc.returncode != 0:
        raise ff.MediaError("object render failed: " + (proc.stderr.read() if proc.stderr else b"").decode(errors="replace")[-300:])
    return out


def _coin(d, cx, cy, r, t, seconds, face, font):
    spin_end = min(1.6, seconds * 0.6)
    ang = (1 - _ease(t / spin_end)) * math.pi * 4          # two full turns, easing to face-on
    sx = abs(math.cos(ang))
    thick = r * 0.12 * math.sin(ang) ** 2 + r * 0.02
    rx = max(2.0, r * sx)
    face_col, edge_col, shade = GOLD
    d.ellipse((cx - r * 1.05, cy + r * 1.05, cx + r * 1.05, cy + r * 1.25), fill=(0, 0, 0, 0) if False else (205, 198, 184))
    for i in range(int(thick), 0, -2):                        # the rim
        d.ellipse((cx - rx + i * 0.5, cy - r + i * 0.2, cx + rx + i * 0.5, cy + r + i * 0.2), fill=edge_col)
    d.ellipse((cx - rx, cy - r, cx + rx, cy + r), fill=face_col, outline=shade, width=max(2, int(r * 0.03)))
    if sx > 0.25:
        d.ellipse((cx - rx * 0.82, cy - r * 0.82, cx + rx * 0.82, cy + r * 0.82), outline=edge_col, width=max(2, int(r * 0.025)))
        if face and sx > 0.6:
            l, tp, rr, b = d.textbbox((0, 0), face, font=font)
            d.text((cx - (rr - l) / 2 - l, cy - (b - tp) / 2 - tp), face, font=font, fill=shade)
    d.chord((cx - rx * 0.9, cy - r * 0.9, cx - rx * 0.1, cy - r * 0.1), 200, 250, fill=(255, 240, 160))   # glint


def _card(d, cx, cy, w, t, seconds, accent, font):
    h = w * 0.63
    flip_t = min(1.4, seconds * 0.5)
    ang = _ease(max(0.0, t - 0.4) / flip_t) * math.pi            # face -> back
    sx = math.cos(ang)
    hw = abs(sx) * w / 2
    lean = math.sin(ang) * h * 0.08                            # perspective: the far edge looks shorter
    front = sx >= 0
    pts = [(cx - hw, cy - h / 2 - lean), (cx + hw, cy - h / 2 + lean), (cx + hw, cy + h / 2 - lean),
           (cx - hw, cy + h / 2 + lean)]
    d.polygon([(x + w * 0.02, y + h * 0.05) for x, y in pts], fill=(200, 192, 176))
    d.polygon(pts, fill=(38, 64, 110) if front else (58, 84, 130))
    if hw > w * 0.15:
        if front:
            chip = (cx - hw * 0.75, cy - h * 0.12, cx - hw * 0.45, cy + h * 0.1)
            d.rectangle(chip, fill=(222, 196, 110))
            d.text((cx - hw * 0.75, cy + h * 0.18), "•••• •••• •••• 0000", font=font, fill=(235, 235, 235))
        else:
            d.rectangle((cx - hw, cy - h * 0.32, cx + hw, cy - h * 0.15), fill=(20, 20, 20))
            d.rectangle((cx - hw * 0.8, cy - h * 0.02, cx + hw * 0.2, cy + h * 0.1), fill=(240, 240, 240))


def _bars(d, W, H, t, plan, accent, font, tall):
    vals, names = plan["values"], plan["names"]
    n = len(vals)
    top = max(vals)
    left, right = W * 0.14, W * 0.86
    base = H * (0.56 if tall else 0.8)
    max_h = H * (0.32 if tall else 0.55)
    slot = (right - left) / n
    bw = slot * 0.5
    depth = bw * 0.35
    for i, v in enumerate(vals):
        grow = _ease((t - 0.15 - i * 0.12) / 0.9)
        bh = max_h * v / top * grow
        x0 = left + i * slot + (slot - bw) / 2
        col = accent if i == n - 1 else (60, 60, 60)
        dark = tuple(int(c * 0.7) for c in col)
        light = tuple(min(255, int(c * 1.15 + 20)) for c in col)
        d.polygon([(x0 + bw, base), (x0 + bw + depth, base - depth), (x0 + bw + depth, base - bh - depth), (x0 + bw, base - bh)], fill=dark)
        d.polygon([(x0, base - bh), (x0 + depth, base - bh - depth), (x0 + bw + depth, base - bh - depth), (x0 + bw, base - bh)], fill=light)
        d.rectangle((x0, base - bh, x0 + bw, base), fill=col)
        if grow > 0.95:
            txt = f"{v:g}"
            l, tp, r, b = d.textbbox((0, 0), txt, font=font)
            d.text((x0 + bw / 2 - (r - l) / 2 - l, base - bh - depth - (b - tp) * 1.6 - tp), txt, font=font, fill=INK)
        if names[i]:
            l, tp, r, b = d.textbbox((0, 0), names[i], font=font)
            d.text((x0 + bw / 2 - (r - l) / 2 - l, base + font.size * 0.4 - tp), names[i], font=font, fill=INK)
    d.rectangle((left - 10, base, right + 10, base + max(4, H // 300)), fill=INK)


def _stack(d, cx, cy, short, t, seconds, count, font):
    r, th = short * 0.16, short * 0.025
    per = max(0.04, min(0.18, (seconds * 0.6) / count))
    landed = min(count, int(max(0.0, t - 0.2) / per) + 1)
    base = cy + short * 0.22
    face, edge, shade = GOLD
    d.ellipse((cx - r * 1.2, base - th, cx + r * 1.2, base + r * 0.4), fill=(205, 198, 184))
    for i in range(landed):
        frac = min(1.0, (t - 0.2 - i * per) / per) if i == landed - 1 else 1.0
        y = base - i * th - (1 - _ease(frac)) * short * 0.25
        d.ellipse((cx - r, y - r * 0.32 + th, cx + r, y + r * 0.32 + th), fill=shade)
        d.rectangle((cx - r, y, cx + r, y + th), fill=edge)
        d.ellipse((cx - r, y - r * 0.32, cx + r, y + r * 0.32), fill=face, outline=shade, width=2)
    txt = f"× {landed}"
    l, tp, rr, b = d.textbbox((0, 0), txt, font=font)
    d.text((cx - (rr - l) / 2 - l, base - landed * th - r * 0.4 - (b - tp) * 1.3 - tp), txt, font=font, fill=INK)
