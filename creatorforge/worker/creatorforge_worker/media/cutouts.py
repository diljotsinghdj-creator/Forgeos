"""Real cut-out pictures for the Vox look: an object, a place or a public figure photographed for real, the subject
cut out, printed in black-and-white halftone with a white paper edge - the way editorial collages are made.

    c = cutouts.get("gavel", lib)            # -> Cutout(path, credit, name) or None
    c = cutouts.get("person:Narendra Modi", lib)

Photos come from Wikimedia Commons, keeping only public-domain and openly licensed files (the credit is kept and
shown). Fetched once on the pod and cached in the library folder; anything the library can't get returns None and
the graphic draws its vector icon instead, so a video never waits on or fails for a picture.

Cutting out: the ISNet model when the pod has it, else OpenCV GrabCut, else a plain-background flood fill. Every
cut is checked (a real subject, not the whole scene, not cut off at the edges) before it is used."""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

# ---- the catalogue: object name -> Commons search (the words a script uses map onto these names) ---------------
CATALOG: dict[str, str] = {
    # hands (the collage workhorse)
    "hand pointing": "hand pointing index finger isolated white background",
    "hand holding": "hand holding isolated white background",
    "hand giving": "hand offering open palm isolated",
    "hand open": "open hand palm isolated white background",
    "hand fist": "raised fist isolated",
    "hand writing": "hand holding pen writing isolated",
    "hands shake": "handshake isolated white background",
    "hand phone": "hand holding smartphone isolated",
    "hand cash": "hand holding banknotes isolated",
    "hand vote": "inked finger india election",
    # money and economy
    "cash": "stack of banknotes isolated white background",
    "rupee note": "500 rupee banknote India",
    "coins": "stack of coins isolated white background",
    "rupee coin": "Indian rupee coin",
    "money bag": "money bag sack isolated",
    "wallet": "leather wallet isolated white background",
    "piggy bank": "piggy bank isolated white background",
    "calculator": "calculator isolated white background",
    "credit card": "credit card isolated",
    "gold": "gold bars bullion",
    "safe": "safe vault isolated",
    "receipt": "paper receipt isolated",
    "shopping cart": "shopping cart isolated white background",
    "price tag": "price tag isolated",
    "stock chart": "stock exchange board",
    # law, power, politics
    "gavel": "gavel isolated white background",
    "scales of justice": "scales of justice isolated",
    "handcuffs": "handcuffs isolated white background",
    "prison bars": "prison cell bars",
    "ballot box": "ballot box isolated",
    "evm": "electronic voting machine India",
    "megaphone": "megaphone isolated white background",
    "microphone": "microphone isolated white background",
    "podium": "lectern podium isolated",
    "crown": "crown isolated white background",
    "chess king": "chess king piece isolated",
    "chess pawn": "chess pawn isolated white background",
    "puppet": "marionette puppet strings",
    "mask": "theatre mask isolated",
    "chain": "metal chain isolated white background",
    "padlock": "padlock isolated white background",
    "key": "old key isolated white background",
    "stamp": "rubber stamp isolated",
    "signature": "fountain pen isolated white background",
    "flag pole": "empty flagpole",
    "crowd": "crowd of people rally",
    "protest": "protest placards crowd",
    "queue": "people queue line",
    "soldier": "soldier silhouette",
    "police": "police officer india",
    "lathi": "police baton",
    # media and tech
    "newspaper": "folded newspaper isolated white background",
    "old newspaper": "vintage newspaper stack",
    "television": "vintage television set isolated",
    "radio": "vintage radio isolated white background",
    "smartphone": "smartphone isolated white background",
    "old phone": "rotary telephone isolated",
    "laptop": "laptop isolated white background",
    "computer": "desktop computer isolated",
    "camera": "camera isolated white background",
    "server": "server rack data center",
    "satellite": "satellite in orbit",
    "magnifying glass": "magnifying glass isolated white background",
    "envelope": "envelope letter isolated white background",
    "documents": "stack of documents papers isolated",
    "file folder": "file folder isolated",
    "book": "old book isolated white background",
    "books": "stack of books isolated white background",
    "typewriter": "typewriter isolated white background",
    "pen": "fountain pen isolated",
    "pencil": "pencil isolated white background",
    "clipboard": "clipboard isolated white background",
    "speech bubble": "speech balloon",
    # everyday objects and symbols
    "clock": "wall clock isolated white background",
    "hourglass": "hourglass isolated white background",
    "calendar": "desk calendar isolated",
    "light bulb": "light bulb isolated white background",
    "bomb": "cartoon bomb fuse",
    "fire": "fire flames isolated black background",
    "smoke": "smoke isolated",
    "ladder": "wooden ladder isolated white background",
    "stairs": "stone staircase",
    "door": "old wooden door",
    "umbrella": "umbrella isolated white background",
    "dice": "dice isolated white background",
    "trophy": "trophy cup isolated white background",
    "medal": "medal isolated white background",
    "rocket": "rocket launch",
    "globe": "terrestrial globe isolated",
    "compass": "compass isolated white background",
    "map": "old map paper",
    "binoculars": "binoculars isolated white background",
    "shoe": "leather shoe isolated white background",
    "boot": "boot isolated white background",
    "suitcase": "suitcase isolated white background",
    "briefcase": "briefcase isolated white background",
    "pill": "pills isolated white background",
    "syringe": "syringe isolated white background",
    "stethoscope": "stethoscope isolated white background",
    "brain": "human brain model",
    "heart": "anatomical heart model",
    "eye": "human eye close up",
    "tree": "tree isolated white background",
    "wheat": "wheat ears isolated",
    "tractor": "tractor india",
    "water drop": "water drop",
    "oil barrel": "oil barrel isolated",
    "factory chimney": "factory chimney smoke",
    "power tower": "electricity pylon",
    "solar panel": "solar panel",
    # people as figures (charts with figures standing on bars)
    "businessman": "businessman standing full length isolated white background",
    "worker": "construction worker standing full length isolated",
    "farmer standing": "indian farmer standing full length",
    "student": "student standing full length isolated white background",
    "woman standing": "woman standing full length isolated white background",
    "man standing": "man standing full length isolated white background",
    "doctor": "doctor standing full length isolated white background",
    # transport
    "car": "car isolated white background",
    "truck": "truck isolated white background",
    "bus": "bus india",
    "train": "indian railways train",
    "plane": "airliner in flight",
    "ship": "cargo ship",
    "boat": "boat isolated",
    "bicycle": "bicycle isolated white background",
    "auto rickshaw": "auto rickshaw india",
    # places (India first)
    "parliament": "Parliament House New Delhi",
    "new parliament": "New Parliament building India",
    "red fort": "Red Fort Delhi",
    "india gate": "India Gate New Delhi",
    "supreme court": "Supreme Court of India building",
    "rashtrapati bhavan": "Rashtrapati Bhavan",
    "taj mahal": "Taj Mahal",
    "gateway of india": "Gateway of India Mumbai",
    "qutub minar": "Qutb Minar",
    "village": "indian village houses",
    "skyline": "Mumbai skyline",
    "office building": "office building facade",
    "skyscraper": "skyscraper",
    "bank": "bank building columns",
    "temple": "hindu temple india",
    "school": "school building india",
    "hospital": "hospital building india",
    "factory": "factory building",
    "farm": "farm field india",
    "column": "greek column isolated",
    "capitol": "United States Capitol",
    "white house": "White House Washington",
    "kremlin": "Moscow Kremlin",
    "big ben": "Big Ben Elizabeth Tower",
}

