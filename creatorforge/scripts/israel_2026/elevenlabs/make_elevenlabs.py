"""Narration-only files for ElevenLabs, one per render part (R1-R6), for the English and the Hinglish version.
Only the spoken lines, in order, with <break> pauses (longer after strong/dramatic lines and at chapter starts).
Each file is cut into chunks of at most CHUNK characters (ElevenLabs takes a limited amount of text per generation);
generate every chunk, then join them into one R<n>.mp3 per part (see README_ELEVENLABS.txt).
Hindi: numbers are written out as Hindi words so they are read in Hindi, not English.
Run:  python3 make_elevenlabs.py"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHUNK = 2800
PAUSE = {"calm": 0.6, "question": 0.7, "strong": 0.8, "urgent": 0.7, "dramatic": 1.0}
DIRECTION = re.compile(r"^(?:Tone|Visual|Text|Stock|Cite|Chart|Map|Globe|Steps|Timeline|Quote|Article|Statement|Split|Big|Pie|"
                       r"Icons|Squares|Receipt|Animate|Draw|Bubble|Thought|Archive|Transition|Clip|Object|On-screen hook|Title|Tags|Source):")

ONES = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
        "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस "
        "छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस "
        "उनचास पचास इक्यावन बावन तिरेपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरेसठ चौंसठ "
        "पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर "
        "उन्यासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी नब्बे इक्यानवे बानवे "
        "तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे").split()
assert len(ONES) == 100


def hi(n: int) -> str:
    """Integer to Hindi words (Indian grouping: hazaar, lakh, crore)."""
    if n < 100:
        return ONES[n]
    out = []
    for size, word in ((10**7, "करोड़"), (10**5, "लाख"), (1000, "हज़ार"), (100, "सौ")):
        if n >= size:
            out.append(f"{hi(n // size)} {word}")
            n %= size
    if n:
        out.append(ONES[n])
    return " ".join(out)


def year(n: int) -> str:
    """Years the way Hindi speakers say them: 1996 = unnees sau chhiyaanve, 2026 = do hazaar chhabbees."""
    if 1100 <= n < 2000:
        return f"{ONES[n // 100]} सौ" + (f" {ONES[n % 100]}" if n % 100 else "")
    return hi(n)


def hindi_numbers(t: str) -> str:
    t = t.replace("E1", "ई-वन").replace("61वीं", "इकसठवीं")
    t = re.sub(r"केस (\d{4})", lambda m: "केस " + hi(int(m.group(1))), t)
    t = re.sub(r"Resolution (\d+)", lambda m: "Resolution " + " ".join(ONES[int(d)] for d in m.group(1)), t)
    t = re.sub(r"(\d+)\.(\d+)", lambda m: hi(int(m.group(1))) + " दशमलव " + " ".join(ONES[int(d)] for d in m.group(2)), t)
    t = re.sub(r"\b(1[1-9]\d\d|20\d\d)\b", lambda m: year(int(m.group(1))), t)
    t = re.sub(r"\d{1,3}(?:,\d{3})+|\d+", lambda m: hi(int(m.group(0).replace(",", ""))), t)
    return t


def spoken(render_file: str):
    """(text, tone, chapter_start) for every spoken line of a render part, skipping headers and directions."""
    out, chapter = [], False
    blocks = re.split(r"\n\s*\n", open(render_file, encoding="utf-8").read().strip())
    for b in blocks:
        ls = [l.strip() for l in b.splitlines() if l.strip()]
        if not ls:
            continue
        if ls[0].startswith("Chapter:"):
            chapter, ls = True, ls[1:]
            if not ls:
                continue
        if ls[0].startswith("Israel 2026") or DIRECTION.match(ls[0]):
            continue                         # header block (name, hook, title, tags, sources)
        tone = next((l.split(":", 1)[1].strip().lower() for l in ls[1:] if l.startswith("Tone:")), "calm")
        out.append((ls[0], tone, chapter))
        chapter = False
    return out


def write(lang: str, render_dir: str, prefix: str, convert):
    files = sorted(f for f in os.listdir(render_dir) if f.startswith("R") and f.endswith(".txt"))
    report = []
    for f in files:
        part = f.split("_", 1)[0]                           # R1 ... R6
        items = spoken(os.path.join(render_dir, f))
        chunks, cur = [], ""
        for i, (text, tone, chap) in enumerate(items):
            piece = convert(text) + "\n"
            if i < len(items) - 1:          # pause before the next line; longer when the next line opens a chapter
                gap = 1.5 if items[i + 1][2] else PAUSE.get(tone, 0.6)
                piece += f'<break time="{gap}s" />\n'
            if cur and len(cur) + len(piece) > CHUNK:
                chunks.append(cur)
                cur = ""
            cur += piece
        chunks.append(cur)
        body = [f"# {prefix} {part} - {lang} narration for ElevenLabs ({len(items)} lines, {len(chunks)} chunks)",
                "# Generate each chunk separately (paste the text between the CHUNK lines, not these # lines),",
                f"# then join the chunk MP3s into {part}.mp3 - see README_ELEVENLABS.txt.", ""]
        for k, c in enumerate(chunks, 1):
            body += [f"===== CHUNK {k} of {len(chunks)} ({len(c)} characters) =====", c.rstrip(), ""]
        name = f"{prefix}_{part}_ElevenLabs.txt"
        open(os.path.join(HERE, name), "w", encoding="utf-8").write("\n".join(body))
        report.append(f"{name}: {len(items)} lines, {len(chunks)} chunks")
    return report


rep = write("Hinglish", os.path.join(ROOT, "hinglish", "render"), "Hinglish", hindi_numbers)
rep += write("English", os.path.join(ROOT, "render"), "English", lambda t: t)
print("\n".join(rep))
