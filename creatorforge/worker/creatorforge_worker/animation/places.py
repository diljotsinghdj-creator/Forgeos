"""Any building or place a script names, anywhere in the world, drawn as a recognisable structure - not a box.

    compose("the Indian parliament")            -> a legislature: portico, columns, a round chamber, Indian palette
    compose("Supreme Court", region="us")       -> a neoclassical court with a pediment
    compose("Jama Masjid")                      -> a mosque: domes and minarets
    compose("a factory in Ohio")                -> sawtooth roof and chimneys
    compose("Tokyo station")                    -> a station hall in East Asian colours

Two decisions, both from the words (any language the script uses: English, Hinglish and Hindi keywords, place
names of countries and big cities, so "Lok Sabha", "Nirvachan Sadan", "Kremlin" or "Capitol" all work):

* what it is   one of ~30 archetypes - legislature/civic, court, palace, fort/castle, temple, mosque, church,
               gurdwara, synagogue, pagoda/monastery, stupa, modern tower/office/bank, school/university, hospital,
               station, airport, port, factory, power plant, dam, bridge, stadium, market, cinema/theatre,
               police/prison, monument/memorial/gate, pyramid, village/huts, camp/tents, apartments, farm/barn,
               house - and a plain civic building for any other "building", "office", "commission", "bhavan"...
* how it looks the architecture of where it is: South Asian, East Asian, Southeast Asian, Middle Eastern,
               European, Russian/Eastern European, North American, Latin American, African, or modern - from the
               phrase, else the script's region (`region=`), else modern.

Every structure carries its name on a plaque (`board` part), so a viewer reads what it is, and it is an
illustration (no real building is copied; national flags and emblems are never drawn - a plain pennant at most).
The parts obey the asset rules (asset_lib.validate): closed shapes, all parts touching, standing on the ground."""
from __future__ import annotations

import math
import re

# ---- regions -----------------------------------------------------------------------------------------------------
REGION_WORDS = {
    "south_asia": r"india|indian|bharat|delhi|mumbai|bombay|kolkata|calcutta|chennai|madras|bengaluru|bangalore|"
                  r"hyderabad|lucknow|patna|jaipur|ahmedabad|pune|bhopal|kerala|punjab|bihar|gujarat|bengal|varanasi|"
                  r"banaras|agra|amritsar|ayodhya|kanpur|indore|nagpur|surat|kochi|goa|assam|odisha|kashmir|"
                  r"srinagar|chandigarh|rajasthan|madhya pradesh|uttar pradesh|maharashtra|tamil|karnataka|"
                  r"telangana|andhra|haryana|jharkhand|uttarakhand|"
                  r"pakistan|lahore|karachi|islamabad|bangladesh|dhaka|nepal|kathmandu|sri lanka|colombo|bhutan|"
                  r"lok sabha|rajya sabha|vidhan|sansad|bhavan|bhawan|sadan|mahal|qila|kila|mandir|gurdwara|"
                  r"भारत|दिल्ली|संसद|भवन|सदन|मंदिर|मस्जिद",
    "east_asia": r"china|chinese|beijing|shanghai|hong kong|taiwan|taipei|japan|japanese|tokyo|kyoto|osaka|korea|"
                 r"korean|seoul|pyongyang|mongolia",
    "southeast_asia": r"thailand|thai|bangkok|vietnam|hanoi|saigon|cambodia|laos|myanmar|burma|yangon|malaysia|"
                      r"kuala lumpur|singapore|indonesia|jakarta|bali|philippines|manila",
    "middle_east": r"arab|saudi|riyadh|mecca|makkah|medina|uae|emirates|dubai|abu dhabi|qatar|doha|kuwait|bahrain|"
                   r"oman|yemen|iran|tehran|iraq|baghdad|syria|damascus|lebanon|beirut|jordan|amman|israel|"
                   r"jerusalem|tel aviv|gaza|palestin\w*|turkey|turkish|istanbul|ankara|egypt|cairo|afghanistan|kabul|"
                   r"morocco|algeria|tunisia|libya",
    "russia": r"russia|russian|moscow|kremlin|st\.? petersburg|ukraine|kyiv|kiev|belarus|minsk|soviet|serbia|"
              r"belgrade|bulgaria|romania",
    "europe": r"europe|european|britain|british|uk\b|england|london|scotland|wales|ireland|dublin|france|french|"
              r"paris|germany|german|berlin|italy|italian|rome|spain|spanish|madrid|portugal|lisbon|netherlands|"
              r"dutch|amsterdam|belgium|brussels|switzerland|geneva|austria|vienna|poland|warsaw|czech|prague|"
              r"hungary|budapest|greece|athens|sweden|stockholm|norway|oslo|denmark|finland|westminster|vatican",
    "north_america": r"\busa?\b|united states|america\b|american|washington|new york|capitol|congress|senate|"
                     r"white house|california|texas|chicago|canada|canadian|ottawa|toronto",
    "latin_america": r"mexico|mexican|brazil|brasilia|rio|sao paulo|argentina|buenos aires|chile|santiago|peru|"
                     r"lima|colombia|bogota|venezuela|caracas|cuba|havana|bolivia|ecuador|quito|uruguay",
    "africa": r"africa|african|nigeria|lagos|abuja|kenya|nairobi|ethiopia|addis|ghana|accra|south africa|"
              r"johannesburg|cape town|pretoria|tanzania|uganda|kampala|rwanda|kigali|senegal|dakar|mali|timbuktu|"
              r"congo|kinshasa|sudan|khartoum|zimbabwe|zambia|mozambique|cameroon|ivory coast",
}
def _words(rx: str) -> re.Pattern:
    """Whole words for Latin script (with an optional plural: "temples", "factories"), so "small" is not a mall and
    "woman" is not Oman; Devanagari keys still match inside words (vowel signs are not word characters)."""
    return re.compile(r"(?<![A-Za-z])(?:" + rx + r")(?:e?s)?(?![A-Za-z])", re.I)


_REGION_RX = {k: _words(v) for k, v in REGION_WORDS.items()}

