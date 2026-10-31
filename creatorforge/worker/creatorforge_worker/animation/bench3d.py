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


# ---- Film C: "The Ball on the Wall" (90 s) --------------------------------------------------------------------------
WALL = (5.4, 7.0, 1.4)                                 # x0, x1, top: a garden wall too high to reach
CRATE_X0 = 2.4
LAMP_X = -7.7                                          # a lamp post on the path, left of the bench


def film_c(fixes=None, rest_x: float | None = None):
    """A complete short story for the 3D stage, with shot marks for the camera.
    Setup: Kit walks in and sits on the bench to read; Ash and Ivy arrive and play catch.
    Rising: a throw lands on top of the garden wall; Ivy jumps twice and can't reach; she goes for a crate.
    Climax: Ash runs, jumps, hangs, pulls himself up the wall, gets the ball, celebrates - just as Ivy has pushed the
    crate into place (too late: she shrugs) - and jumps back down.
    Comic turn: Mo walks in from the other side reading his phone, straight into the lamp post. BONK.
    Resolution: everyone laughs; the ball goes Ash -> Mo -> Kit; they gather at the bench as the lamps come on."""
    w = World()
    w.platforms.append(WALL)
    ash = Actor(Look(name="Ash"), x=-12.5, facing=1, world=w, seed=1)
    ivy = Actor(Look(name="Ivy", height=1.68), x=-9.0, facing=1, world=w, seed=2)
    kit = Actor(Look(name="Kit", height=1.7), x=-14.0, facing=1, world=w, seed=3)
    mo = Actor(Look(name="Mo", height=1.8), x=-24.0, facing=1, world=w, seed=4)
    ball = Prop("ball", -1.7, 0.0, 0.22, 0.22, color=(240, 150, 40), data={"friction": 4.0})
    ball.name = "ball"
    crate = Prop("crate", CRATE_X0, 0.0, 0.6, 0.5, color=(196, 140, 72))
    crate.name = "crate"
    shots = []                                          # (t0, t1, kind, [subjects]) for the camera
    # setup -------------------------------------------------------------------------------------------------------------
    t_k = kit.walk(0.5, BENCH_X + 0.38, 0.9)
    shots.append((0.0, t_k + 1.0, "establish", ["Kit"]))
    sit_end = M.sit(kit, t_k + 0.1, 0.45, 200.0)
    kit.gesture(t_k + 1.5, "phone", 9.0)
    t_a = ash.walk(2.2, -2.2, 1.3)
    t_i = ivy.walk(3.0, 1.8, 1.4)
    ivy.turn(t_i + 0.05, -1)
    ash.gesture(t_a + 0.1, "wave", 1.3)
    ivy.gesture(t_i + 0.1, "wave", 1.3)
    ash.look_at(t_a, t_a + 2.0, ivy)
    ivy.look_at(t_i, t_i + 2.0, ash)
    t = M.pick_up(ash, max(t_a, t_i) + 1.0, ball)
    shots.append((t_k + 1.0, t, "two", ["Ash", "Ivy"]))
    play0 = t
    for k in range(3):
        arr = M.throw(ash, t + 0.3, ball, lambda tt: M.chest(ivy, tt), 0.85)
        M.catch(ivy, arr, ball, hold=0.7)
        if k == 1:
            ivy.gesture(arr + 0.75, "laugh", 1.0)
        arr = M.throw(ivy, arr + 0.75 + (0.9 if k == 1 else 0.0), ball, lambda tt: M.chest(ash, tt), 0.85)
        M.catch(ash, arr, ball, hold=0.8)
        t = arr + 0.8
    shots.append((play0, t, "two", ["Ash", "Ivy"]))
    # rising ------------------------------------------------------------------------------------------------------------
    long_t = t + 0.2
    ball.data["friction"] = 45.0                        # a high lob that lands dead on the wall top
    land = M.throw(ash, long_t, ball, (WALL[0] + 0.35, WALL[2] + 0.11), 1.6, bounce=0.1)
    ivy.look_at(long_t + 0.3, land + 2.0, ball)
    ivy.turn(land - 0.5, 1)
    ash.gesture(land + 0.1, "facepalm", 1.3)
    shots.append((long_t, land + 1.2, "follow", ["Ash", "Ivy", "ball"]))
    t = ivy.walk(land + 0.6, WALL[0] - 0.55, 1.2)
    for k in range(2):                                 # once, twice: can't reach
        t = M.jump(ivy, t + 0.25, 0.0, 0.38 + 0.08 * k)
        ivy.say_symbol(t - 0.3, t + 0.6, "!" if k == 0 else "?!")
    ivy.gesture(t + 0.1, "shrug", 1.2)
    ivy.look_at(t, t + 1.5, ash)
    shots.append((land + 1.2, t + 1.4, "medium", ["Ivy"]))
    # climax ------------------------------------------------------------------------------------------------------------
    t_i = t + 1.3
    ivy.turn(t_i, -1)
    t_i = ivy.walk(t_i + 0.2, CRATE_X0 - 0.75, 1.1)
    ivy.turn(t_i + 0.05, 1)
    ash.gesture(t_i - 1.0, "beckon", 1.0)
    t_r = ash.run(t_i - 0.2, WALL[0] - 0.95, 3.0)
    top_t = M.climb(ash, t_r + 0.3, 0.95, WALL[2])
    t_p = M.push(ivy, t_i + 0.5, crate, (WALL[0] - 0.45) - CRATE_X0 - 0.3, 0.55)
    shots.append((t_i - 1.2, top_t, "action", ["Ash", "Ivy"]))
    rest = rest_x if rest_x is not None else WALL[0] + 0.75   # measured from a first pass when available
    t_w = ash.walk(top_t + 0.3, rest - 0.38, 0.8)
    pick = M.pick_up(ash, t_w + 0.2, ball)
    ash.gesture(pick + 0.1, "cheer", 1.6)
    ash.say_symbol(pick + 0.2, pick + 1.4, "Got it!")
    ivy.look_at(t_p, pick + 3.0, ash)
    ivy.gesture(max(t_p + 0.2, pick + 0.4), "shrug", 1.3)
    ivy.say_symbol(max(t_p + 0.2, pick + 0.4), max(t_p + 0.2, pick + 0.4) + 1.0, "...")
    ash.turn(pick + 1.9, -1)
    edge = WALL[0] - 0.45
    down = M.jump(ash, pick + 2.3, ash.hips_x(pick + 2.2) - edge + 0.1, 0.25, land=-WALL[2])
    shots.append((top_t, down + 1.0, "low", ["Ash", "Ivy"]))
    # comic turn ----------------------------------------------------------------------------------------------------------
    t_m0 = down + 1.2
    t_m = mo.walk(t_m0 - 8.0, LAMP_X - 0.34, 1.1)      # he has been walking in all along, nose in his phone
    t_m = max(t_m, t_m0 + 1.8)
    mo.gesture(t_m0 - 7.9, "phone", t_m - t_m0 + 7.8)
    bonk = M.knockback(mo, t_m, 0.6)
    mo.say_symbol(t_m + 0.05, t_m + 1.0, "BONK")
    shots.append((t_m0, bonk + 0.6, "medium", ["Mo"]))
    walk_a = ash.walk(down + 0.6, -3.2, 1.3)
    walk_i = ivy.walk(t_p + 0.6 if t_p + 0.6 > down else down + 0.4, -1.9, 1.2)
    for a, d in ((ash, 0.2), (ivy, 0.35), (kit, 0.5)):
        a.look_at(t_m - 0.1, t_m + 3.0, mo)
        a.gesture(t_m + d + 0.3, "laugh", 2.0)
    kit.say_symbol(t_m + 0.6, t_m + 1.6, "Ha!")
    mo.gesture(bonk + 0.2, "scratch_head", 1.5)
    mo.gesture(bonk + 1.8, "laugh", 1.5)
    shots.append((bonk + 0.6, bonk + 3.4, "group", ["Mo", "Kit", "Ash", "Ivy"]))
    # resolution ----------------------------------------------------------------------------------------------------------
    t_g = max(walk_a, walk_i, bonk + 3.4)
    t_mo = mo.walk(bonk + 3.0, BENCH_X - 1.3, 1.0)
    arr = M.throw(ash, max(t_g, t_mo) + 0.4, ball, lambda tt: M.chest(mo, tt), 1.0)
    M.catch(mo, arr, ball, hold=1.0)
    arr2 = M.throw(mo, arr + 1.1, ball, lambda tt: M.chest(kit, tt), 0.8)
    M.catch(kit, arr2, ball, hold=6.0)
    kit.gesture(arr2 + 0.6, "cheer", 1.6)
    for a in (ash, ivy, mo):
        a.look_at(arr2 - 1.0, arr2 + 3.0, kit)
        a.gesture(arr2 + 1.8, "cheer", 1.6)
    shots.append((t_g, arr2 + 3.6, "group", ["Mo", "Kit", "Ash", "Ivy"]))
    total = arr2 + 15.0                                 # the light goes; hold on the group
    shots.append((arr2 + 3.6, total, "wide", ["Mo", "Kit", "Ash", "Ivy"]))
    actors = [ash, ivy, kit, mo]
    if fixes:
        from . import qc
        qc.apply(type("S", (), {"actors": actors})(), fixes)
    return actors, [ball, crate], w, total, {"sit_end": sit_end, "land": land, "top": top_t, "bonk": t_m,
                                             "shots": shots}


