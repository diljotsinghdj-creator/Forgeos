"""Filling the area behind a cut-out subject, so a 2.5D camera move never opens a hole.

Backends, best first:
    lama     LaMa (big-lama, Apache-2.0) as TorchScript: fills large areas with plausible texture that matches the
             surroundings; needs PyTorch (the pod) and big-lama.pt (CF_LAMA, else <data>/models/big-lama.pt;
             setup downloads it from the Sanster/models GitHub release).
    opencv   OpenCV Telea: fine for thin edges, smudges large areas.
The fill is never shown as evidence: it only sits behind a nearer layer, and the photo module records it in the
asset's modification history.
"""
from __future__ import annotations

import os
from pathlib import Path

_LAMA: dict = {}


def lama_model() -> Path | None:
    p = Path(os.environ.get("CF_LAMA") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "models" / "big-lama.pt")
    return p if p.is_file() else None


def lama_ready() -> bool:
    try:
        import torch  # noqa: F401
    except ImportError:
        return False
    return lama_model() is not None


def _lama(rgb, mask):
    """rgb: HxWx3 uint8, mask: HxW uint8 (255 = fill). Returns HxWx3 uint8."""
    import numpy as np
    import torch
    key = str(lama_model())
    if key not in _LAMA:
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        _LAMA[key] = (torch.jit.load(key, map_location=dev).eval(), dev)
    net, dev = _LAMA[key]
    h, w = mask.shape
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8                # the model works on multiples of 8
    img = np.pad(rgb, ((0, ph), (0, pw), (0, 0)), mode="reflect").astype("float32") / 255.0
    m = (np.pad(mask, ((0, ph), (0, pw)), mode="reflect") > 127).astype("float32")
    with torch.no_grad():
        ti = torch.from_numpy(img.transpose(2, 0, 1))[None].to(dev)
        tm = torch.from_numpy(m)[None, None].to(dev)
        out = net(ti, tm)[0].permute(1, 2, 0).cpu().numpy()
    return (np.clip(out, 0, 1) * 255).astype("uint8")[:h, :w]


def fill(rgb, mask) -> tuple[object, str]:
    """(filled image as HxWx3 uint8, which backend did it)."""
    import numpy as np
    if lama_ready():
        try:
            return _lama(np.asarray(rgb, np.uint8), np.asarray(mask, np.uint8)), "LaMa inpainting"
        except Exception:  # noqa: BLE001 - the OpenCV fill below still works
            pass
    import cv2
    a = np.asarray(rgb, np.uint8)
    small = cv2.resize(a, (a.shape[1] // 2, a.shape[0] // 2))
    hs = cv2.resize(np.asarray(mask, np.uint8), (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    return cv2.resize(cv2.inpaint(small, hs, 7, cv2.INPAINT_TELEA), (a.shape[1], a.shape[0])), "OpenCV inpainting"
