"""The Vox director: every narration line gets one drawn graphic (no AI pictures), and every graphic line is
checked before anything renders.

    script, report = ensure(script_text, llm)      # fills lines that have no graphic, fixes what can be fixed
    issues = check(script_text)                    # what is still wrong, in plain words

A line's graphic is chosen by the script AI when one is available (from the catalogue below, English labels,
never inventing facts), otherwise by rules: numbers -> Chart, dates -> Calendar, places -> Map, objects and
actions -> Animate, the rest -> a cut-out Statement."""
from __future__ import annotations

import json
import re
import unicodedata

from . import director

# ---- the catalogue the script AI chooses from (exact syntax) --------------------------------------------------
CATALOG = """GRAPHICS (pick ONE per line; labels and on-screen words in ENGLISH; copy facts only from the line itself):
Hero: <object> [+ <object>] | <HEADLINE 2-4 words> | <tag> · <tag> | <short note>
    - THE MAIN LOOK: a big real cut-out photo of an object, place or public figure (person:Full Name), a black-box
      headline, small tags and a note. Objects: hand pointing, cash, coins, gavel, handcuffs, ballot box, evm,
      megaphone, microphone, crown, puppet, mask, chain, padlock, newspaper, television, smartphone, laptop, server,
      magnifying glass, documents, clock, hourglass, light bulb, ladder, trophy, factory chimney, tractor, crowd,
      parliament, supreme court, red fort, india gate, village, skyline, office building ... (any everyday object)
      e.g. Hero: smartphone + crowd | ONE MESSAGE | 8 AM · every day | sent to lakhs of groups
           Hero: person:Amit Shah | THE CLAIM | Kota · 2018
    Opinion lines only: add "| prop: blindfold|mask|zip|crown|strings|chains|megaphone" over a person:Name photo
    (ignoring facts -> blindfold, silenced -> zip, controlled -> strings, power -> crown, propaganda -> megaphone).
Opener: <object or person:Name> | <headline, *key words* highlighted> | <kicker e.g. Chapter 2>  - hooks, new parts
Pinmap: <Indian city/state or country> | <the real headline> | <publisher, month year>  - news tied to a place
Clipping: <the real headline> | <publisher, month year> | <object> + <object> | <chapter number>  - a torn newspaper
Pinboard: <centre item> · <item> · <item> | <title>  - who/what is connected (items: objects, person:Name,
    dates like 20 SEP 2018, or one-word cards like SOLVED)
Reveal: <document line> · <line> · <line> | <document name> | <the phrase to highlight>  - zoom into a document
Desk: <object> + <object> | <LABEL> | <short note>  - research / an investigation on grid paper
BigNumber: <a year or number> | <object> | <caption>  - a huge year/number with the subject breaking out of it
Seats: <party/alliance> <seats>, <party> <seats>, Others <seats> | <title>  - a parliament of seat dots
Stack: coins|pillars|chimneys|buildings|books | <label> <value>, <label> <value> | <title>  - bars as real things
Stand: <who> <value> vs <who> <value> | <title> | <note>  - people standing on their bars (income, wealth)
Fan: <label> <value>, <label> <value>, ... | <title> | <object or person:Name>  - shares around a photo
Trend: <year> <value>, <year> <value>, ... | <title> | <object>  - a line chart with the object's photo under the line
Slice: <n>% | <object> | <what the share is>  - a share cut out of a real object
Route: <place> → <place> → <place> | <title> | plane|ship|car|train  - a journey on a paper map
Compare: <object or person:Name> [+ <second>] | <before label> | <after label> | <title>  - then vs now
Photoline: <year> <event> (<object>) → <year> <event> (<object>) | <title>  - a timeline of photo cards
Tv: <object or person:Name> | <label e.g. 1975 broadcast> | <caption>  - something seen on old television
Hero styles: add "| style: word|disc|box|bars|grid" to choose the look (grid = cut-out with a colour offset on grid paper)
Clockmap: <city> <time>, <city> <time>, ... | <title> | <zone>  - the same moment in many places
Tornsplit: <object> + <object> | <BIG HEADLINE 2-4 words> | <kicker>  - a chapter or story opener
Newscard: <date> | <the real headline> | <the line under it> | person:Name | <publisher>  - a news report card
Blueprint: <object> | <title> | <fact> · <fact> · <fact>  - how a place or machine works
Fly: <place> [→ <place>] | <title> | satellite  - a real-map fly-in (satellite imagery when it helps)
Route/Pinmap: add "| atlas" for the printed-atlas look
Any graphic: add "| marker: <3-6 words>" for a red hand-drawn circle round the subject and a handwritten note
    (Johnny Harris style) - use it on the line's key fact, about one line in five.
Chart: <number> | <what it counts>              - one number counting up (e.g. Chart: ₹29.7 crore | Google ads in 30 days)
Chart: <a> vs <b> | <label a>, <label b>        - two numbers as bars
Pie: <n>% | <what>                               - a share
Icons: <k> of <n> | people | <what>              - "9 of 10" style
Calendar: <DD MON YYYY> | <what happened>        - a specific date
Clock: <time> | <what>                           - a time of day
Timeline: <YEAR event> → <YEAR event> | <title>  - events across years
Map: <Place> | <note>    or   Map: <A> → <B>     - a place or a route
Steps: <a> → <b> → <c> | <title>                 - a process, 2-5 steps
Animate: <objects and an action in plain English> | <title>
    actions: flies/drives/sails from A to B (carrying X), grows, falls, spreads to many, attacks, stacks up, splits,
    buzzes, blocks/deletes, A vs B, cycle, A → B → C. Any everyday object works (phone, plane, cash, court, crowd...).
Quote: <exact words> | <who, when>               - only when the line quotes someone (translate faithfully, add "(translated)")
Article: <real headline> | <publisher, month year> - only when the line cites a named report
Document: <exact line> | <document, year>
Social: <account> | <post text> | <12K likes · 3K shares>
Comments: <post> | <comment> · <comment> · <comment>
Trending: <#hashtag> | <#other> · <#other>
Chat: <group> | them: <message> · me: <reply>     - a recreated chat (shown labelled)
Search: <query> | <result> · <result>
Stamp: <FAKE / MANIPULATED MEDIA ...> | <what it is stamped on>
Sign: <PLACARD TEXT> | placard|banner|billboard
Board: <centre> · <link> · <link> | <title>       - who is connected to whom
Statement: <max 8 words, *key word* highlighted> - a punchline or turning point
Chapter: Part <n> | <title>                      - a new section"""

