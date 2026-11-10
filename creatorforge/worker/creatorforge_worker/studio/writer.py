"""The screenplay: concept, acts, and for every narration line its delivery, its evidence and its graphic.

    {"id": "aral-sea", "title": "...", "genre": "environment", "language": "en", "voice": "am_michael", "lang": "en-us",
     "concept": {"logline", "central_question", "conflict", "discovery", "unanswered", "consequences", "implications",
                 "structure": "investigative|chronological|mystery|character", "structure_note", "visual_concept"},
     "pronunciation": {"Moynaq": "Moy-nahk"},
     "scenes": [{"id": "S01", "act": "hook", "role": "opening", "narration": "...", "delivery": "quiet, curious",
                 "pause": 0.6, "emphasis": ["sand"], "claims": ["C13"], "graphic": "Hero: ship | ...",
                 "camera": "", "transition": ""}],
     "thumbnail": "BigNumber: ...", "cutdowns": [{"title": "...", "scenes": ["S01", "S02"]}]}

check() is the editorial review: a screenplay with an error is not produced.
write() asks a language model for a screenplay from the dossier, then reviews it (one repair round).
"""
from __future__ import annotations

import json
import re

from .dossier import NEEDS_ATTRIBUTION, Dossier, attributed, figures_in

ACTS = ("hook", "world", "investigation", "discovery", "consequences", "ending")
WORDS_PER_SECOND = 2.6          # a documentary narrator, for the hook-length estimate before the audio exists
INTERRUPT_SECONDS = 20          # no stretch this long without a new kind of picture (a visual pattern interrupt)
# Phrases that make a script sound generated; the showrunner bans them by name (channels/SHOWRUNNER.md)
BANNED_PHRASES = ("delve", "delving", "testament to", "moreover", "in a world where", "it's important to remember",
                  "it is important to remember", "let's unpack", "lets unpack", "buckle up", "game-changer", "game changer",
                  "unlock the secrets", "in today's fast-paced", "navigate the complexities", "tapestry")
# The narrative engines a new film is pitched in; back-to-back films never share one (channels/SHOWRUNNER.md)
ENGINES = {"reverse-autopsy": "start at the aftermath and rewind clock by clock",
           "live-viewer-trap": "a 45-second test in which the viewer's own brain falls for the effect",
           "trojan-horse": "an everyday object or rule hiding a large machine",
           "historical-echo": "a modern tactic paralleled with a forgotten historical con or survival glitch"}


def graphic_problem(graphic: str) -> str:
    from .. import vox_director as vd
    from ..media import scene3d
    kind = graphic.split(":", 1)[0].strip().lower()
    if kind == "key":
        from ..media import composite
        return "" if composite.parse(graphic.split(":", 1)[1]) else "a key shot needs a foreground and a background"
    if kind in scene3d.KINDS:
        return "" if scene3d.plan_for(kind, graphic.split(":", 1)[1]) else "the 3D graphic can't be drawn from this line"
    return vd.valid(graphic)


