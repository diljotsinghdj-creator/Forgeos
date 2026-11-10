"""Narration audio, one file per scene, so every scene's timing comes from its own waveform.

Voices, best first:
    kokoro   Kokoro-82M through kokoro-onnx (Apache-2.0): natural English, Hindi and other voices, CPU-only. The model
             files (kokoro-v1.0.int8.onnx or kokoro-v1.0.onnx, voices-v1.0.bin) live in CF_KOKORO_DIR
             (default <data>/models/kokoro); setup downloads them from the kokoro-onnx GitHub release.
    flite    FFmpeg's built-in voice: robotic, a last resort so a draft can still be timed.
On the pod the production pipeline's own voices (ElevenLabs, Gemini, Chatterbox...) can replace these: they are
called through the same synth() so the timeline is still built from the real audio.

Pronunciation: the screenplay's guide ({"Moynaq": "Moy-nahk"}) is applied to the text the voice reads only; the
captions and the narration script keep the correct spelling.
"""
from __future__ import annotations

import os
import re
import subprocess
import threading
import wave
from pathlib import Path

SR = 48000
_lock = threading.Lock()
_kokoro = None


def model_dir() -> Path:
    return Path(os.environ.get("CF_KOKORO_DIR") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "models" / "kokoro")


def kokoro_ready() -> bool:
    d = model_dir()
    try:
        import kokoro_onnx  # noqa: F401
    except ImportError:
        return False
    return (d / "voices-v1.0.bin").is_file() and any((d / f).is_file() for f in ("kokoro-v1.0.int8.onnx", "kokoro-v1.0.onnx"))


def _engine():
    global _kokoro
    with _lock:
        if _kokoro is None:
            from kokoro_onnx import Kokoro
            d = model_dir()
            onnx = next(d / f for f in ("kokoro-v1.0.onnx", "kokoro-v1.0.int8.onnx") if (d / f).is_file())
            _kokoro = Kokoro(str(onnx), str(d / "voices-v1.0.bin"))
        return _kokoro


def speakable(text: str, guide: dict[str, str]) -> str:
    """The text the voice reads: pronunciation respellings applied as whole words."""
    out = text
    for word, say in sorted((guide or {}).items(), key=lambda kv: -len(kv[0])):
        out = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", say, out)
    return out


def _write(path: Path, samples, sr: int) -> None:
    import numpy as np
    a = (np.clip(np.asarray(samples, dtype="float32"), -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(a.tobytes())


def _trim(samples, sr: int, floor: float = 0.006, keep: float = 0.06):
    """Cuts the voice's own leading and trailing silence (the timeline adds measured pauses instead)."""
    import numpy as np
    a = np.asarray(samples, dtype="float32")
    loud = np.where(np.abs(a) > floor)[0]
    if not len(loud):
        return a
    k = int(keep * sr)
    return a[max(0, loud[0] - k): min(len(a), loud[-1] + k)]


def synth(text: str, out: Path, voice: str = "am_michael", speed: float = 1.0, lang: str = "en-us",
          guide: dict[str, str] | None = None) -> tuple[float, str]:
    """Speaks `text` into `out` (48 kHz mono). Returns (seconds, engine used)."""
    said = speakable(text, guide or {})
    out.parent.mkdir(parents=True, exist_ok=True)
    if kokoro_ready():
        k = _engine()
        samples, sr = k.create(said, voice=voice, speed=float(speed), lang=lang)
        tmp = out.with_suffix(".raw.wav")
        _write(tmp, _trim(samples, sr), sr)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(tmp), "-ar", str(SR), "-ac", "1", str(out)], check=True)
        tmp.unlink(missing_ok=True)
        engine = f"kokoro:{voice}"
    else:
        safe = said.replace("\\", " ").replace("'", "’").replace(":", ",").replace("%", " percent")
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"flite=text='{safe}':voice=slt",
                        "-ar", str(SR), "-ac", "1", str(out)], check=True)
        engine = "flite (robotic fallback)"
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate(), engine


def pauses_in(path: Path, min_gap: float = 0.18) -> list[tuple[float, float]]:
    """Silences inside a spoken line (start, length): where the voice breathes, for cutting beats on real audio."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(path), "-af", f"silencedetect=noise=-38dB:d={min_gap}", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=120).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
    return [(a, round(b - a, 3)) for a, b in zip(st, en)]


DELIVERY_SPEED = {"slow": 0.9, "measured": 0.94, "quiet": 0.95, "grave": 0.92, "warm": 0.97, "curious": 1.0,
                  "neutral": 1.0, "brisk": 1.05, "urgent": 1.08}


def speed_for(delivery: str) -> float:
    d = (delivery or "").lower()
    return next((v for k, v in DELIVERY_SPEED.items() if k in d), 1.0)
