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


def test_critic_flags_staging_and_dead_air_and_fixes_what_it_can():
    from creatorforge_worker.animation import critic
    a = Actor(Look(name="A"), x=-1.0, facing=-1)            # facing away from B
    b = Actor(Look(name="B"), x=1.0, facing=-1)
    a.say_line(0.5, 2.5, "Listen to me!")
    R = qc.record(_scene([a, b]), 6.0)
    sc = SimpleNamespace(cams=[], width=1920, ppm=230)
    rv = critic.review(R, sc)
    cats = {n.category for n in rv.notes}
    assert "staging" in cats and "dead_air" in cats
    assert any(n.auto for n in rv.notes if n.category == "staging")
    assert all(not n.auto for n in rv.notes if n.category == "dead_air")   # judgement calls are left to a person
    done = critic.revise(sc, R, rv)
    assert any("turns to face" in d for d in done)


def test_comedy_structures_stage_cleanly_and_point_the_camera_at_the_reaction():
    from creatorforge_worker.animation import comedy as C
    from creatorforge_worker.animation import motions as M
    from creatorforge_worker.animation.timing import PROFILES
    sc = SimpleNamespace(actors=[], fps=30)
    a = Actor(Look(name="Raj"), x=-1.0, faceless=False)
    b = Actor(Look(name="Ivy"), x=1.2, facing=-1, faceless=False)
    for x in (a, b):
        x.timing = PROFILES["comedy"]
    t = C.double_take(a, 0.5, b, sc)
    t = C.slow_burn(b, t + 0.3, a, 2.4, sc)
    t = C.rule_of_three(a, t + 0.4, lambda x, tt: M.jump(x, tt, 0.4, 0.3), lambda x, tt: C.pratfall(x, tt, sc))
    t = C.button(b, t + 0.3, sc)
    sc.actors += [a, b]
    assert [x.name for x in a.acts].count("jump") == 2 and "trip_roll" in [x.name for x in a.acts]
    assert {n for _, _, ns in sc.focus for n in ns} == {"Raj", "Ivy"}
    rep = qc.inspect(qc.record(sc, t + 0.5))
    roll = [x for x in a.acts if x.name == "trip_roll"][0]
    # the only tolerated defect is the documented arm snap as the hands leave the floor mid-roll
    assert all(d.kind == "snap" and roll.t0 <= d.t0 <= roll.t1 for d in rep.defects)


def test_asset_library_generates_validates_and_refuses_broken_assets(tmp_path):
    from creatorforge_worker.animation import asset_lib as A
    lib = A.Library(tmp_path / "lib")
    car = A.generate("a small red car")
    assert car["kind"] == "car" and not A.errors(A.validate(car))
    assert A.compatible(car, "ride")[0] and not A.compatible(car, "carry")[0]
    assert A.compatible(A.generate("a dog"), "walk")[0] and A.compatible(A.generate("a chair"), "sit")[0]
    aid = lib.register(car)
    assert A.Library(tmp_path / "lib").get(aid)["name"] == "a small red car"      # persisted and reloaded
    mesh = A.to_mesh(car)
    assert mesh["open_edges"] == 0 and len(mesh["faces"]) > 20
    bad = A._asset("car", "bad", [A.poly("bow", [(0, 0), (1, 1), (1, 0), (0, 1)], (200, 0, 0)),
                                  A.circle("w", 0.8, 0.3, 0.3, (0, 0, 0), rig={"type": "spin", "pivot": [0.9, 0.3]})], 2, 1)
    found = {i.check for i in A.validate(bad)}
    assert {"self_intersection", "wobble"} <= found
    try:
        lib.register(bad)
        raise AssertionError("a broken asset was registered")
    except ValueError:
        pass
    assert lib.obtain("a flying saucer")[1] == "placeholder"                        # never invents a shape


def test_wheels_roll_without_skidding_and_legs_stop_when_the_animal_stops():
    from creatorforge_worker.animation import asset_lib as A
    car = A.generate("car")
    wheel = next(p for p in car["parts"] if p["id"] == "wheel_f")
    ang, _ = A.rig_angle(wheel, 0.0, 1.0, 2.0)
    assert abs(abs(ang) * wheel["r"] - 1.0) < 1e-6                                 # arc length == distance
    leg = next(p for p in A.generate("dog")["parts"] if p.get("rig", {}).get("gait"))
    assert abs(A.rig_angle(leg, 1.0, 0.37, 0.0)[0]) < 1e-9                          # standing still: legs at rest
    assert abs(A.rig_angle(leg, 1.0, 0.37, 1.0)[0]) > 0.05


