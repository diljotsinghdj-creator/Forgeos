"""A score written to the cuts: every scene gets a whole number of bars (the tempo flexes per scene), so each cut
lands on a downbeat, and each cut is marked by harmony (the scene walks home to the dominant, the cut arrives on the
tonic), not by a volume hit. Method adapted from iart-ai/javascript-animation-skills (MIT, 'soundtrack' skill),
rewritten in numpy so the studio needs no browser for audio.

Voices (all synthesised, nothing licensed): soft pad, plucked arpeggio (Karplus-Strong), round bass, soft kick and a
shaker. Layers enter one per bar at the start (never kick and bass together), and an optional break (a silent bar)
can sit before a payoff cut. `sync_check` measures every cut: OFF-BEAT beyond 100 ms or STARTLE above +6 dB fails.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SR = 48000
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
# scale degrees (0-based) for the body of a scene; the last bar of every scene is V, the next scene opens on I
PROG = {"minor": [[0, 5, 2, 6], [0, 3, 5, 6], [0, 5, 3, 6]], "major": [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 0, 4]]}


def plan(cuts: list[float], total: float, bpm: float = 84.0, lo: float = 66.0, hi: float = 104.0) -> list[dict]:
    """Scenes between cuts. Each gets a whole number of beats (so every cut lands on a beat; on a downbeat whenever the
    count is a multiple of four) at a tempo inside [lo, hi], as close to `bpm` as possible."""
    edges = [0.0] + sorted(c for c in cuts if 0.3 < c < total - 0.3) + [total]
    out = []
    for a, b in zip(edges, edges[1:]):
        length = b - a
        best = None
        for beats in range(2, 4 * 64):
            tempo = 60.0 * beats / length
            outside = max(0.0, lo - tempo, tempo - hi)
            score = (outside, (beats % 4 != 0) * .5 + abs(tempo - bpm) / 100)   # prefer in range, then whole bars, then near bpm
            if best is None or score < best[0]:
                best = (score, beats, tempo)
            if tempo > hi + 40:
                break
        _, beats, tempo = best
        out.append({"start": a, "end": b, "bars": beats / 4, "bpm": tempo})
    return out


def _note(root_midi: int, scale: list[int], degree: int, octave: int = 0) -> float:
    o, d = divmod(degree, 7)
    return 440.0 * 2 ** ((root_midi + scale[d] + 12 * (o + octave) - 69) / 12)


def _chord(root_midi, scale, degree):
    return [_note(root_midi, scale, degree + k) for k in (0, 2, 4)]


def _env(n, a, r):
    e = np.ones(n)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _pluck(freq, dur, bright=.5, seed=0):
    n = int(dur * SR)
    p = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p) * bright
    out = np.zeros(n)
    for i in range(n):
        v = buf[i % p]
        out[i] = v
        buf[i % p] = .5 * (v + buf[(i + 1) % p]) * .996
    return out * _env(n, .002, min(.3, dur * .5))


def _pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.004 * t) + .25 * np.sin(2 * np.pi * f * 2 * t) for f in freqs)
    return s / (len(freqs) * 1.75) * _env(n, min(.6, dur * .3), min(.5, dur * .3))


def _kick(dur=.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * (50 + 80 * np.exp(-t * 30)) * t) * np.exp(-t * 9)


def _shaker(dur=.08, seed=1):
    n = int(dur * SR)
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    x = np.diff(x, prepend=0)                     # high-passed noise
    return x * np.exp(-np.arange(n) / SR * 60) * .25


def compose(cuts: list[float], total: float, out: Path, mode: str = "minor", root_midi: int = 50, bpm: float = 84.0,
            breaks: tuple[int, ...] = (), seed: int = 3) -> tuple[Path, list[dict]]:
    """Render the score to a stereo WAV. breaks: scene indexes whose last bar falls silent before the cut."""
    scenes = plan(cuts, total, bpm)
    scale = MINOR if mode == "minor" else MAJOR
    L = int(total * SR) + SR
    pad, pl, bass, perc = (np.zeros(L) for _ in range(4))
    rng = np.random.default_rng(seed)
    bar_index = 0
    for si, sc in enumerate(scenes):
        bar = (sc["end"] - sc["start"]) / sc["bars"]
        prog = PROG[mode][si % len(PROG[mode])]
        for b in range(max(1, math.ceil(sc["bars"]))):
            t0 = sc["start"] + b * bar
            last = b == math.ceil(sc["bars"]) - 1
            deg = 4 if (last and sc["bars"] >= 1 and b > 0) else prog[b % len(prog)]   # walk home to V, the cut lands on I
            if si in breaks and last:
                bar_index += 1
                continue
            i0 = int(t0 * SR)
            ch = _chord(root_midi, scale, deg)
            seg = _pad([f / 2 for f in ch], min(bar, sc["end"] - t0))
            pad[i0:i0 + len(seg)] += seg * .55
            ramp = lambda entry: min(1.0, .25 + .25 * (bar_index - entry))        # a new layer fades in over ~3 bars
            if bar_index >= 1:                                            # layers enter one per bar
                for k in range(8):
                    if t0 + k * bar / 8 >= sc["end"] - .01:
                        break
                    f = ch[[0, 1, 2, 1, 0, 2, 1, 2][k]] * (2 if k % 4 == 3 else 1)
                    s = _pluck(f, bar / 8 * 1.6, .45 + .1 * rng.random(), seed + bar_index * 8 + k)
                    j = int((t0 + k * bar / 8) * SR)
                    pl[j:j + len(s)] += s[:max(0, L - j)] * (.30 if k % 2 == 0 else .22) * ramp(1)
            if bar_index >= 2:
                t = np.arange(int(min(bar, sc["end"] - t0) * SR)) / SR
                bf = ch[0] / 4
                s = (np.sin(2 * np.pi * bf * t) + .3 * np.sin(4 * np.pi * bf * t)) * _env(len(t), .02, .2) * .35
                bass[i0:i0 + len(s)] += s[:max(0, L - i0)] * ramp(2)
            if bar_index >= 3:
                for q in range(4):
                    if t0 + q * bar / 4 >= sc["end"] - .01:
                        break
                    j = int((t0 + q * bar / 4) * SR)
                    if q in (0, 2):
                        s = _kick() * (.42 if q == 0 else .32)
                        perc[j:j + len(s)] += s[:max(0, L - j)] * ramp(3)
                    for h in range(2):
                        jj = int((t0 + (q + h * .5) * bar / 4) * SR)
                        s = _shaker(seed=bar_index * 8 + q * 2 + h)
                        perc[jj:jj + len(s)] += s[:max(0, L - jj)] * ramp(3)
            bar_index += 1
    mix = pad + pl + bass + perc
    # a little room: two short feedback echoes
    for d, g in ((.11, .22), (.23, .13)):
        k = int(d * SR)
        mix[k:] += mix[:-k] * g
    mix = mix[:int(total * SR)]
    fade = int(2.5 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix[:int(.4 * SR)] *= np.linspace(0, 1, int(.4 * SR))
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * .8
    st = np.stack([mix, np.roll(mix, int(.006 * SR)) * .97], 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes((np.clip(st, -1, 1) * 32767).astype("<i2").tobytes())
    return out, scenes


def sync_check(wav: Path, cues: list[float], tol: float = .10, startle_db: float = 6.0) -> list[dict]:
    """For each cue: offset to the nearest strong onset, and the loudness jump into it (vs the second before)."""
    with wave.open(str(wav)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32).reshape(-1, ch).mean(1) / 32768
    hop, win = 256, 1024
    frames = np.lib.stride_tricks.sliding_window_view(a, win)[::hop] * np.hanning(win)
    mag = np.abs(np.fft.rfft(frames, axis=1))
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    ft = (np.arange(len(flux)) + 1) * hop / sr
    rms = lambda s, e: 20 * math.log10(np.sqrt(np.mean(a[max(0, int(s * sr)):max(int(s * sr) + 1, int(e * sr))] ** 2)) + 1e-9)
    rows = []
    for c in cues:
        if c < 1.0 or c > len(a) / sr - 2.5:
            continue
        m = (ft > c - 2) & (ft < c + 2)
        if not m.any():
            continue
        thr = np.percentile(flux[m], 80)
        near = (ft > c - .5) & (ft < c + .5) & (flux >= thr)
        off = float(ft[near][np.argmin(np.abs(ft[near] - c))] - c) if near.any() else None
        jump = rms(c, c + .25) - rms(c - 1.0, c)
        rows.append({"cue": round(c, 2), "offset_ms": None if off is None else round(off * 1000), "jump_db": round(jump, 1),
                     "ok": off is not None and abs(off) <= tol and jump <= startle_db})
    return rows
