"""Sound design synchronised to the animation (for video, not music production).

`events(recording, scene)` reads what actually happened in a recorded performance (qc.record) and lists sound
events with their exact time and place:

    footstep    the frame a foot touches down (louder for a run or a landing, lighter on tiptoe)
    land        a body arriving from a jump or fall (a thump)
    whoosh      an object leaving a hand fast (a throw)
    catch       an object arriving in hands (a slap)
    bounce      an object hitting the ground, quieter each bounce
    clap        two hands meeting
    voice       cartoon "speech" syllables during each speech bubble, a pitch per character, rising on questions
    pop         a speech bubble or symbol appearing
    comedy      a slide whistle as someone trips, a bonk on a knockback, a "boing" on a pain hop

`mix(events, seconds, scene, ambience)` synthesises everything (no samples to license), pans each sound by where
it happens on screen, lays an ambience bed under it (studio room tone, outdoors air and birds, indoors hum; an
anxious mood adds a heartbeat in time with the picture), and writes a 48 kHz stereo WAV for Scene.render."""
from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SR = 48000


@dataclass
class Event:
    t: float
    kind: str
    x: float = 0.0
    gain: float = 1.0
    pitch: float = 1.0
    who: str = ""


def events(R, sc=None) -> list[Event]:
    out: list[Event] = []
    dt = 1 / R.fps
    for i, a in enumerate(R.actors):
        F = R.joints[i]
        name = a.look.name
        pitch = 0.75 + (hash(name) % 7) * 0.09
        g0 = lambda x: a._floor(x) + a.ankle            # noqa: E731
        vy_prev = 0.0
        for n in range(1, len(F)):
            for k in range(2):
                p0, p1 = F[n - 1]["legs"][k][2], F[n]["legs"][k][2]
                was_up = p0[1] - g0(p0[0]) > 0.006
                down = abs(p1[1] - g0(p1[0])) < 0.003
                if was_up and down:
                    speed = abs(p1[1] - p0[1]) / dt
                    out.append(Event(R.times[n], "footstep", p1[0], min(1.0, 0.35 + 0.25 * speed), 1.0, name))
            vy = (F[n]["hip"][1] - F[n - 1]["hip"][1]) / dt
            if vy_prev < -2.0 and vy > vy_prev + 2.5:     # a fall stopped by the ground
                out.append(Event(R.times[n], "land", F[n]["hip"][0], min(1.0, -vy_prev / 5), 1.0, name))
            vy_prev = vy
            clapping = any(g0 <= R.times[n] <= g1 and gn == "clap" for g0, g1, gn in a.loco.gestures)
            wa, wb = F[n]["arms"][0][2], F[n]["arms"][1][2]
            pa, pb = F[n - 1]["arms"][0][2], F[n - 1]["arms"][1][2]
            if clapping and math.dist(wa, wb) < 0.07 <= math.dist(pa, pb):   # only a real clap, hands meeting
                out.append(Event(R.times[n], "clap", wa[0], 0.8, 1.0, name))
        for t0, t1, text in a.bubbles:
            out.append(Event(t0, "pop", a.hips_x(t0), 0.4, 1.3, name))
            syl = max(1, int(len(text) / 3.2))
            talk = min(t1 - t0 - 0.2, 0.065 * len(text) + 0.3)
            for s in range(syl):
                ts = t0 + talk * s / syl
                rise = 1.0 + (0.25 * s / syl if text.rstrip().endswith("?") else -0.08 * s / syl)
                out.append(Event(ts, "voice", a.hips_x(ts), 0.5, pitch * rise * (1 + 0.06 * math.sin(s * 2.1)), name))
        for t0, t1, sym in a.symbols:
            out.append(Event(t0, "pop", a.hips_x(t0), 0.35, 1.6, name))
        for act in a.acts:
            R_ = act.resolved or []
            for (ta, pa, _, _), (tb, pb, _, ball) in zip(R_, R_[1:]):      # the end of a flight is a touch-down
                if ball and pb.feet:
                    out.append(Event(tb, "land", pb.x, 0.8, 1.0, name))
            if act.name == "put_down":
                out.append(Event(act.t0 + 0.5, "set_down", a.hips_x(act.t0), 0.5, 1.0, name))
            if act.name == "trip_roll":
                out.append(Event(act.t0, "slide_whistle", a.hips_x(act.t0), 0.7, 1.0, name))
            elif act.name == "knockback":
                out.append(Event(act.t0 + 0.05, "bonk", a.hips_x(act.t0), 0.9, 1.0, name))
            elif act.name == "pain_hop":
                out.append(Event(act.t0 + 0.1, "boing", a.hips_x(act.t0), 0.6, 1.0, name))
    for j, p in enumerate(R.prop_objs):
        P = R.props[j]
        flights = [f["t0"] for f in getattr(p, "flights", [])]
        catches = [c[0] for c in p.carriers if c[0] > 0]
        for ft in flights:
            n = min(len(P) - 2, int(ft * R.fps) + 2)
            v = math.dist(P[n + 1][:2], P[n][:2]) / dt
            if v > 2.5:
                out.append(Event(ft, "whoosh", P[n][0], min(1.0, v / 12), 1.0, p.kind))
        bounces, last = 0, -1.0
        ground = (lambda x: 0.0)
        w = next((f.get("world") for f in getattr(p, "flights", []) if f.get("world")), None)
        if w is not None:
            ground = w.ground
        for n in range(2, len(P)):
            tn = R.times[n]
            held = any(c[0] <= tn <= c[1] for c in p.carriers)
            vy0 = (P[n - 1][1] - P[n - 2][1]) / dt
            vy1 = (P[n][1] - P[n - 1][1]) / dt
            at_ground = P[n][1] - ground(P[n][0]) < 0.03 or P[n - 1][1] - ground(P[n - 1][0]) < 0.03
            if (not held and at_ground and vy0 < -0.8 and vy1 > vy0 + 0.8 and tn - last > 0.12
                    and not any(abs(tn - c) < 0.08 for c in catches)):
                bounces += 1
                last = tn
                out.append(Event(tn, "bounce", P[n][0], min(1.0, -vy0 / 6), 1.0 + 0.05 * bounces, p.kind))
        for c in catches:
            if any(0.1 < c - ft < 3.0 for ft in flights):
                n = min(len(P) - 1, int(c * R.fps))
                out.append(Event(c, "catch", P[n][0], 0.8, 1.0, p.kind))
    return sorted(out, key=lambda e: e.t)


