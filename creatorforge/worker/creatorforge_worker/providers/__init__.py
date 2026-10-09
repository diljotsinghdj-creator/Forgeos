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


# The app can lend its own (usually much stronger) text AI - Gemini, Groq, ... - to plan a production's script and
# shots. Kept in memory per job only; if it fails, the pod's local model takes over.
_director_llms: dict[str, tuple[str, str, str]] = {}


def set_director_llm(job_id: str, d: dict) -> None:
    url, model, key = str(d.get("url", "")).strip(), str(d.get("model", "")).strip(), str(d.get("key", "")).strip()
    if url.startswith("https://") and model and len(_director_llms) < 500:
        _director_llms[job_id] = (url, model, key)


class _FallbackLLM:
    def __init__(self, primary, backup):
        self.primary, self.backup = primary, backup
        self.id = f"{primary.id} (from app)" + (f", backup {backup.id}" if backup else "")

    def complete_json(self, system: str, user: str) -> str:
        try:
            return self.primary.complete_json(system, user)
        except Exception:  # noqa: BLE001 - quota, bad key, network: keep the video going
            if self.backup is None:
                raise
            self.id = f"{self.backup.id} (app AI failed)"
            return self.backup.complete_json(system, user)


def director_llm(cfg: Config, job_id: str):
    """The best script/shot planner for a job: the app's AI when lent, the pod's local model as backup."""
    try:
        local = build_llm(cfg)
    except NotConfigured:
        local = None
    lent = _director_llms.get(job_id)
    if lent and cfg.llm_url != "mock":
        from .llm_openai import OpenAICompatibleLLM
        return _FallbackLLM(OpenAICompatibleLLM(lent[0], lent[1], lent[2], timeout=180), local)
    if local is None:
        raise NotConfigured("No script model configured (set CF_LLM_URL and CF_LLM_MODEL)")
    return local


_stock_keys: dict[str, tuple[str, str]] = {}


_photo_keys: dict[str, str] = {}


def set_stock_key(job_id: str, d: dict) -> None:
    """Stock keys lent by the app (Pixabay or an old Pexels key; Unsplash for photos), memory only."""
    from .stock_video import detect
    key = str(d.get("key", "")).strip()
    if key and len(_stock_keys) < 500:
        provider = str(d.get("provider", "") or "").strip().lower()
        _stock_keys[job_id] = (provider if provider in ("pexels", "pixabay", "mock") else detect(key), key)
    unsplash = str(d.get("unsplash", "") or "").strip()
    if unsplash and len(_photo_keys) < 500:
        _photo_keys[job_id] = unsplash


def stock_key(job_id: str) -> tuple[str, str] | None:
    return _stock_keys.get(job_id)


def stock_sources(job_id: str, cfg: Config) -> list[tuple[str, str]]:
    """Where this production looks for real footage: the app's keyed library first, then the keyless ones."""
    keyed = _stock_keys.get(job_id)
    if keyed and keyed[0] == "mock":
        return [keyed]
    free = [(name, "") for name in stock_video_free()] if cfg.free_stock else []
    return ([keyed] if keyed else []) + free


def photo_sources(job_id: str, cfg: Config) -> list[tuple[str, str]]:
    """Where this production looks for real photos when no footage fits: Unsplash, Pixabay, then Openverse."""
    keyed = _stock_keys.get(job_id)
    if keyed and keyed[0] == "mock":
        return [("mock", "")]
    out = [("unsplash", _photo_keys[job_id])] if job_id in _photo_keys else []
    if keyed and keyed[0] == "pixabay":
        out.append(keyed)
    if cfg.free_stock:
        from .stock_photo import FREE_SOURCES
        out += [(name, "") for name in FREE_SOURCES]
    return out


def stock_video_free() -> tuple[str, ...]:
    from .stock_video import FREE_SOURCES
    return FREE_SOURCES


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
        prov = DiffusersImageProvider(cfg.image_model, cfg.image_steps, cfg.image_hires)
    else:
        raise NotConfigured("No image model configured (set CF_IMAGE_PROVIDER to a1111 or diffusers)")
    _image_cache[key] = prov
    return prov


def voice_profile(cfg: Config, voice_id: str | None, extra: list[VoiceProfile] | None = None) -> VoiceProfile:
    voices = list(cfg.voices) + list(extra or [])
    if not voices:
        raise NotConfigured("No narration voice configured (set CF_PIPER_MODEL, CF_KOKORO_VOICE, CF_VOICES or add one in the app)")
    if not voice_id:
        return voices[0]
    for v in voices:
        if v.id == voice_id:
            return v
    raise NotConfigured(f"Unknown voice profile '{voice_id}'")


def chatterbox_ready(cfg: Config) -> bool:
    """True when the local Chatterbox server answers (it installs in the background after a pod start)."""
    try:
        import httpx
        return httpx.get(f"{cfg.chatterbox_url.rstrip('/')}/health", timeout=3).status_code == 200
    except Exception:  # noqa: BLE001
        return False


def build_voice(cfg: Config, profile: VoiceProfile):
    if profile.provider == "mock":
        _mock_allowed(cfg, f"voice profile {profile.id}")
        from .mock import MockVoice
        return MockVoice()
    from .tts import ChatterboxVoice, KokoroVoice, PiperVoice
    if profile.provider == "piper":
        return PiperVoice(profile.voice, profile.speed)
    if profile.provider == "kokoro":
        return KokoroVoice(profile.voice, profile.speed, profile.lang)
    if profile.provider == "chatterbox":
        return ChatterboxVoice(profile.voice, profile.style or "natural", cfg.data_dir, cfg.chatterbox_url)
    raise NotConfigured(f"Unknown voice provider '{profile.provider}'")


_video_cache: dict[tuple, object] = {}


def build_video(cfg: Config):
    key = (cfg.video_provider, cfg.video_url, cfg.video_model, cfg.video_quality)
    if key in _video_cache:
        return _video_cache[key]
    p = cfg.video_provider
    if p == "mock":
        _mock_allowed(cfg, "CF_VIDEO_PROVIDER")
        from .mock import MockVideo
        prov = MockVideo()
    elif p == "http":
        if not cfg.video_url:
            raise NotConfigured("CF_VIDEO_URL is required for the http video provider")
        from .video import HttpVideoProvider
        prov = HttpVideoProvider(cfg.video_url)
    elif p == "diffusers":
        from .video import DiffusersVideoProvider
        prov = DiffusersVideoProvider(cfg.video_model, quality=cfg.video_quality)
    else:
        raise NotConfigured("No video model configured (set CF_VIDEO_PROVIDER to diffusers or http)")
    _video_cache[key] = prov
    return prov


def build_music(cfg: Config):
    """Returns None when no music model is configured (the local track library is used instead)."""
    p = cfg.music_provider
    if not p:
        return None
    if p == "mock":
        _mock_allowed(cfg, "CF_MUSIC_PROVIDER")
        from .mock import MockMusic
        return MockMusic()
    if p == "http":
        if not cfg.music_url:
            raise NotConfigured("CF_MUSIC_URL is required for the http music provider")
        from .music import HttpMusicProvider
        return HttpMusicProvider(cfg.music_url)
    if p == "stable-audio":
        from .music import StableAudioProvider
        return StableAudioProvider(cfg.music_model)
    raise NotConfigured(f"Unknown music provider '{p}'")


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
