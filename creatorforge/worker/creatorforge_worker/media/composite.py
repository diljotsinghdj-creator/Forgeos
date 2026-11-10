"""Green-screen compositing: a keyed clip over a background picture or clip (FFmpeg chromakey + overlay).

    Key: <foreground src> | background: <src> | color: 00FF00 | similarity: 0.12 | position: center|left|right | scale: 0.8

Sources are ledger assets ("asset:V0003") or files. Used for presenter or object footage shot on a key colour (stock
green-screen clips, the creator's own recordings); the background is a real photo, footage or a rendered graphic.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .ff import MediaError


def parse(spec: str) -> dict | None:
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    opt = {k.strip().lower(): v.strip() for p in parts[1:] for k, sep, v in [p.partition(":")] if sep}
    if not opt.get("background"):
        return None
    col = re.sub(r"[^0-9A-Fa-f]", "", opt.get("color", "00FF00"))[:6] or "00FF00"
    return {"type": "key", "fg": parts[0], "bg": opt["background"], "color": col.upper(),
            "similarity": min(0.4, max(0.02, float(re.sub(r"[^\d.]", "", opt.get("similarity", "0.12")) or 0.12))),
            "position": opt.get("position", "center").lower(), "scale": min(1.0, max(0.2, float(re.sub(r"[^\d.]", "", opt.get("scale", "0.85")) or 0.85)))}


def render(spec: str, width: int, height: int, seconds: float, out: Path, fps: int = 24) -> Path:
    from . import photo
    plan = parse(spec)
    if plan is None:
        raise MediaError("key: needs a foreground and a background")
    fg, _ = photo.resolve(plan["fg"])
    bg, _ = photo.resolve(plan["bg"])
    still = bg.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    bgin = (["-loop", "1", "-t", f"{seconds:.2f}", "-i", str(bg)] if still else ["-stream_loop", "-1", "-t", f"{seconds:.2f}", "-i", str(bg)])
    x = {"left": "W*0.05", "right": "W-w-W*0.05"}.get(plan["position"], "(W-w)/2")
    graph = (f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps},setsar=1[bg];"
             f"[1:v]fps={fps},scale=-2:{int(height * plan['scale'])},chromakey=0x{plan['color']}:{plan['similarity']}:0.08,"
             f"despill=type=green[fg];[bg][fg]overlay=x={x}:y=H-h:shortest=1,format=yuv420p[v]")
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *bgin, "-stream_loop", "-1", "-t", f"{seconds:.2f}", "-i", str(fg),
                        "-filter_complex", graph, "-map", "[v]", "-t", f"{seconds:.2f}", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                        str(out)], capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise MediaError(f"key: {r.stderr[-300:]}")
    return out
