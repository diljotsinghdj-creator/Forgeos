"""The research evidence database: every claim a documentary makes, where it comes from, how sure we are.

    {"topic": "...", "researched": "2026-11-10", "method": "how the research was done and what could not be reached",
     "claims": [{"id": "C01", "claim": "...", "status": "verified", "confidence": "high",
                 "figures": ["68,000", "1960"],               # the exact figures / years this claim lets the film use
                 "sources": [{"title": "...", "url": "https://...", "date": "2014-09-30",
                              "quote": "the source's own words, or a faithful summary marked [summary]"}],
                 "contradictions": ["other sources say ..."], "notes": "..."}]}

Statuses (what the film may do with a claim):
    verified        several independent sources agree, or a primary record says it      -> stated as fact
    reported        one credible source reports it                                       -> attributed ("according to")
    estimate        a figure that is an estimate                                         -> said as an estimate
    disputed        sources disagree                                                     -> the disagreement is said
    allegation      someone alleges it                                                   -> attributed, never as fact
    interpretation  a reading of the facts (ours or an expert's)                         -> framed as interpretation
    opinion         someone's view                                                       -> attributed
    method          how a graphic was made (e.g. an area measured from an outline)       -> stated on screen
    unverified      not checked                                                          -> may not be used
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

STATUSES = ("verified", "reported", "estimate", "disputed", "allegation", "interpretation", "opinion", "method", "unverified")
NEEDS_ATTRIBUTION = ("reported", "estimate", "disputed", "allegation", "opinion", "interpretation")
ATTRIBUTION_CUES = ("according to", "reported", "reports", "report", "say", "says", "said", "claims", "claimed",
                    "estimate", "estimated", "estimates", "about", "roughly", "around", "nearly", "some", "accounts",
                    "debated", "disputed", "unclear", "argue", "argued", "believe", "suggest", "officials", "researchers",
                    "scientists", "records", "measured", "according", "by one", "one study", "the world bank", "nasa",
                    "के मुताबिक", "के अनुसार", "बताया", "कहा", "दावा", "अनुमान", "करीब", "लगभग")
CONFIDENCE = ("high", "medium", "low")


@dataclass
class Claim:
    id: str
    claim: str
    status: str
    confidence: str = "medium"
    figures: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Dossier:
    topic: str
    claims: dict[str, Claim]
    researched: str = ""
    method: str = ""

    @staticmethod
    def load(path: Path | str) -> "Dossier":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return Dossier.from_dict(d)

    @staticmethod
    def from_dict(d: dict) -> "Dossier":
        cl = {}
        for c in d.get("claims", []):
            cl[str(c["id"])] = Claim(id=str(c["id"]), claim=str(c.get("claim", "")), status=str(c.get("status", "unverified")),
                                     confidence=str(c.get("confidence", "medium")), figures=[str(x) for x in c.get("figures", [])],
                                     sources=list(c.get("sources", [])), contradictions=list(c.get("contradictions", [])),
                                     notes=str(c.get("notes", "")))
        return Dossier(topic=str(d.get("topic", "")), claims=cl, researched=str(d.get("researched", "")), method=str(d.get("method", "")))

    def to_dict(self) -> dict:
        return {"topic": self.topic, "researched": self.researched, "method": self.method,
                "claims": [c.__dict__ for c in self.claims.values()]}

    def check(self) -> list[dict]:
        """Problems that stop a film: [{"level": "error"|"warning", "claim": id, "problem": ...}]."""
        out = []
        for c in self.claims.values():
            def bad(level, msg):
                out.append({"level": level, "claim": c.id, "problem": msg})
            if c.status not in STATUSES:
                bad("error", f"unknown status '{c.status}'")
            if c.confidence not in CONFIDENCE:
                bad("error", f"unknown confidence '{c.confidence}'")
            if not c.claim.strip():
                bad("error", "empty claim")
            if c.status != "method" and not c.sources:
                bad("error", "no source")
            for s in c.sources:
                u = str(s.get("url", ""))
                if c.status != "method" and not (urlparse(u).scheme in ("http", "https") and urlparse(u).netloc):
                    bad("error", f"source without a valid URL: {s.get('title', '')!r}")
                if not str(s.get("quote", "")).strip():
                    bad("warning", f"source has no quotation or summary: {u}")
            hosts = {urlparse(str(s.get("url", ""))).netloc.removeprefix("www.") for s in c.sources}
            if c.status == "verified" and len(hosts) < 2 and not any(s.get("primary") for s in c.sources):
                bad("error", "'verified' needs two independent sources or one primary record")
            if c.status == "disputed" and not c.contradictions:
                bad("error", "'disputed' without the contradicting accounts")
        return out

    def figures(self, ids: list[str]) -> set[str]:
        return {norm_figure(f) for i in ids if i in self.claims for f in self.claims[i].figures}

    def to_markdown(self) -> str:
        lines = [f"# Research dossier: {self.topic}", "", f"Researched: {self.researched}", "", "## Method", "", self.method, "",
                 "## Claims", "", "| ID | Claim | Status | Confidence | Figures |", "|---|---|---|---|---|"]
        for c in self.claims.values():
            lines.append(f"| {c.id} | {c.claim.replace('|', '/')} | {c.status} | {c.confidence} | {', '.join(c.figures)} |")
        lines += ["", "## Evidence", ""]
        for c in self.claims.values():
            lines += [f"### {c.id}. {c.claim}", "", f"Status: **{c.status}** · confidence: **{c.confidence}**", ""]
            for s in c.sources:
                lines.append(f"- [{s.get('title') or s.get('url')}]({s.get('url', '')})" + (f" ({s['date']})" if s.get("date") else "")
                             + (f": \"{s['quote']}\"" if s.get("quote") else ""))
            if c.contradictions:
                lines += ["", "Contradicting accounts:"] + [f"- {x}" for x in c.contradictions]
            if c.notes:
                lines += ["", f"Notes: {c.notes}"]
            lines.append("")
        return "\n".join(lines)


_WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twelve": 12, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "hundred": 100}


def norm_figure(s: str) -> str:
    """'68,000 km²' -> '68000'; '$64.5 million' -> '64.5'; '1960s' -> '1960'; '10%' -> '10'."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(s))
    return m.group(0).replace(",", "").rstrip("0").rstrip(".") if m and "." in m.group(0) else (m.group(0).replace(",", "") if m else "")


def figures_in(text: str) -> list[str]:
    """Every figure written with digits in a narration line or a graphic line (normalised)."""
    out = []
    for m in re.finditer(r"(?<![\w.])\d[\d,]*(?:\.\d+)?", text or ""):
        f = norm_figure(m.group(0))
        if f and f not in ("0", "1", "2", "3"):        # small counts ("two seas") are words, not evidence
            out.append(f)
    return out


def attributed(text: str) -> bool:
    t = (text or "").lower()
    return any(c in t for c in ATTRIBUTION_CUES)