SYSTEM = f"""You are the visual director of a Vox-style explainer. Every narration line (Hindi/Hinglish) gets exactly
ONE animated graphic that SHOWS what the line says - the viewer must understand the line with the sound off.
{CATALOG}
RULES:
- English on screen. Short labels (max 6 words). Never invent numbers, names, dates or quotes not in the line.
- Variety: never the same graphic type on two lines in a row; at most 1 Statement in every 4 lines.
- Numbers -> Chart/Pie/Icons. Dates -> Calendar/Timeline. Places on a map -> Map. People, objects, institutions,
  ideas -> Hero (a metaphor object: power -> crown, control -> puppet, lies -> mask, law -> gavel, money -> cash).
  Movement or a process -> Animate. About half the lines should be Hero.
- Real people: only as person:Full Name in a Hero (their real photo); never drawn or cartoon.
Return JSON only: {{"lines": [{{"n": <line number>, "graphic": "<one line from the catalogue>"}}]}}"""

KINDS = set(director.FULL_FRAME) | {"chart"}
_KEY = re.compile(r"^\s*([A-Za-z][A-Za-z -]{1,24})\s*:\s*(.*)$")
_DEV = re.compile(r"[ऀ-ॿ]")

# ---- Hindi words a narration uses -> English for labels and icons ------------------------------------------------
HI_EN = {
    "फ़ोन": "phone", "फोन": "phone", "मोबाइल": "phone", "मैसेज": "message", "संदेश": "message", "व्हाट्सऐप": "whatsapp",
    "ग्रुप": "group", "ग्रुप्स": "groups", "वीडियो": "video", "पोस्ट": "post", "ट्वीट": "tweet", "अकाउंट": "account",
    "ट्रोल": "troll", "ट्रोल्स": "trolls", "पैसा": "money", "पैसे": "money", "रुपये": "rupees", "करोड़": "crore",
    "लाख": "lakh", "ऐड": "ads", "विज्ञापन": "ads", "सरकार": "government", "अदालत": "court", "कोर्ट": "court",
    "पुलिस": "police", "जेल": "jail", "किसान": "farmers", "पत्रकार": "journalist", "नेता": "leader", "पार्टी": "party",
    "चुनाव": "election", "वोट": "vote", "मतदाता": "voters", "लोग": "people", "भीड़": "crowd", "शहर": "city",
    "गाँव": "village", "दफ़्तर": "office", "ऑफ़िस": "office", "मंच": "stage", "किताब": "book", "रिपोर्ट": "report",
    "दस्तावेज़": "document", "अख़बार": "newspaper", "ख़बर": "news", "ख़बरें": "news", "झूठ": "lie", "सच": "truth",
    "डर": "fear", "नफ़रत": "hate", "भरोसा": "trust", "मशीन": "machine", "कंपनी": "company", "बैंक": "bank",
    "टैक्स": "tax", "आयकर": "tax", "हवाई": "plane", "जहाज़": "ship", "ट्रेन": "train", "कार": "car", "ट्रक": "truck",
    "घर": "home", "स्कूल": "school", "अस्पताल": "hospital", "दुनिया": "world", "देश": "country", "फ़ेसबुक": "facebook",
    "गूगल": "google", "ट्विटर": "twitter", "एक्स": "x", "यूट्यूब": "youtube", "डेटा": "data", "वेबसाइट": "website",
    "हैशटैग": "hashtag", "कमेंट": "comments", "लाइक": "likes", "शेयर": "share", "फ़ॉरवर्ड": "forward",
    "ब्लॉक": "block", "डिलीट": "delete", "आदेश": "order", "क़ानून": "law", "नियम": "rules", "सेना": "army",
}
HI_VERB = {"फैल": "spreads", "वायरल": "spreads", "बढ़": "grows", "बढ़ा": "grows", "गिर": "falls", "घट": "falls",
           "हमला": "attack", "टूट पड़": "attack", "ब्लॉक": "blocks", "हटा": "blocks", "रोक": "blocks", "डिलीट": "blocks",
           "भेज": "sends", "पहुँच": "reaches", "जा": "goes", "उड़": "flies", "बँट": "splits"}
