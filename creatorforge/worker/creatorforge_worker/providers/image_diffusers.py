"""In-process Hugging Face diffusers pipeline. Default model FLUX.1-schnell (Apache-2.0,
4 steps). Requires a CUDA/MPS GPU in practice: pip install 'creatorforge-worker[diffusers]'."""
from __future__ import annotations

import threading
from pathlib import Path

from .base import cancelled, is_oom, place_on_gpu, step_callback, NotConfigured, ProviderError


class DiffusersImageProvider:
    _lock = threading.Lock()

    def __init__(self, model: str = "", steps: int = 0):
        self.model = model or "black-forest-labs/FLUX.1-schnell"
        m = self.model.lower()
        # SDXL with the DPM++ 2M Karras sampler looks as good at 25 steps as the default sampler at 30+.
        self.steps = steps or (4 if "schnell" in m else 25 if "xl" in m else 30)
        self.id = f"diffusers:{self.model}"
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
            image.save(out, format="PNG")
