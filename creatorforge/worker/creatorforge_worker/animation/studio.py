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
import re
from pathlib import Path

from . import storyboard as SB
from . import visual_reasoning as VR

WEATHER = [(r"\b(stops? raining|rain stops|sun comes out|clears? up)\b", "clear"),
           (r"\b(thunder\w*|lightning|storm\w*)\b", "storm"), (r"\b(rain\w*|downpour|drizzl\w*|monsoon)\b", "rain"),
           (r"\b(snow\w*|blizzard)\b", "snow"), (r"\b(wind|winds|windy|gale|breez\w*|gust\w*)\b", "wind")]
TIME_OF_DAY = [(r"\b(dawn|sunrise|early morning)\b", "dawn"), (r"\b(sunset|dusk|evening)\b", "dusk"),
               (r"\b(night\w*|midnight|dark)\b", "night"), (r"\b(morning|noon|afternoon|daylight)\b", "day")]
BODY = [[40, 110, 200], [200, 70, 110], [60, 150, 90], [230, 140, 30], [120, 80, 170], [60, 60, 60]]
KNOWN_VERBS = {v for _, v in SB.VERBS}


WORLD_WORDS = [
    (r"\b(outer space|space station|spaceship|rocket|planet|the moon|on mars|orbit|galaxy|asteroid|astronaut)s?\b", "space"),
    (r"\b(underwater|coral reef|reef|seabed|ocean floor|under the sea|deep sea)\b", "underwater"),
    (r"\b(beach|shore|ocean|coast|harbou?r|waves)\b", "ocean"),
    (r"\b(forest|woods|jungle)\b", "forest"),
    (r"\b(mountains?|peak|summit|himalayas?|alps)\b", "mountains"),
    (r"\b(desert|dunes?|sahara)\b", "desert"),
    (r"\b(savanna|grassland|safari|plains)\b", "savanna"),
    (r"\b(castle|kingdom|palace|dragon'?s? lair)\b", "castle"),
    (r"\b(pyramids?|ancient|temple|pharaoh|roman|empire|centurion)\b", "ancient"),
    (r"\b(cells?|bloodstream|blood vessel|virus(es)?|bacteria|immune system|neurons?|inside the body)\b", "microscopic"),
    (r"\b(his mind|her mind|their mind|the mind|dreams?|imagination|memories)\b", "mind"),
    (r"\b(classroom|school)\b", "interior:school"),
    (r"\b(office|meeting room)\b", "interior:office"),
    (r"\b(kitchen|bedroom|living room|at home|the house)\b", "interior:home"),
    (r"\b(village|farm|fields?)\b", "village"),
    (r"\b(city|street|town|market|downtown)\b", "city"),
]


