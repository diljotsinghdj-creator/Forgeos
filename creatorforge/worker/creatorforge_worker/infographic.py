"""Narration -> one infographic per line, with no directions from the writer.

    f = facts(line)                    # what the line says that can be shown: numbers, places, people, dates...
    g = pick(line, f, n, total, prev)  # the infographic that shows it (English on screen, nothing invented)
    ok = mute_test(f, g)               # would a viewer get the line's key fact with the sound off?

An infographic shows a fact instead of saying it. The picker maps each kind of fact to the form that shows it best:
how many -> bars/coins/seats/big number, a share -> slice, change -> trend, where -> map/route, when -> calendar/clock,
who said what -> news card/quote, false claims -> a stamp, things and ideas -> a drawn or real object. Labels are
built only from words in the line (dictionaries of common Hinglish words, names, places and publishers), so no fact
is ever invented; when the script AI is available it writes richer labels and this is the safety net."""
from __future__ import annotations

import re
import zlib

from . import vox_director as vd

# ---- dictionaries (Devanagari as narrations write it -> English for the screen) ------------------------------------
PEOPLE = {
    "नरेंद्र मोदी": "Narendra Modi", "मोदी": "Narendra Modi", "अमित शाह": "Amit Shah", "शाह": "Amit Shah",
    "राहुल गांधी": "Rahul Gandhi", "सोनिया गांधी": "Sonia Gandhi", "अखिलेश यादव": "Akhilesh Yadav",
    "मुलायम सिंह": "Mulayam Singh Yadav", "अमित मालवीय": "Amit Malviya", "मालवीय": "Amit Malviya",
    "अरविंद केजरीवाल": "Arvind Kejriwal", "केजरीवाल": "Arvind Kejriwal", "ममता बनर्जी": "Mamata Banerjee",
    "योगी आदित्यनाथ": "Yogi Adityanath", "नीतीश कुमार": "Nitish Kumar", "सुब्रमण्यम स्वामी": "Subramanian Swamy",
    "मनमोहन सिंह": "Manmohan Singh", "इंदिरा गांधी": "Indira Gandhi", "जवाहरलाल नेहरू": "Jawaharlal Nehru",
    "नेहरू": "Jawaharlal Nehru", "महात्मा गांधी": "Mahatma Gandhi", "गांधी जी": "Mahatma Gandhi",
    "सरदार पटेल": "Vallabhbhai Patel", "अंबेडकर": "B. R. Ambedkar", "डोनाल्ड ट्रंप": "Donald Trump",
    "ट्रंप": "Donald Trump", "पुतिन": "Vladimir Putin", "शी जिनपिंग": "Xi Jinping", "एलन मस्क": "Elon Musk",
    "मुकेश अंबानी": "Mukesh Ambani", "अंबानी": "Mukesh Ambani", "गौतम अडानी": "Gautam Adani", "अडानी": "Gautam Adani",
    "रतन टाटा": "Ratan Tata"}
PARTIES = {"बीजेपी": "BJP", "भाजपा": "BJP", "कांग्रेस": "Congress", "आम आदमी पार्टी": "AAP", "सपा": "SP", "समाजवादी पार्टी": "SP",
           "बसपा": "BSP", "टीएमसी": "TMC", "डीएमके": "DMK", "एनडीए": "NDA", "इंडिया गठबंधन": "INDIA bloc", "शिवसेना": "Shiv Sena",
           "जेडीयू": "JDU", "आरजेडी": "RJD", "सीपीएम": "CPI(M)"}
