"""The Vox director: every narration line gets a drawn graphic (English on screen, never an AI picture), and every
graphic line is checked before a video renders."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from creatorforge_worker import vox_director as v
from creatorforge_worker.api import create_app
from creatorforge_worker.media import maps

NARRATION = """सुबह के आठ बजे। लाखों फ़ोन एक साथ बजते हैं।
<break time="1.2s" />
सितंबर दो हज़ार अठारह. राजस्थान का कोटा।
बीजेपी ने गूगल पर उनतीस करोड़ सत्तर लाख रुपये खर्च किए।
अड़तीस फ़ीसदी लोग।
और जो कहा, वो सुनकर आप चौंक जाएँगे।
ये बात अध्यक्ष ने अपने ही कार्यकर्ताओं के सामने कही थी।
"""


class FakeLLM:
    id = "fake"

    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def complete_json(self, system, user):
        self.calls += 1
        assert "GRAPHICS" in system and "English" in system
        return json.dumps(self.answer)


class BrokenLLM:
    id = "broken"

    def complete_json(self, system, user):
        raise RuntimeError("quota")


def test_spoken_hindi_numbers_dates_and_times():
    assert v._spoken_numbers("उनतीस करोड़ सत्तर लाख") == [(29.7, 10**7)]
    assert v._spoken_numbers("दो हज़ार अठारह") == [(2018.0, 1)]
    assert v._spoken_numbers("डेढ़ लाख") == [(1.5, 100000)]
    assert v.rule_graphic("बीजेपी ने उनतीस करोड़ सत्तर लाख रुपये खर्च किए").startswith("Chart: ₹29.7 crore")
    assert v.rule_graphic("अड़तीस फ़ीसदी लोग").startswith("Chart: 38%")
    assert v.rule_graphic("सुबह के आठ बजे।").startswith("Clock: 8:00 AM")
    assert v.rule_graphic("सितंबर दो हज़ार अठारह").startswith("Calendar: SEP 2018")


def test_hindi_words_match_whole_words_only():
    # "कार" (car) is not inside "कार्यकर्ताओं" (workers); फ़ोन and फोन are the same word
    assert "car" not in v._english("अपने ही कार्यकर्ताओं के सामने")
    assert "phone" in v._english("लाखों फोन बजते हैं")


def test_maps_find_indian_states_and_town_region_pairs():
    for name in ("Kota, Rajasthan", "Uttar Pradesh", "Mandi, Himachal Pradesh", "Shaheen Bagh, New Delhi"):
        assert maps.parse(name), name


def test_every_line_gets_a_valid_graphic_without_ai():
    out, report = v.ensure(NARRATION)
    _, bl = v.blocks(out)
    assert len(bl) == 6                                    # the pause tag is not a narration line
    assert "<break" not in out
    assert all(v.graphic_kind(b) for b in bl)
    assert not [i for i in v.check(out) if i["level"] == "error"]
    assert v.graphic_kind(bl[0]) == "clock"
    assert any(r.startswith("line ") for r in report)
    # narration words are never changed
    assert [b["line"] for b in bl][0] == "सुबह के आठ बजे। लाखों फ़ोन एक साथ बजते हैं।"


def test_script_ai_picks_graphics_and_bad_answers_fall_back_to_rules():
    llm = FakeLLM({"lines": [{"n": 1, "graphic": "Clock: 8:00 AM | Millions of phones buzz"},
                             {"n": 2, "graphic": "Map: Kota, Rajasthan | September 2018"},
                             {"n": 3, "graphic": "Statement: हिंदी में"},             # Hindi on screen: refused
                             {"n": 5, "graphic": "Nonsense: x"}]})
    out, report = v.ensure(NARRATION, llm)
    _, bl = v.blocks(out)
    assert llm.calls == 1
    assert "Clock: 8:00 AM | Millions of phones buzz" in bl[0]["dirs"]
    assert "Map: Kota, Rajasthan | September 2018" in bl[1]["dirs"]
    assert v.graphic_kind(bl[2]) == "chart"               # from the rules
    assert all(v.graphic_kind(b) for b in bl)
    out2, report2 = v.ensure(NARRATION, BrokenLLM())
    assert any("rules" in r for r in report2) and all(v.graphic_kind(b) for b in v.blocks(out2)[1])


def test_broken_graphics_are_replaced_and_ai_pictures_dropped():
    script = ("Title: Test\n\nपहली लाइन, दिल्ली की कहानी।\nMap: Atlantis Prime | nowhere\nVisual: a crowd at night\n\n"
              "दूसरी लाइन।\nArchive: Parliament 1950\n")
    issues = v.check(script)
    assert any("place not found" in i["problem"] for i in issues)
    out, report = v.ensure(script)
    assert "Atlantis" not in out and "Visual:" not in out
    assert "Map: New Delhi" in out
    assert "Archive: Parliament 1950" in out               # a real photo line is kept and counts as covered
    _, bl = v.blocks(out)
    assert v.graphic_kind(bl[1]) == ""


def test_the_bjp_graphics_script_has_no_errors():
    from pathlib import Path
    script = (Path(__file__).resolve().parents[2] / "scripts" / "bjp_it_cell" / "BJP_IT_CELL_ALL_GRAPHICS.txt")
    if not script.is_file():
        return
    assert not [i for i in v.check(script.read_text(encoding="utf-8")) if i["level"] == "error"]


def test_scripts_direct_and_check_endpoints(cfg):
    with TestClient(create_app(cfg)) as c:
        r = c.post("/v1/scripts/check", json={"script": NARRATION})
        assert r.status_code == 200 and r.json()["errors"] >= 1    # no graphics yet
        r = c.post("/v1/scripts/direct", json={"script": NARRATION})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["errors"] == 0 and body["script"].count("\n\n") >= 5


def test_a_vox_production_draws_every_line_without_ai_pictures(cfg):
    from .conftest import wait_for
    script = ("सुबह के आठ बजे। लाखों फ़ोन एक साथ बजते हैं।\n"
              "बीजेपी ने गूगल पर उनतीस करोड़ सत्तर लाख रुपये खर्च किए।\n"
              "सितंबर दो हज़ार अठारह. राजस्थान का कोटा।\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "style": "editorial", "vox_graphics": True,
                                              "template": "youtube_longform"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()), timeout=600)
        assert job["status"] == "READY", job
        assert "Clock: 8:00 AM" not in job["spec"]["script"]           # directions are never narrated
        assert len(job["spec"]["shots"]) == 3
        assert job.get("vox_report")
        work = cfg.jobs_dir / jid / "work"
        assert list(work.glob("chart_*.mp4"))


def test_month_and_year_calendar_never_invents_a_day():
    from creatorforge_worker.media import motion
    p = motion.plan_for("calendar", "SEP 2018 | Kota")
    assert p["day"] is None and p["month"] == "SEP" and p["year"] == "2018"
    assert motion.plan_for("calendar", "26 SEP 2018")["day"] == 26


def test_a_graphic_line_split_across_scenes_keeps_its_graphic():
    from creatorforge_worker import director
    raw = "\n".join(open(Path(__file__).resolve().parents[2] / "scripts" / "bjp_it_cell" /
                         "BJP_IT_CELL_ElevenLabs_PART_1.txt", encoding="utf-8").read().split("\n")[:14])
    fixed, _ = v.ensure(raw)
    spec = director.ProductionSpec.from_dict({"script": fixed, "style": "editorial", "vox_graphics": True,
                                              "template": "youtube_longform"})
    plan = director.direct_script(None, spec)
    director.plan_beats(None, plan, spec)
    beats = [b for s in plan.scenes for b in (s.beats or [])]
    assert beats and all(b.get("extra") or b.get("chart") for b in beats)
