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

from .base import cancelled, is_oom, place_on_gpu, step_callback, NotConfigured, ProviderError


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


# Speed/quality presets (CF_VIDEO_QUALITY): (max long side, steps, max frames). Generation time grows with
# pixels x frames x steps, so "fast" is roughly 5x quicker than "best". Clips are upscaled to 1080p when the
# video is assembled, and Shorts are watched on phones, so "fast" (480p-class, Wan's native low size) looks fine.
QUALITY = {
    "fast": (832, 20, 81),
    "balanced": (1024, 30, 97),
    "best": (0, 40, 0),   # 0 = the model's own maximum
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

    def __init__(self, model: str = "", steps: int = 0, quality: str = "fast"):
        self.model = model or "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
        self.fps, self.step, self.max_frames, self.max_side, self.guidance = _profile(self.model)
        self._fixed_steps = steps
        self._model_limits = (self.max_side, self.max_frames)
        self.placement = ""
        self.set_quality(quality)

    def set_quality(self, quality: str) -> None:
        """Switches the speed preset for the next clips (same loaded model, no reload)."""
        self.quality = quality if quality in QUALITY else "fast"
        side, q_steps, frames = QUALITY[self.quality]
        self.max_side = min(self._model_limits[0], side) if side else self._model_limits[0]
        self.max_frames = min(self._model_limits[1], frames) if frames else self._model_limits[1]
        self.steps = self._fixed_steps or q_steps
        self.id = f"diffusers-i2v:{self.model}:{self.quality}"
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
            # Wan 2.2 5B needs ~24 GB with its text encoder; keep it all on the GPU when there's room.
            self.placement = place_on_gpu(pipe, keep_resident_gb=40)
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
                try:
                    result = pipe(**kwargs)
                except Exception as e:  # noqa: BLE001
                    if not (is_oom(e) and self.placement == "gpu"):
                        raise
                    pipe.to("cpu"); torch.cuda.empty_cache(); pipe.enable_model_cpu_offload(); self.placement = "offload"
                    result = pipe(**kwargs)
                if cancelled():
                    from ..media.ff import Cancelled
                    raise Cancelled()
                export_to_video(result.frames[0], str(out), fps=self.fps)
            except Exception as e:  # noqa: BLE001
                if type(e).__name__ == "Cancelled":
                    raise
                raise ProviderError(f"video generation failed: {e}") from e