# per region: wall, trim, roof, dome, accent, window, dome shape, roof shape
STYLES = {
    "south_asia":     dict(wall=(214, 150, 112), trim=(246, 236, 218), roof=(176, 98, 70), dome=(244, 238, 226),
                           accent=(222, 140, 50), win=(92, 70, 60), dome_kind="bulb", roof_kind="flat"),
    "east_asia":      dict(wall=(196, 64, 52), trim=(236, 214, 150), roof=(52, 86, 84), dome=(52, 86, 84),
                           accent=(230, 180, 60), win=(70, 46, 40), dome_kind="half", roof_kind="eaves"),
    "southeast_asia": dict(wall=(236, 214, 170), trim=(214, 170, 70), roof=(176, 60, 46), dome=(214, 170, 70),
                           accent=(70, 110, 160), win=(90, 64, 46), dome_kind="bell", roof_kind="eaves"),
    "middle_east":    dict(wall=(228, 206, 164), trim=(246, 238, 220), roof=(196, 170, 120), dome=(60, 140, 150),
                           accent=(212, 170, 70), win=(70, 90, 110), dome_kind="bulb", roof_kind="flat"),
    "russia":         dict(wall=(206, 82, 66), trim=(244, 240, 230), roof=(70, 110, 90), dome=(214, 172, 60),
                           accent=(60, 120, 90), win=(60, 70, 90), dome_kind="onion", roof_kind="pitched"),
    "europe":         dict(wall=(206, 200, 188), trim=(236, 232, 222), roof=(84, 92, 110), dome=(120, 150, 140),
                           accent=(150, 60, 50), win=(70, 90, 120), dome_kind="half", roof_kind="pitched"),
    "north_america":  dict(wall=(238, 236, 228), trim=(250, 250, 246), roof=(150, 154, 160), dome=(244, 244, 240),
                           accent=(60, 80, 130), win=(70, 90, 120), dome_kind="half", roof_kind="flat"),
    "latin_america":  dict(wall=(240, 204, 120), trim=(250, 244, 230), roof=(188, 90, 60), dome=(70, 130, 170),
                           accent=(60, 140, 120), win=(80, 60, 50), dome_kind="half", roof_kind="tile"),
    "africa":         dict(wall=(196, 136, 86), trim=(226, 186, 130), roof=(150, 110, 70), dome=(186, 126, 80),
                           accent=(200, 90, 50), win=(70, 50, 40), dome_kind="half", roof_kind="flat"),
    "modern":         dict(wall=(196, 202, 210), trim=(236, 238, 242), roof=(110, 116, 126), dome=(150, 170, 190),
                           accent=(60, 120, 190), win=(120, 160, 196), dome_kind="half", roof_kind="flat"),
}


# a structure that by itself says where its architecture comes from (when nothing else does)
KIND_REGION = {"mosque": "middle_east", "gurdwara": "south_asia", "temple": "south_asia", "pagoda": "east_asia",
               "stupa": "southeast_asia", "church": "europe", "synagogue": "europe", "pyramid": "middle_east"}


def region_of(*texts: str) -> str:
    """The architecture region named in any of the texts (the phrase first), else 'modern'."""
    for text in texts:
        if not text:
            continue
        for name, rx in _REGION_RX.items():
            if rx.search(text):
                return name
        if re.search(r"[\u0900-\u097F]", text):     # written in Devanagari: South Asia
            return "south_asia"
    return "modern"


# ---- what it is ---------------------------------------------------------------------------------------------------
KINDS = [  # (archetype, keywords) - first match wins, so specific before general
    ("stupa", r"stupa|pagoda of|dagoba"),
    ("pagoda", r"pagoda|monastery|buddhist temple|vihara|wat\b|shinto|shrine of japan"),
    ("mosque", r"mosque|masjid|dargah|minaret|मस्जिद"),
    ("gurdwara", r"gurdwara|gurudwara|golden temple|गुरुद्वारा"),
    ("church", r"church|cathedral|chapel|basilica|abbey|chirch"),
    ("synagogue", r"synagogue"),
    ("temple", r"temple|mandir|shrine|devalaya|kovil|मंदिर"),
    ("court", r"supreme court|high court|court|tribunal|अदालत|न्यायालय"),
    ("legislature", r"parliament|lok sabha|rajya sabha|vidhan sabha|vidhan sabha|assembly|congress|capitol|senate|"
                    r"legislat\w*|sansad|knesset|duma|reichstag|bundestag|diet\b|majlis|national assembly|संसद|सदन"),
    ("tomb", r"tomb|mausoleum|maqbara|मकबरा"),
    ("palace", r"palace|mahal|white house|rashtrapati bhavan|raj bhavan|presidential|residence of|kremlin|"
               r"महल|भवन"),
    ("fort", r"fort\b|fortress|castle|citadel|qila|kila|किला"),
    ("pyramid", r"pyramid"),
    ("monument", r"monument|memorial|statue|gate\b|gateway|arch\b|triumphal|obelisk|minar\b|pillar|tomb|"
                 r"mausoleum|cenotaph|smarak|स्मारक"),
    ("police", r"police station|police chowki|police|thana|jail|prison|penitentiary|lock-?up|पुलिस|जेल"),
    ("power", r"power plant|power station|nuclear|reactor|thermal plant|coal plant"),
    ("dam", r"\bdam\b|barrage|reservoir"),
    ("bridge", r"bridge|flyover|overpass|पुल"),
    ("airport", r"airport|airfield|aerodrome|हवाई अड्डा"),
    ("station", r"station|terminal|terminus|railway|metro|depot|स्टेशन"),
    ("port", r"\bport\b|harbou?r|dock|shipyard|jetty"),
    ("stadium", r"stadium|arena|cricket ground|olympic|football ground|sports complex|स्टेडियम"),
    ("hospital", r"hospital|clinic|medical college|aiims|health cent\w*|dispensary|अस्पताल"),
    ("school", r"school|college|university|institute|academy|campus|iit\b|iim\b|library|विद्यालय|स्कूल"),
    ("cinema", r"cinema|theatre|theater|opera|concert hall|multiplex"),
    ("market", r"market|bazaa?r|mandi|souk|mall|marketplace|बाज़ार|बाजार|मंडी"),
    ("factory", r"factory|factories|plant\b|mill\b|refinery|workshop|warehouse|industr\w*|foundry|कारखाना|फ़ैक्टरी"),
    ("tower", r"skyscraper|tower|headquarters|\bhq\b|bank\b|exchange|corporate|tech park|it park|office block|"
              r"trade cent\w*"),
    ("apartments", r"apartment|flats\b|housing|residential|society\b|tenement|chawl"),
    ("village", r"village|hut\b|huts|slum|basti|colony|settlement|गाँव|गांव"),
    ("camp", r"refugee camp|camp\b|tents?\b|shelter"),
    ("farm", r"farm|barn|field|orchard|खेत"),
    ("civic", r"building|office|ministry|secretariat|commission|council|municipal|city hall|town hall|embassy|"
              r"consulate|department|bureau|agency|board\b|authority|cent(?:re|er)\b|hall\b|complex|bhavan|"
              r"bhawan|sadan|niwas|nivas|headquarter|कार्यालय|दफ़्तर|आयोग"),
]
_KIND_RX = [(k, _words(rx)) for k, rx in KINDS]


