"""Stress-test scenes (A-G). Each builder stages a fresh scene and returns it with its length, so the QC loop
(qc.refine) can record, inspect, correct and re-stage it before anything is rendered."""
from __future__ import annotations

from . import motions as M
from . import rig2d
from .behaviour import PERSONALITIES, Ensemble
from .stick import Actor, World


# ---- Test F (3D): the performance; blender3d.demo_f films it ----------------------------------------------------------
CRATE_X, BENCH_X = 6.0, 9.6


def testf_world() -> World:
    w = World()
    w.stairs(-1.5, 5, 0.17, 0.3, landing=1.0)                 # up from x=-1.5 to a landing 0.85 m high
    for i in range(5):                                       # and down the far side
        a0 = 1.0 + i * 0.3
        w.platforms.append((a0, a0 + 0.3, 0.85 - 0.17 * (i + 1)))
    return w


def testf_cast(fixes=()):
    """Ash climbs the stairs, crosses the landing and comes down; Kit sprints in and vaults a crate; Ivy sits on a
    bench and laughs at the vault; the Ensemble adds the others' reactions."""
    w = testf_world()
    actors = [Actor(rig2d.Look(name=n, height=1.75), x=x, facing=f, world=w, seed=k)
              for k, (n, x, f) in enumerate((("Ash", -3.0, 1.0), ("Ivy", 12.0, -1.0), ("Kit", 2.9, 1.0)))]
    ash, ivy, kit = actors
    for a in actors:
        a.loco.express(0, "neutral")
    t = ash.walk(0.3, 2.2, 1.2)
    ash.loco.express(t - 1.0, "happy", 0.3)
    kit.look_at(0.0, t - 1.4, ash)                           # Kit watches Ash come down, then goes
    t_k = kit.run(t - 1.4, CRATE_X - 0.95, 3.6)
    t_k = M.jump(kit, t_k - 0.05, dist=1.75, height=0.55)
    kit.loco.express(t_k - 1.2, "excited", 0.2)
    kit.feel(t_k, t_k + 1.6, "excited")
    t_i = ivy.walk(0.5, BENCH_X - 0.36, 1.0)
    t_i = M.sit(ivy, t_i + 0.1, 0.46, max(2.0, t_k + 2.6 - t_i))
    ivy.loco.express(t_k + 0.2, "laughing", 0.2)
    ivy.feel(t_k + 0.3, t_k + 1.8, "laugh")
    ash.loco.express(t_k + 0.1, "surprised", 0.15)
    Ensemble(actors, {"Ash": PERSONALITIES["kind"], "Ivy": PERSONALITIES["cheerful"], "Kit": PERSONALITIES["bold"]},
             "comedy").apply()
    by = {a.look.name: a for a in actors}
    for name, t0, t1, dz in fixes:
        by[name].depth.append((t0, t1, dz))
    return actors, w, max(t_k + 3.0, t_i + 0.5)


def testf_checked(fps: int = 24):
    """Test F's cast after the QC loop: (actors, world, seconds, report before, report after, fixes)."""
    from types import SimpleNamespace

    from . import qc
    actors, w, total = testf_cast()
    sc = SimpleNamespace(actors=actors, fps=fps)              # QC needs no renderer
    R = qc.record(sc, total)
    before = qc.inspect(R)
    fixes = qc.corrections(R, before)
    actors, w, total = testf_cast(fixes)
    sc = SimpleNamespace(actors=actors, fps=fps)
    after = qc.inspect(qc.record(sc, total))
    actors, w, total = testf_cast(fixes)                     # fresh, for filming
    return actors, w, total, before, after, fixes


# ---- 2D stress tests A-E ----------------------------------------------------------------------------------------------
def _studio(tone=(246, 244, 238)):
    from . import scene2d
    sc = scene2d.Scene(ppm=230, ground=0.8, horizon=0.6)
    scene2d.studio(sc, paper=tone)
    return sc


def _label(sc, text, notes=()):
    from .stick_demos import _caption
    sc.overlay = _caption(text, list(notes))


