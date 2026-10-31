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
    (r"electoral bonds?|चुनावी बॉन्ड|इलेक्टोरल बॉन्ड",
     r"bond|envelope|cash|donat",
     ["A sealed brown envelope full of cash slid across a desk", "A sealed envelope tied with string on a dark desk"]),
    (r"press conferences?",
     r"podium|microphone|press",
     ["An empty press-conference podium covered in microphones"]),
    (r"discount\w*|\d+ ?% off|half price|on sale|\bsale\b|bargain\w*|markdown",
     r"discount|sale|% ?off|price tag|clearance",
     ["A shop window of discounted clothes on hangers, bright red tags turned away",
      "A row of red discount price tags on clothes hanging on a rail",
      "A yellow clearance sticker slapped over an old price on a product box"]),
    (r"\bvot(e|es|er|ers|ing)\b|\bballot\w*|\bpolls?\b|polling|वोट|मतदा|मतपत्र",
     r"ballot|vote|voter|polling|election",
     ["A hand dropping a folded paper ballot into a ballot box",
      "A folded paper ballot and a pen inside a curtained polling booth",
      "A voter's finger marked with indelible ink held up after voting"]),
    (r"\belections?\b|electoral|चुनाव|निर्वाचन",
     r"ballot|vote|polling|election|campaign",
     ["Rows of steel ballot boxes lined up in a counting hall",
      "Strings of party flags and bunting over a city street at dusk"]),
    (r"\bparliament\b|lok sabha|rajya sabha|lawmakers?|\bmps\b|संसद|लोकसभा|लोक सभा|राज्यसभा",
     r"parliament|chamber|assembly|legislat",
     ["The circular chamber of a national parliament with rows of green benches"]),
    (r"supreme court|high court|\bcourts?\b|\bjudges?\b|judiciary|verdict|ruling|अदालत|न्यायालय|कोर्ट|जज",
     r"court|judge|gavel|bench|robe|law",
     ["A wooden judge's gavel resting on a sound block in a courtroom",
      "The empty bench of a high court under bright lights"]),
    (r"\bpolice\b(?! the| it| them| their)|\bcops?\b|police officers?|पुलिस",
     r"police|officer|baton|barricade|riot|uniform",
     ["Police officers in riot gear standing in a line, seen from behind",
      "Metal police barricades across a city road"]),
    (r"\barrest\w*|\bjail\w*|\bprison\w*|\bdetain\w*|custody|गिरफ़?्तार|जेल|हिरासत",
     r"handcuff|cell|prison|jail|bars|arrest|police van",
     ["A pair of steel handcuffs on a table", "The barred door of a prison cell"]),
    (r"protest\w*|demonstrat\w*|\bmarch(ed|es|ing)?\b|rally|rallies|प्रदर्शन|आंदोलन|विरोध|धरना|रैली",
     r"protest|placard|crowd|march|banner|rally",
     ["A crowd holding blank protest placards seen from behind",
      "Protesters marching down a wide avenue holding banners, faces too small to see"]),
    (r"journalist\w*|reporter\w*|\bpress\b|newspaper\w*|\bmedia\b|news\b|पत्रकार|मीडिया|अख़?बार",
     r"newspaper|journalist|reporter|press|microphone|camera|news",
     ["Bundles of newspapers tied with twine on a pavement at dawn, seen edge-on",
      "A press photographer's camera and a closed notebook on a desk"]),
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
     ["A hand holding a smartphone face-down on a kitchen table",
      "A stack of opened envelopes beside a coffee cup, seen from the side"]),
    (r"free trial",
     r"trial|phone|app|screen|calendar",
     ["An hourglass beside a phone lying face-down on a desk"]),
    (r"credit cards?|debit cards?|bank cards?|\bcard\b",
     r"card",
     ["A credit card held over a card payment terminal"]),
    (r"\bbanks?\b|banking",
     r"bank|vault|atm|card|cash",
     ["The stone front of a bank with tall columns", "A cash machine glowing on a street at night, seen from the side"]),
    (r"\bloans?\b|\bdebts?\b|\bowe\w*|borrow\w*|interest rates?",
     r"loan|debt|bill|statement|calculator|red",
     ["A tall pile of closed envelopes on a doormat", "A calculator on a closed folder under a desk lamp"]),
    (r"\btax(es|ed)?\b|income tax",
     r"tax|form|calculator|receipt",
     ["A calculator and a closed cardboard folder on a desk under a lamp"]),
    (r"\badvert\w*|\bads?\b|advertising|billboards?|marketing|publicity|campaign\w*",
     r"advert|billboard|poster|ad\b|marketing|campaign",
     ["A giant roadside billboard frame lit from below at night, seen from far below",
      "A busy subway platform with commuters walking past, motion blurred"]),
    (r"\bprices?\b|pric(ed|ing)",
     r"price|tag|label|receipt|shelf",
     ["A shopper's hand reaching for a product on a supermarket shelf"]),
    (r"supermarkets?|grocer\w*|\bshop(s|ping|per|pers)?\b|\bstores?\b|retail\w*",
     r"shop|store|supermarket|shelf|trolley|basket|checkout",
     ["A supermarket aisle with packed shelves and a shopping trolley",
      "Shoppers with bags walking along a high street, seen from behind"]),
    (r"checkout|basket|\bcart\b",
     r"checkout|basket|cart|trolley|till",
     ["A shopping basket full of items at a supermarket checkout"]),
    (r"receipts?|\bbill\b|invoice\w*",
     r"receipt|bill|invoice",
     ["A crumpled paper receipt curled on a counter, seen edge-on, out of focus"]),
    (r"\bmoney\b|\bcash\b|\bpounds\b|\bdollars\b|\brupees\b|[₹$£€]\s?\d|\b(?:rs\.?|inr|usd)\s?\d|"
     r"\bworth\s+(?:[₹$£€]\s?)?\d|रुपये|रुपए|नकद|पैसा|पैसे",
     r"money|cash|note|coin|wallet|crore|rupee|pound|dollar|bank",
     ["Bundles of banknotes tied with paper bands, seen from the side edge, shallow focus",
      "Coins spilling out of an open leather wallet on a wooden table"]),
    (r"\bsalar\w*|\bwages?\b|paycheck|payslip",
     r"salary|wage|payslip|pay",
     ["A worker's hands counting coins on a wooden table"]),
    (r"\brent\b|mortgage|landlord|housing",
     r"rent|house|home|key|mortgage|flat",
     ["A set of house keys hanging in an apartment door lock"]),
    (r"insurance|insur\w+",
     r"insur|policy|umbrella|form",
     ["An umbrella shielding a small model house from rain"]),
    (r"\bscam\w*|fraud\w*|con artist|swindl\w*",
     r"scam|fraud|phone|hook|warning|mask|con",
     ["A phone lying face-down on a dark table, its screen light spilling out",
      "A fishing hook with a banknote on it"]),
    (r"lotter\w+|jackpot|gambl\w*|casino",
     r"lotter|ticket|casino|jackpot|chips|dice",
     ["Casino chips stacked on a green felt table", "Dice tumbling across a green felt table"]),
    (r"stock market|shares\b|investors?|wall street",
     r"stock|trading|chart|screen|exchange",
     ["A trader's silhouette against walls of glowing screens, all out of focus"]),
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
     ["An hourglass with the last grains of sand falling, hard side light"]),
    (r"\bcalendar\b|\bdeadline\b",
     r"calendar",
     ["An hourglass on a desk beside a closed file folder"]),
    (r"\bstadium\b|cricket",
     r"stadium|cricket|pitch",
     ["A packed cricket stadium under floodlights, seen from high above"]),
    (r"bulldozers?|demoli\w+|बुलडोज़?र",
     r"bulldozer|demoli|rubble",
     ["A yellow bulldozer beside a pile of rubble from a demolished house"]),
    (r"internet shutdowns?|shut down the internet|cut the internet",
     r"signal|router|phone|internet",
     ["A phone lying face-down in a dark room beside a dead router"]),
    (r"spyware|hack\w*|surveillance",
     r"spy|hack|code|camera|surveillance|phone",
     ["A security camera on a pole pointing down at a street",
      "A laptop glowing in a dark room, its screen out of focus"]),
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
_COMPILED = [(re.compile(rf"(?:\b|(?=[₹$£€]))(?:{say})", re.I), re.compile(show, re.I), pics)
             for say, show, pics in CONCEPTS]

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
                  "MAX", "AP", "LLC", "PLC", "LTD", "NHS", "SIR", "RTI", "IAS", "IPS", "CEC", "CJI", "LOP", "FIR",
                  "BLO", "NOC", "GDP", "MLA", "MLAS"}