def check(sp: dict, dossier: Dossier) -> list[dict]:
    out = []

    def add(level, scene, msg):
        out.append({"level": level, "scene": scene, "problem": msg})
    scenes = sp.get("scenes") or []
    if not scenes:
        add("error", "-", "no scenes")
        return out
    for k in ("logline", "central_question"):
        if not (sp.get("concept") or {}).get(k):
            add("error", "concept", f"concept has no {k}")
    eng = str(sp.get("engine", "")).strip()
    if eng and eng not in ENGINES:
        add("error", "concept", f"engine must be one of {', '.join(ENGINES)}")
    elif not eng:
        add("warning", "concept", "no narrative engine named (engine: " + " | ".join(ENGINES) + ")")
    seen_ids, seen_text = set(), set()
    for i, s in enumerate(scenes):
        sid = str(s.get("id") or f"#{i + 1}")
        if sid in seen_ids:
            add("error", sid, "duplicate scene id")
        seen_ids.add(sid)
        text = str(s.get("narration", "")).strip()
        if not text:
            add("error", sid, "no narration")
        if text in seen_text:
            add("error", sid, "narration repeats an earlier line")
        low = text.lower().replace("’", "'")
        for ph in BANNED_PHRASES:
            if re.search(rf"(?<![a-z]){re.escape(ph)}(?![a-z])", low):
                add("error", sid, f"banned phrase '{ph}': it reads as generated")
        seen_text.add(text)
        if s.get("act") not in ACTS:
            add("error", sid, f"act must be one of {', '.join(ACTS)}")
        g = str(s.get("graphic", "")).strip()
        if not g:
            add("error", sid, "no graphic: every line needs a deliberate visual")
        else:
            p = graphic_problem(g)
            if p:
                add("error", sid, f"graphic: {p}")
        ids = [str(c) for c in s.get("claims", [])]
        for c in ids:
            if c not in dossier.claims:
                add("error", sid, f"cites {c}, which is not in the dossier")
            elif dossier.claims[c].status == "unverified":
                add("error", sid, f"cites {c}, which is unverified")
        # every figure said or shown must be one the cited evidence supports
        allowed = dossier.figures(ids)
        for f in figures_in(text) + figures_in(g.split(":", 1)[1] if ":" in g else g):
            if f not in allowed:
                add("error", sid, f"the figure {f} is not in the evidence this scene cites ({', '.join(ids) or 'none'})")
        needs = [c for c in ids if c in dossier.claims and dossier.claims[c].status in NEEDS_ATTRIBUTION]
        if needs and not attributed(text):
            add("error", sid, f"{', '.join(needs)} must be attributed or qualified in the narration "
                              f"({', '.join(dossier.claims[c].status for c in needs)})")
        if i and str(scenes[i - 1].get("graphic", "")).split(":")[0] == g.split(":")[0] and g:
            add("warning", sid, "the same kind of graphic as the line before")
    # pattern interrupts: no stretch of about 20 s on one kind of picture
    run_kind, run_secs, run_start = None, 0.0, None
    for s in scenes:
        sid = str(s.get("id", "?"))
        secs = len(str(s.get("narration", "")).split()) / WORDS_PER_SECOND + float(s.get("pause", 0) or 0)
        kind = str(s.get("graphic", "")).split(":")[0].strip().lower()
        # on-screen words must be readable in the time the line is up: 0.5 s plus 0.3 s a word
        shown = [x.strip() for x in str(s.get("graphic", "")).split(":", 1)[-1].split("|")]
        shown = [x for x in shown if x and ":" not in x and not re.fullmatch(r"[\w-]+", x)]
        words = sum(len(x.split()) for x in shown)
        if words and secs < 0.5 + 0.3 * words:
            add("warning", sid, f"{words} on-screen words need about {0.5 + 0.3 * words:.0f}s to read; the line lasts about {secs:.0f}s")
        if secs > INTERRUPT_SECONDS:
            add("warning", sid, f"about {secs:.0f}s on one picture: split it or add a visual pattern interrupt")
        if kind == run_kind:
            run_secs += secs
        else:
            run_kind, run_secs, run_start = kind, secs, sid
        if run_secs > INTERRUPT_SECONDS and kind == run_kind and run_start != sid:
            add("warning", sid, f"about {run_secs:.0f}s of '{kind}' since {run_start}: no visual pattern interrupt")
            run_secs = -1e9                       # report a run once
    # structure: a hook first, the central question asked early
    if scenes[0].get("act") != "hook":
        add("error", scenes[0].get("id", "#1"), "the film must open on its hook")
    hook = [s for s in scenes if s.get("act") == "hook"]
    secs = sum(len(str(s.get("narration", "")).split()) for s in hook) / WORDS_PER_SECOND
    if secs > 45:
        add("warning", "hook", f"the hook runs about {secs:.0f}s; it should land in 15-30s")
    if not any("?" in str(s.get("narration", "")) for s in scenes[:max(3, len(hook) + 1)]):
        add("warning", "hook", "the central question is not asked in the opening")
    acts = [s.get("act") for s in scenes]
    order = [a for a in ACTS if a in acts]
    if [a for a in dict.fromkeys(acts)] != order:
        add("warning", "structure", "acts are out of their usual order (fine if the story needs it)")
    if acts[-1] != "ending":
        add("error", scenes[-1].get("id", "-"), "the film must end on its ending")
    return out


