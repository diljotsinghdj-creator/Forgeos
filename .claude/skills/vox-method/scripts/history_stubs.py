#!/usr/bin/env python3
"""Build comparison stubs of recent films from CreatorForge's studio history, for blueprint_check.py --compare.

Usage:
  python3 history_stubs.py --repo /home/user/Forgeos --out ./compare_stubs [--last 3]
  python3 blueprint_check.py blueprint.json --compare compare_stubs/1_*.json compare_stubs/2_*.json compare_stubs/3_*.json

Sources, newest first:
  1. creatorforge/channels/blueprints/*.json: real blueprints saved when a film was shown to the owner (best);
  2. creatorforge/channels/studio_history/variation_ledger.json + SEEN.json: the studio's own records, mapped onto
     this skill's vocabulary (approximate, because the studio's kinds and ours differ).
Stubs carry only what the sameness check reads: engine, lead technique, opening, transition family, texture, accent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# studio vocabulary -> this skill's visual modes (approximate)
KIND = {
    "bignumber": "big_number", "counter": "big_number", "number": "big_number", "hero": "big_number",
    "footage": "news_footage", "photo": "archival_photo", "photos": "archival_photo", "photo3d": "archival_photo",
    "satellite": "satellite", "document": "document", "courtdoc": "document", "article": "newspaper",
    "newscard": "newspaper", "clipping": "newspaper", "arrows": "map_route", "route": "map_route", "flowmap": "map_route",
    "pinmap": "map_2d", "borders": "map_2d", "heatmap": "map_2d", "sizemap": "scale_comparison", "fly": "map_globe",
    "globe": "map_globe", "chat": "ui_recreation", "social": "ui_recreation", "search": "ui_recreation",
    "reel": "ui_recreation", "statement": "kinetic_type", "quote": "quote_card", "opener": "title_card",
    "timeline": "timeline", "flowchart": "flowchart", "orgchart": "diagram", "planets": "3d_model",
    "terrain3d": "3d_model", "squares": "unit_chart", "grids": "unit_chart", "units": "unit_chart",
    "chart": "chart", "columns": "chart", "trend": "chart", "pie": "unit_chart", "table": "table",
}
LEAD = {"data": "chart", "3d": "3d_model", "maps": "map_2d", "map": "map_2d", "documents": "document_annotated",
        "document": "document_annotated", "collage": "collage", "illustration": "illustration", "photos": "archival_photo",
        "archive": "archival_photo", "footage": "news_footage", "typography": "kinetic_type", "ui": "ui_recreation"}
FAMILY = {"camera moves": "push_through", "hard cuts": "cut", "cuts": "cut", "paper": "paper_tear",
          "morph": "morph", "shape-morph": "morph", "wipes": "mask_wipe", "map": "map_fly", "dissolves": "dissolve"}


def from_ledger(repo: Path, last: int) -> list[dict]:
    hist = repo / "creatorforge/channels/studio_history/variation_ledger.json"
    seen_f = repo / "creatorforge/channels/SEEN.json"
    ledger = json.loads(hist.read_text()) if hist.exists() else []
    seen = {e.get("id"): e for e in (json.loads(seen_f.read_text()) if seen_f.exists() else [])}
    out = []
    for e in reversed(ledger[-last:] if ledger else []):
        s = seen.get(e.get("film"), {})
        opening = KIND.get(str(e.get("opening", "")).lower(), str(e.get("opening", "")))
        out.append({"title": e.get("film"), "engine": s.get("engine", ""), "source": "studio ledger (approximate)",
                    "dna": {"lead_technique": LEAD.get(str(e.get("lead", "")).lower(), e.get("lead", "")),
                            "opening_shot": opening,
                            "transition_family": FAMILY.get(str(e.get("family", "")).lower(), e.get("family", "")),
                            "texture": s.get("look", ""), "signature_device": "",
                            "palette": {"accent": e.get("accent", "")}},
                    "scenes": [{"visual_mode": opening}]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="compare_stubs")
    ap.add_argument("--last", type=int, default=3)
    a = ap.parse_args()
    repo, out = Path(a.repo), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    saved = sorted((repo / "creatorforge/channels/blueprints").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    stubs = [json.loads(p.read_text()) for p in saved[:a.last]]
    if len(stubs) < a.last:
        stubs += from_ledger(repo, a.last)[: a.last - len(stubs)]
    for i, s in enumerate(stubs, 1):
        name = f"{i}_{str(s.get('title', 'film')).replace('/', '-').replace(' ', '-')[:40]}.json"
        (out / name).write_text(json.dumps(s, indent=1))
        print(f"{out / name}  ({s.get('source', 'saved blueprint')})")
    if not stubs:
        print("no history found: nothing to compare against")


if __name__ == "__main__":
    main()
