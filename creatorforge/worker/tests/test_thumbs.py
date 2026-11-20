"""Face-off thumbnails: 9:16, the people's photos and the map of India drawn, credits kept for the description."""
from PIL import Image, ImageDraw

from creatorforge_worker import thumbs
from creatorforge_worker.media import maps


def test_face_off_thumbnail(tmp_path, monkeypatch):
    def fake(name, cache):
        im = Image.new("RGB", (600, 800), (90, 100, 120))
        ImageDraw.Draw(im).ellipse((200, 120, 400, 360), fill=(200, 200, 205))
        return im, f"{name}: Someone / Wikimedia Commons (CC BY 4.0)"
    monkeypatch.setattr(thumbs, "photo", fake)
    out = tmp_path / "t.png"
    credits = thumbs.face_off(["Narendra Modi", "Amit Shah", "Gyanesh Kumar"], ["Rahul Gandhi"], "Chunav Ayog Ka Sach",
                              "Chunav Ayukt Kaun Chunta Hai?", "CJI Bahar! 2 vs 1", "Sarkar + CEC", "Vipaksh", out,
                              tmp_path / "data")
    assert Image.open(out).size == (1080, 1920)
    assert len(credits) == 4 and credits[0].startswith("Narendra Modi:")


def test_india_is_drawn_with_its_official_northern_boundary():
    lats = [p[1] for r in maps._find("India")["rings"] for p in r]
    assert max(lats) > 36.8           # all of Jammu & Kashmir and Ladakh, as on the Survey of India map
