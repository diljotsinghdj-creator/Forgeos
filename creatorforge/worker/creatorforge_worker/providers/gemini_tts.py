"""Narration by Google's Gemini speech models - the most natural Hindi available (AI4Bharat's 2026 listening study of
Indian-language voices ranked Gemini first in 9 of 10 languages). The narrator is directed like an actor: who they are,
how the language should sound, and the tone of every line (providers.delivery), then the transcript word for word.

The key is the creator's own Gemini key: GEMINI_API_KEY on the pod, or the app's Script AI key when that is Gemini
(lent with each video, memory only). Output is 24 kHz mono PCM."""
from __future__ import annotations

import base64
import re
import threading
import time
import wave
from pathlib import Path

from .base import NotConfigured, ProviderError

API = "https://generativelanguage.googleapis.com/v1beta"
MODELS = ("gemini-2.5-pro-preview-tts", "gemini-2.5-flash-preview-tts")

# Gemini's male voices (the rest are female), so a fallback narrator keeps the same gender.
MALE = {"Charon", "Orus", "Puck", "Fenrir", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Algenib", "Rasalgethi",
        "Alnilam", "Schedar", "Achird", "Zubenelgenubi", "Sadachbia", "Sadaltager"}

# Who is speaking. Profiles pick one with "style".
PERSONAS = {
    "news": "a senior Hindi TV news anchor from Delhi presenting a prime-time investigation: authoritative, clear, "
            "confident, never shouting",
    "documentary": "a deep-voiced documentary narrator telling a true story that matters: measured, grave, intimate",
    "bold": "a fearless investigative journalist laying out evidence: sharp, direct, every fact lands",
    "storyteller": "a warm storyteller who makes listeners lean in: natural, expressive, close to the microphone",
}
LANGUAGES = {
    "hi": "everyday spoken Hindi as heard on Indian news channels - Hindustani, not bookish Sanskritised Hindi. "
          "English words and names inside the Hindi (Election Commission, Supreme Court, BJP) are said the way "
          "Indians say them in Hindi speech. Devanagari numbers and words are read naturally",
    "en": "natural spoken English",
}
TONES = {
    "calm": "steady and clear, setting the scene",
    "warm": "warm and close, like talking to one person",
    "question": "a real question - the voice rises and leaves it hanging for a beat",
    "dramatic": "slower and weighty, building suspense, a breath before the key words",
    "strong": "punchy and firm - every word lands, then a short pause",
    "urgent": "faster and pressing, with energy",
    "sad": "quiet and slower, with respect for the people it is about",
}