def _core(phrase: str) -> str:
    """The noun phrase that names the thing: before 'in/of/at...' or a bracket, without trailing place names
    ("the parliament in Delhi" -> "the parliament", "IIT Delhi" -> "IIT", "Supreme Court" stays)."""
    core = re.split(r"\s+(?:in|at|of|near|from|on|outside|inside)\s+|\s*[(,]", phrase.strip(), maxsplit=1)[0].strip()
    words = core.split()
    while len(words) > 1 and any(rx.fullmatch(words[-1]) for rx in _REGION_RX.values()) and \
            not any(rx.fullmatch(words[-1]) for _, rx in _KIND_RX):   # "US Capitol" keeps its Capitol
        words.pop()
    return " ".join(words)


def kind_of(phrase: str) -> str | None:
    """The structure the phrase names - its last word decides ("court order" is a document, "Supreme Court" a
    court); Devanagari phrases match anywhere."""
    core = _core(phrase)
    deva = bool(re.search(r"[\u0900-\u097F]", core))
    for k, rx in _KIND_RX:
        for m in rx.finditer(core):
            if deva or m.end() >= len(core.rstrip(" .!?'\"")):
                return k
    return None


def is_structure(phrase: str) -> bool:
    return kind_of(phrase) is not None


# ---- drawing kit --------------------------------------------------------------------------------------------------
class _B:
    """Collects parts with unique ids; everything in metres, origin at the bottom centre."""

    def __init__(self, st):
        self.parts, self.st, self.n = [], st, 0

    def _id(self, base):
        self.n += 1
        return f"{base}{self.n}"

    def poly(self, base, pts, fill, z=0):
        from .asset_lib import poly
        self.parts.append(poly(self._id(base), pts, fill, z))

    def rect(self, base, x0, y0, x1, y1, fill, z=0):
        self.poly(base, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, z)

    def circle(self, base, cx, cy, r, fill, z=0):
        from .asset_lib import circle
        self.parts.append(circle(self._id(base), cx, cy, r, fill, z))

    def line(self, base, pts, fill, width, z=0):
        from .asset_lib import line
        self.parts.append(line(self._id(base), pts, fill, width, z))

    # -- pieces --
    def windows(self, x0, x1, y0, y1, rows, cols, arched=False, z=2, fill=None):
        fill = fill or self.st["win"]
        cw, rh = (x1 - x0) / cols, (y1 - y0) / rows
        for r in range(rows):
            for c in range(cols):
                a, b = x0 + c * cw + cw * 0.28, x0 + (c + 1) * cw - cw * 0.28
                lo, hi = y0 + r * rh + rh * 0.22, y0 + (r + 1) * rh - rh * 0.18
                if arched:
                    mid, rad = (a + b) / 2, (b - a) / 2
                    top = hi - rad
                    pts = [(a, lo), (b, lo), (b, top)] + [(mid + rad * math.cos(t_), top + rad * math.sin(t_))
                                                          for t_ in [math.pi * i / 8 for i in range(1, 8)]] + [(a, top)]
                    self.poly("win", pts, fill, z)
                else:
                    self.rect("win", a, lo, b, hi, fill, z)

    def door(self, cx, w, h, z=3, arched=True):
        a, b = cx - w / 2, cx + w / 2
        if arched:
            top = h - w / 2
            pts = [(a, 0), (b, 0), (b, top)] + [(cx + w / 2 * math.cos(math.pi * i / 8), top + w / 2 * math.sin(math.pi * i / 8))
                                                for i in range(1, 8)] + [(a, top)]
            self.poly("door", pts, (92, 64, 46), z)
        else:
            self.rect("door", a, 0, b, h, (92, 64, 46), z)

    def columns(self, x0, x1, y0, y1, n, z=3):
        st = self.st
        cw = (x1 - x0) / (n * 2 - 1)
        for i in range(n):
            a = x0 + i * 2 * cw
            self.rect("col", a, y0, a + cw, y1, st["trim"], z)
        self.rect("beam", x0 - cw * 0.4, y1, x1 + cw * 0.4, y1 + cw * 1.1, st["trim"], z)
        return y1 + cw * 1.1

    def pediment(self, x0, x1, y, h, z=3):
        self.poly("pediment", [(x0, y), (x1, y), ((x0 + x1) / 2, y + h)], self.st["trim"], z)

    def dome(self, cx, y, r, kind=None, z=4, fill=None, finial=True):
        kind = kind or self.st["dome_kind"]
        fill = fill or self.st["dome"]
        if kind == "onion":
            pts = [(cx - r * 0.8, y)]
            for i in range(1, 12):
                u = i / 12
                bulge = math.sin(math.pi * min(1.0, u * 1.35)) * (1 - u) ** 0.6
                pts.append((cx - r * (0.8 * (1 - u) + 0.5 * bulge), y + r * 2.0 * u))
            top = (cx, y + r * 2.15)
            pts = pts + [top] + [(2 * cx - x_, y_) for x_, y_ in reversed(pts)]
            self.poly("dome", pts, fill, z)
            tip = y + r * 2.15
        elif kind == "bulb":                          # Mughal / Islamic: swells, then rises to a point
            right = []
            for i in range(11):
                v = i / 10
                wid = r * (0.92 + 0.22 * math.sin(math.pi * v * 0.8)) * (1 - v) ** 0.6
                right.append((cx + wid, y + r * 1.45 * v))
            pts = right + [(2 * cx - x_, y_) for x_, y_ in reversed(right[:-1])]
            self.poly("dome", pts, fill, z)
            tip = y + r * 1.45
        elif kind == "bell":                         # a stupa / Southeast Asian bell with a spire
            pts = [(cx - r, y), (cx + r, y)] + [(cx + r * math.cos(math.pi * i / 12), y + r * 0.9 * math.sin(math.pi * i / 12))
                                               for i in range(1, 12)]
            self.poly("dome", pts, fill, z)
            self.poly("spire", [(cx - r * 0.18, y + r * 0.88), (cx + r * 0.18, y + r * 0.88), (cx, y + r * 2.2)],
                      self.st["trim"], z + 1)
            return y + r * 2.2
        else:                                        # a half dome on its drum
            pts = [(cx + r * math.cos(math.pi * i / 16), y + r * math.sin(math.pi * i / 16)) for i in range(17)]
            self.poly("dome", pts, fill, z)
            tip = y + r
        if finial:
            self.line("finial", [(cx, tip - 0.02), (cx, tip + r * 0.35)], self.st["accent"], max(0.06, r * 0.08), z + 1)
            return tip + r * 0.35
        return tip

    def minaret(self, cx, h, w, z=1):
        st = self.st
        self.rect("minaret", cx - w / 2, 0, cx + w / 2, h, st["trim"], z)
        self.rect("balcony", cx - w * 0.85, h * 0.7, cx + w * 0.85, h * 0.74, st["accent"], z + 1)
        self.dome(cx, h, w * 0.75, "bulb" if st["dome_kind"] != "onion" else "onion", z + 1, finial=False)

    def spire(self, cx, y, w, h, z=4):
        self.poly("spire", [(cx - w / 2, y), (cx + w / 2, y), (cx, y + h)], self.st["roof"], z)

    def pitched(self, x0, x1, y, h, z=4, fill=None):
        self.poly("roof", [(x0 - 0.3, y), (x1 + 0.3, y), ((x0 + x1) / 2, y + h)], fill or self.st["roof"], z)

    def eaves(self, x0, x1, y, h, z=4, fill=None):
        """An East Asian roof: wide eaves whose tips turn up."""
        fill = fill or self.st["roof"]
        o = (x1 - x0) * 0.16
        self.poly("eave", [(x0 - o, y + h * 0.3), (x0 - o * 0.6, y), (x1 + o * 0.6, y), (x1 + o, y + h * 0.3),
                           (x1 - o * 0.3, y + h * 0.5), ((x0 + x1) / 2 + (x1 - x0) * 0.18, y + h),
                           ((x0 + x1) / 2 - (x1 - x0) * 0.18, y + h), (x0 + o * 0.3, y + h * 0.5)], fill, z)

    def roof(self, x0, x1, y, h, z=4):
        k = self.st["roof_kind"]
        if k == "eaves":
            self.eaves(x0, x1, y, h, z)
        elif k in ("pitched", "tile"):
            self.pitched(x0, x1, y, h * 0.8, z)
        else:
            self.rect("parapet", x0 - 0.15, y, x1 + 0.15, y + h * 0.18, self.st["trim"], z)

    def battlements(self, x0, x1, y, size, z=3):
        n = max(3, int((x1 - x0) / (size * 2)))
        step = (x1 - x0) / n
        for i in range(n):
            a = x0 + i * step
            self.rect("merlon", a, y, a + step * 0.55, y + size, self.st["wall"], z)

    def plaque(self, cx, y, w, z=6):
        from .asset_lib import rect                   # id "board": the renderer writes the name on it
        self.parts.append(rect("board", cx - w / 2, y, cx + w / 2, y + min(w * 0.22, 1.0), (250, 246, 236), z))

    def pennant(self, x, y, h=1.2, z=6):
        self.line("pole", [(x, y), (x, y + h)], (90, 90, 96), 0.06, z)
        self.poly("pennant", [(x, y + h), (x + h * 0.45, y + h * 0.88), (x, y + h * 0.76)], self.st["accent"], z + 1)


