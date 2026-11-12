#!/usr/bin/env python3
"""Lint a production blueprint (blueprint.json) before anyone draws, records or renders from it.

Usage:
  python3 blueprint_check.py blueprint.json                    # CreatorForge house rules (default)
  python3 blueprint_check.py blueprint.json --profile generic  # craft rules only
  python3 blueprint_check.py blueprint.json --compare other.json [other2.json ...]   # sameness vs earlier films
  python3 blueprint_check.py blueprint.json --json             # machine-readable report

Exit code 0 = no errors (warnings allowed), 1 = errors, 2 = unreadable input.
Standard library only. The schema is described in references/production_workflow.md and
assets/templates/blueprint.json.
"""
from __future__ import annotations

import argparse
import colorsys
import json
import re
import statistics
import sys
from pathlib import Path

# ---- the visual-mode vocabulary (references/visual_decision_engine.md) -----------------------------------------------
# role: evidence = real material that proves; explain = a graphic that explains; recreation = a labelled rebuild;
# atmosphere = mood/context; text = type-led frames. hold: still frames hold one picture, build frames assemble on screen.
MODES = {
    # evidence
    "archival_photo": ("evidence", "still"), "archival_footage": ("evidence", "build"),
    "location_footage": ("evidence", "build"), "news_footage": ("evidence", "build"),
    "document": ("evidence", "still"), "newspaper": ("evidence", "still"), "screenshot": ("evidence", "still"),
    "satellite": ("evidence", "build"), "official_record": ("evidence", "still"), "interview": ("evidence", "build"),
    "photo_annotated": ("evidence", "build"), "document_annotated": ("evidence", "build"),
    # explain
    "map_2d": ("explain", "build"), "map_globe": ("explain", "build"), "map_route": ("explain", "build"),
    "chart": ("explain", "build"), "data_viz": ("explain", "build"), "unit_chart": ("explain", "build"),
    "big_number": ("explain", "build"), "timeline": ("explain", "build"), "diagram": ("explain", "build"),
    "flowchart": ("explain", "build"), "network": ("explain", "build"), "process_animation": ("explain", "build"),
    "3d_model": ("explain", "build"), "simulation": ("explain", "build"), "scale_comparison": ("explain", "build"),
    "split_screen": ("explain", "build"), "illustration": ("explain", "build"), "collage": ("explain", "build"),
    "visual_metaphor": ("explain", "build"), "notation": ("explain", "build"), "table": ("explain", "build"),
    # recreation (must carry a RECREATION / ILLUSTRATIVE badge)
    "ui_recreation": ("recreation", "build"), "reenactment": ("recreation", "build"),
    "illustrated_scene": ("recreation", "build"),
    # atmosphere
    "stock_footage": ("atmosphere", "build"), "stock_photo": ("atmosphere", "still"), "texture_plate": ("atmosphere", "still"),
    # text-led
    "kinetic_type": ("text", "build"), "quote_card": ("text", "still"), "title_card": ("text", "still"),
    "chapter_card": ("text", "still"), "end_card": ("text", "still"),
}
PURPOSES = {"hook", "inform", "context", "prove", "emotion", "turn", "payoff", "transition"}
BADGES = {"", "VERIFIED", "REPORTED", "ESTIMATE", "DISPUTED", "ALLEGATION", "PARTY CLAIM", "OPINION",
          "ILLUSTRATIVE", "RECREATION", "ILLUSTRATION · OPINION"}
TRANSITION_FAMILIES = {"cut", "match_cut", "whip", "push_through", "zoom_through", "mask_wipe", "paper_tear",
                       "map_fly", "morph", "dissolve", "dip", "graphic_match", "j_cut", "l_cut", "smash_cut", "hold_black"}
SCENE_FIELDS = ("id", "start", "end", "narration", "viewer_understands", "purpose", "visual_mode", "visual",
                "why_this_visual", "motion", "on_screen_text", "sound", "transition_out")
TOP_FIELDS = ("title", "channel", "central_question", "answer", "hook", "dna", "chapters", "scenes")
DNA_FIELDS = ("lead_technique", "support_technique", "palette", "typography", "motion_language", "transition_family",
              "sound_palette", "texture", "opening_shot", "signature_device")
