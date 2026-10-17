"""Built-in narrators are human-like; the plain robotic ones are retired without breaking saved choices."""
import json
import re
from pathlib import Path

from creatorforge_worker import providers
from creatorforge_worker.config import VoiceProfile
from creatorforge_worker.providers import tts

SETUP = Path(__file__).resolve().parents[1] / "cloud" / "setup_gpu.sh"


def _builtins():
    line = re.search(r"^CF_VOICES='(.*)'$", SETUP.read_text(), re.M).group(1)
    return json.loads(line)


def test_every_english_narrator_is_human_like():
    voices = _builtins()
    english = [v for v in voices if v["provider"] != "kokoro"]
    assert len(english) >= 15 and voices[0]["id"] == "deep_doc"               # default: a human-like narrator
    assert all(v["provider"] == "chatterbox" and "★" in v["name"] for v in english)
    plain = [v for v in voices if v["provider"] == "kokoro"]
    assert {v["id"] for v in plain} == {"es_f", "fr_f", "hi_f", "it_f", "pt_f"}  # kept only for dubbing
    assert {"indian_m_human", "indian_f_human"} <= {v["id"] for v in voices}
    ids = {v["id"] for v in voices}
    assert set(providers.RETIRED_VOICES.values()) <= ids                      # every retired id has a home


def test_a_saved_retired_voice_gets_its_human_like_version(cfg):
    cfg.voices = [VoiceProfile(v["id"], v["name"], v["provider"], v["voice"], 1.0, v.get("lang", "a"), v.get("style", ""))
                  for v in _builtins()]
    assert providers.voice_profile(cfg, "warm").id == "warm_human"
    assert providers.voice_profile(cfg, "british_m").id == "storyteller_uk"
    assert providers.voice_profile(cfg, None).id == "deep_doc"


def test_a_hindi_timbre_reads_a_hindi_reference(tmp_path, monkeypatch):
    said = []

    class FakeKokoro:
        def __init__(self, vid, speed, lang):
            self.lang = lang

        def synthesize(self, text, out):
            said.append((self.lang, text))
            Path(out).write_bytes(b"RIFF")
    monkeypatch.setattr(tts, "KokoroVoice", FakeKokoro)
    tts.ChatterboxVoice("kokoro:hm_omega", "documentary", tmp_path).reference()
    tts.ChatterboxVoice("kokoro:am_michael", "documentary", tmp_path).reference()
    assert said[0][0] == "h" and "कहानी" in said[0][1]
    assert said[1] == ("a", tts.REF_TEXT)
