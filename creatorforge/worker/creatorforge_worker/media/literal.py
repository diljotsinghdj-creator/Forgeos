"""Show what the narration says. Two passes over the planned beats (each beat = a few spoken words + a picture):

1. NAMED SUBJECTS - a person, party, institution or landmark named in the words ("Modi", "the BJP", "Congress",
   "Parliament", "the Supreme Court", "Rahul Gandhi") gets a real picture of it, found by name on Wikipedia /
   Wikimedia Commons at image time (beat["named"]). Logos and party symbols are used to identify who is being
   talked about; people get a real photo even on a faceless channel (they are public figures named in the line).
2. EVERYDAY THINGS - a concrete thing the words mention ("discount", "vote", "ballot", "subscription", "credit
   card", "police") gets a picture of exactly that, when the writer's own Visual line shows something else.

Each subject is shown on its first mention and again at most every few beats, so a video isn't the same face
or logo on repeat. Beats carrying a full-frame graphic, a split screen or the writer's own Stock search are left
alone. Safe to run more than once (beats already handled are marked)."""
from __future__ import annotations

import re

# ---- 2. everyday things --------------------------------------------------------------------------------------
# (what the words say, what the picture must already show to count as a match, pictures to use instead)
CONCEPTS: list[tuple[str, str, list[str]]] = [
    (r"electoral bonds?",
     r"bond|envelope|cash|donat",
     ["A sealed brown envelope full of cash slid across a desk", "Printed bond certificates in a stack, text blurred"]),
    (r"press conferences?",
     r"podium|microphone|press",
     ["An empty press-conference podium covered in microphones"]),
    (r"discount\w*|\d+ ?% off|half price|on sale|\bsale\b|bargain\w*|markdown",
     r"discount|sale|% ?off|price tag|clearance",
     ["A bright red SALE 50% OFF sign hanging in a shop window",
      "A row of red discount price tags on clothes hanging on a rail",
      "A yellow clearance sticker slapped over an old price on a product box"]),
    (r"\bvot(e|es|er|ers|ing)\b|\bballot\w*|\bpolls?\b|polling",
     r"ballot|vote|voter|polling|election",
     ["A hand dropping a folded paper ballot into a ballot box",
      "A paper ballot paper with a pen resting on it inside a polling booth",
      "A voter's finger marked with indelible ink held up after voting"]),
    (r"\belections?\b|electoral",
     r"ballot|vote|polling|election|campaign",
     ["Rows of steel ballot boxes lined up in a counting hall",
      "Election campaign posters pasted along a city wall, faces blurred"]),
    (r"\bparliament\b|lok sabha|rajya sabha|lawmakers?|\bmps\b",
     r"parliament|chamber|assembly|legislat",
     ["The circular chamber of a national parliament with rows of green benches"]),
    (r"supreme court|high court|\bcourts?\b|\bjudges?\b|judiciary|verdict|ruling",
     r"court|judge|gavel|bench|robe|law",
     ["A wooden judge's gavel resting on a sound block in a courtroom",
      "The empty bench of a high court under bright lights"]),
    (r"\bpolice\b(?! the| it| them| their)|\bcops?\b|police officers?",
     r"police|officer|baton|barricade|riot|uniform",
     ["Police officers in riot gear standing in a line, seen from behind",
      "Metal police barricades across a city road"]),
    (r"\barrest\w*|\bjail\w*|\bprison\w*|\bdetain\w*|custody",
     r"handcuff|cell|prison|jail|bars|arrest|police van",
     ["A pair of steel handcuffs on a table", "The barred door of a prison cell"]),
    (r"protest\w*|demonstrat\w*|\bmarch(ed|es|ing)?\b|rally|rallies",
     r"protest|placard|crowd|march|banner|rally",
     ["A crowd holding blank protest placards seen from behind",
      "Protesters marching down a wide avenue holding banners, faces too small to see"]),
    (r"journalist\w*|reporter\w*|\bpress\b|newspaper\w*|\bmedia\b|news\b",
     r"newspaper|journalist|reporter|press|microphone|camera|news",
     ["A stack of folded newspapers on a news-stand, headlines blurred",
      "A press photographer's camera and a reporter's notebook on a desk"]),
    (r"\btelevision\b|\btv\b|tv channels?|news channels?",
     r"tv|television|screen|studio",
     ["A television news studio with bright lights and an empty anchor desk"]),
    (r"internet|online|website|\bweb\b",
     r"internet|laptop|phone|screen|cable|router|web",
     ["A Wi-Fi router with blinking lights on a desk", "Hands typing on a laptop in a dark room"]),
    (r"\bphones?\b|smartphone\w*|\bapps?\b",
     r"phone|smartphone|app|screen",
     ["A hand holding a smartphone with a glowing screen, content blurred"]),
    (r"subscri\w+",
     r"subscri|phone|app|card|statement|screen",
     ["A smartphone showing a monthly subscription renewal screen, text blurred",
      "A bank statement with a repeating monthly subscription charge highlighted, figures blurred"]),
    (r"free trial",
     r"trial|phone|app|screen|calendar",
     ["A calendar with day 8 circled in red next to a phone"]),
    (r"credit cards?|debit cards?|bank cards?|\bcard\b",
     r"card",
     ["A credit card held over a card payment terminal"]),
    (r"\bbanks?\b|banking",
     r"bank|vault|atm|card|cash",
     ["The stone front of a bank with tall columns", "A cash machine screen glowing on a street at night"]),
    (r"\bloans?\b|\bdebts?\b|\bowe\w*|borrow\w*|interest rates?",
     r"loan|debt|bill|statement|calculator|red",
     ["A pile of unpaid bills stamped OVERDUE in red", "A calculator on top of a loan agreement, text blurred"]),
    (r"\btax(es|ed)?\b|income tax",
     r"tax|form|calculator|receipt",
     ["A tax return form on a desk beside a calculator, text blurred"]),
    (r"\badvert\w*|\bads?\b|advertising|billboards?|marketing|publicity|campaign\w*",
     r"advert|billboard|poster|ad\b|marketing|campaign",
     ["A giant roadside billboard lit up at night, image blurred",
      "Rows of advertising posters in a subway station, images blurred"]),
    (r"\bprices?\b|pric(ed|ing)",
     r"price|tag|label|receipt|shelf",
     ["Price labels on a supermarket shelf, close-up"]),
    (r"supermarkets?|grocer\w*|\bshop(s|ping|per|pers)?\b|\bstores?\b|retail\w*",
     r"shop|store|supermarket|shelf|trolley|basket|checkout",
     ["A supermarket aisle with packed shelves and a shopping trolley",
      "Shoppers with bags walking along a high street, seen from behind"]),
    (r"checkout|basket|\bcart\b",
     r"checkout|basket|cart|trolley|till",
     ["A shopping basket full of items at a supermarket checkout"]),
    (r"receipts?|\bbill\b|invoice\w*",
     r"receipt|bill|invoice",
     ["A long paper till receipt curling on a counter, figures blurred"]),
    (r"\bmoney\b|\bcash\b|\bpounds\b|\bdollars\b|\brupees\b|\bcrore\b|\blakh\b|\bbillion\b|\bmillion\b",
     r"money|cash|note|coin|wallet|crore|rupee|pound|dollar|bank",
     ["A thick stack of banknotes held together with a paper band",
      "Coins and banknotes spilling out of an open wallet"]),
    (r"\bsalar\w*|\bwages?\b|paycheck|payslip",
     r"salary|wage|payslip|pay",
     ["A payslip on a desk next to a calculator, figures blurred"]),
    (r"\brent\b|mortgage|landlord|housing",
     r"rent|house|home|key|mortgage|flat",
     ["A set of house keys on a rental agreement, text blurred"]),
    (r"insurance|insur\w+",
     r"insur|policy|umbrella|form",
     ["An insurance policy document with a pen on top, text blurred"]),
    (r"\bscam\w*|fraud\w*|con artist|swindl\w*",
     r"scam|fraud|phone|hook|warning|mask|con",
     ["A phone showing a suspicious text message warning, content blurred",
      "A fishing hook with a banknote on it"]),
    (r"lotter\w+|jackpot|gambl\w*|casino",
     r"lotter|ticket|casino|jackpot|chips|dice",
     ["A scratched lottery ticket and a coin on a table", "Casino chips stacked on a green felt table"]),
    (r"stock market|shares\b|investors?|wall street",
     r"stock|trading|chart|screen|exchange",
     ["A trading screen full of red and green stock prices"]),
    (r"bitcoin|crypto\w*|tokens?\b",
     r"bitcoin|crypto|coin|token",
     ["A gold bitcoin coin on a computer keyboard"]),
    (r"\bfactor(y|ies)\b|manufactur\w*",
     r"factory|machine|assembly",
     ["A factory floor with an assembly line and machines"]),
    (r"vaccin\w+|\bcovid\b|pandemic",
     r"vaccin|syringe|vial|mask",
     ["A nurse's gloved hands filling a syringe from a vaccine vial"]),
    (r"hospitals?|doctors?|patients?",
     r"hospital|doctor|ward|patient|medical",
     ["A hospital corridor with an empty bed"]),
    (r"universit\w+|students?|campus|college",
     r"universit|student|campus|college|lecture|library",
     ["University students with backpacks walking across a campus, seen from behind"]),
    (r"\bschools?\b|classroom",
     r"school|classroom|desk|pupil",
     ["An empty classroom with rows of desks"]),
    (r"\blibrary\b",
     r"library|books|reading",
     ["A university library reading room with long tables and shelves of books"]),
    (r"\bfarmers?\b|\bcrops?\b|\bharvest\w*",
     r"farm|crop|field|harvest|tractor",
     ["A farmer seen from behind walking through a green wheat field"]),
    (r"\brice\b|\bgrain\b|ration\w*|food",
     r"rice|grain|sack|food|ration",
     ["Sacks of rice and grain stacked in a warehouse"]),
    (r"petrol|\bfuel\b|\bgas prices?\b",
     r"petrol|fuel|pump|station",
     ["A fuel pump nozzle in a car at a petrol station"]),
    (r"\bgym\b|gym membership",
     r"gym|treadmill|weights|dumbbell",
     ["An empty gym with rows of treadmills"]),
    (r"countdown|\btimer\b|deadline|ticking",
     r"clock|timer|countdown|hourglass|watch",
     ["A digital countdown timer on a screen running out"]),
    (r"\bcalendar\b|\bdeadline\b",
     r"calendar",
     ["A wall calendar with a date circled in red"]),
    (r"\bstadium\b|cricket",
     r"stadium|cricket|pitch",
     ["A packed cricket stadium under floodlights, seen from high above"]),
    (r"bulldozers?|demoli\w+",
     r"bulldozer|demoli|rubble",
     ["A yellow bulldozer beside a pile of rubble from a demolished house"]),
    (r"internet shutdowns?|shut down the internet|cut the internet",
     r"signal|router|phone|internet",
     ["A phone screen showing no signal in a dark room"]),
    (r"spyware|hack\w*|surveillance",
     r"spy|hack|code|camera|surveillance|phone",
     ["A security camera on a pole pointing down at a street",
      "Green code on a laptop screen in a dark room"]),
    (r"riots?|violence|mob\b",
     r"riot|smoke|fire|burn|broken|mob",
     ["Smoke rising over a city street with a burnt-out shop"]),
    (r"\bdonations?\b|\bdonors?\b|funding|\bbonds?\b",
     r"donat|envelope|cash|bond|money",
     ["A sealed brown envelope full of cash slid across a desk"]),
    (r"\bdocumentar\w+|\bfilm\b|\bbbc\b",
     r"documentar|film|camera|screen|tv",
     ["A film camera on a tripod pointed at an empty room"]),
]
_COMPILED = [(re.compile(rf"\b(?:{say})", re.I), re.compile(show, re.I), pics) for say, show, pics in CONCEPTS]