_GROUPS = {"muslim", "muslims", "hindu", "hindus", "christian", "christians", "sikh", "sikhs", "jain", "jains",
           "buddhist", "buddhists", "dalit", "dalits", "adivasi", "adivasis", "tribal", "tribals", "vokkaliga",
           "vokkaligas", "lingayat", "lingayats", "brahmin", "brahmins", "obc", "obcs", "jat", "jats", "maratha",
           "marathas", "yadav", "yadavs", "rohingya", "bangladeshis"}
_ROLE_WORDS = {"leader", "leaders", "minister", "ministers", "government", "MP", "MPs", "chief", "spokesperson",
               "candidate", "official", "officials", "member", "members", "wing", "workers", "supporters"}
_ROLE_LOWER = {"minister", "ministers", "article", "section", "act", "chief", "president", "leader", "court", "party",
               "secretary", "spokesperson", "commissioner", "governor", "speaker", "judge", "justice"}
_TITLES = re.compile(r"^(?:(?:Union|Home|Finance|Defence|Defense|External Affairs|Foreign|Deputy|Former|Ex|Then|"
                     r"Railway|Education|Health|Law|Interior|Cabinet|State|Party|National|Congress|BJP|AAP|TMC|BSP|SP|JDU|RJD|NCP|"
                     r"CPI|CPM|DMK|INC|Shiv Sena|Chief|Election|Lok Sabha|Rajya Sabha|"
                     r"Opposition|Delhi|Kerala|Punjab|Bengal|Bihar|Gujarat|Assam|Karnataka|Maharashtra|UP|"
                     r"Uttar Pradesh|Tamil Nadu|Telangana|Rajasthan|Haryana|Odisha|Jharkhand|Goa|"
                     r"[A-Z][a-z]+ Pradesh)\s+)*"
                     r"(?:PM|Prime Minister|President|Justice|Chief Justice|Mr|Mrs|Ms|Dr|Sir|Lord|Lady|Judge|Senator|"
                     r"Minister|Chief Minister|CM|Deputy CM|General(?= [A-Z][a-z]+ [A-Z])|King|Queen|Prince|Princess|Leader of(?: the)? Opposition|"
                     r"LoP|Governor|Speaker|Secretary|Spokesperson|Commissioner|Chief|Chairman|Chairperson|Shri|Smt|Prof|"
                     r"(?:party )?[Pp]resident|[Cc]hief|MP|MLA|MLC|[Cc]andidate|[Ll]eader|[Ss]pokesperson|[Aa]dviser|[Mm]inister)\.?\s+(?=\S)")
