"""Following a subject through footage: a mask for every frame (rotoscoping), its centre and its box.

    track(frames, box) -> [{"mask": path, "cx", "cy", "box": [x0, y0, x1, y1]} per frame]    (fractions of the frame)

Backends, best first:
    sam2      SAM 2 (Segment Anything 2, Apache-2.0) video predictor: one box on the first frame, a temporally
              consistent mask on every frame. Needs PyTorch, the `sam2` package and a checkpoint (CF_SAM2, else
              <data>/models/sam2.1_hiera_small.pt with the matching config); setup installs them on the pod.
    birefnet  BiRefNet on each frame (no tracking between frames: slower and may flicker on busy footage).
The box comes from the shot's line (`subject: x, y, w, h`), else from the subject BiRefNet finds on the first frame.
Used by Footage shots for `cutout` (the subject cut out of the footage onto the paper) and `follow` (a marker that
stays on the subject).
"""
from __future__ import annotations

import os
from pathlib import Path

from .ff import MediaError

CONFIGS = {"tiny": "configs/sam2.1/sam2.1_hiera_t.yaml", "small": "configs/sam2.1/sam2.1_hiera_s.yaml",
           "base_plus": "configs/sam2.1/sam2.1_hiera_b+.yaml", "large": "configs/sam2.1/sam2.1_hiera_l.yaml"}
_PRED: dict = {}
BACKEND = None          # tests set a callable(frames, box) -> list of HxW uint8 masks


def checkpoint() -> Path | None:
    p = Path(os.environ.get("CF_SAM2") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "models" / "sam2.1_hiera_small.pt")
    return p if p.is_file() else None


def sam2_ready() -> bool:
    try:
        import sam2  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        return False
    return checkpoint() is not None


def _sam2(frames: list[Path], box_px: list[float]):
    import numpy as np
    import torch
    from sam2.build_sam import build_sam2_video_predictor
    ck = checkpoint()
    size = next((k for k in CONFIGS if k in ck.name.replace("+", "_plus")), "small")
    key = str(ck)
    if key not in _PRED:
        _PRED[key] = build_sam2_video_predictor(CONFIGS[size], str(ck), device="cuda" if torch.cuda.is_available() else "cpu")
    pred = _PRED[key]
    with torch.inference_mode():
        state = pred.init_state(video_path=str(frames[0].parent))
        pred.add_new_points_or_box(state, frame_idx=0, obj_id=1, box=np.array(box_px, np.float32))
        out = {}
        for idx, _, logits in pred.propagate_in_video(state):
            out[idx] = ((logits[0, 0] > 0).cpu().numpy() * 255).astype("uint8")
    return [out.get(i) for i in range(len(frames))]


def _birefnet_each(frames: list[Path]):
    import numpy as np
    from PIL import Image
    from . import cutouts
    path = cutouts.birefnet_model()
    if path is None:
        raise MediaError("tracking footage needs SAM 2 or BiRefNet on the worker")
    return [np.asarray(cutouts._birefnet(Image.open(f).convert("RGB"), path)) for f in frames]


def first_box(frame: Path) -> list[float] | None:
    """The subject's box on a frame, from BiRefNet (fractions)."""
    import numpy as np
    from PIL import Image
    from . import cutouts
    path = cutouts.birefnet_model()
    if path is None:
        return None
    m = np.asarray(cutouts._birefnet(Image.open(frame).convert("RGB"), path)) > 127
    if m.mean() < 0.005:
        return None
    ys, xs = np.nonzero(m)
    h, w = m.shape
    return [xs.min() / w, ys.min() / h, (xs.max() - xs.min()) / w, (ys.max() - ys.min()) / h]


def track(frames: list[Path], box: list[float] | None, out_dir: Path) -> tuple[list[dict], str]:
    """Masks and positions for every frame, and how they were made."""
    import numpy as np
    from PIL import Image
    if not frames:
        raise MediaError("track: no frames")
    w, h = Image.open(frames[0]).size
    box = box or first_box(frames[0])
    if BACKEND is not None:
        masks, how = BACKEND(frames, box), "test tracker"
    elif sam2_ready() and box:
        masks, how = _sam2(frames, [box[0] * w, box[1] * h, (box[0] + box[2]) * w, (box[1] + box[3]) * h]), "SAM 2 video tracking"
    else:
        masks, how = _birefnet_each(frames), "BiRefNet on each frame (no tracking)"
    out_dir.mkdir(parents=True, exist_ok=True)
    res, last = [], None
    for i, m in enumerate(masks):
        if m is None:
            m = last if last is not None else np.zeros((h, w), np.uint8)
        m = np.asarray(Image.fromarray(np.asarray(m, np.uint8)).resize((w, h)), np.uint8)
        last = m
        p = out_dir / f"m_{i:05d}.png"
        Image.fromarray(m).save(p)
        ys, xs = np.nonzero(m > 127)
        if len(xs):
            res.append({"mask": p, "cx": float(xs.mean() / w), "cy": float(ys.mean() / h),
                        "box": [float(xs.min() / w), float(ys.min() / h), float(xs.max() / w), float(ys.max() / h)]})
        else:
            res.append({"mask": p, "cx": res[-1]["cx"] if res else .5, "cy": res[-1]["cy"] if res else .5,
                        "box": res[-1]["box"] if res else [.4, .4, .6, .6]})
    return res, how