MONTHS = {"जनवरी": "JAN", "फ़रवरी": "FEB", "फरवरी": "FEB", "मार्च": "MAR", "अप्रैल": "APR", "मई": "MAY", "जून": "JUN",
          "जुलाई": "JUL", "अगस्त": "AUG", "सितंबर": "SEP", "अक्टूबर": "OCT", "नवंबर": "NOV", "दिसंबर": "DEC",
          "january": "JAN", "february": "FEB", "march": "MAR", "april": "APR", "may": "MAY", "june": "JUN",
          "july": "JUL", "august": "AUG", "september": "SEP", "october": "OCT", "november": "NOV", "december": "DEC"}
PLACES = {"दिल्ली": "New Delhi", "मुंबई": "Mumbai", "कोलकाता": "Kolkata", "चेन्नई": "Chennai", "बेंगलुरु": "Bengaluru",
          "हैदराबाद": "Hyderabad", "पुणे": "Pune", "अहमदाबाद": "Ahmedabad", "जयपुर": "Jaipur", "लखनऊ": "Lucknow",
          "पटना": "Patna", "कोटा": "Kota", "मंडी": "Mandi", "उत्तर प्रदेश": "Uttar Pradesh", "बिहार": "Bihar",
          "गुजरात": "Gujarat", "पंजाब": "Punjab", "केरल": "Kerala", "कश्मीर": "Kashmir", "लंदन": "London",
          "अमेरिका": "United States", "चीन": "China", "पाकिस्तान": "Pakistan", "दुबई": "Dubai", "रूस": "Russia",
          "जिनेवा": "Geneva", "शाहीन बाग़": "Shaheen Bagh", "राजस्थान": "Rajasthan", "हिमाचल": "Himachal Pradesh"}
HI_NUM = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "बीस": 20,
          "तीस": 30, "चालीस": 40, "पचास": 50, "सौ": 100, "हज़ार": 1000}


