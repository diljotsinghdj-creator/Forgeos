#!/usr/bin/env python3
"""Gate a QC scorecard (assets/templates/qc_scorecard.json).

Usage: python3 qc_check.py qc_scorecard.json
Rules (documentary_quality_control.md): every category scored 1-10 with written evidence; critical categories
(research_depth, accuracy_and_honesty, information_clarity, rights_and_sourcing) need 9+; all others 8+.
Any category below the bar must appear in weak_areas with a revision. Exit 0 = ready, 1 = revise.
"""
import json
import sys

CRITICAL = {"research_depth", "accuracy_and_honesty", "information_clarity", "rights_and_sourcing"}
REQUIRED = CRITICAL | {"storytelling", "visual_explanation", "graphic_design", "animation", "editing", "narration",
                       "sound_design", "audience_engagement", "originality"}


def main(path):
    sc = json.load(open(path))
    cats = sc.get("categories", {})
    weak_text = " ".join(sc.get("weak_areas", [])).lower()
    problems = []
    for c in sorted(REQUIRED):
        v = cats.get(c)
        if not v:
            problems.append(f"{c}: not scored")
            continue
        s, ev = v.get("score", 0), str(v.get("evidence", ""))
        if not isinstance(s, (int, float)) or not 1 <= s <= 10:
            problems.append(f"{c}: score must be 1-10")
            continue
        if len(ev) < 25 or ev.startswith("<"):
            problems.append(f"{c}: no written evidence for the score")
        bar = 9 if c in CRITICAL else 8
        if s < bar:
            msg = f"{c}: {s} < {bar}"
            if c.replace("_", " ") not in weak_text and c not in weak_text:
                msg += " and it is not listed in weak_areas with a revision"
            problems.append(msg)
    for p in problems:
        print("REVISE", p)
    ok = not problems
    print("READY FOR OWNER" if ok else f"REVISE ({len(problems)} issues)")
    if ok and sc.get("verdict") != "ready for owner":
        print("note: verdict field still says", sc.get("verdict"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else 2)
