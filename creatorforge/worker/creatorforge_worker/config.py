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
    provider: str  # "piper" | "kokoro" | "chatterbox" | "mock"
    voice: str  # piper: .onnx path; kokoro: voice id (af_heart); chatterbox: default | kokoro:<id> | asset:<id>
    speed: float = 1.0
    lang: str = "a"  # kokoro language code
    style: str = ""  # chatterbox delivery: documentary | natural | calm | energetic


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
    image_hires: bool = True  # SDXL-family 1.5x refine pass (sharper faces and detail)
    video_provider: str = ""  # "diffusers" | "http" | "mock" ("" = AI video clips unavailable)
    video_url: str = ""
    video_model: str = ""
    chatterbox_url: str = "http://127.0.0.1:8770"
    video_quality: str = "fast"  # "fast" | "balanced" | "best" (AI video clips: speed vs detail)
    asr_provider: str = ""  # "whisper" | "" (estimated captions)
    whisper_model: str = "small"
    whisper_device: str = "auto"
    music_dir: str = ""
    sfx_dir: str = ""
    music_provider: str = ""  # "stable-audio" | "http" | "mock" ("" = use the local library)
    music_url: str = ""
    music_model: str = ""
    voices: list[VoiceProfile] = field(default_factory=list)
    youtube_api_key: str = ""  # optional, free: adds YouTube to the Trend Radar
    free_stock: bool = False  # keyless footage (NASA, Wikimedia Commons) for beats the planner marks; on for real pods
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
            image_hires=_env("CF_IMAGE_HIRES", "1") not in ("0", "false", "off"),
            video_provider=_env("CF_VIDEO_PROVIDER"),
            video_url=_env("CF_VIDEO_URL"),
            video_model=_env("CF_VIDEO_MODEL"),
            video_quality=_env("CF_VIDEO_QUALITY", "fast"),
            chatterbox_url=_env("CF_CHATTERBOX_URL", "http://127.0.0.1:8770"),
            asr_provider=_env("CF_ASR_PROVIDER"),
            whisper_model=_env("CF_WHISPER_MODEL", "small"),
            whisper_device=_env("CF_WHISPER_DEVICE", "auto"),
            music_dir=_env("CF_MUSIC_DIR"),
            sfx_dir=_env("CF_SFX_DIR"),
            music_provider=_env("CF_MUSIC_PROVIDER"),
            music_url=_env("CF_MUSIC_URL"),
            music_model=_env("CF_MUSIC_MODEL"),
            voices=voices,
            youtube_api_key=_env("CF_YOUTUBE_API_KEY"),
            allow_mock=_env("CF_ALLOW_MOCK") == "1",
            free_stock=_env("CF_FREE_STOCK", "1") != "0",
        )
        return cfg
