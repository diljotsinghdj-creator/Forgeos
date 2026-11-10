"""The showrunner rules in the editorial review: banned phrases, visual pattern interrupts, narrative engines and the
anti-clone check against the channel's previous film."""
from creatorforge_worker.studio import writer
from creatorforge_worker.studio.dossier import Dossier


def _sp(**kw):
    sp = {"id": "f2", "channel": "dragon-psychology", "engine": "trojan-horse", "hook_mechanism": "everyday object",
          "metaphors": ["two-track grid"], "concept": {"logline": "x", "central_question": "why?"},
          "scenes": [{"id": "S1", "act": "hook", "narration": "Why does a calm voice beat a smart brain?", "graphic": "Statement: *Why*?"},
                     {"id": "S2", "act": "ending", "narration": "Hang up. Call back.", "graphic": "Statement: Hang *up*"}]}
    sp.update(kw)
    return sp


def test_banned_phrases_and_engines_are_errors():
    d = Dossier(topic="t", claims={})
    sp = _sp()
    sp["scenes"][0]["narration"] = "Let's unpack why we delve into scams?"
    probs = [p["problem"] for p in writer.check(sp, d) if p["level"] == "error"]
    assert any("let's unpack" in p for p in probs) and any("'delve'" in p for p in probs)
    assert any("engine must be one of" in p["problem"] for p in writer.check(_sp(engine="montage"), d))
    assert not [p for p in writer.check(_sp(), d) if p["level"] == "error"]


def test_long_stretches_without_a_new_picture_are_flagged():
    d = Dossier(topic="t", claims={})
    long = " ".join(["word"] * 40)
    sp = _sp()
    sp["scenes"] = [{"id": "S1", "act": "hook", "narration": "Why? " + long, "graphic": "Statement: a"},
                    {"id": "S2", "act": "world", "narration": long, "graphic": "Statement: b"},
                    {"id": "S3", "act": "ending", "narration": "End.", "graphic": "Statement: *End*"}]
    warns = [p["problem"] for p in writer.check(sp, d) if p["level"] == "warning"]
    assert any("no visual pattern interrupt" in w for w in warns)


def test_back_to_back_films_never_share_engine_hook_or_metaphor():
    hist = [{"id": "f0", "channel": "dragon-psychology", "engine": "historical-echo", "hook_mechanism": "x", "metaphors": ["balance scale"]},
            {"id": "f1", "channel": "dragon-psychology", "engine": "trojan-horse", "hook_mechanism": "everyday object",
             "metaphors": ["two-track grid"]},
            {"id": "p1", "channel": "print-facts", "engine": "reverse-autopsy", "hook_mechanism": "y", "metaphors": []}]
    probs = writer.novelty(_sp(), hist)
    assert len([p for p in probs if p["level"] == "error"]) == 3
    fresh = writer.novelty(_sp(engine="live-viewer-trap", hook_mechanism="viewer test", metaphors=["balance scale"]), hist)
    assert not [p for p in fresh if p["level"] == "error"] and any("last few films" in p["problem"] for p in fresh)
    assert writer.novelty(_sp(channel="new-channel"), hist) == []
