"""Characters that notice each other. After a scene is directed, an Ensemble looks at every emotional beat (a
`feel`) and has the other characters react through their bodies - with their own personality and reaction time:

    angry       a timid character backs away and looks scared; a bold one squares up; anyone else is startled
    laugh/happy laughter is catching for warm characters; a grumpy one rolls their eyes (sarcastic)
    sad         a warm character walks over and puts a hand on their shoulder; others look on, a little sad
    surprised   everyone near turns to see what happened
    scared      others look where they look, and the timid get scared too
    confused    a helpful character steps up with an explaining gesture

Nothing is described in a caption: every reaction is an animated behaviour (a step, a lean, a feeling, where the
head turns). Reactions only go where the character is free - they never overwrite directed action - and idle
characters always look at whoever is doing something (attention)."""
from __future__ import annotations

from dataclasses import dataclass

from . import motions as M
from .stick import Actor
from .timing import PROFILES, Timing


@dataclass(frozen=True)
class Personality:
    name: str
    boldness: float = 0.0        # -1 timid .. +1 bold
    warmth: float = 0.0          # -1 cold .. +1 warm
    energy: float = 1.0          # how big and fast they react
    delay: float = 1.0           # multiplies the timing profile's reaction delay


PERSONALITIES = {
    "timid": Personality("timid", -0.8, 0.3, 0.9, 1.3),
    "bold": Personality("bold", 0.8, -0.1, 1.2, 0.7),
    "cheerful": Personality("cheerful", 0.2, 0.8, 1.3, 0.8),
    "grumpy": Personality("grumpy", 0.3, -0.7, 0.8, 1.2),
    "calm": Personality("calm", 0.1, 0.4, 0.7, 1.4),
    "kind": Personality("kind", 0.0, 0.9, 1.0, 1.0),
}


@dataclass
class Reaction:
    who: str
    to: str
    t: float
    trigger: str
    response: str


class Ensemble:
    def __init__(self, actors: list[Actor], personalities: dict | None = None, timing: Timing | str = "explainer",
                 reach: float = 4.5):
        self.actors = actors
        self.pers = {a: (personalities or {}).get(a.look.name, Personality("plain")) for a in actors}
        self.timing = PROFILES[timing] if isinstance(timing, str) else timing
        self.reach = reach
        self.log: list[Reaction] = []

    # ---- where people are while the scene was being directed (build time: from the plan, not the frames) -----
    @staticmethod
    def _x(a: Actor, t: float) -> float:
        return a.hips_x(t)

    def _delay(self, b: Actor) -> float:
        return self.timing.reaction_delay * self.pers[b].delay

    def apply(self) -> list[Reaction]:
        events = sorted(((t0, t1, emo, a) for a in self.actors for t0, t1, emo in a.feels), key=lambda e: (e[0], e[1]))
        for t0, t1, emo, a in events:
            for b in self.actors:
                if b is a or abs(self._x(b, t0) - self._x(a, t0)) > self.reach:
                    continue
                self._react(b, a, emo, t0, t1)
        self._attention()
        return self.log

    def _react(self, b: Actor, a: Actor, emo: str, t0: float, t1: float):
        P = self.pers[b]
        t = t0 + self._delay(b)
        dur = max(1.0, min(2.6, t1 - t0))
        towards = 1.0 if self._x(a, t) > self._x(b, t) else -1.0
        resp = None
        if emo in ("angry", "frustrated"):
            if P.boldness < -0.3 and not b.busy(t, t + 1.0, moving_only=True):
                self._face(b, t, towards)
                M.step_back(b, t, 0.3 + 0.15 * P.energy)
                b.feel(t + 0.85, t + 0.85 + dur, "scared")
                resp = "steps back, scared"
            elif P.boldness > 0.3 and not b.busy(t, t + dur):
                self._face(b, t, towards)
                b.feel(t, t + dur, "angry" if P.warmth < 0 else "confident")
                resp = "squares up"
            elif not b.busy(t, t + 0.9):
                b.feel(t, t + 0.9, "surprised")
                resp = "startled"
        elif emo in ("laugh", "happy", "excited"):
            if P.warmth > 0.2 and not b.busy(t, t + dur):
                b.feel(t, t + dur, "laugh" if emo == "laugh" else "happy")
                resp = "laughs along" if emo == "laugh" else "cheers up"
            elif P.warmth < -0.3 and not b.busy(t, t + dur):
                b.feel(t, t + dur, "sarcastic")
                resp = "rolls their eyes"
        elif emo == "sad":
            gap = self._x(a, t) - self._x(b, t)
            if P.warmth > 0.5 and abs(gap) > 0.5 and not b.busy(t, t + dur + 2.5):
                end = b.walk(t, self._x(a, t) - towards * 0.55, 1.0)
                M.comfort(b, end + 0.1, a, max(1.2, t1 - end))
                resp = "walks over and comforts"
            elif not b.busy(t, t + dur):
                b.feel(t, t + dur, "sad")
                resp = "looks on, saddened"
        elif emo in ("surprised", "scared", "fear"):
            if not b.busy(t, t + 0.8, moving_only=True):
                self._face(b, t, towards)
            if P.boldness < -0.3 and emo != "surprised" and not b.busy(t, t + dur):
                b.feel(t, t + dur, "scared")
                resp = "gets scared too"
            elif not b.busy(t, t + 0.8):
                b.feel(t, t + 0.8, "surprised")
                resp = "turns to look"
        elif emo == "confused":
            if P.warmth > 0.3 and not b.busy(t, t + 1.6, moving_only=True):
                b.gesture(t, "explain", 1.6)
                resp = "explains"
        if resp:
            b.look_at(t, t + dur, a)
            self.log.append(Reaction(b.look.name, a.look.name, round(t, 2), emo, resp))

    @staticmethod
    def _face(b: Actor, t: float, towards: float):
        if b._facing_at_build(t) != towards and not b.busy(t, t + 0.3, moving_only=True):
            b.turn(t, towards)

    def _attention(self, step: float = 0.5):
        """Idle characters look at whoever is most active near them (acting > moving > feeling)."""
        T = max([a.t1 for x in self.actors for a in x.acts] + [m[1] for x in self.actors for m in x.loco.moves] + [0])
        for b in self.actors:
            t = 0.0
            while t < T:
                if not b.busy(t, t + step) and not any(l0 < t + step and l1 > t for l0, l1, _ in b.looks):
                    best, score = None, 0.0
                    for a in self.actors:
                        if a is b or abs(self._x(a, t) - self._x(b, t)) > self.reach:
                            continue
                        s = 3.0 if any(x.t0 < t + step and x.t1 > t for x in a.acts) else 0.0
                        s += 1.5 if a.busy(t, t + step, moving_only=True) else 0.0
                        s += 1.0 if any(f0 < t + step and f1 > t for f0, f1, _ in a.feels) else 0.0
                        if s > score:
                            best, score = a, s
                    if best is not None:
                        b.look_at(t, t + step, best)
                t += step
