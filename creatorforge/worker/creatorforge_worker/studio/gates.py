"""The owner's five gates (2026-11-11): rules the studio enforces itself, so they hold whether or not anyone remembers them.

1. **No pick, no script.** A channel film or a sample is not written or drawn until the owner has picked one of three
   pitched narrative engines, recorded in the screenplay as
   ``"pick": {"engine": ..., "pitched": [three engines], "owner_words": "...", "date": "YYYY-MM-DD"}``.
2. **Seen means used.** Everything the owner has been shown (films, samples, storyboards) is in ``channels/SEEN.json``.
   A new piece may not repeat the last piece's engine, look or stand-in voice, the opening shot of the last three, or,
   on the same topic, a hook or a shot already shown (unless the owner asked for it: ``"reuse": ["S2", ...]``).
3. **Evidence first.** On Print Facts, a real document, photo or footage comes before the first explanatory graphic.
   Where none can be had, the screenplay says so (``"evidence_waiver": {"reason": ..., "told_owner": true}``) and the
   pre-show list carries it.
4. **Pacing.** A still shot holds at most 4.5 s and a shot that builds at most 7 s (the last shot 1.5 s more); the
   average hold is at most 5 s. A longer line is split into more shots.
5. **Pre-show list.** Every render writes ``PRESHOW.md``: what still breaks or bends the rules, what is a stand-in and
   what is missing. It goes to the owner with the video, before any summary.

The gates apply to the two channels and to samples (``"sample_for": "print-facts"``); test reels are left alone."""
from __future__ import annotations

import json
import os
import re
import statistics
from datetime import date
from pathlib import Path

CHANNELS = ("print-facts", "dragon-psychology")
CHANNELS_DIR = Path(__file__).resolve().parents[3] / "channels"
SEEN_FILE = CHANNELS_DIR / "SEEN.json"
HISTORY_DIR = CHANNELS_DIR / "studio_history"

# real material: a photograph, footage, satellite imagery or a document scan carried as a file
EVIDENCE_KINDS = ("photo", "photos", "footage", "photo3d", "satellite")
# graphics that explain (data, diagrams, maps, 3D comparisons); recreations, titles and hooks are neither
EXPLAIN_KINDS = ("counter", "bignumber", "number", "stack", "stand", "fan", "trend", "slice", "seats", "pie", "chart", "columns",
                 "dots", "table", "polltrack", "area", "candles", "pyramid", "squares", "icons", "units", "flowchart", "linkmap",
                 "orgchart", "steps", "timeline", "blueprint", "staircase", "scale", "bars3d", "prism", "explode", "towers3d",
                 "planets", "terrain3d", "flowmap", "heatmap", "shrink", "morph", "borders", "sizemap", "route", "arrows", "railmap",
                 "compare", "sunrise", "zones", "clockmap")
# shots that hold one picture; everything else builds on screen as it is named
STILL_KINDS = ("hero", "statement", "newscard", "tornsplit", "clipping", "quote", "interview", "opener", "endcard", "document",
               "article", "photo", "reveal", "stamp", "sign", "title3d", "courtdoc")
MAX_STILL, MAX_BUILD, LAST_EXTRA, MAX_MEAN = 4.5, 7.0, 1.5, 5.0
RECREATION_KINDS = ("chat", "social", "comments", "trending", "search")


def applies(sp: dict) -> bool:
    return sp.get("channel") in CHANNELS or sp.get("sample_for") in CHANNELS


def channel_of(sp: dict) -> str:
    return sp.get("channel") if sp.get("channel") in CHANNELS else sp.get("sample_for", "")


def topic_of(sp: dict) -> str:
    t = sp.get("topic") or re.sub(r"-sample(-?\d+)?$|-v\d+$", "", sp.get("id", ""))
    return re.sub(r"\W+", "-", str(t).lower()).strip("-")


def _kind(graphic: str) -> str:
    return str(graphic).split(":", 1)[0].strip().lower()


