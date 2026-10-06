"""Fail-closed asset and export verification. Nothing is marked READY unless it passes."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .ff import MediaError, probe

PNG = b"\x89PNG\r\n\x1a\n"


def image(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size < 1000:
        raise MediaError("image missing or too small")
    head = path.read_bytes()[:8]
    if not (head.startswith(PNG) or head[:3] == b"\xff\xd8\xff"):
        raise MediaError("output is not a PNG/JPEG image")
    v = [s for s in probe(path)["streams"] if s.get("codec_type") == "video"]
    if not v or int(v[0]["width"]) < 256 or int(v[0]["height"]) < 256:
        raise MediaError("image resolution too small")
    return {"width": int(v[0]["width"]), "height": int(v[0]["height"])}


def wav(path: Path) -> float:
    if not path.is_file() or path.stat().st_size < 1000:
        raise MediaError("audio missing or too small")
    head = path.read_bytes()[:12]
    if head[:4] != b"RIFF" or head[8:12] != b"WAVE":
        raise MediaError("output is not a WAV file")
    d = float(probe(path)["format"]["duration"])
    if d < 0.3:
        raise MediaError("narration shorter than 0.3s")
    return d


def clip(path: Path) -> float:
    if not path.is_file() or path.stat().st_size < 2000:
        raise MediaError("video clip missing or too small")
    info = probe(path)
    v = [s for s in info["streams"] if s.get("codec_type") == "video"]
    if not v:
        raise MediaError("video clip has no video stream")
    d = float(info["format"].get("duration") or 0)
    if d < 0.5:
        raise MediaError("video clip shorter than 0.5s")
    return d


def mp4(path: Path, width: int, height: int, expected_s: float) -> dict:
    """Checks container, codecs, resolution, duration, then fully decodes the file."""
    if not path.is_file() or path.stat().st_size < 10_000:
        raise MediaError("export missing or too small")
    info = probe(path)
    streams = info["streams"]
    v = [s for s in streams if s.get("codec_type") == "video"]
    a = [s for s in streams if s.get("codec_type") == "audio"]
    if len(v) != 1 or v[0].get("codec_name") != "h264":
        raise MediaError("export must contain exactly one H.264 video stream")
    if len(a) != 1 or a[0].get("codec_name") != "aac":
        raise MediaError("export must contain exactly one AAC audio stream")
    if (int(v[0]["width"]), int(v[0]["height"])) != (width, height):
        raise MediaError(f"export is {v[0]['width']}x{v[0]['height']}, expected {width}x{height}")
    dur = float(info["format"]["duration"])
    if abs(dur - expected_s) > 0.75:
        raise MediaError(f"export duration {dur:.2f}s, expected {expected_s:.2f}s")
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, timeout=1800)
    if p.returncode != 0 or p.stderr.strip():
        raise MediaError(f"export failed full decode check: {p.stderr.decode(errors='replace')[-300:]}")
    return {"width": width, "height": height, "duration_s": round(dur, 3), "video_codec": "h264",
            "audio_codec": "aac", "bytes": path.stat().st_size, "decode_check": "passed"}
