"""Keyless stock footage (NASA, Wikimedia Commons): relevance and licence filters, source fallback, trimming."""
import subprocess

import httpx
import pytest

from creatorforge_worker.providers import stock_video
from creatorforge_worker.providers.base import ProviderError


class R:
    def __init__(self, data, code=200):
        self._d, self.status_code = data, code

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("bad", request=None, response=None)


def test_relevance_needs_the_search_words():
    assert stock_video.relevant("rocket launch", "Artemis I rocket launches from Kennedy")
    assert not stock_video.relevant("rocket launch", "Astronaut interview about the space station")
    assert stock_video.relevant("ocean waves crashing", "Big waves on the ocean at dawn")   # 2 of 3 is enough
    assert not stock_video.relevant("", "anything")


def test_nasa_picks_large_file_of_a_matching_video(monkeypatch):
    def get(url, **kw):
        if url.endswith("/search"):
            return R({"collection": {"items": [
                {"data": [{"nasa_id": "a1", "title": "Press conference", "description": "officials talk"}]},
                {"data": [{"nasa_id": "b2", "title": "Rocket launch at night", "keywords": ["launch"]}]}]}})
        assert url.endswith("/asset/b2")
        return R({"collection": {"items": [{"href": "http://images-assets.nasa.gov/video/b2/b2~orig.mp4"},
                                           {"href": "http://images-assets.nasa.gov/video/b2/b2~large.mp4"}]}})
    monkeypatch.setattr(httpx, "get", get)
    found = stock_video.search("nasa", "", "rocket launch")
    assert [f["url"] for f in found] == ["https://images-assets.nasa.gov/video/b2/b2~large.mp4"]
    assert found[0]["credit"] == "NASA" and found[0]["trim"]


def test_wikimedia_keeps_free_licences_and_credits_the_author(monkeypatch):
    def page(i, title, licence, h=1080):
        return {"index": i, "title": f"File:{title}.webm", "videoinfo": [{
            "url": f"https://upload.wikimedia.org/{i}.webm", "size": 5_000_000, "width": 1920, "height": h,
            "duration": 30, "extmetadata": {"LicenseShortName": {"value": licence},
                                            "Artist": {"value": "<a href='x'>Jane Doe</a>"}},
            "derivatives": [{"src": f"https://upload.wikimedia.org/{i}.720p.webm", "width": 1280, "height": 720},
                            {"src": f"https://upload.wikimedia.org/{i}.2160p.webm", "width": 3840, "height": 2160}]}]}
    monkeypatch.setattr(httpx, "get", lambda url, **kw: R({"query": {"pages": {
        "1": page(1, "City street at night", "CC BY-NC 4.0"),
        "2": page(2, "Busy city street in Tokyo", "CC BY-SA 4.0"),
        "3": page(3, "Mountain lake", "Public domain")}}}))
    found = stock_video.search("wikimedia", "", "city street")
    assert len(found) == 1
    assert found[0]["url"].endswith("2.720p.webm")
    assert found[0]["credit"] == "Jane Doe / Wikimedia Commons (CC BY-SA 4.0)"


def test_search_any_falls_through_failing_and_empty_sources(monkeypatch):
    calls = []

    def search(provider, key, query, portrait=True):
        calls.append(provider)
        if provider == "pixabay":
            raise ProviderError("down")
        return [] if provider == "nasa" else [{"url": "u", "credit": "c"}]
    monkeypatch.setattr(stock_video, "search", search)
    assert stock_video.search_any([("pixabay", "k"), ("nasa", ""), ("wikimedia", "")], "crowd") == [{"url": "u", "credit": "c"}]
    assert calls == ["pixabay", "nasa", "wikimedia"]


def test_trim_cuts_a_short_h264_piece(tmp_path):
    src = tmp_path / "long.webm"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=20:r=24",
                    "-c:v", "libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8", str(src)], check=True)
    dst = tmp_path / "out.mp4"
    stock_video._trim(src, dst)
    from creatorforge_worker.media import ff
    assert 7.5 <= ff.duration(dst) <= 8.5


def test_free_sources_follow_config(cfg):
    from creatorforge_worker import providers
    assert providers.stock_sources("nojob", cfg) == []          # tests never touch the network
    cfg.free_stock = True
    assert providers.stock_sources("nojob", cfg) == [("nasa", ""), ("wikimedia", ""), ("archive", "")]


