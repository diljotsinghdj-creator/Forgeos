"""The owner's five gates (studio/gates.py): each one stops what it should and lets through what it should."""
import json
from pathlib import Path

import pytest

from creatorforge_worker.studio import gates

FILMS = Path(__file__).resolve().parents[2] / "films"
PICK = {"engine": "reverse-autopsy", "pitched": ["reverse-autopsy", "historical-echo", "trojan-horse"],
        "owner_words": "Go with 1", "date": "2026-11-11"}


def sp(**kw):
    base = {"id": "x-sample", "channel": "sample", "sample_for": "print-facts", "engine": "reverse-autopsy", "pick": dict(PICK),
            "hook_mechanism": "a resignation letter", "voice": "bf_emma",
            "scenes": [{"id": "S1", "narration": "On 17 August the chief was replaced.", "graphic": "Photo: letter.jpg | The letter"},
                       {"id": "S2", "narration": "Eleven years earlier.", "graphic": "Counter: 0 → 11 | years"}]}
    base.update(kw)
    return base


# ---- gate 1: no pick, no script ----
def test_gate1_refuses_without_the_owners_pick():
    assert gates.check_pick(sp(pick=None))[0]["gate"] == 1
    assert gates.check_pick(sp()) == []


def test_gate1_refuses_a_pick_that_is_not_the_screenplays_engine_or_was_not_pitched():
    assert any("not the owner's pick" in i["problem"] for i in gates.check_pick(sp(engine="trojan-horse")))
    bad = dict(PICK, pitched=["reverse-autopsy", "historical-echo"])
    assert gates.check_pick(sp(pick=bad))
    assert gates.check_pick(sp(pick=dict(PICK, owner_words="")))


def test_gates_leave_test_reels_alone():
    assert not gates.applies({"channel": "test"}) and gates.applies(sp()) and gates.applies({"channel": "print-facts"})


# ---- gate 2: seen means used ----
def test_gate2_stops_the_last_pieces_engine_look_voice_and_opening():
    last = gates.entry(sp(id="prev", engine="reverse-autopsy", voice="bf_emma"), "sample", "newsprint")
    found = gates.check_seen(sp(), "newsprint", [last])
    probs = " ".join(i["problem"] for i in found)
    assert "engine" in probs and "look" in probs and "voice" in probs and "opens on 'photo'" in probs


def test_gate2_lets_the_owners_own_voice_repeat_and_a_rerender_of_the_same_piece():
    last = gates.entry(sp(id="prev", engine="historical-echo", voice="dj (owner's ElevenLabs voice)",
                          scenes=[{"id": "S1", "narration": "x", "graphic": "Globe: India"}]), "sample", "archive")
    me = sp(voice="dj (owner's ElevenLabs voice)")
    assert gates.check_seen(me, "field", [last]) == []
    assert gates.check_seen(me, "field", [gates.entry(me, "sample", "field")]) == []


def test_gate2_catches_the_bjp_sample_repeating_the_storyboard():
    """The mistake that made this gate: the BJP sample re-used the storyboard the owner had already seen."""
    shown = gates.seen(Path(__file__).resolve().parents[2] / "channels" / "SEEN.json")
    board = [r for r in shown if r["kind"] == "storyboard"]
    assert board, "SEEN.json must hold the BJP storyboard"
    mine = json.loads((FILMS / "bjp-it-cell-sample" / "screenplay.json").read_text())
    mine["id"] = "bjp-it-cell-sample-2"
    found = gates.check_seen(mine, "field", board)
    assert {"S1", "S2"} <= {i["scene"] for i in found}, found


def test_gate2_reuse_is_allowed_only_for_the_shots_listed():
    board = {"id": "b", "kind": "storyboard", "topic": "x", "shots": ["Flowchart: A → B → C | The chain"], "engine": "", "look": "",
             "voice": "", "opening": "footage", "hook_mechanism": "", "hook_line": ""}
    me = sp(scenes=[{"id": "S1", "narration": "n", "graphic": "Photo: a.jpg"}, {"id": "S2", "narration": "n", "graphic": "Flowchart: A → B → C | The chain"}])
    assert any(i["scene"] == "S2" for i in gates.check_seen(me, "field", [board]))
    assert not any(i["scene"] == "S2" for i in gates.check_seen(dict(me, reuse=["S2"]), "field", [board]))


