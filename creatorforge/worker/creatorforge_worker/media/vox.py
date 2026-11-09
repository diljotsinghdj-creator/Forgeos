"""The Vox look: editorial collage scenes drawn as smooth vector animation (SVG in headless Chromium, like motion.py),
with one shared style kit so every scene of every video looks like the same designed magazine:

- printed paper (fine grain, soft mottling) in one paper tone, black ink and ONE accent colour per video
- real cut-out photos (cutouts.py: halftone black-and-white with a white paper edge and a soft shadow), big:
  the subject fills 50-70% of the frame
- type: Anton (big words), Playfair Display (black-box serif headlines), Inter (tags), JetBrains Mono (notes)
- black boxes with white type, small tags, highlighter sweeps, brush strokes, accent discs and bars
- the big word sits BEHIND the subject (depth), blurred accent orb, vertical side text, a mono date/place line,
  crosshair marks, thin leader-line callouts
- motion the Vox way: pieces drop, slide or snap in on a 12 fps "stutter" while the camera pushes in smoothly with
  a little parallax (the background moves less than the subject)

Scenes (one per script line):
    Hero: gavel | THE VERDICT | 2019 · Supreme Court | five judges, one voice
          subject(s) "a + b" or person:Name | headline | tags (·) | a note with a leader line
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
import os
import re
from pathlib import Path

from .ff import MediaError

FONTS = Path(__file__).parent / "vendor" / "fonts"
ACCENTS = {"yellow": "#F2C200", "red": "#D7262B", "blue": "#2D6BDB", "orange": "#F07A1A", "teal": "#14968A",
           "green": "#2E9B4F"}
PAPERS = {"cream": "#EFE8DA", "grey": "#E5E3DE", "white": "#F4F2EE", "dark": "#1B1B1D", "kraft": "#C9A777", "crumple": "#EADFC9", "atlas": "#E9E1C8",
          "grid": "#F1F0EC"}
INK = "#141414"
LAYOUTS = ("word", "disc", "box", "bars", "grid")
# symbolic props laid over a real photo (opt-in editorial cartoons; the face itself is never changed)
PROPS = ("blindfold", "mask", "zip", "crown", "strings", "chains", "megaphone")
FACE_PROPS = ("blindfold", "mask", "zip", "crown")
KINDS = ("hero", "desk", "pinboard", "opener", "reveal", "clipping", "pinmap", "bignumber",
         "seats", "stack", "stand", "fan", "trend", "slice", "route", "compare", "photoline", "tv",
         "clockmap", "tornsplit", "newscard", "blueprint", "pyramid", "flowchart", "linkmap", "orgchart", "heatmap",
         "courtdoc", "table", "interview", "endcard", "polltrack", "area", "candles", "arrows", "railmap", "sizemap",
         "borders", "morph")


# A look per video, so no two films share one face: paper, type, map colours and marker pen differ, the method doesn't.
# head = headline serif, big = condensed number face, hand = marker handwriting.
LOOKS = {
    "archive":   {"paper": "#EFE8DA", "head": "Playfair", "big": "Anton", "hand": "Caveat", "mark": "#D7262B",
                  "sea": "#B8CDD1", "land": "#EFE3C2", "edge": "#8E7E5C", "accent": "yellow"},
    "newsprint": {"paper": "#E5E3DE", "head": "DMSerif", "big": "Bebas", "hand": "Kalam", "mark": "#1F4FB8",
                  "sea": "#C3CFD3", "land": "#F3EFE4", "edge": "#6F6F6A", "accent": "red"},
    "kraft":     {"paper": "#D8C39C", "head": "Archivo", "big": "Oswald", "hand": "Marker", "mark": "#111111",
                  "sea": "#9FB4B0", "land": "#E9DCBC", "edge": "#5E4E33", "accent": "orange"},
    "chart":     {"paper": "#F4F2EE", "head": "Inter", "big": "Archivo", "hand": "Caveat", "mark": "#E0442C",
                  "sea": "#A9C6E0", "land": "#F7F4EC", "edge": "#7C8A99", "accent": "blue"},
    "sepia":     {"paper": "#E8DCC0", "head": "Playfair", "big": "Bebas", "hand": "Kalam", "mark": "#8B1E1E",
                  "sea": "#C7C1A6", "land": "#EDE3C8", "edge": "#7A6A48", "accent": "#A8652A"},
    "engraving": {"paper": "#E6E4DC", "head": "Playfair", "big": "Oswald", "hand": "Caveat", "mark": "#1C1C1C",
                  "sea": "#AEB9BC", "land": "#ECE6D6", "edge": "#55524A", "accent": "#7B2D26"},
    "field":     {"paper": "#E9EDE4", "head": "DMSerif", "big": "Anton", "hand": "Marker", "mark": "#C2410C",
                  "sea": "#B5D0C8", "land": "#EEE9D6", "edge": "#6E7B66", "accent": "teal"},
}


# Layouts per graphic type, rotated through a video so the same kind never gets the same layout twice in a row.
# base = the scene as designed; mirror = the composition flipped (words and photos stay readable, never for maps,
# timelines, parliaments or before/after, where left and right mean something); card = the whole graphic printed on a
# paper card lying on a desk; side = BigNumber's own second layout.
_FLIP = ("hero", "opener", "newscard", "tornsplit", "desk", "pinboard", "clipping", "tv", "blueprint", "reveal",
         "interview")
LAYOUT_SETS = {k: (["base", "mirror", "card"] if k in _FLIP else ["base", "card"]) for k in KINDS}
LAYOUT_SETS["bignumber"] = ["base", "side", "card"]
DESKS = ("#3B2F25", "#5A4632", "#2E3A40", "#6B5B4B", "#262626")


# "| badge: alleged" on any scene: the standing of what is on screen, said plainly in the corner
BADGES = {"verified": ("VERIFIED", "#1F7A4D"), "record": ("ON RECORD", "#1F7A4D"), "court": ("COURT RECORD", "#1F4FB8"),
          "official": ("OFFICIAL DATA", "#1F4FB8"), "reported": ("REPORTED", "#5A5A5A"), "alleg": ("ALLEGED", "#C2410C"),
          "claim": ("CLAIM", "#C2410C"), "denie": ("DENIED", "#5A5A5A"), "response": ("RESPONSE", "#5A5A5A"),
          "unverified": ("UNVERIFIED", "#B3261E"), "opinion": ("OPINION", "#7A3E8C"), "estimate": ("ESTIMATE", "#5A5A5A")}
FX = ("dust", "embers", "snow", "rain", "confetti", "sparks")       # "| fx: embers": particles over the scene
EXITS = ("rise", "fall", "side", "shrink")                           # how a scene leaves; rotated, or "| exit: none"


def wants_voice(kind: str, spec: str) -> bool:
    """Scenes whose graphics move with the narration: an interview always, any scene that says '| voice'."""
    return kind == "interview" or bool(re.search(r"\|\s*voice\s*(\||$)", spec or "", re.I))


def layout_for(kind: str, turn: int, seed: int) -> str:
    """The layout of this kind's `turn`-th graphic (0, 1, 2...) in a video with this seed."""
    opts = LAYOUT_SETS.get(kind, ["base"])
    return opts[(turn + seed + _seed("lay", kind)) % len(opts)]


def plan_layouts(kinds: list[str], seed: int) -> list[str]:
    """A layout for every graphic of a video, in order: each kind takes turns through its layouts, and a shot never
    has the same layout as the shot before it when its kind has another one ('' for a line that isn't a Vox kind)."""
    turn: dict[str, int] = {}
    out: list[str] = []
    for k in kinds:
        if k not in KINDS:
            out.append("")
            continue
        opts = LAYOUT_SETS.get(k, ["base"])
        lay = layout_for(k, turn.get(k, 0), seed)
        if out and out[-1] == lay and len(opts) > 1:
            turn[k] = turn.get(k, 0) + 1
            lay = layout_for(k, turn[k], seed)
        turn[k] = turn.get(k, 0) + 1
        out.append(lay)
    return out


def _lum(hex_: str) -> float:
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio of two colours (1 = the same, 21 = black on white)."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable(colour: str, paper: str, least: float = 2.6) -> str:
    """The colour, darkened just enough to be read as large type on this paper (yellow on cream becomes mustard).
    Blocks, discs and bars keep the true accent; only type set straight on the paper uses this."""
    c = colour
    for _ in range(24):
        if contrast(c, paper) >= least:
            break
        r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
        c = "#%02X%02X%02X" % (int(r * 0.93), int(g * 0.93), int(b * 0.93))
    return c


def look_of(theme: str) -> dict:
    """'editorial~2@red/kraft' -> the kraft look (default: archive, the original look)."""
    name = ((theme or "").split("/") + ["", ""])[1]
    return LOOKS.get(name.strip().lower(), LOOKS["archive"])


def choose_look(text: str, era: int | None = None) -> str:
    """The look for a video: an old story (before 1950) gets sepia; otherwise one picked from the script itself, so
    the same script always gets the same look and two scripts rarely share one."""
    if era is not None and era < 1950:
        return "sepia"
    names = [k for k in LOOKS if k not in ("sepia", "engraving")]
    return names[_seed("look", text) % len(names)]


def era_of(text: str) -> int | None:
    """The year the story is set in: the middle of the years the script names (1500-2099), so one look back at 1914
    in a story about 2018 doesn't turn the whole video sepia. None when it names no year."""
    ys = sorted(int(y) for y in re.findall(r"(?<!\d)(1[5-9]\d\d|20\d\d)(?!\d)", text or ""))
    return ys[(len(ys) - 1) // 2] if ys else None


def accent_of(theme: str) -> str:
    """'editorial~2@red' -> the red accent; a hex colour is used as given; default yellow."""
    _, _, acc = (theme or "").partition("@")
    acc = acc.partition("/")[0].strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", acc):
        return acc
    return ACCENTS.get(acc.lower(), ACCENTS["yellow"])


def _seed(*parts) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


# ---- reading a scene line -------------------------------------------------------------------------------------------
def parse_hero(spec: str) -> dict | None:
    """'gavel + crowd | THE VERDICT | 2019 · Supreme Court | note' -> plan (no pictures yet)."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    opts = {}
    keep = []
    for p in parts[1:]:
        m = re.fullmatch(r"(style|layout|word|date|place|side|prop)\s*[:=]\s*(.+)", p, re.I)
        if m:
            opts[m.group(1).lower()] = m.group(2).strip()
        else:
            keep.append(p)
    subjects = [s.strip() for s in re.split(r"\s+\+\s+|\s*&\s*", parts[0]) if s.strip()][:3]
    headline = keep[0] if keep else ""
    tags = [t.strip() for t in re.split(r"·|•|;", keep[1]) if t.strip()][:5] if len(keep) > 1 else []
    note = keep[2] if len(keep) > 2 else ""
    layout = (opts.get("style") or opts.get("layout") or "").lower()
    if layout not in LAYOUTS:
        layout = LAYOUTS[_seed(spec) % len(LAYOUTS)]
    word = opts.get("word") or ""
    if not word and layout == "word":
        # the big word behind the subject: the headline when short, else its strongest word
        hw = re.sub(r"[^\w\s'-]", "", headline).split()
        word = headline if 0 < len(hw) <= 2 else (max(hw, key=len) if hw else subjects[0].split(":")[-1])
    meta = [x for x in (opts.get("date", ""), opts.get("place", "")) if x]
    prop = opts.get("prop", "").strip().lower()
    return {"type": "hero", "subjects": subjects, "headline": headline, "tags": tags, "note": note,
            "layout": layout, "word": word.upper()[:14], "meta": meta, "side": opts.get("side", ""),
            "prop": prop if prop in PROPS else "",
            "seed": _seed(spec) % 10000}


_DATE = re.compile(r"^(?:(\d{1,2})\s+)?([A-Za-z]{3,9})\.?\s+(?:(\d{1,2}),?\s+)?(\d{4})$")


def _item(text: str) -> dict:
    """An evidence item: a date card, a photo (object or person:Name) or a word card."""
    from . import cutouts
    t = text.strip()
    m = _DATE.match(t)
    if m:
        return {"kind": "date", "mon": m.group(2)[:3].upper(), "day": m.group(1) or m.group(3) or "", "year": m.group(4)}
    if t.lower().startswith("person:") or cutouts.resolve(t):
        return {"kind": "photo", "name": t}
    return {"kind": "word", "text": t.upper()[:22]}


def _split_list(s: str) -> list[str]:
    return [x.strip() for x in re.split(r"\s+\+\s+|·|•|;", s or "") if x.strip()]


def parse_desk(spec: str) -> dict | None:
    """'Desk: dna + documents + pen | Methylated DNA | note' - photos and props on grid paper."""
    parts = [p.strip() for p in (spec or "").split("|")]
    subs = _split_list(parts[0])[:4]
    if not subs:
        return None
    return {"type": "desk", "subjects": subs, "label": parts[1] if len(parts) > 1 else "",
            "note": parts[2] if len(parts) > 2 else "", "seed": _seed(spec) % 10000}


def parse_evidence(spec: str) -> dict | None:
    """'Evidence: person:Name · old phone · DEC 20 1962 · SOLVED | title' - the first item in the middle."""
    parts = [p.strip() for p in (spec or "").split("|")]
    items = [_item(x) for x in re.split(r"·|•|;", parts[0]) if x.strip()][:6]
    if len(items) < 2:
        return None
    return {"type": "evidence", "items": items, "title": parts[1] if len(parts) > 1 else "",
            "subjects": [i["name"] for i in items if i["kind"] == "photo"], "tone": "kraft", "seed": _seed(spec) % 10000}


def parse_opener(spec: str) -> dict | None:
    """'Opener: person:Name | He noticed *something strange* | Chapter 2' - colour panel + photo."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return {"type": "opener", "subjects": [parts[0]], "headline": parts[1], "kicker": parts[2] if len(parts) > 2 else "",
            "seed": _seed(spec) % 10000}


def parse_reveal(spec: str) -> dict | None:
    """'Reveal: line · line · line | title | the phrase to highlight' - a magnifier sweeps a document."""
    parts = [p.strip() for p in (spec or "").split("|")]
    rows = [x.strip() for x in re.split(r"·|•|;", parts[0]) if x.strip()][:7]
    if not rows:
        return None
    return {"type": "reveal", "rows": rows, "title": parts[1] if len(parts) > 1 else "",
            "mark": parts[2] if len(parts) > 2 else "", "subjects": ["hand holding"], "seed": _seed(spec) % 10000}


