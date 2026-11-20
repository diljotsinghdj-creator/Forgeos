"""Script -> animation. A sentence describing a moment becomes an acted scene: who is in it, where, what they do,
how they feel and say, then camera and render.

    "A stickman receives shocking news on his phone."
      -> one man; studio; looks at his phone (phone gesture, focused) -> the news lands: shocked face, hands up,
         a small jump back -> a beat of stillness -> the camera pushes in on the reaction.

Rule-based on purpose: it is predictable, free and offline. Quoted words are spoken (lip-synced)."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import creatures, rig2d, scene2d, speech
from .rig2d import Look

FEMALE = re.compile(r"\b(woman|women|girl|she|her|mother|mom|wife|sister|lady|daughter|grandmother|aunt)\b", re.I)
MALE = re.compile(r"\b(man|men|boy|he|his|him|father|dad|husband|brother|son|grandfather|uncle|guy)\b", re.I)
CHILD = re.compile(r"\b(child|kid|boy|girl|student|baby)\b", re.I)
OLD = re.compile(r"\b(old|elderly|grandfather|grandmother|aged|senior)\b", re.I)
TWO = re.compile(r"\b(two|friends|couple|together|each other|argue|argues|arguing|talks? (?:to|with)|meets?|and (?:a|his|her|the) "
                 r"(?:friend|wife|husband|boss|teacher|man|woman|girl|boy))\b", re.I)

# reaction to news/events: (expression, gesture, jump)
REACTIONS = [
    (re.compile(r"shock|shocking|terrible|horrible|bad news|unbelievable|disaster|fired|scam", re.I), ("shocked", "surprise", True)),
    (re.compile(r"great|good news|won|win|promot|passed|happy|amazing|lottery|selected", re.I), ("excited", "cheer", True)),
    (re.compile(r"sad|death|died|lost|heartbreak|rejected|failed|breakup", re.I), ("crying", "cover_face", False)),
    (re.compile(r"angry|furious|annoy|rage|mad", re.I), ("furious", "shake_fist", False)),
    (re.compile(r"confus|strange|weird|puzzl", re.I), ("confused", "scratch_head", False)),
    (re.compile(r"scar|fear|afraid|terrif|panic", re.I), ("terrified", "hands_up", True)),
    (re.compile(r"embarrass|awkward", re.I), ("embarrassed", "facepalm", False)),
]
ACTIONS = [
    (re.compile(r"\b(phone|message|text|news|email|notification|call)\b", re.I), "phone"),
    (re.compile(r"\b(walks?|walking|enters?|arrives?|comes? in)\b", re.I), "walk"),
    (re.compile(r"\b(runs?|running|rushes|sprints?|races?)\b", re.I), "run"),
    (re.compile(r"\b(jumps?|leaps?|hops?)\b", re.I), "jump"),
    (re.compile(r"\b(waves?|greets?)\b", re.I), "wave"),
    (re.compile(r"\b(laughs?|laughing|giggles?|jokes?)\b", re.I), "laugh"),
    (re.compile(r"\b(thinks?|wonders?|ponders?|considers?|thinking)\b", re.I), "think"),
    (re.compile(r"\b(argues?|arguing|fights?|shouts?|yells?)\b", re.I), "argue"),
    (re.compile(r"\b(dances?|dancing|celebrates?|celebrating)\b", re.I), "dance"),
    (re.compile(r"\b(points?|shows?)\b", re.I), "point"),
    (re.compile(r"\b(sleeps?|sleepy|tired|yawns?|exhausted)\b", re.I), "sleepy"),
    (re.compile(r"\b(claps?|applauds?)\b", re.I), "clap"),
    (re.compile(r"\b(shrugs?)\b", re.I), "shrug"),
    (re.compile(r"\b(says?|tells?|explains?|asks?|talks?|speaks?)\b", re.I), "talk"),
]


@dataclass
class Plan:
    place: str = "studio"
    people: list = field(default_factory=list)       # Looks
    steps: list = field(default_factory=list)        # ("action", arg)
    camel: bool = False
    quote: str = ""
    feeling: tuple | None = None


def plan(sentence: str) -> Plan:
    s = sentence.strip()
    p = Plan()
    low = s.lower()
    p.place = "desert" if re.search(r"desert|camel|sand|dune", low) else \
        "park" if re.search(r"park|garden|bench|outside|street", low) else "studio"
    p.camel = "camel" in low
    q = re.search(r"[\"“](.+?)[\"”]", s)
    p.quote = q.group(1) if q else ""
    female = bool(FEMALE.search(s)) and not MALE.search(s.split(" and ")[0])
    look = _look(female, bool(CHILD.search(s)), bool(OLD.search(s)), 0)
    p.people.append(look)
    if TWO.search(s):
        p.people.append(_look(not female, False, False, 1))
    p.feeling = next((r for rx, r in REACTIONS if rx.search(s)), None)
    seen = []
    for rx, act in ACTIONS:
        m = rx.search(s)
        if m:
            seen.append((m.start(), act))
    p.steps = [a for _, a in sorted(seen)]
    if not p.steps:
        p.steps = ["walk"]
    if p.quote and "talk" not in p.steps:
        p.steps.append("talk")
    return p


def _look(female: bool, child: bool, old: bool, i: int) -> Look:
    if female:
        lk = Look(name="She", height=1.64, hair="ponytail" if not old else "bun", body=(200, 70, 95) if i else None,
                  skirt=(205, 75, 100), hair_color=(60, 35, 25) if not old else (200, 200, 205), line=1.15)
    else:
        lk = Look(name="He", height=1.78, hair="short" if i else "none", body=(50, 105, 190) if i else None,
                  hair_color=(40, 30, 25) if not old else (205, 205, 210), line=1.15)
    if child:
        lk.height, lk.head = 1.2, 1.35
    if old:
        lk.hunch, lk.cane, lk.glasses = 0.6, True, True
        lk.beard = not female
    return lk


def build(p: Plan, width: int, height: int, work: Path) -> tuple[scene2d.Scene, float, list]:
    portrait = height > width
    sc = scene2d.Scene(width=width, height=height, ppm=(300 if not portrait else 330) * min(width, height) / 1080,
                       ground=0.8 if portrait else 0.84, horizon=0.55)
    {"desert": scene2d.desert, "park": scene2d.park}.get(p.place, scene2d.studio)(sc)
    a = rig2d.Character(p.people[0], x=-3.2 if "walk" in p.steps or "run" in p.steps else -0.3, seed=3)
    sc.actors.append(a)
    b = None
    if len(p.people) > 1:
        b = rig2d.Character(p.people[1], x=1.2, facing=-1, seed=8)
        sc.actors.append(b)
    if p.camel:
        sc.actors.insert(0, creatures.Camel(x=a.x - 2.6, z=1.18))
    clips = []
    t = 0.3
    feel = p.feeling or ("happy", "wave", False)
    for step in p.steps:
        if step in ("walk", "run"):
            stop = 0.0 if b else 0.0
            t = (a.run if step == "run" else a.walk)(t, stop - (0.2 if b else 0.0))
            if p.camel:
                sc.actors[0].walk(0.4, stop - 2.4)
            t += 0.2
        elif step == "phone":
            a.express(t, "focused", 0.3)
            a.gesture(t, "phone", 2.2)
            t += 2.0
            expr, gest, jump = feel
            a.express(t, expr, 0.15)
            if jump:
                a.jump(t, 0.2)
            a.gesture(t + 0.1, gest, 2.2)
            if expr in ("shocked", "terrified"):
                sc.shake.append((t + 0.1, t + 0.6, 5))
            t += 2.6
        elif step == "jump":
            a.express(t, "excited", 0.2)
            t = a.jump(t, 0.4)
        elif step in ("wave", "laugh", "think", "point", "clap", "shrug"):
            a.express(t, {"wave": "happy", "laugh": "laughing", "think": "thoughtful", "point": "excited",
                          "clap": "joyful", "shrug": "confused"}[step], 0.25)
            t = a.gesture(t, step, 2.0) + 0.2
        elif step == "dance":
            a.express(t, "joyful", 0.25)
            a.gesture(t, "cheer", 1.4)
            a.jump(t + 0.3, 0.25)
            a.gesture(t + 1.4, "clap", 1.4)
            t += 3.0
        elif step == "sleepy":
            a.express(t, "sleepy", 0.6)
            t += 3.0
        elif step == "argue" and b:
            a.express(t, "angry", 0.2)
            a.gesture(t, "shake_fist", 1.6)
            b.express(t + 0.8, "furious", 0.2)
            b.gesture(t + 1.6, "angry", 1.6)
            t += 3.4
        elif step == "talk":
            text = p.quote or "Did you see that?"
            expr = feel[0] if p.feeling else "happy"
            end, wav = a.say(t, text, work / f"line_{len(clips)}.wav", expr=expr)
            clips.append((t, wav))
            if b:
                b.express(t + 0.4, "curious", 0.3)
                b.nod(end - 0.3, 0.8)
            t = end + 0.4
    if p.feeling and "phone" not in p.steps:
        expr, gest, jump = p.feeling
        a.express(t, expr, 0.2)
        a.gesture(t, gest, 2.0)
        if jump:
            a.jump(t, 0.2)
        t += 2.2
    total = t + 0.8
    mid = (0.0 if not b else 0.5)
    sc.cams += [scene2d.CamKey(0, mid if not ("walk" in p.steps or "run" in p.steps) else -1.5, 0, 1.0),
                scene2d.CamKey(min(3.0, total * 0.3), mid, 0, 1.05), scene2d.CamKey(total, mid, -0.1, 1.25 if not b else 1.12)]
    return sc, total, clips


def render(sentence: str, out: Path, width: int = 1280, height: int = 720, work: Path | None = None) -> Path:
    out = Path(out)
    work = Path(work or out.parent)
    work.mkdir(parents=True, exist_ok=True)
    sc, total, clips = build(plan(sentence), width, height, work)
    audio = speech.mix(clips, total, work / (out.stem + "_voice.wav")) if clips else None
    return sc.render(out, total, audio_wav=audio)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    portrait = "--portrait" in sys.argv
    print(render(args[0], Path(args[1]), *((720, 1280) if portrait else (1280, 720))))