def _owner_voice(voice: str) -> bool:
    return "owner" in str(voice or "").lower()


def _err(gate: int, scene: str, problem: str, level: str = "error") -> dict:
    return {"gate": gate, "level": level, "scene": scene, "problem": problem}


# ---- gate 1 -----------------------------------------------------------------------------------------------------------
def check_pick(sp: dict) -> list[dict]:
    from .writer import ENGINES
    p = sp.get("pick") or {}
    if not p:
        return [_err(1, "-", "no engine picked by the owner: pitch three engines (writer.pitch) and record the owner's pick "
                             "as \"pick\" before writing or drawing")]
    out = []
    pitched = [str(x) for x in p.get("pitched", [])]
    if len(set(pitched)) != 3 or any(x not in ENGINES for x in pitched):
        out.append(_err(1, "-", f"the pick must name the three engines that were pitched (from {', '.join(ENGINES)})"))
    if p.get("engine") not in pitched:
        out.append(_err(1, "-", "the picked engine is not one of the three pitched"))
    if p.get("engine") != sp.get("engine"):
        out.append(_err(1, "-", f"the screenplay's engine '{sp.get('engine')}' is not the owner's pick '{p.get('engine')}'"))
    if not str(p.get("owner_words", "")).strip() or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(p.get("date", ""))):
        out.append(_err(1, "-", "the pick needs the owner's own words and the date they picked"))
    return out


# ---- gate 2 -----------------------------------------------------------------------------------------------------------
def seen(path: Path | None = None) -> list[dict]:
    p = Path(path or os.environ.get("CF_SEEN") or SEEN_FILE)
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _words(graphic: str) -> set[str]:
    spec = str(graphic).split(":", 1)[-1]
    head = " ".join(x for x in spec.split("|")[:2] if ":" not in x.strip()[:12])
    return {w for w in re.findall(r"[a-z0-9]+", head.lower()) if len(w) > 2 or w.isdigit()}


def similar(a: str, b: str) -> float:
    if _kind(a) != _kind(b):
        return 0.0
    x, y = _words(a), _words(b)
    return len(x & y) / max(1, len(x | y))


def entry(sp: dict, kind: str, look: str = "", day: str = "") -> dict:
    sc = sp.get("scenes", [])
    return {"id": sp.get("id", ""), "kind": kind, "channel": channel_of(sp) or sp.get("channel", ""), "topic": topic_of(sp),
            "date": day or date.today().isoformat(), "engine": sp.get("engine", ""), "hook_mechanism": sp.get("hook_mechanism", ""),
            "hook_line": sc[0].get("narration", "") if sc else "", "opening": _kind(sc[0]["graphic"]) if sc else "",
            "shots": [s.get("graphic", "") for s in sc], "voice": sp.get("voice", ""), "look": look}


def record(e: dict, path: Path | None = None) -> None:
    p = Path(path or os.environ.get("CF_SEEN") or SEEN_FILE)
    rows = [x for x in seen(p) if not (x.get("id") == e["id"] and x.get("kind") == e["kind"])] + [e]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


