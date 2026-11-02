"""Narration by ElevenLabs, straight from the script: no exporting chunks, merging MP3s, uploading or syncing.

Every scene is spoken by the creator's own ElevenLabs voice, and every line keeps the writer's Tone: as a direction -
an audio tag on Eleven v3 ([serious], [curious], ...), a pause and a steadier or freer delivery on Multilingual v2.
The neighbouring lines are sent along (v2) so scene after scene sounds like one continuous read. Because each scene
is its own take, the pictures follow the voice exactly - there is nothing to sync afterwards.

The key is the creator's own: ELEVENLABS_API_KEY on the pod, or the key saved in the app (lent with each video,
memory only, never written to disk). Takes are cached, so a resumed or re-rendered video doesn't spend credits again."""
from __future__ import annotations

import re
import subprocess
import tempfile
import time
import wave
from pathlib import Path

from .base import NotConfigured, ProviderError

API = "https://api.elevenlabs.io/v1"
MODELS = {"v3": "eleven_v3", "multilingual": "eleven_multilingual_v2", "flash": "eleven_flash_v2_5"}
LIMIT = {"eleven_v3": 4500, "eleven_multilingual_v2": 9000, "eleven_flash_v2_5": 9000}   # characters per request

# The writer's Tone: as an Eleven v3 audio tag
TAGS = {"calm": "[serious]", "warm": "[warmly]", "question": "[curious]", "dramatic": "[dramatic]",
        "strong": "[firmly]", "urgent": "[urgent]", "sad": "[sad]"}
# Multilingual v2 has no tags: a tone moves stability (lower = more expressive) and style
SETTINGS = {"calm": (0.55, 0.15), "warm": (0.5, 0.25), "question": (0.45, 0.3), "dramatic": (0.35, 0.45),
            "strong": (0.4, 0.4), "urgent": (0.4, 0.35), "sad": (0.5, 0.3)}


def model_id(style: str) -> str:
    return MODELS.get(style or "v3", style if str(style).startswith("eleven_") else MODELS["v3"])


def script_text(segments: list[dict], model: str) -> str:
    """The lines as ElevenLabs should read them: a tag before each line on v3, break tags on the other models."""
    out = []
    for k, sg in enumerate(segments):
        text = str(sg.get("text") or "").strip()
        if not text:
            continue
        tone = sg.get("tone") or "calm"
        if model == "eleven_v3":
            out.append(f"{TAGS.get(tone, '[serious]')} {text}")
        else:
            pause = float(sg.get("pause") or 0)
            out.append(text + (f' <break time="{min(3.0, max(0.3, pause)):.1f}s" />'
                               if k < len(segments) - 1 and pause else ""))
    return "\n".join(out)


def _batches(segments: list[dict], limit: int) -> list[list[dict]]:
    out, cur, n = [], [], 0
    for sg in segments:
        size = len(str(sg.get("text") or "")) + 30
        if cur and n + size > limit:
            out.append(cur)
            cur, n = [], 0
        cur.append(sg)
        n += size
    if cur:
        out.append(cur)
    return out


def _mood_tone(mood: str) -> str:
    m = (mood or "").lower()
    return "dramatic" if any(w in m for w in ("shock", "fear", "tension", "suspense", "anger")) else "calm"


