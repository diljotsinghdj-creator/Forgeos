"""The narration rewritten the way a newsreader says it, for voices that read text literally (Chatterbox):
"₹13 crore" -> "thirteen crore rupees" / "तेरह करोड़ रुपये", "40%" -> "forty percent", "ED" -> "E D" / "ई डी".
Captions keep the script's own spelling; only the voice hears this."""
from __future__ import annotations

import re

_EN_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
            "sixteen seventeen eighteen nineteen").split()
_EN_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

_HI = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस "
       "बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस "
       "पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस "
       "सैंतालीस अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ "
       "इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर "
       "पचहत्तर छिहत्तर सतहत्तर अठहत्तर उन्यासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी "
       "अट्ठासी नवासी नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे").split()

_HI_LETTERS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                       "ए बी सी डी ई एफ जी एच आई जे के एल एम एन ओ पी क्यू आर एस टी यू वी डब्ल्यू एक्स वाई ज़ेड".split()))

# Capitals said as words, not letter by letter (acronyms that are words, and words written in capitals for emphasis).
WORDLIKE = {"NEET", "AIIMS", "SEBI", "NASA", "NATO", "ISRO", "NITI", "COVID", "UNICEF", "UNESCO", "AYUSH", "OK",
            "WHO", "IS", "IT", "NO", "NOT", "AND", "THE", "ALL", "YOU", "WAS", "ARE", "LIE", "WHY", "HOW", "NOW",
            "BUT", "OR", "TO", "OF", "IN", "ON", "AT", "BE", "WE", "ME", "MY", "SO", "DO", "GO", "AN", "AS", "BY",
            "IF", "UP", "HE", "SHE", "HIS", "HER", "OUR", "WHAT", "THIS", "THAT", "THEY", "THEM", "LIES", "DEAD",
            "ONE", "TWO", "TEN", "YES", "NEW", "BIG", "OUT", "OFF", "WAR", "JAIL", "RAID", "BAN", "FAKE", "TRUE",
            "LOST", "GONE", "FREE", "WHEN", "WHERE", "NEVER", "EVERY", "STOP", "READ", "LOOK", "NAME", "VOTE"}
# Four- and five-letter capitals that are spelled out (shorter ones are, unless they are words above).
SPELLED = {"PMLA", "UAPA", "NDTV", "CBDT", "NCRB", "CAPF", "INDIA", "NSCN", "AICC", "AITC", "UPSC", "SSC", "BSNL",
           "ONGC", "LPG", "HDFC", "ICICI", "IPL", "BCCI", "NHRC", "NCPCR", "CPIM", "CPI", "DMK", "AIADMK", "UGC", "NCERT"}


def _en_int(n: int) -> str:
    if n < 20:
        return _EN_ONES[n]
    if n < 100:
        return _EN_TENS[n // 10] + ("" if n % 10 == 0 else "-" + _EN_ONES[n % 10])
    for size, name in ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"), (1000, "thousand"), (100, "hundred")):
        if n >= size:
            rest = n % size
            head = f"{_en_int(n // size)} {name}"
            return head if not rest else f"{head}{' and ' if rest < 100 else ' '}{_en_int(rest)}"
    return str(n)


def _hi_int(n: int) -> str:
    if n < 100:
        return _HI[n]
    for size, name in ((10**7, "करोड़"), (10**5, "लाख"), (1000, "हज़ार"), (100, "सौ")):
        if n >= size:
            rest = n % size
            return f"{_hi_int(n // size)} {name}" + (f" {_hi_int(rest)}" if rest else "")
    return str(n)


def number_words(num: str, lang: str = "en", year_ok: bool = True) -> str:
    """"6,060" -> "six thousand and sixty"; "13.3" -> "thirteen point three"; "2024" -> "twenty twenty-four"."""
    num = num.replace(",", "")
    whole, _, frac = num.partition(".")
    if not whole.isdigit() or len(whole) > 15:
        return num
    n = int(whole)
    hi = lang == "hi"
    if lang not in ("en", "hi"):
        return num
    if not hi and year_ok and not frac and len(whole) == 4 and 1100 <= n <= 2099 and n % 1000 >= 10:
        head, tail = divmod(n, 100)
        said = f"{_en_int(head)} {'hundred' if tail == 0 else ('oh ' + _en_int(tail) if tail < 10 else _en_int(tail))}"
    else:
        said = _hi_int(n) if hi else _en_int(n)
    if frac.isdigit():
        digits = " ".join((_HI if hi else _EN_ONES)[int(d)] for d in frac)
        said += f" {'दशमलव' if hi else 'point'} {digits}"
    return said


def _spell(acronym: str, lang: str) -> str:
    if lang == "hi":
        return " ".join(_HI_LETTERS.get(c, c) for c in acronym)
    return " ".join(acronym)


_MONEY = re.compile(r"(?:₹|\bRs\.?\s?|\bINR\s?)\s?(\d[\d,]*(?:\.\d+)?)(\s?(?:crore|cr|lakh|करोड़|लाख|million|billion|"
                    r"thousand|हज़ार|हजार)(?![\w\u0900-\u097F]))?", re.I)
_DOLLAR = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)(\s?(?:million|billion|trillion|thousand)\b)?", re.I)
_PCT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s?%")
_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{2,3})+|\d+)(\.\d+)?(?![\w])")
_ACRO = re.compile(r"(?<![\w.])([A-Z]{2,6})s?(?![\w])")


def speakable(text: str, lang: str = "en") -> str:
    """The line as it should be said aloud in this language ("en" or "hi"; other languages are left alone)."""
    lang = (lang or "en").lower()[:2]
    if lang not in ("en", "hi"):
        return text
    hi = lang == "hi"

    def money(m: re.Match, cur_en: str, cur_hi: str) -> str:
        unit = (m.group(2) or "").strip()
        unit = {"cr": "crore"}.get(unit.lower(), unit)
        if hi:
            unit = {"crore": "करोड़", "lakh": "लाख", "thousand": "हज़ार"}.get(unit.lower(), unit)
        amount = number_words(m.group(1), lang, year_ok=False)
        return " ".join(p for p in (amount, unit, cur_hi if hi else cur_en) if p)

    text = _MONEY.sub(lambda m: money(m, "rupees", "रुपये"), text)
    text = _DOLLAR.sub(lambda m: money(m, "dollars", "डॉलर"), text)
    text = _PCT.sub(lambda m: f"{number_words(m.group(1), lang, False)} {'प्रतिशत' if hi else 'percent'}", text)
    text = _NUM.sub(lambda m: number_words(m.group(1) + (m.group(2) or ""), lang), text)

    def acronym(m: re.Match) -> str:
        a = m.group(1)
        vowels = re.search(r"[AEIOU]", a)
        if a in WORDLIKE or (len(a) > 3 and vowels and a not in SPELLED) or a == "INDIA":
            return m.group(0)
        return _spell(a, lang) + ("s" if m.group(0).endswith("s") and not hi else "")
    text = _ACRO.sub(acronym, text)
    return text