def check_seen(sp: dict, look: str, rows: list[dict]) -> list[dict]:
    rows = [r for r in rows if r.get("id") != sp.get("id")]           # a re-render of the same piece is not a repeat
    out = []
    if not rows:
        return out
    last, last3 = rows[-1], rows[-3:]
    if sp.get("engine") and sp.get("engine") == last.get("engine"):
        out.append(_err(2, "-", f"engine '{sp['engine']}' was the last piece's ({last['id']})"))
    if look and look == last.get("look"):
        out.append(_err(2, "-", f"look '{look}' was the last piece's ({last['id']}): change the paper, palette and type treatment"))
    v = sp.get("voice", "")
    if v and not _owner_voice(v) and v == last.get("voice"):
        out.append(_err(2, "-", f"stand-in voice '{v}' was the last piece's ({last['id']}): rotate it"))
    first = _kind(sp["scenes"][0]["graphic"]) if sp.get("scenes") else ""
    if first and first in [r.get("opening") for r in last3]:
        out.append(_err(2, sp["scenes"][0].get("id", "S1"), f"opens on '{first}', as one of the last three pieces did"))
    same = [r for r in rows if r.get("topic") == topic_of(sp)]
    reuse = set(sp.get("reuse", []))
    for r in same:
        if sp.get("hook_mechanism") and sp.get("hook_mechanism") == r.get("hook_mechanism"):
            out.append(_err(2, "-", f"hook '{sp['hook_mechanism']}' was already shown in {r['id']} ({r['kind']})"))
        hl = set(re.findall(r"[a-z]+", r.get("hook_line", "").lower()))
        mine = set(re.findall(r"[a-z]+", (sp["scenes"][0].get("narration", "") if sp.get("scenes") else "").lower()))
        if hl and len(hl & mine) / max(1, len(hl | mine)) >= 0.5:
            out.append(_err(2, "S1", f"the opening line repeats the one shown in {r['id']}"))
    for s in sp.get("scenes", []):
        if s.get("id") in reuse:
            continue
        for r in same:
            hit = max((similar(s.get("graphic", ""), g) for g in r.get("shots", [])), default=0.0)
            if hit >= 0.5:
                out.append(_err(2, s.get("id", "?"), f"this shot was already shown in {r['id']} ({r['kind']}); "
                                                     "design a new one, or list it under \"reuse\" if the owner asked for it"))
                break
            nums = set(re.findall(r"\d[\d,.]*\d|\d", str(s.get("graphic", "")).split("|")[0]))
            if len(nums) >= 2 and any(len(nums & set(re.findall(r"\d[\d,.]*\d|\d", str(g).split("|")[0]))) >= 2 for g in r.get("shots", [])):
                out.append(_err(2, s.get("id", "?"), f"the same figures were already charted in {r['id']}: "
                                                     "say why they are back, or show them a new way", "warning"))
                break
    return out


# ---- gate 3 -----------------------------------------------------------------------------------------------------------
def check_evidence(sp: dict) -> list[dict]:
    if channel_of(sp) != "print-facts":
        return []
    for s in sp.get("scenes", []):
        k = _kind(s.get("graphic", ""))
        if k in EVIDENCE_KINDS:
            return []
        if k in EXPLAIN_KINDS:
            w = sp.get("evidence_waiver") or {}
            if w.get("reason") and w.get("told_owner"):
                return [_err(3, s.get("id", "?"), f"no real evidence before the first explanation (waived: {w['reason']})", "warning")]
            return [_err(3, s.get("id", "?"), f"'{k}' explains before any real document, photo or footage is shown: put the "
                                              "evidence first, or record an evidence_waiver the owner has been told about")]
    return []


# ---- gate 4 -----------------------------------------------------------------------------------------------------------
def check_pacing(timeline: list[dict], kinds: list[str]) -> list[dict]:
    out, holds = [], []
    for i, (t, k) in enumerate(zip(timeline, kinds)):
        d = t["end"] - t["start"]
        holds.append(d)
        cap = (MAX_STILL if k in STILL_KINDS else MAX_BUILD) + (LAST_EXTRA if i == len(timeline) - 1 else 0)
        if d > cap + 0.05:
            out.append(_err(4, t["scene"], f"'{k}' holds {d:.1f}s (most {cap:.1f}s for a {'still' if k in STILL_KINDS else 'building'} "
                                           "shot): split the line into more shots"))
    if holds and statistics.mean(holds) > MAX_MEAN + 0.05:
        out.append(_err(4, "-", f"the average hold is {statistics.mean(holds):.1f}s (most {MAX_MEAN:.1f}s)"))
    return out


# ---- gate 5 -----------------------------------------------------------------------------------------------------------
def missing_symbols(sp: dict) -> list[str]:
    from ..media import vox
    lg, out = vox.logos(), []
    for s in sp.get("scenes", []):
        m = re.search(r"\|\s*logo\s*:\s*([^|]+)", s.get("graphic", ""))
        for k in [x.strip().lower() for x in (m.group(1).split(",") if m else [])]:
            if k in lg and lg[k].get("party") and not lg[k].get("img"):
                out.append(f"{s.get('id')}: the {lg[k]['short']} symbol is left out (no official file in the data folder)")
    return out


