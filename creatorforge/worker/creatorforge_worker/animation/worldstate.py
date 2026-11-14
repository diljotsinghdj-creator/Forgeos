"""Persistent world state across a production.

Every scene starts from the state the last one ended in and hands its own end state on:

    state = WorldState()                                  # empty world
    actors, props = seed(state, cast_specs, prop_specs)   # characters stand where they were, hold what they held,
                                                          # face the way they faced, still feel what they felt
    ... direct and record the scene ...
    end = capture(recording)                              # who is where, holding what, feeling what, at the end
    issues = check(previous_end, start_of_next)           # continuity report

What is tracked per entity: position (x, ground height, depth lane), facing, posture (standing / sitting / lying),
what each character holds and who holds each prop, the current feeling, and the look (colours, height) so a
costume cannot change between shots. Continuity issues: a held object vanishing or changing hands off screen, a
character jumping position or flipping screen direction between consecutive shots without a cut reason, an
object appearing or disappearing, a look changing, and an emotion snapping (furious to laughing) with no beat."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .stick import Actor, Prop

OVERLAYS = {"sign", "scale", "chart", "diagram", "stat", "photo", "label", "cloud", "basket", "relations", "evidence",
            "folder"}
CALM = {"neutral", "happy", "confident", "curious", ""}
HOT = {"angry", "furious", "scared", "sad", "crying"}


@dataclass
class Entity:
    name: str
    kind: str                       # "actor" | "prop"
    x: float = 0.0
    y: float = 0.0
    z: float = 1.0
    facing: float = 1.0
    posture: str = "standing"
    holding: list = field(default_factory=list)
    held_by: str = ""
    feeling: str = ""
    look: dict = field(default_factory=dict)
    visible: bool = True


@dataclass
class WorldState:
    scene: str = ""
    t: float = 0.0
    entities: dict = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1)

    def actor(self, name: str) -> Entity | None:
        e = self.entities.get(name)
        return e if e and e.kind == "actor" else None


def _look(a: Actor) -> dict:
    L = a.look
    return {"body": list(L.body) if L.body else None, "height": round(L.height, 3), "faceless": a.faceless}


def _colours(v):
    """JSON gives colours as lists; drawing needs tuples. [r, g, b] (and [r, g, b, a]) of ints become tuples."""
    if isinstance(v, list):
        if 3 <= len(v) <= 4 and all(isinstance(c, int) and not isinstance(c, bool) and 0 <= c <= 255 for c in v):
            return tuple(v)
        return [_colours(x) for x in v]
    if isinstance(v, dict):
        return {k: _colours(x) for k, x in v.items()}
    return v


def _plain(data: dict) -> dict:
    """The JSON-safe part of a prop's data (what it looks like), so it can be rebuilt in the next scene."""
    out = {}
    for k, v in data.items():
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            continue
        out[k] = v
    return out


def capture(actors: list, props: list, t: float, scene: str = "") -> WorldState:
    """The state of everything at time t (after the scene has been played up to t)."""
    ws = WorldState(scene, t)
    for a in actors:
        act = a._current_act(t)
        posture = "sitting" if act is not None and act.name == "sit" and t - act.t0 > 0.95 else \
            "lying" if act is not None and act.name in ("trip_roll", "knockback") else "standing"
        feel = next((emo for f0, f1, emo in a.feels if f0 <= t <= f1), "")
        p = getattr(a, "pose_now", None)
        ws.entities[a.look.name] = Entity(a.look.name, "actor", round(a.hip[0], 3), round(a._floor(a.hip[0]), 3),
                                          a.z_at(t), (p.f if p else a.loco.facing), posture, [], "", feel, _look(a))
    for p in props:
        x, y, ang = p.pos(t)
        holder = next((c[2].look.name for c in p.carriers if c[0] <= t <= c[1] and hasattr(c[2], "look")), "")
        name = getattr(p, "name", None) or p.label or f"{p.kind}@{p.x:.1f}"
        ws.entities[name] = Entity(name, "prop", round(x, 3), round(y, 3), getattr(p, "z", 1.0), 1.0, "", [], holder,
                                   "", {"kind": p.kind, "w": p.w, "h": p.h, "color": list(p.color), "label": p.label,
                                    "data": _plain(p.data)})
        if holder and holder in ws.entities:
            ws.entities[holder].holding.append(name)
    return ws


