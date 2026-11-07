"""Visual metaphors: an abstract idea in a line becomes a small animated picture - the way an explainer channel draws
"prices are rising" as price tags climbing, or "time is running out" as an hourglass draining.

    match("Unemployment has doubled")   -> "unemployment"
    recipe("unemployment")              -> what to draw and how it moves

Each metaphor is a few flat object pictures (objects.py) with a motion: rise, fall, grow, shrink, pulse, fly, tip,
multiply, stack, split, dim, crack, drain. They are always labelled "Illustration" on screen (visual_reasoning sets
the label), never stand in for evidence, and an allegation never becomes a metaphor (visual_reasoning sends it to
the sourced-evidence path first). Keywords in English, Hinglish and Hindi."""
from __future__ import annotations

import math
import re

# (concept, keywords, [items]); an item: picture phrase, motion, (dx, dy) metres from the bottom centre, size metres
LIB = [
    ("unemployment", r"unemploy\w*|jobless\w*|job loss\w*|lost (?:their|his|her)? ?jobs?|layoffs?|laid off|"
                     r"berozgar\w*|बेरोज़गार\w*|बेरोजगार\w*",
     [("briefcase", "fall", (-0.7, 1.4), 0.45), ("briefcase", "fall", (0.0, 1.7), 0.45),
      ("briefcase", "fall", (0.7, 1.5), 0.45), ("no entry", "pulse", (0.0, 0.2), 0.5)]),
    ("delay", r"delay\w*|pending|backlog|red tape|bureaucra\w*|years? to decide|stuck for|still waiting|"
              r"लंबित|देरी",
     [("file folder", "stack", (-0.5, 0.0), 0.45), ("hourglass", "tip", (0.6, 0.6), 0.6)]),
    ("inequality", r"inequal\w*|gap between rich and poor|rich get richer|wealth gap|the richest|top 1|"
                   r"असमानता|amir.{0,10}garib",
     [("coin", "stack", (-0.6, 0.0), 0.35), ("coin", "pulse", (0.6, 0.0), 0.35)]),
    ("debt", r"\bdebt\w*|\bloans?\b|borrow\w*|owes?\b|deficit|karz\w*|कर्ज़\w*|कर्ज\w*|उधार",
     [("chains", "pulse", (0.0, 0.1), 0.7), ("money with wings", "fly", (0.0, 0.9), 0.5)]),
    ("pollution", r"pollut\w*|smog|air quality|aqi\b|emission\w*|toxic air|prdushan|प्रदूषण",
     [("factory", "pulse", (-0.4, 0.0), 1.1), ("cloud", "multiply", (0.4, 1.3), 0.5)]),
    ("climate", r"climate change|global warming|heatwave|heat wave|temperatures? (?:rise|rising|soar)|"
                r"जलवायु|गर्मी",
     [("globe", "pulse", (-0.4, 0.3), 0.8), ("thermometer", "rise", (0.6, 0.1), 0.7)]),
    ("drought", r"drought|water shortage|dry (?:wells|taps|rivers)|no water|sukha|सूखा|पानी की कमी",
     [("droplet", "shrink", (0.0, 0.4), 0.8)]),
    ("flood", r"flood\w*|deluge|inundat\w*|baadh|बाढ़",
     [("house building", "pulse", (0.0, 0.0), 0.9), ("water wave", "rise", (0.0, -0.4), 1.2)]),
    ("growth", r"econom\w* (?:grew|grows|growing|boom\w*)|growth rate|\bgdp\b.{0,20}(?:rose|grew|up)|"
               r"\bboom\w*|thriv\w*|vikas|विकास",
     [("seedling", "grow", (-0.5, 0.0), 0.7), ("chart with upwards trend", "rise", (0.5, 0.3), 0.7)]),
    ("recession", r"recession|slowdown|econom\w* (?:shrank|shrinks|slow\w*|contract\w*)|downturn|crash\w*|"
                  r"मंदी",
     [("chart with downwards trend", "fall", (0.0, 0.6), 0.8)]),
    ("censorship", r"censor\w*|gag(?:ged)?\b|silenc\w*|free speech|press freedom|banned (?:the )?(?:book|film|news)|"
                   r"सेंसर",
     [("microphone", "pulse", (0.0, 0.3), 0.7), ("lock", "fall", (0.0, 0.9), 0.4)]),
    ("surveillance", r"surveil\w*|spying|spyware|pegasus|privacy|tracked|monitor(?:ed|ing) (?:citizens|phones)|"
                     r"निगरानी|जासूसी",
     [("left-pointing magnifying glass", "swing", (0.0, 0.6), 0.7), ("mobile phone", "pulse", (0.0, 0.2), 0.3)]),
    ("division", r"divid\w*|polari[sz]\w*|split\b|rift|communal|us versus them|बँटवारा|बंटवारा|ध्रुवीकरण",
     [("house building", "split", (0.0, 0.0), 0.7)]),
    ("unity", r"unit(?:y|ed|e)\b|together|solidarity|alliance|एकता|मिलकर",
     [("chains", "pulse", (0.0, 0.3), 0.8)]),
    ("misinformation", r"fake news|misinformation|disinformation|propaganda|rumou?rs?|whatsapp forward|"
                       r"अफवाह|झूठी खबर",
     [("newspaper", "pulse", (-0.3, 0.2), 0.6), ("warning sign", "pulse", (0.4, 0.7), 0.45)]),
    ("deadline", r"deadline|time is running out|running out of time|last date|countdown|before it'?s too late|"
                 r"समय सीमा",
     [("hourglass", "tip", (0.0, 0.2), 0.8), ("alarm clock", "pulse", (0.7, 0.1), 0.45)]),
    ("trust", r"lost (?:public )?trust|trust deficit|betray\w*|broken promises?|disillusion\w*|भरोसा टूट",
     [("broken heart", "pulse", (0.0, 0.4), 0.6)]),
    ("education", r"educat\w*|literacy|schooling|learning|shiksha|शिक्षा|पढ़ाई",
     [("books", "stack", (-0.4, 0.0), 0.5), ("electric light bulb", "pulse", (0.5, 0.9), 0.45)]),
    ("pandemic", r"pandemic|epidemic|outbreak|virus spread\w*|infections? (?:rose|rise|spread)|covid|महामारी",
     [("microbe", "multiply", (0.0, 0.6), 0.35)]),
    ("war", r"\bwar\b|conflict|fighting|clashes|border tension|युद्ध|जंग",
     [("crossed swords", "pulse", (0.0, 0.5), 0.8), ("fire", "pulse", (0.0, 0.0), 0.6)]),
    ("peace", r"\bpeace\b|ceasefire|truce|treaty|शांति|समझौता",
     [("dove of peace", "fly", (0.0, 0.8), 0.6)]),
    ("energy", r"power cuts?|blackout|electricity shortage|energy crisis|load ?shedding|बिजली कटौती",
     [("battery", "drain", (-0.4, 0.2), 0.5), ("electric light bulb", "dim", (0.5, 0.8), 0.5)]),
    ("migration", r"migra\w*|refugees? (?:flee|fled|crossing)|displaced|exodus|palayan|पलायन",
     [("luggage", "walk", (-0.9, 0.0), 0.45), ("luggage", "walk", (-0.3, 0.0), 0.45),
      ("luggage", "walk", (0.3, 0.0), 0.45)]),
    ("technology", r"\bai\b|artificial intelligence|automation|robots? (?:replac|tak)\w*|technolog\w*|digital",
     [("personal computer", "pulse", (-0.4, 0.1), 0.6), ("mechanical arm", "swing", (0.5, 0.3), 0.6)]),
    ("justice", r"justice|verdict|acquitt\w*|convict\w*|the law|fair trial|न्याय|फैसला",
     [("scales", "tip", (0.0, 0.3), 0.8)]),
    ("price_fall", r"prices? (?:fell|fall|drop\w*|came down|crash\w*)|cheaper|deflation|सस्ता|दाम घटे",
     [("receipt", "fall", (-0.4, 0.9), 0.4), ("shopping trolley", "pulse", (0.4, 0.0), 0.6)]),
    ("housing", r"rent\w* (?:rose|rising|soar\w*)|housing crisis|homeless\w*|unaffordable homes?|property prices|"
                r"मकान|किराया",
     [("house building", "pulse", (-0.4, 0.0), 0.8), ("money bag", "rise", (0.5, 0.2), 0.5)]),
    ("hunger", r"hunger|starv\w*|malnutrition|food shortage|empty plates?|bhukhmari|भुखमरी|भूख",
     [("fork and knife with plate", "pulse", (0.0, 0.2), 0.6), ("cooked rice", "shrink", (0.0, 0.75), 0.4)]),
    ("poverty", r"povert\w*|\bpoor\b|below the poverty line|garibi|गरीबी",
     [("purse", "shrink", (0.0, 0.3), 0.6)]),
    ("taxes", r"tax(?:es)? (?:rose|hike\w*|increase\w*)|\bgst\b|new tax|टैक्स|कर बढ़",
     [("receipt", "stack", (-0.3, 0.0), 0.4), ("money with wings", "fly", (0.4, 0.6), 0.45)]),
]
_RX = [(c, re.compile(rx, re.I), items) for c, rx, items in LIB]


