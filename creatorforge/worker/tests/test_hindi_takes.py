"""Every Hindi take is heard back before it is used: a take that slips into English, reads something else or skips the
script is recorded again; the writer's Tone reaches one-line scenes too."""
from creatorforge_worker.providers import delivery

SCRIPT = "और आज? वोटर लिस्ट से तेरह दशमलव तीन करोड़ नाम कटे।"


def test_a_good_hindi_take_passes_even_with_whisper_spellings():
    heard = {"text": "और आज, वोटर लिस्ट से तेरह दशमलव तीन करोड नाम कटे", "lang": "hi", "prob": 0.9}
    score, problem = delivery.judge(SCRIPT, heard, "hi")
    assert problem == "" and score > 0.9


def test_english_or_wrong_words_are_caught():
    leaked = {"text": "How to say it slow and suspenseful और आज वोटर लिस्ट", "lang": "hi", "prob": 0.5}
    assert "English" in delivery.judge(SCRIPT, leaked, "hi")[1]
    english = {"text": "And today, thirteen crore names were cut", "lang": "en", "prob": 0.95}
    assert "not Hindi" in delivery.judge(SCRIPT, english, "hi")[1]
    garbled = {"text": "अरे बाबा कुछ और ही बात", "lang": "hi", "prob": 0.8}
    assert "words heard" in delivery.judge(SCRIPT, garbled, "hi")[1]
    assert delivery.judge("Hello there", english, "en") == (1.0, "")


def test_a_one_line_scene_keeps_the_writers_tone():
    beats = [{"text": "जवाब आज तक नहीं मिला।", "extra": {"tone": "sad"}}]
    assert delivery.segments(beats, "जवाब आज तक नहीं मिला।")[0]["tone"] == "sad"
    # the narration was reworded (pronunciation list): the writer's tone still holds
    assert delivery.segments(beats, "जवाब आज तक नहीं मिला")[0]["tone"] == "sad"


def test_bad_takes_are_recorded_again_and_the_best_kept(cfg, monkeypatch, tmp_path):
    from creatorforge_worker import pipeline, providers
    takes = iter([{"text": "Line one dramatic", "lang": "en", "prob": 0.9},
                  {"text": "और आज? वोटर लिस्ट से तेरह दशमलव तीन करोड़ नाम कटे", "lang": "hi", "prob": 0.9}])

    class Ear:
        def listen(self, wav):
            return next(takes)
    monkeypatch.setattr(providers, "build_asr", lambda c: Ear())
    cfg.asr_provider = "whisper"
    made = []

    def speak(p):
        made.append(p)
        import wave
        with wave.open(str(p), "wb") as w:
            w.setnchannels(1), w.setsampwidth(2), w.setframerate(24000)
            w.writeframes(b"\x10\x20" * 24000)
    runner = pipeline.Pipeline.__new__(pipeline.Pipeline)
    runner.cfg = cfg
    first = runner._cached("voice", "k1", ".wav", speak, pipeline.verify.wav)
    src, verdict = runner._listened(first, "k1", SCRIPT, "hi", speak)
    assert verdict == "re-recorded" and src != first and len(made) == 2