def seed(state: WorldState, cast: list[dict], props: list[dict], world=None, carry: bool = False) -> tuple[dict, dict]:
    """Characters and props for a new scene, continuing from `state`. cast: [{name, look, x?, facing?}];
    props: [{name, kind, x, y, w, h}]. A character who ended the last scene somewhere starts there (unless the
    spec moves them, which then counts as a cut), keeps facing that way, keeps holding what they held and starts
    in the feeling they ended in. Returns ({name: Actor}, {name: Prop})."""
    actors, live = {}, {}
    for c in cast:
        prev = state.actor(c["name"])
        x = c.get("x", prev.x if prev else 0.0)
        f = c.get("facing", prev.facing if prev else 1.0)
        look = c["look"]
        if prev and prev.look:                          # same costume as last time
            if prev.look.get("body") and look.body is None:
                look.body = tuple(prev.look["body"])
        a = Actor(look, x=x, facing=f, faceless=c.get("faceless", prev.look.get("faceless", True) if prev else True),
                  world=world, seed=c.get("seed", len(actors)))
        if prev and prev.feeling and prev.feeling not in CALM:
            a.feel(0.0, c.get("carry_feeling", 1.2), prev.feeling)     # still feeling it as the shot opens
        actors[c["name"]] = a
    for p in props:
        live[p["name"]] = Prop(p.get("kind", "crate"), p.get("x", 0.0), p.get("y", 0.0), p.get("w", 0.4),
                               p.get("h", 0.3), z=p.get("z", 1.0), label=p.get("label", p["name"]),
                               color=tuple(p.get("color", (240, 200, 80))), data=_colours(dict(p.get("data", {}))))
        live[p["name"]].name = p["name"]                # identity across scenes (the label is what is drawn)
    if carry:                                          # a continuing shot: physical things stay where they were left
        for name, e in state.entities.items():         # (illustrations shown for one line do not follow you around)
            if e.kind == "prop" and e.look.get("kind") in OVERLAYS and not e.look.get("data", {}).get("persist"):
                continue
            if e.kind == "prop" and name not in live and not (e.held_by and e.held_by in actors):
                live[name] = Prop(e.look.get("kind", "crate"), e.x, e.y, e.look.get("w", 0.4), e.look.get("h", 0.3),
                                  z=e.z, label=e.look.get("label", name), color=tuple(e.look.get("color", (240, 200, 80))),
                                  data=_colours({k: v for k, v in e.look.get("data", {}).items() if k != "grip_dy"}))
                live[name].name = name
    for name, e in state.entities.items():             # things still in someone's hands come with them
        if e.kind != "prop" or not e.held_by or e.held_by not in actors:
            continue
        pr = live.get(name)
        if pr is None:
            pr = Prop(e.look.get("kind", "crate"), e.x, e.y, e.look.get("w", 0.4), e.look.get("h", 0.3), z=e.z,
                      label=e.look.get("label", name), color=tuple(e.look.get("color", (240, 200, 80))),
                      data=_colours(dict(e.look.get("data", {}))))
            pr.name = name
            live[name] = pr
        pr.carriers.append((0.0, 1e9, actors[e.held_by], "near"))
        pr.data.setdefault("grip_dy", -pr.h * 0.55)
        actors[e.held_by].loco.gesture(0.0, "carry", 1e6)
    return actors, live


@dataclass
class Issue:
    kind: str
    who: str
    detail: str
    severity: str = "error"           # "error" breaks continuity; "warn" is worth a look


def check(prev_end: WorldState, next_start: WorldState, cut: bool = False) -> list[Issue]:
    """Continuity between the end of one shot and the start of the next. cut=True means a deliberate cut to a new
    place or time (positions may change; objects in hands and looks still may not)."""
    out = []
    for name, a in prev_end.entities.items():
        b = next_start.entities.get(name)
        if a.kind == "prop":
            if a.held_by and (b is None or b.held_by != a.held_by):
                out.append(Issue("held_object_lost", name, f"held by {a.held_by} at the end of {prev_end.scene}, "
                                 f"{'missing' if b is None else 'held by ' + (b.held_by or 'nobody')} in "
                                 f"{next_start.scene}"))
            elif b is None and not cut:
                out.append(Issue("object_vanished", name, f"gone between {prev_end.scene} and {next_start.scene}",
                                 "warn"))
            continue
        if b is None:
            continue
        if a.look and b.look and a.look != b.look:
            out.append(Issue("look_changed", name, f"{a.look} -> {b.look}"))
        if not cut:
            if abs(a.x - b.x) > 0.5:
                out.append(Issue("position_jump", name, f"x {a.x:.2f} -> {b.x:.2f} with no cut"))
            if a.facing != b.facing:
                out.append(Issue("screen_direction", name, "faces the other way in the next shot", "warn"))
            if a.posture != b.posture:
                out.append(Issue("posture_jump", name, f"{a.posture} -> {b.posture}"))
        if a.feeling in HOT and b.feeling in ("happy", "laugh", "joyful") :
            out.append(Issue("emotion_snap", name, f"{a.feeling} -> {b.feeling} with no beat in between", "warn"))
    for name, b in next_start.entities.items():
        if b.kind == "prop" and name not in prev_end.entities and b.held_by:
            out.append(Issue("object_appeared_in_hand", name, f"{b.held_by} holds it with no pick-up", "warn"))
    return out
