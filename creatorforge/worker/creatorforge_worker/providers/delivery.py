"""How each line is said, for the human-like voice: a tone per line (the writer's "Tone:", or read from the line
itself) turned into the engine's expressiveness, pacing and the pause after it. One scene's narration is spoken
as a run of lines, each in its own tone, so a question rises, a hard fact lands and a death is said slowly."""
from __future__ import annotations

import re

# tone: (exaggeration, cfg_weight, pause after the line in seconds). Higher exaggeration = more intense and a little
# faster; lower cfg_weight = looser, slower, more deliberate pacing.
TONES = {
    "calm": (0.35, 0.5, 0.35),
    "warm": (0.45, 0.5, 0.35),
    "question": (0.6, 0.4, 0.5),
    "dramatic": (0.75, 0.3, 0.5),
    "strong": (0.85, 0.3, 0.6),
    "urgent": (0.7, 0.45, 0.2),
    "sad": (0.3, 0.3, 0.6),
}
ALIASES = {"serious": "calm", "neutral": "calm", "soft": "warm", "curious": "question", "questioning": "question",
           "shock": "dramatic", "suspense": "dramatic", "tense": "dramatic", "angry": "urgent", "fast": "urgent",
           "emotional": "sad", "somber": "sad", "sombre": "sad", "slow": "sad", "whisper": "sad", "punch": "strong",
           "hard": "strong", "firm": "strong",
           "शांत": "calm", "नाटकीय": "dramatic", "सवाल": "question", "दुखी": "sad", "भावुक": "sad", "ज़ोरदार": "strong",
           "तेज़": "urgent", "गर्मजोशी": "warm"}
_SAD = re.compile(r"\b(died|death|dead|killed|suicide|victims?|survivors?|abuse\w*|grief|funeral|mourn\w*)\b|"
                  r"मौत|मृत|आत्महत्या|पीड़ित|शोषण|संघर्ष|दर्द|आँसू|बच्ची", re.I)
_SHOCK = {"shock", "fear", "terror", "horror", "tension", "suspense", "intrigue", "anger", "disgust"}


def tone_of(line: dict, emotion: str = "") -> str:
    """The tone of one line: the writer's Tone:, else what the line itself asks for."""
    extra = line.get("extra") or {}
    t = str(extra.get("tone") or "").strip().lower()
    if t:
        return ALIASES.get(t, t) if ALIASES.get(t, t) in TONES else "calm"
    text = str(line.get("text") or "").strip()
    if extra.get("statement") or extra.get("big"):
        return "strong"
    if text.endswith("?") or text.endswith("?\""):
        return "question"
    if _SAD.search(text):
        return "sad"
    if len(text.split()) <= 4:
        return "strong"
    if (emotion or "").lower() in _SHOCK:
        return "dramatic"
    return "calm"


def segments(beats: list[dict], narration: str, emotion: str = "") -> list[dict]:
    """The scene's narration as lines with their tones: [{"text", "tone", "pause"}]. A line just before a chapter
    card or a statement gets a longer pause. One segment when the lines don't add up to the narration."""
    lines: list[dict] = []
    for b in beats:
        if not str(b.get("text") or "").strip():
            continue
        if lines and not re.search(r"[.!?…।॥][\"'”’)]*$", lines[-1]["text"].strip()):
            # a sentence the cuts split in two is still said in one breath, in its first part's tone
            merged = dict(lines[-1])
            merged["text"] = f"{lines[-1]['text'].strip()} {b['text'].strip()}"
            merged["extra"] = {**(b.get("extra") or {}), **(lines[-1].get("extra") or {})}
            lines[-1] = merged
        else:
            lines.append(b)
    if not lines or " ".join(" ".join(b["text"] for b in lines).split()) != " ".join(narration.split()):
        return [{"text": narration, "tone": tone_of({"text": narration}, emotion), "pause": 0.0}]
    out = []
    for k, b in enumerate(lines):
        tone = tone_of(b, b.get("emotion") or emotion)
        pause = TONES[tone][2]
        nxt = (lines[k + 1].get("extra") or {}) if k + 1 < len(lines) else {}
        if (b.get("extra") or {}).get("chapter") or nxt.get("statement") or nxt.get("chapter"):
            pause += 0.4                      # a beat of silence before a chapter card or a big statement
        out.append({"text": b["text"], "tone": tone, "pause": round(pause, 2)})
    return out


def engine_params(tone: str, base: tuple[float, float]) -> tuple[float, float]:
    """The engine's (exaggeration, cfg_weight) for a tone, nudged by the voice's own style."""
    ex, cw, _ = TONES.get(tone, TONES["calm"])
    bex, bcw = base
    return round(min(1.0, max(0.2, (ex * 2 + bex) / 3)), 3), round(min(0.8, max(0.2, (cw * 2 + bcw) / 3)), 3)
