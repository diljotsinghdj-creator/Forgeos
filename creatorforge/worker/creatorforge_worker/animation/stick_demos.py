"""Stick-figure action demos:  python -m creatorforge_worker.animation.stick_demos 1|2|3|4 out_dir

1 - fluid movement: walk, sprint, jump a crate, climb a wall, walk the top, jump down, trip, roll, recover, run on
2 - three faceless characters: confusion, anger, excitement and a laugh, told only with bodies
3 - political explainer: a parliamentary process with a folder, a diagram that gets rearranged, a chart
4 - real material: a stickman on a real news screenshot and photo, a statistic, then the documentary footage"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import ImageFont

from . import motions as M
from . import scene2d
from .rig2d import Look
from .stick import Actor, Prop, World

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _paper(sc, tone=(246, 244, 238)):
    scene2d.studio(sc, paper=tone)


def _caption(label: str, notes: list[tuple] = ()):
    def draw(d, W, H, t):
        f = ImageFont.truetype(BOLD, int(H * 0.026))
        a = int(255 * min(1.0, t / 0.5))
        d.rounded_rectangle([W * 0.02, H * 0.035, W * 0.02 + d.textlength(label, font=f) + H * 0.04, H * 0.035 + H * 0.055],
                            radius=H * 0.01, fill=(20, 20, 24, int(a * 0.75)))
        d.text((W * 0.02 + H * 0.02, H * 0.046), label, font=f, fill=(255, 255, 255, a))
        for t0, t1, text in notes:
            if t0 <= t <= t1:
                g = ImageFont.truetype(BOLD, int(H * 0.04))
                w = d.textlength(text, font=g)
                y = H * 0.87
                d.rounded_rectangle([W / 2 - w / 2 - H * 0.02, y - H * 0.012, W / 2 + w / 2 + H * 0.02, y + H * 0.056],
                                    radius=H * 0.012, fill=(10, 10, 14, 175))
                d.text((W / 2 - w / 2, y), text, font=g, fill=(255, 255, 255))
    return draw


def demo1(out: Path) -> Path:
    sc, hero, total = demo1_cast()
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"))


def demo1_cast():
    """Walk, run, jump a block, climb a wall, jump down, trip, roll, recover - staged, not rendered."""
    world = World()
    world.platforms.append((4.0, 6.5, 1.3))
    sc = scene2d.Scene(ppm=240, ground=0.8, horizon=0.6)
    _paper(sc)
    wall = Prop("crate", 5.25, 0.0, 2.5, 1.3, label="")
    block = Prop("crate", 0.3, 0.0, 0.5, 0.45)
    hero = Actor(Look(name="Dash", body=(235, 110, 30), line=1.0), x=-6.0, world=world, seed=1)
    sc.actors += [wall, block, hero]
    t = hero.walk(0.3, -3.6, 1.35)
    t = hero.run(t - 0.15, -0.65, 4.2)
    t = M.jump(hero, t - 0.05, dist=1.85, height=0.65)
    t = hero.run(t, 3.5, 3.6)
    t = M.climb(hero, t - 0.05, wall=0.5, top=1.3)
    hero.feel(t + 0.05, t + 1.1, "confident")
    t = hero.walk(t + 1.1, 6.15, 1.3)
    t = M.jump(hero, t, dist=1.5, height=0.4, land=-1.3)
    t = hero.run(t, 10.0, 4.0)
    t = M.trip_roll(hero, t - 0.12)
    hero.feel(t, t + 1.0, "embarrassed")
    t = hero.run(t + 1.0, 16.5, 4.0)
    total = t - 0.8
    sc.cams += [scene2d.CamKey(0.0, 1.2, 0, 1.0, follow=hero), scene2d.CamKey(total, 1.6, 0, 1.0, follow=hero)]
    sc.overlay = _caption("Demo 1 - fluid movement (2D rig, keyframes + physics)")
    return sc, hero, total


def demo2(out: Path) -> Path:
    """No words, no faces: Blue is puzzled by a box, Red loses his temper with it, Green just opens it."""
    sc = scene2d.Scene(ppm=300, ground=0.8, horizon=0.6)
    _paper(sc, (244, 241, 233))
    gift = Prop("gift", 0.0, 0.0, 0.7, 0.62, label="?")
    blue = Actor(Look(name="Blue", body=(45, 105, 205), line=1.0), x=-4.2, seed=2)
    red = Actor(Look(name="Red", body=(212, 48, 44), line=1.1, height=1.9), x=5.8, facing=-1, seed=5)
    green = Actor(Look(name="Green", body=(52, 165, 78), line=1.0, height=1.45, head=1.15), x=-7.5, seed=7)
    sc.actors += [gift, red, blue, green]
    # Blue: finds the box, curious, then puzzled
    t = blue.walk(0.2, -1.1, 1.25)
    blue.feel(t, t + 2.2, "curious")
    blue.say_symbol(t + 1.0, t + 4.2, "?")
    blue.feel(t + 2.2, t + 4.4, "confused")
    # Red: arrives sure of himself, shoves it, it won't budge, loses it, kicks it, hurts his foot
    t = red.walk(4.6, 1.05, 1.3)
    red.feel(t, t + 1.3, "confident")
    t += 1.3
    grab = lambda tt: (gift.pos(tt)[0] + 0.3, 0.42)                  # noqa: E731
    red.reach(t, t + 1.5, grab, (gift.pos(t)[0] + 0.3, 0.25))
    red.posture(t, t + 1.5, lean=0.6, crouch=0.07)
    gift.data["shake"] = [(t, 0, "linear"), (t + 0.3, 1, "linear"), (t + 1.3, 1, "linear"), (t + 1.5, 0, "linear")]
    t += 1.5
    red.feel(t, t + 1.0, "frustrated")
    red.say_symbol(t + 0.2, t + 2.2, "#@!")
    red.feel(t + 1.0, t + 1.8, "angry")
    t_kick = t + 1.8
    t = M.kick(red, t_kick, 1.0)
    gift.data["shake"] += [(t_kick + 0.35, 0, "linear"), (t_kick + 0.4, 1, "linear"), (t_kick + 0.7, 0, "linear")]
    t = M.pain_hop(red, t - 0.15, hops=5, travel=-0.6)
    blue.feel(t_kick + 0.4, t_kick + 1.0, "surprised")
    blue.feel(t_kick + 1.0, t_kick + 2.6, "laugh")
    blue.walk(t_kick + 2.6, -1.9, 0.9)                 # steps back, still giggling, to give the box room
    blue.turn(t_kick + 3.8, 1)
    # Green: bounds in, hops over Blue, pokes the box - which bursts open and flattens Red
    t_g = green.run(t_kick - 0.6, -3.1, 3.4)
    green.feel(t_g, t_g + 1.2, "excited")
    green.say_symbol(t_g + 0.2, t_g + 1.4, "!")
    t_g = M.jump(green, t_g + 1.25, dist=1.75, height=0.75)        # hops right over Blue
    t_g = green.walk(t_g + 0.1, -0.8, 1.0)
    t_tap = t_g + 0.2
    t_g = M.tap(green, t_tap, (gift.x - 0.3, 0.55))
    pop = t_tap + 0.3
    gift.data["pop"] = [(pop, 0, "linear"), (pop + 0.5, 1, "out")]
    red.say_symbol(pop + 0.05, pop + 0.9, "!")
    t_r = M.knockback(red, pop + 0.12, push=0.9)
    green.feel(pop + 0.2, pop + 2.4, "excited")
    blue.feel(pop + 0.3, pop + 3.6, "laugh")
    red.feel(t_r, t_r + 1.2, "embarrassed")
    end = t_r + 1.2
    for who in (red, blue, green):
        who.feel(end, end + 2.4, "laugh")
    total = end + 2.8
    sc.cams += [scene2d.CamKey(0, -0.8, 0, 1.0), scene2d.CamKey(5.0, 0.0, 0, 1.0), scene2d.CamKey(t_kick - 0.5, 0.6, -0.1, 1.2),
                scene2d.CamKey(t_kick + 2.5, 0.4, -0.1, 1.2), scene2d.CamKey(pop - 0.4, 0.0, 0, 1.0),
                scene2d.CamKey(total, 0.2, 0, 1.08)]
    sc.overlay = _caption("Demo 2 - body language only: no faces, no words")
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"))


def chamber(sc, span=(-12.0, 12.0)):
    """An original, generic parliamentary chamber (no real emblems): panelled wall, tiers of green benches curving
    round, a raised presiding officer's chair, a timber floor."""
    sc.sky = ((236, 226, 204), (226, 212, 186))

    def wall(d, w, h, left, scale, gy):
        d.rectangle([0, gy - 4.6 * scale, w, gy], fill=(150, 98, 62))
        x = 0.0
        while x < w:
            d.line([(x, gy - 4.6 * scale), (x, gy)], fill=(122, 78, 48), width=max(2, int(scale * 0.02)))
            x += 0.9 * scale
        d.rectangle([0, gy - 4.75 * scale, w, gy - 4.6 * scale], fill=(196, 160, 90))
        for tier in range(2, -1, -1):                   # back rows first; each row a bench on its own step
            base = gy - (0.5 + 0.62 * tier) * scale
            pts_top, pts_low = [], []
            xx = -0.5 * scale
            while xx < w + scale:
                wx = left + xx / scale
                y = base - 0.02 * wx * wx * scale
                pts_top.append((xx, y - 0.45 * scale))
                pts_low.append((xx, y))
                xx += 0.5 * scale
            d.polygon(pts_low + [(x, y + 0.62 * scale) for x, y in reversed(pts_low)], fill=(112, 72, 46))   # step
            d.polygon(pts_top + list(reversed(pts_low)), fill=(56, 120, 82))                                 # bench
            for x, y in pts_top[::2]:
                d.line([(x, y + 0.04 * scale), (x, y + 0.43 * scale)], fill=(40, 92, 62), width=max(2, int(scale * 0.02)))
            d.line(pts_top, fill=(84, 150, 108), width=max(2, int(scale * 0.03)))
        cx = (0.0 - left) * scale                       # presiding officer's chair
        d.rectangle([cx - 0.75 * scale, gy - 1.1 * scale, cx + 0.75 * scale, gy], fill=(110, 66, 40))
        d.rounded_rectangle([cx - 0.45 * scale, gy - 3.0 * scale, cx + 0.45 * scale, gy - 1.1 * scale],
                            radius=0.3 * scale, fill=(126, 30, 38), outline=(80, 20, 24), width=max(2, int(scale * 0.02)))
        d.rectangle([0, gy, w, h], fill=(176, 132, 88))
        x = 0.0
        while x < w:
            d.line([(x, gy), (x - 0.6 * scale, h)], fill=(160, 118, 76), width=max(2, int(scale * 0.012)))
            x += 0.7 * scale
    sc.layers.append(scene2d.Layer(1.0, wall, span))


