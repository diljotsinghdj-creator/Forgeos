"""The style tools: BiRefNet / LaMa / SAM 2 fallbacks, footage tracking, deck.gl data maps, satellite before / after.
Synthetic pictures only; the imagery services are stood in for."""
import io
import json
import subprocess
import urllib.parse

import pytest

from creatorforge_worker import vox_director
from creatorforge_worker.media import datamap, inpaint, motion, photo, satellite, track, vox
from creatorforge_worker.media.ff import MediaError
from creatorforge_worker.studio import decide


def _jpeg(w, h, sea, cloudy=False):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (176, 150, 110))
    d = ImageDraw.Draw(im)
    d.ellipse([w * (.5 - sea), h * (.5 - sea), w * (.5 + sea), h * (.5 + sea)], fill=(30, 70, 95))
    if cloudy:
        d.rectangle([0, 0, w * .8, h * .8], fill=(240, 240, 240))
    b = io.BytesIO()
    im.save(b, "JPEG")
    return b.getvalue()


@pytest.fixture()
def gibs(monkeypatch, tmp_path):
    asked = []

    def fake(url, data, headers):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        day = q["TIME"][0]
        asked.append(day)
        return _jpeg(int(q["WIDTH"][0]), int(q["HEIGHT"][0]), .4 if day < "2010" else .12, cloudy=day.endswith("-01"))
    monkeypatch.setattr(satellite, "HTTP", fake)
    monkeypatch.setenv("CF_DATA_DIR", str(tmp_path / "data"))
    return asked


def test_satellite_lines_parse():
    p = satellite.parse("Aral Sea | 2000 vs 2020 | fade | The sea that left | km: 420")
    assert p["dates"] == ["2000-08-01", "2020-08-01"] and p["mode"] == "fade" and p["title"] == "The sea that left" and p["km"] == 420
    b = satellite.parse("bbox: 58,43,62,47 | 2017-06 vs 2023-06-20 | source: sentinel")
    assert b["bbox"] == [58, 43, 62, 47] and b["dates"] == ["2017-06-15", "2023-06-20"] and b["source"] == "sentinel" and b["mode"] == "swipe"
    assert satellite.parse("Aral Sea | 2000") is None                       # one date is not a before / after
    assert satellite.parse("Nowhereville Xq | 2000 vs 2020") is None        # never a guessed position
    assert satellite.parse("bbox: 62,43,58,47 | 2000 vs 2020") is None
    url = satellite.gibs_url("modis", [58, 43, 62, 47], "2000-08-01", 800, 600)
    assert "MODIS_Terra_CorrectedReflectance_TrueColor" in url and "TIME=2000-08-01" in url and "BBOX=58.0000%2C43.0000" in url
    w, h = satellite._size([58, 43, 62, 47], 1000)
    assert h == 1000 and 700 < w < 760                                    # degrees of longitude are shorter at 45°N


def test_satellite_picks_the_clearest_day_and_never_another_year(gibs, tmp_path):
    plan = satellite.parse("Aral Sea | 2000-08-01 vs 2020-08-01")
    shots = satellite.fetch(plan, tmp_path / "c", 400)
    assert [s["date"] for s in shots] == ["2000-08-02", "2020-08-02"]      # the asked day is cloudy; the next is clear
    assert all(abs(int(d[-2:]) - 1) <= 2 for d in gibs)                    # only days round the asked date are tried
    assert shots[0]["credit"].startswith("NASA GIBS / MODIS Terra")
    with pytest.raises(MediaError, match="starts on"):
        satellite.fetch(satellite.parse("Aral Sea | 1995 vs 2020"), tmp_path / "c", 400)
    line, credit, _ = satellite.prepare("Aral Sea | 2000 vs 2020 | split | Then and now", tmp_path / "w", 640, 360)
    assert " | split | Then and now | labels: 2000, 2020" in line and credit == "NASA GIBS / MODIS Terra"
    assert photo.parse("photos", line)["mode"] == "split"


