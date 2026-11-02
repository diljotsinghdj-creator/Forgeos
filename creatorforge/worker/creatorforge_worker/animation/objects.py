"""Any everyday object a script names - a laptop, a ballot paper, a sword, a vaccine, a microphone, a tractor tyre -
drawn in CreatorForge's flat ink look instead of a labelled box.

    compose("a laptop")        -> asset with one flattened picture part, 0.35 m wide, the right way up
    compose("ballot papers")   -> the ballot-box-with-ballot picture
    find("sword")              -> ("⚔", "CROSSED SWORDS")

Where the pictures come from: the open Noto Color Emoji font (SIL Open Font License) already on the machine - about
1,400 objects, foods, tools, devices, plants, animals, buildings and symbols, each with an official Unicode name.
A phrase is matched by a synonym table (English, Hinglish, Hindi) and then by the words of those names, so most nouns
in any script find a picture. People, faces, hands and national flags are never used: people are the stick
characters, and flags of countries are not drawn. The picture is flattened (posterised colours, an ink rim) so it
sits in the same world as the stickmen, and it gets a plausible real-world size next to a 1.75 m person.

Nothing matched -> ValueError, and the caller keeps its honest labelled placeholder."""
from __future__ import annotations

import base64
import io
import re
import unicodedata
from functools import lru_cache

FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
RANGES = [(0x2300, 0x23FF), (0x2600, 0x27BF), (0x1F300, 0x1F5FF), (0x1F680, 0x1F6FF), (0x1F900, 0x1F9FF),
          (0x1FA70, 0x1FAFF)]
NEVER = re.compile(r"FACE|\bPERSON\b|\bMAN\b|\bMEN\b|WOMAN|WOMEN|\bBOY\b|\bGIRL\b|\bBABY\b(?! BOTTLE)|"
                   r"\bHANDS?\b|FINGER|THUMBS|REGIONAL INDICATOR|SKIN TONE|\bKISS\b|COUPLE|FAMILY|SILHOUETTE|"
                   r"OLDER|ADULT|\bCHILD\b|PRINCE|PRINCESS|SANTA|\bELF\b|ZOMBIE|VAMPIRE|MERPERSON|GENIE|TROLL|"
                   r"POLICE OFFICER|GUARDSMAN|DETECTIVE|CONSTRUCTION WORKER|BRIDE|FLEXED|\bEAR\b(?! OF)|NOSE|"
                   r"\bEYES?\b|TONGUE|MOUTH|LIPS|\bFOOT\b|\bLEG\b|ANATOMICAL|SPEAKING HEAD|\bBUSTS?\b|"
                   r"PEDESTRIAN|RUNNER|SWIMMER|SURFER|ROWBOAT|HORSE RACING|SKIER|SNOWBOARDER|GOLFER|WRESTLERS|"
                   r"JUGGLING|CARTWHEEL|WATER POLO|LIFTER|BICYCLIST|DANCER|\bBATH\b|SLEEPING ACCOMMODATION|"
                   r"LOTUS POSITION|CLIMBING|FENCER|BOWING|RAISING|GESTURE|POUTING|FROWNING|NAIL POLISH|SELFIE|MOAI|"
                   r"OGRE|GOBLIN|ALIEN|ROBOT|SKULL|GHOST|CLOWN|PILE OF POO|\bIMP\b")


def _never(name: str) -> bool:
    """People, body parts and national flags are never pictures (a white or chequered flag is fine)."""
    if NEVER.search(name):
        return True
    return bool(re.search(r"\bFLAGS?\b", name)) and not re.search(r"WHITE|CHEQUERED|TRIANGULAR", name)


