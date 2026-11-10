"""The art direction document: a creative treatment written for one film, different from the films before it.

Fifteen decisions (identity, narrative approach, visual concept, palette, typography, cinematography, maps, infographics,
animation, footage, sound, rhythm, opening, climax, ending). Each axis has several treatments; the film's genre narrows
them, and the studio history (the last films' choices) rules out what was just used, so two films on similar topics
still look, move and sound different. The document is both written out for people and applied by the renderer
(look, accent, camera policy, frame rate of drawn graphics, breath between lines, music, ambience).
"""
from __future__ import annotations

import json
import threading
import zlib
from pathlib import Path

GENRES = ("environment", "politics", "history", "economics", "geopolitics", "human", "science", "investigation")

AXES = {
    "look": {"environment": ["field", "chart", "archive"], "politics": ["newsprint", "kraft", "chart"],
             "history": ["sepia", "engraving", "archive"], "economics": ["chart", "newsprint", "kraft"],
             "geopolitics": ["archive", "field", "engraving"], "human": ["kraft", "archive", "field"],
             "science": ["chart", "field", "newsprint"], "investigation": ["newsprint", "kraft", "archive"]},
    "cinematography": [
        ("restrained", "Mostly still frames; the camera only moves to follow an argument (a push on the fact that matters)",
         {"default": "still", "maps": "push", "data": "still", "evidence": "still", "people": "still", "3d": "orbit"}),
        ("drifting", "A slow lateral drift on everything, as if the camera is walking past the evidence",
         {"default": "drift", "maps": "drift", "data": "drift", "evidence": "still", "people": "drift", "3d": "orbit"}),
        ("investigative", "Push in on evidence and on the detail being circled, pull back on maps to give context",
         {"default": "push", "maps": "pull", "data": "push", "evidence": "focus", "people": "push", "3d": "orbit"}),
        ("breathing", "Alternating pull and push, slow, so the frame seems to breathe with the narration",
         {"default": "pull", "maps": "push", "data": "pull", "evidence": "still", "people": "pull", "3d": "orbit"})],
    "maps": [("atlas", "Engraved atlas: pale hatched sea, cream land, serif place names", "atlas"),
             ("marker", "Paper map with red marker: hatching, hand-drawn routes and circles", "pen"),
             ("relief", "Real terrain and measured outlines first; flat maps only for context", "relief")],
    "infographics": [("objects", "Charts built from the things themselves: coins, figures, ships", "objects"),
                     ("editorial", "Clean editorial charts: thin rules, one accent, big numbers", "flat"),
                     ("dimensional", "Data in light and shadow: 3D bars and maps where the size is the story", "3d")],
    "animation": [("hand", "Drawn graphics step at 12 frames a second, the hand-made cadence", True),
                  ("fluid", "Everything moves at the full frame rate, smooth and measured", False)],
    "rhythm": [("measured", "Long holds on evidence; a full breath after every line", 1.25),
               ("brisk", "Short gaps, cuts on the word, the film keeps moving", 0.8),
               ("tidal", "Fast when the story builds, slow when it lands", 1.0)],
    "grade": [("warm", "A warm print: lifted reds, held-back blues, soft vignette"),
              ("cool", "Cool and clear: a steel tint for distance and evidence"),
              ("bleach", "Bleach bypass: high contrast, low saturation, for hard stories"),
              ("neutral", "Neutral: the pictures as they are, only matched to each other")],
    "music": [("drone", "Low sustained drones that change key with each act"),
              ("pulse", "A soft pulse under the investigation, released at the turn"),
              ("sparse", "Near silence; music only at the opening, the turn and the end")],
}


def _pick(options: list, used: list, seed: int):
    """An option the last films did not use: the window is one shorter than the number of options, so there is
    always a fresh one and no treatment comes back until the others have had their turn."""
    window = [u for u in used[-max(1, len(options) - 1):] if u]
    fresh = [o for o in options if (o[0] if isinstance(o, tuple) else o) not in window]
    pool = fresh or options
    return pool[seed % len(pool)]


