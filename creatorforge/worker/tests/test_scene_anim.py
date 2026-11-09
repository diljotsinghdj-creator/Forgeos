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