# ---- 1. named subjects -----------------------------------------------------------------------------------------
_STOP = set("""I A An The And But So Or Nor For Yet Then Now Here There This That These Those It Its He She They We You
His Her Their Our Your Who What Why How When Where Which Whose Whom If Unless Until Because Since While As At By In On
Of To From With Without Into Onto Over Under After Before Even Just Only Still Also Not No Yes Every Each All Some Any
One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Twenty Hundred Thousand Million Billion First Second
Third Last Next Most More Less Many Much Few Watch Notice Imagine Remember Look Guess Meet Let Tonight Today Yesterday
Tomorrow Monday Tuesday Wednesday Thursday Friday Saturday Sunday January February March April May June July August
September October November December Mr Mrs Ms Dr Part Move Chapter Fun Fact Fake Real Arrests Elections Researchers
Critics Supporters Students Police Officials Their Everywhere Nowhere Nobody Somebody Everyone Anyone Okay Ok Well
Right Wrong True False Yes Hi Hello Thanks Sorry Please Wait Stop Same Other Another Such Like Unlike Again Once
Twice Ever Never Always Sometimes Often Maybe Perhaps Almost Nearly About Around Is Are Was Were Be Been Has Have Had
Do Does Did Can Could Will Would Shall Should May Might Must Do Don't Doesn't Didn't Isn't Aren't Wasn't Weren't It's
That's There's Here's What's Who's He's She's They're We're You're I'm Let's Can't Won't""".split())
_SKIP_ACRONYMS = {"OK", "TV", "AI", "PM", "CEO", "GDP", "USD", "GBP", "INR", "PDF", "SMS", "UPI", "ATM", "VAT", "ID",
                  "MP", "MPS", "UK", "US", "USA", "EU", "UN", "AM", "FM", "AD", "BC", "DNA", "IQ", "HR", "PR", "CCTV",
                  "MAX", "AP", "LLC", "INC", "PLC", "LTD", "NHS"}
