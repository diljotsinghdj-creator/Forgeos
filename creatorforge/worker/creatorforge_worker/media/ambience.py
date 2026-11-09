"""Ambient beds: the quiet sound of where a shot is. A map over the sea has water under it, a land map has wind,
a document has the hush of a room and a pen, an old photograph has a projector, a 3D shot has a low studio hum.
The beds are made with FFmpeg's own generators (no downloads, no samples), cut to each shot with soft fades, and
mixed far under the voice.

    beds = ambience.place(folder, [(start, seconds, kind, spec)])   -> [(wav, start, gain)] for render.mix_audio
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .ff import MediaError

# name: (lavfi source, gain in the mix)
BEDS = {
    "sea": ("anoisesrc=c=brown:a=0.9:r=48000,lowpass=f=700,tremolo=f=0.13:d=0.75,highpass=f=40", 0.16),
    "wind": ("anoisesrc=c=pink:a=0.8:r=48000,bandpass=f=420:w=380,tremolo=f=0.21:d=0.6", 0.12),
    "room": ("anoisesrc=c=brown:a=0.5:r=48000,lowpass=f=260,highpass=f=30", 0.14),
    "paper": ("anoisesrc=c=white:a=0.35:r=48000,highpass=f=2200,lowpass=f=7000,tremolo=f=5.5:d=0.9,"
              "volume='0.25+0.75*lt(mod(t,1.9),0.5)':eval=frame", 0.07),
    "projector": ("anoisesrc=c=white:a=0.5:r=48000,highpass=f=900,lowpass=f=3200,tremolo=f=18:d=0.8", 0.08),
    "hum": ("sine=f=55:r=48000,tremolo=f=0.4:d=0.3,volume=0.5", 0.10),
    "city": ("anoisesrc=c=brown:a=0.8:r=48000,lowpass=f=1100,highpass=f=70,tremolo=f=0.09:d=0.4", 0.11),
}
SEA = {"route", "railmap"}
LAND_MAPS = {"fly", "map", "globe", "pinmap", "heatmap", "arrows", "borders", "clockmap", "shade", "sizemap"}
PAPERS = {"document", "article", "clipping", "newscard", "courtdoc", "receipt", "reveal", "table", "pinboard", "desk"}
THREE_D = {"bars3d", "prism", "explode", "title3d", "object"}


def bed_for(kind: str, spec: str = "", archive: bool = False) -> str:
    """The bed a shot gets ('' = none: a chart or a title keeps the music and the voice alone)."""
    s = (spec or "").lower()
    if archive:
        return "projector"
    if kind == "route":
        return "sea" if "ship" in s else "wind"
    if kind in LAND_MAPS or kind == "railmap":
        return "city" if kind in ("fly", "railmap") else "wind"
    if kind in PAPERS:
        return "paper" if kind in ("document", "courtdoc", "reveal", "receipt") else "room"
    if kind in THREE_D:
        return "hum"
    return ""


def _bed(folder: Path, name: str, seconds: float) -> Path:
    """The bed cut to a shot: its length rounded up to half a second, faded in and out."""
    d = max(1.0, round(seconds * 2 + 0.49) / 2)
    out = folder / f"{name}_{int(d * 10):04d}.wav"
    if out.is_file() and out.stat().st_size > 1000:
        return out
    folder.mkdir(parents=True, exist_ok=True)
    src, _ = BEDS[name]
    fade = min(0.5, d / 4)
    r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, "-t", f"{d:.2f}",
                        "-af", f"afade=t=in:d={fade:.2f},afade=t=out:st={d - fade:.2f}:d={fade:.2f}", "-ac", "2",
                        "-ar", "48000", str(out)], capture_output=True, timeout=120)
    if r.returncode != 0 or not out.is_file():
        raise MediaError(f"ambience: {r.stderr.decode()[-200:]}")
    return out


def place(folder: Path, shots: list[tuple[float, float, str, str, bool]]) -> list[tuple[Path, float, float]]:
    """shots: (start, seconds, kind, spec, archive). Neighbouring shots with the same bed share one long bed, so
    the room doesn't blink at every cut."""
    runs: list[list] = []
    for start, seconds, kind, spec, archive in shots:
        name = bed_for(kind, spec, archive)
        if not name or seconds < 0.8:
            continue
        if runs and runs[-1][0] == name and abs(runs[-1][1] + runs[-1][2] - start) < 0.3:
            runs[-1][2] = start + seconds - runs[-1][1]
        else:
            runs.append([name, start, seconds])
    out = []
    for name, start, seconds in runs:
        try:
            out.append((_bed(folder, name, seconds), max(0.0, start - 0.1), BEDS[name][1]))
        except (MediaError, OSError, subprocess.SubprocessError):
            continue                      # a bed is never worth failing a video for
    return out
