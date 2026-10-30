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
PROFILE_FOR = {"story": "comedy", "comedy": "comedy", "science": "explainer", "economics": "explainer", "history": "drama",
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
    (r"\bchas(?:es|ed|e)\b|\bfollows?\b", "chase"), (r"\bsteals?\b|\bstole\b|\bsnatch\w*", "steal"),
    (r"\blands?\b(?! at the same)|\blanded\b|\bswoops?\b|\bflies (?:in|down)", "land"),
    (r"\brows?\b|\browed\b|\bpaddles?\b|\bsails?\b|\bdrives?\b|\brides?\b|\bcycles?\b", "ride"),
    (r"\blaugh(?:s|ed)?\b|\bgiggl\w*", "laugh"),
]
ROLE_NOUNS = r"baker|student|teacher|friend|friends|customer|customers|king|queen|scientist|astronaut|soldier|worker|" \
             r"workers|people|crowd|farmer|doctor|child|children|man|woman|boy|girl|officer|leader|voters?|everyone|" \
             r"fisherman|fishermen|shopkeeper|vendor|sailor|driver|mother|father|grandmother|grandfather|neighbou?r|" \
             r"chef|guard|nurse|pilot|policeman|policewoman|grandma|grandpa"
TITLES = re.compile(r"^(?:Old|Young|Little|Big|Mr|Mrs|Ms|Dr|Uncle|Aunt|Auntie|Grandma|Grandpa|Granny|Sir|Lady)\.?\s+"
                    r"(?=[A-Z])")
ANIMALS = r"pelican|seagull|gull|crow|parrot|pigeon|sparrow|eagle|duck|hen|chicken|owl|heron|bird|dog|puppy|cat|" \
          r"kitten|cow|buffalo|ox|horse|pony|donkey|goat|sheep|monkey|elephant|lion|tiger|camel|rabbit|mouse|rat|fox|" \
          r"bear|deer|squirrel|frog|snake|turtle"
PLACES = r"harbou?r|port|dock|beach|shore|sea|river|lake|village|town|city|street|road|market|park|field|farm|" \
         r"forest|garden|hill|mountain|desert|dawn|sunrise|sunset|night|morning|evening|room|kitchen|office|school|" \
         r"classroom|home"
ADJ = r"(?:(?!(?:and|or|but|with|to|of|at|in|on|past|into|next)\b)[a-z]+(?:'s)?\s+){0,2}?"
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
    things: list = field(default_factory=list)     # objects and scenery the line names (built from the asset library)


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
    if scores[best] <= 1 and re.search(rf"\b(?:{ANIMALS})\b", text, re.I) or scores[best] == 0 and \
            re.search(r"\b[A-Z][a-z]+ (?:\w+ ){0,3}(?:walks|runs|rows|laughs|chases|finds|says)\b", text):
        return "story"                                # a tale with characters, not a subject explainer
    return best if scores[best] else "psychology"


