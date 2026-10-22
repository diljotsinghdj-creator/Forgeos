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
    try:
        d = float(probe(path)["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        d = 0.0
    if not d > 0:
        raise MediaError(f"{Path(path).name} has no playable length (empty or broken file)")
    return d


def filter_path(path: Path | str) -> str:
    """A file path written as a filter option value (unquoted), escaped for both ffmpeg parsing levels - so a
    folder with an apostrophe, colon, comma or bracket in its name still works."""
    s = str(path)
    for a, b in (("\\", "\\\\"), (":", "\\:"), ("'", "\\'")):            # option-value level
        s = s.replace(a, b)
    for a, b in (("\\", "\\\\"), ("'", "\\'"), ("[", "\\["), ("]", "\\]"), (",", "\\,"), (";", "\\;")):
        s = s.replace(a, b)                                                # filtergraph level
    return s


def ass_filter(path: Path | str) -> str:
    """The ASS-subtitle filter with complex text shaping, so Hindi (Devanagari) conjuncts and vowel signs join up
    correctly (the default simple shaping breaks "दिल्ली" into "दलि्ली")."""
    return f"ass=filename={filter_path(path)}:shaping=complex"