class ElevenLabsVoice:
    """voice: an ElevenLabs voice id. style: v3 (most expressive, audio tags) | multilingual (steadiest) | flash."""

    def __init__(self, voice: str, style: str = "v3", lang: str = "hi", key: str = "", client=None):
        if not key:
            raise NotConfigured("The ElevenLabs voice needs your ElevenLabs key: save it in the app (Settings -> "
                                "ElevenLabs) or add ELEVENLABS_API_KEY to worker.env on the pod")
        if voice and not re.fullmatch(r"[A-Za-z0-9]{6,40}", voice):
            raise NotConfigured(f"'{voice[:40]}' is not an ElevenLabs voice id - pick the voice again in the app")
        if not voice:
            raise NotConfigured("Pick one of your ElevenLabs voices in the app (Library -> Voice Profiles)")
        lang = (lang or "hi").lower()
        self.lang = {"h": "hi", "a": "en", "b": "en"}.get(lang, lang[:2])
        self.voice, self.key, self.client = voice, key, client
        self.model = model_id(style)
        self.mood = ""
        self.previous_text = ""          # the line before this scene, so v2 carries the intonation across scenes
        self.id = f"elevenlabs:{voice}:{self.model}:{self.lang}"

    def _post(self, url: str, body: dict):
        headers = {"xi-api-key": self.key, "Accept": "audio/mpeg"}
        if self.client is not None:
            return self.client.post(url, json=body, headers=headers, timeout=300)
        import httpx
        return httpx.post(url, json=body, headers=headers, timeout=300)

    def _take(self, text: str, tone: str, previous: str = "") -> bytes:
        stab, style = SETTINGS.get(tone, SETTINGS["calm"])
        body: dict = {"text": text, "model_id": self.model,
                      "voice_settings": {"stability": 0.5 if self.model == "eleven_v3" else stab,
                                         "similarity_boost": 0.8, "style": 0.0 if self.model == "eleven_v3" else style,
                                         "use_speaker_boost": True}}
        if self.model != "eleven_multilingual_v2" and self.lang in ("hi", "en"):
            body["language_code"] = self.lang
        if self.model != "eleven_v3" and previous:
            body["previous_text"] = previous[-500:]
        url = f"{API}/text-to-speech/{self.voice}?output_format=mp3_44100_128"
        last = ""
        for attempt in range(4):
            try:
                r = self._post(url, body)
            except Exception as e:  # noqa: BLE001 - network: wait and try again
                last = f"network: {str(e)[:120]}"
                time.sleep(3 * (attempt + 1))
                continue
            if r.status_code == 200 and len(r.content) > 500:
                return r.content
            detail = r.text[:300] if r.status_code != 200 else "empty audio"
            low = detail.lower()
            if "quota" in low or "credits" in low:
                raise ProviderError("ElevenLabs credits used up for this month - top up or upgrade on elevenlabs.io, "
                                    "then tap Retry (finished scenes are kept)")
            if r.status_code == 401:
                raise NotConfigured("ElevenLabs rejected the key - check it in the app (Settings -> ElevenLabs)")
            if r.status_code == 404 or "voice_not_found" in low:
                raise NotConfigured(f"ElevenLabs voice {self.voice} not found in your account - pick it again in "
                                    "Library -> Voice Profiles")
            if r.status_code in (429, 500, 502, 503, 504) or r.status_code == 200:
                last = f"{r.status_code}: {detail[:120]}"
                time.sleep(4 * (attempt + 1))
                continue
            raise ProviderError(f"ElevenLabs: {r.status_code} {detail}")
        raise ProviderError(f"ElevenLabs voice failed: {last}")

    def synthesize(self, text: str, out_wav: Path, segments: list[dict] | None = None) -> None:
        segs = [sg for sg in segments or [] if str(sg.get("text") or "").strip()]
        if not segs:
            segs = [{"text": text, "tone": _mood_tone(self.mood), "pause": 0.0}]
        mp3s = []
        previous = self.previous_text
        for batch in _batches(segs, LIMIT.get(self.model, 4500)):
            spoken = script_text(batch, self.model)
            mp3s.append(self._take(spoken, batch[0].get("tone") or "calm", previous))
            previous = " ".join(str(sg["text"]) for sg in batch)
        self.previous_text = previous
        out_wav = Path(out_wav)
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as d:
            parts = []
            for k, data in enumerate(mp3s):
                src, dst = Path(d) / f"{k}.mp3", Path(d) / f"{k}.wav"
                src.write_bytes(data)
                r = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1",
                                    "-ar", "44100", "-c:a", "pcm_s16le", str(dst)], capture_output=True, text=True)
                if r.returncode != 0 or not dst.is_file():
                    raise ProviderError(f"ElevenLabs audio could not be decoded: {r.stderr[-200:]}")
                parts.append(dst)
            with wave.open(str(out_wav), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(44100)
                for p in parts:
                    with wave.open(str(p), "rb") as rd:
                        w.writeframes(rd.readframes(rd.getnframes()))


def list_voices(key: str, client=None) -> list[dict]:
    """The voices in the creator's ElevenLabs account: [{"id", "name", "labels"}]."""
    if not key:
        raise NotConfigured("Save your ElevenLabs key first (Settings -> ElevenLabs)")
    headers = {"xi-api-key": key}
    if client is not None:
        r = client.get(f"{API}/voices", headers=headers, timeout=30)
    else:
        import httpx
        r = httpx.get(f"{API}/voices", headers=headers, timeout=30)
    if r.status_code == 401:
        raise NotConfigured("ElevenLabs rejected the key (or it lacks the 'Voices: read' permission)")
    if r.status_code >= 400:
        raise ProviderError(f"ElevenLabs: {r.status_code} {r.text[:200]}")
    out = []
    for v in r.json().get("voices") or []:
        labels = v.get("labels") or {}
        desc = ", ".join(str(x) for x in (labels.get("gender"), labels.get("accent"), labels.get("age"),
                                          labels.get("use_case") or labels.get("description")) if x)
        out.append({"id": v.get("voice_id", ""), "name": v.get("name", ""), "labels": desc,
                    "category": v.get("category", "")})
    return [v for v in out if v["id"]]