# what people call things -> words of the Unicode name (first found wins)
SYN = {
    "laptop": "personal computer", "computer": "personal computer", "pc": "personal computer",
    "desktop": "desktop computer", "server": "desktop computer", "monitor": "desktop computer",
    "phone": "mobile phone", "mobile": "mobile phone", "smartphone": "mobile phone", "cellphone": "mobile phone",
    "telephone": "telephone receiver", "tv": "television", "television": "television", "screen": "television",
    "ballot": "ballot box with ballot", "ballot paper": "ballot box with ballot", "ballot papers": "ballot box with ballot",
    "budget": "money bag", "fund": "money bag", "funds": "money bag", "loan": "money with wings", "debt": "money with wings",
    "fertiliser": "seedling", "fertilizer": "seedling", "seeds": "seedling", "scheme": "page facing up",
    "policy": "page facing up", "bill (law)": "scroll", "order": "scroll", "verdict": "scales", "judgement": "scales",
    "judgment": "scales", "fir": "page facing up", "complaint": "page facing up", "affidavit": "scroll", "vote": "ballot box with ballot", "evm": "ballot box with ballot",
    "voting": "ballot box with ballot", "election": "ballot box with ballot",
    "money": "money bag", "cash": "banknote with dollar sign", "note": "banknote with dollar sign",
    "notes": "banknote with dollar sign", "rupee": "banknote with dollar sign", "rupees": "banknote with dollar sign",
    "bribe": "money with wings", "coin": "coin", "coins": "coin", "gold": "coin", "wallet": "purse", "purse": "purse",
    "gun": "pistol", "pistol": "pistol", "rifle": "pistol", "weapon": "pistol", "sword": "crossed swords",
    "swords": "crossed swords", "knife": "hocho", "dagger": "dagger knife", "bomb": "bomb", "missile": "rocket",
    "rocket": "rocket", "shield": "shield", "bow": "bow and arrow", "arrow": "bow and arrow",
    "document": "page facing up", "documents": "page facing up", "paper": "page facing up", "papers": "page facing up",
    "file": "file folder", "files": "file folder", "folder": "file folder", "report": "page facing up",
    "letter": "envelope", "mail": "envelope", "email": "e-mail symbol", "newspaper": "newspaper", "news": "newspaper",
    "book": "open book", "books": "books", "notebook": "notebook", "diary": "notebook", "pen": "lower left ballpoint pen",
    "pencil": "pencil", "contract": "scroll", "scroll": "scroll", "certificate": "scroll", "law": "balance scale",
    "justice": "scales", "scale": "scales", "scales": "scales", "court": "scales", "key": "key", "lock": "lock",
    "chain": "chains", "chains": "chains", "handcuffs": "chains", "prison": "chains", "jail": "chains",
    "microphone": "microphone", "mic": "microphone", "speech": "microphone", "megaphone": "cheering megaphone",
    "loudspeaker": "public address loudspeaker", "camera": "camera", "video": "movie camera", "film": "film frames",
    "radio": "radio", "clock": "mantelpiece clock", "watch": "watch", "time": "hourglass", "hourglass": "hourglass",
    "calendar": "calendar", "date": "calendar", "chart": "chart with upwards trend", "graph": "chart with upwards trend",
    "growth": "chart with upwards trend", "loss": "chart with downwards trend", "fall": "chart with downwards trend",
    "data": "bar chart", "statistics": "bar chart", "stats": "bar chart", "map": "world map", "globe": "globe",
    "world": "globe", "earth": "globe", "satellite": "satellite", "medicine": "pill", "pill": "pill", "pills": "pill",
    "tablet": "pill", "vaccine": "syringe", "injection": "syringe", "syringe": "syringe", "virus": "microbe",
    "hospital": "hospital", "ambulance": "ambulance", "thermometer": "thermometer", "mask": "medical mask",
    "bulb": "electric light bulb", "idea": "electric light bulb", "electricity": "high voltage sign",
    "power": "high voltage sign", "battery": "battery", "plug": "electric plug", "oil": "oil drum",
    "petrol": "fuel pump", "fuel": "fuel pump", "diesel": "fuel pump", "gas": "fuel pump", "fire": "fire",
    "flame": "fire", "water": "droplet", "rain": "cloud with rain", "flood": "water wave", "wave": "water wave",
    "sun": "black sun with rays", "heat": "fire", "storm": "thunder cloud and rain", "lightning": "high voltage sign",
    "tree": "deciduous tree", "forest": "evergreen tree", "plant": "seedling", "crop": "sheaf of rice",
    "crops": "sheaf of rice", "wheat": "ear of rice", "rice": "cooked rice", "food": "cooked rice", "grain": "ear of rice",
    "onion": "onion", "tomato": "tomato", "potato": "potato", "milk": "glass of milk", "bread": "bread",
    "tea": "teacup without handle", "chai": "teacup without handle", "coffee": "hot beverage", "apple": "red apple",
    "mango": "mango", "banana": "banana", "egg": "egg", "meat": "cut of meat", "fish": "fish", "sugar": "sugar cubes" ,
    "salt": "salt shaker", "flour": "ear of rice", "car": "automobile", "tractor": "tractor", "truck": "delivery truck",
    "lorry": "delivery truck", "ship": "ship", "boat": "sailboat", "plane": "airplane", "train": "steam locomotive",
    "bicycle": "bicycle", "bike": "bicycle", "motorcycle": "racing motorcycle", "scooter": "motor scooter",
    "tyre": "wheel", "tire": "wheel", "wheel": "wheel", "fuel tanker": "delivery truck", "factory": "factory",
    "house": "house building", "home": "house building", "trophy": "trophy", "medal": "sports medal",
    "award": "trophy", "crown": "crown", "ring": "ring", "gift": "wrapped present", "box": "package",
    "parcel": "package", "package": "package", "bag": "handbag", "briefcase": "briefcase", "suitcase": "luggage",
    "luggage": "luggage", "shopping": "shopping trolley", "cart": "shopping trolley", "basket": "basket",
    "ticket": "ticket", "receipt": "receipt", "bill": "receipt", "invoice": "receipt", "tax": "receipt",
    "card": "credit card", "credit": "credit card", "bank": "bank", "atm": "automated teller machine",
    "placard": "placard", "banner": "placard", "sign": "placard", "poster": "placard", "flag": "waving white flag",
    "hammer": "hammer", "tool": "hammer and wrench", "tools": "hammer and wrench", "wrench": "wrench", "axe": "axe",
    "saw": "carpentry saw", "brick": "brick", "bricks": "brick", "rock": "rock", "stone": "rock", "wood": "wood",
    "ladder": "ladder", "rope": "knot", "bucket": "bucket", "broom": "broom", "chair": "chair", "bed": "bed",
    "door": "door", "window": "window", "toilet": "toilet", "mirror": "mirror", "candle": "candle", "lamp": "candle",
    "magnifier": "left-pointing magnifying glass", "investigation": "left-pointing magnifying glass",
    "search": "left-pointing magnifying glass", "evidence": "left-pointing magnifying glass", "ball": "soccer ball",
    "football": "soccer ball", "cricket": "cricket bat and ball", "bat": "cricket bat and ball", "guitar": "guitar",
    "drum": "drum with drumsticks", "music": "musical note", "game": "video game", "dice": "game die",
    "puzzle": "jigsaw puzzle piece", "teddy": "teddy bear", "toy": "teddy bear", "umbrella": "umbrella",
    "hat": "top hat", "cap": "billed cap", "shirt": "t-shirt", "dress": "dress", "shoe": "athletic shoe",
    "shoes": "athletic shoe", "glasses": "eyeglasses", "spectacles": "eyeglasses", "bottle": "bottle with popping cork",
    "glass": "tumbler glass", "cup": "teacup without handle", "plate": "fork and knife with plate", "pot": "cooking",
    "pan": "cooking", "tent": "tent", "dam": "water wave", "bridge": "bridge at night", "telescope": "telescope",
    "microscope": "microscope", "dna": "dna double helix", "atom": "atom symbol", "magnet": "magnet",
    "test tube": "test tube", "lab": "alembic", "robot": "mechanical arm", "ai": "mechanical arm", "chip": "electric plug",
    "drone": "helicopter", "helicopter": "helicopter", "parachute": "parachute", "anchor": "anchor",
    "compass": "compass", "flashlight": "electric torch", "torch": "electric torch", "bell": "bell",
    "alarm": "police cars revolving light", "siren": "police cars revolving light", "warning": "warning sign",
    "danger": "warning sign", "stop": "octagonal sign", "no": "no entry", "ban": "no entry sign", "banned": "no entry sign",
    "heart": "heavy black heart", "love": "heavy black heart", "star": "white medium star", "question": "black question mark ornament",
    # Hinglish and Hindi
    "kitab": "open book", "paisa": "money bag", "paise": "money bag", "notebandi": "banknote with dollar sign",
    "chunav": "ballot box with ballot", "kursi": "chair", "jhanda": "waving white flag", "dawai": "pill", "khana": "cooked rice",
    "किताब": "open book", "पैसा": "money bag", "पैसे": "money bag", "नोट": "banknote with dollar sign",
    "वोट": "ballot box with ballot", "मतपत्र": "ballot box with ballot", "चुनाव": "ballot box with ballot",
    "फ़ोन": "mobile phone", "फोन": "mobile phone", "कुर्सी": "chair", "दवा": "pill", "दवाई": "pill",
    "घड़ी": "mantelpiece clock", "चाबी": "key", "ताला": "lock", "आग": "fire", "पानी": "droplet",
    "रोटी": "bread", "चावल": "cooked rice", "गेहूं": "ear of rice", "कलम": "lower left ballpoint pen",
    "अख़बार": "newspaper", "अखबार": "newspaper", "तराज़ू": "scales", "तराजू": "scales", "बम": "bomb",
    "बंदूक": "pistol", "तलवार": "crossed swords", "माइक": "microphone", "कैमरा": "camera", "ट्रैक्टर": "tractor",
}

