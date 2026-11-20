"""Background music generation (optional; a local track library works without any model).

- stable-audio: Stable Audio Open via diffusers on the worker GPU (up to ~47s per call; longer
  videos loop the bed). Check the model licence for your use.
- http: your own server at POST {url}/v1/music/generate (JSON: prompt, seconds) -> audio bytes."""
from __future__ import annotations

import threading
import wave
from pathlib import Path

import httpx

from .base import NotConfigured, ProviderError


class HttpMusicProvider:
    max_seconds = 300.0

    def __init__(self, base_url: str, timeout: float = 1200):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.id = "http-music"

    def generate(self, prompt: str, seconds: float, seed: int, out: Path) -> None:
        try:
            r = httpx.post(f"{self.base_url}/v1/music/generate", json={"prompt": prompt, "seconds": round(seconds, 1),
                                                                        "seed": seed}, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise ProviderError(f"Music server unreachable at {self.base_url}: {e}") from e
        if r.status_code >= 400:
            raise ProviderError(f"Music server HTTP {r.status_code}: {r.text[:300]}")
        out.write_bytes(r.content)


class StableAudioProvider:
    max_seconds = 47.0
    _lock = threading.Lock()

    def __init__(self, model: str = ""):
        self.model = model or "stabilityai/stable-audio-open-1.0"
        self.id = f"stable-audio:{self.model}"
        self._pipe = None

    def generate(self, prompt: str, seconds: float, seed: int, out: Path) -> None:
        try:
            import numpy as np
            import torch
            from diffusers import StableAudioPipeline
        except ImportError as e:
            raise NotConfigured("diffusers backend not installed: pip install 'creatorforge-worker[diffusers]'") from e
        with self._lock:
            if self._pipe is None:
                if not torch.cuda.is_available():
                    raise NotConfigured("Stable Audio needs a CUDA GPU on the worker")
                self._pipe = StableAudioPipeline.from_pretrained(self.model, torch_dtype=torch.float16).to("cuda")
            try:
                audio = self._pipe(prompt, negative_prompt="vocals, singing, speech, low quality", num_inference_steps=100,
                                   audio_end_in_s=min(seconds, self.max_seconds),
                                   generator=torch.Generator("cuda").manual_seed(seed)).audios[0]
            except Exception as e:  # noqa: BLE001
                raise ProviderError(f"music generation failed: {e}") from e
        data = audio.T.float().cpu().numpy()  # (samples, channels)
        pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
        with wave.open(str(out), "wb") as w:
            w.setnchannels(pcm.shape[1])
            w.setsampwidth(2)
            w.setframerate(self._pipe.vae.sampling_rate)
            w.writeframes(pcm.tobytes())