# ---- gate 3: evidence first ----
def test_gate3_evidence_before_explanation_on_print_facts():
    explain_first = sp(scenes=[{"id": "S1", "narration": "n", "graphic": "Chat: Family | them: hi"},
                               {"id": "S2", "narration": "n", "graphic": "Flowchart: A → B | chain"}])
    assert gates.check_evidence(explain_first)[0]["scene"] == "S2"
    assert gates.check_evidence(sp()) == []
    waived = dict(explain_first, evidence_waiver={"reason": "archives blocked here", "told_owner": True})
    assert gates.check_evidence(waived)[0]["level"] == "warning"
    assert gates.check_evidence(dict(explain_first, sample_for="dragon-psychology")) == []


# ---- gate 4: pacing ----
def tl(*holds):
    out, t = [], 0.0
    for i, h in enumerate(holds):
        out.append({"scene": f"S{i + 1}", "start": t, "end": t + h})
        t += h
    return out


def test_gate4_still_shots_and_building_shots_have_their_own_limits():
    assert gates.check_pacing(tl(3, 4), ["newscard", "units"]) == []
    found = gates.check_pacing(tl(6, 4), ["newscard", "units"])
    assert found and found[0]["scene"] == "S1"
    assert gates.check_pacing(tl(4, 9.5, 3), ["chat", "units", "hero"])[0]["scene"] == "S2"      # the BJP sample's 687 shot
    assert gates.check_pacing(tl(4, 5.5), ["units", "hero"]) == []                               # the last shot may hold longer


def test_gate4_average_hold():
    assert any(i["scene"] == "-" for i in gates.check_pacing(tl(6.5, 6.5, 6.5), ["units", "units", "units"]))


# ---- gate 5: the pre-show list ----
def test_gate5_preshow_lists_rules_gaps_and_every_shot(monkeypatch, tmp_path):
    monkeypatch.setenv("CF_DATA_DIR", str(tmp_path))
    s = sp(target_seconds=30, scenes=[{"id": "S1", "narration": "n", "graphic": "Chat: Family | them: hi"},
                                      {"id": "S2", "narration": "n", "graphic": "Stand: A 5 vs B 3 | t | logo: bjp"}])
    issues = gates.check_pacing(tl(3, 9), ["chat", "stand"])
    text = gates.preshow(s, issues, tl(3, 9), ["chat", "stand"], {"seconds": 33.7},
                         {"symbols": gates.missing_symbols(s), "brainlog": ["Use judgment, not the nearest template"]})
    assert "Gate 4, Pacing:** S2" in text and "33.7s against 30s asked (over)" in text
    assert "BJP symbol is left out" in text and "a recreation (chat)" in text and "No real document" in text
    assert "a stand-in, not the owner's ElevenLabs voice" in text and "| S2 |" in text and "Use judgment" in text


def test_seen_record_replaces_the_same_piece(tmp_path):
    f = tmp_path / "seen.json"
    gates.record(gates.entry(sp(), "sample", "a"), f)
    gates.record(gates.entry(sp(), "sample", "b"), f)
    assert [r["look"] for r in gates.seen(f)] == ["b"]


def test_produce_stops_at_gate1_before_anything_is_drawn(tmp_path, monkeypatch):
    from creatorforge_worker.studio.produce import ProductionStopped, produce
    monkeypatch.setenv("CF_STUDIO_HISTORY", str(tmp_path / "h"))
    monkeypatch.setenv("CF_SEEN", str(tmp_path / "seen.json"))
    mine = json.loads((FILMS / "bjp-it-cell-sample" / "screenplay.json").read_text())
    mine.pop("pick", None)
    (tmp_path / "sp.json").write_text(json.dumps(mine))
    with pytest.raises(ProductionStopped, match="gate 1"):
        produce(tmp_path / "sp.json", FILMS / "bjp-it-cell-sample" / "dossier.json", tmp_path / "out", progress=lambda *a: None)
    assert not list((tmp_path / "out" / "scenes").glob("*.mp4"))
    assert "gate 1" in (tmp_path / "out" / "writing" / "gates.md").read_text()
