"""Exact word timings for narration (faster-whisper, MIT; model base.en, int8 on CPU).
word_times(wav) -> [(word, start_s, end_s)]. Replaces the length-based estimate used for captions.
The model downloads once to creatorforge-data/models/whisper (git-ignored)."""
import wave
from pathlib import Path

import numpy as np

_MODEL = None
MODELS = Path(__file__).resolve().parents[2] / "creatorforge-data" / "models" / "whisper"


def _model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("base.en", device="cpu", compute_type="int8", download_root=str(MODELS))
    return _MODEL


def _load(path):
    with wave.open(str(path)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch == 2:
        a = a.reshape(-1, 2).mean(1)
    return np.interp(np.arange(0, len(a), sr / 16000), np.arange(len(a)), a).astype(np.float32)


def word_times(wav, prompt=""):
    """prompt: the script line, so names and numbers are spelled as written."""
    segs, _ = _model().transcribe(_load(wav), word_timestamps=True, initial_prompt=prompt or None, language="en")
    return [(x.word.strip(), float(x.start), float(x.end)) for s in segs for x in s.words]
