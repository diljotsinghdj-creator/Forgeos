"""Trend sources. Each one turns a public, documented feed into a list of Signals.

All of them are free. Only YouTube needs a (free) API key. A source that fails or is not
configured is reported in the radar's source status and the other sources still count."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable
from urllib.parse import quote

import httpx

from .niches import REGIONS, Niche

USER_AGENT = "CreatorForge-TrendRadar/1.0 (self-hosted; +https://github.com/diljotsinghdj-creator/Forgeos)"
DAYS = {"week": 7, "month": 30, "year": 365}


@dataclass
class Signal:
    source: str  # "wikipedia" | "google_trends" | "news" | "reddit" | "hackernews" | "youtube"
    title: str
    url: str = ""
    metric: int = 0  # views, upvotes, points or searches; 0 when the feed has no number
    metric_label: str = ""
    publisher: str = ""
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class SourceError(Exception):
    pass


Fetch = Callable[[str], tuple[int, str]]


def http_fetch(url: str) -> tuple[int, str]:
    try:
        r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, timeout=15, follow_redirects=True)
    except httpx.HTTPError as e:
        raise SourceError(f"unreachable: {e}") from e
    return r.status_code, r.text


def _get_json(fetch: Fetch, url: str):
    status, text = fetch(url)
    if status >= 400:
        raise SourceError(f"HTTP {status}")
    try:
        import json
        return json.loads(text)
    except ValueError as e:
        raise SourceError("unexpected response (not JSON)") from e


def _get_xml(fetch: Fetch, url: str) -> ET.Element:
    status, text = fetch(url)
    if status >= 400:
        raise SourceError(f"HTTP {status}")
    try:
        return ET.fromstring(text)
    except ET.ParseError as e:
        raise SourceError("unexpected response (not RSS)") from e


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(el: ET.Element, name: str) -> ET.Element | None:
    return next((c for c in el if _local(c.tag) == name), None)


def _text(el: ET.Element | None) -> str:
    return html.unescape((el.text or "").strip()) if el is not None else ""


def _count(s: str) -> int:
    digits = re.sub(r"[^\d]", "", s or "")
    return int(digits) if digits else 0


# ---- Wikipedia most-read --------------------------------------------------------------------

_WIKI_SKIP = re.compile(r"^(Main_Page|Special:|Wikipedia:|File:|Portal:|Help:|Category:|Template:|Talk:|User:|"
                        r"Search|-$|XXX|Cleopatra$|Bible$|Pornhub|XHamster|Xvideos)", re.I)


def wikipedia(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date) -> list[Signal]:
    project = REGIONS.get(region, REGIONS["GB"])["wiki"]
    base = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{project}/all-access"
    urls: list[str] = []
    if period == "week":
        urls = [f"{base}/{d:%Y/%m/%d}" for d in (today - timedelta(days=2 + i) for i in range(7))]
    else:
        first = today.replace(day=1)
        months = 1 if period == "month" else 12
        for _ in range(months):
            first = (first - timedelta(days=1)).replace(day=1)
            urls.append(f"{base}/{first:%Y/%m}/all-days")
    views: dict[str, int] = {}
    errors = 0
    for url in urls:
        try:
            data = _get_json(fetch, url)
        except SourceError:
            errors += 1
            continue
        for item in data.get("items") or []:
            for a in item.get("articles") or []:
                name = str(a.get("article", ""))
                if name and not _WIKI_SKIP.search(name):
                    views[name] = views.get(name, 0) + int(a.get("views") or 0)
    if errors == len(urls):
        raise SourceError("Wikipedia pageviews unavailable")
    top = sorted(views.items(), key=lambda kv: -kv[1])[:60]
    return [Signal("wikipedia", n.replace("_", " "), f"https://en.wikipedia.org/wiki/{quote(n)}", v, "page views")
            for n, v in top]


# ---- Google Trends (what people search right now) -----------------------------------------

def google_trends(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date) -> list[Signal]:
    if period != "week":
        return []  # the public feed only covers the last few days
    root = _get_xml(fetch, f"https://trends.google.com/trending/rss?geo={region}")
    out = []
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        title = _text(_child(item, "title"))
        if not title:
            continue
        news = [c for c in item if _local(c.tag) == "news_item"]
        snippet = _text(_child(news[0], "news_item_title")) if news else ""
        link = _text(_child(news[0], "news_item_url")) if news else ""
        out.append(Signal("google_trends", title, link, _count(_text(_child(item, "approx_traffic"))), "searches",
                          _text(_child(news[0], "news_item_source")) if news else "", snippet))
    return out


# ---- Google News headlines ----------------------------------------------------------------

def news(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date) -> list[Signal]:
    r = REGIONS.get(region, REGIONS["GB"])
    q = query or niche.news_query
    tail = f"hl={r['hl']}&gl={region}&ceid={r['ceid']}"
    if q:
        url = f"https://news.google.com/rss/search?q={quote(f'{q} when:{DAYS[period]}d')}&{tail}"
    elif period == "week":
        url = f"https://news.google.com/rss?{tail}"
    else:
        return []  # top stories are only "now"; month/year need a topic
    root = _get_xml(fetch, url)
    out = []
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        title = _text(_child(item, "title"))
        publisher = _text(_child(item, "source"))
        if publisher and title.endswith(f" - {publisher}"):
            title = title[: -len(publisher) - 3]
        if title:
            out.append(Signal("news", title, _text(_child(item, "link")), 0, "", publisher))
    return out[:60]


# ---- Reddit ---------------------------------------------------------------------------------

def reddit(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date) -> list[Signal]:
    if query:
        url = f"https://www.reddit.com/search.json?q={quote(query)}&sort=top&t={period}&limit=50"
    elif niche.subreddits:
        url = f"https://www.reddit.com/r/{'+'.join(niche.subreddits)}/top.json?t={period}&limit=60"
    else:
        return []
    data = _get_json(fetch, url)
    out = []
    for child in (data.get("data") or {}).get("children") or []:
        d = child.get("data") or {}
        if d.get("stickied") or d.get("over_18"):
            continue
        title = html.unescape(str(d.get("title", "")).strip())
        title = re.sub(r"^(TIL|TIL that|TIL:)\s+", "", title, flags=re.I)
        if title:
            out.append(Signal("reddit", title, f"https://www.reddit.com{d.get('permalink', '')}", int(d.get("score") or 0),
                              "upvotes", f"r/{d.get('subreddit', '')}", str(d.get("selftext", ""))[:280]))
    return out


# ---- Hacker News ----------------------------------------------------------------------------

def hackernews(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date) -> list[Signal]:
    q = query if query else niche.hn_query
    if q is None:
        return []
    since = int((datetime.combine(today, datetime.min.time(), timezone.utc) - timedelta(days=DAYS[period])).timestamp())
    data = _get_json(fetch, f"https://hn.algolia.com/api/v1/search?query={quote(q)}&tags=story"
                            f"&numericFilters=created_at_i>{since},points>30&hitsPerPage=60")
    hits = sorted(data.get("hits") or [], key=lambda h: -int(h.get("points") or 0))
    return [Signal("hackernews", str(h.get("title", "")).strip(),
                   h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                   int(h.get("points") or 0), "points", "Hacker News") for h in hits if h.get("title")][:40]


# ---- YouTube (optional free API key) -----------------------------------------------------------

def youtube(fetch: Fetch, period: str, niche: Niche, region: str, query: str, today: date, key: str = "") -> list[Signal]:
    if not key:
        raise SourceError("add a free YouTube Data API key (CF_YOUTUBE_API_KEY) to include YouTube")
    api = "https://www.googleapis.com/youtube/v3"
    q = query or niche.youtube_query
    if period == "week" and not query:
        url = f"{api}/videos?part=snippet,statistics&chart=mostPopular&regionCode={region}&maxResults=50&key={key}"
        if niche.youtube_category:
            url += f"&videoCategoryId={niche.youtube_category}"
        items = _get_json(fetch, url).get("items") or []
    else:
        if not q:
            return []
        after = (datetime.combine(today, datetime.min.time(), timezone.utc) - timedelta(days=DAYS[period]))
        found = _get_json(fetch, f"{api}/search?part=snippet&type=video&order=viewCount&maxResults=25&regionCode={region}"
                                 f"&publishedAfter={after:%Y-%m-%dT%H:%M:%SZ}&q={quote(q)}&key={key}").get("items") or []
        ids = ",".join(i["id"]["videoId"] for i in found if isinstance(i.get("id"), dict) and i["id"].get("videoId"))
        items = _get_json(fetch, f"{api}/videos?part=snippet,statistics&id={ids}&key={key}").get("items") or [] if ids else []
    out = []
    for it in items:
        sn = it.get("snippet") or {}
        title = html.unescape(str(sn.get("title", "")).strip())
        if title:
            out.append(Signal("youtube", title, f"https://www.youtube.com/watch?v={it.get('id')}",
                              int((it.get("statistics") or {}).get("viewCount") or 0), "views",
                              str(sn.get("channelTitle", "")), str(sn.get("description", ""))[:280]))
    return sorted(out, key=lambda s: -s.metric)


SOURCES = {
    "wikipedia": wikipedia,
    "google_trends": google_trends,
    "news": news,
    "reddit": reddit,
    "hackernews": hackernews,
    "youtube": youtube,
}
# How much one place in each list counts. Search and watch data beat headlines.
WEIGHTS = {"google_trends": 1.2, "youtube": 1.2, "wikipedia": 1.0, "reddit": 0.9, "news": 0.8, "hackernews": 0.7}
LABELS = {"wikipedia": "Wikipedia", "google_trends": "Google Trends", "news": "News", "reddit": "Reddit",
          "hackernews": "Hacker News", "youtube": "YouTube"}
