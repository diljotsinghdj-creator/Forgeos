"""The documentary studio: evidence rules, editorial review, art direction that never repeats, captions from the real
audio, research and writing through a model (with stand-ins for the search engine and the model)."""
import json
from pathlib import Path

import pytest

from creatorforge_worker.studio import artdirection, research, writer
from creatorforge_worker.studio.dossier import Dossier, attributed, figures_in, norm_figure
from creatorforge_worker.studio.produce import captions

FILM = Path(__file__).resolve().parents[2] / "films" / "aral-sea"


def _d(claims):
    return Dossier.from_dict({"topic": "t", "claims": claims})


SRC2 = [{"title": "a", "url": "https://a.org/x", "quote": "q"}, {"title": "b", "url": "https://b.org/y", "quote": "q"}]


def test_figures_are_normalised():
    assert norm_figure("68,000 km²") == "68000" and norm_figure("$64.5 million") == "64.5" and norm_figure("1960s") == "1960"
    assert figures_in("about 68,000 square km in 1960, down to 6,800; two seas") == ["68000", "1960", "6800"]
    assert attributed("According to one account, it doubled") and not attributed("It doubled.")


def test_the_dossier_refuses_weak_evidence():
    bad = _d([{"id": "C1", "claim": "x", "status": "verified", "sources": [SRC2[0]]},          # one source cannot verify
              {"id": "C2", "claim": "y", "status": "disputed", "sources": SRC2},               # disputed without the other side
              {"id": "C3", "claim": "z", "status": "reported", "sources": [{"title": "n", "url": "not a url", "quote": "q"}]},
              {"id": "C4", "claim": "w", "status": "rumour", "sources": SRC2}])
    probs = {(p["claim"], p["problem"].split(" ")[0]) for p in bad.check() if p["level"] == "error"}
    assert ("C1", "'verified'") in probs and ("C2", "'disputed'") in probs and ("C3", "source") in probs and ("C4", "unknown") in probs
    assert not _d([{"id": "C1", "claim": "x", "status": "verified", "sources": SRC2}]).check()


def _sp(scenes, **kw):
    base = {"id": "t", "title": "T", "concept": {"logline": "l", "central_question": "Why?"}, "scenes": scenes}
    base.update(kw)
    return base


def test_editorial_review_catches_unsupported_figures_unattributed_claims_and_bad_graphics():
    d = _d([{"id": "C1", "claim": "It covered 68,000 km2 in 1960", "status": "verified", "figures": ["68,000", "1960"], "sources": SRC2},
            {"id": "C2", "claim": "Catch doubled", "status": "reported", "figures": ["2"], "sources": SRC2[:1]},
            {"id": "C3", "claim": "x", "status": "unverified", "sources": SRC2[:1]}])
    ok = [{"id": "S1", "act": "hook", "narration": "How do you lose a sea? In 1960 it covered 68,000 square kilometres.", "claims": ["C1"],
           "graphic": "BigNumber: 68,000 km² | ship | in 1960"},
          {"id": "S2", "act": "ending", "narration": "According to one report, the catch doubled.", "claims": ["C2"],
           "graphic": "Endcard: T | the end | Sources: A · B"}]
    assert not [i for i in writer.check(_sp(ok), d) if i["level"] == "error"]
    bad = json.loads(json.dumps(ok))
    bad[0]["narration"] = "How do you lose a sea? In 1961 it covered 70,000 square kilometres."   # figures the evidence lacks
    bad[1]["narration"] = "The catch doubled."                                                      # a reported claim stated as fact
    bad[1]["claims"] = ["C2", "C3"]                                                                  # an unverified claim
    bad[0]["graphic"] = "Pinmap: Atlantis | x"                                                       # a graphic that can't be drawn
    probs = " | ".join(i["problem"] for i in writer.check(_sp(bad), d) if i["level"] == "error")
    assert "1961" in probs and "70000" in probs and "must be attributed" in probs and "unverified" in probs and "graphic" in probs


def test_the_aral_sea_film_passes_its_own_review():
    d = Dossier.load(FILM / "dossier.json")
    assert not d.check()
    sp = json.loads((FILM / "screenplay.json").read_text(encoding="utf-8"))
    assert not [i for i in writer.check(sp, d) if i["level"] == "error"]
    assert len(sp["scenes"]) >= 25 and sp["scenes"][0]["act"] == "hook" and sp["scenes"][-1]["act"] == "ending"


