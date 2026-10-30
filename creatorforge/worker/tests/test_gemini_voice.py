"""Google's Gemini voices: Hindi read word for word in the tone of each line, the key never needed on disk, and a
narrator that still finishes the video when Google can't speak."""
import base64
import json
import math
import struct
import wave

import pytest

from creatorforge_worker import providers
from creatorforge_worker.config import VoiceProfile
from creatorforge_worker.providers import gemini_tts
from creatorforge_worker.providers.base import NotConfigured, ProviderError

PCM = b"\x01\x00" * 24000 * 3          # 3 s of 24 kHz audio


class Resp:
    def __init__(self, status, data=None, text=""):
        self.status_code, self._data, self.text = status, data, text or json.dumps(data or {})

    def json(self):
        return self._data


def _audio(pcm=PCM):
    return {"candidates": [{"content": {"parts": [{"inlineData": {"mimeType": "audio/L16;codec=pcm;rate=24000",
                                                                  "data": base64.b64encode(pcm).decode()}}]}}]}


class Client:
    def __init__(self, *answers):
        self.answers, self.calls = list(answers), []

    def post(self, url, json, headers, timeout):
        self.calls.append((url, json, headers))
        return self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    gemini_tts.GeminiVoice._working.clear()
    monkeypatch.setattr(gemini_tts.time, "sleep", lambda s: None)


def test_each_line_is_directed_and_the_transcript_is_exact(tmp_path):
    c = Client(Resp(200, _audio()))
    v = gemini_tts.GeminiVoice("Charon", "news", "hi", key="k-123456", client=c)
    segs = [{"text": "चुनाव आयोग ने क्या किया?", "tone": "question"}, {"text": "तेरह करोड़ नाम।", "tone": "strong"}]
    v.synthesize("चुनाव आयोग ने क्या किया? तेरह करोड़ नाम।", tmp_path / "a.wav", segments=segs)
    url, body, headers = c.calls[0]
    assert url.endswith("/models/gemini-2.5-pro-preview-tts:generateContent") and headers["x-goog-api-key"] == "k-123456"
    prompt = body["contents"][0]["parts"][0]["text"]
    assert prompt.endswith("TRANSCRIPT:\nचुनाव आयोग ने क्या किया?\nतेरह करोड़ नाम।")
    assert "Line 1: genuinely asking" in prompt and "Line 2: hard-hitting" in prompt and "Hindi" in prompt
    cfg = body["generationConfig"]
    assert cfg["responseModalities"] == ["AUDIO"]
    assert cfg["speechConfig"]["voiceConfig"]["prebuiltVoiceConfig"]["voiceName"] == "Charon"
    with wave.open(str(tmp_path / "a.wav")) as w:
        assert (w.getframerate(), w.getnchannels(), w.getnframes()) == (24000, 1, 72000)


def test_a_model_without_quota_hands_over_to_the_next(tmp_path):
    c = Client(Resp(429, text='{"error": {"details": [{"retryDelay": "3s"}]}}'), Resp(200, _audio()))
    v = gemini_tts.GeminiVoice("Kore", "news", "hi", key="k", client=c)
    v.synthesize("एक दो तीन चार", tmp_path / "a.wav")
    assert "pro" in c.calls[0][0] and "flash" in c.calls[1][0]
    v.synthesize("एक दो तीन चार", tmp_path / "b.wav")
    assert "flash" in c.calls[2][0]                       # remembers the model that answers


def test_out_of_quota_and_bad_keys_say_what_to_do(tmp_path):
    v = gemini_tts.GeminiVoice("Kore", "news", "hi", key="k", client=Client(Resp(429, text="quota")))
    with pytest.raises(ProviderError, match="billing"):
        v.synthesize("नमस्ते", tmp_path / "a.wav")
    v = gemini_tts.GeminiVoice("Kore", "news", "hi", key="k", client=Client(Resp(403, text="denied")))
    with pytest.raises(NotConfigured, match="key"):
        v.synthesize("नमस्ते", tmp_path / "a.wav")
    with pytest.raises(NotConfigured):
        gemini_tts.GeminiVoice("Kore", key="")


def test_a_cut_off_take_is_redone(tmp_path):
    short = _audio(b"\x01\x00" * 2400)                   # 0.1 s for 20 words: stopped early
    c = Client(Resp(200, short), Resp(200, _audio()))
    gemini_tts.GeminiVoice("Charon", key="k", client=c).synthesize("शब्द " * 20, tmp_path / "a.wav")
    assert len(c.calls) == 2
    with wave.open(str(tmp_path / "a.wav")) as w:
        assert w.getnframes() == 72000