_ROLE_WORDS = {"leader", "leaders", "minister", "ministers", "government", "MP", "MPs", "chief", "spokesperson",
               "candidate", "official", "officials", "member", "members", "wing", "workers", "supporters"}
_TITLES = re.compile(r"^(?:PM|Prime Minister|President|Justice|Chief Justice|Mr|Mrs|Ms|Dr|Sir|Lord|Lady|Judge|Senator|"
                     r"Minister|Chief Minister|CM|General|King|Queen|Prince|Princess)\s+")
_SPAN = re.compile(r"\b(?:[A-Z][\w'’.-]*|[A-Z]{2,6})(?:\s+(?:of|the|and|for|de|von|van|al)?\s*(?:[A-Z][\w'’.-]*|[A-Z]{2,6}))*")
COUNTRIES = ("India", "Pakistan", "Bangladesh", "China", "Britain", "United Kingdom", "England", "France", "Germany",
             "Italy", "Spain", "Japan", "Russia", "Australia", "Canada", "America", "United States", "Brazil", "Nigeria",
             "Kenya", "South Africa", "Ireland", "Scotland", "Turkey", "Hungary", "Israel", "Europe", "Asia", "Africa",
             "Wales", "London", "New York", "Washington")

MAX_PER_SUBJECT = 6        # a named subject is shown at most this many times in one video
GAP_BEATS = 6              # ... and not again within this many beats
CONCEPT_GAP = 5            # an everyday thing is shown again only after this many beats
MAX_PER_CONCEPT = 4


