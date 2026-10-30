"""A library of stick-figure moves, each built from the principles: anticipation before effort, physical timing
(airtime from gravity), squash on impact, overshoot on recovery, follow-through after.

Each function adds an action to an Actor at time t and returns when it ends. Distances are metres along the way
the actor faces; heights are above the ground where the move starts."""
from __future__ import annotations

import math

from .stick import Actor, G

TAU = 2 * math.pi


def _stand(a: Actor) -> float:
    return (a.l_thigh + a.l_shin) * 0.985 + a.ankle


def jump(a: Actor, t: float, dist: float = 1.2, height: float = 0.5, land: float = 0.0, style: str = "normal") -> float:
    """Crouch, spring, tuck at the apex, land on bent legs, recover with a little overshoot.
    land: height of the landing spot relative to here (onto a crate > 0, off a ledge < 0).
    The timings come from the physics: the push-off ends at exactly the speed the flight needs, the flight
    is one gravity arc, and the knees absorb the landing speed instead of stopping it dead."""
    H, y0 = a.H, _stand(a)
    up = max(0.15, height)
    crouch, take_off, touch = y0 - 0.17 * H, y0 + 0.02 * H, land + y0 - 0.01 * H
    t_up = math.sqrt(2 * up / G)
    t_down = math.sqrt(2 * max(0.05, take_off + up - touch) / G)
    t_push = min(0.3, max(0.12, 2 * (take_off - crouch) / (G * t_up)))       # constant push: v_end = 2d/T
    t_absorb = min(0.35, max(0.12, 3 * 0.15 * H / (G * t_down)))             # ease-out starts at 3d/T
    push_dx, absorb_dx = 0.12, 0.1
    fly = dist - push_dx - absorb_dx
    t1 = 0.24 + t_push
    t2 = t1 + t_up
    t3 = t2 + t_down
    t4 = t3 + t_absorb
    keys = [
        (0.24, dict(y=crouch, lean=0.42, head=0.15, au=-0.7, al=-0.45, bu=-0.6, bl=-0.35, squash=0.93,
                    feet="keep"), "inout"),                                             # anticipation
        (t1, dict(dx=push_dx, y=take_off, lean=0.18, head=-0.1, au=2.7, al=2.9, bu=2.5, bl=2.7, squash=1.07,
                  lu=-0.15, ll=-0.25, mu=-0.35, ml=-0.45, feet="keep"), "accel"),       # take-off: toes leave last
        (t2, dict(dx=push_dx + fly * t_up / (t_up + t_down), y=take_off + up, lean=0.25, head=0.0, au=1.3, al=1.6,
                  bu=1.1, bl=1.5, lu=1.35, ll=-0.15, mu=1.05, ml=-0.35, squash=1.0, feet=None, ballistic=True),
         "linear"),                                                                     # apex, knees tucked
        (t3, dict(dx=dist - absorb_dx, y=touch, lean=0.22, au=1.2, al=1.5, bu=1.0, bl=1.3, squash=1.0,
                  feet=((dist + 0.1 * H, land), (dist - 0.08 * H, land)), ballistic=True), "linear"),  # touch-down
        (t4, dict(dx=dist, y=land + y0 - 0.16 * H, lean=0.38, au=0.8, al=1.1, bu=0.6, bl=0.9, squash=0.9), "out"),
        # the knees take the landing
        (t4 + 0.38, dict(y=land + y0, lean=0.04, head=0.0, au=0.1, al=0.25, bu=0.06, bl=0.2, squash=1.0), "back"),
    ]
    return a.act(t, keys, "jump", dx=dist)