def test_a():
    """Natural movement: walk, stop and look back, turn, climb stairs, cross, descend, run, jump a crate, land, walk to
    a bench, turn, sit, look around."""
    from .stick import Prop
    w = World()
    w.stairs(0.0, 5, 0.17, 0.3, landing=1.2)
    for i in range(5):
        a0 = 2.7 + i * 0.3
        w.platforms.append((a0, a0 + 0.3, 0.85 - 0.17 * (i + 1)))
    sc = _studio()
    steps = Prop("steps", 2.1, 0.0, 4.4, 0.85, data={"world": w})
    crate = Prop("crate", 7.2, 0.0, 0.5, 0.45)
    bench = Prop("bench", 11.0, 0.0, 0.5, 0.9, data={"seat": 0.45, "back": 1.0})   # side-on: its depth, not length
    sam = Actor(rig2d.Look(name="Sam", body=(40, 110, 200), line=1.0), x=-6.5, world=w, seed=3)
    sc.actors += [steps, crate, bench, sam]
    t = sam.walk(0.3, -3.0, 1.2)
    sam.turn(t + 0.3, -1)                                     # stops, looks back over the way he came
    sam.look_at(t + 0.4, t + 1.6, (-7.0, 1.0))
    sam.feel(t + 0.4, t + 1.6, "curious")
    sam.turn(t + 1.8, 1)
    t = sam.walk(t + 2.0, 4.7, 1.2)                           # up, across, down (one stair per step)
    t = sam.run(t + 0.1, 7.2 - 1.0, 3.6)
    t = M.jump(sam, t - 0.05, dist=1.95, height=0.55)
    t = sam.walk(t + 0.1, 11.0 - 0.38, 1.1)
    sam.turn(t + 0.2, -1)
    t = M.sit(sam, t + 0.4, 0.45, 3.2)
    sam.look_at(t - 3.6, t - 2.4, (8.0, 1.0))
    sam.look_at(t - 2.2, t - 1.0, (13.0, 2.2))
    sam.feel(t - 3.4, t - 1.0, "happy")
    _label(sc, "Test A - natural movement (2D stick engine)")
    return sc, t + 0.8


def test_b():
    """Emotional performance: surprise, confusion, anger, humour and reconciliation between two characters - faces,
    body language, reactions and timing."""
    from .timing import PROFILES
    sc = _studio((247, 240, 230))
    mia = Actor(rig2d.Look(name="Mia", body=(200, 70, 120), skin=(236, 196, 166), height=1.62, line=1.0), x=-0.9,
                faceless=False, seed=5)
    leo = Actor(rig2d.Look(name="Leo", body=(50, 120, 190), skin=(205, 155, 115), height=1.78, line=1.0), x=6.5,
                facing=-1, faceless=False, seed=8)
    for a in (mia, leo):
        a.timing = PROFILES["comedy"]
        a.loco.express(0, "neutral")
    sc.actors += [mia, leo]
    mia.loco.express(0.0, "bored")
    mia.loco.gesture(0.3, "phone", 3.2)
    t = leo.walk(0.6, 0.9, 1.1)
    mia.look_at(t - 1.2, t + 20, leo)
    leo.look_at(t - 0.4, t + 20, mia)
    mia.say_line(t - 0.8, t + 1.4, "Leo?! You're back!", "surprised")
    mia.feel(t - 0.8, t + 0.6, "surprised")
    mia.say_symbol(t - 0.8, t + 0.2, "!")
    leo.say_line(t + 1.7, t + 3.9, "Back? I only went out for milk...", "confused")
    leo.gesture(t + 1.9, "shrug", 1.6)
    mia.say_line(t + 4.2, t + 6.4, "That was THREE DAYS ago!", "angry")
    mia.feel(t + 4.2, t + 6.4, "angry")
    mia.gesture(t + 4.4, "shake_fist", 1.6)
    leo.say_line(t + 7.0, t + 9.2, "The queue was... very long.", "nervous")
    leo.gesture(t + 7.2, "scratch_head", 1.8)
    mia.loco.express(t + 9.3, "suspicious", 0.3)
    mia.say_symbol(t + 9.4, t + 10.3, "...")
    mia.loco.express(t + 10.4, "laughing", 0.2)
    mia.feel(t + 10.4, t + 12.2, "laugh")
    leo.say_line(t + 12.5, t + 14.4, "I did bring the milk.", "happy")
    leo.gesture(t + 12.6, "explain", 1.6)
    mia.say_line(t + 14.7, t + 16.5, "...Fine. Come here.", "happy")
    t_w = mia.walk(t + 15.3, 0.25, 0.8)
    mid = lambda tt: ((mia.hips_x(tt) + leo.hips_x(tt)) / 2, 1.55)   # noqa: E731 - a high five between them
    mia.reach(t_w + 0.2, t_w + 0.9, mid, None)
    leo.reach(t_w + 0.2, t_w + 0.9, mid, None)
    for a in (mia, leo):
        a.loco.express(t_w + 0.6, "joyful", 0.2)
        a.feel(t_w + 1.0, t_w + 2.6, "happy")
    Ensemble([mia, leo], {"Mia": PERSONALITIES["bold"], "Leo": PERSONALITIES["timid"]}, "comedy").apply()
    _label(sc, "Test B - emotional performance (faces, body language, reactions)")
    return sc, t_w + 3.0