def _names(sentence: str, known: list[str]) -> list[str]:
    words = [m.group(0) for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", sentence)]
    words = [w for w in words if not re.fullmatch(r"(In|On|At|The|A|An|He|She|They|It|When|Some|With|Without|Both|"
                                                  r"Then|After|Before|But|And|This|That|Everyone|Thousands)\s+.*", w)]
    skip = {"In", "On", "At", "The", "A", "An", "He", "She", "They", "It", "His", "Her", "When", "Some", "With",
            "Without", "Both", "Everyone", "Then", "After", "Before", "But", "And", "Thousands", "Moon", "British",
            "Salt", "March", "Salt March", "This", "That", "One", "Two", "Three", "Dandi", "Apollo"}
    out = [TITLES.sub("", w) for w in words if w not in skip]
    return [w for w in dict.fromkeys(out) if w not in ("I",)] or [k for k in known if k.lower() in sentence.lower()]


def plan(script: str, title: str = "") -> Storyboard:
    sents = _sentences(script)
    domain = _domain(script)
    profile = PROFILE_FOR[domain]
    cast: dict[str, Character] = {}
    last_subject = None
    mentioned_all: list = []
    beats = []
    clock = 0.0
    for i, s in enumerate(sents):
        names = _names(s, list(cast))
        pos = {n: s.find(n) for n in names}
        roles = []
        for m in re.finditer(rf"\b(?:a|an|the|her|his|their)\s+{ADJ}({ROLE_NOUNS})(?:'s)?\b", s, re.I):
            before = s[:m.start()].rstrip()
            appos = re.search(r"([A-Z][a-z]+)$", before)                                   # "Tomas the fisherman"
            if appos and m.group(0).lower().startswith("the ") and TITLES.sub("", appos.group(1)) in names + list(cast):
                cast.setdefault(appos.group(1), Character(appos.group(1), m.group(1).lower())).role = m.group(1).lower()
                continue
            nxt = re.match(r"\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", s[m.end():])          # "her friend Sam"
            roles.append((m.group(1), nxt.group(1) if nxt else ""))
        for m in re.finditer(rf"\b(?:a|an|the|her|his|their)\s+({ADJ})({ANIMALS})\b", s, re.I):
            key = m.group(2).capitalize()
            if key not in cast:
                cast[key] = Character(key, "animal", face=False, personality="cheerful",
                                      label=(m.group(1) + m.group(2)).strip())
            pos[key] = m.start(2)
            names.append(key)
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
        mentioned = mentioned_all                     # who has been named so far, most recent last
        subject = names[0] if names else (last_subject or next(iter(cast), None))
        if re.match(r"\s*(?:he|she|they)\b", s, re.I) and last_subject:          # "He laughs" - the last subject
            subject = last_subject
            names = [subject] + [n for n in names if n != subject]
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
        if not others and re.search(r"\b(him|her)\b", s, re.I):                # "lands next to him"
            people = [n for n in reversed(mentioned) if n != subject and cast.get(n) and cast[n].role != "animal"]
            if people:
                others = [people[0]]
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
        things = []                                   # nouns that need an asset: "his boat", "the lighthouse"
        taken = {c.label.split()[-1].lower() for c in cast.values() if c.role == "animal"} | \
            {c.role for c in cast.values()} | {n.lower() for n in cast}
        stop = r"(?:a|an|the|his|her|their|its|and|or|but|with|to|of|at|in|on|into|onto|past|next|from|by|for|" \
               r"is|are|was|were|then|him|them|it)"
        verbs_rx = "|".join(rx for rx, _ in VERBS)
        for m in re.finditer(rf"\b(?:a|an|the|his|her|their|its)\s+((?:(?!{stop}\b)[a-z']+\s*){{1,3}})", s):
            words_ = m.group(1).split()
            while len(words_) > 1 and re.match(rf"(?:{verbs_rx})$", words_[-1], re.I):
                words_.pop()                              # "the pelican lands" - stop before the verb
            head = words_[-1].lower().rstrip("'s")
            phrase = " ".join(words_)
            if head in taken or re.fullmatch(rf"(?:{ROLE_NOUNS}|{ANIMALS})", head) or re.match(rf"(?:{verbs_rx})$", head, re.I):
                continue
            if re.fullmatch(rf"(?:{PLACES})", head):
                continue
            things.append(phrase)
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
        mentioned_all = [n for n in mentioned if n not in names] + list(names)
        env = _environment(s, domain, beats[-1].environment if beats else None)
        beats.append(Beat(i, s, domain, env, list(dict.fromkeys([subject] + others)), props,
                          [asdict(a) for a in acts], emo[1], STYLE_FOR[profile], profile,
                          (round(clock, 2), round(clock + dur, 2)), "cut" if i == 0 else "continue", metaphors,
                          figures, list(dict.fromkeys(things))))
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


def _environment(s: str, domain: str, previous: str | None = None) -> str:
    """Where the line happens; a line that names no place stays where the story already is."""
    if re.search(r"\b(sea|beach|march|road|street|outside|park|harbou?r|port|dock|shore|river|lake|village|field|"
                 r"farm|forest|garden|hill|mountain|dawn|sunrise|sunset|market stalls?|lighthouse|boat)\b", s, re.I):
        return "outdoors"
    if re.search(r"room|class|exam|shop|bakery|lab|office", s, re.I):
        return "indoors"
    if previous:
        return previous
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
    every = list(dict.fromkeys(n for b in beats for n in b.characters))
    first = {n: next(i for i, b in enumerate(beats) if n in b.characters) for n in every}
    animal_names = [n for n in every if cast.get(n) and cast[n].role == "animal"]
    names = [n for n in every if n not in animal_names and first[n] == 0]   # on stage from the start
    late = [n for n in every if n not in animal_names and first[n] > 0]     # they walk in when they first appear
    actors: dict[str, Actor] = {}
    spots = {n: (-1.6 + 3.2 * k / max(1, len(names) - 1)) if len(names) > 1 else 0.0 for k, n in enumerate(names)}
    world = _Stuff(sc, w)
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
    for bi, b in enumerate(beats):
        t0, t1 = b.narration_window[0] - t_shift, b.narration_window[1] - t_shift
        t = max(t, t0 + 0.3)
        notes.append((t0 + 0.1, t1 - 0.1, b.narration))
        here = next((x.hips_x(t) for n, x in actors.items() if n in b.characters), None)
        if here is None:
            here = next((world.animals[n].pos(t)[0] for n in b.characters if n in world.animals), 0.0)
        for n in b.characters:                      # newcomers: animals from the asset library, people walk in
            if n in animal_names and n not in world.animals:
                world.animal(n, cast[n].label or n, here, t, landing=any(a["verb"] == "land" and a["who"] == n
                                                                         for a in b.actions))
            elif n in late and n not in actors:
                k = len(actors)
                c = cast.get(n, Character(n))
                a = Actor(rig2d.Look(name=n, body=COLORS[k % len(COLORS)], line=1.0,
                                     skin=(226, 186, 150) if c.face else None, height=1.5 if c.role in
                                     ("girl", "boy", "child") else 1.7),
                          x=here + 6.5, facing=-1.0, faceless=not c.face, world=w, seed=k * 3)
                a.timing = PROFILES[beats[0].timing]
                actors[n] = a
                sc.actors.append(a)
                t = a.walk(t, here + 1.6, 1.3) + 0.1
                world.log.append(f"{n} walks in at {t:.1f} s (first named in line {bi + 1})")
        world.place(b, here, t, actors)
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
            if a["who"] in world.animals:
                t = world.animal_do(a, t, actors, b)
                continue
            who = actors.get(a["who"]) or next(iter(actors.values()))
            if a["verb"] in ("chase", "ride", "laugh", "give") and world.handles(a, who, actors, b):
                t = world.actor_do(a, who, t, actors, b)
                continue
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
    sc.asset_log = world.assets
    sc.decisions = world.log
    sc.overlay = _caption(f"{board.title} - script-to-animation ({board.domain}; illustrations labelled)", notes)
    return sc, t + 0.6


SMALL = r"fish|basket|bag|cup|phone|book|key|hat|coin|flower|letter|bottle|ball|box|plate|apple|umbrella|parcel|gift|" \
        r"bread|cake|toy|stick|net"
VEHICLES = ("boat", "car", "bus", "bicycle")


class _Stuff:
    """Animals, objects and scenery for a script, built from the asset library (generated when it can, a labelled
    placeholder when it can't - both logged), and what the animals do."""

    def __init__(self, sc, w):
        from . import asset_lib
        self.sc, self.w, self.A = sc, w, asset_lib
        self.lib = asset_lib.Library.default()
        self.things: dict = {}
        self.animals: dict = {}
        self.held: dict = {}
        self.assets: list = []
        self.log: list = []

    def _asset(self, phrase, head, small, big):
        q = self.A.parse(phrase)
        aid, how = self.lib.obtain(phrase if q["kind"] else head)
        a = self.lib.get(aid)
        if how == "placeholder":
            w_, h_ = (0.34, 0.2) if small else (1.4, 3.2) if big else (1.0, 1.2)
            aid = self.lib.register(self.A.placeholder(head, w_, h_), render_test=False)
            a = self.lib.get(aid)
        self.assets.append({"for": phrase, "asset": aid, "how": how, "kind": a["kind"]})
        return a

    def _prop(self, a, x, y, z, name, flip=1.0):
        p = Prop("shape", x, y, a["w"], a["h"], z=z, label=name,
                 data={"parts": a["parts"], "text": a.get("text", ""), "flip": flip})
        p.name = name
        return p

    def thing(self, phrase, x, y=0.0):
        head = re.sub(r"'s$", "", phrase.split()[-1].lower())
        if head in self.things:
            return self.things[head]
        small = bool(re.fullmatch(SMALL, head))
        kind = self.A.parse(phrase)["kind"]
        big = not small and kind not in VEHICLES
        a = self._asset(phrase, head, small, big)
        z = 1.0 if small or kind in VEHICLES else 1.6
        p = self._prop(a, x, y, z, head)
        p.data["kind"] = kind or ""
        self.things[head] = p
        if z > 1.0:
            self.sc.actors.insert(0, p)
        else:
            self.sc.actors.append(p)
        return p

    def place(self, b, here, t, actors):
        """Scenery named in a line is put ahead of the action; a vehicle under its rider; small things wait for
        the action that uses them."""
        ahead = 2.2
        for phrase in b.things:
            head = re.sub(r"'s$", "", phrase.split()[-1].lower())
            if head in self.things or re.fullmatch(SMALL, head):
                continue
            kind = self.A.parse(phrase)["kind"]
            if kind in VEHICLES:
                self.thing(phrase, here)
            else:
                self.thing(phrase, here + ahead)
                ahead += 2.6

    def animal(self, name, desc, here, t, landing):
        a = self._asset(desc, name.lower(), False, False)
        x, y = (here + 7.0, 3.2) if landing else (here + 6.0, 0.0)
        p = self._prop(a, x, y, 1.0, name, flip=-1.0)
        p.data["flips"] = [[0.0, -1.0]]
        self.animals[name] = p
        self.sc.actors.append(p)
        if not landing:
            self.move(p, t, t + 2.0, here + 1.4, 0.0)

    def move(self, p, t0, t1, x, y, how="inout"):
        x0 = p.pos(t0)[0]
        if abs(x - x0) > 0.05:
            p.data.setdefault("flips", []).append([t0, 1.0 if x > x0 else -1.0])
        p.move(t0, t1, x, y, 0.0, how)
        obj = self.held.get(p.name)
        if obj is not None:
            d = 1.0 if x >= x0 else -1.0
            obj.move(t0, t1, x + d * p.w * 0.42, y + p.h * 0.62, 0.0, how)

    def _small(self, b, near):
        phrase = next((ph for ph in b.things if re.fullmatch(SMALL, re.sub(r"'s$", "", ph.split()[-1].lower()))), None)
        return self.thing(phrase, near) if phrase else None

    def animal_do(self, act, t, actors, b):
        p = self.animals[act["who"]]
        v = act["verb"]
        tgt = actors.get(act["target"]) if act["target"] else None
        x, y, _ = p.pos(t)
        if v == "land":
            tx = (tgt.hips_x(t) + 1.1) if tgt is not None else x - 3.0
            self.move(p, t, t + 1.5, tx, 0.0, "out")
            if tgt is not None:
                tgt.look_at(t, t + 2.5, p)
            return t + 1.6
        if v == "steal":
            obj = self._small(b, (tgt.hips_x(t) + 0.55) if tgt is not None else x - 0.5)
            if obj is None:
                return t + 0.5
            if tgt is not None:
                tgt.look_at(t, t + 2.0, obj)
            ox = obj.pos(t)[0]
            self.move(p, t, t + 0.5, ox - 0.1, 0.0)
            self.held[p.name] = obj
            self.log.append(f"{p.name} grabs the {obj.name} at {t + 0.5:.1f} s")
            self.move(p, t + 0.6, t + 1.5, ox + 1.6, 1.1, "out")
            if tgt is not None:
                tgt.loco.express(t + 0.6, "shocked", 0.15)
                tgt.say_symbol(t + 0.7, t + 1.6, "!")
            return t + 1.6
        if v == "drop":
            obj = self.held.pop(p.name, None)
            tx = (tgt.hips_x(t) + 0.45) if tgt is not None else x + 1.0
            basket = None
            if tgt is not None:
                for phrase in b.things:
                    if phrase != "fish" and re.fullmatch(SMALL, re.sub(r"'s$", "", phrase.split()[-1].lower())) and \
                            (obj is None or not phrase.endswith(obj.name)):
                        basket = self.thing(phrase, tx)
            self.move(p, t, t + 1.4, tx, 1.5)
            if obj is not None:
                obj.move(t, t + 1.4, tx + 0.15, 1.5 + p.h * 0.62, 0.0, "inout")
                floor = (basket.h * 0.6) if basket is not None else 0.0
                obj.move(t + 1.45, t + 1.85, tx, floor, 0.0, "in")
                self.log.append(f"{p.name} drops the {obj.name}" + (f" into the {basket.name}" if basket else ""))
            self.move(p, t + 1.9, t + 3.2, tx + 6.0, 3.0, "in")
            if tgt is not None:
                tgt.look_at(t, t + 3.0, p)
                tgt.loco.express(t + 1.8, "happy", 0.3)
            return t + 2.4
        if v in ("walk", "run", "chase"):
            self.move(p, t, t + 1.6, x + 2.5, y)
            return t + 1.7
        return t + 0.8

    def handles(self, act, who, actors, b) -> bool:
        if act["verb"] == "chase":
            return act["target"] in self.animals
        if act["verb"] == "ride":
            return any(self.A.parse(ph)["kind"] in VEHICLES for ph in b.things)
        if act["verb"] == "give":
            return any(re.fullmatch(SMALL, ph.split()[-1]) and ph.split()[-1] in self.things for ph in b.things)
        return act["verb"] == "laugh"

    def actor_do(self, act, a, t, actors, b):
        v = act["verb"]
        x = a.hips_x(t)
        f = a._facing_at_build(t)
        if v == "laugh":
            a.gesture(t, "laugh", 1.6)
            a.feel(t, t + 1.8, "laugh")
            if not a.faceless:
                a.loco.express(t, "laughing", 0.2)
            return t + 1.2
        if v == "ride":                                # the rider stands in the vehicle and moves with it
            veh = next(self.things[re.sub(r"'s$", "", ph.split()[-1].lower())] for ph in b.things
                       if self.A.parse(ph)["kind"] in VEHICLES)
            dist, dur = 3.2 * f, 3.4
            veh.x = x
            veh.move(t + 0.5, t + dur, x + dist, 0.0, 0.0, "linear")
            y0 = M._stand(a)
            deck = veh.h * 0.55
            row = lambda k: dict(au=0.9 if k % 2 else 0.25, al=1.2 if k % 2 else 0.5, bu=0.85 if k % 2 else 0.2,   # noqa: E731
                                 bl=1.1 if k % 2 else 0.45)
            keys = [(0.5, dict(y=y0 + deck, feet=(None, None), **row(0)), "inout")]     # settle into the vehicle
            for k in range(1, 6):                      # rowing strokes while the vehicle carries them
                keys.append((0.5 + (dur - 0.5) * k / 6, dict(dx=dist * f * k / 6, y=y0 + deck, feet=(None, None),
                                                             **row(k)), "linear"))
            keys.append((dur, dict(dx=dist * f, y=y0 + deck, feet=(None, None), **row(0)), "linear"))
            keys.append((dur + 0.55, dict(dx=dist * f + 0.55, y=y0, lean=0.0, au=0.3, al=0.6, bu=0.3, bl=0.6), "settle"))
            self.log.append(f"{a.look.name} rides the {veh.name} {abs(dist):.1f} m and steps out")
            return a.act(t, keys, "ride", dx=dist * f + 0.55) + 0.2
        if v == "chase":
            p = self.animals[act["target"]]
            px, py, _ = p.pos(t)
            d = 1.0 if px >= x else -1.0
            self.move(p, t, t + 2.6, px + 5.5 * d, max(py, 1.3), "inout")
            a.look_at(t, t + 3.0, p)
            a.say_symbol(t + 0.2, t + 1.4, "Hey!")
            return a.run(t + 0.2, px + 5.5 * d - 1.4 * d, 3.0) + 0.2
        if v == "give":                                # the thing is already with them: a gesture, not a hand-over
            tgt = actors.get(act["target"])
            if tgt is not None:
                d = 1.0 if tgt.hips_x(t) > x else -1.0
                end = a.walk(t, tgt.hips_x(t) - d * 0.9, 1.0) if abs(tgt.hips_x(t) - x) > 1.2 else t
                a.gesture(end + 0.1, "point", 1.2)
                a.nod(end + 1.3)
                tgt.gesture(end + 1.4, "wave", 1.2)
                self.log.append(f"'gives her the fish': the fish is already in her basket, so {a.look.name} lets "
                                "her keep it (a point and a nod) - an interpretation")
                return end + 2.4
        return t + 0.8


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
        sc.actors.insert(0, Prop("bench", x - f * 0.38, 0.0, 0.5, 0.9, data={"seat": 0.45, "back": -f}))
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
    from . import sound
    wav = sound.soundtrack(build, fixes, sc, T, board.beats[0].environment, out.with_suffix(".wav"))
    sc.render(out, T, android=out.with_name(out.stem + "_android.mp4"), audio_wav=wav)
    video = qc.check_video(out, T, sc.fps)
    out.with_suffix(".qc.json").write_text(_json.dumps(dict(motion=_json.loads(report.to_json()), corrections=fixes,
                                                            framing=[vars(d) for d in framing], video=video),
                                                       indent=1, default=str))
    return out