def test_editor_undo_redo_and_versions(tmp_path):
    from creatorforge_worker.animation.production import Editor
    doc = {"title": "t", "scenes": [{"id": "a", "cast": [{"name": "Raj"}], "props": [{"name": "box", "kind": "crate"}],
                                     "steps": [{"t": 0.2, "who": "Raj", "do": "walk", "to": 1.0}]}]}
    ed = Editor(doc, tmp_path / "hist")
    ed.update_step("a", 0, to=2.0).set_expression("a", "Raj", 1.0, "happy").replace_asset("a", "box", "chair")
    v1 = ed.save_version("first pass")
    ed.add_scene({"id": "b", "cast": [], "props": [], "steps": []}).move_scene("b", 0)
    assert [s["id"] for s in ed.doc["scenes"]] == ["b", "a"]
    assert ed.undo().startswith("move scene") and ed.undo().startswith("add scene")
    assert [s["id"] for s in ed.doc["scenes"]] == ["a"]
    assert ed.redo().startswith("add scene") and len(ed.doc["scenes"]) == 2
    ed.restore(v1)
    assert len(ed.doc["scenes"]) == 1 and ed.doc["scenes"][0]["steps"][0]["to"] == 2.0
    assert ed.doc["scenes"][0]["props"][0]["asset"] == "chair"
    assert ed.versions()[0]["message"] == "first pass"
    assert ed.undo().startswith("restore") and len(ed.doc["scenes"]) == 2


def test_scenes_carry_world_state_and_unchanged_scenes_are_not_rendered_twice(tmp_path):
    from creatorforge_worker.animation import production as P
    doc = {"title": "t", "scenes": [
        {"id": "s1", "cast": [{"name": "Asha", "x": 0.0}], "props": [{"name": "parcel", "kind": "crate", "x": 1.0}],
         "steps": [{"t": 0.2, "who": "Asha", "do": "walk", "to": 0.6}, {"t": "+0.1", "who": "Asha", "do": "pick_up",
                                                                         "what": "parcel"}]},
        {"id": "s2", "cut": False, "cast": [{"name": "Asha"}], "props": [{"name": "car", "asset": "a blue car", "x": -3}],
         "steps": [{"t": 0.2, "do": "move", "what": "car", "to": 3.0, "speed": 4.0},
                   {"t": "+0.1", "who": "Asha", "do": "put_down", "what": "parcel"}]}]}
    states = P.plan_states(doc)
    end1, (start2, end2) = states[0][1], states[1][:2]
    assert end1.entities["parcel"].held_by == "Asha" and start2.entities["parcel"].held_by == "Asha"
    assert abs(start2.entities["Asha"].x - end1.entities["Asha"].x) < 0.05          # she starts where she stopped
    assert not states[1][4]                                                          # no continuity issues
    assert end2.entities["parcel"].held_by == "" and end2.entities["car"].x == 3.0
    r = P.render(doc, tmp_path / "t.mp4", "preview")
    assert r["video"]["missing"] == 0 and not any(s["cached"] for s in r["scenes"])
    r = P.render(doc, tmp_path / "t.mp4", "preview")
    assert all(s["cached"] for s in r["scenes"]) and r["render_seconds"] < 1.0


def test_a_ball_thrown_back_and_forth_never_snaps_back_into_an_old_hold():
    from creatorforge_worker.animation import bench3d
    actors, props, w, total, before, after, fixes = bench3d.checked(24)
    assert before.clean, before.summary()            # three throws by one person, a bounce, a pick-up: no prop jumps
    ball = props[0]
    ash = [c for c in ball.carriers if c[2].look.name == "Ash"]
    assert all(c1 - c0 < 6.0 for c0, c1, _, _ in ash)


def test_an_unfamiliar_script_gets_its_cast_objects_and_places():
    from creatorforge_worker.animation import benchmarks as B, storyboard
    board = storyboard.plan(B.UNFAMILIAR, "The Pelican")
    roles = {n: c.role for n, c in board.cast.items()}
    assert roles == {"Tomas": "fisherman", "Pelican": "animal", "Girl": "girl"}
    assert board.domain == "story" and all(b.environment == "outdoors" for b in board.beats)
    verbs = [(a["who"], a["verb"], a["target"]) for b in board.beats for a in b.actions]
    assert ("Pelican", "steal", "Tomas") in verbs and ("Tomas", "chase", "Pelican") in verbs
    assert ("Pelican", "drop", "Girl") in verbs and ("Tomas", "give", "Girl") in verbs
    sc, T = storyboard.stage(board)
    how = {a["for"]: (a["kind"], a["how"]) for a in sc.asset_log}
    assert how["cheeky pelican"][0] == "bird" and how["boat"][0] == "boat"
    assert how["lighthouse"][1] == "placeholder"               # nothing in the library: labelled, not invented
    assert qc.inspect(qc.record(sc, T)).clean


