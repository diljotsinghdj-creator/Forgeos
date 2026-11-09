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
         "clockmap", "tornsplit", "newscard", "blueprint")


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
    "field":     {"paper": "#E9EDE4", "head": "DMSerif", "big": "Anton", "hand": "Marker", "mark": "#C2410C",
                  "sea": "#B5D0C8", "land": "#EEE9D6", "edge": "#6E7B66", "accent": "teal"},
}


def look_of(theme: str) -> dict:
    """'editorial~2@red/kraft' -> the kraft look (default: archive, the original look)."""
    name = ((theme or "").split("/") + ["", ""])[1]
    return LOOKS.get(name.strip().lower(), LOOKS["archive"])


def choose_look(text: str, era: int | None = None) -> str:
    """The look for a video: an old story (before 1950) gets sepia; otherwise one picked from the script itself, so
    the same script always gets the same look and two scripts rarely share one."""
    if era is not None and era < 1950:
        return "sepia"
    names = [k for k in LOOKS if k != "sepia"]
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
    return {"type": "number", "number": parts[0][:8], "subjects": _split_list(parts[1])[:1] if len(parts) > 1 else [],
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
            xs = [x for r in f["rings"] for x, _ in r]
            ys = [y for r in f["rings"] for _, y in r]
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
    pad_x = max(8.0, (max(lons) - min(lons)) * 0.35)
    pad_y = max(6.0, (max(lats) - min(lats)) * 0.45)
    box = [min(lons) - pad_x, min(lats) - pad_y, max(lons) + pad_x, max(lats) + pad_y]
    # the visible box keeps the frame's shape; countries that touch it are drawn
    w = maps._world()
    shapes = []
    for c in w["countries"]:
        for r in c["r"]:
            if any(box[0] - 60 <= x <= box[2] + 60 and box[1] - 40 <= y <= box[3] + 40 for x, y in r[:: max(1, len(r) // 30)]):
                shapes.append([[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // 160)]])
    from .scene_anim import icon_nodes, find_icon
    atlas = any(re.fullmatch(r"(style\s*[:=]\s*)?atlas", x.strip(), re.I) for x in parts[1:])
    pen = any(re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I) for x in parts[1:])
    parts = [x for x in parts if not re.fullmatch(r"(style\s*[:=]\s*)?pen", x.strip(), re.I)]
    return {"type": "route", "pen": pen, "stops": stops, "box": box, "shapes": shapes[:400], "title": parts[1] if len(parts) > 1 and not
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


PARSERS = {"hero": parse_hero, "desk": parse_desk, "pinboard": parse_evidence, "opener": parse_opener,
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
    plan = fn(spec)
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
const FG=DARK?'#F3EFE6':INK;
const draw=SVG().addTo('body').size(W,H);
const tracks=[], cam=[];
const E={out:t=>1-Math.pow(1-t,3), back:t=>{const c=1.6,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)},
  inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2, snap:t=>1-Math.pow(1-t,5), lin:t=>t};
function at(start,dur,fn,e){tracks.push({start,dur,fn,e:e||E.out})}
let seed=P.seed||1;function rnd(){seed=(seed*16807)%2147483647;return (seed-1)/2147483646}
// ---- layers (back to front) and the camera ----
const L={};L.paper=draw.group();const CONTENT=draw.group();
['back','mid','hero','front'].forEach(k=>L[k]=CONTENT.group());L.side=draw.group();L.grain=draw.group();
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
function camera(t){const p=E.inout(Math.min(1,t/Math.max(DUR,.1)));const m=K.cam||0;
  const fx=(m===3&&FOCUS)?Math.max(W*.3,Math.min(W*.7,FOCUS.x)):W/2,fy=(m===3&&FOCUS)?Math.max(H*.3,Math.min(H*.65,FOCUS.y)):H*.46;
  for(const k in DEPTH){const d=DEPTH[k]*(m===3?1.3:1);const q=m===1?1-p:p;const z=1+d*q;
    const dx=m===2?(p-.5)*d*W*1.6*(K.dir||1):0;
    L[k].attr({transform:`translate(${fx*(1-z)+dx},${fy*(1-z)}) scale(${m===2?1+d*.4:z})`})}}
// ---- the style kit ----
function T(g,s,size,x,y,o){o=o||{};const t=g.text(String(s)).font({family:(K.fam||{})[o.family]||o.family||'Inter',size:size,weight:o.weight||600,
  anchor:o.anchor||'middle',style:o.italic?'italic':'normal'}).fill(o.fill||FG).attr({x:x,y:y,'dominant-baseline':'central'});
  if(o.ls)t.attr({'letter-spacing':o.ls});return t}
function fit(t,maxw){const w=t.bbox().width;if(w>maxw)t.font({size:t.font('size')*maxw/w});return t}
function lines(s,size,maxw,family,weight,most){const words=String(s).split(/\s+/).filter(Boolean),out=[];let cur='';
  const pr=draw.text('').font({family:(K.fam||{})[family]||family,size:size,weight:weight});
  for(const w of words){const tr=cur?cur+' '+w:w;pr.text(tr);if(cur&&pr.bbox().width>maxw){out.push(cur);cur=w}else cur=tr}
  if(cur)out.push(cur);pr.remove();return out.slice(0,most||3)}
function boxText(g,s,size,x,y,o){ // black box(es), white serif type - one box per line, like a cut label
  o=o||{};const ls=lines(String(s).toUpperCase(),size,o.maxw||W*.4,o.family||'Playfair',900,o.most||3);const grp=g.group();const pad=size*.28;
  let yy=y;const anchor=o.anchor||'start';
  ls.forEach((ln,i)=>{const row=grp.group();const t=T(row,ln,size,0,0,{family:o.family||'Playfair',weight:900,anchor:'start',fill:o.ink||'#FFFFFF',ls:'0.02em'});
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
    const ig=grp.group();for(const nd of ((pic&&pic.o)||[])){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    const k=r*1.15/24;ig.attr({fill:'none',stroke:INK,'stroke-width':1.6,'stroke-linecap':'round','stroke-linejoin':'round',
      transform:`translate(${x-12*k},${y-h/2-12*k}) scale(${k})`});grp.data('w',r*2)}
  return grp}
// ---- motion kit (the stutter: these run on 12 fps steps) ----
function drop(el,start,dist,rot){el.opacity(0);const base=el.attr('transform')||'';
  at(start,.55,p=>{el.opacity(p>0?1:0);el.attr({transform:`translate(0,${-(dist||H*.25)*(1-p)}) rotate(${(rot||0)*(1-p)},${W/2},${H/2}) ${base}`})},E.back)}
function slide(el,start,dx,dy){el.opacity(0);const base=el.attr('transform')||'';
  at(start,.45,p=>{el.opacity(Math.min(1,p*2));el.attr({transform:`translate(${(dx||0)*(1-p)},${(dy||0)*(1-p)}) ${base}`})},E.snap)}
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
  o=o||{};const parts=String(s).split(/(\*[^*]+\*)/).filter(Boolean);const grp=g.group();let cx=0;const marks=[];
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
  ls.forEach((ln,i)=>{const row=L.front.group();let cx=0;ln.split(' ').forEach(w=>{const t=T(row,w,size,cx,0,{family:'Playfair',weight:900,anchor:'start',fill:hi.has(w)?'#FFFFFF':INK});cx+=t.bbox().width+size*.22});
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
  if(pic&&!TALL&&(K.v||0)%2===1)return numberSide(pic);const big=T(L.back,P.number,TALL?W*.42:H*(pic?.5:.56),W/2,pic?(TALL?H*.22:H*.3):(TALL?H*.34:H*.4),{family:'Anton',weight:400,fill:ACC});fit(big,W*.92);
  slide(big,.05,0,H*.06);
  if(pic){const h=TALL?H*.36:H*.56;const g=picture(L.hero,pic,W/2,TALL?H*.64:H*.86,h);drop(g,.35,H*.25,-2)}
  if(P.caption){const c=pic?fit(T(L.front,P.caption,U*.04,W/2,TALL?H*.7:H*.92,{family:'Inter',weight:800,fill:'#C0262D'}),W*.9)
      :boxText(L.front,P.caption,U*.055,W/2,TALL?H*.5:H*.7,{anchor:'middle',maxw:W*.86,most:2});wipe(c,.9)}
  if(P.kicker){const k=T(L.front,P.kicker.toUpperCase(),U*.024,W/2,TALL?H*.08:H*.08,{family:'Inter',weight:800,fill:'#C0262D',ls:'0.45em'});wipe(k,.2)}}

function numberSide(pic){ // second layout: the number and its words on the left, the subject standing on the right
  // the number across the top, the subject lower right, the words lower left: nothing overlaps the figure
  const big=T(L.back,P.number,H*.34,W*.05,H*.24,{family:'Anton',weight:400,fill:ACC,anchor:'start'});fit(big,W*.9);slide(big,.05,-W*.05,0);
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
  const per=Math.max(.6,(DUR-1.2)/Math.max(1,legs.length));
  pts.forEach((p,i)=>{const pin=L.front.group();const k=U*.05/24;const ig=pin.group();for(const nd of P.pin){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    ig.attr({fill:'#2A1A10',stroke:'#F3E9D4','stroke-width':1.2,transform:`translate(${p[0]-12*k},${p[1]-22*k}) scale(${k})`});popIn(pin,p[0],p[1],.3+i*per,.35);
    const lb=tag(L.front,P.stops[i].name,0,0,{size:U*.02});const bb=lb.bbox();const left=p[0]+U*.02+bb.width>W-U*.03;
    lb.attr({transform:`translate(${left?p[0]-U*.02-bb.width-bb.x:p[0]+U*.02-bb.x},${p[1]+U*.02})`});slide(lb,.4+i*per,(left?-1:1)*W*.02,0)});
  legs.forEach((l,i)=>{const path=L.mid.path(`M${l[0]} ${l[1]} Q${l[2]} ${l[3]} ${l[4]} ${l[5]}`).fill('none').stroke({color:'#2A1A10',width:U*.004,dasharray:`${U*.012} ${U*.01}`});
    if(P.atlas)path.stroke({color:'#0F7C7A',width:U*.006,dasharray:'none'});
    if(P.pen){path.opacity(0);const q=[];const pl=path.node.getTotalLength();for(let k=0;k<=24;k++){const pt=path.node.getPointAtLength(pl*k/24);q.push([pt.x,pt.y])}
      penLine(L.mid,q,.5+i*per,per*.9);penCircle(L.front,l[4],l[5],U*.045,.5+(i+1)*per)}
    const len=path.node.getTotalLength();const mask=draw.mask().add(draw.path(`M${l[0]} ${l[1]} Q${l[2]} ${l[3]} ${l[4]} ${l[5]}`).fill('none').stroke({color:'#fff',width:U*.02}));
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

const SCENES={hero,desk,evidence,opener,reveal,headline,pinmap,number,seats,stack,stand,fan,trend,slice,route,compare,photoline,tv,
  clockmap,tornsplit,newscard,blueprint};
async function boot(){
  try{await Promise.all(Array.from(document.fonts).map(f=>f.load()))}catch(e){}
  const imgs=[];(P.pics||[]).forEach(p=>{if(p.img)imgs.push(new Promise(r=>{const i=new Image();i.onload=i.onerror=r;i.src=p.img}))});
  await Promise.all(imgs);
  (SCENES[P.type]||hero)();companion();logoLayer();markerLayer();
  const film=filmLayer();
  window.frame=function(t){camera(t);const tq=Math.floor(t*12+1e-6)/12;   // the hand-made 12 fps stutter
    for(const k of tracks){const p=Math.max(0,Math.min(1,(tq-k.start)/k.dur));k.fn(k.e(p))}film(t,tq)};
  window.frame(0);window.READY=true}
boot();
</script></body></html>"""


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           lib: Path | None = None, model: Path | None = None, fetch: bool = True, fps: int | None = None,
           tone: str = "cream", sources: list[tuple[str, str]] | None = None, props: bool = False) -> Path:
    """Draws one Vox scene into `out` (H.264)."""
    from . import motion
    if not motion.enabled():
        raise MediaError("vox scenes need the animation engine (Chromium + Playwright)")
    plan = plan_for(kind, spec)
    if plan is None:
        raise MediaError(f"vox: nothing to draw from {spec!r}")
    _pictures(plan, lib, model, fetch, sources, era_in(theme))
    if plan["type"] == "hero" and not plan["pics"]:
        raise MediaError("vox: no picture or icon for the subject")
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(1.5, float(seconds))
    look = look_of(theme)
    tone = plan.get("tone") or ("grid" if plan["type"] in ("desk", "reveal", "newscard") else tone)
    paper_hex = look["paper"] if tone == "cream" else PAPERS.get(tone, PAPERS["cream"])
    bg, grain = paper(paper_hex, width, height, work)
    kit = {"acc": accent_of(theme), "acc2": "#E0442C" if accent_of(theme) != ACCENTS["red"] else "#F2C200", "ink": INK, "paper": paper_hex, "dark": tone == "dark", "tone": tone, "props": props,
           "bg": bg.as_uri(), "grain": grain.as_uri(),
           "mark": look["mark"], "cam": _seed("cam", spec, theme) % 4, "v": _seed("layout", spec, theme) % 2, "dir": 1 if _seed("dir", spec) % 2 else -1, "fam": {"Playfair": look["head"], "Anton": look["big"], "Caveat": look["hand"]}}
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
