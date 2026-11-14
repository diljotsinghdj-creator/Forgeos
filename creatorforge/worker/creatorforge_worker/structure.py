"""Structured graphics from narration alone: the director's rules for the graphics that need more than one fact
(a pyramid, an organisation chart, a table, a poll line, stacked areas, a price candle, a flow, a transport network,
buildings to scale, an exploded view, a page of a judgment).

Each rule only fires when the line itself carries the whole structure - the names AND the numbers, in an order that
pairs them without guessing - and builds the graphic from exactly those words. A line that carries less gets the
simpler graphic it always got. Nothing is ever filled in:

    pyramid   two or more age bands, each "from A to B: X men, Y women"
    orgchart  a word about rank ("के अधीन", "reports to") and three or more named offices or bodies
    table     two or more named places or parties, each with the same two figures
    polltrack three or more months or years, each with one percentage
    area      two or more years and two or more named series, each series with a figure per year
    candles   a price that opened, rose to, fell to and closed at four figures
    flowchart a word of sequence ("फिर", "उसके बाद") and three or more named steps, not all of them places
    railmap   a word about a line or network (rail, metro, pipeline, corridor) and three or more places
    towers3d  two or more named buildings, each with its height in metres
    explode   a word about what is inside, a named thing and two or more named parts
    courtdoc  a named court and words in quotation marks: shown verbatim, in the language they were given in
"""
from __future__ import annotations

import re

from . import vox_director as vd

ROLES = {"प्रधानमंत्री": "Prime Minister", "राष्ट्रपति": "President", "उपराष्ट्रपति": "Vice President", "मुख्यमंत्री": "Chief Minister",
         "राज्यपाल": "Governor", "गृह मंत्री": "Home Minister", "वित्त मंत्री": "Finance Minister", "रक्षा मंत्री": "Defence Minister",
         "विदेश मंत्री": "Foreign Minister", "गृह मंत्रालय": "Home Ministry", "वित्त मंत्रालय": "Finance Ministry",
         "रक्षा मंत्रालय": "Defence Ministry", "विदेश मंत्रालय": "Foreign Ministry", "कैबिनेट": "Cabinet", "संसद": "Parliament",
         "सीबीआई": "CBI", "ईडी": "ED", "एनआईए": "NIA", "आईबी": "IB", "रॉ": "RAW", "पुलिस": "Police", "सेना": "Army",
         "नौसेना": "Navy", "वायुसेना": "Air Force", "सीईओ": "CEO", "चेयरमैन": "Chairman", "निदेशक": "Director", "सचिव": "Secretary",
         "बोर्ड": "Board", "आयकर विभाग": "Income Tax Dept", "चुनाव आयोग": "Election Commission", "आरबीआई": "RBI",
         "सेबी": "SEBI", "नीति आयोग": "NITI Aayog", "राज्य सरकार": "State government", "केंद्र सरकार": "Central government",
         "ज़िला कलेक्टर": "District Collector", "कलेक्टर": "District Collector"}
STEPS = {"किसान": "Farmer", "मंडी": "Market", "व्यापारी": "Trader", "दुकान": "Shop", "ग्राहक": "Customer", "फ़ैक्ट्री": "Factory",
         "फैक्ट्री": "Factory", "कारख़ाना": "Factory", "गोदाम": "Warehouse", "बंदरगाह": "Port", "बैंक": "Bank", "कंपनी": "Company",
         "ट्रस्ट": "Trust", "पार्टी": "Party", "दानकर्ता": "Donor", "दान": "Donation", "सरकार": "Government", "ठेकेदार": "Contractor",
         "एजेंसी": "Agency", "मतदाता": "Voter", "खदान": "Mine", "रिफ़ाइनरी": "Refinery", "पेट्रोल पंप": "Petrol pump",
         "अस्पताल": "Hospital", "मरीज़": "Patient", "स्कूल": "School", "सर्वर": "Server", "फ़ोन": "Phone", "ऐप": "App"}
SERIES = {"कोयला": "Coal", "कोयले": "Coal", "सौर": "Solar", "पवन": "Wind", "गैस": "Gas", "परमाणु": "Nuclear", "तेल": "Oil",
          "पनबिजली": "Hydro", "आयात": "Imports", "निर्यात": "Exports", "शहरी": "Urban", "ग्रामीण": "Rural", "कृषि": "Farming",
          "उद्योग": "Industry", "सेवा": "Services", "पुरुष": "Men", "महिला": "Women"}
