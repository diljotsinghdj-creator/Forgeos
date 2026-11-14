"""Demonstration films for the 2D/2.5D engine:  python -m creatorforge_worker.animation.demos A|B|C [out_dir]

A - a stickman walks in, stops, introduces himself, laughs, gets angry, is surprised (lip-synced speech)
B - two expressive characters talk: dialogue, reactions, gestures, camera cuts
C - cinematic 2.5D: a traveller and a camel cross a desert at golden hour, parallax mountains, moving camera"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import ImageFont

from . import creatures, rig2d, scene2d, speech
from .rig2d import Look

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _label(text: str):
    def draw(d, W, H, t):
        try:
            f = ImageFont.truetype(FONT, int(H * 0.028))
        except OSError:
            f = ImageFont.load_default()
        a = int(255 * min(1.0, t / 0.6))
        d.rounded_rectangle([W * 0.025, H * 0.04, W * 0.025 + d.textlength(text, font=f) + H * 0.04, H * 0.04 + H * 0.06],
                            radius=H * 0.012, fill=(20, 20, 24, int(a * 0.7)))
        d.text((W * 0.025 + H * 0.02, H * 0.052), text, font=f, fill=(255, 255, 255, a))
    return draw


def _subtitles(lines: list[tuple[float, float, str]], label: str = ""):
    head = _label(label) if label else None

    def draw(d, W, H, t):
        if head:
            head(d, W, H, t)
        for t0, t1, text in lines:
            if t0 <= t <= t1:
                f = ImageFont.truetype(FONT, int(H * 0.042))
                w = d.textlength(text, font=f)
                y = H * 0.88
                d.rounded_rectangle([W / 2 - w / 2 - H * 0.02, y - H * 0.012, W / 2 + w / 2 + H * 0.02, y + H * 0.058],
                                    radius=H * 0.012, fill=(10, 10, 14, 170))
                d.text((W / 2 - w / 2, y), text, font=f, fill=(255, 255, 255))
    return draw


def demo_a(out: Path, work: Path) -> Path:
    sc = scene2d.Scene(ppm=330, ground=0.86, horizon=0.55)
    scene2d.studio(sc)
    sam = rig2d.Character(Look(name="Sam", line=1.15), x=-4.2, seed=2)
    sc.actors.append(sam)
    clips, subs = [], []

    def line(t, text, expr, gesture="talk"):
        end, wav = sam.say(t, text, work / f"a_{len(clips)}.wav", expr=expr, gesture=gesture, rate=150)
        clips.append((t, wav))
        subs.append((t, end + 0.2, text))
        return end
    t = sam.walk(0.2, 0.0, speed=1.3)                       # walks in, eases to a stop, settles on both feet
    sam.express(0.0, "neutral")
    sam.express(t - 0.6, "happy", 0.4)
    t = line(t + 0.5, "Hi! I'm Sam.", "happy")
    t = line(t + 0.25, "Let me tell you a joke.", "mischievous")
    t += 0.3
    sam.express(t, "laughing", 0.25)
    sam.gesture(t, "laugh", 2.2)
    end, wav = sam.say(t + 0.1, "Ha ha ha ha ha!", work / "a_laugh.wav", gesture=None, rate=210, pitch=70)
    clips.append((t + 0.1, wav))
    t += 2.4
    sam.express(t, "furious", 0.25)
    sc.shake.append((t + 0.3, t + 1.0, 6))
    end = line(t + 0.25, "Hey! Who took my sandwich?", "furious", "shake_fist")
    t = end + 0.4
    sam.express(t, "shocked", 0.12)
    sam.jump(t, 0.25)
    sam.gesture(t + 0.1, "surprise", 1.8)
    t = line(t + 1.25, "Wait... it was me?", "surprised", None)
    sam.express(t + 0.2, "embarrassed", 0.4)
    sam.gesture(t + 0.2, "scratch_head", 1.6)
    t += 1.8
    sam.express(t, "happy", 0.4)
    sam.gesture(t, "wave", 1.6)
    t = sam.walk(t + 1.5, 6.5, speed=1.4)
    total = t - 0.6
    sc.cams += [scene2d.CamKey(0, 0.9, 0, 1.0, follow=sam), scene2d.CamKey(2.6, 0.5, 0, 1.0, follow=sam),
                scene2d.CamKey(4.3, 0.0, 0, 1.0), scene2d.CamKey(5.0, 0.0, -0.15, 1.35),
                scene2d.CamKey(total - 4.0, 0.0, -0.15, 1.35), scene2d.CamKey(total - 2.6, 0.6, 0, 1.0),
                scene2d.CamKey(total, 1.4, 0, 1.0)]
    sc.overlay = _subtitles(subs, "Demo A - 2D stickman")
    audio = speech.mix(clips, total, work / "a_mix.wav")
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"), audio_wav=audio)


def demo_b(out: Path, work: Path) -> Path:
    sc = scene2d.Scene(ppm=300, ground=0.86, horizon=0.58)
    scene2d.park(sc)
    maya = rig2d.Character(Look(name="Maya", ink=(30, 30, 40), body=(200, 70, 90), skin=(255, 236, 222), hair="ponytail",
                                hair_color=(60, 35, 25), skirt=(210, 80, 100), bow=(250, 200, 60), line=1.25,
                                height=1.65), x=-6.0, seed=5)
    leo = rig2d.Character(Look(name="Leo", ink=(30, 30, 40), body=(50, 110, 200), skin=(240, 214, 190), hair="spiky",
                               hair_color=(40, 30, 20), glasses=True, tie=(220, 60, 50), line=1.25, height=1.8),
                          x=1.3, facing=-1, seed=9)
    sc.actors += [leo, maya]
    clips, subs = [], []

    def say(who, t, text, expr, gesture="talk", **kw):
        end, wav = who.say(t, text, work / f"b_{len(clips)}.wav", expr=expr, gesture=gesture,
                           voice=kw.pop("voice", ""), rate=kw.pop("rate", 155), pitch=kw.pop("pitch", 50))
        clips.append((t, wav))
        subs.append((t, end + 0.15, f"{who.look.name}: {text}"))
        return end
    leo.gesture(0.0, "phone", 4.6)
    leo.express(0.0, "focused")
    t = maya.walk(0.3, -0.4, speed=1.35)
    maya.express(t - 1.0, "happy", 0.4)
    maya.gesture(t - 0.4, "wave", 1.4)
    t = say(maya, t, "Hey Leo! What are you reading?", "excited", None, voice="en-us+f3", pitch=62)
    leo.turn(t - 0.6, -1)
    leo.express(t - 0.3, "worried", 0.3)
    t = say(leo, t + 0.3, "The exam results are out.", "worried", "phone", voice="en-us+m3", pitch=40)
    maya.express(t, "curious", 0.3)
    t = say(maya, t + 0.25, "And? Did you pass?", "anxious", "talk", voice="en-us+f3", pitch=62)
    leo.express(t + 0.2, "thoughtful", 0.4)
    leo.gesture(t + 0.2, "think", 1.2)
    leo.express(t + 1.3, "excited", 0.2)
    leo.jump(t + 1.3, 0.3)
    leo.gesture(t + 1.4, "cheer", 2.0)
    t = say(leo, t + 1.6, "I got the top score!", "joyful", None, voice="en-us+m3", pitch=48, rate=170)
    maya.express(t - 0.8, "joyful", 0.25)
    maya.gesture(t - 0.6, "clap", 1.8)
    t = say(maya, t + 0.4, "That's amazing! I knew you could do it!", "joyful", "explain", voice="en-us+f3",
            pitch=66, rate=165)
    leo.express(t, "embarrassed", 0.3)
    t = say(leo, t + 0.2, "Thanks. Coffee? My treat.", "happy", "beckon", voice="en-us+m3", pitch=45)
    maya.nod(t + 0.1, 0.9)
    leo.walk(t + 0.6, 6.5, speed=1.3)
    end = maya.walk(t + 0.9, 5.6, speed=1.3)
    total = end - 0.4
    sc.cams += [scene2d.CamKey(0, -0.6, 0, 1.0), scene2d.CamKey(4.0, 0.45, 0, 1.0), scene2d.CamKey(6.0, 0.45, -0.1, 1.25),
                scene2d.CamKey(total - 3.5, 0.45, -0.1, 1.25), scene2d.CamKey(total, 3.5, 0, 1.0)]
    sc.overlay = _subtitles(subs, "Demo B - expressive stickman conversation")
    audio = speech.mix(clips, total, work / "b_mix.wav")
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"), audio_wav=audio)


def demo_c(out: Path, work: Path) -> Path:
    sc = scene2d.Scene(ppm=210, ground=0.8, horizon=0.56)
    scene2d.desert(sc)
    zara = rig2d.Character(Look(name="Zara", ink=(40, 28, 22), body=(70, 50, 40), skin=(236, 196, 160), hair="long",
                                hair_color=(30, 20, 15), shirt=(220, 235, 245), cap=(240, 236, 220), line=1.2,
                                height=1.72), x=-9.0, seed=4)
    camel = creatures.Camel(x=-11.6, z=1.18)       # a step behind Zara: smaller, slower across the screen
    sc.actors += [camel, zara]
    sc.extras += [creatures.Bird(-14, 4.2, 1.5, 1), creatures.Bird(-15.5, 4.6, 1.5, 2.5)]
    zara.walk(0.5, 4.0, speed=1.05)
    camel.walk(0.6, 1.4, speed=1.05)
    zara.express(0.0, "determined")
    zara.express(7.5, "tired", 0.6)
    zara.express(12.3, "proud", 0.5)
    zara.turn(13.4, -1)
    zara.gesture(13.4, "point", 2.0)
    zara.express(13.6, "excited", 0.3)
    end, wav = zara.say(13.8, "Look! The oasis is just there.", work / "c_0.wav", voice="en-us+f2", pitch=58,
                        expr="excited", gesture=None)
    total = 17.5
    sc.cams += [scene2d.CamKey(0, -9.0, 0.3, 1.15), scene2d.CamKey(4.0, -6.2, 0.2, 1.0),
                scene2d.CamKey(12.0, 2.0, 0.1, 1.0), scene2d.CamKey(total, 3.2, -0.1, 1.3)]
    sc.overlay = _subtitles([(13.8, end + 0.3, "Zara: Look! The oasis is just there.")],
                            "Demo C - cinematic 2.5D desert")
    audio = speech.mix([(13.8, wav)], total, work / "c_mix.wav")
    return sc.render(out, total, android=out.with_name(out.stem + "_android.mp4"), audio_wav=audio)


if __name__ == "__main__":
    which = (sys.argv[1] if len(sys.argv) > 1 else "A").upper()
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else ".").resolve()
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    fn = {"A": demo_a, "B": demo_b, "C": demo_c}[which]
    names = {"A": "Demo_A_2D_stickman", "B": "Demo_B_conversation", "C": "Demo_C_2.5D_desert"}
    print(fn(out_dir / f"{names[which]}.mp4", work))
