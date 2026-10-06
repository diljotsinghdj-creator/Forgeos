"""Worker configuration, read from environment variables (see README)."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class VoiceProfile:
    id: str
    name: str
    provider: str  # "piper" | "kokoro" | "mock"
    voice: str  # piper: path to .onnx model; kokoro: voice id (e.g. af_heart)
    speed: float = 1.0
    lang: str = "a"  # kokoro language code


@dataclass
class Config:
    data_dir: Path
    token: str = ""
    # Providers. Empty means "not configured" -> the stage fails closed.
    llm_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""
    image_provider: str = ""  # "a1111" | "diffusers" | "mock"
    image_url: str = ""
    image_model: str = ""
    image_steps: int = 0
    asr_provider: str = ""  # "whisper" | "" (estimated captions)
    whisper_model: str = "small"
    whisper_device: str = "auto"
    music_dir: str = ""
    voices: list[VoiceProfile] = field(default_factory=list)
    allow_mock: bool = False

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "productions"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @staticmethod
    def from_env() -> "Config":
        voices: list[VoiceProfile] = []
        raw = _env("CF_VOICES")
        if raw:
            for v in json.loads(raw):
                voices.append(VoiceProfile(**v))
        elif _env("CF_PIPER_MODEL"):
            voices.append(VoiceProfile("default", "Default narrator", "piper", _env("CF_PIPER_MODEL")))
        elif _env("CF_KOKORO_VOICE"):
            voices.append(VoiceProfile("default", "Default narrator", "kokoro", _env("CF_KOKORO_VOICE")))
        cfg = Config(
            data_dir=Path(_env("CF_DATA_DIR", "./creatorforge-data")).resolve(),
            token=_env("CF_WORKER_TOKEN"),
            llm_url=_env("CF_LLM_URL"),
            llm_model=_env("CF_LLM_MODEL"),
            llm_api_key=_env("CF_LLM_API_KEY"),
            image_provider=_env("CF_IMAGE_PROVIDER"),
            image_url=_env("CF_IMAGE_URL"),
            image_model=_env("CF_IMAGE_MODEL"),
            image_steps=int(_env("CF_IMAGE_STEPS", "0") or 0),
            asr_provider=_env("CF_ASR_PROVIDER"),
            whisper_model=_env("CF_WHISPER_MODEL", "small"),
            whisper_device=_env("CF_WHISPER_DEVICE", "auto"),
            music_dir=_env("CF_MUSIC_DIR"),
            voices=voices,
            allow_mock=_env("CF_ALLOW_MOCK") == "1",
        )
        return cfg