# ---- archetypes ---------------------------------------------------------------------------------------------------
def _legislature(B, s):
    st = B.st
    w, h = 13 * s, 4.6 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.4, -w * 0.2, 0.3, h - 0.4, 2, 3, arched=st["dome_kind"] != "half")
    B.windows(w * 0.2, w / 2 - 0.4, 0.3, h - 0.4, 2, 3, arched=st["dome_kind"] != "half")
    top = B.columns(-w * 0.18, w * 0.18, 0, h * 0.86, 6)
    B.pediment(-w * 0.21, w * 0.21, top, h * 0.32)
    B.rect("drum", -w * 0.13, h, w * 0.13, h + 1.1 * s, st["trim"], 1)
    B.dome(0, h + 1.1 * s, w * 0.13)
    B.roof(-w / 2, w / 2, h, 0.9 * s, 1)
    B.plaque(0, h * 0.06, w * 0.24)
    B.door(0, w * 0.06, h * 0.5)


def _court(B, s):
    st = B.st
    w, h = 12 * s, 5.0 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.rect("steps", -w * 0.36, 0, w * 0.36, 0.45 * s, st["trim"], 4)
    top = B.columns(-w * 0.34, w * 0.34, 0.45 * s, h * 0.92, 8)
    B.pediment(-w * 0.38, w * 0.38, top, h * 0.34)
    B.plaque(0, top + h * 0.06, w * 0.22, z=7)
    if st["dome_kind"] != "half" or st["_region"] == "north_america":
        B.rect("drum", -w * 0.1, top + h * 0.3, w * 0.1, top + h * 0.3 + 0.9 * s, st["trim"], 1)
        B.dome(0, top + h * 0.3 + 0.9 * s, w * 0.1)


def _palace(B, s):
    st = B.st
    w, h = 15 * s, 4.4 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.3, h - 0.3, 2, 9, arched=True)
    B.rect("centre", -w * 0.16, 0, w * 0.16, h * 1.25, st["trim"], 1)
    B.door(0, w * 0.07, h * 0.55)
    B.dome(0, h * 1.25, w * 0.13)
    for sx in (-1, 1):
        B.rect("wing", sx * w * 0.5 - (0 if sx > 0 else 0), 0, sx * w * 0.38, h * 1.12, st["trim"], 1)
        B.dome(sx * w * 0.44, h * 1.12, w * 0.05, z=5, finial=False)
    B.roof(-w / 2, w / 2, h, 0.8 * s, 2)
    B.plaque(0, h * 0.62, w * 0.14, z=7)


def _fort(B, s):
    st = B.st
    w, h = 15 * s, 4.6 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.battlements(-w / 2, w / 2, h, 0.5 * s)
    for sx in (-1, 1):
        B.rect("tower", sx * w / 2 - 1.4 * s, 0, sx * w / 2 + 1.4 * s, h * 1.35, st["wall"], 1)
        if st["dome_kind"] in ("bulb", "onion"):
            B.dome(sx * w / 2, h * 1.35, 1.1 * s, z=2, finial=False)
        else:
            B.battlements(sx * w / 2 - 1.4 * s, sx * w / 2 + 1.4 * s, h * 1.35, 0.45 * s, z=2)
    B.door(0, 2.2 * s, h * 0.7)
    B.plaque(0, h * 0.78, w * 0.16, z=7)


