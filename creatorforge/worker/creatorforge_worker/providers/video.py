"""Image-to-video engines that turn each scene still into a moving clip.

- diffusers: in-process open models (default Lightricks/LTX-Video; Wan 2.x I2V also works).
  Needs a CUDA GPU in practice.
- http: any server you run that implements POST {url}/v1/video/i2v
  (JSON: image_base64, prompt, seconds, width, height, seed -> raw MP4 bytes), e.g. a small
  wrapper around ComfyUI."""
from __future__ import annotations

import base64
import threading
from pathlib import Path

import httpx

from .base import NotConfigured, ProviderError


class HttpVideoProvider:
    def __init__(self, base_url: str, timeout: float = 1800):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.id = "http-i2v"

    def generate(self, image: Path, prompt: str, seconds: float, width: int, height: int, seed: int, out: Path) -> None:
        body = {"image_base64": base64.b64encode(image.read_bytes()).decode(), "prompt": prompt,
                "seconds": round(seconds, 2), "width": width, "height": height, "seed": seed}
        try:
            r = httpx.post(f"{self.base_url}/v1/video/i2v", json=body, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise ProviderError(f"Video server unreachable at {self.base_url}: {e}") from e
        if r.status_code >= 400:
            raise ProviderError(f"Video server HTTP {r.status_code}: {r.text[:300]}")
        out.write_bytes(r.content)


class DiffusersVideoProvider:
    _lock = threading.Lock()

    def __init__(self, model: str = "", steps: int = 0):
        self.model = model or "Lightricks/LTX-Video"
        self.steps = steps or 40
        self.id = f"diffusers-i2v:{self.model}"
        self._pipe = None
        self._fps = 24

    def _load(self):
        if self._pipe is None:
            try:
                import torch
                from diffusers import DiffusionPipeline
            except ImportError as e:
                raise NotConfigured("diffusers backend not installed: pip install 'creatorforge-worker[diffusers]'") from e
            if not torch.cuda.is_available():
                raise NotConfigured("AI video clips need a CUDA GPU on the worker")
            pipe = DiffusionPipeline.from_pretrained(self.model, torch_dtype=torch.bfloat16)
            pipe.enable_model_cpu_offload()
            if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()
            self._fps = 16 if "wan" in self.model.lower() else 24
            self._pipe = pipe
        return self._pipe

    def generate(self, image: Path, prompt: str, seconds: float, width: int, height: int, seed: int, out: Path) -> None:
        import torch
        from diffusers.utils import export_to_video, load_image

        with self._lock:
            pipe = self._load()
            # Video models need dimensions divisible by 32 and a frame count of 8k+1 (LTX) / 4k+1 (Wan).
            w, h = max(256, width // 32 * 32), max(256, height // 32 * 32)
            step = 4 if "wan" in self.model.lower() else 8
            frames = max(step + 1, int(seconds * self._fps) // step * step + 1)
            try:
                result = pipe(image=load_image(str(image)).resize((w, h)), prompt=prompt, width=w, height=h,
                              num_frames=frames, num_inference_steps=self.steps,
                              generator=torch.Generator("cpu").manual_seed(seed))
                export_to_video(result.frames[0], str(out), fps=self._fps)
            except Exception as e:  # noqa: BLE001
                raise ProviderError(f"video generation failed: {e}") from e