def parse_headline(spec: str) -> dict | None:
    """'Headline: Manufacturers may sack workers | The Hindu, Jan 2024 | factory + crowd | 02'."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    num = next((p for p in parts[2:] if re.fullmatch(r"\d{1,3}", p)), "")
    subs = next((_split_list(p) for p in parts[2:] if p and p != num), [])[:3]
    return {"type": "headline", "text": parts[0][:110], "source": parts[1] if len(parts) > 1 else "",
            "subjects": subs, "number": num, "seed": _seed(spec) % 10000}


def parse_pinmap(spec: str) -> dict | None:
    """'Pinmap: Kota | Amit Shah's speech to IT cell volunteers | Hindustan Times, Sep 2018'."""
    from . import maps
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    f = maps._find(parts[0])
    if not f:
        return None
    if f["kind"] == "country":
        country, pin = f, None
    else:
        pin = (f["lon"], f["lat"])
        # the country around the place: the one whose borders contain it (India first, the most common case)
        country = None
        if 6 <= f["lat"] <= 37 and 68 <= f["lon"] <= 98:
            ind = maps._find("India")
            if ind and _inside(f["lon"], f["lat"], ind["rings"]):
                country = ind
        if country is None:
            for c in maps._world()["countries"]:
                if _inside(f["lon"], f["lat"], c["r"]):
                    country = {"kind": "country", "name": c["n"], "rings": c["r"]}
                    break
        if country is None:
            return None
    rings = [r for r in country["rings"] if len(r) > 3]
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    def norm(lon, lat):
        return [round((lon - lon0) * k, 4), round(lat1 - lat, 4)]
    span = max((lon1 - lon0) * k, lat1 - lat0)
    shapes = [[[round(v / span, 4) for v in norm(x, y)] for x, y in r[:: max(1, len(r) // 400)]] for r in rings]
    atlas = any(re.fullmatch(r"(style\s*[:=]\s*)?atlas", x.strip(), re.I) for x in parts[1:])
    parts = [x for x in parts if not re.fullmatch(r"(style\s*[:=]\s*)?atlas", x.strip(), re.I)]
    pen = any(re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I) for x in parts[1:])
    parts = [x for x in parts if not re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I)]
    pinned = next((x for x in parts[1:] if x.lower().startswith("person:")), "")
    parts = [x for x in parts if x != pinned]
    out = {"type": "pinmap", "place": f.get("name", parts[0]), "shapes": shapes, "atlas": atlas, "tone": "atlas" if atlas else "",
           "subjects": [pinned] if pinned else [], "pen": pen,
           "box": [round((lon1 - lon0) * k / span, 4), round((lat1 - lat0) / span, 4)],
           "headline": parts[1] if len(parts) > 1 else "", "source": parts[2] if len(parts) > 2 else "",
           "country": country.get("name", ""), "seed": _seed(spec) % 10000}
    if pin:
        out["pin"] = [round(v / span, 4) for v in norm(*pin)]
    return out


def parse_number(spec: str) -> dict | None:
    """'Number: 1984 | television | War is peace | George Orwell' - a huge number the subject breaks out of."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not re.search(r"\d", parts[0]):
        return None
    # Latin figures are cut short ("₹29.7 cr"); a Hindi unit is never cut mid-word (the marks would be lost)
    return {"type": "number", "number": parts[0][:16] if re.search(r"[\u0900-\u097F]", parts[0]) else parts[0][:8], "subjects": _split_list(parts[1])[:1] if len(parts) > 1 else [],
            "caption": parts[2] if len(parts) > 2 else "", "kicker": parts[3] if len(parts) > 3 else "",
            "seed": _seed(spec) % 10000}


_NUM = re.compile(r"([₹$£€]?)\s*(-?\d[\d,]*(?:\.\d+)?)\s*(%|cr(?:ore)?|lakh|k|m|bn|b|million|billion|kt|seats)?", re.I)


def _pairs(text: str) -> list[dict]:
    """'NDA 293, INDIA 234' / 'UP ₹40 crore; Bihar 25' -> [{label, value, shown}] (label may come after)."""
    out = []
    for part in re.split(r",(?!\d{2,3}\b)|;|·|•", text or ""):
        part = part.strip()
        m = None
        for m in _NUM.finditer(part):
            pass
        if not part or m is None:
            continue
        label = (part[:m.start()] + part[m.end():]).strip(" :-=")
        try:
            v = float(m.group(2).replace(",", ""))
        except ValueError:
            continue
        out.append({"label": label[:28], "value": v, "shown": m.group(0).strip()})
    return out


def parse_seats(spec: str) -> dict | None:
    """'Seats: NDA 293, INDIA 234, Others 16 | Lok Sabha 2024' - a parliament of dots; majority line drawn."""
    parts = [p.strip() for p in (spec or "").split("|")]
    groups = [g for g in _pairs(parts[0]) if g["value"] > 0][:8]
    if not groups:
        return None
    total = int(sum(g["value"] for g in groups))
    if not 3 <= total <= 1200:
        return None
    return {"type": "seats", "groups": groups, "total": total, "majority": total // 2 + 1,
            "title": parts[1] if len(parts) > 1 else "", "seed": _seed(spec) % 10000}


MATERIALS = ("coins", "pillars", "chimneys", "buildings", "books", "bars")


def parse_stack(spec: str) -> dict | None:
    """'Stack: coins | UP 40, Bihar 25, MP 12 | Seats by state' - bars drawn as real things."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2:
        return None
    mat = parts[0].lower().rstrip("s") + "s" if parts[0] else "bars"
    mat = next((m for m in MATERIALS if m.startswith(mat[:4])), "bars")
    vals = [v for v in _pairs(parts[1]) if v["value"] >= 0][:7]
    if len(vals) < 2:
        return None
    return {"type": "stack", "material": mat, "values": vals, "title": parts[2] if len(parts) > 2 else "",
            "seed": _seed(spec) % 10000}


def parse_stand(spec: str) -> dict | None:
    """'Stand: farmer ₹10,218 vs CEO ₹4,24,114 | 2024 | per month' - figures standing on their bars."""
    parts = [p.strip() for p in (spec or "").split("|")]
    sides = [x.strip() for x in re.split(r"\s+vs\.?\s+", parts[0], flags=re.I) if x.strip()][:3]
    vals = []
    for sd in sides:
        pr = _pairs(sd)
        if not pr:
            return None
        vals.append(pr[0])
    if len(vals) < 2:
        return None
    from .cutouts import figure
    return {"type": "stand", "values": vals, "subjects": [figure(v["label"]) for v in vals],
            "title": parts[1] if len(parts) > 1 else "", "note": parts[2] if len(parts) > 2 else "",
            "seed": _seed(spec) % 10000}


def parse_fan(spec: str) -> dict | None:
    """'Fan: Hotels $378M, Tokens $57M, Licensing $31M | Trump's $600M year | person:Donald Trump'."""
    parts = [p.strip() for p in (spec or "").split("|")]
    vals = [v for v in _pairs(parts[0]) if v["value"] > 0][:8]
    if len(vals) < 2:
        return None
    return {"type": "fan", "values": sorted(vals, key=lambda v: -v["value"]), "title": parts[1] if len(parts) > 1 else "",
            "subjects": [parts[2]] if len(parts) > 2 and parts[2] else [], "seed": _seed(spec) % 10000}


def parse_trend(spec: str) -> dict | None:
    """'Trend: 1990 100, 2000 62, 2010 31, 2024 12 | What ₹100 buys | rupee note' - the picture fills under the line."""
    parts = [p.strip() for p in (spec or "").split("|")]
    pts = []
    for part in re.split(r",(?!\d{2,3}\b)|;|·", parts[0]):
        m = re.match(r"\s*(\d{4}|[A-Za-z]{3,9}\s*\d{0,4})\s*[:=]?\s*([₹$£€]?)\s*(-?\d[\d,]*(?:\.\d+)?)\s*(%|cr|crore|lakh|k|m|bn)?", part)
        if m:
            pts.append({"x": m.group(1).strip(), "value": float(m.group(3).replace(",", "")),
                        "shown": f"{m.group(2)}{m.group(3)}{m.group(4) or ''}"})
    if len(pts) < 2:
        return None
    return {"type": "trend", "points": pts[:12], "title": parts[1] if len(parts) > 1 else "",
            "subjects": [parts[2]] if len(parts) > 2 and parts[2] else [], "seed": _seed(spec) % 10000}


def parse_slice(spec: str) -> dict | None:
    """'Slice: 12% | brain | activated' - a wedge of the real object, in the accent colour."""
    parts = [p.strip() for p in (spec or "").split("|")]
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", parts[0] if parts else "")
    if not m or len(parts) < 2 or not parts[1]:
        return None
    return {"type": "slice", "pct": min(100.0, float(m.group(1))), "shown": m.group(0), "subjects": [parts[1]],
            "label": parts[2] if len(parts) > 2 else "", "seed": _seed(spec) % 10000}


def _geo(names: list[str]) -> list[dict]:
    from . import maps
    out = []
    for n in names:
        f = maps._find(n)
        if not f:
            return []
        if f["kind"] == "city":
            out.append({"name": f["name"], "lon": f["lon"], "lat": f["lat"]})
        else:
            big = max(f["rings"], key=len)          # the mainland: a box round every island puts Russia in the Atlantic
            xs, ys = [x for x, _ in big], [y for _, y in big]
            out.append({"name": f["name"], "lon": (min(xs) + max(xs)) / 2, "lat": (min(ys) + max(ys)) / 2})
    return out


def parse_route(spec: str) -> dict | None:
    """'Route: New Delhi → Dubai → London | The escape route | plane' - a paper map, dashed routes drawn on, the
    plane (or ship/car/train) travelling them, pins at every stop."""
    from . import maps
    parts = [p.strip() for p in (spec or "").split("|")]
    stops = _geo([x.strip() for x in re.split(r"→|->|\bto\b", parts[0]) if x.strip()][:6])
    if len(stops) < 2:
        return None
    vehicle = next((p.lower() for p in parts[2:] if p and "atlas" not in p.lower() and p.strip().lower() not in ("pen", "style: pen")), "plane")
    vehicle = next((v for v in ("plane", "ship", "car", "train", "truck", "bus") if v in vehicle), "plane")
    lons = [s["lon"] for s in stops]
    lats = [s["lat"] for s in stops]
    paths = []
    if vehicle == "ship":
        # a ship goes by sea: round the capes, through the canals (searoute); a leg with no sea way stays an arc
        from . import searoute
        shift = 0.0
        for a, b in zip(stops, stops[1:]):
            sp = [[x + shift, y] for x, y in searoute.path(a["lon"] - shift, a["lat"], b["lon"], b["lat"])]
            if sp:
                shift = round((sp[-1][0] - b["lon"]) / 360) * 360     # past the date line the map carries on, unwrapped
                b["lon"] = sp[-1][0]
            paths.append(sp[:: max(1, len(sp) // 90)] + ([sp[-1]] if sp else []))
        lons = [s["lon"] for s in stops] + [q[0] for sp in paths for q in sp]
        lats = lats + [q[1] for sp in paths for q in sp]
    pad_x = max(8.0, (max(lons) - min(lons)) * 0.35)
    pad_y = max(6.0, (max(lats) - min(lats)) * 0.45)
    box = [min(lons) - pad_x, min(lats) - pad_y, max(lons) + pad_x, max(lats) + pad_y]
    # the visible box keeps the frame's shape; countries that touch it are drawn
    w = maps._world()
    shapes = []
    offs = [o for o in (-360, 0, 360) if box[0] - 60 <= 180 + o and box[2] + 60 >= -180 + o]   # past the date line too
    for c in w["countries"]:
        for r in c["r"]:
            for off in offs:
                if any(box[0] - 60 <= x + off <= box[2] + 60 and box[1] - 40 <= y <= box[3] + 40 for x, y in r[:: max(1, len(r) // 30)]):
                    shapes.append([[round(x + off, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 160)]])
    from .scene_anim import icon_nodes, find_icon
    atlas = any(re.fullmatch(r"(style\s*[:=]\s*)?atlas", x.strip(), re.I) for x in parts[1:])
    pen = any(re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I) for x in parts[1:])
    parts = [x for x in parts if not re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I)]
    return {"type": "route", "pen": pen, "stops": stops, "box": box, "paths": paths, "shapes": shapes[:700], "title": parts[1] if len(parts) > 1 and not
            re.fullmatch(r"(style\s*[:=]\s*)?atlas", parts[1], re.I) else "",
            "vehicle": vehicle, "icon": icon_nodes(find_icon(vehicle) or "plane"), "pin": icon_nodes("map-pin"),
            "atlas": atlas, "tone": "atlas" if atlas else "crumple", "seed": _seed(spec) % 10000}


def parse_compare(spec: str) -> dict | None:
    """'Compare: rupee note | 1991 | 2024' (one picture, before/after) or 'Compare: a + b | before | after'."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 3 or not parts[0]:
        return None
    subs = _split_list(parts[0])[:2]
    return {"type": "compare", "subjects": subs, "left": parts[1], "right": parts[2],
            "title": parts[3] if len(parts) > 3 else "", "seed": _seed(spec) % 10000}


def parse_photoline(spec: str) -> dict | None:
    """'Photoline: 1935 Laws enacted (documents) → 1939 War begins (soldier) → 1941 Pearl Harbor (ship) | title'."""
    parts = [p.strip() for p in (spec or "").split("|")]
    items = []
    for x in re.split(r"→|->", parts[0]):
        m = re.match(r"\s*(\d{3,4}|[A-Za-z]{3}\s+\d{4})\s+([^()]+?)\s*(?:\(([^)]+)\))?\s*$", x)
        if m:
            items.append({"when": m.group(1), "what": m.group(2).strip()[:40], "pic": (m.group(3) or "").strip()})
    if len(items) < 2:
        return None
    return {"type": "photoline", "items": items[:5], "subjects": [i["pic"] for i in items[:5] if i["pic"]],
            "title": parts[1] if len(parts) > 1 else "", "tone": "grid", "seed": _seed(spec) % 10000}


def parse_tv(spec: str) -> dict | None:
    """'Tv: person:Name | 1975 broadcast | the Emergency is declared' - a picture inside an old TV set."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    return {"type": "tv", "subjects": [parts[0]], "label": parts[1] if len(parts) > 1 else "",
            "caption": parts[2] if len(parts) > 2 else "", "seed": _seed(spec) % 10000}


def _region(points: list[tuple[float, float]], pad: float = 0.35) -> tuple[list, list]:
    """Country shapes around some lon/lat points, and the box to show."""
    from . import maps
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    px = max(3.0, (max(lons) - min(lons)) * pad)
    py = max(2.5, (max(lats) - min(lats)) * pad)
    box = [min(lons) - px, min(lats) - py, max(lons) + px, max(lats) + py]
    shapes = []
    for c in maps._world()["countries"]:
        for r in c["r"]:
            if any(box[0] - 40 <= x <= box[2] + 40 and box[1] - 25 <= y <= box[3] + 25 for x, y in r[:: max(1, len(r) // 30)]):
                shapes.append({"n": c["n"], "r": [[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 220)]]})
    return box, shapes[:450]


def _inside(x: float, y: float, rings: list) -> bool:
    """Point in any of a country's rings (ray casting)."""
    for r in rings:
        inside = False
        for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1:
                inside = not inside
        if inside:
            return True
    return False


def parse_clockmap(spec: str) -> dict | None:
    """'Clockmap: Mumbai 9:30, Delhi 9:30, Kolkata 9:30, Guwahati 9:30 | One country, one clock | IST' - a clock at
    every city, joined by lines, the time in a big box."""
    parts = [p.strip() for p in (spec or "").split("|")]
    cities = []
    for x in re.split(r",|;|·", parts[0] if parts else ""):
        m = re.match(r"\s*(.+?)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*$", x.strip(), re.I)
        if not m:
            continue
        g = _geo([m.group(1)])
        if not g:
            return None
        h = int(m.group(2)) % 12 + (12 if (m.group(4) or "").lower() == "pm" else 0)
        cities.append({**g[0], "h": h, "m": int(m.group(3) or 0), "shown": f"{m.group(2)}:{m.group(3) or '00'}"})
    if len(cities) < 2:
        return None
    box, shapes = _region([(c["lon"], c["lat"]) for c in cities])
    from . import maps
    home = ""
    for c in maps._world()["countries"]:
        if c["n"] in {sh["n"] for sh in shapes} and _inside(cities[0]["lon"], cities[0]["lat"], c["r"]):
            home = c["n"]
            break
    return {"type": "clockmap", "cities": cities[:10], "box": box, "shapes": shapes, "home": home,
            "title": parts[1] if len(parts) > 1 else "",
            "zone": parts[2] if len(parts) > 2 else "", "tone": "white", "seed": _seed(spec) % 10000}


def parse_tornsplit(spec: str) -> dict | None:
    """'Tornsplit: ship + crane | One steel box | 1956' - a big condensed headline, a cut-out on the paper side, a
    torn accent panel with halftone dots and a second cut-out on it."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return {"type": "tornsplit", "subjects": _split_list(parts[0])[:2], "headline": parts[1][:40],
            "kicker": parts[2] if len(parts) > 2 else "", "seed": _seed(spec) % 10000}


def parse_newscard(spec: str) -> dict | None:
    """'Newscard: 29 Aug 2024 | The headline | the line under it | person:Name | Publisher' - a news card on grid
    paper: red date box, the headline highlighted as it is read, the person beside it, the publisher's name in type."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[1]:
        return None
    from . import cutouts
    rest = parts[2:]
    subject = next((x for x in rest if x.lower().startswith("person:") or cutouts.resolve(x)), "")
    others = [x for x in rest if x and x != subject]
    return {"type": "newscard", "date": parts[0][:24], "headline": parts[1][:120], "sub": others[0][:160] if others else "",
            "source": others[1][:40] if len(others) > 1 else "", "subjects": [subject] if subject else [],
            "tone": "grid", "seed": _seed(spec) % 10000}


def parse_blueprint(spec: str) -> dict | None:
    """'Blueprint: factory | Factory production | 3 shifts · 1,200 workers · 40 trucks a day' - a cut-out on a blue
    grid card, an arrow pointing at it, a few bullet lines."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    pts = [x.strip() for x in re.split(r"·|•|;", parts[2]) if x.strip()][:4] if len(parts) > 2 else []
    return {"type": "blueprint", "subjects": [parts[0]], "title": parts[1][:40], "points": pts, "seed": _seed(spec) % 10000}


# drawn illustrations (vendor/illustrations.js) for subjects without a photo: script word -> drawing
ILLUS = {"ship": "ship", "container ship": "ship", "cargo ship": "ship", "vessel": "ship", "boat": "ship",
         "container": "container", "shipping container": "container", "crane": "crane", "truck": "truck",
         "lorry": "truck", "factory": "factory", "factory chimney": "factory", "warehouse": "warehouse",
         "coins": "coins", "coin": "coins", "rupee coin": "coins", "cash": "banknote", "money": "banknote",
         "banknote": "banknote", "rupee note": "banknote", "notes": "banknote", "money bag": "moneybag",
         "smartphone": "smartphone", "phone": "smartphone", "mobile": "smartphone", "hand phone": "smartphone",
         "laptop": "laptop", "computer": "laptop", "television": "television", "tv": "television",
         "newspaper": "newspaper", "old newspaper": "newspaper", "news": "newspaper", "documents": "documents",
         "document": "documents", "file folder": "documents", "report": "documents", "skyscraper": "skyscraper",
         "office building": "skyscraper", "skyline": "skyscraper", "building": "building", "parliament": "building",
         "new parliament": "building", "supreme court": "building", "bank": "building", "column": "building",
         "house": "house", "home": "house", "village": "house", "plane": "plane", "airplane": "plane",
         "flight": "plane", "train": "train", "car": "car", "tractor": "tractor", "farmer standing": "person",
         "oil barrel": "oil barrel", "oil": "oil barrel", "globe": "globe", "world": "globe", "person": "person",
         "man standing": "person", "woman standing": "person", "businessman": "person", "worker": "person",
         "student": "person", "doctor": "person", "crowd": "crowd", "people": "crowd", "protest": "crowd",
         "queue": "crowd", "megaphone": "megaphone", "gavel": "gavel", "scales of justice": "gavel",
         "ballot box": "ballot box", "evm": "ballot box", "light bulb": "light bulb", "padlock": "padlock",
         "book": "book", "books": "book", "briefcase": "briefcase", "pill": "pill", "power tower": "tower",
         "tower": "tower", "chart": "chart", "stock chart": "chart", "port": "port", "harbour": "port",
         "auto rickshaw": "auto rickshaw", "auto": "auto rickshaw", "rickshaw": "auto rickshaw", "scooter": "scooter",
         "bike": "scooter", "motorcycle": "scooter", "bus": "bus", "india gate": "arch", "gateway of india": "arch",
         "monument": "arch", "arch": "arch", "round parliament": "round parliament", "temple": "temple",
         "mandir": "temple", "hut": "hut", "farm": "hut", "chai": "chai", "tea": "chai", "cup": "chai",
         "cricket": "cricket bat", "cricket bat": "cricket bat", "scales": "scales", "justice": "scales",
         "law": "scales", "handcuffs": "handcuffs", "arrest": "handcuffs", "microphone": "microphone",
         "speech": "microphone", "camera": "camera", "photo": "camera", "rocket": "rocket", "isro": "rocket",
         "satellite": "satellite", "space": "rocket", "solar panel": "solar panel", "solar": "solar panel",
         "wind turbine": "wind turbine", "wind": "wind turbine", "hospital": "hospital", "school": "school",
         "education": "school", "bridge": "bridge", "dam": "dam", "hourglass": "hourglass", "deadline": "hourglass",
         "time": "hourglass", "key": "key", "freedom": "key", "calendar": "calendar", "date": "calendar",
         "man": "man", "man standing": "man", "worker": "man", "farmer standing": "man", "voter": "man",
         "woman": "woman", "woman standing": "woman", "women": "woman"}


# Objects that looked different in another era: (before this year, the period drawing, the photo to search for).
# A 1914 story gets a steamship, not a container ship.
ERA_ILLUS = {"ship": (1950, "steamer", "steamship"), "train": (1960, "steamtrain", "steam locomotive"),
             "plane": (1940, "biplane", "biplane"), "smartphone": (1995, "rotaryphone", "rotary telephone"),
             "car": (1940, "oldcar", "vintage car"), "television": (1940, "newspaper", "old newspaper")}


def illustration(name: str, era: int | None = None) -> str | None:
    from .cutouts import resolve
    n = (name or "").strip().lower()
    key = ILLUS.get(n) or ILLUS.get(resolve(n) or "") or ILLUS.get(n.rstrip("s"))
    return period(key, era)[0] if key else None


def period(key: str | None, era: int | None) -> tuple[str | None, str | None]:
    """(drawing, photo search) for an object in the story's era; the modern ones when the era is unknown or recent."""
    if key and era and key in ERA_ILLUS and era < ERA_ILLUS[key][0]:
        return ERA_ILLUS[key][1], ERA_ILLUS[key][2]
    return key, None


def era_in(theme: str) -> int | None:
    """'editorial~1@red/sepia/1914' -> 1914."""
    bits = (theme or "").split("/")
    return int(bits[2]) if len(bits) > 2 and bits[2].strip().isdigit() else None


def parse_pyramid(spec: str) -> dict | None:
    """'Pyramid: India, 2021 | 0-14 13.4/12.2; 15-29 14/12.9; 30-44 11/10.4; 45-59 7.6/7.3; 60+ 4.9/5.2 | Men, Women'
    - a population pyramid: one band per age group, left and right bars growing out from the middle."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2:
        return None
    bands = []
    for chunk in re.split(r";|,(?!\d)", parts[1]):
        m = re.match(r"\s*(.+?)\s+([\d.]+)\s*%?\s*/\s*([\d.]+)\s*%?\s*$", chunk)
        if m:
            bands.append({"label": m.group(1).strip()[:10], "l": float(m.group(2)), "r": float(m.group(3)),
                          "ls": m.group(2), "rs": m.group(3)})
    if len(bands) < 2:
        return None
    sides = [x.strip() for x in re.split(r",|/", parts[2])][:2] if len(parts) > 2 and parts[2] else []
    sides += ["Men", "Women"][len(sides):]
    return {"type": "pyramid", "title": parts[0][:44], "bands": bands[:12], "left": sides[0][:14], "right": sides[1][:14],
            "unit": parts[3][:16] if len(parts) > 3 else "", "tone": "grid", "seed": _seed(spec) % 10000}


def parse_flow(spec: str) -> dict | None:
    """'Flowchart: Donor → Electoral trust (₹5 crore) → Party → Ad agency | How the money moved' - boxes joined by
    arrows that draw one after another; a token travels the chain. A note in brackets sits under the name."""
    parts = [p.strip() for p in (spec or "").split("|")]
    nodes = []
    for x in re.split(r"→|->|=>", parts[0]):
        x = x.strip()
        if not x:
            continue
        m = re.match(r"(.+?)\s*\((.+)\)\s*$", x)
        nodes.append({"name": (m.group(1) if m else x).strip()[:30], "note": (m.group(2).strip()[:26] if m else "")})
    if not 2 <= len(nodes) <= 6:
        return None
    return {"type": "flowchart", "nodes": nodes, "title": parts[1][:48] if len(parts) > 1 else "", "tone": "grid",
            "seed": _seed(spec) % 10000}


def parse_linkmap(spec: str) -> dict | None:
    """'Linkmap: Shell company | Director: funds; Bank: loans; Minister: licence; Auditor: signed off | Who is linked'
    - a relationship map: the subject in the middle, the others round it, each link drawn and labelled."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    nodes = []
    for x in re.split(r";|,", parts[1]):
        name, _, how = x.partition(":")
        if name.strip():
            nodes.append({"name": name.strip()[:24], "how": how.strip()[:22]})
    if not 2 <= len(nodes) <= 8:
        return None
    return {"type": "linkmap", "centre": parts[0][:26], "nodes": nodes, "title": parts[2][:48] if len(parts) > 2 else "",
            "tone": "crumple", "seed": _seed(spec) % 10000}


def parse_orgchart(spec: str) -> dict | None:
    """'Orgchart: Prime Minister | Home, Finance, Defence, External Affairs | The cabinet' - who reports to whom:
    the top box, a row of boxes under it, connectors drawn down. A third part 'A > x, y' hangs boxes under A."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    kids = [{"name": x.strip()[:22], "kids": []} for x in parts[1].split(",") if x.strip()][:6]
    if len(kids) < 2:
        return None
    title = ""
    for extra in parts[2:]:
        if ">" in extra:
            par, _, sub = extra.partition(">")
            k = next((c for c in kids if c["name"].lower() == par.strip().lower()), None)
            if k:
                k["kids"] = [x.strip()[:20] for x in sub.split(",") if x.strip()][:3]
        elif not title:
            title = extra[:48]
    return {"type": "orgchart", "top": parts[0][:26], "kids": kids, "title": title, "tone": "grid",
            "seed": _seed(spec) % 10000}


_COUNTRY_ALIAS = {"usa": "united states of america", "us": "united states of america", "america": "united states of america",
                  "united states": "united states of america", "uk": "united kingdom", "britain": "united kingdom",
                  "uae": "united arab emirates", "russia": "russia", "south korea": "south korea", "drc": "dem. rep. congo",
                  "czech republic": "czechia", "ivory coast": "côte d'ivoire", "burma": "myanmar"}


def _country(name: str) -> dict | None:
    from . import maps
    n = maps._norm(_COUNTRY_ALIAS.get(name.strip().lower(), name))
    cs = maps._world()["countries"]
    return next((c for c in cs if maps._norm(c["n"]) == n), None) or \
        next((c for c in cs if n and maps._norm(c["n"]).startswith(n)), None)


_STATE_ALIAS = {"up": "uttar pradesh", "mp": "madhya pradesh", "ap": "andhra pradesh", "hp": "himachal pradesh",
                "tn": "tamil nadu", "wb": "west bengal", "j&k": "jammu and kashmir", "jk": "jammu and kashmir",
                "orissa": "odisha", "uttaranchal": "uttarakhand", "bengal": "west bengal", "nyc": "new york"}


@functools.lru_cache(maxsize=1)
def _states() -> dict:
    """States and provinces of every country (Natural Earth admin-1, public domain): the nine largest countries at
    1:50m, the rest thinned from 1:10m, with their local and alternative names under "a"."""
    return json.loads((Path(__file__).with_name("states.json")).read_text(encoding="utf-8"))


def _fold(name: str) -> str:
    """'Québec' -> 'quebec': accents folded, then the map lookup's own normalising."""
    import unicodedata
    from . import maps
    return maps._norm("".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c)))


def _state_heat(vals: list[dict]) -> tuple[str, list] | None:
    """(country, [(state, value)]) when the labels are states of one country."""
    from . import maps
    best = None
    for country, sts in _states().items():
        idx = {_fold(a): st for st in sts for a in st.get("a", [])}     # local and alternative names
        idx.update({_fold(st["n"]): st for st in sts})
        hit = [(idx[n], v) for v in vals for n in [_fold(_STATE_ALIAS.get(v["label"].strip().lower(), v["label"]))] if n in idx]
        if len(hit) >= 2 and (best is None or len(hit) > len(best[1]) or (len(hit) == len(best[1]) and country == "India")):
            best = (country, hit)
    return best


def parse_heatmap(spec: str) -> dict | None:
    """'Heatmap: India 1.9, China 8.0, USA 14.9, Brazil 2.2, Germany 8.1 | CO2 per person | tonnes, 2022' - countries
    shaded by their number (darker = more), each labelled, with a scale; the rest of the map stays pale."""
    from . import maps
    parts = [p.strip() for p in (spec or "").split("|")]
    vals = []
    pairs = _pairs(parts[0])
    for v in pairs:
        c = _country(v["label"])
        if c:
            vals.append((c, v))
    world = maps._world()["countries"]
    st = _state_heat(pairs) if len(vals) < 2 or len(vals) < len(pairs) / 2 else None
    if st:
        # states of one country: its other states stay pale, the rest of the world paler still
        vals = st[1]
        world = [{"n": x["n"], "r": x["r"]} for x in _states()[st[0]] if x["n"] not in {c["n"] for c, _ in vals}] + \
            [c for c in world if c["n"] != st[0]]
    mapcredit = ""
    if len(vals) < 2 or len(vals) < len(pairs) / 2:
        # districts (downloaded per country, see media/districts.py): the country's other districts stay pale
        from . import districts
        dd = districts.find([v["label"] for v in pairs])
        if dd:
            vals = [({"n": u["n"], "r": u["r"]}, v) for u, v in zip(dd[1], pairs) if u]
            world = [{"n": u["n"], "r": u["r"]} for u in dd[2]]
            mapcredit = dd[3]
    if len(vals) < 2:
        return None
    pts = [(x, y) for c, _ in vals for r in sorted(c["r"], key=len)[-1:] for x, y in r]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    box = [min(xs), max(-56.0, min(ys)), max(xs), min(78.0, max(ys))]
    named = {c["n"] for c, _ in vals}
    items = []
    for c, v in vals[:14]:
        big = max(c["r"], key=len)
        rings = [[[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 140)]] for r in c["r"] if len(r) >= 8 or r is big]
        items.append({"name": c["n"], "label": v["label"], "value": v["value"], "shown": v["shown"], "rings": rings[:12],
                      "at": [round(sum(q[0] for q in big) / len(big), 2), round(sum(q[1] for q in big) / len(big), 2)]})
    others = []
    for c in world:
        if c["n"] in named:
            continue
        for r in c["r"]:
            if len(r) >= (4 if mapcredit else 12) and any(box[0] - 40 <= x <= box[2] + 40 and box[1] - 30 <= y <= box[3] + 30 for x, y in r[:: max(1, len(r) // 20)]):
                others.append([[round(x, 1), round(y, 1)] for x, y in r[:: max(1, len(r) // 70)]])
    return {"type": "heatmap", "items": items, "others": others[:420], "box": box, "title": parts[1][:48] if len(parts) > 1 else "",
            "unit": parts[2][:26] if len(parts) > 2 else "", "tone": "atlas", "mapcredit": mapcredit,
            "seed": _seed(spec) % 10000}


def _map_frame(pts: list[tuple[float, float]], pad: float = 0.35) -> tuple[list[float], list]:
    """(visible box, the country outlines that touch it) round some lon/lat points."""
    from . import maps
    lons, lats = [q[0] for q in pts], [q[1] for q in pts]
    px = max(6.0, (max(lons) - min(lons)) * pad)
    py = max(4.0, (max(lats) - min(lats)) * pad)
    box = [min(lons) - px, max(-58.0, min(lats) - py), max(lons) + px, min(80.0, max(lats) + py)]
    shapes = []
    for c in maps._world()["countries"]:
        for r in c["r"]:
            if any(box[0] - 50 <= x <= box[2] + 50 and box[1] - 35 <= y <= box[3] + 35 for x, y in r[:: max(1, len(r) // 30)]):
                shapes.append([[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 150)]])
    return box, shapes[:420]


def parse_courtdoc(spec: str) -> dict | None:
    """'Courtdoc: Supreme Court of India | M. Siddiq v. Mahant Suresh Das | "the finding, in the court's words" |
    para 788 · 9 Nov 2019' - the page of a judgment: the court, the case, the quoted paragraph highlighted as read."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 3 or not parts[2].strip(' "“”'):
        return None
    return {"type": "courtdoc", "court": parts[0][:60], "case": parts[1][:80], "quote": parts[2].strip(' "“”')[:260],
            "ref": parts[3][:60] if len(parts) > 3 else "", "badge": BADGES["court"], "tone": "grid",
            "seed": _seed(spec) % 10000}


def parse_table(spec: str) -> dict | None:
    """'Table: State, Seats, Vote % | UP, 62, 49.6; Bihar, 39, 53.3; MP, 28, 58.0 | 2019 result | highlight: 2'
    - a data table that fills row by row; one row can be picked out."""
    hl = 0
    m = re.search(r"\|\s*highlight\s*[:=]\s*(\d+)", spec or "", re.I)
    if m:
        hl = int(m.group(1))
        spec = spec[:m.start()] + spec[m.end():]
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2:
        return None
    head = [h.strip()[:18] for h in parts[0].split(",") if h.strip()][:5]
    rows = [[c.strip()[:20] for c in re.split(r",(?!\d{2,3}\b)", r)][:len(head)] for r in parts[1].split(";") if r.strip()][:8]
    rows = [r for r in rows if len(r) == len(head)]
    if len(head) < 2 or len(rows) < 2:
        return None
    return {"type": "table", "head": head, "rows": rows, "title": parts[2][:48] if len(parts) > 2 else "",
            "source": parts[3][:50] if len(parts) > 3 else "", "hl": hl if 1 <= hl <= len(rows) else 0, "tone": "grid",
            "seed": _seed(spec) % 10000}


def parse_interview(spec: str) -> dict | None:
    """'Interview: person:Raghuram Rajan | "the words they said" | Former RBI Governor · 2019, The Hindu' - the
    speaker's photo, a lower third with name and role, the pull quote typed beside them."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    who = parts[0] if parts[0].lower().startswith("person:") else "person:" + parts[0]
    return {"type": "interview", "subjects": [who], "name": who.split(":", 1)[1].strip()[:40],
            "quote": parts[1].strip(' "“”')[:200], "role": parts[2][:70] if len(parts) > 2 else "",
            "seed": _seed(spec) % 10000}


def parse_endcard(spec: str) -> dict | None:
    """'Endcard: The canal that changed trade | Watch next: the Suez story | Sources: ACP · Lloyd's List · UNCTAD'"""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    src = next((p.split(":", 1)[1] for p in parts[1:] if p.lower().startswith(("sources:", "source:"))), "")
    rest = [p for p in parts[1:] if not p.lower().startswith(("sources:", "source:"))]
    return {"type": "endcard", "title": parts[0][:60], "line": rest[0][:70] if rest else "",
            "sources": [x.strip()[:34] for x in re.split(r"·|;|,", src) if x.strip()][:6], "seed": _seed(spec) % 10000}


def parse_polltrack(spec: str) -> dict | None:
    """'Polltrack: Jan 38, Feb 41, Mar 39, Apr 44, May 47 | Approval rating | ±3 | %' - a poll line with its margin
    of error as a band; the last reading is the big number."""
    parts = [p.strip() for p in (spec or "").split("|")]
    pts = _pairs(parts[0])
    if len(pts) < 3:
        return None
    m = re.search(r"([\d.]+)", parts[2]) if len(parts) > 2 else None
    return {"type": "polltrack", "points": pts[:14], "title": parts[1][:48] if len(parts) > 1 else "",
            "moe": float(m.group(1)) if m else 0.0, "unit": parts[3][:6] if len(parts) > 3 else "", "tone": "grid",
            "seed": _seed(spec) % 10000}


def parse_area(spec: str) -> dict | None:
    """'Area: 2019, 2020, 2021, 2022 | Coal: 60, 58, 55, 50; Solar: 5, 9, 14, 22; Wind: 6, 8, 9, 11 | Power mix'
    - a stacked area chart that fills from left to right."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2:
        return None
    xs = [x.strip()[:8] for x in parts[0].split(",") if x.strip()]
    series = []
    for chunk in parts[1].split(";"):
        name, _, vals = chunk.partition(":")
        try:
            v = [float(x) for x in vals.split(",") if x.strip()]
        except ValueError:
            return None
        if name.strip() and len(v) == len(xs):
            series.append({"name": name.strip()[:16], "v": v})
    if len(xs) < 2 or not 2 <= len(series) <= 5:
        return None
    return {"type": "area", "xs": xs[:12], "series": series, "title": parts[2][:48] if len(parts) > 2 else "",
            "unit": parts[3][:14] if len(parts) > 3 else "", "tone": "grid", "seed": _seed(spec) % 10000}


def parse_candles(spec: str) -> dict | None:
    """'Candles: Mon 100/112/96/108; Tue 108/115/104/106; Wed 106/107/90/93 | Share price | ₹' - open/high/low/close
    candles drawn one by one; up days in the accent, down days in ink."""
    parts = [p.strip() for p in (spec or "").split("|")]
    cs = []
    for chunk in parts[0].split(";"):
        m = re.match(r"\s*(.*?)\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)\s*$", chunk)
        if m:
            o, h, lo, c = (float(m.group(i)) for i in (2, 3, 4, 5))
            if lo <= min(o, c) and h >= max(o, c):
                cs.append({"label": m.group(1)[:8], "o": o, "h": h, "l": lo, "c": c})
    if len(cs) < 3:
        return None
    return {"type": "candles", "candles": cs[:24], "title": parts[1][:48] if len(parts) > 1 else "",
            "unit": parts[2][:6] if len(parts) > 2 else "", "tone": "grid", "seed": _seed(spec) % 10000}


def parse_arrows(spec: str) -> dict | None:
    """'Arrows: Belarus → Kyiv (north); Russia → Kharkiv (east); Crimea → Kherson | February 2022' - movement on a
    map (armies, migration, trade): broad arrows that sweep from one place to the next, each one named."""
    parts = [p.strip() for p in (spec or "").split("|")]
    arrows = []
    for chunk in parts[0].split(";"):
        m = re.match(r"\s*(.+?)\s*(?:→|->)\s*(.+?)\s*(?:\((.+)\))?\s*$", chunk)
        if not m:
            continue
        g = _geo([m.group(1), m.group(2)])
        if len(g) == 2:
            arrows.append({"a": g[0], "b": g[1], "label": (m.group(3) or "").strip()[:22]})
    if not arrows:
        return None
    box, shapes = _map_frame([(e["lon"], e["lat"]) for a in arrows for e in (a["a"], a["b"])], 0.45)
    return {"type": "arrows", "arrows": arrows[:6], "box": box, "shapes": shapes, "title": parts[1][:48] if len(parts) > 1 else "",
            "tone": "atlas", "seed": _seed(spec) % 10000}


def parse_railmap(spec: str) -> dict | None:
    """'Railmap: Delhi - Kanpur - Patna - Kolkata; Delhi - Jaipur - Ahmedabad - Mumbai | Freight corridors' - a
    transport network: each line draws through its stations, a different colour per line, stations named once."""
    parts = [p.strip() for p in (spec or "").split("|")]
    lines = []
    for chunk in parts[0].split(";"):
        name, sep, rest = chunk.partition(":")
        stops = _geo([x.strip() for x in re.split(r"\s+-\s+|→|->|–|—", rest if sep else chunk) if x.strip()][:9])
        if len(stops) >= 2:
            lines.append({"name": name.strip()[:18] if sep else "", "stops": stops})
    if not lines:
        return None
    box, shapes = _map_frame([(s["lon"], s["lat"]) for ln in lines for s in ln["stops"]], 0.3)
    return {"type": "railmap", "lines": lines[:5], "box": box, "shapes": shapes, "title": parts[1][:48] if len(parts) > 1 else "",
            "tone": "atlas", "seed": _seed(spec) % 10000}


def _ring_area_km2(r: list) -> float:
    import math
    a = 0.0
    for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
        a += math.radians(x2 - x1) * (2 + math.sin(math.radians(y1)) + math.sin(math.radians(y2)))
    return abs(a) * 6371.0088 ** 2 / 2


def parse_sizemap(spec: str) -> dict | None:
    """'Sizemap: India vs Germany | How big is it really?' - two countries at the same scale: the first is drawn,
    morphs into the second, then both outlines sit together with how many times bigger one is."""
    import math
    parts = [p.strip() for p in (spec or "").split("|")]
    names = [x.strip() for x in re.split(r"\s+vs\.?\s+", parts[0], flags=re.I) if x.strip()]
    cs = [_country(n) for n in names[:2]]
    if len(cs) != 2 or not all(cs) or cs[0] is cs[1]:
        return None
    items = []
    for c, n in zip(cs, names):
        big = max(c["r"], key=_ring_area_km2)
        lat0 = sum(y for _, y in big) / len(big)
        lon0 = sum(x for x, _ in big) / len(big)
        k = math.cos(math.radians(lat0))
        step = max(1, len(big) // 200)
        items.append({"name": n[:22], "km2": round(sum(_ring_area_km2(r) for r in c["r"])),
                      "ring": [[round((x - lon0) * k * 111.32, 1), round(-(y - lat0) * 110.57, 1)] for x, y in big[::step]]})
    return {"type": "sizemap", "items": items, "title": parts[1][:48] if len(parts) > 1 else "", "tone": "grid",
            "seed": _seed(spec) % 10000}


REGIONS = {"europe": [-12, 34, 45, 71], "world": [-170, -56, 180, 78], "asia": [25, -10, 150, 60],
           "south asia": [58, 4, 100, 40], "middle east": [24, 10, 66, 44], "africa": [-20, -36, 54, 38],
           "north america": [-140, 8, -52, 62], "south america": [-84, -56, -32, 14], "east asia": [95, 15, 150, 55],
           "southeast asia": [90, -12, 142, 28], "balkans": [12, 34, 32, 49]}


def parse_borders(spec: str) -> dict | None:
    """'Borders: 1914 → today | Europe | The map before the war' - the borders of a past year (history.py), then
    the map redraws itself as it is now; the old lines stay as a dashed ghost and the year counts across.
    'Borders: 1914 | Europe' shows the one year. Needs the dated maps on the worker (see media/history.py)."""
    from . import history, maps
    parts = [p.strip() for p in (spec or "").split("|")]
    ys = re.findall(r"(?<!\d)(1[5-9]\d\d|20\d\d)(?!\d)", parts[0])
    if not ys:
        return None
    ya = int(ys[0])
    yb = int(ys[1]) if len(ys) > 1 else (0 if re.search(r"today|now|present", parts[0], re.I) else None)
    fa = history.nearest(ya)
    if fa is None:
        return None                                   # no dated maps on this worker: never today's map with an old date
    region = (parts[1] if len(parts) > 1 else "world").strip().lower()
    box = REGIONS.get(region)
    if box is None:
        f = maps._find(region)
        if not f:
            return None
        if f["kind"] == "city":
            box = [f["lon"] - 9, f["lat"] - 6, f["lon"] + 9, f["lat"] + 6]
        else:
            big = max(f["rings"], key=len)
            xs, ys2 = [x for x, _ in big], [y for _, y in big]
            px, py = max(4.0, (max(xs) - min(xs)) * .5), max(3.0, (max(ys2) - min(ys2)) * .5)
            box = [min(xs) - px, min(ys2) - py, max(xs) + px, max(ys2) + py]

    def clip(cs):
        out = []
        for c in cs:
            rings = [r for r in c["r"] if any(box[0] - 12 <= x <= box[2] + 12 and box[1] - 8 <= y <= box[3] + 8
                                              for x, y in r[:: max(1, len(r) // 24)])]
            if rings:
                big = max(rings, key=len)
                inside = [q for q in big if box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]]
                xs, ys2 = [q[0] for q in big], [q[1] for q in big]
                out.append({"n": c["n"], "r": [[[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 150)]] for r in rings[:8]],
                            "size": (max(xs) - min(xs)) * (max(ys2) - min(ys2)) * (len(inside) / max(1, len(big))),
                            "at": [round(sum(q[0] for q in inside) / len(inside), 2), round(sum(q[1] for q in inside) / len(inside), 2)]
                            if inside else None})
        return out
    then = clip(history.load(fa))
    if not then:
        return None
    if yb is None:
        now = []
    elif yb == 0 or yb >= 2011 or history.nearest(yb) in (None, fa):
        now = clip(maps._world()["countries"])
        yb = yb or 0
    else:
        now = clip(history.load(history.nearest(yb)))
    for group in (then, now):
        for c in sorted(group, key=lambda c: -c["size"])[:9]:
            c["label"] = bool(c["at"] and c["n"])
    return {"type": "borders", "then": then[:160], "now": now[:160], "ya": ya, "yb": yb, "box": box,
            "title": parts[2][:48] if len(parts) > 2 else "", "tone": "atlas", "mapcredit": history.CREDIT,
            "seed": _seed(spec) % 10000}


def _basic_shape(name: str) -> list | None:
    """Plain shapes for Morph: unit-box outlines (y down)."""
    import math
    n = name.strip().lower()
    poly = {"triangle": 3, "square": 4, "diamond": 4, "pentagon": 5, "hexagon": 6, "octagon": 8, "circle": 72}
    if n in poly:
        k, rot = poly[n], {"square": math.pi / 4, "triangle": -math.pi / 2, "pentagon": -math.pi / 2}.get(n, 0.0)
        return [[math.cos(rot + i / k * 2 * math.pi), math.sin(rot + i / k * 2 * math.pi)] for i in range(k)]
    if n == "star":
        return [[(1 if i % 2 == 0 else .42) * math.cos(-math.pi / 2 + i / 10 * 2 * math.pi),
                 (1 if i % 2 == 0 else .42) * math.sin(-math.pi / 2 + i / 10 * 2 * math.pi)] for i in range(10)]
    if n == "heart":
        return [[16 * math.sin(t) ** 3 / 17, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 17]
                for t in (i / 80 * 2 * math.pi for i in range(80))]
    if n in ("drop", "droplet"):
        return [[.72 * math.sin(t) * (1 - math.cos(t)) / 1.3 * 1.0, -math.cos(t) * .95 - .05] for t in (i / 70 * 2 * math.pi for i in range(70))]
    if n == "arrow":
        return [[-1, -.3], [.2, -.3], [.2, -.75], [1, 0], [.2, .75], [.2, .3], [-1, .3]]
    return None


def _outline(name: str) -> dict | None:
    """A named shape as one closed outline in a unit box: a plain shape, a country, or a state / province."""
    import math
    r = _basic_shape(name)
    label = name.strip()
    if r is None:
        c = _country(name)
        if c is None:
            key = _fold(_STATE_ALIAS.get(name.strip().lower(), name))
            c = next((st for sts in [_states().get("India", [])] + list(_states().values()) for st in sts
                      if _fold(st["n"]) == key or key in [_fold(a) for a in st.get("a", [])]), None)
        if c is None:
            return None
        big = max(c["r"], key=_ring_area_km2)
        lat0 = sum(y for _, y in big) / len(big)
        k = math.cos(math.radians(lat0))
        r = [[x * k, -y] for x, y in big[:: max(1, len(big) // 220)]]
        label = c["n"]
    xs, ys = [q[0] for q in r], [q[1] for q in r]
    sc = 2 / max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return {"name": label[:24], "ring": [[round((x - cx) * sc, 4), round((y - cy) * sc, 4)] for x, y in r]}


def parse_morph(spec: str) -> dict | None:
    """'Morph: India → drop → Bihar | Where the water goes' - one shape flows into the next (2-4 shapes): countries,
    states and provinces, or plain shapes (circle, square, triangle, diamond, pentagon, hexagon, octagon, star,
    heart, drop, arrow). Each is drawn to fill the frame; for true relative size use Sizemap."""
    parts = [p.strip() for p in (spec or "").split("|")]
    shapes = [_outline(x) for x in re.split(r"→|->|=>", parts[0]) if x.strip()][:4]
    if len(shapes) < 2 or not all(shapes):
        return None
    return {"type": "morph", "shapes": shapes, "title": parts[1][:48] if len(parts) > 1 else "",
            "caption": parts[2][:60] if len(parts) > 2 else "", "seed": _seed(spec) % 10000}


PARSERS = {"morph": parse_morph, "borders": parse_borders, "courtdoc": parse_courtdoc, "table": parse_table, "interview": parse_interview, "endcard": parse_endcard,
           "polltrack": parse_polltrack, "area": parse_area, "candles": parse_candles, "arrows": parse_arrows,
           "railmap": parse_railmap, "sizemap": parse_sizemap,
           "pyramid": parse_pyramid, "flowchart": parse_flow, "linkmap": parse_linkmap, "orgchart": parse_orgchart,
           "heatmap": parse_heatmap, "hero": parse_hero, "desk": parse_desk, "pinboard": parse_evidence, "opener": parse_opener,
           "reveal": parse_reveal, "clipping": parse_headline, "pinmap": parse_pinmap, "bignumber": parse_number,
           "seats": parse_seats, "stack": parse_stack, "stand": parse_stand, "fan": parse_fan, "trend": parse_trend,
           "slice": parse_slice, "route": parse_route, "compare": parse_compare, "photoline": parse_photoline,
           "tv": parse_tv, "clockmap": parse_clockmap, "tornsplit": parse_tornsplit, "newscard": parse_newscard,
           "blueprint": parse_blueprint}


_LOGOS: dict | None = None


def logos() -> dict:
    """Official brand marks (Simple Icons, CC0 data) by key: {title, hex, d}."""
    global _LOGOS
    if _LOGOS is None:
        try:
            _LOGOS = json.loads((Path(__file__).parent / "vendor" / "logos.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _LOGOS = {}
    return _LOGOS


LOGO_WORDS = {"whatsapp": "whatsapp", "व्हाट्सऐप": "whatsapp", "व्हाट्सएप": "whatsapp", "facebook": "facebook",
              "फ़ेसबुक": "facebook", "फेसबुक": "facebook", "instagram": "instagram", "इंस्टाग्राम": "instagram",
              "twitter": "x", "ट्विटर": "x", "एक्स": "x", "youtube": "youtube", "यूट्यूब": "youtube", "telegram": "telegram",
              "टेलीग्राम": "telegram", "google": "google", "गूगल": "google", "meta": "meta", "मेटा": "meta",
              "snapchat": "snapchat", "स्नैपचैट": "snapchat", "tiktok": "tiktok", "टिकटॉक": "tiktok", "jio": "jio",
              "जियो": "jio", "paytm": "paytm", "पेटीएम": "paytm", "phonepe": "phonepe", "फ़ोनपे": "phonepe",
              "फोनपे": "phonepe", "google pay": "googlepay", "गूगल पे": "googlepay", "zomato": "zomato", "ज़ोमैटो": "zomato",
              "swiggy": "swiggy", "स्विगी": "swiggy", "airtel": "airtel", "एयरटेल": "airtel", "netflix": "netflix",
              "नेटफ्लिक्स": "netflix", "spotify": "spotify", "wikipedia": "wikipedia", "विकिपीडिया": "wikipedia",
              "android": "android", "एंड्रॉयड": "android", "apple": "apple", "एप्पल": "apple", "iphone": "apple",
              "samsung": "samsung", "सैमसंग": "samsung", "tesla": "tesla", "टेस्ला": "tesla", "uber": "uber", "उबर": "uber",
              "signal": "signal", "सिग्नल": "signal", "threads": "threads", "reddit": "reddit", "gmail": "gmail",
              "google maps": "googlemaps", "nvidia": "nvidia", "एनवीडिया": "nvidia", "intel": "intel", "visa": "visa",
              "mastercard": "mastercard", "bitcoin": "bitcoin", "बिटकॉइन": "bitcoin", "tata": "tata", "टाटा": "tata",
              "infosys": "infosys", "इंफ़ोसिस": "infosys", "wipro": "wipro", "xiaomi": "xiaomi", "oneplus": "oneplus",
              "vivo": "vivo", "oppo": "oppo", "zoom": "zoom", "discord": "discord", "messenger": "messenger",
              "wechat": "wechat", "hdfc": "hdfcbank", "icici": "icicibank", "bluesky": "bluesky", "pinterest": "pinterest"}


def logo_key(word: str) -> str:
    w = (word or "").strip().lower().removeprefix("logo:").removesuffix(" logo").removesuffix(" app").strip()
    k = LOGO_WORDS.get(w, w.replace(" ", ""))
    return k if k in logos() else ""


def plan_for(kind: str, spec: str) -> dict | None:
    fn = PARSERS.get(kind)
    if not fn:
        return None
    # "| marker: <note>" on any scene: a hand-drawn marker circle round the subject and a handwritten note
    marks = []
    lg = re.search(r"\|\s*logos?\s*[:=]\s*([^|]+)", spec or "", re.I)
    if lg:
        marks = [k for k in (logo_key(x) for x in re.split(r",|\+|·", lg.group(1))) if k][:3]
        spec = (spec[:lg.start()] + spec[lg.end():]).strip()
    comp = ""
    w = re.search(r"\|\s*with\s*[:=]\s*([^|]+)", spec or "", re.I)
    if w:
        comp = w.group(1).strip()[:60]
        spec = (spec[:w.start()] + spec[w.end():]).strip()
    note = ""
    m = re.search(r"\|\s*marker\s*[:=]\s*([^|]+)", spec or "", re.I)
    if m:
        note = m.group(1).strip()[:60]
        spec = (spec[:m.start()] + spec[m.end():]).strip()
    spec = re.sub(r"\|\s*voice\s*(?=\||$)", "", spec or "", flags=re.I).strip()     # "| voice": see wants_voice
    opts = {}
    for key in ("badge", "fx", "inset", "exit"):
        mm = re.search(rf"\|\s*{key}\s*[:=]\s*([^|]+)", spec or "", re.I)
        if mm:
            opts[key] = mm.group(1).strip()[:60]
            spec = (spec[:mm.start()] + spec[mm.end():]).strip()
    plan = fn(spec)
    if plan is not None:
        b = opts.get("badge", "").lower()
        if b:
            # how sure we are, on screen: a fact from a record, a report, an allegation, a response, an opinion
            plan["badge"] = next((v for k, v in BADGES.items() if b.startswith(k)), "")
        if opts.get("fx", "").lower() in FX:
            plan["fx"] = opts["fx"].lower()
        if opts.get("exit", "").lower() in EXITS + ("none",):
            plan["exit"] = opts["exit"].lower()
        if opts.get("inset"):
            plan["inset"] = opts["inset"]
    if plan is not None and note:
        plan["marker"] = note
    if plan is not None and marks:
        plan["logos"] = [dict(logos()[k], key=k) for k in marks]
    if plan is not None and comp:
        plan["with"] = comp if comp.lower().startswith("person:") else "person:" + comp
    return plan


# ---- pictures -------------------------------------------------------------------------------------------------------
def _pictures(plan: dict, lib: Path | None, model: Path | None, fetch: bool,
              sources: list[tuple[str, str]] | None = None, era: int | None = None) -> None:
    """Each subject: a cut-out photo {img, w, h, credit} or the vector icon {o} when there's no photo."""
    from . import cutouts
    from .scene_anim import find_icon, icon_nodes
    out = []
    for s in plan.get("subjects", []):
        name = s if s.lower().startswith("person:") else s.lower()
        if name.startswith("logo:") or (logo_key(name) and not cutouts.resolve(name)):
            k = logo_key(name)
            if k:
                out.append({"name": s, "logo": dict(logos()[k], key=k)})
                continue
        old_draw, old_photo = period(illustration(name), era) if not name.startswith("person:") else (None, None)
        if old_photo:
            # a period object: a photo of the old one, else its period drawing; never today's version in 1914
            c = cutouts.get(old_photo, lib, model=model, fetch=fetch, sources=sources)
            if c is None:
                out.append({"name": s, "draw": old_draw})
                continue
        else:
            c = cutouts.get(name, lib, model=model, fetch=fetch, sources=sources)
        if c is not None:
            from PIL import Image
            with Image.open(c.path) as im:
                w, h = im.size
            pic = {"name": s, "img": c.path.as_uri(), "w": w, "h": h, "credit": c.credit}
            if plan.get("prop") in FACE_PROPS and not out:
                pic["face"] = face_box(c.path)
            out.append(pic)
        elif name.startswith("person:"):
            # no photo of this person (yet): a plain drawn figure, never a made-up face; the name stays in the tags
            out.append({"name": s, "draw": "person"})
        else:
            drawn = illustration(name, era)
            if drawn:
                out.append({"name": s, "draw": drawn})           # a drawn illustration, never a placeholder
            else:
                icon = find_icon(name.split()[-1]) or find_icon(name) or "circle"
                out.append({"name": s, "o": icon_nodes(icon)})
    plan["pics"] = out
    if plan.get("with"):
        c = cutouts.get(plan["with"], lib, model=model, fetch=fetch, sources=sources)
        if c is not None:
            from PIL import Image
            with Image.open(c.path) as im:
                w, h = im.size
            plan["comp"] = {"name": plan["with"], "img": c.path.as_uri(), "w": w, "h": h, "credit": c.credit}
            out = out + [plan["comp"]]
        else:
            plan["comp"] = {"name": plan["with"], "draw": "person"}
    if plan.get("inset"):
        nm = plan["inset"] if plan["inset"].lower().startswith("person:") else plan["inset"].lower()
        c = cutouts.get(nm, lib, model=model, fetch=fetch, sources=sources)
        if c is not None:
            from PIL import Image
            with Image.open(c.path) as im:
                w, h = im.size
            plan["insetpic"] = {"name": plan["inset"], "img": c.path.as_uri(), "w": w, "h": h, "credit": c.credit}
            out = out + [plan["insetpic"]]
        else:
            drawn = "person" if nm.startswith("person:") else illustration(nm, era)
            plan["insetpic"] = {"name": plan["inset"], "draw": drawn} if drawn else None
    credits = sorted({p["credit"] for p in out if p.get("credit")})
    plan["credit"] = ("Photo: " + "; ".join(credits))[:120] if credits else ""


def face_box(path: Path) -> list[float] | None:
    """The main face in a cut-out photo as [x, y, w, h] (0-1 of the picture), or None (OpenCV's face finder)."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            g = np.asarray(im.convert("L"))
        casc = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
        faces = casc.detectMultiScale(g, scaleFactor=1.08, minNeighbors=6, minSize=(max(24, g.shape[1] // 12),) * 2)
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return [round(x / g.shape[1], 4), round(y / g.shape[0], 4), round(w / g.shape[1], 4), round(h / g.shape[0], 4)]
    except Exception:  # noqa: BLE001 - no OpenCV / unreadable: face props are left out
        return None


# ---- paper and grain (baked once per size/tone) ---------------------------------------------------------------------
def paper(tone: str, w: int, h: int, work: Path) -> tuple[Path, Path]:
    """(paper background PNG, transparent fine-grain overlay PNG)."""
    import numpy as np
    from PIL import Image, ImageFilter
    work.mkdir(parents=True, exist_ok=True)
    bg, gr = work / f"vox_paper_{tone[1:]}_{w}x{h}.png", work / f"vox_grain_{w}x{h}.png"
    if not bg.is_file():
        rng = np.random.default_rng(7)
        base = np.array([int(tone[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
        small = Image.fromarray((rng.random((max(2, h // 40), max(2, w // 40))) * 255).astype("uint8"), "L")
        mottle = np.asarray(small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(w / 60)),
                            np.float32) / 255 - 0.5
        fine = rng.normal(0, 1, (h, w)).astype(np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        vig = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
        dark = base.mean() < 90
        img = base[None, None, :] + (mottle * 10)[..., None] + (fine * 3.2)[..., None] - (vig * (18 if not dark else 10))[..., None]
        if tone.upper() == PAPERS["crumple"].upper():
            # crumpled paper: a web of soft creases, each a light ridge beside a dark fold
            from PIL import ImageDraw
            crease = Image.new("L", (w, h), 128)
            d = ImageDraw.Draw(crease)
            for _ in range(70):
                x, y = rng.random() * w, rng.random() * h
                for _ in range(int(rng.integers(3, 8))):
                    nx, ny = x + rng.normal(0, w * .09), y + rng.normal(0, h * .09)
                    d.line([(x, y), (nx, ny)], fill=int(rng.choice([70, 190])), width=max(1, w // 900))
                    x, y = nx, ny
            c = np.asarray(crease.filter(ImageFilter.GaussianBlur(max(1.0, w / 700))), np.float32) - 128
            facets = np.asarray(Image.fromarray((rng.random((max(2, h // 120), max(2, w // 120))) * 255).astype("uint8"), "L")
                                .resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(w / 400)), np.float32) / 255 - .5
            img = img + (c * 0.35 + facets * 14)[..., None]
        Image.fromarray(np.clip(img, 0, 255).astype("uint8"), "RGB").save(bg)
    if not gr.is_file():
        rng = np.random.default_rng(11)
        n = rng.normal(0, 1, (h, w)).astype(np.float32)
        a = np.clip(np.abs(n) * 26, 0, 70).astype("uint8")
        v = np.where(n > 0, 255, 0).astype("uint8")
        Image.fromarray(np.dstack([v, v, v, a]), "RGBA").save(gr)
    return bg, gr


def _font_css() -> str:
    faces = [("Anton", "anton-latin-400-normal", 400, "normal"), ("Bebas", "bebas-neue-latin-400-normal", 400, "normal"),
             ("Playfair", "playfair-display-latin-400-normal", 400, "normal"),
             ("Playfair", "playfair-display-latin-700-normal", 700, "normal"),
             ("Playfair", "playfair-display-latin-900-normal", 900, "normal"),
             ("Playfair", "playfair-display-latin-700-italic", 700, "italic"),
             ("DMSerif", "dm-serif-display-latin-400-normal", 400, "normal"),
             ("Inter", "inter-latin-400-normal", 400, "normal"), ("Inter", "inter-latin-600-normal", 600, "normal"),
             ("Inter", "inter-latin-800-normal", 800, "normal"),
             ("Mono", "jetbrains-mono-latin-400-normal", 400, "normal"),
             ("Mono", "jetbrains-mono-latin-700-normal", 700, "normal"),
             ("Oswald", "oswald-latin-600-normal", 600, "normal"), ("Archivo", "archivo-black-latin-400-normal", 400, "normal"),
             ("Caveat", "caveat-latin-700-normal", 700, "normal"), ("Marker", "permanent-marker-latin-400-normal", 400, "normal"),
             ("Kalam", "kalam-latin-700-normal", 700, "normal"), ("Kalam", "kalam-devanagari-700-normal", 700, "normal")]
    # Hindi under the same family names and the same weights (unicode-range: Devanagari only), so a Hindi headline
    # is set in a display face of the same character as the Latin one instead of falling back to a system font
    hindi = {"Playfair": "rozha-one-devanagari-400-normal", "DMSerif": "rozha-one-devanagari-400-normal",
             "Anton": "teko-devanagari-700-normal", "Bebas": "teko-devanagari-700-normal",
             "Oswald": "teko-devanagari-700-normal", "Archivo": "teko-devanagari-700-normal",
             "Mono": "mukta-devanagari-600-normal", "Caveat": "kalam-devanagari-700-normal",
             "Marker": "kalam-devanagari-700-normal"}
    for fam, _, wt, st in list(faces):
        if fam == "Inter":
            faces.append((fam, f"mukta-devanagari-{800 if wt >= 800 else 600}-normal", wt, st))
        elif fam in hindi:
            faces.append((fam, hindi[fam], wt, st))
    out = []
    for fam, f, wt, st in faces:
        p = FONTS / f"{f}.woff2"
        if p.is_file():
            rng = ";unicode-range:U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20B9,U+25CC,U+A830-A839,U+A8E0-A8FF" \
                if "devanagari" in f else ""
            out.append(f"@font-face{{font-family:'{fam}';src:url('{p.as_uri()}') format('woff2');"
                       f"font-weight:{wt};font-style:{st}{rng}}}")
    return "\n".join(out)


# ---- the page -------------------------------------------------------------------------------------------------------
_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
html,body{margin:0;padding:0;background:%PAPER%;overflow:hidden}
svg{display:block}
</style><script>%SVGJS%</script><script>%ILLU%</script></head><body><script>
const P=%PLAN%, W=%W%, H=%H%, DUR=%DUR%, K=%KIT%;
const TALL=H>W, U=Math.min(W,H), ACC=K.acc, INK=K.ink, PAPER=K.paper, DARK=K.dark;
// money drawings carry the currency the graphic's own figures are in (a dollar story never shows a rupee note)
window.CUR=(JSON.stringify(P).match(/[$£€¥₹]/)||['₹'])[0];
const ACT=K.dark?K.acc:(K.accText||K.acc);   // the accent as type on the paper: dark enough to read
const FG=DARK?'#F3EFE6':INK;
const draw=SVG().addTo('body').size(W,H);
const tracks=[], cam=[];
const E={out:t=>1-Math.pow(1-t,3), back:t=>{const c=1.6,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)},
  inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2, snap:t=>1-Math.pow(1-t,5), lin:t=>t};
function at(start,dur,fn,e){tracks.push({start,dur,fn,e:e||E.out})}
let seed=P.seed||1;function rnd(){seed=(seed*16807)%2147483647;return (seed-1)/2147483646}
// ---- layers (back to front) and the camera ----
const L={};L.paper=draw.group();const CONTENT=draw.group();const STAGE=CONTENT.group();   // STAGE: the layout's frame
['back','mid','hero','front'].forEach(k=>L[k]=STAGE.group());L.side=draw.group();L.grain=draw.group();
draw.defs().svg(`<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="${U*.004}" dy="${U*.012}" stdDeviation="${U*.011}" flood-color="#000" flood-opacity=".32"/></filter>
<filter id="softshadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="${U*.006}" stdDeviation="${U*.006}" flood-color="#000" flood-opacity=".22"/></filter>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="${U*.035}"/></filter>
<pattern id="ildots" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="2.5" cy="2.5" r="1.1" fill="#000" fill-opacity=".22"/></pattern>
<filter id="dof" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${U*.006}"/></filter>
<filter id="tint"><feFlood flood-color="${K.acc2||'#E0442C'}"/><feComposite in2="SourceAlpha" operator="in"/></filter>
<filter id="redch"><feColorMatrix type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .55 0"/></filter>
<filter id="cyanch"><feColorMatrix type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .55 0"/></filter>`);
L.paper.image(K.bg).size(W,H);
L.grain.image(K.grain).size(W,H).attr({style:'mix-blend-mode:multiply'}).opacity(DARK?.25:.55);
const DEPTH={paper:.012,back:.03,mid:.045,hero:.07,front:.055,side:.08};
// camera moves (one per shot, rotated through a video): 0 push in, 1 pull back, 2 slow lateral drift, 3 push in on the
// focus (the circled thing), so cut after cut the eye doesn't get the same move
// the exit: in the last moments the layers leave one after another (rise, fall, side or shrink), front first
const XORDER=['front','hero','mid','back'];
function exitOf(k,t){if(K.exit==='none'||k==='paper')return null;const i=XORDER.indexOf(k==='side'?'front':k);if(i<0)return null;
  const q=Math.max(0,Math.min(1,(t-(DUR-.62)-i*.05)/.3));if(q<=0)return null;const e=q*q;
  return {o:1-e,tx:K.exit==='side'?(K.dir||1)*W*.14*e:0,ty:K.exit==='rise'?-H*.1*e:K.exit==='fall'?H*.1*e:0,s:K.exit==='shrink'?1-.1*e:1}}
function camera(t){const p=E.inout(Math.min(1,t/Math.max(DUR,.1)));const m=K.cam||0;
  const fx=(m===3&&FOCUS)?Math.max(W*.3,Math.min(W*.7,FOCUS.x)):W/2,fy=(m===3&&FOCUS)?Math.max(H*.3,Math.min(H*.65,FOCUS.y)):H*.46;
  for(const k in DEPTH){const d=DEPTH[k]*(m===3?1.3:1);const q=m===1?1-p:p;const z=1+d*q;
    const dx=m===2?(p-.5)*(W*.03+d*W*.12)*(K.dir||1):0;   // layers travel together: labels stay on their bars
    const x=exitOf(k,t),zz=(m===2?1+d*.4:z)*(x?x.s:1);
    L[k].attr({transform:`translate(${fx*(1-zz)+dx+(x?x.tx:0)},${fy*(1-zz)+(x?x.ty:0)}) scale(${zz})`,opacity:x?x.o:1})}}
// ---- the style kit ----
function T(g,s,size,x,y,o){o=o||{};const t=g.text(String(s)).font({family:(K.fam||{})[o.family]||o.family||'Inter',size:size,weight:o.weight||600,
  anchor:o.anchor||'middle',style:o.italic?'italic':'normal'}).fill(o.fill||FG).attr({x:x,y:y,'dominant-baseline':'central'});
  if(o.ls&&!/[\u0900-\u097F]/.test(String(s)))t.attr({'letter-spacing':o.ls});return t}   // tracking breaks Devanagari conjuncts
function fit(t,maxw){const w=t.bbox().width;if(w>maxw)t.font({size:t.font('size')*maxw/w});return t}
function lines(s,size,maxw,family,weight,most){const words=String(s).split(/\s+/).filter(Boolean),out=[];let cur='';
  const pr=draw.text('').font({family:(K.fam||{})[family]||family,size:size,weight:weight});
  for(const w of words){const tr=cur?cur+' '+w:w;pr.text(tr);if(cur&&pr.bbox().width>maxw){out.push(cur);cur=w}else cur=tr}
  if(cur)out.push(cur);pr.remove();return out.slice(0,most||3)}
function boxText(g,s,size,x,y,o){ // black box(es), white serif type - one box per line, like a cut label
  o=o||{};const ls=lines(String(s).toUpperCase(),size,o.maxw||W*.4,o.family||'Playfair',900,o.most||3);const grp=g.group();const pad=size*.28;
  let yy=y;const anchor=o.anchor||'start';
  ls.forEach((ln,i)=>{const row=grp.group().addClass('keep');const t=T(row,ln,size,0,0,{family:o.family||'Playfair',weight:900,anchor:'start',fill:o.ink||'#FFFFFF',ls:'0.02em'});
    const bb=t.bbox();const r=row.rect(bb.width+pad*2,bb.height+pad*1.1).move(bb.x-pad,bb.y-pad*.55).fill(o.bg||'#111111').back();
    const w=bb.width+pad*2;const x0=anchor==='middle'?x-w/2+pad:anchor==='end'?x-w+pad:x+pad;
    row.attr({transform:`translate(${x0+(o.stagger?(i%2)*size*.9:0)},${yy})`});row.data('x',x0+(o.stagger?(i%2)*size*.9:0)).data('y',yy);yy+=bb.height+pad*1.5});
  return grp}
function tag(g,s,x,y,o){o=o||{};const grp=g.group();const size=o.size||U*.021;
  const t=T(grp,String(s).toUpperCase(),size,0,0,{family:'Inter',weight:800,anchor:'start',fill:o.ink||INK,ls:'0.14em'});
  const bb=t.bbox(),pad=size*.55;grp.rect(bb.width+pad*2,bb.height+pad*1.2).move(bb.x-pad,bb.y-pad*.6).fill(o.bg||'#FFFFFF')
    .stroke({color:o.ink||INK,width:Math.max(1,size*.07)}).back();
  grp.attr({transform:`translate(${x},${y})`});grp.data('w',bb.width+pad*2);return grp}
function highlight(g,bb,start,color){const r=g.rect(0,bb.height*.9).move(bb.x-bb.height*.12,bb.y+bb.height*.08).fill(color||ACC).back();
  at(start,.45,p=>r.width(Math.max(.1,(bb.width+bb.height*.24)*p)),E.inout);return r}
function brush(g,x,y,w,h,color,angle){ // a dry-brush stroke: ragged ends, streaky body
  const grp=g.group();const n=26;
  for(let k=0;k<7;k++){const yy=y+h*(k/7)+rnd()*h*.06;const th=h/7*(1.25+rnd()*.5);const x0=x+rnd()*w*.05;const x1=x+w*(.9+rnd()*.1);
    grp.rect(x1-x0,th).move(x0,yy).radius(th/2).fill(color||ACC).opacity(.86+rnd()*.14)}
  for(let k=0;k<n;k++){grp.circle(h*(.05+rnd()*.07)).center(x+w*(rnd()<.5?rnd()*.06:.94+rnd()*.06),y+rnd()*h).fill(color||ACC)}
  grp.attr({transform:`rotate(${angle||-6},${x+w/2},${y+h/2})`});return grp}
function disc(g,cx,cy,r,color){return g.circle(r*2).center(cx,cy).fill(color||ACC)}
function orb(g,cx,cy,r){return g.circle(r*2).center(cx,cy).fill(ACC).opacity(.85).attr({filter:'url(#blur)'})}
function cross(g,x,y,s){const c=g.group();c.line(x-s,y,x+s,y).stroke({color:FG,width:Math.max(1,U*.0016)});
  c.line(x,y-s,x,y+s).stroke({color:FG,width:Math.max(1,U*.0016)});c.circle(s*.9).center(x,y).fill('none').stroke({color:FG,width:Math.max(1,U*.0016)});return c}
function side(g,s){if(!s)return;const t=T(g,String(s),U*.019,0,0,{family:'Inter',weight:600,anchor:'middle',ls:'0.18em'});
  t.attr({transform:`translate(${W-U*.035},${H*.42}) rotate(90)`});return t}
function mono(g,s,x,y,o){o=o||{};const t=T(g,s,o.size||U*.019,x,y,{family:'Mono',weight:o.weight||400,anchor:o.anchor||'start',fill:o.fill||FG});
  if(o.type)typeIn(t,String(s),o.at||.6);return t}
function typeIn(t,full,start){ // the typewriter: letters appear one by one with a block cursor
  t.text('');at(start,Math.min(1.4,.1+full.length*.035),p=>{const n=Math.round(full.length*p);t.text(full.slice(0,n)+(p<1?'▌':''))},E.lin)}
function callout(g,x1,y1,x2,y2,s,start){ // dot on the subject, an elbow line, a mono note
  const dot=g.circle(U*.012).center(x1,y1).fill(ACC).stroke({color:INK,width:Math.max(1,U*.002)});
  const ln=g.polyline([[x1,y1],[x1,y1]]).fill('none').stroke({color:FG,width:Math.max(1,U*.0018)});
  const ls=lines(s,U*.027,W*.24,'Mono',400,3);const tg=g.group();const right=x2>x1;
  ls.forEach((l,i)=>mono(tg,l,x2+(right?U*.012:-U*.012),y2+i*U*.036,{size:U*.027,anchor:right?'start':'end',type:true,at:start+.5+i*.3}));
  [dot,tg].forEach(e=>e.opacity(0));
  at(start,.6,p=>{dot.opacity(Math.min(1,p*3));const mx=x1+(x2-x1)*.35;
    const pts=[[x1,y1],[mx,y2],[x2,y2]];const seg=p<.5?[[x1,y1],[x1+(mx-x1)*p*2,y1+(y2-y1)*p*2]]:[pts[0],pts[1],[mx+(x2-mx)*(p-.5)*2,y2]];
    ln.plot(seg);tg.opacity(p>.8?(p-.8)*5:0)},E.inout)}
function picture(g,pic,x,y,h,o){ // a cut-out photo (or its icon) with its height h, centred at x, bottom at y
  o=o||{};const grp=g.group();
  if(pic&&pic.img){const w=h*pic.w/pic.h;
    if(o.offset){grp.image(pic.img).size(w,h).move(x-w/2+U*.014,y-h+U*.01).attr({filter:'url(#tint)'})}   // a printed colour offset
    grp.image(pic.img).size(w,h).move(x-w/2,y-h).attr({filter:o.offset?'none':'url(#shadow)'});grp.data('w',w)}
  else if(pic&&pic.logo){const t=logoTile(grp,pic.logo,x,y-h/2,h);grp.data('w',h)}
  else if(pic&&pic.draw&&window.ILLU&&ILLU[pic.draw]){const [bw,bh,fn]=ILLU[pic.draw];const k=h/bh;const ig=grp.group();
    fn(ig,ACC);ig.attr({transform:`translate(${x-bw*k/2},${y-h}) scale(${k})`,filter:'url(#shadow)'});grp.data('w',bw*k)}
  else{const r=h*.42;grp.circle(r*2).center(x,y-h/2).fill(o.iconBg||'#FFFFFF').stroke({color:INK,width:U*.005}).attr({filter:'url(#softshadow)'});
    const ig=grp.group().addClass('keep');for(const nd of ((pic&&pic.o)||[])){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    const k=r*1.15/24;ig.attr({fill:'none',stroke:INK,'stroke-width':1.6,'stroke-linecap':'round','stroke-linejoin':'round',
      transform:`translate(${x-12*k},${y-h/2-12*k}) scale(${k})`});grp.data('w',r*2)}
  return grp}
// ---- motion kit (the stutter: these run on 12 fps steps) ----
function drop(el,start,dist,rot){el.opacity(0);const base=el.attr('transform')||'';const mb=mblur(el);
  at(start,.55,p=>{el.opacity(p>0?1:0);mb(Math.min(1,p),0,dist||H*.25);el.attr({transform:`translate(0,${-(dist||H*.25)*(1-p)}) rotate(${(rot||0)*(1-p)},${W/2},${H/2}) ${base}`})},E.back)}
// motion blur: while something travels it smears along its path, and snaps sharp when it lands
let MBN=0;function mblur(el){const id='mb'+(MBN++);const f=draw.defs().element('filter').attr({id:id,x:'-30%',y:'-30%',width:'160%',height:'160%'});
  const gb=f.element('feGaussianBlur').attr({stdDeviation:'0 0'});const w=document.createElementNS('http://www.w3.org/2000/svg','g');
  el.node.parentNode.insertBefore(w,el.node);w.appendChild(el.node);let last=0;
  return function(p,dx,dy){const v=Math.max(0,p-last);last=p;const sx=Math.min(U*.03,Math.abs(dx)*v*.9),sy=Math.min(U*.03,Math.abs(dy)*v*.9);
    if(p>=1||sx+sy<.4){w.removeAttribute('filter')}else{gb.attr({stdDeviation:sx.toFixed(1)+' '+sy.toFixed(1)});w.setAttribute('filter','url(#'+id+')')}}}
function slide(el,start,dx,dy){el.opacity(0);const base=el.attr('transform')||'';const mb=(Math.abs(dx||0)+Math.abs(dy||0))>U*.04?mblur(el):null;
  at(start,.45,p=>{el.opacity(Math.min(1,p*2));el.attr({transform:`translate(${(dx||0)*(1-p)},${(dy||0)*(1-p)}) ${base}`});if(mb)mb(p,dx||0,dy||0)},E.snap)}
function popIn(el,cx,cy,start,d){el.opacity(0);const base=el.attr('transform')||'';
  at(start,d||.42,p=>{const s=.4+.6*p;el.opacity(Math.min(1,p*2.5));el.attr({transform:`translate(${cx*(1-s)},${cy*(1-s)}) scale(${s}) ${base}`})},E.back)}
function wipe(el,start){el.opacity(0);at(start,.35,p=>el.opacity(p),E.lin)}

// ---- scenes ----
function propOver(g,pic,x,y,h){ // a symbolic prop laid over the photo (never changing the face itself)
  const w=h*(pic.w||1)/(pic.h||1),x0=x-w/2,y0=y-h;const f=pic.face;const grp=L.hero.group();const red='#D32F2F';
  if(['blindfold','mask','zip','crown'].includes(P.prop)&&!f)return null;
  if(f){const fx=x0+f[0]*w,fy=y0+f[1]*h,fw=f[2]*w,fh=f[3]*h;
    if(P.prop==='blindfold'){const by=fy+fh*.36,bw=fw*1.5,bh=fh*.2;grp.rect(bw,bh).move(fx+fw/2-bw/2,by).radius(bh*.25).fill(red)
        .attr({transform:`rotate(-3,${fx+fw/2},${by})`});grp.polygon([[fx+fw*1.2,by+bh*.4],[fx+fw*1.55,by+bh*1.8],[fx+fw*1.35,by+bh*1.9]].map(p=>p.join(',')).join(' ')).fill(red)}
    if(P.prop==='mask'){const by=fy+fh*.32,mw=fw*1.15,mh=fh*.26;grp.ellipse(mw,mh).center(fx+fw/2,by+mh/2).fill('#111');
      grp.ellipse(mw*.28,mh*.42).center(fx+fw*.3,by+mh/2).fill('#FFF').opacity(.0)}
    if(P.prop==='zip'){const zy=fy+fh*.82,zw=fw*.6;grp.rect(zw,fh*.07).move(fx+fw/2-zw/2,zy-fh*.035).fill('#C9A24A').stroke({color:'#6B5114',width:U*.002});
      for(let k=0;k<9;k++)grp.line(fx+fw/2-zw/2+zw*k/8,zy-fh*.035,fx+fw/2-zw/2+zw*k/8,zy+fh*.035).stroke({color:'#6B5114',width:U*.002});
      grp.rect(fh*.08,fh*.14).move(fx+fw/2+zw/2-fh*.02,zy-fh*.02).fill('#9C7A2A')}
    if(P.prop==='crown'){const cy=fy-fh*.42,cw=fw*.9;const pts=[[0,1],[0,.3],[.2,.6],[.35,0],[.5,.55],[.65,0],[.8,.6],[1,.3],[1,1]];
      grp.polygon(pts.map(p=>[fx+fw/2-cw/2+p[0]*cw,cy+p[1]*fh*.38].join(',')).join(' ')).fill('#E2B13C').stroke({color:'#7A5A12',width:U*.003})}}
  if(P.prop==='strings'){[.18,.5,.82].forEach(k=>{const sx=x0+w*k,sy=y0+h*(k===.5?.08:.3);grp.line(sx,U*.06,sx,sy).stroke({color:'#2A2A2A',width:Math.max(1.5,U*.0028)})});
    grp.rect(w*.9,U*.02).move(x0+w*.05,U*.05).fill('#5B3A1E').radius(U*.006)}
  if(P.prop==='chains'){for(let k=0;k<12;k++){const cx=x0+w*(.05+k*.08),cy=y0+h*.72+Math.sin(k)*h*.01;grp.ellipse(w*.1,h*.04).center(cx,cy).fill('none')
      .stroke({color:'#777',width:U*.008}).attr({transform:`rotate(${k%2?0:90},${cx},${cy})`})}}
  if(P.prop==='megaphone'){const mx=x0+w*.85,my=y0+h*.45;grp.polygon([[mx,my-h*.04],[mx+w*.35,my-h*.12],[mx+w*.35,my+h*.12],[mx,my+h*.04]].map(p=>p.join(',')).join(' ')).fill(red)}
  grp.attr({style:'filter:drop-shadow(0 2px 3px rgba(0,0,0,.35))'});return grp}
function hit(a,b){return a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h}
function free(r,taken){return r.x>=U*.03&&r.x+r.w<=W-U*.03&&r.y>=U*.03&&r.y+r.h<=(TALL?H*.6:H*.77)&&!taken.some(t=>hit(r,t))}
function hero(){
  const pics=P.pics||[], lay=P.layout, taken=[];
  const BOT=TALL?H*.62:H*.78;                       // above the captions
  let HH=TALL?H*.40:H*.66;                          // the subject fills most of the frame height
  const main=pics[0]||{};const ar=main.img?main.w/main.h:(main.draw&&window.ILLU&&ILLU[main.draw]?ILLU[main.draw][0]/ILLU[main.draw][1]:.84);
  const maxW=W*(TALL?(lay==='word'?.7:.86):(lay==='box'?.46:lay==='word'?.36:.6));   // 'word': the word must show both sides
  if(HH*ar>maxW)HH=maxW/ar;                         // a wide subject: as big as the width allows
  const MW=HH*ar;
  let cx=(lay==='box'&&!TALL)?W*.31:W/2;
  cx=Math.max(U*.05+MW/2,Math.min(W-U*.05-MW/2,cx));
  const heroBox={x:cx-MW/2,y:BOT-HH,w:MW,h:HH};FOCUS={x:cx,y:BOT-HH*.52,rx:Math.min(MW*.56,U*.42),ry:Math.min(HH*.58,U*.36)};
  const core={x:cx-MW*.3,y:BOT-HH*.85,w:MW*.6,h:HH*.7};taken.push(core);
  // back: the accent shape and the big word sit behind the subject
  if(lay==='disc'){const r=Math.max(HH*.46,MW*.48);const dx=cx+MW*.1,dy=BOT-HH*.62;const d=disc(L.back,dx,dy,r);popIn(d,dx,dy,.05,.5)}
  if(lay==='bars'){const bw=Math.max(MW*.22,W*(TALL?.12:.06));[[-.52,0,ACC],[.42,.12,INK]].forEach(([k,dy,c],i)=>{
      const x=cx+k*MW;const bh=HH*(1.04-dy);
      const b=L.back.rect(bw,bh).move(x-bw/2,BOT-bh).fill(c).opacity(i?0.92:1).attr({transform:`rotate(${i?4:-5},${x},${BOT})`});
      slide(b,.05+i*.12,0,H*.4)})}
  if(lay==='box'&&!TALL){const b=brush(L.back,cx-MW*.62,BOT-HH*.45,MW*1.24,HH*.22,ACC,-8);wipe(b,.1)}
  if(lay==='grid'){const gw=MW*1.5,gh=HH*1.02,gx=cx-gw/2,gy=BOT-gh;const gg=L.back.group();const st=U*.045;
    for(let x=gx;x<=gx+gw+1;x+=st)gg.line(x,gy,x,gy+gh).stroke({color:FG,width:Math.max(1,U*.0012)}).opacity(.45);
    for(let y=gy;y<=gy+gh+1;y+=st)gg.line(gx,y,gx+gw,y).stroke({color:FG,width:Math.max(1,U*.0012)}).opacity(.45);wipe(gg,.05)}
  if(lay==='word'){
    const word=P.word||(P.headline||'').toUpperCase();
    // widescreen: behind the subject's upper half (the subject cuts through it); Shorts: across the top, the
    // subject rising into its lower edge
    const t=TALL?T(L.back,word,W*.3,W/2,BOT-HH-W*.06,{family:'Anton',weight:400,fill:FG})
                :T(L.back,word,H*.5,W/2,BOT-HH*.66,{family:'Anton',weight:400,fill:FG,ls:'0.01em'});
    fit(t,W*.92);slide(t,.15,0,H*.06);const bb=t.bbox();taken.push({x:bb.x,y:bb.y,w:bb.width,h:bb.height})}
  orb(L.back,cx+(rnd()<.5?-1:1)*MW*.45,BOT-HH*.22,U*.075);
  // the subject(s): main one big, the others smaller at its sides
  pics.forEach((pic,i)=>{const isMain=i===0;const h=isMain?HH:HH*.46;
    const side=i===1?1:-1;const x=isMain?cx:Math.max(U*.12,Math.min(W-U*.12,cx+side*(MW*.5+HH*.22)));const y=isMain?BOT:BOT-HH*.02;
    const g=picture(isMain?L.hero:L.mid,pic,x,y,h,{offset:lay==='grid'});
    if(!isMain)taken.push({x:x-h*.4,y:y-h,w:h*.8,h:h});
    if(isMain&&P.prop&&K.props){const pg=propOver(g,pic,x,y,h);if(pg)drop(pg,.35,H*.3,-3)}
    drop(g,isMain?.35:.6+i*.15,H*.3,isMain?-3:4)});
  if(P.prop&&K.props){const it=tag(L.front,'ILLUSTRATION · OPINION',0,0,{size:U*.018,bg:'#111',ink:'#FFF'});
    const bb=it.bbox();it.attr({transform:`translate(${W-U*.05-bb.width},${U*.09})`});wipe(it,.5)}
  // headline: black boxes, serif
  if(P.headline&&!(lay==='word'&&P.word&&P.word===P.headline.toUpperCase())){
    let g;
    if(lay==='box'&&!TALL){g=boxText(L.front,P.headline,U*.075,Math.min(W*.6,cx+MW/2+U*.04),H*.28,{maxw:W*.34,stagger:true});
      g.children().forEach((row,i)=>slide(row,.75+i*.18,W*.06,0))}
    else{g=boxText(L.front,P.headline,U*(TALL?.055:.052),W/2,TALL?H*.11:H*.085,{anchor:'middle',maxw:W*.8,most:2});
      g.children().forEach((row,i)=>slide(row,.7+i*.15,0,-H*.05))}
    const bb=g.rbox(draw);taken.push({x:bb.x-U*.02,y:bb.y-U*.02,w:bb.width+U*.04,h:bb.height+U*.04})}
  // tags: around the subject's edges, never on the headline, the subject's middle or each other
  const cand=[];const ys=[.18,.42,.66,.3,.54,.06];
  for(const fy of ys){cand.push([heroBox.x-U*.02,BOT-HH*(1-fy),'end']);cand.push([heroBox.x+MW+U*.02,BOT-HH*(1-fy),'start'])}
  (P.tags||[]).forEach((s,i)=>{const g=tag(L.front,s,0,0,lay==='grid'?{bg:ACC,size:U*.026}:{});const bb=g.bbox();const tw=bb.width,th=bb.height;
    let spot=null;for(let k=0;k<cand.length&&!spot;k++){const [x,y,an]=cand[(k+i)%cand.length];
      const r={x:an==='end'?x-tw:x,y:y-th/2,w:tw,h:th};if(free(r,taken))spot=r}
    if(!spot){g.remove();return}
    taken.push({x:spot.x-U*.01,y:spot.y-U*.01,w:spot.w+U*.02,h:spot.h+U*.02});
    g.attr({transform:`translate(${spot.x-bb.x},${spot.y-bb.y})`});slide(g,1.0+i*.22,(spot.x<cx?-1:1)*W*.05,0)});
  // note with a leader line from the subject
  if(P.note){const right=cx<W*.55;const x1=cx+(right?MW*.12:-MW*.12),y1=BOT-HH*.6;
    let x2=right?Math.min(W*.72,heroBox.x+MW+U*.08):Math.max(W*.28,heroBox.x-U*.08),y2=TALL?H*.68:H*.62;
    const roomBeside=right?W-(heroBox.x+MW):heroBox.x;
    if(roomBeside<W*.22){x2=Math.min(W*.66,cx+MW*.2);y2=Math.max(H*.2,heroBox.y-U*.07)}   // a wide subject: the note goes above it
    callout(L.front,x1,y1,x2,y2,P.note,1.3)}
  // the small print: crosshairs, the mono date/place line, side text, the photo credit
  const c=U*.016;[[U*.05,U*.05],[W-U*.05,U*.05]].forEach(([x,y])=>cross(L.front,x,y,c));
  if(P.meta&&P.meta.length){mono(L.front,P.meta.join('  ·  ').toUpperCase(),U*.05,TALL?H*.66:H*.75,{weight:700,type:true,at:.9})}
  if(P.side)side(L.front,P.side.toUpperCase());
  if(P.credit){mono(L.front,P.credit,W-U*.03,H-U*.025,{size:U*.014,anchor:'end',fill:DARK?'#BBBBBB':'#555555'})}
}

// ---- more kit: torn paper, tape, pins, prints ----
function torn(g,x,y,w,h,fill,o){o=o||{};const pts=[];const st=Math.max(6,Math.round(w/(U*.018)));const j=U*.006;
  for(let i=0;i<=st;i++)pts.push([x+w*i/st,y+(rnd()-.5)*j*(o.top===false?0:1)]);
  const sv=Math.max(4,Math.round(h/(U*.018)));for(let i=1;i<=sv;i++)pts.push([x+w+(rnd()-.5)*j*(o.side===false?0:1),y+h*i/sv]);
  for(let i=st;i>=0;i--)pts.push([x+w*i/st,y+h+(rnd()-.5)*j*2.2]);
  for(let i=sv;i>0;i--)pts.push([x+(rnd()-.5)*j*(o.side===false?0:1),y+h*i/sv]);
  return g.polygon(pts.map(q=>q.join(',')).join(' ')).fill(fill||'#F4F0E6')}
function tape(g,x,y,w,ang){const t=g.rect(w,w*.32).move(x-w/2,y-w*.16).fill('#EFE6C9').opacity(.82)
  .attr({transform:`rotate(${ang||0},${x},${y})`});return t}
function pinAt(g,x,y){const p=g.group();p.circle(U*.026).center(x,y).fill('#B88A2E').stroke({color:'#6B4E14',width:Math.max(1,U*.002)});
  p.circle(U*.009).center(x-U*.004,y-U*.004).fill('#F2D58A');p.attr({filter:'url(#softshadow)'});return p}
function printCard(g,pic,x,y,h,ang,o){ // a photo print: white card with the cut-out (or its name) on it
  o=o||{};const grp=g.group();const ar=pic&&pic.img?pic.w/pic.h:1;const iw=Math.min(h*ar,h*1.5),ih=iw/ar;const pad=h*.06;
  grp.rect(iw+pad*2,ih+pad*2+(o.caption?h*.14:0)).move(x-iw/2-pad,y-ih/2-pad).fill('#FBFAF6').attr({filter:'url(#shadow)'});
  if(pic&&pic.img)grp.image(pic.img).size(iw,ih).move(x-iw/2,y-ih/2);
  else if(pic&&(pic.o||pic.draw)){const sub=picture(grp,pic,x,y+ih/2,ih*.9)}
  else T(grp,(o.label||'').toUpperCase(),h*.12,x,y,{family:'Archivo',weight:400,fill:INK});
  if(o.caption)T(grp,o.caption.toUpperCase(),h*.07,x,y+ih/2+pad+h*.06,{family:'Mono',weight:700,fill:INK});
  grp.attr({transform:`rotate(${ang||0},${x},${y})`});return grp}
function picOf(name){return (P.pics||[]).find(p=>p.name===name)}
function rich(g,s,size,x,y,o){ // a headline where *words* get the accent highlighter
  o=o||{};const parts=String(s).split(/(\*[^*]+\*)/).filter(Boolean);const grp=g.group().addClass('keep');let cx=0;const marks=[];
  parts.forEach(pt=>{const hl=pt.startsWith('*');const t=T(grp,pt.replace(/\*/g,''),size,cx,0,{family:o.family||'Playfair',weight:o.weight||900,anchor:'start',fill:o.fill||FG});
    const bb=t.bbox();if(hl)marks.push(bb);cx+=bb.width+size*.18});
  marks.forEach((bb,i)=>highlight(grp,bb,(o.start||.6)+.15*i,o.mark||ACC));
  const w=cx-size*.18;grp.attr({transform:`translate(${o.anchor==='middle'?x-w/2:x},${y})`});grp.data('w',w);return grp}

// ---- round 2 scenes ----
function desk(){ // grid paper, a pen, stacked photo prints, a paperclip and a label strip
  const g=L.paper.group().opacity(.55);const st=Math.round(U/22);
  for(let x=0;x<W;x+=st)g.line(x,0,x,H).stroke({color:'#9DB7CF',width:1});for(let y=0;y<H;y+=st)g.line(0,y,W,y).stroke({color:'#9DB7CF',width:1});
  const pen=L.back.group();pen.rect(U*.42,U*.03).move(-U*.21,-U*.015).radius(U*.015).fill('#1E2A44');pen.rect(U*.06,U*.034).move(U*.17,-U*.017).fill('#111');
  pen.attr({transform:`translate(${W*.12},${H*.2}) rotate(-38)`});slide(pen,.05,-W*.1,0);
  const subs=P.subjects||[];const cx=W*.5,cy=TALL?H*.36:H*.44,h=TALL?H*.26:H*.46;
  subs.forEach((n,i)=>{const k=subs.length-1-i;const pic=picOf(n);const ang=[-4,3,-2,5][i%4];
    const c=printCard(L.hero,pic,cx+(k-(subs.length-1)/2)*h*.28,cy+k*h*.04,h*(i===0?1:.82),ang,{label:n});
    drop(c,.2+k*.18,H*.25,ang*2)});
  if(P.label){const strip=L.front.group();const lb=T(strip,P.label.toUpperCase(),U*.05,0,0,{family:'Bebas',weight:400,anchor:'start',fill:INK,ls:'0.04em'});
    const bb=lb.bbox();strip.rect(bb.width+U*.06,bb.height+U*.02).move(bb.x-U*.03,bb.y-U*.01).fill(ACC).back();
    const x=cx-h*.55,y=cy+h*.58;strip.attr({transform:`translate(${x},${y}) rotate(-3)`});slide(strip,.95,-W*.1,0)}
  const clip=L.front.group();clip.path(`M0 ${U*.12} L0 ${U*.02} Q0 0 ${U*.018} 0 Q${U*.036} 0 ${U*.036} ${U*.02} L${U*.036} ${U*.1}`).fill('none')
    .stroke({color:'#9AA0A6',width:U*.006,linecap:'round'});clip.attr({transform:`translate(${cx-h*.48},${cy-h*.56})`});wipe(clip,.9);
  if(P.note){const nx=TALL?W*.12:cx+h*.62,ny=TALL?cy+h*.95:cy-h*.4;const t=T(L.front,P.note,U*.032,nx,ny,{family:'Mono',weight:700,anchor:'start',fill:INK});fit(t,W-nx-U*.05);wipe(t,1.2);
    const u=L.front.line(nx,ny+U*.04,nx,ny+U*.04).stroke({color:INK,width:U*.004});
    at(1.3,.5,p=>u.plot(nx,ny+U*.04,nx+t.bbox().width*p,ny+U*.04),E.inout)}}

function evidence(){ // a pinned board on kraft paper: cards, red string pin to pin, tape, an EVIDENCE tag
  const it=P.items, n=it.length;const cx=W/2,cy=TALL?H*.36:H*.43;const R=TALL?[W*.34,H*.2]:[W*.32,H*.27];
  const pos=[[cx,cy]];for(let i=1;i<n;i++){const a=-Math.PI*.82+(i-1)*(Math.PI*1.64/Math.max(1,n-2))*(n>2?1:0)+(n===2?Math.PI*.82:0);
    pos.push([cx+Math.cos(a)*R[0],cy+Math.sin(a)*R[1]*1.05])}
  const sz=TALL?U*.3:U*.3;const pins=[];
  it.forEach((x,i)=>{const [px,py]=pos[i];const ang=(rnd()-.5)*8;const h=i===0?sz*1.25:sz*.78;let card;
    if(x.kind==='photo'){const pic=picOf(x.name);card=printCard(L.hero,pic||null,px,py,h,ang,{label:x.name.replace(/^person:/i,''),
        caption:x.name.toLowerCase().startsWith('person:')?x.name.slice(7):''});}
    else if(x.kind==='date'){card=L.hero.group();const w=h*.62,hh=h*.75;torn(card,px-w/2,py-hh/2,w,hh,'#F6F2E7');
      T(card,x.mon,hh*.16,px,py-hh*.28,{family:'Archivo',weight:400,fill:INK});T(card,x.day||'',hh*.36,px,py+hh*.02,{family:'Archivo',weight:400,fill:INK});
      T(card,x.year,hh*.14,px,py+hh*.32,{family:'Archivo',weight:400,fill:INK});card.attr({transform:`rotate(${ang},${px},${py})`,filter:'url(#shadow)'})}
    else{card=L.hero.group();const t=T(card,x.text,h*.2,px,py,{family:'Archivo',weight:400,fill:INK});const bb=t.bbox();
      torn(card,bb.x-h*.08,bb.y-h*.06,bb.width+h*.16,bb.height+h*.12,'#F6F2E7').back();card.attr({transform:`rotate(${ang},${px},${py})`,filter:'url(#shadow)'})}
    const bb=card.rbox(draw);const pinY=bb.y+U*.02;pins.push([px,pinY]);
    drop(card,.15+i*.22,H*.2,ang);const pn=pinAt(L.front,px,pinY);popIn(pn,px,pinY,.35+i*.22,.3);
    if(i>0)tape(L.front,bb.x+bb.width*.15,bb.y+bb.height*.92,U*.07,-20)});
  for(let i=1;i<n;i++){const [x1,y1]=pins[0],[x2,y2]=pins[i];const ln=L.mid.line(x1,y1,x1,y1).stroke({color:'#C0262D',width:U*.004});
    at(.5+i*.25,.45,p=>ln.plot(x1,y1,x1+(x2-x1)*p,y1+(y2-y1)*p),E.inout)}
  const casey=/\?|case|evidence|crime|murder|scam|who|mystery|probe|investigat/i.test(P.title||'');
  if(casey){const ev=tag(L.front,'EVIDENCE',0,0,{size:U*.026});const eb=ev.bbox();ev.attr({transform:`translate(${cx-eb.width/2},${TALL?H*.6:H*.74})`});wipe(ev,1.4)}
  if(P.title){const g=boxText(L.front,P.title,U*.05,W/2,TALL?H*.08:H*.06,{anchor:'middle',maxw:W*.8,most:1});g.children().forEach((r,i)=>slide(r,.1,0,-H*.05))}
  if(casey){const q=L.front.group();q.circle(U*.09).center(W-U*.12,TALL?H*.6:H*.72).fill('none').stroke({color:'#C0262D',width:U*.006});
  T(q,'?',U*.06,W-U*.12,TALL?H*.6:H*.72,{family:'Archivo',weight:400,fill:'#C0262D'});wipe(q,1.6)}}

function opener(){ // a colour panel with the headline, the photo beside it
  const real=((P.pics||[])[0]||{}).img||((P.pics||[])[0]||{}).draw;if(!real)P.pics=[];
  const left=!TALL&&!!real;const pw=left?W*.46:W,ph=left?H:(real?H*.42:H);const pan=L.back.rect(pw,ph).move(0,0).fill(ACC);
  slide(pan,0,left?-pw:0,left?0:-ph);
  const pic=(P.pics||[])[0];
  if(pic){const h=left?H*.86:H*.46;const x=left?W*.72:W/2;const y=left?H*.97:H*.94;const g=picture(L.hero,pic,x,y,h);drop(g,.3,H*.2,-2)}
  const size=left?U*.1:U*.12;const ls=lines(P.headline.replace(/\*/g,''),size,(left?pw:W)*.84,'Playfair',900,3);
  const words=P.headline.split(/(\*[^*]+\*)/).filter(Boolean);const hi=new Set();words.forEach(w=>{if(w.startsWith('*'))w.replace(/\*/g,'').split(/\s+/).forEach(x=>hi.add(x))});
  const x0=left?W*.05:W*.08;let y=left?H*.5-ls.length*size*.6:(real?H*.12:H*.46-ls.length*size*.55);
  if(P.kicker){const k=T(L.front,P.kicker.toUpperCase(),U*.03,x0,y-size*.75,{family:'Inter',weight:800,anchor:'start',fill:INK,ls:'0.16em'});wipe(k,.3)}
  ls.forEach((ln,i)=>{const row=L.front.group().addClass('keep');let cx=0;ln.split(' ').forEach(w=>{const t=T(row,w,size,cx,0,{family:'Playfair',weight:900,anchor:'start',fill:hi.has(w)?'#FFFFFF':INK});cx+=t.bbox().width+size*.22});
    row.attr({transform:`translate(${x0},${y+i*size*1.1})`});slide(row,.45+i*.15,-W*.05,0)})}

function reveal(){ // a document; a magnifier sweeps it and the beam shows the text big and sharp
  const docW=TALL?W*.84:W*.56,docH=TALL?H*.4:H*.58,dx=W/2-docW/2,dy=TALL?H*.16:H*.16;
  const doc=L.back.group();torn(doc,dx,dy,docW,docH,'#FBF9F3');doc.attr({filter:'url(#shadow)'});slide(doc,0,0,H*.1);
  const rows=P.rows;const rs=docH/(rows.length+2.2);
  rows.forEach((r,i)=>{const t=T(L.back,r,rs*.42,dx+docW*.08,dy+rs*(i+1.4),{family:'Mono',weight:700,anchor:'start',fill:'#3A3A3A'});wipe(t,.15+i*.05);
    if(P.mark&&r.toLowerCase().includes(P.mark.toLowerCase()))highlight(L.back,t.bbox(),1.6)});
  if(P.title){const g=boxText(L.front,P.title,U*.05,W/2,TALL?H*.07:H*.075,{anchor:'middle',maxw:W*.8,most:1});g.children().forEach(r=>slide(r,.1,0,-H*.04))}
  // the lens: a magnified copy of the document inside a circle that sweeps down
  const R=U*(TALL?.17:.15);const lens=L.front.group();const clipC=draw.clip().add(draw.circle(R*2).center(0,0));
  const mag=lens.group().clipWith(clipC);const inner=mag.group();
  inner.rect(docW,docH).move(dx,dy).fill('#FFFFFF');
  rows.forEach((r,i)=>T(inner,r,rs*.42,dx+docW*.08,dy+rs*(i+1.4),{family:'Mono',weight:700,anchor:'start',fill:'#111'}));
  lens.circle(R*2).center(0,0).fill('none').stroke({color:'#222',width:U*.012});
  const handle=lens.rect(U*.03,U*.16).move(R*.62,R*.62).radius(U*.01).fill('#2A2A2A').attr({transform:`rotate(-45,${R*.62},${R*.62})`});
  const hand=(P.pics||[])[0];if(hand&&hand.img){const hh=U*.22;lens.image(hand.img).size(hh*hand.w/hand.h,hh).move(R*.8,R*.75)}
  lens.attr({filter:'url(#shadow)'});lens.opacity(0);
  const path=[[dx+docW*.25,dy+rs*1.2],[dx+docW*.62,dy+rs*2.5],[dx+docW*.35,dy+rs*(rows.length*.8+1)]];
  at(.5,Math.max(1.5,DUR-.9),p=>{lens.opacity(Math.min(1,p*6));const q=p*(path.length-1),i=Math.min(path.length-2,Math.floor(q)),f=q-i;
    const x=path[i][0]+(path[i+1][0]-path[i][0])*f,y=path[i][1]+(path[i+1][1]-path[i][1])*f;
    lens.attr({transform:`translate(${x},${y})`});const z=1.8;inner.attr({transform:`translate(${-x*z},${-y*z}) scale(${z})`})},E.inout)}

function newsprint(){ // a pile of newspaper scraps behind: columns of grey type lines, no readable words
  const g=L.paper.group().opacity(DARK?.25:.5);
  for(let k=0;k<16;k++){const w=U*(.35+rnd()*.4),h=U*(.25+rnd()*.35),x=rnd()*W-w*.2,y=rnd()*H-h*.2,a=(rnd()-.5)*14;
    const sc=g.group();torn(sc,x,y,w,h,['#E9E4D8','#DCD6C8','#F1EDE3'][k%3]);const cols=2+Math.floor(rnd()*2);
    for(let c=0;c<cols;c++)for(let r=0;r<Math.floor(h/(U*.022));r++){const lw=(w/cols-U*.03)*(.6+rnd()*.4);
      sc.rect(lw,U*.008).move(x+U*.02+c*w/cols,y+U*.03+r*U*.022).fill('#9A958A').opacity(.7)}
    if(rnd()<.6)sc.rect(w*.8,U*.035).move(x+U*.02,y+U*.012).fill('#555').opacity(.8);
    sc.attr({transform:`rotate(${a},${x+w/2},${y+h/2})`})}}
function headline(){ // a torn newspaper headline with cut-outs around it, a big chapter number
  newsprint();
  const cw=TALL?W*.82:W*.44,ch=TALL?H*.2:H*.36,cx=W/2-cw/2+(TALL?0:W*.04),cy=TALL?H*.34:H*.42;
  if(P.number){const n=T(L.back,P.number,TALL?W*.38:H*.42,TALL?W/2:W*.2,TALL?H*.16:H*.36,{family:'Inter',weight:800,fill:DARK?'#F3EFE6':'#FFFFFF'});
    n.attr({style:'paint-order:stroke',stroke:DARK?'none':'#00000010'});slide(n,.05,-W*.05,0)}
  disc(L.back,cx+cw*.85,cy-ch*.05,U*.12,ACC);
  const subs=P.subjects||[];subs.forEach((nm,i)=>{const pic=picOf(nm);if(!pic)return;const h=TALL?H*.24:H*.5;
    const x=[cx+cw*.5,cx-cw*.02,cx+cw*1.02][i%3],y=cy+(i===0?ch*.05:ch*.75);const g=picture(L.mid,pic,x,y,i===0?h:h*.6);drop(g,.25+i*.2,H*.25,i?4:-3)});
  const card=L.hero.group();torn(card,cx,cy,cw,ch,'#EEE9DC');card.attr({filter:'url(#shadow)'});
  const size=Math.min(ch*.26,U*.065);const ls=lines(P.text,size,cw*.86,'Playfair',700,3);
  ls.forEach((l,i)=>T(card,l,size,cx+cw*.07,cy+ch*.2+i*size*1.12,{family:'Playfair',weight:700,anchor:'start',fill:'#1A1A1A'}));
  if(P.source)T(card,P.source.toUpperCase(),U*.018,cx+cw*.07,cy+ch*.9,{family:'Mono',weight:700,anchor:'start',fill:'#555'});
  drop(card,.6,H*.2,-4);tape(L.front,cx+cw*.1,cy+U*.01,U*.09,-12);
}

function pinmap(){ // the country outline; the place highlighted; the headline clipping drops on the pin
  const bx=P.box,ms=Math.min((TALL?W*.86:W*.5)/bx[0],(TALL?H*.42:H*.72)/bx[1]);const ox=(TALL?W/2:W*.34)-bx[0]*ms/2,oy=(TALL?H*.28:H*.42)-bx[1]*ms/2;
  if(P.atlas)atlasSea();
  const m=L.back.group();P.shapes.forEach(r=>{m.polygon(r.map(q=>[ox+q[0]*ms,oy+q[1]*ms].join(',')).join(' ')).fill(P.pen?'#EFE3C2':P.atlas?(P.pin?'#EFE3C2':'#D9542C'):(P.pin?'#E2DBCC':ACC))
    .stroke({color:P.atlas?'#8E7E5C':'#9A9282',width:Math.max(1,U*.0016)})});if(P.atlas)depthOfField(m);m.opacity(0);at(0,.6,p=>m.opacity(p));
  if(P.country){const c=T(L.back,P.country.toUpperCase(),U*.03,ox+bx[0]*ms/2,oy-U*.03,{family:'Inter',weight:800,ls:'0.3em',fill:'#8C8577'});wipe(c,.3)}
  let px=ox+bx[0]*ms*(P.pin?.5:.92),py=oy+bx[1]*ms/2;   // no pin: the card goes beside the country, not on it
  if(P.pen&&!P.pin)P.shapes.forEach(r=>penHatch(L.mid,r.map(q=>[ox+q[0]*ms,oy+q[1]*ms]),.4));
  if(P.pen&&P.pin)penCircle(L.front,ox+P.pin[0]*ms,oy+P.pin[1]*ms,U*.06,.9);
  if(P.pin){px=ox+P.pin[0]*ms;py=oy+P.pin[1]*ms;FOCUS={x:px,y:py,rx:U*.07,ry:U*.06};const ring=L.mid.circle(U*.05).center(px,py).fill(ACC).opacity(.5);popIn(ring,px,py,.5);
    const dot=L.mid.circle(U*.02).center(px,py).fill('#C0262D').stroke({color:'#FFFFFF',width:U*.004});popIn(dot,px,py,.55);
    const lb=tag(L.front,P.place,px+U*.025,py-U*.05);slide(lb,.7,W*.03,0)}
  const who=(P.pics||[])[0];   // a real photo pinned beside the place, like evidence on a map
  if(who){const h=TALL?H*.2:H*.34,x=TALL?Math.min(W*.78,px+W*.22):Math.max(W*.14,px-W*.2),y=TALL?Math.max(H*.2,py-H*.1):Math.max(H*.26,py-H*.05);
    const card=printCard(L.hero,who,x,y,h,-4,{caption:(who.name||'').replace(/^person:/i,'')});drop(card,.7,H*.2,-6);
    pinAt(L.front,x,y-h*.5+U*.012);const ln=L.mid.line(x,y,px,py).stroke({color:'#C0262D',width:U*.003});wipe(ln,1.0)}
  if(P.headline){const cw=TALL?W*.8:W*.38,ch=TALL?H*.16:H*.26;const cx=TALL?W*.1:Math.min(W-cw-U*.04,px+U*.24),cy=TALL?H*.58:Math.max(H*.14,py-ch*.4);
    const card=L.hero.group();torn(card,cx,cy,cw,ch,'#F3EFE4');const size=Math.min(ch*.24,U*.05);
    lines(P.headline,size,cw*.86,'Playfair',700,3).forEach((l,i)=>T(card,l,size,cx+cw*.07,cy+ch*.22+i*size*1.12,{family:'Playfair',weight:700,anchor:'start',fill:'#1A1A1A'}));
    if(P.source)T(card,P.source.toUpperCase(),U*.017,cx+cw*.07,cy+ch*.88,{family:'Mono',weight:700,anchor:'start',fill:'#555'});
    card.attr({filter:'url(#shadow)'});drop(card,1.0,H*.2,-3);const pn=pinAt(L.front,cx+cw/2,cy+U*.015);popIn(pn,cx+cw/2,cy+U*.015,1.4,.3)}}

function number(){ // a huge number; the subject breaks out of it
  const pic=(((P.pics||[])[0]||{}).img||((P.pics||[])[0]||{}).draw)?(P.pics||[])[0]:null;
  if(pic&&!TALL&&K.lay==='side')return numberSide(pic);const big=T(L.back,P.number,TALL?W*.42:H*(pic?.5:.56),W/2,pic?(TALL?H*.22:H*.3):(TALL?H*.34:H*.4),{family:'Anton',weight:400,fill:ACT});fit(big,W*.92);
  slide(big,.05,0,H*.06);
  if(pic){const d0=pic.draw&&window.ILLU[pic.draw],ar0=pic.img?pic.w/pic.h:d0?d0[0]/d0[1]:1;
    const h=TALL?H*.36:Math.min(H*.56,W*.42/ar0,H*.46*(ar0>1.3?1:1.22));   // a wide subject stays under the figure, not over it
    const g=picture(L.hero,pic,W/2,TALL?H*.64:H*.86,h);drop(g,.35,H*.25,-2);
    FOCUS=FOCUS||{x:W/2,y:(TALL?H*.64:H*.86)-h*.45,rx:Math.min(U*.3,(g.data('w')||h)*.6),ry:h*.42}}   // marker and logos go by the subject, off the figure
  if(P.caption){const c=pic?fit(T(L.front,P.caption,U*.04,W/2,TALL?H*.7:H*.92,{family:'Inter',weight:800,fill:'#C0262D'}),W*.9)
      :boxText(L.front,P.caption,U*.055,W/2,TALL?H*.5:H*.7,{anchor:'middle',maxw:W*.86,most:2});wipe(c,.9)}
  if(P.kicker){const k=T(L.front,P.kicker.toUpperCase(),U*.024,W/2,TALL?H*.08:H*.08,{family:'Inter',weight:800,fill:'#C0262D',ls:'0.45em'});wipe(k,.2)}}

function numberSide(pic){ // second layout: the number and its words on the left, the subject standing on the right
  // the number across the top, the subject lower right, the words lower left: nothing overlaps the figure
  const big=T(L.back,P.number,H*.34,W*.05,H*.24,{family:'Anton',weight:400,fill:ACT,anchor:'start'});fit(big,W*.9);slide(big,.05,-W*.05,0);
  const d=pic.draw&&window.ILLU[pic.draw],ar=pic.img?pic.w/pic.h:d?d[0]/d[1]:1;   // tall subjects stand taller
  const ph=Math.min(H*.74,W*.5/ar),g=picture(L.hero,pic,ar<1?W*.72:W*.66,H*.95,ph);drop(g,.35,H*.25,2);FOCUS=FOCUS||{x:W*.32,y:H*.4,rx:W*.26,ry:H*.2};
  if(P.caption){const c=boxText(L.front,P.caption,U*.05,W*.05,H*.66,{anchor:'start',maxw:W*.36,most:3});wipe(c,.9)}
  if(P.kicker){const k=T(L.front,P.kicker.toUpperCase(),U*.024,W*.05,H*.06,{family:'Inter',weight:800,fill:'#C0262D',ls:'0.45em',anchor:'start'});wipe(k,.2)}}

// ---- round 3: charts made of objects ----
function chartTitle(s){if(!s)return;const g=boxText(L.front,s,U*.05,W/2,TALL?H*.07:H*.075,{anchor:'middle',maxw:W*.84,most:2});
  g.children().forEach((r,i)=>slide(r,.05+i*.1,0,-H*.04))}
function valLabel(g,s,x,y,o){o=o||{};const t=T(g,s,o.size||U*.045,x,y,{family:'Anton',weight:400,fill:o.fill||FG,anchor:o.anchor||'middle'});return t}
function seats(){ // the semicircle of dots, filled in party order; the majority line
  chartTitle(P.title);const n=P.total;const cx=W/2,cy=TALL?H*.5:H*.7;const R1=TALL?W*.44:Math.min(W*.36,H*.52),R0=R1*.42;
  let rows=1;while(true){let cap=0;for(let r=0;r<rows;r++){const rr=R0+(R1-R0)*(r+.5)/rows;cap+=Math.floor(Math.PI*rr/((R1-R0)/rows))}if(cap>=n||rows>30)break;rows++}
  const pts=[];for(let r=0;r<rows;r++){const rr=R0+(R1-R0)*(r+.5)/rows;const k=Math.floor(Math.PI*rr/((R1-R0)/rows));for(let i=0;i<k;i++){const a=Math.PI-(Math.PI*(i+.5)/k);pts.push([a,cx+Math.cos(a)*rr,cy-Math.sin(a)*rr])}}
  pts.sort((p,q)=>q[0]-p[0]);const dot=(R1-R0)/rows*.78;
  const cols=[ACC,DARK?'#E8E2D4':'#2B2B2B','#9A9A9A','#C9C1B0','#6E8CA8','#B5735A','#7A9A6E','#B9A35E'];
  let k=0;P.groups.forEach((g,gi)=>{const c=cols[gi%cols.length];const cnt=Math.round(g.value);const st=.3+gi*.45;
    for(let i=0;i<cnt&&k<pts.length;i++,k++){const p=pts[k];const d=L.hero.circle(dot).center(p[1],p[2]).fill(c);d.opacity(0);const t0=st+i/cnt*.9;at(t0,.08,q=>d.opacity(q),E.lin)}
    const lx=TALL?W*.1:(gi%2?cx+R1+U*.04:cx-R1-U*.04),ly=TALL?cy+U*.08+gi*U*.07:cy-R1*.75+Math.floor(gi/2)*U*.12;
    const lg=L.front.group();lg.rect(U*.03,U*.03).move(0,-U*.015).fill(c);
    const tt=T(lg,`${g.label} — ${g.shown}`.toUpperCase(),U*.03,U*.045,0,{family:'Inter',weight:800,anchor:'start'});
    const an=(TALL||gi%2)?'start':'end';if(an==='end'){lg.attr({transform:`translate(${lx-tt.bbox().width-U*.045},${ly})`})}else lg.attr({transform:`translate(${lx},${ly})`});
    wipe(lg,st+.4)});
  const ml=L.front.line(cx,cy-R1-U*.02,cx,cy-R0+U*.01).stroke({color:FG,width:U*.003,dasharray:`${U*.008} ${U*.006}`});wipe(ml,1.6);
  const mt=T(L.front,`MAJORITY ${P.majority}`,U*.024,cx,cy-R1-U*.045,{family:'Mono',weight:700});wipe(mt,1.7);
  const tot=T(L.front,String(P.total),U*.075,cx,cy-U*.06,{family:'Anton',weight:400});const ts=T(L.front,'SEATS',U*.022,cx,cy-U*.005,{family:'Inter',weight:800,ls:'.2em'});wipe(tot,.2);wipe(ts,.25)}
function material(g,mat,x,y,w,h,color,i){ // one bar as a real thing; x,y = bottom-left
  if(mat==='coins'){const ch=w*.16;const n=Math.max(1,Math.round(h/ch));for(let k=0;k<n;k++){const yy=y-(k+1)*ch;
      g.ellipse(w,ch*1.1).move(x,yy).fill(k%2?'#C9A24A':'#D9B55A').stroke({color:'#8A6A22',width:Math.max(1,U*.0015)})}
    g.ellipse(w,ch*1.1).move(x,y-n*ch-ch*.55).fill('#E8C86E').stroke({color:'#8A6A22',width:Math.max(1,U*.0015)});return}
  if(mat==='pillars'){g.rect(w*1.2,w*.14).move(x-w*.1,y-w*.14).fill('#DCD6CA');const sh=h-w*.36;
    g.rect(w,sh).move(x,y-w*.14-sh).fill('#EDE8DE');for(let k=1;k<6;k++)g.line(x+w*k/6,y-w*.14-sh,x+w*k/6,y-w*.14).stroke({color:'#B9B1A1',width:Math.max(1,w*.02)});
    g.rect(w*1.25,w*.22).move(x-w*.125,y-h).fill('#DCD6CA');g.rect(w*1.25,h).move(x-w*.125,y-h).fill('none').stroke({color:'#00000010'});return}
  if(mat==='chimneys'){const top=y-h;g.polygon([[x+w*.1,y],[x+w*.9,y],[x+w*.8,top],[x+w*.2,top]].map(p=>p.join(',')).join(' ')).fill(color);
    for(let k=1;k<4;k++){const yy=top+h*k/4;g.rect(w*.66,h*.03).move(x+w*.17,yy).fill('#00000022')}
    g.rect(w*.7,w*.12).move(x+w*.15,top-w*.06).fill('#333');
    const sm=g.group();for(let k=0;k<5;k++)sm.circle(w*(.5+k*.18)).center(x+w*.5+k*w*.18,top-w*.3-k*w*.28).fill('#2A2A2A').opacity(.55-k*.07);
    sm.attr({filter:'url(#blur)'}).opacity(.9);return}
  if(mat==='buildings'){g.rect(w,h).move(x,y-h).fill(color);const cw=w/5,rh=w/5;for(let r=0;r*rh<h-rh;r++)for(let c=0;c<4;c++)
      g.rect(cw*.55,rh*.5).move(x+cw*(c+.6),y-h+rh*(r+.4)).fill(i%2?'#F3E9C8':'#FFFFFF').opacity(.75);
    g.rect(w*.06,h*.12).move(x+w*.47,y-h-h*.12).fill(color);return}
  if(mat==='books'){const cols2=['#7A2E26','#E2B13C','#1F4E3D','#7B5233','#222','#2C3E66','#8B3A2B'];g.rect(w,h).move(x,y-h).fill(cols2[i%cols2.length]).radius(w*.04);
    g.rect(w,h*.04).move(x,y-h*.9).fill('#D8B65A').opacity(.8);g.rect(w,h*.04).move(x,y-h*.12).fill('#D8B65A').opacity(.8);return}
  g.rect(w,h).move(x,y-h).fill(color)}
function stack(){
  chartTitle(P.title);const vs=P.values,n=vs.length,mx=Math.max(...vs.map(v=>v.value));
  const base=TALL?H*.66:H*.82,area=W*(TALL?.84:.7),maxh=TALL?H*.42:H*.56,gap=area/n,bw=Math.min(gap*.56,U*.2);
  L.mid.line(W/2-area/2,base,W/2+area/2,base).stroke({color:FG,width:U*.004});
  vs.forEach((v,i)=>{const x=W/2-area/2+gap*(i+.5)-bw/2;const h=Math.max(U*.02,maxh*v.value/mx);const g=L.hero.group();
    material(g,P.material,x,base,bw,h,v.value===mx?ACC:'#3A3A3A',i);const clip=draw.clip().add(draw.rect(W,H).move(0,0));
    const st=.25+i*.25;g.opacity(0);at(st,.6,p=>{g.opacity(1);g.attr({transform:`translate(0,${h*(1-p)})`})},E.back);
    if(v.value===mx)FOCUS={x:x+bw/2,y:base-h*.55,rx:bw*.95,ry:Math.max(h*.6,U*.08)};
    const lm=(P.logos||[]).find(m=>!m.used&&v.label&&(m.title.toLowerCase()===v.label.toLowerCase()||m.key===v.label.toLowerCase()));
    if(lm){lm.used=true;const sz=Math.min(bw*.8,U*.1),ty=base-h-U*.12-sz/2;const t=logoTile(L.front,lm,x+bw/2,ty,sz);popIn(t,x+bw/2,ty,st+.55,.35)}
    const lb=valLabel(L.front,v.shown,x+bw/2,base-h-U*.05,{fill:v.value===mx?FG:FG});wipe(lb,st+.5);
    if(v.label){const t=T(L.front,v.label.toUpperCase(),U*.026,x+bw/2,base+U*.035,{family:'Inter',weight:800,ls:'.08em'});fit(t,gap*.95);wipe(t,st+.3)}})}
function stand(){ // figures standing on their bars, value boxes beside them
  chartTitle(P.title);const vs=P.values,n=vs.length,mx=Math.max(...vs.map(v=>v.value));const pics=P.pics||[];
  const base=TALL?H*.72:H*.86,area=W*(TALL?.86:.62),maxh=TALL?H*.34:H*.42,gap=area/n,bw=gap*.62;
  vs.forEach((v,i)=>{const x=W/2-area/2+gap*(i+.5)-bw/2;const h=Math.max(U*.05,maxh*Math.sqrt(v.value/mx));const st=.2+i*.4;
    const b=L.mid.rect(bw,h).move(x,base-h).fill(i===n-1?'#3E4A55':'#56626C');slide(b,st,0,h);
    const fh=TALL?H*.16:H*.24;const pic=pics[i];let fig;
    if(pic&&pic.img){fig=picture(L.hero,pic,x+bw/2,base-h,fh)}
    else{fig=L.hero.group();const cx=x+bw/2,top=base-h-fh;fig.circle(fh*.18).center(cx,top+fh*.1).fill(INK);
      fig.rect(fh*.22,fh*.42).move(cx-fh*.11,top+fh*.2).radius(fh*.05).fill(INK);fig.rect(fh*.07,fh*.4).move(cx-fh*.1,top+fh*.6).fill(INK);fig.rect(fh*.07,fh*.4).move(cx+fh*.03,top+fh*.6).fill(INK)}
    drop(fig,st+.35,H*.15,0);
    const box=L.front.group();const t=T(box,v.shown,U*.05,0,0,{family:'Anton',weight:400,anchor:'start',fill:'#FFFFFF'});const bb=t.bbox();
    box.rect(bb.width+U*.04,bb.height+U*.02).move(bb.x-U*.02,bb.y-U*.01).fill('#C24A2B').back();
    const lb=T(box,(v.label||'').toUpperCase(),U*.022,0,-bb.height*.85,{family:'Inter',weight:800,anchor:'start',ls:'.1em'});
    const bx=TALL?x+bw*.05:x+bw+U*.03,by=TALL?base-h+U*.1:base-h+U*.05;box.attr({transform:`translate(${bx},${by})`});slide(box,st+.6,W*.03,0)});
  if(P.note){const t=T(L.front,P.note.toUpperCase(),U*.02,W/2,base+U*.035,{family:'Mono',weight:700});wipe(t,1.5)}}
function fan(){ // curved bars around a photo disc, longest first
  const vs=P.values,mx=vs[0].value;const cx=TALL?W/2:W*.4,cy=TALL?H*.42:H*.5,r0=TALL?W*.17:H*.2,rmax=TALL?W*.34:H*.44;
  const a0=-Math.PI*.95,span=Math.PI*1.3,seg=span/vs.length;
  vs.forEach((v,i)=>{const r1=r0+(rmax-r0)*Math.sqrt(v.value/mx);const s0=a0+i*seg+seg*.04,s1=a0+(i+1)*seg-seg*.04;
    const arc=(rr,a)=>[cx+Math.cos(a)*rr,cy+Math.sin(a)*rr];const st=.3+i*.2;
    const pth=L.back.path('').fill(i===0?ACC:(i%2?'#D9532C':'#E7703F'));
    at(st,.6,p=>{const r=r0+(r1-r0)*p;const A=arc(r0,s0),B=arc(r,s0),C=arc(r,s1),D=arc(r0,s1);
      pth.plot(`M${A} L${B} A${r} ${r} 0 0 1 ${C} L${D} A${r0} ${r0} 0 0 0 ${A}`.replace(/,/g,' '))},E.out);
    const mid=(s0+s1)/2;const lx=cx+Math.cos(mid)*(r1+U*.02),ly=cy+Math.sin(mid)*(r1+U*.02);
    const vl=T(L.front,v.shown,U*(i===0?.05:.032),cx+Math.cos(mid)*(r0+(r1-r0)*.62),cy+Math.sin(mid)*(r0+(r1-r0)*.62),{family:'Anton',weight:400,fill:'#FFFFFF'});wipe(vl,st+.5);
    const lt=T(L.front,(v.label||'').toUpperCase(),U*.022,lx,ly,{family:'Inter',weight:800,anchor:Math.cos(mid)>=0?'start':'end',ls:'.08em'});
    lt.attr({transform:`rotate(${(Math.cos(mid)>=0?mid:mid+Math.PI)*180/Math.PI},${lx},${ly})`});wipe(lt,st+.5)});
  const d=L.mid.circle(r0*1.9).center(cx,cy).fill(DARK?'#EEE':'#1C1C1C');popIn(d,cx,cy,.1);
  const pic=(P.pics||[])[0];if(pic&&pic.img){const g=picture(L.hero,pic,cx,cy+r0*1.05,r0*2.1);drop(g,.3,H*.2,0)}
  if(P.title){const g=boxText(L.front,P.title,U*.06,TALL?W/2:W*.04,TALL?H*.8:H*.8,{anchor:TALL?'middle':'start',maxw:TALL?W*.86:W*.4,most:2});g.children().forEach((r,i)=>slide(r,.9+i*.15,-W*.05,0))}}
function trend(){ // the line chart; the picture fills the area under the line; labelled points
  chartTitle(P.title);const pts=P.points,n=pts.length,mx=Math.max(...pts.map(p=>p.value)),mn=0;
  const L0=W*(TALL?.1:.12),R0=W*(TALL?.9:.88),T0=TALL?H*.2:H*.22,B0=TALL?H*.62:H*.8;
  const xy=pts.map((p,i)=>[L0+(R0-L0)*i/(n-1),B0-(B0-T0)*(p.value-mn)/(mx-mn||1)]);
  const area=[[L0,B0],...xy,[R0,B0]];const pic=(P.pics||[])[0];
  const clipEl=draw.clip().add(draw.polygon(area.map(p=>p.join(',')).join(' ')));
  const fill=L.back.group().clipWith(clipEl);
  if(pic&&pic.img){const iw=R0-L0,ih=iw*pic.h/pic.w;fill.image(pic.img).size(Math.max(iw,(B0-T0)*pic.w/pic.h),Math.max(ih,B0-T0)).move(L0,T0).opacity(.95)}
  else fill.rect(R0-L0,B0-T0).move(L0,T0).fill(ACC).opacity(.85);
  const cover=L.back.rect(R0-L0,B0-T0+U*.01).move(L0,T0).fill(PAPER);at(.3,Math.min(2.2,DUR*.55),p=>cover.width(Math.max(.1,(R0-L0)*(1-p))).x(L0+(R0-L0)*p),E.inout);
  L.mid.line(L0,B0,R0,B0).stroke({color:FG,width:U*.004});
  const line=L.mid.polyline(xy.map(p=>p.join(',')).join(' ')).fill('none').stroke({color:FG,width:U*.006,linejoin:'round'});
  const len=line.node.getTotalLength();line.attr({'stroke-dasharray':len,'stroke-dashoffset':len});at(.3,Math.min(2.2,DUR*.55),p=>line.attr({'stroke-dashoffset':len*(1-p)}),E.inout);
  xy.forEach((q,i)=>{const s0=.3+Math.min(2.2,DUR*.55)*i/(n-1);const c=L.front.circle(U*.022).center(q[0],q[1]).fill('#FFFFFF').stroke({color:FG,width:U*.004});popIn(c,q[0],q[1],s0,.3);
    const v=T(L.front,pts[i].shown,U*.034,q[0],q[1]-U*.04,{family:'Anton',weight:400});wipe(v,s0+.1);
    const x=T(L.front,pts[i].x,U*.024,q[0],B0+U*.035,{family:'Mono',weight:700});wipe(x,s0)})}
function slice(){ // the real object with a wedge in the accent colour and a callout
  const pic=(P.pics||[])[0];let h=TALL?H*.42:H*.62;if(pic&&pic.img&&h*pic.w/pic.h>W*(TALL?.84:.6))h=W*(TALL?.84:.6)*pic.h/pic.w;
  const cx=TALL?W/2:W*.42,by=TALL?H*.66:H*.84;
  let g;if(pic)g=picture(L.hero,pic,cx,by,h);drop(g||L.hero.group(),.2,H*.2,0);
  const r=h*.45,cy=by-h*.55;const a0=-Math.PI/2,a1=a0+Math.PI*2*P.pct/100;const wedge=L.front.path('').fill(ACC).opacity(.92).stroke({color:'#FFFFFF',width:U*.004});
  at(.8,.6,p=>{const a=a0+(a1-a0)*p;const large=(a-a0)>Math.PI?1:0;wedge.plot(`M${cx} ${cy} L${cx+Math.cos(a0)*r} ${cy+Math.sin(a0)*r} A${r} ${r} 0 ${large} 1 ${cx+Math.cos(a)*r} ${cy+Math.sin(a)*r} Z`)},E.inout);
  const am=(a0+a1)/2;const x1=cx+Math.cos(am)*r*.7,y1=cy+Math.sin(am)*r*.7;const x2=TALL?W*.82:W*.8,y2=TALL?H*.18:H*.2;
  const ln=L.front.polyline([[x1,y1],[x1,y1]]).fill('none').stroke({color:FG,width:U*.003});
  at(1.3,.5,p=>ln.plot([[x1,y1],[x1+(x2-x1)*p,y1+(y2-y1)*p]]),E.inout);
  const big=T(L.front,P.shown,U*.07,x2,y2-U*.06,{family:'Anton',weight:400,anchor:'end',fill:ACC==='#F2C200'?FG:ACC});wipe(big,1.7);
  if(P.label){const t=T(L.front,P.label.toUpperCase(),U*.028,x2,y2+U*.005,{family:'Inter',weight:800,anchor:'end',ls:'.08em'});wipe(t,1.8)}}

// ---- atlas look: pale sea with engraved hatching, cream land, serif labels, shallow depth of field ----
function atlasSea(){const g=L.paper.group();g.rect(W,H).fill('#B8CDD1');const st=U*.012;
  for(let y=0;y<H;y+=st)g.line(0,y,W,y).stroke({color:'#9DB6BC',width:Math.max(1,U*.0012)});return g}
function depthOfField(grp){ // the edges go soft: a blurred copy under, the sharp map faded out towards the edges
  const soft=grp.clone();L.paper.add(soft);soft.attr({filter:'url(#dof)'});
  const gr=draw.gradient('radial',a=>{a.stop(0,'#fff');a.stop(.55,'#fff');a.stop(1,'#000')});
  const m=draw.mask().add(draw.rect(W,H).fill(gr));grp.maskWith(m)}

// ---- Johnny Harris pen: a shaky red marker line along any path, drawn on as the narration goes ----
function penLine(g,pts,start,dur,color,width){ // pts: [[x,y],...] - a wobbly marker stroke through them
  const out=[];for(let i=0;i<pts.length-1;i++){const [a,b]=[pts[i],pts[i+1]];const n=Math.max(4,Math.round(Math.hypot(b[0]-a[0],b[1]-a[1])/(U*.02)));
    for(let k=0;k<n;k++){const t=k/n;out.push([a[0]+(b[0]-a[0])*t+(rnd()-.5)*U*.004,a[1]+(b[1]-a[1])*t+(rnd()-.5)*U*.004])}}
  out.push(pts[pts.length-1]);
  const pl=g.path('M'+out.map(q=>q.join(' ')).join(' L')).fill('none').stroke({color:color||K.mark||'#D7262B',width:width||U*.008,linecap:'round',linejoin:'round'}).opacity(.92);
  const len=pl.node.getTotalLength();pl.attr({'stroke-dasharray':len,'stroke-dashoffset':len});at(start,dur,p=>pl.attr({'stroke-dashoffset':len*(1-p)}),E.inout);return pl}
function penCircle(g,x,y,r,start){const pts=[];for(let i=0;i<=26;i++){const a=-1.9+i/26*Math.PI*2.2;const j=1+(rnd()-.5)*.12;pts.push([x+Math.cos(a)*r*j,y+Math.sin(a)*r*j*.85])}
  return penLine(g,pts,start,.45)}
function penHatch(g,poly,start){ // marker hatching inside a shape (a country, a region)
  const xs=poly.map(q=>q[0]),ys=poly.map(q=>q[1]);const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const cl=draw.clip().add(draw.polygon(poly.map(q=>q.join(',')).join(' ')));const h=g.group().clipWith(cl);const st=U*.018;let i=0;
  for(let d=-(y1-y0);d<x1-x0;d+=st,i++){h.line(x0+d,y1,x0+d+(y1-y0),y0).stroke({color:K.mark||'#D7262B',width:U*.004,linecap:'round'}).opacity(0)
    .attr({'data-i':i})}
  const ls=h.children();at(start,.9,p=>ls.forEach((l,k)=>l.opacity(k/ls.length<p?.55:0)),E.lin);return h}

// ---- round 5 ----
function route(){ // a paper map; dashed routes draw themselves; the vehicle travels them; pins at each stop
  const [x0,y0,x1,y1]=P.box;const kx=Math.cos((y0+y1)/2*Math.PI/180);
  const ls=P.stops.map(q=>q.lon),as=P.stops.map(q=>q.lat);const sx=Math.max(4,(Math.max(...ls)-Math.min(...ls))*kx),sy=Math.max(3,Math.max(...as)-Math.min(...as));
  const s=Math.min(W*(TALL?.7:.72)/sx,H*(TALL?.4:.56)/sy);const cxl=(Math.max(...ls)+Math.min(...ls))/2,cyl=(Math.max(...as)+Math.min(...as))/2;
  const ox=W/2-cxl*kx*s,oy=H*(TALL?.4:.5)+cyl*s;
  const pr=(lon,lat)=>[ox+lon*kx*s,oy-lat*s];
  if(P.atlas)atlasSea();
  const land=L.back.group();P.shapes.forEach(r=>land.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill(P.atlas?'#EFE3C2':'#9C5B2E')
    .opacity(P.atlas?1:.88).stroke(P.atlas?{color:'#8E7E5C',width:Math.max(1,U*.0015)}:{width:0}));
  if(!P.atlas)land.attr({style:'mix-blend-mode:multiply'});else depthOfField(land);wipe(land,0);
  if(P.title){const g=boxText(L.front,P.title,U*.05,W/2,TALL?H*.07:H*.075,{anchor:'middle',maxw:W*.84,most:1});g.children().forEach(r=>slide(r,.1,0,-H*.04))}
  const pts=P.stops.map(st=>pr(st.lon,st.lat));{const e=pts.length>=3?pts[Math.floor(pts.length/2)]:pts[pts.length-1];FOCUS={x:e[0],y:e[1],rx:U*.07,ry:U*.06}}   // a waypoint is the story
  // compass rose
  const cr=L.mid.group(),cx=U*.13,cy=TALL?H*.62:H*.68,R=U*.07;cr.circle(R*2).center(cx,cy).fill('none').stroke({color:'#3A2A1A',width:U*.002});
  [[0,-1],[1,0],[0,1],[-1,0]].forEach(([a,b],i)=>cr.polygon([[cx+a*R,cy+b*R],[cx+b*R*.18,cy-a*R*.18],[cx-b*R*.18,cy+a*R*.18]].map(p=>p.join(',')).join(' ')).fill(i%2?'#7A5230':'#3A2A1A'));
  T(cr,'N',U*.022,cx,cy-R-U*.02,{family:'Playfair',weight:700,fill:'#3A2A1A'});wipe(cr,.2);
  const legs=[];for(let i=0;i<pts.length-1;i++){const [ax,ay]=pts[i],[bx,by]=pts[i+1];const mx=(ax+bx)/2,my=Math.min(ay,by)-Math.hypot(bx-ax,by-ay)*.22;legs.push([ax,ay,mx,my,bx,by])}
  // a sea leg follows its charted path (smoothed through the midpoints); any other leg is an arc
  const legD=(l,i)=>{const sp=(P.paths||[])[i];if(!sp||sp.length<3)return `M${l[0]} ${l[1]} Q${l[2]} ${l[3]} ${l[4]} ${l[5]}`;
    const q=sp.map(z=>pr(z[0],z[1]));let d=`M${q[0][0].toFixed(1)} ${q[0][1].toFixed(1)}`;
    for(let k=1;k<q.length-1;k++){const mx=(q[k][0]+q[k+1][0])/2,my=(q[k][1]+q[k+1][1])/2;d+=` Q${q[k][0].toFixed(1)} ${q[k][1].toFixed(1)} ${mx.toFixed(1)} ${my.toFixed(1)}`}
    const e=q[q.length-1];return d+` L${e[0].toFixed(1)} ${e[1].toFixed(1)}`};
  const per=Math.max(.6,(DUR-1.2)/Math.max(1,legs.length));
  pts.forEach((p,i)=>{const pin=L.front.group();const k=U*.05/24;const ig=pin.group();for(const nd of P.pin){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    ig.attr({fill:'#2A1A10',stroke:'#F3E9D4','stroke-width':1.2,transform:`translate(${p[0]-12*k},${p[1]-22*k}) scale(${k})`});popIn(pin,p[0],p[1],.3+i*per,.35);
    const lb=tag(L.front,P.stops[i].name,0,0,{size:U*.02});const bb=lb.bbox();const left=p[0]+U*.02+bb.width>W-U*.03;
    lb.attr({transform:`translate(${left?p[0]-U*.02-bb.width-bb.x:p[0]+U*.02-bb.x},${p[1]+U*.02})`});slide(lb,.4+i*per,(left?-1:1)*W*.02,0)});
  legs.forEach((l,i)=>{const path=L.mid.path(legD(l,i)).fill('none').stroke({color:'#2A1A10',width:U*.004,dasharray:`${U*.012} ${U*.01}`});
    if(P.atlas)path.stroke({color:'#0F7C7A',width:U*.006,dasharray:'none'});
    if(P.pen){path.opacity(0);const q=[];const pl=path.node.getTotalLength();for(let k=0;k<=24;k++){const pt=path.node.getPointAtLength(pl*k/24);q.push([pt.x,pt.y])}
      penLine(L.mid,q,.5+i*per,per*.9);penCircle(L.front,l[4],l[5],U*.045,.5+(i+1)*per)}
    const len=path.node.getTotalLength();const mask=draw.mask().add(draw.path(legD(l,i)).fill('none').stroke({color:'#fff',width:U*.02}));
    const mp=mask.children()[0];mp.attr({'stroke-dasharray':len,'stroke-dashoffset':len});path.maskWith(mask);
    const v=L.front.group();const vk=U*.1/24;v.circle(U*.085).center(0,0).fill('#F3E9D4').stroke({color:'#2A1A10',width:U*.003});
    const vg=v.group();for(const nd of P.icon){try{vg.element(nd[0]).attr(nd[1])}catch(e){}}
    vg.attr({fill:'none',stroke:'#2A1A10','stroke-width':1.8,'stroke-linecap':'round','stroke-linejoin':'round',transform:`translate(${-12*vk*.62},${-12*vk*.62}) scale(${vk*.62})`});v.opacity(0);
    const st=.5+i*per;
    at(st,per*.9,p=>{mp.attr({'stroke-dashoffset':len*(1-p)});const q=path.node.getPointAtLength(len*p),q2=path.node.getPointAtLength(Math.min(len,len*p+2));
      const ang=Math.atan2(q2.y-q.y,q2.x-q.x)*180/Math.PI;v.opacity(p>0&&p<.97?1:0);
      v.attr({transform:`translate(${q.x},${q.y}) rotate(${ang+45})`})},E.inout)})}
function compare(){ // one picture split by a yellow line: the left half faded "before", the right half "after"
  const pics=P.pics||[];const a=pics[0],b=pics[1]||pics[0];const h=TALL?H*.6:H*.86;const cx=W/2,by=TALL?H*.72:H*.95;
  if(a){const ga=picture(L.mid,a,cx,by,h);ga.attr({style:'filter:grayscale(1) contrast(.8) brightness(1.15)'})}
  const clip=draw.clip().add(draw.rect(W,H).move(W/2,0));const crect=clip.children()[0];
  if(b){const gb=picture(L.hero,b,cx,by,h);gb.clipWith(clip)}
  const line=L.front.rect(U*.012,H).move(W/2-U*.006,0).fill(ACC);
  at(.3,1.2,p=>{const x=W*(1-p*.5);crect.x(x);line.x(x-U*.006)},E.inout);
  const l=T(L.front,P.left,U*.075,W*.27,TALL?H*.5:H*.62,{family:'Playfair',weight:700,italic:true,fill:'#FFFFFF'});l.attr({style:'paint-order:stroke',stroke:'#111','stroke-width':U*.006});
  const r=T(L.front,P.right,U*.09,W*.72,TALL?H*.5:H*.62,{family:'Playfair',weight:700,italic:true,fill:'#FFFFFF'});r.attr({style:'paint-order:stroke',stroke:'#111','stroke-width':U*.006});
  wipe(l,.4);wipe(r,1.3);if(P.title){const g=boxText(L.front,P.title,U*.05,W/2,TALL?H*.07:H*.075,{anchor:'middle',maxw:W*.84,most:1});g.children().forEach(q=>slide(q,.1,0,-H*.04))}}
function photoline(){ // a timeline of photo cards with yellow tags and a highlighter rule
  const it=P.items,n=it.length;if(P.title){const g=boxText(L.front,P.title,U*.06,W/2,TALL?H*.07:H*.09,{anchor:'middle',maxw:W*.84,most:1});g.children().forEach(q=>slide(q,.1,0,-H*.04))}
  const ly=TALL?H*.6:H*.72;const rule=L.back.rect(0,U*.022).move(W*.05,ly).fill(ACC).opacity(.85);at(.2,.8,p=>rule.width(W*.9*p),E.inout);
  const gap=(TALL?W*.92:W*.86)/n;
  it.forEach((x,i)=>{const cx=W/2+(i-(n-1)/2)*gap,cw=Math.min(gap*.82,U*.42),ch=cw*.72,cy=ly-U*.08-ch;const st=.35+i*.35;const card=L.hero.group();
    card.rect(cw+U*.02,ch+U*.02).move(cx-cw/2-U*.01,cy-U*.01).fill(ACC);
    const pic=x.pic?picOf(x.pic):null;if(pic&&pic.img){const r=Math.min(cw/pic.w,ch/pic.h);card.rect(cw,ch).move(cx-cw/2,cy).fill('#E9E4D8');card.image(pic.img).size(pic.w*r,pic.h*r).move(cx-pic.w*r/2,cy+ch-pic.h*r)}
    else if(pic){card.rect(cw,ch).move(cx-cw/2,cy).fill('#F3EFE6');picture(card,pic,cx,cy+ch*.95,ch*.8)}else card.rect(cw,ch).move(cx-cw/2,cy).fill('#F3EFE6');
    const lab=tag(card,x.what,0,0,{bg:ACC,size:U*(TALL?.02:.022)});const lb=lab.bbox();lab.attr({transform:`translate(${cx-lb.width/2},${cy+ch-lb.height*.2})`});
    card.attr({filter:'url(#shadow)'});drop(card,st,H*.2,0);
    card.polygon([[cx-U*.015,ly-U*.03],[cx+U*.015,ly-U*.03],[cx,ly-U*.005]].map(p=>p.join(',')).join(' ')).fill(INK);
    const yr=T(L.front,x.when,U*.07,cx,ly+U*.09,{family:'Playfair',weight:900});wipe(yr,st+.2)})}
function tv(){ // an old TV set: the picture inside with scan lines and a colour fringe
  const tw=TALL?W*.86:Math.min(W*.56,H*.62/.78),th=tw*.78,tx=W/2-tw/2,ty=TALL?H*.18:H*.1;const set=L.hero.group();
  set.rect(tw,th).move(tx,ty).radius(U*.03).fill('#3B2E25').stroke({color:'#1C1410',width:U*.006});
  const sw=tw*.74,sh=th*.78,sx=tx+tw*.05,sy=ty+th*.11;set.rect(sw,sh).move(sx,sy).radius(U*.05).fill('#0E0E0E');
  for(let k=0;k<3;k++)set.circle(U*.045).center(tx+tw*.9,ty+th*(.25+k*.2)).fill('#8C7A62').stroke({color:'#222',width:U*.003});
  for(let k=0;k<8;k++)set.line(tx+tw*.84,ty+th*(.75+k*.025),tx+tw*.96,ty+th*(.75+k*.025)).stroke({color:'#222',width:U*.003});
  set.rect(tw*.06,U*.06).move(tx+tw*.12,ty+th).fill('#1C1410');set.rect(tw*.06,U*.06).move(tx+tw*.82,ty+th).fill('#1C1410');
  const scr=draw.clip().add(draw.rect(sw,sh).move(sx,sy).radius(U*.05));const inner=L.hero.group().clipWith(scr);
  inner.rect(sw,sh).move(sx,sy).fill('#CFC8B8');const pic=(P.pics||[])[0];
  if(pic&&pic.img){const r=Math.max(sw/pic.w,sh/pic.h)*.95;const iw=pic.w*r,ih=pic.h*r,ix=sx+sw/2-iw/2,iy=sy+sh-ih;
    inner.image(pic.img).size(iw,ih).move(ix-U*.006,iy).attr({filter:'url(#redch)'});inner.image(pic.img).size(iw,ih).move(ix+U*.006,iy).attr({filter:'url(#cyanch)'});
    inner.image(pic.img).size(iw,ih).move(ix,iy).opacity(.6)}
  else if(pic)picture(inner,pic,sx+sw/2,sy+sh*.95,sh*.8);
  for(let y=sy;y<sy+sh;y+=U*.006)inner.rect(sw,U*.0025).move(sx,y).fill('#000').opacity(.18);
  const glare=inner.rect(sw,sh).move(sx,sy).fill('#FFFFFF').opacity(.06);
  set.opacity(0);at(0,.3,p=>set.opacity(p));inner.opacity(0);at(.35,.25,p=>inner.opacity(p>.5?1:p*2*(p*10%1>.5?1:.3)),E.lin);
  if(P.label){const t=tag(L.front,P.label,tx,ty-U*.05,{bg:ACC,size:U*.026});slide(t,.6,-W*.04,0)}
  if(P.caption){const c=boxText(L.front,P.caption,U*.045,W/2,ty+th+U*.12,{anchor:'middle',maxw:W*.86,most:2});c.children().forEach((q,i)=>slide(q,.9+i*.12,0,H*.04))}}

// ---- round 6 ----
function clockFace(g,x,y,r,h,m,start){ // a station clock; its hands sweep to the time
  const c=g.group();c.circle(r*2).center(x,y).fill('#FFFFFF').stroke({color:'#1E5C78',width:r*.14});
  for(let k=0;k<12;k++){const a=k*Math.PI/6;c.line(x+Math.sin(a)*r*.72,y-Math.cos(a)*r*.72,x+Math.sin(a)*r*.86,y-Math.cos(a)*r*.86).stroke({color:'#111',width:r*(k%3?.05:.1)})}
  const hh=c.line(x,y,x,y-r*.5).stroke({color:'#111',width:r*.12,linecap:'round'}),mm=c.line(x,y,x,y-r*.78).stroke({color:'#111',width:r*.08,linecap:'round'});
  c.circle(r*.14).center(x,y).fill('#C62828');
  at(start,.9,p=>{const ha=((h%12)+m/60)*Math.PI/6*p+(1-p)*-Math.PI/2,ma=(m/60)*Math.PI*2*p+(1-p)*Math.PI;
    hh.plot(x,y,x+Math.sin(ha)*r*.5,y-Math.cos(ha)*r*.5);mm.plot(x,y,x+Math.sin(ma)*r*.78,y-Math.cos(ma)*r*.78)},E.inout);
  c.attr({filter:'url(#softshadow)'});return c}
function clockmap(){ // a light map, a clock at every city, joined by lines, the time in a big red box
  const [x0,y0,x1,y1]=P.box;const kx=Math.cos((y0+y1)/2*Math.PI/180);const bw=(x1-x0)*kx,bh=y1-y0;
  const s=Math.min(W*.86/bw,H*(TALL?.5:.74)/bh);const ox=W/2-(x0+x1)/2*kx*s,oy=H*(TALL?.42:.53)+(y0+y1)/2*s;const pr=(lon,lat)=>[ox+lon*kx*s,oy-lat*s];
  L.paper.rect(W,H).fill('#E7EEF1');
  const land=L.back.group();const home=P.cities.length?null:null;
  P.shapes.forEach(sh=>{const home=sh.n===P.home;land.polygon(sh.r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill(home?'#FBFAF6':'#EEECE6')
    .stroke({color:home?'#D04A3A':'#B9B5AC',width:Math.max(1.2,U*(home?.003:.0015))}).back().opacity(1)});
  land.children().filter(c=>c.attr('stroke')==='#D04A3A').forEach(c=>c.front());wipe(land,0);
  const pts=P.cities.map(c=>pr(c.lon,c.lat));FOCUS={x:pts[0][0],y:pts[0][1],rx:U*.06,ry:U*.06};const r=Math.min(U*.045,Math.max(U*.026,U*.3/P.cities.length));
  for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i];const ln=L.mid.line(a[0],a[1],a[0],a[1]).stroke({color:'#4B6E7E',width:U*.004});
    at(.4+i*.18,.4,p=>ln.plot(a[0],a[1],a[0]+(b[0]-a[0])*p,a[1]+(b[1]-a[1])*p),E.inout)}
  pts.forEach((q,i)=>{const st=.25+i*.18;const c=clockFace(L.hero,q[0],q[1],r,P.cities[i].h,P.cities[i].m,st+.2);popIn(c,q[0],q[1],st,.35);
    const t=T(L.front,P.cities[i].name.toUpperCase(),U*.02,q[0],q[1]-r-U*.02,{family:'Inter',weight:800,ls:'.06em'});
    t.attr({style:'paint-order:stroke',stroke:'#E7EEF1','stroke-width':U*.006});wipe(t,st+.2)});
  const tb=L.front.group();const hh=String(P.cities[0].shown).split(':');const big=T(tb,hh[0],U*.09,0,0,{family:'Archivo',weight:400,fill:'#FFFFFF',anchor:'start'});
  const bb=big.bbox();const mn=T(tb,':'+(hh[1]||'00'),U*.045,bb.x+bb.width+U*.012,0,{family:'Archivo',weight:400,fill:'#FFFFFF',anchor:'start'});
  const mb=mn.bbox();tb.rect(mb.x+mb.width-bb.x+U*.04,bb.height+U*.02).move(bb.x-U*.02,bb.y-U*.01).radius(U*.01).fill('#D32F2F').back();
  tb.attr({transform:`translate(${TALL?W*.08:W*.06},${TALL?H*.12:H*.14})`});popIn(tb,W*.1,H*.14,.15);
  if(P.zone){const z=tag(L.front,P.zone,TALL?W*.08:W*.06,TALL?H*.19:H*.25,{bg:'#FFFFFF'});wipe(z,.5)}
  if(P.title){const g=boxText(L.front,P.title,U*.05,TALL?W*.58:W/2,TALL?H*.06:H*.075,{anchor:'middle',maxw:TALL?W*.68:W*.6,most:2});g.children().forEach(q=>slide(q,.1,0,-H*.04))}}
function tornsplit(){ // a big condensed headline, a cut-out on paper, a torn accent panel with halftone dots, a navy corner
  const navy='#1E2B4A';const pat=draw.pattern(U*.014,U*.014,a=>a.circle(U*.006).center(U*.007,U*.007).fill('#000').opacity(.18));
  const ex=TALL?[[W*.0,H*.62],[W,H*.48]]:[[W*.66,0],[W*.54,H]];const pts=[];const n=40;
  for(let i=0;i<=n;i++){const t=i/n;pts.push([ex[0][0]+(ex[1][0]-ex[0][0])*t+(rnd()-.5)*U*.02,ex[0][1]+(ex[1][1]-ex[0][1])*t+(rnd()-.5)*U*.02])}
  const poly=TALL?pts.concat([[W,H],[0,H]]):pts.concat([[W,H],[W,0]]);
  const panel=L.back.group();panel.polygon(poly.map(q=>q.join(',')).join(' ')).fill(ACC);panel.polygon(poly.map(q=>q.join(',')).join(' ')).fill(pat);
  panel.polyline(pts.map(q=>q.join(',')).join(' ')).fill('none').stroke({color:'#F7F2E6',width:U*.012});slide(panel,.05,TALL?0:W*.3,TALL?H*.2:0);
  const corner=L.back.group();const cp=[[0,H*.72],[W*.12,H*.8],[W*.16,H],[0,H]];corner.polygon(cp.map(q=>q.join(',')).join(' ')).fill(navy);if(!TALL)slide(corner,.1,-W*.1,0);else corner.remove();
  const pics=P.pics||[];
  const fitH=(pic,h,maxw)=>{const ar=pic.img?pic.w/pic.h:(pic.draw&&ILLU[pic.draw]?ILLU[pic.draw][0]/ILLU[pic.draw][1]:1);return Math.min(h,maxw/ar)};
  if(pics[0]){const h=fitH(pics[0],TALL?H*.3:H*.56,TALL?W*.8:W*.46);const g=picture(L.hero,pics[0],TALL?W*.42:W*.3,TALL?H*.6:H*.92,h);drop(g,.35,H*.25,-2)}
  if(pics[1]){const h=fitH(pics[1],TALL?H*.3:H*.62,TALL?W*.6:W*.36);const g=picture(L.mid,pics[1],TALL?W*.62:W*.8,TALL?H*.95:H*.86,h);drop(g,.55,H*.25,2)}
  const size=TALL?W*.17:H*.2;const ls=lines(P.headline.toUpperCase(),size,TALL?W*.9:W*.56,'Anton',400,2);
  ls.forEach((l,i)=>{const t=T(L.front,l,size,W*.04,(TALL?H*.1:H*.17)+i*size*1.02,{family:'Anton',weight:400,anchor:'start',fill:navy});slide(t,.2+i*.12,-W*.05,0)});
  const bar=L.front.rect(0,U*.016).move(W*.04,(TALL?H*.1:H*.17)+ls.length*size*1.02-size*.35).fill(ACC==='#D7262B'?navy:'#E0442C');at(.7,.4,p=>bar.width(Math.max(.1,W*.2*p)),E.inout);
  if(P.kicker){const k=T(L.front,P.kicker.toUpperCase(),U*.026,W*.04,(TALL?H*.1:H*.17)+ls.length*size*1.02-size*.05,{family:'Mono',weight:700,anchor:'start',fill:navy});wipe(k,.9)}}
function newscard(){ // a news card on grid paper: red date box, the headline highlighted as it is read, the person beside it
  const g=L.paper.group().opacity(.5);const st=Math.round(U/18);
  for(let x=0;x<W;x+=st)g.line(x,0,x,H).stroke({color:'#8E8672',width:1});for(let y=0;y<H;y+=st)g.line(0,y,W,y).stroke({color:'#8E8672',width:1});
  const pic=(((P.pics||[])[0]||{}).img||((P.pics||[])[0]||{}).draw)?(P.pics||[])[0]:null;const left=W*.06,maxw=pic&&!TALL?W*.44:W*.86;let y=TALL?H*.12:H*.16;
  const db=L.front.group();const dt=T(db,P.date,U*.034,0,0,{family:'Inter',weight:600,anchor:'start',fill:'#FFFFFF'});const bb=dt.bbox();
  db.rect(bb.width+U*.04,bb.height+U*.024).move(bb.x-U*.02,bb.y-U*.012).fill('#D32F2F').back();db.attr({transform:`translate(${left+U*.02},${y})`});slide(db,.1,-W*.05,0);
  y+=U*.1;const hs=U*(TALL?.058:.052);const hl=lines(P.headline,hs,maxw,'Inter',800,3);
  hl.forEach((l,i)=>{const t=T(L.front,l,hs,left,y+i*hs*1.25,{family:'Inter',weight:800,anchor:'start',fill:INK});wipe(t,.3+i*.1);highlight(L.mid,t.bbox(),.8+i*.35,'#F2C94C')});
  y+=hl.length*hs*1.25+U*.03;
  if(P.sub){const ss=U*.03;lines(P.sub,ss,maxw,'Inter',400,3).forEach((l,i)=>{const t=T(L.front,l,ss,left+U*.03,y+i*ss*1.4,{family:'Inter',weight:400,anchor:'start',fill:'#333'});wipe(t,1.2+i*.1)});y+=U*.16}
  if(P.source){const ln=L.front.line(left,y,left,y).stroke({color:INK,width:U*.003});at(1.5,.5,p=>ln.plot(left,y,left+W*.24*p,y),E.inout);
    const t=T(L.front,P.source,U*.045,left+W*.26,y,{family:'Playfair',weight:700,italic:true,anchor:'start',fill:INK});wipe(t,1.8)}
  if(pic){const h=TALL?H*.36:H*.86;const g=picture(L.hero,pic,TALL?W*.6:W*.8,TALL?H*.98:H*1.0,h);drop(g,.4,H*.2,0)}}
function blueprint(){ // a blue card with a white grid; the cut-out; an arrow that points at it; a few bullet lines
  const bg=L.paper.group();bg.rect(W,H).fill('#2F6FD6');const st=Math.round(U/16);
  for(let x=0;x<W;x+=st)bg.line(x,0,x,H).stroke({color:'#FFFFFF',width:1}).opacity(.28);for(let y=0;y<H;y+=st)bg.line(0,y,W,y).stroke({color:'#FFFFFF',width:1}).opacity(.28);
  const pic=(P.pics||[])[0];const cx=TALL?W*.5:W*.66,by=TALL?H*.6:H*.82,h=TALL?H*.3:H*.5;
  if(pic){const g=picture(L.hero,pic,cx,by,h);drop(g,.3,H*.2,0)}
  const tx=TALL?W*.08:W*.07;const t=T(L.front,P.title,U*.065,tx,TALL?H*.12:H*.2,{family:'Inter',weight:800,anchor:'start',fill:'#FFFFFF'});fit(t,TALL?W*.84:W*.42);slide(t,.15,-W*.05,0);
  (P.points||[]).forEach((pt,i)=>{const y=(TALL?H*.68:H*.36)+i*U*.075;const d=L.front.polygon([[0,-U*.012],[U*.018,0],[0,U*.012]].map(q=>q.join(',')).join(' ')).fill('#FFFFFF');
    d.attr({transform:`translate(${tx},${y})`});const l=T(L.front,pt,U*.034,tx+U*.035,y,{family:'Inter',weight:600,anchor:'start',fill:'#FFFFFF'});fit(l,TALL?W*.8:W*.38);wipe(d,.7+i*.2);wipe(l,.75+i*.2)});
  const ax=TALL?W*.7:W*.5,ay=TALL?H*.24:H*.2,bx=cx+(TALL?0:-h*.15),bY=by-h*.95;
  const arrow=L.front.path(`M${ax} ${ay} Q${ax+U*.2} ${ay-U*.08} ${bx} ${bY}`).fill('none').stroke({color:'#FFFFFF',width:U*.006,linecap:'round'});
  const len=arrow.node.getTotalLength();arrow.attr({'stroke-dasharray':len,'stroke-dashoffset':len});at(.9,.6,p=>arrow.attr({'stroke-dashoffset':len*(1-p)}),E.inout);
  const q=arrow.node.getPointAtLength(len),q2=arrow.node.getPointAtLength(len-2);const ang=Math.atan2(q.y-q2.y,q.x-q2.x)*180/Math.PI;
  const head=L.front.polygon([[0,0],[-U*.03,-U*.018],[-U*.03,U*.018]].map(z=>z.join(',')).join(' ')).fill('#FFFFFF');head.attr({transform:`translate(${q.x},${q.y}) rotate(${ang})`});wipe(head,1.45)}

// ---- brand marks: the platform the line names, as its own app tile (official mark, own colour) ----
function logoTile(g,m,cx,cy,size){const t=g.group();const r=size*.22;
  t.rect(size,size).move(cx-size/2,cy-size/2).radius(r).fill(m.hex).stroke({color:'#FFFFFF',width:size*.04});
  const k=size*.6/24;t.path(m.d).fill('#FFFFFF').attr({transform:`translate(${cx-12*k},${cy-12*k}) scale(${k})`});
  t.attr({filter:'url(#shadow)'});return t}
function logoLayer(){const ms=(P.logos||[]).filter(m=>!m.used);if(!ms.length)return;
  const f=FOCUS||{x:W*.7,y:H*.35,rx:U*.1,ry:U*.1};const size=U*(TALL?.13:.12);
  ms.forEach((m,i)=>{let x=f.x+f.rx*.85+i*size*1.15,y=f.y-f.ry*.85;x=Math.min(W-size*.7,Math.max(size*.7,x));y=Math.max(size*.8,y);
    const t=logoTile(L.front,m,x,y,size);t.attr({transform:`rotate(${i%2?6:-6},${x},${y})`});popIn(t,x,y,.55+i*.15,.4)})}

// ---- the papercut companion: a public figure named in the line, cut out of a real photo, beside the infographic ----
function companion(){const c=P.comp;if(!c)return;
  // the infographic steps aside: it shrinks a little and moves away from the side the person stands on
  const h=TALL?H*.38:H*.96, y=H;
  const ar=c.img?c.w/c.h:(window.ILLU&&ILLU.person?ILLU.person[0]/ILLU.person[1]:.4);const ww=Math.min(h*ar,TALL?W*.56:W*.3);const hh=ww/ar;
  const x=TALL?W*.3:ww/2+U*.02;
  if(TALL){const k=.72;CONTENT.attr({transform:`translate(${W*(1-k)/2},${H*.01}) scale(${k})`})}
  else{const right=ww+U*.05,k=Math.min(.8,(W-right)/W);CONTENT.attr({transform:`translate(${right},${H*(1-k)/2}) scale(${k})`})}
  const disc=L.side.circle(hh*.62).center(x,y-hh*.62).fill(ACC);popIn(disc,x,y-hh*.62,.15,.45);
  const g=picture(L.side,c,x,y,hh,{offset:true});slide(g,.25,-W*.25,0);
  const nm=(c.name||'').replace(/^person:/i,'');
  if(nm){const t=tag(L.side,nm,0,0,{bg:ACC,size:U*.024});const bb=t.bbox();
    t.attr({transform:`translate(${Math.max(U*.03,x-bb.width/2)},${TALL?H*.6:y-hh-U*.06})`});slide(t,.6,-W*.1,0)}
  if(c.credit)mono(L.side,'Photo: '+c.credit,U*.03,H-U*.025,{size:U*.013,fill:DARK?'#BBBBBB':'#555555'})}

// ---- the Johnny Harris layer: a red marker circle scribbled round the subject, an arrow, a handwritten note ----
let FOCUS=null;   // {x,y,rx,ry} set by a scene: what the marker circles
function markerLayer(){if(!P.marker)return;const f=FOCUS||{x:W/2,y:H*.45,rx:U*.2,ry:U*.16};const red=K.mark||'#D7262B',g=L.front.group();
  const n=48,pts=[];const turns=1.12,a0=-Math.PI*.6;
  for(let i=0;i<=n;i++){const a=a0+i/n*Math.PI*2*turns;const j=1+(rnd()-.5)*.06+(i/n)*.06;pts.push([f.x+Math.cos(a)*f.rx*j,f.y+Math.sin(a)*f.ry*j])}
  const ring=g.path('M'+pts.map(q=>q.join(' ')).join(' L')).fill('none').stroke({color:red,width:U*.008,linecap:'round',linejoin:'round'}).opacity(.9);
  const len=ring.node.getTotalLength();ring.attr({'stroke-dasharray':len,'stroke-dashoffset':len});at(1.0,.55,p=>ring.attr({'stroke-dashoffset':len*(1-p)}),E.inout);
  // the note goes where there is room: beside the circle, else above or below it
  const roomR=W-(f.x+f.rx),roomL=f.x-f.rx,probe=T(g,P.marker,U*.058,0,0,{family:'Caveat',weight:700});const need=probe.bbox().width+U*.12;probe.remove();
  let right=roomR>=roomL,nx,ny;
  if(Math.max(roomR,roomL)>=Math.min(need,W*.3)){nx=right?f.x+f.rx+U*.08:f.x-f.rx-U*.08;ny=Math.max(H*.2,f.y-f.ry-U*.04)}
  else{right=true;nx=Math.max(U*.06,Math.min(W-need,f.x-need/2));ny=f.y+f.ry+U*.1<(TALL?H*.6:H*.76)?f.y+f.ry+U*.1:Math.max(H*.14,f.y-f.ry-U*.06)}
  const t=T(g,P.marker,U*.058,nx,ny,{family:'Caveat',weight:700,fill:red,anchor:right?'start':'end'});fit(t,right?W-nx-U*.04:nx-U*.04);
  t.attr({transform:`rotate(${right?-4:4},${nx},${ny})`});const tb=t.bbox();
  const sx=right?tb.x-U*.01:tb.x+tb.width+U*.01,sy=ny+U*.02,ex=f.x+(right?1:-1)*f.rx*.72,ey=f.y-f.ry*.72;
  const cx=(sx+ex)/2,cy=Math.min(sy,ey)-U*.06;const arr=g.path(`M${sx} ${sy} Q${cx} ${cy} ${ex} ${ey}`).fill('none').stroke({color:red,width:U*.006,linecap:'round'});
  const al=arr.node.getTotalLength();arr.attr({'stroke-dasharray':al,'stroke-dashoffset':al});at(1.5,.4,p=>arr.attr({'stroke-dashoffset':al*(1-p)}),E.inout);
  const q=arr.node.getPointAtLength(al),q2=arr.node.getPointAtLength(al-3);const ang=Math.atan2(q.y-q2.y,q.x-q2.x);
  const hd=g.path(`M${q.x-Math.cos(ang-0.5)*U*.03} ${q.y-Math.sin(ang-0.5)*U*.03} L${q.x} ${q.y} L${q.x-Math.cos(ang+0.5)*U*.03} ${q.y-Math.sin(ang+0.5)*U*.03}`)
    .fill('none').stroke({color:red,width:U*.006,linecap:'round',linejoin:'round'});wipe(hd,1.88);t.opacity(0);at(1.6,.3,p=>t.opacity(p),E.lin)}

// ---- the film: gate weave, dust and scratches on every frame, a warm light leak on openers (Johnny Harris) ----
function filmLayer(){if(K.film===false)return()=>{};const g=L.grain.group();let last=-1;
  const leak=['opener','tornsplit','number','headline'].includes(P.type)||P.leak;
  let lk=null;if(leak){const gr=draw.gradient('radial',a=>{a.stop(0,'#FFB347',.9);a.stop(.45,'#FF6A2A',.45);a.stop(1,'#FF6A2A',0)});
    lk=L.grain.circle(U*1.3).center(-U*.2,H*.2).fill(gr).attr({style:'mix-blend-mode:screen'}).opacity(0)}
  return function(t,tq){
    if(lk){const p=Math.min(1,t/1.6);lk.center(-U*.2+W*.5*p,H*(.2+.1*p)).opacity(Math.max(0,Math.sin(Math.PI*Math.min(1,t/1.8)))*.55)}
    const tick=Math.round(tq*12);if(tick===last)return;last=tick;g.clear();
    let sd=tick*9301+P.seed;const r=()=>{sd=(sd*16807)%2147483647;return (sd-1)/2147483646};
    const n=3+Math.floor(r()*5);for(let i=0;i<n;i++){g.circle(U*(.002+r()*.004)).center(r()*W,r()*H).fill(r()<.5?'#000':'#FFF').opacity(.25+r()*.3)}
    if(r()<.22){const x=r()*W;g.line(x,0,x+(r()-.5)*U*.02,H).stroke({color:'#000',width:Math.max(1,U*.0012)}).opacity(.12)}
    if(r()<.06){const x=r()*W,y=r()*H;g.path(`M${x} ${y} q ${U*.02} ${U*.01} ${U*.04} ${-U*.005} t ${U*.03} ${U*.02}`).fill('none').stroke({color:'#000',width:1.2}).opacity(.35)}
    const dx=(r()-.5)*U*.0024,dy=(r()-.5)*U*.0024;draw.node.style.transform=`translate(${dx}px,${dy}px) scale(1.004)`}}   // gate weave

// ---- standing of the evidence, particles, an inset picture ----
function badgeLayer(){if(!P.badge||!P.badge[0])return;const [txt,col]=P.badge;const g=L.front.group().addClass('keep');
  const x=U*.05,y=TALL?H*.135:H*.9;const t=T(g,txt,U*.024,x+U*.03,y,{family:'Mono',weight:700,anchor:'start',fill:col,ls:'.14em'});const bb=t.bbox();
  g.rect(bb.width+U*.05,bb.height+U*.022).move(x-U*.004,y-bb.height/2-U*.011).fill('#FBF8F0').stroke({color:col,width:U*.004}).back();
  g.circle(U*.012).center(x+U*.012,y).fill(col);g.attr({transform:`rotate(-2,${x},${y})`});popIn(g,x,y,.9,.3)}
function insetLayer(){const pic=P.insetpic;if(!pic)return;const w=TALL?W*.3:W*.17,h=w*1.18,x=W-w-U*.05,y=TALL?H*.6:H-h-U*.11;   // low in the corner: clear of headlinesconst g=L.front.group().addClass('keep');
  g.rect(w+U*.016,h+U*.016).move(x-U*.008+U*.008,y-U*.008+U*.008).fill(INK);g.rect(w+U*.016,h+U*.016).move(x-U*.008,y-U*.008).fill('#FBF8F0').stroke({color:INK,width:U*.003});
  const cl=draw.clip();cl.rect(w,h).move(x,y);const inner=g.group();inner.rect(w,h).move(x,y).fill(ACC);
  const ph=pic.img?Math.max(h,w*pic.h/pic.w):h*.92;picture(inner,pic,x+w/2,y+h+(pic.img?ph-h:0)*.0,ph,{});inner.clipWith(cl);
  const nm=String(pic.name||'').replace(/^person:/i,'');if(nm){const t=T(g,nm.toUpperCase(),U*.017,x+w/2,y+h+U*.03,{family:'Mono',weight:700});fit(t,w*1.2)}
  g.attr({transform:`rotate(2.5,${x+w/2},${y+h/2})`});drop(g,.7,H*.2,3)}
function voiceLayer(){const lv=P.levels;if(!lv||!lv.length)return()=>{};const n=TALL?22:28,bw=U*.012,gap=U*.008,tot=n*(bw+gap);
  const x0=P.type==='interview'&&!TALL?W*.52:(W-tot)/2,y=P.type==='interview'?(TALL?H*.93:H*.86):H*.95,g=L.front.group();
  const bars=[];for(let i=0;i<n;i++)bars.push(g.rect(bw,2).move(x0+i*(bw+gap),y-1).fill(i%5===2?(K.mark||'#D7262B'):FG).radius(bw*.3));
  let sd=(P.seed||1)+11;const ph=bars.map(()=>{sd=(sd*16807)%2147483647;return sd/2147483647*6.28});
  return function(t){const f=t*12,i=Math.min(lv.length-1,Math.floor(f)),a=lv[i]||0,b=lv[Math.min(lv.length-1,i+1)]||0,v=a+(b-a)*(f-i);
    bars.forEach((r,k)=>{const h=Math.max(2,U*.07*v*(.35+.65*Math.abs(Math.sin(ph[k]+t*7+k*.6))));r.height(h).y(y-h/2)})}}
function fxLayer(){const kind=P.fx;if(!kind)return()=>{};const g=draw.group();g.insertBefore(L.grain);const n={dust:46,embers:40,snow:70,rain:90,confetti:60,sparks:36}[kind];
  let sd=(P.seed||1)*7+3;const r=()=>{sd=(sd*16807)%2147483647;return (sd-1)/2147483646};const ps=[];
  const cols={dust:['#FFFFFF'],embers:['#FF8A2A','#FFC14D','#E0442C'],snow:['#FFFFFF'],rain:['#DDE8EE'],confetti:[ACC,'#E0442C','#2D6BDB','#14968A','#FFFFFF'],sparks:['#FFE08A','#FFFFFF']}[kind];
  for(let i=0;i<n;i++){const o={x:r()*W,y:r()*H,v:.3+r()*.7,ph:r()*6.28,sz:U*(.003+r()*.006),c:cols[Math.floor(r()*cols.length)]};
    o.el=kind==='rain'?g.line(0,0,-U*.006,U*.03).stroke({color:o.c,width:Math.max(1,U*.0016)}).opacity(.5)
      :kind==='confetti'?g.rect(o.sz*2.4,o.sz*1.2).fill(o.c):g.circle(o.sz*2).fill(o.c).opacity(kind==='dust'?.35:.85);ps.push(o)}
  return function(t){ps.forEach(o=>{let x,y,a=1;
    if(kind==='dust'){x=o.x+Math.sin(t*.4*o.v+o.ph)*U*.03;y=o.y+Math.cos(t*.3*o.v+o.ph)*U*.02;a=.2+.25*Math.sin(t*o.v+o.ph)**2}
    else if(kind==='embers'||kind==='sparks'){const life=((t*o.v*.35+o.ph/6.28)%1);x=o.x+Math.sin(t*1.3+o.ph)*U*.03;y=H*1.05-life*H*1.15;a=1-life}
    else{const sp=kind==='rain'?2.2:kind==='snow'?.16:.3;y=((o.y+t*H*sp*o.v)%(H*1.1))-H*.05;x=o.x+(kind==='rain'?-(y/H)*U*.12:Math.sin(t*1.1*o.v+o.ph)*U*.03)}
    if(kind==='rain')o.el.attr({transform:`translate(${x},${y})`});else if(kind==='confetti')o.el.attr({transform:`translate(${x},${y}) rotate(${(t*200*o.v+o.ph*57)%360})`});
    else o.el.center(x,y).opacity(Math.max(0,a))})}}

// ---- layouts: the same scene, composed another way ----
function keepReadable(root){ // under a mirror, every word, photo and logo flips back in place so nothing reads backwards
  const els=[];root.node.querySelectorAll('text,image,.keep').forEach(n=>{if(!n.parentNode.closest||!n.parentNode.closest('.keep'))els.push(n)});
  els.forEach(n=>{let b;try{b=n.getBBox()}catch(e){return}let cx=b.x+b.width/2,cy=b.y+b.height/2;
    const m=n.transform&&n.transform.baseVal.consolidate();if(m){const q=m.matrix;cx=q.a*(b.x+b.width/2)+q.c*cy+q.e}
    const w=document.createElementNS('http://www.w3.org/2000/svg','g');w.setAttribute('transform',`matrix(-1,0,0,1,${2*cx},0)`);
    n.parentNode.insertBefore(w,n);w.appendChild(n)})}
function layout(){const lay=K.lay||'base';
  if(lay==='mirror'){STAGE.attr({transform:`matrix(-1,0,0,1,${W},0)`});keepReadable(STAGE);if(FOCUS)FOCUS.x=W-FOCUS.x}
  else if(lay==='card'){ // the graphic printed on a card, lying a little crooked on a desk
    const k=.84,rot=((P.seed||0)%2?1.4:-1.4),tr=`rotate(${rot},${W/2},${H/2}) translate(${W*(1-k)/2},${H*(1-k)/2}) scale(${k})`;
    const card=CONTENT.group();card.back();card.rect(W,H).fill(PAPER).attr({filter:'url(#shadow)'});
    L.paper.children().forEach(c=>card.add(c));card.attr({transform:tr});STAGE.attr({transform:tr});
    L.paper.rect(W,H).fill(K.desk||'#3B2F25');const d=L.paper.group().opacity(.18);const st=Math.round(U/30);
    for(let y=0;y<H;y+=st)d.line(0,y,W,y+(((y/st)%3)-1)*U*.004).stroke({color:'#000',width:Math.max(1,U*.002)});   // wood grain
    if(FOCUS){FOCUS=Object.assign({},FOCUS,{x:W*(1-k)/2+FOCUS.x*k,y:H*(1-k)/2+FOCUS.y*k,rx:FOCUS.rx*k,ry:FOCUS.ry*k})}}}

// ---- data and structure diagrams ----
function mix(a,b,t){const h=c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));const x=h(a),y=h(b);
  return '#'+x.map((v,i)=>Math.round(v+(y[i]-v)*t).toString(16).padStart(2,'0')).join('')}
function count(t,to,start,dur,fmt){at(start,dur,p=>{t.node.textContent=fmt(to*p)},E.out)}   // a number that counts up
function pyramid(){ // population pyramid: bands from the youngest at the bottom, two sides growing from the middle
  chartTitle(P.title);const bs=P.bands,n=bs.length,mx=Math.max(...bs.map(b=>Math.max(b.l,b.r)));
  const top=TALL?H*.2:H*.24,bot=TALL?H*.8:H*.9,rh=(bot-top)/n,bar=rh*.76,cx=W/2,gc=U*.075,mw=W*(TALL?.3:.3);
  const dec=v=>(String(v).split('.')[1]||'').length;
  [[P.left,cx-gc-mw*.5,'#3E4A55'],[P.right,cx+gc+mw*.5,ACC]].forEach(([s,x,c],i)=>{const t=T(L.front,s.toUpperCase(),U*.03,x,top-U*.04,{family:'Inter',weight:800,ls:'.14em'});
    const sw=L.front.rect(U*.02,U*.02).center(x-t.bbox().width/2-U*.025,top-U*.04).fill(c);wipe(t,.15+i*.1);wipe(sw,.15+i*.1)});
  bs.forEach((b,i)=>{const y=bot-(i+1)*rh+(rh-bar)/2,lw=mw*b.l/mx,rw=mw*b.r/mx,st=.3+i*.11;
    const lr=L.hero.rect(.1,bar).move(cx-gc,y).fill('#3E4A55');at(st,.7,p=>{lr.width(Math.max(.1,lw*p)).x(cx-gc-lw*p)});
    const rr=L.hero.rect(.1,bar).move(cx+gc,y).fill(ACC);at(st,.7,p=>rr.width(Math.max(.1,rw*p)));
    wipe(T(L.front,b.label,Math.min(U*.028,bar*.6),cx,y+bar/2,{family:'Mono',weight:700}),st);
    const fs=Math.min(U*.026,bar*.58);
    const lv=T(L.front,'0',fs,cx-gc-lw-U*.012,y+bar/2,{family:'Inter',weight:800,anchor:'end'});lv.opacity(0);at(st+.1,.2,p=>lv.opacity(p));count(lv,b.l,st,.8,v=>v.toFixed(dec(b.ls)));
    const rv=T(L.front,'0',fs,cx+gc+rw+U*.012,y+bar/2,{family:'Inter',weight:800,anchor:'start'});rv.opacity(0);at(st+.1,.2,p=>rv.opacity(p));count(rv,b.r,st,.8,v=>v.toFixed(dec(b.rs)));
    if(Math.max(b.l,b.r)===mx)FOCUS={x:b.l>=b.r?cx-gc-lw/2:cx+gc+rw/2,y:y+bar/2,rx:Math.max(lw,rw)*.62,ry:bar*.95}});
  L.mid.line(cx-gc,top-U*.01,cx-gc,bot).stroke({color:FG,width:U*.002}).opacity(.5);L.mid.line(cx+gc,top-U*.01,cx+gc,bot).stroke({color:FG,width:U*.002}).opacity(.5);
  if(P.unit)wipe(mono(L.front,P.unit.toUpperCase(),W-U*.05,bot+U*.03,{anchor:'end',weight:700}),.6)}
function nodeBox(g,name,note,x,y,bw,bh,fill){const b=g.group();
  b.rect(bw,bh).move(x-bw/2+U*.008,y-bh/2+U*.008).fill(INK);b.rect(bw,bh).move(x-bw/2,y-bh/2).fill(fill||'#FBF8F0').stroke({color:INK,width:U*.004});
  const fs=Math.min(U*.03,bh*.3),ls=lines(name,fs,bw*.88,'Inter',800,2),oy=note?-fs*.45:0;
  ls.forEach((l,k)=>fit(T(b,l,fs,x,y+oy+(k-(ls.length-1)/2)*fs*1.15,{family:'Inter',weight:800,fill:INK}),bw*.9));
  if(note)fit(T(b,note,fs*.68,x,y+bh/2-fs*.62,{family:'Mono',weight:700,fill:'#3A3A3A'}),bw*.9);return b}
function arrowHead(g,x,y,ang,start){const s=U*.022;const h=g.path(`M${x-Math.cos(ang-.5)*s} ${y-Math.sin(ang-.5)*s} L${x} ${y} L${x-Math.cos(ang+.5)*s} ${y-Math.sin(ang+.5)*s}`)
  .fill('none').stroke({color:K.mark||'#D7262B',width:U*.007,linecap:'round',linejoin:'round'});wipe(h,start);return h}
function flow(){ // boxes joined by arrows drawn one after another; a token travels the chain
  chartTitle(P.title);const ns=P.nodes,n=ns.length,hz=!TALL;
  const span=hz?W*.9:H*.66,step=span/n,bw=hz?Math.min(step*.74,U*.42):W*.62,bh=hz?U*.19:Math.min(step*.62,U*.15);
  const pos=ns.map((_,i)=>hz?[W*.05+step*(i+.5),H*.54+(i%2?U*.05:-U*.05)]:[W/2,H*.19+step*(i+.5)]);
  ns.forEach((nd,i)=>{const [x,y]=pos[i],st=.25+i*.6,last=i===n-1;const g=nodeBox(L.hero,nd.name,nd.note,x,y,bw,bh,last?ACC:null);popIn(g,x,y,st,.35);
    if(!last){const [x2,y2]=pos[i+1];const a=hz?[x+bw/2+U*.012,y]:[x,y+bh/2+U*.012],b=hz?[x2-bw/2-U*.018,y2]:[x2,y2-bh/2-U*.018];
      penLine(L.mid,[a,b],st+.3,.3);arrowHead(L.mid,b[0],b[1],Math.atan2(b[1]-a[1],b[0]-a[0]),st+.56)}
    const num=T(L.front,String(i+1),U*.024,x-bw/2+U*.004,y-bh/2-U*.004,{family:'Mono',weight:700,fill:'#FFFFFF'});const bb=num.bbox();
    const tag=L.front.circle(U*.04).center(bb.cx,bb.cy).fill(INK);num.front();popIn(tag,bb.cx,bb.cy,st+.1,.25);wipe(num,st+.15)});
  const dot=L.front.circle(U*.028).fill(K.mark||'#D7262B').stroke({color:'#FFFFFF',width:U*.005}).opacity(0);
  at(.5,(n-1)*.6,p=>{const f=p*(n-1),i=Math.min(n-2,Math.floor(f)),t=f-i;dot.opacity(p>0&&p<1?1:0).center(pos[i][0]+(pos[i+1][0]-pos[i][0])*t,pos[i][1]+(pos[i+1][1]-pos[i][1])*t-(hz?bh*.62:0)+(hz?0:0))},E.lin);
  const e=pos[n-1];FOCUS={x:e[0],y:e[1],rx:bw*.62,ry:bh*.8}}
function linkmap(){ // the subject in the middle, the others round it; every link is drawn and named
  chartTitle(P.title);const ns=P.nodes,n=ns.length,cx=W/2,cy=TALL?H*.5:H*.56,rx=W*(TALL?.34:.34),ry=H*(TALL?.28:.3);
  const cr=U*.12;const cg=L.hero.group();cg.circle(cr*2).center(cx+U*.008,cy+U*.008).fill(INK);cg.circle(cr*2).center(cx,cy).fill(ACC).stroke({color:INK,width:U*.005});
  const cl=lines(P.centre,U*.032,cr*1.7,'Inter',800,3);cl.forEach((l,k)=>fit(T(cg,l.toUpperCase(),U*.032,cx,cy+(k-(cl.length-1)/2)*U*.038,{family:'Inter',weight:800,fill:INK}),cr*1.8));
  popIn(cg,cx,cy,.15,.4);FOCUS={x:cx,y:cy,rx:cr*1.25,ry:cr*1.25};
  ns.forEach((nd,i)=>{const a=-Math.PI/2+(i+.5)/n*Math.PI*2,x=cx+Math.cos(a)*rx,y=cy+Math.sin(a)*ry,st=.55+i*.38;
    const bw=Math.min(U*.3,W*.24),bh=U*.085;const g=nodeBox(L.hero,nd.name,'',x,y,bw,bh,'#FBF8F0');
    const d=Math.hypot(x-cx,y-cy),ux=(x-cx)/d,uy=(y-cy)/d;const p1=[cx+ux*cr*1.06,cy+uy*cr*1.06],p2=[x-ux*Math.min(bw*.5,bh*.9/Math.max(.2,Math.abs(uy))),y-uy*bh*.62];
    penLine(L.mid,[p1,p2],st,.35,INK,U*.005);popIn(g,x,y,st+.3,.3);
    if(nd.how){const mx2=(p1[0]+p2[0])/2,my=(p1[1]+p2[1])/2;const t=T(L.front,nd.how,U*.021,mx2,my,{family:'Mono',weight:700,fill:'#FFFFFF'});const bb=t.bbox();
      const tg=L.front.rect(bb.width+U*.02,bb.height+U*.008).center(mx2,my).fill(K.mark||'#D7262B');t.front();wipe(tg,st+.4);wipe(t,st+.45)}})}
function orgchart(){ // who reports to whom: the top box, the row under it, connectors drawn down
  chartTitle(P.title);const ks=P.kids,n=ks.length,deep=ks.some(k=>k.kids.length);
  const ty=TALL?H*.24:H*.28,ky=TALL?H*.46:(deep?H*.52:H*.62),area=W*.92,gap=area/n,bw=Math.min(gap*.86,U*.36),bh=U*.11;
  const top=nodeBox(L.hero,P.top,'',W/2,ty,Math.min(W*.4,U*.5),bh*1.15,ACC);popIn(top,W/2,ty,.15,.4);FOCUS={x:W/2,y:ty,rx:Math.min(W*.24,U*.3),ry:bh};
  const busY=(ty+ky)/2;penLine(L.mid,[[W/2,ty+bh*.6],[W/2,busY]],.5,.2,INK,U*.005);
  penLine(L.mid,[[W*.04+gap*.5,busY],[W*.04+gap*(n-.5),busY]],.65,.35,INK,U*.005);
  ks.forEach((k,i)=>{const x=W*.04+gap*(i+.5),st=.95+i*.2;penLine(L.mid,[[x,busY],[x,ky-bh*.55]],st,.2,INK,U*.005);
    const g=nodeBox(L.hero,k.name,'',x,ky,bw,bh,null);popIn(g,x,ky,st+.15,.3);
    k.kids.forEach((c,j)=>{const cy2=ky+bh*1.25+j*bh*.95,s2=st+.5+j*.15;penLine(L.mid,[[x-bw*.4,ky+bh*.5],[x-bw*.4,cy2],[x-bw*.3,cy2]],s2,.2,INK,U*.004);
      const t=T(L.front,c,Math.min(U*.024,bh*.3),x-bw*.27,cy2,{family:'Inter',weight:600,anchor:'start'});fit(t,bw*.8);wipe(t,s2+.15)})})}
function heatmap(){ // countries shaded by their number, labelled, with a scale
  chartTitle(P.title);const [x0,y0,x1,y1]=P.box,kx=Math.cos((y0+y1)/2*Math.PI/180);
  const s=Math.min(W*.84/Math.max(8,(x1-x0)*kx),H*(TALL?.5:.62)/Math.max(6,y1-y0)),cxl=(x0+x1)/2,cyl=(y0+y1)/2,ox=W/2-cxl*kx*s,oy=H*(TALL?.46:.53)+cyl*s;
  const pr=(lon,lat)=>[ox+lon*kx*s,oy-lat*s];atlasSea();
  const bg=L.back.group();P.others.forEach(r=>bg.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill('#EFE3C2').stroke({color:'#8E7E5C',width:Math.max(1,U*.0012)}));
  const vs=P.items.map(i=>i.value),mn=Math.min(...vs),mx=Math.max(...vs),lo=mix('#EFE3C2',ACC,.22);
  const order=P.items.slice().sort((a,b)=>a.value-b.value);const placed=[];
  order.forEach((it,i)=>{const f=mx>mn?(it.value-mn)/(mx-mn):1,col=mix(lo,ACC,f),st=.4+i*.3;const g=L.hero.group();
    it.rings.forEach(r=>g.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill('#EFE3C2').stroke({color:INK,width:Math.max(1,U*.002)}));
    at(st,.6,p=>g.children().forEach(c=>c.fill(mix('#EFE3C2',col,p))),E.inout);
    const [px,py]=pr(it.at[0],it.at[1]);const lab=L.front.group();const t=T(lab,it.shown,U*.034,px,py,{family:'Anton',weight:400,fill:'#FFFFFF'});
    const nm=T(lab,it.label.toUpperCase(),U*.017,px,py+U*.034,{family:'Inter',weight:800,fill:'#FFFFFF',ls:'.1em'});const bb=lab.bbox();
    lab.rect(bb.width+U*.024,bb.height+U*.014).center(bb.cx,bb.cy).fill(INK).back();
    // neighbours' labels step apart (down, up, further down...) and keep a leader line to their place
    const bw=bb.width+U*.03,bh=bb.height+U*.02;let dy=0;const hit=d=>placed.some(q=>Math.abs(q[0]-px)<(q[2]+bw)/2&&Math.abs(q[1]-(py+d))<(q[3]+bh)/2);
    for(const d of [0,1,-1,2,-2,3,-3]){if(!hit(d*bh)){dy=d*bh;break}}
    placed.push([px,py+dy,bw,bh]);if(dy){L.front.line(px,py,px,py+dy).stroke({color:INK,width:U*.003}).back();L.front.circle(U*.01).center(px,py).fill(INK);lab.attr({transform:`translate(0,${dy})`})}
    popIn(lab,px,py+dy,st+.35,.3);
    if(it.value===mx)FOCUS={x:px,y:py+dy,rx:Math.max(U*.09,bb.width*.8),ry:Math.max(U*.07,bb.height)}});
  const lw=W*(TALL?.5:.26),lx=W-lw-U*.09,ly=H-U*.13,gr=draw.gradient('linear',a=>{a.stop(0,lo);a.stop(1,ACC)});
  const lg=L.front.group();lg.rect(lw,U*.02).move(lx,ly).fill(gr).stroke({color:INK,width:U*.002});
  T(lg,String(mn),U*.02,lx,ly+U*.04,{family:'Mono',weight:700,anchor:'start'});T(lg,String(mx),U*.02,lx+lw,ly+U*.04,{family:'Mono',weight:700,anchor:'end'});
  if(P.unit)T(lg,P.unit.toUpperCase(),U*.018,lx+lw/2,ly-U*.022,{family:'Inter',weight:800,ls:'.12em'});wipe(lg,.3);
  if(P.mapcredit)wipe(mono(L.front,P.mapcredit.toUpperCase(),U*.04,H-U*.03,{size:U*.013}),.8)}

// ---- evidence, tables, interviews, end card ----
function greek(g,x,y,w,rows,rh,col){for(let i=0;i<rows;i++){const ww=w*(i===rows-1?.55:.86+((i*37)%13)/100);g.rect(ww,rh*.34).move(x,y+i*rh).fill(col||'#B9B4A8')}}
function courtdoc(){ // a page of the judgment: court, case, the paragraph in its own words, highlighted as it is read
  const pw=TALL?W*.86:Math.min(W*.56,H*1.0),ph=TALL?H*.74:H*.9,px=TALL?(W-pw)/2:W*.07,py=TALL?H*.16:H*.07;const page=L.hero.group();
  page.rect(pw,ph).move(px+U*.012,py+U*.012).fill('#00000030');page.rect(pw,ph).move(px,py).fill('#FBF9F3').stroke({color:'#B9B4A8',width:U*.002});
  const cx=px+pw/2,m=pw*.09;fit(T(page,P.court.toUpperCase(),U*.026,cx,py+ph*.07,{family:'Playfair',weight:700,fill:'#1A1A1A',ls:'.12em'}),pw*.82);
  page.line(px+m,py+ph*.105,px+pw-m,py+ph*.105).stroke({color:'#1A1A1A',width:U*.002});page.line(px+m,py+ph*.112,px+pw-m,py+ph*.112).stroke({color:'#1A1A1A',width:U*.001});
  const cs=lines(P.case,U*.022,pw*.8,'Playfair',700,2);cs.forEach((l,i)=>T(page,l,U*.022,cx,py+ph*.155+i*U*.028,{family:'Playfair',weight:700,fill:'#1A1A1A',italic:true}));
  let y=py+ph*.25;const rh=U*.03;greek(page,px+m,y,pw-2*m,3,rh);y+=rh*3.6;
  const qs=TALL?U*.036:U*.03,ql=lines(P.quote,qs,pw-2*m-U*.05,'Playfair',400,7);const q0=y;
  ql.forEach((l,i)=>{const t=T(L.front,l,qs,px+m+U*.05,y+i*qs*1.42,{family:'Playfair',weight:400,anchor:'start',fill:'#111'});const bb=t.bbox();
    highlight(L.front,bb,1.0+i*.42,mix('#FBF9F3',ACC,.55));t.front()});
  const num=(P.ref.match(/(?:para(?:graph)?\.?\s*)(\d+)/i)||[])[1];if(num)T(page,num+'.',qs*.8,px+m,q0,{family:'Playfair',weight:700,anchor:'start',fill:'#1A1A1A'});
  y+=ql.length*qs*1.42+rh*.6;const left=Math.max(0,Math.min(6,Math.floor((py+ph*.9-y)/rh)));greek(page,px+m,y,pw-2*m,left,rh);
  if(P.ref)T(page,P.ref.toUpperCase(),U*.016,px+pw-m,py+ph*.955,{family:'Mono',weight:700,anchor:'end',fill:'#555'});
  page.attr({transform:`rotate(-1.2,${cx},${py+ph/2})`});drop(page,.1,H*.3,-3);
  FOCUS={x:cx,y:q0+ql.length*qs*.7,rx:pw*.5,ry:Math.max(U*.08,ql.length*qs*.9)};
  if(!TALL){const sx=px+pw+W*.05,sw=W-sx-W*.05;const k=T(L.front,'IN THE COURT\'S WORDS',U*.022,sx,H*.3,{family:'Inter',weight:800,anchor:'start',ls:'.16em',fill:K.mark||'#C0262D'});wipe(k,.6);
    const b=boxText(L.front,P.case.split(/ v\.? /i)[0],U*.05,sx,H*.4,{anchor:'start',maxw:sw,most:3});wipe(b,.8)}}
function table(){ // a data table that fills row by row
  chartTitle(P.title);const hd=P.head,rows=P.rows,nc=hd.length,nr=rows.length;const tw=W*(TALL?.9:.74),x0=(W-tw)/2,y0=TALL?H*.2:H*.22;
  const rh=Math.min(U*.09,(H*(TALL?.6:.66))/(nr+1)),fs=Math.min(U*.034,rh*.42);const num=c=>rows.every(r=>/^[\s₹$€£]?[\d.,]+\s*%?\w{0,6}$/.test(r[c]));
  const cw=hd.map((_,c)=>c===0?1.5:1),tot=cw.reduce((a,b)=>a+b,0);let acc=0;const cx=cw.map(w=>{const x=x0+tw*acc/tot;acc+=w;return [x,tw*w/tot]});
  const hb=L.hero.rect(tw,rh).move(x0,y0).fill(INK);wipe(hb,.15);
  hd.forEach((h,c)=>{const r=c>0&&num(c);const t=T(L.front,h.toUpperCase(),fs*.72,r?cx[c][0]+cx[c][1]-rh*.3:cx[c][0]+rh*.3,y0+rh/2,{family:'Inter',weight:800,anchor:r?'end':'start',fill:'#FFFFFF',ls:'.1em'});fit(t,cx[c][1]*.9);wipe(t,.2)});
  rows.forEach((rw,i)=>{const y=y0+rh*(i+1),st=.45+i*.22,hl=P.hl===i+1;const g=L.hero.group();
    g.rect(tw,rh).move(x0,y).fill(hl?ACC:(i%2?'#00000010':'#FFFFFF90'));g.line(x0,y+rh,x0+tw,y+rh).stroke({color:INK,width:U*.0015});
    rw.forEach((v,c)=>{const r=c>0&&num(c);const t=T(g,v,fs,r?cx[c][0]+cx[c][1]-rh*.3:cx[c][0]+rh*.3,y+rh/2,{family:c===0?'Inter':'Mono',weight:c===0||hl?800:700,anchor:r?'end':'start',fill:INK});fit(t,cx[c][1]*.9)});
    slide(g,st,-W*.03,0);if(hl)FOCUS={x:W/2,y:y+rh/2,rx:tw*.53,ry:rh*.8}});
  L.mid.rect(tw,rh*(nr+1)).move(x0,y0).fill('none').stroke({color:INK,width:U*.003});
  if(P.source)wipe(mono(L.front,('SOURCE: '+P.source).toUpperCase(),x0,y0+rh*(nr+1)+U*.035,{weight:700}),.5+nr*.22)}
function interview(){ // the speaker, a lower third with name and role, the pull quote typed beside them
  const pic=(P.pics||[])[0];const px=TALL?W*.5:W*.26,ph=TALL?H*.46:H*.88,base=TALL?H*.56:H;
  const disc=L.back.circle(U*.62).center(px,base-ph*.5).fill(ACC).opacity(.9);popIn(disc,px,base-ph*.5,.05,.5);
  const g=picture(L.hero,pic,px,base,ph);drop(g,.2,H*.2,-2);
  const ly=TALL?H*.565:H*.8,lx=TALL?W*.06:W*.05,lw=TALL?W*.88:W*.42;const lt=L.front.group().addClass('keep');
  lt.rect(lw,U*.075).move(lx,ly).fill(INK);lt.rect(U*.012,U*.075).move(lx,ly).fill(ACC);
  fit(T(lt,P.name.toUpperCase(),U*.036,lx+U*.035,ly+U*.038,{family:'Inter',weight:800,anchor:'start',fill:'#FFFFFF',ls:'.04em'}),lw*.9);
  if(P.role){lt.rect(lw*.86,U*.046).move(lx,ly+U*.075).fill('#FBF8F0').stroke({color:INK,width:U*.002});
    fit(T(lt,P.role,U*.021,lx+U*.035,ly+U*.099,{family:'Mono',weight:700,anchor:'start',fill:INK}),lw*.8)}
  slide(lt,.7,-W*.12,0);
  const qx=TALL?W*.08:W*.52,qy=TALL?H*.68:H*.26,qw=TALL?W*.84:W*.42,qs=TALL?U*.05:U*.052;
  const mk=T(L.front,'“',qs*3.2,qx-U*.008,qy,{family:'Playfair',weight:900,anchor:'start',fill:ACC});wipe(mk,.9);
  const ql=lines(P.quote,qs,qw,'Playfair',700,TALL?5:6);
  ql.forEach((l,i)=>{const t=T(L.front,l,qs,qx,qy+qs*1.1+i*qs*1.28,{family:'Playfair',weight:700,anchor:'start'});typeIn(t,l,1.1+i*.5)});
  FOCUS={x:px,y:base-ph*.62,rx:U*.2,ry:U*.22}}
function endcard(){ // the closing slate: title, one line, the sources
  const bar=L.back.rect(W,H*.012).move(0,H*.5).fill(ACC);at(.1,.6,p=>bar.width(Math.max(.1,W*p)),E.inout);
  const ts=TALL?U*.085:U*.1,tl=lines(P.title,ts,W*.84,'Playfair',900,3);tl.forEach((l,i)=>{const t=T(L.front,l,ts,W/2,H*.45-(tl.length-1-i)*ts*1.1-ts*.6,{family:'Playfair',weight:900});slide(t,.3+i*.15,0,H*.05)});
  if(P.line){const b=boxText(L.front,P.line,U*.04,W/2,H*.57,{anchor:'middle',maxw:W*.8,most:2});wipe(b,1.0)}
  if(P.sources.length){const k=T(L.front,'SOURCES',U*.02,W/2,H*(TALL?.74:.76),{family:'Inter',weight:800,ls:'.3em',fill:K.mark||'#C0262D'});wipe(k,1.3);
    const per=TALL?2:3;P.sources.forEach((s2,i)=>{const row=Math.floor(i/per),col=i%per,n=Math.min(per,P.sources.length-row*per);
      const t=T(L.front,s2,U*.022,W/2+(col-(n-1)/2)*W*(TALL?.42:.28),H*(TALL?.78:.81)+row*U*.04,{family:'Mono',weight:700});fit(t,W*(TALL?.4:.26));wipe(t,1.45+i*.1)})}}
// ---- more charts ----
function axes(L0,R0,T0,B0,mn,mx,unit,ticks){const g=L.mid.group();for(let i=0;i<=ticks;i++){const v=mn+(mx-mn)*i/ticks,y=B0-(B0-T0)*i/ticks;
  g.line(L0,y,R0,y).stroke({color:FG,width:U*.0012}).opacity(i?.25:.9);T(g,(Math.abs(v)>=100?Math.round(v):+v.toFixed(1))+(unit?(unit.length>1?' ':'')+unit:''),U*.019,L0-U*.02,y,{family:'Mono',weight:700,anchor:'end'})}wipe(g,.15);return g}
function revealClip(L0,R0,start,dur){const c=draw.clip();const r=c.rect(.1,H).move(L0-U*.02,0);at(start,dur,p=>r.width(Math.max(.1,(R0-L0+U*.04)*p)),E.inout);return c}
function polltrack(){ // a poll line, its margin of error as a band, the latest reading large
  chartTitle(P.title);const pts=P.points,n=pts.length,vs=pts.map(p=>p.value),m=P.moe||0;let mn=Math.min(...vs)-m,mx=Math.max(...vs)+m;const pad=(mx-mn)*.18||1;mn=Math.max(0,mn-pad);mx+=pad;
  const L0=W*(TALL?.16:.14),R0=W*(TALL?.9:.8),T0=TALL?H*.24:H*.24,B0=TALL?H*.62:H*.8;axes(L0,R0,T0,B0,mn,mx,P.unit,4);
  const X=i=>L0+(R0-L0)*i/(n-1),Y=v=>B0-(B0-T0)*(v-mn)/(mx-mn);const clip=revealClip(L0,R0,.4,1.5);const g=L.hero.group().clipWith(clip);
  if(m){g.polygon(pts.map((p,i)=>[X(i),Y(p.value+m)]).concat(pts.map((p,i)=>[X(i),Y(p.value-m)]).reverse()).map(q=>q.join(',')).join(' ')).fill(ACC).opacity(.28)}
  g.polyline(pts.map((p,i)=>[X(i),Y(p.value)].join(',')).join(' ')).fill('none').stroke({color:ACC,width:U*.009,linejoin:'round',linecap:'round'});
  pts.forEach((p,i)=>{const st=.4+1.5*i/(n-1);const d=L.front.circle(U*.022).center(X(i),Y(p.value)).fill('#FFFFFF').stroke({color:INK,width:U*.005});popIn(d,X(i),Y(p.value),st,.25);
    if(p.label){const t=T(L.front,p.label.toUpperCase(),U*.019,X(i),B0+U*.035,{family:'Inter',weight:800});fit(t,(R0-L0)/n*.95);wipe(t,st)}});
  const last=pts[n-1],lx=X(n-1),ly=Y(last.value);const big=T(L.front,last.shown+(P.unit&&!last.shown.includes(P.unit)?P.unit:''),U*.09,TALL?W/2:R0+U*.03,TALL?H*.72:ly,{family:'Anton',weight:400,anchor:TALL?'middle':'start'});fit(big,TALL?W*.8:W-R0-U*.06);slide(big,2.0,U*.04,0);
  if(m){const t=T(L.front,'±'+m+' margin of error',U*.02,TALL?W/2:R0+U*.03,(TALL?H*.72:ly)+U*.07,{family:'Mono',weight:700,anchor:TALL?'middle':'start'});fit(t,TALL?W*.8:W-R0-U*.05);wipe(t,2.2)}
  FOCUS={x:lx,y:ly,rx:U*.06,ry:U*.06}}
function area(){ // stacked areas filling from the left
  chartTitle(P.title);const xs=P.xs,n=xs.length,ser=P.series;const tot=xs.map((_,i)=>ser.reduce((a,s2)=>a+s2.v[i],0)),mx=Math.max(...tot)*1.08;
  const L0=W*(TALL?.16:.13),R0=W*(TALL?.92:.76),T0=TALL?H*.22:H*.24,B0=TALL?H*.6:H*.8;axes(L0,R0,T0,B0,0,mx,P.unit,4);
  const X=i=>L0+(R0-L0)*i/(n-1),Y=v=>B0-(B0-T0)*v/mx;const clip=revealClip(L0,R0,.4,1.7);const g=L.hero.group().clipWith(clip);
  const cols=[ACC,'#3E4A55',mix(ACC,'#FFFFFF',.5),'#8C8577',mix(ACC,'#000000',.45)];let base=xs.map(()=>0);
  ser.forEach((s2,k)=>{const top=base.map((b,i)=>b+s2.v[i]);g.polygon(top.map((v,i)=>[X(i),Y(v)]).concat(base.map((v,i)=>[X(i),Y(v)]).reverse()).map(q=>q.join(',')).join(' ')).fill(cols[k%cols.length]).stroke({color:PAPER,width:U*.003});
    const ly=TALL?H*.68+k*U*.055:Y((top[n-1]+base[n-1])/2),lx=TALL?W*.2:R0+U*.03;const lg=L.front.group();if(TALL)lg.rect(U*.03,U*.03).move(lx-U*.05,ly-U*.015).fill(cols[k%cols.length]);
    const t=T(lg,s2.name.toUpperCase()+'  '+s2.v[n-1],U*.026,lx,ly,{family:'Inter',weight:800,anchor:'start'});fit(t,TALL?W*.7:W-R0-U*.05);wipe(lg,1.6+k*.2);base=top});
  xs.forEach((x,i)=>{if(n>7&&i%2)return;const t=T(L.front,x,U*.02,X(i),B0+U*.035,{family:'Mono',weight:700});wipe(t,.4+1.7*i/(n-1))})}
function candles(){ // open / high / low / close, one candle at a time
  chartTitle(P.title);const cs=P.candles,n=cs.length;let mn=Math.min(...cs.map(c=>c.l)),mx=Math.max(...cs.map(c=>c.h));const pad=(mx-mn)*.1||1;mn-=pad;mx+=pad;
  const L0=W*(TALL?.18:.14),R0=W*(TALL?.94:.88),T0=TALL?H*.24:H*.24,B0=TALL?H*.66:H*.8;axes(L0,R0,T0,B0,mn,mx,'',4);
  const gap=(R0-L0)/n,bw=Math.min(gap*.6,U*.06),Y=v=>B0-(B0-T0)*(v-mn)/(mx-mn);
  cs.forEach((c,i)=>{const x=L0+gap*(i+.5),up=c.c>=c.o,col=up?ACC:INK,st=.35+i*(1.8/n);const g=L.hero.group();
    g.line(x,Y(c.h),x,Y(c.l)).stroke({color:INK,width:U*.003});const top=Y(Math.max(c.o,c.c)),hh=Math.max(U*.004,Math.abs(Y(c.o)-Y(c.c)));
    g.rect(bw,hh).move(x-bw/2,top).fill(col).stroke({color:INK,width:U*.002});popIn(g,x,Y((c.h+c.l)/2),st,.25);
    if(c.label&&(n<=10||i%2===0)){const t=T(L.front,c.label.toUpperCase(),U*.018,x,B0+U*.035,{family:'Mono',weight:700});fit(t,gap*1.6);wipe(t,st)}});
  const a=cs[0].o,b=cs[n-1].c,ch=(b-a)/a*100;const big=T(L.front,(ch>=0?'+':'')+ch.toFixed(1)+'%',U*.075,R0,T0-U*.02,{family:'Anton',weight:400,anchor:'end',fill:ch>=0?ACT:(K.mark||'#C0262D')});slide(big,2.3,U*.04,0);
  const sub=T(L.front,(P.unit||'')+a+' → '+(P.unit||'')+b,U*.022,R0,T0+U*.035,{family:'Mono',weight:700,anchor:'end'});wipe(sub,2.5);
  FOCUS={x:L0+gap*(n-.5),y:Y((cs[n-1].h+cs[n-1].l)/2),rx:Math.max(bw,U*.05),ry:Math.max(U*.07,(Y(cs[n-1].l)-Y(cs[n-1].h))*.7)}}
// ---- more maps ----
function mapFrame(fw,fh){const [x0,y0,x1,y1]=P.box,kx=Math.cos((y0+y1)/2*Math.PI/180);
  const s=Math.min(W*fw/Math.max(4,(x1-x0)*kx),H*fh/Math.max(3,y1-y0)),ox=W/2-(x0+x1)/2*kx*s,oy=H*(TALL?.46:.53)+(y0+y1)/2*s;
  const pr=(lon,lat)=>[ox+lon*kx*s,oy-lat*s];atlasSea();const land=L.back.group();
  P.shapes.forEach(r=>land.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill('#EFE3C2').stroke({color:'#8E7E5C',width:Math.max(1,U*.0015)}));depthOfField(land);return pr}
function placeTag(g,name,x,y,start,dy){const t=T(g,name.toUpperCase(),U*.02,x,y+(dy||-U*.035),{family:'Inter',weight:800,ls:'.1em',fill:'#FFFFFF'});const bb=t.bbox();
  const r=g.rect(bb.width+U*.018,bb.height+U*.008).center(bb.cx,bb.cy).fill(INK);t.front();wipe(r,start);wipe(t,start);return bb}
function arrows(){ // broad arrows sweeping from place to place: armies, migration, trade
  chartTitle(P.title);const pr=mapFrame(TALL?.8:.7,TALL?.5:.6);const col=K.mark||'#C0262D';const seen={};
  P.arrows.forEach((a,i)=>{const [x1,y1]=pr(a.a.lon,a.a.lat),[x2,y2]=pr(a.b.lon,a.b.lat),st=.5+i*.55;const d=Math.hypot(x2-x1,y2-y1)||1,nx=-(y2-y1)/d,ny=(x2-x1)/d,bend=d*.18*(i%2?-1:1);
    const cxm=(x1+x2)/2+nx*bend,cym=(y1+y2)/2+ny*bend;const N=28,wid=Math.min(U*.03,d*.09);const q=t=>[(1-t)*(1-t)*x1+2*(1-t)*t*cxm+t*t*x2,(1-t)*(1-t)*y1+2*(1-t)*t*cym+t*t*y2];
    const g=L.hero.group();const body=g.path('').fill(col).opacity(.88).stroke({color:'#FFFFFF',width:U*.003,linejoin:'round'});
    at(st,.7,p=>{const te=Math.max(.02,p*.86);const Lp=[],Rp=[];for(let k=0;k<=N;k++){const t=te*k/N,[x,y]=q(t),[xa,ya]=q(Math.min(1,t+.01));const dd=Math.hypot(xa-x,ya-y)||1,px=-(ya-y)/dd,py=(xa-x)/dd,w=wid*(.35+.65*k/N);Lp.push([x+px*w,y+py*w]);Rp.push([x-px*w,y-py*w])}
      const [hx,hy]=q(te),[tx,ty]=q(Math.min(1,te+.14)),[bx,by]=q(te-.01);const dd=Math.hypot(hx-bx,hy-by)||1,px=-(hy-by)/dd,py=(hx-bx)/dd;
      const pts=[...Lp,[hx+px*wid*2.1,hy+py*wid*2.1],[tx,ty],[hx-px*wid*2.1,hy-py*wid*2.1],...Rp.reverse()];body.plot('M'+pts.map(z=>z[0].toFixed(1)+' '+z[1].toFixed(1)).join(' L')+' Z')},E.inout);
    [[a.a,x1,y1,st],[a.b,x2,y2,st+.6]].forEach(([e,x,y,s2])=>{if(seen[e.name])return;seen[e.name]=1;const dt=L.mid.circle(U*.016).center(x,y).fill(INK).stroke({color:'#FFFFFF',width:U*.003});popIn(dt,x,y,s2,.25);placeTag(L.front,e.name,x,y,s2+.1,y<H*.2?U*.035:-U*.035)});
    if(a.label){const [mx2,my]=q(.45);const t=T(L.front,a.label,U*.03,mx2+nx*bend*.5,my+ny*bend*.5-U*.03,{family:'Caveat',weight:700,fill:col});wipe(t,st+.5)}
    if(i===P.arrows.length-1)FOCUS={x:x2,y:y2,rx:U*.08,ry:U*.07}})}
function railmap(){ // a transport network: each line draws through its stations
  chartTitle(P.title);const pr=mapFrame(TALL?.8:.7,TALL?.5:.6);const cols=[K.mark||'#C0262D','#1F4FB8','#1F7A4D','#B8860B','#7A3E8C'];const seen={};let t0=.4;
  P.lines.forEach((ln,i)=>{const col=cols[i%cols.length],pts=ln.stops.map(s2=>pr(s2.lon,s2.lat));const dur=.5+pts.length*.22;
    const cas=L.mid.polyline(pts.map(q=>q.join(',')).join(' ')).fill('none').stroke({color:'#FFFFFF',width:U*.016,linejoin:'round',linecap:'round'});
    const pl=L.mid.polyline(pts.map(q=>q.join(',')).join(' ')).fill('none').stroke({color:col,width:U*.009,linejoin:'round',linecap:'round'});
    [cas,pl].forEach(e=>{const len=e.node.getTotalLength();e.attr({'stroke-dasharray':len,'stroke-dashoffset':len});at(t0,dur,p=>e.attr({'stroke-dashoffset':len*(1-p)}),E.inout)});
    ln.stops.forEach((s2,k)=>{const [x,y]=pts[k],st=t0+dur*k/(pts.length-1);const d=L.hero.circle(U*.022).center(x,y).fill('#FFFFFF').stroke({color:col,width:U*.006});popIn(d,x,y,st,.22);
      if(!seen[s2.name]){seen[s2.name]=1;placeTag(L.front,s2.name,x,y,st+.05,(k+i)%2?U*.036:-U*.036)}});
    if(ln.name){const lg=L.front.group();const y=H*(TALL?.84:.9)-i*U*.045;lg.line(U*.06,y,U*.12,y).stroke({color:col,width:U*.009,linecap:'round'});T(lg,ln.name.toUpperCase(),U*.02,U*.14,y,{family:'Inter',weight:800,anchor:'start',ls:'.08em'});wipe(lg,t0)}
    t0+=dur*.7;const e=pts[pts.length-1];FOCUS={x:e[0],y:e[1],rx:U*.07,ry:U*.06}})}
function resample(r,n){const d=[0];for(let i=1;i<=r.length;i++){const a=r[i-1],b=r[i%r.length];d.push(d[i-1]+Math.hypot(b[0]-a[0],b[1]-a[1]))}const tot=d[r.length],o=[];let j=0;
  for(let k=0;k<n;k++){const t=tot*k/n;while(d[j+1]<t)j++;const a=r[j],b=r[(j+1)%r.length],f=(t-d[j])/Math.max(1e-9,d[j+1]-d[j]);o.push([a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f])}
  let bi=0,bv=1e18;o.forEach((q,i)=>{const v=q[1]*1e3-q[0];if(v<bv){bv=v;bi=i}});return o.slice(bi).concat(o.slice(0,bi))}   // both start at their northernmost point
function sizemap(){ // two countries at one scale: the first morphs into the second, then both sit together
  chartTitle(P.title);const [A,B]=P.items,N=180;const ext=r=>{const xs=r.map(q=>q[0]),ys=r.map(q=>q[1]);return [Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys),(Math.max(...xs)+Math.min(...xs))/2,(Math.max(...ys)+Math.min(...ys))/2]};
  const ea=ext(A.ring),eb=ext(B.ring);const s=Math.min(W*(TALL?.8:.5)/Math.max(ea[0],eb[0]),H*(TALL?.42:.58)/Math.max(ea[1],eb[1]));const cx=W/2,cy=H*(TALL?.45:.52);
  const ra=resample(A.ring.map(q=>[(q[0]-ea[2])*s+cx,(q[1]-ea[3])*s+cy]),N),rb=resample(B.ring.map(q=>[(q[0]-eb[2])*s+cx,(q[1]-eb[3])*s+cy]),N);
  const str=r=>r.map(q=>q[0].toFixed(1)+','+q[1].toFixed(1)).join(' ');const big=A.km2>=B.km2;
  const ghost=L.mid.polygon(str(ra)).fill('none').stroke({color:INK,width:U*.004,dasharray:`${U*.012} ${U*.01}`}).opacity(0);
  const shape=L.hero.polygon(str(ra)).fill(ACC).stroke({color:INK,width:U*.004,linejoin:'round'});popIn(shape,cx,cy,.2,.5);
  at(1.5,.9,p=>{shape.plot(str(ra.map((q,i)=>[q[0]+(rb[i][0]-q[0])*p,q[1]+(rb[i][1]-q[1])*p])));shape.fill(mix(ACC,'#3E4A55',p));ghost.opacity(p)},E.inout);
  const na=T(L.front,A.name.toUpperCase(),U*.034,cx,cy-Math.max(ea[1],eb[1])*s/2-U*.05,{family:'Inter',weight:800,ls:'.1em'});wipe(na,.5);
  at(1.5,.9,p=>{na.node.textContent=(p<.5?A.name:B.name).toUpperCase();na.opacity(Math.abs(p-.5)*2)},E.lin);
  const ratio=Math.max(A.km2,B.km2)/Math.min(A.km2,B.km2),fmt=v=>v>=1e6?(v/1e6).toFixed(2)+' million km²':Math.round(v/1e3)+',000 km²';
  const y=H*(TALL?.76:.88);const t=boxText(L.front,(big?A.name:B.name)+' is '+(ratio>=10?Math.round(ratio):ratio.toFixed(1))+'× bigger',U*.045,W/2,y-U*.05,{anchor:'middle',maxw:W*.86,most:2});wipe(t,2.6);
  const sub=T(L.front,A.name+' '+fmt(A.km2)+'  ·  '+B.name+' '+fmt(B.km2),U*.02,W/2,y+U*.05,{family:'Mono',weight:700});fit(sub,W*.9);wipe(sub,2.8);
  const sc=L.front.group();const km=[100,200,500,1000,2000].find(v=>v*s>U*.12)||2000;sc.line(U*.06,H*.93,U*.06+km*s,H*.93).stroke({color:FG,width:U*.004});T(sc,km+' km',U*.018,U*.06+km*s/2,H*.93-U*.022,{family:'Mono',weight:700});wipe(sc,.6);
  FOCUS={x:cx,y:cy,rx:Math.min(ea[0],eb[0])*s*.55,ry:Math.min(ea[1],eb[1])*s*.55}}

function borders(){ // the borders of a past year; then the map redraws as it is now, the old lines left as a dashed ghost
  chartTitle(P.title);const [x0,y0,x1,y1]=P.box,kx=Math.cos((y0+y1)/2*Math.PI/180);const s=Math.min(W/Math.max(4,(x1-x0)*kx),H*(TALL?.62:.86)/Math.max(3,y1-y0))*1.1;   // the whole region in view
  const ox=W/2-(x0+x1)/2*kx*s,oy=H*(TALL?.48:.54)+(y0+y1)/2*s,pr=(lon,lat)=>[ox+lon*kx*s,oy-lat*s];atlasSea();
  const tones=['#EFE3C2',mix('#EFE3C2',ACC,.16),mix('#EFE3C2','#8E7E5C',.2),mix('#EFE3C2',ACC,.3),mix('#EFE3C2','#3E4A55',.14)];
  const layer=(cs,g,stroke)=>cs.forEach((c,i)=>c.r.forEach(r=>g.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill(tones[(c.n.length+i)%tones.length]).stroke({color:stroke,width:Math.max(1,U*.0022),linejoin:'round'})));
  const labels=(cs,g,start)=>cs.filter(c=>c.label).forEach((c,i)=>{const [x,y]=pr(c.at[0],c.at[1]);if(x<W*.06||x>W*.94||y<H*.16||y>H*.92)return;
    const ls=lines(c.n.toUpperCase(),U*.019,U*.26,'Playfair',700,2);const lg=g.group();ls.forEach((l,k)=>T(lg,l,U*.019,x,y+(k-(ls.length-1)/2)*U*.024,{family:'Playfair',weight:700,fill:'#2A2218',ls:'.12em'}));wipe(lg,start+i*.07)});
  const gThen=L.back.group(),lThen=L.mid.group();layer(P.then,gThen,'#5E4E33');labels(P.then,lThen,.5);wipe(gThen,.05);
  const two=P.now&&P.now.length;const yx=TALL?W/2:W*.1,yy=TALL?H*.14:H*.86;
  const ys=TALL?U*.11:U*.12,yw=ys*2.9,yg=L.front.group();yg.rect(yw,ys*1.15).move(TALL?yx-yw/2:yx-ys*.2,yy-ys*.6).fill(INK);
  const yr=T(yg,String(P.ya),ys,TALL?yx:yx+yw/2-ys*.2,yy,{family:'Anton',weight:400,anchor:'middle',fill:'#FFFFFF'});slide(yg,.2,0,H*.04);
  if(two){const gNow=L.back.group(),lNow=L.mid.group();layer(P.now,gNow,'#5E4E33');labels(P.now,lNow,2.6);gNow.opacity(0);
    const ghost=L.hero.group();P.then.forEach(c=>c.r.slice(0,3).forEach(r=>ghost.polygon(r.map(q=>pr(q[0],q[1]).join(',')).join(' ')).fill('none').stroke({color:K.mark||'#C0262D',width:Math.max(1.2,U*.003),dasharray:`${U*.01} ${U*.008}`,linejoin:'round'})));ghost.opacity(0);
    const end=P.yb||new Date().getFullYear();
    at(1.7,1.1,p=>{gNow.opacity(p);gThen.opacity(1-p);lThen.opacity(Math.max(0,1-p*2.5));ghost.opacity(p*.9);yr.node.textContent=(P.yb===0&&p>=1)?'TODAY':String(Math.round(P.ya+(end-P.ya)*p))},E.inout);
    const key=L.front.group();const kx2=TALL?W*.1:W*.1,ky=TALL?H*.9:H*.94;key.line(kx2,ky,kx2+U*.07,ky).stroke({color:K.mark||'#C0262D',width:U*.004,dasharray:`${U*.01} ${U*.008}`});
    T(key,'BORDERS IN '+P.ya,U*.018,kx2+U*.085,ky,{family:'Mono',weight:700,anchor:'start'});wipe(key,2.4)}
  wipe(mono(L.front,P.mapcredit.toUpperCase(),W-U*.04,H-U*.03,{anchor:'end',size:U*.013}),.8)}

function morph(){ // one outline flows into the next; the name changes with it
  chartTitle(P.title);const N=200,R=Math.min(W*(TALL?.38:.24),H*(TALL?.26:(P.caption?.26:.32))),cx=W/2,cy=H*(TALL?.46:(P.caption?.45:.52));
  const rs=P.shapes.map(sh=>resample(sh.ring.map(q=>[cx+q[0]*R,cy+q[1]*R]),N)),k=rs.length;
  // start every outline at its top point and run it the same way round, so shapes don't turn inside out
  const turn=r=>{let a=0;for(let i=0;i<r.length;i++){const p=r[i],q=r[(i+1)%r.length];a+=p[0]*q[1]-q[0]*p[1]}return a};
  rs.forEach((r,i)=>{if(turn(r)<0){const f=r[0];rs[i]=[f].concat(r.slice(1).reverse())}});
  const str=r=>r.map(q=>q[0].toFixed(1)+','+q[1].toFixed(1)).join(' ');const cols=[ACC,'#3E4A55',K.mark||'#D7262B',mix(ACC,'#000000',.4)];
  const sh=L.hero.polygon(str(rs[0])).fill(cols[0]).stroke({color:INK,width:U*.005,linejoin:'round'});const shadow=L.mid.polygon(str(rs[0])).fill(INK).opacity(.18).attr({transform:`translate(${U*.012},${U*.014})`});
  popIn(sh,cx,cy,.15,.5);wipe(shadow,.5);
  const nm=T(L.front,P.shapes[0].name.toUpperCase(),U*.04,cx,cy+R+U*.08,{family:'Inter',weight:800,ls:'.12em'});wipe(nm,.5);
  // one track for the whole chain (separate tracks would each reset the outline to their own start)
  const each=Math.max(.9,(DUR-1.7)/(k-1)),mv=Math.min(1.0,each*.7);
  at(.9,each*(k-1),q=>{const tt=q*each*(k-1),i=Math.min(k-2,Math.floor(tt/each)),p=E.inout(Math.min(1,(tt-i*each)/mv)),a=rs[i],b=rs[i+1];
    const m=a.map((v,j)=>[v[0]+(b[j][0]-v[0])*p,v[1]+(b[j][1]-v[1])*p]);sh.plot(str(m));shadow.plot(str(m));sh.fill(mix(cols[i%cols.length],cols[(i+1)%cols.length],p));
    nm.node.textContent=(p<.5?P.shapes[i].name:P.shapes[i+1].name).toUpperCase();nm.opacity(Math.max(.001,Math.abs(p-.5)*2))},E.lin);
  if(P.caption){const c=boxText(L.front,P.caption,U*.04,cx,cy+R+U*.16,{anchor:'middle',maxw:W*.8,most:2});wipe(c,1.1)}
  FOCUS={x:cx,y:cy,rx:R*1.05,ry:R*1.05}}

const SCENES={morph,borders,courtdoc,table,interview,endcard,polltrack,area,candles,arrows,railmap,sizemap,pyramid,flowchart:flow,linkmap,orgchart,heatmap,hero,desk,evidence,opener,reveal,headline,pinmap,number,seats,stack,stand,fan,trend,slice,route,compare,photoline,tv,
  clockmap,tornsplit,newscard,blueprint};
async function boot(){
  try{await Promise.all(Array.from(document.fonts).map(f=>f.load()))}catch(e){}
  const imgs=[];(P.pics||[]).forEach(p=>{if(p.img)imgs.push(new Promise(r=>{const i=new Image();i.onload=i.onerror=r;i.src=p.img}))});
  await Promise.all(imgs);
  (SCENES[P.type]||hero)();logoLayer();markerLayer();badgeLayer();insetLayer();layout();companion();
  const film=filmLayer(),fx=fxLayer(),voice=voiceLayer();
  window.frame=function(t){camera(t);const tq=Math.floor(t*12+1e-6)/12;   // the hand-made 12 fps stutter
    for(const k of tracks){const p=Math.max(0,Math.min(1,(tq-k.start)/k.dur));k.fn(k.e(p))}film(t,tq);fx(t);voice(t)};
  window.frame(0);window.READY=true}
boot();
</script></body></html>"""


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           lib: Path | None = None, model: Path | None = None, fetch: bool = True, fps: int | None = None,
           tone: str = "cream", sources: list[tuple[str, str]] | None = None, props: bool = False,
           layout: str = "", levels: list[float] | None = None) -> Path:
    """Draws one Vox scene into `out` (H.264). `layout` is one of LAYOUT_SETS[kind] (default: picked from the spec)."""
    from . import motion
    if not motion.enabled():
        raise MediaError("vox scenes need the animation engine (Chromium + Playwright)")
    plan = plan_for(kind, spec)
    if plan is None:
        raise MediaError(f"vox: nothing to draw from {spec!r}")
    _pictures(plan, lib, model, fetch, sources, era_in(theme))
    # asset check before the render: a photo much smaller than the size it is shown at will look soft
    soft = [f"{p.get('name')}: {p['w']}x{p['h']} px shown about {int(height * (0.4 if height > width else 0.6))} px tall"
            for p in plan.get("pics", []) if p.get("img") and p.get("h", 9999) < height * (0.4 if height > width else 0.6) * 0.55]
    if soft:
        out.with_suffix(".qa.json").write_text(json.dumps({"low_resolution": soft}), encoding="utf-8")
    if levels and wants_voice(kind, spec):
        plan["levels"] = [float(v) for v in levels][:1200]     # the voice, 12 readings a second: the bars move with it
    if plan["type"] == "hero" and not plan["pics"]:
        raise MediaError("vox: no picture or icon for the subject")
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(1.5, float(seconds))
    look = look_of(theme)
    tone = plan.get("tone") or ("grid" if plan["type"] in ("desk", "reveal", "newscard") else tone)
    paper_hex = look["paper"] if tone == "cream" else PAPERS.get(tone, PAPERS["cream"])
    bg, grain = paper(paper_hex, width, height, work)
    kit = {"acc": accent_of(theme), "accText": readable(accent_of(theme), paper_hex), "acc2": "#E0442C" if accent_of(theme) != ACCENTS["red"] else "#F2C200", "ink": INK, "paper": paper_hex, "dark": tone == "dark", "tone": tone, "props": props,
           "bg": bg.as_uri(), "grain": grain.as_uri(),
           "mark": look["mark"], "cam": _seed("cam", spec, theme) % 4, "exit": plan.get("exit") or EXITS[_seed("exit", spec, theme) % len(EXITS)], "lay": layout if layout in LAYOUT_SETS.get(kind, ()) else
           layout_for(kind, 0, _seed("layout", spec, theme)), "desk": DESKS[_seed("desk", theme) % len(DESKS)], "dir": 1 if _seed("dir", spec) % 2 else -1, "fam": {"Playfair": look["head"], "Anton": look["big"], "Caveat": look["hand"]}}
    js = _PAGE
    for old, new in (("#B8CDD1", look["sea"]), ("#EFE3C2", look["land"]), ("#8E7E5C", look["edge"])):
        js = js.replace(old, new)
    page = (js.replace("%SVGJS%", motion.VENDOR.read_text(encoding="utf-8")).replace("%FONTS%", _font_css())
            .replace("%ILLU%", (Path(__file__).parent / "vendor" / "illustrations.js").read_text(encoding="utf-8"))
            .replace("%PAPER%", paper_hex).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{seconds:.3f}")
            .replace("%KIT%", json.dumps(kit)))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"vox_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    return motion.capture(html, width, height, seconds, fps, out)