def _temple(B, s):
    st = B.st
    reg = st.get("_region")
    if reg in ("east_asia", "southeast_asia"):
        return _pagoda(B, s)
    if reg in ("europe", "north_america") and st["dome_kind"] == "half":     # a classical temple
        w, h = 11 * s, 4.0 * s
        B.rect("base", -w / 2, 0, w / 2, 0.6 * s, st["trim"], 0)
        top = B.columns(-w * 0.44, w * 0.44, 0.6 * s, h, 7)
        B.pediment(-w * 0.48, w * 0.48, top, h * 0.32)
        B.plaque(0, 0.0, w * 0.2, z=7)
        return
    w, h = 9 * s, 3.4 * s                            # a mandir: hall, porch and a curved tower (shikhara)
    B.rect("base", -w / 2, 0, w / 2, 0.6 * s, st["trim"], 0)
    B.rect("hall", -w / 2 + 0.4, 0.6 * s, w * 0.1, h, st["wall"], 1)
    B.door(-w * 0.18, 1.0 * s, h * 0.6, z=4)
    cx, base = w * 0.24, 0.6 * s
    tw, th = 3.6 * s, 6.6 * s
    pts = [(cx - tw / 2, base), (cx + tw / 2, base)]
    for i in range(1, 11):
        u = i / 10
        pts.append((cx + tw / 2 * (1 - u ** 1.7) * (1 - 0.15 * u), base + th * u))
    pts = pts + [(2 * cx - x_, y_) for x_, y_ in reversed(pts[2:-1])]
    B.poly("shikhara", pts, st["wall"], 2)
    B.circle("amalaka", cx, base + th + 0.25 * s, 0.4 * s, st["trim"], 3)
    B.pennant(cx, base + th + 0.55 * s, 1.1 * s)
    B.roof(-w / 2 + 0.4, w * 0.1, h, 0.8 * s, 2)
    B.plaque(-w * 0.18, h * 0.72, w * 0.26, z=6)


def _pagoda(B, s):
    st = B.st
    w, tiers = 7 * s, 4
    y = 0.0
    B.rect("base", -w / 2, 0, w / 2, 0.5 * s, st["trim"], 0)
    y = 0.5 * s
    for i in range(tiers):
        tw = w * (0.8 - 0.14 * i)
        hh = 1.5 * s * (1 - 0.1 * i)
        B.rect("storey", -tw / 2, y - 0.02, tw / 2, y + hh, st["wall"], 1 + 2 * i)
        if i == 0:
            B.door(0, 0.9 * s, hh * 0.85, z=2)
        B.eaves(-tw / 2, tw / 2, y + hh - 0.05, 0.9 * s, z=2 + 2 * i)
        y += hh + 0.45 * s
    B.line("finial", [(0, y - 0.1), (0, y + 1.6 * s)], st["accent"], 0.12 * s, 20)
    B.plaque(0, 0.0, w * 0.3, z=7)


def _stupa(B, s):
    st = B.st
    w = 8 * s
    B.rect("base", -w / 2, 0, w / 2, 0.9 * s, st["trim"], 0)
    B.dome(0, 0.9 * s, w * 0.36, "bell", z=1)
    B.plaque(0, 0.1 * s, w * 0.3, z=6)


def _mosque(B, s):
    st = B.st
    w, h = 12 * s, 3.8 * s
    B.rect("hall", -w * 0.36, 0, w * 0.36, h, st["wall"], 0)
    B.windows(-w * 0.34, w * 0.34, 0.4, h - 0.3, 1, 5, arched=True)
    B.rect("iwan", -w * 0.11, 0, w * 0.11, h * 1.25, st["trim"], 1)
    B.door(0, w * 0.1, h * 0.85, z=2)
    B.dome(0, h * 1.25, w * 0.14, "bulb" if st["dome_kind"] != "onion" else "onion", z=2)
    for sx in (-1, 1):
        B.dome(sx * w * 0.25, h, w * 0.07, "bulb", z=2, finial=False)
        B.minaret(sx * (w * 0.36 + 0.55 * s), h * 2.1, 0.8 * s, z=1)
    B.plaque(0, h * 0.94, w * 0.16, z=7)


def _gurdwara(B, s):
    B.st = dict(B.st, wall=(244, 242, 236), dome=(222, 182, 70))
    w, h = 10 * s, 4.0 * s
    st = B.st
    B.rect("hall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.3, h - 0.3, 1, 7, arched=True)
    B.dome(0, h, w * 0.2, "bulb", z=2)
    for sx in (-1, 1):
        B.dome(sx * w * 0.4, h, w * 0.06, "bulb", z=2, finial=False)
    B.pennant(w / 2 + 0.6 * s, 0, 5.5 * s)
    B.rect("plinth", w / 2, 0, w / 2 + 1.2 * s, 0.4 * s, st["trim"], 1)
    B.plaque(0, h * 0.55, w * 0.2, z=7)


def _church(B, s):
    st = B.st
    w, h = 8 * s, 4.6 * s
    B.rect("nave", -w / 2, 0, w * 0.2, h, st["wall"], 0)
    B.pitched(-w / 2, w * 0.2, h, 2.4 * s, z=1)
    B.windows(-w / 2 + 0.3, w * 0.15, 0.6, h - 0.4, 1, 3, arched=True)
    B.rect("tower", w * 0.2, 0, w / 2, h * 1.55, st["wall"], 1)
    B.door(w * 0.35, 1.0 * s, 2.2 * s, z=3)
    if st["dome_kind"] == "onion":
        B.dome(w * 0.35, h * 1.55, 0.9 * s, "onion", z=2)
    else:
        B.spire(w * 0.35, h * 1.55, (w * 0.3), 3.6 * s, z=2)
    B.circle("rose", w * 0.35, h * 1.2, 0.5 * s, st["win"], 3)
    B.plaque(-w * 0.15, h * 0.06, w * 0.34, z=7)


def _synagogue(B, s):
    st = B.st
    w, h = 9 * s, 5.0 * s
    B.rect("hall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.6, h - 0.4, 2, 5, arched=True)
    B.door(0, 1.4 * s, 2.6 * s, z=3)
    B.roof(-w / 2, w / 2, h, 1.2 * s, 1)
    B.plaque(0, h * 0.62, w * 0.3, z=7)


def _tower(B, s):
    st = B.st
    w, h = 6 * s, 15 * s
    B.rect("body", -w / 2, 0, w / 2, h, (130, 160, 190) if st["_region"] == "modern" else st["wall"], 0)
    B.windows(-w / 2 + 0.2, w / 2 - 0.2, 1.2 * s, h - 0.4, 14, 4, fill=(186, 214, 236))
    B.rect("lobby", -w * 0.3, 0, w * 0.3, 1.2 * s, (60, 70, 86), 2)
    B.rect("crown", -w * 0.3, h, w * 0.3, h + 0.8 * s, st["trim"], 1)
    B.line("mast", [(0, h + 0.75 * s), (0, h + 2.6 * s)], (90, 96, 106), 0.1 * s, 2)
    B.plaque(0, 1.25 * s, w * 0.5, z=4)


def _school(B, s):
    st = B.st
    w, h = 13 * s, 4.4 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.3, h - 0.3, 2, 8)
    B.rect("entrance", -w * 0.12, 0, w * 0.12, h * 1.3, st["trim"], 1)
    B.door(0, w * 0.08, h * 0.5, z=3)
    B.circle("clock", 0, h * 1.05, 0.45 * s, (250, 250, 246), 3)
    B.roof(-w / 2, w / 2, h, 1.0 * s, 1)
    B.pennant(w * 0.12 - 0.1, h * 1.3, 1.6 * s)
    B.plaque(0, h * 0.62, w * 0.2, z=7)


def _hospital(B, s):
    st = B.st
    w, h = 12 * s, 6 * s
    B.rect("wall", -w / 2, 0, w / 2, h, (240, 242, 244), 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 1.4 * s, h - 0.3, 3, 8, fill=(150, 196, 220))
    B.rect("canopy", -w * 0.2, 1.3 * s, w * 0.2, 1.55 * s, st["accent"], 2)
    B.door(0, w * 0.12, 1.3 * s, arched=False, z=3)
    B.rect("sign", -0.55 * s, h - 0.05, 0.55 * s, h + 1.1 * s, (60, 140, 90), 1)     # an "H" panel, not a red cross
    B.rect("h1", -0.3 * s, h + 0.15 * s, -0.15 * s, h + 0.9 * s, (250, 250, 250), 2)
    B.rect("h2", 0.15 * s, h + 0.15 * s, 0.3 * s, h + 0.9 * s, (250, 250, 250), 2)
    B.rect("h3", -0.15 * s, h + 0.45 * s, 0.15 * s, h + 0.6 * s, (250, 250, 250), 2)
    B.plaque(0, 1.6 * s, w * 0.3, z=4)


def _station(B, s):
    st = B.st
    w, h = 15 * s, 3.6 * s
    B.rect("hall", -w / 2, 0, w / 2, h, st["wall"], 0)
    pts = [(-w * 0.4, h)] + [(w * 0.4 * math.cos(math.pi * (1 - i / 16)), h + 2.4 * s * math.sin(math.pi * i / 16))
                             for i in range(1, 16)] + [(w * 0.4, h)]
    B.poly("vault", pts, st["roof"], 1)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.3, h - 0.3, 1, 7, arched=True)
    B.rect("clocktower", w * 0.42, 0, w / 2 + 0.6 * s, h * 2.0, st["trim"], 2)
    B.circle("clock", w * 0.46 + 0.3 * s, h * 1.7, 0.5 * s, (250, 250, 246), 3)
    B.plaque(-w * 0.05, h * 0.62, w * 0.3, z=6)


