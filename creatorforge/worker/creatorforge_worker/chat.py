"""Chat with your Director: shape a video in conversation. Each turn returns a reply plus the
current draft (idea or script and settings) that can be produced with one tap."""
from __future__ import annotations

import json
import re

from .providers.base import ProviderError
from .templates import STYLE_PRESETS, TEMPLATES

SYSTEM = f"""You are the AI Director of CreatorForge, a studio for faceless YouTube Shorts, TikTok and YouTube videos. DIRECTOR_CHAT
Talk with the creator like a sharp, friendly producer. Help them turn a rough thought into a video that will perform.
Each turn:
- Answer in 1-4 short sentences. Ask at most ONE question, only when it really matters.
- Keep a DRAFT of the video up to date. Fill in sensible defaults yourself; don't make the creator choose everything.
- If the creator asks for a script, write the full narration in draft.script (spoken words only, hook first, CTA last).
- Never invent facts presented as news. For real events, keep claims general or ask the creator for sources.
- Set ready=true once the draft is good enough to produce.
Allowed templates: {", ".join(TEMPLATES)} (9:16 shorts use shorts_cinematic or reels_punchy; long YouTube uses youtube_longform).
Allowed styles: {", ".join(STYLE_PRESETS)}.
ai_video: "off" (stills with camera motion, cheapest), "hook" (AI motion on the first scene), "all" (every scene, slowest).
Return JSON only:
{{"reply":"...","ready":false,"suggestions":["up to 3 short replies the creator might tap"],
"draft":{{"title":"...","idea":"one paragraph brief","hook":"...","script":"","duration_s":45,
"template":"shorts_cinematic","style":"cinematic","ai_video":"off"}}}}"""

DEFAULT_DRAFT = {"title": "", "idea": "", "hook": "", "script": "", "duration_s": 45, "template": "shorts_cinematic",
                 "style": "cinematic", "ai_video": "off"}


def _clean_draft(d: dict, previous: dict) -> dict:
    out = dict(DEFAULT_DRAFT)
    out.update({k: v for k, v in (previous or {}).items() if k in DEFAULT_DRAFT})
    for k in DEFAULT_DRAFT:
        if k in d and d[k] not in (None, ""):
            out[k] = d[k]
    out["title"] = str(out["title"]).strip()[:100]
    out["idea"] = str(out["idea"]).strip()[:3000]
    out["hook"] = str(out["hook"]).strip()[:160]
    out["script"] = str(out["script"]).strip()[:20000]
    try:
        out["duration_s"] = max(10, min(900, int(out["duration_s"])))
    except (TypeError, ValueError):
        out["duration_s"] = 45
    if out["template"] not in TEMPLATES:
        out["template"] = "youtube_longform" if out["duration_s"] > 90 else "shorts_cinematic"
    if out["style"] not in STYLE_PRESETS:
        out["style"] = "cinematic"
    if out["ai_video"] not in ("off", "hook", "all"):
        out["ai_video"] = "off"
    return out


def chat(llm, messages: list[dict], draft: dict | None = None) -> dict:
    convo = [m for m in messages if isinstance(m, dict) and m.get("role") in ("user", "assistant") and str(m.get("content", "")).strip()]
    if not convo or convo[-1]["role"] != "user":
        raise ValueError("send the conversation with the creator's latest message last")
    convo = convo[-20:]
    transcript = "\n".join(f"{'CREATOR' if m['role'] == 'user' else 'DIRECTOR'}: {str(m['content']).strip()[:4000]}" for m in convo)
    user = f"CURRENT DRAFT: {json.dumps(_clean_draft({}, draft or {}))}\n\nCONVERSATION:\n{transcript}\n\nReply as DIRECTOR."
    error = ""
    for _ in range(2):
        raw = llm.complete_json(SYSTEM, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. Return JSON only.")
        try:
            m = re.search(r"\{.*\}", raw, re.S)
            data = json.loads(m.group(0)) if m else None
            if not isinstance(data, dict) or not str(data.get("reply", "")).strip():
                raise ValueError("missing reply")
            new = _clean_draft(data.get("draft") if isinstance(data.get("draft"), dict) else {}, draft or {})
            ready = bool(data.get("ready")) and bool(new["idea"] or new["script"])
            return {"reply": str(data["reply"]).strip()[:2000], "ready": ready, "draft": new,
                    "suggestions": [str(s).strip()[:60] for s in data.get("suggestions") or [] if str(s).strip()][:3]}
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)
    raise ProviderError(f"the script model returned an invalid chat answer twice: {error}")


def production_body(draft: dict, base: dict | None = None) -> dict:
    d = _clean_draft(draft, {})
    body = dict(base or {})
    body.update(template=d["template"], style=d["style"], motion="stills" if d["ai_video"] == "off" else "ai_video",
                ai_video_scenes="all" if d["ai_video"] == "all" else "hook")
    if d["script"]:
        body.update(script=d["script"], idea=d["title"] or "")
    else:
        brief = d["idea"] or d["title"]
        body.update(idea=(f"{brief}\nHook: {d['hook']}" if d["hook"] else brief), duration_s=d["duration_s"], script="")
    return body
