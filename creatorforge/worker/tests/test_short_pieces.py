"""The five pieces built for the BJP Short: reel, conveyor, tiles, pile (vox) and the 3D phone (scene3d)."""
import json
from pathlib import Path

import pytest

from creatorforge_worker.media import motion, scene3d, vox

SPECS = {"reel": "rap | Just a *catchy reel*?",
         "conveyor": "APPROVED | 6 | In Delhi, one official signs off every post | Every post, *one sign-off*",
         "tiles": "Bihar | 72 | 1 tile = 1,000 groups | Bihar, 2020: *72,000* groups | planned (ThePrint)",
         "pile": "17 | FALSE, MISLEADING | Flagged *17 times* | flagged by fact-checkers",
         "grids": "pro-BJP pages 28, pro-Congress pages 21 | It isn't *one party* | junk news per 100 links, 2019 | logo: facebook"}


def test_parsers():
    r = vox.plan_for("reel", SPECS["reel"])
    assert r["badge"] == vox.BADGES["recreation"]                       # a recreated post is always labelled
    assert vox.plan_for("reel", SPECS["reel"] + " | badge: reported")["badge"] == vox.BADGES["reported"]
    c = vox.parse_conveyor(SPECS["conveyor"])
    assert c["stamp"] == "APPROVED" and c["n"] == 6
    t = vox.parse_tiles(SPECS["tiles"])
    assert t["name"] == "Bihar" and len(t["pts"]) == 72 and t["per"] == 1000 and t["others"]
    assert vox.parse_tiles("Atlantis | 5 | 1 tile = 10 x") is None
    p = vox.parse_pile(SPECS["pile"])
    assert p["n"] == 17 and p["stamps"] == ["FALSE", "MISLEADING"]
    g = vox.parse_grids("pro-BJP pages 28 vs pro-Congress pages 21 | t")
    assert [v["value"] for v in g["values"]] == [28, 21]
    assert vox.parse_grids("a 120, b 3 | over a hundred") is None and vox.parse_grids("a 5 | one grid") is None
    e = scene3d.parse_explode("phone | THE POST: your screen; THE SIGN-OFF: one official, every post")
    assert e["layers"][1] == "THE SIGN-OFF: one official, every post"


@pytest.mark.parametrize("kind", list(SPECS))
def test_renders_cleanly_tall(kind, tmp_path):
    """At the real Short size (the readability floor makes half-size test frames unrepresentative)."""
    if not motion.enabled():
        return
    out = vox.render(kind, SPECS[kind], "editorial~0@#D7262B/newsprint/", 1080, 1920, 2.5, tmp_path / f"{kind}.mp4", tmp_path / "w", fps=6)
    qa = json.loads(Path(str(out).replace(".mp4", ".qa.json")).read_text())
    assert not qa["text_cut_off"] and not qa["text_overlap"], qa
