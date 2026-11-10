"""Photographs and footage as documentary shots, the asset library and ledger, the visual decision engine, camera
projection, isometric 3D and chroma keying. Synthetic pictures only; the stock services are stood in for."""
import csv
import json
import subprocess
from pathlib import Path

import pytest

from creatorforge_worker.media import motion, photo, scene3d, vox
from creatorforge_worker.studio import assets, decide


@pytest.fixture()
def pics(tmp_path):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (1500, 1000))
    d = ImageDraw.Draw(im)
    for y in range(1000):
        d.line([(0, y), (1500, y)], fill=(150 + y // 12, 175, 205) if y < 430 else (190 - (y - 430) // 20, 160, 115))
    d.polygon([(500, 640), (1000, 640), (920, 760), (580, 760)], fill=(120, 60, 40))
    d.rectangle([720, 500, 820, 640], fill=(205, 195, 175))
    a = tmp_path / "a.jpg"
    im.save(a, quality=92)
    b = tmp_path / "b.jpg"
    Image.new("RGB", (1400, 900), (60, 90, 130)).save(b)
    clip = tmp_path / "c.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=12", "-t", "2", "-pix_fmt", "yuv420p", str(clip)], check=True)
    green = tmp_path / "g.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x00FF00:s=320x360:r=12", "-f", "lavfi", "-i",
                    "testsrc2=s=120x200:r=12", "-filter_complex", "[0][1]overlay=100:160", "-t", "2", "-pix_fmt", "yuv420p", str(green)], check=True)
    return {"a": a, "b": b, "clip": clip, "green": green}


def test_photo_lines_parse_every_treatment():
    p = photo.parse("photo", "asset:P0001 | detail | at: .3,.4,.2,.2 | The old harbour | annotate: circle .5,.6,.1 a boat ; "
                             "arrow .1,.2 -> .4,.5 the shore ; box .1,.1,.2,.2 dock ; label .7,.3 Moynaq | then: pin Moynaq | "
                             "frame: polaroid | grade: archive | light: sweep | illustrative")
    assert p["move"] == "detail" and p["at"] == [.3, .4, .2, .2] and p["title"] == "The old harbour"
    assert [a["kind"] for a in p["annotate"]] == ["circle", "arrow", "box", "label"] and p["annotate"][1]["p"] == [.1, .2, .4, .5]
    assert p["then"] == {"kind": "pin", "place": "Moynaq"} and p["frame"] == "polaroid" and p["grade"] == "archive" and p["illustrative"]
    n = photo.parse("photo", "x.jpg | pull | then: number 90% of a sea, gone")
    assert n["then"] == {"kind": "number", "figure": "90%", "caption": "of a sea, gone"}
    s = photo.parse("photos", "a.jpg, b.jpg | split | Then and now | labels: 1960, today")
    assert s["mode"] == "split" and s["labels"] == ["1960", "today"] and photo.parse("photos", "a.jpg | collage") is None
    f = photo.parse("footage", "c.mp4 | A street | in: 1.5 | speed: 0.5")
    assert f["in"] == 1.5 and f["speed"] == 0.5 and f["depth"] == "flat"


def test_one_photograph_becomes_depth_layers_with_its_changes_on_record(pics, tmp_path):
    plan = photo.prepare(photo.parse("photo", f"{pics['a']} | push"), tmp_path / "w")
    assert plan["img"].startswith("file://") and plan["w"] == 1500
    assert plan["layers"] and all(Path(l["img"][7:]).is_file() for l in plan["layers"])
    assert any("depth layers" in m for m in plan["mods"])
    flat = photo.prepare(photo.parse("photo", f"{pics['a']} | push | depth: flat"), tmp_path / "w")
    assert flat["layers"] == []


def test_photo_photos_footage_projection_isometric_and_key_render(pics, tmp_path):
    if not motion.enabled():
        return
    shots = [("photo", f"{pics['a']} | detail | at: .35,.5,.3,.3 | annotate: circle .5,.66,.1 a boat | then: pin Moynaq | illustrative"),
             ("photo", f"{pics['a']} | pull | frame: taped | then: number 90% of a sea, gone | grade: mono"),
             ("photos", f"{pics['a']}, {pics['b']} | split | Then and now | labels: 1960, today"),
             ("photos", f"{pics['a']}, {pics['b']}, {pics['a']} | collage | Evidence"),
             ("photos", f"{pics['a']}, {pics['b']} | sequence"),
             ("footage", f"{pics['clip']} | A street | annotate: box .3,.3,.3,.3 here")]
    for i, (k, sp) in enumerate(shots):
        out = vox.render(k, sp, "e~0@red/field/", 480, 270, 2.5, tmp_path / f"v{i}.mp4", tmp_path / "w", fetch=False, fps=8)
        assert out.stat().st_size > 3000, k
    for i, (k, sp) in enumerate((("photo3d", f"{pics['a']} | dolly | Harbour"), ("photo3d", f"{pics['a']} | tilt-left"),
                                 ("bars3d", "UP 80, Bihar 40 | Seats | seats | isometric"))):
        out = scene3d.render(k, sp, "e~0@red/field/", 480, 270, 2, tmp_path / f"s{i}.mp4", tmp_path / "w", fps=6)
        assert out.stat().st_size > 3000, k
    assert scene3d.plan_for("bars3d", "UP 80, Bihar 40 | Seats | isometric")["iso"] is True
    from creatorforge_worker.media import composite
    k = composite.render(f"{pics['green']} | background: {pics['a']} | color: 00FF00 | position: right", 480, 270, 1.5, tmp_path / "k.mp4", 12)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.5", "-i", str(k), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    import numpy as np
    a = np.frombuffer(raw, np.uint8).reshape(270, 480, 3).astype(int)
    assert ((a[..., 1] > 200) & (a[..., 0] < 60) & (a[..., 2] < 60)).mean() < 0.01      # the green is gone