def match(text: str) -> str | None:
    for c, rx, _ in _RX:
        if rx.search(text):
            return c
    return None


def recipe(concept: str) -> list:
    return next((items for c, _, items in _RX if c == concept), [])


def _ease(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def pose(motion: str, u: float, t: float, k: int):
    """(dx, dy, scale, alpha, angle, copies) for a motion at progress u (0..1) and time t."""
    e = _ease(u)
    if motion == "rise":
        return 0.0, 0.9 * e, 1.0, 1.0, 0.0, 1
    if motion == "fall":
        return 0.0, -1.2 * e, 1.0, 1.0 - 0.3 * e, 20.0 * e * (1 if k % 2 else -1), 1
    if motion == "grow":
        return 0.0, 0.0, 0.4 + 0.9 * e, 1.0, 0.0, 1
    if motion == "drain":                            # empties: shrinks but never below a third
        return 0.0, 0.0, 1.0 - 0.6 * e, 1.0, 0.0, 1
    if motion == "shrink":
        return 0.0, 0.0, 1.15 - 0.75 * e, 1.0, 0.0, 1
    if motion == "fly":
        return 0.7 * e, 0.5 * e + 0.08 * math.sin(t * 9), 1.0, 1.0 - 0.5 * e, -10.0 * e, 1
    if motion == "tip":
        return 0.0, 0.0, 1.0, 1.0, 25.0 * math.sin(t * 1.6), 1
    if motion == "swing":
        return 0.5 * math.sin(t * 2.2), 0.0, 1.0, 1.0, 10.0 * math.sin(t * 2.2), 1
    if motion == "multiply":
        return 0.0, 0.0, 1.0, 1.0, 0.0, 1 + int(6 * e)
    if motion == "stack":
        return 0.0, 0.0, 1.0, 1.0, 0.0, 1 + int(5 * e)
    if motion == "split":
        return 0.0, 0.0, 1.0, 1.0, 0.0, -1          # drawn as two halves moving apart
    if motion == "dim":
        return 0.0, 0.0, 1.0, 1.0 - 0.75 * e, 0.0, 1
    if motion == "walk":
        return 1.0 * e, 0.05 * abs(math.sin(t * 7 + k)), 1.0, 1.0, 0.0, 1
    return 0.0, 0.0, 1.0 + 0.07 * math.sin(t * 5 + k), 1.0, 0.0, 1     # pulse


SCATTER = [(0, 0), (-0.55, 0.35), (0.55, 0.3), (-0.3, 0.8), (0.4, 0.85), (0.0, 1.25), (-0.65, 1.1)]


def draw(p, d, S, scale, t):
    """A 'metaphor' prop: its pictures, moving. p.data: concept, t0, t1."""
    from PIL import Image
    from . import objects
    t0, t1 = p.data.get("t0", 0.0), p.data.get("t1", 1.0)
    u = (t - t0 - 0.4) / max(0.5, (t1 - t0) - 1.2)
    show = p.value("show", t, 1.0) if hasattr(p, "value") else 1.0
    if show <= 0.01:
        return
    x, y, _ = p.pos(t)
    for k, (phrase, motion, (dx, dy), size) in enumerate(recipe(p.data.get("concept", ""))):
        hit = objects.exact(phrase) or objects.find(phrase)
        if hit is None:
            continue
        pic = objects.flat(hit[0])
        ox, oy, sc_, alpha, ang, copies = pose(motion, u, t, k)
        spots = [(0.0, 0.0)] if copies == 1 else \
            [(0.0, i * size * 0.55) for i in range(copies)] if motion == "stack" else \
            [(SCATTER[i % 7][0] * size * 1.6, SCATTER[i % 7][1] * size) for i in range(max(1, copies))]
        if copies == -1:                                   # split: two halves drift apart, a crack between
            gap = 0.45 * _ease(u)
            halves = [(pic.crop((0, 0, pic.width // 2, pic.height)), -size / 4 - gap),
                      (pic.crop((pic.width // 2, 0, pic.width, pic.height)), size / 4 + gap)]
            for half, hx in halves:
                _paste(d, half, S, x + dx + hx, y + dy, size / 2, size * pic.height / pic.width, 1.0, 0.0, show)
            continue
        for sx, sy in spots:
            w = size * sc_
            h = w * pic.height / pic.width
            _paste(d, pic, S, x + dx + ox + sx, y + dy + oy + sy, w, h, alpha * show, ang, show)


def _paste(d, pic, S, cx, by, w, h, alpha, ang, show):
    from PIL import Image
    (x0, y0), (x1, y1) = S(cx - w / 2, by + h), S(cx + w / 2, by)
    pw, ph = int(abs(x1 - x0)), int(abs(y1 - y0))
    if pw < 2 or ph < 2 or not hasattr(d, "_image"):
        return
    im = pic.resize((pw, ph), Image.LANCZOS)
    if ang:
        im = im.rotate(ang, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.getchannel("A").point(lambda v: int(v * max(0.0, alpha)))
        im.putalpha(a)
    d._image.paste(im, (int(min(x0, x1) - (im.width - pw) / 2), int(min(y0, y1) - (im.height - ph) / 2)), im)
