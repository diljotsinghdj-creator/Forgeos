"""Visual reasoning: how to *show* an idea, and how honestly.

Every line of a script gets a representation mode before anything is drawn:

    LITERAL      what is described happens on screen (a person walks, a ball drops)
    DEMO         a working demonstration of a principle (gravity: two objects really fall under the same g)
    DIAGRAM      relationships, processes and quantities (who appoints whom, a flow, a chart of numbers)
    METAPHOR     an idea shown as an image (prices as a basket whose tags climb) - always labelled "Illustration"
    SATIRE       exaggeration to make a point - always labelled "Satire"
    REENACTMENT  real past events dramatised with stick figures - always labelled "Reconstruction"
    EVIDENCE     documents, footage, sourced numbers - only from sources supplied with the script

The rules that keep documentary content honest:
* an allegation (corruption, bribery, fraud, "accused of") is never acted out as if it happened; it becomes an
  EVIDENCE chain built only from the sources given - each step carries its source - or, without sources, a card
  that says "Allegation - unverified" with who made it;
* numbers become a chart only with a source; otherwise they are marked "figure from the script";
* metaphors, satire and reconstructions carry their label on screen for as long as they are shown.

`reason(sentence, sources)` returns a VisualPlan; `stage(sc, plan, t0, t1, x)` puts it on a Scene; `audit(plans)`
lists any factual element that is missing a source."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LITERAL, DEMO, DIAGRAM, METAPHOR, SATIRE, REENACT, EVIDENCE = (
    "literal", "demonstration", "diagram", "metaphor", "satire", "reenactment", "evidence")
LABELS = {METAPHOR: "Illustration", SATIRE: "Satire", REENACT: "Reconstruction (illustration)"}


@dataclass
class VisualPlan:
    sentence: str
    mode: str
    concept: str = ""
    elements: list = field(default_factory=list)     # what to draw: dicts with a "kind"
    label: str = ""                                   # must be on screen while it is shown
    claims: list = field(default_factory=list)       # factual claims found in the line
    sourced: bool = True
    note: str = ""


ALLEGATION = re.compile(r"\b(corrupt\w*|brib\w*|scam|fraud|launder\w*|kickback|embezzl\w*|accused|alleg\w*|rigg\w*|"
                        r"kickbacks?|siphon\w*)\b", re.I)
SATIRE_CUE = re.compile(r"\b(satire|imagine if|as if|apparently|of course,|supposedly|mock)\b", re.I)
PAST_EVENT = re.compile(r"\b(in|on|by)\s+(1[0-9]{3}|20[0-2][0-9])\b|\bcentury\b", re.I)
NUMBER = re.compile(r"(\d[\d,.]*)\s*(%|per cent|percent|crore|lakh|rupees|dollars|million|billion)?", re.I)

CONCEPTS = [
    # (pattern, concept, mode, elements)
    (r"inflation|prices?\b.{0,40}\b(?:rise[sn]?|rose|go(?:es)? up|went up|increas\w*|climb\w*|soar\w*)|cost of living|"
     r"more expensive",
     "inflation", METAPHOR, [{"kind": "basket", "items": ["rice", "milk", "oil"], "rise": 0.25}]),
    (r"appoint\w*|oversee\w*|controls?|reports? to|accountable|power over|selection committee|institution",
     "power", DIAGRAM, [{"kind": "relations"}]),
    (r"anxi\w+|panic|stress\w*|overwhelm\w*|nervous|dread",
     "anxiety", METAPHOR, [{"kind": "mood", "mood": "anxious"}, {"kind": "cloud"}]),
    (r"calm\w*|reliev\w*|relax\w*|breathe",
     "calm", METAPHOR, [{"kind": "mood", "mood": "calm"}]),
    (r"gravity|falls? at the same|drop(?:s|ped)? .*(?:ball|feather|apple)|vacuum",
     "gravity", DEMO, [{"kind": "drop_pair"}]),
    (r"vote|ballot|election",
     "voting", LITERAL, [{"kind": "ballot_box"}]),
    (r"supply|demand|market",
     "market", DIAGRAM, [{"kind": "chart"}]),
]


def reason(sentence: str, sources: list[dict] | None = None) -> VisualPlan:
    """sources: [{"claim": text it supports, "source": "Publisher, date", "kind": "document|photo|footage|data",
    "path": optional image}]"""
    sources = sources or []
    s = sentence
    claims = [m.group(0).strip(" ,.") for m in NUMBER.finditer(s)
              if m.group(1) and not re.fullmatch(r"(1[0-9]|20)\d\d", m.group(1).rstrip(",."))]
    supporting = [src for src in sources if src.get("claim") and _overlap(src["claim"], s) > 0.3]
    if ALLEGATION.search(s):
        who = re.search(r"\b(according to|said|says|claims?|alleges?|accused by)\s+((?:the )?[\w ]+?)(?:[,.]|$)", s)
        if supporting:
            return VisualPlan(s, EVIDENCE, "allegation", [{"kind": "evidence_chain", "steps": [
                {"text": src["claim"], "source": src["source"]} for src in supporting]}],
                "Allegation - as reported", claims, True,
                "shown as the documented sequence, each step with its source; nothing is acted out")
        return VisualPlan(s, EVIDENCE, "allegation", [{"kind": "allegation_card", "by": who.group(2) if who else ""}],
                          "Allegation - unverified", claims, False,
                          "no sources supplied: shown as an attributed, unverified allegation, never reenacted")
    if SATIRE_CUE.search(s):
        return VisualPlan(s, SATIRE, "satire", [{"kind": "exaggerate"}], LABELS[SATIRE], claims, True)
    for rx, concept, mode, elems in CONCEPTS:
        if re.search(rx, s, re.I):
            plan = VisualPlan(s, mode, concept, [dict(e) for e in elems], LABELS.get(mode, ""), claims, True)
            for e in plan.elements:
                if e["kind"] == "basket":                # the goods the line actually names
                    named = [g for g in GOODS if re.search(rf"\b{g}\b", s, re.I)]
                    e["items"] = (named + [g for g in e["items"] if g not in named])[:3]
                if e["kind"] == "relations":             # the institutions the line actually names
                    e.update(_relations(s))
            if claims and mode in (DIAGRAM, METAPHOR):
                plan.sourced = bool(supporting)
                if not supporting:
                    plan.note = "numbers shown as 'figure from the script' (no source supplied)"
            return plan
    if PAST_EVENT.search(s) and re.search(r"\b[A-Z][a-z]+\b", s[1:]):
        return VisualPlan(s, REENACT, "history", [{"kind": "reconstruction"}], LABELS[REENACT], claims,
                          bool(supporting) or not claims)
    if claims:
        return VisualPlan(s, DIAGRAM if supporting else LITERAL, "figures",
                          [{"kind": "stat", "value": claims[0], "source": supporting[0]["source"] if supporting else ""}],
                          "", claims, bool(supporting),
                          "" if supporting else "figure shown as 'from the script' (no source supplied)")
    return VisualPlan(s, LITERAL, "action")


GOODS = ["rice", "milk", "oil", "bread", "petrol", "diesel", "vegetables", "onions", "tomatoes", "sugar", "rent",
         "gas", "fuel", "wheat", "flour", "eggs", "medicine"]
VERB_REL = re.compile(r"(?P<a>(?:the )?[A-Z][\w]*(?: [A-Z][\w]*)*)\s+(?P<v>appoints?|oversees?|controls?|reports? to|"
                      r"answers? to|nominates?|chooses?|selects?|funds?)\s+(?P<b>(?:two of the three members of )?"
                      r"(?:the )?[\w ]+?)(?:[,.]|$| and )")


def _relations(s: str) -> dict:
    m = VERB_REL.search(s)
    if not m:
        return {}
    a = m.group("a").replace("The ", "").strip()
    b = re.sub(r"^(two of the three members of )?(the )?", "", m.group("b").strip(), flags=re.I)
    b = b[:1].upper() + b[1:]
    return {"nodes": [[a, 0.2, 0.75], [b, 0.8, 0.25]], "edges": [[0, 1, m.group("v")]]}


def _overlap(a: str, b: str) -> float:
    wa = {w for w in re.findall(r"[a-z0-9]+", a.lower()) if len(w) > 3}
    wb = {w for w in re.findall(r"[a-z0-9]+", b.lower()) if len(w) > 3}
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


def audit(plans: list[VisualPlan]) -> list[str]:
    """Every factual element without a source, and every non-literal visual missing its label."""
    out = []
    for p in plans:
        if not p.sourced:
            out.append(f"unsourced {p.concept or 'claim'}: {p.sentence!r} - {p.note}")
        if p.mode in LABELS and not p.label:
            out.append(f"{p.mode} without an on-screen label: {p.sentence!r}")
    return out


# ---- staging ---------------------------------------------------------------------------------------------------------
def stage(sc, plan: VisualPlan, t0: float, t1: float, x: float = 3.2, actors: dict | None = None, world=None):
    """Puts the plan's visuals on the scene between t0 and t1, near world x. Returns the props it added."""
    from .stick import Prop
    added = []
    show = [(t0, 0.0, "linear"), (t0 + 0.5, 1.0, "inout"), (t1 - 0.4, 1.0, "linear"), (t1, 0.0, "inout")]
    for e in plan.elements:
        k = e["kind"]
        if k == "basket":
            items = e["items"]
            base = [40, 30, 120][:len(items)]
            data = {"items": items, "show": show}
            for i, b0 in enumerate(base):
                data[f"p{i}"] = [(t0, float(b0), "linear"), (t1 - 0.8, float(b0) * (1 + e["rise"] * (i + 1) / 2), "inout")]
            added.append(Prop("basket", x, 0.0, 2.3, 1.7, label=plan.label, data=data))
        elif k == "relations":
            added.append(Prop("relations", x + 0.6, 0.9, 3.2, 1.6, data={"show": show, "nodes": e.get("nodes"),
                                                                         "edges": e.get("edges")}))
        elif k == "mood":
            sc.moods = getattr(sc, "moods", []) + [(t0, t1, e["mood"])]
        elif k == "cloud":
            added.append(Prop("cloud", x - 3.0, 2.05, 0.9, 0.38, label=plan.label or "illustration", data={"show": show}))
        elif k == "evidence_chain":
            added.append(Prop("evidence", x + 0.6, 0.35, 5.0, 1.9, label=plan.label,
                              data={"steps": e["steps"], "reveal": [(t0 + 0.3, 0.0, "linear"), (t1 - 0.8, 1.0, "linear")],
                                    "show": show}))
        elif k == "allegation_card":
            text = "Allegation - unverified" + (f" (made by {e['by']})" if e.get("by") else "")
            added.append(Prop("sign", x, 1.2, 2.6, 0.7, label=text, data={"show": show}))
        elif k == "stat":
            added.append(Prop("stat", x, 1.3, 1.9, 0.9, data={
                "value": e["value"], "label": e["source"] or "figure from the script",
                "pop": [(t0 + 0.4, 0.0, "linear"), (t0 + 0.9, 1.0, "back")]}))
        elif k == "ballot_box":
            added.append(Prop("crate", x, 0.0, 0.6, 0.6, label="VOTES"))
        elif k == "reconstruction" or k == "exaggerate":
            sc.tags = getattr(sc, "tags", []) + [(t0, t1, plan.label)]
    for p in added:
        sc.actors.insert(0, p)
    if plan.label and plan.mode in LABELS:
        sc.tags = getattr(sc, "tags", []) + [(t0, t1, plan.label)]
    return added