BANNED = ("delve", "delving", "testament to", "moreover", "in a world where", "it's important to remember",
          "it is important to remember", "let's unpack", "lets unpack", "buckle up", "game-changer", "game changer",
          "unlock the secrets", "in today's fast-paced", "navigate the complexities", "tapestry")
SIGNATURE_YELLOW = "#FFDD33"
NUM_RE = re.compile(r"(?<![\w#])(\d[\d,.]*\s*(%|percent|million|billion|trillion|crore|lakh|km|miles|years?)?)", re.I)

HOUSE = {"max_still": 4.5, "max_build": 7.0, "last_extra": 1.5, "max_mean": 5.0, "interrupt_every": 20.0,
         "stock_share": 0.25, "effect_max": 3, "min_modes": 5, "max_mode_share": 0.40}
GENERIC = {"max_still": 6.0, "max_build": 10.0, "last_extra": 2.0, "max_mean": 6.5, "interrupt_every": 20.0,
           "stock_share": 0.25, "effect_max": 3, "min_modes": 4, "max_mode_share": 0.45}


def hue(hexcol: str) -> float | None:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(hexcol).strip())
    if not m:
        return None
    r, g, b = (int(m.group(1)[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    return None if s < 0.15 else h * 360


def hue_gap(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


class Report:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, level: str, where: str, msg: str):
        self.items.append({"level": level, "where": where, "msg": msg})

    @property
    def errors(self):
        return [i for i in self.items if i["level"] == "error"]


def check(bp: dict, prof: dict, house: bool, rep: Report) -> dict:
    for f in TOP_FIELDS:
        if not bp.get(f):
            rep.add("error", "top", f"missing '{f}'")
    dna = bp.get("dna") or {}
    for f in DNA_FIELDS:
        if not dna.get(f):
            rep.add("error", "dna", f"missing dna.{f}: every film declares its own identity")
    pal = dna.get("palette") or {}
    if house:
        ch = bp.get("channel", "")
        if ch not in ("print-facts", "dragon-psychology"):
            rep.add("error", "top", "channel must be print-facts or dragon-psychology")
        pick = bp.get("pick") or {}
        if not (pick.get("engine") and len(pick.get("pitched", [])) == 3):
            rep.add("error", "top", "gate 1: no recorded pick of one of three pitched engines (pick.engine, pick.pitched[3])")
        if str(pal.get("signal", "")).upper() != SIGNATURE_YELLOW:
            rep.add("error", "dna.palette", f"signal must be the signature yellow {SIGNATURE_YELLOW}")
        acc = hue(pal.get("accent", ""))
        if acc is not None and hue_gap(acc, hue(SIGNATURE_YELLOW)) < 30:
            rep.add("error", "dna.palette", "accent sits too close to the signature yellow (keep it 30°+ away)")
        if bp.get("language", "en") != "en":
            rep.add("error", "top", "all videos are in English")

    scenes = bp.get("scenes") or []
    holds, modes_time, kinds = [], {}, []
    last_change_t, last_mode = 0.0, None
    effects: dict[str, int] = {}
    first_evidence = first_explain = None
    prev_end = 0.0
    total = 0.0
    trans_prev = None
    for i, s in enumerate(scenes):
        sid = str(s.get("id", f"#{i + 1}"))
        for f in SCENE_FIELDS:
            if s.get(f) in (None, "", []):
                rep.add("error", sid, f"missing '{f}'")
        try:
            st, en = float(s.get("start", 0)), float(s.get("end", 0))
        except (TypeError, ValueError):
            rep.add("error", sid, "start/end must be numbers (seconds)")
            continue
        d = en - st
        if d <= 0:
            rep.add("error", sid, "end must be after start")
            continue
        if abs(st - prev_end) > 0.05:
            rep.add("warning", sid, f"gap or overlap: starts at {st:.2f}s, previous ended {prev_end:.2f}s")
        prev_end, total = en, max(total, en)
        mode = s.get("visual_mode", "")
        if mode not in MODES:
            rep.add("error", sid, f"unknown visual_mode '{mode}' (see references/visual_decision_engine.md)")
            role, hold = "explain", "build"
        else:
            role, hold = MODES[mode]
        kinds.append(mode)
        holds.append(d)
        cap = (prof["max_still"] if hold == "still" else prof["max_build"]) + (prof["last_extra"] if i == len(scenes) - 1 else 0)
        if d > cap + 0.05:
            rep.add("error", sid, f"pacing: '{mode}' holds {d:.1f}s (max {cap:.1f}s for a {hold} shot); split the line")
        modes_time[mode] = modes_time.get(mode, 0) + d
        if mode != last_mode:
            last_change_t, last_mode = st, mode
        elif en - last_change_t > prof["interrupt_every"]:
            rep.add("error", sid, f"no pattern interrupt for {en - last_change_t:.0f}s (same visual_mode '{mode}')")
            last_change_t = en
        if s.get("purpose") and s["purpose"] not in PURPOSES:
            rep.add("error", sid, f"purpose must be one of {sorted(PURPOSES)}")
        badge = str(s.get("badge", "") or "").upper()
        if badge not in BADGES:
            rep.add("warning", sid, f"unusual badge '{badge}'")
        if role == "recreation" and badge not in ("RECREATION", "ILLUSTRATIVE", "ILLUSTRATION · OPINION"):
            rep.add("error", sid, f"'{mode}' is a recreation: it needs a RECREATION or ILLUSTRATIVE badge")
        if mode in ("stock_footage", "stock_photo") and s.get("depicts_specific") and badge != "ILLUSTRATIVE":
            rep.add("error", sid, "generic stock standing in for a specific place/event must be badged ILLUSTRATIVE")
        if role == "evidence" and first_evidence is None:
            first_evidence = i
        if role == "explain" and first_explain is None:
            first_explain = i
        if role == "evidence" and not (s.get("asset_ids") or s.get("asset_needed")):
            rep.add("error", sid, "evidence shot names no asset (asset_ids) or acquisition need (asset_needed)")
        narr = str(s.get("narration", ""))
        low = narr.lower()
        for ph in BANNED:
            if re.search(rf"(?<![a-z]){re.escape(ph)}(?![a-z])", low):
                rep.add("error", sid, f"banned phrase '{ph}'")
        nums = [m.group(1) for m in NUM_RE.finditer(narr) if not re.fullmatch(r"(19|20)\d\d", m.group(1).strip())]
        if nums and not s.get("claim_ids"):
            rep.add("error", sid, f"narration states {nums[0]!r} but cites no dossier claim (claim_ids)")
        if nums and not s.get("on_screen_text"):
            rep.add("warning", sid, "a figure is spoken but nothing is on screen (mute test)")
        for fx in s.get("effects", []) or []:
            effects[fx] = effects.get(fx, 0) + 1
        snd = s.get("sound") or {}
        if isinstance(snd, str):
            rep.add("warning", sid, "sound should be an object {music, sfx, ambience, silence}")
        tr = s.get("transition_out") or {}
        fam = tr.get("family") if isinstance(tr, dict) else str(tr)
        if fam and fam not in TRANSITION_FAMILIES:
            rep.add("warning", sid, f"unknown transition family '{fam}'")
        if fam in ("cut",) and trans_prev == "cut" and not (isinstance(tr, dict) and tr.get("cause")):
            rep.add("warning", sid, "two plain cuts in a row without a stated cause")
        trans_prev = fam

    if house and bp.get("channel") == "print-facts" and first_explain is not None:
        if first_evidence is None or first_evidence > first_explain:
            w = bp.get("evidence_waiver") or {}
            if w.get("reason") and w.get("told_owner"):
                rep.add("warning", "gate 3", f"evidence-first waived: {w['reason']}")
            else:
                rep.add("error", "gate 3", f"scene {first_explain + 1} explains before any real evidence is shown")
    if holds and statistics.mean(holds) > prof["max_mean"] + 0.05:
        rep.add("error", "pacing", f"average hold {statistics.mean(holds):.1f}s (max {prof['max_mean']:.1f}s)")
    if total:
        stock = sum(v for k, v in modes_time.items() if k in ("stock_footage", "stock_photo"))
        if stock / total > prof["stock_share"]:
            rep.add("error", "mix", f"stock is {stock / total:.0%} of runtime (max {prof['stock_share']:.0%})")
        distinct = len(modes_time)
        if distinct < prof["min_modes"]:
            rep.add("error", "mix", f"only {distinct} visual modes; a documentary needs at least {prof['min_modes']}")
        top_mode, top_t = max(modes_time.items(), key=lambda kv: kv[1])
        if top_t / total > prof["max_mode_share"] and top_mode != dna.get("lead_technique"):
            rep.add("warning", "mix", f"'{top_mode}' fills {top_t / total:.0%} of runtime but is not the declared lead")
        if top_t / total > 0.60:
            rep.add("error", "mix", f"'{top_mode}' fills {top_t / total:.0%} of runtime: one formula, not a film")
        lead = dna.get("lead_technique")
        if lead and lead in MODES and modes_time.get(lead, 0) == 0:
            rep.add("error", "dna", f"declared lead technique '{lead}' never appears in the scenes")
    for fx, n in effects.items():
        if n > prof["effect_max"]:
            rep.add("error", "effects", f"effect '{fx}' used {n} times (max {prof['effect_max']})")
    if scenes:
        s0 = scenes[0]
        if float(s0.get("end", 99)) > 5.5 and s0.get("purpose") != "hook":
            rep.add("warning", "hook", "the first scene is not a hook landing inside 5 s")
        if s0.get("visual_mode") in ("title_card", "chapter_card", "end_card"):
            rep.add("error", "hook", "the film opens on a title card: open on the subject")
    ch_ids = {c.get("id") for c in bp.get("chapters", []) if isinstance(c, dict)}
    if ch_ids and any(s.get("chapter") not in ch_ids for s in scenes):
        rep.add("warning", "chapters", "some scenes name no known chapter")
    return {"runtime": total, "modes": modes_time, "mean_hold": statistics.mean(holds) if holds else 0}


def compare(bp: dict, others: list[dict], rep: Report):
    dna = bp.get("dna") or {}
    acc = hue((dna.get("palette") or {}).get("accent", ""))
    for j, o in enumerate(others):
        od = o.get("dna") or {}
        tag = o.get("title", f"other#{j + 1}")
        for f in ("lead_technique", "opening_shot", "transition_family", "signature_device", "texture"):
            if dna.get(f) and dna.get(f) == od.get(f):
                level = "error" if (j == 0 or f in ("opening_shot",)) else "warning"
                rep.add(level, "sameness", f"{f} '{dna.get(f)}' repeats {tag}")
        if bp.get("engine") and bp.get("engine") == o.get("engine") and j == 0:
            rep.add("error", "sameness", f"engine '{bp['engine']}' repeats the previous film {tag}")
        oacc = hue((od.get("palette") or {}).get("accent", ""))
        if acc is not None and oacc is not None:
            gap = hue_gap(acc, oacc)
            if j == 0 and gap < 120:
                rep.add("error", "sameness", f"accent hue only {gap:.0f}° from the previous film {tag} (need 120°)")
            elif gap < 60:
                rep.add("warning", "sameness", f"accent hue {gap:.0f}° from {tag}")
        s0 = (bp.get("scenes") or [{}])[0].get("visual_mode")
        o0 = (o.get("scenes") or [{}])[0].get("visual_mode")
        if s0 and s0 == o0:
            rep.add("error", "sameness", f"opening visual mode '{s0}' repeats {tag}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("blueprint")
    ap.add_argument("--profile", choices=("house", "generic"), default="house")
    ap.add_argument("--compare", nargs="*", default=[], help="earlier blueprints, most recent first")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        bp = json.loads(Path(a.blueprint).read_text())
        others = [json.loads(Path(p).read_text()) for p in a.compare]
    except Exception as e:  # noqa: BLE001
        print(f"cannot read blueprint: {e}", file=sys.stderr)
        return 2
    rep = Report()
    stats = check(bp, HOUSE if a.profile == "house" else GENERIC, a.profile == "house", rep)
    if others:
        compare(bp, others, rep)
    if a.json:
        print(json.dumps({"ok": not rep.errors, "stats": stats, "issues": rep.items}, indent=2))
    else:
        for it in rep.items:
            print(f"{it['level'].upper():8} {it['where']:12} {it['msg']}")
        mix = ", ".join(f"{k} {v:.0f}s" for k, v in sorted(stats["modes"].items(), key=lambda kv: -kv[1]))
        print(f"\nruntime {stats['runtime']:.0f}s · mean hold {stats['mean_hold']:.1f}s · modes: {mix}")
        print("PASS" if not rep.errors else f"FAIL ({len(rep.errors)} errors)")
    return 0 if not rep.errors else 1


if __name__ == "__main__":
    sys.exit(main())
