"""Timing profiles: how a film breathes. The same action reads differently in a comedy (a big anticipation, a snappy
overshoot, a held pose for the laugh, a beat before anyone reacts), an explainer (clean and even), political satire
(deadpan holds), drama (slower, longer pauses, little overshoot) or action (fast, small anticipation, punchy).

    actor.timing = PROFILES["comedy"]

A profile changes every keyframed action that actor performs: segment durations (except flights, which keep real
gravity, and push-offs, which must end at the take-off speed), the first segment (anticipation), overshoot on
"back" eases, how far arms, lean and head go (exaggeration), an extra hold at the end of each action, and how long
the character takes to react to others (used by behaviour.Ensemble)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    name: str
    tempo: float = 1.0           # > 1 faster
    anticipation: float = 1.0    # scales the first segment of every action
    overshoot: float = 1.0       # scales the "back" ease overshoot
    exaggerate: float = 1.0      # scales how far arms, lean and head move from where the action began
    hold: float = 0.0            # extra seconds holding the final pose of an action
    reaction_delay: float = 0.3  # seconds before reacting to someone else
    pause: float = 0.4           # a dramatic pause between beats (for directors and planners)


PROFILES = {
    "explainer": Timing("explainer", 1.0, 1.0, 1.0, 1.0, 0.1, 0.3, 0.4),
    "comedy": Timing("comedy", 1.1, 1.35, 1.5, 1.25, 0.3, 0.45, 0.6),
    "satire": Timing("satire", 1.05, 1.15, 1.3, 1.2, 0.45, 0.6, 0.8),
    "drama": Timing("drama", 0.8, 1.2, 0.6, 0.9, 0.5, 0.7, 1.1),
    "action": Timing("action", 1.3, 0.8, 1.2, 1.15, 0.0, 0.15, 0.2),
}
