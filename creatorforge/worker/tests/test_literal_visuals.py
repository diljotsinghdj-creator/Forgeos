"""Pictures follow the words: named people/parties/places get real pictures, everyday things a literal one."""
import io

from creatorforge_worker import director
from creatorforge_worker.media import literal
from creatorforge_worker.providers import wiki_image


def _plan(lines):
    """lines: [(spoken text, visual, extra)] -> a one-scene plan with one beat per line."""
    beats = [{"text": t, "visual": v, "extra": e or {}, "overlay": o} for t, v, e, o in lines]
    return director.ProductionPlan("t", "", "", "", [director.ShotPlan(" ".join(b["text"] for b in beats),
                                                                       beats[0]["visual"], beats=beats)])


def test_named_subjects_are_found_and_cleaned():
    known = {"Modi", "BJP", "Congress"}
    assert literal.proper_nouns("Then Rahul Gandhi got the maximum sentence.", known) == ["Rahul Gandhi"]
    assert literal.proper_nouns("A BJP MP explained why.", known) == ["BJP"]
    assert literal.proper_nouns("And the BJP took about half of it.", known) == ["BJP"]
    assert literal.proper_nouns("Modi has even said the agency is independent.", known) == ["Modi"]
    assert literal.proper_nouns("Researchers at V-Dem now call it an autocracy.", known) == ["V-Dem"]
    assert literal.proper_nouns("Founder Trevor Milton was convicted.", known) == ["Trevor Milton"]
    assert literal.proper_nouns("His photo was on India's Covid certificates.", known) == ["Covid"]   # countries skipped


def test_enrich_marks_names_swaps_literal_pictures_and_leaves_graphics_alone():
    script = ("Meet Leah. Congress called it match-fixing and the BJP called it a win. "
              "Every discount is an anchor. Police the anchor.")
    plan = _plan([
        ("Meet Leah.", "A woman seen from behind in a shop", {}, "LEAH · FICTIONAL"),
        ("Congress called it match-fixing.", "A football on an empty pitch", {}, ""),
        ("The BJP called it a win.", "A trophy on a shelf", {"statement": "A *win*"}, ""),
        ("Every discount is an anchor.", "A ship's anchor on a beach", {}, ""),
        ("Police the anchor.", "A ship's anchor on a beach", {}, ""),
    ])
    literal.enrich(plan, script)
    b = plan.scenes[0].beats
    assert "named" not in b[0]                                    # the writer labelled Leah fictional
    assert b[1]["named"]["name"] == "Congress"
    assert "named" not in b[2] and b[2]["visual"] == "A trophy on a shelf"   # full-frame statement: untouched
    assert "discount" in b[3]["visual"].lower() or "sale" in b[3]["visual"].lower()
    assert b[4]["visual"] == "A ship's anchor on a beach"        # "police" as a verb is not a police picture
    before = [dict(x) for x in b]
    literal.enrich(plan, script)                                  # safe to run again
    assert [dict(x) for x in b] == before


def test_a_picture_that_already_shows_the_thing_is_kept():
    plan = _plan([("Vote for the change.", "A hand dropping a paper ballot into a box", {}, "")])
    literal.enrich(plan, "Vote for the change.")
    assert plan.scenes[0].beats[0]["visual"] == "A hand dropping a paper ballot into a box"


def test_repeated_subjects_are_spaced_out():
    lines = [(f"The BJP did thing {i}.", f"Picture {i}", {}, "") for i in range(14)]
    plan = _plan(lines)
    literal.enrich(plan, " ".join(t for t, *_ in lines))
    marked = [i for i, b in enumerate(plan.scenes[0].beats) if b.get("named")]
    assert marked[0] == 0 and all(b - a >= literal.GAP_BEATS for a, b in zip(marked, marked[1:]))