def test_world_effects_crowds_and_transitions_render_to_exact_length(tmp_path):
    from creatorforge_worker.animation import production as P
    from creatorforge_worker.animation.benchmarks import REAL
    doc = {"title": "t", "scenes": [
        {"id": "a", "cast": [{"name": "Ana", "x": -2.0}, {"name": "Crowd", "crowd": 3, "x": 2.0, "facing": -1}],
         "props": [{"name": "lamp", "asset": "lamp", "x": 0.5}, {"name": "doc", "kind": "photo", "x": 1.0, "y": 0.4,
                                                                "w": 2.0, "h": 1.4,
                                                                "data": {"image": str(REAL / "voters_lists.png")}}],
         "layers": {"light": [[0, "dusk"], [1.5, "night"]], "weather": [[0.5, 4.0, "rain", 1.0]], "wind": 0.4},
         "outro": {"push_into": "doc", "dur": 1.2},
         "steps": [{"t": 0.2, "who": "Crowd", "do": "gesture", "name": "cover_face", "dur": 1.0},
                   {"t": "+0.1", "do": "caption", "text": "Rain at night.", "hold": True,
                    "voice": {"say": "Rain at night.", "lang": "en"}}]},
        {"id": "b", "transition": {"kind": "dissolve", "dur": 0.5}, "cast": [{"name": "Ana", "x": -1.0}],
         "layers": {"backdrop": {"image": str(REAL / "voters_lists.png"), "credit": "Real photo"}},
         "steps": [{"t": 0.2, "who": "Ana", "do": "walk", "to": 0.5}], "seconds": 3.0}]}
    st = P.plan_states(doc)
    sc, T, actors, live = P.stage_scene(doc["scenes"][0], st[0][6])
    assert sum(1 for n in actors if n.startswith("Crowd")) == 3 and sc.narration and sc.weather
    r = P.render(doc, tmp_path / "w.mp4", "preview")
    assert r["video"]["missing"] == 0 and r["delivery"]["sync_ok"] and r["delivery"]["aspect_ok"]
    assert r["subtitles"]["count"] == 1 and not r["subtitles"]["issues"]


def test_the_sound_mix_never_trips_on_rounding(tmp_path):
    from creatorforge_worker.animation import sound
    for k, secs in enumerate([5.4, 6.4, 6.399999, 12.7, 13.85, 17.04, 3.6]):   # lengths whose bed rounds up
        out = sound.mix([], secs, None, "outdoors", tmp_path / f"m{k}.wav")
        assert out.exists()


def test_illustrations_stay_in_their_scene_but_objects_persist():
    from creatorforge_worker.animation import production as P
    doc = {"title": "t", "scenes": [
        {"id": "a", "cast": [{"name": "Noor", "x": 0}], "props": [
            {"name": "worry", "kind": "sign", "x": 2, "y": 1, "w": 1.5, "h": 0.5, "label": "What if?"},
            {"name": "cup", "kind": "crate", "x": 1, "w": 0.2, "h": 0.2},
            {"name": "plan", "kind": "sign", "x": -2, "y": 1, "w": 1.5, "h": 0.5, "label": "Plan", "data": {"persist": True}}],
         "steps": [{"t": 0.2, "who": "Noor", "do": "gesture", "name": "think", "dur": 1}]},
        {"id": "b", "cut": False, "cast": [{"name": "Noor"}], "props": [],
         "steps": [{"t": 0.2, "who": "Noor", "do": "nod"}]}]}
    st = P.plan_states(doc)
    _, _, _, live = P.stage_scene(doc["scenes"][1], st[1][6])
    assert "cup" in live and "plan" in live and "worry" not in live


def test_a_failed_scene_does_not_sink_the_film_and_a_rerun_redoes_only_it(tmp_path):
    import pytest
    from creatorforge_worker.animation import production as P
    from creatorforge_worker.animation.benchmarks import REAL
    good = {"id": "a", "cast": [{"name": "A", "x": 0}], "props": [], "steps": [{"t": 0.2, "who": "A", "do": "nod"}],
            "seconds": 2.0}
    doc = {"title": "t", "scenes": [good, {"id": "b", "footage": str(tmp_path / "missing.mp4"), "dur": 2.0}]}
    with pytest.raises(P.RenderFailed) as e:
        P.render(doc, tmp_path / "f.mp4", "preview", cache_dir=tmp_path / "c")
    assert [f["scene"] for f in e.value.report["failures"]] == ["b"]
    assert not list((tmp_path / "c").glob("*.partial.mp4"))                  # no half file left as a cache hit
    doc["scenes"][1]["footage"] = str(REAL / "footage_portrait.mp4")
    r = P.render(doc, tmp_path / "f.mp4", "preview", cache_dir=tmp_path / "c")
    assert [s["cached"] for s in r["scenes"]] == [True, False] and r["video"]["missing"] == 0
    assert r["provenance"][0]["file"] == "footage_portrait.mp4" and r["provenance_issues"]     # rights not verified


def test_the_whole_story_is_planned_and_checked_before_rendering(tmp_path):
    import pytest
    from creatorforge_worker.animation import studio
    doc, notes = studio.make("Two friends, Amir and Bea, carry a heavy box up the stairs. Amir slips and drops it. "
                             "Bea laughs, then helps him pick it up. They sit on the bench, tired.")
    story = notes["story"]
    assert story["roles"][0] == "setup" and story["roles"][-1] == "resolution"
    assert story["roles"][story["intensity"].index(max(story["intensity"]))] == "climax"
    assert [s["arc"] for s in doc["scenes"]] == story["roles"]
    assert any(st["do"] == "wait" for st in doc["scenes"][-1]["steps"])           # the ending breathes
    with pytest.raises(ValueError, match="allegation"):                         # never acted out, never unsourced
        studio.film("The minister took bribes from a builder.", tmp_path / "x.mp4")