def _sentences(text: str) -> list[tuple[int, str]]:
    out, start = [], 0
    for m in re.finditer(r"[.!?]+[\"'”’)]*\s+", text):
        out.append((start, text[start:m.end()]))
        start = m.end()
    if start < len(text):
        out.append((start, text[start:]))
    return out


def proper_nouns(text: str, known: set[str]) -> list[str]:
    """Names in a piece of narration, in order: "Narendra Modi", "BJP", "Supreme Court", "Rahul Gandhi". A single
    capitalised word at the start of a sentence only counts if the script also uses it mid-sentence (so "Modi has
    said..." counts, "Researchers say..." does not)."""
    names: list[str] = []
    for _, sent in _sentences(text):
        for m in _SPAN.finditer(sent):
            raw = m.group(0).strip(" .,'’-")
            # "India's Covid" / "Delhi and Mumbai": a possessive or "and" separates two names
            for piece in re.split(r"['’]s\s+|\s+and\s+", raw):
                piece = re.sub(r"['’]s$", "", piece.strip())
                words = piece.split()
                stripped = False
                while words and (words[0] in _STOP or words[0].islower()):
                    words, stripped = words[1:], True
                while words and (words[-1].islower() or words[-1] in _SKIP_ACRONYMS or words[-1] in _ROLE_WORDS):
                    words = words[:-1]
                lead = m.start() == len(sent) - len(sent.lstrip()) and piece is not None and raw.startswith(piece)
                if lead and not stripped and len(words) > 1 and words[0] not in known and not words[0].isupper():
                    words = words[1:]            # "Founder Trevor Milton", "Called MCAS": a sentence-start word
                if words:
                    _keep(names, words, sent, m.start(), known)
    return list(dict.fromkeys(names))