def test_art_direction_changes_from_film_to_film(tmp_path):
    scenes = [{"graphic": "Pinmap: India | x", "narration": "a", "role": "opening"}, {"graphic": "Endcard: x", "narration": "b", "role": "ending"}]
    seen = []
    for i in range(4):
        doc = artdirection.direct(f"film{i}", "Same topic", "environment", {"logline": "l", "central_question": "q"}, scenes,
                                  artdirection.history(tmp_path))
        artdirection.remember(tmp_path, {"id": doc["id"], **{k: doc[k] for k in ("look", "accent", "cinematography", "maps", "infographics",
                                                                                "animation", "rhythm", "music")}})
        seen.append(doc)
    for a, b in zip(seen, seen[1:]):
        same = [k for k in ("look", "cinematography", "maps", "infographics", "rhythm", "music") if a[k] == b[k]]
        assert len(same) <= 1, same                      # consecutive films share at most one treatment
    md = artdirection.to_markdown(seen[0])
    for n in range(1, 16):
        assert f"## {n}." in md
    assert artdirection.camera_for(seen[0], "courtdoc") in ("still", "focus")


def test_captions_follow_the_voice_and_never_run_past_the_line():
    scenes = [{"narration": "In 1960 it covered about sixty-eight thousand square kilometres, and then the rivers were turned away."}]
    tl = [{"start": 10.0, "end": 16.0, "speech_s": 5.0, "pauses": [(2.4, 0.3)]}]
    cues = captions(scenes, tl)
    assert len(cues) >= 2 and all(len(c) <= 42 for _, _, c in cues)
    assert cues[0][0] >= 10.0 and cues[-1][1] <= 10.0 + 0.18 + 5.0 + 1e-6
    assert any(abs(b - (10.18 + 2.55)) < 0.05 for _, b, _ in cues)       # a cue ends where the narrator breathes


class FakeSearch(research.SearchProvider):
    def search(self, query, count=6):
        return [{"title": "NASA", "url": "https://nasa.gov/a", "snippet": "The sea shrank to about 10 percent of its 1960 area."},
                {"title": "UNEP", "url": "https://unep.org/b", "snippet": "Today the sea is about 10 percent of its 1960 area."},
                {"title": "Blog", "url": "https://blog.example/c", "snippet": "Something else entirely."}]


class FakeLLM:
    def __init__(self, answers):
        self.answers = list(answers)

    def complete_json(self, system, user):
        return json.dumps(self.answers.pop(0))


def test_research_keeps_only_claims_whose_words_are_in_the_source():
    llm = FakeLLM([{"queries": ["aral sea area"]},
                   {"claims": [{"claim": "Shrank to about 10% of its 1960 area", "label": "fact", "figures": ["10", "1960"],
                                "sources": [{"n": 0, "quote": "The sea shrank to about 10 percent"}, {"n": 1, "quote": "about 10 percent of its 1960 area"}]},
                               {"claim": "Invented", "label": "fact", "figures": ["99"], "sources": [{"n": 2, "quote": "the sea was 99 km deep"}]}]}])
    d = research.research("Aral Sea", llm, FakeSearch())
    assert len(d.claims) == 1
    c = next(iter(d.claims.values()))
    assert c.status == "verified" and len(c.sources) == 2 and not d.check()
    with pytest.raises(RuntimeError):
        research.research("x", FakeLLM([]), None) if not research.provider() else (_ for _ in ()).throw(RuntimeError())


def test_the_writer_repairs_a_screenplay_its_review_rejects():
    d = _d([{"id": "C1", "claim": "68,000 km2 in 1960", "status": "verified", "figures": ["68,000", "1960"], "sources": SRC2}])
    first = _sp([{"id": "S1", "act": "hook", "narration": "Why did it vanish? It was 70,000 square kilometres.", "claims": ["C1"],
                  "graphic": "BigNumber: 70,000 km² | ship | then"},
                 {"id": "S2", "act": "ending", "narration": "The end.", "claims": [], "graphic": "Endcard: T | x | Sources: A"}])
    fixed = json.loads(json.dumps(first))
    fixed["scenes"][0].update(narration="Why did it vanish? It was 68,000 square kilometres in 1960.", graphic="BigNumber: 68,000 km² | ship | in 1960")
    llm = FakeLLM([first, fixed])
    sp, issues = writer.write(llm, d)
    assert not [i for i in issues if i["level"] == "error"] and "68,000" in sp["scenes"][0]["narration"]