def test_sentinel_needs_its_keys_and_sends_a_least_cloud_request(monkeypatch, tmp_path):
    for k in ("CF_CDSE_CLIENT_ID", "CF_CDSE_CLIENT_SECRET", "SH_CLIENT_ID", "SH_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    plan = satellite.parse("bbox: 58,43,62,47 | 2017 vs 2023 | source: sentinel")
    # without keys the public AWS archive is used instead (test_sentinel_without_an_account_...)
    monkeypatch.setenv("CF_CDSE_CLIENT_ID", "id")
    monkeypatch.setenv("CF_CDSE_CLIENT_SECRET", "secret")
    sent = []

    def fake(url, data, headers):
        sent.append((url, data, headers))
        if url.endswith("/token"):
            return json.dumps({"access_token": "t0k"}).encode()
        return _jpeg(300, 300, .3)
    monkeypatch.setattr(satellite, "HTTP", fake)
    shots = satellite.fetch(plan, tmp_path / "c", 600)
    assert len(shots) == 2 and shots[1]["credit"] == "Contains modified Copernicus Sentinel data 2023"
    body = json.loads(sent[1][1])
    assert sent[1][2]["Authorization"] == "Bearer t0k" and body["input"]["data"][0]["dataFilter"]["mosaickingOrder"] == "leastCC"
    assert sum(1 for u, _, _ in sent if u.endswith("/token")) == 1
    with pytest.raises(MediaError, match="mid-2015"):
        satellite.fetch(satellite.parse("bbox: 58,43,62,47 | 2005 vs 2023 | source: sentinel"), tmp_path / "c")


def test_data_maps_parse_and_arcs_stay_on_the_map():
    f = datamap.parse("flowmap", "China → USA 120, China → Netherlands 90 | Container trade | million tonnes | src: test")
    assert [i["value"] for i in f["items"]] == [120, 90] and f["unit"] == "million tonnes" and f["src"] == "test"
    path = f["items"][0]["path"]
    lats = [p[1] for p in path]
    assert max(lats) <= max(path[0][1], path[-1][1]) + 1e-6               # a straight line on the flat map, not over the pole
    assert max(p[2] for p in path) <= 900_000
    assert datamap.parse("flowmap", "China → Atlantisq 5 | x") is None
    c = datamap.parse("columns", "India 1.43, China 1.41 | Population | billion")
    assert c["type"] == "columns" and len(c["items"]) == 2 and datamap.parse("dots", "Tokyo 37 | One") is None


def test_new_kinds_are_known_to_the_director_and_the_decision_engine():
    for g in ("Satellite: Aral Sea | 2000 vs 2020 | swipe | Gone", "Flowmap: China → USA 120 | Trade",
              "Columns: India 1.4, China 1.4 | People", "Dots: Tokyo 37, Delhi 32 | Cities"):
        assert vox_director.valid(g) == "", g
    assert vox_director.valid("Satellite: Nowhereville Xq | 2000 vs 2020")
    assert all(k in vox.KINDS for k in ("satellite", "flowmap", "columns", "dots"))
    opt = {"treatment": "graphic", "what": "Satellite: Aral Sea | 2000 vs 2020"}
    from creatorforge_worker import infographic
    s = decide.score(opt, "The sea shrank.", infographic.facts("The sea shrank."), "geography", [], True, False)
    assert s["authentic"] == 1.0


def test_lama_falls_back_to_opencv_and_tracking_fills_lost_frames(tmp_path, monkeypatch):
    import numpy as np
    from PIL import Image
    monkeypatch.setenv("CF_LAMA", str(tmp_path / "none.pt"))
    rgb = np.full((60, 80, 3), 120, np.uint8)
    mask = np.zeros((60, 80), np.uint8)
    mask[20:40, 30:50] = 255
    rgb[20:40, 30:50] = 0
    out, how = inpaint.fill(rgb, mask)
    assert how == "OpenCV inpainting" and abs(int(np.asarray(out)[30, 40].mean()) - 120) < 25
    frames = []
    for i in range(4):
        f = tmp_path / f"f{i:05d}.jpg"
        Image.new("RGB", (80, 60), (10, 10, 10)).save(f)
        frames.append(f)

    def fake(fr, box):
        ms = []
        for i in range(len(fr)):
            m = np.zeros((30, 40), np.uint8)
            m[5:15, 5 + i * 5:15 + i * 5] = 255
            ms.append(None if i == 2 else m)                      # a lost frame keeps the last mask
        return ms
    monkeypatch.setattr(track, "BACKEND", fake)
    res, how = track.track(frames, [.1, .1, .3, .3], tmp_path / "m")
    assert how == "test tracker" and len(res) == 4 and res[2]["cx"] == res[1]["cx"] and res[3]["cx"] > res[0]["cx"]
    assert Image.open(res[0]["mask"]).size == (80, 60)
    p = photo.parse("footage", "c.mp4 | cutout | follow: the boat | subject: .2,.2,.3,.3")
    assert p["cutout"] and p["follow"] == "the boat" and p["subject"] == [.2, .2, .3, .3] and p["title"] == ""


def test_satellite_and_data_map_scenes_render(gibs, tmp_path):
    if not motion.enabled():
        return
    for mode in ("swipe", "fade"):
        out = vox.render("satellite", f"Aral Sea | 2000 vs 2020 | {mode} | Gone", "e~0@red/field/", 480, 270, 3, tmp_path / f"s{mode}.mp4",
                         tmp_path / "w", fps=8)
        assert out.stat().st_size > 3000
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "2.8", "-i", str(tmp_path / "sswipe.mp4"), "-frames:v", "1", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    import numpy as np
    a = np.frombuffer(raw, np.uint8).reshape(270, 480, 3).astype(int)
    assert ((a[..., 2] > a[..., 0] + 30)).mean() < 0.25                  # the wipe ends on the small 2020 sea
    out = vox.render("dots", "Tokyo 37, Delhi 32, Shanghai 29 | Cities | million", "e~0@red/field/", 480, 270, 2, tmp_path / "d.mp4",
                     tmp_path / "w", fps=6)
    assert out.stat().st_size > 3000


def test_sentinel_without_an_account_uses_the_public_aws_archive(monkeypatch, tmp_path):
    from PIL import Image
    from creatorforge_worker.media import sentinel_aws
    for k in ("CF_CDSE_CLIENT_ID", "CF_CDSE_CLIENT_SECRET", "SH_CLIENT_ID", "SH_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(sentinel_aws, "tile_of", lambda lon, lat: ("41", "T", "NM"))

    def http(url):
        if "list-type=2" in url:
            pre = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["prefix"][0]
            return ("<ListBucketResult>" + "".join(f"<CommonPrefixes><Prefix>{pre}S2A_41TNM_2023{pre.split('/')[-2].zfill(2)}{d:02d}_0_L2A/</Prefix></CommonPrefixes>"
                                                    for d in (3, 10, 18)) + "</ListBucketResult>").encode()
        cloud = {"03": 60.0, "10": 2.0, "18": 1.5}[url.split("_0_L2A.json")[0][-2:]]
        return json.dumps({"properties": {"eo:cloud_cover": cloud, "s2:nodata_pixel_percentage": 0}}).encode()
    reads = []
    monkeypatch.setattr(sentinel_aws, "HTTP", http)
    monkeypatch.setattr(sentinel_aws, "READ", lambda url, bbox, w, h: reads.append(url) or Image.new("RGB", (w, h), (90, 120, 80)))
    plan = satellite.parse("bbox: 58.6,43.6,59.1,43.95 | 2023-06-12 vs 2023-06-20 | source: sentinel")
    shots = satellite.fetch(plan, tmp_path / "c", 400)
    assert shots[0]["date"] in ("2023-06-10", "2023-06-18") and "AWS Open Data" in shots[0]["credit"]
    assert all(u.endswith("/TCI.tif") for u in reads) and "2023-06-03" not in shots[0]["date"]   # the cloudy scene loses
