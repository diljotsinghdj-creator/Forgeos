"""In-process Hugging Face diffusers pipeline. Default model FLUX.1-schnell (Apache-2.0,
4 steps). Requires a CUDA/MPS GPU in practice: pip install 'creatorforge-worker[diffusers]'."""
from __future__ import annotations

import threading
from pathlib import Path

from .base import cancelled, is_oom, place_on_gpu, step_callback, NotConfigured, ProviderError


class DiffusersImageProvider:
    _lock = threading.Lock()

    def __init__(self, model: str = "", steps: int = 0, hires: bool = True):
        self.model = model or "black-forest-labs/FLUX.1-schnell"
        m = self.model.lower()
        # SDXL with the DPM++ 2M Karras sampler looks as good at 25 steps as the default sampler at 30+.
        self.steps = steps or (4 if "schnell" in m else 25 if "xl" in m else 30)
        # Hi-res pass (SDXL family): re-render the image at 1.5x with light img2img. Fixes soft, smeared faces and
        # gives the 1080p render real detail instead of an upscale. FLUX is already sharp, so it's skipped there.
        self.hires = hires and "xl" in m and "schnell" not in m
        self.id = f"diffusers:{self.model}" + (":hires" if self.hires else "")
        self._img2img = None
        self._pipe = None

    def _load(self):
        if self._pipe is None:
            try:
                import torch
                from diffusers import AutoPipelineForText2Image
            except ImportError as e:
                raise NotConfigured("diffusers backend not installed: pip install 'creatorforge-worker[diffusers]'") from e
            device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
            dtype = torch.bfloat16 if device == "cuda" else torch.float32
            pipe = AutoPipelineForText2Image.from_pretrained(self.model, torch_dtype=dtype)
            if "xl" in self.model.lower() and "schnell" not in self.model.lower():
                from diffusers import DPMSolverMultistepScheduler
                pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
            if device == "cuda":
                self.placement = place_on_gpu(pipe, keep_resident_gb=20)   # SDXL ~7 GB, FLUX ~24 GB in bf16
            else:
                pipe = pipe.to(device)
            self._pipe = pipe
        return self._pipe

    def generate(self, prompt: str, negative: str, width: int, height: int, seed: int, out: Path) -> None:
        import torch

        with self._lock:
            pipe = self._load()
            kwargs = dict(prompt=prompt, width=width, height=height, num_inference_steps=self.steps,
                          generator=torch.Generator("cpu").manual_seed(seed))
            if "schnell" in self.model.lower():
                kwargs["guidance_scale"] = 0.0
            elif negative:
                kwargs["negative_prompt"] = negative
            kwargs.update(step_callback(pipe))
            try:
                try:
                    image = pipe(**kwargs).images[0]
                except Exception as e:  # noqa: BLE001
                    if not (is_oom(e) and getattr(self, "placement", "") == "gpu"):
                        raise
                    # Another model is holding GPU memory: fall back to streaming from RAM and try once more.
                    import torch
                    pipe.to("cpu"); torch.cuda.empty_cache(); pipe.enable_model_cpu_offload(); self.placement = "offload"
                    image = pipe(**kwargs).images[0]
            except Exception as e:  # noqa: BLE001 - surface any backend failure
                raise ProviderError(f"diffusers generation failed: {e}") from e
            if cancelled():
                from ..media.ff import Cancelled
                raise Cancelled()
            if self.hires:
                image = self._refine(pipe, image, prompt, negative, width, height, seed)
            image.save(out, format="PNG")

    def _refine(self, pipe, image, prompt: str, negative: str, width: int, height: int, seed: int):
        import torch
        from PIL import Image

        try:
            if self._img2img is None:
                from diffusers import AutoPipelineForImage2Image
                self._img2img = AutoPipelineForImage2Image.from_pipe(pipe)   # shares the loaded weights
            w, h = int(width * 1.5) // 8 * 8, int(height * 1.5) // 8 * 8
            kwargs = dict(prompt=prompt, image=image.resize((w, h), Image.LANCZOS), strength=0.3,
                          num_inference_steps=max(20, self.steps), generator=torch.Generator("cpu").manual_seed(seed))
            if negative:
                kwargs["negative_prompt"] = negative
            kwargs.update(step_callback(self._img2img))
            return self._img2img(**kwargs).images[0]
        except Exception as e:  # noqa: BLE001 - the base image is still good; never fail a scene over the extra pass
            if is_oom(e):
                torch.cuda.empty_cache()
            return image
