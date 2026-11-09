"""The Vox look: real cut-out photos (halftone, paper edge), the Hero scene, one accent colour, the shared paper,
grain and fonts in every animated graphic."""
import subprocess
from pathlib import Path

import pytest

from creatorforge_worker import director, vox_director
from creatorforge_worker.media import cutouts, motion, vox


def _object_on_white(path: Path) -> Path:
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (600, 500), (252, 252, 250))
    d = ImageDraw.Draw(im)
    d.rectangle((220, 120, 380, 300), fill=(90, 60, 40))           # a gavel-ish head
    d.rectangle((285, 300, 315, 450), fill=(120, 80, 50))          # its handle
    im.save(path)
    return path


def test_a_photo_on_plain_background_becomes_a_halftone_cutout(tmp_path):
    out = cutouts.make(_object_on_white(tmp_path / "raw.png"), tmp_path / "gavel.png")
    assert out and out.is_file()
    from PIL import Image
    im = Image.open(out)
    assert im.mode == "RGBA"
    assert im.getpixel((0, 0))[3] == 0                    # background removed
    px = [im.getpixel((x, y)) for x in range(im.width // 2 - 20, im.width // 2 + 20) for y in range(im.height // 3, im.height // 3 + 30)]
    assert all(abs(p[0] - p[1]) < 6 and abs(p[1] - p[2]) < 8 for p in px)   # printed in black and white


def test_scene_words_resolve_to_library_objects():
    assert cutouts.resolve("money") == "cash"
    assert cutouts.resolve("Court") == "gavel"
    assert cutouts.resolve("person:Narendra Modi") == "person:Narendra Modi"
    assert cutouts.resolve("zzzz") is None


def test_no_photo_and_no_network_means_no_cutout_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    assert cutouts.get("gavel", tmp_path) is None


def test_hero_lines_parse_and_validate():
    p = vox.plan_for("hero", "gavel + crowd | The verdict | 2019 · Supreme Court | five judges | style: disc")
    assert p["subjects"] == ["gavel", "crowd"] and p["headline"] == "The verdict"
    assert p["tags"] == ["2019", "Supreme Court"] and p["note"] == "five judges" and p["layout"] == "disc"
    assert vox.plan_for("hero", "") is None
    assert "hero" in director.FULL_FRAME
    assert vox_director.valid("Hero: gavel | The verdict") == ""
    assert "7 words" in vox_director.valid("Hero: gavel | one two three four five six seven eight")


def test_accent_colour_and_theme_tint_travel_together():
    assert vox.accent_of("editorial~2@red") == vox.ACCENTS["red"]
    assert vox.accent_of("editorial") == vox.ACCENTS["yellow"]
    assert vox.accent_of("editorial@#123456") == "#123456"
    assert motion.split_theme("editorial~1@blue")[1] == motion.PALETTE[1]


def test_rules_give_objects_a_hero_scene():
    g = vox_director.rule_graphic("आलोचकों ने कहा, ये झूठ फैलाने की खुली छूट थी।")
    assert g.startswith("Hero: mask")


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
def test_a_hero_scene_renders_with_a_photo_and_with_only_an_icon(tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    lib = tmp_path / "lib"
    cutouts.make(_object_on_white(tmp_path / "raw.png"), lib / "gavel.png")
    for spec in ("gavel | The verdict | 2019 · Supreme Court | five judges", "ballot box | Vote | style: word"):
        out = tmp_path / f"{len(spec)}.mp4"
        vox.render("hero", spec, "editorial@red", 640, 360, 2.0, out, tmp_path / "w", lib=lib, fetch=False, fps=12)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                                 capture_output=True, text=True).stdout)
        assert 1.8 < d < 2.3


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
def test_a_video_with_hero_lines_renders_them(cfg, monkeypatch):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    script = ("एक ही मैसेज, लाखों ग्रुप्स में।\nHero: smartphone + crowd | One message | 8 AM · every day\n\n"
              "और अदालत ने फ़ैसला सुनाया।\nHero: gavel | The verdict | style: word\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "style": "editorial", "vox_graphics": True,
                                              "template": "youtube_longform"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()), timeout=600)
        assert job["status"] == "READY", job
        assert len(list((cfg.jobs_dir / jid / "work").glob("hero_*.mp4"))) == 2


