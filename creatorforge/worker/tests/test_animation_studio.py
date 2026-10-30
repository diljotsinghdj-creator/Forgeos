"""The studio layer: QC finds real defects and the loop corrects what it can, the camera keeps faces in frame, the
storyboard turns unfamiliar scripts into structured plans, and an interrupted render resumes identically."""
import json
from types import SimpleNamespace

from creatorforge_worker.animation import camera, qc, storyboard
from creatorforge_worker.animation.rig2d import Look
from creatorforge_worker.animation.stick import Actor


def _scene(actors, fps=30):
    return SimpleNamespace(actors=actors, fps=fps)


def test_qc_flags_a_body_passing_through_another_and_the_loop_fixes_it():
    a = Actor(Look(name="A"), x=-2.0)
    b = Actor(Look(name="B"), x=2.0, facing=-1)
    a.walk(0.2, 2.5, 1.2)                                   # walks straight through B
    R = qc.record(_scene([a, b]), 6.0)
    rep = qc.inspect(R)
    assert any(d.kind == "overlap" for d in rep.defects)
    fixes = qc.corrections(R, rep)
    assert fixes and fixes[0][0] == "A"                     # the one moving steps aside
    a2, b2 = Actor(Look(name="A"), x=-2.0), Actor(Look(name="B"), x=2.0, facing=-1)
    a2.walk(0.2, 2.5, 1.2)
    sc = _scene([a2, b2])
    qc.apply(sc, fixes)
    assert not any(d.kind == "overlap" for d in qc.inspect(qc.record(sc, 6.0)).defects)


def test_qc_catches_a_frozen_character_but_not_a_breathing_one():
    a = Actor(Look(name="Idle"), x=0.0)
    R = qc.record(_scene([a]), 8.0)
    assert not any(d.kind == "frozen" for d in qc.inspect(R).defects)   # standing still still breathes
    R.joints[0] = [R.joints[0][0]] * len(R.joints[0])                   # the same pose held for 8 s
    assert any(d.kind == "frozen" for d in qc.inspect(R).defects)


def test_camera_director_keeps_the_heads_in_the_safe_area():
    from creatorforge_worker.animation import scene2d
    a = Actor(Look(name="Runner"), x=-6.0)
    a.run(0.2, 8.0, 3.8)
    sc = scene2d.Scene(width=640, height=360, ppm=80)
    sc.actors.append(a)
    R = qc.record(sc, 6.0)
    sc2 = scene2d.Scene(width=640, height=360, ppm=80)
    sc2.cams = camera.direct(R, sc2, style="action")
    assert not qc.framing(sc2, R)


def test_storyboard_reads_unfamiliar_scripts_into_structured_plans():
    b = storyboard.plan("Maya is nervous before her exam. Her friend Sam reminds her to breathe slowly. "
                        "Maya takes a deep breath and feels calmer.")
    d = json.loads(b.to_json())
    assert d["domain"] == "psychology" and len(d["beats"]) == 3
    assert {"Maya", "Sam"} <= set(b.cast)
    assert d["beats"][1]["actions"][0]["who"] == "Sam"
    assert "breathe" in [a["verb"] for a in d["beats"][2]["actions"]]
    h = storyboard.plan("In 1930, Gandhi led the Salt March to Dandi. Thousands of people walked with him for 24 days.")
    assert not h.cast["Gandhi"].face and "illustration" in h.cast["Gandhi"].label     # real person: no drawn face
    assert any("24 days" in f for bt in h.beats for f in bt.figures)                   # numbers flagged as the script's
    s = storyboard.plan("A student drops a ball and a feather inside a vacuum tube. With no air, both fall at the same rate.")
    verbs = [a["verb"] for bt in s.beats for a in bt.actions]
    assert "equal_fall" in verbs and "trip" not in verbs
    sc, T = storyboard.stage(s)
    assert T > 5 and qc.inspect(qc.record(sc, T)).clean


def test_an_interrupted_render_resumes_to_the_same_video(tmp_path):
    from creatorforge_worker.animation import scene2d
    from creatorforge_worker.animation.scene2d import _frames

    def build():
        sc = scene2d.Scene(width=320, height=180, ppm=45, fps=24)
        a = Actor(x=-2.0)
        a.run(0.1, 2.0, 3.0)
        sc.actors.append(a)
        return sc
    build().render(tmp_path / "v.mp4", 2.0, chunk=0.5)
    first = (tmp_path / "v.mp4").read_bytes()
    parts = sorted((tmp_path / "v_parts").glob("part_*.mp4"))
    parts[2].unlink()                                       # as if the render had died there
    build().render(tmp_path / "v.mp4", 2.0, chunk=0.5)
    assert _frames(tmp_path / "v.mp4") == 48
    assert (tmp_path / "v.mp4").read_bytes() == first
