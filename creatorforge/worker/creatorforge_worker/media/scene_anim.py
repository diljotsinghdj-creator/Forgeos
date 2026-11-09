"""Animate anything a script asks for, in the Vox paper style - no AI, so nothing comes out distorted.

    Animate: plane flies from Delhi to Dubai carrying money bags
    Animate: one message spreads to thousands of phones | Going viral
    Animate: trolls attack a journalist
    Animate: police → court → jail | The process
    Animate: cash stack grows | ₹29.7 crore in 30 days

The line is read for its objects (any of ~5,000 free Tabler icons, MIT licence, found by name or tag), its
action (move, grow, shrink, multiply, attack, stack, split, alert, block, compare, cycle, connect, show) and its
places ("from Delhi to Dubai"). Text after "|" is the title. The motion engine draws it (see motion.py)."""
from __future__ import annotations

import functools
import json
import re
from pathlib import Path

ICONS = Path(__file__).parent / "vendor" / "tabler_icons.json"

# words a script uses -> the icon that shows it best (checked before the library's own names and tags)
SYNONYMS = {
    "plane": "plane", "aeroplane": "plane", "airplane": "plane", "flight": "plane-departure", "jet": "plane",
    "car": "car", "taxi": "car", "truck": "truck", "lorry": "truck", "bus": "bus", "train": "train",
    "metro": "train", "bike": "motorbike", "motorcycle": "motorbike", "scooter": "scooter", "boat": "sailboat",
    "ship": "ship", "cargo": "ship", "rocket": "rocket", "helicopter": "helicopter", "ambulance": "ambulance",
    "city": "building-skyscraper", "cities": "building-skyscraper", "building": "building", "office": "building",
    "skyscraper": "building-skyscraper", "parliament": "building-bank", "government": "building-bank",
    "ministry": "building-bank", "bank": "building-bank", "court": "gavel", "judge": "gavel", "law": "scale",
    "justice": "scale", "jail": "lock", "prison": "lock", "police": "shield", "army": "shield",
    "factory": "building-factory", "home": "home", "house": "home", "village": "home", "school": "school",
    "hospital": "building-hospital", "temple": "building-church", "shop": "building-store", "store": "building-store",
    "money": "cash", "cash": "cash", "rupee": "currency-rupee", "rupees": "currency-rupee", "crore": "currency-rupee",
    "lakh": "currency-rupee", "dollar": "currency-dollar", "coin": "coin", "coins": "coins", "moneybag": "moneybag",
    "bag": "moneybag", "salary": "cash", "tax": "receipt-tax", "bill": "receipt", "receipt": "receipt",
    "loan": "cash-banknote", "debt": "cash-banknote", "ads": "ad", "ad": "ad", "advert": "ad",
    "phone": "device-mobile", "phones": "device-mobile", "mobile": "device-mobile", "smartphone": "device-mobile",
    "laptop": "device-laptop", "computer": "device-desktop", "tv": "device-tv", "television": "device-tv",
    "message": "message", "messages": "message", "chat": "messages", "whatsapp": "message-circle",
    "forward": "share", "share": "share", "post": "news", "tweet": "message-2", "video": "video",
    "news": "news", "newspaper": "news", "article": "file-text", "document": "file-text", "file": "file-text",
    "report": "report", "letter": "mail", "email": "mail", "contract": "contract", "book": "book",
    "camera": "camera", "photo": "photo", "microphone": "microphone", "speech": "microphone", "stage": "microphone",
    "person": "user", "man": "user", "woman": "user", "people": "users", "crowd": "users-group",
    "public": "users-group", "voter": "user-check", "voters": "users", "worker": "user", "workers": "users",
    "volunteer": "user-heart", "volunteers": "users", "troll": "mood-angry", "trolls": "mood-angry",
    "journalist": "microphone-2", "reporter": "microphone-2", "leader": "user-star", "politician": "user-star",
    "minister": "user-star", "farmer": "plant", "farmers": "plant", "student": "school", "students": "school",
    "doctor": "stethoscope", "child": "baby-carriage", "family": "users-group",
    "vote": "checkbox", "ballot": "checkbox", "election": "checkbox", "evm": "checkbox", "party": "flag",
    "lie": "mood-sad", "lies": "mood-sad", "truth": "check", "fake": "alert-triangle", "warning": "alert-triangle",
    "fear": "mood-sad", "anger": "mood-angry", "hate": "mood-angry", "love": "heart", "trust": "heart-handshake",
    "idea": "bulb", "brain": "brain", "mind": "brain", "time": "clock", "clock": "clock", "deadline": "clock",
    "calendar": "calendar", "date": "calendar", "world": "world", "globe": "world", "earth": "world",
    "map": "map", "india": "map-pin", "country": "map", "data": "database", "server": "server", "cloud": "cloud",
    "internet": "world-www", "website": "world-www", "app": "apps", "lock": "lock", "key": "key",
    "password": "key", "secret": "eye-off", "eye": "eye", "watch": "eye", "search": "search", "fire": "flame",
    "water": "droplet", "food": "bowl", "oil": "droplet", "gold": "coin", "fuel": "gas-station", "power": "bolt",
    "electricity": "bolt", "chart": "chart-line", "graph": "chart-line", "growth": "trending-up",
    "loss": "trending-down", "profit": "trending-up", "like": "thumb-up", "likes": "thumb-up", "heart": "heart",
    "bomb": "bomb", "gun": "target", "weapon": "target", "target": "target", "hashtag": "hash", "trend": "trending-up",
    "bell": "bell", "notification": "bell", "notifications": "bell", "alarm": "alarm", "robot": "robot",
    "ai": "robot", "virus": "virus", "medicine": "pill", "tree": "tree", "factory_smoke": "building-factory-2",
    # platforms: generic shapes, never their logos
    "google": "search", "twitter": "message-2", "x": "message-2", "facebook": "users", "meta": "users",
    "instagram": "camera", "youtube": "player-play", "telegram": "send", "tiktok": "music", "netflix": "device-tv",
}

