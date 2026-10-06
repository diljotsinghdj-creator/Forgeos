"""Narration engines that need no paid credits: Piper (CPU, fast) and Kokoro (Apache-2.0)."""
from __future__ import annotations

import shutil
import subprocess
import threading
import wave
from pathlib import Path

from .base import NotConfigured, ProviderError


class PiperVoice:
    def __init__(self, model_path: str, speed: float = 1.0):
        self.model_path = model_path
        self.speed = speed
        self.id = f"piper:{Path(model_path).name}"

    def synthesize(self, text: str, out_wav: Path) -> None:
        exe = shutil.which("piper")
        if not exe:
            raise NotConfigured("piper executable not found on PATH")
        if not Path(self.model_path).is_file():
            raise NotConfigured(f"Piper voice model missing: {self.model_path}")
        cmd = [exe, "--model", self.model_path, "--output_file", str(out_wav),
               "--length_scale", f"{1.0 / max(self.speed, 0.1):.3f}"]
        p = subprocess.run(cmd, input=text.encode(), capture_output=True, timeout=600)
        if p.returncode != 0:
            raise ProviderError(f"piper failed: {p.stderr.decode(errors='replace')[-300:]}")


class KokoroVoice:
    _pipes: dict[str, object] = {}
    _lock = threading.Lock()

    def __init__(self, voice: str, speed: float = 1.0, lang: str = "a"):
        self.voice = voice
        self.speed = speed
        self.lang = lang
        self.id = f"kokoro:{voice}"

    def synthesize(self, text: str, out_wav: Path) -> None:
        try:
            import numpy as np
            from kokoro import KPipeline
        except ImportError as e:
            raise NotConfigured("kokoro not installed: pip install 'creatorforge-worker[kokoro]'") from e
        with self._lock:
            pipe = self._pipes.get(self.lang) or KPipeline(lang_code=self.lang)
            self._pipes[self.lang] = pipe
            chunks = [audio for _, _, audio in pipe(text, voice=self.voice, speed=self.speed)]
        if not chunks:
            raise ProviderError("kokoro produced no audio")
        audio = np.concatenate([np.asarray(c, dtype="float32") for c in chunks])
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(pcm)