def climb(a: Actor, t: float, wall: float, top: float) -> float:
    """Onto a ledge `wall` metres ahead and `top` metres high. Chest-high: crouch, spring with the hands onto the
    edge, lock the arms, knee up, stand (a mantle). Above reach: jump, catch the edge, hang, pull up, then the
    same knee-up. The push-off speed carries into the rise, and the feet hang clear of the floor and the wall."""
    H, y0 = a.H, _stand(a)
    arms = a.l_up + a.l_fore - 0.02
    torso = a.l_torso * 0.86 * 0.95
    crouch, take_off = y0 - 0.14 * H, y0 + 0.02 * H
    support = top + arms - torso                          # hands on the edge, arms straight, hips by the edge
    hang = top - arms - torso                             # hanging from the edge by straight arms
    t_push = 0.22
    v = 2 * (take_off - crouch) / t_push                  # the speed the push ends with
    edge_n, edge_f = (wall + 0.04 * H, top), (wall + 0.1 * H, top)
    keys = [
        (0.22, dict(y=crouch, lean=0.3, au=-0.5, al=-0.3, bu=-0.4, bl=-0.3, feet="keep", squash=0.94), "inout"),
        (0.22 + t_push, dict(dx=wall - 0.3 * H, y=take_off, lean=0.12, head=-0.35, au=2.6, al=2.7, bu=2.5, bl=2.6,
                             feet="keep", squash=1.05), "accel"),                          # spring, arms up
    ]
    t_ = 0.22 + t_push
    if hang > take_off + 0.05:                            # out of reach: jump and catch it
        rise = hang - take_off
        t_ += min(0.6, max(0.2, 3 * rise / v))
        keys += [
            (t_, dict(dx=wall - 0.2 * H, y=hang, lean=-0.05, head=-0.45, hands=(edge_n, edge_f), lu=0.25, ll=-0.1,
                      mu=-0.1, ml=-0.3, feet=None, squash=1.02), "out"),                    # catch
            (t_ + 0.3, dict(y=hang - 0.03 * H, lean=0.02, lu=0.05, ll=-0.05, mu=0.15, ml=0.1, squash=1.0), "inout"),
            (t_ + 0.42, dict(y=hang - 0.025 * H, lean=0.06, head=-0.3), "inout"),           # the swing settles
            (t_ + 1.05, dict(dx=wall - 0.17 * H, y=support, lean=0.25, head=-0.1, lu=-0.15, ll=-0.55, mu=-0.35,
                             ml=-0.8), "inout"),                                           # pull up
        ]
        t_ += 1.05
    else:                                                 # a mantle: the spring carries straight onto the arms
        t_ += min(0.8, max(0.3, 3 * (support - take_off) / v))
        keys += [(t_, dict(dx=wall - 0.17 * H, y=support, lean=0.25, head=-0.1, hands=(edge_n, edge_f), lu=-0.15,
                           ll=-0.55, mu=-0.35, ml=-0.8, feet=None, squash=1.0), "out")]   # arms locked on the edge
    keys += [
        (t_ + 0.25, dict(dx=wall - 0.12 * H, y=support + 0.02 * H, lean=0.45, head=0.1, lu=1.9, ll=0.9, mu=-0.4,
                         ml=-0.9, feet=((wall + 0.09 * H, top), None)), "inout"),          # knee up, foot on the edge
        (t_ + 0.55, dict(dx=wall + 0.02 * H, y=top + y0 * 0.72, lean=0.55, head=0.25, hands=(None, None), au=0.6,
                         al=0.9, bu=0.4, bl=0.7, feet=("prev", (wall + 0.02 * H, top))), "inout"),  # feet on top
        (t_ + 0.9, dict(dx=wall + 0.06 * H, y=top + y0, lean=0.04, head=0.0, au=0.1, al=0.25, bu=0.06, bl=0.2),
         "back"),
    ]
    return a.act(t, keys, "climb", dx=wall + 0.06 * H)