PUBLISHERS = {"द क्विंट": "The Quint", "क्विंट": "The Quint", "द हिंदू": "The Hindu", "हिंदू": "The Hindu",
              "इंडियन एक्सप्रेस": "The Indian Express", "द वायर": "The Wire", "स्क्रॉल": "Scroll",
              "डेक्कन हेराल्ड": "Deccan Herald", "हिंदुस्तान टाइम्स": "Hindustan Times", "टाइम्स ऑफ़ इंडिया": "Times of India",
              "बीबीसी": "BBC", "रॉयटर्स": "Reuters", "अल जज़ीरा": "Al Jazeera", "वॉशिंगटन पोस्ट": "The Washington Post",
              "न्यूयॉर्क टाइम्स": "The New York Times", "ऑल्ट न्यूज़": "Alt News", "न्यूज़लॉन्ड्री": "Newslaundry",
              "द रिपोर्टर्स कलेक्टिव": "The Reporters' Collective", "इंडिया टुडे": "India Today", "एनडीटीवी": "NDTV",
              "प्रिंट": "ThePrint", "लाइव मिंट": "Mint", "इकोनॉमिक टाइम्स": "The Economic Times", "आरबीआई": "RBI",
              "सुप्रीम कोर्ट": "Supreme Court", "चुनाव आयोग": "Election Commission", "लोकसभा": "Lok Sabha"}
PLACES_MORE = {"कोटा": "Kota", "भारत": "India", "चीन": "China", "जापान": "Japan", "रूस": "Russia", "यूक्रेन": "Ukraine",
               "अमेरिका": "United States", "ब्रिटेन": "United Kingdom", "लंदन": "London", "पेरिस": "Paris",
               "न्यूयॉर्क": "New York", "दुबई": "Dubai", "सिंगापुर": "Singapore", "श्रीलंका": "Sri Lanka", "नेपाल": "Nepal",
               "बांग्लादेश": "Bangladesh", "पाकिस्तान": "Pakistan", "अफ़ग़ानिस्तान": "Afghanistan", "ईरान": "Iran",
               "इज़राइल": "Israel", "सऊदी अरब": "Saudi Arabia", "हैदराबाद": "Hyderabad", "अहमदाबाद": "Ahmedabad",
               "सूरत": "Surat", "इंदौर": "Indore", "भोपाल": "Bhopal", "नागपुर": "Nagpur", "वाराणसी": "Varanasi",
               "अयोध्या": "Ayodhya", "गोवा": "Goa", "असम": "Assam", "मणिपुर": "Manipur", "ओडिशा": "Odisha",
               "तमिलनाडु": "Tamil Nadu", "कर्नाटक": "Karnataka", "महाराष्ट्र": "Maharashtra", "बंगाल": "West Bengal",
               "हरियाणा": "Haryana", "उत्तराखंड": "Uttarakhand", "झारखंड": "Jharkhand", "छत्तीसगढ़": "Chhattisgarh",
               "मध्य प्रदेश": "Madhya Pradesh", "आंध्र प्रदेश": "Andhra Pradesh", "तेलंगाना": "Telangana", "लद्दाख": "Ladakh",
               "मुंद्रा": "Mundra", "ह्यूस्टन": "Houston", "न्यू जर्सी": "Newark"}
# common narration words -> short English for labels and headlines
CONCEPTS = {"झूठ": "lies", "झूठा": "false", "सच": "truth", "सच्चा": "true", "सच्चाई": "truth", "वायरल": "viral",
            "मैसेज": "message", "संदेश": "message", "व्हाट्सऐप": "WhatsApp", "ग्रुप": "groups", "नेटवर्क": "network",
            "चुनाव": "election", "वोट": "votes", "सीट": "seats", "सरकार": "government", "पार्टी": "party",
            "ट्रोल": "trolls", "ऐड": "ads", "विज्ञापन": "ads", "पैसा": "money", "पैसे": "money", "कंपनी": "company",
            "अदालत": "court", "कोर्ट": "court", "क़ानून": "law", "आरोप": "allegation", "पक्ष": "side", "इनकार": "denial",
            "कैंपेन": "campaign", "प्रचार": "propaganda", "नफ़रत": "hate", "डर": "fear", "भरोसा": "trust", "मशीन": "machine",
            "लोग": "people", "किसान": "farmers", "मज़दूर": "workers", "नौकरी": "jobs", "महंगाई": "inflation", "क़र्ज़": "debt",
            "टैक्स": "tax", "बजट": "budget", "रिपोर्ट": "report", "ख़बर": "news", "सवाल": "question", "जवाब": "answer",
            "सुबह": "morning", "रात": "night", "हर": "every", "दुनिया": "world", "देश": "country", "शहर": "city",
            "जहाज़": "ship", "कंटेनर": "container", "बंदरगाह": "port", "ट्रेन": "train", "फ़ोन": "phone", "वीडियो": "video",
            "फ़ेक": "fake", "फ़ैक्ट": "fact", "डेटा": "data", "पुलिस": "police", "जेल": "jail", "स्कूल": "school",
            "अस्पताल": "hospital", "पानी": "water", "बिजली": "power", "तेल": "oil", "सोना": "gold", "खाना": "food"}
