"""faster-whisper word timestamps for synchronized captions."""
from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path

from .base import NotConfigured, ProviderError, Word


class WhisperASR:
    _lock = threading.Lock()

    def __init__(self, model: str = "small", device: str = "auto"):
        self.model_name = model
        self.device = device
        self.id = f"whisper:{model}"
        self._model = None

    def words(self, wav: Path) -> list[Word]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise NotConfigured("faster-whisper not installed: pip install 'creatorforge-worker[whisper]'") from e
        audio = _load_audio(wav)
        with self._lock:
            try:
                if self._model is None:
                    self._model = WhisperModel(self.model_name, device=self.device)
                out = self._run(audio)
            except Exception as e:  # noqa: BLE001
                if "out of memory" not in str(e).lower() and "cuda" not in str(e).lower():
                    raise ProviderError(f"whisper transcription failed: {e}") from e
                # The image/video/voice models can fill the GPU on a long video: free what the GPU caches and
                # finish on the CPU (the small model transcribes a 7-minute narration in a minute or two there).
                self._model = None
                _free_gpu()
                try:
                    self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
                    out = self._run(audio)
                except Exception as e2:  # noqa: BLE001
                    raise ProviderError(f"whisper transcription failed: {e2}") from e2
        return [w for w in out if w.text]

    def listen(self, wav: Path, lang: str = "hi") -> dict:
        """What the take says: {text, lang, prob} - the language Whisper hears, and the words in `lang`'s script
        (forcing the language keeps Hindi in Devanagari rather than Urdu letters; English still comes out as English)."""
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise NotConfigured("faster-whisper not installed") from e
        audio = _load_audio(wav)
        with self._lock:
            try:
                if self._model is None:
                    self._model = WhisperModel(self.model_name, device=self.device)
                heard_lang, prob = "", 0.0
                try:
                    heard_lang, prob, _ = self._model.detect_language(audio)
                except Exception:  # noqa: BLE001 - older faster-whisper: the transcript alone decides
                    pass
                segments, _ = self._model.transcribe(audio, language=lang, beam_size=1, vad_filter=False)
                text = " ".join(s.text.strip() for s in segments)
            except Exception as e:  # noqa: BLE001
                raise ProviderError(f"whisper listen failed: {e}") from e
        return {"text": text, "lang": heard_lang, "prob": float(prob)}

    def _run(self, audio) -> list[Word]:
        segments, _ = self._model.transcribe(audio, word_timestamps=True, vad_filter=False)
        return [Word(w.word.strip(), float(w.start), float(w.end)) for s in segments for w in (s.words or [])]


def _free_gpu() -> None:
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:  # noqa: BLE001 - no torch: nothing to free
        pass


def _load_audio(path: Path):
    """16 kHz mono float32 via ffmpeg. Bypasses faster-whisper's PyAV decoder, which breaks on
    newer PyAV releases ("open() got an unexpected keyword argument 'metadata_errors'")."""
    import numpy as np

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return str(path)
    raw = subprocess.run([ffmpeg, "-nostdin", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()