def novelty(sp: dict, hist: list[dict]) -> list[dict]:
    """The anti-clone check: a film never shares its narrative engine, its hook mechanism or a visual metaphor with
    the channel's previous film. `hist` is the studio history (oldest first)."""
    out = []
    chan = str(sp.get("channel", "")).strip().lower()
    prev = [h for h in hist if str(h.get("channel", "")).strip().lower() == chan and h.get("id") != sp.get("id")]
    if not prev:
        return out
    last = prev[-1]
    if sp.get("engine") and sp.get("engine") == last.get("engine"):
        out.append({"level": "error", "scene": "concept", "problem": f"the narrative engine '{sp['engine']}' was used by the previous film ({last.get('id')})"})
    hook = str(sp.get("hook_mechanism", "")).strip().lower()
    if hook and hook == str(last.get("hook_mechanism", "")).strip().lower():
        out.append({"level": "error", "scene": "hook", "problem": f"the hook mechanism '{hook}' was used by the previous film ({last.get('id')})"})
    used = {str(m).strip().lower() for m in last.get("metaphors", [])}
    for m in sp.get("metaphors", []):
        if str(m).strip().lower() in used:
            out.append({"level": "error", "scene": "concept", "problem": f"the visual metaphor '{m}' was used by the previous film ({last.get('id')})"})
    older = {str(m).strip().lower() for h in prev[-4:-1] for m in h.get("metaphors", [])}
    for m in sp.get("metaphors", []):
        if str(m).strip().lower() in older:
            out.append({"level": "warning", "scene": "concept", "problem": f"the visual metaphor '{m}' was used in the last few films"})
    return out


PROMPT = """You are an investigative documentary writer. Write a complete documentary screenplay as JSON from the
research dossier below. Rules:
- Build it around ONE central question. Open with a scene, contradiction or revelation (15-30 s), never "today we".
- Acts in order: hook, world, investigation, discovery (the turn), consequences, ending (return to the question).
- Narration: written for the ear: short, punchy sentences, sudden pacing shifts, curiosity ("Wait. Look at this line.").
  One to two sentences per scene. Never use: {banned}. Bridge acts with open-loop questions.
- Use the narrative engine given in the brief; name it in "engine", the hook's mechanism in "hook_mechanism" and the
  film's visual metaphors in "metaphors". Change the kind of picture at least every 20 seconds.
- Every scene cites the dossier claim ids it relies on ("claims"). Use ONLY figures that are in those claims' "figures".
  Claims marked reported / estimate / disputed / allegation / opinion / interpretation must be attributed or qualified
  in the narration ("according to...", "an estimate", "is still debated"). Never use an unverified claim.
- Every scene has one graphic line from the catalogue below that shows what the line says (on-screen words in English).
  Do not use the same kind of graphic twice in a row. Mark the opening, the climax and the ending with "role".
- Add "delivery" (e.g. "quiet, curious"), "pause" (seconds after the line), "emphasis" (words) per scene, a
  "pronunciation" guide for hard names, a "thumbnail" graphic line and 1-2 "cutdowns" (scene ids, 30-60 s each).
Return JSON with keys: id, title, channel, genre, language, engine, hook_mechanism, metaphors[], concept{logline, central_question, conflict, discovery, unanswered,
consequences, implications, structure, structure_note, visual_concept}, pronunciation, scenes[], thumbnail, cutdowns.

GRAPHICS CATALOGUE:
{catalogue}

DOSSIER:
{dossier}
"""


def pitch(dossier: Dossier, hist: list[dict] | None = None, channel: str = "", llm=None) -> list[dict]:
    """Step one of every new film: three different narrative engines for the owner to pick from. No script is written
    before the pick (channels/SHOWRUNNER.md). The channel's previous engine is never offered. With a language model,
    each pitch gets a one-line opening written from the dossier; without one, the engine's own description stands."""
    chan = channel.strip().lower()
    prev = [h for h in (hist or []) if str(h.get("channel", "")).strip().lower() == chan]
    last = prev[-1].get("engine") if prev else None
    recent = [h.get("engine") for h in prev[-3:]]
    pool = [e for e in ENGINES if e != last]
    pool.sort(key=lambda e: recent.count(e))          # the least-used engines first
    out = [{"engine": e, "how": ENGINES[e], "opening": ""} for e in pool[:3]]
    if llm is not None and dossier.claims:
        facts = "\n".join(f"- {c.claim}" for c in list(dossier.claims.values())[:40])
        ask = ("For each narrative engine below, write ONE opening beat (two sentences, for the ear) for a documentary on "
               f"'{dossier.topic}', using only these facts:\n{facts}\n\nEngines:\n" +
               "\n".join(f"{p['engine']}: {p['how']}" for p in out) +
               '\nReturn JSON: {"pitches": [{"engine": ..., "opening": ...}]}. Never use: ' + ", ".join(BANNED_PHRASES))
        try:
            raw = llm.complete_json("You pitch documentary openings as strict JSON.", ask)
            got = json.loads(raw if isinstance(raw, str) else json.dumps(raw)).get("pitches", [])
            lines = {str(g.get("engine")): str(g.get("opening", "")).strip() for g in got if isinstance(g, dict)}
            for p in out:
                line = lines.get(p["engine"], "")
                if line and not any(re.search(rf"(?<![a-z]){re.escape(b)}(?![a-z])", line.lower()) for b in BANNED_PHRASES):
                    p["opening"] = line
        except Exception:  # noqa: BLE001 - a pitch without an opening line is still a pitch
            pass
    return out


