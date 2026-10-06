"""Synchronized captions and text overlays as an ASS subtitle file (burned in by FFmpeg)."""
from __future__ import annotations

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
    return "".join(ch for ch in w.lower() if ch.isalnum())


def _highlight(text: str, words: set[str]) -> str:
    """Auto Edit emphasis: key words pop in gold and slightly larger."""
    out = []
    for w in text.split():
        e = _esc(w)
        out.append(f"{{\\c&H0037AFD4&\\fscx112\\fscy112}}{e}{{\\r}}" if words and _norm(w) in words else e)
    return " ".join(out)


def write_ass(path: Path, width: int, height: int, scale: float, position: float,
              cues: list[Word], overlays: list[Overlay], emphasis: set[str] | None = None) -> None:
    emphasis = {_norm(w) for w in (emphasis or set()) if _norm(w)}
    fs = int(height * scale)
    big = int(fs * 1.35)
    small = int(fs * 0.85)
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
        f"Style: Caption,DejaVu Sans,{fs},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(2, fs // 12)},{max(1, fs // 24)},2,{side},{side},{caption_margin},1",
        f"Style: Hook,DejaVu Sans,{big},&H0037AFD4,&H0037AFD4,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(3, big // 10)},{max(1, big // 20)},8,{side},{side},{top},1",
        f"Style: Callout,DejaVu Sans,{small},&H00FFFFFF,&H00FFFFFF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,3,"
        f"{max(4, small // 4)},0,8,{side},{side},{top},1",
        f"Style: CTA,DejaVu Sans,{big},&H0037AFD4,&H0037AFD4,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,"
        f"{max(3, big // 10)},{max(1, big // 20)},5,{side},{side},0,1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for c in cues:
        lines.append(f"Dialogue: 0,{_ts(c.start)},{_ts(c.end)},Caption,,0,0,0,,{_highlight(c.text, emphasis)}")
    for o in overlays:
        if o.text.strip() and o.end > o.start:
            lines.append(f"Dialogue: 1,{_ts(o.start)},{_ts(o.end)},{o.style},,0,0,0,,{{\\fad(200,200)}}{_esc(o.text)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
