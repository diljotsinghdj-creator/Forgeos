"""Speech for animated characters, with the timing of every sound, so mouths move with the words.

espeak-ng (free, offline, English and Hindi among ~100 languages) speaks the line and reports each phoneme and when it
is heard; each phoneme becomes a mouth shape (viseme). A recorded or TTS voice from elsewhere can be used instead:
`estimate_visemes` times the mouth shapes from the text and the audio length."""
from __future__ import annotations

import ctypes
import math
import os
import re
import struct
import wave
from pathlib import Path

# mouth shapes: (open 0..1, width 0.5..1.3, round 0..1)
VISEMES = {
    "rest": (0.0, 1.0, 0.0), "MBP": (0.0, 0.92, 0.0), "FV": (0.08, 1.02, 0.0), "TH": (0.14, 1.0, 0.0),
    "L": (0.3, 1.0, 0.0), "WQ": (0.18, 0.62, 1.0), "O": (0.55, 0.72, 0.85), "U": (0.25, 0.62, 0.9),
    "AI": (0.78, 1.06, 0.0), "E": (0.38, 1.2, 0.0), "CDGK": (0.26, 1.06, 0.0),
}


def viseme_of(ph: str) -> str:
    """espeak's ASCII phoneme name -> mouth shape."""
    p = ph.strip("'`,%=_:;!-")
    if not p:
        return "rest"
    c = p[0]
    if c in "pbm":
        return "MBP"
    if c in "fv":
        return "FV"
    if c in "TD":
        return "TH"
    if c == "l":
        return "L"
    if c == "w":
        return "WQ"
    if c in "oO0" or p.startswith("aU"):
        return "O"
    if c in "uU":
        return "U"
    if c in "aAV@3&":
        return "AI"
    if c in "eEiIy":
        return "E"
    return "CDGK"


class _Event(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("unique_identifier", ctypes.c_uint), ("text_position", ctypes.c_int),
                ("length", ctypes.c_int), ("audio_position", ctypes.c_int), ("sample", ctypes.c_int),
                ("user_data", ctypes.c_void_p), ("id", ctypes.c_char * 8)]


_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.POINTER(_Event))
_lib = None
_rate = 22050


def _espeak():
    global _lib, _rate
    if _lib is None:
        import espeakng_loader
        lib = ctypes.CDLL(espeakng_loader.get_library_path())
        lib.espeak_Initialize.restype = ctypes.c_int
        _rate = lib.espeak_Initialize(2, 0, os.path.dirname(espeakng_loader.get_data_path()).encode(), 1)
        if _rate <= 0:
            raise RuntimeError("espeak-ng failed to start")
        _lib = lib
    return _lib


def say(text: str, out_wav: Path, lang: str = "en", voice: str = "", rate: int = 165, pitch: int = 50,
        range_: int = 60) -> list[tuple[float, str]]:
    """Speaks `text` into out_wav; returns [(seconds, viseme)] - when each mouth shape starts.
    voice: an espeak voice ("en-us", "en-gb", "hi", ...; "+f3" style variants pick another timbre)."""
    lib = _espeak()
    samples: list[bytes] = []
    marks: list[tuple[float, str]] = []

    def cb(wav, n, events):
        if n > 0:
            samples.append(ctypes.string_at(wav, n * 2))
        i = 0
        while events[i].type != 0:
            e = events[i]
            if e.type == 7:                     # phoneme
                marks.append((e.audio_position / 1000.0, e.id.split(b"\0")[0].decode(errors="ignore")))
            i += 1
        return 0
    handle = _CALLBACK(cb)
    lib.espeak_SetSynthCallback(handle)
    v = voice or {"hi": "hi", "en": "en-us"}.get(lang, lang)
    lib.espeak_SetVoiceByName(v.encode())
    lib.espeak_SetParameter(1, rate, 0)
    lib.espeak_SetParameter(3, pitch, 0)
    lib.espeak_SetParameter(4, range_, 0)
    data = text.encode("utf-8")
    lib.espeak_Synth(data, len(data) + 1, 0, 1, 0, 1, None, None)
    lib.espeak_Synchronize()
    pcm = b"".join(samples)
    out_wav = Path(out_wav)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(_rate)
        w.writeframes(pcm)
    out, last = [], None
    for t, ph in marks:
        vis = viseme_of(ph)
        if vis != last:
            out.append((round(t, 3), vis))
            last = vis
    out.append((round(len(pcm) / 2 / _rate, 3), "rest"))
    return out