# The channels' own names, said in a call to action ("Follow Print Facts"): never a subject to look up
BRANDS = ("Print Facts", "Hidden Economics", "Corporate Autopsies", "Modi's India", "Modi’s India", "India 2026",
          "CreatorForge")
_BRAND_RX = re.compile("|".join(re.escape(b) for b in BRANDS), re.I)
# Names in Hindi lines, as the English name Wikipedia knows them (longest first when matching)
HINDI_NAMES = {"नरेंद्र मोदी": "Narendra Modi", "मोदी": "Narendra Modi", "बीजेपी": "BJP", "भाजपा": "BJP",
               "राहुल गांधी": "Rahul Gandhi", "सोनिया गांधी": "Sonia Gandhi", "प्रियंका गांधी": "Priyanka Gandhi",
               "अमित शाह": "Amit Shah", "अरविंद केजरीवाल": "Arvind Kejriwal", "केजरीवाल": "Arvind Kejriwal",
               "ममता बनर्जी": "Mamata Banerjee", "योगी आदित्यनाथ": "Yogi Adityanath", "निर्मला सीतारमण": "Nirmala Sitharaman",
               "सुप्रीम कोर्ट": "Supreme Court of India", "सर्वोच्च न्यायालय": "Supreme Court of India",
               "चुनाव आयोग": "Election Commission of India", "निर्वाचन आयोग": "Election Commission of India",
               "ईडी": "ED", "प्रवर्तन निदेशालय": "ED", "सीबीआई": "CBI", "एनआईए": "NIA", "आरबीआई": "RBI",
               "आरएसएस": "RSS", "कांग्रेस": "Indian National Congress", "आम आदमी पार्टी": "Aam Aadmi Party",
               "संसद": "Parliament of India", "कॉकरोच जनता पार्टी": "Cockroach Janta Party",
               "जंतर मंतर": "Jantar Mantar", "इंडिया गेट": "India Gate", "लाल किला": "Red Fort",
               "जेफ़्री एपस्टीन": "Jeffrey Epstein", "जेफ्री एपस्टीन": "Jeffrey Epstein", "एपस्टीन": "Jeffrey Epstein",
               "घिसलेन मैक्सवेल": "Ghislaine Maxwell", "मैक्सवेल": "Ghislaine Maxwell",
               "वर्जीनिया जिउफ्रे": "Virginia Giuffre", "जिउफ्रे": "Virginia Giuffre",
               "अलेक्स अकोस्टा": "Alexander Acosta", "एलेक्स अकोस्टा": "Alexander Acosta", "अकोस्टा": "Alexander Acosta",
               "जेपी मॉर्गन": "JPMorgan Chase", "डॉयचे बैंक": "Deutsche Bank", "एफ़बीआई": "FBI", "एफबीआई": "FBI",
               "अमेरिकी न्याय विभाग": "United States Department of Justice",
               "पाम बीच": "Palm Beach, Florida", "मियामी हेराल्ड": "Miami Herald",
               "ज्ञानेश कुमार": "Gyanesh Kumar", "ज्ञानेश": "Gyanesh Kumar", "राजीव कुमार": "Rajiv Kumar (civil servant)",
               "सुखबीर सिंह संधू": "Sukhbir Singh Sandhu", "विवेक जोशी": "Vivek Joshi", "अखिलेश यादव": "Akhilesh Yadav",
               "अभिषेक बनर्जी": "Abhishek Banerjee", "डेरेक ओ'ब्रायन": "Derek O'Brien", "डेरेक ओब्रायन": "Derek O'Brien",
               "मल्लिकार्जुन खड़गे": "Mallikarjun Kharge", "खड़गे": "Mallikarjun Kharge", "ओम बिरला": "Om Birla",
               "सी पी राधाकृष्णन": "C. P. Radhakrishnan", "सूर्यकांत": "Surya Kant", "जस्टिस सूर्यकांत": "Surya Kant",
               "कॉकरोच जनता पार्टी": "Cockroach Janta Party", "रवि शंकर प्रसाद": "Ravi Shankar Prasad",
               "नीतीश कुमार": "Nitish Kumar", "तेजस्वी यादव": "Tejashwi Yadav", "महादेवपुरा": "Mahadevapura",
               "आलंद": "Aland, Karnataka", "रामलीला मैदान": "Ramlila Maidan", "प्रियंका गांधी": "Priyanka Gandhi"}