# sizes in metres (the larger side) for the words of the names; default 0.4
SIZE = [(r"computer|television|monitor", 0.55), (r"ballot box", 0.5), (r"swords|dagger|hocho", 0.8),
        (r"mobile phone|calculator|pill|coin|key|ring|syringe|thermometer|pen|pencil|watch|battery|plug", 0.16),
        (r"banknote|envelope|page|receipt|ticket|card|scroll|newspaper|book|notebook|calendar|file folder", 0.3),
        (r"money bag|package|present|briefcase|handbag|purse|basket|bucket|luggage", 0.5),
        (r"automobile|car\b|tractor|truck|ship|sailboat|airplane|locomotive|helicopter|ambulance", 3.0),
        (r"bicycle|motorcycle|scooter", 1.6), (r"house|factory|bank|hospital|tent|bridge", 4.0),
        (r"tree|evergreen", 4.0), (r"chair|guitar|drum|ladder|door|window|bed|toilet|mirror", 1.0),
        (r"placard", 1.3), (r"white flag", 1.6), (r"oil drum|fuel pump", 1.2), (r"wheel", 0.9),
        (r"rock|brick|wood", 0.35), (r"chart|bar chart", 0.6), (r"globe|world map", 0.6), (r"fire", 0.9)]


@lru_cache(maxsize=1)
def _index() -> list[tuple[str, str, set]]:
    out = []
    for lo, hi in RANGES:
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            name = unicodedata.name(ch, "")
            if not name or _never(name):
                continue
            out.append((ch, name, set(re.findall(r"[a-z]+", name.lower()))))
    return out


