"""Separating a recording into voice and everything else, with Demucs (MIT, Meta's music source separation).

    instrumental(track, work) -> (path, how)   a licensed song with its singing removed, so it can sit under narration
    clean_voice(take, work)  -> (path, how)    a narration recorded over music or room noise, with only the voice kept

Demucs is optional (`pip install demucs`, GPU recommended). Without it the file is used as it is and the result says
so. Nothing is invented: separation only removes; it never adds sound that was not in the recording.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = None      # tests set a callable(path, out_dir) -> {"vocals": Path, "no_vocals": Path}


def ready() -> bool:
    if BACKEND is not None:
        return True
    try:
        import demucs  # noqa: F401
    except ImportError:
        return False
    return True


def separate(path: Path, work: Path) -> dict:
    path, work = Path(path), Path(work)
    key = hashlib.sha1(f"{path.resolve()}:{path.stat().st_size}".encode()).hexdigest()[:12]
    out = work / f"stems_{key}"
    done = {"vocals": out / "vocals.wav", "no_vocals": out / "no_vocals.wav"}
    if all(p.is_file() for p in done.values()):
        return done
    out.mkdir(parents=True, exist_ok=True)
    if BACKEND is not None:
        got = BACKEND(path, out)
    else:
        subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", "htdemucs", "-o", str(out), str(path)],
                       check=True, timeout=3600, capture_output=True)
        d = out / "htdemucs" / path.stem
        got = {"vocals": d / "vocals.wav", "no_vocals": d / "no_vocals.wav"}
    for k, p in got.items():
        if Path(p) != done[k]:
            shutil.copy(p, done[k])
    return done


def instrumental(track: Path, work: Path) -> tuple[Path, str]:
    if not ready():
        return Path(track), "as supplied (Demucs not installed, so any singing stays)"
    return separate(track, work)["no_vocals"], "singing removed with Demucs"


def clean_voice(take: Path, work: Path) -> tuple[Path, str]:
    if not ready():
        return Path(take), "as recorded (Demucs not installed)"
    return separate(take, work)["vocals"], "voice isolated with Demucs"