def trip_roll(a: Actor, t: float, speed: float = 3.6) -> float:
    """Running, a foot catches: pitch forward, hands to the floor, a tucked forward roll, up on one knee, back
    on the feet. Through the roll the limbs turn WITH the body (absolute angle = angle-to-torso - lean), so
    nothing whips round on its own."""
    H, y0 = a.H, _stand(a)

    def body(lean, arm_n, arm_f, elbow, thigh_n, thigh_f, knee):
        """Limb angles given relative to the torso (0 = hanging along it, + = forward / tucked)."""
        return dict(lean=lean, au=arm_n - lean, al=arm_n + elbow - lean, bu=arm_f - lean, bl=arm_f + elbow - lean,
                    lu=thigh_n - lean, ll=thigh_n - knee - lean, mu=thigh_f - lean, ml=thigh_f - knee - lean)
    keys = [
        (0.1, dict(dx=0.3, head=-0.3, feet="keep", **body(0.7, 2.0, 1.8, -0.1, 0.0, 1.2, 0.4)), "linear"),
        # the catch: the toe is stuck, the arms fly forward
        (0.38, dict(dx=1.0, y=0.4 * H, head=0.2, feet=None, squash=0.9,
                    hands=((1.0 + 0.42 * H, 0.03), (1.0 + 0.36 * H, 0.03)), **body(1.45, 1.6, 1.6, 0.0, 0.1, 0.4, 0.5)),
         "in"),                                                                         # dive, palms on the floor
        (0.52, dict(dx=1.25, y=0.33 * H, head=1.1, squash=0.74,
                    **body(1.45 + 0.25 * TAU, 1.7, 1.5, 0.6, 2.2, 1.9, 2.5)), "linear"),  # over the shoulders, tucking
        (0.66, dict(dx=1.5, y=0.26 * H, head=1.1, squash=0.7, hands=(None, None),
                    **body(1.45 + 0.5 * TAU, 1.7, 1.5, 0.9, 2.4, 2.2, 2.6)), "linear"),  # a ball: chin in, knees hugged
        (0.92, dict(dx=1.95, y=0.3 * H, head=0.7, squash=0.82,
                    **body(0.5 + TAU, 1.6, 1.3, 0.6, 2.0, 1.2, 2.4)), "out"),            # rolling up
        (1.12, dict(dx=2.1, y=0.42 * H, head=0.1, squash=1.0, feet=((2.1 + 0.2 * H, 0), (2.1 - 0.12 * H, 0)),
                    **body(0.4 + TAU, 0.9, 1.6, 0.4, 1.4, 0.2, 1.4)), "out"),             # up on one knee
        (1.5, dict(dx=2.2, y=y0 - 0.05 * H, head=-0.2, au=0.9 - TAU, al=1.0 - TAU, bu=-0.4 - TAU, bl=0.1 - TAU, lean=0.05 + TAU),
         "back"),                                                                # up, arms out for balance
        (1.85, dict(head=0.25, au=0.1 - TAU, al=0.25 - TAU, bu=0.06 - TAU, bl=0.2 - TAU), "inout"),  # shake it off
        (2.05, dict(head=-0.2), "inout"),
        (2.2, dict(head=0.0), "inout"),
    ]
    return a.act(t, keys, "trip_roll", dx=2.2)


def knockback(a: Actor, t: float, push: float = 1.0) -> float:
    """Hit from the front: thrown back off the feet, lands sitting, scrambles up."""
    H, y0 = a.H, _stand(a)
    keys = [
        (0.08, dict(lean=-0.5, head=-0.5, au=1.6, al=1.8, bu=1.4, bl=1.6, feet="keep"), "snap"),
        (0.2, dict(dx=-0.25 * push, y=y0 + 0.05, lean=-0.8, head=-0.4, lu=0.5, ll=0.3, mu=0.7, ml=0.5, feet=None),
         "out"),
        (0.62, dict(dx=-1.0 * push, y=0.27 * H, lean=-0.45, head=0.3, au=-0.6, al=-0.9, bu=-0.5, bl=-0.8, lu=1.45,
                    ll=1.45, mu=1.5, ml=1.5, squash=0.9, ballistic=True), "linear"),       # lands sitting
        (1.4, dict(lean=-0.3, head=0.45, squash=1.0), "inout"),                            # dazed
        (1.75, dict(dx=-1.0 * push, y=0.4 * H, lean=0.6, head=0.1, au=0.6, al=0.4, bu=0.2, bl=0.2,
                    feet=((-1.0 * push + 0.24 * H, 0), (-1.0 * push + 0.08 * H, 0))), "inout"),   # feet tucked in
        (2.1, dict(dx=-1.0 * push + 0.15 * H, y=y0, lean=0.03, head=0.0, au=0.1, al=0.25, bu=0.06, bl=0.2), "back"),
    ]
    return a.act(t, keys, "knockback", dx=-1.0 * push + 0.15 * a.H)