def test_round_two_scenes_parse_and_validate():
    assert vox.plan_for("pinmap", "Kota | A speech | HT, Sep 2018")["pin"]
    assert vox.plan_for("pinmap", "Atlantis | x") is None
    pb = vox.plan_for("pinboard", "gavel · 20 SEP 2018 · SOLVED | The case")
    assert [i["kind"] for i in pb["items"]] == ["photo", "date", "word"] and pb["tone"] == "kraft"
    assert vox.plan_for("clipping", "Rupee falls 9% | The Hindu, Jan 2024 | cash | 02")["number"] == "02"
    assert vox.plan_for("bignumber", "1984 | television | War is peace")["number"] == "1984"
    assert vox.plan_for("bignumber", "no digits | tv") is None
    assert vox.plan_for("reveal", "a · b · c | Doc | b")["rows"] == ["a", "b", "c"]
    assert vox.plan_for("opener", "tv | He noticed *something*")["headline"]
    for k in vox.KINDS:
        assert k in director.FULL_FRAME
    assert vox_director.valid("Pinmap: Atlantis | x") == "place not found on the map"


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
@pytest.mark.parametrize("kind,spec", [
    ("desk", "documents + pen | Methylated DNA | 1 in 3"),
    ("pinboard", "gavel · old phone · 20 SEP 2018 · SOLVED | The case"),
    ("opener", "television | He noticed *something strange* | Chapter 2"),
    ("reveal", "Fall 2019 · term gpa 3.33 · Dean's list | The transcript | gpa 3.33"),
    ("clipping", "Rupee falls 9% | The Hindu, Jan 2024 | cash | 02"),
    ("pinmap", "Kota | We can make any message viral | Hindustan Times, Sep 2018"),
    ("bignumber", "1984 | television | War is peace | George Orwell")])
def test_every_round_two_scene_renders(kind, spec, tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    out = tmp_path / f"{kind}.mp4"
    vox.render(kind, spec, "editorial@red", 640, 360, 2.0, out, tmp_path / "w", lib=tmp_path / "lib", fetch=False, fps=12)
    assert out.stat().st_size > 2000


def test_object_charts_parse():
    s = vox.plan_for("seats", "NDA 293, INDIA 234, Others 16 | Lok Sabha 2024")
    assert s["total"] == 543 and s["majority"] == 272
    assert vox.plan_for("stack", "coins | UP 80, Bihar 40")["material"] == "coins"
    st = vox.plan_for("stand", "farmer ₹10,218 vs CEO ₹4,24,114 | Monthly income")
    assert [v["value"] for v in st["values"]] == [10218, 424114] and st["subjects"] == ["farmer standing", "businessman"]
    assert vox.plan_for("fan", "A $3M, B $9M | x")["values"][0]["label"] == "B"
    assert len(vox.plan_for("trend", "1990 100, 2000 62, 2024 12 | x | rupee note")["points"]) == 3
    assert vox.plan_for("slice", "12% | brain | activated")["pct"] == 12
    assert vox.plan_for("seats", "nothing") is None and vox.plan_for("slice", "brain") is None
    assert vox_director.valid("Seats: NDA 293, INDIA 234 | Lok Sabha") == ""


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
@pytest.mark.parametrize("kind,spec", [
    ("seats", "NDA 293, INDIA 234, Others 16 | Lok Sabha 2024"), ("stack", "chimneys | China 29.5%, India 6.8% | CO2"),
    ("stand", "farmer ₹10,218 vs CEO ₹4,24,114 | Income"), ("fan", "A $378M, B $57M, C $31M | Revenue"),
    ("trend", "1990 100, 2000 62, 2024 12 | What ₹100 buys"), ("slice", "12% | brain | activated")])
def test_every_object_chart_renders(kind, spec, tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    out = tmp_path / f"{kind}.mp4"
    vox.render(kind, spec, "editorial@blue", 640, 360, 2.0, out, tmp_path / "w", lib=tmp_path / "lib", fetch=False, fps=12)
    assert out.stat().st_size > 2000


def test_music_beats_and_cuts_on_the_beat(tmp_path):
    from creatorforge_worker.media import render
    click, track = tmp_path / "c.wav", tmp_path / "beat.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=0.05,apad=pad_dur=0.45",
                    "-t", "0.5", str(click)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "39", "-i", str(click), "-t", "20", str(track)], check=True)
    beats = render.music_beats(track)
    gaps = [b - a for a, b in zip(beats, beats[1:])]
    assert len(beats) >= 35 and all(abs(g - 0.5) < 0.03 for g in gaps)
    cuts = [1.27, 2.77, 4.21]
    off = render.music_offset(beats, cuts)
    assert all(min(abs(b - (c + off)) for b in beats) <= 0.08 for c in cuts)
    assert render.music_offset([], cuts) == 0.0


def test_channel_rules_flags_logos_and_props():
    assert "flags" in vox_director.valid("Hero: flag | India")
    assert "brand logos" in vox_director.valid("Hero: google logo | Ads")
    assert vox_director.valid("Hero: smartphone | Google ads | Google · 30 days") == ""
    assert "props" in vox_director.valid("Hero: person:A | Claim | prop: blindfold")
    assert vox_director.valid("Hero: person:A | Claim | prop: blindfold", props=True) == ""
    assert "real person" in vox_director.valid("Hero: gavel | Claim | prop: blindfold", props=True)
    out, rep = vox_director.ensure("एक।\nHero: person:A | The claim | prop: blindfold\n")
    assert "prop" not in out.lower() and "Hero: person:A | The claim" in out
    s = "एक।\nHero: person:A | x | prop: blindfold\n\nदो।\nHero: person:B | y\n"
    assert any("fair" in i["problem"] for i in vox_director.check(s, props=True))