def documents_wall(sc, span=(12.0, 30.0)):
    if not any(getattr(L, "_chamber", False) for L in sc.layers):
        sc.sky = ((52, 56, 66), (70, 74, 84))         # whatever the camera reveals above or below matches the set

    def wall(d, w, h, left, scale, gy):
        d.rectangle([0, 0, w, gy], fill=(52, 56, 66))
        d.rectangle([0, gy, w, h], fill=(70, 74, 84))
    sc.layers.append(scene2d.Layer(1.0, wall, span))


def demo3(out: Path) -> Path:
    from .. import animation as _pkg                                    # noqa: F401
    real = Path(__file__).parent / "assets"
    sc = scene2d.Scene(ppm=210, ground=0.84, horizon=0.6)
    chamber(sc)
    documents_wall(sc)
    table = Prop("table", 0.0, 0.0, 2.2, 0.85)
    folder = Prop("folder", -4.0, 0.0, 0.9, 0.62, label="ELECTION REFORM")
    order = ["Bill", "Lok Sabha", "Rajya Sabha", "President", "Act"]
    colors = [(90, 90, 110), (46, 125, 80), (176, 64, 72), (60, 100, 190), (200, 140, 30)]
    slots = [-2.4, -1.2, 0.0, 1.2, 2.4]
    start = [3, 4, 0, 1, 2]                     # where each box first lands: scrambled
    diagram = Prop("diagram", 0.0, 1.95, 6.0, 0.6, data={"boxes": order, "colors": colors})
    chart = Prop("chart", 9.0, 0.0, 2.6, 2.0, data={
        "title": "Who picks the Election Commissioners?", "bars": [("Govt. picks", (214, 80, 52)),
                                                                  ("Opposition", (52, 110, 200))],
        "max": 2.4, "source": "CEC & ECs (Appointment...) Act, 2023: PM, a Union Minister, Leader of Opposition"})
    ec = Prop("photo", 16.2, 0.55, 3.3, 2.18, data={"image": str(real / "ec_photo.png"),
                                                    "credit": "Real photo: Election Commission of India"})
    scroll = Prop("photo", 20.6, 0.4, 2.0, 2.36, data={"image": str(real / "scroll_headline.png"),
                                                       "credit": "Real screenshot: Scroll.in, Feb 2025",
                                                       "highlight": (0.24, 0.255, 0.77, 0.4)})
    blue = Actor(Look(name="Clerk", body=(45, 105, 205)), x=-7.5, seed=2)
    green = Actor(Look(name="MP", body=(52, 160, 78), height=1.7), x=7.0, facing=-1, seed=4)
    orange = Actor(Look(name="Guide", body=(235, 115, 30), height=1.8), x=7.2, facing=-1, seed=6)
    sc.actors += [table, ec, scroll, chart, folder, diagram, blue, green, orange]
    notes = []
    # the clerk carries the folder in and sets it on the table
    folder.carriers.append((0.0, 1e9, blue, "near"))
    folder.data.update(grip_dx=0.18, grip_dy=-0.45)
    blue.loco.gesture(0.0, "carry", 6.0)
    t = blue.walk(0.3, -1.25, 1.2)
    end, release = M.put_down(blue, t, folder)
    folder.move(release, release + 0.25, -0.35, 0.85)
    notes.append((0.6, 4.6, "A new bill on election reform arrives in Parliament."))
    # the MP opens it - out springs the process, in the wrong order
    t = green.walk(1.5, 1.2, 1.2)
    t = max(t, end + 0.2)
    M.tap(green, t, (-0.35, 1.2))
    folder.data["open"] = [(t + 0.3, 0.0, "linear"), (t + 0.8, 1.0, "back")]
    diagram.data["reveal"] = [(t + 0.8, 0.0, "linear"), (t + 1.8, 1.0, "out")]
    for i in range(5):
        diagram.data[f"bx{i}"] = [(0, slots[start[i]], "linear")]
    t += 1.9
    notes.append((t - 1.0, t + 2.6, "How does a bill become law?"))
    blue.turn(t, 1)
    blue.feel(t + 0.2, t + 2.8, "confused")
    blue.say_symbol(t + 0.4, t + 2.8, "?")
    green.feel(t + 0.4, t + 2.4, "frustrated")
    # the guide walks in and puts the steps in order, box by box
    t = orange.walk(t - 1.2, 3.0, 1.6)
    moves = [(0, 0), (1, 1), (2, 2)]              # box i to slot j (the rest follow)
    cur = {i: slots[start[i]] for i in range(5)}
    for i, j in moves:
        src, dst = cur[i], slots[j]
        others = [k for k in range(5) if k != i and abs(cur[k] - dst) < 0.01]
        t = orange.walk(t, src + 0.35, 1.7)
        grab = (lambda ii: (lambda tt: (diagram.pos(tt)[0] + diagram.value(f"bx{ii}", tt), 2.0)))(i)
        t_end = orange.walk(t + 0.3, dst + 0.35, 1.25)
        orange.reach(t, t_end + 0.25, grab, None)
        diagram.data[f"bx{i}"] += [(t + 0.35, src, "linear"), (t_end, dst, "inout")]
        for k in others:                          # the box in the way slides over to the free slot
            diagram.data[f"bx{k}"] += [(t + 0.35, cur[k], "linear"), (t_end, src, "inout")]
            cur[k] = src
        cur[i] = dst
        t = t_end + 0.15
    # the last two may still be swapped: settle them
    for k in range(5):
        if abs(cur[k] - slots[k]) > 0.01:
            diagram.data[f"bx{k}"] += [(t, cur[k], "linear"), (t + 0.6, slots[k], "inout")]
    t += 0.8
    t_sorted = t                                  # the caption states the order only once the boxes show it
    t = M.point_at(orange, t, (-2.4, 2.25), 2.6)
    notes.append((t_sorted - 0.2, t + 0.3, "Bill, then Lok Sabha, then Rajya Sabha, then the President's assent."))
    blue.feel(t - 1.2, t + 0.4, "happy")
    blue.turn(t - 1.4, 1)
    green.feel(t - 1.2, t + 0.4, "happy")
    # the camera turns to the real record
    t_doc = t + 0.4
    notes.append((t_doc + 0.6, t_doc + 5.4, "In 2023 a new law changed how Election Commissioners are chosen."))
    scroll.data["hl"] = [(t_doc + 3.0, 0.0, "linear"), (t_doc + 3.9, 1.0, "out")]
    t_back = t_doc + 6.2
    # back in the chamber, the guide pushes in the chart
    orange.turn(t_back - 2.8, 1)                  # off camera while we look at the record
    t_w = orange.walk(t_back - 2.8, 7.4, 1.5)
    orange.turn(t_w + 0.05, -1)
    t = M.push(orange, max(t_w + 0.4, t_back + 0.6), chart, -3.0, 0.8)
    chart.data["v0"] = [(t, 0.0, "linear"), (t + 0.9, 2.0, "back")]
    chart.data["v1"] = [(t + 0.5, 0.0, "linear"), (t + 1.4, 1.0, "back")]
    notes.append((t, t + 4.4, "The selection panel: two government picks, one from the Opposition."))
    blue.feel(t + 1.5, t + 3.2, "surprised")
    green.feel(t + 1.6, t + 4.0, "confused")
    t = M.point_at(orange, t + 1.6, (4.7, 1.2), 1.6)
    total = t + 1.2
    sc.cams += [scene2d.CamKey(0, -3.0, 0, 1.0), scene2d.CamKey(3.5, -1.0, 0, 1.0), scene2d.CamKey(t_doc - 3.0, 0.4, 0, 1.0),
                scene2d.CamKey(t_doc, 0.4, 0, 1.0), scene2d.CamKey(t_doc + 1.6, 16.2, 0.2, 1.12),
                scene2d.CamKey(t_doc + 2.8, 20.6, 0.15, 1.1), scene2d.CamKey(t_doc + 4.8, 20.6, -0.15, 1.6),
                scene2d.CamKey(t_back, 3.6, 0, 1.0), scene2d.CamKey(total, 4.2, 0, 1.0)]
    sc.overlay = _caption("Demo 3 - political explainer (animated illustration; real documents labelled)", notes)
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"))


