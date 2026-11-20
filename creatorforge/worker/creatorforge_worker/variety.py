"""Every video different, no exception.

Each directed video leaves a fingerprint (its look, its hook, the order of its graphic kinds) in a small history on
the worker. A new video:
- takes a look none of the recent videos used (old stories pick between the period looks),
- is re-directed with another shot order while its sequence is too close to a recent video's,
- and, once rendered, is compared frame by frame with the previous finished video (palette and picture similarity);
  the result is written into the job's quality report.
"""
from __future__ import annotations

import json
import subprocess
import threading
from difflib import SequenceMatcher
from pathlib import Path

HISTORY_N = 40          # videos remembered
TOO_CLOSE = 0.72        # sequence similarity at or above this is a repeat
SAME_LOOK = 0.55        # finished videos whose frames score at or above this look alike
OLD_LOOKS = ("sepia", "engraving")
_lock = threading.Lock()


def _file(data_dir: Path) -> Path:
    return Path(data_dir) / "variety.json"


def load(data_dir: Path) -> list[dict]:
    try:
        h = json.loads(_file(data_dir).read_text(encoding="utf-8"))
        return h if isinstance(h, list) else []
    except (OSError, ValueError):
        return []


def remember(data_dir: Path, fp: dict) -> None:
    with _lock:
        h = [x for x in load(data_dir) if x.get("id") != fp.get("id")] + [fp]
        p = _file(data_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(h[-HISTORY_N:], ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)


def pick_look(script: str, era: int | None, history: list[dict]) -> str:
    """A look the recent videos didn't use: modern looks rotate through the five, old stories through the period
    looks. The script's own seed breaks ties, so the same script on an empty history gets the same look."""
    from .media import vox
    pool = list(OLD_LOOKS) if era is not None and era < 1950 else [k for k in vox.LOOKS if k not in OLD_LOOKS]
    recent = [x.get("look") for x in history[-(len(pool) - 1):]] if len(pool) > 1 else []
    start = vox._seed("look", script) % len(pool)
    order = pool[start:] + pool[:start]
    free = [k for k in order if k not in recent]
    if free:
        return free[0]
    # every look used recently: the one used longest ago
    last_use = {k: max((i for i, x in enumerate(history) if x.get("look") == k), default=-1) for k in pool}
    return min(order, key=lambda k: last_use[k])


def kinds(script: str) -> list[str]:
    from . import vox_director as vd
    return [vd.graphic_kind(b) or "-" for b in vd.blocks(script)[1]]


def layouts(ks: list[str], seed: int) -> list[str]:
    """The layout each graphic will get (the pipeline uses the same vox.plan_layouts)."""
    from .media import vox
    return [f"{k}:{lay}" if lay else k for k, lay in zip(ks, vox.plan_layouts(ks, seed))]


def fingerprint(script: str, look: str, job_id: str = "", seed: int = 0) -> dict:
    k = kinds(script)
    return {"id": job_id, "look": look, "hook": (layouts(k[:1], seed) or [""])[0], "kinds": k,
            "layouts": layouts(k, seed), "seed": seed}


def similarity(a: dict, b: dict) -> float:
    """0 (nothing alike) .. 1 (the same video): mostly the order of graphic kinds, then the look and the hook."""
    seq = SequenceMatcher(None, a.get("kinds") or [], b.get("kinds") or []).ratio()
    lay = SequenceMatcher(None, a.get("layouts") or [], b.get("layouts") or []).ratio()
    return round(.4 * seq + .2 * lay + .25 * (a.get("look") == b.get("look")) + .15 * (a.get("hook") == b.get("hook")), 3)


def closest(fp: dict, history: list[dict]) -> tuple[float, str]:
    best = (0.0, "")
    for h in history[-HISTORY_N:]:
        if h.get("id") and h.get("id") == fp.get("id"):
            continue
        s = similarity(fp, h)
        if s > best[0]:
            best = (s, h.get("id", ""))
    return best


class _Once:
    """The script AI answers once; re-directing with another shot order reuses its answer."""

    def __init__(self, llm):
        self.llm, self.id, self._ans = llm, getattr(llm, "id", "llm"), None

    def complete_json(self, system, user):
        if self._ans is None:
            self._ans = self.llm.complete_json(system, user)
        return self._ans


def direct_unique(script: str, llm, props: bool, look: str, history: list[dict], job_id: str = "",
                  tries: int = 8) -> tuple[str, list[str], dict, float]:
    """vox_director.ensure, re-run with other shot orders until the video doesn't repeat a recent one.
    Returns (script, report, fingerprint, similarity to the closest recent video)."""
    from . import vox_director as vd
    once = _Once(llm) if llm is not None else None
    best = None
    for t in range(tries):
        seed = (vd.script_seed(script) + t * 7919) or 1
        fixed, report = vd.ensure(script, once, props=props, seed=seed, spread=1.0 + t)   # wider each try
        fp = fingerprint(fixed, look, job_id, seed)
        sim, _ = closest(fp, history)
        if best is None or sim < best[3]:
            best = (fixed, report, fp, sim)
        if sim < TOO_CLOSE:
            break
    return best


# ---- the finished videos, compared ----------------------------------------------------------------------------------
def _frames(video: Path, n: int = 8, size: int = 32):
    import numpy as np
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    out = []
    for i in range(n):
        t = dur * (i + .5) / n
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                              "-vf", f"scale={size}:{size}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, timeout=60).stdout
        if len(raw) == size * size * 3:
            out.append(np.frombuffer(raw, np.uint8).reshape(size, size, 3).astype(np.float32))
    return out


def compare_videos(a: Path, b: Path) -> dict:
    """How alike two finished videos look: palette (the colours they're made of) and pictures (each frame against
    its best match in the other video). 0..1 each; `same_look` when their blend reaches SAME_LOOK."""
    import numpy as np
    fa, fb = _frames(Path(a)), _frames(Path(b))
    if not fa or not fb:
        return {"palette": None, "pictures": None, "same_look": None}

    def hist(fs):
        h = np.zeros(64)
        for f in fs:
            q = (f // 64).astype(int)
            np.add.at(h, q[..., 0] * 16 + q[..., 1] * 4 + q[..., 2], 1)
        return h / h.sum()

    palette = float(np.minimum(hist(fa), hist(fb)).sum())

    def dhash(f):
        g = f.mean(axis=2)
        return (g[:, 1:] > g[:, :-1]).flatten()

    ha, hb = [dhash(f) for f in fa], [dhash(f) for f in fb]
    pictures = float(np.mean([max(1 - np.mean(x != y) for y in hb) for x in ha]))
    pictures = max(0.0, (pictures - .5) * 2)        # two unrelated frames already agree on about half the bits
    score = .6 * palette + .4 * pictures
    # calibrated on the two samples that looked "too similar" (shipping and Panama, same look: 0.59)
    return {"palette": round(palette, 3), "pictures": round(pictures, 3), "score": round(score, 3),
            "same_look": bool(score >= SAME_LOOK)}