# whole narration phrases -> a ready English headline (checked first, in the order they appear)
PHRASES = [("सच्चा हो या झूठा", "true or false"), ("सच हो या झूठ", "true or false"), ("कोई भी मैसेज", "any message"),
           ("वायरल कर सकते", "we can make it viral"), ("आगे भेजेंगे", "will you forward it?"), ("फ़ॉरवर्ड करेंगे", "will you forward it?"),
           ("कोई सच्चाई नहीं", "no truth in it"), ("सच्चाई नहीं", "not true"), ("फिर भी वो वायरल", "viral anyway"),
           ("स्वतंत्र रूप से नहीं", "not independently verified"), ("हर सुबह", "every morning"), ("एक ही मैसेज", "one message"),
           ("कितना बड़ा", "how big?"), ("किसने", "who did it?"), ("क्यों", "why?"), ("कैसे", "how?"), ("पहली बार", "first time"),
           ("सबसे बड़ा", "the biggest"), ("दुनिया में", "in the world"), ("करोड़ों", "crores"), ("लाखों", "lakhs")]
FALSE_WORDS = ("झूठ", "झूठा", "फ़ेक", "फेक", "ग़लत", "गलत", "बेबुनियाद", "सच्चाई नहीं", "कोई सच्चाई", "मनगढ़ंत", "भ्रामक")
MESSAGE_WORDS = ("मैसेज", "व्हाट्सऐप", "फ़ॉरवर्ड", "फॉरवर्ड", "ट्वीट", "पोस्ट", "संदेश", "ग्रुप्स")
SOURCE_CUES = ("के मुताबिक़", "के मुताबिक", "के अनुसार", "रिपोर्ट", "ने लिखा", "ने छापा", "की पड़ताल", "ने बताया")
SIDE_CUES = ("पक्ष", "इनकार", "बताते", "का कहना", "ने कहा कि ये", "आरोपों को", "खंडन")
SEAT_WORDS = ("सीट", "सीटें", "सीटों", "सांसद")
VEHICLE = {"जहाज़": "ship", "जहाज": "ship", "हवाई": "plane", "फ़्लाइट": "plane", "ट्रेन": "train", "कार": "car", "ट्रक": "truck"}


def _find(table: dict, line: str) -> list[str]:
    """Matches in the order they appear in the line (longest names first where they overlap)."""
    toks = vd._tokens(line)
    hits = []
    for hi, en in sorted(table.items(), key=lambda kv: -len(kv[0])):
        if vd._has(toks, hi) and en not in [h[1] for h in hits]:
            pos = vd._plain(line).find(vd._plain(hi))
            hits.append((pos if pos >= 0 else 10**6, en))
    return [en for _, en in sorted(hits)]


def _phrases(line: str) -> list[str]:
    plain = vd._plain(line)
    found = [(plain.find(vd._plain(hi)), vd._plain(hi), en) for hi, en in PHRASES if vd._plain(hi) in plain]
    # a phrase inside a longer matched phrase ("सच्चाई नहीं" in "कोई सच्चाई नहीं") is the same thing
    keep = [x for x in found if not any(x[1] != y[1] and x[1] in y[1] for y in found)]
    return [en for _, _, en in sorted(keep)]


