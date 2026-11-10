"""An original score for each film, synthesised with FFmpeg (no samples, nothing licensed): a bed per act whose
chord, colour and motion follow the act's mood, crossfaded, kept far under the voice.

Moods: unease (suspended minor), inquiry (minor with a soft pulse), revelation (rising: minor to its relative major),
loss (low minor, slow), resolve (major add9). The art direction's music treatment shapes it: "drone" holds chords,
"pulse" adds a heartbeat pulse in the investigation, "sparse" plays only the opening, the turn and the end.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# mood: (chord as frequencies, pulse?)
NOTES = {"A1": 55.0, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.0, "A2": 110.0, "B2": 123.47, "C3": 130.81,
         "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.0, "A3": 220.0, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63}
MOODS = {"unease": ["A1", "E2", "B2", "C3", "E3"], "inquiry": ["D2", "A2", "D3", "F3", "A3"],
         "revelation": ["C2", "G2", "E3", "G3", "C4"], "loss": ["F2", "C3", "F3", "G3", "C4"],
         "resolve": ["C2", "G2", "D3", "E3", "G3", "D4"]}
ACT_MOOD = {"hook": "unease", "world": "inquiry", "investigation": "inquiry", "discovery": "revelation",
            "consequences": "loss", "ending": "resolve"}


def _bed(mood: str, seconds: float, pulse: bool, out: Path) -> Path:
    fr = [NOTES[n] for n in MOODS.get(mood, MOODS["inquiry"])]
    # each voice: a sine with its own slow swell; the top notes quieter; a gentle detune for width
    parts = []
    for i, f in enumerate(fr):
        amp = 0.11 / (1 + i * 0.55)
        lfo = 0.07 + i * 0.023
        parts.append(f"{amp:.3f}*(0.6+0.4*sin(2*PI*{lfo:.3f}*t+{i}))*(sin(2*PI*{f:.2f}*t)+0.35*sin(2*PI*{f * 1.003:.2f}*t))")
    if pulse:
        parts.append(f"0.09*sin(2*PI*{fr[0] * 2:.2f}*t)*exp(-7*mod(t,0.8))")
    expr = "+".join(parts)
    fade = min(2.5, seconds / 4)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"aevalsrc='{expr}|{expr}':s=48000:d={seconds:.2f}",
                    "-af", f"lowpass=f=1800,aecho=0.6:0.5:180|370:0.25|0.15,afade=t=in:d={fade:.2f},"
                           f"afade=t=out:st={max(0.0, seconds - fade):.2f}:d={fade:.2f}", "-ac", "2", str(out)],
                   check=True, timeout=600)
    return out


def compose(acts: list[tuple[str, float, float]], treatment: str, work: Path) -> Path | None:
    """acts: (act name, start, seconds) covering the film. Returns one stereo WAV the length of the film."""
    work.mkdir(parents=True, exist_ok=True)
    if not acts:
        return None
    total = acts[-1][1] + acts[-1][2]
    beds = []
    for k, (name, start, seconds) in enumerate(acts):
        mood = ACT_MOOD.get(name.lower(), "inquiry")
        if treatment == "sparse" and name.lower() not in ("hook", "discovery", "ending"):
            continue
        pulse = treatment == "pulse" and name.lower() in ("investigation", "world")
        beds.append((start, _bed(mood, seconds + 2.0, pulse, work / f"score_{k:02d}_{mood}.wav")))
    if not beds:
        return None
    out = work / "score.wav"
    args, mix = [], []
    for i, (start, f) in enumerate(beds):
        args += ["-i", str(f)]
        ms = int(max(0.0, start - 1.0) * 1000)
        mix.append(f"[{i}:a]adelay={ms}|{ms}[b{i}]")
    graph = ";".join(mix) + ";" + "".join(f"[b{i}]" for i in range(len(beds))) + \
        f"amix=inputs={len(beds)}:duration=longest:normalize=0,atrim=0:{total:.2f},loudnorm=I=-30:TP=-6[a]"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", *args, "-filter_complex", graph, "-map", "[a]",
                    "-ar", "48000", str(out)], check=True, timeout=900)
    return out