def test_names_match_and_resolve_checks_the_page_is_the_right_one(monkeypatch):
    assert wiki_image.names_match("BJP", "Bharatiya Janata Party")
    assert wiki_image.names_match("SEC", "U.S. Securities and Exchange Commission")
    assert wiki_image.names_match("Modi", "Narendra Modi")
    assert wiki_image.names_match("Supreme Court", "Supreme Court of India")
    assert not wiki_image.names_match("SEC", "Southeastern Conference")
    pages = {"Leah": {"search": [{"title": "Leah", "snippet": "biblical figure"}],
                      "page": {"title": "Leah", "description": "Biblical figure", "pageimage": "Leah.jpg"}},
             "Congress India": {"search": [{"title": "Indian National Congress", "snippet": "political party in India"}],
                                "page": {"title": "Indian National Congress", "description": "Political party in India",
                                         "pageimage": "INC_hand_symbol.svg"}}}

    def fake_get(params, timeout=20):
        if params.get("list") == "search":
            q = params["srsearch"]
            return {"query": {"search": pages.get(q, {}).get("search", [])}}
        title = params["titles"]
        page = next((v["page"] for v in pages.values() if v["page"]["title"] == title), {})
        return {"query": {"pages": {"1": page}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    assert wiki_image.resolve("Leah", "Britain", ["Britain", "Anchor"]) is None       # a different Leah: nothing
    got = wiki_image.resolve("Congress", "India", ["India", "BJP"])
    assert got["title"] == "Indian National Congress" and got["image"] == "INC_hand_symbol.svg"


def test_logos_go_on_a_card_and_portraits_are_not_cropped(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from PIL import Image
    pngs = {}
    logo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    logo.paste((255, 120, 0, 255), (100, 100, 200, 200))
    buf = io.BytesIO(); logo.save(buf, "PNG"); pngs["logo"] = buf.getvalue()
    portrait = Image.new("RGB", (400, 800), (90, 60, 40))
    buf = io.BytesIO(); portrait.save(buf, "JPEG"); pngs["portrait"] = buf.getvalue()
    monkeypatch.setattr(wiki_image.httpx, "get", lambda url, **k: SimpleNamespace(
        content=pngs[url], raise_for_status=lambda: None))
    card = wiki_image.fetch_framed({"url": "logo", "logo": True}, tmp_path, (1920, 1080))
    with Image.open(card) as im:
        assert im.size == (1920, 1080) and im.getpixel((10, 10)) == (242, 236, 223) or im.getpixel((10, 10))[0] > 230
    framed = wiki_image.fetch_framed({"url": "portrait", "logo": False}, tmp_path, (1920, 1080))
    with Image.open(framed) as im:
        assert im.size == (1920, 1080)
        centre, edge = im.getpixel((960, 540)), im.getpixel((40, 540))
        assert centre[0] > edge[0]          # the photo whole in the middle, a dimmed blurred copy at the sides


def test_the_named_subject_gets_its_real_picture_and_a_credit(cfg, tmp_path, monkeypatch):
    from PIL import Image
    from creatorforge_worker.pipeline import Pipeline
    from creatorforge_worker.store import JobStore
    cfg.free_stock = True
    pipe = Pipeline(cfg, JobStore(cfg.jobs_dir))
    calls = []

    def fake_resolve(name, context="", topic=None, city=""):
        calls.append(name)
        return {"title": "Bharatiya Janata Party", "description": "Political party in India", "image": "BJP.svg"}

    def fake_framed(pic, cache, size, timeout=60):
        out = tmp_path / (pic["url"].rsplit("/", 1)[-1] + ".jpg")
        import random
        im = Image.new("RGB", (64, 36))
        im.putdata([(random.randrange(256), random.randrange(256), random.randrange(256)) for _ in range(64 * 36)])
        im.resize(size).save(out)                      # a detailed picture (a flat one would count as blank)
        return out
    monkeypatch.setattr(wiki_image, "resolve", fake_resolve)
    monkeypatch.setattr(wiki_image, "pictures", lambda page, more=True: [
        {"url": "https://x/BJP.svg", "credit": "BJP logo (identification)", "logo": True},
        {"url": "https://x/rally.jpg", "credit": "Someone / Wikimedia (CC BY-SA 4.0)", "logo": False}])
    monkeypatch.setattr(wiki_image, "fetch_framed", fake_framed)
    job = {"id": "abc", "providers": {}, "spec": {"idea": "test video", "aspect": "16:9"}}
    named = {"name": "BJP", "context": "India", "topic": ["India"]}
    first = pipe._named_photo(job, named, (1920, 1080))
    second = pipe._named_photo(job, named, (1920, 1080))
    assert first.name == "BJP.svg.jpg" and second.name == "rally.jpg.jpg"    # a different picture next time
    assert calls == ["BJP"]                                                  # looked up once per video
    assert "BJP logo (identification)" in job["stock_credits"]
    assert "2 named people/places" in job["providers"]["match"]
    cfg.free_stock = False
    assert pipe._named_photo(job, named, (1920, 1080)) is None               # no internet pictures: nothing


def test_the_story_country_decides_courts_police_and_streets(monkeypatch):
    assert wiki_image.other_country("Supreme Court of the United States", "India")
    assert not wiki_image.other_country("Supreme Court of India", "India")
    assert literal.setting_for("A man climbing the steps of a high court", "India").startswith("in India, Indian people")
    assert literal.setting_for("A pair of handcuffs on a table", "India") == ""            # an object: no setting
    assert literal.setting_for("A crowd outside Parliament in Delhi", "India") == ""        # already says where
    hits = {"Supreme Court India": [{"title": "Supreme Court of the United States", "snippet": ""},
                                    {"title": "Supreme Court of India", "snippet": ""}]}
    pages = {"Supreme Court of the United States": "Highest court of the United States",
             "Supreme Court of India": "Highest court of India"}

    def fake_get(params, timeout=20):
        if params.get("list") == "search":
            return {"query": {"search": hits.get(params["srsearch"], [])}}
        t = params["titles"]
        return {"query": {"pages": {"1": {"title": t, "description": pages[t], "pageimage": t + ".jpg"}}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    assert wiki_image.resolve("Supreme Court", "India", ["India"])["title"] == "Supreme Court of India"


def test_an_acronym_is_never_a_person_with_the_same_letters(monkeypatch):
    # "ED" in Indian news is the Enforcement Directorate, not Ed Sheeran
    assert not wiki_image.names_match("ED", "Ed Sheeran")
    assert wiki_image.names_match("ED", "Enforcement Directorate")
    assert wiki_image.names_match("BJP", "Bharatiya Janata Party")
    asked = []

    def fake_get(params):
        if params.get("list") == "search":
            asked.append(params["srsearch"])
            return {"query": {"search": [{"title": "Ed Sheeran", "snippet": "English singer"},
                                         {"title": "Enforcement Directorate", "snippet": "Indian agency"}]}}
        t = params["titles"]
        return {"query": {"pages": {"1": {"title": t, "description": "Indian law enforcement agency"
                                          if t.startswith("Enforcement") else "English singer-songwriter"}}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    assert wiki_image.resolve("ED", "India", ["India"])["title"] == "Enforcement Directorate"
    assert asked[0].startswith("Enforcement Directorate")
    assert wiki_image.resolve("SIR", "India") is None and wiki_image.resolve("PM", "India") is None


def test_a_lone_name_is_the_full_name_this_story_uses():
    script = ("Amit Shah spoke in Amethi. Rahul Gandhi replied the same day. Then Shah repeated it. "
              "Rahul laughed. Sonia Gandhi stayed silent while Priyanka Gandhi campaigned. Gandhi family again.")
    known = literal.mid_sentence_names(script)
    names = literal.full_names(script, known)
    assert literal.expand_name("Shah", names) == "Amit Shah"
    assert literal.expand_name("Rahul", names) == "Rahul Gandhi"
    assert literal.expand_name("Gandhi", names) is None             # three Gandhis: no guessing
    assert literal.expand_name("BJP", names) == "BJP"


def test_a_lone_name_needs_the_story_not_just_the_country(monkeypatch):
    def fake_get(params, timeout=20):
        if params.get("list") == "search":
            return {"query": {"search": [{"title": "KL Rahul", "snippet": "Indian international cricketer"}]}}
        return {"query": {"pages": {"1": {"title": "KL Rahul", "description": "Indian cricketer (born 1992)"}}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    assert wiki_image.resolve("Rahul", "India", ["India", "BJP", "Congress", "Modi"]) is None


def test_a_delhi_story_gets_delhis_landmark_not_jaipurs(monkeypatch):
    asked = []

    def fake_get(params, timeout=20):
        if params.get("list") == "search":
            asked.append(params["srsearch"])
            return {"query": {"search": [{"title": "Jantar Mantar, Jaipur", "snippet": "observatory in Jaipur"},
                                         {"title": "Jantar Mantar, New Delhi", "snippet": "observatory in New Delhi"}]}}
        t = params["titles"]
        desc = "Astronomical observatory in Jaipur, Rajasthan" if "Jaipur" in t else "Astronomical observatory in New Delhi"
        return {"query": {"pages": {"1": {"title": t, "description": desc}}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    got = wiki_image.resolve("Jantar Mantar", "India", ["India", "BJP"], "New Delhi")
    assert got["title"] == "Jantar Mantar, New Delhi" and asked[0] == "Jantar Mantar New Delhi"
    assert literal.context_city("Protest at Jantar Mantar. Delhi Police detained them in New Delhi.") == "New Delhi"
    assert "New Delhi" in literal.setting_for("A crowded street at dusk", "India", "New Delhi")


def test_repeat_photos_never_include_an_artwork_that_shares_a_name(monkeypatch):
    from creatorforge_worker.providers import archive_photo
    monkeypatch.setattr(wiki_image, "file_info", lambda f, width=1600: {"url": "lead", "credit": "c", "logo": False})
    monkeypatch.setattr(archive_photo, "search", lambda q, limit=8: [
        {"title": "Mughal painting of Shah Jahan with Amit Shah collection", "url": "a", "credit": "x"},
        {"title": "Amit Shah addressing a rally in 2019", "url": "b", "credit": "y"},
        {"title": "Shah Abbas portrait 17th century", "url": "c", "credit": "z"}])
    pics = wiki_image.pictures({"title": "Amit Shah", "image": "Amit_Shah.jpg"})
    assert [p["url"] for p in pics] == ["lead", "b"]


def test_protest_and_arrest_lines_show_the_movement_itself():
    script = ("The Cockroach Janta Party marched on Delhi. The CJP wants the election chief out. "
              "Police detained its founder. Thousands joined the protest at Jantar Mantar.")
    known = literal.mid_sentence_names(script)
    assert literal.movement(script, known) == "Cockroach Janta Party"
    plan = _plan([("Police detained its founder at the airport.", "A dark airport gate at night", {}, ""),
                  ("Prices went up again this year.", "A market stall", {}, ""),
                  ("Then the protesters kept marching.", "A wide avenue", {}, "")])
    literal.enrich(plan, script)
    beats = plan.scenes[0].beats
    assert beats[0]["named"]["name"] == "Cockroach Janta Party"
    assert not beats[1].get("named")
    assert wiki_image.ACRONYMS["CJP"] == "Cockroach Janta Party"


def test_india_is_shown_modern_and_in_colour():
    spec = director.ProductionSpec.from_dict({"idea": "india protests story", "style": "investigative"})
    beats = [{"text": "India votes today.", "visual": "Voters queueing outside a polling station"},
             {"text": "In 1975 India changed.", "visual": "A crowd outside a court", "extra": {"archive": "1975"}}]
    plan = director.ProductionPlan("t", "", "", "", [director.ShotPlan(" ".join(b["text"] for b in beats),
                                                                       beats[0]["visual"], beats=beats)])
    plan.scenes[0].narration = "India votes today in India. India changed in 1975. India."
    director.prompt_forge(plan, spec)
    now, then = plan.scenes[0].beats
    assert "modern full-colour" in now["prompt"] and "sepia" not in now["prompt"].split("negative")[0]
    assert "black and white" in now["negative"] and "slum" in now["negative"]
    assert "black and white archival" in then["prompt"]            # a history line keeps its old-photo look