def _history_file(data_dir: Path) -> Path:
    return Path(data_dir) / "studio_history.json"


_lock = threading.Lock()


def history(data_dir: Path) -> list[dict]:
    try:
        h = json.loads(_history_file(data_dir).read_text(encoding="utf-8"))
        return h if isinstance(h, list) else []
    except (OSError, ValueError):
        return []


def remember(data_dir: Path, entry: dict) -> None:
    with _lock:
        h = [x for x in history(data_dir) if x.get("id") != entry.get("id")] + [entry]
        p = _history_file(data_dir)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(h[-60:], ensure_ascii=False, indent=1), encoding="utf-8")


def direct(film_id: str, title: str, genre: str, concept: dict, scenes: list[dict], hist: list[dict],
           overrides: dict | None = None) -> dict:
    """The art direction for one film. `scenes` are the screenplay's scenes (their graphics show what the film is
    made of); `hist` the studio history; `overrides` the writer's own choices, which always win."""
    from ..media import vox
    genre = genre if genre in GENRES else "investigation"
    seed = zlib.crc32(f"{film_id}|{title}".encode())
    recent = hist[-8:]
    used = {ax: [h.get(ax) for h in recent] for ax in ("look", "cinematography", "maps", "infographics", "animation", "rhythm", "music", "accent")}
    # the genre's looks first; once those have all had a turn, any look the last films did not use
    looks = [x for x in AXES["look"][genre] if x in vox.LOOKS] or list(vox.LOOKS)
    if all(x in used["look"][-2:] for x in looks):
        looks = [x for x in vox.LOOKS if x not in used["look"][-3:]] or looks
    look = _pick(looks, used["look"], seed)
    accents = [a for a in vox.ACCENTS if a != "yellow"] + ["yellow"]
    accent = _pick(accents, used["accent"] + [vox.LOOKS[look]["accent"]], seed >> 3)
    cine = _pick(AXES["cinematography"], used["cinematography"], seed >> 5)
    maps = _pick(AXES["maps"], used["maps"], seed >> 7)
    info = _pick(AXES["infographics"], used["infographics"], seed >> 9)
    anim = _pick(AXES["animation"], used["animation"], seed >> 11)
    rhythm = _pick(AXES["rhythm"], used["rhythm"], seed >> 13)
    music = _pick(AXES["music"], used["music"], seed >> 15)
    grade = _pick(AXES["grade"], [h.get("grade") for h in recent], seed >> 17)
    ov = overrides or {}
    look = ov.get("look", look) if ov.get("look") in vox.LOOKS else look
    accent = ov.get("accent", accent)
    L = vox.LOOKS[look]
    kinds = [str(s.get("graphic", "")).split(":", 1)[0].strip().lower() for s in scenes]
    opening = next((s for s in scenes if s.get("role") == "opening"), scenes[0] if scenes else {})
    climax = next((s for s in scenes if s.get("role") == "climax"), {})
    ending = next((s for s in reversed(scenes) if s.get("role") == "ending"), scenes[-1] if scenes else {})

    def what(s):
        return str(s.get("graphic", "")).split("|")[0].strip() or "-"
    doc = {
        "id": film_id, "title": title, "genre": genre,
        "identity": f"{title}: {concept.get('logline', '')}".strip(": "),
        "narrative_approach": concept.get("structure", "investigative") + " - " + concept.get("structure_note", "built around one question: "
                                                                                                + concept.get("central_question", "")),
        "visual_concept": concept.get("visual_concept") or f"The {genre} story told through {maps[1].split(':')[0].lower()} maps and "
                                                           f"{info[1].split(':')[0].lower()}, on {look} paper",
        "look": look, "accent": accent,
        "palette": {"paper": L["paper"], "ink": "#141414", "accent": vox.ACCENTS.get(accent, accent), "marker": L["mark"],
                    "sea": L["sea"], "land": L["land"]},
        "typography": {"headlines": L["head"], "figures": L["big"], "notes": L["hand"], "labels": "Inter", "sources": "JetBrains Mono",
                       "hindi": "Rozha One / Teko / Mukta under the same roles"},
        "cinematography": cine[0], "cinematography_note": cine[1], "camera_policy": cine[2],
        "maps": maps[0], "maps_note": maps[1], "map_style": maps[2],
        "infographics": info[0], "infographics_note": info[1], "chart_style": info[2],
        "animation": anim[0], "animation_note": anim[1], "stepped": anim[2],
        "footage_strategy": concept.get("footage_strategy") or ("Real photographs and archive footage where a licence allows; "
                                                                "every reconstruction is drawn and labelled as one"),
        "sound": f"{music[1]}; ambience follows each place (sea, wind, room, paper)", "music": music[0],
        "rhythm": rhythm[0], "rhythm_note": rhythm[1], "breath": rhythm[2],
        "grade": grade[0], "grade_note": grade[1],
        "opening_sequence": f"{what(opening)}: {opening.get('narration', '')[:90]}",
        "visual_climax": f"{what(climax)}: {climax.get('narration', '')[:90]}" if climax else "-",
        "ending_sequence": f"{what(ending)}: {ending.get('narration', '')[:90]}",
        "graphics_used": sorted(set(k for k in kinds if k)),
    }
    return doc