def write(llm, dossier: Dossier, brief: str = "", tries: int = 2, engine: str = "") -> tuple[dict, list[dict]]:
    """A screenplay written by the language model and reviewed; returns (screenplay, remaining issues).
    `engine` is the owner's pick from pitch(); the screenplay is held to it."""
    if engine and engine not in ENGINES:
        raise ValueError(f"engine must be one of {', '.join(ENGINES)}")
    if engine:
        brief = (brief + "\n" if brief else "") + f"NARRATIVE ENGINE (the producer's pick): {engine}: {ENGINES[engine]}"
    from .. import vox_director as vd
    from ..media import scene3d
    cat = vd.CATALOG + "\n" + scene3d.__doc__
    user = PROMPT.replace("{banned}", ", ".join(BANNED_PHRASES)).replace("{catalogue}", cat).replace("{dossier}", json.dumps(dossier.to_dict(), ensure_ascii=False)[:60000])
    if brief:
        user += "\nBRIEF FROM THE PRODUCER:\n" + brief
    sp, issues = {}, [{"level": "error", "scene": "-", "problem": "not written"}]
    for _ in range(tries):
        raw = llm.complete_json("You write documentary screenplays as strict JSON.", user)
        try:
            sp = json.loads(raw if isinstance(raw, str) else json.dumps(raw))
        except ValueError:
            m = re.search(r"\{.*\}", str(raw), re.S)
            sp = json.loads(m.group(0)) if m else {}
        if engine and isinstance(sp, dict):
            sp["engine"] = engine
        issues = check(sp, dossier)
        if not [i for i in issues if i["level"] == "error"]:
            break
        user += "\n\nYOUR LAST SCREENPLAY HAD THESE PROBLEMS - FIX EVERY ONE AND RETURN THE WHOLE JSON AGAIN:\n" + \
            "\n".join(f"- {i['scene']}: {i['problem']}" for i in issues if i["level"] == "error")
    return sp, issues


def narration_markdown(sp: dict, timeline: list[dict] | None = None) -> str:
    """The narration script for a narrator: scene numbers, timestamps, delivery, pauses, emphasis, pronunciation."""
    at = {t["scene"]: t for t in (timeline or [])}
    lines = [f"# Narration: {sp.get('title', '')}", ""]
    if sp.get("pronunciation"):
        lines += ["## Pronunciation", ""] + [f"- **{k}**: {v}" for k, v in sp["pronunciation"].items()] + [""]
    lines += ["## Script", ""]
    act = None
    for s in sp["scenes"]:
        if s.get("act") != act:
            act = s.get("act")
            lines += [f"### {act.title()}", ""]
        t = at.get(s["id"])
        stamp = f"[{_ts(t['start'])}-{_ts(t['end'])}] " if t else ""
        emph = s.get("emphasis") or []
        text = s["narration"]
        for w in emph:
            text = re.sub(rf"(?<!\w)({re.escape(w)})(?!\w)", r"**\1**", text, count=1)
        lines.append(f"**{s['id']}** {stamp}*({s.get('delivery', 'neutral')})* {text}"
                     + (f"  *[pause {s.get('pause')}s]*" if s.get("pause") else ""))
        lines.append("")
    return "\n".join(lines)


def _ts(x: float) -> str:
    return f"{int(x // 60)}:{x % 60:04.1f}"


def screenplay_markdown(sp: dict, dossier: Dossier) -> str:
    c = sp.get("concept", {})
    lines = [f"# {sp.get('title', '')}", "", f"*{c.get('logline', '')}*", "", "## Concept", ""]
    for k in ("central_question", "conflict", "discovery", "unanswered", "consequences", "implications", "structure", "structure_note"):
        if c.get(k):
            lines.append(f"- **{k.replace('_', ' ').capitalize()}**: {c[k]}")
    lines += ["", "## Screenplay", ""]
    act = None
    for s in sp["scenes"]:
        if s.get("act") != act:
            act = s.get("act")
            lines += [f"### {act.title()}", ""]
        lines += [f"**{s['id']}**" + (f" ({s['role']})" if s.get("role") else ""), "",
                  f"NARRATION ({s.get('delivery', 'neutral')}): {s['narration']}", "",
                  f"VISUAL: `{s['graphic']}`", "",
                  "EVIDENCE: " + ", ".join(f"{i} ({dossier.claims[i].status})" for i in s.get("claims", []) if i in dossier.claims), ""]
    return "\n".join(lines)


