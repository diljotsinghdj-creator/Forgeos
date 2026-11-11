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
    res = {"lufs": float(d["input_i"]), "true_peak": float(d["input_tp"])}
    precise = lufs_precise(path)
    if precise is not None:
        res["lufs_bs1770"] = precise           # a second, independent measurement (pyloudnorm, ITU-R BS.1770-4)
    return res


def lufs_precise(path: Path, rate: int = 48000) -> float | None:
    """Integrated loudness with pyloudnorm (MIT), when installed; None otherwise."""
    try:
        import numpy as np
        import pyloudnorm
    except ImportError:
        return None
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-vn", "-ac", "2", "-ar", str(rate), "-f", "f32le", "-"],
                         capture_output=True, timeout=600).stdout
    if not raw:
        return None
    data = np.frombuffer(raw, np.float32).reshape(-1, 2)
    if len(data) < rate // 2:
        return None
    v = pyloudnorm.Meter(rate).integrated_loudness(data)
    return round(float(v), 2) if np.isfinite(v) else None


def silences(path: Path, total: float) -> list[tuple[float, float]]:
    out = _stderr(["-i", str(path), "-vn", "-af", f"silencedetect=noise=-42dB:d={MAX_GAP_S}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    gaps = []
    for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
        if s > 0.3 and e < total - 1.0:      # ignore the lead-in and the outro tail
            gaps.append((round(s, 2), round(e - s, 2)))
    return gaps


FROZEN_S = 3.0      # a picture that doesn't move for this long reads as a slideshow, not a film


def freezes(path: Path) -> list[tuple[float, float]]:
    """Stretches where the picture doesn't move at all (no push-in, no new shot): (start, seconds)."""
    out = _stderr(["-i", str(path), "-map", "0:v:0", "-vf", f"freezedetect=n=0.0008:d={FROZEN_S}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", out)]
    lens = [float(x) for x in re.findall(r"freeze_duration: ([\d.]+)", out)]
    return list(zip(starts, lens))


def blacks(path: Path, total: float = 0.0) -> list[tuple[float, float]]:
    """Black stretches (a missing picture or a failed clip), ignoring the fade at the very end: (start, seconds)."""
    out = _stderr(["-i", str(path), "-map", "0:v:0", "-vf", "blackdetect=d=0.25:pix_th=0.06", "-f", "null", "-"])
    found = [(float(a), float(b) - float(a)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out)]
    return [(s, d) for s, d in found if s > 0.2 and not (total and s + d >= total - 0.8)]   # the closing fade is fine


def first_frame(path: Path) -> dict:
    out = _stderr(["-i", str(path), "-frames:v", "1", "-vf", "signalstats,metadata=print,blurdetect,metadata=print",
                   "-f", "null", "-"])
    bright = re.search(r"lavfi\.signalstats\.YAVG=([\d.]+)", out)
    high = re.search(r"lavfi\.signalstats\.YHIGH=([\d.]+)", out)
    blur = re.search(r"lavfi\.blur=([\d.]+)", out)
    return {"brightness": float(bright.group(1)) if bright else None, "highlights": float(high.group(1)) if high else None,
            "blur": float(blur.group(1)) if blur else None}


def _samples(path: Path, total: float, n: int = 12, size: int = 96):
    """n small RGB frames spread over the film: [(seconds, array[h, w, 3])]."""
    import subprocess
    import numpy as np
    out = []
    for i in range(n):
        t = max(0.0, total * (i + 0.5) / n)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(path), "-frames:v", "1", "-vf",
                              f"scale={size}:{size}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, timeout=60).stdout
        if len(raw) == size * size * 3:
            out.append((round(t, 1), np.frombuffer(raw, np.uint8).reshape(size, size, 3).astype("float32")))
    return out


def picture_checks(path: Path, total: float) -> dict:
    """What the eye would catch across the film, from sampled frames:
    flat  - frames with almost no contrast (text and picture can't be told apart)
    grade - frames whose colour balance is far from the film's own (a clip that wasn't graded like the rest)"""
    import numpy as np
    fr = _samples(path, total)
    if len(fr) < 3:
        return {"flat": [], "grade": []}
    flat, warmth = [], []
    for t, a in fr:
        y = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        lo, hi = np.percentile(y, [3, 97])
        if hi - lo < 38:
            flat.append(t)
        warmth.append(float(a[..., 0].mean() - a[..., 2].mean()))
    med = float(np.median(warmth))
    grade = [t for (t, _), w in zip(fr, warmth) if abs(w - med) > 42]
    return {"flat": flat, "grade": grade if len(grade) <= len(fr) // 3 else []}   # many "outliers" = a varied film


def frame_size(path: Path) -> tuple[int, int] | None:
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True, timeout=60).stdout.strip()
    m = re.match(r"(\d+),(\d+)", r)
    return (int(m.group(1)), int(m.group(2))) if m else None


def audio_ends_cleanly(path: Path, total: float) -> bool:
    """False when the sound is still loud in the last 60 ms (a cut-off word or a music bed chopped mid-note)."""
    out = _stderr(["-ss", f"{max(0.0, total - 0.06):.3f}", "-i", str(path), "-vn", "-af", "astats=metadata=0", "-f", "null", "-"])
    m = re.findall(r"RMS level dB: (-?[\d.]+|-inf)", out)
    return not m or m[-1] == "-inf" or float(m[-1]) < -32.0


def check(path: Path, total: float, asr_matches: list[float], target_lufs: float = -14.0,
          expected_size: tuple[int, int] | None = None) -> dict:
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
    frozen = freezes(path)
    add("no frozen picture", not frozen, "none" if not frozen else
        ", ".join(f"{d:.1f}s still at {s:.1f}s" for s, d in frozen[:4]))
    black = blacks(path, total)
    add("no black frames", not black, "none" if not black else
        ", ".join(f"{d:.1f}s black at {s:.1f}s" for s, d in black[:4]))
    ff = first_frame(path)
    if ff["brightness"] is not None:
        # a dark frame with something lit on it (a planet in space, a lamp in a room) is a picture, not a blank
        lit = ff["brightness"] >= 22 or (ff["brightness"] >= 8 and (ff.get("highlights") or 0) >= 120)
        add("first frame visible", lit, f"brightness {ff['brightness']:.0f}/255, highlights {ff.get('highlights') or 0:.0f}/255")
    if ff["blur"] is not None:
        add("first frame sharp", ff["blur"] <= 8.0, f"blur score {ff['blur']:.1f}")
    try:
        pc = picture_checks(path, total)
        add("readable contrast", not pc["flat"], "none flat" if not pc["flat"] else
            "almost no contrast at " + ", ".join(f"{t:.0f}s" for t in pc["flat"][:5]))
        add("consistent colour grade", not pc["grade"], "even" if not pc["grade"] else
            "colour balance jumps at " + ", ".join(f"{t:.0f}s" for t in pc["grade"][:5]))
    except Exception:  # noqa: BLE001 - a check that can't run is not a failed video
        pass
    if expected_size:
        got = frame_size(path)
        if got:
            add("frame size", got == tuple(expected_size), f"{got[0]}x{got[1]}" + ("" if got == tuple(expected_size)
                                                                                 else f" (expected {expected_size[0]}x{expected_size[1]})"))
    add("audio ends cleanly", audio_ends_cleanly(path, total), "fades out" if audio_ends_cleanly(path, total)
        else "the sound is cut off at the very end")
    if asr_matches:
        worst = min(asr_matches)
        add("narration matches script", worst >= 0.8,
            f"lowest scene match {worst:.0%}" + ("" if worst >= 0.8 else " - a word may be mispronounced or skipped"))
    warnings = [f"{c['name']}: {c['detail']}" for c in checks if not c["ok"]]
    return {"passed": not warnings, "checks": checks, "warnings": warnings}
