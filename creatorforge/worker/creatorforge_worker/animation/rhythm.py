"""Comic and dramatic timing from the narration's own rhythm: where to hold, where the punchline lands, who reacts.

Evenly spaced lines feel flat; what explainers and cartoons do is set up, wait, hit, react:

* a held beat (silence, stillness) before a line that turns ("But...", "Suddenly", "Instead"), before a short line
  that follows a long one (the punchline shape), and after a question (let it hang);
* a reaction shot after a punchline, a shock or a joke: someone else in the scene reacts - a take with "!" for a
  shock, a laugh for a joke, a scowl for an outrage, a slump for bad news - and the camera punches in on them;
* a small "button" hold after the reaction before the next line.

    rhythm(["Prices went up by forty percent, and the government said everything was fine.", "It wasn't."])
    -> [{"pause": 0.15, ...}, {"pause": 0.65, "punch": True, "react": "take", ...}]

Every decision carries its reason, for the plan notes."""
from __future__ import annotations

import re

TURN = re.compile(r"^\s*(?:but|however|suddenly|then|instead|and then|yet|still|meanwhile|lekin|magar|par|"
                  r"अचानक|लेकिन|मगर|फिर)\b", re.I)
SHOCK = re.compile(r"shock\w*|stunn\w*|can'?t believe|gasp\w*|unbelievabl\w*|jaw|whoa|wow|हैरान|चौंक", re.I)
JOKE = re.compile(r"\b(?:ha(?:ha)+|laugh\w*|joke\w*|funny|hilarious|ridiculous|absurd|of course|obviously|"
                  r"apparently|surprise,? surprise|मज़ाक|हँस)\b", re.I)
OUTRAGE = re.compile(r"\b(?:outrag\w*|furious|angry|scandal\w*|shameful|unfair|how dare|enough|गुस्सा|नाराज़)\b", re.I)
BAD = re.compile(r"\b(?:died|dead|killed|lost everything|devastat\w*|tragic|collapsed|मौत|मर गए|तबाह)\b", re.I)


def _words(s: str) -> int:
    return len(re.findall(r"\w+", s))


def rhythm(lines: list[str], emotions: list[str] | None = None) -> list[dict]:
    """For each line: pause (s of held beat before it), punch (bool), react (None | take | laugh | scowl | slump),
    button (s held after the reaction) and why."""
    emotions = emotions or [""] * len(lines)
    out = []
    for i, s in enumerate(lines):
        prev = lines[i - 1] if i else ""
        n, pn = _words(s), _words(prev)
        why = []
        pause = 0.15
        punch = False
        if i and TURN.search(s):
            pause, why = 0.45, why + ["a turn: hold before it"]
        if i and n <= 7 and pn >= 12:
            pause, punch, why = 0.65, True, why + ["short after long: the punchline lands after a beat"]
        if prev.rstrip().endswith("?"):
            pause, why = max(pause, 0.5), why + ["the question hangs"]
        if prev.rstrip().endswith(("...", "…")) or re.search(r"[—–-]\s*$", prev):
            pause, punch, why = max(pause, 0.6), True, why + ["a trailing line sets up the next"]
        if n <= 8 and s.rstrip().endswith("!"):
            punch, why = True, why + ["an exclamation"]
        emo = (emotions[i] or "").lower()
        react = None
        if SHOCK.search(s) or emo in ("surprised", "shocked"):
            react = "take"
        elif JOKE.search(s) or emo in ("laugh", "happy") and punch:
            react = "laugh"
        elif OUTRAGE.search(s) or emo in ("angry", "frustrated"):
            react = "scowl"
        elif BAD.search(s) or emo == "sad":
            react = "slump"
        elif punch:
            react = "take"
        if react:
            why.append(f"someone reacts: {react}")
        out.append({"pause": round(pause, 2), "punch": punch, "react": react,
                    "button": 0.45 if react else 0.0, "why": "; ".join(why)})
    return out