def test_render_survives_a_clip_that_changes_size_mid_stream(tmp_path):
    """Stock footage can switch resolution part-way through; each shot is rendered on its own so the final
    edit never has to rebuild a giant filter graph mid-stream (that crashed FFmpeg on a real pod)."""
    import threading
    from creatorforge_worker.media import ff, render
    parts = []
    for i, size in enumerate(("640x360", "320x568")):
        p = tmp_path / f"p{i}.ts"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=s={size}:d=1.5:r=24",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-f", "mpegts", str(p)], check=True)
        parts.append(p.read_bytes())
    mixed = tmp_path / "mixed.ts"
    mixed.write_bytes(b"".join(parts))
    still = tmp_path / "s.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x5a2828:s=540x960", "-frames:v", "1",
                    str(still)], check=True)
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "6",
                    str(audio)], check=True)
    clips = [render.Clip(still, 1.5, "push in", "cut"), render.Clip(still, 2.5, "pan left", "cut", mixed, ff.duration(mixed)),
             render.Clip(still, 1.5, "punch", "flash")]
    out = tmp_path / "out.mp4"
    total = render.render_video(clips, audio, None, 270, 480, out, tmp_path / "work", threading.Event(), grade="film")
    assert abs(ff.duration(out) - total) < 0.2
    again = sorted((tmp_path / "work").glob("seg_*.mp4"))
    assert len(again) == 3                       # a retry reuses these instead of re-rendering


def test_archive_finds_matching_prelinger_film(monkeypatch):
    def get(url, **kw):
        if "advancedsearch" in url:
            assert "collection:(prelinger)" in kw["params"]["q"]
            return R({"response": {"docs": [
                {"identifier": "CookingTips1950", "title": "Kitchen tips", "description": "how to bake"},
                {"identifier": "Office1952", "title": "Office meeting etiquette", "subject": ["business", "meeting"]}]}})
        assert url.endswith("/metadata/Office1952")
        return R({"files": [{"name": "Office1952_512kb.mp4", "format": "512Kb MPEG4", "size": "9000000"},
                            {"name": "Office1952.mp4", "format": "h.264", "size": "60000000", "length": "612.4",
                             "width": "640", "height": "480"},
                            {"name": "Office1952.mpeg", "format": "MPEG2", "size": "900000000"}]})
    monkeypatch.setattr(httpx, "get", get)
    found = stock_video.search("archive", "", "office meeting")
    assert [f["url"] for f in found] == ["https://archive.org/download/Office1952/Office1952.mp4"]
    assert found[0]["credit"] == "Prelinger Archives / Internet Archive" and found[0]["trim"]


def test_openverse_keeps_relevant_commercial_photos(monkeypatch):
    from creatorforge_worker.providers import stock_photo

    def photo(title, lic, w=3000, h=2000, tags=()):
        return {"url": f"https://img/{title}.jpg", "title": title, "license": lic, "license_version": "4.0",
                "width": w, "height": h, "creator": "Ann", "source": "flickr", "tags": [{"name": t} for t in tags]}
    monkeypatch.setattr(httpx, "get", lambda url, **kw: R({"results": [
        photo("chess board", "by-nc"), photo("old chess pieces", "by-sa"), photo("chess", "cc0", 600, 400),
        photo("sunset", "cc0", tags=["beach"])]}))
    found = stock_photo.search("openverse", "", "chess pieces")
    assert [f["url"] for f in found] == ["https://img/old chess pieces.jpg"]
    assert found[0]["credit"] == "Ann / flickr (CC BY-SA 4.0)"


def test_unsplash_uses_client_id_and_credits_photographer(monkeypatch):
    from creatorforge_worker.providers import stock_photo
    seen = {}

    def get(url, **kw):
        seen.update(kw.get("headers") or {})
        return R({"results": [{"urls": {"raw": "https://images.unsplash.com/p1?ixid=x"}, "width": 3000, "height": 4500,
                               "user": {"name": "Jo Lee"}, "links": {"download_location": "https://api.unsplash.com/d/1"}}]})
    monkeypatch.setattr(httpx, "get", get)
    found = stock_photo.search("unsplash", "KEY", "dark hallway")
    assert seen["Authorization"] == "Client-ID KEY"
    assert found[0]["credit"] == "Photo by Jo Lee on Unsplash" and found[0]["url"].endswith("&w=2160&q=85&fm=jpg&fit=max")