def demo4(out: Path) -> Path:
    """A stickman on real material: points out a real headline, climbs onto the screenshot and walks across it,
    jumps to a real photo, a sourced statistic pops up, then he points to a screen and the film cuts into the
    real documentary footage."""
    real = Path(__file__).parent / "assets"
    work = out.parent / "work4"
    work.mkdir(parents=True, exist_ok=True)
    world = World()
    sc = scene2d.Scene(ppm=220, ground=0.8, horizon=0.62)
    documents_wall(sc, span=(-14.0, 18.0))
    scroll = Prop("photo", 0.0, 0.0, 2.04, 2.4, data={"image": str(real / "scroll_headline.png"),
                                                      "credit": "Real screenshot: Scroll.in, Feb 2025",
                                                      "highlight": (0.24, 0.255, 0.77, 0.4)})
    voters = Prop("photo", 3.4, 0.0, 3.0, 1.55, data={"image": str(real / "voters_lists.png"),
                                                     "credit": "Real photo: voters checking draft lists"})
    stat = Prop("stat", 6.9, 2.0, 2.7, 0.95, label="13.3 crore",
                data={"sub": "names cut from draft voter lists", "source": "As reported by Deccan Herald, Sep 2026"})
    screen = Prop("photo", 9.2, 0.62, 1.2, 1.29, data={"image": str(real / "footage_first.png"),
                                                      "credit": "Real footage"})
    stand = Prop("table", 9.2, 0.0, 0.5, 0.62)
    world.platforms += [(-1.02, 1.02, 2.4), (1.9, 4.9, 1.55)]
    guy = Actor(Look(name="Guide", body=(235, 115, 30)), x=-6.0, world=world, seed=3)
    sc.actors += [scroll, voters, stand, screen, stat, guy]
    notes = []
    t = guy.walk(0.2, -1.55, 1.3)
    guy.feel(t, t + 1.0, "curious")
    t = M.point_at(guy, t + 1.0, (-0.45, 1.6), 1.7)
    scroll.data["hl"] = [(t - 1.9, 0.0, "linear"), (t - 1.1, 1.0, "out")]
    notes.append((t - 2.2, t + 0.6, "A real headline - Scroll.in, February 2025"))
    t = M.climb(guy, t + 0.1, wall=0.53, top=2.4)
    t = guy.walk(t + 0.2, 0.68, 1.2)              # stops with both feet on the screenshot, not over its edge
    t = M.jump(guy, t, dist=1.64, height=0.35, land=-0.85)
    t = guy.walk(t + 0.1, 2.95, 1.1)
    stat.data["pop"] = [(t, 0.0, "linear"), (t + 0.5, 1.0, "linear")]
    notes.append((t, t + 3.4, "The statistic, with its source on screen"))
    guy.turn(t + 0.3, 1)
    t = M.point_at(guy, t + 0.4, (5.7, 2.6), 1.6)
    guy.feel(t, t + 1.2, "surprised")
    t = guy.walk(t + 1.2, 4.62, 1.1)
    t = M.jump(guy, t, dist=1.3, height=0.3, land=-1.55)
    t = guy.walk(t + 0.1, 7.9, 1.3)
    notes.append((t - 0.4, t + 2.4, "...and into the real documentary footage"))
    t = M.point_at(guy, t, (8.7, 1.3), 1.0)
    push_in = t - 0.6
    total = push_in + 2.2
    yc = 0.62 + 1.29 / 2
    cy_full = yc - (0.8 - 0.5) * 1080 / 220
    t_hl = scroll.data["hl"][0][0]
    sc.cams += [scene2d.CamKey(0.0, -3.0, 0.0, 1.0), scene2d.CamKey(t_hl - 1.4, -1.0, 0.25, 1.0),
                scene2d.CamKey(t_hl - 0.2, -0.55, 0.55, 1.5), scene2d.CamKey(t_hl + 2.2, -0.55, 0.55, 1.5),
                scene2d.CamKey(t_hl + 3.6, -0.2, 0.95, 1.0), scene2d.CamKey(t_hl + 7.0, 1.0, 1.2, 1.0),
                scene2d.CamKey(t_hl + 9.6, 4.2, 1.2, 1.0), scene2d.CamKey(t_hl + 13.5, 5.0, 0.7, 1.0),  # room above the leap
                scene2d.CamKey(push_in - 1.6, 7.6, 0.0, 1.0), scene2d.CamKey(push_in, 8.4, 0.0, 1.0),
                scene2d.CamKey(total, 9.2, cy_full, 2.15)]
    sc.overlay = _caption("Demo 4 - animation on real material (real items labelled)", notes)
    anim = sc.render(work / "anim.mp4", total)
    # the real footage, framed for 16:9 (blurred fill behind), joined with a dissolve
    foot = real / "footage_portrait.mp4"
    framed = work / "footage_169.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(foot), "-filter_complex",
                    "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=24:2,"
                    "eq=brightness=-0.12[bg];[0:v]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,"
                    f"drawbox=x=60:y=930:w=820:h=86:color=black@0.62:t=fill,"
                    f"drawtext=fontfile={BOLD}:text='REAL FOOTAGE':x=84:y=944:fontsize=30:fontcolor=white,"
                    f"drawtext=fontfile={BOLD}:text='from the Print Facts report on the CEC appointment':x=84:y=982:"
                    "fontsize=24:fontcolor=0xdddddd,fps=30,format=yuv420p",
                    "-c:v", "libx264", "-crf", "14", "-preset", "slow", str(framed)], check=True)
    off = max(0.1, total - 0.5)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(anim), "-i", str(framed), "-filter_complex",
                    f"[0:v][1:v]xfade=transition=fade:duration=0.5:offset={off:.2f},format=yuv420p",
                    "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-profile:v", "high", "-movflags", "+faststart",
                    str(out)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(out), "-c:v", "libx264", "-profile:v", "main", "-level",
                    "4.0", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(out.with_name(out.stem + "_android.mp4"))], check=True)
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "1"
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    names = {"1": "Demo1_fluid_movement", "2": "Demo2_body_language", "3": "Demo3_political_explainer",
             "4": "Demo4_real_footage"}
    fn = globals()[f"demo{which}"]
    print(fn(out_dir / f"{names[which]}.mp4"))
