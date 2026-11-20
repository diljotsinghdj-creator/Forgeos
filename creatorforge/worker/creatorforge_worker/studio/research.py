"""Research: from a topic to an evidence dossier.

1. A search provider finds sources for a set of research questions (the questions come from the language model:
   central issue, people and institutions, background, timeline, primary records, official statistics, reporting,
   conflicting accounts, misinformation, implications, unknowns).
2. The language model reads the results and proposes claims, each tied to the result it came from, with that
   result's own words.
3. The studio - not the model - decides each claim's status: two or more independent hosts agree -> verified;
   one -> reported; the model's "estimate" / "disputed" / "allegation" / "opinion" labels are kept. A claim whose
   quotation is not found in its source's text is dropped. Nothing without a URL survives.

Search providers (the key is set in the pod's environment, never in a script): Brave Search (CF_BRAVE_KEY),
Tavily (CF_TAVILY_KEY). Without one, research() raises and a dossier must be supplied by hand.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date

from .dossier import Dossier

QUESTIONS_PROMPT = """List 10-14 web search queries that would research this documentary topic thoroughly: the central
issue, the people and institutions, the background, the timeline, primary records (government, parliament, court,
official statistics), academic work, credible reporting, conflicting accounts, misleading claims, the financial /
political / social implications, and what is unknown. Return JSON: {"queries": ["...", ...]}.
TOPIC: """

CLAIMS_PROMPT = """From these search results, extract the factual claims a documentary on the topic could use. Rules:
- Each claim must come from one or more of the results, and "quote" must be copied from that result's text.
- "figures": the exact numbers / years the claim supports, as written.
- "label": fact | estimate | disputed | allegation | opinion | interpretation.
- Note contradictions between results.
Return JSON: {"claims": [{"claim": "...", "label": "...", "figures": [...], "sources": [{"n": <result number>,
"quote": "..."}], "contradictions": ["..."]}]}
TOPIC: {topic}
RESULTS:
{results}"""


class SearchProvider:
    def search(self, query: str, count: int = 6) -> list[dict]:   # [{"title", "url", "snippet", "date"}]
        raise NotImplementedError


class BraveSearch(SearchProvider):
    def __init__(self, key: str):
        self.key = key

    def search(self, query, count=6):
        url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": query, "count": count})
        req = urllib.request.Request(url, headers={"X-Subscription-Token": self.key, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
        return [{"title": x.get("title", ""), "url": x.get("url", ""), "snippet": re.sub(r"<[^>]+>", "", x.get("description", "")),
                 "date": x.get("page_age", "")[:10]} for x in d.get("web", {}).get("results", [])]


class TavilySearch(SearchProvider):
    def __init__(self, key: str):
        self.key = key

    def search(self, query, count=6):
        body = json.dumps({"api_key": self.key, "query": query, "max_results": count, "include_raw_content": False}).encode()
        req = urllib.request.Request("https://api.tavily.com/search", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read())
        return [{"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("content", ""),
                 "date": (x.get("published_date") or "")[:10]} for x in d.get("results", [])]


def provider() -> SearchProvider | None:
    if os.environ.get("CF_BRAVE_KEY"):
        return BraveSearch(os.environ["CF_BRAVE_KEY"])
    if os.environ.get("CF_TAVILY_KEY"):
        return TavilySearch(os.environ["CF_TAVILY_KEY"])
    return None


def _host(u: str) -> str:
    return urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w%.,\s]", " ", s.lower())).strip()


def research(topic: str, llm, search: SearchProvider | None = None, per_query: int = 6) -> Dossier:
    search = search or provider()
    if search is None:
        raise RuntimeError("no search provider: set CF_BRAVE_KEY or CF_TAVILY_KEY on the worker, or supply a dossier")
    qs = json.loads(llm.complete_json("You plan documentary research.", QUESTIONS_PROMPT + topic)).get("queries", [])[:14]
    results, seen = [], set()
    for q in qs:
        for r in search.search(q, per_query):
            if r.get("url") and r["url"] not in seen:
                seen.add(r["url"])
                results.append(r)
    listing = "\n".join(f"[{i}] {r['title']} ({r['url']}) {r.get('date', '')}\n{r['snippet']}" for i, r in enumerate(results))
    raw = json.loads(llm.complete_json("You extract sourced claims as strict JSON.",
                                       CLAIMS_PROMPT.replace("{topic}", topic).replace("{results}", listing[:90000])))
    claims = []
    for k, c in enumerate(raw.get("claims", [])):
        srcs = []
        for s in c.get("sources", []):
            n = s.get("n")
            if not isinstance(n, int) or not 0 <= n < len(results):
                continue
            r = results[n]
            quote = str(s.get("quote", "")).strip()
            if not quote or _norm(quote)[:60] not in _norm(r["snippet"]):
                continue                    # the words are not in the source: the claim does not stand on it
            srcs.append({"title": r["title"], "url": r["url"], "date": r.get("date", ""), "quote": quote})
        if not srcs:
            continue
        hosts = {_host(s["url"]) for s in srcs}
        label = str(c.get("label", "fact")).lower()
        status = {"estimate": "estimate", "disputed": "disputed", "allegation": "allegation", "opinion": "opinion",
                  "interpretation": "interpretation"}.get(label, "verified" if len(hosts) >= 2 else "reported")
        if status == "disputed" and not c.get("contradictions"):
            status = "reported"
        claims.append({"id": f"C{k + 1:02d}", "claim": str(c.get("claim", ""))[:400], "status": status,
                       "confidence": "high" if len(hosts) >= 3 else "medium" if len(hosts) == 2 else "low",
                       "figures": [str(x) for x in c.get("figures", [])][:8], "sources": srcs,
                       "contradictions": [str(x) for x in c.get("contradictions", [])][:4]})
    return Dossier.from_dict({"topic": topic, "researched": date.today().isoformat(), "claims": claims,
                              "method": f"{len(qs)} searches, {len(results)} results read by the model; a claim stands "
                                        "only on results whose own text contains its quotation; status from the number "
                                        "of independent sources."})