_HINDI_RX = re.compile("|".join(re.escape(k) for k in sorted(HINDI_NAMES, key=len, reverse=True)))
_SPAN = re.compile(r"\b(?:[A-Z][\w'’.-]*|[A-Z]{2,6})(?:\s+(?:of|the|and|for|de|von|van|al)?\s*(?:[A-Z][\w'’.-]*|[A-Z]{2,6}))*")
COUNTRIES = ("India", "Pakistan", "Bangladesh", "China", "Britain", "United Kingdom", "England", "France", "Germany",
             "Italy", "Spain", "Japan", "Russia", "Australia", "Canada", "America", "United States", "Brazil", "Nigeria",
             "Kenya", "South Africa", "Ireland", "Scotland", "Turkey", "Hungary", "Israel", "Europe", "Asia", "Africa",
             "Wales", "London", "New York", "Washington")

MAX_PER_SUBJECT = 6        # a named subject is shown at most this many times in one video
GAP_BEATS = 6              # ... and not again within this many beats
CONCEPT_GAP = 5            # an everyday thing is shown again only after this many beats
MAX_PER_CONCEPT = 4


_NOT_END = re.compile(r"(?:^|[\s.(])[A-Z]$|\b(?:Dr|Mr|Mrs|Ms|St|Jr|Sr|vs|No|Prof|Gen|Lt|Col|Smt|Shri|Rs)$")
_NUMBER_ABBR = re.compile(r"\b(?:No|Rs)$")


def _sentences(text: str) -> list[tuple[int, str]]:
    out, start = [], 0
    for m in re.finditer(r"[.!?।॥]+[\"'”’)]*\s+", text):
        if text[m.start()] == "." and _NOT_END.search(text[start:m.start()]) and not (
                _NUMBER_ABBR.search(text[start:m.start()]) and not text[m.end():m.end() + 1].isdigit()):
            continue                      # ("No. 5" and "Rs. 50" go on; "Is it? No. That needs..." ends)                      # an initial or a title: "J.P. Nadda", "Dr. Ambedkar", "the U.S. Senate"
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
    text = _BRAND_RX.sub(lambda m: " " * len(m.group(0)), text or "")
    text = re.sub(r"\bSC\s*/\s*STs?\b", lambda m: m.group(0).lower(), text)   # the SC/ST Act, not the Supreme Court
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
                if (lead and not stripped and len(words) > 1 and words[0] not in known and not words[0].isupper()
                        and _ordinary(words[0])):
                    words = words[1:]            # "Founder Trevor Milton", "Called MCAS": a sentence-start word
                    while words and (words[0] in _STOP or words[0].islower()):
                        words = words[1:]        # "Housing for All" -> "All", not "for All"
                if any(w.lower().strip("'’") in _GROUPS for w in words):
                    continue                     # "Muslims", "Indian Muslim", "Vokkaligas": a community, not a subject
                if words:
                    _keep(names, words, sent, m.start(), known)
    names += [HINDI_NAMES[m.group(0)] for m in _HINDI_RX.finditer(text)]
    return list(dict.fromkeys(names))