class GeminiVoice:
    """voice: a Gemini prebuilt voice (Charon, Orus, Kore, Sulafat, ...). style: a PERSONAS key."""
    _lock = threading.Lock()
    _working: dict[str, str] = {}     # key fingerprint -> the model that last answered (skips ones without quota)

    def __init__(self, voice: str, style: str = "news", lang: str = "hi", key: str = "", models: tuple[str, ...] = MODELS,
                 client=None):
        if not key:
            raise NotConfigured("The Google voice needs a Gemini key: add your Gemini key in the app (Settings -> "
                                "Script AI) or set GEMINI_API_KEY on the pod")
        lang = (lang or "hi").lower()
        self.lang = {"h": "hi", "a": "en", "b": "en"}.get(lang, lang[:2])
        self.voice = voice or "Charon"
        self.style = style if style in PERSONAS else "news"
        self.key = key
        self.models = tuple(models) or MODELS
        self.client = client
        self.mood = ""
        self.id = f"gemini:{self.voice}:{self.style}:{self.lang}"

    def prompt(self, text: str, segments: list[dict] | None = None) -> str:
        lines = [str(s.get("text") or "").strip() for s in segments or []]
        lines = [ln for ln in lines if ln]
        language = LANGUAGES.get(self.lang, "natural spoken " + self.lang)
        notes = [f"Read the TRANSCRIPT aloud exactly as written, word for word - do not translate, add, skip or "
                 f"repeat words, and never read these notes or the headings.",
                 f"VOICE: {PERSONAS[self.style]}.",
                 f"LANGUAGE: {language}.",
                 "DELIVERY: like a real person, not a machine - natural rhythm, short pauses at commas, a clear pause "
                 "at each full stop or ।, emphasis on numbers, names and the key word of each line."]
        if segments and len(lines) > 1:
            notes.append("LINE NOTES (one per transcript line, in order):")
            notes += [f"Line {i}: {TONES.get(s.get('tone', 'calm'), TONES['calm'])}."
                      for i, s in enumerate((s for s in segments if str(s.get('text') or '').strip()), 1)]
            transcript = "\n".join(lines)
        else:
            mood = (self.mood or "").lower()
            if any(w in mood for w in ("shock", "fear", "tension", "suspense", "anger", "intrigue")):
                notes.append(f"MOOD: {TONES['dramatic']}.")
            elif segments:
                notes.append(f"MOOD: {TONES.get(segments[0].get('tone', 'calm'), TONES['calm'])}.")
            transcript = text.strip()
        return "\n".join(notes) + "\n\nTRANSCRIPT:\n" + transcript

    def _post(self, model: str, body: dict):
        if self.client is not None:
            return self.client.post(f"{API}/models/{model}:generateContent", json=body,
                                    headers={"x-goog-api-key": self.key}, timeout=300)
        import httpx
        return httpx.post(f"{API}/models/{model}:generateContent", json=body, headers={"x-goog-api-key": self.key},
                          timeout=300)

    def _audio(self, text: str, segments: list[dict] | None) -> tuple[bytes, int]:
        body = {"contents": [{"role": "user", "parts": [{"text": self.prompt(text, segments)}]}],
                "generationConfig": {"responseModalities": ["AUDIO"],
                                     "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": self.voice}}}}}
        fp = self.key[-6:]
        with self._lock:
            first = self._working.get(fp)
        order = ([first] if first in self.models else []) + [m for m in self.models if m != first]
        last, wait = "", 0.0
        for rnd in range(4):
            if wait:
                time.sleep(wait)
            wait = 0.0
            for model in order:
                try:
                    r = self._post(model, body)
                except Exception as e:  # noqa: BLE001 - network: try again next round
                    last = f"network: {str(e)[:120]}"
                    wait = max(wait, 5.0)
                    continue
                if r.status_code in (401, 403):
                    raise NotConfigured(f"Google rejected the Gemini key ({r.status_code}) - check it in the app or "
                                        f"GEMINI_API_KEY on the pod")
                if r.status_code in (400, 404) and ("not found" in r.text.lower() or "not supported" in r.text.lower()):
                    last = f"{model} unavailable"
                    continue
                if r.status_code == 429 or r.status_code >= 500:
                    last = f"{model}: {'quota' if r.status_code == 429 else 'server busy'}"
                    hint = re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', r.text)
                    wait = max(wait, min(60.0, float(hint.group(1)) + 1 if hint else 10.0 * (rnd + 1)))
                    continue
                if r.status_code >= 400:
                    raise ProviderError(f"gemini voice: {r.status_code} {r.text[:300]}")
                pcm, rate, why = _pcm(r.json())
                if not pcm:
                    last, wait = f"{model}: no audio ({why})", max(wait, 2.0)
                    continue
                with self._lock:
                    self._working[fp] = model
                return pcm, rate
        if "quota" in last:
            raise ProviderError("Gemini voice quota reached - Google's free tier allows only a few voice requests a "
                                "day; turn on billing for your Gemini key (a 10-minute video costs well under $1) or "
                                "resume the video later - finished scenes are kept")
        raise ProviderError(f"gemini voice failed: {last}")

    def synthesize(self, text: str, out_wav: Path, segments: list[dict] | None = None) -> None:
        words = max(1, len(text.split()))
        pcm, rate = self._audio(text, segments)
        secs = len(pcm) / 2 / rate
        if secs < words * 0.12 or secs > words * 1.2 + 4:
            # cut off or rambling (the model sometimes stops early or repeats): one fresh take
            pcm2, rate2 = self._audio(text, segments)
            secs2 = len(pcm2) / 2 / rate2
            if abs(secs2 - words * 0.4) < abs(secs - words * 0.4):
                pcm, rate = pcm2, rate2
        out_wav = Path(out_wav)
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out_wav), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(pcm)


def _pcm(data: dict) -> tuple[bytes, int, str]:
    """The audio in a generateContent answer: (16-bit PCM, sample rate, why-empty)."""
    cands = data.get("candidates") or []
    if not cands:
        fb = (data.get("promptFeedback") or {}).get("blockReason", "")
        return b"", 24000, fb or "empty answer"
    out, rate = b"", 24000
    for part in (cands[0].get("content") or {}).get("parts") or []:
        inline = part.get("inlineData") or part.get("inline_data") or {}
        if inline.get("data"):
            m = re.search(r"rate=(\d+)", inline.get("mimeType") or inline.get("mime_type") or "")
            rate = int(m.group(1)) if m else rate
            out += base64.b64decode(inline["data"])
    return out[: len(out) - len(out) % 2], rate, cands[0].get("finishReason", "no audio part")
