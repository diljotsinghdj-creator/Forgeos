"""The director: one pipeline from a script to a finished film.

    Script -> analysis (storyboard.plan: domain, cast, verbs, emotions, objects, places)
           -> research (each line matched to the sources supplied with it; what has no source is flagged)
           -> storyboard (visual_reasoning: how each line is shown - literal, demonstration, diagram, metaphor,
              satire, reconstruction, evidence)
           -> casting (people as stick figures - real public figures faceless and labelled; animals and objects
              from the asset library, or labelled placeholders)
           -> environment (indoors / outdoors / studio, scenery from the nouns)
           -> production document (production.py: editable, cached, continuity-checked)
           -> render (QC loop, camera with framing check, sound, narration) -> inspection report -> revision

    make(script, title, sources, voice) -> (doc, notes)   the document is plain JSON: open it in the editor, change
                                                           anything, render again (unchanged scenes come from cache)
    film(script, out, ...)              -> report          make + production.render + the critic's review

Nothing is silently substituted: whatever the script asks for that the studio cannot show (an unknown action, an
object with no generator, a claim with no source) is listed in notes["limitations"] with what was done instead."""
from __future__ import annotations

import json
from pathlib import Path

from . import storyboard as SB
from . import visual_reasoning as VR

BODY = [[40, 110, 200], [200, 70, 110], [60, 150, 90], [230, 140, 30], [120, 80, 170], [60, 60, 60]]
KNOWN_VERBS = {v for _, v in SB.VERBS}


