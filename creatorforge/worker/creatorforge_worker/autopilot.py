"""Channel Autopilot: each channel has a niche, a voice, a look and a posting rhythm. Autopilot turns
this week's trends in that niche into a dated content plan; you approve, skip or edit each slot, and
approved slots become productions (automatically the day before they're due, if you switch that on)."""
from __future__ import annotations

import json
import math
import os
import threading
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .templates import STYLE_PRESETS
from .trends import NICHES, REGIONS
from .trends import writer as trend_writer
from .trends.sources import SourceError

FORMATS = ("shorts", "long", "mixed")


def _clean(d: dict, old: dict | None = None) -> dict:
    c = dict(old or {})
    for k in ("name", "niche", "keyword", "region", "format", "per_week", "style", "voice", "ai_video", "tone",
              "audience", "post_time", "auto_produce"):
        if k in d:
            c[k] = d[k]
    c["name"] = str(c.get("name", "")).strip()[:60]
    if len(c["name"]) < 2:
        raise ValueError("give the channel a name")
    c["niche"] = str(c.get("niche") or "all")
    if c["niche"] not in NICHES:
        raise ValueError(f"unknown niche '{c['niche']}'")
    c["keyword"] = str(c.get("keyword", "")).strip()[:80]
    if c["niche"] == "custom" and len(c["keyword"]) < 2:
        raise ValueError("a 'My keyword' channel needs a keyword")
    c["region"] = str(c.get("region") or "GB").upper()
    if c["region"] not in REGIONS:
        raise ValueError(f"region must be one of {', '.join(REGIONS)}")
    c["format"] = str(c.get("format") or "shorts")
    if c["format"] not in FORMATS:
        raise ValueError("format must be shorts, long or mixed")
    try:
        c["per_week"] = max(1, min(21, int(c.get("per_week") or 7)))
    except (TypeError, ValueError):
        raise ValueError("per_week must be a number from 1 to 21") from None
    c["style"] = str(c.get("style") or "cinematic")
    if c["style"] not in STYLE_PRESETS and len(c["style"]) > 300:
        raise ValueError("style is too long")
    c["voice"] = str(c.get("voice") or "")
    c["ai_video"] = str(c.get("ai_video") or "off")
    if c["ai_video"] not in ("off", "hook", "all"):
        raise ValueError("ai_video must be off, hook or all")
    c["tone"] = str(c.get("tone", "")).strip()[:200]
    c["audience"] = str(c.get("audience", "")).strip()[:200]
    c["post_time"] = str(c.get("post_time") or "18:00")[:5]
    c["auto_produce"] = bool(c.get("auto_produce", False))
    return c


class ChannelStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _read(self) -> list[dict]:
        return json.loads(self.path.read_text()) if self.path.is_file() else []

    def _write(self, items: list[dict]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=1))
        os.replace(tmp, self.path)

    def list(self) -> list[dict]:
        with self._lock:
            return self._read()

    def get(self, cid: str) -> dict:
        for c in self.list():
            if c["id"] == cid:
                return c
        raise KeyError(cid)

    def create(self, d: dict) -> dict:
        c = _clean(d)
        with self._lock:
            items = self._read()
            if any(o["name"].lower() == c["name"].lower() for o in items):
                raise ValueError(f"a channel named '{c['name']}' already exists")
            c.update(id=uuid.uuid4().hex[:12], created_at=time.time(), plan=None)
            items.append(c)
            self._write(items)
            return c

    def update(self, cid: str, d: dict) -> dict:
        with self._lock:
            items = self._read()
            for i, c in enumerate(items):
                if c["id"] == cid:
                    items[i] = _clean(d, c)
                    self._write(items)
                    return items[i]
        raise KeyError(cid)

    def save(self, channel: dict) -> dict:
        with self._lock:
            items = self._read()
            for i, c in enumerate(items):
                if c["id"] == channel["id"]:
                    items[i] = channel
                    self._write(items)
                    return channel
        raise KeyError(channel["id"])

    def delete(self, cid: str) -> None:
        with self._lock:
            items = self._read()
            kept = [c for c in items if c["id"] != cid]
            if len(kept) == len(items):
                raise KeyError(cid)
            self._write(kept)


def _formats(channel: dict, n: int) -> list[str]:
    if channel["format"] == "shorts":
        return ["short"] * n
    if channel["format"] == "long":
        return ["long"] * n
    # mixed: one long video for every three shorts
    return ["long" if i % 4 == 3 else "short" for i in range(n)]


def make_plan(llm, radar, channel: dict, today: date | None = None) -> dict:
    """Builds next week's dated plan for a channel from this week's trends in its niche."""
    today = today or datetime.now(timezone.utc).date()
    n = channel["per_week"]
    niche = NICHES[channel["niche"]]
    note = "; ".join(x for x in [niche.name, f"tone: {channel['tone']}" if channel["tone"] else "",
                                 f"audience: {channel['audience']}" if channel["audience"] else ""] if x)
    try:
        scan = radar.scan("week", channel["niche"], channel["region"], channel["keyword"])
        trends = scan["items"]
        if len(trends) < 3:  # quiet week: add evergreen topics from this year
            trends += radar.scan("year", channel["niche"], channel["region"], channel["keyword"])["items"]
    except SourceError:
        trends = []
    if not trends:
        topic = channel["keyword"] or niche.name
        trends = [{"id": "", "title": f"Evergreen {topic}", "headlines": [], "signals": []}]
    formats = _formats(channel, n)
    per_trend = 2 if n > 3 else 1
    slots: list[dict] = []
    t = 0
    while len(slots) < n and t < len(trends) + 3:
        trend = trends[t % len(trends)]
        need = min(per_trend, n - len(slots))
        fmt_needed = formats[len(slots):len(slots) + need]
        fmt = fmt_needed[0] if len(set(fmt_needed)) == 1 else "mixed"
        for idea in trend_writer.ideas(llm, trend, need, fmt, note, "week"):
            if len(slots) >= n:
                break
            want = formats[len(slots)]
            if idea["format"] != want:
                idea = dict(idea, format=want, seconds=45 if want == "short" else 600)
            slots.append({"trend_id": trend.get("id", ""), "trend_title": trend["title"], "idea": idea,
                          "trend": {"title": trend["title"], "headlines": trend.get("headlines", [])[:6],
                                    "signals": trend.get("signals", [])[:8]}})
        t += 1
    start = today + timedelta(days=1)
    items = []
    for i, s in enumerate(slots):
        day = start + timedelta(days=math.floor(i * 7 / max(len(slots), 1)))
        items.append(dict(s, id=uuid.uuid4().hex[:10], day=day.isoformat(), time=channel["post_time"],
                          status="planned", production_id=None))
    return {"created_at": time.time(), "week_start": start.isoformat(), "items": items}


def production_body(channel: dict, item: dict) -> dict:
    base = {"style": channel["style"], "voice": channel["voice"],
            "motion": "stills" if channel["ai_video"] == "off" else "ai_video",
            "ai_video_scenes": "all" if channel["ai_video"] == "all" else "hook"}
    body = trend_writer.production_spec(item.get("trend") or {"title": item["trend_title"]}, item["idea"], base)
    body["title"] = item["idea"]["title"]
    return body


def due_items(channel: dict, today: date) -> list[dict]:
    """Approved slots due tomorrow or earlier that have not been produced yet."""
    plan = channel.get("plan") or {}
    limit = (today + timedelta(days=1)).isoformat()
    return [i for i in plan.get("items", []) if i["status"] == "approved" and i["day"] <= limit and not i.get("production_id")]
