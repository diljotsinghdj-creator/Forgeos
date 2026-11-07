"""The Editorial type look ("kinetic"): every line of the script becomes a typographic card, the way modern political
explainer Shorts are cut.

    — 17 FEB 2025 · चयन समिति                     a red dated kicker (Place:, else Cite:, else a date in the line)
    कुछ ही घंटों में,
    नियुक्ति हो *गई।*                              bold headline; the accent word in crimson serif italic

    [ a black-and-white portrait cut-out on a red circle ]   when the line names a person (their real photo)
    [ a calendar page with the day circled ]                  when the line gives a full date and names nobody
    [ a torn-edge black-and-white photograph ]                otherwise, the line's own picture

Lines with Tone: dramatic or sad turn the card navy, with the accent in yellow. Words written *like this* in the line,
or in a Big:/Statement: line, are the accent; otherwise the last word is.

The background (paper, circle, portrait, calendar, photo) is composed once per line with Pillow; the words animate
over it in an ASS subtitle layer (they rise in one line at a time, the accent last, a date ring draws itself)."""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path

from . import ff

PAPER = (239, 234, 224)
NAVY = (14, 22, 46)
CRIMSON = (178, 30, 48)
YELLOW = (240, 196, 72)
INK = (22, 22, 26)

MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
             "november", "december"]
MONTHS_HI = ["जनवरी", "फ़रवरी|फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर|सितम्बर",
             "अक्टूबर|अक्तूबर", "नवंबर|नवम्बर", "दिसंबर|दिसम्बर"]
_MON = "|".join([m for m in MONTHS_EN] + [m[:3] for m in MONTHS_EN] + MONTHS_HI)
DATE = re.compile(rf"(\d{{1,2}})\s*({_MON})\.?,?\s*(\d{{4}})|({_MON})\.?\s+(\d{{1,2}}),?\s*(\d{{4}})", re.I)
YEAR = re.compile(r"\b(1[89]\d\d|20\d\d)\b")


def _ass_col(rgb, alpha: int = 0) -> str:
    r, g, b = rgb
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def _month_index(word: str) -> int:
    w = word.lower().rstrip(".")
    for i, m in enumerate(MONTHS_EN):
        if w == m or w == m[:3]:
            return i
    for i, m in enumerate(MONTHS_HI):
        if word in m.split("|"):
            return i
    return -1


def find_date(*texts: str):
    """(day, month 0-11, year) for the first full date in the texts, or None."""
    for t in texts:
        m = DATE.search(t or "")
        if m:
            if m.group(1):
                return int(m.group(1)), _month_index(m.group(2)), int(m.group(3))
            return int(m.group(5)), _month_index(m.group(4)), int(m.group(6))
    return None


# ---- the words ------------------------------------------------------------------------------------------------------
def headline(beat: dict) -> tuple[str, str]:
    """(kicker, headline) for a beat. The headline keeps *accent* marks."""
    extra = beat.get("extra") or {}
    text = str(extra.get("big") or extra.get("statement") or beat.get("text") or "").strip()
    words = text.split()
    if len(words) > 12:                                  # the first clause, else the first ten words
        first = re.split(r"(?<=[,।;:!?])\s+", text)[0]
        text = first if len(first.split()) <= 12 else " ".join(words[:10]) + "…"
    if re.search(r"[A-Za-z]", text) and not re.search(r"[ऀ-ॿ]", text):
        text = text.lower()                              # the editorial look sets Latin headlines in lower case
    if "*" not in text and text:
        ws = text.split()
        n = 2 if len(ws) > 2 and len(ws[-1].strip(".,!?।")) <= 3 else 1
        text = " ".join(ws[:-n] + ["*" + " ".join(ws[-n:]) + "*"])
    kicker = str(extra.get("place") or "").strip()
    if not kicker and extra.get("cite"):
        kicker = str(extra["cite"]).split(",")[0].strip()
    if not kicker:
        d = find_date(beat.get("text", ""))
        if d:
            kicker = f"{d[0]} {MONTHS_EN[d[1]][:3].upper()} {d[2]}"
        else:
            y = YEAR.search(beat.get("text", "") or "")
            kicker = y.group(1) if y else ""
    return kicker.upper() if re.search(r"[A-Za-z]", kicker) else kicker, text


def _wrap(text: str, per: int) -> list[str]:
    """Rows of about `per` characters; an *accent phrase* stays whole on one row."""
    text = re.sub(r"\*[^*]+\*", lambda m: m.group(0).replace(" ", "\u00a0"), text)
    lines, cur = [], ""
    for w in text.split(" "):
        if not w:
            continue
        if cur and len((cur + " " + w).replace("*", "")) > per:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return [ln.replace("\u00a0", " ") for ln in lines]


