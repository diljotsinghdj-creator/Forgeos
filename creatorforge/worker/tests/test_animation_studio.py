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


# ---- world state and visual reasoning --------------------------------------------------------------------------------
def test_world_state_carries_what_is_held_and_catches_continuity_breaks():
    from creatorforge_worker.animation import motions as M
    from creatorforge_worker.animation import worldstate as W
    from creatorforge_worker.animation.stick import Prop
    ana = Actor(Look(name="Ana", body=(200, 60, 60)), x=-2.0)
    folder = Prop("folder", -1.4, 0.0, 0.3, 0.06, label="EVIDENCE")
    t = M.pick_up(ana, 0.2, folder)
    t = ana.walk(t + 0.1, 1.0, 1.1)
    ana.feel(t - 1, t + 1, "angry")
    for i in range(int((t + 0.5) * 30)):
        ana.step(i / 30, 1 / 30)
    end = W.capture([ana], [folder], t + 0.5, "shot1")
    assert end.entities["Ana"].holding == ["EVIDENCE"] and end.entities["EVIDENCE"].held_by == "Ana"
    actors, props = W.seed(end, [{"name": "Ana", "look": Look(name="Ana")}], [])
    a2, p2 = actors["Ana"], props["EVIDENCE"]
    for i in range(10):
        a2.step(i / 30, 1 / 30)
    start = W.capture([a2], [p2], 0.0, "shot2")
    assert W.check(end, start) == []                       # same place, same costume, still holding it, still angry
    assert start.entities["Ana"].feeling == "angry"
    b = Actor(Look(name="Ana", body=(40, 90, 200)), x=4.0, facing=-1)
    b.step(0.0, 1 / 30)
    kinds = {i.kind for i in W.check(end, W.capture([b], [], 0.0, "careless"))}
    assert {"look_changed", "position_jump", "held_object_lost"} <= kinds


def test_visual_reasoning_picks_honest_representations():
    from creatorforge_worker.animation import visual_reasoning as V
    assert V.reason("Prices of rice and milk went up sharply this year.").concept == "inflation"
    p = V.reason("The Prime Minister appoints two of the three members of the selection committee.")
    assert p.mode == V.DIAGRAM and p.elements[0]["nodes"][0][0] == "Prime Minister"
    assert V.reason("Riya feels anxious before the interview.").label == "Illustration"
    assert V.reason("Gravity pulls a ball and a feather down at the same rate in a vacuum.").mode == V.DEMO
    bare = V.reason("The minister is accused of taking bribes, according to the opposition.")
    assert bare.mode == V.EVIDENCE and not bare.sourced and bare.elements[0]["kind"] == "allegation_card"
    src = [{"claim": "The contract was awarded without a tender", "source": "CAG report 2024"}]
    doc = V.reason("The contract was awarded without a tender, critics allege.", src)
    assert doc.elements[0]["kind"] == "evidence_chain" and doc.elements[0]["steps"][0]["source"] == "CAG report 2024"
    assert V.reason("In 1947, India became independent.").label.startswith("Reconstruction")
    assert V.reason("Imagine if every pothole got its own minister.").label == "Satire"
    assert any("unsourced" in x for x in V.audit([V.reason("Inflation rose to 7% last year.")]))


def test_performance_director_coordinates_a_conversation():
    from creatorforge_worker.animation import performance as P
    from creatorforge_worker.animation.behaviour import PERSONALITIES as PE
    assert P.read_line("Ha ha, you are hopeless.")[0] == "laugh"
    assert P.read_line("Why would you do that?")[2] == "shrug"
    mia = Actor(Look(name="Mia"), x=-0.9, faceless=False)
    leo = Actor(Look(name="Leo"), x=0.9, facing=-1, faceless=False)
    lines = [{"who": "Mia", "text": "Leo! Where were you?"}, {"who": "Leo", "text": "I only went out for milk..."},
             {"who": "Mia", "text": "That was THREE DAYS ago!!", "emotion": "angry"},
             {"who": "Leo", "text": "Sorry. The queue was very long."}, {"who": "Mia", "text": "Ha ha, you are hopeless."}]
    end, log = P.perform(lines, {"Mia": mia, "Leo": leo}, {"Mia": PE["bold"], "Leo": PE["timid"]}, 0.5, "comedy")
    acts = [(d.who, d.what) for d in log]
    assert ("Leo", "reacts scared") in acts                       # the timid one flinches at the anger
    assert any(w == "Leo" and x == "nods" for w, x in acts)       # listening
    g = [x for w, x in acts if w == "Mia" and x.startswith("gesture")]
    assert all(a != b for a, b in zip(g, g[1:]))                  # never the same gesture twice running
    assert len(mia.bubbles) == 3 and len(leo.bubbles) == 2 and mia.loco.lines   # spoken, mouth moving
    assert qc.inspect(qc.record(_scene([mia, leo]), end + 1)).clean


def test_sounds_land_on_the_frames_where_things_happen(tmp_path):
    import wave as _wave

    from creatorforge_worker.animation import motions as M
    from creatorforge_worker.animation import sound
    from creatorforge_worker.animation.stick import Prop
    a, b = Actor(Look(name="A"), x=0.0), Actor(Look(name="B"), x=4.0, facing=-1)
    ball = Prop("ball", 0.5, 0.0, 0.22, 0.22)
    t = a.walk(0.2, 0.3, 0.8)
    t = M.pick_up(a, t + 0.1, ball)
    t_arr = M.throw(a, t + 0.4, ball, lambda tt: M.chest(b, tt), flight=0.9)
    M.catch(b, t_arr, ball, hold=3.0)                                # held through the jump: no drop
    M.jump(b, t_arr + 1.0, dist=0.6, height=0.4)
    R = qc.record(_scene([a, b, ball]), t_arr + 3.0)
    ev = sound.events(R)
    kinds = [e.kind for e in ev]
    assert kinds.count("whoosh") == 1 and kinds.count("catch") == 1 and kinds.count("land") == 1
    assert "clap" not in kinds and "bounce" not in kinds              # no false hits from carrying or hanging arms
    catch = next(e for e in ev if e.kind == "catch")
    assert abs(catch.t - t_arr) < 1 / 30 + 1e-6
    fs = [e for e in ev if e.kind == "footstep"]
    for e in fs:                                                      # every footstep: a foot really touched down
        i = [x.look.name for x in R.actors].index(e.who)
        n = round(e.t * R.fps)
        assert any(abs(R.joints[i][n]["legs"][k][2][1] - R.actors[i].ankle) < 0.004 for k in range(2))
    wav = sound.mix(ev, t_arr + 3.0, out=tmp_path / "m.wav")
    with _wave.open(str(wav)) as w:
        assert w.getnchannels() == 2 and w.getframerate() == 48000