def _keep(names: list[str], words: list[str], sent: str, at: int, known: set[str]) -> None:
    span = " ".join(words)
    if len(words) == 1:
        w = words[0]
        if w.isupper() and len(w) >= 2:
            if w in _SKIP_ACRONYMS:
                return
        elif len(w) < 3 or _ordinary(w):
            return
        elif at == len(sent) - len(sent.lstrip()) and w not in known:
            return                        # sentence start: needs mid-sentence evidence
    if span in COUNTRIES:
        return                            # countries have their own Map/Globe graphics
    names.append(span)


# Everyday words that often open a sentence ("Thousands marched.", "People want answers."): never a name just because
# the script happens not to write them in lower case somewhere else.
_COMMON_STARTS = set("""people thousands millions hundreds billions dozens lakhs crores everyone everybody nobody someone
somebody anyone today tonight yesterday tomorrow now then later soon once meanwhile still critics officials experts
researchers scientists analysts voters citizens protesters students women men children kids families parents workers
farmers police lawyers judges journalists reporters leaders ministers politicians companies businesses banks shoppers
customers investors buyers sellers prices profits taxes nothing everything something anything most many some few
several others both all each every neither none ordinary rich poor young old state centre center opposition count
fine otherwise slogans democracy courts press authorities reputation anarchists government governments agencies
ministry nation country citizens youth power truth justice freedom silence question questions answer answers
examine follow watch look see read ask check consider think listen share subscribe comment tell remember picture
founder phones different fair cut defend turns freed top ye papa mummy beta bhai didi within inside promises promise rural urban home
housing termites x-ray infiltrators traitors patriot patriots
take give make keep show bring put get go come try call pay hold turn leave find run start ban jail silence arrest
""".split())


# Words shaped like ordinary English ("Dragged", "Officially", "Joblessness", "Accountability", "Saying")
_ORDINARY = re.compile(r"(?:(?<![emv])ed|ing|ly|ness|ity|ities|lty|tion|tions|sion|ment|ments|ance|ence|ise|ize|ate|ism|ists?|"
                       r"ful|less|ous|ive|able|ible)$")
_NUMBER_WORD = re.compile(r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|one|two|three|four|five|six|"
                          r"seven|eight|nine|ten|hundred|thousand)\b[-\w]*$", re.I)


_FAMOUS = {"Congress", "Parliament", "Senate", "Pentagon", "Kremlin", "Vatican", "Brexit", "Modi", "Gandhi", "Trump",
           "Putin", "Biden", "Amazon", "Google", "Apple", "Facebook", "Meta", "Twitter", "Netflix", "Tesla", "Boeing"}
_CONTRACTION = re.compile(r"['’](ll|d|re|ve|m|s)$|n['’]t$", re.I)


def _ordinary(w: str) -> bool:
    """An everyday English word, a nationality or a number, however it is capitalised."""
    low = w.lower()
    return (w in _STOP or low in _COMMON_STARTS or bool(_ORDINARY.search(low)) or w in _DEMONYM.values()
            or bool(_NUMBER_WORD.match(w)) or bool(_CONTRACTION.search(w)) or low in _ROLE_LOWER)


def mid_sentence_names(script: str) -> set[str]:
    """Real proper nouns: capitalised words that appear somewhere other than the start of a sentence, or that the
    script never writes in lower case ("Congress called it..." - there is no "congress" anywhere) and that isn't
    shaped like an ordinary word ("Dragged into...", "Officially,", "Accountability." are not names)."""
    lower = set(re.findall(r"\b[a-z][\w'’-]*", script))
    caps = re.findall(r"\b[A-Z][a-z][\w'’-]+", script)
    # only at sentence starts: a name if it recurs ("Vadra got bail... Vadra said") or is a well-known one-word
    # institution - a one-off "Cut." / "Defend it." / "Turns out" is an ordinary word
    found = {w for w in caps
             if w.lower() not in lower and w not in _STOP and not _ordinary(w)
             and (caps.count(w) >= 2 or w in _FAMOUS)}
    for _, sent in _sentences(script):
        body = sent.strip()
        for m in re.finditer(r"(?<=[\w,;:’'\"]\s)([A-Z][\w'’.-]+)", body):
            found.add(re.sub(r"['’]s$", "", m.group(1)).strip(".,"))
    return found


