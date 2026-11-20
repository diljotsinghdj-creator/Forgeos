#!/usr/bin/env python3
"""Rank visual modes for each beat of a script: the first pass of the visual decision engine.

Usage:
  python3 visual_decide.py beats.json --domain geography economics [--avoid map_globe chart] [--out decisions.md]

beats.json: [{"id": "S1", "narration": "...", "need": "<need>", "have_evidence": true|false}, ...]
  need is one of NEEDS below (what the line asks the viewer to understand).
  have_evidence: a real photo / footage / document for this exact line is known to exist.

It only proposes. The producer still writes why_this_visual for every scene and may overrule it, with a reason.
The rules behind the table are in references/visual_decision_engine.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# need -> candidate modes, best first (craft defaults, before subject and history adjust them)
NEEDS = {
    "specific_place": ["map_globe", "satellite", "location_footage", "archival_photo", "map_2d"],
    "route_or_movement": ["map_route", "map_2d", "satellite", "process_animation"],
    "scale_or_size": ["scale_comparison", "3d_model", "unit_chart", "map_2d", "big_number"],
    "single_number": ["big_number", "unit_chart", "kinetic_type", "photo_annotated"],
    "comparison": ["split_screen", "chart", "unit_chart", "scale_comparison", "table"],
    "change_over_time": ["chart", "timeline", "satellite", "map_2d", "split_screen"],
    "share_of_whole": ["unit_chart", "data_viz", "chart"],
    "geographic_distribution": ["map_2d", "data_viz", "map_globe"],
    "sequence_of_events": ["timeline", "archival_footage", "news_footage", "collage"],
    "causal_mechanism": ["diagram", "process_animation", "flowchart", "visual_metaphor"],
    "system_or_network": ["network", "flowchart", "diagram", "map_route"],
    "institution": ["diagram", "flowchart", "official_record", "location_footage"],
    "physical_process": ["process_animation", "3d_model", "simulation", "location_footage"],
    "invisible_process": ["simulation", "process_animation", "3d_model", "visual_metaphor", "illustration"],
    "real_person": ["archival_photo", "news_footage", "interview", "quote_card"],
    "real_event": ["news_footage", "archival_footage", "archival_photo", "newspaper", "satellite"],
    "document_claim": ["document_annotated", "official_record", "screenshot", "newspaper"],
    "quote": ["quote_card", "document_annotated", "interview", "newspaper"],
    "abstract_concept": ["visual_metaphor", "illustration", "diagram", "collage", "kinetic_type"],
    "human_consequence": ["location_footage", "archival_photo", "interview", "news_footage"],
    "interface_behaviour": ["screenshot", "ui_recreation", "process_animation"],
    "historical_moment": ["archival_photo", "archival_footage", "newspaper", "map_2d", "collage"],
    "hypothetical": ["illustrated_scene", "simulation", "visual_metaphor", "diagram"],
    "definition": ["kinetic_type", "diagram", "illustration", "notation"],
    "sound_or_music": ["notation", "diagram", "archival_footage", "kinetic_type"],
    "emotional_beat": ["location_footage", "archival_photo", "texture_plate", "kinetic_type"],
}
# the subject's native material: modes that belong to each domain get a lift
DOMAIN = {
    "geography": ["map_globe", "map_2d", "map_route", "satellite", "location_footage", "scale_comparison"],
    "economics": ["chart", "data_viz", "unit_chart", "big_number", "flowchart", "document_annotated", "table"],
    "history": ["archival_photo", "archival_footage", "newspaper", "timeline", "map_2d", "document_annotated"],
    "technology": ["ui_recreation", "screenshot", "3d_model", "process_animation", "diagram", "network"],
    "science": ["simulation", "process_animation", "3d_model", "diagram", "scale_comparison", "illustration"],
    "politics": ["news_footage", "official_record", "document_annotated", "map_2d", "chart", "quote_card"],
    "culture": ["archival_footage", "collage", "kinetic_type", "notation", "split_screen", "archival_photo"],
    "psychology": ["illustrated_scene", "visual_metaphor", "diagram", "ui_recreation", "kinetic_type", "chart"],
    "human-interest": ["location_footage", "interview", "archival_photo", "document", "map_2d"],
    "investigative": ["document_annotated", "official_record", "satellite", "map_route", "network", "screenshot"],
}
EVIDENCE = {"archival_photo", "archival_footage", "location_footage", "news_footage", "document", "newspaper",
            "screenshot", "satellite", "official_record", "interview", "photo_annotated", "document_annotated"}


def rank(beat: dict, domains: list[str], avoid: set[str], prev: str | None) -> list[tuple[str, float, list[str]]]:
    need = beat.get("need", "")
    base = NEEDS.get(need)
    if not base:
        return [("?", 0, [f"unknown need '{need}'; choose from: {', '.join(NEEDS)}"])]
    native = {m for d in domains for m in DOMAIN.get(d, [])}
    out = []
    pool = list(dict.fromkeys(base + [m for m in native if m not in base]))
    for m in pool:
        why, score = [], 0.0
        if m in base:
            score += 10 - base.index(m) * 1.5
            why.append(f"fits '{need}'")
        if m in native:
            score += 3
            why.append("native to the subject")
        if m in EVIDENCE:
            if beat.get("have_evidence"):
                score += 3
                why.append("real material exists: evidence beats explanation")
            else:
                score -= 4
                why.append("needs real material not yet found")
        if m in avoid:
            score -= 5
            why.append("lead of a recent film: rotate")
        if m == prev:
            score -= 3
            why.append("same as the previous shot")
        if m in ("stock_footage", "stock_photo"):
            score -= 6
        out.append((m, score, why))
    out.sort(key=lambda t: -t[1])
    return out[:4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("beats")
    ap.add_argument("--domain", nargs="+", default=[])
    ap.add_argument("--avoid", nargs="*", default=[])
    ap.add_argument("--out")
    a = ap.parse_args()
    beats = json.loads(Path(a.beats).read_text())
    lines = ["# Visual decisions (first pass)", "", f"Domains: {', '.join(a.domain) or '-'} · rotate away from: "
             f"{', '.join(a.avoid) or '-'}", ""]
    prev = None
    for b in beats:
        r = rank(b, a.domain, set(a.avoid), prev)
        prev = r[0][0]
        lines.append(f"## {b.get('id')} · need: {b.get('need')}")
        lines.append(f"> {b.get('narration', '')}")
        for m, sc, why in r:
            lines.append(f"- **{m}** ({sc:.1f}): {'; '.join(why)}")
        lines.append("")
    text = "\n".join(lines)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