_LETTERS = [(re.compile(r"[pbm]|[पफबभम]"), "MBP"), (re.compile(r"[fv]|[फ़व]"), "FV"), (re.compile(r"th"), "TH"),
            (re.compile(r"[l]|[ल]"), "L"), (re.compile(r"[wq]"), "WQ"), (re.compile(r"[o]|[ओऔ]|[ोौ]"), "O"),
            (re.compile(r"[u]|[उऊ]|[ुू]"), "U"), (re.compile(r"[a]|[अआ]|[ा]"), "AI"), (re.compile(r"[eiy]|[इईएऐ]|[िीेै]"), "E")]


def estimate_visemes(text: str, seconds: float, start: float = 0.0) -> list[tuple[float, str]]:
    """Mouth shapes timed across a line from someone else's audio (a recording, a TTS voice): letters spread evenly over
    the spoken length, closing at spaces and punctuation."""
    units = [ch for ch in text.lower() if not ch.isspace()] or ["a"]
    step = seconds / len(units)
    out, last = [], None
    for i, ch in enumerate(units):
        vis = "rest" if not ch.isalnum() and not "ऀ" <= ch <= "ॿ" else \
            next((v for rx, v in _LETTERS if rx.match(ch)), "CDGK")
        if vis != last:
            out.append((round(start + i * step, 3), vis))
            last = vis
    out.append((round(start + seconds, 3), "rest"))
    return out


def mouth_at(track: list[tuple[float, str]], t: float) -> tuple[float, float, float]:
    """(open, width, round) at time t, eased between shapes (a mouth never snaps)."""
    if not track or t < track[0][0] or t > track[-1][0] + 0.15:
        return VISEMES["rest"]
    i = max(k for k, (tk, _) in enumerate(track) if tk <= t) if t >= track[0][0] else 0
    a = VISEMES[track[i][1]]
    if i + 1 >= len(track):
        return a
    t0, t1 = track[i][0], track[i + 1][0]
    b = VISEMES[track[i + 1][1]]
    k = min(1.0, max(0.0, (t - t0) / max(0.04, min(0.09, t1 - t0))))     # reach the shape in 40-90 ms
    k = k * k * (3 - 2 * k)
    prev = VISEMES[track[i - 1][1]] if i > 0 else VISEMES["rest"]
    cur = tuple(p + (q - p) * k for p, q in zip(prev, a))
    return cur if t < t1 - 0.03 else tuple(c + (n - c) * 0.3 for c, n in zip(cur, b))


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def mix(clips: list[tuple[float, Path]], total: float, out: Path, rate: int = 44100) -> Path:
    """Places each (start seconds, wav) on one track (mono, 16-bit)."""
    buf = [0.0] * int(total * rate + 1)
    for start, path in clips:
        with wave.open(str(path)) as w:
            sr, n = w.getframerate(), w.getnframes()
            data = struct.unpack(f"<{n}h", w.readframes(n))
        k = sr / rate
        off = int(start * rate)
        for i in range(int(n / k)):
            j = off + i
            if 0 <= j < len(buf):
                buf[j] += data[int(i * k)] / 32768.0
    peak = max(1e-6, max(abs(x) for x in buf))
    g = min(1.0, 0.89 / peak)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{len(buf)}h", *(int(max(-1, min(1, x * g)) * 32767) for x in buf)))
    return out


__all__ = ["say", "estimate_visemes", "mouth_at", "mix", "wav_seconds", "VISEMES", "math"]
