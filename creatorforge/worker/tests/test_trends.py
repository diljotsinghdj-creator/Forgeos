"""Trend Radar: parsing, grouping, niches, caching, ideas, scripts and one-tap production (no network)."""
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app
from creatorforge_worker.providers.mock import MockLLM
from creatorforge_worker.trends import TrendRadar, writer
from creatorforge_worker.trends.radar import tokens
from creatorforge_worker.trends.sources import SourceError

WIKI = {"items": [{"articles": [
    {"article": "Main_Page", "views": 9_000_000}, {"article": "Special:Search", "views": 800_000},
    {"article": "Comet_Atlas", "views": 400_000}, {"article": "Oasis_(band)", "views": 300_000},
    {"article": "Battle_of_Hastings", "views": 90_000}]}]}
GTRENDS = """<?xml version="1.0"?><rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0"><channel>
<item><title>oasis</title><ht:approx_traffic>500,000+</ht:approx_traffic>
<ht:news_item><ht:news_item_title>Oasis announce extra reunion dates</ht:news_item_title>
<ht:news_item_url>https://example.com/oasis</ht:news_item_url><ht:news_item_source>BBC</ht:news_item_source></ht:news_item></item>
<item><title>comet atlas</title><ht:approx_traffic>100,000+</ht:approx_traffic></item>
</channel></rss>"""
NEWS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Comet Atlas visible tonight: how to see it - The Guardian</title><link>https://news.example/1</link>
<source url="https://theguardian.com">The Guardian</source></item>
<item><title>Oasis reunion tour adds stadium dates - Sky News</title><link>https://news.example/2</link>
<source url="https://news.sky.com">Sky News</source></item>
<item><title>Interest rates held at 4% - Reuters</title><link>https://news.example/3</link><source>Reuters</source></item>
</channel></rss>"""
REDDIT = {"data": {"children": [
    {"data": {"title": "Pinned rules", "stickied": True, "score": 1, "permalink": "/r/x/1", "subreddit": "x"}},
    {"data": {"title": "TIL comet Atlas last passed 80,000 years ago", "score": 45000, "permalink": "/r/til/2",
              "subreddit": "todayilearned", "selftext": ""}},
    {"data": {"title": "Photo of my cat", "score": 900, "permalink": "/r/cats/3", "subreddit": "cats"}}]}}
HN = {"hits": [{"title": "Show HN: A tiny AI video editor", "points": 300, "objectID": "1", "url": "https://x.dev"}]}


def fake_fetch(calls=None, fail=()):
    def fetch(url: str):
        if calls is not None:
            calls.append(url)
        for key in fail:
            if key in url:
                return 503, "down"
        if "wikimedia.org" in url:
            return 200, json.dumps(WIKI)
        if "trends.google.com" in url:
            return 200, GTRENDS
        if "news.google.com" in url:
            return 200, NEWS
        if "reddit.com" in url:
            return 200, json.dumps(REDDIT)
        if "algolia" in url:
            return 200, json.dumps(HN)
        return 404, "?"
    return fetch


def radar(tmp_path, calls=None, fail=()):
    return TrendRadar(tmp_path, fetch=fake_fetch(calls, fail), today=lambda: date(2026, 10, 7))


def test_tokens_drop_noise():
    assert tokens("The Comets of 2026: what's NEW?") == {"comet"}
    assert "ai" in tokens("AI takes over")


def test_scan_groups_signals_into_topics(tmp_path):
    out = radar(tmp_path).scan("week", "all", "GB")
    titles = [i["title"] for i in out["items"]]
    assert "Main Page" not in titles and not any(t.startswith("Special") for t in titles)
    comet = next(i for i in out["items"] if "comet" in i["title"].lower())
    # Wikipedia, Google Trends, News and Reddit all talk about the comet: one topic, top of the list.
    assert {"Wikipedia", "News", "Reddit", "Google Trends"} <= set(comet["sources"])
    assert out["items"][0]["id"] == comet["id"] and comet["heat"] == 100
    oasis = next(i for i in out["items"] if "oasis" in i["title"].lower())
    assert "Oasis reunion tour adds stadium dates" in oasis["headlines"]
    assert out["sources"]["youtube"]["ok"] is False and "CF_YOUTUBE_API_KEY" in out["sources"]["youtube"]["error"]
    assert out["sources"]["reddit"]["count"] == 2  # stickied post skipped


def test_cache_and_refresh(tmp_path):
    calls = []
    r = radar(tmp_path, calls)
    first = r.scan("week")
    n = len(calls)
    second = r.scan("week")
    assert second["cached"] is True and len(calls) == n and second["items"][0]["id"] == first["items"][0]["id"]
    r.scan("week", refresh=True)
    assert len(calls) > n
    assert r.find(first["items"][0]["id"])["title"] == first["items"][0]["title"]


def test_periods_and_niches_hit_the_right_feeds(tmp_path):
    calls = []
    r = radar(tmp_path, calls)
    r.scan("year", "history")
    wiki = [u for u in calls if "wikimedia" in u]
    assert len(wiki) == 12 and all(u.endswith("/all-days") for u in wiki)
    assert any("t=year" in u and "AskHistorians" in u for u in calls)
    assert not any("trends.google.com" in u for u in calls)  # the search feed is "now" only
    assert not any("algolia" in u for u in calls)  # no Hacker News for history
    hist = r.scan("year", "history")
    assert any("Hastings" in i["title"] for i in hist["items"])
    assert not any("Oasis" in i["title"] for i in hist["items"] if "Wikipedia" in i["sources"] and len(i["sources"]) == 1)


def test_custom_keyword_and_validation(tmp_path):
    calls = []
    r = radar(tmp_path, calls)
    with pytest.raises(ValueError):
        r.scan("week", "custom", query="")
    with pytest.raises(ValueError):
        r.scan("decade")
    out = r.scan("month", "custom", query="comet")
    assert any("search.json?q=comet" in u for u in calls)
    assert all("comet" in i["title"].lower() or "comet" in " ".join(i["headlines"]).lower()
               for i in out["items"] if set(i["sources"]) <= {"Wikipedia", "Google Trends"})


def test_failing_sources_are_reported_not_fatal(tmp_path):
    out = radar(tmp_path, fail=("reddit", "wikimedia")).scan("week")
    assert out["sources"]["reddit"]["ok"] is False and out["items"]
    with pytest.raises(SourceError):
        radar(tmp_path, fail=("reddit", "wikimedia", "google.com", "algolia")).scan("week", refresh=True)


def test_ideas_and_grounded_script(tmp_path):
    trend = radar(tmp_path).scan("week")["items"][0]
    ideas = writer.ideas(MockLLM(), trend, 3, "short")
    assert len(ideas) == 3 and all(i["format"] == "short" and 15 <= i["seconds"] <= 60 for i in ideas)
    s = writer.script(MockLLM(), trend, ideas[0], 45)
    assert len(s["script"].split()) >= 40 and s["hashtags"][0] == "#trending" and "#news" in s["hashtags"]
    assert s["sources"] and s["sources"][0]["title"] == trend["signals"][0]["title"]


class BadLLM:
    def complete_json(self, system, user):
        return '{"ideas": []}'


def test_writer_fails_closed():
    from creatorforge_worker.providers.base import ProviderError
    with pytest.raises(ProviderError):
        writer.ideas(BadLLM(), {"title": "x"}, 2)


def test_production_spec_uses_real_headlines():
    trend = {"title": "Comet Atlas", "headlines": ["Comet visible tonight"]}
    spec = writer.production_spec(trend, {"title": "See the comet", "hook": "Look up", "seconds": 600}, {})
    assert spec["template"] == "youtube_longform" and spec["duration_s"] == 600 and "Comet visible tonight" in spec["idea"]
    spec = writer.production_spec(trend, {"title": "T", "script": "Exact words here please."}, {"template": "reels_punchy"})
    assert spec["script"] == "Exact words here please." and spec["template"] == "reels_punchy"


def test_api_trends_to_productions(cfg):
    app = create_app(cfg, start_runner=False)
    app.state.radar.fetch = fake_fetch()
    app.state.radar.today = lambda: date(2026, 10, 7)
    c = TestClient(app)
    opts = c.get("/v1/trends/options").json()
    assert "history" in [n["id"] for n in opts["niches"]] and opts["youtube"] is False
    assert c.get("/v1/trends?period=decade").status_code == 422
    out = c.get("/v1/trends?period=week&niche=all&limit=2").json()
    assert len(out["items"]) == 2
    tid = out["items"][0]["id"]
    ideas = c.post("/v1/trends/ideas", json={"trend_id": tid, "count": 2}).json()["ideas"]
    assert len(ideas) == 2
    script = c.post("/v1/trends/script", json={"trend_id": tid, "idea": ideas[0], "seconds": 30}).json()
    assert script["script"]
    assert c.post("/v1/trends/ideas", json={"trend_id": "nope"}).status_code == 404
    ideas[1]["script"] = script["script"]
    r = c.post("/v1/trends/produce", json={"trend_id": tid, "ideas": ideas, "production": {"template": "reels_punchy"}})
    assert r.status_code == 202
    jobs = r.json()["productions"]
    assert len(jobs) == 2 and jobs[0]["status"] == "QUEUED"
    specs = [c.get(f"/v1/productions/{j['id']}").json()["spec"] for j in jobs]
    assert specs[1]["script"] == script["script"] and not specs[0]["script"]
    assert c.post("/v1/trends/ideas", json={"topic": "Comet Atlas", "count": 1}).status_code == 200