def facts(line: str) -> dict:
    """Everything in a narration line that can be shown."""
    toks = vd._tokens(line)
    nums = []
    clock_h = {m.group(1) for m in re.finditer(r"(\S+)\s+बज", line)}
    for v, unit in vd._spoken_numbers(line):
        if unit == 1 and (1900 <= v <= 2100 or v < 10):
            continue                 # a year, or "two networks" - a count, not a figure to chart
        if unit == 1 and any(vd._HI_N.get(vd._plain(h)) == v for h in clock_h):
            continue                 # "आठ बजे" is a time
        nums.append({"value": v * unit, "shown": f"{v:g}" + (f" {vd._UNIT[unit]}" if unit in vd._UNIT else "")})
    for m in re.finditer(r"(?<![\d.])(\d[\d,]*(?:\.\d+)?)\s*(करोड़|लाख|crore|lakh|%|प्रतिशत)?", line):
        raw = m.group(1).replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        if (1900 <= v <= 2100 or v < 10) and not m.group(2):
            continue
        unit = {"करोड़": 10**7, "crore": 10**7, "लाख": 10**5, "lakh": 10**5}.get(m.group(2) or "", 1)
        nums.append({"value": v * unit, "shown": f"{m.group(1)}" + (f" {vd._UNIT[unit]}" if unit in vd._UNIT else
                                                                  ("%" if m.group(2) in ("%", "प्रतिशत") else ""))})
    money = any(vd._has(toks, w) for w in ("रुपये", "रुपए", "रुपया", "डॉलर")) or "₹" in line or "$" in line
    if money:
        for n in nums:
            if not n["shown"].startswith(("₹", "$")):
                n["shown"] = ("$" if "डॉलर" in line or "$" in line else "₹") + n["shown"]
    pct = vd._number(line) if any(w in vd._plain(line) for w in ("प्रतिशत", "फीसदी", "परसेंट")) or "%" in line else ""
    full, year = vd._date(line)
    years = sorted({int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", line)} |
                   {int(v) for v, u in vd._spoken_numbers(line) if u == 1 and 1900 <= v <= 2100})
    places = _find(vd.PLACES, line) + [p for p in _find(PLACES_MORE, line)]
    places = list(dict.fromkeys(places))
    return {
        "numbers": nums[:4], "money": money, "percent": pct, "date": full if full and re.search(r"\d", full.split()[0]) else "",
        "month_year": full, "years": years, "time": vd._clock(line), "places": places[:4],
        "people": _find(PEOPLE, line)[:2], "parties": _find(PARTIES, line)[:3], "publisher": (_find(PUBLISHERS, line) or [""])[0],
        "cited": any(c in vd._plain(line) for c in map(vd._plain, SOURCE_CUES)),
        "false": any(vd._plain(w) in vd._plain(line) for w in FALSE_WORDS),
        "message": any(vd._has(toks, w) for w in MESSAGE_WORDS),
        "side": any(vd._plain(c) in vd._plain(line) for c in SIDE_CUES),
        "seats": any(vd._has(toks, w) for w in SEAT_WORDS),
        "question": line.strip().endswith("?"),
        "quote": bool(re.search(r"[\"“”]", line)) or ("कहा" in line and vd._has(toks, "हम")),
        "vehicle": (_find(VEHICLE, line) or ["plane"])[0],
        "concepts": _find(CONCEPTS, line)[:4], "phrases": _phrases(line)[:2],
        "objects": [w for w in vd._english(line) if _drawable(w)][:2],
    }


def _drawable(word: str) -> bool:
    from .media import cutouts, vox
    return bool(vox.illustration(word) or cutouts.resolve(word))


def _obj(f: dict, default: str = "") -> str:
    from .media import cutouts, vox
    for w in f["objects"]:
        name = cutouts.resolve(w) or w
        if vox.illustration(name) or cutouts.resolve(w):
            return name
    return default


def _headline(f: dict, most: int = 3) -> str:
    """A short English headline from the line's own words: its phrases first, else its key nouns in order."""
    if f.get("phrases"):
        h = ", ".join(f["phrases"][:2])
        return h[:1].upper() + h[1:]
    words = [c for c in f["concepts"] if c not in ("every", "morning", "night", "party", "question", "answer")]
    h = " ".join(words[:most]).strip()
    return h[:1].upper() + h[1:]          # keep brand capitals (WhatsApp), only the first letter goes up


def key_facts(f: dict) -> list[str]:
    """What the viewer must see for the line to work with the sound off."""
    out = [n["shown"] for n in f["numbers"][:2]] + ([f["percent"]] if f["percent"] else [])
    out += [str(y) for y in f["years"][:1]] + f["places"][:2]
    if not out and not (f["false"] or f["side"] or f["message"]):
        out += f["people"][:1]
    if f["time"]:
        out.append(f["time"].split()[0])
    return [x for x in out if x]


def mute_test(f: dict, graphic: str) -> bool:
    """True when the graphic shows the line's key fact (or the line has no hard fact to show)."""
    keys = key_facts(f)
    if not keys:
        return True
    g = graphic.lower().replace(",", "")
    def norm(x: str) -> str:
        return x.lower().replace(",", "").replace("₹", "").replace("$", "").strip()
    return any(norm(k) and (norm(k) in g or norm(k).split()[0] in g) for k in keys)


# ---- choosing the infographic ---------------------------------------------------------------------------------------
def candidates(line: str, f: dict, n: int, total: int, ahead: dict | None = None) -> list[str]:
    """Infographics that show this line, best first. `ahead` is the next line's facts (who said a quote)."""
    out: list[str] = []
    if f["quote"] and ahead and ahead.get("people") and not f["people"]:
        # a quote whose speaker is named in the next line: the speaker's real photo with the words (translated)
        sp = ahead["people"][0]
        out.append(f"Hero: person:{sp} | “{_headline(f) or 'In their words'}” | {sp} · translated | style: box")
    obj = _obj(f)
    head = _headline(f) or (f["places"][0] if f["places"] else "")
    who = f["people"][0] if f["people"] else ""
    year = str(f["years"][0]) if f["years"] else ""
    nums = f["numbers"]
    # the opening line is the hook: a title card with the most concrete thing in it
    if n == 1:
        kick = " · ".join(x for x in (who, f["places"][0] if f["places"] else "", year) if x)
        if nums:
            out.append(f"BigNumber: {nums[0]['shown']} | {obj or 'crowd'} | {head or 'The number'}" + (f" | {kick}" if kick else ""))
        if f["places"] and not f.get("phrases"):        # a cold open on the place itself
            out.append(f"Pinmap: {f['places'][0]} | {who or head or f['places'][0]} | atlas")
        out.append(f"Opener: {obj or 'megaphone'} | {head or 'The story'} | {kick or 'Print Facts'}")
    if f["question"] and n == total:
        q = head if head.endswith("?") else (f"{head}?" if head else "What do you think?")
        out.append(f"Opener: {obj or 'smartphone'} | {q} | Print Facts")
    # who reported it: the report itself
    if f["publisher"] and (f["cited"] or nums):
        if f["places"]:
            out.append(f"Pinmap: {f['places'][0]} | {head or 'The report'} | {f['publisher']}" + (f", {year}" if year else ""))
        if nums:
            out.append(f"BigNumber: {nums[0]['shown']} | {obj or 'documents'} | {head or 'reported'} | {f['publisher']}")
        out.append(f"Newscard: {year or 'Report'} | {head or 'The report'} | {' · '.join(key_facts(f)[:2])} | "
                   f"{('person:' + who) if who else (obj or 'newspaper')} | {f['publisher']}")
    # someone's side / a denial
    if f["side"] and (who or f["parties"]):
        side = f["parties"][0] if f["parties"] else who
        out.append(f"Hero: {('person:' + who) if who else 'megaphone'} | The {side} side | {who or side} | "
                   f"{head or 'their response'} | style: box")
    # false claims get stamped
    if f["false"]:
        out.append(f"Stamp: FALSE | {head or 'the claim'}")
    # numbers: seats, a comparison, a share, one big number
    if f["seats"] and len(nums) >= 2 and len(f["parties"]) >= 2:
        out.append("Seats: " + ", ".join(f"{p} {int(x['value'])}" for p, x in zip(f["parties"], nums)) + f" | {head or 'Seats'}")
    if len(nums) >= 2:
        mat = "coins" if f["money"] else "bars"
        nouns = [c for c in f["concepts"] if c in ("network", "groups", "people", "votes", "seats", "ads", "jobs", "farmers",
                                                    "workers", "money", "tax", "debt", "budget", "company")]
        label = (nouns[0] if nouns else "Value").capitalize()
        title = " · ".join(x for x in (head if f.get("phrases") else label, f["places"][0] if f["places"] else "") if x)
        out.append(f"Stack: {mat} | {label} 1 {nums[0]['shown']}, {label} 2 {nums[1]['shown']} | {title or 'Compared'}")
    if f["percent"]:
        out.append(f"Slice: {f['percent']} | {obj or 'globe'} | {head or 'share'}")
    if len(nums) == 1:
        cap = head or " "
        if f["time"]:
            cap = f"{cap} · {f['time']}".strip(" ·")
        out.append(f"BigNumber: {nums[0]['shown']} | {obj or ('banknote' if f['money'] else 'crowd')} | {cap}")
    # time and place
    if f["time"] and len(f["places"]) >= 2:
        out.append("Clockmap: " + ", ".join(f"{p} {f['time'].split()[0]}" for p in f["places"]) + f" | {head or 'Same moment'}")
    if f["time"]:
        out.append(f"Clock: {f['time']} | {head or 'Every day'}")
    if len(f["places"]) >= 2:
        out.append(f"Route: {' → '.join(f['places'][:4])} | {head or 'The route'} | {f['vehicle']} | atlas | pen")
    if f["places"]:
        ph = _headline(f) or " · ".join(x for x in (who, f["parties"][0] if f["parties"] else "", year) if x) or head
        from .media import maps
        country = (maps._find(f["places"][0]) or {}).get("kind") == "country"
        out.append(f"Pinmap: {f['places'][0]} | {ph}".rstrip(" |") + (f" | person:{who}" if who else "")
                   + (" | pen" if country else " | atlas"))      # a whole country gets the marker hatching
    if f["date"]:
        out.append(f"Calendar: {f['date']} | {head or ''}".rstrip(" |"))
    if f["month_year"] and not f["date"]:
        out.append(f"Calendar: {f['month_year']} | {head or ''}".rstrip(" |"))
    if len(f["years"]) >= 2:
        out.append(f"BigNumber: {f['years'][0]} | {obj or 'calendar'} | {head or 'then'} | {f['years'][0]} → {f['years'][-1]}")
    # messages and quotes
    if f["message"] and not nums:
        out.append(f"Hero: smartphone | {head or 'The message'} | {' · '.join(key_facts(f)[:2]) or 'forwarded'} | style: disc")
    # people and things
    hard = bool(nums or f["percent"] or f["places"] or f["publisher"] or f["false"] or f["time"] or f["date"])
    if who and not hard:     # with a fact to show, the infographic leads and the person stands beside it (with:)
        tags = " · ".join(x for x in (who, f["parties"][0] if f["parties"] else "", f["places"][0] if f["places"] else "", year) if x)
        out.append(f"Hero: person:{who} | {head or who} | {tags} | style: grid")
    if obj:
        out.append(f"Hero: {obj} | {head or obj.title()}" + (f" | {year}" if year else ""))
    if year:
        out.append(f"BigNumber: {year} | {obj or ''} | {head or ' '}".replace("|  |", "| |"))
    return out


# when an object has just been on screen, a related one tells the same line without repeating the picture
ALTERNATES = {"smartphone": ["crowd", "megaphone", "laptop", "newspaper", "tower"], "crowd": ["house", "megaphone", "person"],
              "megaphone": ["newspaper", "television", "crowd"], "newspaper": ["documents", "television", "laptop"],
              "documents": ["newspaper", "book", "laptop"], "banknote": ["coins", "moneybag", "briefcase"],
              "coins": ["banknote", "moneybag"], "building": ["skyscraper", "gavel", "documents"],
              "ship": ["container", "port", "crane"], "container": ["ship", "port", "truck"], "person": ["crowd", "megaphone"]}


def _subject(g: str) -> str:
    """The pictured object of a graphic line ('' when it has none)."""
    kind, _, spec = g.partition(":")
    kind = kind.strip().lower()
    parts = [p.strip() for p in spec.split("|")]
    if kind in ("hero", "opener", "tornsplit", "blueprint", "tv"):
        return parts[0].split("+")[0].strip().lower() if parts else ""
    if kind in ("bignumber", "slice", "trend") and len(parts) > 1:
        return parts[1].split("+")[0].strip().lower()
    return ""


def _vary(g: str, used: list[str]) -> str:
    """Swaps the pictured object for a related one when it was in the last shot or twice already."""
    sub = _subject(g)
    if not sub or sub.startswith("person:"):
        return g
    if not (used[-1:] == [sub] or used.count(sub) >= 2):
        return g
    for alt in ALTERNATES.get(sub, []):
        if alt not in used[-2:] and used.count(alt) < 2:
            return g.replace(sub, alt, 1) if sub in g else g
    return g


# Vox / Johnny Harris first: real people, maps with marker notes, documents and clippings; flat forms last
STYLE_RANK = {"pinmap": 0, "route": 0, "newscard": 1, "clipping": 1, "hero": 2, "pinboard": 2, "reveal": 2,
              "bignumber": 3, "compare": 3, "photoline": 3, "clockmap": 3, "seats": 4, "stack": 4, "trend": 4,
              "slice": 5, "calendar": 5, "stamp": 6, "clock": 6, "opener": 7, "tornsplit": 7, "statement": 9}


def _jitter(seed: int, kind: str) -> float:
    """A per-video nudge to a kind's rank (0 to 2.5), so videos with the same kinds of lines don't come out in one
    fixed order: one leads with maps, another with numbers or papers. The same script always gets the same order."""
    return (zlib.crc32(f"{seed}:{kind}".encode()) % 1000) / 400 if seed else 0.0


def _ranked(cands: list[str], n: int, total: int, f: dict | None = None, seed: int = 0) -> list[str]:
    kind = lambda g: g.split(":", 1)[0].strip().lower()     # noqa: E731
    if n == total:
        return cands                     # the payoff keeps its own order
    if n == 1:
        if not seed or len(cands) < 2:
            return cands
        # the hook: a number, a place or a title card; which one leads differs per video (a quote stays first)
        lead = [g for g in cands if kind(g) == "hero"]
        rest = [g for g in cands if kind(g) != "hero"]
        k = seed % len(rest)
        return lead + rest[k:] + rest[:k]
    rank = dict(STYLE_RANK)
    if f and f.get("false"):
        rank["stamp"] = -1               # a debunk line: the FALSE stamp is the point of the shot
    return sorted(cands, key=lambda g: (-9 if rank.get(kind(g), 5) < 0 else rank.get(kind(g), 5) + _jitter(seed, kind(g))))


PRONOUNS = ("उन्होंने", "उनके", "उनका", "उनकी", "उन्हें", "वे", "उनसे")


def carry_person(line: str, f: dict, last: str) -> dict:
    """A line that says 'he said' (उन्होंने...) about the person just named keeps that person beside it."""
    if not f["people"] and last and any(vd._has(vd._tokens(line), w) for w in PRONOUNS):
        f = dict(f)
        f["people"] = [last]
        f["carried"] = True
    return f


def platforms(line: str) -> list[str]:
    """Platforms and companies the line names, as logo keys (WhatsApp, Google, Facebook...)."""
    from .media import vox
    toks = vd._tokens(line)
    low = line.lower()
    out = []
    for word, key in vox.LOGO_WORDS.items():
        hit = vd._has(toks, word) if vd._DEV.search(word) else re.search(rf"\b{re.escape(word)}\b", low)
        if hit and key in vox.logos() and key not in out:
            out.append(key)
    return out[:2]


def _with_logos(g: str, line: str) -> str:
    from .media import vox
    kind = g.split(":", 1)[0].strip().lower()
    keys = platforms(line)
    if not keys or kind not in vox.KINDS or "logo" in g.lower():
        return g
    return f"{g} | logo: {', '.join(keys)}"


def _with_person(g: str, f: dict) -> str:
    """A public figure named in the line stands beside the infographic as a papercut photo (unless the graphic is
    already their photo). Only on the Vox scenes, which make room for them."""
    from .media import vox
    kind = g.split(":", 1)[0].strip().lower()
    if not f["people"] or kind not in vox.KINDS or "with:" in g:
        return g
    who = f["people"][0]
    if f"person:{who}".lower() in g.lower():
        others = [p for p in f["people"][1:] if f"person:{p}".lower() not in g.lower()]
        if not others:
            return g
        who = others[0]
    return f"{g} | with: person:{who}"


def _marked(g: str, f: dict, prev: list[str]) -> str:
    """Johnny Harris annotates the key fact in red marker: on maps, people and numbers, not on every line."""
    kind = g.split(":", 1)[0].strip().lower()
    if "marker:" in g or kind not in ("pinmap", "route", "hero", "bignumber", "newscard", "stack"):
        return g
    if any("marker:" in p for p in prev[-3:]):
        return g                                       # a budget: about one shot in four, or it stops meaning "look"
    note = ""
    nums = f["numbers"]
    if kind == "stack" and len(nums) >= 2:
        unit = nums[0]["shown"].split()[-1] if " " in nums[0]["shown"] else ""
        if unit and all(x["shown"].endswith(unit) for x in nums[:2]):
            tot = sum(x["value"] for x in nums[:2]) / {"lakh": 1e5, "crore": 1e7}.get(unit, 1)
            note = f"= {tot:g} {unit} together"          # the sum the viewer would do in their head
    if not note:
        note = next((p for p in (f.get("phrases") or []) if p.lower() not in g.lower()), "")
    return f"{g} | marker: {note}" if note else g      # never a note that only repeats what is on screen


def pick(line: str, f: dict, n: int, total: int, prev: list[str], props: bool = False, ahead: dict | None = None,
         seed: int = 0) -> str:
    """The first candidate that draws, passes the mute test and doesn't repeat the last two graphics' kind; its
    pictured object is varied so the same thing isn't on screen shot after shot."""
    recent = [p.split(":", 1)[0].strip().lower() for p in prev[-2:]]
    used = [_subject(p) for p in prev if _subject(p)]
    for g in _ranked(candidates(line, f, n, total, ahead), n, total, f, seed):
        if n < total:                      # the closing line keeps its own object: it's the payoff
            g = _vary(g, used)
        kind = g.split(":", 1)[0].strip().lower()
        if kind in recent and kind not in ("hero",) or (kind == "hero" and recent[-1:] == ["hero"]):
            continue
        if vd.valid(g, True, props) or not mute_test(f, g):
            continue
        return _with_logos(_with_person(_marked(g, f, prev), f), line)
    return ""