def film_c_checked(fps: int = 24):
    from types import SimpleNamespace

    from . import qc
    actors, props, w, total, marks = film_c()
    R = qc.record(SimpleNamespace(actors=actors + props, fps=fps), total)
    k = min(len(R.times) - 1, int(marks["top"] * fps))
    rest = R.props[0][k][0]                            # measure where the ball really came to rest on the wall...
    actors, props, w, total, marks = film_c(rest_x=rest)                 # ...and stage the pick-up there
    R = qc.record(SimpleNamespace(actors=actors + props, fps=fps), total)
    before = qc.inspect(R)
    fixes = qc.corrections(R, before)
    actors, props, w, total, marks = film_c(fixes, rest)
    after = qc.inspect(qc.record(SimpleNamespace(actors=actors + props, fps=fps), total))
    actors, props, w, total, marks = film_c(fixes, rest)
    marks["ball_rest_x"] = round(rest, 3)
    return actors, props, w, total, before, after, fixes, marks


def film_c_sound(out_wav, fps: int = 24):
    """Film C's soundtrack from the same staging the 3D film is posed from: footsteps, the ball (throws, catches,
    bounces), the jump and climb, Mo's BONK, outdoor ambience. No camera panning (the 3D camera is not modelled)."""
    from types import SimpleNamespace

    from . import qc, sound
    actors, props, w, total, before, after, fixes, marks = film_c_checked(fps)
    probe = SimpleNamespace(actors=actors + props, fps=fps)
    R = qc.record(probe, total)
    ev = sound.events(R, probe)                        # includes the knockback's bonk
    return sound.mix(ev, total, None, "outdoors", out_wav), total


