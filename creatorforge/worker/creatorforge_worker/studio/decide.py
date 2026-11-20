"""The visual decision engine: for every line, what the viewer needs to understand decides what they see.

classify() reads the line (and the evidence it cites) for what it needs to explain:
    person_event, geography, statistic, history, finance, institution, abstract, document, location, sequence,
    process, human
options() lays out the treatments that could carry it:
    A  footage        moving pictures of the subject or place (stock: atmosphere and context only)
    B  photograph     a real photograph, moved in 2.5D, annotated
    C  graphic        the custom graphic that shows the line's facts (map, chart, diagram, document, 3D)
    D  combination    a photograph that hands over to a map or a figure, or a document over a map
score() weighs each one: does it show the line's key facts with the sound off; how authentic is it for this claim
(a real photo of the very subject > an illustrative stock picture); does it suit what the line needs (the table
below); would it repeat the shot before; can it be had (assets found or likely). choose() keeps every option and its
scores, so the decision is on record (writing/visual_decisions.md).

    need            preferred treatments, best first
    person_event    photograph (verified) · footage · document · combination
    geography       map graphic · combination (photo -> map) · photograph
    statistic       custom infographic · combination (photo -> figure)
    history         archive photograph · labelled reconstruction (graphic) · map graphic
    finance         financial diagram (graphic) · document
    institution     organisational graphic
    abstract        illustration / metaphor (graphic)
    document        the document itself, annotated (graphic / photograph)
    location        photograph · footage · map graphic
    sequence        timeline (graphic)
    process         2D / 3D process animation (graphic)
    human           photograph · footage
"""
from __future__ import annotations

import os
import re

NEEDS = ("person_event", "geography", "statistic", "history", "finance", "institution", "abstract", "document", "location",
         "sequence", "process", "human")
PREFER = {"person_event": ["photo", "footage", "combo", "graphic"], "geography": ["graphic", "combo", "photo", "footage"],
          "statistic": ["graphic", "combo", "photo", "footage"], "history": ["photo", "graphic", "combo", "footage"],
          "finance": ["graphic", "combo", "photo", "footage"], "institution": ["graphic", "combo", "photo", "footage"],
          "abstract": ["graphic", "photo", "combo", "footage"], "document": ["graphic", "photo", "combo", "footage"],
          "location": ["photo", "footage", "combo", "graphic"], "sequence": ["graphic", "combo", "photo", "footage"],
          "process": ["graphic", "combo", "footage", "photo"], "human": ["photo", "footage", "combo", "graphic"]}
CUES = {
    "document": ("report", "document", "court", "judgment", "filed", "letter", "records", "minutes", "memo", "according to the",
                 "रिपोर्ट", "दस्तावेज़", "अदालत", "फ़ैसला"),
    "finance": ("money", "billion", "million", "dollars", "rupees", "pounds", "crore", "lakh", "loan", "budget", "profit", "paid",
                "funds", "cost", "price", "रुपये", "डॉलर", "पैसा", "कर्ज़"),
    "institution": ("ministry", "department", "board", "agency", "company", "subsidiar", "committee", "government", "parliament",
                    "मंत्रालय", "सरकार", "कंपनी", "विभाग"),
    "process": ("how", "works", "inside", "flows", "pumped", "process", "made of", "turns into", "कैसे", "अंदर"),
    "sequence": ("then", "after", "before", "until", "by the time", "फिर", "बाद", "पहले"),
    "human": ("people", "families", "lives", "workers", "jobs", "children", "fishermen", "residents", "illness", "lost their",
              "लोग", "परिवार", "मज़दूर", "बच्चे"),
    "geography": ("border", "north", "south", "east", "west", "between", "route", "river", "sea", "coast", "map", "region",
                  "सीमा", "नदी", "समुद्र", "रास्ता"),
    "location": ("this is", "sits", "a town", "a city", "a village", "here", "यह है", "शहर", "गाँव"),
}


def _has(text: str, words) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def classify(line: str, facts: dict, claims: list | None = None) -> list[str]:
    """What the line needs, most important first."""
    needs = []
    if _has(line, CUES["document"]) and claims:
        needs.append("document")
    if facts.get("numbers") or facts.get("percent"):
        needs.append("finance" if facts.get("money") or _has(line, CUES["finance"]) else "statistic")
    if facts.get("people") or (facts.get("date") and facts.get("places")):
        needs.append("person_event")
    if any(y < 1990 for y in facts.get("years", [])):
        needs.append("history")
    if len(facts.get("years", [])) >= 2 or (facts.get("years") and _has(line, CUES["sequence"])):
        needs.append("sequence")
    if _has(line, CUES["institution"]) and not facts.get("numbers"):
        needs.append("institution")
    if facts.get("places"):
        needs.append("location" if _has(line, CUES["location"]) else "geography")
    elif _has(line, CUES["geography"]):
        needs.append("geography")
    if _has(line, CUES["process"]):
        needs.append("process")
    if _has(line, CUES["human"]):
        needs.append("human")
    return list(dict.fromkeys(needs)) or ["abstract"]