BUILDINGS = {"बुर्ज ख़लीफ़ा": "Burj Khalifa", "बुर्ज खलीफा": "Burj Khalifa", "एफ़िल टावर": "Eiffel Tower", "एफिल टावर": "Eiffel Tower",
             "क़ुतुब मीनार": "Qutub Minar", "कुतुब मीनार": "Qutub Minar", "स्टैच्यू ऑफ़ यूनिटी": "Statue of Unity",
             "स्टैच्यू ऑफ यूनिटी": "Statue of Unity", "ताजमहल": "Taj Mahal", "ताज महल": "Taj Mahal", "शंघाई टावर": "Shanghai Tower",
             "एम्पायर स्टेट": "Empire State Building", "स्टैच्यू ऑफ़ लिबर्टी": "Statue of Liberty", "पीसा की मीनार": "Tower of Pisa",
             "चारमीनार": "Charminar", "इंडिया गेट": "India Gate", "गेटवे ऑफ़ इंडिया": "Gateway of India", "बिग बेन": "Big Ben"}
THINGS = {"स्मार्टफ़ोन": "Smartphone", "स्मार्टफोन": "Smartphone", "फ़ोन": "Phone", "फोन": "Phone", "मोबाइल": "Phone", "लैपटॉप": "Laptop",
          "कार": "Car", "इलेक्ट्रिक कार": "Electric car", "जहाज़": "Ship", "हवाई जहाज़": "Aircraft", "रॉकेट": "Rocket",
          "ईवीएम": "EVM", "ड्रोन": "Drone", "सोलर पैनल": "Solar panel", "रिएक्टर": "Reactor", "ट्रेन": "Train", "उपग्रह": "Satellite"}
PARTS = {"शीशा": "Glass", "ग्लास": "Glass", "स्क्रीन": "Display", "डिस्प्ले": "Display", "बैटरी": "Battery", "कैमरा": "Camera",
         "चिप": "Logic chip", "प्रोसेसर": "Processor chip", "मदरबोर्ड": "Logic board", "सर्किट बोर्ड": "Circuit board", "बोर्ड": "Circuit board",
         "इंजन": "Engine", "मोटर": "Motor", "पहिए": "Wheels", "पहिये": "Wheels", "ढांचा": "Frame", "ढाँचा": "Frame", "बॉडी": "Body",
         "कवर": "Back cover", "खोल": "Shell", "टैंक": "Fuel tank", "पंखा": "Fan", "सेंसर": "Sensor", "स्पीकर": "Speaker",
         "कंटेनर": "Containers", "डेक": "Deck", "पतवार": "Hull", "केबिन": "Cabin", "कंट्रोल यूनिट": "Control unit",
         "बैलट यूनिट": "Ballot unit", "पैनल": "Panel"}
COURTS = {"सुप्रीम कोर्ट": "Supreme Court of India", "सर्वोच्च न्यायालय": "Supreme Court of India", "दिल्ली हाई कोर्ट": "Delhi High Court",
          "बॉम्बे हाई कोर्ट": "Bombay High Court", "इलाहाबाद हाई कोर्ट": "Allahabad High Court", "मद्रास हाई कोर्ट": "Madras High Court",
          "कलकत्ता हाई कोर्ट": "Calcutta High Court", "हाई कोर्ट": "High Court", "उच्च न्यायालय": "High Court"}
MONTHS = {"जनवरी": "Jan", "फ़रवरी": "Feb", "फरवरी": "Feb", "मार्च": "Mar", "अप्रैल": "Apr", "मई": "May", "जून": "Jun", "जुलाई": "Jul",
          "अगस्त": "Aug", "सितंबर": "Sep", "अक्टूबर": "Oct", "नवंबर": "Nov", "दिसंबर": "Dec"}
ORG_CUES = ("के अधीन", "के नीचे", "के तहत", "के मातहत", "को रिपोर्ट", "रिपोर्ट करते", "reports to", "answers to")
SEQ_CUES = ("फिर", "उसके बाद", "इसके बाद", "वहाँ से", "वहां से", "आख़िर में", "आखिर में", "then", "after that")
NET_CUES = ("रेल", "रेलवे", "मेट्रो", "पाइपलाइन", "हाईवे", "एक्सप्रेसवे", "कॉरिडोर", "गलियारा", "नहर", "rail", "metro", "pipeline",
            "highway", "corridor")