# ---- the picture ----------------------------------------------------------------------------------------------------
def _paper(w, h, dark):
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(7)
    base = np.array(NAVY if dark else PAPER, dtype=np.float32)
    noise = rng.normal(0, 4.5 if not dark else 3.0, (h // 3 + 1, w // 3 + 1)).astype(np.float32)
    n = np.asarray(Image.fromarray(noise).resize((w, h), Image.BICUBIC), dtype=np.float32)
    a = np.clip(base[None, None, :] + n[..., None], 0, 255).astype("uint8")
    return Image.fromarray(a, "RGB")


def _bw(im, contrast=1.25):
    from PIL import ImageEnhance, ImageOps
    g = ImageOps.grayscale(im.convert("RGB"))
    g = ImageEnhance.Contrast(g).enhance(contrast)
    return g.convert("RGB")


def _portrait(bg, picture: Path, cut: Path | None, w, h, wide):
    """A red circle and the person in black and white over it, rising from the bottom edge."""
    from PIL import Image, ImageDraw
    cx, cy = (int(w * 0.7), int(h * 0.58)) if wide else (int(w * 0.5), int(h * 0.7))
    r = int(min(w, h) * (0.27 if not wide else 0.3))
    d = ImageDraw.Draw(bg)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CRIMSON)
    if cut is not None:
        person = Image.open(cut).convert("RGBA")
        bw = _bw(person)
        bw.putalpha(person.getchannel("A"))
        target_h = int(h * (0.5 if not wide else 0.62))
        k = target_h / person.height
        bw = bw.resize((max(1, int(person.width * k)), target_h), Image.LANCZOS)
        if bw.width > w * 0.9:
            bw = bw.resize((int(w * 0.9), int(bw.height * w * 0.9 / bw.width)), Image.LANCZOS)
        bg.paste(bw, (cx - bw.width // 2, h - bw.height), bw)
        return
    with Image.open(picture) as im:                      # no cut-out on this machine: a round black-and-white crop
        src = _bw(im)
    s = min(src.width, src.height)
    top = int((src.height - s) * 0.25)                   # faces sit in the upper part of a portrait
    crop = src.crop(((src.width - s) // 2, top, (src.width - s) // 2 + s, top + s)).resize((2 * r - 24, 2 * r - 24))
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).ellipse([0, 0, crop.width - 1, crop.height - 1], fill=255)
    bg.paste(crop, (cx - crop.width // 2, cy - crop.height // 2), mask)


def _photo(bg, picture: Path, w, h, wide, dark):
    """The line's picture as a black-and-white print with torn edges, slightly turned."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    with Image.open(picture) as im:
        pic = _bw(im, 1.15)
    pw = int(w * (0.42 if wide else 0.7))
    ph = int(pw * pic.height / pic.width)
    ph = min(ph, int(h * (0.6 if wide else 0.38)))
    pic = pic.resize((pw, int(pw * pic.height / pic.width)), Image.LANCZOS).crop((0, 0, pw, ph))
    rng = random.Random(pw * 31 + ph)
    border = int(pw * 0.035)
    card = Image.new("RGBA", (pw + 2 * border, ph + 2 * border), (250, 248, 242, 255))
    card.paste(pic, (border, border))
    mask = Image.new("L", card.size, 0)
    md = ImageDraw.Draw(mask)
    pts = []
    step = 14
    W_, H_ = card.size
    for x in range(0, W_, step):
        pts.append((x, rng.uniform(0, 7)))
    for y in range(0, H_, step):
        pts.append((W_ - rng.uniform(0, 7), y))
    for x in range(W_, 0, -step):
        pts.append((x, H_ - rng.uniform(0, 7)))
    for y in range(H_, 0, -step):
        pts.append((rng.uniform(0, 7), y))
    md.polygon(pts, fill=255)
    card.putalpha(mask)
    card = card.rotate(-2.0, resample=Image.BICUBIC, expand=True)
    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    shadow.putalpha(card.getchannel("A").point(lambda v: 70 if v > 0 else 0).filter(ImageFilter.GaussianBlur(10)))
    x0 = int(w * 0.52) if wide else (w - card.width) // 2
    y0 = int(h * 0.3) if wide else int(h * 0.5)
    bg.paste(shadow, (x0 + 8, y0 + 12), shadow)
    bg.paste(card, (x0, y0), card)


def _calendar(bg, day, month, year, w, h, wide, dark, font_path):
    """A calendar page for the month; the ring around the day is drawn by the text layer (it animates)."""
    import calendar
    from PIL import Image, ImageDraw, ImageFont
    cw = int(w * (0.36 if wide else 0.66))
    chh = int(cw * 0.86)
    x0 = int(w * 0.56) if wide else (w - cw) // 2
    y0 = int(h * 0.26) if wide else int(h * 0.5)
    card = Image.new("RGB", (cw, chh), (34, 44, 72) if dark else (252, 251, 247))
    d = ImageDraw.Draw(card)
    fg = (236, 236, 240) if dark else INK
    big = ImageFont.truetype(font_path, max(10, int(cw * 0.07)))
    small = ImageFont.truetype(font_path, max(8, int(cw * 0.045)))
    d.text((cw * 0.07, chh * 0.06), f"{MONTHS_EN[month].upper()} {year}", font=big, fill=CRIMSON)
    for i, wd in enumerate("SMTWTFS"):
        d.text((cw * (0.1 + i * 0.125), chh * 0.2), wd, font=small, fill=(140, 140, 150))
    cal = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month + 1)
    spot = None
    for r_, week in enumerate(cal):
        for c_, dd in enumerate(week):
            if dd:
                x, y = cw * (0.1 + c_ * 0.125), chh * (0.3 + r_ * 0.11)
                d.text((x, y), str(dd), font=small, fill=fg)
                if dd == day:
                    spot = (x0 + x + small.getlength(str(dd)) / 2, y0 + y + small.size * 0.55)
    shadow = Image.new("RGBA", (cw + 30, chh + 30), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([15, 15, cw + 15, chh + 15], fill=(0, 0, 0, 50))
    from PIL import ImageFilter
    bg.paste(shadow.filter(ImageFilter.GaussianBlur(9)), (x0 - 7, y0 + 2), shadow.filter(ImageFilter.GaussianBlur(9)))
    bg.paste(card, (x0, y0))
    return spot, small.size


def _font_file(bold=True) -> str:
    import subprocess
    for name in (("Archivo Black", "Inter:black", "DejaVu Sans:bold") if bold else ("DejaVu Sans",)):
        try:
            p = subprocess.run(["fc-match", "-f", "%{file}", name], capture_output=True, text=True, timeout=10).stdout
        except Exception:  # noqa: BLE001
            p = ""
        if p:
            return p
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---- the card -------------------------------------------------------------------------------------------------------
def render(beat: dict, picture: Path | None, size: tuple[int, int], seconds: float, out: Path, work: Path,
           cut_model: Path | None = None) -> Path:
    """One line as an editorial type card (an mp4 of `seconds`)."""
    from PIL import Image
    from .captions import EXPLAINER_FONT, _have_font
    w, h = size
    wide = w > h
    extra = beat.get("extra") or {}
    tone = str(extra.get("tone") or beat.get("tone") or "").lower()
    dark = tone in ("dramatic", "sad")
    kicker, head = headline(beat)
    named = beat.get("named") or {}
    person = bool(named) and not named.get("logo") and not named.get("movement") and \
        str(named.get("kind", "person")) in ("person", "")
    date = find_date(str(extra.get("place") or ""), beat.get("text", ""))
    work.mkdir(parents=True, exist_ok=True)
    bg = _paper(w, h, dark)
    ring = None
    if person and picture is not None and Path(picture).is_file():
        from . import layout
        cut = layout.cutout(Path(picture), work, cut_model) if cut_model else None
        _portrait(bg, Path(picture), cut, w, h, wide)
    elif date and date[1] >= 0:
        ring = _calendar(bg, date[0], date[1], date[2], w, h, wide, dark, _font_file())
    elif picture is not None and Path(picture).is_file():
        _photo(bg, Path(picture), w, h, wide, dark)
    key = f"{beat.get('text', '')}|{picture}|{size}|{dark}|{date}|{person}"
    png = work / f"kbg_{hashlib.sha256(key.encode()).hexdigest()[:14]}.png"
    bg.save(png)

    deva = bool(re.search(r"[\u0900-\u097F]", head + kicker))
    font = _deva_family() if deva else (EXPLAINER_FONT if _have_font(EXPLAINER_FONT) else "DejaVu Sans")
    serif = _deva_family(serif=True) if deva else "DejaVu Serif"
    ink = (236, 236, 240) if dark else INK
    accent = YELLOW if dark else CRIMSON
    fs = int(w * (0.088 if not wide else 0.055))
    if len(head.replace("*", "")) <= 16:
        fs = int(fs * 1.45)                              # a Big: line, a few words: set it large
    left = int(w * 0.07)
    top = int(h * (0.16 if not wide else 0.2))
    per = int((14 if not wide else 22) * (1.35 if deva else 1.0) * (0.088 * w) / max(1, fs) * (1 if not wide else 1.4))
    lines = _wrap(head, max(8, per))
    while len(lines) > 4 and fs > w * 0.045:             # too many rows: smaller type, never a lost accent
        fs = int(fs * 0.88)
        per = int(per / 0.88)
        lines = _wrap(head, per)
    ev = []

    def ts(t):
        t = max(0.0, t)
        return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
    end = ts(seconds)
    if kicker:
        ev.append(f"Dialogue: 2,{ts(0.05)},{end},K,,0,0,0,,{{\\an7\\pos({left},{top - int(fs * 0.9)})"
                  f"\\fs{int(w * 0.03)}\\1c{_ass_col(accent)}\\fad(200,0)}}— {_esc(kicker)}")
    t0 = 0.12
    for i, ln in enumerate(lines):
        parts = re.split(r"(\*[^*]+\*)", ln)
        body = ""
        for p in parts:
            if p.startswith("*") and p.endswith("*"):
                body += (f"{{\\fn{serif}\\i1\\b0\\1c{_ass_col(accent)}\\alpha&HFF&"
                         f"\\t({int((t0 + 0.25) * 1000)},{int((t0 + 0.55) * 1000)},\\alpha&H00&)}}{_esc(p[1:-1])}"
                         f"{{\\fn{font}\\i0\\1c{_ass_col(ink)}}}")
            else:
                body += _esc(p)
        y = top + int(i * fs * 1.12)
        ev.append(f"Dialogue: 3,{ts(t0)},{end},H,,0,0,0,,{{\\an7\\move({left},{y + int(fs * 0.4)},{left},{y},0,220)"
                  f"\\fad(180,0)\\1c{_ass_col(ink)}}}{body}")
        t0 += 0.16
    if ring:
        (rx, ry), s = ring
        rr = s * 1.05
        steps = 24
        pts = " ".join(f"l {rx + rr * math.cos(2 * math.pi * k / steps):.0f} {ry + rr * math.sin(2 * math.pi * k / steps):.0f}"
                       for k in range(1, steps + 1))
        ev.append(f"Dialogue: 4,{ts(0.6)},{end},H,,0,0,0,,{{\\an7\\pos(0,0)\\p1\\bord{max(2, int(s * 0.12))}"
                  f"\\3c{_ass_col(CRIMSON)}\\1a&HFF&\\3a&HFF&\\t(0,300,\\3a&H00&)}}"
                  f"m {rx + rr:.0f} {ry:.0f} {pts}{{\\p0}}")
    head_ = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 2", "",
             "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
             "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
             "MarginL, MarginR, MarginV, Encoding",
             f"Style: H,{font},{fs},{_ass_col(ink)},{_ass_col(ink)},&H00000000,&H00000000,{-1 if deva else 0},0,0,0,"
             f"100,100,{0 if deva else -1},0,1,0,0,7,0,0,0,1",
             f"Style: K,{font},{int(w * 0.03)},{_ass_col(accent)},{_ass_col(accent)},&H00000000,&H00000000,-1,0,0,0,"
             f"100,100,{0 if deva else 2},0,1,0,0,7,0,0,0,1",           # letter-spacing would break Devanagari
             "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    ass = work / f"kin_{hashlib.sha256(chr(10).join(ev).encode()).hexdigest()[:14]}.ass"
    ass.write_text("\n".join(head_ + ev) + "\n", encoding="utf-8")
    # a slow push-in keeps the card alive; the words sit on top
    vf = (f"scale={int(w * 1.04)}:{int(h * 1.04)},zoompan=z='1+0.035*on/({max(1, int(seconds * 30))})'"
          f":x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={w}x{h}:fps=30,{ff.ass_filter(ass)},format=yuv420p")
    ff.run(["-loop", "1", "-i", str(png), "-t", f"{seconds:.2f}", "-vf", vf, "-r", "30", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
    return out


def _deva_family(serif: bool = False) -> str:
    """A font family that has Devanagari (bold sans for headlines, serif for the accent)."""
    import subprocess
    q = ":lang=hi:style=Bold" if not serif else ":lang=hi:family=FreeSerif"
    for pat in ((q, ":lang=hi:weight=bold", ":lang=hi") if not serif else (q, ":lang=hi")):
        try:
            fam = subprocess.run(["fc-match", "-f", "%{family}", pat], capture_output=True, text=True,
                                 timeout=10).stdout.split(",")[0].strip()
        except Exception:  # noqa: BLE001
            fam = ""
        if fam:
            return fam
    return "FreeSans"


def _esc(t: str) -> str:
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")")
