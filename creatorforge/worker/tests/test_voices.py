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
    english = [v for v in voices if v["provider"] != "kokoro" and v.get("lang", "a") == "a"]
    assert len(english) >= 15 and voices[0]["id"] == "deep_doc"               # default: a human-like narrator
    assert all(v["provider"] == "chatterbox" and "★" in v["name"] for v in english)
    plain = [v for v in voices if v["provider"] == "kokoro"]
    assert {v["id"] for v in plain} == {"es_f", "fr_f", "it_f", "pt_f"}       # kept only for dubbing
    hindi = {v["id"]: v for v in voices if v.get("lang") == "hi"}
    assert {"hindi_m_human", "hindi_f_human", "hi_f"} <= set(hindi)          # Hindi, human-like, male and female
    assert all(v["provider"] == "chatterbox" for v in hindi.values())
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


def test_hindi_voices_speak_hindi_and_fall_back_to_a_hindi_voice(cfg, monkeypatch):
    sent = []

    class Resp:
        status_code = 200

    def fake_post(url, json, timeout):
        sent.append(json)
        Path(json["out"]).write_bytes(b"RIFF")
        return Resp()
    import httpx
    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(tts.ChatterboxVoice, "reference", lambda self: "")
    cfg.voices = [VoiceProfile(v["id"], v["name"], v["provider"], v["voice"], 1.0, v.get("lang", "a"), v.get("style", ""))
                  for v in _builtins()]
    hindi = providers.build_voice(cfg, providers.voice_profile(cfg, "hindi_m_human"))
    english = providers.build_voice(cfg, providers.voice_profile(cfg, "indian_m_human"))
    assert hindi.lang == "hi" and english.lang == "en"
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    hindi.synthesize("नमस्ते। यह एक परीक्षण है।", cfg.data_dir / "h.wav")
    english.synthesize("Hello.", cfg.data_dir / "e.wav")
    assert sent[0]["lang"] == "hi" and sent[1]["lang"] == "en"


def test_hindi_sentences_split_on_the_danda():
    from creatorforge_worker import director
    assert director.split_sentences("यह पहला वाक्य है। यह दूसरा है।") == ["यह पहला वाक्य है।", "यह दूसरा है।"]


def test_a_hindi_script_in_devanagari_is_read_as_narration():
    from creatorforge_worker import director
    raw = ("वोटर लिस्ट से नाम गायब\nOn-screen hook: आपका नाम गायब?\n\nसोचिए, वोटर लिस्ट से आपका नाम गायब?\n"
           "Visual: A voter ID card\n\nये है क्या? एस आई आर।\nVisual: A voter register\n\n"
           "आपने अपना नाम कब जाँचा था?\nVisual: The Election Commission building\n")
    spec = director.ProductionSpec.from_dict({"script": raw})
    assert spec.script.startswith("सोचिए") and "Visual" not in spec.script
    assert len(spec.shots) == 3 and spec.shots[0][1] == "A voter ID card"
    assert director._words("ये है क्या?") == ["ये", "है", "क्या"]
