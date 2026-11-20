"""Story-level planning: the whole script is read before any scene is staged.

    analyze(board, target_seconds=None) -> Story

* arc       each beat gets a role - setup, rising, climax, falling, resolution. The climax is the beat with the
            most intensity (turn words like "suddenly"/"but"/"until", strong emotions, physical action, conflict
            verbs), placed after the setup; the last beat resolves.
* emotion   a track per character: the feeling each beat gives them, carried forward and fading over the
            following beats instead of resetting every sentence; a swing from a negative to a positive feeling
            gets an in-between beat.
* pacing    seconds per beat scaled by role (setup and rising move, the climax gets room and a held beat after
            it, the resolution breathes); comedy gets a pause before a turn ("but", "suddenly").
* camera    style per role: wider for setup and resolution, closer and slower for the climax.
* checks    dependencies (someone acting on a person or animal the story has not introduced, "the X" for an
            object never introduced and not obvious from the setting), actions the studio cannot animate,
            claims without sources, and the planned length against a target.

Errors stop a render (studio.film raises unless forced); warnings are reported with the plan."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

TURN = re.compile(r"\b(suddenly|but|until|however|instead|without warning|just as|all of a sudden)\b", re.I)
STRONG = {"angry": 2, "scared": 2, "sad": 1.5, "surprised": 1.5, "laugh": 1, "embarrassed": 1, "nervous": 1.2,
          "happy": 0.8, "frustrated": 1.6}
ACTION = {"trip": 1.5, "chase": 1.5, "steal": 1.5, "drop": 1.0, "knock": 1.2, "throw": 1.0, "jump": 0.8,
          "run": 0.8, "argue": 1.4, "reflex": 0.8, "land": 0.6}
NEGATIVE = {"angry", "scared", "sad", "frustrated", "nervous", "embarrassed"}
POSITIVE = {"happy", "laugh", "confident", "joyful"}
ROLE_PACE = {"setup": 1.0, "rising": 0.95, "climax": 1.25, "falling": 1.0, "resolution": 1.15}
ROLE_CAMERA = {"setup": "explainer", "rising": "comedy", "climax": "drama", "falling": "explainer",
               "resolution": "explainer"}


@dataclass
class Story:
    roles: list = field(default_factory=list)            # role per beat
    intensity: list = field(default_factory=list)
    emotions: dict = field(default_factory=dict)         # character -> [feeling per beat]
    transitions: list = field(default_factory=list)      # (beat, character, from, to) swings that get a beat
    pace: list = field(default_factory=list)             # multiplier per beat
    holds: list = field(default_factory=list)            # extra seconds after a beat
    camera: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    planned_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("roles", "intensity", "emotions", "transitions", "pace", "holds",
                                              "camera", "errors", "warnings", "planned_seconds")}


def analyze(board, target_seconds: float | None = None, sources: list | None = None) -> Story:
    from . import visual_reasoning as VR
    beats = board.beats
    n = len(beats)
    st = Story()
    if not n:
        st.errors.append("the script has no sentences")
        return st
    # intensity and arc
    for b in beats:
        k = 0.0
        k += 1.5 if TURN.search(b.narration) else 0.0
        k += STRONG.get(b.emotion, 0.0)
        k += sum(ACTION.get(a["verb"], 0.0) for a in b.actions)
        k += 0.5 * max(0, len(b.characters) - 1)
        st.intensity.append(round(k, 2))
    lo = 1 if n > 2 else 0
    hi = n - 1 if n > 2 else n
    climax = max(range(lo, hi), key=lambda i: (st.intensity[i], i)) if hi > lo else n - 1
    for i in range(n):
        if n == 1:
            role = "setup"
        elif i == n - 1 and n > 2:
            role = "resolution"
        elif i == climax:
            role = "climax"
        elif i < climax:
            role = "setup" if i == 0 else "rising"
        else:
            role = "falling"
        st.roles.append(role)
    # emotional tracks: carried forward, fading
    cast = getattr(board, "cast", {})
    people = [c for c in cast if cast[c].role != "crowd"]
    for c in people:
        track, cur, age = [], "", 0
        for i, b in enumerate(beats):
            if c in b.characters[:1] and b.emotion:
                new = b.emotion
                if cur in NEGATIVE and new in POSITIVE:
                    st.transitions.append((i, c, cur, new))
                cur, age = new, 0
            else:
                age += 1
                if age > 2:
                    cur = ""
            track.append(cur)
        st.emotions[c] = track
    # pacing
    comedy = board.domain in ("comedy", "story")
    total = 0.0
    for i, b in enumerate(beats):
        p = ROLE_PACE[st.roles[i]]
        hold = 0.0
        if st.roles[i] == "climax":
            hold = 0.9
        if i == n - 1:
            hold = max(hold, 1.2)
        if comedy and i + 1 < n and TURN.search(beats[i + 1].narration):
            hold = max(hold, 0.6)                     # the beat before the turn
        st.pace.append(p)
        st.holds.append(hold)
        st.camera.append(ROLE_CAMERA[st.roles[i]])
        total += (b.narration_window[1] - b.narration_window[0]) * p + hold
    st.planned_seconds = round(total, 1)
    # dependencies and checks
    introduced: set = set()
    named_objects: set = set()
    for i, b in enumerate(beats):
        for a in b.actions:
            if a["target"] and a["target"] not in introduced and a["target"] not in b.characters:
                st.warnings.append(f"line {i + 1}: {a['who']} acts on {a['target']}, who has not appeared yet")
        introduced.update(b.characters)
        for m in re.finditer(r"\b(?:a|an|some|his|her|their)\s+(?:[a-z]+\s+)?([a-z]+)\b", b.narration):
            named_objects.add(m.group(1).lower())
        for m in re.finditer(r"\bthe\s+([a-z]+)\b", b.narration):
            w = m.group(1).lower()
            from .storyboard import ANIMALS, ROLE_NOUNS
            if re.fullmatch(rf"(?:{ROLE_NOUNS}|{ANIMALS})", w):
                continue
            if w not in named_objects and w not in {c.lower() for c in cast} and \
                    not re.fullmatch(r"(?:same|other|next|first|last|whole|end|day|night|way|world|room|floor|"
                                     r"table|door|window|street|road|market|kitchen|harbour|park|city|town|sea|"
                                     r"sky|ground|stairs|bench|government|court|law|people|state|country)", w):
                st.warnings.append(f"line {i + 1}: 'the {w}' was not introduced earlier - it will be shown as "
                                   "if it was always there")
            named_objects.add(w)
        plan = VR.reason(b.narration, sources or [])
        if not plan.sourced:
            st.warnings.append(f"line {i + 1}: {plan.note or 'a claim with no source'}")
        if plan.mode == VR.EVIDENCE and not plan.sourced:
            st.errors.append(f"line {i + 1}: an allegation with no source - supply one, or rephrase it as "
                             "an attributed claim")
    if target_seconds:
        if total < 0.75 * target_seconds:
            st.warnings.append(f"planned {total:.0f} s, well under the {target_seconds:.0f} s target")
        elif total > 1.3 * target_seconds:
            st.warnings.append(f"planned {total:.0f} s, well over the {target_seconds:.0f} s target")
    return st