def options(line: str, facts: dict, need: str, graphic: str = "", visual: dict | None = None) -> list[dict]:
    """The candidate treatments for a line. `graphic` is the writer's (or the director's) graphic line; `visual` the
    scene's photo / footage need ({subject, place, ...})."""
    from .. import infographic as ig
    out = []
    v = visual or {}
    subject = v.get("subject") or (facts.get("objects") or [""])[0] or (facts.get("places") or [""])[0]
    place = v.get("place") or (facts.get("places") or [""])[0]
    if subject:
        out.append({"treatment": "footage", "what": f"stock footage: {subject}" + (f", {place}" if place else ""), "subject": subject, "place": place})
        out.append({"treatment": "photo", "what": f"photograph: {subject}" + (f", {place}" if place else "") + " (2.5D, annotated)",
                    "subject": subject, "place": place})
    g = graphic or next(iter(ig.candidates(line, facts, 3, 9)), "")
    if g:
        out.append({"treatment": "graphic", "what": g})
    keys = ig.key_facts(facts)
    if subject and (keys or place):
        then = f"then: pin {place}" if place and not facts.get("numbers") else (f"then: number {keys[0]}" if keys else "")
        if then:
            out.append({"treatment": "combo", "what": f"photograph of {subject} that hands over ({then})", "subject": subject, "place": place,
                        "then": then})
    return out


def score(opt: dict, line: str, facts: dict, need: str, prev_kinds: list[str], specific: bool, assets_likely: bool) -> dict:
    from .. import infographic as ig
    t = opt["treatment"]
    keys = ig.key_facts(facts)
    if t == "graphic":
        explains = 1.0 if ig.mute_test(facts, opt["what"]) else 0.4
    elif t == "combo":
        explains = 0.95 if keys else 0.7
    else:
        explains = 1.0 if not keys else 0.35          # a picture alone can't carry a figure or a date
    authentic = {"photo": 1.0 if specific else 0.55, "footage": 0.9 if specific else 0.45, "combo": 0.9 if specific else 0.6,
                 "graphic": 0.8 if keys else 0.6}[t]
    sat = t == "graphic" and opt["what"].split(":", 1)[0].strip().lower() == "satellite"
    if sat:
        authentic = 1.0                               # real imagery of this very place on the stated dates
    rank = PREFER.get(need, PREFER["abstract"]).index(t)
    fit = 1.0 - rank * 0.25
    kind = opt["what"].split(":", 1)[0].strip().lower() if t == "graphic" else t
    variety = 0.5 if kind in prev_kinds[-1:] else 0.8 if kind in prev_kinds[-2:] else 1.0
    avail = (0.85 if sat else 1.0) if t == "graphic" else (0.75 if assets_likely else 0.0)
    total = .32 * explains + .22 * authentic + .26 * fit + .1 * variety + .1 * avail
    return {**opt, "explains": round(explains, 2), "authentic": round(authentic, 2), "fit": round(fit, 2), "variety": variety,
            "available": avail, "score": round(total, 3)}


def assets_likely() -> bool:
    """Are there photo / footage sources on this worker (keys in the environment, or the keyless ones)?"""
    return any(os.environ.get(k) for k in ("PIXABAY_KEY", "CF_PIXABAY_KEY", "UNSPLASH_KEY", "CF_UNSPLASH_KEY", "PEXELS_KEY", "CF_PEXELS_KEY")) \
        or os.environ.get("CF_FREE_STOCK", "1") != "0"


def choose(line: str, scene: dict, prev_kinds: list[str]) -> dict:
    """The decision for one scene: its needs, every option with its scores, the winner and why."""
    from .. import infographic as ig
    facts = ig.facts(line)
    if not facts["places"]:
        # English narration: places are the capitalised names the map knows ("Moynaq", "Central Asia")
        from ..media import maps
        names = re.findall(r"\b([A-Z][a-z]+(?:[ -][A-Z][a-z]+)?)\b", line)
        facts["places"] = [n for n in dict.fromkeys(names) if n.lower() not in ("this", "the", "nasa", "then", "but", "and", "so", "in")
                           and maps._find(n)][:4]
    if not facts["numbers"]:
        facts["numbers"] = [{"value": float(x.replace(",", "")), "shown": x} for x in re.findall(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", line)
                            if not 1900 <= float(x.replace(",", "")) <= 2100][:4]
    needs = classify(line, facts, scene.get("claims"))
    v = scene.get("visual") or {}
    specific = bool(v.get("specific", bool(facts.get("people") or facts.get("places"))))
    opts = [score(o, line, facts, needs[0], prev_kinds, specific, assets_likely()) for o in options(line, facts, needs[0], scene.get("graphic", ""), v)]
    # an option this worker cannot fill (a photo with no photo source) stays in the report but is never chosen
    opts.sort(key=lambda o: (o["available"] <= 0, -o["score"]))
    best = opts[0] if opts else None
    why = ""
    if best:
        why = (f"{best['treatment']} best explains a '{needs[0]}' line: shows the key facts {best['explains']:.0%}, "
               f"authenticity {best['authentic']:.0%}, fit {best['fit']:.0%}")
    return {"needs": needs, "options": opts, "chosen": best, "why": why}


def to_markdown(decisions: list[tuple[str, str, dict, str]]) -> str:
    """decisions: (scene id, narration, decision, what was used)."""
    out = ["# Visual decisions", "", "For every line: what it needs to explain, the treatments considered, their scores, and what was used.", ""]
    for sid, text, d, used in decisions:
        out += [f"## {sid}: {text}", "", f"Needs: {', '.join(d['needs'])}", "", "| Option | What | Explains | Authentic | Fit | Variety | Available | Score |",
                "|---|---|---|---|---|---|---|---|"]
        for o in d["options"]:
            out.append(f"| {o['treatment']} | {o['what'][:70]} | {o['explains']} | {o['authentic']} | {o['fit']} | {o['variety']} | {o['available']} | **{o['score']}** |")
        out += ["", f"Decision: {d['why']}", "", f"Used: `{used}`", ""]
    return "\n".join(out)