def pick_up(a: Actor, t: float, prop, hand: str = "near", carry_until: float | None = None) -> float:
    """Bend from the hips with the knees, grab, lift with the legs (the object then rides in the hand)."""
    H, y0 = a.H, _stand(a)
    grip = lambda tt: prop.pos(tt)[0:1] + (prop.pos(tt)[1] + prop.h * 0.55,)   # noqa: E731
    keys = [
        (0.35, dict(y=y0 - 0.2 * H, lean=1.0, head=0.4, hands=(grip, grip), feet="keep"), "inout"),
        (0.55, dict(lean=1.05, head=0.5), "inout"),
        (0.95, dict(y=y0, lean=0.05, head=0.0, hands=(None, None), au=0.95, al=1.2, bu=0.85, bl=1.15), "out"),
    ]
    end = a.act(t, keys, "pick_up")
    prop.carriers.append((t + 0.55, carry_until or 1e9, a, hand))
    prop.data.setdefault("grip_dy", -prop.h * 0.55)
    a.loco.gesture(t + 0.95, "carry", (carry_until or end + 60) - t - 0.95)
    return end


def put_down(a: Actor, t: float, prop, at_dx: float = 0.35, on: float = 0.0) -> float:
    """Lower the object onto the ground (or a surface `on` high) in front, straighten up."""
    H, y0 = a.H, _stand(a)
    keys = [
        (0.45, dict(y=y0 - 0.16 * H + on * 0.5, lean=0.8, head=0.3, au=1.0, al=1.1, bu=0.9, bl=1.0, feet="keep"),
         "inout"),
        (0.85, dict(y=y0, lean=0.04, head=0.0, au=0.1, al=0.25, bu=0.06, bl=0.2), "back"),
    ]
    end = a.act(t, keys, "put_down")
    for i, c in enumerate(prop.carriers):
        if c[0] <= t + 0.45 <= c[1] and c[2] is a:
            prop.carriers[i] = (c[0], t + 0.45, a, c[3])
    a.loco.gestures = [(g0, min(g1, t), n) if n == "carry" else (g0, g1, n) for g0, g1, n in a.loco.gestures]
    return end, (t + 0.45)


def point_at(a: Actor, t: float, target, dur: float = 1.6, hand: str = "near") -> float:
    """Arm thrown out to the target (an x, y world point) with a snap, held, eased back."""
    hs = (target, None) if hand == "near" else (None, target)
    keys = [
        (0.12, dict(lean=-0.05, au=0.3, al=0.9, feet="keep"), "inout"),          # a little wind-up
        (0.3, dict(lean=0.08, head=0.1, hands=hs), "snap"),
        (0.3 + dur, dict(hands=hs), "linear"),
        (0.6 + dur, dict(lean=0.03, head=0.0, hands=(None, None), au=0.1, al=0.25, bu=0.06, bl=0.2), "inout"),
    ]
    return a.act(t, keys, "point")


