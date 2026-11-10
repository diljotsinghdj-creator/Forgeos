"""Pod self-test: checks every tool the studio can use and says, for each, whether it works here.

    python -m creatorforge_worker.selftest [--network] [--json report.json]

Without --network only local things are checked (installed packages, model files, the browser, FFmpeg). With it,
one small request goes to each online service that has a key: NASA GIBS (no key), Sentinel Hub, Freesound,
ElevenLabs (voices list only), Pixabay. Key values are never printed or written: only whether a key is set.
Each line is one of: works, missing (not installed / no key / no model), failed (installed but did not work).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _row(name: str, status: str, detail: str = "") -> dict:
    return {"tool": name, "status": status, "detail": detail[:200]}


def _try(name: str, fn) -> dict:
    try:
        res = fn()
        if isinstance(res, dict):
            return res
        return _row(name, "works" if res else "missing", "" if res else "not available")
    except Exception as e:  # noqa: BLE001 - a self-test reports every failure, it never stops
        return _row(name, "failed", f"{type(e).__name__}: {e}")


def local_checks() -> list[dict]:
    from .media import cutouts, depth3d, inpaint, motion, stems, track
    from .studio import score, voice
    rows = [
        _try("FFmpeg", lambda: _row("FFmpeg", "works" if shutil.which("ffmpeg") else "missing")),
        _try("Chromium animation engine", lambda: _row("Chromium animation engine", "works" if motion.enabled() else "missing",
                                                         "" if motion.enabled() else "Playwright / Chromium not found")),
        _try("BiRefNet cut-outs", lambda: _row("BiRefNet cut-outs", "works" if cutouts.birefnet_model() else "missing",
                                                 str(cutouts.birefnet_model() or "no birefnet*.onnx in <data>/models"))),
        _try("LaMa fill", lambda: _row("LaMa fill", "works" if inpaint.lama_ready() else "missing",
                                         "" if inpaint.lama_ready() else "needs torch and <data>/models/big-lama.pt (OpenCV is used meanwhile)")),
        _try("SAM 2 tracking", lambda: _row("SAM 2 tracking", "works" if track.sam2_ready() else "missing",
                                              "" if track.sam2_ready() else "needs the sam2 package and sam2.1_hiera_small.pt (BiRefNet per frame meanwhile)")),
        _try("Depth Anything V2", lambda: _row("Depth Anything V2", "works" if depth3d.enabled() else "missing")),
        _try("Kokoro voice", lambda: _row("Kokoro voice", "works" if voice.kokoro_ready() else "missing")),
        _try("ElevenLabs key", lambda: _row("ElevenLabs key", "works" if os.environ.get("ELEVENLABS_API_KEY") else "missing",
                                              "set" if os.environ.get("ELEVENLABS_API_KEY") else "ELEVENLABS_API_KEY not set")),
        _try("Demucs stems", lambda: _row("Demucs stems", "works" if stems.ready() else "missing")),
        _try("ACE-Step composer", lambda: _row("ACE-Step composer", "works" if score.ace_ready() else "missing",
                                                 "" if score.ace_ready() else "needs the acestep package and CF_ACESTEP=1")),
    ]
    try:
        import pyloudnorm  # noqa: F401
        rows.append(_row("pyloudnorm loudness", "works"))
    except ImportError:
        rows.append(_row("pyloudnorm loudness", "missing"))
    for name, var in (("Freesound key", ("FREESOUND_KEY", "CF_FREESOUND_KEY")), ("Pixabay key", ("PIXABAY_KEY",)),
                      ("Unsplash key", ("UNSPLASH_KEY",)), ("Pexels key", ("PEXELS_KEY",)),
                      ("Sentinel Hub keys", ("CF_CDSE_CLIENT_ID", "SH_CLIENT_ID")), ("Search key", ("CF_BRAVE_KEY", "CF_TAVILY_KEY"))):
        ok = any(os.environ.get(v) for v in var)
        rows.append(_row(name, "works" if ok else "missing", "set" if ok else f"{' or '.join(var)} not set"))
    return rows


def network_checks(work: Path) -> list[dict]:
    rows = []

    def gibs():
        from .media import satellite
        plan = satellite.parse("bbox: 58,43,62,47 | 2020-08-01 vs 2020-08-05")
        shots = satellite.fetch(plan, work / "sat", 256)
        return _row("NASA GIBS imagery", "works", f"{len(shots)} pictures, {shots[0]['credit']}")
    rows.append(_try("NASA GIBS imagery", gibs))

    def freesound():
        from .providers import freesound as fs
        if not fs.key():
            return _row("Freesound search", "missing", "no key")
        return _row("Freesound search", "works", f"{len(fs.search('whoosh', fs.key(), n=2))} results")
    rows.append(_try("Freesound search", freesound))

    def eleven():
        if not os.environ.get("ELEVENLABS_API_KEY"):
            return _row("ElevenLabs reachable", "missing", "no key")
        import urllib.request
        req = urllib.request.Request("https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]})
        with urllib.request.urlopen(req, timeout=20) as r:      # noqa: S310
            n = len(json.loads(r.read()).get("voices", []))
        return _row("ElevenLabs reachable", "works", f"{n} voices on the account")
    rows.append(_try("ElevenLabs reachable", eleven))
    return rows


def render_check(work: Path) -> dict:
    from .media import motion, vox
    if not motion.enabled():
        return _row("Scene render", "missing", "no animation engine")
    out = vox.render("myth", "A test line | The engine draws | TEST", "e~0@red/field/", 480, 270, 2.0, work / "selftest.mp4",
                     work, fetch=False, fps=8)
    return _row("Scene render", "works" if out.stat().st_size > 3000 else "failed", f"{out.stat().st_size} bytes")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    work = Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "selftest"
    work.mkdir(parents=True, exist_ok=True)
    rows = local_checks() + [_try("Scene render", lambda: render_check(work))]
    if "--network" in argv:
        rows += network_checks(work)
    width = max(len(r["tool"]) for r in rows)
    for r in rows:
        mark = {"works": "OK  ", "missing": "--  ", "failed": "FAIL"}[r["status"]]
        print(f"{mark} {r['tool']:<{width}}  {r['detail']}")
    print(f"\n{sum(r['status'] == 'works' for r in rows)} work, {sum(r['status'] == 'missing' for r in rows)} missing, "
          f"{sum(r['status'] == 'failed' for r in rows)} failed")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 1 if any(r["status"] == "failed" for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
