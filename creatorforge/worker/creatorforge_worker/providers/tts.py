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


REF_TEXT = ("Long before the first cities rose, people gathered around fires and told stories. "
            "Some were warnings, some were dreams, and a few were simply too strange to forget. "
            "Tonight, we follow one of them, from the very beginning.")


class ChatterboxVoice:
    """Human-sounding narration via the local Chatterbox server (see chatterbox_server.py).

    voice: "default" (Chatterbox's own voice), "kokoro:<id>" (a Kokoro voice used as the timbre, spoken with
    Chatterbox's natural rhythm), "asset:<id>" (a voice sample the creator uploaded - their own voice, or one
    they have permission to use) or a path to a WAV on the worker.
    style: delivery preset - documentary (slow, deep, deliberate), natural, calm, energetic."""
    STYLES = {"documentary": (0.35, 0.25), "natural": (0.5, 0.5), "calm": (0.3, 0.4), "energetic": (0.8, 0.45)}
    _ref_lock = threading.Lock()

    def __init__(self, voice: str, style: str = "natural", data_dir: Path | None = None, url: str = "http://127.0.0.1:8770"):
        self.voice = voice or "default"
        self.style = style if style in self.STYLES else "natural"
        self.data_dir = Path(data_dir or ".")
        self.url = url.rstrip("/")
        self.mood = ""   # set per scene by the pipeline: the emotion of the line being spoken
        self.id = f"chatterbox:{self.voice}:{self.style}"

    def reference(self) -> str:
        v = self.voice
        if v == "default":
            return ""
        if v.startswith("kokoro:"):
            vid = v.split(":", 1)[1]
            ref = self.data_dir / "voice_refs" / f"kokoro_{vid}.wav"
            with self._ref_lock:
                if not ref.is_file():
                    ref.parent.mkdir(parents=True, exist_ok=True)
                    tmp = ref.with_suffix(".tmp.wav")
                    KokoroVoice(vid, 0.95, vid[0] if vid[:1] in tuple("abefhijpz") else "a").synthesize(REF_TEXT, tmp)
                    tmp.replace(ref)
            return str(ref)
        if v.startswith("asset:"):
            aid = v.split(":", 1)[1]
            hits = sorted((self.data_dir / "library" / "assets" / "files").glob(f"{aid}.*"))
            if not hits:
                raise NotConfigured("This voice's sample was deleted from the Asset Library - upload it again")
            # Phone recordings are usually m4a/mp3: hand Chatterbox a clean mono WAV (max 30 s) instead.
            ref = self.data_dir / "voice_refs" / f"asset_{aid}.wav"
            with self._ref_lock:
                if not ref.is_file():
                    ref.parent.mkdir(parents=True, exist_ok=True)
                    tmp = ref.with_suffix(".tmp.wav")
                    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(hits[0]), "-t", "30",
                                        "-ac", "1", "-ar", "24000", str(tmp)], capture_output=True, timeout=120)
                    if p.returncode != 0:
                        raise ProviderError(f"couldn't read the voice sample: {p.stderr.decode(errors='replace')[-200:]}")
                    tmp.replace(ref)
            return str(ref)
        if Path(v).is_file():
            return v
        raise NotConfigured(f"Chatterbox voice not found: {v}")

    def synthesize(self, text: str, out_wav: Path) -> None:
        import httpx

        ex, cw = self.STYLES[self.style]
        m = (self.mood or "").lower()
        if any(w in m for w in ("shock", "fear", "terror", "horror", "tension", "suspense", "intrigue", "anger", "disgust")):
            ex, cw = min(1.0, ex + 0.25), max(0.2, cw - 0.1)     # sharper, more urgent delivery
        elif any(w in m for w in ("calm", "resolve", "relief", "warm", "curiosity")):
            ex = max(0.25, ex - 0.1)                              # settle the voice for set-up and takeaways
        body = {"text": text, "out": str(Path(out_wav).resolve()), "ref": self.reference(), "exaggeration": ex, "cfg_weight": cw}
        try:
            r = httpx.post(f"{self.url}/tts", json=body, timeout=1800)
        except httpx.HTTPError as e:
            raise NotConfigured("The human-like voice engine (Chatterbox) isn't running yet - it installs in the "
                                "background a few minutes after the pod starts. Pick another voice or try again soon.") from e
        if r.status_code >= 400:
            raise ProviderError(f"chatterbox: {r.text[:300]}")
        if not Path(out_wav).is_file():
            raise ProviderError("chatterbox produced no audio")
