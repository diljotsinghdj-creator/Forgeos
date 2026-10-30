"""The animation engine: feet never slide, characters never collapse, every expression draws, speech drives the
mouth, sentences become acted scenes, and an "Animate:" line in a script plays an animated scene."""
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from creatorforge_worker.animation import face as F
from creatorforge_worker.animation import rig2d, script, speech


def _walk(c, seconds, fps=30):
    slide, low, prev = 0.0, 9.0, None
    for i in range(int(seconds * fps)):
        t = i / fps
        c.step(t, 1 / fps)
        cur = [(f.x, f.swing is None and f.y == 0) for f in c._feet]
        if prev:
            for (x0, p0), (x1, p1) in zip(prev, cur):
                if p0 and p1:
                    slide = max(slide, abs(x1 - x0))
        prev = cur
        if any(t0 <= t <= t1 for t0, t1, *_ in c.moves):
            low = min(low, c.hip[1])
    return slide, low


def test_planted_feet_never_slide_and_the_body_stays_up():
    c = rig2d.Character(rig2d.Look(), x=0.0)
    c.walk(0.2, 4.0, speed=1.3)
    c.run(4.5, 10.0)
    slide, low = _walk(c, 9.0)
    assert slide == 0.0
    assert low > 0.75 * (c.l_thigh + c.l_shin)          # a walk dips the hips a few cm, never a crouch


def test_turning_around_and_walking_off_does_not_collapse():
    m = rig2d.Character(rig2d.Look(height=1.66), x=1.2)
    m.turns = [(0.0, 1.0)]
    m.turn(4.0, -1)
    m.walk(6.0, 6.8, speed=1.3)
    slide, low = _walk(m, 12.0, 24)
    assert slide == 0.0 and low > 0.85 * (m.l_thigh + m.l_shin)


def test_a_stop_ends_on_both_feet_near_the_body():
    c = rig2d.Character(rig2d.Look(), x=0.0)
    c.walk(0.2, 3.0)
    _walk(c, 6.0)
    a, b = c._feet
    assert not a.swing and not b.swing and abs(a.x - b.x) < 0.3 * c.H
    assert min(a.x, b.x) - 0.06 * c.H <= c.hip[0] <= max(a.x, b.x) + 0.06 * c.H


def test_every_expression_and_gesture_draws():
    img = Image.new("RGB", (400, 400), "white")
    d = ImageDraw.Draw(img, "RGBA")
    for name in F.EXPRESSIONS:
        F.draw(d, 200, 200, 80, F.expression(name), 0.4, 1.0)
    c = rig2d.Character(rig2d.Look(hair="ponytail", glasses=True, tie=(200, 0, 0), beard=True, cane=True), x=0)
    for i, g in enumerate(rig2d.GESTURES):
        c.gesture(i * 1.0, g, 1.0)
    for i in range(len(rig2d.GESTURES) * 30):
        t = i / 30
        c.step(t, 1 / 30)
        rig2d.draw(d, c, c.pose(t), lambda x, y: (200 + x * 100, 380 - y * 100), 100, t)
    assert len(F.EXPRESSIONS) >= 36


def test_speech_drives_the_mouth(tmp_path):
    track = speech.say("Hello there, how are you?", tmp_path / "a.wav")
    assert speech.wav_seconds(tmp_path / "a.wav") > 1.0 and len(track) > 8
    opens = [speech.mouth_at(track, t / 50)[0] for t in range(0, int(track[-1][0] * 50))]
    assert max(opens) > 0.5 and min(opens) < 0.1         # the mouth opens and closes with the words
    hi = speech.say("नमस्ते, आप कैसे हैं?", tmp_path / "h.wav", "hi")
    assert len(hi) > 5


def test_sentences_become_scenes():
    p = script.plan("A stickman receives shocking news on his phone.")
    assert p.steps[0] == "phone" and p.feeling[0] == "shocked"
    p = script.plan("Two friends argue in the park.")
    assert len(p.people) == 2 and p.place == "park" and "argue" in p.steps
    p = script.plan('An old woman walks through the desert with her camel and says "Almost home."')
    assert p.place == "desert" and p.camel and p.people[0].cane and p.quote == "Almost home."


@pytest.mark.ffmpeg
def test_an_animate_line_plays_an_animated_scene(cfg):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    text = ("The Phone Call\n\nIt was an ordinary Tuesday evening.\nVisual: A quiet street at dusk\n\n"
            "He opened the message and froze.\nVisual: A man at a desk\n"
            "Animate: a stickman receives shocking news on his phone\n\n"
            "Nothing would be the same again.\nVisual: A quiet street at night\n\n"
            "Tomorrow, everything would change.\nVisual: Sunrise over the city\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": text, "duration_s": 15}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
    assert job["status"] == "READY", job.get("error")
    assert job["providers"].get("animation") == "CreatorForge 2D animation"
    clips = [n for s in job["scenes"] for n in (s.get("beat_clips") or []) if n and "_anim" in n]
    assert clips and (cfg.jobs_dir / jid / clips[0]).stat().st_size > 10_000