def test_c():
    """Physical interaction: carry a box to a table and put it down, push a heavy crate, jump up onto it and down,
    throw and catch a ball, and a fumbled catch that bounces and rolls away."""
    from .stick import Prop
    w = World()
    w.platforms.append((3.05, 3.95, 0.8))                    # where the pushed crate ends up (it can be stood on)
    sc = _studio((240, 244, 246))
    table = Prop("table", -0.7, 0.0, 1.2, 0.75)
    box = Prop("crate", -4.2, 0.0, 0.42, 0.36, label="BOOKS")
    big = Prop("crate", 1.5, 0.0, 0.9, 0.8)
    ball = Prop("ball", 8.6, 0.0, 0.24, 0.24, color=(230, 90, 60), data={"friction": 3.0})
    ana = Actor(rig2d.Look(name="Ana", body=(200, 80, 60), line=1.0), x=-6.0, world=w, seed=1)
    ben = Actor(rig2d.Look(name="Ben", body=(60, 90, 170), line=1.0, height=1.85), x=0.2, world=w, seed=2)
    cy = Actor(rig2d.Look(name="Cy", body=(60, 150, 90), line=1.0), x=10.0, facing=-1, world=w, seed=3)
    sc.actors += [table, box, big, ball, ana, ben, cy]
    t = ana.walk(0.3, -4.55, 1.1)
    t = M.pick_up(ana, t + 0.1, box)
    t = ana.walk(t + 0.2, -1.25, 0.95)
    t_a = M.put_down(ana, t + 0.1, box, at_dx=0.55, on=0.75)
    ana.turn(t_a + 0.3, 1)
    t_b = M.push(ben, 0.6, big, 2.0, 0.6)
    t_b = ben.walk(t_b + 0.3, 1.2, 1.0)
    ben.turn(t_b + 0.2, 1)
    t = cy.walk(0.8, 8.9, 1.0)
    t = M.pick_up(cy, t + 0.1, ball)
    t = cy.walk(t + 0.2, 4.75, 1.2)
    t = max(t, t_b + 0.5)
    t = M.jump(cy, t + 0.1, dist=0.85, height=0.45, land=0.8)            # up onto the crate
    t = M.jump(cy, t + 0.4, dist=1.2, height=0.3, land=-0.8)             # and down the far side
    ana_hands = lambda tt: M.chest(ana, tt)                              # noqa: E731
    t_arr = M.throw(cy, t + 0.5, ball, ana_hands, flight=0.95)
    t_c = M.catch(ana, t_arr, ball, hold=1.2)
    ana.feel(t_c, t_c + 1.2, "happy")
    t_arr2 = M.throw(ana, t_c + 0.1, ball, lambda tt: (ben.hips_x(tt) + 0.7, 0.0), flight=1.1)   # Ben misses it
    ben.reach(t_arr2 - 0.5, t_arr2 + 0.2, lambda tt: (ben.hips_x(tt) + 0.55, 0.9), None)
    ben.feel(t_arr2 + 0.2, t_arr2 + 1.6, "embarrassed")
    Ensemble([ana, ben, cy], {"Ana": PERSONALITIES["cheerful"], "Cy": PERSONALITIES["cheerful"],
                              "Ben": PERSONALITIES["calm"]}, "comedy").apply()
    _label(sc, "Test C - physical interaction (carry, push, climb, throw, catch, bounce)")
    return sc, t_arr2 + 3.2


