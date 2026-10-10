"""Turns a trending topic into video ideas and a script that only uses facts from the sources."""
from __future__ import annotations

import json
import re

from ..providers.base import ProviderError
from ..templates import TEMPLATES, WORDS_PER_SECOND

IDEAS_SYSTEM = """You are the strategist for faceless YouTube Shorts, TikTok and long-form channels. TREND_IDEAS
Given a trending topic and the real signals behind it, propose video ideas that ride the trend.
Rules:
- Hooks are at most 12 words and make the viewer need the answer. No lies, no fake quotes.
- Every angle must be supported by the SIGNALS. Do not invent facts, numbers or events.
- For short videos (<= 60s) pick one sharp angle. For long videos pick an angle with depth (story, explainer, timeline, top-list).
- Mix formats: explainer, story, "what nobody tells you", top-N list, myth vs fact, timeline, prediction (clearly labelled opinion).
- why_now: one sentence on why this is worth posting now.
Return JSON only: {"ideas":[{"title":"...","hook":"...","angle":"...","format":"short|long","why_now":"...","seconds":45}]}"""

SCRIPT_SYSTEM = """You write narration for faceless social videos. TREND_SCRIPT
Write a voice-over script about the IDEA using ONLY facts found in the numbered SOURCES.
Rules:
- First sentence is the hook. Last sentence is a short call to action.
- Plain spoken English, short sentences, no stage directions, no emojis, no headings, no scene labels.
- If a detail is not in the SOURCES, do not state it as fact. You may give clearly labelled opinion ("I think", "it might").
- Never invent quotes, statistics, dates or names.
- Hit the target word count.
Return JSON only: {"title":"...","script":"...","description":"one-paragraph video description",
"hashtags":["#..."],"facts_used":[1,2]}"""


def _extract(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise ValueError("no JSON object in the answer")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("answer is not a JSON object")
    return data


def _signals_block(trend: dict) -> str:
    lines = []
    for i, s in enumerate(trend.get("signals") or [], 1):
        metric = f" {s['metric']:,} {s['metric_label']}" if s.get("metric") and s.get("metric_label") else ""
        where = s.get("publisher") or s.get("source", "")
        snippet = f" — {s['snippet'][:240]}" if s.get("snippet") else ""
        lines.append(f"{i}. [{where}{metric}] {s.get('title', '')}{snippet}")
    if not lines:
        lines = [f"{i}. {h}" for i, h in enumerate(trend.get("headlines") or [trend.get("title", "")], 1)]
    return "\n".join(lines)


def _ask(llm, system: str, user: str, check) -> dict:
    error = ""
    for _ in range(2):
        raw = llm.complete_json(system, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. "
                                                               "Return corrected JSON only.")
        try:
            return check(_extract(raw))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            error = str(e)
    raise ProviderError(f"the script model returned invalid output twice: {error}")


def ideas(llm, trend: dict, count: int = 5, fmt: str = "short", niche: str = "", period: str = "week") -> list[dict]:
    count = max(1, min(10, int(count)))
    if fmt not in ("short", "long", "mixed"):
        raise ValueError("format must be short, long or mixed")
    user = (f"TOPIC: {trend.get('title', '')}\nPERIOD: trending this {period}\nNICHE: {niche or 'general'}\n"
            f"FORMAT: {fmt} ({'<= 60 seconds' if fmt == 'short' else '6-12 minutes' if fmt == 'long' else 'mix of both'})\n"
            f"COUNT: {count}\nSIGNALS:\n{_signals_block(trend)}")

    def check(d: dict) -> list[dict]:
        out = []
        for it in d.get("ideas") or []:
            if not isinstance(it, dict):
                continue
            title = str(it.get("title", "")).strip()[:120]
            hook = str(it.get("hook", "")).strip()[:140]
            if not title or not hook:
                continue
            f = str(it.get("format", "")).lower()
            f = f if f in ("short", "long") else ("long" if fmt == "long" else "short")
            try:
                secs = int(it.get("seconds") or 0)
            except (TypeError, ValueError):
                secs = 0
            secs = secs if secs else (600 if f == "long" else 45)
            secs = max(15, min(60, secs)) if f == "short" else max(120, min(900, secs))
            out.append({"title": title, "hook": hook, "angle": str(it.get("angle", "")).strip()[:400],
                        "format": f, "why_now": str(it.get("why_now", "")).strip()[:240], "seconds": secs})
        if not out:
            raise ValueError("no usable ideas (each needs a title and a hook)")
        return out[:count]
    return _ask(llm, IDEAS_SYSTEM, user, check)


def script(llm, trend: dict, idea: dict, seconds: int = 45) -> dict:
    seconds = max(15, min(900, int(seconds or idea.get("seconds") or 45)))
    words = round(seconds * WORDS_PER_SECOND)
    sigs = trend.get("signals") or []
    user = (f"IDEA: {idea.get('title', trend.get('title', ''))}\nHOOK: {idea.get('hook', '')}\n"
            f"ANGLE: {idea.get('angle', '')}\nTOPIC: {trend.get('title', '')}\n"
            f"TARGET: about {words} words ({seconds} seconds of narration)\nSOURCES:\n{_signals_block(trend)}")

    def check(d: dict) -> dict:
        text = re.sub(r"\s+", " ", str(d.get("script", ""))).strip()
        if len(text.split()) < max(15, words // 3):
            raise ValueError(f"script is too short ({len(text.split())} words, need about {words})")
        used = [int(n) for n in d.get("facts_used") or [] if str(n).isdigit() and 1 <= int(n) <= len(sigs)]
        tags = [("#" + re.sub(r"[^\w]", "", str(t))).replace("##", "#") for t in d.get("hashtags") or []]
        return {"title": str(d.get("title", "") or idea.get("title", "")).strip()[:100],
                "script": text[:20000], "description": str(d.get("description", "")).strip()[:1500],
                "hashtags": [t for t in tags if len(t) > 1][:12], "seconds": seconds,
                "sources": [{"title": sigs[n - 1]["title"], "url": sigs[n - 1].get("url", "")} for n in used],
                "verify": "Check names, dates and numbers against the linked sources before posting."}
    return _ask(llm, SCRIPT_SYSTEM, user, check)


def production_spec(trend: dict, idea: dict, base: dict) -> dict:
    """Builds a /v1/productions body for one idea. With a written script the narration is used word for word;
    otherwise the Director writes it from the idea plus the trend's real headlines."""
    spec = dict(base)
    spec.pop("script", None)
    if idea.get("script"):
        spec["script"] = str(idea["script"])
        spec["idea"] = str(idea.get("title") or trend.get("title", ""))[:200]
        return spec
    facts = "\n".join(f"- {h}" for h in ([trend.get("title", "")] + list(trend.get("headlines") or []))[:6] if h)
    spec["idea"] = (f"{idea.get('title') or trend.get('title', '')}\nHook: {idea.get('hook', '')}\n"
                    f"Angle: {idea.get('angle', '')}\nUse only these real facts from this week's sources:\n{facts}")[:3900]
    if "duration_s" not in base:
        secs = int(idea.get("seconds") or 45)
        spec["duration_s"] = max(10, min(900, secs))
    if "template" not in base:
        long = "youtube_longform" if "youtube_longform" in TEMPLATES else "shorts_cinematic"
        spec["template"] = "shorts_cinematic" if int(spec.get("duration_s", 45)) <= 60 else long
    return spec
