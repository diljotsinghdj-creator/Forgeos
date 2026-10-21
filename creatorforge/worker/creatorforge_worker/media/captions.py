"""Synchronized captions and text overlays as an ASS subtitle file (burned in by FFmpeg)."""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from ..providers.base import Word


@dataclass
class Overlay:
    start: float
    end: float
    text: str
    style: str  # Hook | Callout | CTA


def estimate_words(text: str, start: float, spoken_s: float) -> list[Word]:
    """Distributes script words across the measured narration length, weighted by word length."""
    words = text.split()
    if not words:
        return []
    weights = [len(w) + 2 for w in words]
    total = sum(weights)
    out, t = [], start
    for w, wt in zip(words, weights):
        d = spoken_s * wt / total
        out.append(Word(w, t, t + d))
        t += d
    return out


def group(words: list[Word], per: int) -> list[Word]:
    cues = []
    for i in range(0, len(words), per):
        chunk = words[i:i + per]
        cues.append(Word(" ".join(w.text for w in chunk), chunk[0].start, chunk[-1].end))
    for a, b in zip(cues, cues[1:]):
        a.end = max(a.end, min(b.start, a.end + 0.3))
    return cues


def _ts(s: float) -> str:
    s = max(0.0, s)
    cs = int(round(s * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    sec, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


def _esc(t: str) -> str:
    return t.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def _norm(w: str) -> str:
    """A word for matching: letters, digits and vowel signs only (Hindi matras are marks, not alnum - dropping them
    would make करोड़ match करड and कटा match कटे)."""
    return "".join(ch for ch in w.lower() if ch.isalnum() or unicodedata.category(ch).startswith("M"))


VIRAMA = "\u094D"


def graphemes(text: str) -> list[str]:
    """Text split into what a reader sees as one letter: a consonant keeps its vowel signs, and a Hindi conjunct
    (consonant + virama + consonant, as in ल्ल) stays whole - typing "दिल्ली" mark by mark would break the shaping."""
    out: list[str] = []
    for ch in text:
        if out and (unicodedata.category(ch).startswith("M") or ch in "\u200C\u200D" or out[-1].endswith(VIRAMA)):
            out[-1] += ch
        else:
            out.append(ch)
    return out


def ass_color(hex_rgb: str, default: str) -> str:
    """#RRGGBB -> ASS &H00BBGGRR."""
    h = (hex_rgb or "").lstrip("#")
    if len(h) != 6:
        return default
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def _highlight(text: str, words: set[str], color: str = "&H0037AFD4") -> str:
    """Auto Edit emphasis: key words pop in the highlight colour and slightly larger."""
    out = []
    for w in text.split():
        e = _esc(w)
        out.append(f"{{\\c{color}&\\fscx112\\fscy112}}{e}{{\\r}}" if words and _norm(w) in words else e)
    return " ".join(out)


EXPLAINER_FONT = "Archivo Black"   # free (SIL OFL) heavy grotesque; the pod installs it, DejaVu Sans otherwise


def _have_font(name: str) -> bool:
    import shutil
    import subprocess
    if not shutil.which("fc-list"):
        return False
    try:
        return name.lower() in subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True,
                                              timeout=10).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return False


def write_ass(path: Path, width: int, height: int, scale: float, position: float,
              cues: list[Word], overlays: list[Overlay], emphasis: set[str] | None = None,
              caption_color: str = "", highlight_color: str = "", callout_look: str = "") -> None:
    """callout_look "highlighter": on-screen text as bold black words on a yellow marker box that wipes in -
    the editorial explainer look. Default: white text on a dark box."""
    emphasis = {_norm(w) for w in (emphasis or set()) if _norm(w)}
    cap = ass_color(caption_color, "&H00FFFFFF")
    hi = ass_color(highlight_color, "&H0037AFD4")
    fs = int(height * scale)
    big = int(fs * 1.35)
    small = int(fs * 0.85)
    if callout_look in ("highlighter", "redpen") and width > height:
        # Widescreen explainers are watched on TVs and laptops from a distance: captions, callouts and the hook
        # card need to read at a glance (the template sizes suit phones).
        fs, big, small = int(height * 0.05), int(height * 0.085), int(height * 0.056)
    caption_margin = int(height * (1 - position))
    top = int(height * 0.10)
    side = int(width * 0.07)
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        f"Style: Caption,DejaVu Sans,{fs},{cap},{cap},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(2, fs // 12)},{max(1, fs // 24)},2,{side},{side},{caption_margin},1",
        f"Style: Hook,DejaVu Sans,{big},{hi},{hi},&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(3, big // 10)},{max(1, big // 20)},8,{side},{side},{top},1",
        (f"Style: Callout,DejaVu Sans,{small},&H00111111,&H00111111,&H0018C8F5,&H0018C8F5,-1,0,0,0,100,100,0,0,3,"
         f"{max(6, small // 3)},0,8,{side},{side},{top},1" if callout_look == "highlighter" else
         f"Style: Callout,DejaVu Sans,{small},&H002E10C8,&H002E10C8,&H00D8E8EF,&H00D8E8EF,-1,0,0,0,100,100,0,0,3,"
         f"{max(6, small // 3)},0,8,{side},{side},{top},1" if callout_look == "redpen" else
         f"Style: Callout,DejaVu Sans,{small},&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,"
         f"{max(4, small // 4)},0,8,{side},{side},{top},1"),
        f"Style: CTA,DejaVu Sans,{big},{hi},{hi},&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(3, big // 10)},{max(1, big // 20)},5,{side},{side},0,1",
        f"Style: Brand,DejaVu Sans,{small},{hi},{hi},&H00000000,&HA0000000,-1,0,0,0,100,100,2,0,1,"
        f"{max(2, small // 10)},0,8,{side},{side},{int(height * 0.04)},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    explainer = callout_look in ("highlighter", "redpen")
    if explainer:
        # Video-essay type: a heavy grotesque, black on cream paper strips; key words get a highlighter box; the hook
        # and the call to action sit on a solid highlighter block. Calm - no bouncing.
        font = EXPLAINER_FONT if _have_font(EXPLAINER_FONT) else "DejaVu Sans"
        mark = "&H002BD6F7" if callout_look == "highlighter" else "&H002E10C8"     # yellow / red pen
        ink, paper = "&H00141414", "&H00EEF5F8"
        pad = max(6, fs // 4)
        lines = [ln for ln in lines if not ln.startswith(("Style: Caption,", "Style: Hook,", "Style: CTA,"))]
        lines[-3:-3] = [
            f"Style: Caption,{font},{int(fs * 0.92)},{ink},{ink},{paper},{paper},0,0,0,0,100,100,0,0,3,{pad},0,2,"
            f"{side},{side},{caption_margin},1",
            f"Style: Hook,{font},{big},{ink},{ink},{mark},{mark},0,0,0,0,100,100,0,0,3,{max(8, big // 4)},0,8,"
            f"{side},{side},{top},1",
            # the closing call to action sits next to the captions (below on Shorts, above on widescreen), not across
            # the middle of the last picture
            f"Style: CTA,{font},{big},{ink},{ink},{mark},{mark},0,0,0,0,100,100,0,0,3,{max(8, big // 4)},0,2,"
            f"{side},{side},{max(int(height * 0.12), caption_margin - int(fs * 2.2)) if height > width else caption_margin + int(fs * 2.4)},1",
        ]
        if callout_look == "highlighter":
            lines = [ln.replace("Style: Callout,DejaVu Sans,", f"Style: Callout,{font},")
                     .replace("&H0018C8F5,&H0018C8F5,-1,", f"{mark},{mark},0,") for ln in lines]
    for c in cues:
        if explainer:
            words = []
            for wd in c.text.split():
                e = _esc(wd)
                words.append(f"{{\\3c{mark}&}}{e}{{\\3c{paper}&}}" if emphasis and _norm(wd) in emphasis else e)
            lines.append(f"Dialogue: 0,{_ts(c.start)},{_ts(c.end)},Caption,,0,0,0,,{{\\fad(60,0)}}{' '.join(words)}")
            continue
        # Pop-in: each caption lands at 75% size and springs to full size in 0.12 s (the Shorts "bounce").
        pop = "{\\fscx75\\fscy75\\t(0,120,\\fscx104\\fscy104)\\t(120,180,\\fscx100\\fscy100)}"
        lines.append(f"Dialogue: 0,{_ts(c.start)},{_ts(c.end)},Caption,,0,0,0,,{pop}{_highlight(c.text, emphasis, hi)}")
    from . import marks
    pen = "&H002E10C8" if callout_look == "redpen" else marks.PEN
    font_name = EXPLAINER_FONT if explainer and _have_font(EXPLAINER_FONT) else "DejaVu Sans"
    ev = lines.index("[Events]") - 1
    huge = int(min(width, height) * 0.2)
    lines[ev:ev] = [f"Style: Big,{font_name},{huge},&H0000D7F7,&H0000D7F7,&H00141414,&H00000000,0,0,0,0,100,100,2,0,1,"
                    f"{max(6, huge // 9)},{max(3, huge // 18)},5,0,0,0,1"]
    lines[ev:ev] = ["Style: Mark,DejaVu Sans,20,&H00FFFFFF,&H00FFFFFF,&H00141414,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
                    f"Style: BubbleText,{font_name},{fs},&H00141414,&HFF141414,&H00FFFFFF,&H00000000,0,0,0,0,100,100,0,0,1,"
                    f"0,0,5,0,0,0,1"]
    callout_y = top + small * 1.45          # just under a one-line callout at the top
    for o in overlays:
        if o.style == "Draw" and o.end > o.start:
            box = next((c for c in overlays if c.style == "Callout" and c.start < o.end and c.end > o.start), None)
            target = None
            if box is not None:
                # the pen goes on what the script highlights: the line's Text: box at the top of the frame
                tw = min(width - 2 * side, len(box.text) * small * 0.6 + small)
                target = (width / 2 - tw / 2, top - small * 0.2, width / 2 + tw / 2, top + small * 1.25)
            kinds = [k.strip() for k in o.text.replace("+", ",").split(",") if k.strip()]
            if target is None and not o.text.startswith("subject:"):
                # nothing specific to point at: a circle or arrow over a random spot is noise - keep only verdicts
                kinds = [k for k in kinds if k not in marks.TARGETED]
            if not kinds:
                continue
            lines += marks.mark_events(", ".join(kinds).replace("subject:", ""), o.start, o.end, width, height, pen,
                                       None, target)
            continue
        if o.style == "Place" and o.text.strip() and o.end > o.start:
            lines += marks.place_events(o.text, o.start, o.end, width, height, font_name, pen)
            continue
        if o.style == "Cite" and o.text.strip() and o.end > o.start:
            lines += marks.cite_events(o.text, o.start, o.end, width, height, font_name)
            continue
        if o.style == "Sting" and o.text.strip() and o.end > o.start:
            # the channel's sign-off: its name drops onto a highlighter strip that wipes open, a pen line under it
            name = _esc(o.text.strip().upper())
            y = height * (0.2 if height > width else 0.16)
            size = int(min(width, height) * 0.06)
            lines.append(f"Dialogue: 7,{_ts(o.start)},{_ts(o.end)},Callout,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{y:.0f})"
                         f"\\fs{size}\\fscx15\\t(0,260,\\fscx100)\\fad(0,200)}}{name}")
            uw = len(o.text) * size * 0.36
            lines.append(f"Dialogue: 7,{_ts(o.start + 0.3)},{_ts(o.end)},Mark,,0,0,0,,{{\\an7\\pos(0,0)"
                         f"\\clip(0,0,{width / 2 - uw:.0f},{height})\\t(0,300,\\clip(0,0,{width / 2 + uw:.0f},{height}))"
                         f"\\p1\\bord{max(3, size // 12)}\\1a&HFF&\\3c{pen}&\\fad(0,200)}}"
                         f"m {width / 2 - uw:.0f} {y + size * 0.85:.0f} l {width / 2 + uw:.0f} {y + size * 0.8:.0f} "
                         f"l {width / 2 - uw:.0f} {y + size * 0.85:.0f}")
            continue
        if o.style == "Big" and o.text.strip() and o.end > o.start:
            # one or two words slam in huge, tilted, then hold - the key word of the line, on screen
            words = o.text.strip().upper()
            y = height * (0.42 if height > width else 0.5)
            lines.append(f"Dialogue: 6,{_ts(o.start)},{_ts(o.end)},Big,,0,0,0,,{{\\an5\\pos({width / 2:.0f},{y:.0f})"
                         f"\\frz4\\fscx260\\fscy260\\alpha&H60&\\t(0,150,\\fscx96\\fscy96\\alpha&H00&)"
                         f"\\t(150,230,\\fscx100\\fscy100)\\fad(0,150)}}{_esc(words)}")
            continue
        if o.style in ("Bubble", "Think") and o.text.strip() and o.end > o.start:
            lines += marks.bubble_events(o.text, o.start, o.end, width, height, o.style == "Think", font_name)
            continue
        if o.text.strip() and o.end > o.start:
            # Highlighter: the marker box sweeps open left to right, like someone highlighting the words.
            fx = ("{\\fad(120,200)\\fscx15\\t(0,220,\\fscx100)}" if callout_look in ("highlighter", "redpen") and o.style == "Callout"
                  else "{\\fad(200,200)}")
            lines.append(f"Dialogue: 1,{_ts(o.start)},{_ts(o.end)},{o.style},,0,0,0,,{fx}{_esc(o.text)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def script_spelling(heard: list[Word], script: str) -> tuple[list[Word], float]:
    """Puts the script's words on Whisper's timings, so captions always show the script exactly - every word, in
    its own spelling ("₹13 crore", not what the voice said, "thirteen crore rupees"). Words Whisper heard the same
    take their own timing; a stretch heard differently, or a word Whisper missed, shares the time around it.
    Returns (words, match ratio)."""
    import difflib
    said = script.split()
    if not heard or not said:
        return list(heard), 0.0
    a = [_norm(w.text) for w in heard]
    b = [_norm(w) for w in said]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out: list[Word] = []

    def spread(words: list[str], start: float, end: float) -> None:
        end = max(end, start + 0.12 * len(words))
        weights = [max(1, len(w)) for w in words]
        t, total = start, sum(weights)
        for w, wt in zip(words, weights):
            d = (end - start) * wt / total
            out.append(Word(w, round(t, 3), round(t + d, 3)))
            t += d

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            out += [Word(said[j1 + k], heard[i1 + k].start, heard[i1 + k].end) for k in range(i2 - i1)]
        elif op == "replace":
            spread(said[j1:j2], heard[i1].start, heard[i2 - 1].end)
        elif op == "insert":
            # a word Whisper didn't hear: squeezed into the gap where it was said
            start = out[-1].end if out else heard[0].start
            nxt = heard[i1].start if i1 < len(heard) else start + 0.25 * (j2 - j1)
            spread(said[j1:j2], start, max(nxt, start + 0.1))
        # "delete": a word Whisper heard that isn't in the script (a filler, a mis-hearing) - not captioned
    return out, round(sm.ratio(), 3)