# ---- reading a script into blocks ----------------------------------------------------------------------------------
def blocks(script: str) -> tuple[list[str], list[dict]]:
    """(header lines, [{"line": spoken text, "dirs": [direction lines]}]). A plain paragraph is split into lines
    of one or two sentences (each gets its own graphic)."""
    keys = set(director._META_KEYS)
    raw = (script or "").replace("\r", "").split("\n")
    header: list[str] = []
    out: list[dict] = []
    seen_spoken = False
    head_keys = {"on-screen hook", "on screen hook", "onscreen hook", "hook text", "title", "post title", "video title",
                 "tags", "hashtags", "source", "sources", "description"}
    first = next((i for i, l in enumerate(raw) if l.strip()), None)
    has_header = any(_KEY.match(l) and _KEY.match(l).group(1).strip().lower() in head_keys for l in raw[:8])
    for i, ln in enumerate(raw):
        s = ln.strip()
        if not s:
            continue
        m = _KEY.match(s)
        key = m.group(1).strip().lower() if m else ""
        if m and key in keys:
            if not seen_spoken and key in head_keys | {"visual style"}:
                header.append(s)
            elif out:
                out[-1]["dirs"].append(s)
            else:
                header.append(s)
            continue
        if i == first and has_header:
            header.insert(0, s)           # the video's name
            continue
        s = re.sub(r"\s*<[^>]+>\s*", " ", s).strip()        # voice tags (<break .../>) are not narration
        if not s:
            continue
        seen_spoken = True
        for piece in _split(s):
            out.append({"line": piece, "dirs": []})
    return header, out


def _split(text: str, most: int = 18) -> list[str]:
    """A long spoken line as pieces of whole sentences, about 6 s each (narration words unchanged)."""
    if len(text.split()) <= most:
        return [text]
    sents = [x.strip() for x in re.findall(r"[^।.!?]+[।.!?]*", text) if x.strip()]
    out, cur = [], ""
    for s in sents:
        if cur and len((cur + " " + s).split()) > most:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out or [text]


def render_blocks(header: list[str], bl: list[dict]) -> str:
    return "\n\n".join(["\n".join(header)] + ["\n".join([b["line"]] + b["dirs"]) for b in bl]).strip() + "\n"


def graphic_kind(b: dict) -> str:
    for d in b["dirs"]:
        m = _KEY.match(d)
        if m and m.group(1).strip().lower() in KINDS:
            return m.group(1).strip().lower()
    return ""


# ---- rules (no AI) -----------------------------------------------------------------------------------------------
_NUKTA = "\u093c"
_SUFFIX = ("", "ों", "ें", "ो", "े", "ी", "ा", "्स", "यों", "एँ", "ें", "ाओं", "ियों", "िया")
_HI_1_100 = ("एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस इक्कीस "
             "बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस "
             "सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास "
             "पचास इक्यावन बावन तिरेपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरेसठ चौंसठ पैंसठ "
             "छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर "
             "उन्यासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे "
             "तिरानवे चौरानवे पचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे").split()
_HI_N = {unicodedata.normalize("NFD", w).replace(_NUKTA, ""): i for i, w in enumerate(_HI_1_100, 1)} | {_plain_k: v for _plain_k, v in ((unicodedata.normalize("NFD", k).replace(_NUKTA, ""), v)
                                  for k, v in {"छः": 6, "पांच": 5, "डेढ़": 1.5, "ढाई": 2.5}.items())}
_MULT = {unicodedata.normalize("NFD", k).replace(_NUKTA, ""): v
         for k, v in {"सौ": 100, "हज़ार": 1000, "लाख": 100000, "करोड़": 10**7, "अरब": 10**9}.items()}
_UNIT = {100000: "lakh", 10**7: "crore", 10**9: "billion"}
_PAUSE = re.compile(r"^\s*(<[^>]+>\s*)+$")


def _plain(t: str) -> str:
    """Spelling-proof Hindi: फ़ोन == फोन, करोड़ == करोड."""
    return unicodedata.normalize("NFD", t).replace(_NUKTA, "")


def _tokens(line: str) -> list[str]:
    return [_plain(w) for w in re.findall(r"[^\s,.।!?;:()\"'“”‘’…-]+", line)]


def _has(tokens: list[str], hi: str) -> bool:
    """A Hindi word in the line as a whole word (with its plural/case endings) - "कार" is not in "कार्यकर्ता"."""
    hi = _plain(hi)
    parts = hi.split()
    if len(parts) > 1:
        return any(tokens[i:i + len(parts)] == parts for i in range(len(tokens)))
    return any(t == hi + suf for t in tokens for suf in _SUFFIX)


