"""Builds the configured providers. A stage whose provider is not configured fails closed."""
from __future__ import annotations

from ..config import Config, VoiceProfile
from .base import NotConfigured


def _mock_allowed(cfg: Config, what: str) -> None:
    if not cfg.allow_mock:
        raise NotConfigured(f"{what} is set to 'mock' but CF_ALLOW_MOCK=1 is not set (mock output is test-only)")


def build_llm(cfg: Config):
    if cfg.llm_url == "mock":
        _mock_allowed(cfg, "CF_LLM_URL")
        from .mock import MockLLM
        return MockLLM()
    if not cfg.llm_url or not cfg.llm_model:
        raise NotConfigured("No script model configured (set CF_LLM_URL and CF_LLM_MODEL)")
    from .llm_openai import OpenAICompatibleLLM
    return OpenAICompatibleLLM(cfg.llm_url, cfg.llm_model, cfg.llm_api_key)


_image_cache: dict[tuple, object] = {}


def build_image(cfg: Config):
    key = (cfg.image_provider, cfg.image_url, cfg.image_model, cfg.image_steps)
    if key in _image_cache:
        return _image_cache[key]
    p = cfg.image_provider
    if p == "mock":
        _mock_allowed(cfg, "CF_IMAGE_PROVIDER")
        from .mock import MockImage
        prov = MockImage()
    elif p == "a1111":
        if not cfg.image_url:
            raise NotConfigured("CF_IMAGE_URL is required for the a1111 image provider")
        from .image_a1111 import A1111ImageProvider
        prov = A1111ImageProvider(cfg.image_url, cfg.image_steps)
    elif p == "diffusers":
        from .image_diffusers import DiffusersImageProvider
        prov = DiffusersImageProvider(cfg.image_model, cfg.image_steps)
    else:
        raise NotConfigured("No image model configured (set CF_IMAGE_PROVIDER to a1111 or diffusers)")
    _image_cache[key] = prov
    return prov


def voice_profile(cfg: Config, voice_id: str | None) -> VoiceProfile:
    if not cfg.voices:
        raise NotConfigured("No narration voice configured (set CF_PIPER_MODEL, CF_KOKORO_VOICE or CF_VOICES)")
    if not voice_id:
        return cfg.voices[0]
    for v in cfg.voices:
        if v.id == voice_id:
            return v
    raise NotConfigured(f"Unknown voice profile '{voice_id}'")


def build_voice(cfg: Config, profile: VoiceProfile):
    if profile.provider == "mock":
        _mock_allowed(cfg, f"voice profile {profile.id}")
        from .mock import MockVoice
        return MockVoice()
    from .tts import KokoroVoice, PiperVoice
    if profile.provider == "piper":
        return PiperVoice(profile.voice, profile.speed)
    if profile.provider == "kokoro":
        return KokoroVoice(profile.voice, profile.speed, profile.lang)
    raise NotConfigured(f"Unknown voice provider '{profile.provider}'")


_asr = None


def build_asr(cfg: Config):
    """Returns None when Whisper is not configured; captions then use estimated timing
    and the production records caption_source='estimated'."""
    global _asr
    if cfg.asr_provider != "whisper":
        return None
    if _asr is None:
        from .asr_whisper import WhisperASR
        _asr = WhisperASR(cfg.whisper_model, cfg.whisper_device)
    return _asr