# the words scripts use -> catalogue names
ALIASES: dict[str, str] = {
    "money": "cash", "rupees": "rupee note", "currency": "cash", "notes": "cash", "coin": "coins",
    "phone": "smartphone", "mobile": "smartphone", "whatsapp": "smartphone", "message": "smartphone",
    "tv": "television", "news": "newspaper", "paper": "newspaper", "report": "documents", "document": "documents",
    "file": "file folder", "court": "gavel", "judge": "gavel", "law": "scales of justice", "justice": "scales of justice",
    "arrest": "handcuffs", "jail": "prison bars", "election": "ballot box", "vote": "ballot box", "voters": "crowd",
    "people": "crowd", "rally": "crowd", "speech": "microphone", "leader": "podium", "power": "crown",
    "control": "puppet", "lie": "mask", "fake": "mask", "propaganda": "megaphone", "search": "magnifying glass",
    "investigation": "magnifying glass", "evidence": "magnifying glass", "time": "clock", "deadline": "hourglass",
    "idea": "light bulb", "growth": "stairs", "rise": "stairs", "success": "trophy", "ads": "megaphone",
    "data": "server", "internet": "server", "website": "laptop", "farmers": "tractor", "farmer": "tractor",
    "government": "parliament", "delhi": "india gate", "army": "soldier", "travel": "suitcase", "business": "briefcase",
    "company": "office building", "health": "stethoscope", "medicine": "pill", "pollution": "factory chimney",
    "oil": "oil barrel", "electricity": "power tower", "school": "school", "education": "books", "book": "book",
    "letter": "envelope", "secret": "padlock", "freedom": "key", "trap": "chain", "plane": "plane", "flight": "plane",
    "stage": "podium", "rally speech": "podium", "censorship": "padlock", "corruption": "cash", "bribe": "hand cash",
    "inflation": "shopping cart", "prices": "price tag", "economy": "coins", "debt": "chain", "tax": "calculator",
    "budget": "calculator", "scam": "mask", "truth": "magnifying glass", "fear": "padlock", "hope": "light bulb",
    "risk": "dice", "luck": "dice", "war": "soldier", "attack": "bomb", "crisis": "fire", "danger": "fire",
    "victory": "trophy", "winner": "trophy", "race": "trophy", "strategy": "chess king", "game": "chess pawn",
    "pawn": "chess pawn", "voice": "microphone", "speak": "megaphone", "surveillance": "camera", "spy": "binoculars",
    "watch": "binoculars", "world": "globe", "global": "globe", "trade": "ship", "export": "ship", "jobs": "briefcase",
}

