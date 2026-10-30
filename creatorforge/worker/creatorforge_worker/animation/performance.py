"""Performance direction: a line of dialogue becomes a whole performance, not a gesture.

    perform(lines, actors, personalities, start, timing) -> end time, decisions

For each line (speaker, text, optional emotion, optional listener):
* anticipation - a small breath in (chin up, chest up) a beat before the first word;
* facing and gaze - the speaker turns to and looks at the listener; on a long, thoughtful line they glance away
  mid-sentence and come back; listeners look at whoever is talking;
* expression - from the emotion given, or read from the words (a question, an exclamation, laughter, apology,
  anger, fear, greeting); the change is blended at the speaker's own speed (energetic quick, calm slow), and a big
  swing (furious -> laughing) passes through an in-between beat instead of snapping;
* gesture - chosen by what the line does (asks, insists, explains, greets, laughs, refuses, points at someone) and by
  personality (energetic characters gesture bigger and more often, calm ones less), never the same gesture twice
  in a row by the same character;
* speech - a bubble timed to a speaking pace set by personality; the mouth moves when the character has a face;
* listeners - nod at statements, react with their own feeling (warm characters mirror, grumpy ones contrast, timid
  ones flinch at anger) after their personal reaction delay;
* pauses - a beat between lines from the timing profile, longer before a punchline ("..." or a final "!" in comedy).

Every decision is returned (who, when, what, why) so a critic or an editor can review and change it."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .behaviour import PERSONALITIES, Personality
from .stick import Actor
from .timing import PROFILES, Timing

READ = [  # (pattern on the words, emotion, face, gesture)
    (r"\bha(?:[\s,]*ha)+\b|\b(lol|hilarious|funny)\b", "laugh", "laughing", "laugh"),
    (r"\b(sorry|apolog|my fault|forgive)\b", "embarrassed", "embarrassed", "scratch_head"),
    (r"\b(no way|stop|never|how dare|enough)\b|!{2,}", "angry", "angry", "shake_fist"),
    (r"\b(scared|afraid|help|oh no)\b", "scared", "frightened", "hands_up"),
    (r"\b(hello|hi|hey|welcome|good morning)\b", "happy", "happy", "wave"),
    (r"\b(thank|great|wonderful|love|yes!)\b", "happy", "joyful", "cheer"),
    (r"\b(why|how|what|really)\b.*\?$|\?$", "curious", "confused", "shrug"),
    (r"\b(because|so|that means|here's|first|then)\b", "", "focused", "explain"),
    (r"!$", "surprised", "surprised", "point"),
]
HOT, COOL = {"angry", "furious", "scared", "sad", "frustrated"}, {"happy", "laugh", "joyful", "excited"}


@dataclass
class Decision:
    who: str
    t: float
    what: str
    why: str


def read_line(text: str) -> tuple[str, str, str]:
    for rx, emo, face, gesture in READ:
        if re.search(rx, text.strip(), re.I):
            return emo, face, gesture
    return "", "neutral", "talk"


def perform(lines: list[dict], actors: dict, personalities: dict | None = None, start: float = 0.5,
            timing: Timing | str = "explainer") -> tuple[float, list[Decision]]:
    """lines: [{"who": name, "text": "...", "emotion": optional, "to": optional listener name}]"""
    tm = PROFILES[timing] if isinstance(timing, str) else timing
    pers = {n: (personalities or {}).get(n, PERSONALITIES.get("kind")) for n in actors}
    log: list[Decision] = []
    last_gesture: dict[str, str] = {}
    last_feel: dict[str, str] = {}
    t = start
    for k, ln in enumerate(lines):
        who, text = ln["who"], ln["text"]
        a: Actor = actors[who]
        P: Personality = pers[who] or Personality("plain")
        listener_name = ln.get("to") or next((n for n in actors if n != who), None)
        b: Actor | None = actors.get(listener_name) if listener_name else None
        emo, face, gesture = read_line(text)
        emo = ln.get("emotion", emo) or emo
        if ln.get("emotion"):
            face = {"angry": "angry", "laugh": "laughing", "scared": "frightened", "sad": "sad",
                    "happy": "happy", "surprised": "surprised", "confused": "confused"}.get(emo, face)
        punch = tm.name == "comedy" and (k == len(lines) - 1 or text.endswith("...") or text.endswith("!"))
        t += tm.pause * (1.6 if punch else 1.0) * (1.0 if k else 0.0)
        # face the listener and look at them; everyone else looks at the speaker
        if b is not None:
            towards = 1.0 if b.hips_x(t) > a.hips_x(t) else -1.0
            if a._facing_at_build(t) != towards and not a.busy(t - 0.2, t + 0.3, moving_only=True):
                a.turn(t - 0.2, towards)
                log.append(Decision(who, t - 0.2, "turn to listener", f"facing away from {listener_name}"))
        words = len(text.split())
        pace = 2.7 * P.energy
        dur = max(1.4, words / pace + 0.6)
        for n, o in actors.items():
            if n != who:
                o.look_at(t - 0.3, t + dur, a)
        if b is not None:
            if words > 10 and gesture in ("explain", "talk"):            # glance away to think, come back
                mid = t + dur * 0.45
                a.look_at(t - 0.2, mid - 0.15, b)
                a.look_at(mid - 0.15, mid + 0.5, (a.hips_x(mid) - (b.hips_x(mid) - a.hips_x(mid)) * 0.5, 2.2))
                a.look_at(mid + 0.5, t + dur, b)
                log.append(Decision(who, mid, "glance away", "a long, thoughtful line"))
            else:
                a.look_at(t - 0.2, t + dur, b)
        # anticipation: a breath in before speaking
        a.nods.append((t - 0.35, t - 0.05, "breath"))
        # expression with its transition
        blend = 0.12 if P.energy > 1.15 else 0.4 if P.energy < 0.85 else 0.25
        prev = last_feel.get(who, "")
        if prev in HOT and emo in COOL or prev in COOL and emo in HOT:
            a.loco.express(t - 0.3, "surprised" if emo in COOL else "neutral", 0.15)
            log.append(Decision(who, t - 0.3, "in-between beat", f"{prev} -> {emo} is too big a jump"))
        if not a.faceless:
            a.loco.express(t - 0.1, face, blend)
        if emo:
            a.feel(t, t + dur, emo)
            last_feel[who] = emo
        # gesture, never the same twice in a row, scaled by personality
        if gesture == last_gesture.get(who):
            gesture = {"explain": "talk", "talk": "explain", "point": "talk", "shrug": "think"}.get(gesture, "talk")
            log.append(Decision(who, t, "varied gesture", "would have repeated the last one"))
        if P.energy >= 0.8 or gesture not in ("talk",):
            a.gesture(t + 0.1, gesture, min(dur, 2.2))
            last_gesture[who] = gesture
            log.append(Decision(who, t + 0.1, f"gesture {gesture}", f"line reads as {emo or 'neutral'}"))
        a.say_line(t, t + dur, text)
        # listeners react, in character, after their own delay
        for n, o in actors.items():
            if n == who:
                continue
            Q = pers[n] or Personality("plain")
            rt = t + dur * 0.6 + tm.reaction_delay * Q.delay
            if emo in ("angry", "frustrated"):
                r = "scared" if Q.boldness < -0.3 else "angry" if Q.boldness > 0.4 and Q.warmth < 0 else "surprised"
            elif emo in COOL:
                r = "happy" if Q.warmth > 0.2 else "sarcastic" if Q.warmth < -0.3 else ""
            elif emo == "sad":
                r = "sad" if Q.warmth > 0 else ""
            else:
                r = ""
            if r and not o.busy(rt, rt + 1.0):
                o.feel(rt, rt + 1.2, r)
                if not o.faceless:
                    o.loco.express(rt, {"scared": "nervous", "angry": "angry", "happy": "happy", "sad": "sad",
                                        "surprised": "surprised", "sarcastic": "sarcastic"}[r], 0.25)
                log.append(Decision(n, rt, f"reacts {r}", f"to {who}'s {emo} line, personality {Q.name}"))
            elif not emo or emo in ("curious", ""):
                o.nod(t + dur * 0.7, 0.6, "yes")
                log.append(Decision(n, t + dur * 0.7, "nods", "listening"))
        t += dur
    return t, log