def preshow(sp: dict, gate_issues: list[dict], timeline: list[dict], kinds: list[str], report: dict, extra: dict) -> str:
    """The list the owner reads with the video: everything that still breaks or bends a rule, first."""
    secs = report.get("seconds") or (timeline[-1]["end"] if timeline else 0)
    tgt = sp.get("target_seconds")
    L = [f"# Before you watch: {sp.get('title', '')}", "",
         "Read this with the video. It lists what still breaks or bends your rules, what is a stand-in and what is missing.", ""]
    L += ["## Rules", ""]
    names = {1: "No pick, no script", 2: "Seen means used", 3: "Evidence first", 4: "Pacing"}
    for g in (1, 2, 3, 4):
        mine = [i for i in gate_issues if i["gate"] == g]
        L.append(f"- **Gate {g}, {names[g]}:** " + ("passed" if not mine else "; ".join(f"{i['scene']}: {i['problem']}" for i in mine)))
    L += ["", "## Against what was asked", ""]
    L.append(f"- Length: {secs:.1f}s" + (f" against {tgt}s asked" + (" (over)" if secs > tgt * 1.05 else "") if tgt else ""))
    L.append(f"- Language: {sp.get('language', '?')}; channel: {channel_of(sp) or sp.get('channel', '?')}")
    L.append(f"- Voice: {sp.get('voice', '?')}" + ("" if _owner_voice(sp.get("voice", "")) else " (a stand-in, not the owner's ElevenLabs voice)"))
    L += ["", "## Stand-ins and gaps", ""]
    gaps = list(extra.get("symbols", []))
    gaps += [f"{s.get('id')}: a recreation ({_kind(s['graphic'])}), labelled RECREATION" for s in sp.get("scenes", [])
             if _kind(s.get("graphic", "")) in RECREATION_KINDS]
    if not any(k in EVIDENCE_KINDS for k in kinds):
        gaps.append("No real document, photo or footage anywhere in the piece")
    L += [f"- {g}" for g in gaps] or ["- none found"]
    L += ["", "## Warnings from the studio's own checks", ""]
    warns = [f"editorial {i['scene']}: {i['problem']}" for i in extra.get("editorial", []) if i["level"] == "warning"]
    warns += [f"variation {i['scene']}: {i['problem']}" for i in extra.get("variation", []) if i["level"] == "warning"]
    warns += [f"quality: {w}" for w in extra.get("qc", [])]
    warns += [f"retention: weakest shot {w}" for w in extra.get("weakest", [])]
    L += [f"- {w}" for w in warns] or ["- none"]
    L += ["", "## Shot by shot", "", "| Shot | Time | Hold | Kind | Role |", "|---|---|---|---|---|"]
    for t, k in zip(timeline, kinds):
        role = ("evidence" if k in EVIDENCE_KINDS else "explains" if k in EXPLAIN_KINDS else "recreation" if k in RECREATION_KINDS
                else "still" if k in STILL_KINDS else "builds")
        L.append(f"| {t['scene']} | {t['start']:.1f}-{t['end']:.1f}s | {t['end'] - t['start']:.1f}s | {k} | {role} |")
    L += ["", "## Brain Log rules to check by eye", ""]
    L += [f"- {r}" for r in extra.get("brainlog", [])] or ["- (no Brain Log found)"]
    return "\n".join(L) + "\n"


def brainlog_rules(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    return [m.group(1).strip() for m in re.finditer(r"^### \d{4}-\d{2}-\d{2}: (.+)$", text, re.M)]


def stop_message(issues: list[dict]) -> str:
    return "; ".join(f"gate {i['gate']} {i['scene']}: {i['problem']}" for i in issues if i["level"] == "error")