def test_d():
    """Cinematic action: a chase - vault, climb, a thrown ball that knocks the chaser down, a trip and roll, a kicked
    crate and a pain hop, and both end up laughing."""
    from .stick import Prop
    w = World()
    w.platforms.append((6.6, 10.0, 1.3))
    sc = _studio((236, 232, 224))
    sc.motion_blur = 3
    wall = Prop("crate", 8.3, 0.0, 3.4, 1.3)
    c1 = Prop("crate", -1.0, 0.0, 0.5, 0.45)
    c2 = Prop("crate", 4.6, 0.0, 0.6, 0.5)
    ball = Prop("ball", 8.0, 1.3, 0.24, 0.24, color=(250, 200, 40))
    zip_ = Actor(rig2d.Look(name="Zip", body=(240, 170, 20), line=1.0), x=-6.0, world=w, seed=4)
    rex = Actor(rig2d.Look(name="Rex", body=(205, 50, 45), line=1.1, height=1.85), x=-9.5, world=w, seed=6)
    sc.actors += [wall, c1, c2, ball, zip_, rex]
    t = zip_.run(0.2, -2.0, 4.2)
    t = M.jump(zip_, t - 0.05, dist=1.9, height=0.5)
    t = zip_.run(t, 6.1, 4.2)
    t = M.climb(zip_, t - 0.05, wall=0.5, top=1.3)
    t = zip_.walk(t + 0.1, 8.5, 1.2)
    zip_.turn(t + 0.1, -1)                                   # turn first: a held object would swap hands in 2D
    t = M.pick_up(zip_, t + 0.4, ball)
    tr = rex.run(1.0, -2.0, 4.4)
    tr = M.jump(rex, tr - 0.05, dist=1.9, height=0.5)
    tr = rex.run(tr, 2.6, 4.4)
    tr = M.trip_roll(rex, tr - 0.12)                       # ends near 4.8 - just short of the second crate
    rex.feel(tr, tr + 0.8, "frustrated")
    t_k = M.kick(rex, tr + 0.9)
    c2.move(t_k - 0.55, t_k - 0.4, c2.x + 0.04, 0.0)        # the crate doesn't budge (much)
    t_h = M.pain_hop(rex, t_k - 0.15, hops=4, travel=-0.6)
    t_throw = max(t + 0.4, t_h - 0.9)
    t_arr = M.throw(zip_, t_throw, ball, lambda tt: M.chest(rex, tt), flight=0.75)
    t_kb = M.knockback(rex, t_arr - 0.05, push=0.8)
    ball.launch(t_arr + 0.02, (-1.5, 2.2), world=w)        # it bounces off him
    zip_.feel(t_arr + 0.2, t_arr + 1.8, "laugh")
    zip_.gesture(t_arr + 0.2, "laugh", 1.6)
    rex.feel(t_kb + 0.1, t_kb + 1.8, "laugh")
    sc.shake += [(t_k - 0.3, t_k + 0.1, 6), (t_arr, t_arr + 0.35, 10)]
    Ensemble([zip_, rex], {"Zip": PERSONALITIES["cheerful"], "Rex": PERSONALITIES["bold"]}, "action").apply()
    _label(sc, "Test D - cinematic action (original choreography)")
    return sc, t_kb + 2.2


