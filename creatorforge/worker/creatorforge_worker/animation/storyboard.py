"""Universal script -> animation director. A script (any subject: psychology, history, science, economics, comedy,
politics) becomes structured scene plans, then staged scenes on the stick engine.

    plan(script)  -> Storyboard: a list of Beat specs, each with the narration line it covers, the characters (role,
                     look, personality), props and visual metaphors, the environment, an ordered list of actions
                     (who, verb, target, emotion, line), the camera style, the timing profile, the narration window
                     and the transition. It is plain data (to_json) - it can be inspected and edited before rendering.
    stage(board)  -> (scene, seconds) for qc.refine / Scene.render.

How it reads a sentence (rule-based on purpose: free, offline, predictable, and every choice can be traced):
* subject area from the vocabulary -> timing profile (comedy, drama, explainer, satire) and look;
* characters: names and role nouns ("a baker", "her friend Sam", "customers"), plurals become a small crowd;
  real historical or political figures are drawn faceless and labelled as an illustration;
* actions from a verb lexicon mapped to engine moves (walk, run, jump, climb, sit, trip/fall, throw, catch, drop,
  carry, give, push, point, explain, think, argue, celebrate, clap, bow, comfort, shake hands, hide, read...);
* emotions and subtext (nervous, relieved, "pretends", "but") -> feelings, faces and reactions;
* concepts -> visual metaphors (prices rising -> a price card that changes; equal fall -> two objects dropped
  under the same gravity; a protest -> a marching group; a vote -> a ballot box) labelled "Illustration";
* numbers in the script are shown as cards marked "figure from the script" - never as verified facts;
* quotes are spoken in bubbles (lip-synced when the character has a face)."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from . import motions as M
from . import rig2d
from .behaviour import PERSONALITIES, Ensemble
from .stick import Actor, Prop, World
from .timing import PROFILES

# ---- vocabulary -------------------------------------------------------------------------------------------------------
DOMAINS = {
    "comedy": r"juggl|slip|banana|trip|clumsy|prank|joke|funny|oops|accidentally|bows?\b|tries to impress",
    "science": r"gravity|vacuum|experiment|atom|energy|force|speed|planet|moon|physics|chemical|cell|scientist|lab",
    "economics": r"price|cost|rupee|dollar|market|supply|demand|inflation|sell|buy|customer|wage|tax|profit|bank",
    "history": r"\b1[0-9]{3}\b|century|king|queen|empire|march|independence|british|colonial|ancient|war\b",
    "psychology": r"nervous|anxious|calm|breathe|stress|confidence|memory|habit|fear|mind|feel|motivation",
    "politics": r"election|vote|parliament|minister|party|government|opposition|court|law\b|policy|commission",
}
PROFILE_FOR = {"comedy": "comedy", "science": "explainer", "economics": "explainer", "history": "drama",
               "psychology": "drama", "politics": "satire"}
STYLE_FOR = {"comedy": "comedy", "drama": "drama", "explainer": "explainer", "satire": "satire"}

EMOTIONS = [
    (r"nervous|anxious|worried|tense", "nervous", "scared"),
    (r"calm|relax|relieved|peaceful", "happy", "happy"),
    (r"confiden|proud|brave|determined", "confident", "confident"),
    (r"happy|glad|delight|joy|cheer|celebrat", "joyful", "happy"),
    (r"laugh|funny|giggl", "laughing", "laugh"),
    (r"angr|furious|annoy|(?<!peaceful )protest", "angry", "angry"),
    (r"buy less|disappoint|can't afford|too expensive", "disappointed", "sad"),
    (r"sad|upset|cry|lonely", "sad", "sad"),
    (r"surpris|shock|amaz|suddenly", "surprised", "surprised"),
    (r"confus|puzzl|wonder", "confused", "confused"),
    (r"embarrass|awkward|clumsy", "embarrassed", "embarrassed"),
    (r"scared|afraid|fear|terrif", "frightened", "scared"),
    (r"curious|notice|watch|look", "curious", "curious"),
]
# verb -> engine action (checked in this order; the first matches in sentence order make the action list)
VERBS = [
    (r"\bjuggl\w*", "juggle"), (r"\bdrops?|dropped|lets? (?:it )?fall", "drop"), (r"\bslip(?:s|ped)?|trip(?:s|ped)?|(?<!both )falls?\b(?! at the same)|tumbl", "trip"),
    (r"\brolls?\b", "roll"), (r"\bthrows?|tosses?|passes\b", "throw"), (r"\bcatch(?:es)?\b", "catch"),
    (r"\bpick(?:s|ed)? up|lift(?:s|ed)?|grab(?:s|bed)?", "pick"), (r"\bcarr(?:y|ies)|brings?\b", "carry"), (r"\bgives?|hands? (?:over|him|her)", "give"),
    (r"\bpush(?:es)?|shoves?", "push"), (r"\bclimbs?", "climb"), (r"\bjumps?|leaps?|hops?", "jump"),
    (r"\bruns?|rushes|races?|sprints?|hurr(?:y|ies)", "run"), (r"\bmarch(?:es|ed)?\b|led\b|leads\b", "march"),
    (r"\bwalks?|walked|enters?|arrives?|goes? (?:in|into|to)|steps? into", "walk"),
    (r"\bsits?|sat\b", "sit"), (r"\bstands? up|stood up|gets? up", "stand"), (r"\bbow(?:s|ed)?\b", "bow"),
    (r"\bclap(?:s|ped)?|applaud", "clap"), (r"\bcheers?|celebrat", "cheer"), (r"\bwaves?|greets?", "wave"),
    (r"\bpoint(?:s|ed)?|show(?:s|ed)?\b|demonstrat", "point"), (r"\bexplains?|teaches|reminds?|tells?|advis", "explain"),
    (r"\bargue[sd]?|shout(?:s|ed)?|yell(?:s|ed)?|(?<!peaceful )protest(?:s|ed)?", "argue"), (r"\bthinks?|remembers?|imagines?|wonders?", "think"),
    (r"\bbreathes?|deep breath", "breathe"), (r"\bhugs?|comforts?|consoles?", "comfort"),
    (r"\bshakes? hands", "handshake"), (r"\bhides?|sneaks?", "hide"), (r"\breads?|studies|writes?", "read"),
    (r"\bvotes?\b", "vote"), (r"\bsells?|buys?|pays?", "trade"), (r"\braises? the price|prices? (?:rise|go up)|costs? go up",
                                                                     "price_up"),
    (r"\bfall at the same|land at the same|hit the bottom together|same rate|same speed", "equal_fall"),
]
ROLE_NOUNS = r"baker|student|teacher|friend|friends|customer|customers|king|queen|scientist|astronaut|soldier|worker|" \
             r"workers|people|crowd|farmer|doctor|child|children|man|woman|boy|girl|officer|leader|voters?|everyone"
PLURAL = re.compile(r"\b(friends|customers|workers|people|crowd|children|voters|everyone|thousands)\b", re.I)
REAL_PEOPLE_HINT = re.compile(r"\b(Gandhi|Nehru|Modi|Shah|Ambedkar|Bose|Newton|Einstein|Scott|Armstrong|"
                              r"Churchill|Lincoln|Kumar|Rahul)\b")
OBJECTS = [(r"orange|apple|ball|fruit", "ball"), (r"salt|handful", "ball"), (r"feather", "feather"),
           (r"bread|loaf|cake", "crate"), (r"box|book|parcel", "crate"), (r"paper|ballot|letter", "folder")]


# ---- the plan -----------------------------------------------------------------------------------------------------------
@dataclass
class Character:
    name: str
    role: str = ""
    face: bool = True
    personality: str = "plain"
    label: str = ""


@dataclass
class Action:
    who: str
    verb: str
    target: str = ""
    emotion: str = ""
    line: str = ""


@dataclass
class Beat:
    index: int
    narration: str
    domain: str
    environment: str
    characters: list
    props: list
    actions: list
    emotion: str
    camera: str
    timing: str
    narration_window: tuple
    transition: str
    metaphors: list = field(default_factory=list)
    figures: list = field(default_factory=list)


@dataclass
class Storyboard:
    title: str
    domain: str
    beats: list

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1, ensure_ascii=False)


def _sentences(script: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", script.strip())
    return [p.strip() for p in parts if p.strip()]


def _domain(text: str) -> str:
    scores = {d: len(re.findall(rx, text, re.I)) for d, rx in DOMAINS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "psychology"


def _names(sentence: str, known: list[str]) -> list[str]:
    words = [m.group(0) for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", sentence)]
    words = [w for w in words if not re.fullmatch(r"(In|On|At|The|A|An|He|She|They|It|When|Some|With|Without|Both|"
                                                  r"Then|After|Before|But|And|This|That|Everyone|Thousands)\s+.*", w)]
    skip = {"In", "On", "At", "The", "A", "An", "He", "She", "They", "It", "His", "Her", "When", "Some", "With",
            "Without", "Both", "Everyone", "Then", "After", "Before", "But", "And", "Thousands", "Moon", "British",
            "Salt", "March", "Salt March", "This", "That", "One", "Two", "Three", "Dandi", "Apollo"}
    out = [w for w in words if w not in skip]
    return [w for w in dict.fromkeys(out) if w not in ("I",)] or [k for k in known if k.lower() in sentence.lower()]


def plan(script: str, title: str = "") -> Storyboard:
    sents = _sentences(script)
    domain = _domain(script)
    profile = PROFILE_FOR[domain]
    cast: dict[str, Character] = {}
    last_subject = None
    beats = []
    clock = 0.0
    for i, s in enumerate(sents):
        names = _names(s, list(cast))
        pos = {n: s.find(n) for n in names}
        roles = []
        for m in re.finditer(rf"\b(?:a|an|the|her|his|their)\s+({ROLE_NOUNS})\b", s, re.I):
            nxt = re.match(r"\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", s[m.end():])          # "her friend Sam"
            roles.append((m.group(1), nxt.group(1) if nxt else ""))
        for role, nm in roles:
            key = nm or role.capitalize()
            if nm and nm in names:
                names.remove(nm)
            if key not in cast:
                cast[key] = Character(key, role.lower(), personality=_personality(role.lower(), s))
            pos[key] = s.lower().find(role.lower())
            names.append(key)
        names = sorted(dict.fromkeys(names), key=lambda n: pos.get(n, 999) if pos.get(n, -1) >= 0 else 999)
        for n in names:
            if n not in cast:
                real = bool(REAL_PEOPLE_HINT.search(n)) or domain in ("history", "politics")
                cast[n] = Character(n, "person", face=not real, personality=_personality("", s),
                                    label=f"{n} (illustration)" if real else "")
        subject = names[0] if names else (last_subject or next(iter(cast), None))
        if subject is None:
            subject = "Narrator"
            cast[subject] = Character(subject, "guide")
        last_subject = subject
        crowd = bool(PLURAL.search(s))
        if crowd and not any(c.role in ("crowd",) for c in cast.values()):
            cast.setdefault("Crowd", Character("Crowd", "crowd", face=False, personality="cheerful"))
        emo = next(((face, feel) for rx, face, feel in EMOTIONS if re.search(rx, s, re.I)), ("", ""))
        verbs = sorted((m.start(), v) for rx, v in VERBS for m in [re.search(rx, s, re.I)] if m)
        others = [n for n in names[1:]] + (["Crowd"] if crowd and subject != "Crowd" else [])
        target = others[0] if others else ""
        acts = []
        if any(v == "equal_fall" for _, v in verbs):
            verbs = [(p, v) for p, v in verbs if v != "trip"]
        if crowd and any(v == "walk" for _, v in verbs) and re.search(r"\bwith (him|her|them)\b", s, re.I):
            verbs = [(p, "march" if v == "walk" else v) for p, v in verbs]          # walking together
        for _, v in verbs:
            who = subject
            if v in ("clap", "cheer") and crowd:
                who = "Crowd"
            acts.append(Action(who, v, target if target != who else "", emo[1], ""))
        q = re.search(r"[\"“](.+?)[\"”]", s)
        if q:
            acts.append(Action(subject, "say", target, emo[1], q.group(1)))
        if not acts:
            acts.append(Action(subject, "explain" if domain in ("science", "economics", "politics") else "think",
                               target, emo[1]))
        props = sorted({kind for rx, kind in OBJECTS if re.search(rx, s, re.I)})
        figures = re.findall(r"\b(\d[\d,.]*\s*(?:%|per cent|rupees|dollars|days|km|years)?)", s)
        metaphors = []
        if any(a.verb == "price_up" for a in acts) or re.search(r"price|cost", s, re.I):
            metaphors.append("price card")
        if any(a.verb == "equal_fall" for a in acts):
            metaphors.append("two objects, same gravity")
        if re.search(r"protest|march", s, re.I):
            metaphors.append("marching group")
        if re.search(r"vote|ballot|election", s, re.I):
            metaphors.append("ballot box")
        if emo[1] in ("scared",) or re.search(r"nervous|anxious|stress", s, re.I):
            metaphors.append("storm cloud of worry")
        words = len(s.split())
        dur = max(4.0, min(9.0, words / 2.4 + 1.4))
        beats.append(Beat(i, s, domain, _environment(s, domain), list(dict.fromkeys([subject] + others)), props,
                          [asdict(a) for a in acts], emo[1], STYLE_FOR[profile], profile,
                          (round(clock, 2), round(clock + dur, 2)), "cut" if i == 0 else "continue", metaphors,
                          figures))
        clock += dur
    board = Storyboard(title or sents[0][:60], domain, beats)
    board.cast = cast
    return board


def _personality(role: str, s: str) -> str:
    if re.search(r"nervous|shy|anxious", s, re.I):
        return "timid"
    if role in ("friend", "teacher", "doctor"):
        return "kind"
    if role in ("customers", "crowd", "people", "friends", "everyone"):
        return "cheerful"
    return "plain"


def _environment(s: str, domain: str) -> str:
    if re.search(r"sea|beach|march|road|street|outside|park", s, re.I):
        return "outdoors"
    if re.search(r"room|class|exam|shop|bakery|lab|office", s, re.I):
        return "indoors"
    return "studio" if domain in ("science", "economics", "politics") else "indoors"


# ---- staging ----------------------------------------------------------------------------------------------------------
COLORS = [(40, 110, 200), (200, 70, 110), (60, 150, 90), (230, 140, 30), (120, 80, 170), (60, 60, 60)]


def stage(board: Storyboard, beat_index: int | None = None):
    """The whole storyboard (or one beat) as a scene on the stick engine: (scene, seconds)."""
    from . import scene2d
    from .stick_demos import _caption
    beats = board.beats if beat_index is None else [board.beats[beat_index]]
    t_shift = beats[0].narration_window[0]
    sc = scene2d.Scene(ppm=230, ground=0.8, horizon=0.6)
    tone = {"outdoors": (232, 238, 226), "indoors": (246, 242, 234), "studio": (240, 242, 246)}[beats[0].environment]
    scene2d.studio(sc, paper=tone)
    w = World()
    cast = getattr(board, "cast", {})
    names = list(dict.fromkeys(n for b in beats for n in b.characters))
    actors: dict[str, Actor] = {}
    spots = {n: (-1.6 + 3.2 * k / max(1, len(names) - 1)) if len(names) > 1 else 0.0 for k, n in enumerate(names)}
    for k, n in enumerate(names):
        c = cast.get(n, Character(n))
        crowd = c.role == "crowd"
        members = 3 if crowd else 1
        for m in range(members):
            nm = n if m == 0 else f"{n}{m + 1}"
            x = spots[n] + (m - 1) * 0.75 if crowd else spots[n]
            a = Actor(rig2d.Look(name=nm, body=COLORS[(k + m) % len(COLORS)], line=1.0,
                                 skin=(226, 186, 150) if c.face else None,
                                 height=1.7 if not crowd else 1.55 + 0.1 * m),
                      x=x, facing=1.0 if x <= 0 else -1.0, faceless=not c.face, world=w, seed=k * 3 + m)
            a.timing = PROFILES[beats[0].timing]
            a.loco.express(0, "neutral")
            actors[nm] = a
    sc.actors += list(actors.values())
    notes = []
    focus = []
    props_live: dict = {}
    t = 0.3
    for b in beats:
        t0, t1 = b.narration_window[0] - t_shift, b.narration_window[1] - t_shift
        t = max(t, t0 + 0.3)
        notes.append((t0 + 0.1, t1 - 0.1, b.narration))
        for fig in b.figures[:1]:
            card = Prop("stat", 3.6, 1.35, 1.9, 0.9, data={"value": fig, "label": "figure from the script",
                                                          "pop": [(t0 + 0.6, 0.0, "linear"), (t0 + 1.1, 1.0, "back")]})
            sc.actors.insert(0, card)
        subj = actors.get(b.characters[0])
        if subj is not None:
            props_live["_subject_x"] = subj.hips_x(t0)
        focus.append((t0, t1, b.characters[:2]))
        for mph in b.metaphors:
            _metaphor(sc, w, mph, t0, t1, props_live)
        for a in b.actions:
            who = actors.get(a["who"]) or next(iter(actors.values()))
            tgt = actors.get(a["target"]) if a["target"] else None
            t = _do(sc, w, who, tgt, a, t, actors, props_live)
        if b.emotion:
            for nm, act in actors.items():
                if nm.startswith(b.characters[0]) and not act.busy(t - 0.2, t + 1.2):
                    act.feel(t - 0.2, t + 1.4, b.emotion)
                    act.loco.express(t - 0.2, {"scared": "nervous", "laugh": "laughing"}.get(b.emotion, b.emotion), 0.3)
        t = max(t + 0.3, t1)
    Ensemble(list(actors.values()), {n: PERSONALITIES.get(cast[n].personality, PERSONALITIES["kind"])
                                     for n in cast if cast[n].personality in PERSONALITIES and n in actors},
             beats[0].timing).apply()
    sc.focus = focus                                  # the camera frames whoever each line is about
    sc.overlay = _caption(f"{board.title} - script-to-animation ({board.domain}; illustrations labelled)", notes)
    return sc, t + 0.6


def _metaphor(sc, w, kind, t0, t1, live):
    if kind == "price card" and "price" not in live:
        p = Prop("sign", -3.4, 0.9, 1.3, 0.75, label="PRICE", data={})
        live["price"] = p
        sc.actors.insert(0, p)
    elif kind == "ballot box" and "ballot" not in live:
        p = Prop("crate", 3.0, 0.0, 0.6, 0.6, label="VOTES")
        live["ballot"] = p
        sc.actors.insert(0, p)
    elif kind == "storm cloud of worry":
        x = live.get("_subject_x", -1.6)
        p = Prop("cloud", x, 2.05, 0.9, 0.38, label="illustration",
                 data={"show": [(t0, 0.0, "linear"), (t0 + 0.6, 1.0, "inout"), (t1 - 0.6, 1.0, "linear"),
                                (t1, 0.0, "inout")]})
        sc.actors.insert(0, p)
    elif kind == "marching group":
        pass                                          # done by the actors themselves (march)
    elif kind == "two objects, same gravity" and "drop_pair" not in live:
        live["drop_pair"] = True


def _obj(sc, live, kind, x, y=0.0):
    key = f"obj_{kind}"
    if key not in live:
        size = {"ball": (0.2, 0.2), "feather": (0.22, 0.08), "crate": (0.4, 0.3), "folder": (0.3, 0.06)}[kind]
        p = Prop("ball" if kind in ("ball", "feather") else kind, x, y, *size,
                 color=(240, 150, 40) if kind == "ball" else (235, 235, 240), data={"friction": 5.0})
        live[key] = p
        sc.actors.append(p)
    return live[key]


def _do(sc, w, a: Actor, b: Actor | None, act: dict, t: float, actors: dict, live: dict) -> float:
    v = act["verb"]
    x = a.hips_x(t)
    f = a._facing_at_build(t)
    if b is not None:
        f = 1.0 if b.hips_x(t) > x else -1.0
        a.look_at(t, t + 2.5, b)
    if v in ("walk", "march"):
        dest = (b.hips_x(t) - f * 0.9) if b is not None else x + f * 1.4
        end = a.walk(t, dest, 0.9 if v == "march" else 1.1)
        if v == "march":
            for nm, o in actors.items():
                if o is not a and not o.busy(t, end):
                    o.walk(t + 0.2, o.hips_x(t) + (dest - x), 0.9)
        return end + 0.2
    if v == "run":
        return a.run(t, x + f * 2.5, 3.4) + 0.2
    if v == "jump":
        return M.jump(a, t, dist=0.8, height=0.4) + 0.1
    if v in ("trip", "roll"):
        if any(m[0] <= t <= m[1] for m in a.loco.moves):
            return t
        return M.trip_roll(a, a.run(t, x + f * 1.2, 3.0) - 0.12) + 0.2
    if v == "climb":
        w.platforms.append((x + f * 0.6, x + f * 1.6, 0.9) if f > 0 else (x - 1.6, x - 0.6, 0.9))
        sc.actors.insert(0, Prop("crate", x + f * 1.1, 0.0, 1.0, 0.9))
        return M.climb(a, t, wall=0.6, top=0.9) + 0.2
    if v == "sit":
        sc.actors.insert(0, Prop("bench", x - f * 0.38, 0.0, 1.2, 0.9, data={"seat": 0.45, "back": -f}))
        return M.sit(a, t, 0.45, 2.0) + 0.1
    if v == "bow":
        return a.act(t, [(0.4, dict(lean=0.9, head=0.4, feet="keep"), "inout"), (0.9, dict(lean=0.9), "linear"),
                         (1.4, dict(lean=0.03, head=0.0), "settle")], "bow")
    if v in ("clap", "cheer", "wave", "point", "explain", "argue", "think", "read"):
        g = {"clap": "clap", "cheer": "cheer", "wave": "wave", "point": "point", "explain": "explain",
             "argue": "shake_fist", "think": "think", "read": "phone"}[v]
        dur = 2.0
        for nm, o in actors.items():
            if nm == a.look.name or (a.look.name == "Crowd" and nm.startswith("Crowd")):
                o.gesture(t, g, dur)
                if v == "argue":
                    o.feel(t, t + dur, "angry")
                    o.say_symbol(t + 0.2, t + 1.4, "#@!")
                if v == "think":
                    o.say_symbol(t + 0.2, t + 1.8, "?")
        return t + dur
    if v == "breathe":
        return a.act(t, [(0.9, dict(lean=-0.12, head=-0.25, au=0.35, al=0.6, bu=0.3, bl=0.5, feet="keep"), "inout"),
                         (1.3, dict(lean=-0.12), "linear"), (2.4, dict(lean=0.0, head=0.05, au=0.1, al=0.25, bu=0.06,
                                                                       bl=0.2), "inout")], "breathe")
    if v == "comfort" and b is not None:
        end = a.walk(t, b.hips_x(t) - f * 0.55, 1.0)
        return M.comfort(a, end + 0.1, b, 1.6)
    if v == "handshake" and b is not None:
        end = a.walk(t, b.hips_x(t) - f * 0.7, 1.0)
        mid = lambda tt: ((a.hips_x(tt) + b.hips_x(tt)) / 2, 1.0)   # noqa: E731
        a.reach(end, end + 1.4, mid, None)
        b.reach(end, end + 1.4, mid, None)
        return end + 1.5
    if v in ("pick", "carry", "give", "trade"):
        kind = "crate" if v in ("give", "trade", "carry") else "ball"
        obj = _obj(sc, live, kind, x + f * 0.45)
        end = M.pick_up(a, t, obj)
        if b is not None and v in ("give", "trade"):
            end = a.walk(end + 0.1, b.hips_x(end) - f * 0.8, 1.0)
            end = M.put_down(a, end + 0.1, obj)
        elif v == "carry":
            end = a.walk(end + 0.1, x + f * 1.5, 1.0)
        return end + 0.1
    if v == "juggle":
        obj = _obj(sc, live, "ball", x + f * 0.4)
        end = M.pick_up(a, t, obj)
        for k in range(3):                              # up and caught, three times
            end = M.throw(a, end, obj, lambda tt: M.chest(a, tt), flight=0.75)
            M.catch(a, end, obj, hold=0.15)
            end += 0.2
        return end
    if v == "drop":
        obj = live.get("obj_ball") or _obj(sc, live, "ball", x + f * 0.4)
        if not obj.carriers:
            M.pick_up(a, t, obj)
            t += 1.0
        for i, c in enumerate(obj.carriers):
            obj.carriers[i] = (c[0], min(c[1], t + 0.1), c[2], c[3])
        obj.launch(t + 0.1, (f * 0.6, 0.0), world=w)
        return t + 0.9
    if v == "equal_fall":
        for k, (kind, dx) in enumerate((("ball", -0.25), ("feather", 0.25))):
            p = _obj(sc, live, kind, x + f * (0.7 + dx), 1.6)
            p.launch(t + 0.2, (0.0, 0.0), bounce=0.0, world=w)  # no air: same gravity, same fall
        a.look_at(t, t + 1.5, (x + f * 0.7, 0.6))
        return t + 1.6
    if v == "price_up":
        price = live.get("price")
        if price is not None:
            price.label = "PRICE  ↑"
        return t + 0.8
    if v == "vote":
        box = live.get("ballot") or _obj(sc, live, "crate", 3.0)
        end = a.walk(t, box.x - f * 0.6, 1.0)
        return M.tap(a, end + 0.1, (box.x, 0.65)) + 0.1
    if v == "say":
        return a.say_line(t, t + max(2.0, 0.07 * len(act["line"]) + 1.0), act["line"], None) + 0.1
    if v == "hide":
        a.posture(t, t + 2.0, lean=0.5, crouch=0.15)
        return a.walk(t, x - f * 1.0, 0.6) + 0.2
    return t + 1.0


if __name__ == "__main__":
    import sys
    from pathlib import Path
    script = Path(sys.argv[1]).read_text() if Path(sys.argv[1]).exists() else sys.argv[1]
    board = plan(script)
    print(board.to_json())


def render_script(script: str, out, title: str = "", width: int = 1280, height: int = 720):
    """Plan -> stage -> QC loop (corrections, camera) -> render -> check. Writes the plan and QC report next to it."""
    import json as _json
    from pathlib import Path

    from . import qc
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    board = plan(script, title)
    out.with_suffix(".plan.json").write_text(board.to_json())

    def build():
        sc, T = stage(board)
        return sc.resize(width, height), T
    sc, T, report, framing, passes, fixes = qc.refine(build, style=board.beats[0].camera)
    sc.render(out, T, android=out.with_name(out.stem + "_android.mp4"))
    video = qc.check_video(out, T, sc.fps)
    out.with_suffix(".qc.json").write_text(_json.dumps(dict(motion=_json.loads(report.to_json()), corrections=fixes,
                                                            framing=[vars(d) for d in framing], video=video),
                                                       indent=1, default=str))
    return out
