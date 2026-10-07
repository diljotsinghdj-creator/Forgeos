"""Image-to-video engines that turn each scene still into a moving clip.

- diffusers: in-process open models on the worker GPU. Default Wan 2.2 TI2V-5B (Apache-2.0, 720p,
  24 GB GPU); Wan-AI/Wan2.2-I2V-A14B-Diffusers for the highest realism (48-80 GB); LTX-Video works too.
- http: any server you run that implements POST {url}/v1/video/i2v
  (JSON: image_base64, prompt, seconds, width, height, seed -> raw MP4 bytes), e.g. a small
  wrapper around ComfyUI."""
from __future__ import annotations

import base64
import threading
from pathlib import Path

import httpx

from .base import cancelled, step_callback, NotConfigured, ProviderError


class HttpVideoProvider:
    def __init__(self, base_url: str, timeout: float = 1800):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.id = "http-i2v"

    def generate(self, image: Path, prompt: str, negative: str, seconds: float, width: int, height: int, seed: int,
                 out: Path) -> None:
        body = {"image_base64": base64.b64encode(image.read_bytes()).decode(), "prompt": prompt, "negative_prompt": negative,
                "seconds": round(seconds, 2), "width": width, "height": height, "seed": seed}
        try:
            r = httpx.post(f"{self.base_url}/v1/video/i2v", json=body, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise ProviderError(f"Video server unreachable at {self.base_url}: {e}") from e
        if r.status_code >= 400:
            raise ProviderError(f"Video server HTTP {r.status_code}: {r.text[:300]}")
        out.write_bytes(r.content)


# Per-model generation limits: (fps, frame step, max frames, max long side, guidance)
_PROFILES = {
    "wan2.2-ti2v-5b": (24, 4, 121, 1280, 5.0),   # 720p, fits a 24 GB GPU with CPU offload
    "wan2.2-i2v-a14b": (16, 4, 81, 1280, 3.5),   # highest realism; 48-80 GB GPU
    "wan": (16, 4, 81, 832, 5.0),
    "ltx": (24, 8, 161, 1216, 3.0),
}


def _profile(model: str) -> tuple[int, int, int, int, float]:
    m = model.lower()
    for key, prof in _PROFILES.items():
        if key in m:
            return prof
    return _PROFILES["ltx"]


class DiffusersVideoProvider:
    """Image-to-video on the worker GPU. Default: Wan 2.2 TI2V-5B (Apache-2.0)."""
    _lock = threading.Lock()

    def __init__(self, model: str = "", steps: int = 0):
        self.model = model or "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
        self.fps, self.step, self.max_frames, self.max_side, self.guidance = _profile(self.model)
        self.steps = steps or (40 if "wan" in self.model.lower() else 40)
        self.id = f"diffusers-i2v:{self.model}"
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            try:
                import torch
                import diffusers
            except ImportError as e:
                raise NotConfigured("diffusers backend not installed: pip install 'creatorforge-worker[diffusers]'") from e
            if not torch.cuda.is_available():
                raise NotConfigured("AI video clips need a CUDA GPU on the worker")
            cls = getattr(diffusers, "WanImageToVideoPipeline", None) if "wan" in self.model.lower() else None
            pipe = (cls or diffusers.DiffusionPipeline).from_pretrained(self.model, torch_dtype=torch.bfloat16)
            pipe.enable_model_cpu_offload()
            if hasattr(pipe, "vae") and hasattr(pipe.vae, "enable_tiling"):
                pipe.vae.enable_tiling()
            self._pipe = pipe
        return self._pipe

    def _size(self, width: int, height: int) -> tuple[int, int]:
        scale = min(1.0, self.max_side / max(width, height))
        return max(256, int(width * scale) // 32 * 32), max(256, int(height * scale) // 32 * 32)

    def generate(self, image: Path, prompt: str, negative: str, seconds: float, width: int, height: int, seed: int,
                 out: Path) -> None:
        import torch
        from diffusers.utils import export_to_video, load_image

        with self._lock:
            pipe = self._load()
            w, h = self._size(width, height)
            frames = int(min(seconds * self.fps, self.max_frames - 1)) // self.step * self.step + 1
            frames = max(self.step + 1, frames)
            kwargs = dict(image=load_image(str(image)).resize((w, h)), prompt=prompt, width=w, height=h,
                          num_frames=frames, num_inference_steps=self.steps, guidance_scale=self.guidance,
                          generator=torch.Generator("cpu").manual_seed(seed))
            if negative:
                kwargs["negative_prompt"] = negative
            kwargs.update(step_callback(pipe))
            try:
                result = pipe(**kwargs)
                if cancelled():
                    from ..media.ff import Cancelled
                    raise Cancelled()
                export_to_video(result.frames[0], str(out), fps=self.fps)
            except Exception as e:  # noqa: BLE001
                if type(e).__name__ == "Cancelled":
                    raise
                raise ProviderError(f"video generation failed: {e}") from e