# Cities a story can be set in, with the names that place a line there ("Jantar Mantar" is Delhi's, not Jaipur's).
CITIES = {"New Delhi": ("Delhi", "New Delhi", "Jantar Mantar", "India Gate", "Connaught Place", "Kartavya Path",
                        "Janpath", "Ramlila Maidan", "Okhla", "Tihar", "Rouse Avenue", "Raisina"),
          "Mumbai": ("Mumbai", "Bombay"), "Kolkata": ("Kolkata", "Calcutta"), "Chennai": ("Chennai", "Madras"),
          "Bengaluru": ("Bengaluru", "Bangalore"), "Hyderabad": ("Hyderabad",), "Ahmedabad": ("Ahmedabad",),
          "Lucknow": ("Lucknow",), "Patna": ("Patna",), "Jaipur": ("Jaipur",), "Srinagar": ("Srinagar",),
          "Pune": ("Pune",), "Varanasi": ("Varanasi",)}


CITIES_HINDI = {"New Delhi": ("दिल्ली", "जंतर मंतर", "इंडिया गेट", "रामलीला मैदान", "तिहाड़"), "Mumbai": ("मुंबई",),
                "Kolkata": ("कोलकाता",), "Chennai": ("चेन्नई",), "Bengaluru": ("बेंगलुरु",), "Hyderabad": ("हैदराबाद",),
                "Lucknow": ("लखनऊ",), "Patna": ("पटना",), "Jaipur": ("जयपुर",), "Varanasi": ("वाराणसी",)}


def context_city(script: str) -> str:
    """The city the story mostly happens in ("New Delhi" for a script about protests at Jantar Mantar), or ""."""
    counts = {c: sum(len(re.findall(rf"\b{re.escape(n)}\b", script)) for n in names) for c, names in CITIES.items()}
    for c, names in CITIES_HINDI.items():
        counts[c] += sum(script.count(n) for n in names)     # Devanagari: no \b (vowel signs aren't word characters)
    best = max(counts, key=counts.get)
    return best if counts[best] >= 2 else ""


def full_names(script: str, known: set[str]) -> dict[str, list[str]]:
    """Each first or last name -> the full names in this script it belongs to: "Rahul" -> ["Rahul Gandhi"],
    "Shah" -> ["Amit Shah"], "Gandhi" -> ["Rahul Gandhi", "Sonia Gandhi", ...] (most mentioned first)."""
    counts: dict[str, int] = {}
    for _, sent in _sentences(script):
        for name in proper_nouns(sent, known):
            name = _clean(name)
            if len(name.split()) >= 2 and not name.isupper():
                counts[name] = counts.get(name, 0) + 1
    out: dict[str, list[str]] = {}
    for name in sorted(counts, key=lambda n: -counts[n]):
        words = name.split()
        for w in {words[0], words[-1]}:
            out.setdefault(w.lower(), []).append(name)
    return out


def expand_name(name: str, names: dict[str, list[str]]) -> str | None:
    """A lone first or last name as the full name this script uses ("Shah" -> "Amit Shah"). None when it could
    be several people here ("Gandhi" in a script about Rahul, Sonia and Priyanka Gandhi): better no picture than
    the wrong face."""
    if len(name.split()) != 1 or name.isupper():
        return name
    if name in COUNTRIES or any(name in v for v in CITIES.values()):
        return name                       # "Delhi" is the city, not "Delhi Police"
    hits = names.get(name.lower(), [])
    if not hits:
        return name
    return hits[0] if len(hits) == 1 else None


_MOVEMENT = re.compile(r"\b(Party|Movement|Andolan|Morcha|Union|Sangathan|Front|Sena|Collective)\b")
_MAINSTREAM = {"bharatiya janata party", "indian national congress", "aam aadmi party", "samajwadi party",
               "communist party of india", "nationalist congress party", "bahujan samaj party", "janata dal"}
