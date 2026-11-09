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
    assert v.graphic_kind(bl[2]) in ("chart", "bignumber")  # the infographic picker: the money as a big number
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
    assert "Pinmap: New Delhi" in out
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
        assert list(work.glob("chart_*.mp4")) + list(work.glob("bignumber_*.mp4"))


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


def test_narration_alone_gets_a_sensible_infographic_per_line():
    from creatorforge_worker import infographic as ig
    f = ig.facts("उन्होंने बताया, उत्तर प्रदेश चुनाव में पार्टी के दो व्हाट्सऐप नेटवर्क थे। पंद्रह लाख और सत्रह लाख लोग।")
    assert [n["shown"] for n in f["numbers"]] == ["15 lakh", "17 lakh"]         # "दो नेटवर्क" is a count, not a figure
    assert "Uttar Pradesh" in f["places"]
    assert ig.facts("हर सुबह आठ बजे, एक ही मैसेज।")["numbers"] == []              # a clock time, not a number
    assert ig.facts("आप उसे आगे भेजेंगे?")["parties"] == []                        # "आप" is "you", not AAP
    script = ("\"हम कोई भी मैसेज वायरल कर सकते हैं। सच्चा हो या झूठा।\"\n"
              "ये बात अमित शाह ने कोटा में कही थी।\n"
              "उन्होंने बताया, दो व्हाट्सऐप नेटवर्क थे। पंद्रह लाख और सत्रह लाख लोग।\n"
              "शाह ने ख़ुद माना, उसमें कोई सच्चाई नहीं थी।\n"
              "डेक्कन हेराल्ड के मुताबिक़, पचास लाख व्हाट्सऐप ग्रुप्स।\n"
              "तो सवाल ये है, आप उसे आगे भेजेंगे या नहीं?\n")
    out, rep = v.ensure(script)
    _, bl = v.blocks(out)
    kinds = [v.graphic_kind(b) for b in bl]
    assert kinds[0] == "hero" and "person:Amit Shah" in bl[0]["dirs"][0]   # the speaker's real photo with the quote
    assert kinds[-1] == "opener"
    assert "pinmap" in kinds and "stack" in kinds and "stamp" in kinds
    assert "newscard" in kinds or "bignumber" in kinds        # the reported figure, as the report itself
    assert "Kota" in out and "15 lakh" in out and "50 lakh" in out and "Deccan Herald" in out
    assert "forward it?" in out.lower()
    assert not [i for i in v.check(out) if i["level"] == "error"]


def test_the_mute_test_rejects_graphics_that_miss_the_key_fact():
    from creatorforge_worker import infographic as ig
    f = ig.facts("बीजेपी ने गूगल पर उनतीस करोड़ सत्तर लाख रुपये खर्च किए।")
    assert ig.mute_test(f, "BigNumber: ₹29.7 crore | banknote | Google ads")
    assert not ig.mute_test(f, "Hero: megaphone | Ads")


def test_every_video_gets_its_own_look_and_old_stories_get_old_objects():
    from creatorforge_worker.media import vox
    looks = {vox.choose_look(f"script number {i}") for i in range(30)}
    assert len(looks) >= 4                                         # not one face for every video
    assert vox.choose_look("x", vox.era_of("In 1914 the canal opened.")) == "sepia"
    assert vox.era_of("1914 ... 2018 ... 2020") == 2018            # one look back doesn't turn a modern story sepia
    assert vox.illustration("ship", 1914) == "steamer" and vox.illustration("ship", 2020) == "ship"
    assert vox.illustration("phone", 1960) == "rotaryphone" and vox.illustration("plane", 1925) == "biplane"
    assert vox.look_of("editorial~1@red/kraft/1914")["head"] == "Archivo"
    assert vox.accent_of("editorial~1@red/kraft/1914") == vox.ACCENTS["red"] and vox.era_in("e@red/kraft/1914") == 1914