def _english(line: str) -> list[str]:
    toks = _tokens(line)
    words: list[str] = []
    for hi, en in HI_EN.items():
        if _has(toks, hi) and en.rstrip("s") not in [w.rstrip("s") for w in words]:
            words.append(en)
    for w in re.findall(r"[A-Za-z]{3,}", re.sub(r"<[^>]*>", " ", line)):
        if w.lower().rstrip("s") not in [x.rstrip("s") for x in words]:
            words.append(w.lower())
    return words


def _spoken_numbers(line: str) -> list[tuple[float, int]]:
    """Numbers said in words: "पंद्रह लाख" -> (15, 100000); "उनतीस करोड़ सत्तर लाख" -> (29.7, 10**7);
    "दो हज़ार अठारह" -> (2018, 1)."""
    toks, out, i = _tokens(line), [], 0

    def num_at(k: int):
        if k >= len(toks):
            return None
        t = toks[k]
        if re.fullmatch(r"\d[\d,]*(?:\.\d+)?", t):
            return float(t.replace(",", ""))
        return _HI_N.get(t)

    while i < len(toks):
        n = num_at(i)
        # "एक" alone is usually "a/one" in Hindi, not a number worth a chart
        if n is None or (toks[i] == "एक" and not _MULT.get(toks[i + 1] if i + 1 < len(toks) else "")):
            i += 1
            continue
        base, big, small, j = 0.0, 1, float(n), i + 1
        while j < len(toks):
            m = _MULT.get(toks[j])
            if not m:
                break
            if m in (100, 1000):
                small *= m
            else:
                base += small * m
                big = max(big, m)
                small = 0.0
            j += 1
            nxt = num_at(j)
            if nxt is None:
                break
            if m in (100, 1000) or _MULT.get(toks[j + 1] if j + 1 < len(toks) else ""):
                small += float(nxt)
                j += 1
            else:
                break
        total = base + small
        out.append((round(total / big, 2), big))
        i = j
    return out


def _number(line: str) -> str:
    m = re.search(r"(₹\s?[\d,.]+\s*(?:करोड़|लाख|crore|lakh|million|billion)?|[\d,.]+\s*(?:%|प्रतिशत|करोड़|लाख|crore|lakh))", line)
    if m:
        v = m.group(1).replace("प्रतिशत", "%").replace("करोड़", " crore").replace("लाख", " lakh")
        return re.sub(r"\s+", " ", v).strip()
    money = any(_has(_tokens(line), w) for w in ("रुपये", "रुपए", "रुपया"))
    pct = any(w in _plain(line) for w in ("प्रतिशत", "फीसदी", "परसेंट"))
    for n, unit in _spoken_numbers(line):
        if pct and unit == 1 and n <= 100:
            return f"{n:g}%"
        if unit > 1 or (n >= 100 and not 1900 <= n <= 2100):
            return ("₹" if money else "") + f"{n:g}" + (f" {_UNIT[unit]}" if unit in _UNIT else "")
    return ""


def _date(line: str) -> tuple[str, str]:
    year = re.search(r"\b(19\d\d|20\d\d)\b", line)
    yr = year.group(1) if year else next((f"{n:g}" for n, u in _spoken_numbers(line) if u == 1 and 1900 <= n <= 2100), "")
    toks = _tokens(line)
    mon = next((v for k, v in MONTHS.items() if _has(toks, k) or k in line.lower().split()), "")
    day = ""
    for k in MONTHS:
        mm = re.search(rf"\b([1-9]|[12]\d|3[01])\s+{re.escape(k)}", line)
        if mm:
            day = mm.group(1)
    full = f"{day} {mon} {yr}".strip() if day and mon else (f"{mon} {yr}" if mon and yr else "")
    return full, yr


def _clock(line: str) -> str:
    toks = _tokens(line)
    for i, t in enumerate(toks[:-1]):
        if toks[i + 1] in ("बजे", "बजकर") and (t in _HI_N or t.isdigit()):
            h = int(_HI_N.get(t) or int(t))
            pm = any(_has(toks, w) for w in ("शाम", "रात", "दोपहर"))
            return f"{h}:00 {'PM' if pm else 'AM'}"
    m = re.search(r"\b(\d{1,2}(?::\d\d)?\s*(?:am|pm|AM|PM))", line)
    return m.group(1) if m else ""


