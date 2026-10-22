"""Pre-post quality check on the finished video. Never blocks a video - it lists what a viewer would notice so it
can be fixed before posting: loudness, clipping, dead air, a dark or blurry first frame, captions that drift from
the script."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

LOUDNESS_TOLERANCE = 2.0   # LU either side of the target
MAX_GAP_S = 0.8            # silence longer than this inside the video feels like a mistake


def _stderr(args: list[str]) -> str:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", *args], capture_output=True, timeout=900)
    return p.stderr.decode(errors="replace")


def loudness(path: Path) -> dict:
    out = _stderr(["-i", str(path), "-vn", "-af", "loudnorm=I=-14:TP=-1.5:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        return {}
    d = json.loads(m.group(0))
    return {"lufs": float(d["input_i"]), "true_peak": float(d["input_tp"])}


def silences(path: Path, total: float) -> list[tuple[float, float]]:
    out = _stderr(["-i", str(path), "-vn", "-af", f"silencedetect=noise=-42dB:d={MAX_GAP_S}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    gaps = []
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s > 0.3 and e < total - 1.0:      # ignore the lead-in and the outro tail
            gaps.append((round(s, 2), round(e - s, 2)))
    return gaps


def first_frame(path: Path) -> dict:
    out = _stderr(["-i", str(path), "-frames:v", "1", "-vf", "signalstats,metadata=print,blurdetect,metadata=print",
                   "-f", "null", "-"])
    bright = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", out)
    blur = re.search(r"lavfi\.blur=([\d.]+)", out)
    return {"brightness": float(bright.group(1)) if bright else None, "blur": float(blur.group(1)) if blur else None}


def check(path: Path, total: float, asr_matches: list[float], target_lufs: float = -14.0) -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    lv = loudness(path)
    if lv:
        add("loudness", abs(lv["lufs"] - target_lufs) <= LOUDNESS_TOLERANCE,
            f"{lv['lufs']:.1f} LUFS (target {target_lufs:.0f})")
        add("no clipping", lv["true_peak"] <= -0.5, f"true peak {lv['true_peak']:.1f} dBTP")
    gaps = silences(path, total)
    add("no dead air", not gaps, "none" if not gaps else
        ", ".join(f"{d:.1f}s silence at {s:.1f}s" for s, d in gaps[:4]))
    ff = first_frame(path)
    if ff["brightness"] is not None:
        add("first frame visible", ff["brightness"] >= 22, f"brightness {ff['brightness']:.0f}/255")
    if ff["blur"] is not None:
        add("first frame sharp", ff["blur"] <= 8.0, f"blur score {ff['blur']:.1f}")
    if asr_matches:
        worst = min(asr_matches)
        add("narration matches script", worst >= 0.8,
            f"lowest scene match {worst:.0%}" + ("" if worst >= 0.8 else " - a word may be mispronounced or skipped"))
    warnings = [f"{c['name']}: {c['detail']}" for c in checks if not c["ok"]]
    return {"passed": not warnings, "checks": checks, "warnings": warnings}