INSIDE_CUES = ("के अंदर", "के भीतर", "हिस्से", "परतें", "बना होता", "बनी होती", "बना है", "बनी है", "inside", "made of", "layers")
PCT_CUES = ("प्रतिशत", "फ़ीसदी", "फीसदी", "परसेंट", "%")


def _plain(s: str) -> str:
    return vd._plain(s)


def _has(line: str, cues) -> bool:
    p = _plain(line).lower()
    return any(_plain(c).lower() in p for c in cues)


def ordered(line: str, *tables: dict) -> list[str]:
    """English names from the tables, in the order the line says them; a short name inside a longer match is dropped."""
    p = _plain(line)
    hits = []
    for t in tables:
        for hi, en in t.items():
            k = _plain(hi)
            for m in re.finditer(re.escape(k), p):
                a, b = m.start(), m.end()
                # whole words only: no Devanagari letter straight before the match
                if a > 0 and vd._DEV.search(p[a - 1]):
                    continue
                hits.append((a, b, en))
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    out, end = [], -1
    for a, b, en in hits:
        if a >= end and en not in out:
            out.append(en)
            end = b
    return out


def numbers(line: str, years: bool = False, small: bool = True) -> list[dict]:
    """Every number in the line, in order: {"value", "shown"}. Years (1900-2100) are left out unless asked for."""
    out = []
    for v, unit in vd._spoken_numbers(line):
        if unit == 1 and 1900 <= v <= 2100 and not years:
            continue
        if unit == 1 and v < 10 and not small:
            continue
        out.append({"value": v * unit, "shown": f"{v:g}" + (f" {vd._UNIT[unit]}" if unit in vd._UNIT else "")})
    for m in re.finditer(r"(?<![\d.])(\d[\d,]*(?:\.\d+)?)", line):
        try:
            v = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if 1900 <= v <= 2100 and not years and "." not in m.group(1):
            continue
        out.append({"value": v, "shown": m.group(1)})
    return out


def year_list(line: str) -> list[int]:
    ys = [int(v) for v, u in vd._spoken_numbers(line) if u == 1 and 1900 <= v <= 2100]
    ys += [int(y) for y in re.findall(r"(?<!\d)(19\d\d|20\d\d)(?!\d)", line)]
    return list(dict.fromkeys(ys))


def quoted(line: str) -> str:
    m = re.search(r"[\"“]([^\"“”]{8,300})[\"”]", line)
    return m.group(1).strip() if m else ""


