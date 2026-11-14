"""The parts built for the BJP IT cell sample: unit chart, the messaging-app chat, no stand-in party symbol tiles."""
from creatorforge_worker.media import cards, layout_qa, vox


def test_units_parses_whole_counts_and_refuses_fractions():
    p = vox.parse_units("Congress-linked 687 vs BJP-leaning 15 | Facebook takedowns, 2019 | one square = one page")
    assert p["type"] == "units" and [v["value"] for v in p["values"]] == [687, 15]
    assert vox.parse_units("A 2.5 vs B 1 | x") is None
    assert vox.parse_units("A 5000 vs B 10 | too many to draw") is None


def test_chat_options_never_become_message_text():
    spec = "Family group | them: fwd: SHARE THIS · me: Is this true? | app: whatsapp"
    out, _ = cards.chat_lines(spec, "editorial", 1920, 1080, 5.0)
    text = "\n".join(out)
    assert "app:" not in text and "logo:" not in text and "fwd:" not in text
    assert "Forwarded many times" in text
    assert layout_qa.check_card("chat", spec, "editorial", 1920, 1080, 5.0) == []


def test_party_symbol_without_official_file_is_left_out(monkeypatch, tmp_path):
    monkeypatch.setenv("CF_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CF_SYMBOL_SLOTS", raising=False)
    plan = vox.plan_for("stand", "A 5 vs B 3 | title | logo: bjp, facebook")
    keys = [m["key"] for m in plan.get("logos", [])]
    assert "facebook" in keys and "bjp" not in keys
    monkeypatch.setenv("CF_SYMBOL_SLOTS", "1")
    assert "bjp" in [m["key"] for m in vox.plan_for("stand", "A 5 vs B 3 | title | logo: bjp")["logos"]]
