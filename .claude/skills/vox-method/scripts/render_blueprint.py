#!/usr/bin/env python3
"""Turn blueprint.json into the human-readable production blueprint (blueprint.md).

Usage: python3 render_blueprint.py blueprint.json [-o blueprint.md]

The markdown has: the film card (question, answer, engine, DNA), the chapter map, one scene card per shot,
then three department sheets derived from the scenes (asset pull list, music and sound cue sheet, edit list).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def ts(x) -> str:
    x = float(x)
    return f"{int(x // 60)}:{x % 60:04.1f}"


def snd(s) -> str:
    if isinstance(s, dict):
        parts = [f"{k}: {v}" for k, v in s.items() if v not in (None, "", False)]
        return "; ".join(parts) or "-"
    return str(s or "-")


def tr(t) -> str:
    if isinstance(t, dict):
        return f"{t.get('family', '')}" + (f" ({t['cause']})" if t.get("cause") else "")
    return str(t or "-")


def render(bp: dict) -> str:
    d = bp.get("dna", {})
    pal = d.get("palette", {})
    L = [f"# {bp.get('title', 'Untitled')}: production blueprint", ""]
    L += [f"**Channel:** {bp.get('channel', '')} · **Runtime target:** {bp.get('runtime_target_s', '?')} s · "
          f"**Engine:** {bp.get('engine', '')}", "",
          f"**Central question:** {bp.get('central_question', '')}", "",
          f"**Answer:** {bp.get('answer', '')}", "",
          f"**Why now:** {bp.get('why_now', '')}", ""]
    h = bp.get("hook", {})
    L += [f"**Hook ({h.get('mechanism', '')}):** first frame {h.get('first_frame', '')}; first line “{h.get('line', '')}”", ""]
    L += ["## Video DNA", "", "| | |", "|---|---|"]
    for k in ("lead_technique", "support_technique", "typography", "texture", "motion_language", "transition_family",
              "sound_palette", "opening_shot", "signature_device"):
        L.append(f"| {k.replace('_', ' ')} | {d.get(k, '')} |")
    L.append(f"| palette | base {pal.get('base', '')} · accent {pal.get('accent', '')} · signal {pal.get('signal', '')} "
             f"({pal.get('from_subject', '')}) |")
    L += ["", "## Chapter map", "", "| # | Title | Job | Open loop into next |", "|---|---|---|---|"]
    for c in bp.get("chapters", []):
        L.append(f"| {c.get('id')} | {c.get('title')} | {c.get('job')} | {c.get('open_loop', '')} |")
    L += ["", "## Scene cards", ""]
    for s in bp.get("scenes", []):
        L += [f"### {s.get('id')} · {ts(s.get('start', 0))}–{ts(s.get('end', 0))} · {s.get('visual_mode')} · {s.get('purpose')}"
              + (f" · **{s['badge']}**" if s.get("badge") else ""), "",
              f"> {s.get('narration', '')}", "",
              f"- **Viewer understands:** {s.get('viewer_understands', '')}",
              f"- **On screen:** {s.get('visual', '')}",
              f"- **Why this visual:** {s.get('why_this_visual', '')}"
              + (f" (rejected: {', '.join(s['alternatives'])})" if s.get("alternatives") else ""),
              f"- **Motion:** {s.get('motion', '')}",
              f"- **Text:** {s.get('on_screen_text', '')}",
              f"- **Sound:** {snd(s.get('sound'))}",
              f"- **Out:** {tr(s.get('transition_out'))}",
              f"- **Claims:** {', '.join(s.get('claim_ids', []) or ['-'])} · **Assets:** "
              f"{', '.join(s.get('asset_ids', []) or []) or s.get('asset_needed', '-')}", ""]
    L += ["## Asset pull list", "", "| Scene | Mode | Have | Need |", "|---|---|---|---|"]
    for s in bp.get("scenes", []):
        if s.get("asset_ids") or s.get("asset_needed"):
            L.append(f"| {s.get('id')} | {s.get('visual_mode')} | {', '.join(s.get('asset_ids', []) or [])} | "
                     f"{s.get('asset_needed', '')} |")
    L += ["", "## Music and sound cue sheet", "", "| In | Scene | Music | SFX | Ambience | Silence |", "|---|---|---|---|---|---|"]
    for s in bp.get("scenes", []):
        so = s.get("sound") or {}
        if isinstance(so, dict):
            L.append(f"| {ts(s.get('start', 0))} | {s.get('id')} | {so.get('music', '')} | {so.get('sfx', '')} | "
                     f"{so.get('ambience', '')} | {'yes' if so.get('silence') else ''} |")
    L += ["", "## Edit list", "", "| # | In | Out | Hold | Mode | Transition out |", "|---|---|---|---|---|---|"]
    for i, s in enumerate(bp.get("scenes", []), 1):
        L.append(f"| {i} | {ts(s.get('start', 0))} | {ts(s.get('end', 0))} | {float(s.get('end', 0)) - float(s.get('start', 0)):.1f}s | "
                 f"{s.get('visual_mode')} | {tr(s.get('transition_out'))} |")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blueprint")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    bp = json.loads(Path(a.blueprint).read_text())
    out = Path(a.out) if a.out else Path(a.blueprint).with_suffix(".md")
    out.write_text(render(bp), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