def make(script: str, title: str = "", sources: list | None = None, voice: dict | None = None,
         spoken: list | None = None, target_seconds: float | None = None, style="auto", world=None,
         format: dict | None = None) -> tuple[dict, dict]:
    """voice: {"lang": "en"|"hi", "rate": ..} to narrate (None: subtitles only). spoken: optional per-sentence text to
    speak when it differs from the subtitle (Hinglish: the subtitle in Roman letters, the voice from Devanagari).
    style: "auto" (chosen from the script's genre), a preset name or {"name", "stylization", ...}; world: a world
    name for every scene (None: chosen per line from the places named); format: {"aspect", "fps"}. Every choice is
    written into the document, where it can be changed."""
    from . import cinematic
    from . import story as ST
    board = SB.plan(script, title)
    style_name, why = cinematic.choose(script, board.domain, None if style == "auto" else style)
    illustrated = style_name not in ("stick", None)
    cast = getattr(board, "cast", {})
    arc = ST.analyze(board, target_seconds, sources)          # the whole story first: arc, feelings, pacing
    notes = {"domain": board.domain, "decisions": [f"style: {style_name} ({why})"], "limitations": [], "sources": [],
             "story": arc.to_dict()}
    place = world
    people = [n for n, c in cast.items() if c.role != "animal" and c.role != "crowd"]
    colour = {n: BODY[k % len(BODY)] for k, n in enumerate(people)}
    present: list[str] = []
    animals_seen: dict = {}
    scenes = []
    prev_env = None
    sky: dict = {}                                      # weather and time of day persist until the script changes them
    for i, b in enumerate(board.beats):
        low = b.narration.lower()
        wx = next((k for rx, k in WEATHER if re.search(rx, low)), None)
        tod = next((k for rx, k in TIME_OF_DAY if re.search(rx, low)), None)
        if wx == "clear":
            sky.pop("weather", None)
        elif wx:
            sky["weather"] = [[0.0, 9999.0, wx, 1.0]]
            sky["wind"] = 0.6 if wx in ("storm", "wind") else 0.2
            notes["decisions"].append(f"line {i + 1}: {wx} from here on")
            if wx == "storm":
                tod = tod or "storm"
        if tod:
            sky["light"] = [[0.0, sky["light"][-1][1]], [0.8, tod]] if sky.get("light") else [[0.0, tod]]
            notes["decisions"].append(f"line {i + 1}: light becomes {tod}")
        elif sky.get("light"):
            sky["light"] = [[0.0, sky["light"][-1][1]]]
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
            spec = {"name": n, "body": colour[n], "faceless": not c.face and not (illustrated and not c.label),
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
        subj_rx = "|".join(re.escape(n) for n in list(cast) + ["he", "she", "it", "they", "He", "She", "It", "They"])
        for m in re.finditer(rf"\b(?:(?:{subj_rx})\b(?:\s+\w+ly)?\s+([a-z]+(?:es|s|ed))|(?:they|we|and they)\s+([a-z]{{3,}}))\b",
                             b.narration, re.I):
            w = (m.group(1) or m.group(2)).lower()
            if not any(re.search(rx, w, re.I) for rx, _ in SB.VERBS) and w not in ("is", "was", "has", "does", "goes", "are",
                                                                                         "were", "have", "the", "all"):
                notes["limitations"].append(f"line {i + 1}: '{w}' is not an action the studio can animate yet")
        acts = b.actions
        if wx and wx != "clear" and all(a["verb"] in ("think", "explain") for a in acts):
            acts = []                                  # nobody does anything - the weather happens to them
            for k, n in enumerate(lineup):
                steps.append({"t": "+0.1" if k == 0 else "+0.05", "do": "look", "who": n, "at": [0.0, 4.0],
                              "dur": 1.0, "wait": False})
                steps.append({"t": "+0.5", "do": "gesture", "who": n, "name": "cover_face" if wx != "wind"
                              else "hands_up", "dur": 1.6, "wait": k == len(lineup) - 1})
            notes["decisions"].append(f"line {i + 1}: everyone looks up and shelters from the {wx}")
        for a in acts:
            if a["verb"] not in KNOWN_VERBS and a["verb"] not in ("say", "explain", "think"):
                notes["limitations"].append(f"line {i + 1}: '{a['verb']}' has no animation - shown as a gesture")
            if a["verb"] == "say":
                steps.append({"t": "+0.2", "do": "say", "who": a["who"], "text": a["line"]})
                continue
            steps.append({"t": "+0.2", "do": "act", "who": a["who"], "verb": a["verb"], "target": a["target"],
                          "things": b.things, "line": b.narration})
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
        for n in lineup:                               # feelings carry from earlier beats (fading), and a big
            felt = arc.emotions.get(n, [""] * len(board.beats))[i]          # swing passes through neutral
            if any(tr[0] == i and tr[1] == n for tr in arc.transitions):
                steps.insert(0, {"t": 0.0, "do": "express", "who": n, "face": "neutral", "blend": 0.5,
                                 "wait": False})
                notes["decisions"].append(f"line {i + 1}: {n} passes through a neutral beat before the change")
            elif felt and felt != b.emotion and cast.get(n) and cast[n].face is not None:
                steps.insert(0, {"t": 0.0, "do": "feel", "who": n, "emotion": felt, "dur": 1.8, "wait": False})
        steps.append({"t": "+0.0", "do": "wait_notes"})
        extra = arc.holds[i] + max(0.0, arc.pace[i] - 1.0) * (b.narration_window[1] - b.narration_window[0])
        if extra > 0.05:                               # the climax gets room, the ending breathes, a turn waits
            steps.append({"t": "+0.0", "do": "wait", "dur": round(extra, 2)})
        layers = {k: v for k, v in sky.items()}
        if illustrated or world:                       # a painted world for the place the line names
            named = next((w_ for rx, w_ in WORLD_WORDS if re.search(rx, low)), None)
            if not world and named and named != place:
                notes["decisions"].append(f"line {i + 1}: world becomes {named}")
                place = named
            if place is None:
                place = {"indoors": "interior:home", "outdoors": "village"}.get(b.environment, "city")
                notes["decisions"].append(f"line {i + 1}: no place named - {place} (change the scene's world)")
            night = any(k_[1] == "night" for k_ in sky.get("light", []))
            layers["world"] = place + (":night" if night and place in ("city", "forest") else "")
        scenes.append({"layers": layers, "id": f"s{i + 1:02d}", "name": b.narration[:38] + ("..." if len(b.narration) > 38 else ""),
                       "place": b.environment, "cut": cut, "timing": b.timing, "cast": cast_specs,
                       "animals": list(animals_seen.values()), "things": b.things, "props": [],
                       "focus": [n for n in b.characters[:2]], "camera": {"style": arc.camera[i]},
                       "arc": arc.roles[i], "steps": steps})
        present = lineup
    doc = {"title": board.title, "fps": 24, "source_script": script, "scenes": scenes}
    if illustrated:
        doc["style"] = style if isinstance(style, dict) else style_name
    if format:
        doc["format"] = dict(format)
    return doc, notes


def film(script: str, out: Path, title: str = "", sources: list | None = None, voice: dict | None = None,
         spoken: list | None = None, quality: str = "preview", workers: int = 2, target_seconds: float | None = None,
         force: bool = False, style="auto", world=None, format: dict | None = None) -> dict:
    """make -> validate the plan -> render -> review. Writes <out>.doc.json (the editable source),
    <out>.plan.json (the story plan) and <out>.report.json. A plan with errors is not rendered unless forced."""
    from . import critic, production, qc
    out = Path(out)
    doc, notes = make(script, title, sources, voice, spoken, target_seconds, style, world, format)
    out.with_suffix(".plan.json").write_text(json.dumps(notes["story"], indent=1, ensure_ascii=False))
    if notes["story"]["errors"] and not force:
        raise ValueError("the story plan has errors: " + "; ".join(notes["story"]["errors"]))
    out.with_suffix(".doc.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    rep = production.render(doc, out, quality, workers=workers)
    quality = production.quality_for(doc, quality)
    states = production.plan_states(doc, quality)
    reviews, assets = [], []
    for sd, st in zip(production.scenes_of(doc), states):
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
