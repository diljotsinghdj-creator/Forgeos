"""The stickman polish: gestures that show what the narration means, a camera that keeps a group in frame and
punches in on reactions, smears and squash-and-stretch on fast motion, and CreatorForge's signature line."""
import math

from PIL import Image, ImageDraw

from creatorforge_worker.animation import camera, cinematic, comedy as C, motions as M, qc
from creatorforge_worker.animation.performance import gestures_for
from creatorforge_worker.animation.rig2d import GESTURES, Look, _g
from creatorforge_worker.animation.scene2d import Scene
from creatorforge_worker.animation.stick import Actor


def test_gestures_land_on_the_words_that_carry_the_meaning():
    g = gestures_for("13.3 करोड़ वोटरों के नाम कटे। ज़िम्मेदार कौन?", 4.5)
    assert [x[1] for x in g] == ["wide", "fall"]                 # arms open on "crore", a dropping hand on "cut"
    assert gestures_for("Prices went up by 40 percent, but wages fell.", 4.5)[1][1] == "weigh"
    assert gestures_for("I never said that.", 2.0)[0][1] == "stop"
    assert gestures_for("Only three people knew.", 2.0)[0][1] == "small"
    assert gestures_for("Why does this matter?", 2.0)[0][1] == "shrug"
    assert gestures_for("The committee met on Tuesday.", 2.0)[0][1] in ("explain", "talk")
    # never the same gesture twice in a row, and every gesture exists in the rig
    assert gestures_for("Prices went up.", 2.0, last="rise")[0][1] != "rise"
    assert gestures_for("The meeting ended.", 2.0, last="explain")[0][1] == "talk"
    for name in ("wide", "small", "rise", "fall", "chest", "stop", "weigh", "count", "you"):
        assert name in GESTURES and _g(name, 0.5)[0] is not None
    # a long line gets a second beat, timed later in the line; a short line one
    g = gestures_for("We were told everything was fine, but the numbers fell sharply.", 5.0)
    assert len(g) == 2 and g[1][0] - g[0][0] >= 1.6


def _crowd(n=6, spread=1.6):
    sc = Scene(width=640, height=360, fps=24, ppm=260 / 3)      # the framing of a 1920x1080 stage, smaller
    actors = [Actor(Look(name=f"P{i}"), x=i * spread) for i in range(n)]
    sc.actors += actors
    for i, a in enumerate(actors):                             # a crowd marching together
        a.walk(0.0, a.hips_x(0.0) + 7.0)
    return sc, actors


def test_a_group_wider_than_the_widest_shot_is_kept_whole():
    sc, actors = _crowd()
    R = qc.record(sc, 4.0)                                       # while they march
    ppm = sc.ppm
    sc.cams = camera.direct(R, sc)
    assert sc.ppm < ppm                                          # the stage is drawn smaller...
    assert not qc.framing(sc, R)                                 # ...and nobody's head leaves the frame


def test_the_camera_punches_in_on_a_double_take():
    sc = Scene(width=640, height=360, fps=24, ppm=260 / 3)
    a, b = Actor(Look(name="Raj"), x=0.0), Actor(Look(name="Ivy"), x=2.0, facing=-1.0)
    sc.actors += [a, b]
    end = C.double_take(a, 0.5, b, sc=sc)
    R = qc.record(sc, end + 1.0)
    hits = camera.punches(R, sc)
    assert hits and abs(hits[0][0] - (0.5 + 1.45)) < 0.2 and R.actors[hits[0][1]] is a
    sc.cams = camera.direct(R, sc, style="comedy")
    t0 = hits[0][0]
    before = sc.camera(t0 - 0.2)[2]
    during = sc.camera(t0 + 0.5)[2]
    after = sc.camera(t0 + 2.5)[2]
    assert during > before * 1.15 and after < during              # snaps in on the reaction, then lets go


def test_fast_limbs_smear_and_flights_stretch():
    a = Actor(Look(name="Raj"))
    end = M.kick(a, 0.2, power=1.2)

    def S(x, y):
        return 200 + x * 120, 330 - y * 120
    smeared = 0
    for n in range(int((end + 0.2) * 24)):
        t = n / 24
        a.step(t, 1 / 24)
        img = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
        a._smears(ImageDraw.Draw(img, "RGBA"), S, a.joints(a.pose_now), t, (30, 30, 30), 4)
        smeared += img.convert("L").getextrema()[0] < 250
    assert smeared > 0                                           # the kick's fast shin leaves a smear
    b = Actor(Look(name="Ivy"))
    end = M.jump(b, 0.2, dist=1.2, height=0.6)
    sq = []
    for n in range(int(end * 60)):
        b.step(n / 60, 1 / 60)
        sq.append(b.pose_now.squash)
    assert max(sq) > 1.07 and min(sq) < 0.95                      # stretched rising, squashed landing


def test_the_signature_look_boils_on_twos_and_keeps_planted_feet_still():
    st = cinematic.get("signature")
    assert st.body == "stick" and st.boil > 0 and st.taper > 0 and st.paper > 0
    a = Actor(Look(name="Raj"))
    a.step(0.0, 1 / 24)
    J = a.joints(a.pose_now)
    j1, j2, j3 = a._boil(J, 0.00, 0.0035), a._boil(J, 0.04, 0.0035), a._boil(J, 0.09, 0.0035)
    assert j1["head"] == j2["head"] != j3["head"]               # re-drawn 12 times a second, not every frame
    for i in range(2):
        assert j3["legs"][i][2] == J["legs"][i][2]               # a standing foot never jitters
    assert max(abs(j3["head"][k] - J["head"][k]) for k in range(2)) < 0.01   # under a centimetre
    from creatorforge_worker.animation import studio
    doc, _ = studio.make("The minister announced a new tax. Traders protested outside parliament.")
    assert doc.get("style") == "signature"                       # the default stick look is the signature one
    doc, _ = studio.make("Raj walks to the bus stop. Raj waves.", style="signature")
    assert doc.get("style") == "signature"
    doc, _ = studio.make("Raj walks to the bus stop. Raj waves.", style="stick")
    assert doc.get("style") in (None, "stick")


def test_a_bus_stop_is_a_sign_and_scenery_never_covers_the_cast():
    from types import SimpleNamespace

    from creatorforge_worker.animation.stick import World
    from creatorforge_worker.animation.storyboard import _Stuff
    sc = Scene(width=640, height=360, fps=24)
    raj = Actor(Look(name="Raj"))
    sc.actors.append(raj)
    st = _Stuff(sc, World())
    st.place(SimpleNamespace(things=["bus stop"], narration="Raj runs to the bus stop."), 0.0, 0.0, {"Raj": raj})
    sign = st.things["bus stop"]
    assert sign.data["text"] == "BUS STOP" and "bus" not in st.things     # a sign with its name, not a bus
    assert sc.actors.index(sign) < sc.actors.index(raj)                 # drawn behind him
    st.place(SimpleNamespace(things=["the bus"], narration="The bus leaves without him."), 0.0, 0.0, {"Raj": raj})
    bus = st.things["bus"]
    assert abs(bus.pos(0.0)[0]) > 1.5 and sc.actors.index(bus) < sc.actors.index(raj)   # not parked on him
    doc, _ = __import__("creatorforge_worker.animation.studio", fromlist=["make"]).make(
        "Raj runs to the bus stop. Raj is shocked.", style="signature")
    assert all(c["faceless"] for sc_ in doc["scenes"] for c in sc_["cast"])  # signature stickmen act with the body
