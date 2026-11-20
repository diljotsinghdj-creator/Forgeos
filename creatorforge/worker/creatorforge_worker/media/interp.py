"""Smooth AI clips: AI video comes out at about 16-24 frames a second; at a 60 fps edit every frame would be shown
two or three times and motion judders. RIFE (rife-ncnn-vulkan, MIT) invents the in-between frames on the GPU; if it
is not installed, FFmpeg's motion-compensated interpolation does the same job more slowly.

    smooth(clip, 60, work) -> a new clip at 60 fps, or the clip itself when it is already smooth enough."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .ff import MediaError

RIFE = os.environ.get("CF_RIFE", "/workspace/rife/rife-ncnn-vulkan")


def fps_of(clip: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate",
                        "-of", "json", str(clip)], capture_output=True, text=True)
    try:
        num, den = json.loads(r.stdout)["streams"][0]["avg_frame_rate"].split("/")
        return float(num) / float(den or 1)
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return 0.0


def _rife(clip: Path, src_fps: float, fps: int, out: Path) -> None:
    exe = Path(RIFE)
    models = exe.parent / "rife-v4.6"
    with tempfile.TemporaryDirectory(prefix="cf_rife_") as tmp:
        a, b = Path(tmp) / "in", Path(tmp) / "out"
        a.mkdir()
        b.mkdir()
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(clip), "-vsync", "0", str(a / "%08d.png")],
                       check=True)
        n = len(list(a.glob("*.png")))
        target = max(n, int(round(n * fps / max(1.0, src_fps))))
        cmd = [str(exe), "-i", str(a), "-o", str(b), "-n", str(target)]
        if models.is_dir():
            cmd += ["-m", str(models)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-framerate", str(fps), "-i",
                        str(b / "%08d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt",
                        "yuv420p", str(out)], check=True)


def smooth(clip: Path, fps: int, work: Path) -> Path:
    """The clip interpolated up to `fps` when it is well below it; otherwise the clip unchanged."""
    src = fps_of(clip)
    if fps < 50 or not src or src >= fps * 0.75:
        return clip
    out = work / f"smooth_{hashlib.sha256(f'{clip}|{fps}'.encode()).hexdigest()[:14]}.mp4"
    if out.is_file():
        return out
    try:
        if Path(RIFE).is_file() and os.access(RIFE, os.X_OK):
            _rife(clip, src, fps, out)
        else:
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(clip), "-vf",
                            f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-an",
                            str(out)], check=True, timeout=1800)
    except (OSError, subprocess.SubprocessError) as e:
        out.unlink(missing_ok=True)
        raise MediaError(f"interpolation failed: {e}") from None
    return out
