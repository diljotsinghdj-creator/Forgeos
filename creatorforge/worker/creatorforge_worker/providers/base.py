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


# ---- cancellation reaching inside long model calls -------------------------------------------
import threading as _threading

_local = _threading.local()


def set_cancel(event) -> None:
    """The runner registers the current production's cancel event for its worker thread."""
    _local.event = event


def cancelled() -> bool:
    ev = getattr(_local, "event", None)
    return ev is not None and ev.is_set()


def step_callback(pipe) -> dict:
    """diffusers kwargs that stop a running image/video generation between denoising steps when the user cancels."""
    import inspect
    try:
        params = inspect.signature(pipe.__call__).parameters
    except (TypeError, ValueError, AttributeError):
        return {}
    if "callback_on_step_end" not in params:
        return {}

    def on_step_end(p, step, timestep, callback_kwargs):
        if cancelled():
            p._interrupt = True
        return callback_kwargs
    return {"callback_on_step_end": on_step_end}
