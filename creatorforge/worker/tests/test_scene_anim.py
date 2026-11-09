"""Animate: lines - any object (Tabler icons) and action, drawn without AI."""
from creatorforge_worker.media.scene_anim import find_icon, parse


def test_objects_and_actions_are_read_from_plain_english():
    p = parse("plane flies from Delhi to Dubai carrying money bags | Where the money went")
    assert p["action"] == "move" and p["actors"][0]["icon"] == "plane"
    assert (p["from"], p["to"], p["title"]) == ("Delhi", "Dubai", "Where the money went") and p["cargo"]["icon"]
    assert parse("trolls attack a journalist")["action"] == "converge"
    assert [a["icon"] for a in parse("police → court → jail")["actors"]] == ["shield", "gavel", "lock"]
    assert parse("government blocks a tweet")["action"] == "block"
    assert parse("one message spreads to thousands of phones")["action"] == "multiply"
    assert parse("ship sails from Chennai to Singapore")["actors"][0]["icon"] == "ship"
    assert parse("factory shuts down")["action"] == "block"
    assert all(a["o"] for a in parse("voters vs money")["actors"])


def test_letter_icons_are_never_picked_for_words():
    assert find_icon("march") is None or "letter" not in find_icon("march")
    assert find_icon("skyscraper") == "building-skyscraper"


def test_new_vox_graphics_are_planned():
    from creatorforge_worker import director
    from creatorforge_worker.media.motion import plan_for
    assert plan_for("clock", "8:00 AM | Every morning")["h"] == 8
    assert plan_for("clock", "9:30 pm")["h"] == 21
    c = plan_for("calendar", "14 FEB 2023 | Income Tax survey")
    assert (c["day"], c["month"], c["year"]) == (14, "FEB", "2023")
    assert plan_for("sign", "REMOVE HIM | banner")["style"] == "banner"
    assert plan_for("social", "Party | text | 12K likes · 3K shares")["stats"] == ["12K likes", "3K shares"]
    assert len(plan_for("comments", "Your post | a · b · c")["items"]) == 3
    assert plan_for("trending", "#Tag | #A · #B")["others"] == ["#A", "#B"]
    assert plan_for("stamp", "manipulated media | the post")["text"] == "MANIPULATED MEDIA"
    for k in ("clock", "calendar", "sign", "social", "comments", "trending", "stamp", "animate"):
        assert k in director.FULL_FRAME