def film_c_finish(video, out, fps: int = 24):
    """Adds Film C's soundtrack and its comic text (BONK, "Got it!", "Ha!") as captions at the right moments - the
    3D renderer does not draw text - then writes the master and an Android copy."""
    import subprocess
    from pathlib import Path
    out = Path(out)
    wav, total = film_c_sound(out.with_suffix(".wav"), fps)
    actors, *_ = film_c_checked(fps)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    texts = []
    for a in actors:
        for t0, t1, sym in a.symbols:
            label = f"{a.look.name}: {sym}" if sym not in ("BONK",) else "BONK!"
            safe = label.replace("'", "’").replace(":", "\\\\:").replace("!", "\\\\!")
            texts.append(f"drawtext=fontfile={font}:text='{safe}':fontsize=h/14:fontcolor=white:borderw=4:"
                         f"bordercolor=black@0.85:x=(w-text_w)/2:y=h*0.08:enable='between(t,{t0:.2f},{t1:.2f})'")
    vf = ",".join(texts) or "null"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(wav), "-filter_complex",
                    f"[0:v]{vf},format=yuv420p[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "16",
                    "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-shortest", "-movflags",
                    "+faststart", str(out)], check=True)
    android = out.with_name(out.stem + "_android.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-profile:v", "main", "-level",
                    "4.0", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", "-movflags", "+faststart",
                    str(android)], check=True)
    return out, android, len(texts)