# action -> words that ask for it
VERBS = {
    "move": "fly flies flew flying drive drives drove driving sail sails sailing travel travels travelled go goes "
            "went moves moving ship ships shipped send sends sent transfer transfers transferred carry carries "
            "carried deliver delivers delivered smuggle smuggled reach reaches flow flows march marches marched "
            "rally rallies walk walks run runs rush rushes head heads",
    "grow": "grow grows grew growing rise rises rising increase increases soar soars jump jumps boom booms "
            "double doubles inflate surge surges climb climbs balloon",
    "shrink": "shrink shrinks fall falls fell drop drops dropped decrease decreases decline declines crash "
              "crashes collapse collapses sink sinks",
    "multiply": "spread spreads spreading viral multiply multiplies copies copied forwarded explode explodes "
                "replicate reaches_millions",
    "converge": "attack attacks attacked surround surrounds troll trolls trolled swarm swarms mob mobs "
                "target targets gang gangs",
    "stack": "stack stacks stacked pile piles accumulate accumulates hoard hoards collect collects",
    "split": "split splits divide divides divided break breaks separate separates",
    "shake": "ring rings buzz buzzes alert alerts alarm notify notifies shake shakes panic vibrate",
    "block": "block blocks blocked ban bans banned delete deletes deleted remove removes removed stop stops "
             "censor censored withheld cancel cancelled shut shuts close closes closed seal sealed raid raided",
    "compare": "vs versus compare compared against",
    "cycle": "cycle cycles loop loops repeat repeats circle again",
    "connect": "link links linked connect connects connected leads chain then",
}
_VERB_OF = {w: act for act, words in VERBS.items() for w in words.split()}
STOP = set("a an the of to in on at by for with and or from into onto over under as is are was were be been being "
           "it its this that these those their his her our your my one two three many much more most some all any "
           "each every very just only also than then there here who whom which what when where why how not no "
           "out up down off about after before while during per via".split())


# letter/number glyphs, and brand logos (no real logos on screen), are never picked for a word
_LETTERS = re.compile(r"^(?:brand-|(?:circle-|square-|hexagon-|octagon-|pentagon-|triangle-)?(?:dotted-|dashed-)?(?:letter|number|alphabet|"
                      r"circle-number|square-number|roman))", re.I)


