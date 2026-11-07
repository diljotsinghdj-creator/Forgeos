"""Stable Diffusion WebUI API (AUTOMATIC1111 / Forge / SD.Next): POST /sdapi/v1/txt2img.
Forge can serve FLUX and SDXL checkpoints through the same API."""
from __future__ import annotations

import base64
from pathlib import Path

import httpx

from .base import ProviderError


class A1111ImageProvider:
    def __init__(self, base_url: str, steps: int = 0, timeout: float = 900):
        self.base_url = base_url.rstrip("/")
        self.steps = steps or 25
        self.timeout = timeout
        self.id = "a1111"

    def generate(self, prompt: str, negative: str, width: int, height: int, seed: int, out: Path) -> None:
        body = {
            "prompt": prompt,
            "negative_prompt": negative,
            "width": width,
            "height": height,
            "steps": self.steps,
            "seed": seed,
            "batch_size": 1,
            "n_iter": 1,
        }
        try:
            r = httpx.post(f"{self.base_url}/sdapi/v1/txt2img", json=body, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise ProviderError(f"Image server unreachable at {self.base_url}: {e}") from e
        if r.status_code >= 400:
            raise ProviderError(f"Image server HTTP {r.status_code}: {r.text[:300]}")
        try:
            data = base64.b64decode(r.json()["images"][0].split(",", 1)[-1])
        except (KeyError, IndexError, ValueError) as e:
            raise ProviderError("Image server returned no image") from e
        out.write_bytes(data)
