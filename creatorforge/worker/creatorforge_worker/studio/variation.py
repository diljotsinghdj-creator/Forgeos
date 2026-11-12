"""The variation ledger: every film keeps about 20% fixed (the brand layer) and changes the other 80% on purpose,
starting from its subject (channels/MASTER_DIRECTIVES.md, "Every video different").

    plan(sp, ledger)            -> the film's variable layer: native material, lead and support technique, palette
                                   hue (from the subject, away from the last films), opening shot, tempo, camera
                                   grammar, transition family, sound palette
    check(sp, plan, ledger)     -> problems ({level, scene, problem}); an error stops production
    row(...) / Ledger           -> one row per film, kept in <data>/variation_ledger.json (and as markdown)
    keyframes(...)              -> the opening, climax and ending frames beside the last three films' (qc sheet), with a
                                   numeric "could these be swapped?" score

The lead technique is measured from the scenes themselves, not taken from what the screenplay declares.
"""
from __future__ import annotations

import colorsys
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

TECHNIQUES = ("data", "documents", "maps", "collage", "3d", "illustration")
KIND_TECHNIQUE = {
    **{k: "data" for k in ("counter", "bignumber", "number", "stack", "stand", "fan", "trend", "slice", "seats", "pie", "chart",
                            "columns", "dots", "table", "polltrack", "area", "candles", "pyramid", "squares", "icons", "units", "tiles", "pile", "grids")},
    **{k: "documents" for k in ("courtdoc", "reveal", "clipping", "newscard", "headline", "document", "quote", "desk", "interview",
                                 "article", "social", "chat", "tornsplit", "comments", "trending", "search", "reel")},
    **{k: "maps" for k in ("pinmap", "route", "arrows", "railmap", "sizemap", "heatmap", "shrink", "morph", "borders", "flowmap",
                            "satellite", "fly", "map", "clockmap", "globe", "sunrise", "zones", "wash")},
    **{k: "collage" for k in ("frame", "poster", "hero", "opener", "pinboard", "photos", "photo", "photoline", "tv", "compare", "footage", "photo3d")},
    **{k: "3d" for k in ("bars3d", "prism", "explode", "title3d", "terrain3d", "towers3d", "planets")},
    **{k: "illustration" for k in ("animate", "statement", "myth", "staircase", "scale", "blueprint", "flowchart", "linkmap",
                                    "orgchart", "steps", "timeline", "endcard", "chapter", "stamp", "sign", "clock", "calendar", "conveyor")},
}
# transitions grouped into families; a film's family is the one most of its cuts belong to
FAMILIES = {"wipes": ("wipe", "slide", "page", "tear", "reveal", "iris", "squeeze"),
            "match cuts": ("match", "dissolve", "fade", "morph"),
            "camera moves": ("push", "zoom", "whip", "dive", "drop"),
            "hard cuts": ("cut", "dipcut", "dip", "flash", "blur")}

# Subject -> visual language (starting points to break away from, not templates). hues: candidate accent hues (degrees)
SUBJECTS = {
    "money":      {"native": "prices, flows, experiments", "lead": "data", "support": "illustration", "hues": [140, 40, 95],
                   "camera": "steady push-ins", "tempo": 4.0, "family": "camera moves", "sound": "dry pulse; coin and register textures"},
    "politics":   {"native": "documents, institutions, votes", "lead": "documents", "support": "illustration", "hues": [0, 220, 30, 200],
                   "camera": "static, hard cuts", "tempo": 1.5, "family": "hard cuts", "sound": "low drone; typewriter ticks"},
    "evolution":  {"native": "fossils, anatomy, timelines", "lead": "illustration", "support": "maps", "hues": [30, 90, 45, 15],
                   "camera": "slow pans and parallax", "tempo": 4.0, "family": "camera moves", "sound": "natural ambience; sparse strings"},
    "mind":       {"native": "experiments, illusions", "lead": "3d", "support": "illustration", "hues": [280, 190, 320],
                   "camera": "moves through space", "tempo": 4.0, "family": "match cuts", "sound": "soft synth; glitch accents"},
    "fear":       {"native": "official statistics, news imagery", "lead": "data", "support": "documents", "hues": [5, 20, 350],
                   "camera": "slow reveals", "tempo": 4.0, "family": "wipes", "sound": "heartbeat; sub-bass"},
    "technology": {"native": "interfaces, systems", "lead": "illustration", "support": "data", "hues": [180, 300, 160],
                   "camera": "fast wipes", "tempo": 1.5, "family": "wipes", "sound": "clicks; light electronic beat"},
    "culture":    {"native": "interviews, places, archival photos", "lead": "collage", "support": "maps", "hues": [25, 200, 340],
                   "camera": "slow cinematic moves, long holds", "tempo": 4.0, "family": "camera moves", "sound": "piano or acoustic bed"},
}
GENRE_SUBJECT = {"economics": "money", "politics": "politics", "investigation": "politics", "geopolitics": "politics",
                 "history": "culture", "human": "culture", "science": "evolution", "environment": "evolution"}