def retention_audit(sp: dict, timeline: list[dict] | None = None) -> dict:
    """The [RETENTION & MISTAKE AUDIT] every draft ends with: the weakest 10% of scenes, every stretch of more than 20 s
    without a visual pattern interrupt, and what to sharpen in each. Scores are heuristics a person reviews; the
    rewrite itself is the writer's (or the language model's) job and is asked for, never invented here."""
    scenes = sp.get("scenes") or []
    when = {str(t.get("scene")): (float(t.get("start", 0)), float(t.get("end", 0))) for t in (timeline or [])}
    rows, t0 = [], 0.0
    for i, s in enumerate(scenes):
        sid = str(s.get("id", f"#{i + 1}"))
        text = str(s.get("narration", ""))
        words = text.split()
        secs = (when[sid][1] - when[sid][0]) if sid in when else len(words) / WORDS_PER_SECOND + float(s.get("pause", 0) or 0)
        start = when[sid][0] if sid in when else t0
        t0 = start + secs
        kind = str(s.get("graphic", "")).split(":")[0].strip().lower()
        why, score = [], 0.0
        if secs > 12:
            score += (secs - 12) / 4
            why.append(f"{secs:.0f}s on one picture")
        if words and sum(len(w) for w in words) / len(words) > 6.2:
            score += 1
            why.append("long words: hard on the ear")
        if words and len(words) / max(1, text.count(".") + text.count("?") + text.count("!")) > 22:
            score += 1
            why.append("long sentences")
        if i and kind == str(scenes[i - 1].get("graphic", "")).split(":")[0].strip().lower():
            score += 1.5
            why.append(f"same kind of picture as the line before ({kind})")
        if not s.get("claims") and s.get("act") not in ("hook", "ending") and not re.search(r"\?", text):
            score += .5
            why.append("no evidence cited and no question asked")
        if s.get("act") in ("investigation", "consequences") and i + 1 < len(scenes) and scenes[i + 1].get("act") != s.get("act") \
                and "?" not in text:
            score += 1
            why.append("act ends without an open loop")
        rows.append({"scene": sid, "start": round(start, 1), "seconds": round(secs, 1), "kind": kind, "score": round(score, 2), "why": why})
    n = max(1, round(len(rows) * .1))
    weakest = [r for r in sorted(rows, key=lambda r: -r["score"]) if r["score"] > 0][:n]
    gaps, run = [], None
    for r in rows:
        if run and r["kind"] == run["kind"]:
            run["end"] = r["start"] + r["seconds"]
            run["scenes"].append(r["scene"])
        else:
            if run and run["end"] - run["start"] > INTERRUPT_SECONDS:
                gaps.append(run)
            run = {"kind": r["kind"], "start": r["start"], "end": r["start"] + r["seconds"], "scenes": [r["scene"]]}
    if run and run["end"] - run["start"] > INTERRUPT_SECONDS:
        gaps.append(run)
    return {"weakest": weakest, "no_interrupt": [{**g, "start": round(g["start"], 1), "end": round(g["end"], 1)} for g in gaps], "scenes": rows}


def retention_markdown(sp: dict, audit: dict) -> str:
    by = {str(s.get("id")): s for s in sp.get("scenes") or []}
    out = ["# [RETENTION & MISTAKE AUDIT]", "", f"Film: {sp.get('title', '')}", "", "## 1. The weakest 10%", ""]
    for w in audit["weakest"] or []:
        out += [f"- **{w['scene']}** at {_ts(w['start'])} ({w['seconds']}s, {w['kind']}): {'; '.join(w['why'])}",
                f"  - Now: \"{by.get(w['scene'], {}).get('narration', '')}\"",
                "  - Sharper rewrite: _to write before the next draft: shorter, one concrete image, end on a question_"]
    if not audit["weakest"]:
        out.append("- nothing scored as weak; a person still watches the draft")
    out += ["", "## 2. Stretches over 20 s without a visual pattern interrupt", ""]
    out += [f"- {_ts(g['start'])}-{_ts(g['end'])}: {g['kind']} across {', '.join(g['scenes'])}: cut in a map, document or "
            "number, or change the camera" for g in audit["no_interrupt"]] or ["- none"]
    out += ["", "## 3. Fact audit", "", "See editorial_review.md: every figure is checked against the claims each scene cites."]
    return "\n".join(out)