def test_the_key_comes_from_the_pod_or_the_apps_gemini_script_ai(cfg):
    assert providers.gemini_key(cfg, "job1") == ""
    providers.set_director_llm("job1", {"url": "https://generativelanguage.googleapis.com/v1beta/openai",
                                        "model": "gemini-flash-latest", "key": "app-key"})
    providers.set_director_llm("job2", {"url": "https://api.groq.com/openai/v1", "model": "llama", "key": "groq"})
    assert providers.gemini_key(cfg, "job1") == "app-key" and providers.gemini_key(cfg, "job2") == ""
    assert providers.gemini_key(cfg, lent={"url": "https://generativelanguage.googleapis.com/x", "key": "p"}) == "p"
    cfg.gemini_api_key = "pod-key"
    assert providers.gemini_key(cfg, "job2") == "pod-key"
    v = providers.build_voice(cfg, VoiceProfile("g", "Google", "gemini", "Charon", 1.0, "hi", "news"), "job2")
    assert v.key == "pod-key" and v.lang == "hi" and v.id == "gemini:Charon:news:hi"


@pytest.mark.ffmpeg
def test_a_hindi_video_is_narrated_by_the_google_voice(cfg, monkeypatch):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    prompts = []

    def post(self, model, body):
        prompts.append(body["contents"][0]["parts"][0]["text"])
        words = len(prompts[-1].rsplit("TRANSCRIPT:", 1)[1].split())
        n = int(24000 * 0.4 * words)          # a tone, so the silence trim keeps it
        return Resp(200, _audio(b"".join(struct.pack("<h", int(8000 * math.sin(i / 8))) for i in range(n))))
    monkeypatch.setattr(gemini_tts.GeminiVoice, "_post", post)
    cfg.gemini_api_key = "pod-key"
    cfg.voices.append(VoiceProfile("hindi_anchor_m_google", "Hindi anchor (Google)", "gemini", "Charon", 1.0, "hi", "news"))
    script = ("Chunav Ayog Ka Sach\n\nचुनाव आयोग पर सवाल क्यों उठ रहे हैं?\nVisual: A queue of voters outside a polling booth\n\n"
              "ED ने ₹13 करोड़ जब्त किए।\nVisual: Stacks of rupee notes on a table\nTone: strong\n\n"
              "जवाब आज तक नहीं मिला।\nVisual: A closed office door\nTone: sad\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20,
                                              "voice": "hindi_anchor_m_google"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
    assert job["status"] == "READY", (job.get("error"), job["stages"])
    assert "gemini:Charon" in job["providers"]["voice"] and "unavailable" not in job["providers"]["voice"]
    said = "\n".join(p.rsplit("TRANSCRIPT:", 1)[1] for p in prompts)
    assert "तेरह करोड़ रुपये" in said and "ई डी" in said          # numbers and acronyms said in full


def test_a_one_line_scene_is_said_in_its_tone():
    v = gemini_tts.GeminiVoice("Charon", key="k")
    p = v.prompt("जवाब आज तक नहीं मिला।", [{"text": "जवाब आज तक नहीं मिला।", "tone": "sad"}])
    assert "soft, slow and grave" in p and p.endswith("TRANSCRIPT:\nजवाब आज तक नहीं मिला।")
    p = v.prompt("और आज?", [{"text": "और आज?", "tone": "dramatic"}])
    assert "suspenseful" in p


@pytest.mark.ffmpeg
def test_without_a_key_it_stops_clearly_and_the_pictures_still_go_to_capcut(cfg):
    import io
    import zipfile

    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    cfg.voices.append(VoiceProfile("hindi_anchor_m_google", "Hindi anchor (Google)", "gemini", "Charon", 1.0, "hi", "news"))
    script = ("Chunav Ayog Ka Sach\n\nचुनाव आयोग पर सवाल क्यों उठ रहे हैं?\nVisual: A queue of voters outside a polling booth\n\n"
              "जवाब आज तक नहीं मिला।\nVisual: A closed office door\nTone: sad\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20,
                                              "voice": "hindi_anchor_m_google"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "FAILED" and "Gemini key" in job["stages"]["narration"]["error"]
        r = c.get(f"/v1/productions/{jid}/export")
        assert r.status_code == 200
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = set(z.namelist())
        assert {"media/01_scene.png", "script.txt", "NO_VOICE_YET.txt", "timeline.csv"} <= names
        assert "जवाब आज तक नहीं मिला।" in z.read("script.txt").decode()