# ---- synthesis ---------------------------------------------------------------------------------------------------------
def _t(d):
    return np.arange(int(d * SR)) / SR


def _noise(n, rng):
    return rng.standard_normal(n)


def _lp(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):                         # one-pole low-pass (short sounds only)
        acc += a * (v - acc)
        y[i] = acc
    return y


def synth(e: Event, rng) -> np.ndarray:
    k = e.kind
    if k == "footstep":
        t = _t(0.09)
        x = _noise(len(t), rng) * np.exp(-t * 70)
        x = _lp(x, 0.18) * 1.6 + 0.4 * np.sin(2 * math.pi * 90 * t) * np.exp(-t * 60)
        return x * e.gain * 0.5
    if k == "land":
        t = _t(0.3)
        return (np.sin(2 * math.pi * (55 + 40 * np.exp(-t * 25)) * t) * np.exp(-t * 14) +
                0.3 * _lp(_noise(len(t), rng), 0.1) * np.exp(-t * 30)) * e.gain * 0.8
    if k == "set_down":
        t = _t(0.12)
        return (_lp(_noise(len(t), rng), 0.25) * np.exp(-t * 45) + 0.4 * np.sin(2 * math.pi * 140 * t) * np.exp(-t * 40)) * 0.5
    if k == "whoosh":
        t = _t(0.35)
        env = np.sin(math.pi * t / 0.35) ** 2
        return _lp(_noise(len(t), rng), 0.35) * env * e.gain * 0.45
    if k == "catch":
        t = _t(0.08)
        return (_noise(len(t), rng) * np.exp(-t * 90) + 0.5 * np.sin(2 * math.pi * 300 * t) * np.exp(-t * 70)) * 0.5
    if k == "bounce":
        t = _t(0.15)
        f = 180 * e.pitch
        return (np.sin(2 * math.pi * (f + 120 * np.exp(-t * 40)) * t) * np.exp(-t * 28)) * e.gain * 0.6
    if k == "clap":
        t = _t(0.06)
        return _noise(len(t), rng) * np.exp(-t * 110) * 0.7
    if k == "pop":
        t = _t(0.08)
        return np.sin(2 * math.pi * (700 * e.pitch - 2500 * t) * t) * np.exp(-t * 45) * e.gain * 0.5
    if k == "voice":                                    # a cartoon syllable: a voiced blip with a formant-ish edge
        t = _t(0.11)
        f0 = 210 * e.pitch
        env = np.sin(math.pi * np.minimum(1.0, t / 0.11)) ** 1.5
        x = sum(np.sin(2 * math.pi * f0 * h * t) / h for h in (1, 2, 3, 5))
        return x * env * e.gain * 0.18
    if k == "slide_whistle":
        t = _t(0.7)
        f = 1400 * np.exp(-t * 2.2)
        return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.minimum(1, t * 20) * np.exp(-t * 1.2) * e.gain * 0.35
    if k == "bonk":
        t = _t(0.35)
        return (np.sin(2 * math.pi * 520 * t) * np.exp(-t * 18) + 0.6 * np.sin(2 * math.pi * 780 * t) * np.exp(-t * 22)
                ) * e.gain * 0.5
    if k == "boing":
        t = _t(0.45)
        f = 160 + 90 * np.sin(2 * math.pi * 9 * t) * np.exp(-t * 4)
        return np.sin(2 * math.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * e.gain * 0.45
    return np.zeros(1)


def ambience(kind: str, seconds: float, rng, moods=()) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    base = np.cumsum(rng.standard_normal(n))
    base -= np.convolve(base, np.ones(4801) / 4801, mode="same")    # take out the drift: a soft brown-ish bed
    base /= max(1e-9, np.abs(base).max())
    if kind == "outdoors":
        bed = base * 0.05 * (0.7 + 0.3 * np.sin(2 * math.pi * 0.11 * t))
        for k in range(int(seconds / 2.3)):                         # a few birds
            t0 = rng.uniform(0, max(0.1, seconds - 0.5))
            i0, L = int(t0 * SR), int(0.18 * SR)
            if i0 + L < n:
                tt = np.arange(L) / SR
                f = 3200 + 900 * np.sin(2 * math.pi * 14 * tt)
                bed[i0:i0 + L] += 0.04 * np.sin(2 * math.pi * np.cumsum(f) / SR) * np.sin(math.pi * tt / 0.18)
    elif kind == "indoors":
        bed = base * 0.03 + 0.008 * np.sin(2 * math.pi * 50 * t)
    else:
        bed = base * 0.025
    for t0, t1, mood in moods:
        if mood == "anxious":                                        # heartbeat in time with the picture's pulse
            beat = 1 / 1.6
            k = t0
            while k < t1:
                for off, g in ((0.0, 1.0), (0.18, 0.6)):
                    i0 = int((k + off) * SR)
                    L = int(0.12 * SR)
                    if 0 <= i0 and i0 + L < n:
                        tt = np.arange(L) / SR
                        bed[i0:i0 + L] += 0.35 * g * np.sin(2 * math.pi * 48 * tt) * np.exp(-tt * 30)
                k += beat
    return bed


def mix(evts: list[Event], seconds: float, sc=None, place: str = "studio", out: Path | None = None) -> Path:
    rng = np.random.default_rng(7)
    n = int(seconds * SR) + SR
    L = np.zeros(n)
    Rch = np.zeros(n)
    bed = ambience(place, seconds + 1.0, rng, getattr(sc, "moods", []) if sc else [])[:n]   # rounding can add 1
    L[:len(bed)] += bed
    Rch[:len(bed)] += bed
    half = (sc.width / sc.ppm / 2) if sc else 4.0
    for e in evts:
        x = synth(e, rng)
        i0 = int(e.t * SR)
        if i0 >= n or len(x) < 2:
            continue
        cx = sc.camera(e.t)[0] if sc else 0.0
        pan = max(-1.0, min(1.0, (e.x - cx) / half))
        gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        m = min(len(x), n - i0)
        L[i0:i0 + m] += x[:m] * gl
        Rch[i0:i0 + m] += x[:m] * gr
    peak = max(1e-9, np.abs(L).max(), np.abs(Rch).max())
    g = min(1.0, 0.89 / peak)                                      # no clipping (peak about -1 dBFS)
    data = (np.stack([L, Rch], axis=1)[:int(seconds * SR)] * g * 32767).astype(np.int16)
    out = Path(out or "mix.wav")
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return out


def soundtrack(build, fixes, sc_render, seconds: float, place: str, out: Path) -> Path:
    """Events from a separately staged copy of the scene (recording plays it), panned with the final camera."""
    from . import qc
    probe, _ = build()
    qc.apply(probe, fixes)
    R = qc.record(probe, seconds, sc_render.fps)
    return mix(events(R, probe), seconds, sc_render, place, out)
