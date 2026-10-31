"""The keyframe stick engine: bones never stretch, planted feet never skate, nothing passes through the floor,
jumps fly on real gravity, and handing an action back to walking never makes the body jump."""
import math

from creatorforge_worker.animation import motions as M
from creatorforge_worker.animation.stick import Actor, G, Prop
from creatorforge_worker.animation.stick_demos import demo1_cast


def _d(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _play(actors, seconds, who, fps=30):
    frames = []
    for i in range(int(seconds * fps)):
        t = i / fps
        for a in actors:
            a.step(t, 1 / fps)
        frames.append((t, who.joints(who.pose_now)))
    return frames


def _problems(a, frames):
    """Bone stretch, the worst planted-foot skid and the deepest dip under the floor."""
    stretch = skid = 0.0
    under = 0.0
    prev = None
    for _, J in frames:
        for sh, el, wr in J["arms"]:
            stretch = max(stretch, abs(_d(sh, el) - a.l_up), abs(_d(el, wr) - a.l_fore))
        for i, (hip, kn, ank, _) in enumerate(J["legs"]):
            stretch = max(stretch, abs(_d(hip, kn) - a.l_thigh), abs(_d(kn, ank) - a.l_shin))
            floor = a._floor(ank[0]) + a.ankle
            under = min(under, ank[1] - floor)
            if prev:
                p0 = prev["legs"][i][2]
                if abs(p0[1] - (a._floor(p0[0]) + a.ankle)) < 0.002 and abs(ank[1] - floor) < 0.002:
                    skid = max(skid, abs(ank[0] - p0[0]))
        hx, hy = J["head"]
        under = min(under, hy - a.r_head - a._floor(hx))
        prev = J
    return stretch, skid, under


def test_every_move_keeps_bones_whole_feet_planted_and_the_body_above_the_floor():
    a = Actor(x=0.0)
    t = a.walk(0.2, 3.0)
    t = M.jump(a, t + 0.2, dist=1.2, height=0.5)
    t = a.walk(t + 0.1, 6.0)
    box = Prop("crate", 7.0, 0.0, 0.5, 0.5)
    t = M.push(a, t + 0.2, box, 1.5)
    t = M.trip_roll(a, t + 0.2)
    t = M.knockback(a, t + 0.3)
    t = a.walk(t + 0.2, a._end_x + 1.5)
    stretch, skid, under = _problems(a, _play([a, box], t + 0.5, a))
    assert stretch < 1e-3                  # fixed-length bones: no rubber limbs, no broken joints
    assert skid < 0.012                    # a planted foot moves less than a centimetre a frame (landing impact)
    assert under > -1e-3                   # feet, hands and head stop at the floor


def test_demo1_course_platform_and_all():
    sc, hero, total = demo1_cast()
    stretch, skid, under = _problems(hero, _play(sc.actors, total, hero))
    assert stretch < 1e-3 and skid < 0.012 and under > -1e-3


def test_a_jump_is_ballistic_and_the_take_off_does_not_jerk():
    a = Actor(x=0.0)
    t0 = 0.2
    M.jump(a, t0, dist=1.2, height=0.5)
    frames = _play([a], t0 + 2.0, a, fps=60)
    hips = [J["hip"] for _, J in frames]
    apex = max(range(len(hips)), key=lambda i: hips[i][1])
    start_y = hips[int(t0 * 60)][1]
    assert 0.45 < hips[apex][1] - start_y < 0.62                 # crouch + 0.5 m of flight
    vel = [(hips[i + 1][1] - hips[i][1]) * 60 for i in range(len(hips) - 1)]
    assert max(abs(v) for v in vel) < 1.4 * math.sqrt(2 * G * 0.5)   # never faster than the flight needs
    acc = [(vel[i + 1] - vel[i]) * 60 for i in range(apex - 8, apex + 8)]
    assert all(-1.5 * G < g < -0.5 * G for g in acc)               # gravity at the top of the arc


def test_handing_back_to_walking_keeps_the_body_where_the_action_left_it():
    a = Actor(x=0.0)
    t = M.jump(a, 0.2, dist=1.0, height=0.4)
    a.walk(t + 0.05, 4.0)
    frames = _play([a], t + 3.0, a)
    jumps = [_d(frames[i][1]["hip"], frames[i + 1][1]["hip"]) for i in range(len(frames) - 1)]
    assert max(jumps) < 0.12                                       # no snap back to where the walk started


def test_limbs_turn_with_the_body_through_a_roll():
    a = Actor(x=0.0)
    t0 = 0.2
    end = M.trip_roll(a, t0)
    frames = _play([a], end + 0.3, a, fps=60)

    def rel(J, i):                          # thigh direction relative to the torso
        hip, kn = J["legs"][i][:2]
        th = math.atan2(kn[0] - hip[0], kn[1] - hip[1])
        tor = math.atan2(J["neck"][0] - hip[0], J["neck"][1] - hip[1])
        return (th - tor + math.pi) % (2 * math.pi) - math.pi
    worst = max(abs((rel(frames[k + 1][1], i) - rel(frames[k][1], i) + math.pi) % (2 * math.pi) - math.pi)
                for k in range(len(frames) - 1) for i in (0, 1))
    assert worst < 0.35                     # under 20 degrees a frame at 60 fps relative to the body: no whip


# ---- locomotion over terrain, sitting, crawling --------------------------------------------------------------
def _stairs_world():
    from creatorforge_worker.animation.stick import World
    w = World()
    w.stairs(0.0, 6, 0.17, 0.3)
    for i in range(6):
        w.platforms.append((3.0 + i * 0.3, 3.0 + (i + 1) * 0.3, 1.02 - 0.17 * (i + 1)))
    w.ramps.append((6.0, 9.0, 0.0, 0.6))
    return w


def test_stairs_and_slopes_one_stair_per_step_no_skid_no_jolt():
    w = _stairs_world()
    a = Actor(x=-2.0, world=w)
    t = a.walk(0.2, 8.5, 1.1)
    frames = _play([a], t + 0.5, a)
    stretch, skid, under = _problems(a, frames)
    assert stretch < 1e-3 and skid < 0.005 and under > -1e-3
    hips = [J["hip"] for _, J in frames]
    vy = [abs(hips[i + 1][1] - hips[i][1]) * 30 for i in range(len(hips) - 1)]
    assert max(vy) < 1.5                                # the body climbs and descends at a walking pace
    landings = []
    seen = set()
    b = Actor(x=-2.0, world=w)
    b.walk(0.2, 8.5, 1.1)
    for i in range(int(t * 30)):
        b.step(i / 30, 1 / 30)
        for ft in b.loco._feet:
            if ft.swing and ft.swing[0] not in seen:
                seen.add(ft.swing[0])
                landings.append((w.ground(ft.swing[2]), w.ground(ft.swing[3])))
    on_stairs = [abs(g1 - g0) for g0, g1 in landings if abs(g1 - g0) > 0.05 and g0 != g1 and (g0 * 100) % 17 < 1e-6]
    assert all(d < 0.36 for d in on_stairs)            # never more than one stair past where the foot left


def test_sitting_and_crawling_keep_contact():
    a = Actor(x=0.0)
    t = M.sit(a, 0.2, 0.45, 1.5)
    a.feel(1.5, 2.5, "laugh")                          # the upper body still reacts while seated
    t = a.walk(t + 0.2, 1.5)
    t = M.crawl(a, t + 0.3, 1.6)
    frames = _play([a], t + 0.5, a)
    stretch, skid, under = _problems(a, frames)
    assert stretch < 1e-3 and skid < 0.006 and under > -1e-3
    seated = [J for tt, J in frames if 1.4 < tt < 1.7]
    assert all(J["hip"][1] < 0.62 for J in seated)
    crawling = [J for tt, J in frames if t - 3.0 < tt < t - 1.6]
    assert all(min(l[1][1] for l in J["legs"]) < 0.06 for J in crawling)   # knees on the floor


# ---- behaviour, timing, physics -----------------------------------------------------------------------------
def test_characters_react_to_each_other_in_character():
    from creatorforge_worker.animation.behaviour import PERSONALITIES as P
    from creatorforge_worker.animation.behaviour import Ensemble
    from creatorforge_worker.animation.rig2d import Look
    red, blue = Actor(Look(name="Red"), x=0.0), Actor(Look(name="Blue"), x=1.2, facing=-1)
    green, kim = Actor(Look(name="Green"), x=-1.4), Actor(Look(name="Kim"), x=3.6, facing=-1)
    red.feel(1.0, 3.0, "angry")
    blue.feel(5.0, 7.0, "sad")
    log = Ensemble([red, blue, green, kim], {"Blue": P["timid"], "Green": P["bold"], "Kim": P["kind"]}).apply()
    said = {(r.who, r.trigger): r.response for r in log}
    assert said[("Blue", "angry")].startswith("steps back")
    assert said[("Green", "angry")] == "squares up"
    assert said[("Kim", "sad")] == "walks over and comforts"
    assert all(r.t > 1.0 for r in log if r.trigger == "angry")         # reactions come after a beat
    cast = [red, blue, green, kim]
    frames = {id(x): [] for x in cast}
    for i in range(int(9 * 30)):
        for x in cast:
            x.step(i / 30, 1 / 30)
        for x in cast:
            frames[id(x)].append((i / 30, x.joints(x.pose_now)))
    for x in cast:
        stretch, skid, under = _problems(x, frames[id(x)])
        hips = [J["hip"] for _, J in frames[id(x)]]
        assert stretch < 1e-3 and skid < 0.005 and under > -1e-3
        assert max(_d(hips[i], hips[i + 1]) for i in range(len(hips) - 1)) < 0.08   # no pops into reactions


def test_timing_profiles_change_the_same_action():
    from creatorforge_worker.animation.timing import PROFILES
    ends = {}
    for name in ("action", "explainer", "drama"):
        a = Actor(x=0.0)
        a.timing = PROFILES[name]
        ends[name] = M.kick(a, 0.0)
    assert ends["action"] < ends["explainer"] < ends["drama"]
    a = Actor(x=0.0)
    a.timing = PROFILES["comedy"]
    end = M.jump(a, 0.2, dist=1.0, height=0.5)
    frames = _play([a], end + 0.3, a, fps=60)
    hips = [J["hip"] for _, J in frames]
    apex = max(range(len(hips)), key=lambda i: hips[i][1])
    vel = [(hips[i + 1][1] - hips[i][1]) * 60 for i in range(len(hips) - 1)]
    acc = [(vel[i + 1] - vel[i]) * 60 for i in range(apex - 6, apex + 6)]
    assert all(-1.5 * G < g < -0.5 * G for g in acc)  # retimed, but the flight is still real gravity


def test_throw_and_catch_meet_in_the_hands():
    from creatorforge_worker.animation.rig2d import Look
    a, b = Actor(Look(name="A"), x=0.0), Actor(Look(name="B"), x=4.0, facing=-1)
    ball = Prop("ball", 0.5, 0.0, 0.22, 0.22)
    t = a.walk(0.2, 0.3, 0.8)
    t = M.pick_up(a, t + 0.1, ball)
    t_arr = M.throw(a, t + 0.4, ball, lambda tt: M.chest(b, tt), flight=0.9)
    M.catch(b, t_arr, ball, hold=1.0)
    gaps, path = [], []
    for i in range(int((t_arr + 0.8) * 60)):
        tt = i / 60
        for o in (a, b, ball):
            o.step(tt, 1 / 60)
        x, y, _ = ball.pos(tt)
        path.append((x, y))
        if t_arr <= tt <= t_arr + 0.5:
            gaps.append(_d(b.joints(b.pose_now)["arms"][0][2], (x, y + 0.11)))
    assert max(gaps) < 0.03                              # caught: the ball is in the hands
    assert max(_d(path[i], path[i + 1]) for i in range(len(path) - 1)) * 60 < 26   # no teleports (a throw ~20 m/s)


def test_a_dropped_object_bounces_lower_each_time_and_comes_to_rest():
    box = Prop("ball", 0.0, 1.5, 0.2, 0.2)
    box.launch(0.0, (1.0, 0.0))
    ys = [box.pos(i / 120)[1] for i in range(int(4 * 120))]
    peaks = [ys[i] for i in range(1, len(ys) - 1) if ys[i - 1] < ys[i] >= ys[i + 1] and ys[i] > 0.01]
    assert len(peaks) >= 2 and all(p2 < p1 for p1, p2 in zip(peaks, peaks[1:]))
    assert box.pos(3.9) == box.pos(3.95)                  # at rest