def camera_for(doc: dict, kind: str) -> str:
    """The shot's camera from the film's policy (a scene's own camera wins)."""
    pol = doc.get("camera_policy", {})
    if kind in ("pinmap", "route", "heatmap", "arrows", "railmap", "borders", "shrink", "sizemap", "morph"):
        return pol.get("maps", "push")
    if kind in ("stack", "trend", "slice", "bignumber", "table", "pyramid", "polltrack", "area", "candles", "flowchart", "orgchart",
                "linkmap", "seats", "stand", "compare"):
        return pol.get("data", "push")
    if kind in ("courtdoc", "newscard", "clipping", "desk", "pinboard", "reveal"):
        return pol.get("evidence", "still")
    if kind in ("interview", "hero"):
        return pol.get("people", "push")
    return pol.get("default", "push")


def to_markdown(doc: dict) -> str:
    rows = [("1. Documentary identity", doc["identity"]), ("2. Narrative approach", doc["narrative_approach"]),
            ("3. Visual concept", doc["visual_concept"]),
            ("4. Colour palette", ", ".join(f"{k} {v}" for k, v in doc["palette"].items()) + f" (look: {doc['look']})"),
            ("5. Typography", ", ".join(f"{k}: {v}" for k, v in doc["typography"].items())),
            ("6. Cinematography", f"{doc['cinematography']}: {doc['cinematography_note']}"),
            ("7. Map treatment", f"{doc['maps']}: {doc['maps_note']}"),
            ("8. Infographic treatment", f"{doc['infographics']}: {doc['infographics_note']}"),
            ("9. Animation style", f"{doc['animation']}: {doc['animation_note']}"),
            ("10. Footage strategy", doc["footage_strategy"]), ("11. Sound design", doc["sound"]),
            ("12. Editing rhythm", f"{doc['rhythm']}: {doc['rhythm_note']}"), ("12b. Colour grade", f"{doc['grade']}: {doc['grade_note']}"), ("13. Opening sequence", doc["opening_sequence"]),
            ("14. Visual climax", doc["visual_climax"]), ("15. Ending sequence", doc["ending_sequence"])]
    return "\n".join([f"# Art direction: {doc['title']}", ""] + [f"## {a}\n\n{b}\n" for a, b in rows] +
                     ["## Graphics in this film", "", ", ".join(doc["graphics_used"]), ""])
