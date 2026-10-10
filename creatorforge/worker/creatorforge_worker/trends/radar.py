"""Collects signals from every source, groups them into topics and ranks the topics."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from .niches import NICHES, REGIONS, Niche
from .sources import LABELS, SOURCES, WEIGHTS, Fetch, Signal, SourceError, http_fetch

PERIODS = ("week", "month", "year")
CACHE_TTL = {"week": 2 * 3600, "month": 12 * 3600, "year": 48 * 3600}
ENTITY_SOURCES = ("google_trends", "wikipedia")  # short names of people, events and things: they anchor topics

_STOP = set("""a an the and or but of to in on at for from by with without into over under about after before
is are was were be been being has have had do does did will would can could should may might must this that these
those it its it's i you he she they we them his her their our your my me us not no yes so as if than then there here
what which who whom whose when where why how all any each more most other some such only own same too very just
new says say said vs via amid how why what over up out off one two three first last year years week weeks month months
day days today now 2024 2025 2026 2027 get got make makes made video watch people man woman""".split())


def tokens(title: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", title.lower().replace("'s", ""))
    out = set()
    for w in words:
        if w in _STOP or (len(w) < 3 and w not in ("ai", "uk", "us", "f1")):
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


class _Cluster:
    def __init__(self, anchor: Signal, score: float):
        self.anchor = anchor
        self.key = tokens(anchor.title)
        self.signals: list[tuple[Signal, float]] = [(anchor, score)]

    def matches(self, sig: Signal, toks: set[str]) -> bool:
        if not self.key or not toks:
            return False
        common = self.key & toks
        if (len(self.key) == 1 and self.anchor.source in ENTITY_SOURCES) or (len(toks) == 1 and sig.source in ENTITY_SOURCES):
            # A one-word entity ("Oasis") matches a headline that names it, if the word is distinctive enough.
            return any(len(w) >= 4 for w in common)
        return len(common) >= 2 and len(common) / min(len(self.key), len(toks)) >= 0.6

    def score(self) -> float:
        best: dict[str, float] = {}
        for s, v in self.signals:
            best[s.source] = max(best.get(s.source, 0.0), v)
        # Extra mentions in the same source add a little; agreement across sources adds a lot.
        extra = sum(v for s, v in self.signals) - sum(best.values())
        return sum(best.values()) + 0.15 * extra

    def to_dict(self, max_score: float, period: str) -> dict:
        ordered = sorted(self.signals, key=lambda sv: -sv[1])
        sources = sorted({s.source for s, _ in self.signals}, key=lambda k: -WEIGHTS.get(k, 0))
        metrics: dict[str, int] = {}
        for s, _ in self.signals:
            if s.metric and s.metric_label:
                metrics[s.metric_label] = metrics.get(s.metric_label, 0) + s.metric
        title = self.anchor.title.strip()
        headlines = []
        for s, _ in ordered:
            if s.title != title and s.title not in headlines:
                headlines.append(s.title)
        score = self.score()
        return {
            "id": hashlib.sha1(title.lower().encode()).hexdigest()[:12],
            "title": title,
            "heat": round(100 * score / max_score) if max_score else 0,
            "score": round(score, 3),
            "sources": [LABELS[k] for k in sources],
            "metrics": metrics,
            "headlines": headlines[:6],
            "signals": [s.to_dict() for s, _ in ordered[:10]],
            "evergreen": period == "year",
        }


class TrendRadar:
    def __init__(self, data_dir: Path, youtube_key: str = "", fetch: Fetch | None = None,
                 today: Callable[[], date] | None = None):
        self.dir = data_dir / "trends"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.youtube_key = youtube_key
        self.fetch = fetch or http_fetch
        self.today = today or (lambda: datetime.now(timezone.utc).date())
        self._lock = threading.Lock()

    # ---- public --------------------------------------------------------------------------
    def scan(self, period: str = "week", niche: str = "all", region: str = "GB", query: str = "",
             refresh: bool = False, limit: int = 30) -> dict:
        if period not in PERIODS:
            raise ValueError("period must be week, month or year")
        if niche not in NICHES:
            raise ValueError(f"unknown niche '{niche}'")
        region = region.upper()
        if region not in REGIONS:
            raise ValueError(f"region must be one of {', '.join(REGIONS)}")
        query = re.sub(r"\s+", " ", query).strip()[:80]
        if niche == "custom" and len(query) < 2:
            raise ValueError("type a keyword for 'My keyword'")
        if niche != "custom":
            query = ""
        path = self._cache_path(period, niche, region, query)
        if not refresh and path.exists():
            try:
                cached = json.loads(path.read_text())
                if time.time() - cached["fetched_ts"] < CACHE_TTL[period]:
                    cached["cached"] = True
                    cached["items"] = cached["items"][:limit]
                    return cached
            except (ValueError, KeyError):
                pass
        result = self._collect(period, NICHES[niche], region, query)
        result["items"] = result["items"][:60]
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(result))
        tmp.replace(path)
        result = dict(result, cached=False)
        result["items"] = result["items"][:limit]
        return result

    def find(self, trend_id: str) -> dict | None:
        """Looks a topic up in recent scans (newest first)."""
        for path in sorted(self.dir.glob("*.json"), key=lambda p: -p.stat().st_mtime):
            try:
                for item in json.loads(path.read_text()).get("items", []):
                    if item.get("id") == trend_id:
                        return item
            except ValueError:
                continue
        return None

    # ---- internals -----------------------------------------------------------------------
    def _cache_path(self, period: str, niche: str, region: str, query: str) -> Path:
        q = hashlib.sha1(query.lower().encode()).hexdigest()[:8] if query else "all"
        return self.dir / f"{period}_{niche}_{region}_{q}.json"

    def _run(self, name: str, period: str, niche: Niche, region: str, query: str) -> list[Signal]:
        fn = SOURCES[name]
        today = self.today()
        if name == "youtube":
            return fn(self.fetch, period, niche, region, query, today, key=self.youtube_key)
        if name in ENTITY_SOURCES and query:
            return fn(self.fetch, period, NICHES["all"], region, "", today)
        return fn(self.fetch, period, niche, region, query, today)

    def _wanted(self, niche: Niche, query: str) -> list[str]:
        names = ["news", "reddit", "hackernews", "youtube"]
        if niche.id == "all" or niche.keywords or query:
            names.insert(0, "google_trends")
        if niche.wikipedia or query:
            names.insert(0, "wikipedia")
        return names

    def _collect(self, period: str, niche: Niche, region: str, query: str) -> dict:
        names = self._wanted(niche, query)
        status: dict[str, dict] = {}
        lists: dict[str, list[Signal]] = {}
        with ThreadPoolExecutor(max_workers=len(names)) as pool:
            futures = {n: pool.submit(self._run, n, period, niche, region, query) for n in names}
            for n, fut in futures.items():
                try:
                    sigs = fut.result()
                except SourceError as e:
                    status[n] = {"name": LABELS[n], "ok": False, "count": 0, "error": str(e)}
                    continue
                except Exception as e:  # a broken feed must never take the radar down
                    status[n] = {"name": LABELS[n], "ok": False, "count": 0, "error": f"failed: {type(e).__name__}"}
                    continue
                sigs = self._filter(n, sigs, niche, query)
                lists[n] = sigs
                status[n] = {"name": LABELS[n], "ok": True, "count": len(sigs), "error": ""}
        if not any(lists.values()):
            errors = "; ".join(f"{s['name']}: {s['error'] or 'nothing found'}" for s in status.values())
            raise SourceError(f"no trend source returned anything ({errors})")
        clusters = self._cluster(lists)
        top = max((c.score() for c in clusters), default=0.0)
        items = [c.to_dict(top, period) for c in sorted(clusters, key=lambda c: -c.score())]
        return {"period": period, "niche": niche.id, "region": region, "query": query,
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fetched_ts": time.time(),
                "sources": status, "items": items}

    @staticmethod
    def _filter(name: str, sigs: list[Signal], niche: Niche, query: str) -> list[Signal]:
        if name not in ENTITY_SOURCES:
            return sigs
        words = tokens(query) if query else set(niche.keywords) if niche.keywords else set()
        if not words:
            return sigs

        def hit(s: Signal) -> bool:
            text = f"{s.title} {s.snippet}".lower()
            return any(re.search(rf"\b{re.escape(w)}", text) for w in words)
        return [s for s in sigs if hit(s)]

    @staticmethod
    def _cluster(lists: dict[str, list[Signal]]) -> list[_Cluster]:
        scored: list[tuple[Signal, float]] = []
        for name, sigs in lists.items():
            n = max(len(sigs), 1)
            for rank, s in enumerate(sigs):
                scored.append((s, WEIGHTS.get(name, 0.5) * (1 - 0.8 * rank / n)))
        # Entities first, so headlines attach to the person or event they are about.
        scored.sort(key=lambda sv: (sv[0].source not in ENTITY_SOURCES, -sv[1]))
        clusters: list[_Cluster] = []
        for s, v in scored:
            toks = tokens(s.title)
            home = next((c for c in clusters if c.matches(s, toks)), None)
            if home:
                home.signals.append((s, v))
            elif toks:
                clusters.append(_Cluster(s, v))
        return clusters
