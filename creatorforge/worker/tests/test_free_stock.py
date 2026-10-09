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
    from PIL import Image
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
    Image.new("RGB", (540, 960), (90, 40, 40)).save(still)
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