def test_e():
    """Political explainer with real material: a real headline (credited), the process as a flow diagram, the panel
    as a chart with its legal source, and a balance as a labelled visual metaphor."""
    from pathlib import Path

    from .stick import Prop
    real = Path(__file__).parent / "assets"
    sc = _studio((238, 236, 230))
    flow = Prop("diagram", 0.6, 2.05, 6.6, 0.62, data={
        "boxes": ["Search committee shortlists 5", "Selection committee picks 1", "President appoints"],
        "colors": [(90, 110, 140), (60, 120, 190), (200, 140, 40)], "reveal": [(0.0, 0.0, "linear")]})
    panel = Prop("chart", 6.6, 0.0, 2.7, 2.0, data={
        "title": "Selection committee (2023 Act)", "bars": [("Government", (200, 90, 50)), ("Opposition", (60, 110, 200))],
        "max": 3.0, "source": "Source: CEC & ECs Act 2023, s.7(1)"})
    scale = Prop("scale", 10.6, 0.0, 2.0, 1.45, label="Illustration", data={
        "left_label": "PM + Minister", "right_label": "Leader of Opp.", "left_n": 2, "right_n": 1,
        "left_color": (200, 90, 50), "right_color": (60, 110, 200), "tilt": [(0.0, 0.0, "linear")]})
    head = Prop("photo", 15.0, 0.3, 2.04, 2.4, data={"image": str(real / "scroll_headline.png"),
                                                    "credit": "Real screenshot: Scroll.in, Feb 2025",
                                                    "highlight": (0.24, 0.255, 0.77, 0.4)})
    guide = Actor(rig2d.Look(name="Guide", body=(235, 115, 30), line=1.0), x=-3.4, seed=6)
    sc.actors += [flow, panel, scale, head, guide]
    notes = []
    t = guide.walk(0.3, -2.4, 1.1)
    notes.append((0.6, 5.0, "In 2023 Parliament passed a new law on choosing the Chief Election Commissioner."))
    flow.data["reveal"] = [(1.2, 0.0, "linear"), (3.6, 1.0, "linear")]
    t = M.point_at(guide, t + 0.4, (-1.6, 2.3), 1.2)
    notes.append((t - 0.4, t + 3.2, "A search committee shortlists five names; the selection committee picks one."))
    t = M.point_at(guide, t + 0.2, (3.0, 2.3), 1.6)
    notes.append((t, t + 2.6, "The President then makes the appointment."))
    t = guide.walk(t + 0.6, 5.0, 1.2)
    panel.data["v0"] = [(t, 0.0, "linear"), (t + 0.9, 2.0, "back")]
    panel.data["v1"] = [(t + 0.4, 0.0, "linear"), (t + 1.3, 1.0, "back")]
    notes.append((t, t + 4.2, "On the committee: the PM, a Union Cabinet Minister and the Leader of the Opposition."))
    t = M.point_at(guide, t + 0.5, (6.6, 1.4), 2.6)
    t = guide.walk(t + 0.3, 9.0, 1.2)
    scale.data["tilt"] = [(t + 0.2, 0.0, "linear"), (t + 1.4, 0.32, "settle")]
    notes.append((t, t + 3.4, "So two of the three members come from the government."))
    guide.feel(t + 1.5, t + 3.2, "confused")
    t += 3.6
    notes.append((t, t + 4.6, "Critics, including the Opposition, say this gives the government the deciding say; "
                              "the government says Parliament set the process."))
    guide.gesture(t + 0.2, "explain", 2.0)
    guide.gesture(t + 2.4, "shrug", 1.6)
    t = guide.walk(t + 4.4, 13.4, 1.2)
    notes.append((t, t + 4.0, "In February 2025, Gyanesh Kumar was appointed CEC under this law."))
    t = M.point_at(guide, t + 0.4, (14.6, 1.85), 2.6)
    head.data["hl"] = [(t - 2.4, 0.0, "linear"), (t - 1.6, 1.0, "out")]
    _label(sc, "Test E - political explainer (animation; real items labelled; metaphor labelled)", notes)
    return sc, t + 1.0


TESTS = {"A": (test_a, "explainer"), "B": (test_b, "comedy"), "C": (test_c, "comedy"), "D": (test_d, "action"),
         "E": (test_e, "explainer")}


def run(which: str, out_dir, android: bool = True):
    """Stage -> QC (record, inspect, correct) -> direct the camera -> check framing -> render -> check the file.
    Writes <name>.mp4, <name>_android.mp4 and <name>_qc.json."""
    import json
    from pathlib import Path

    from . import qc
    build, style = TESTS[which]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    first, seconds = build()
    before = qc.inspect(qc.record(first, seconds))
    sc, seconds, after, framing, passes, fixes = qc.refine(build, style=style)
    name = f"Test{which}"
    out = out_dir / f"{name}.mp4"
    from . import sound
    wav = sound.soundtrack(build, fixes, sc, seconds, "studio", out_dir / f"{name}.wav")
    sc.render(out, seconds, android=out_dir / f"{name}_android.mp4" if android else None, audio_wav=wav)
    video = qc.check_video(out, seconds, sc.fps)
    report = dict(test=which, seconds=round(seconds, 2), style=style, motion_before=json.loads(before.to_json()),
                  corrections=fixes, motion_after=json.loads(after.to_json()),
                  framing_defects=[vars(d) for d in framing], camera_passes=passes, video=video)
    (out_dir / f"{name}_qc.json").write_text(json.dumps(report, indent=1, default=str))
    return out, report


if __name__ == "__main__":
    import sys
    o, r = run(sys.argv[1].upper(), sys.argv[2] if len(sys.argv) > 2 else ".")
    print(o, "motion:", r["motion_after"]["defects"] and len(r["motion_after"]["defects"]), "framing:",
          len(r["framing_defects"]), "video:", r["video"])
