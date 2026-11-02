"""ElevenLabs narration straight from the script: each line directed by its Tone:, the creator's own voice and key
(lent by the app or on the pod, never on disk), and a clear stop - not a different voice - when it can't speak."""
import subprocess

import pytest

from creatorforge_worker import providers
from creatorforge_worker.config import VoiceProfile
from creatorforge_worker.providers import elevenlabs_tts as el
from creatorforge_worker.providers.base import NotConfigured, ProviderError

VID = "JBFqnCBsd6RMkjVDRZzb"


class Resp:
    def __init__(self, status, content=b"", text=""):
        self.status_code, self.content, self.text = status, content, text


def _mp3(seconds: float) -> bytes:
    return subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
                           f"sine=frequency=220:duration={seconds:.2f}", "-ac", "1", "-f", "mp3", "-"],
                          capture_output=True, check=True).stdout


@pytest.fixture(autouse=True)
def _no_wait(monkeypatch):
    monkeypatch.setattr(el.time, "sleep", lambda s: None)


def test_v3_gets_an_audio_tag_per_line_and_v2_gets_pauses():
    segs = [{"text": "13.3 करोड़ नाम कटे।", "tone": "strong", "pause": 0.8},
            {"text": "ज़िम्मेदार कौन?", "tone": "question", "pause": 0.7}]
    assert el.script_text(segs, "eleven_v3") == "[firmly] 13.3 करोड़ नाम कटे।\n[curious] ज़िम्मेदार कौन?"
    v2 = el.script_text(segs, "eleven_multilingual_v2")
    assert '<break time="0.8s" />' in v2 and "[" not in v2 and v2.endswith("ज़िम्मेदार कौन?")
    assert el.model_id("multilingual") == "eleven_multilingual_v2" and el.model_id("") == "eleven_v3"


def test_errors_say_what_to_do():
    with pytest.raises(NotConfigured, match="ElevenLabs key"):
        el.ElevenLabsVoice(VID, key="")
    with pytest.raises(NotConfigured, match="not an ElevenLabs voice id"):
        el.ElevenLabsVoice("../../v1/user", key="k")

    class C:
        def __init__(self, r):
            self.r = r

        def post(self, *a, **k):
            return self.r
    quota = el.ElevenLabsVoice(VID, key="k", client=C(Resp(401, text='{"detail":{"status":"quota_exceeded"}}')))
    with pytest.raises(ProviderError, match="credits"):
        quota._take("नमस्ते", "calm")
    bad = el.ElevenLabsVoice(VID, key="k", client=C(Resp(401, text='{"detail":{"status":"invalid_api_key"}}')))
    with pytest.raises(NotConfigured, match="rejected the key"):
        bad._take("नमस्ते", "calm")


@pytest.mark.ffmpeg
def test_a_long_scene_is_split_and_joined_and_v2_carries_the_previous_line(tmp_path):
    calls = []

    class C:
        def post(self, url, json, headers, timeout):
            calls.append((url, json, headers))
            return Resp(200, _mp3(1.0))
    v = el.ElevenLabsVoice(VID, "multilingual", "hi", key="secret", client=C())
    v.previous_text = "पिछली लाइन।"
    segs = [{"text": "क" * 5000, "tone": "calm", "pause": 0.5}, {"text": "ख" * 5000, "tone": "sad", "pause": 0}]
    v.synthesize("", tmp_path / "o.wav", segs)
    import wave
    with wave.open(str(tmp_path / "o.wav")) as w:
        assert 1.9 < w.getnframes() / w.getframerate() < 2.3        # two takes joined
    assert len(calls) == 2 and calls[0][2]["xi-api-key"] == "secret" and VID in calls[0][0]
    assert calls[0][1]["previous_text"] == "पिछली लाइन।" and calls[1][1]["previous_text"].startswith("क")
    assert v.previous_text.startswith("ख")


def test_the_key_is_lent_by_the_app_or_set_on_the_pod(cfg):
    job = "eleven-key-job"
    try:
        assert providers.elevenlabs_key(cfg, job) == ""
        providers.set_elevenlabs_key(job, {"key": " app-key "})
        assert providers.elevenlabs_key(cfg, job) == "app-key"
        assert providers.elevenlabs_key(cfg, lent={"key": "preview"}) == "preview"
        cfg.elevenlabs_api_key = "pod-key"
        assert providers.elevenlabs_key(cfg, "other") == "pod-key"
        v = providers.build_voice(cfg, VoiceProfile("e", "Mine", "elevenlabs", VID, 1.0, "hi", "v3"), job)
        assert v.key == "app-key" and v.model == "eleven_v3" and v.lang == "hi"
    finally:
        providers._eleven_keys.pop(job, None)