def rule_graphic(line: str, prev_kind: str = "", prev_graphic: str = "") -> str:
    """One graphic for a narration line without the script AI ('' when the rules find nothing to show)."""
    words = _english(line)
    nouns = [w for w in words if w not in ("crore", "lakh", "rupees")][:2]
    label = " ".join(nouns).title()
    num = _number(line)
    if num and prev_kind != "chart":
        return f"Chart: {num}" + (f" | {label}" if label else "")
    clock = _clock(line)
    if clock and prev_kind != "clock":
        return f"Clock: {clock}" + (f" | {label}" if label else "")
    full, year = _date(line)
    if full and prev_kind != "calendar":
        return f"Calendar: {full}" + (f" | {label}" if label else "")
    place = next((v for k, v in PLACES.items() if _has(_tokens(line), k)), "")
    if place and prev_kind != "map":
        return f"Map: {place}" + (f" | {label}" if label else "")
    verb = next((v for k, v in HI_VERB.items() if _has(_tokens(line), k)), "")
    from .media import cutouts
    objs = [w for w in words if cutouts.resolve(w)][:2]
    if objs and not verb and prev_kind != "hero":
        subj = " + ".join(cutouts.resolve(w) for w in objs)
        tags = " · ".join(t for t in (year, place) if t)
        return f"Hero: {subj} | {' '.join(objs).upper()}" + (f" | {tags}" if tags else "")
    if nouns and prev_kind != "animate":
        if verb and len(nouns) >= 2:
            return f"Animate: {nouns[0]} {verb} {nouns[1]}"
        if verb:
            return f"Animate: {nouns[0]} {verb}"
        return f"Animate: {nouns[0]} → {nouns[1]}" if len(nouns) > 1 else f"Animate: {nouns[0]}"
    if year and prev_kind != "statement":
        return f"Statement: *{year}*"
    if objs:
        return f"Hero: {' + '.join(cutouts.resolve(w) for w in objs)} | {' '.join(objs).upper()}"
    if nouns and prev_kind == "animate":
        return f"Statement: *{nouns[0].upper()}*" if len(nouns) == 1 else f"Statement: {nouns[0]} and *{nouns[1]}*"
    return ""


# ---- checking and fixing -----------------------------------------------------------------------------------------
BRANDS = {"google", "facebook", "meta", "whatsapp", "youtube", "instagram", "twitter", "tiktok", "jio", "airtel",
          "spotify", "gaana", "amazon", "flipkart", "apple", "microsoft", "netflix", "paytm", "snapdeal", "uber", "ola",
          "zomato", "swiggy", "tesla", "nvidia", "openai", "chatgpt", "telegram", "snapchat", "linkedin", "reliance",
          "adani", "tata", "infosys", "samsung", "coca-cola", "pepsi", "mcdonald's", "starbucks"}


def _content_rules(kind: str, spec: str, props: bool) -> str:
    """Channel rules that hold for every graphic: no national flags, no brand logos as pictures, no props over a
    real person unless the video turned them on."""
    from .media import vox
    pictured = []
    if kind in vox.KINDS:
        pictured = [str(x).lower() for x in (vox.plan_for(kind, spec) or {}).get("subjects", [])]
    elif kind in ("animate", "object"):
        pictured = [spec.split("|")[0].lower()]
    if any(re.search(r"\bflags?\b", x) and "pole" not in x for x in pictured):
        return "no national flags (name the country in a tag instead)"
    if kind in vox.KINDS:
        p = vox.plan_for(kind, spec) or {}
        subs = pictured
        bad = [b for b in BRANDS for sub in subs if not sub.startswith("person:") and re.search(rf"\b{re.escape(b)}\b", sub)]
        if bad:
            return f"no brand logos as pictures ('{bad[0]}'): show a smartphone/laptop and name it in a tag"
        if p.get("prop") and not props:
            return "symbolic props over a real person are off for this video (turn on Editorial cartoon props)"
        if p.get("prop") and not any(sub.startswith("person:") for sub in subs[:1]):
            return "props go on a real person's photo (person:Name first)"
    return ""