EFFECT_CAP = 3


def hue_of(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)[0] * 360


def hex_of(hue: float, light: float = .46, sat: float = .72) -> str:
    r, g, b = colorsys.hls_to_rgb((hue % 360) / 360, light, sat)
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in (r, g, b))


SIGNATURE_HUE = 50.0   # the signature yellow #FFDD33 (media/vox.py SIGNATURE)


def hue_gap(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _kind(graphic: str) -> str:
    return str(graphic or "").split(":")[0].strip().lower()


def techniques(sp: dict) -> Counter:
    return Counter(KIND_TECHNIQUE.get(_kind(s.get("graphic")), "illustration") for s in sp.get("scenes") or [])


def family_of(transition: str) -> str:
    t = (transition or "").lower()
    return next((f for f, ts in FAMILIES.items() if t in ts), "hard cuts")


def subject_of(sp: dict) -> str:
    s = str(sp.get("subject", "")).strip().lower()
    return s if s in SUBJECTS else GENRE_SUBJECT.get(str(sp.get("genre", "")).lower(), "politics")


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def rows(self, channel: str | None = None) -> list[dict]:
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            rows = []
        return [r for r in rows if channel is None or r.get("channel") == channel]

    def add(self, row: dict) -> None:
        rows = [r for r in self.rows() if r.get("film") != row.get("film")] + [row]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    def markdown(self) -> str:
        cols = ("film", "date", "channel", "question", "native", "lead", "support", "accent", "opening", "family", "tempo", "sound")
        out = ["# Variation ledger", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for r in self.rows():
            out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/")[:60] for c in cols) + " |")
        return "\n".join(out)


def plan(sp: dict, prev: list[dict]) -> dict:
    """The variable layer for this film, chosen from its subject and away from the channel's last films."""
    subj = subject_of(sp)
    base = SUBJECTS[subj]
    last3 = prev[-3:]
    used = [hue_of(r["accent"]) for r in last3 if re.fullmatch(r"#[0-9A-Fa-f]{6}", str(r.get("accent", "")))]
    # the subject's own hues first; when none clears the last films, walk the wheel in 15-degree steps
    cands = list(base["hues"]) + [h for h in range(0, 360, 15) if h not in base["hues"]]
    # a film's accent keeps clear of the channel's signature yellow, so the highlighter always stands out
    cands = [h for h in cands if hue_gap(h, SIGNATURE_HUE) >= 25] or cands
    def score(h):
        if not used:
            return (1, 0)
        return (hue_gap(h, used[-1]) >= 120, min(hue_gap(h, u) for u in used))
    hue = max(cands, key=lambda h: (score(h), -cands.index(h) * 1e-6))
    t = techniques(sp)
    ranked = [k for k, _ in t.most_common()]
    return {"subject": subj, "native": sp.get("native_material") or base["native"],
            "lead": ranked[0] if ranked else base["lead"], "support": ranked[1] if len(ranked) > 1 else base["support"],
            "suggested_lead": base["lead"], "accent": hex_of(hue), "hue": hue, "camera": base["camera"],
            "tempo": float(sp.get("tempo") or base["tempo"]), "family": sp.get("transition_family") or base["family"],
            "sound": sp.get("sound_palette") or base["sound"],
            "opening": _kind((sp.get("scenes") or [{}])[0].get("graphic"))}


def check(sp: dict, p: dict, prev: list[dict]) -> list[dict]:
    out = []

    def add(level, scene, msg):
        out.append({"level": level, "scene": scene, "problem": msg})
    concept = sp.get("concept") or {}
    if not concept.get("central_question"):
        add("error", "concept", "no central question (one line)")
    if not (concept.get("claim") or sp.get("claim")):
        add("error", "concept", "no one-sentence claim")
    if not sp.get("native_material"):
        add("warning", "concept", f"native material not named; the subject's default is used ({p['native']})")
    last2, last3 = prev[-2:], prev[-3:]
    if any(r.get("lead") == p["lead"] for r in last2):
        add("error", "variation", f"lead technique '{p['lead']}' was the lead of one of the last two films")
    if len(prev) >= 2 and all(r.get("lead") == p["lead"] for r in prev[-2:]):
        add("error", "variation", f"'{p['lead']}' would lead three films in a row")
    hues = [hue_of(r["accent"]) for r in last3 if re.fullmatch(r"#[0-9A-Fa-f]{6}", str(r.get("accent", "")))]
    if hues and hue_gap(p["hue"], hues[-1]) < 120:
        add("error", "variation", f"palette hue {p['hue']:.0f}° is within a third of the wheel of the last film's ({hues[-1]:.0f}°)")
    for h in hues[:-1]:
        if hue_gap(p["hue"], h) < 120:
            add("warning", "variation", f"palette hue {p['hue']:.0f}° is {hue_gap(p['hue'], h):.0f}° from an earlier film's "
                                        f"({h:.0f}°); with three films spread round the wheel 120° from all is not always possible")
    if any(r.get("opening") == p["opening"] for r in last3):
        add("error", "variation", f"opening shot type '{p['opening']}' was used by one of the last three films")
    if prev and prev[-1].get("family") == p["family"]:
        add("error", "variation", f"transition family '{p['family']}' was the last film's")
    fx = Counter(m.group(1).strip().lower() for s in sp.get("scenes") or []
                 for m in re.finditer(r"\|\s*fx\s*[:=]\s*([^|]+)", str(s.get("graphic", "")), re.I))
    for name, n in fx.items():
        if n > EFFECT_CAP:
            add("error", "effects", f"the '{name}' effect is used {n} times (at most {EFFECT_CAP} a film)")
    if len({s.get("act") for s in sp.get("scenes") or []}) < 2:
        add("error", "sound", "one music cue only: the score needs at least two (it changes with the acts)")
    for s in sp.get("scenes") or []:
        role = str(s.get("purpose", "")).lower()
        if role and role not in ("explain", "prove", "orient", "move"):
            add("warning", str(s.get("id")), "purpose should be explain, prove, orient or move")
    return out


def row(film: str, sp: dict, p: dict, keyframes: list[str] | None = None, beds: list[str] | None = None,
        avg_shot: float | None = None) -> dict:
    return {"film": film, "date": date.today().isoformat(), "channel": sp.get("channel", ""),
            "question": (sp.get("concept") or {}).get("central_question", ""),
            "claim": (sp.get("concept") or {}).get("claim") or sp.get("claim", ""), "native": p["native"], "lead": p["lead"],
            "support": p["support"], "accent": p["accent"], "opening": p["opening"], "family": p["family"],
            "tempo": p["tempo"], "avg_shot": avg_shot, "camera": p["camera"], "sound": p["sound"],
            "keyframes": keyframes or [], "beds": sorted(set(beds or []))}


def markdown(p: dict, issues: list[dict]) -> str:
    lines = ["# Variation (this film's variable layer)", ""] + [f"- **{k}**: {v}" for k, v in p.items()]
    lines += ["", "## Checks", ""] + ([f"- **{i['level']}** {i['scene']}: {i['problem']}" for i in issues] or ["- all clear"])
    return "\n".join(lines)


def _signature(png: Path):
    """A coarse colour histogram (8 levels a channel, so near-identical shades match) and the texture (edge energy)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB").resize((96, 54)), int) // 32
    h = np.bincount((a[..., 0] * 64 + a[..., 1] * 8 + a[..., 2]).ravel(), minlength=512).astype(float)
    g = np.asarray(Image.open(png).convert("L").resize((96, 54)), float)
    grad = np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean()
    return h / h.sum(), grad


def swappable(a: list[Path], b: list[Path]) -> float:
    """0..1: how alike two films' key frames are (colour histograms and texture); above 0.85 they could be swapped."""
    import numpy as np
    if not a or not b:
        return 0.0
    sims = []
    for x, y in zip(a, b):
        hx, gx = _signature(x)
        hy, gy = _signature(y)
        colour = float(np.minimum(hx, hy).sum())
        texture = 1 - min(1.0, abs(gx - gy) / max(gx, gy, 1e-6))
        sims.append(.75 * colour + .25 * texture)
    return round(sum(sims) / len(sims), 3)


def keyframes(video: Path, times: list[float], out_dir: Path, prev: list[dict], sheet: Path) -> tuple[list[str], list[dict]]:
    """Grabs this film's opening, climax and ending frames, sets them beside the last three films' and scores how
    alike they are. Returns (frame paths, problems)."""
    import subprocess
    from PIL import Image, ImageDraw
    out_dir.mkdir(parents=True, exist_ok=True)
    mine = []
    for i, t in enumerate(times[:3]):
        f = out_dir / f"key{i + 1}.png"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                        "-vf", "scale=480:-2", str(f)], check=True)
        mine.append(f)
    problems, rows = [], [("this film", mine)]
    for r in prev[-3:]:
        fs = [Path(k) for k in r.get("keyframes", []) if Path(k).is_file()]
        if fs:
            rows.append((r.get("film", "?"), fs))
            s = swappable(mine, fs)
            if s > .85:
                problems.append({"level": "warning", "scene": "keyframes",
                                 "problem": f"key frames look like {r.get('film')}'s (similarity {s}): redesign before polishing"})
    w, h = 480, 270
    im = Image.new("RGB", (w * 3 + 200, h * len(rows)), (24, 24, 24))
    d = ImageDraw.Draw(im)
    for j, (name, fs) in enumerate(rows):
        d.text((10, j * h + 10), str(name)[:22], fill=(235, 235, 235))
        for i, f in enumerate(fs[:3]):
            im.paste(Image.open(f).convert("RGB").resize((w, h)), (200 + i * w, j * h))
    sheet.parent.mkdir(parents=True, exist_ok=True)
    im.save(sheet)
    return [str(f) for f in mine], problems
