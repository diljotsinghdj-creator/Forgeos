"""The sunrise map (media/sunrise.py): the Sun's position is right, the specs parse, and a clip renders."""
from datetime import date

from creatorforge_worker.media import sunrise as s


def test_sunrise_times_match_published_values():
    d = date(2026, 6, 21)
    delhi = s.sunrise(77.21, 28.61, d, 5.5)          # Delhi's midsummer sunrise is published as about 5:23-5:24 IST
    assert abs(delhi - (5 + 23.5 / 60)) < 3 / 60
    dong, kutch = s.sunrise(97.02, 28.17, d, 5.5), s.sunrise(68.8, 23.8, d, 5.5)
    assert dong < 4.5 and 2.0 < kutch - dong < 2.2   # Arunachal before 4:30; Kutch just over two hours later


def test_parse_sunrise_zones_and_frozen_clock():
    p = s.parse("sunrise", "21 June 2026 3:50 → 4:30 | IST 5.5 | pins: Dong @97.02,28.17 | Title")
    assert p["t0"] < p["t1"] and p["pins"][0]["lon"] == 97.02 and p["title"] == "Title"
    q = s.parse("sunrise", "21 June 2026 5:15 | IST 5.5 | clocks: Delhi @77.21,28.61 | One clock")
    assert q["t0"] == q["t1"] == 5.25 and q["clocks"][0]["name"] == "Delhi"
    z = s.parse("zones", "89.87 | IST-I, UTC+5:30; IST-II, UTC+6:30 | Two clocks | note")
    assert z["split"] == 89.87 and len(z["names"]) == 2
    assert s.parse("sunrise", "sometime | x") is None


def test_render_small_clip(tmp_path):
    from creatorforge_worker.media import ff
    p = s.parse("sunrise", "21 June 2026 4:00 → 4:20 | IST 5.5 | pins: Dong @97.02,28.17 | T")
    out = s.render(p, 320, 180, 1.0, tmp_path / "a.mp4", fps=8)
    assert ff.duration(out) > 0.8