def _keep(names: list[str], words: list[str], sent: str, at: int, known: set[str]) -> None:
    span = " ".join(words)
    if len(words) == 1:
        w = words[0]
        if w.isupper() and len(w) >= 2:
            if w in _SKIP_ACRONYMS:
                return
        elif w in _STOP or len(w) < 3:
            return
        elif at == len(sent) - len(sent.lstrip()) and w not in known:
            return                        # sentence start: needs mid-sentence evidence
    if span in COUNTRIES:
        return                            # countries have their own Map/Globe graphics
    names.append(span)


def mid_sentence_names(script: str) -> set[str]:
    """Real proper nouns: capitalised words that appear somewhere other than the start of a sentence, or that the
    script never writes in lower case ("Congress called it..." - there is no "congress" anywhere)."""
    lower = set(re.findall(r"\b[a-z][\w'’-]*", script))
    found = {w for w in re.findall(r"\b[A-Z][a-z][\w'’-]+", script) if w.lower() not in lower and w not in _STOP}
    for _, sent in _sentences(script):
        body = sent.strip()
        for m in re.finditer(r"(?<=[\w,;:’'\"]\s)([A-Z][\w'’.-]+)", body):
            found.add(re.sub(r"['’]s$", "", m.group(1)).strip(".,"))
    return found


def context_country(script: str) -> str:
    counts = {c: len(re.findall(rf"\b{re.escape(c)}\b", script)) for c in COUNTRIES}
    best = max(counts, key=counts.get) if counts else ""
    return best if counts.get(best, 0) >= 3 else ""


def _clean(name: str) -> str:
    return _TITLES.sub("", name).strip()


def _protected(b: dict) -> bool:
    extra = b.get("extra") or {}
    return bool(b.get("chart") or b.get("stock") or extra.get("split") or extra.get("archive")
                or any(extra.get(k) for k in ("map", "globe", "steps", "timeline", "icons", "chapter", "quote", "screen",
                                               "document", "statement", "object", "article", "chat", "search", "pie",
                                               "squares", "shade", "timer", "receipt")))