def test_profiles_only_take_voice_ids_and_models(tmp_path):
    from creatorforge_worker.library import VoiceStore
    s = VoiceStore(tmp_path / "v.json")
    ok = s._clean({"name": "Mera narrator", "provider": "elevenlabs", "voice": VID, "style": "v3", "lang": "hi"})
    assert ok["provider"] == "elevenlabs" and ok["style"] == "v3"
    with pytest.raises(ValueError, match="voice id"):
        s._clean({"name": "x", "provider": "elevenlabs", "voice": "Adam the narrator"})
    with pytest.raises(ValueError, match="v3, multilingual or flash"):
        s._clean({"name": "x", "provider": "elevenlabs", "voice": VID, "style": "documentary"})


@pytest.mark.ffmpeg
def test_a_hindi_script_video_is_narrated_by_elevenlabs_with_the_key_never_saved(cfg, monkeypatch):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    sent = []

    def post(self, url, body):
        sent.append(body)
        return Resp(200, _mp3(0.45 * max(1, len(body["text"].split()))))
    monkeypatch.setattr(el.ElevenLabsVoice, "_post", post)
    cfg.voices.append(VoiceProfile("my_eleven", "My ElevenLabs", "elevenlabs", VID, 1.0, "hi", "v3"))
    script = ("Chunav Ayog Ka Sach\n\nचुनाव आयोग पर सवाल क्यों उठ रहे हैं?\nVisual: A queue of voters outside a polling booth\n\n"
              "ED ने ₹13 करोड़ जब्त किए।\nVisual: Stacks of rupee notes on a table\nTone: strong\n\n"
              "जवाब आज तक नहीं मिला।\nVisual: A closed office door\nTone: sad\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20, "voice": "my_eleven",
                                              "elevenlabs": {"key": "lent-secret"}}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
    assert job["status"] == "READY", (job.get("error"), job["stages"])
    assert "elevenlabs:" + VID in job["providers"]["voice"]
    said = "\n".join(b["text"] for b in sent)
    assert "[firmly]" in said and "[sad]" in said and "तेरह करोड़ रुपये" in said
    for f in (cfg.data_dir).rglob("*.json"):
        assert "lent-secret" not in f.read_text(errors="ignore")


@pytest.mark.ffmpeg
def test_without_a_key_it_stops_and_says_so_instead_of_using_another_voice(cfg):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    cfg.voices.append(VoiceProfile("my_eleven", "My ElevenLabs", "elevenlabs", VID, 1.0, "hi", "v3"))
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": ("Chunav Ayog Ka Sach\n\nचुनाव आयोग पर सवाल क्यों उठ रहे हैं?\n"
                                                         "Visual: A queue of voters outside a polling booth\n\n"
                                                         "जवाब आज तक नहीं मिला।\nVisual: A closed office door\nTone: sad\n"),
                                              "duration_s": 20, "voice": "my_eleven"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
    assert job["status"] == "FAILED" and "ElevenLabs" in job["stages"]["narration"]["error"]


def test_the_voice_picker_lists_the_accounts_voices(cfg, monkeypatch):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    class C:
        def get(self, url, headers, timeout):
            assert headers["xi-api-key"] == "k"
            return type("R", (), {"status_code": 200, "text": "", "json": lambda s: {"voices": [
                {"voice_id": VID, "name": "George", "category": "premade",
                 "labels": {"gender": "male", "accent": "british", "age": "middle aged"}}]}})()
    real = el.list_voices
    monkeypatch.setattr(el, "list_voices", lambda key: real(key, client=C()))
    with TestClient(create_app(cfg)) as c:
        r = c.post("/v1/voice/elevenlabs/voices", json={"key": "k"})
        assert r.status_code == 200 and r.json()[0] == {"id": VID, "name": "George", "category": "premade",
                                                        "labels": "male, british, middle aged"}
        assert c.post("/v1/voice/elevenlabs/voices", json={}).status_code == 400
