"""FFmpeg/ffprobe helpers with cancellation support."""
from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path


class Cancelled(Exception):
    pass


class MediaError(RuntimeError):
    pass


def run(args: list[str], cancel: threading.Event | None = None, cwd: Path | None = None, timeout: float = 3600) -> None:
    proc = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-nostdin", "-v", "error", *args],
                            cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    start = time.monotonic()
    while proc.poll() is None:
        if cancel is not None and cancel.is_set():
            proc.kill()
            proc.wait()
            raise Cancelled()
        if time.monotonic() - start > timeout:
            proc.kill()
            proc.wait()
            raise MediaError("ffmpeg timed out")
        time.sleep(0.1)
    err = proc.stderr.read().decode(errors="replace") if proc.stderr else ""
    if proc.returncode != 0:
        raise MediaError(f"ffmpeg failed ({proc.returncode}): {err[-800:]}")


def probe(path: Path) -> dict:
    p = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, timeout=120)
    if p.returncode != 0:
        raise MediaError(f"ffprobe could not read {path.name}: {p.stderr.decode(errors='replace')[-300:]}")
    return json.loads(p.stdout)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])
