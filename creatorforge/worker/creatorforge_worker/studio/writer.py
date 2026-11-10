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


PROMPT = """You are an investigative documentary writer. Write a complete documentary screenplay as JSON from the
research dossier below. Rules:
- Build it around ONE central question. Open with a scene, contradiction or revelation (15-30 s), never "today we".
- Acts in order: hook, world, investigation, discovery (the turn), consequences, ending (return to the question).
- Narration: conversational, precise, varied sentence length, no AI phrasing. One to two sentences per scene.
- Every scene cites the dossier claim ids it relies on ("claims"). Use ONLY figures that are in those claims' "figures".
  Claims marked reported / estimate / disputed / allegation / opinion / interpretation must be attributed or qualified
  in the narration ("according to...", "an estimate", "is still debated"). Never use an unverified claim.
- Every scene has one graphic line from the catalogue below that shows what the line says (on-screen words in English).
  Do not use the same kind of graphic twice in a row. Mark the opening, the climax and the ending with "role".
- Add "delivery" (e.g. "quiet, curious"), "pause" (seconds after the line), "emphasis" (words) per scene, a
  "pronunciation" guide for hard names, a "thumbnail" graphic line and 1-2 "cutdowns" (scene ids, 30-60 s each).
Return JSON with keys: id, title, genre, language, concept{logline, central_question, conflict, discovery, unanswered,
consequences, implications, structure, structure_note, visual_concept}, pronunciation, scenes[], thumbnail, cutdowns.

GRAPHICS CATALOGUE:
{catalogue}

DOSSIER:
{dossier}
"""


def write(llm, dossier: Dossier, brief: str = "", tries: int = 2) -> tuple[dict, list[dict]]:
    """A screenplay written by the language model and reviewed; returns (screenplay, remaining issues)."""
    from .. import vox_director as vd
    from ..media import scene3d
    cat = vd.CATALOG + "\n" + scene3d.__doc__
    user = PROMPT.replace("{catalogue}", cat).replace("{dossier}", json.dumps(dossier.to_dict(), ensure_ascii=False)[:60000])
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
