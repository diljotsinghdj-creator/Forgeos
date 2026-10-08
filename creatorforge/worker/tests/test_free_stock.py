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
    assert providers.stock_sources("nojob", cfg) == [("nasa", ""), ("wikimedia", "")]