_PLACES = {"parliament", "new parliament", "red fort", "india gate", "supreme court", "rashtrapati bhavan", "taj mahal",
           "gateway of india", "qutub minar", "capitol", "white house", "kremlin", "big ben"}

_OK_LICENCE = re.compile(r"^(public domain|pd\b|pd-|cc0|cc by(-sa)?( \d\.\d)?|cc-by(-sa)?(-\d\.\d)?|no restrictions)",
                         re.I)


@dataclass
class Cutout:
    name: str
    path: Path
    credit: str = ""


FIGURES = {"ceo": "businessman", "boss": "businessman", "billionaire": "businessman", "rich": "businessman",
           "1%": "businessman", "worker": "worker", "labour": "worker", "labourer": "worker", "employee": "worker",
           "farmer": "farmer standing", "kisan": "farmer standing", "student": "student", "woman": "woman standing",
           "women": "woman standing", "man": "man standing", "men": "man standing", "doctor": "doctor",
           "teacher": "man standing", "voter": "man standing", "citizen": "man standing"}


def figure(label: str) -> str:
    """A person figure for a chart label ('farmer' -> 'farmer standing'); generic person otherwise."""
    words = re.findall(r"[a-z0-9%]+", (label or "").lower())
    return next((FIGURES[w] for w in words if w in FIGURES), "man standing")


