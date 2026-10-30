"""Acceptance benchmark: a multi-character 3D scene. Four characters in a park, staged on the stick engine (so the
same physics, contact and QC apply) and filmed in Blender by blender3d.demo_g:

    Kit walks to a bench and sits down to watch. Ash picks up a ball and plays catch with Ivy; the third throw goes
    long, sails over Ivy's jump, lands and bounces on gravity and rolls to a stop. Mo, walking in from the far side,
    picks it up and throws it back; Ash catches it; Ash and Ivy cheer and Kit claps from the bench.

The ball is a real projectile (released from the hand, flies on g = 9.8, bounces losing energy, rolls to rest);
nobody else's hands touch it in between. Generated library assets (a car, a lamp post, trees) are extruded into
closed meshes for the set, so the asset pipeline is exercised in 3D too."""
from __future__ import annotations

from . import motions as M
from .rig2d import Look
from .stick import Actor, Prop, World

BENCH_X = -5.0


def cast(fixes=None):
    w = World()
    ash = Actor(Look(name="Ash"), x=-2.6, facing=1, world=w, seed=1)
    ivy = Actor(Look(name="Ivy", height=1.68), x=1.7, facing=-1, world=w, seed=2)
    kit = Actor(Look(name="Kit", height=1.7), x=-8.6, facing=1, world=w, seed=3)
    mo = Actor(Look(name="Mo", height=1.8), x=10.5, facing=-1, world=w, seed=4)
    ball = Prop("ball", -2.12, 0.0, 0.22, 0.22, color=(240, 150, 40), data={"friction": 4.0})
    ball.name = "ball"
    # Kit: to the bench, sit and watch
    t = kit.walk(0.3, BENCH_X + 0.38, 1.1)
    t_sit = t + 0.1
    sit_end = M.sit(kit, t_sit, 0.45, 13.0)
    # Ash and Ivy: catch, twice
    t = M.pick_up(ash, 0.6, ball, carry_until=None)
    arr = M.throw(ash, t + 0.3, ball, lambda tt: M.chest(ivy, tt), 0.85)
    M.catch(ivy, arr, ball, hold=0.7)
    arr = M.throw(ivy, arr + 0.75, ball, lambda tt: M.chest(ash, tt), 0.85)
    M.catch(ash, arr, ball, hold=0.7)
    # the long one: over Ivy's jump, lands behind her and bounces to rest
    long_t = arr + 0.8
    land = M.throw(ash, long_t, ball, (ivy.hips_x(long_t) + 3.2, 0.11), 1.25)
    M.jump(ivy, land - 0.75, 0.0, 0.32)
    ivy.look_at(long_t + 0.3, land + 2.5, ball)
    ivy.turn(land + 0.4, 1)
    ash.gesture(land + 0.2, "facepalm", 1.2)
    rest_t = land + 2.2
    bx = ball.pos(rest_t)[0]
    # Mo walks in, picks it up, throws it back to Ash
    t = mo.walk(land - 1.6, bx + 0.45, 1.3)
    t = M.pick_up(mo, max(t + 0.1, rest_t), ball)
    mo.gesture(t + 0.05, "wave", 1.0)
    arr = M.throw(mo, t + 1.1, ball, lambda tt: M.chest(ash, tt), 1.3)
    M.catch(ash, arr, ball, hold=1.6)
    ivy.turn(arr - 0.9, -1)
    for a, g in ((ash, "cheer"), (ivy, "cheer"), (kit, "clap")):
        a.gesture(arr + 0.4, g, 1.6)
    mo.gesture(arr + 0.6, "wave", 1.4)
    for a in (ash, ivy, mo):
        a.look_at(arr + 0.4, arr + 2.2, kit)
    total = min(arr + 2.6, sit_end)
    actors = [ash, ivy, kit, mo]
    if fixes:
        from . import qc
        qc.apply(type("S", (), {"actors": actors})(), fixes)
    return actors, [ball], w, total


def checked(fps: int = 24):
    """(actors, props, world, seconds, report before, report after, fixes) after the QC loop."""
    from types import SimpleNamespace

    from . import qc
    actors, props, w, total = cast()
    R = qc.record(SimpleNamespace(actors=actors + props, fps=fps), total)
    before = qc.inspect(R)
    fixes = qc.corrections(R, before)
    actors, props, w, total = cast(fixes)
    after = qc.inspect(qc.record(SimpleNamespace(actors=actors + props, fps=fps), total))
    actors, props, w, total = cast(fixes)
    return actors, props, w, total, before, after, fixes