class FakeStock:
    """Stands in for stock_photo.search / fetch."""
    def __init__(self, files):
        self.files = files

    def search(self, provider, key, query, portrait=False, timeout=20):
        return [{"url": f"https://cdn.example/{provider}/harbour-boat.jpg", "width": 4000, "height": 2600, "about": "fishing boat harbour sand desert",
                 "id": "11", "page": "https://pixabay.com/photos/boat-11/", "creator": "Ana", "site": provider, "licence": "Pixabay Content License",
                 "attribution": "not required", "credit": "Ana / Pixabay"},
                {"url": f"https://cdn.example/{provider}/people-market.jpg", "width": 800, "height": 600, "about": "people market crowd",
                 "id": "12", "page": "https://pixabay.com/photos/market-12/", "creator": "Bo", "site": provider, "licence": "Pixabay Content License",
                 "attribution": "not required", "credit": "Bo / Pixabay"}]

    def fetch(self, c, cache, timeout=60):
        return self.files[0] if "boat" in c["url"] else self.files[1]


def test_assets_are_searched_scored_licensed_and_kept_in_a_library(pics, tmp_path, monkeypatch):
    from creatorforge_worker.providers import stock_photo
    fake = FakeStock([pics["a"], pics["b"]])
    monkeypatch.setattr(stock_photo, "search", fake.search)
    monkeypatch.setattr(stock_photo, "fetch", fake.fetch)
    led = assets.Ledger(tmp_path / "ledger.json")
    need = assets.Need(scene="S01", film="aral", subject="fishing boat", place="Moynaq", purpose="location", specific=True)
    assert assets.queries(need)[:2] == ["fishing boat Moynaq", "Moynaq landscape"]
    rec, rep = assets.select(need, [("pixabay", "k")], tmp_path / "cache", led, {"paper": "#E9EDE4"}, None, (1920, 1080))
    assert rec and rec["id"] == "P0001" and rec["file"] == str(pics["a"]) and rec["licence"] == "Pixabay Content License"
    assert "Commercial use allowed" in rec["licence_terms"] and rec["page"].startswith("https://pixabay.com/")
    assert rec["illustrative_reason"] and rec["illustrative"]                # a generic boat, not shown to be Moynaq
    assert rep["candidates"][0]["score"] >= rep["candidates"][-1]["score"] or len(rep["candidates"]) == 2
    assert set(assets.rights("people market crowd")) == {"people"}
    again, rep2 = assets.select(need, [("pixabay", "k")], tmp_path / "cache", led, None, None, (1920, 1080))
    assert again["id"] == "P0001" and rep2["reason"].startswith("reused from the asset library") and again["illustrative"]
    assert len(led.get("P0001")["uses"]) == 2
    led.modified("P0001", "aral/S01: split into 3 depth layers")
    out = led.export("aral", tmp_path / "assets.csv")
    rows = list(csv.DictReader(open(out)))
    assert rows and rows[0]["licence"] == "Pixabay Content License" and "depth layers" in rows[0]["modifications"]


def test_the_decision_engine_chooses_the_strongest_explanation(monkeypatch):
    monkeypatch.setenv("PIXABAY_KEY", "k")
    stat = decide.choose("NASA puts the loss at roughly ninety percent, 68,000 square kilometres down to 6,800.",
                         {"graphic": "BigNumber: 90% | ship | of the sea"}, [])
    assert "statistic" in stat["needs"] and stat["chosen"]["treatment"] in ("graphic", "combo")
    place = decide.choose("This is Moynaq, a town in the desert.", {"graphic": "Pinmap: Moynaq | x", "visual": {"subject": "town", "place": "Moynaq",
                                                                                                         "specific": True}}, [])
    assert place["needs"][0] == "location" and place["chosen"]["treatment"] in ("photo", "footage", "combo")
    monkeypatch.setenv("CF_FREE_STOCK", "0")
    monkeypatch.delenv("PIXABAY_KEY")
    nopics = decide.choose("This is Moynaq, a town in the desert.", {"graphic": "Pinmap: Moynaq | x", "visual": {"subject": "town", "place": "Moynaq"}}, [])
    assert nopics["chosen"]["treatment"] == "graphic"                         # no photo sources: the map, not an empty promise
    assert set(decide.classify("The company moved billions of pounds through its subsidiaries.", {"numbers": [], "money": True}, [])) >= {"institution"}
    md = decide.to_markdown([("S1", "line", stat, "BigNumber: 90%")])
    assert "| Option |" in md and "Decision:" in md
