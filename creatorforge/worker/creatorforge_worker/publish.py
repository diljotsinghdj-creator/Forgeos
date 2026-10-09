"""Publish kit + CapCut export.

Publish kit: titles, description, hashtags, a pinned comment and thumbnail text for a finished video.
CapCut export: a zip with every scene's media in order, the voice-over, music, an SRT caption file,
the timeline, the finished MP4 and the publish kit, ready to drop into CapCut (or any editor) for polish."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

from .media.captions import group
from .providers.base import ProviderError, Word
from .templates import TEMPLATES

KIT_SYSTEM = """You package faceless social videos for YouTube Shorts, TikTok, Instagram Reels and YouTube. PUBLISH_KIT
Given the video's narration, write the posting kit. Rules: no clickbait lies, no fake claims, titles under 70 characters,
3-5 titles in different styles (curiosity, benefit, number, question), a 2-4 sentence description with a call to action,
8-15 hashtags mixing broad and niche (each starts with #), one pinned comment that sparks replies, thumbnail text of 2-5 words.
Return JSON only: {"titles":["..."],"description":"...","hashtags":["#..."],"pinned_comment":"...","thumbnail_text":"..."}"""


def _narration(job: dict) -> str:
    return " ".join(s.get("narration", "") for s in (job.get("plan") or {}).get("scenes", []))


def fallback_kit(job: dict) -> dict:
    plan = job.get("plan") or {}
    title = job.get("title") or plan.get("title") or "New video"
    words = [w for w in re.findall(r"[A-Za-z]{5,}", _narration(job).lower())]
    common = sorted(set(words), key=lambda w: -words.count(w))[:6]
    return {"titles": [title], "description": f"{plan.get('hook') or title}. {plan.get('cta') or 'Follow for more.'}",
            "hashtags": ["#shorts"] + [f"#{w}" for w in common], "pinned_comment": "What should the next video be about?",
            "thumbnail_text": " ".join(title.split()[:4]), "source": "fallback (no script model)"}


def _make_kit(llm, job: dict) -> dict:
    if llm is None:
        return fallback_kit(job)
    plan = job.get("plan") or {}
    user = (f"TITLE: {job.get('title') or plan.get('title', '')}\nHOOK: {plan.get('hook', '')}\n"
            f"FORMAT: {job['spec'].get('aspect', '9:16')} {job['spec'].get('template', '')}\nNARRATION: {_narration(job)[:6000]}")
    error = ""
    for _ in range(2):
        raw = llm.complete_json(KIT_SYSTEM, user if not error else f"{user}\n\nYour previous answer was invalid: {error}. JSON only.")
        try:
            m = re.search(r"\{.*\}", raw, re.S)
            d = json.loads(m.group(0)) if m else {}
            titles = [str(t).strip()[:100] for t in d.get("titles") or [] if str(t).strip()][:5]
            if not titles:
                raise ValueError("no titles")
            tags = []
            for t in d.get("hashtags") or []:
                t = "#" + re.sub(r"[^\w]", "", str(t))
                if len(t) > 1 and t.lower() not in [x.lower() for x in tags]:
                    tags.append(t)
            return {"titles": titles, "description": str(d.get("description", "")).strip()[:2000],
                    "hashtags": tags[:15], "pinned_comment": str(d.get("pinned_comment", "")).strip()[:300],
                    "thumbnail_text": str(d.get("thumbnail_text", "")).strip()[:40], "source": llm.id}
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)
    raise ProviderError(f"the script model returned an invalid publish kit twice: {error}")


def kit_text(kit: dict) -> str:
    return "\n".join([
        "TITLES", *[f"- {t}" for t in kit["titles"]], "",
        "DESCRIPTION", kit["description"], "", " ".join(kit["hashtags"]), "",
        "PINNED COMMENT", kit["pinned_comment"], "", "THUMBNAIL TEXT", kit["thumbnail_text"], ""])


def _srt_ts(s: float) -> str:
    ms = int(round(max(0.0, s) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def srt(words: list[Word], per: int) -> str:
    out = []
    for i, c in enumerate(group(words, per), 1):
        out += [str(i), f"{_srt_ts(c.start)} --> {_srt_ts(c.end)}", c.text, ""]
    return "\n".join(out)


README = """CreatorForge export - {title}

Folder order = timeline order. To finish in CapCut (phone or desktop):
1. New project -> import everything in media/ in number order (01, 02, ...). Images become stills;
   set each to the length in timeline.csv (or keep CapCut's default and trim to the voice-over).
2. Add audio/voiceover.wav on the audio track. It is the full narration, already timed to the scenes.
3. Add audio/music.* underneath and lower its volume to about 15-20%.
4. Captions: Text -> Auto captions, or import captions.srt (CapCut desktop: Text -> Local captions -> Import).
5. publish.txt has titles, description, hashtags and a pinned comment ready to paste.
creatorforge.mp4 is the finished video CreatorForge rendered, if you just want to post it.
"""


def export_zip(job: dict, jdir: Path, out: Path, kit: dict | None) -> Path:
    plan = job.get("plan") or {}
    shots = plan.get("scenes", [])
    durations = (job.get("edit") or {}).get("durations") or [s.get("narration_s") or 0 for s in job["scenes"]]
    transitions = [""] + list((job.get("edit") or {}).get("transitions") or [])
    title = job.get("title") or plan.get("title") or job["id"]
    tmp = out.with_suffix(".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        rows = io.StringIO()
        w = csv.writer(rows)
        w.writerow(["scene", "file", "start_s", "duration_s", "transition_in", "narration", "visual"])
        start = 0.0
        for i, sc in enumerate(job["scenes"]):
            shot = shots[i] if i < len(shots) else {}
            src = None
            if sc.get("clip") and sc.get("clip_state") == "READY" and (jdir / sc["clip"]).is_file():
                src = jdir / sc["clip"]
            elif sc.get("image") and (jdir / sc["image"]).is_file():
                src = jdir / sc["image"]
            name = ""
            if src is not None:
                name = f"media/{i + 1:02d}_scene{src.suffix}"
                z.write(src, name, compress_type=zipfile.ZIP_STORED)
            if sc.get("narration") and (jdir / sc["narration"]).is_file():
                z.write(jdir / sc["narration"], f"audio/scenes/{i + 1:02d}_voice.wav")
            d = float(durations[i]) if i < len(durations) else 0.0
            w.writerow([i + 1, name, round(start, 2), round(d, 2), transitions[i] if i < len(transitions) else "",
                        shot.get("narration", ""), shot.get("visual", "")])
            start += d
        z.writestr("timeline.csv", rows.getvalue())
        voice = jdir / "work" / "narration.wav"
        if voice.is_file():
            z.write(voice, "audio/voiceover.wav")
        music = Path(job["music_track"]) if job.get("music_track") else None
        if music and music.is_file():
            z.write(music, f"audio/music{music.suffix}", compress_type=zipfile.ZIP_STORED)
        words_file = jdir / "words.json"
        if words_file.is_file():
            per = TEMPLATES.get(job["spec"].get("template"), TEMPLATES["shorts_cinematic"]).words_per_caption
            z.writestr("captions.srt", srt([Word(**d) for d in json.loads(words_file.read_text())], per))
        final = jdir / "creatorforge.mp4"
        if final.is_file():
            z.write(final, "creatorforge.mp4", compress_type=zipfile.ZIP_STORED)
        z.writestr("publish.txt", kit_text(kit or fallback_kit(job)))
        z.writestr("README.txt", README.format(title=title))
    tmp.replace(out)
    return out


def make_kit(llm, job: dict) -> dict:
    """The posting kit, with the writer's own title, cover text, hashtags and source taking priority."""
    kit = _make_kit(llm, job)
    w = (job.get("spec") or {}).get("publish") or {}
    if w.get("title"):
        kit["titles"] = [w["title"]] + [t for t in kit["titles"] if t != w["title"]][:4]
    if w.get("hashtags"):
        kit["hashtags"] = list(dict.fromkeys(list(w["hashtags"]) + kit["hashtags"]))[:15]
    if w.get("cover"):
        kit["thumbnail_text"] = w["cover"]
    if w.get("source") and w["source"] not in kit["description"]:
        cites = [c.strip() for c in w["source"].split(";") if c.strip()]
        label = "Sources:\n" if len(cites) > 1 else "Source: "
        kit["description"] = (kit["description"] + "\n\n" + label + "\n".join(cites)).strip()
    # Wikimedia Commons licences require a credit; NASA asks for one. (Pixabay needs none.)
    owed = [c for c in job.get("stock_credits") or []
            if any(x in c for x in ("Wikimedia", "Unsplash", "Internet Archive", "(CC", "Public domain")) or c == "NASA"]
    if owed:
        kit["description"] = (kit["description"] + "\n\nCredits: " + "; ".join(owed[:8])).strip()
    return kit