_ACTION = re.compile(r"\b(protest\w*|march\w*|rall(?:y|ies)|demonstrat\w*|detain\w*|detention\w*|arrest\w*|"
                     r"crackdown|agitation|dharna|sit-in|marchers|protesters|activists|founder)\b", re.I)


def movement(script: str, known: set[str]) -> str:
    """The protest movement this story is about ("Cockroach Janta Party"), so a line about "the protest" or "the
    arrests" shows that movement - its people, its marches - and not a generic crowd. "" when there isn't one."""
    counts: dict[str, int] = {}
    for _, sent in _sentences(script):
        for name in proper_nouns(sent, known):
            name = _clean(name)
            if len(name.split()) >= 2 and _MOVEMENT.search(name) and name.lower() not in _MAINSTREAM:
                counts[name] = counts.get(name, 0) + 1
    if re.search(r"\bCJP\b|cockroach", script, re.I):
        counts["Cockroach Janta Party"] = counts.get("Cockroach Janta Party", 0) + 2
    best = max(counts, key=counts.get) if counts else ""
    return best if best and counts[best] >= 2 else ""


_COUNTRY_CUES = {"India": ("Indian", "Indians", "Delhi", "Mumbai", "Kolkata", "Chennai", "Bengaluru", "Lok Sabha",
                            "Rajya Sabha", "BJP", "Modi", "Uttar Pradesh", "Bihar", "Kerala", "Gujarat", "Punjab",
                            "Maharashtra", "Karnataka", "West Bengal", "Tamil Nadu", "Assam", "Kashmir", "crore", "lakh"),
                 "United States": ("American", "Americans", "America", "US", "U.S.", "Florida", "California", "Texas",
                                   "FBI", "Congress of the United States")}
_COUNTRY_HINDI = {"India": ("भारत", "हिंदुस्तान", "हिन्दुस्तान", "इंडिया", "दिल्ली", "मोदी", "बीजेपी", "भाजपा"),
                  "United States": ("अमेरिका", "अमेरिकी", "अमरीका", "न्यूयॉर्क", "न्यूयार्क", "फ़्लोरिडा", "फ्लोरिडा",
                                    "वॉशिंगटन", "एफ़बीआई", "एफबीआई", "व्हाइट हाउस")}


def context_country(script: str) -> str:
    """The country the story is about: its own name, its people ("Indian"), its cities, states and parties, and its
    Hindi names all count. A Hindi (Devanagari) script is about India unless it names somewhere else."""
    script = script or ""
    counts = {}
    for c in COUNTRIES:
        cues = (c,) + ((_DEMONYM[c],) if c in _DEMONYM else ()) + _COUNTRY_CUES.get(c, ())
        counts[c] = sum(len(re.findall(rf"\b{re.escape(w)}\b", script)) for w in cues)
        counts[c] += sum(script.count(w) for w in _COUNTRY_HINDI.get(c, ()))
    best = max(counts, key=counts.get) if counts else ""
    if counts.get(best, 0) < 3 and re.search(r"[\u0900-\u097F]{3}", script) and counts.get(best, 0) <= counts["India"]:
        return "India"
    return best if counts.get(best, 0) >= 3 else ""


def _clean(name: str) -> str:
    return _TITLES.sub("", name).strip()


