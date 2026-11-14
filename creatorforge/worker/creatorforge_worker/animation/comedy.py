"""Visual comedy: structures, not just slapstick moves. Each builder stages a classic comic beat with the stick
engine and returns its end time; comedy timing (a beat before the punchline, a hold after it) is built in, and
the camera is pointed at whoever is reacting (sc.focus) because the laugh is usually on the reaction.

    take(a, t)                     squash-and-stretch surprise: rise up stretched, snap, squash down, settle
    double_take(a, t, target)      a casual glance, look away, a beat... snap back with a take and a "!"
    slow_burn(a, t, target, dur)   a stare that heats up: neutral, annoyed, angry - then the explosion
    deadpan(a, t, dur)             no expression, perfectly still apart from a blink, held for the laugh
    pratfall(a, t)                 a trip and roll, then a sheepish recovery (embarrassed, a little wave)
    rule_of_three(a, t, ok, fail)  the same thing works twice; the third time it goes wrong
    button(a, t)                   a small after-gag that closes the scene ("...", a shrug)

These are for cartoons and satire. They never add text or claims; satire is labelled by visual_reasoning."""
from __future__ import annotations

from . import motions as M
from .stick import Actor


def _focus(sc, t0, t1, *names):
    if sc is not None:
        sc.focus = getattr(sc, "focus", []) + [(t0, t1, list(names))]


def take(a: Actor, t: float) -> float:
    H, y0 = a.H, M._stand(a)
    keys = [
        (0.08, dict(y=y0 - 0.04 * H, squash=0.9, feet="keep"), "inout"),                      # tiny anticipation
        (0.2, dict(y=y0 + 0.07 * H, squash=1.12, lean=-0.25, head=-0.45, au=2.4, al=2.8, bu=2.3, bl=2.7,
                   feet="keep"), "out"),                                                     # stretch up, arms fly
        (0.38, dict(y=y0 - 0.05 * H, squash=0.9, lean=0.1, head=0.1), "inout"),                # squash back down
        (0.7, dict(y=y0, squash=1.0, lean=0.0, head=0.0, au=0.3, al=0.6, bu=0.3, bl=0.6), "settle"),
    ]
    return a.act(t, keys, "take")


def double_take(a: Actor, t: float, target, sc=None) -> float:
    a.look_at(t, t + 0.6, target)                             # notices... doesn't register
    a.look_at(t + 0.6, t + 1.3, (a.hips_x(t) - 2.0 * a._facing_at_build(t), 1.4))   # looks away, casual
    if not a.faceless:
        a.loco.express(t, "neutral", 0.2)
    t2 = t + 1.45                                             # the beat
    a.look_at(t2, t2 + 1.4, target)
    if not a.faceless:
        a.loco.express(t2, "shocked", 0.08)
    a.say_symbol(t2 + 0.05, t2 + 1.0, "!")
    end = take(a, t2)
    _focus(sc, t2 - 0.2, end + 0.4, a.look.name)
    return end + 0.2


def slow_burn(a: Actor, t: float, target, dur: float = 3.0, sc=None) -> float:
    a.look_at(t, t + dur + 1.5, target)
    stages = [("neutral", 0.0), ("suspicious", 0.3), ("frustrated", 0.6), ("furious", 0.85)]
    for face, k in stages:
        if not a.faceless:
            a.loco.express(t + dur * k, face, dur * 0.25)
    a.posture(t, t + dur, lean=0.22, crouch=0.0)              # leaning in, slowly
    a.feel(t + dur * 0.6, t + dur, "frustrated")
    boom = t + dur
    a.feel(boom, boom + 1.4, "angry")
    a.gesture(boom, "shake_fist", 1.4)
    a.say_symbol(boom, boom + 1.2, "#@!")
    _focus(sc, t, boom + 1.4, a.look.name)
    return boom + 1.5


def deadpan(a: Actor, t: float, dur: float = 1.6, sc=None) -> float:
    if not a.faceless:
        a.loco.express(t, "bored", 0.1)
    a.act(t, [(dur, dict(feet="keep"), "linear")], "deadpan")   # held: only breath and blinks
    _focus(sc, t, t + dur, a.look.name)
    return t + dur


def pratfall(a: Actor, t: float, sc=None) -> float:
    end = M.trip_roll(a, t)
    a.feel(end, end + 1.3, "embarrassed")
    if not a.faceless:
        a.loco.express(end - 0.3, "embarrassed", 0.2)
    a.gesture(end + 0.4, "wave", 1.0)                         # "I'm fine"
    _focus(sc, t, end + 1.4, a.look.name)
    return end + 1.5


def rule_of_three(a: Actor, t: float, ok, fail, gap: float = 0.5) -> float:
    """ok(a, t) -> end and fail(a, t) -> end stage the success and the failure; ok runs twice, then fail."""
    t = ok(a, t) + gap
    t = ok(a, t) + gap * 1.4                                  # the expectation is set...
    return fail(a, t)                                         # ...and broken


def button(a: Actor, t: float, sc=None) -> float:
    a.say_symbol(t, t + 1.2, "...")
    a.gesture(t + 0.3, "shrug", 1.2)
    _focus(sc, t, t + 1.5, a.look.name)
    return t + 1.5
