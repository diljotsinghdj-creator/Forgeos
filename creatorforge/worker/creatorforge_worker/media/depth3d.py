"""3D camera moves into a still picture: Depth Anything V2 Small (Apache-2.0) estimates how far away every pixel is,
then the camera dollies into the picture - near things grow and slide faster than far things, the way a real camera
moving through a scene looks - instead of a flat zoom.

    depth = estimate(image)                       # 0 = far, 1 = near (cached next to the picture)
    render(image, depth, 5.0, out, 1920, 1080)    # an H.264 shot of the move

The warp runs on the GPU with torch when it can (a few seconds a shot), otherwise with numpy (slow: for tests and
short videos). CF_DEPTH3D=0 turns it off; the pipeline keeps its flat moves whenever anything here is missing."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from .ff import MediaError

MODEL = os.environ.get("CF_DEPTH_MODEL", "depth-anything/Depth-Anything-V2-Small-hf")
_pipe = None


def enabled() -> bool:
    if os.environ.get("CF_DEPTH3D", "1") == "0":
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def estimate(image: Path) -> np.ndarray:
    """Relative depth, 0 (far) .. 1 (near), at the picture's size. Cached as <image>.depth.png."""
    cache = image.with_suffix(image.suffix + ".depth.png")
    if cache.is_file():
        return np.asarray(Image.open(cache), dtype=np.float32) / 65535.0
    global _pipe
    if _pipe is None:
        import torch
        from transformers import pipeline
        _pipe = pipeline("depth-estimation", model=MODEL, device=0 if torch.cuda.is_available() else -1)
    pic = Image.open(image).convert("RGB")
    d = np.asarray(_pipe(pic)["depth"].resize(pic.size, Image.BICUBIC), dtype=np.float32)
    d = (d - d.min()) / max(1e-6, d.max() - d.min())          # Depth Anything: bigger = nearer
    Image.fromarray((d * 65535).astype(np.uint16)).save(cache)
    return d


def _smooth(d: np.ndarray, k: int = 9) -> np.ndarray:
    """A soft depth map (three box blurs, about a Gaussian): hard depth edges tear the picture when it moves."""
    out = d.astype(np.float32)
    for _ in range(3):
        for axis in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[axis] = (k, k)
            c = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis, dtype=np.float64)
            c = np.insert(c, 0, 0, axis=axis)
            n = out.shape[axis]
            out = ((np.take(c, range(2 * k + 1, 2 * k + 1 + n), axis=axis) - np.take(c, range(0, n), axis=axis))
                   / (2 * k + 1)).astype(np.float32)
    return out


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)


def _frame_maps(h: int, w: int, depth: np.ndarray, t: float, move: str, strength: float):
    """Where each output pixel samples the picture at time t (0..1): a dolly in plus a sideways drift, both scaled
    by nearness, so the foreground travels further than the background."""
    e = _ease(t)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    near = depth - 0.35                                         # the far background barely moves
    zoom = 1 + strength * e * (0.55 + near)                     # nearer -> bigger
    side = {"left": -1, "right": 1}.get(move, 0.35)
    dx = side * strength * 0.35 * w * e * near                  # nearer -> slides further
    sx = cx + (xs - cx) / zoom - dx
    sy = cy + (ys - cy) / zoom - strength * 0.05 * h * e * near
    return sx, sy


def _sample_np(img: np.ndarray, sx: np.ndarray, sy: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    sx, sy = np.clip(sx, 0, w - 1.001), np.clip(sy, 0, h - 1.001)
    x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy).astype(np.uint8)


def render(image: Path, depth: np.ndarray, seconds: float, out: Path, width: int, height: int, fps: int = 30,
           move: str = "push", strength: float = 0.14) -> Path:
    """The picture as a 3D camera move, cover-cropped to width x height. move: push | left | right."""
    pic = Image.open(image).convert("RGB")
    # cover-crop the picture and its depth to the frame (a little extra margin hides the edges as it moves)
    k = max(width / pic.width, height / pic.height) * 1.06
    pw, ph = int(pic.width * k + 0.5), int(pic.height * k + 0.5)
    pic = pic.resize((pw, ph), Image.LANCZOS)
    dimg = Image.fromarray(np.clip(depth, 0, 1).astype(np.float32), mode="F").resize((pw, ph), Image.BILINEAR)
    left, top = (pw - width) // 2, (ph - height) // 2
    img = np.asarray(pic.crop((left, top, left + width, top + height)))
    dep = _smooth(np.asarray(dimg.crop((left, top, left + width, top + height)), dtype=np.float32))
    frames = max(2, int(round(seconds * fps)))
    torch_ok = False
    try:
        import torch
        torch_ok = True
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        src = torch.from_numpy(img).to(dev).permute(2, 0, 1)[None].float()
    except ImportError:
        pass
    out.parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset",
                            "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    try:
        for i in range(frames):
            sx, sy = _frame_maps(height, width, dep, i / (frames - 1), move, strength)
            if torch_ok:
                g = torch.stack([torch.from_numpy(sx / (width - 1) * 2 - 1), torch.from_numpy(sy / (height - 1) * 2 - 1)],
                                -1)[None].to(src.device)
                f = torch.nn.functional.grid_sample(src, g, mode="bilinear", padding_mode="border", align_corners=True)
                frame = f[0].permute(1, 2, 0).clamp(0, 255).byte().cpu().numpy()
            else:
                frame = _sample_np(img, sx, sy)
            enc.stdin.write(np.ascontiguousarray(frame).tobytes())
        enc.stdin.close()
        if enc.wait(timeout=600) != 0:
            raise MediaError("depth3d: encode failed")
    except BaseException:
        enc.kill()
        raise
    return out
