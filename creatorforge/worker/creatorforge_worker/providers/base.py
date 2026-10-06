"""Provider interfaces. Every generation engine sits behind one of these so it can be
swapped without touching the pipeline or the Android app."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class ProviderError(RuntimeError):
    """A generation failed. Never swallowed: the stage is marked FAILED."""


class NotConfigured(ProviderError):
    pass


@dataclass
class Word:
    text: str
    start: float
    end: float


class LLMProvider(Protocol):
    id: str

    def complete_json(self, system: str, user: str) -> str: ...


class ImageProvider(Protocol):
    id: str

    def generate(self, prompt: str, negative: str, width: int, height: int, seed: int, out: Path) -> None: ...


class VoiceProvider(Protocol):
    id: str

    def synthesize(self, text: str, out_wav: Path) -> None: ...


class ASRProvider(Protocol):
    id: str

    def words(self, wav: Path) -> list[Word]: ...