def _protected(b: dict) -> bool:
    extra = b.get("extra") or {}
    return bool(b.get("chart") or b.get("stock") or extra.get("split") or extra.get("archive") or extra.get("clip")
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
    city = context_city(script)
    topic = [country] + [w for w, _ in sorted(counts.items(), key=lambda x: -x[1])[:8]]
    names = full_names(script, known)
    cause = movement(script, known)
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
            found = proper_nouns(text, known)
            if country and country != "India":
                # Hindi words for institutions mean the story's own country's ("संसद" in a US story is Congress)
                found = [{"Parliament of India": {"United States": "United States Congress",
                                                  "United Kingdom": "Parliament of the United Kingdom"}.get(country, ""),
                          "Supreme Court of India": f"Supreme Court of the {country}" if country == "United States"
                          else "", "Election Commission of India": ""}.get(n, n) for n in found]
                found = [n for n in found if n]
            found.sort(key=lambda nm: (bool(seen_subject.get(_clean(nm).lower())),     # not shown yet first
                                       len(nm.split()) < 2 or nm.isupper()))          # then full names
            for name in found:
                name = expand_name(_clean(name), names)
                if name and not _TITLES.sub("", f"{name} X").strip(" X"):
                    continue                  # "Home Minister", "Chief Justice" alone: whose photo? none
                if not name or (len(name.split()) == 1 and not name.isupper() and _ordinary(name)):
                    continue                  # "Gandhi" alone, with three Gandhis in the story: no guessing
                key = _clean(name).lower()
                if not key or key in visual.lower() or any(w in made_up for w in key.split()):
                    continue
                shown = seen_subject.setdefault(key, [])
                if len(shown) >= MAX_PER_SUBJECT or (shown and n - shown[-1] < GAP_BEATS):
                    continue
                shown.append(n)
                b["named"] = {"name": _clean(name), "context": country, "city": city, "topic": [t for t in topic if t]}
                break
            # 1b. a line about the protests or arrests shows the movement itself (its leaders, its marches)
            key = cause.lower()
            if not b.get("named") and cause and _ACTION.search(text) and key not in visual.lower():
                shown = seen_subject.setdefault(key, [])
                if len(shown) < MAX_PER_SUBJECT * 2 and not (shown and n - shown[-1] < 3):
                    shown.append(n)
                    b["named"] = {"name": cause, "context": country, "city": city, "topic": [t for t in topic if t],
                                  "movement": True}
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
                if "banknote" in b["visual"] and country:
                    # the story's own currency, as a real photo first (an AI note is a dollar with garbled print)
                    cur = {"India": "Indian rupee"}.get(country, "")
                    if cur:
                        b["visual"] = b["visual"].replace("banknotes", f"{cur} banknotes")
                        b.setdefault("stock", f"{cur.lower()} notes")
                used.append(n)
                break
        if s.beats:
            if s.beats[0].get("literal") and s.visual == s.beats[0].get("writer_visual"):
                s.visual = s.beats[0]["visual"]        # the scene's own picture is beat 1's: keep them in step
        elif beats[0].get("visual") != s.visual or beats[0].get("named"):
            s.visual = beats[0]["visual"]
            s.named = dict(beats[0].get("named") or {})


# ---- the story's country, for AI pictures ---------------------------------------------------------------------
_DEMONYM = {"India": "Indian", "Pakistan": "Pakistani", "Bangladesh": "Bangladeshi", "China": "Chinese",
            "Britain": "British", "United Kingdom": "British", "England": "English", "Scotland": "Scottish",
            "France": "French", "Germany": "German", "Italy": "Italian", "Spain": "Spanish", "Japan": "Japanese",
            "Russia": "Russian", "Australia": "Australian", "Canada": "Canadian", "America": "American",
            "United States": "American", "Brazil": "Brazilian", "Nigeria": "Nigerian", "Kenya": "Kenyan",
            "South Africa": "South African", "Ireland": "Irish", "Turkey": "Turkish", "Hungary": "Hungarian",
            "Israel": "Israeli"}
_PLACE = re.compile(r"\b(street|road|avenue|lane|city|town|village|market|shop|office|building|court\w*|judge|police|"
                    r"officer|crowd|protest\w*|march\w*|rally|voter\w*|polling|ballot|parliament|chamber|campus|"
                    r"universit\w*|student\w*|school|hospital|newsroom|reporter|journalist|station|metro|train|bus|"
                    r"prison|jail|cell|clerk|government|minister|politician|people|person|man|woman|family|worker\w*|"
                    r"farmer\w*|crowd|shoppers?|queue|line of|neighbourhood|home|house|flag\w*|billboard|poster\w*)\b",
                    re.I)
_HAS_PLACE = re.compile(r"\b(" + "|".join(sorted({*COUNTRIES, *_DEMONYM.values(), "Delhi", "Mumbai", "London",
                                                   "Washington", "Tokyo", "Paris", "Hong Kong", "Brooklyn"},
                                                  key=len, reverse=True)) + r")\b", re.I)


def setting_for(visual: str, country: str, city: str = "") -> str:
    """A short prompt addition that puts a people/place/institution picture in the story's country and city ("in
    New Delhi, India, Indian people and Indian buildings"); empty when the picture already names a place or shows
    only objects."""
    if not country or not _PLACE.search(visual or "") or _HAS_PLACE.search(visual or ""):
        return ""
    who = _DEMONYM.get(country, "")
    where = f"{city}, {country}" if city else country
    extra = ", modern capital-city streets and government buildings" if city == "New Delhi" else ""
    return f"in {where}" + (f", {who} people, {who} buildings and streets" if who else "") + extra


# What a Delhi picture must not drift into: the desert forts and painted palaces image models reach for when told "India"
CITY_NEGATIVE = {"New Delhi": ", Rajasthan, desert, sand dunes, fort on a hill, Jaipur pink city, palace courtyard, camels"}
