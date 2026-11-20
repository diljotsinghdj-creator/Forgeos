"""An original score for each film: a bed per act whose colour and motion follow the act's mood, crossfaded, kept far
under the voice.

Composers, best first:
    ACE-Step   (Apache-2.0) generates real instrumental music per act from a mood prompt. On the pod with CF_ACESTEP=1
               (GPU; checkpoints download on first use). Commercial use is allowed.
    synthesis  FFmpeg sine chords, always available, nothing licensed.
A licensed track the creator supplies (`from_track`) is used instead when given; Demucs removes any singing first.

Moods: unease (suspended minor), inquiry (minor with a soft pulse), revelation (rising: minor to its relative major),
loss (low minor, slow), resolve (major add9). The art direction's music treatment shapes it: "drone" holds chords,
"pulse" adds a heartbeat pulse in the investigation, "sparse" plays only the opening, the turn and the end.
"""
from __future__ import annotations

import os
import shutil
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


ACE = None           # tests set a callable(prompt, seconds, out) -> Path
LAST_HOW = ""        # which composer made the last score
ACE_PROMPTS = {
    "unease": "dark minimal cinematic underscore, suspended minor synth pads, low pulse, tense, documentary, no drums, 68 bpm",
    "inquiry": "curious investigative documentary underscore, muted plucked strings, soft piano, light ticking percussion, minor key, 90 bpm",
    "revelation": "cinematic documentary build, rising strings and piano, minor to major, hopeful tension, 84 bpm",
    "loss": "sparse melancholic documentary underscore, low cello, distant piano, slow, minor key, 60 bpm",
    "resolve": "warm resolving documentary underscore, major add9 piano and soft strings, calm, 76 bpm",
}
_PIPE: dict = {}


def ace_ready() -> bool:
    if ACE is not None:
        return True
    if os.environ.get("CF_ACESTEP") != "1":
        return False
    try:
        import acestep  # noqa: F401
    except ImportError:
        return False
    return True


def _ace(mood: str, seconds: float, pulse: bool, out: Path) -> Path:
    prompt = ACE_PROMPTS.get(mood, ACE_PROMPTS["inquiry"]) + (", soft heartbeat pulse" if pulse else "") + ", instrumental"
    secs = min(240.0, max(10.0, seconds))
    raw = out.with_name(out.stem + "_ace.wav")
    if ACE is not None:
        got = Path(ACE(prompt, secs, raw))
    else:
        if "p" not in _PIPE:
            from acestep.pipeline_ace_step import ACEStepPipeline
            _PIPE["p"] = ACEStepPipeline(checkpoint_dir=os.environ.get("CF_ACESTEP_DIR") or None, dtype="bfloat16")
        res = _PIPE["p"](format="wav", audio_duration=secs, prompt=prompt, lyrics="[instrumental]", infer_step=60,
                         guidance_scale=15.0, manual_seeds=[abs(hash(mood)) % 100000], save_path=str(raw))
        got = Path(next(p for p in res if str(p).endswith(".wav")))
    fade = min(2.5, seconds / 4)
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(got), "-af",
                    f"apad,atrim=0:{seconds:.2f},afade=t=in:d={fade:.2f},afade=t=out:st={max(0.0, seconds - fade):.2f}:d={fade:.2f}",
                    "-ar", "48000", "-ac", "2", str(out)], check=True, timeout=600)
    return out


def from_track(track: Path, total: float, work: Path) -> Path:
    """A licensed track the creator supplied: any singing removed (Demucs, when installed), looped or cut to the film,
    faded, and set at the same bed level as the composed score."""
    from ..media import stems
    global LAST_HOW
    work.mkdir(parents=True, exist_ok=True)
    src, how = stems.instrumental(Path(track), work)
    out = work / "score.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src), "-af",
                    f"atrim=0:{total:.2f},afade=t=in:d=1.5,afade=t=out:st={max(0.0, total - 3):.2f}:d=3,loudnorm=I=-30:TP=-6",
                    "-ar", "48000", "-ac", "2", str(out)], check=True, timeout=900)
    LAST_HOW = f"licensed track ({how})"
    return out


def compose(acts: list[tuple[str, float, float]], treatment: str, work: Path) -> Path | None:
    """acts: (act name, start, seconds) covering the film. Returns one stereo WAV the length of the film."""
    work.mkdir(parents=True, exist_ok=True)
    if not acts:
        return None
    global LAST_HOW
    total = acts[-1][1] + acts[-1][2]
    beds, hows = [], set()
    for k, (name, start, seconds) in enumerate(acts):
        mood = ACT_MOOD.get(name.lower(), "inquiry")
        if treatment == "sparse" and name.lower() not in ("hook", "discovery", "ending"):
            continue
        pulse = treatment == "pulse" and name.lower() in ("investigation", "world")
        f = work / f"score_{k:02d}_{mood}.wav"
        made = None
        if ace_ready():
            try:
                made = _ace(mood, seconds + 2.0, pulse, f)
            except Exception:  # noqa: BLE001 - the synthesised bed is always there to fall back on
                made = None
        beds.append((start, made or _bed(mood, seconds + 2.0, pulse, f)))
        hows.add("ACE-Step" if made else "synthesis")
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
    LAST_HOW = " + ".join(sorted(hows))
    return out