def push(a: Actor, t: float, prop, dist: float, speed: float = 0.75) -> float:
    """Both hands on the object, lean in, walk it forward: the feet step for real (no sliding) and the object
    rides along at arm's length."""
    f = 1.0 if dist >= 0 else -1.0
    grab_n = lambda tt: (prop.pos(tt)[0] - f * prop.w * 0.5, prop.pos(tt)[1] + prop.h * 0.55)   # noqa: E731
    grab_f = lambda tt: (prop.pos(tt)[0] - f * prop.w * 0.5, prop.pos(tt)[1] + prop.h * 0.35)   # noqa: E731
    start = t + 0.35
    end = a.walk(start, a._end_x + dist, speed)
    prop.follows.append((start, end, a.loco, None))
    a.reach(t, end + 0.25, grab_n, grab_f)
    a.posture(t, end + 0.25, lean=0.55, crouch=0.05)
    return end + 0.35


def drag(a: Actor, t: float, prop, dist: float, speed: float = 0.8) -> float:
    """One hand on the object, walk it along beside you."""
    grab = lambda tt: (prop.pos(tt)[0], prop.pos(tt)[1] + prop.h * 0.6)          # noqa: E731
    start = t + 0.3
    end = a.walk(start, a._end_x + dist, speed)
    prop.follows.append((start, end, a.loco, None))
    a.reach(t, end + 0.25, grab, None)
    a.posture(t, end + 0.25, lean=0.2)
    return end + 0.35


def kick(a: Actor, t: float, power: float = 1.0) -> float:
    """Wind the leg back, snap it through, follow through high, set it down."""
    H, y0 = a.H, _stand(a)
    keys = [
        (0.28, dict(y=y0 - 0.04 * H, lean=-0.2, head=0.1, au=0.6, al=0.9, bu=-0.5, bl=-0.2, lu=-0.9, ll=-1.6,
                    feet=(None, "keep"), squash=0.97), "inout"),            # anticipation: leg cocked back
        (0.4, dict(lean=-0.35, lu=1.35 * power, ll=1.1 * power, au=-0.4, al=-0.2, bu=1.0, bl=1.3, squash=1.03),
         "snap"),                                                            # strike
        (0.62, dict(lean=-0.25, lu=1.5 * power, ll=1.4 * power), "out"),     # follow-through
        (0.95, dict(y=y0, lean=0.0, head=0.0, lu=0.05, ll=0.0, au=0.1, al=0.25, bu=0.06, bl=0.2, squash=1.0,
                    feet=((0.12 * H, 0), "keep")), "inout"),
    ]
    # the standing leg stays planted the whole time (only the near foot is planted for the kick)
    return a.act(t, keys, "kick")


def pain_hop(a: Actor, t: float, hops: int = 4, travel: float = -0.5) -> float:
    """Clutching a hurt foot: hop on the other leg, small bounces drifting backwards."""
    H, y0 = a.H, _stand(a)
    keys = []
    tt = 0.0
    for i in range(hops):
        dx = travel * (i + 1) / hops
        up = 0.11 * H
        keys.append((tt + 0.14, dict(dx=dx - travel / hops * 0.5, y=y0 + up, lean=0.35, head=0.35, lu=0.0, ll=0.1,
                                     mu=0.9, ml=-1.3, au=0.8, al=1.4, bu=0.5, bl=1.6, feet=None), "out"))
        keys.append((tt + 0.3, dict(dx=dx, y=y0 - 0.04 * H, feet=((dx + 0.02 * H, 0), (dx - 0.18 * H, 0.32 * H)),
                                    squash=0.95), "in"))
        tt += 0.3
    keys.append((tt + 0.4, dict(y=y0, lean=0.05, head=0.1, squash=1.0, au=0.1, al=0.25, bu=0.06, bl=0.2,
                                feet=((travel + 0.09 * H, 0), (travel - 0.08 * H, 0))), "back"))
    return a.act(t, keys, "pain_hop", dx=travel)


def tap(a: Actor, t: float, target) -> float:
    """A light poke at something."""
    keys = [(0.2, dict(lean=0.2, hands=(target, None), feet="keep"), "out"),
            (0.32, dict(lean=0.25), "snap"),
            (0.6, dict(lean=0.03, hands=(None, None), au=0.1, al=0.25), "inout")]
    return a.act(t, keys, "tap")
