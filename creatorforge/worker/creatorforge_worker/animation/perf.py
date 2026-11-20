"""Performance benchmarks for the production renderer (run on an otherwise idle machine).

    python -m creatorforge_worker.animation.perf <out_dir>

Measures on the comedy production (6 scenes, ~72 s): a cold render with 1 and with 2 worker processes, a re-render
with nothing changed (cache), an incremental re-render after editing one scene, the cost of staging + QC alone, final
quality (1080p, 2x supersampling, motion blur) on one scene, and peak memory. Writes perf.json."""
from __future__ import annotations

import copy
import json
import resource
import shutil
import sys
import time
from pathlib import Path

from . import benchmarks as B
from . import production as P


def _peak_mb() -> dict:
    return {"self_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024,
            "children_mb": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024}


def run(out: Path) -> dict:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    doc = B.comedy()
    res = {"production": doc["title"], "scenes": len(doc["scenes"])}
    t = time.time()
    states = P.plan_states(doc, "preview")
    res["stage_and_qc_s"] = round(time.time() - t, 2)
    seconds = sum(s[2] for s in states)
    res["film_seconds"] = round(seconds, 1)
    for workers in (1, 2):
        cache = out / f"cache_w{workers}"
        shutil.rmtree(cache, ignore_errors=True)
        t = time.time()
        P.render(doc, out / f"w{workers}.mp4", "preview", workers=workers, cache_dir=cache)
        res[f"cold_preview_workers{workers}_s"] = round(time.time() - t, 1)
    res["preview_realtime_factor_w2"] = round(res["cold_preview_workers2_s"] / seconds, 2)
    t = time.time()
    r = P.render(doc, out / "w2.mp4", "preview", workers=2, cache_dir=out / "cache_w2")
    res["cached_rerender_s"] = round(time.time() - t, 1)
    res["cached_scenes"] = sum(1 for s in r["scenes"] if s["cached"])
    edited = copy.deepcopy(doc)                         # change one line of dialogue in scene 2
    edited["scenes"][1]["steps"][0]["lines"][0]["text"] = "You take it."
    t = time.time()
    r = P.render(edited, out / "w2_edit.mp4", "preview", workers=2, cache_dir=out / "cache_w2")
    res["incremental_one_scene_edit_s"] = round(time.time() - t, 1)
    res["rerendered_scenes_after_edit"] = [s["id"] for s in r["scenes"] if not s["cached"]]
    one = {"title": "final", "scenes": [doc["scenes"][0]]}
    t = time.time()
    r = P.render(one, out / "final_scene.mp4", "final", workers=1, cache_dir=out / "cache_final")
    secs = r["scenes"][0]["seconds"]
    res["final_1080p_scene_s"] = round(time.time() - t, 1)
    res["final_seconds_per_film_second"] = round(res["final_1080p_scene_s"] / secs, 1)
    res["final_delivery"] = r["delivery"]
    res["peak_memory"] = _peak_mb()
    (out / "perf.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1] if len(sys.argv) > 1 else "perf_out")), indent=1))