def _airport(B, s):
    w, h = 16 * s, 3.2 * s
    B.rect("terminal", -w / 2, 0, w * 0.3, h, (210, 216, 224), 0)
    B.poly("roof", [(-w / 2 - 0.4, h), (w * 0.3 + 0.4, h), (w * 0.3, h + 0.9 * s), (-w / 2, h + 0.5 * s)],
           (150, 156, 166), 1)
    B.windows(-w / 2 + 0.2, w * 0.28, 0.2, h - 0.2, 1, 10, fill=(170, 206, 232))
    B.rect("ctower", w * 0.36, 0, w * 0.42, h * 2.6, (220, 224, 230), 1)
    B.poly("cab", [(w * 0.33, h * 2.6), (w * 0.45, h * 2.6), (w * 0.47, h * 3.0), (w * 0.31, h * 3.0)],
           (120, 170, 210), 2)
    B.plaque(-w * 0.1, h * 0.55, w * 0.3, z=4)


def _port(B, s):
    w = 15 * s
    B.rect("quay", -w / 2, 0, w / 2, 0.8 * s, (150, 150, 156), 0)
    B.rect("shed", -w / 2, 0.8 * s, -w * 0.05, 3.6 * s, (196, 120, 80), 1)
    for i, c in enumerate([(200, 70, 60), (60, 110, 180), (70, 150, 90)]):
        B.rect("container", w * 0.02 + i * 1.5 * s, 0.8 * s, w * 0.02 + i * 1.5 * s + 1.4 * s, 2.2 * s, c, 2)
    B.rect("crane", w * 0.36, 0.8 * s, w * 0.39, 7.5 * s, (230, 180, 50), 3)
    B.rect("jib", w * 0.02, 7.2 * s, w / 2, 7.6 * s, (230, 180, 50), 3)
    B.plaque(-w * 0.27, 2.2 * s, w * 0.3, z=4)


def _factory(B, s):
    st = B.st
    w, h = 14 * s, 4.0 * s
    B.rect("shed", -w / 2, 0, w / 2, h, (176, 170, 164) if st["_region"] == "modern" else st["wall"], 0)
    n = 4
    step = w / n
    for i in range(n):
        a = -w / 2 + i * step
        B.poly("sawtooth", [(a, h), (a + step, h), (a + step, h + 1.6 * s)], st["roof"], 1)
    for k, x in enumerate((w * 0.18, w * 0.36)):
        B.rect("chimney", x - 0.35 * s, h, x + 0.35 * s, h + (5.5 - k) * s, (150, 80, 66), 2)
    B.door(-w * 0.3, 2.4 * s, 3.0 * s, z=3, arched=False)
    B.windows(-w * 0.15, w / 2 - 0.3, 1.0, h - 0.4, 1, 6)
    B.plaque(w * 0.05, h * 0.82, w * 0.3, z=4)


def _power(B, s):
    w = 15 * s
    for k, x in enumerate((-w * 0.3, -w * 0.05)):
        tw, th = 4.0 * s, 8.0 * s
        B.poly("cooling", [(x - tw / 2, 0), (x + tw / 2, 0), (x + tw * 0.3, th * 0.6), (x + tw * 0.38, th),
                           (x - tw * 0.38, th), (x - tw * 0.3, th * 0.6)], (200, 200, 204), k)
    B.rect("hall", w * 0.08, 0, w / 2, 4.0 * s, (170, 176, 186), 2)
    B.rect("stack", w * 0.4, 4.0 * s, w * 0.44, 9.0 * s, (190, 90, 70), 3)
    B.plaque(w * 0.28, 2.0 * s, w * 0.26, z=4)


def _dam(B, s):
    w, h = 16 * s, 6.0 * s
    B.poly("wall", [(-w / 2, 0), (w / 2, 0), (w / 2 - 1.2 * s, h), (-w / 2 + 1.2 * s, h)], (176, 176, 170), 0)
    B.rect("water", -w / 2 + 1.2 * s, h - 0.1, w / 2 - 1.2 * s, h + 0.35 * s, (80, 140, 200), 1)
    for i in range(4):
        x = -w * 0.3 + i * w * 0.2
        B.rect("gate", x - 0.5 * s, h * 0.15, x + 0.5 * s, h * 0.75, (120, 124, 130), 2)
    B.plaque(0, h * 0.78, w * 0.3, z=4)