@functools.lru_cache(maxsize=1)
def _index() -> dict:
    try:
        return json.loads(ICONS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


@functools.lru_cache(maxsize=4096)
def find_icon(word: str) -> str | None:
    """The best icon name for a word (or a two-word phrase), or None."""
    idx = _index()
    w = word.lower().strip().replace(" ", "-")
    if not w or not idx:
        return None
    cand = [w, w.rstrip("s"), w[:-2] if w.endswith("es") else w, w.replace("-", "")]
    for c in cand:
        if c in SYNONYMS and SYNONYMS[c] in idx:
            return SYNONYMS[c]
    for c in cand:
        if c in idx and not _LETTERS.match(c):
            return c
    base = cand[1]
    # a whole-word part of an icon name ("skyscraper" -> building-skyscraper), shortest name first
    names = sorted((n for n in idx if base in n.split("-") and not _LETTERS.match(n)), key=len)
    if names:
        return names[0]
    tagged = sorted((n for n, m in idx.items() if (base in m.get("t", []) or w in m.get("t", []))
                     and not _LETTERS.match(n)), key=len)
    return tagged[0] if tagged else None


def icon_nodes(name: str) -> list:
    return _index().get(name, {}).get("o", [])


def _words(s: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z'_-]*", s.lower())


def parse(spec: str) -> dict | None:
    """The animation plan for a line: {"type": "scene", "action", "actors": [{name, icon, label, o}], "from",
    "to", "cargo", "title"}; None when nothing in the line can be drawn."""
    head, _, title = (spec or "").partition("|")
    head = head.strip()
    if not head:
        return None
    text = head.lower()
    places = re.search(r"\bfrom\s+([a-z][\w .'-]*?)\s+to\s+([a-z][\w .'-]*?)(?=\s+(?:carrying|with|by|via|in|on)\b|[,.;]|$)",
                       head, re.I)
    origin, dest = (places.group(1).strip(), places.group(2).strip()) if places else ("", "")
    cargo_m = re.search(r"\b(?:carrying|with|full of|loaded with)\s+([a-z][\w -]*?)(?=[,.;]|$)", head, re.I)
    # the action: an explicit arrow chain is a sequence; otherwise the first action word
    if "→" in head or "->" in head:
        action = "connect"
    else:
        action = next((_VERB_OF[w] for w in _words(text) if w in _VERB_OF), "")
        if not action:
            action = "move" if places else "show"
        if action == "move" and not places and not re.search(r"\b(?:to|towards|into|at)\b", text):
            action = "show"
    if action == "connect" and ("→" in head or "->" in head):
        parts = [p.strip() for p in re.split(r"→|->", head) if p.strip()]
        actors = []
        for p in parts[:5]:
            ws = [w for w in _words(p) if w not in STOP]
            icon = next((find_icon(" ".join(ws[i:i + 2])) for i in range(len(ws) - 1)
                         if find_icon(" ".join(ws[i:i + 2]))), None) or next((find_icon(w) for w in ws if find_icon(w)), None)
            actors.append({"name": p, "icon": icon or "point", "label": p})
    else:
        skip = set(_words(origin) + _words(dest))
        cargo_words = set(_words(cargo_m.group(1))) if cargo_m else set()
        found: list[tuple[str, str]] = []
        ws = [w for w in _words(text.replace(cargo_m.group(0).lower(), " ") if cargo_m else text)]
        i = 0
        while i < len(ws):
            w = ws[i]
            if w in STOP or w in skip or (w in _VERB_OF and w not in SYNONYMS):
                i += 1
                continue
            pair = f"{w} {ws[i + 1]}" if i + 1 < len(ws) and ws[i + 1] not in STOP and ws[i + 1] not in _VERB_OF else ""
            icon = find_icon(pair) if pair else None
            if icon:
                found.append((pair, icon))
                i += 2
                continue
            icon = find_icon(w)
            if icon and all(icon != f[1] for f in found):
                found.append((w, icon))
            i += 1
        actors = [{"name": n, "icon": ic, "label": n} for n, ic in found[:4]]
        if cargo_m:
            cw = [w for w in _words(cargo_m.group(1)) if w not in STOP]
            cic = (find_icon(" ".join(cw[:2])) if len(cw) >= 2 else None) or next((find_icon(w) for w in cw if find_icon(w)), None)
            cargo = {"name": cargo_m.group(1).strip(), "icon": cic} if cic else None
        else:
            cargo = None
    if action != "connect" or not ("→" in head or "->" in head):
        pass
    else:
        cargo = None
    if not actors:
        return None
    for a in actors:
        a["o"] = icon_nodes(a["icon"]) or icon_nodes("point")
    plan = {"type": "scene", "action": action, "actors": actors, "from": origin.title(), "to": dest.title(),
            "title": title.strip()}
    if cargo:
        plan["cargo"] = {**cargo, "o": icon_nodes(cargo["icon"])}
    # the place pins use the map-pin icon
    plan["pin"] = icon_nodes("map-pin")
    plan["ban"] = icon_nodes("ban")
    plan["mob"] = icon_nodes("mood-angry")
    return plan
