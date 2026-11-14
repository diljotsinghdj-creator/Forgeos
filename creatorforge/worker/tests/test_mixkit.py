"""Mixkit is checked one chosen page at a time; Restricted-licence clips are refused (no monetised YouTube)."""
import httpx

from creatorforge_worker.providers import mixkit


class R:
    status_code = 200

    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_free_licence_is_allowed(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: R('<title>Waterfall in forest - Free Stock Video</title> data-license="videoFree"'))
    c = mixkit.check("https://mixkit.co/free-stock-video/waterfall-in-forest-2213/")
    assert c["allowed"] and c["url"].endswith("/2213/2213-1080.mp4") and c["about"] == "Waterfall in forest"


def test_restricted_licence_is_refused(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: R('<title>Brain - Free Stock Video</title> data-license="videoRestricted"'))
    c = mixkit.check("https://mixkit.co/free-stock-video/scientist-looks-at-3d-brain-model-on-computer-screen-5665/")
    assert not c["allowed"] and "monetised" in c["reason"] and "url" not in c


def test_other_links_are_refused_without_a_request(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no request")))
    assert not mixkit.check("https://mixkit.co/free-stock-video/")["allowed"]
    assert not mixkit.check("https://example.com/free-stock-video/x-1/")["allowed"]