def _sing(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("es") and w[-3] in "sxz":
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


@lru_cache(maxsize=4096)
def find(phrase: str) -> tuple[str, str] | None:
    """(emoji character, Unicode name) for a phrase, or None. The head noun (the last word) counts most."""
    words = [w for w in re.findall(r"[a-z]+|[ऀ-ॿ]+", phrase.lower()) if w not in ("a", "an", "the", "of",
                                                                                            "his", "her", "their")]
    if not words or re.fullmatch(r"(?:man|men|woman|women|person|people|boy|girl|child|children|kid|kids|baby|"
                                 r"crowd|someone|everyone|he|she|they|him|her)", words[-1]):
        return None                                    # people are characters, never pictures
    idx = _index()
    by_name = {n.lower(): (c, n) for c, n, _ in idx}
    for cand in [" ".join(words[-2:])] + list(reversed(words)):          # "test tube", then the head noun first
        key = SYN.get(cand) or SYN.get(_sing(cand))
        if key and key in by_name and _drawable(by_name[key][0]):
            return by_name[key]
    for w in reversed(words):                                            # the head noun in the names
        s = _sing(w)
        if len(s) < 3:
            continue
        hits = [(len(toks), c, n) for c, n, toks in idx if s in toks or w in toks or (s + "s") in toks]
        for _, c, n in sorted(hits):
            if _drawable(c):
                return c, n
    return None


@lru_cache(maxsize=2048)
def _drawable(ch: str) -> bool:
    """The font has a real picture for it (not an empty box)."""
    return _raster(ch) is not None


@lru_cache(maxsize=2048)
def _raster(ch: str):
    from PIL import Image, ImageDraw, ImageFont
    try:
        f = ImageFont.truetype(FONT, 109)
    except OSError:
        return None
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
    box = im.getbbox()
    if not box:
        return None
    im = im.crop(box)
    a = im.getchannel("A")
    colours = len(set(im.convert("RGB").resize((24, 24)).getdata()))
    if colours < 3:                                    # a monochrome missing-glyph box
        return None
    return im


def flatten(im):
    """The CreatorForge look: few flat colours, a dark ink rim, no glossy gradients."""
    from PIL import Image, ImageFilter
    big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    alpha = big.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    rgb = big.convert("RGB").filter(ImageFilter.MedianFilter(5))
    flat = rgb.quantize(colors=7, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    rim = alpha.filter(ImageFilter.MaxFilter(9))
    out = Image.new("RGBA", (big.width + 12, big.height + 12), (0, 0, 0, 0))
    ink = Image.new("RGBA", big.size, (34, 30, 28, 255))
    out.paste(ink, (6, 6), rim)
    body = flat.convert("RGBA")
    body.putalpha(alpha)
    out.paste(body, (6, 6), body)
    return out


def size_of(name: str) -> float:
    low = name.lower()
    return next((s for rx, s in SIZE if re.search(rx, low)), 0.4)


def compose(phrase: str) -> dict:
    """An asset for any object phrase (raises ValueError when no picture fits)."""
    from .asset_lib import _asset
    hit = find(phrase)
    if hit is None:
        raise ValueError(f"no picture for {phrase!r}")
    ch, name = hit
    pic = flatten(_raster(ch))
    big = size_of(name)
    w, h = (big, big * pic.height / pic.width) if pic.width >= pic.height else (big * pic.width / pic.height, big)
    buf = io.BytesIO()
    pic.save(buf, "PNG", optimize=True)
    part = {"id": "art", "shape": "bitmap", "png": base64.b64encode(buf.getvalue()).decode(),
            "pts": [[-w / 2, 0], [w / 2, 0], [w / 2, h], [-w / 2, h]], "fill": [120, 120, 120],
            "line": [34, 30, 28], "z": 0}
    a = _asset("object", phrase.strip(), [part], w, h, uses=["carry", "background"], picture=name.lower())
    a["source"] = f"emoji:{name.lower()} (Noto Color Emoji, OFL) flattened"
    return a


@lru_cache(maxsize=512)
def decode(png_b64: str):
    from PIL import Image
    return Image.open(io.BytesIO(base64.b64decode(png_b64))).convert("RGBA")