def candidates(line: str, f: dict, head: str) -> list[str]:
    """Structured graphics this line fully carries, most specific first ([] for an ordinary line)."""
    from . import infographic as ig
    from .media import vox
    out: list[str] = []
    nums = numbers(line)
    title = head if head and head not in f["places"] else ""

    # a page of a judgment: a named court and its words in quotation marks, shown exactly as given
    court = ordered(line, COURTS)
    q = quoted(line)
    if court and q:
        english = not vd._DEV.search(q)
        out.append(f"Courtdoc: {court[0]} | | \"{q}\" | " + ("" if english else "as quoted") +
                   f" | badge: {'court record' if english else 'reported'}")

    # population pyramid: age bands, each with a figure for men and one for women
    if _has(line, ("पुरुष", "men")) and _has(line, ("महिला", "women")) and _has(line, ("साल", "वर्ष", "उम्र", "आयु", "years")):
        raw = [n["value"] for n in nums]
        if len(raw) >= 8 and len(raw) % 4 == 0 and all(raw[i] < raw[i + 1] for i in range(0, len(raw), 4)):
            men_first = _plain(line).find(_plain("पुरुष")) < _plain(line).find(_plain("महिला"))
            bands = "; ".join(f"{raw[i]:g}-{raw[i + 1]:g} " + (f"{raw[i + 2]:g}/{raw[i + 3]:g}" if men_first else f"{raw[i + 3]:g}/{raw[i + 2]:g}")
                              for i in range(0, len(raw), 4))
            yr = year_list(line)
            out.append(f"Pyramid: {(f['places'] or ['Population'])[0]}{', ' + str(yr[0]) if yr else ''} | {bands} | Men, Women")

    # a price that opened, rose, fell and closed: one candle
    oc = [(w, k) for k, ws in (("o", ("खुला", "खुलकर", "opened")), ("h", ("ऊपर", "ऊँचा", "ऊंचा", "उच्च", "चढ़ा", "high")),
                               ("l", ("नीचे", "निचला", "गिरा", "गिरकर", "low")), ("c", ("बंद", "closed")))
          for w in ws if _plain(w) in _plain(line)]
    kinds = []
    for w, k in sorted(oc, key=lambda x: _plain(line).find(_plain(x[0]))):
        if k not in kinds:
            kinds.append(k)
    if len(kinds) == 4 and len(nums) == 4:
        v = dict(zip(kinds, (n["value"] for n in nums)))
        if v["l"] <= min(v["o"], v["c"]) and v["h"] >= max(v["o"], v["c"]):
            sign = "$" if "डॉलर" in line or "$" in line else ("₹" if f["money"] else "")
            out.append(f"Candles: {v['o']:g}/{v['h']:g}/{v['l']:g}/{v['c']:g} | {title or 'The day'} | {sign}")

    # buildings and their heights
    blds = ordered(line, BUILDINGS)
    if len(blds) >= 2 and len(nums) == len(blds) and _has(line, ("मीटर", "metre", "meter")):
        out.append("Towers3d: " + ", ".join(f"{b} {n['value']:g}" for b, n in zip(blds, nums)) + f" | {title or 'How tall?'} | m")

    # months or years, each with a percentage: a poll or rating line
    labels = ordered(line, MONTHS) or [str(y) for y in year_list(line)]
    if len(labels) >= 3 and len(nums) == len(labels) and _has(line, PCT_CUES):
        out.append("Polltrack: " + ", ".join(f"{la} {n['value']:g}" for la, n in zip(labels, nums)) + f" | {title or 'Over time'} | | %")

    # years and named series, each series with a figure per year
    ys, ser = year_list(line), ordered(line, SERIES)
    if len(ys) >= 2 and len(ser) >= 2 and len(nums) == len(ys) * len(ser):
        k = len(ys)
        rows = "; ".join(f"{s}: " + ", ".join(f"{n['value']:g}" for n in nums[i * k:(i + 1) * k]) for i, s in enumerate(ser))
        out.append(f"Area: {', '.join(str(y) for y in ys)} | {rows} | {title or 'Over the years'}")

    # named places or parties, each with the same two figures: a table
    ents = ordered(line, vd.PLACES, ig.PLACES_MORE)
    if len(ents) < 2:
        ents = ordered(line, ig.PARTIES)
    if len(ents) >= 2 and len(nums) == 2 * len(ents) and not out:
        pct = [("%" in line or _has(line, PCT_CUES))]

        def col(i):
            vals = [nums[r * 2 + i] for r in range(len(ents))]
            if f["seats"] and i == 0:
                return "Seats"
            if all("lakh" in n["shown"] or "crore" in n["shown"] for n in vals):
                return "Amount" if f["money"] else "Number"
            return "Share %" if pct[0] and all(n["value"] <= 100 for n in vals) else "Figure"
        h1, h2 = col(0), col(1)
        if h1 == h2:
            h1, h2 = h1 + " 1", h2 + " 2"
        rows = "; ".join(f"{e}, {nums[i * 2]['shown']}, {nums[i * 2 + 1]['shown']}" for i, e in enumerate(ents))
        out.append(f"Table: Name, {h1}, {h2} | {rows} | {title or 'Side by side'}")

    # rank: who sits under whom
    offices = ordered(line, ROLES, ig.PEOPLE)
    if len(offices) >= 3 and _has(line, ORG_CUES):
        out.append(f"Orgchart: {offices[0]} | {', '.join(offices[1:7])} | {title or 'Who answers to whom'}")

    # a line or network through three or more places
    stops = ordered(line, vd.PLACES, ig.PLACES_MORE)
    if len(stops) >= 3 and _has(line, NET_CUES):
        g = f"Railmap: {' - '.join(stops[:8])} | {title or 'The line'}"
        if vox.plan_for("railmap", g.split(":", 1)[1]):
            out.append(g)

    # a chain of named steps said in sequence (not a journey between places: that is a Route)
    steps = ordered(line, STEPS, ROLES, ig.PARTIES, vd.PLACES, ig.PLACES_MORE)
    if 3 <= len(steps) <= 6 and _has(line, SEQ_CUES) and len([s for s in steps if s in stops]) < len(steps) - 1:
        out.append(f"Flowchart: {' → '.join(steps)} | {title or 'How it moves'}")

    # what is inside a thing
    thing, parts = ordered(line, THINGS), ordered(line, PARTS)
    if thing and len(parts) >= 2 and _has(line, INSIDE_CUES):
        out.append(f"Explode: {thing[0]} | {', '.join(parts[:7])} | What is inside")
    return out