def resolve(word: str) -> str | None:
    """The catalogue name for a script word ("money" -> "cash"), a person ("person:Name"), or None."""
    w = (word or "").strip().lower()
    if not w:
        return None
    if w.startswith("person:"):
        return "person:" + word.split(":", 1)[1].strip()
    if w in CATALOG:
        return w
    if w in ALIASES:
        return ALIASES[w]
    s = w.rstrip("s")
    if s in CATALOG:
        return s
    if s in ALIASES:
        return ALIASES[s]
    hits = [n for n in CATALOG if w in n.split() or s in n.split()]
    if hits:
        return min(hits, key=len)
    # anything else that names an object ("gold bars", "rubber stamp"): searched for as it is; gibberish ("zzzz")
    # has no vowel in some word and is never searched for
    words = w.split()
    if re.fullmatch(r"[a-z][a-z0-9 '\-]{2,40}", w) and len(words) <= 4 and all(re.search(r"[aeiouy]", x) for x in words):
        return "obj:" + w
    return None


def known(word: str) -> bool:
    """True when a word is surely a picture: a person or an object in the catalogue (with its aliases). Scenes that
    must tell a picture from plain text (a pinboard's word card, a news card's subtitle) use this, not the open
    object search, so 'SOLVED' stays a word and 'the line under it' stays a subtitle."""
    r = resolve(word)
    return bool(r) and not r.startswith("obj:")


def library_dir(base: Path | None = None) -> Path:
    d = Path(base or os.environ.get("CF_CUTOUTS") or Path.home() / ".cache" / "creatorforge" / "cutouts")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or hashlib.sha1(name.encode()).hexdigest()[:10]


def cached(name: str, lib: Path | None = None) -> Cutout | None:
    d = library_dir(lib)
    p, meta = d / f"{_slug(name)}.png", d / f"{_slug(name)}.json"
    if p.is_file() and p.stat().st_size > 0:
        credit = ""
        if meta.is_file():
            try:
                credit = json.loads(meta.read_text(encoding="utf-8")).get("credit", "")
            except ValueError:
                pass
        return Cutout(name, p, credit)
    return None


_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def env_sources() -> list[tuple[str, str]]:
    """Stock photo keys set on the pod (PIXABAY_KEY, UNSPLASH_KEY)."""
    out = []
    if os.environ.get("PIXABAY_KEY"):
        out.append(("pixabay", os.environ["PIXABAY_KEY"]))
    if os.environ.get("UNSPLASH_KEY"):
        out.append(("unsplash", os.environ["UNSPLASH_KEY"]))
    return out


def _candidates(name: str, sources: list[tuple[str, str]] | None, timeout: float) -> list[dict]:
    """Photos to try, best source first. Objects: Pixabay/Unsplash (many shot on plain backgrounds, which cut out
    cleanly), then Openverse, then Wikimedia Commons. Public figures and landmarks: Wikimedia Commons only (real,
    openly licensed photos of the actual person or place)."""
    person = name.startswith("person:")
    place = name in _PLACES
    out: list[dict] = []
    if not person and not place:
        from ..providers import stock_photo
        plain = name.removeprefix("obj:").strip()
        for provider, key in (sources if sources is not None else env_sources()):
            if provider not in ("pixabay", "unsplash", "pexels") or not key:
                continue
            q = f"{plain} isolated white background" if provider == "pixabay" else f"{plain} isolated"
            try:
                out += stock_photo.search(provider, key, q, portrait=False, timeout=timeout)[:5]
            except Exception:  # noqa: BLE001 - bad key / quota: next source
                pass
        try:
            out += stock_photo.search("openverse", "", plain, portrait=False, timeout=timeout)[:3]
        except Exception:  # noqa: BLE001
            pass
    queries = [name.split(":", 1)[1] + " official portrait", name.split(":", 1)[1] + " portrait"] if person \
        else [CATALOG.get(name, name.removeprefix("obj:"))]
    for query in queries:
        try:
            from ..providers.archive_photo import search
            out += search(query, timeout=timeout, limit=10)[:6]
        except Exception:  # noqa: BLE001
            pass
    return out


