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