def _bridge(B, s):
    w, h = 18 * s, 3.4 * s
    B.rect("deck", -w / 2, h, w / 2, h + 0.5 * s, (140, 140, 146), 1)
    for x in (-w * 0.3, 0.0, w * 0.3):
        B.rect("pier", x - 0.5 * s, 0, x + 0.5 * s, h, (170, 166, 160), 0)
    for x in (-w * 0.15, w * 0.15):
        B.rect("pylon", x - 0.3 * s, h + 0.5 * s, x + 0.3 * s, h + 4.0 * s, (190, 190, 196), 2)
        B.line("cable", [(x, h + 4.0 * s), (x - w * 0.14, h + 0.55 * s)], (90, 90, 100), 0.06 * s, 3)
        B.line("cable", [(x, h + 4.0 * s), (x + w * 0.14, h + 0.55 * s)], (90, 90, 100), 0.06 * s, 3)
    B.plaque(0, h + 0.5 * s, w * 0.2, z=4)


def _stadium(B, s):
    st = B.st
    w, h = 18 * s, 4.0 * s
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, h * 0.7)] + \
        [(w / 2 * math.cos(math.pi * i / 16), h * 0.7 + h * 0.5 * math.sin(math.pi * i / 16)) for i in range(1, 16)] + \
        [(-w / 2, h * 0.7)]
    B.poly("bowl", pts, st["trim"], 0)
    B.windows(-w / 2 + 0.5, w / 2 - 0.5, 0.4, h * 0.6, 1, 10, arched=True, fill=(110, 120, 140))
    for x in (-w * 0.42, w * 0.42):
        B.rect("mast", x - 0.12 * s, h * 0.7, x + 0.12 * s, h * 2.4, (120, 124, 132), 1)
        B.rect("lights", x - 0.7 * s, h * 2.4, x + 0.7 * s, h * 2.6, (250, 240, 190), 2)
    B.plaque(0, h * 0.62, w * 0.22, z=4)


def _market(B, s):
    st = B.st
    w = 13 * s
    cols = [(220, 80, 70), (60, 120, 190), (230, 170, 50), (70, 150, 90)]
    n = 4
    step = w / n
    for i in range(n):
        a = -w / 2 + i * step
        B.rect("stall", a + 0.15, 0, a + step - 0.15, 1.1 * s, (186, 140, 96), 0)
        B.line("post", [(a + 0.25, 1.1 * s), (a + 0.25, 2.3 * s)], (110, 80, 60), 0.08 * s, 1)
        B.line("post", [(a + step - 0.25, 1.1 * s), (a + step - 0.25, 2.3 * s)], (110, 80, 60), 0.08 * s, 1)
        B.poly("awning", [(a, 2.2 * s), (a + step, 2.2 * s), (a + step - 0.2, 2.9 * s), (a + 0.2, 2.9 * s)],
               cols[i % 4], 2)
    B.rect("arch", -w * 0.08, 2.9 * s - 0.05, w * 0.08, 3.6 * s, st["trim"], 3)
    B.plaque(0, 2.95 * s, w * 0.15, z=4)


def _cinema(B, s):
    st = B.st
    w, h = 11 * s, 5.0 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.rect("marquee", -w * 0.38, h * 0.55, w * 0.38, h * 0.8, (40, 40, 50), 1)
    for i in range(9):
        B.circle("bulb", -w * 0.36 + i * w * 0.09, h * 0.82, 0.1 * s, (250, 220, 120), 2)
    B.door(-w * 0.15, 1.2 * s, 2.4 * s, z=2, arched=False)
    B.door(w * 0.15, 1.2 * s, 2.4 * s, z=2, arched=False)
    B.roof(-w / 2, w / 2, h, 0.9 * s, 1)
    B.plaque(0, h * 0.6, w * 0.6, z=3)


def _police(B, s):
    st = B.st
    w, h = 11 * s, 4.0 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.6, h - 0.3, 1, 6)
    B.rect("bars", -w * 0.42, 0.7, -w * 0.28, h * 0.8, (80, 84, 92), 2)
    B.door(w * 0.2, 1.2 * s, 2.4 * s, z=2, arched=False)
    B.rect("lamp", w * 0.2 - 0.25 * s, 2.5 * s, w * 0.2 + 0.25 * s, 2.9 * s, (70, 110, 190), 3)
    B.roof(-w / 2, w / 2, h, 0.8 * s, 1)
    B.plaque(-w * 0.05, h * 0.82, w * 0.36, z=4)


def _monument(B, s, phrase=""):
    st = B.st
    if re.search(r"gate|arch|गेट", phrase, re.I):
        w, h = 7 * s, 9 * s
        B.rect("leg", -w / 2, 0, -w * 0.18, h * 0.8, st["wall"], 0)
        B.rect("leg", w * 0.18, 0, w / 2, h * 0.8, st["wall"], 0)
        B.rect("lintel", -w / 2 - 0.2, h * 0.8, w / 2 + 0.2, h, st["trim"], 1)
        if st["dome_kind"] in ("bulb", "onion"):
            B.dome(0, h, w * 0.12, z=2)
        B.plaque(0, h * 0.84, w * 0.5, z=3)
        return
    if re.search(r"statue|मूर्ति", phrase, re.I):
        B.rect("plinth", -1.6 * s, 0, 1.6 * s, 3.0 * s, st["trim"], 0)
        B.rect("figure", -0.45 * s, 3.0 * s, 0.45 * s, 6.5 * s, (110, 140, 120), 1)      # a figure, faceless
        B.circle("head", 0, 7.0 * s, 0.5 * s, (110, 140, 120), 2)
        B.plaque(0, 1.0 * s, 2.6 * s, z=3)
        return
    if re.search(r"tomb|mausoleum|maqbara|मकबरा", phrase, re.I):
        w, h = 12 * s, 4.0 * s
        B.rect("plinth", -w / 2, 0, w / 2, 1.0 * s, st["trim"], 0)
        B.rect("body", -w * 0.3, 1.0 * s, w * 0.3, h, (244, 242, 236), 1)
        B.door(0, w * 0.12, h * 0.85, z=3)
        B.dome(0, h, w * 0.2, "bulb", z=2)
        for sx in (-1, 1):
            B.minaret(sx * w * 0.45, h * 1.9, 0.6 * s, z=1)
        B.plaque(0, 0.05 * s, w * 0.25, z=4)
        return
    w, h = 3 * s, 10 * s                             # an obelisk / pillar / memorial
    B.rect("plinth", -w, 0, w, 1.2 * s, st["trim"], 0)
    B.poly("shaft", [(-w * 0.32, 1.2 * s), (w * 0.32, 1.2 * s), (w * 0.22, h), (0, h + 0.8 * s), (-w * 0.22, h)],
           st["wall"], 1)
    B.plaque(0, 0.2 * s, w * 1.5, z=3)