def valid(direction: str, english: bool = True, props: bool = False) -> str:
    """'' when the graphic line will draw correctly; otherwise the reason."""
    m = _KEY.match(direction)
    if not m:
        return "not a graphic line"
    kind, spec = m.group(1).strip().lower(), m.group(2).strip()
    if kind not in KINDS:
        return f"'{m.group(1)}' is not a graphic"
    if not spec:
        return "empty"
    rule = _content_rules(kind, spec, props)
    if rule:
        return rule
    if english and _DEV.search(spec.split("|")[0] if kind in ("quote", "document") else spec):
        return "Hindi text on screen (graphics are English)"
    from .media import motion
    if kind in motion.KINDS:
        if kind == "statement" and len(spec.replace("*", "").split()) > 10:
            return "Statement longer than 10 words"
        try:
            ok = motion.plan_for(kind, spec) is not None
        except Exception:  # noqa: BLE001
            ok = False
        return "" if ok else "the graphic can't be drawn from this line (check its format)"
    from .media import vox
    if kind in vox.KINDS:
        p = vox.plan_for(kind, spec)
        if not p:
            return ("place not found on the map" if kind == "pinmap"
                    else "the graphic can't be drawn from this line (check its format)")
        if kind == "hero" and len(p["headline"].split()) > 7:
            return "Hero headline longer than 7 words"
        if kind == "opener" and len(p["headline"].replace("*", "").split()) > 9:
            return "Opener headline longer than 9 words"
        return ""
    if kind in ("map", "globe", "fly"):
        from .media import maps
        return "" if maps.parse(re.sub(r"=[^→|]*", "", spec)) else "place not found on the map"
    if kind in ("quote", "steps", "timeline", "icons", "screen", "document", "article", "chat", "search", "pie",
                "squares", "timer", "receipt", "chapter"):
        from .media.layout_qa import check_card
        try:
            errs = [i for i in check_card(kind, spec, "editorial", 1920, 1080) if i.level == "error"]
        except Exception as e:  # noqa: BLE001
            return f"can't be drawn ({str(e)[:60]})"
        return "" if not errs else f"layout: {errs[0].what}"
    return ""


def check(script: str, english: bool = True, props: bool = False) -> list[dict]:
    """Everything that would make the video wrong, line by line: [{"n", "line", "level", "problem"}]."""
    _, bl = blocks(script)
    issues = []
    prev = ""
    shown, propped = set(), set()            # people pictured / people given a symbolic prop (fairness check)
    for b in bl:
        for d in b["dirs"]:
            for who in re.findall(r"person:\s*([^|·+\n]+)", d, re.I):
                shown.add(who.strip().lower())
                if re.search(r"\bprop\s*[:=]", d, re.I):
                    propped.add(who.strip().lower())
    if props and propped and shown - propped:
        issues.append({"n": 0, "line": "", "level": "warning",
                       "problem": f"only {', '.join(sorted(propped))} get symbolic props; "
                                  f"{', '.join(sorted(shown - propped))} never do - check the video is fair"})
    for n, b in enumerate(bl, 1):
        kind = graphic_kind(b)
        if not kind and not (_keys(b) & set(REAL)):
            issues.append({"n": n, "line": b["line"][:60], "level": "error", "problem": "no graphic (would need an AI picture)"})
        for d in b["dirs"]:
            m = _KEY.match(d)
            if m and m.group(1).strip().lower() in KINDS:
                why = valid(d, english, props)
                if why:
                    issues.append({"n": n, "line": b["line"][:60], "level": "error", "problem": f"{d[:50]}: {why}"})
            elif m and m.group(1).strip().lower() in ("visual", "visuals", "b-roll", "broll"):
                issues.append({"n": n, "line": b["line"][:60], "level": "warning", "problem": "Visual: asks for an AI picture"})
        if kind and kind == prev and kind != "chapter":
            issues.append({"n": n, "line": b["line"][:60], "level": "warning", "problem": f"same graphic as the line before ({kind})"})
        prev = kind or prev
        if len(b["line"].split()) / 2.4 > 9:
            issues.append({"n": n, "line": b["line"][:60], "level": "warning", "problem": "one graphic held over 9 s - split the line"})
    return issues


