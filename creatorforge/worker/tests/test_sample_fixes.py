"""Fixes found by the 2026-11-12 samples: region maps, the Fly kind in the studio, colon captions, no blank-circle
stand-ins, and the badge kept clear of a photo caption."""
from pathlib import Path

import pytest

from creatorforge_worker.media import maps, photo, vox


def test_regions_are_one_filled_shape():
    africa = maps._find("Africa")
    assert africa["kind"] == "country" and africa["name"] == "Africa" and len(africa["rings"]) > 40
    assert maps._find("EU")["name"] == "European Union"
    assert maps.parse("Africa | 54 countries")["targets"][0]["name"] == "Africa"
    assert maps._find("Georgia")["name"] == "Georgia"          # a country name still wins over any region


def test_a_colon_in_a_caption_stays_in_the_caption():
    p = photo.parse("photo", "asset:P0001 | Guess: how much of the UN is African?")
    assert p is not None and "Guess: how much" in str(p)
    g = photo.parse("photo", "asset:P0001 | a title | grade: archive")
    assert "archive" in str(g)


def test_a_subject_with_no_picture_is_reported_not_drawn_as_a_circle(monkeypatch):
    from creatorforge_worker.media import cutouts
    monkeypatch.setattr(cutouts, "get", lambda *a, **k: None)
    monkeypatch.setattr(vox, "illustration", lambda *a, **k: None)
    plan = {"subjects": ["zqxv flurbonator"]}
    vox._pictures(plan, None, None, False)
    assert plan["pics"] == [] and plan["missing"] == ["zqxv flurbonator"]


def test_the_badge_sits_above_a_photo_caption():
    js = vox.__dict__.get("JS") or Path(vox.__file__).read_text(encoding="utf-8")
    assert "K.capBox=b.bbox()" in js and "cb.y-U*.04" in js


def test_fly_falls_back_to_the_globe_offline(monkeypatch, tmp_path):
    from creatorforge_worker.media import flyover, globe
    from creatorforge_worker.media.ff import MediaError
    from creatorforge_worker.studio import produce

    def no_tiles(*a, **k):
        raise MediaError("no tiles")
    monkeypatch.setattr(flyover, "render", no_tiles)
    seen = {}
    monkeypatch.setattr(globe, "render", lambda plan, *a, **k: seen.setdefault("plan", plan) and tmp_path / "x.mp4")
    produce._render_scene("fly", "Nairobi | where it began", "editorial", 640, 360, 3, tmp_path / "x.mp4", tmp_path,
                          24, None, False, None)
    assert seen["plan"]["targets"][0]["name"] == "Nairobi"
    with pytest.raises(produce.ProductionStopped):
        produce._render_scene("fly", "Zzyzxville Nowhere", "editorial", 640, 360, 3, tmp_path / "y.mp4", tmp_path,
                              24, None, False, None)


def test_archetypes_rotate_and_never_repeat_the_last_one():
    from creatorforge_worker.studio import artdirection as ad
    hist, seen = [], []
    for i in range(10):
        doc = ad.direct(f"film{i}", f"Film {i}", "investigation", {}, [{"graphic": "Statement: x", "narration": "x"}], hist)
        assert doc["archetype"] in ad.ARCHETYPES and doc["episode_visual_theme"].startswith("Archetype ")
        assert doc["look"] == ad.ARCHETYPES[doc["archetype"]]["look"]
        if seen:
            assert doc["archetype"] != seen[-1]
        seen.append(doc["archetype"])
        hist.append({"id": f"film{i}", "archetype": doc["archetype"]})
    assert len(set(seen)) >= 3
    assert ad.direct("x", "X", "history", {}, [{"graphic": "Statement: x"}], [], {"archetype": "d"})["archetype"] == "D"
    psych = ad.archetype_for("human", "Dragon Psychology", [{"archetype": "A"}], 0)
    assert psych == "E"
    assert "Episode Visual Theme" in ad.to_markdown(ad.direct("y", "Y", "economics", {}, [{"graphic": "Statement: y"}], []))


def test_sfx_log_rules(tmp_path):
    from creatorforge_worker.studio import sfxlog
    tl = [{"scene": "s1", "start": 0.0, "end": 4.0, "music": "inquiry"}, {"scene": "s2", "start": 4.0, "end": 8.0, "music": "-"},
          {"scene": "s3", "start": 8.0, "end": 12.0, "music": "-"}, {"scene": "s4", "start": 12.0, "end": 15.0, "music": "release"}]
    foley = sfxlog.treat_foley([(Path("whoosh.wav"), 4.0, 0.5)], 24)
    assert abs(foley[0][1] - (4.0 - 2 / 24)) < 1e-9 and foley[0][4] == 800
    assert sfxlog.music_drops(tl) == [(4.0, 12.0)]
    floor = sfxlog.floor_beds(15.0, tl, tmp_path)
    assert floor[0][0].is_file() and abs(floor[0][2] - 10 ** (-35 / 20)) < 1e-3 and floor[1][1] == 4.0 and floor[1][0].is_file()
    md = sfxlog.markdown("T", tl, foley, [], floor, 24, "drone")
    assert "| 00:03:22 | s2 | Foley | whoosh |" in md and "Room tone" in md and "Noise floor" in md and "drop out" in md