def test_the_marker_is_rationed_and_two_videos_dont_share_one_shot_order():
    from creatorforge_worker import infographic as ig
    script = "\n".join(["बीजेपी ने गूगल पर उनतीस करोड़ सत्तर लाख रुपये खर्च किए।",
                        "राजस्थान के कोटा में पंद्रह लाख लोग।",
                        "डेक्कन हेराल्ड के मुताबिक़, पचास लाख व्हाट्सऐप ग्रुप्स।",
                        "उत्तर प्रदेश में सत्रह लाख लोग।",
                        "दिल्ली में अड़तीस फ़ीसदी लोग।",
                        "तो सवाल ये है, आप उसे आगे भेजेंगे या नहीं?"])
    out, _ = v.ensure(script)
    marks = [i for i, b in enumerate(v.blocks(out)[1]) if any("marker:" in d for d in b["dirs"])]
    assert all(b - a >= 4 for a, b in zip(marks, marks[1:]))       # about one shot in four
    cands = ["Pinmap: Kota | x | atlas", "BigNumber: 15 lakh | crowd | x", "Newscard: 2018 | x | y | newspaper | DH",
             "Stack: 15 lakh, 17 lakh | x", "Trend: 1, 2 | x"]
    orders = {tuple(g.split(":")[0] for g in ig._ranked(cands, 3, 9, None, seed)) for seed in range(1, 40)}
    assert len(orders) >= 3
    hooks = {ig._ranked(["BigNumber: 1 | a | b", "Pinmap: Kota | a", "Opener: a | b | c"], 1, 9, None, s)[0]
             for s in range(1, 20)}
    assert len(hooks) == 3                                          # the opening differs from video to video


def test_no_two_videos_alike_even_the_same_script_twice(tmp_path):
    from creatorforge_worker import variety
    from creatorforge_worker.media import vox
    script = "\n".join(["बीजेपी ने गूगल पर उनतीस करोड़ सत्तर लाख रुपये खर्च किए।",
                        "राजस्थान के कोटा में पंद्रह लाख लोग।",
                        "डेक्कन हेराल्ड के मुताबिक़, पचास लाख व्हाट्सऐप ग्रुप्स।",
                        "दिल्ली में अड़तीस फ़ीसदी लोग।",
                        "तो सवाल ये है, आप उसे आगे भेजेंगे या नहीं?"])
    fps = []
    for i in range(6):
        h = variety.load(tmp_path)
        look = variety.pick_look(script, None, h)
        fixed, _, fp, sim = variety.direct_unique(script, None, False, look, h, f"job{i}")
        assert sim < variety.TOO_CLOSE, (i, sim)
        assert not [x for x in v.check(fixed) if x["level"] == "error"]
        variety.remember(tmp_path, fp)
        fps.append(fp)
    assert len({f["look"] for f in fps[:5]}) == 5                   # five videos, five looks
    assert variety.pick_look("old", 1914, [{"look": "sepia"}]) == "engraving"
    for f in fps:                                                   # neighbouring shots never share a layout
        lays = [x.split(":")[1] for x in f["layouts"] if ":" in x]
        assert all(a != b or len(vox.LAYOUT_SETS[k.split(":")[0]]) == 1
                   for a, b, k in zip(lays, lays[1:], f["layouts"][1:]))


def test_layouts_rotate_per_kind_and_never_repeat_back_to_back():
    from creatorforge_worker.media import vox
    ks = ["pinmap", "pinmap", "bignumber", "bignumber", "bignumber", "hero", "hero", "hero"]
    for seed in range(1, 30):
        lays = vox.plan_layouts(ks, seed)
        assert all(a != b for a, b in zip(lays, lays[1:]))
        assert len(set(lays[2:5])) == 3 and len(set(lays[5:8])) == 3   # three BigNumbers, three layouts


def test_finished_videos_are_compared_frame_by_frame(tmp_path):
    import subprocess
    from creatorforge_worker import variety
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    for out, src in ((a, "testsrc=size=160x90:rate=10"), (b, "mandelbrot=size=160x90:rate=10")):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, "-t", "2", "-pix_fmt", "yuv420p", str(out)],
                       check=True)
    assert variety.compare_videos(a, a)["same_look"] is True
    assert variety.compare_videos(a, b)["same_look"] is False


def test_two_countries_and_a_size_word_get_a_size_map():
    from creatorforge_worker import infographic as ig
    line = "भारत जर्मनी से नौ गुना बड़ा है।"
    g = ig.pick(line, ig.facts(line), 3, 6, [])
    assert g.startswith("Sizemap: India vs Germany") and v.valid(g) == ""
