"""faster-whisper word timestamps for synchronized captions."""
from __future__ import annotations

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
        with self._lock:
            if self._model is None:
                self._model = WhisperModel(self.model_name, device=self.device)
            try:
                segments, _ = self._model.transcribe(str(wav), word_timestamps=True, vad_filter=False)
                out = [Word(w.word.strip(), float(w.start), float(w.end)) for s in segments for w in (s.words or [])]
            except Exception as e:  # noqa: BLE001
                raise ProviderError(f"whisper transcription failed: {e}") from e
        return [w for w in out if w.text]