def _pyramid(B, s):
    w, h = 16 * s, 8 * s
    B.poly("pyramid", [(-w / 2, 0), (w / 2, 0), (0, h)], (214, 180, 120), 0)
    B.poly("shade", [(0, 0), (w / 2, 0), (0, h)], (186, 150, 96), 1)
    B.plaque(-w * 0.12, 0.3 * s, w * 0.2, z=3)


def _apartments(B, s):
    st = B.st
    w = 14 * s
    for i, (x0, x1, h) in enumerate(((-w / 2, -w * 0.05, 10 * s), (-w * 0.05, w / 2, 7.5 * s))):
        B.rect("block", x0, 0, x1, h, st["wall"] if i else st["trim"], i)
        B.windows(x0 + 0.3, x1 - 0.3, 1.2, h - 0.3, int(h / (1.6 * s)), 4)
    B.door(-w * 0.27, 1.2 * s, 2.2 * s, z=3, arched=False)
    B.plaque(w * 0.22, 0.4 * s, w * 0.3, z=4)


def _village(B, s):
    st = B.st
    w = 14 * s
    for i, x in enumerate((-w * 0.33, 0.0, w * 0.33)):
        hw = 1.8 * s
        B.rect("hut", x - hw, 0, x + hw, 2.0 * s, (196, 150, 104) if st["_region"] == "modern" else st["wall"], i)
        B.poly("thatch", [(x - hw - 0.4, 2.0 * s), (x + hw + 0.4, 2.0 * s), (x, 3.6 * s)], (176, 140, 80), i + 3)
        B.door(x, 0.8 * s, 1.4 * s, z=i + 6, arched=False)
    B.rect("path", -w / 2, 0, w / 2, 0.08 * s, (190, 160, 120), 9)
    B.plaque(0, 2.1 * s, w * 0.18, z=10)


def _camp(B, s):
    w = 14 * s
    cols = [(220, 226, 230), (90, 140, 190), (220, 226, 230), (90, 140, 190)]
    for i in range(4):
        x = -w * 0.38 + i * w * 0.25
        B.poly("tent", [(x - 1.6 * s, 0), (x + 1.6 * s, 0), (x, 2.2 * s)], cols[i], i)
        B.poly("flap", [(x - 0.4 * s, 0), (x + 0.4 * s, 0), (x, 1.2 * s)], (60, 64, 72), i + 5)
    B.rect("rope", -w / 2, 0, w / 2, 0.05 * s, (150, 140, 120), 10)
    B.plaque(0, 2.3 * s, w * 0.2, z=11)


def _farm(B, s):
    w = 12 * s
    B.rect("barn", -w * 0.1, 0, w * 0.35, 4.0 * s, (180, 60, 50), 0)
    B.poly("barnroof", [(-w * 0.13, 4.0 * s), (w * 0.38, 4.0 * s), (w * 0.125, 6.0 * s)], (90, 60, 50), 1)
    B.door(w * 0.125, 1.8 * s, 2.8 * s, z=2, arched=False)
    B.rect("field", -w / 2, 0, -w * 0.1, 0.5 * s, (110, 160, 80), 0)
    for i in range(6):
        x = -w / 2 + 0.4 + i * w * 0.065
        B.line("crop", [(x, 0.5 * s), (x, 1.2 * s)], (80, 140, 60), 0.12 * s, 1)
    B.plaque(-w * 0.27, 1.3 * s, w * 0.28, z=3)


def _civic(B, s):
    st = B.st
    w, h = 12 * s, 5.0 * s
    B.rect("wall", -w / 2, 0, w / 2, h, st["wall"], 0)
    B.windows(-w / 2 + 0.3, w / 2 - 0.3, 0.3, h - 0.3, 2, 8, arched=st["dome_kind"] in ("bulb", "onion"))
    B.rect("entrance", -w * 0.13, 0, w * 0.13, h * 1.15, st["trim"], 1)
    B.door(0, w * 0.1, h * 0.55, z=3)
    B.roof(-w / 2, w / 2, h, 1.0 * s, 1)
    B.pennant(w * 0.13 - 0.1, h * 1.15, 1.6 * s)
    B.plaque(0, h * 0.66, w * 0.22, z=7)


BUILD = {"legislature": _legislature, "court": _court, "palace": _palace, "fort": _fort, "temple": _temple,
         "pagoda": _pagoda, "stupa": _stupa, "mosque": _mosque, "gurdwara": _gurdwara, "church": _church,
         "synagogue": _synagogue, "tower": _tower, "school": _school, "hospital": _hospital, "station": _station,
         "airport": _airport, "port": _port, "factory": _factory, "power": _power, "dam": _dam, "bridge": _bridge,
         "stadium": _stadium, "market": _market, "cinema": _cinema, "police": _police, "monument": _monument,
         "pyramid": _pyramid, "apartments": _apartments, "village": _village, "camp": _camp, "farm": _farm,
         "civic": _civic, "tomb": lambda B, s: _monument(B, s, "tomb")}


def _name(phrase: str) -> str:
    """The plaque text: the phrase without articles, short, in capitals."""
    words = [w for w in re.findall(r"[\w'\-\.ऀ-ॿ]+", phrase) if w.lower() not in ("a", "an", "the", "of",
                                                                                         "in", "at", "its", "their")]
    text = " ".join(words)[:26].strip()
    return text.upper() if re.search(r"[A-Za-z]", text) else text


def compose(phrase: str, region: str | None = None, scale: float = 1.0) -> dict:
    """An asset (asset_lib format) for any building or place phrase. Raises ValueError if it isn't one."""
    from .asset_lib import _asset
    kind = kind_of(phrase)
    if kind is None:
        raise ValueError(f"{phrase!r} is not a building or place")
    reg = region_of(phrase)
    if reg == "modern":                              # the script's region, else what the structure implies
        reg = region if region and region != "modern" else KIND_REGION.get(kind, "modern")
    st = dict(STYLES.get(reg, STYLES["modern"]))
    st["_region"] = reg
    B = _B(st)
    s = max(0.4, min(2.0, scale))
    fn = BUILD[kind]
    if kind == "monument":                          # gate, statue, tomb or obelisk from the words
        fn(B, s, phrase)
    else:
        fn(B, s)
    xs = [abs(x) for p in B.parts for x in ([q[0] for q in p["pts"]] if "pts" in p else [p["c"][0] + p["r"], p["c"][0] - p["r"]])]
    ys = [y for p in B.parts for y in ([q[1] for q in p["pts"]] if "pts" in p else [p["c"][1] + p["r"]])]
    w = 2 * max(xs) + 0.05
    h = max(ys) + 0.02
    a = _asset("structure", phrase.strip(), B.parts, w, h, uses=["background", "stand_near"], text=_name(phrase),
               archetype=kind, region=reg)
    a["source"] = f"procedural:structure:{kind}:{reg}"
    return a