_FIX_DROP = ("visual", "visuals", "b-roll", "broll", "big", "split")
REAL = ("archive", "clip", "stock", "stock footage")      # your own photo/clip or real footage: the line is covered


def _keys(b: dict) -> set[str]:
    return {_KEY.match(d).group(1).strip().lower() for d in b["dirs"] if _KEY.match(d)}


def ensure(script: str, llm=None, english: bool = True, props: bool = False) -> tuple[str, list[str]]:
    """The script with a valid graphic on every line. The script AI picks graphics for lines that have none (or
    a broken one); rules cover anything it leaves. Narration words are never changed."""
    header, bl = blocks(script)
    report: list[str] = []
    need = []
    for n, b in enumerate(bl, 1):
        if not props:      # props switched off: the prop goes, the graphic stays
            for i, d in enumerate(b["dirs"]):
                if re.search(r"\|\s*prop\s*[:=][^|]*", d, re.I):
                    b["dirs"][i] = re.sub(r"\s*\|\s*prop\s*[:=][^|]*", "", d, flags=re.I)
                    report.append(f"line {n}: removed the prop (Editorial cartoon props are off)")
        good = [d for d in b["dirs"] if (_KEY.match(d) and _KEY.match(d).group(1).strip().lower() in KINDS and not valid(d, english, props))]
        bad = [d for d in b["dirs"] if (_KEY.match(d) and _KEY.match(d).group(1).strip().lower() in KINDS and valid(d, english, props))]
        for d in bad:
            report.append(f"line {n}: replaced '{d[:40]}' ({valid(d, english, props)})")
        # AI-picture and over-the-picture directions go: every line is a drawn graphic
        keep = [d for d in b["dirs"] if not (_KEY.match(d) and _KEY.match(d).group(1).strip().lower() in KINDS)
                and not (_KEY.match(d) and _KEY.match(d).group(1).strip().lower() in _FIX_DROP)]
        b["dirs"] = keep + good[:1]
        if not good and not (_keys(b) & set(REAL)):
            need.append(n)
    picked: dict[int, str] = {}
    if need and llm is not None:
        try:
            listing = "\n".join(f"{n}. {bl[n - 1]['line']}" for n in need)
            context = "\n".join(f"{i}. {b['line']}" for i, b in enumerate(bl, 1))[:9000]
            raw = llm.complete_json(SYSTEM, f"WHOLE SCRIPT (for context):\n{context}\n\nGIVE A GRAPHIC TO THESE LINES:\n{listing}")
            data = director._extract_json(raw)
            for it in (data.get("lines") or []) if isinstance(data, dict) else []:
                n, g = int(it.get("n", 0)), str(it.get("graphic", "")).strip()
                if n in need and g and not valid(g, english, props):
                    picked[n] = g
        except Exception as e:  # noqa: BLE001 - quota, network, bad JSON: rules take over
            report.append(f"script AI unavailable ({str(e)[:60]}) - graphics chosen by rules")
    prev, prev_g = "", ""
    for n, b in enumerate(bl, 1):
        if n in need:
            g, how = picked.get(n, ""), "AI"
            if not g:
                g, how = rule_graphic(b["line"], prev), "rule"
                if not g or valid(g, english):
                    g = rule_graphic(b["line"], "")
            if not g or valid(g, english):
                # nothing in the line to draw: the previous graphic stays on screen (Vox holds a graphic over a
                # thought); the first line falls back to the video's title card
                g, how = (prev_g, "held") if prev_g else ("Chapter: Part 1 | " + _title(header), "title")
            b["dirs"].append(g)
            report.append(f"line {n}: {how} -> {g[:60]}")
        kind = graphic_kind(b)
        if kind:
            prev = kind
            prev_g = next(d for d in b["dirs"] if _KEY.match(d) and _KEY.match(d).group(1).strip().lower() == kind)
    return render_blocks(header, bl), report


def _title(header: list[str]) -> str:
    for h in header:
        m = _KEY.match(h)
        if m and m.group(1).strip().lower() in ("title", "video title", "post title") and not _DEV.search(m.group(2)):
            return m.group(2).split("|")[0].strip()[:40]
    plain = [h for h in header if not _KEY.match(h) and not _DEV.search(h)]
    return plain[0][:40] if plain else "The story"