def face_count(path: Path, min_frac: int = 10) -> int:
    """How many human faces a picture shows (OpenCV's frontal-face finder; faces at least 1/min_frac of the width).
    -1 when it cannot tell (no OpenCV)."""
    try:
        import cv2
        import numpy as np
        from PIL import Image
        with Image.open(path) as im:
            g = np.asarray(im.convert("L"))
        casc = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
        return len(casc.detectMultiScale(g, scaleFactor=1.08, minNeighbors=10, minSize=(max(24, g.shape[1] // min_frac),) * 2))
    except Exception:  # noqa: BLE001
        return -1


def has_face(path: Path) -> bool:
    """True when a picture shows a human face. An object's stock photo with a model in it would put a private person's
    face on screen: the owner's rules forbid that, so such a cut-out is never used."""
    return face_count(path) > 0


# a "person:" photo must be the person: a lookalike, a statue or a costume is not them (2026-11-13: a search for
# Donald Trump returned a well-known photo of a Trump impersonator beside a Kim Jong-un impersonator)
NOT_THE_PERSON = ("impersonat", "lookalike", "look-alike", "look alike", "double", "parody", "costume", "cosplay",
                  "wax", "madame tussaud", "statue", "sculpture", "bust of", "mural", "graffiti", "caricature", "cartoon",
                  "effigy", "puppet", "mask", "drawing", "painting", "poster of", "cutout", "cardboard")


def person_ok(name: str, r: dict) -> bool:
    """Is this search result a photograph of the actual person (by its title and description)?"""
    text = " ".join(str(r.get(k, "")) for k in ("about", "title")).lower()
    return not any(w in text for w in NOT_THE_PERSON)


def _person_rank(r: dict) -> int:
    """Official portraits first: they show the person alone, facing the camera, with a clear public-domain record."""
    text = " ".join(str(r.get(k, "")) for k in ("about", "title")).lower()
    return 0 if "official" in text and "portrait" in text else 1 if "portrait" in text else 2


def get(word: str, lib: Path | None = None, model: Path | None = None, fetch: bool = True,
        timeout: float = 25, sources: list[tuple[str, str]] | None = None) -> Cutout | None:
    """A ready cut-out for a word (from the library, or fetched and made now when `fetch`), or None."""
    name = resolve(word)
    if not name:
        return None
    person = name.startswith("person:")
    hit = cached(name, lib)
    if hit and not person and has_face(hit.path):
        return None                              # an object photo with someone's face in it: the drawing is used instead
    if hit or not fetch or os.environ.get("CF_CUTOUT_FETCH", "1") == "0":
        return hit
    d = library_dir(lib)
    miss = d / f"{_slug(name)}.miss"
    if miss.is_file():                       # tried before and nothing usable: don't search again
        return None
    with _locks_guard:
        lock = _locks.setdefault(name, threading.Lock())
    with lock:
        hit = cached(name, lib)
        if hit:
            return hit
        results = _candidates(name, sources, timeout)
        if name.startswith("obj:"):
            # a free-form object: the photo must be tagged with it (a "bank vault" search must not give a piggy bank)
            from ..providers.stock_video import relevant
            want = name.removeprefix("obj:")
            results = [r for r in results if relevant(want, " ".join(str(r.get(k, "")) for k in ("about", "title")))]
        if person:
            results = sorted([r for r in results if person_ok(name, r)], key=_person_rank)
        if not results:
            return None                          # offline / blocked: the vector icon is drawn instead
        for r in results[:10]:
            try:
                raw = _download(r["url"], d, timeout)
                if person and face_count(raw, 14) > 1:
                    continue                     # two or more faces: not a portrait of one person (could be anyone)
                out = make(raw, d / f"{_slug(name)}.png", model=model, person=name.startswith("person:"))
            except Exception:  # noqa: BLE001 - try the next photo
                continue
            if out is not None and not person and has_face(out):
                out.unlink(missing_ok=True)      # a model's face in an object photo: never shown; try the next one
                continue
            if out is not None:
                if r.get("track") and r.get("key"):      # Unsplash's API terms: report the download
                    try:
                        import httpx
                        httpx.get(r["track"], headers={"Authorization": f"Client-ID {r['key']}"}, timeout=10)
                    except Exception:  # noqa: BLE001
                        pass
                (d / f"{_slug(name)}.json").write_text(json.dumps(
                    {"name": name, "credit": r.get("credit", ""), "source": r.get("url", ""),
                     "title": r.get("title", "")}, ensure_ascii=False), encoding="utf-8")
                return Cutout(name, out, r.get("credit", ""))
        miss.write_text("no usable photo", encoding="utf-8")
        return None


def _download(url: str, d: Path, timeout: float) -> Path:
    import httpx
    from ..providers.stock_video import UA
    raw = d / "raw" / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".img")
    if raw.is_file():
        return raw
    raw.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.get(url, timeout=timeout, headers={"User-Agent": UA}, follow_redirects=True)
    r.raise_for_status()
    if len(r.content) > 25_000_000:
        raise ValueError("too big")
    raw.write_bytes(r.content)
    return raw


# ---- making a cut-out -----------------------------------------------------------------------------------------------
def make(image: Path, out: Path, model: Path | None = None, person: bool = False, halftone: bool = True) -> Path | None:
    """Cut the subject out of a photo, print it in halftone black-and-white with a white paper edge. None when the
    photo has no clear single subject."""
    from PIL import Image
    with Image.open(image) as im:
        rgb = im.convert("RGB")
    rgb.thumbnail((1600, 1600), Image.LANCZOS)
    mask = _mask(rgb, model, person)
    if mask is None or not _good(mask, person):
        return None
    bbox = mask.point(lambda v: 255 if v > 128 else 0).getbbox()
    rgb, mask = rgb.crop(bbox), mask.crop(bbox)
    art = print_look(rgb, halftone=halftone)
    art.putalpha(mask)
    art = sticker_edge(art)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.stem}.{threading.get_ident()}.part.png")
    art.save(tmp, optimize=True)
    tmp.replace(out)
    return out


_BIREF: dict = {}


def birefnet_model(near: Path | None = None) -> Path | None:
    """BiRefNet (MIT): the sharpest cut-out model we use - hair, fine edges, thin masts. CF_BIREFNET, else a
    birefnet*.onnx beside the ISNet model or in <data>/models."""
    if os.environ.get("CF_BIREFNET") and Path(os.environ["CF_BIREFNET"]).is_file():
        return Path(os.environ["CF_BIREFNET"])
    dirs = [Path(near).parent] if near else []
    dirs.append(Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "models")
    for d in dirs:
        found = sorted(d.glob("birefnet*.onnx")) if d.is_dir() else []
        if found:
            return found[0]
    return None


def _providers() -> list[str]:
    """The GPU first when the pod has one (BiRefNet takes well under a second a frame there; ~17 s on CPU)."""
    try:
        import onnxruntime as ort
        have = ort.get_available_providers()
    except Exception:  # noqa: BLE001
        return ["CPUExecutionProvider"]
    return [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in have] or ["CPUExecutionProvider"]


def birefnet_fast() -> bool:
    return _providers()[0] == "CUDAExecutionProvider"


def _birefnet(rgb, path: Path):
    """Subject mask from BiRefNet (1024x1024, ImageNet normalisation, sigmoid of the first output)."""
    import numpy as np
    from PIL import Image
    if str(path) not in _BIREF:
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.enable_cpu_mem_arena = False        # the arena kept every run's buffers: 12 GB after two frames, 6.7 GB without
        so.enable_mem_pattern = False
        _BIREF[str(path)] = ort.InferenceSession(str(path), so, providers=_providers())
    sess = _BIREF[str(path)]
    x = np.asarray(rgb.convert("RGB").resize((1024, 1024), Image.BICUBIC), np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    pred = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    pred = 1 / (1 + np.exp(-pred))
    return Image.fromarray((np.clip(pred, 0, 1) * 255).astype("uint8"), "L").resize(rgb.size, Image.LANCZOS)


def _mask(rgb, model: Path | None, person: bool):
    """Subject mask (L, 0-255): BiRefNet when available, else ISNet, else GrabCut, else plain-background flood fill."""
    from PIL import Image
    bref = birefnet_model(model)
    if bref is not None:
        try:
            return _birefnet(rgb, bref)
        except Exception:  # noqa: BLE001 - the next model down still cuts
            pass
    if model is not None and Path(model).is_file():
        try:
            import numpy as np
            from .layout import _cutout_session
            session = _cutout_session(Path(model))
            x = np.asarray(rgb.resize((1024, 1024), Image.LANCZOS), dtype=np.float32)
            x = x / max(float(x.max()), 1e-6) - 0.5
            pred = session.run(None, {session.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
            pred = (pred - pred.min()) / max(float(pred.max() - pred.min()), 1e-6)
            return Image.fromarray((pred * 255).astype("uint8"), "L").resize(rgb.size, Image.LANCZOS)
        except Exception:  # noqa: BLE001
            pass
    m = _plain_background(rgb)
    if m is not None:
        return m
    return None if person else _grabcut(rgb)     # never a guessed cut of a real person (a lost head, half a face)


def _plain_background(rgb):
    """Objects photographed on a plain (white or flat) background: flood the background in from the edges."""
    import numpy as np
    from PIL import Image
    a = np.asarray(rgb, dtype=np.int16)
    h, w, _ = a.shape
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    ref = np.median(border, axis=0)
    spread = np.abs(border - ref).max(axis=1)
    if (spread < 28).mean() < 0.85:          # the edges are not one plain colour: not this kind of photo
        return None
    close = (np.abs(a - ref).max(axis=2) < 30)
    # flood fill from the border through "close" pixels
    from collections import deque
    bg = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if close[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if close[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and close[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    m = Image.fromarray(((~bg) * 255).astype("uint8"), "L")
    from PIL import ImageFilter
    return m.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.2))


def _grabcut(rgb):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    from PIL import Image, ImageFilter
    a = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
    h, w = a.shape[:2]
    scale = 640 / max(h, w)
    small = cv2.resize(a, (max(1, int(w * scale)), max(1, int(h * scale)))) if scale < 1 else a
    sh, sw = small.shape[:2]
    mask = np.zeros((sh, sw), np.uint8)
    rect = (int(sw * 0.06), int(sh * 0.04), int(sw * 0.88), int(sh * 0.94))
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(small, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None
    fg = np.where((mask == 1) | (mask == 3), 255, 0).astype("uint8")
    # keep the largest piece only
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n > 1:
        big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        fg = np.where(lab == big, 255, 0).astype("uint8")
    # GrabCut is a fallback: refuse anything doubtful. A cut that runs along the starting rectangle (the sky kept
    # around a rocket) or fills its own box like a slab is a piece of scene, not an object.
    x0, y0, rw, rh = rect
    sides = (fg[y0 + 1, x0:x0 + rw], fg[y0:y0 + rh, x0 + 1], fg[y0:y0 + rh, x0 + rw - 2])
    if any(float((s > 0).mean()) > 0.2 for s in sides):
        return None
    ys, xs = np.nonzero(fg)
    if len(xs) == 0 or (fg > 0).sum() / max(1, (np.ptp(xs) + 1) * (np.ptp(ys) + 1)) > 0.86:
        return None
    m = Image.fromarray(fg, "L").resize(rgb.size, Image.LANCZOS)
    return m.filter(ImageFilter.GaussianBlur(1.5))


def _good(mask, person: bool = False) -> bool:
    """A real single subject: covers 6-70% of the photo, a confident mask, not cut off on three or more sides. A
    head-and-shoulders portrait may fill more of the frame and touch the bottom and both sides (the shoulders), but
    never the top: the head is always whole."""
    import numpy as np
    m = np.asarray(mask)
    cover = float((m > 128).mean())
    if person and float((m[0] > 128).mean()) < 0.05 and 0.06 <= cover <= 0.88:
        return float(((m > 30) & (m < 225)).mean()) <= 0.35 * cover
    if not 0.06 <= cover <= 0.72:
        return False
    unsure = float(((m > 30) & (m < 225)).mean())
    if unsure > 0.35 * cover:
        return False
    edges = sum(float((side > 128).mean()) > 0.25 for side in (m[0], m[-1], m[:, 0], m[:, -1]))
    return edges <= 2          # a person's shoulders may touch the bottom; touching most edges = a whole scene


# ---- the print look -------------------------------------------------------------------------------------------------
def print_look(rgb, halftone: bool = True, cell: float | None = None):
    """Black-and-white editorial print: strong contrast, a fine 45-degree halftone screen blended into the photo
    (the photo stays readable; the dots give the printed-paper texture)."""
    import numpy as np
    from PIL import Image, ImageOps
    g = ImageOps.autocontrast(rgb.convert("L"), cutoff=1.5)
    a = np.asarray(g, dtype=np.float32) / 255.0
    a = np.clip((a - 0.5) * 1.18 + 0.52, 0, 1)                    # a little punch
    if halftone:
        h, w = a.shape
        c = cell or max(3.2, min(h, w) / 170)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        u = (xx + yy) * 0.7071 / c
        v = (xx - yy) * 0.7071 / c
        d = np.hypot(u - np.floor(u) - 0.5, v - np.floor(v) - 0.5) / 0.7071   # 0 at the dot centre .. 1 corner
        dark = 1 - a
        dots = np.where(d < np.sqrt(np.clip(dark, 0, 1)) * 0.95, 0.0, 1.0)
        a = np.clip(a * 0.62 + dots * 0.38 * (0.35 + 0.65 * a) + 0.03, 0, 1)
    ink, paper = np.array([20, 20, 22], np.float32), np.array([247, 244, 236], np.float32)
    out = ink + (paper - ink) * a[..., None]
    return Image.fromarray(out.astype("uint8"), "RGB").convert("RGBA")


def sticker_edge(art, edge: float | None = None):
    """A white paper edge around the cut-out (as if cut from a magazine with scissors)."""
    from PIL import Image, ImageFilter
    w, h = art.size
    e = int(edge or max(4, min(w, h) * 0.014))
    pad = e * 2
    canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    alpha = Image.new("L", canvas.size, 0)
    alpha.paste(art.getchannel("A"), (pad, pad))
    grown = alpha.filter(ImageFilter.MaxFilter(e * 2 + 1)).point(lambda v: 255 if v > 90 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(0.8))
    white = Image.new("RGBA", canvas.size, (250, 248, 242, 255))
    white.putalpha(grown)
    canvas.alpha_composite(white)
    canvas.alpha_composite(art, (pad, pad))
    return canvas


def warm(lib: Path | None = None, model: Path | None = None, names: list[str] | None = None) -> dict:
    """Fetches and makes the whole catalogue (run once in the background on a new pod)."""
    ok, missing = [], []
    for n in names or list(CATALOG):
        (ok if get(n, lib, model=model) else missing).append(n)
    return {"ready": len(ok), "missing": missing}


if __name__ == "__main__":       # python -m creatorforge_worker.media.cutouts <library> [<isnet model>]
    import sys
    lib_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    model_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    print(json.dumps(warm(lib_arg, model_arg)))