def test_photo_sources_order(cfg):
    from creatorforge_worker import providers
    providers.set_stock_key("job-x", {"provider": "pixabay", "key": "pk", "unsplash": "uk"})
    cfg.free_stock = True
    assert providers.photo_sources("job-x", cfg) == [("unsplash", "uk"), ("pixabay", "pk"), ("openverse", "")]
    assert providers.stock_sources("job-x", cfg) == [("pixabay", "pk"), ("nasa", ""), ("wikimedia", ""), ("archive", "")]


def test_photo_fetch_reencodes_and_rejects_junk(tmp_path, monkeypatch):
    from creatorforge_worker.providers import stock_photo
    src = tmp_path / "big.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=3000x2000", "-frames:v", "1", str(src)],
                   check=True)

    class Resp:
        def __init__(self, data):
            self.content = data

        def raise_for_status(self):
            pass
    monkeypatch.setattr(httpx, "get", lambda url, **kw: Resp(src.read_bytes() if "good" in url else b"<html>nope</html>"))
    from creatorforge_worker.media import ff
    out = stock_photo.fetch({"url": "https://x/good.png", "credit": "c"}, tmp_path / "cache")
    stream = ff.probe(out)["streams"][0]
    w, h = int(stream["width"]), int(stream["height"])
    assert out.suffix == ".jpg" and (w, h) == (2400, 1600)
    with pytest.raises(ProviderError):
        stock_photo.fetch({"url": "https://x/bad.png", "credit": "c"}, tmp_path / "cache")


def test_doodle_shots_are_drawn_on(tmp_path):
    """Whiteboard reveal: the first frame is (almost) white paper, the end of the shot is the full picture."""
    import threading
    from creatorforge_worker.media import ff, render
    img = tmp_path / "p.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x2050c0:s=270x480", "-frames:v", "1",
                    str(img)], check=True)
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "3", str(audio)],
                   check=True)
    out = tmp_path / "o.mp4"
    render.render_video([render.Clip(img, 2.5, "static", "cut", reveal="draw")], audio, None, 270, 480, out,
                        tmp_path / "work", threading.Event(), grade="")

    def mean(t):
        p = tmp_path / f"f{t}.raw"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", t, "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                        "-pix_fmt", "gray", str(p)], check=True)
        data = p.read_bytes()
        return sum(data) / len(data)
    assert mean("0.03") > 230 and mean("2.0") < 120     # white paper first, the blue picture at the end


def test_quality_check_reports_loudness_gaps_and_first_frame(tmp_path):
    from creatorforge_worker.media import quality
    good = tmp_path / "good.mp4"
    # bright frame, steady tone at a sensible level, no gaps
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=270x480:d=6:r=24",
                    "-f", "lavfi", "-i", "sine=frequency=220:duration=6", "-af", "volume=0.25",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(good)], check=True)
    bad = tmp_path / "bad.mp4"
    # black first frame, a 2 s silent hole in the middle
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=270x480:d=6:r=24",
                    "-f", "lavfi", "-i", "sine=frequency=220:duration=6",
                    "-af", "volume=0.25,volume=enable='between(t,2,4)':volume=0",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(bad)], check=True)
    g = quality.check(good, 6.0, [0.97], target_lufs=quality.loudness(good)["lufs"])
    assert g["passed"], g
    b = quality.check(bad, 6.0, [0.6])
    names = {c["name"] for c in b["checks"] if not c["ok"]}
    assert {"no dead air", "first frame visible", "narration matches script"} <= names, b


def test_captions_keep_script_spelling_on_whisper_timings():
    from creatorforge_worker.media.captions import script_spelling
    from creatorforge_worker.providers.base import Word
    heard = [Word("off", 0.0, 0.2), Word("com", 0.2, 0.4), Word("fined", 0.4, 0.7), Word("them", 0.7, 0.9)]
    words, ratio = script_spelling(heard, "Offcom fined them.")
    assert [w.text for w in words][-2:] == ["fined", "them."] and ratio < 1
    exact, r2 = script_spelling([Word("Ofcom", 0, 0.3), Word("fined", 0.3, 0.6), Word("them", 0.6, 0.9)], "Ofcom fined them.")
    assert [w.text for w in exact] == ["Ofcom", "fined", "them."] and r2 == 1.0


def test_pronunciations_change_the_voice_not_the_script():
    from creatorforge_worker import director as d
    spec = d.ProductionSpec.from_dict({"script": "Ofcom and the DMCC Act protect you. Ofcom matters.",
                                       "pronounce": {"Ofcom": "Off-com", "DMCC": "D M C C"}})
    assert d.spoken_text(spec.script, spec.pronounce) == "Off-com and the D M C C Act protect you. Off-com matters."
    assert "Ofcom" in spec.script