def fictional_names(script: str) -> set[str]:
    """Names the script itself calls made-up ("Meet Sam. Sam is fictional", "Imagine Priya...")."""
    out = set()
    for _, sent in _sentences(script):
        if re.search(r"\b(fictional|fictitious|imaginary|made[- ]up|invented|imagine|composite|not (a )?real)\b", sent, re.I):
            out |= {w for w in re.findall(r"\b[A-Z][a-z]{2,}\b", sent) if w not in _STOP}
    return out


def enrich(plan, script: str) -> None:
    """Marks beats whose words name a subject (beat["named"]) and swaps in literal pictures for everyday things
    the words mention but the picture doesn't show."""
    known = mid_sentence_names(script)
    # what this script is about, to tell "Modi - Prime Minister of India" from another Modi
    counts = {w: len(re.findall(rf"\b{re.escape(w)}\b", script)) for w in known if len(w) > 3}
    country = context_country(script)
    topic = [country] + [w for w, _ in sorted(counts.items(), key=lambda x: -x[1])[:8]]
    made_up = {n.lower() for n in fictional_names(script)}
    for s in plan.scenes:       # the writer's on-screen labels: "Text: LEAH · FICTIONAL"
        for label in [s.overlay] + [str(b.get("overlay") or "") for b in s.beats]:
            if re.search(r"fictional|illustration|example|imaginary", label or "", re.I):
                made_up |= {w.lower() for w in re.findall(r"[A-Za-z]{3,}", label)} - {"fictional", "illustration",
                                                                                       "example", "imaginary"}
    # a writer's line that carries a graphic keeps all its pictures, even the part after the graphic
    held = {b.get("line") for sc in plan.scenes for b in sc.beats if b.get("line") is not None and _protected(b)}
    seen_subject: dict[str, list[int]] = {}
    seen_concept: dict[int, list[int]] = {}
    n = -1
    for s in plan.scenes:
        beats = s.beats or [{"text": s.narration, "visual": s.visual, "extra": {}, "_scene": True}]
        prev = None
        for b in beats:
            n += 1
            follows_graphic = prev is not None and _protected(prev) and prev.get("visual") == b.get("visual")
            prev = b
            if b.get("literal_done"):
                continue
            b["literal_done"] = True
            if _protected(b) or follows_graphic or (b.get("line") is not None and b.get("line") in held):
                continue
            text = str(b.get("text") or "")
            visual = str(b.get("visual") or "")
            # 1. a named subject the picture doesn't already show by name
            for name in proper_nouns(text, known):
                key = _clean(name).lower()
                if not key or key in visual.lower() or any(w in made_up for w in key.split()):
                    continue
                shown = seen_subject.setdefault(key, [])
                if len(shown) >= MAX_PER_SUBJECT or (shown and n - shown[-1] < GAP_BEATS):
                    continue
                shown.append(n)
                b["named"] = {"name": _clean(name), "context": country, "topic": [t for t in topic if t]}
                break
            if b.get("named"):
                continue
            # 2. an everyday thing the words mention and the picture doesn't show
            for ci, (say, show, pics) in enumerate(_COMPILED):
                if not say.search(text) or show.search(visual):
                    continue
                used = seen_concept.setdefault(ci, [])
                if len(used) >= MAX_PER_CONCEPT or (used and n - used[-1] < CONCEPT_GAP):
                    continue
                b["writer_visual"] = visual           # kept: the storyboard can show what the writer asked for
                b["visual"] = pics[len(used) % len(pics)]
                b["literal"] = say.pattern
                used.append(n)
                break
        if s.beats:
            if s.beats[0].get("literal") and s.visual == s.beats[0].get("writer_visual"):
                s.visual = s.beats[0]["visual"]        # the scene's own picture is beat 1's: keep them in step
        elif beats[0].get("visual") != s.visual or beats[0].get("named"):
            s.visual = beats[0]["visual"]
            s.named = dict(beats[0].get("named") or {})