def test_props_only_when_the_video_allows_them():
    assert vox.plan_for("hero", "person:A | x | prop: blindfold")["prop"] == "blindfold"
    assert vox.plan_for("hero", "person:A | x | prop: halo")["prop"] == ""
    from creatorforge_worker import director as d
    assert d.ProductionSpec.from_dict({"idea": "a test idea here", "editorial_props": True}).editorial_props
    assert not d.ProductionSpec.from_dict({"idea": "a test idea here"}).editorial_props


def test_round_five_scenes_parse():
    r = vox.plan_for("route", "New Delhi → Dubai → London | The route | plane")
    assert [s["name"] for s in r["stops"]] == ["New Delhi", "Dubai", "London"] and r["shapes"] and r["vehicle"] == "plane"
    assert vox.plan_for("route", "Atlantis → Dubai") is None
    assert vox.plan_for("compare", "rupee note | 1991 | 2024")["left"] == "1991"
    p = vox.plan_for("photoline", "1935 Laws (documents) → 1939 War (soldier) | WWII")
    assert [i["when"] for i in p["items"]] == ["1935", "1939"] and p["subjects"] == ["documents", "soldier"]
    assert vox.plan_for("tv", "television | 1975")["subjects"] == ["television"]
    assert vox.plan_for("hero", "gavel | x | style: grid")["layout"] == "grid"


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
@pytest.mark.parametrize("kind,spec", [
    ("route", "New Delhi → Dubai → London | Route | plane"), ("compare", "rupee note | 1991 | 2024 | Then and now"),
    ("photoline", "1935 Laws (documents) → 1939 War (soldier) | WWII"), ("tv", "television | 1975 | Broadcast"),
    ("hero", "gavel | Verdict | 2019 · Court | style: grid")])
def test_every_round_five_scene_renders(kind, spec, tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    out = tmp_path / f"{kind}.mp4"
    vox.render(kind, spec, "editorial", 640, 360, 2.0, out, tmp_path / "w", lib=tmp_path / "lib", fetch=False, fps=12)
    assert out.stat().st_size > 2000


def test_round_six_scenes_parse():
    c = vox.plan_for("clockmap", "Mumbai 9:30, Kolkata 9:30, Chennai 9:30 | One clock | IST")
    assert [x["shown"] for x in c["cities"]] == ["9:30"] * 3 and c["home"] == "India"
    assert vox.plan_for("clockmap", "Atlantis 9:30, Mumbai 9:30") is None
    assert vox.plan_for("tornsplit", "ship + crane | One steel box | 1956")["subjects"] == ["ship", "crane"]
    n = vox.plan_for("newscard", "29 Aug 2024 | A headline | the line under it | person:A | The Paper")
    assert n["subjects"] == ["person:A"] and n["source"] == "The Paper" and n["sub"] == "the line under it"
    assert vox.plan_for("blueprint", "factory | How it works | a · b")["points"] == ["a", "b"]
    assert vox.plan_for("route", "London → Paris | Tour | train | atlas")["atlas"]
    assert vox.plan_for("pinmap", "Kota | head | src | atlas")["atlas"]


def test_satellite_fly_in_option(monkeypatch):
    from creatorforge_worker.media import flyover
    monkeypatch.setattr(flyover, "geocode", lambda name: (25.18, 75.83))
    p = flyover.parse("Kota | Where it began | satellite")
    assert p["satellite"] and p["title"] == "Where it began"
    assert not flyover.parse("Kota | Where it began")["satellite"]
    st = flyover.satellite_style()
    assert st["sources"]["sat"]["type"] == "raster" and "{z}" in st["sources"]["sat"]["tiles"][0]


@pytest.mark.skipif(not motion.enabled(), reason="needs Chromium + Playwright")
@pytest.mark.parametrize("kind,spec", [
    ("clockmap", "Mumbai 9:30, Kolkata 9:30, Chennai 9:30 | One clock | IST"),
    ("tornsplit", "ship + crane | One steel box | 1956"),
    ("newscard", "29 Aug 2024 | A headline | the line under it | gavel | The Paper"),
    ("blueprint", "factory | How it works | a · b"),
    ("route", "London → Paris | Tour | train | atlas"), ("pinmap", "Kota | head | src | atlas")])
def test_every_round_six_scene_renders(kind, spec, tmp_path, monkeypatch):
    monkeypatch.setenv("CF_CUTOUT_FETCH", "0")
    out = tmp_path / f"{kind}.mp4"
    vox.render(kind, spec, "editorial", 640, 360, 2.0, out, tmp_path / "w", lib=tmp_path / "lib", fetch=False, fps=12)
    assert out.stat().st_size > 2000