def make(script: str, title: str = "", sources: list | None = None, voice: dict | None = None,
         spoken: list | None = None) -> tuple[dict, dict]:
    """voice: {"lang": "en"|"hi", "rate": ..} to narrate (None: subtitles only). spoken: optional per-sentence text to
    speak when it differs from the subtitle (Hinglish: the subtitle in Roman letters, the voice from Devanagari)."""
    board = SB.plan(script, title)
    cast = getattr(board, "cast", {})
    notes = {"domain": board.domain, "decisions": [], "limitations": [], "sources": []}
    people = [n for n, c in cast.items() if c.role != "animal" and c.role != "crowd"]
    colour = {n: BODY[k % len(BODY)] for k, n in enumerate(people)}
    present: list[str] = []
    animals_seen: dict = {}
    scenes = []
    prev_env = None
    for i, b in enumerate(board.beats):
        cut = i == 0 or b.environment != prev_env
        prev_env = b.environment
        if cut:
            present = []
        here = [n for n in b.characters if n in people]
        new = [n for n in here if n not in present]
        lineup = present + [n for n in new]
        cast_specs = []
        for k, n in enumerate(lineup):
            c = cast[n]
            spec = {"name": n, "body": colour[n], "faceless": not c.face,
                    "personality": c.personality if c.personality in ("kind", "timid", "energetic", "calm",
                                                                      "grumpy", "cheerful") else "kind",
                    "height": 1.5 if c.role in ("girl", "boy", "child", "children") else 1.72}
            if c.face:
                spec["skin"] = [226, 186, 150]
            if n in new and (present or i > 0) and not cut:
                spec["x"] = "offstage"                 # walks in when first named
            elif n in new:
                spec.update(x=(-1.6 + 3.2 * k / max(1, len(lineup) - 1)) if len(lineup) > 1 else 0.0,
                            facing=1 if k == 0 or len(lineup) == 1 else -1)
            cast_specs.append(spec)
            if c.label:
                notes["decisions"].append(f"{n}: drawn faceless and labelled '{c.label}' (a real person)")
        for n in b.characters:
            if cast.get(n) and cast[n].role == "animal":
                animals_seen[n] = {"name": n, "desc": cast[n].label or n, "landing":
                                   any(a["verb"] == "land" and a["who"] == n for a in b.actions)}
        steps = []
        for n in new:
            if any(s_.get("x") == "offstage" for s_ in cast_specs if s_["name"] == n):
                steps.append({"t": 0.2, "do": "enter", "who": n, "near": (present or here or [n])[0]})
        # how the line is shown, and whether its facts have a source
        sent_sources = [s_ for s_ in (sources or []) if VR._overlap(s_.get("claim", ""), b.narration) > 0.3]
        plan = VR.reason(b.narration, sources or [])
        notes["sources"].append({"line": b.narration, "mode": plan.mode, "sourced": plan.sourced,
                                 "sources": [s_["source"] for s_ in sent_sources]})
        if not plan.sourced:
            notes["limitations"].append(f"line {i + 1}: {plan.note or 'claim without a source'} - "
                                        "supply a source to show it as fact")
        say = (spoken[i] if spoken and i < len(spoken) else b.narration)
        v = {"say": say, **voice} if voice else None
        visual = plan.mode not in (VR.LITERAL,) or plan.elements
        line_step = {"t": "+0.1", "do": "visual" if visual else "caption", "text": b.narration, "wait": False}
        if visual:
            line_step.update(sources=sources or [], dur=max(5.0, b.narration_window[1] - b.narration_window[0]),
                             x=2.6)
        else:
            line_step.update(hold=False)
        if v:
            line_step["voice"] = v
        steps.append(line_step)
        for a in b.actions:
            if a["verb"] not in KNOWN_VERBS and a["verb"] not in ("say", "explain", "think"):
                notes["limitations"].append(f"line {i + 1}: '{a['verb']}' has no animation - shown as a gesture")
            if a["verb"] == "say":
                steps.append({"t": "+0.2", "do": "say", "who": a["who"], "text": a["line"]})
                continue
            steps.append({"t": "+0.2", "do": "act", "who": a["who"], "verb": a["verb"], "target": a["target"],
                          "things": b.things})
            if a["verb"] in ("explain", "think") and len(b.actions) == 1 and not b.metaphors:
                notes["decisions"].append(f"line {i + 1}: no physical action named - "
                                          f"{a['who']} {'explains' if a['verb'] == 'explain' else 'thinks'} it")
        subject = b.characters[0] if b.characters else None
        if b.emotion and subject in people:
            steps.append({"t": "-0.4", "do": "feel", "who": subject, "emotion": b.emotion, "dur": 1.6,
                          "wait": False})
        for m in b.metaphors:
            if m in ("price card", "ballot box", "storm cloud of worry") and not visual:
                steps.append({"t": "+0.0", "do": "metaphor", "who": subject if subject in people else None,
                              "kind": m, "dur": 5.0})
                notes["decisions"].append(f"line {i + 1}: '{m}' (labelled illustration)")
        steps.append({"t": "+0.0", "do": "wait_notes"})
        scenes.append({"id": f"s{i + 1:02d}", "name": b.narration[:38] + ("..." if len(b.narration) > 38 else ""),
                       "place": b.environment, "cut": cut, "timing": b.timing, "cast": cast_specs,
                       "animals": list(animals_seen.values()), "things": b.things, "props": [],
                       "focus": [n for n in b.characters[:2]], "camera": {"style": b.camera}, "steps": steps})
        present = lineup
    doc = {"title": board.title, "fps": 24, "source_script": script, "scenes": scenes}
    return doc, notes


def film(script: str, out: Path, title: str = "", sources: list | None = None, voice: dict | None = None,
         spoken: list | None = None, quality: str = "preview", workers: int = 2) -> dict:
    """make -> render -> review. Writes <out>.doc.json (the editable source) and <out>.report.json."""
    from . import critic, production, qc
    out = Path(out)
    doc, notes = make(script, title, sources, voice, spoken)
    out.with_suffix(".doc.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    rep = production.render(doc, out, quality, workers=workers)
    states = production.plan_states(doc, quality)
    reviews, assets = [], []
    for sd, st in zip(doc["scenes"], states):
        sc, T, _, _ = production.stage_scene(sd, st[6], production.QUALITY[quality]["fps"], quality)
        reviews.append({"scene": sd["id"], **critic.review(qc.record(sc, T), sc).to_dict()})
        for a in getattr(sc, "asset_log", []):
            if a not in assets:
                assets.append(a)
    for a in assets:
        if a["how"] == "placeholder":
            notes["limitations"].append(f"'{a['for']}': no generator in the asset library - shown as a labelled "
                                        "placeholder (add or import an asset to replace it)")
    report = {**rep, "notes": notes, "assets": assets, "critic": reviews}
    out.with_suffix(".report.json").write_text(json.dumps(report, indent=1, default=str, ensure_ascii=False))
    return report
