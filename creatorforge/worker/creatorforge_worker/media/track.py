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


KEYS_CPU = 12          # on a CPU, BiRefNet runs on this many keyframes and optical flow carries the mask between them


def _birefnet_each(frames: list[Path]):
    import numpy as np
    from PIL import Image
    from . import cutouts
    path = cutouts.birefnet_model()
    if path is None:
        raise MediaError("tracking footage needs SAM 2 or BiRefNet on the worker")
    n = len(frames)
    if cutouts.birefnet_fast() or n <= KEYS_CPU:
        return [np.asarray(cutouts._birefnet(Image.open(f).convert("RGB"), path)) for f in frames]
    step = -(-n // KEYS_CPU)
    keys = sorted(set(range(0, n, step)) | {n - 1})
    key_masks = {i: np.asarray(cutouts._birefnet(Image.open(frames[i]).convert("RGB"), path)) for i in keys}
    return propagate(frames, key_masks)


def propagate(frames: list[Path], key_masks: dict) -> list:
    """Masks for every frame from masks on some of them: each in-between frame takes the previous keyframe's mask
    carried forward by dense optical flow (Farneback) and the next keyframe's carried back, blended by distance.
    Real motion only: the flow is measured between the real frames, nothing is drawn."""
    import cv2
    import numpy as np
    gray = [cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2GRAY) for f in frames]
    h, w = gray[0].shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))

    def carry(mask, a, b):                       # mask on frame a, warped to frame b (b = a ± 1)
        flow = cv2.calcOpticalFlowFarneback(gray[b], gray[a], None, 0.5, 3, 21, 3, 5, 1.1, 0)
        return cv2.remap(mask, gx + flow[..., 0], gy + flow[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    keys = sorted(key_masks)
    out = [None] * len(frames)
    for i in keys:
        m = np.asarray(key_masks[i], np.uint8)
        out[i] = cv2.resize(m, (w, h)) if m.shape != (h, w) else m
    for a, b in zip(keys, keys[1:]):
        fwd, bwd = {a: out[a].astype(np.float32)}, {b: out[b].astype(np.float32)}
        for i in range(a + 1, b):
            fwd[i] = carry(fwd[i - 1], i - 1, i)
        for i in range(b - 1, a, -1):
            bwd[i] = carry(bwd[i + 1], i + 1, i)
        for i in range(a + 1, b):
            wgt = (i - a) / (b - a)
            out[i] = np.clip(fwd[i] * (1 - wgt) + bwd[i] * wgt, 0, 255).astype(np.uint8)
    return out


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


def clean(mask):
    """A tidy matte from a raw one: stray specks and background leaks removed (only pieces at least a fifth the size of
    the largest stay), small holes closed, the edge feathered by a pixel or two. It only removes; it never adds subject."""
    import numpy as np
    try:
        import cv2
    except ImportError:
        return mask
    m = (np.asarray(mask, np.uint8) > 127).astype(np.uint8)
    if not m.any():
        return np.asarray(mask, np.uint8)
    k = max(3, (min(m.shape) // 90) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = [i + 1 for i, a in enumerate(areas) if a >= areas.max() * 0.2]
        m = np.isin(lab, keep).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k * 2 + 1, k * 2 + 1), np.uint8))
    return cv2.GaussianBlur(m * 255, (0, 0), max(0.8, k / 3))


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
        if BACKEND is None:
            m = clean(m)
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
