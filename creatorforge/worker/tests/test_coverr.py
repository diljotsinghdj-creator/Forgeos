"""Coverr clips are checked one page at a time; Premium and AI-generated clips are refused."""
import httpx

from creatorforge_worker.providers import coverr


class R:
    status_code = 200

    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def page(premium, ai):
    other = '"title":"Other","urls":{"mp4":"https://cdn.coverr.co/videos/o/1080p.mp4"},"isPremium":false,"isAiGenerated":false,"slug":"other-1"'
    me = (f'"title":"Cycling through the city","maxWidth":1920,"maxHeight":1080,"urls":{{"mp4":"https://cdn.coverr.co/videos/c/1080p.mp4"}},'
          f'"isPremium":{premium},"fps":25,"isAiGenerated":{ai},"slug":"cycling-1","contributor":{{"name":"Jane Doe"}}')
    return R(other + "," + me)


def test_free_stock_clip_is_allowed(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: page("false", "false"))
    c = coverr.check("https://coverr.co/videos/cycling-1")
    assert c["allowed"] and c["url"].endswith("/c/1080p.mp4") and c["credit"] == "Jane Doe / Coverr"


def test_premium_and_ai_are_refused(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: page("true", "false"))
    assert "Premium" in coverr.check("https://coverr.co/videos/cycling-1")["reason"]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: page("false", "true"))
    assert "AI-generated" in coverr.check("https://coverr.co/videos/cycling-1")["reason"]


def test_search_links_are_refused():
    assert not coverr.check("https://coverr.co/s?q=city")["allowed"]
