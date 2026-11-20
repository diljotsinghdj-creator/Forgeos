"""The opening test, look 2: act 0 of SCRIPT.md, from 0:00 to "So how did I do that?".

Look 1 (opening_v1.py) was drawn cards on a slate mat; the owner rejected it on 2026-11-20 ("the look"). This is the rebuild in the
owner's reference style (STYLE_REFERENCES.md): collage, not graphics. Every shot starts from a real piece (assets/real2, made by
cut2.py from Pixabay photos and public-domain engravings), the frame builds piece by piece, and nothing sits still.

The signature: an engraved hand deals cards. One card goes into an engraved head; fifteen more are held up, one word each.

Three rules of the trap decide what may be on screen before the reveal (checked at the bottom of this file):
  1. "sleep" is never said or shown before the third test word;
  2. nothing names the study, the effect or the missing word before the reveal, not even the source line;
  3. nothing names a road sign, the plant line carries no caption, and nothing says the second test is the car clip.

Two passes, because the 60-second promise has to be exact:
  python3 opening.py; film_video.py <film> --voice-only; python3 opening.py; python3 preview.py; film_video.py <film> --workers 3
The wording is SCRIPT.md's, unchanged. Two lines are split in two at a full stop, so each half gets its own shot."""
import json
import math
import wave
from pathlib import Path

from ck import (A, a, W, put, page, cut, hgt, plate, disc, ring, dots, torn, block, bebas, serif, label, marker, mono, hl, tape, card, sheet, word, typed, loop, arrow, sparks,
                credit, stamp, CENTER, SL, PAPER, CO, AM, RED, WHITE, SH)
import props as P

D = Path(__file__).resolve().parent
V = D / "video"; V.mkdir(exist_ok=True)
FPS, WORD_FRAMES, MINUTE, CLIP, AFTER = 24, 34, 60 * 24, (53, 24), 45   # 34 frames = 1.42 s a word; the minute is 1,440 frames; the clip: follow 53 frames, push in 24, then 45 silent on the bump
VOICE, SPEED = "af_heart", 1.1
WORDS = ["Bed", "Rest", "Awake", "Tired", "Dream", "Wake", "Snooze", "Blanket", "Doze", "Slumber", "Snore", "Nap", "Peace", "Yawn", "Drowsy"]
PUSH = [1.0, .5, .5, 1.045, .5, .5]

# ---- the shot plan ---------------------------------------------------------------------------------------------------------
# zone "list" and "gap" make up the minute; w = a gap shot's share of the minute's spare time; fix = a silent shot's length in frames;
# tail = seconds the page keeps building after the line ends (for a stamp that lands in the pause)
S, K = [], {}


def shot(key, vo, pg, t=(0, 1), cam=None, beat=1, zone="", **kw):
    s = {"id": f"0.{len(S) + 1:02d}", "beat": beat, "vo": vo, "page": pg, "t": [round(x, 4) for x in t], "cam": list(cam or PUSH), "zone": zone,
         "capbreak": True, **kw}      # captions go line by line: no group runs on into the next shot's words
    S.append(s); K[key] = s


shot("hook1", "Give me sixty seconds. I'm going to put a memory in your head.", "c_hook", (0, .29), [1.0, .5, .5, 1.06, .5, .5], post=.15)
shot("hook2", "Of something that never happened.", "c_hook", (.3, .55), [2.0, .308, .665, 2.12, .308, .665], post=.2)
shot("hook3", "If it works, you won't feel a thing. You'll just be sure.", "c_hook", (.55, 1), [1.12, .62, .48, 1.28, .7, .36], post=.4)
shot("court", "And this same glitch has helped put innocent people in prison.", "c_court", (0, 1), [1.0, .5, .5, 1.06, .5, .5], post=.6, tail=.45)
shot("instr", "Fifteen words. Don't write them down.", "c_instr", (0, 1), [1.0, .5, .5, 1.05, .5, .5], post=.5)
for i, w in enumerate(WORDS):
    shot(f"w{i + 1}", f"{w}.", f"c_w{i + 1:02d}", (0, 1), PUSH, beat=2, zone="list", pre=.2, mute=True, nocap=True)
shot("done", "Done. Put those away.", "c_drawer", (0, .5), [1.1, .45, .55, 1.08, .46, .52], beat=2, zone="gap", w=.8)
shot("watch", "Watch this once.", "c_drawer", (.5, 1), [1.08, .46, .52, 1.0, .5, .5], beat=2, zone="gap", w=.5)
shot("clipa", "", "c_clip", (0, CLIP[0] / sum(CLIP)), [2.0, .25, .56, 2.0, .75, .56], beat=2, zone="gap", fix=CLIP[0])           # the camera follows the car past the sign and stops as it hits
shot("clipb", "", "c_clip", (CLIP[0] / sum(CLIP), 1), [2.0, .75, .56, 2.6, .808, .64], beat=2, zone="gap", fix=CLIP[1])         # then pushes in on the bump; the sign leaves the frame
shot("witness", "Congratulations. You are now a witness.", "c_witness", (0, 1), [2.6, .808, .64, 2.6, .808, .6], beat=2, zone="gap", w=1.0, pre=AFTER / FPS)   # the clip's last 1.9 s are this shot's silent start
shot("email", "Somewhere, the owner of the blue car that ran the stop sign is drafting a defensive email.", "c_email", (0, 1), [1.0, .5, .5, 1.14, .5, .34], beat=2, zone="gap", w=1.1, nocap=True)   # plant 1 is never on screen, so this line carries no caption
shot("bar", "That amber bar is your minute.", "c_bar", (0, 1), [1.0, .5, .5, 1.03, .53, .5], beat=2, zone="gap", w=.5)
shot("rehearse", "Don't rehearse. I can't see you, but I'll know.", "c_rehearse", (0, 1), [1.03, .53, .5, 1.06, .5, .54], beat=2, zone="gap", w=.9)
shot("sure", "Some of you are already sure you'll pass.", "c_sure", (0, 1), [1.0, .5, .5, 1.05, .52, .47], beat=2, zone="gap", w=.8)
shot("hold", "Hold on to that feeling. We'll need it later.", "c_hold", (0, 1), [1.05, .52, .47, 1.02, .5, .52], beat=2, zone="gap", w=1.0)
shot("folders", "This trick has a lab behind it, and nearly seventy years of paperwork.", "c_folders", (0, 1), [1.0, .5, .5, 1.05, .53, .5], beat=2, zone="gap", w=.8)
shot("later", "You'll get all of it after you've fallen for it.", "c_later", (0, 1), [1.05, .53, .5, 1.0, .5, .5], beat=2, zone="gap", w=1.5, pre=.2, mute=True)
shot("test1", "Time. Three words. Was each one on my list?", "c_test", (0, .5), [1.0, .5, .5, 1.05, .5, .5], beat=3, post=.2, mute=True)
shot("test2", "Yes or no, out loud. If you're on a bus, commit.", "c_test", (.5, 1), [1.05, .5, .5, 1.08, .47, .5], beat=3, post=.45, mute=True)
for n_, (w, post) in enumerate((("Dream", 1.2), ("Door", 1.2), ("Sleep", 1.5))):
    shot(f"tw{n_ + 1}", f"{w}.", f"c_t_{w.lower()}", (0, 1), PUSH, beat=3, pre=.3, post=post, mute=True, nocap=True)
shot("cards", "Dream was on the list. Door wasn't.", "c_cards", (0, 1), [1.0, .5, .5, 1.05, .5, .46], beat=3, post=.25, mute=True)
shot("sleepq", "And sleep?", "c_reveal", (0, 0), [1.5, .82, .36, 1.9, .84, .36], beat=3, post=.45, mute=True)
shot("never", "I never said it.", "c_reveal", (0, 1), [1.9, .84, .36, 2.05, .84, .36], beat=3, post=.3, mute=True)
shot("notonce", "Not once.", "c_reveal2", (0, .4), [1.0, .5, .5, 1.03, .5, .5], beat=3, post=.6, mute=True)
shot("scroll", "Scroll back and check. I'm a video. I can wait.", "c_reveal2", (.4, 1), [1.03, .5, .5, 1.06, .5, .5], beat=3, post=.5)
shot("maj1", "Said yes? You're the majority.", "c_majority", (0, .2), [1.0, .5, .5, 1.05, .46, .5], beat=3, post=.15)
shot("maj2", "When researchers tested this exact list, more than 80 percent of people said yes to \"sleep\".", "c_majority", (.2, .9), [1.05, .46, .5, 1.08, .5, .5], beat=3, post=.35)
shot("title", "And I warned you. It's in the title.", "c_title", (0, 1), [1.0, .5, .5, 1.08, .5, .58], beat=3, post=.6, tail=.3)
shot("warn", "Warnings shrink the effect. They don't remove it.", "c_warning", (0, 1), [1.0, .5, .5, 1.04, .5, .5], beat=3, post=.3)
shot("maj3", "If you said no, well done. It doesn't work on everyone.", "c_majority", (.901, 1), [1.7, .86, .5, 1.8, .86, .46], beat=3, post=.35)
shot("env1", "But I've already planted a second false memory in this video.", "c_envelope", (0, .5), [1.0, .5, .5, 1.08, .5, .5], beat=3, post=.2)
shot("env2", "It isn't a word. I'll collect it at the end.", "c_envelope", (.5, 1), [1.3, .5, .6, 1.36, .5, .62], beat=3, post=.35)
shot("env3", "So how did I do that?", "c_envelope", (1, 1), [1.36, .5, .62, 1.0, .5, .5], beat=3, post=.9)

# ---- timing ------------------------------------------------------------------------------------------------------------------
LINES = json.loads((V / "audio" / "lines.json").read_text()) if (V / "audio" / "lines.json").is_file() else {}


def recorded(i, s):
    """The length of this shot's line as recorded, if the file on disk is this exact text in this voice."""
    f = V / "audio" / f"{i:03d}.wav"
    if s["vo"] and f.is_file() and LINES.get(f.name) == f"{VOICE}|{SPEED}|{s['vo']}":
        with wave.open(str(f)) as w:
            return w.getnframes() / w.getframerate()


guessed = []
for i, s in enumerate(S):
    r = recorded(i, s)
    s["v"] = r if r is not None else (max(.5, len(s["vo"].split()) / 2.9) if s["vo"] else 0.0)
    if s["vo"] and r is None:
        guessed.append(s["id"])

# the minute lasts exactly 1,440 frames: the words and the clip are fixed, the spoken lines share what is left
for s in S:
    if s["zone"] == "list":
        s["frames"] = WORD_FRAMES
    elif s.get("fix"):
        s["frames"] = s["fix"]
talk = [s for s in S if s["zone"] == "gap" and not s.get("fix")]
need = [s.get("pre", 0.0) + s["v"] for s in talk]
spare = (MINUTE - sum(s["frames"] for s in S if "frames" in s)) / FPS - sum(need)
Wt = sum(s["w"] for s in talk)
for s, b in zip(talk, need):
    s["frames"] = math.ceil((b + max(.08, spare * s["w"] / Wt)) * FPS)
talk[-1]["frames"] += MINUTE - sum(s["frames"] for s in S if s["zone"])       # the last pause takes up the rounding
assert spare > 3 and talk[-1]["frames"] / FPS - need[-1] > .5, (spare, "the minute is too full for its lines")
done = 0
for s in S:
    pre = s.get("pre", 0.0)
    if s["zone"]:
        L = s["frames"] / FPS
        if s["vo"]:
            s["post"] = round(L - pre - s["v"] - .004, 4)      # the engine rounds a shot up to whole frames
        else:
            s["hold"], s["post"] = round(L - .004, 4), 0.0
        s["build"] = round(L, 4)                               # the page's timeline runs for the whole shot, so the bar moves evenly
        s["p0"], s["p1"] = done / MINUTE, (done + s["frames"]) / MINUTE
        done += s["frames"]
    elif "tail" in s:
        s["build"] = round(pre + s["v"] + s["tail"], 4)
assert done == MINUTE, done
start = 0.0
for s in S:
    pre = s.get("pre", 0.0)
    s["L"] = math.ceil((pre + s["v"] + s.get("post", .3) + s.get("hold", 0.0)) * FPS - 1e-6) / FPS
    s["B"] = s.get("build") or max(.4, pre + s["v"] if s["v"] else s["L"] * .8)        # the engine's own rule
    s["start"] = start; start += s["L"]
REWIND = f'{int(K["w1"]["start"]) // 60}:{int(K["w1"]["start"]) % 60:02d}'

OWN = ("zone", "w", "fix", "tail", "frames", "p0", "p1", "v", "L", "B", "start")
(V / "shots.json").write_text(json.dumps({"slug": "false-memory-opening-test", "title": "Can I Give You a False Memory in 60 Seconds? (opening test, look 2)", "channel": "dragonpsych",
                                          "voice": VOICE, "speed": SPEED, "treatment": "pulse", "guide": {}, "reload_pages": [], "room_tone": -62,
                                          "shots": [{k: v for k, v in s.items() if k not in OWN} for s in S]}, indent=1))
print(f"shots: {len(S)} · {start:.1f} s · list starts at {K['w1']['start']:.2f} s, test at {K['test1']['start']:.2f} s (gap {K['test1']['start'] - K['w1']['start']:.3f} s) · "
      f"spare time in the minute {spare:.2f} s · rewind tag {REWIND}" + (f" · NOT YET RECORDED (estimates): {guessed}" if guessed else " · every line timed from the recorded voice"))


# ---- when things happen --------------------------------------------------------------------------------------------------------
def T(key, sec):
    """The moment on the page's timeline that falls `sec` seconds into this shot."""
    s = K[key]; t0, t1 = s["t"]
    return t0 + (t1 - t0) * min(1.0, max(0.0, sec) / s["B"])


def an(kind, key, sec, dur=0.0):
    a0 = T(key, sec)
    return f"{kind} {a0:.4f} {max(a0, T(key, sec + dur)):.4f}"


def said(key, frac):
    """Seconds into the shot at which this fraction of the line has been spoken."""
    return K[key].get("pre", 0.0) + K[key]["v"] * frac


def end(key, plus=0.0):
    return said(key, 1) + plus


# ---- the 60-second bar: fixed to the screen, not to the page, so it holds still while the camera moves -------------------------------
def hud(inner):
    return f'<div class="a" data-hud style="left:0;top:0;width:1920px;height:1080px;z-index:95;pointer-events:none">{inner}</div>'


def bar(key, key2=None, y=1012, dark=False, full=False, more=""):
    """The thin amber bar, moving evenly through this shot's share of the minute (key2: the page is shot twice in a row)."""
    edge = "rgba(240,244,248,.5)" if dark else "rgba(20,24,36,.6)"; track = "rgba(20,24,36,.6)" if dark else "rgba(240,244,248,.92)"
    fill = (f'<div class="a" style="left:82px;top:{y + 2}px;width:1756px;height:10px;background:{AM}"></div>' if full else
            f'<div class="a" data-anim="bar 0 1" data-p0="{K[key]["p0"]:.5f}" data-p1="{K[key2 or key]["p1"]:.5f}" data-w="1756" style="left:82px;top:{y + 2}px;height:10px;background:{AM}"></div>')
    return hud(a(f'<div style="width:1760px;height:14px;background:{track};border:2px solid {edge};box-sizing:border-box"></div>', 80, y)
               + fill + a(f'<div style="font:500 15px Mono;letter-spacing:3px;color:{AM if dark else SL};background:{track};padding:0 5px">60 S</div>', 1846, y - 4) + more)


# ---- source lines. Before the reveal they name nothing (see the rules above) ----------------------------------------------------------
S_PRE = "THE 15 WORDS COME FROM A PUBLISHED MEMORY STUDY · IT IS NAMED AFTER THE TEST, SO THE TEST STAYS FAIR"
S_REV = "\"SLEEP\" WAS NEVER SAID OR SHOWN BEFORE THE TEST · THE EFFECT: ROEDIGER & McDERMOTT 1995, J. EXP. PSYCHOL.: LMC · THE LIST: THE STUDY'S 15 ASSOCIATES OF ONE MISSING WORD"

# ---- 0:00 the hook: an engraved hand brings a card to an engraved head -------------------------------------------------------------
def ink(html):
    """A stamp inked twice, so it reads over a busy engraving."""
    return f'<div style="position:relative">{html}<div style="position:absolute;left:0;top:0">{html}</div></div>'


t2 = T("hook2", 0)   # at the cut to shot 2 the headline leaves
hand = (a(card(mono("FILE: ONE MEMORY", 32, SL, 3) + '<div style="height:22px"></div><div style="margin-left:62px">' + typed("SUBJECT: NEVER HAPPENED", 28, 2, an("type", "hook2", .08, 1.0))
               + '<div style="height:10px"></div>' + W(mono("STATUS:", 28, SL, 2), an("qsnap", "hook3", .12)) + '</div>', 596, 404, 0, pad=34), 328, 34)
        + f'<img src="/assets/real2/hand_sign.png" style="position:absolute;left:0;top:0;width:980px;height:{hgt("hand_sign", 980)}px;filter:drop-shadow(8px 10px 0 rgba(20,24,36,.2))">')
put("c_hook", page(
    A(disc(980, CO), 1060, 60, an("pop", "hook1", 0, .35), "z-index:5")
    + A(W(ring(1130, SL, "20 18", 4), "spin 0 1", 'data-deg="26"'), 985, -15, "snap 0 0", "z-index:6")
    + a(dots(560, 330, SL, 18, 2.4, .32), 70, 690, "z-index:4")
    + f'<div data-anim="hide {t2:.4f} {t2:.4f}">' + A(bebas("GIVE ME", 250), 84, 50, an("slam", "hook1", .04, .12), "z-index:10")
    + A(bebas(f'<span style="color:{AM}">60</span> SECONDS', 250), 84, 264, an("qslam", "hook1", .52, .12), "z-index:10") + '</div>'
    + cut("head_brain", 1030, 960, -30, an("drop", "hook1", said("hook1", .46), .45), z=30, boil=T("hook1", said("hook1", .7)), data='data-dx="700" data-dy="0"')
    + A(W(W(hand, an("drift", "hook3", .25, .9), 'data-dx="400"', "position:relative;width:980px;height:470px"),
          an("qdrop", "hook1", said("hook1", .62), .5), 'data-dx="-1000" data-dy="0"'), -30, 500, "snap 0 0", "z-index:20")
    + A(ink(stamp("CERTAIN", 112, -8)), 1150, 262, an("slam", "hook3", said("hook3", .84), .1), "z-index:60")
    + A(label("ONE MEMORY, GOING IN", 20, SL, PAPER, -3), 1250, 880, an("pop", "hook3", .9, .2), "z-index:61"),
    credit("head_brain", "hand_sign") + " · THE CLAIM IS TESTED ON THE VIEWER IN THIS VIDEO · THE STUDY IS NAMED AFTER THE TEST"))

# ---- 0:07 the stakes: the real courthouse, and where it stands ---------------------------------------------------------------------------
k = "court"
ncmap = P.nc_map()[0].replace("#0F1420", "#DCE3EC").replace("#232B3E", "#C6D0DD").replace("#4A5670", "#8794A8")      # the film's map, on paper
MAPW = 450; MAPS = MAPW / 1300
put("c_court", page(
    A(disc(840, CO), 100, 130, an("pop", k, 0, .3), "z-index:5") + A(W(ring(980, SL, "20 18", 4), "spin 0 1", 'data-deg="-22"'), 30, 60, "snap 0 0", "z-index:6")
    + cut("courthouse", 1010, 30, 268, an("qdrop", k, .06, .45), z=20, boil=T(k, .8), data='data-dx="0" data-dy="760"')
    + A(bebas("INNOCENT", 216), 1030, 70, an("slam", k, said(k, .54), .1), "z-index:10") + A(bebas("PEOPLE.", 216), 1030, 254, an("qslam", k, said(k, .54) + .14, .1), "z-index:10")
    + A(bebas("IN PRISON.", 200, AM), 1030, 446, an("slam", k, said(k, .8), .1), "z-index:10")
    + A(f'<div style="background:{WHITE};padding:10px 10px 36px;{SH};transform:rotate(2deg);position:relative"><div style="width:{MAPW}px;height:{640 * MAPS:.0f}px;overflow:hidden">'
        f'<div style="transform:scale({MAPS:.4f});transform-origin:0 0;width:1300px;height:640px">{ncmap}</div></div>'
        f'<div style="position:absolute;left:12px;bottom:9px;font:500 14px Mono;letter-spacing:2px;color:#5B6880">ALAMANCE COUNTY, NORTH CAROLINA</div></div>',
        1420, 630, an("qdrop", k, said(k, .3), .4), "z-index:25", 'data-dx="560" data-dy="0"')
    + A(label("HOLD THAT THOUGHT", 30, AM, SL, -3), 1036, 664, an("slam", k, end(k, .1), .1), "z-index:40")
    + A(marker("we come<br>back here.", 56, SL, -3), 1044, 744, an("wipe", k, end(k, .15), .28), "z-index:40") + arrow(1034, 812, 930, 770, an("draw", k, end(k, .2), .2), SL, 7, -30),
    "PHOTO: W_LEMAY, CC0 (THE COURTHOUSE OF ALAMANCE COUNTY, N.C.: THE COUNTY OF A CASE TOLD LATER) · MAP: NATURAL EARTH · THE FIGURES BEHIND THIS LINE: INNOCENCE PROJECT, DNA EXONERATIONS 1989-2020"))

# ---- 0:11 the instructions: a real pencil, and it snaps ----------------------------------------------------------------------------------
k = "instr"; snap_t = T(k, said(k, .72)); pw = 640; ph = hgt("pencil", pw)
half = lambda poly, dx, dy: (f'<div data-anim="drift {snap_t:.4f} {snap_t:.4f}" data-dx="{dx}" data-dy="{dy}" style="position:absolute;left:0;top:0;clip-path:polygon({poly})">'
                             f'<img src="/assets/real2/pencil.png" style="width:{pw}px;height:{ph}px;display:block;filter:saturate(.7) drop-shadow(8px 10px 0 rgba(20,24,36,.22))"></div>')
put("c_instr", page(
    a(block(800, 880, CO, -4), 150, 100, "z-index:4")
    + A(sheet(serif("PARTICIPANT INSTRUCTIONS", 52) + mono("FORM 15-W · STUDIO RECONSTRUCTION", 18, CO, 4, "margin-top:8px")
              + f'<div style="height:5px;background:{SL};margin:22px 0 38px"></div>' + mono("1. YOU WILL HEAR FIFTEEN WORDS.", 37) + '<div style="height:34px"></div>'
              + mono("2. " + hl("DO NOT WRITE THEM DOWN."), 37) + '<div style="height:34px"></div>' + mono("3. THAT IS THE WHOLE TEST.", 37), 960, 800, -1.5, pad=56),
        90, 130, an("drop", k, 0, .3), "z-index:8", 'data-dx="-500" data-dy="0"')
    + A(f'<div style="position:relative;width:{pw}px;height:{ph}px;transform:rotate(-27deg)">' + half("0 0,58% 0,42% 100%,0 100%", -18, -4) + half("58% 0,100% 0,100% 100%,42% 100%", 20, 6) + '</div>',
        380, 478, an("drop", k, .5, .35), "z-index:30", 'data-dx="500" data-dy="-300"')
    + sparks(700, 768, f"slam {snap_t:.4f} {snap_t:.4f}", AM, 70, 150, 6, 9)
    + A(serif("15", 440, AM), 1190, 30, an("slam", k, .04, .1), "z-index:10") + A(bebas("WORDS", 270), 1196, 470, an("slam", k, .5, .1), "z-index:10")
    + A(label("NO NOTES", 32, SL, PAPER, 4), 1206, 760, an("slam", k, said(k, .95), .1), "z-index:40"),
    credit("pencil") + " · THE VIEWER'S INSTRUCTIONS (OUR WORDING) · " + S_PRE))

# ---- the list: an engraved hand holds up each word. Five ways of holding it, in turn -----------------------------------------------------
HSH = "filter:drop-shadow(9px 11px 0 rgba(20,24,36,.2))"
for i, w_ in enumerate(WORDS):
    U, kind, key = w_.upper(), i % 5, f"w{i + 1}"; pop = lambda dx, dy: (an("drop", key, .03, .16), f'data-dx="{dx}" data-dy="{dy}"'); b0 = T(key, .3)
    boil = lambda html: W(html, f"boil {b0:.4f} 1", 'data-a=".25" data-px="1.2" data-n="40"')
    if kind == 0:      # the pointing hand brings a wide card in from the left
        hw = 1500; hh = hgt("hand_sign", hw); cx0, cx1, cy0, cy1 = .367 * hw, .961 * hw, .073 * hh, .920 * hh
        g = (a(card(CENTER(word(U, cx1 - cx0, cy1 - cy0)), int(cx1 - cx0) + 12, int(cy1 - cy0) + 12, 0, pad=20), int(cx0) - 6, int(cy0) - 6)
             + f'<img src="/assets/real2/hand_sign.png" style="position:absolute;left:0;top:0;width:{hw}px;height:{hh}px;{HSH}">')
        an_, dt = pop(-760, 0); body = (a(disc(760, CO), 700, 150, "z-index:5") + a(dots(420, 300, SL, 18, 2.4, .3), 1420, 80, "z-index:4")
                                        + A(boil(f'<div style="position:relative;width:{hw}px;height:{hh}px">{g}</div>'), -60, 240, an_, "z-index:20", dt))
        used = ("hand_sign",)
    elif kind == 1:    # a hand holds a card up from below
        hw = 1250; hh = hgt("hand_up", hw); x0, y0 = 227, 80; bx0, bx1, by0, by1 = .247 * hw, .926 * hw, .037 * hh, .300 * hh
        an_, dt = pop(0, 760); body = (a(disc(900, CO), 510, 520, "z-index:5") + A(W(ring(1010, SL, "18 16", 4), "spin 0 1", 'data-deg="20"'), 455, 465, "snap 0 0", "z-index:6")
                                       + A(boil(f'<div style="position:relative;width:{hw}px;height:{hh}px"><img src="/assets/real2/hand_up.png" style="width:{hw}px;height:{hh}px;{HSH}">'
                                                + a(CENTER(word(U, bx1 - bx0, by1 - by0)), int(bx0), int(by0), f"width:{int(bx1 - bx0)}px;height:{int(by1 - by0)}px") + '</div>'), x0, y0, an_, "z-index:20", dt))
        used = ("hand_up",)
    elif kind == 2:    # a cuffed hand deals the card down from the top right, at an angle
        hw = 1500; hh = hgt("hand_sleeve", hw); ccx, ccy = .3675 * hw, .7145 * hh; x0, y0 = int(930 - ccx), int(566 - ccy)
        an_, dt = pop(560, -620); body = (a(block(820, 640, CO, -5), 150, 300, "z-index:5") + a(dots(420, 300, SL, 18, 2.4, .3), 130, 60, "z-index:4")
                                          + A(boil(f'<div style="position:relative;width:{hw}px;height:{hh}px"><img src="/assets/real2/hand_sleeve.png" style="width:{hw}px;height:{hh}px;{HSH}">'
                                                   + a(f'<div style="width:760px;height:400px;transform:rotate(-17deg)">{CENTER(word(U, 760, 400))}</div>', int(ccx - 380), int(ccy - 200)) + '</div>'),
                                              x0, y0, an_, "z-index:20", dt))
        used = ("hand_sleeve",)
    elif kind == 3:    # a tall card in a fist, for the short words
        hw = 1000; hh = hgt("hand_card", hw); bx0, bx1, by0, by1 = .265 * hw, .801 * hw, .140 * hh, .689 * hh; x0, y0 = int(960 - (bx0 + bx1) / 2), int(500 - (by0 + by1) / 2)
        an_, dt = pop(0, 800); body = (a(disc(820, CO), 550, 90, "z-index:5")
                                       + A(boil(f'<div style="position:relative;width:{hw}px;height:{hh}px"><img src="/assets/real2/hand_card.png" style="width:{hw}px;height:{hh}px;{HSH}">'
                                                + a(CENTER(word(U, bx1 - bx0, by1 - by0, share=.8)), int(bx0), int(by0), f"width:{int(bx1 - bx0)}px;height:{int(by1 - by0)}px") + '</div>'), x0, y0, an_, "z-index:20", dt))
        used = ("hand_card",)
    else:              # a real manila tag, the word typed on it
        tw_ = 1340; th_ = hgt("tag2", tw_)
        an_, dt = pop(700, -260); body = (a(disc(700, CO), 180, 250, "z-index:5") + a(dots(460, 320, SL, 18, 2.4, .3), 1380, 90, "z-index:4")
                                          + A(boil(f'<div style="position:relative;width:{tw_}px;height:{th_}px;transform:rotate(-4deg)"><img src="/assets/real2/tag2.png" style="width:{tw_}px;height:{th_}px;filter:saturate(.62) drop-shadow(9px 11px 0 rgba(20,24,36,.22))">'
                                                   + a(CENTER(word(U, tw_ * .72, th_ * .7)), int(tw_ * .22), int(th_ * .15), f"width:{int(tw_ * .72)}px;height:{int(th_ * .7)}px") + '</div>'), 290, 190, an_, "z-index:20", dt))
        used = ("tag2",)
    put(f"c_w{i + 1:02d}", page(a(label(f"WORD {i + 1} OF 15", 22), 90, 64, "z-index:40") + body + bar(key), credit(*used) + " · " + S_PRE))

# ---- the minute between the list and the test -------------------------------------------------------------------------------------
kd, kw_ = "done", "watch"
sw = 740; sh_ = hgt("hand_sleeve", sw)
PW, PH = 940, 610; IW = PH * 1280 / 782; OFF = (IW - PW) / 2       # the print of the drawers: the photo covers it, cropped at the sides
DX0, DX1, DY0, DY1 = .41 * IW - OFF, .59 * IW - OFF, .205 * PH, .40 * PH   # the one drawer that takes the cards
PX0, PY0 = 80, 232
lit = f'data-anim="{an("snap", kd, 1.0)}"'
drawers = (f'<div style="position:relative;background:{WHITE};padding:14px 14px 44px;{SH};transform:rotate(-2deg)">'
           f'<div style="position:relative;width:{PW}px;height:{PH}px;overflow:hidden"><img src="/assets/real2/drawers.jpg" style="position:absolute;left:{-OFF:.0f}px;top:0;width:{IW:.0f}px;height:{PH}px">'
           f'<div {lit} style="position:absolute;left:{DX0:.0f}px;top:{DY0:.0f}px;width:{DX1 - DX0:.0f}px;height:{DY1 - DY0:.0f}px;background:{AM};mix-blend-mode:multiply"></div>'
           f'<div {lit} style="position:absolute;left:{DX0 - 5:.0f}px;top:{DY0 - 5:.0f}px;width:{DX1 - DX0:.0f}px;height:{DY1 - DY0:.0f}px;border:5px solid {AM}"></div></div>'
           f'<div style="position:absolute;left:16px;bottom:11px;font:500 17px Mono;letter-spacing:3px;color:#5B6880">15 WORDS · FILED UNDER "LATER"</div>' + a(tape(170, -5), 380, -22) + '</div>')
gone = an("hide", kd, .95)
filed = "".join(A(W(card("", 170, 108, r, lines=True, pad=8), gone), PX0 + 14 + (DX0 + DX1) / 2 - 85 + ox, PY0 + 14 + (DY0 + DY1) / 2 - 54 + oy, an("drop", kd, .34 + j * .15, .22), "z-index:12", 'data-dx="620" data-dy="-380"')
                for j, (ox, oy, r) in enumerate(((-20, -12, -9), (16, 8, 6), (-4, -2, -2))))
put("c_drawer", page(
    a(block(1000, 690, CO, 3), 60, 250, "z-index:4")
    + A(drawers, PX0, PY0, an("drop", kd, 0, .3), "z-index:10", 'data-dx="-400" data-dy="0"') + filed
    + A(f'<div style="position:relative;width:{sw}px;height:{sh_}px"><img src="/assets/real2/hand_sleeve.png" style="width:{sw}px;height:{sh_}px;{HSH}">'
        + a(f'<div style="transform:rotate(-17deg);transform-origin:0 0">{serif("EXHIBIT A", 46)}{mono("ONE SHORT CLIP", 19, SL, 3, "margin-top:8px")}{mono(hl("WATCH IT ONCE"), 19, SL, 3, "margin-top:8px")}</div>',
            int(sw * .13), int(sh_ * .70)) + '</div>',
        1140, 190, an("drop", kd, said(kd, .45), .45), "z-index:20", 'data-dx="700" data-dy="-200"')
    + a('<div style="display:flex;gap:46px;white-space:nowrap">' + W(bebas("WATCH", 200), an("slam", kw_, .05, .1)) + W(bebas("THIS", 200), an("slam", kw_, .28, .1)) + W(bebas("ONCE.", 200, AM), an("slam", kw_, .56, .1)) + '</div>', 84, 44, "z-index:9")
    + bar("done", "watch"), credit("drawers", "hand_sleeve")))

# the clip: one street, seen from the side. The blue car passes the junction's red triangle and bumps the parked red car. No other sign exists in it.
# The camera follows the car, stops on the bump and pushes in; the triangle is in view while the car passes it and leaves the frame on the push.
TC = sum(CLIP) / FPS
ct = lambda sec: round(sec / TC, 4)
BW = 330; BH = hgt("car_blue", BW); RW = 250; RH = hgt("car_red", RW); SGN = 150


def street(moving):
    car = (f'<div class="a" data-anim="move {ct(.15)} {ct(1.95)}" data-dx="-1230" style="left:1290px;top:{762 - BH}px;z-index:30">' if moving else f'<div class="a" style="left:1290px;top:{762 - BH}px;z-index:30">')
    hit = f"slam {ct(1.97)} {ct(1.97)}" if moving else "snap 0 0"
    jolt = f'data-anim="drift {ct(1.97)} {ct(1.97)}" data-dx="14" style="' if moving else 'style="transform:translateX(14px);'
    return (a(f'<div style="width:1920px;height:430px;overflow:hidden;clip-path:polygon(0 4%,7% 1%,15% 5%,24% 0,33% 4%,45% 1%,56% 5%,68% 0,79% 4%,90% 1%,100% 5%,100% 100%,0 100%);filter:blur(1.1px)">'
              f'<img src="/assets/real2/street.jpg" style="width:1920px;height:884px;margin-top:-250px;display:block"></div>', 0, 215, "z-index:5")
            + a(f'<div style="width:1920px;height:430px;background-image:radial-gradient(rgba(20,24,36,.5) 1.3px,transparent 1.8px);background-size:7px 7px;mix-blend-mode:multiply"></div>', 0, 215, "z-index:6")
            + a(f'<div style="width:1920px;height:122px;background:#2A3145"></div>', 0, 645, "z-index:8") + a(f'<div style="width:1920px;height:7px;background:{WHITE}"></div>', 0, 641, "z-index:9")
            + "".join(a(f'<div style="width:70px;height:7px;background:rgba(240,244,248,.75)"></div>', x, 703, "z-index:9") for x in range(20, 1920, 150))
            + a(f'<div style="width:11px;height:150px;background:#5B6880"></div>', 1000 + SGN // 2 - 5, 500, "z-index:14") + cut("sign_face", SGN, 1000, 352, "snap 0 0", z=15)
            + f'<div class="a" {jolt}left:1620px;top:{762 - RH}px;z-index:28"><img src="/assets/real2/car_red.png" style="width:{RW}px;height:{RH}px;display:block;filter:drop-shadow(6px 7px 0 rgba(20,24,36,.25))"></div>'
            + car + f'<img src="/assets/real2/car_blue.png" style="width:{BW}px;height:{BH}px;display:block;transform:scaleX(-1);filter:drop-shadow(6px 7px 0 rgba(20,24,36,.25))"></div>'
            + sparks(1622, 690, hit, AM, 34, 84, 6, 7))


S_CLIP = credit("car_blue", "sign_face", "street") + " · A STUDIO COLLAGE OF REAL PHOTOS (NOT A REAL ACCIDENT)"
put("c_clip", page(street(True) + bar("clipa", "clipb"), S_CLIP, gobo=False))
kx = "witness"
put("c_witness", page(street(False) + cut("eye", 210, 1186, 490, an("pop", kx, said(kx, .5), .25), z=26, boil=T(kx, said(kx, .7)))
                      + arrow(1392, 598, 1596, 672, an("draw", kx, said(kx, .62), .3), AM, 6, -24)
                      + A(label("WITNESS NO. 1 · YOU", 20, AM, SL, -3), 1414, 498, an("slam", kx, said(kx, .8), .1), "z-index:61") + bar(kx), S_CLIP + " · EYE: " + credit("eye")[13:], gobo=False))

k = "email"   # plant 1 is in the narration only; the line is read flat and nothing lands on screen while it is said
tyw = 900; tyh = hgt("typewriter", tyw)
drafts = "".join(cut("ball", bw_, x, y, an("drop", k, t_, .35), rot=r, z=24, data=f'data-dx="{dx}" data-dy="{dy}"')
                 for bw_, x, y, r, t_, dx, dy in ((230, 1440, 600, 14, 1.3, -520, -300), (190, 1560, 770, -30, 2.3, -640, -420), (210, 250, 470, -12, 3.2, 520, -240)))
put("c_email", page(
    a(disc(820, CO), 550, 180, "z-index:4") + A(W(ring(950, SL, "18 16", 4), "spin 0 1", 'data-deg="18"'), 485, 115, "snap 0 0", "z-index:5")
    + A(sheet(mono("ELECTRONIC MAIL · CARBON COPY · DRAFT", 17, CO, 4) + f'<div style="height:4px;background:{CO};margin:12px 0 20px"></div>'
              + mono("FROM: &nbsp;&nbsp;&nbsp;[BLUE CAR]", 26) + mono("TO: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;THE INSURER", 26) + mono("SUBJECT: RE: RE: RE: THE PARKED CAR", 26)
              + f'<div style="height:3px;background:rgba(43,108,176,.4);margin:16px 0 18px"></div>'
              + f'<div style="font:500 36px/1.4 Mono;color:{SL};letter-spacing:1px;white-space:nowrap">To whom it may concern,<br><span style="position:relative;display:inline-block;vertical-align:bottom;height:50px">'
                f'<span data-anim="{an("type", k, said(k, .66), 1.2)}" data-n="20" data-ls="1" style="display:inline-block;overflow:hidden;white-space:nowrap;vertical-align:bottom;height:50px">it was barely a bump</span>'
                f'<span data-anim="{an("growx", k, end(k, .12), .3)}" style="position:absolute;left:-8px;right:-8px;top:50%;height:7px;background:{RED}"></span></span>'
                f'<span style="display:inline-block;width:20px;height:40px;background:{AM};margin-left:12px;vertical-align:bottom;margin-bottom:5px"></span></div>', 740, 620, -1, pad=40),
        590, -70, an("drop", k, .05, .5), "z-index:10", 'data-dx="0" data-dy="420"')
    + cut("typewriter", tyw, 510, 318, "snap 0 0", z=20, boil=0) + drafts
    + cut("car_blue", 330, 96, 720, an("drop", k, .3, .4), rot=-7, z=30, data='data-dx="-500" data-dy="0"') + A(label("THE AUTHOR", 18, SL, PAPER, -5), 150, 860, an("pop", k, .8, .2), "z-index:40")
    + A(label("DRAFTS 1 TO 13", 20, SL, PAPER, 4), 1456, 546, an("pop", k, 2.7, .2), "z-index:40")
    + A(label("DRAFT 14 · UNSENT", 28, AM, SL, 4), 1380, 300, an("slam", k, end(k, .62), .1), "z-index:60") + bar(k),
    credit("typewriter", "car_blue", "ball") + " · SIGHT GAG"))

ticks = "".join(f'<div class="a" style="left:{i * 32}px;top:{650 if i % 10 else 636}px;width:{3 if i % 10 else 6}px;height:{26 if i % 10 else 54}px;background:rgba(20,24,36,.6);z-index:12"></div>' for i in range(1, 60))
nums = "".join(f'<div class="a" style="left:{i * 32 - 22}px;top:700px;font:500 26px Mono;color:{SL};z-index:12">{i}</div>' for i in range(10, 60, 10))
MW = 660; MH = hgt("magnifier", MW); SWW = 290; SWH = hgt("stopwatch", SWW)


def bigbar(key, extra):
    """The bar itself, huge, under a real magnifier, with a real stopwatch on the same second: the same minute, the same place on it (so the thin bar is left off these two pages)."""
    p0, p1 = K[key]["p0"], K[key]["p1"]
    lens = (f'<div style="position:absolute;left:{MW * .2 - 90:.0f}px;top:{MH * .37 - 42:.0f}px;width:180px;text-align:center;font:500 74px/1 Mono;color:{SL}">'
            f'<span data-anim="num 0 1" data-from="{p0 * 60:.2f}" data-to="{p1 * 60:.2f}">0</span><span style="font-size:28px"> S</span></div>')
    watch = (f'<div style="position:relative;width:{SWW}px;height:{SWH}px"><img src="/assets/real2/stopwatch.png" style="width:{SWW}px;height:{SWH}px;filter:drop-shadow(8px 10px 0 rgba(20,24,36,.22))">'
             f'<div data-anim="turn 0 1" data-a0="{p0 * 360:.1f}" data-a1="{p1 * 360:.1f}" style="position:absolute;left:{SWW * .482 - 4:.0f}px;top:{SWH * .63 - SWW * .33:.0f}px;width:8px;height:{SWW * .33:.0f}px;'
             f'background:{AM};transform-origin:50% 100%;border-radius:4px"></div>'
             f'<div style="position:absolute;left:{SWW * .482 - 9:.0f}px;top:{SWH * .63 - 9:.0f}px;width:18px;height:18px;border-radius:50%;background:{SL}"></div></div>')
    return page(a(f'<div style="width:1920px;height:230px;background:rgba(20,24,36,.07);border-top:5px solid {SL};border-bottom:5px solid {SL};box-sizing:border-box"></div>', 0, 410, "z-index:10")
                + f'<div class="a" data-anim="bar 0 1" data-p0="{p0:.5f}" data-p1="{p1:.5f}" data-w="1920" style="left:0;top:415px;height:220px;background:{AM};z-index:11;mix-blend-mode:multiply;'
                  f'clip-path:polygon(0 0,99.3% 0,100% 12%,99.4% 26%,100% 41%,99.2% 55%,100% 70%,99.4% 85%,100% 100%,0 100%)"></div>' + ticks + nums
                + f'<div class="a" data-anim="move 0 1" data-dx="{-(p1 - p0) * 1920:.1f}" style="left:{p1 * 1920 - MW * .2:.0f}px;top:{525 - MH * .37:.0f}px;z-index:50">'
                  f'<img src="/assets/real2/magnifier.png" style="width:{MW}px;height:{MH}px;filter:drop-shadow(10px 12px 0 rgba(20,24,36,.22))">{lens}</div>'
                + a(disc(330, CO), 1512, 56, "z-index:5") + a(watch, 1532, 14, "z-index:40") + a(dots(520, 300, SL, 18, 2.4, .3), 760, 70, "z-index:4") + extra,
                credit("magnifier", "stopwatch") + " · THE 60 SECONDS RUN FROM THE FIRST WORD TO THE TEST")


put("c_bar", bigbar("bar", A(label("YOUR MINUTE", 44, SL, PAPER, -3), 96, 190, an("slam", "bar", .25, .1), "z-index:60") + arrow(520, 250, 640, 400, an("draw", "bar", .45, .3), SL, 8, 30)))
put("c_rehearse", bigbar("rehearse", a(label("YOUR MINUTE", 44, SL, PAPER, -3), 96, 190, "z-index:60") + arrow(520, 250, 640, 400, "snap 0 0", SL, 8, 30)
                                     + A(marker("don't rehearse.", 118, SL, -3), 110, 745, an("wipe", "rehearse", .05, .55), "z-index:60")
                                     + A(label("I CAN'T SEE YOU. I'LL KNOW.", 26, AM, SL, 2), 1150, 800, an("slam", "rehearse", said("rehearse", .74), .1), "z-index:60")))

S_SURE = "THE FEELING OF BEING SURE IS KEPT AS AN EXHIBIT · IT RETURNS LATER IN THE FILM"
S_PHREN = "ENGRAVING FROM \"NEW ILLUSTRATED SELF-INSTRUCTOR IN PHRENOLOGY AND PHYSIOLOGY\" (RAWPIXEL, CC0): A SIGHT GAG, NOT EVIDENCE"
PHW = 820; PHH = hgt("head_phren", PHW); PX, PY = 1096, 170; EX, EY = PX + .835 * PHW, PY + .172 * PHH     # the head, and the patch of it lettered "Self-Esteem"
TGW = 600; TGH = hgt("tag", TGW)


def sure(m):
    """m: the frame builds (the first of the two shots); otherwise it is the finished frame, for the second shot to add to."""
    P_ = lambda html, x, y, anim, extra="": A(html, x, y, anim, extra) if m else a(html, x, y, extra)
    grow = f'data-anim="{an("growx", "sure", said("sure", .55) + .2, .5)}"' if m else ""
    swipe = f'<div {grow} style="width:900px;height:100px;background:{AM};mix-blend-mode:multiply"></div>'
    return (a(disc(800, CO), 1110, 150, "z-index:5") + a(dots(520, 300, SL, 18, 2.4, .3), 90, 640, "z-index:4")
            + P_(mono("SOME OF YOU ARE ALREADY", 40, SL, 6), 100, 96, an("wipe", "sure", .05, .7), "z-index:10")
            + a(swipe, 96, 418, "z-index:8") + P_(serif("SURE.", 338), 100, 196, an("slam", "sure", said("sure", .55), .12), "z-index:12")
            + (cut("head_phren", PHW, PX, PY, an("drop", "sure", .1, .45), z=30, boil=T("sure", .8), data='data-dx="900" data-dy="0"') if m else cut("head_phren", PHW, PX, PY, "snap 0 0", z=30, boil=0))
            + loop(EX, EY, 108, 60, an("draw", "sure", said("sure", .62), .4) if m else "snap 0 0", AM, 9, 4)
            + P_(label("SELF-ESTEEM", 26, AM, SL, 3), 1330, 56, an("qslam", "sure", said("sure", .8), .1), "z-index:61")
            + arrow(1580, 106, EX - 56, EY - 64, an("draw", "sure", said("sure", .85), .2) if m else "snap 0 0", SL, 6, -20))


put("c_sure", page(sure(True) + bar("sure"), S_PHREN + " · " + S_SURE))
put("c_hold", page(sure(False)
                   + A(W(f'<div style="position:relative;width:{TGW}px;height:{TGH}px;transform:rotate(6deg)"><img src="/assets/real2/tag.png" style="width:{TGW}px;height:{TGH}px;filter:saturate(.62) drop-shadow(9px 11px 0 rgba(20,24,36,.22))">'
                         + a(mono("EXHIBIT C", 40, SL, 5) + mono("KEEP", 24, CO, 8), int(TGW * .5), int(TGH * .3)) + '</div>', f"boil {T('hold', .6):.4f} 1", 'data-a=".3" data-px="1.2" data-n="40"'),
                       1290, 700, an("drop", "hold", .1, .4), "z-index:60", 'data-dx="400" data-dy="-300"')
                   + A(marker("hold on to<br>that feeling.", 84, SL, -2), 104, 640, an("wipe", "hold", .2, .8), "z-index:40") + bar("hold"), credit("tag") + " · " + S_PHREN + " · " + S_SURE))
S_FOLD = "THE STUDIES ARE NAMED AFTER THE TEST · 1959 TO 2026 IS 67 YEARS"
files = lambda when="": (A(plate("files", 800, 900, 2, "24% 50%", "PAPERWORK"), 1030, 60, when, "z-index:10", 'data-dx="0" data-dy="900"') if when else a(plate("files", 800, 900, 2, "24% 50%", "PAPERWORK"), 1030, 60, "z-index:10"))
put("c_folders", page(a(block(860, 960, CO, -2), 1000, 40, "z-index:4") + files(an("drop", "folders", .05, .7))
                      + A(label("PAPERWORK SINCE 1959", 30, SL, PAPER, -3), 100, 110, an("qslam", "folders", said("folders", .3), .1), "z-index:40")
                      + A(serif("67", 470, AM), 80, 150, an("slam", "folders", said("folders", .64), .1), "z-index:12") + A(bebas("YEARS", 250), 100, 610, an("slam", "folders", said("folders", .64) + .12, .1), "z-index:12")
                      + bar("folders"), credit("files") + " · " + S_FOLD))
put("c_later", page(a(block(860, 960, CO, -2), 1000, 40, "z-index:4") + files() + a(label("PAPERWORK SINCE 1959", 30, SL, PAPER, -3), 100, 110, "z-index:40")
                    + A(bebas("YOU'LL GET", 200), 96, 200, an("wipe", "later", .2, .35), "z-index:12") + A(bebas("ALL OF IT", 200), 96, 372, an("wipe", "later", .5, .3), "z-index:12")
                    + A(marker("after you've<br>fallen for it.", 96, CO, -2), 106, 590, an("wipe", "later", said("later", .44), .8), "z-index:12")
                    + A(f'<div style="width:300px;height:250px;box-sizing:border-box;background:{AM};padding:26px 20px;transform:rotate(5deg);box-shadow:8px 10px 0 rgba(20,24,36,.25);font:400 100px/1 Marker;color:{SL}">LATER.</div>',
                        1300, 40, an("slam", "later", end("later", .1), .1), "z-index:60") + bar("later"), credit("files") + " · " + S_FOLD))

# ---- the test: the lights go down ------------------------------------------------------------------------------------------------
S_TEST = "THE TEST: YES OR NO, OUT LOUD · THE STUDY IS NAMED AFTER THE TEST"
HW = 1600; HH = hgt("hand_sign", HW); IX0, IX1, IY0, IY1 = .367 * HW, .961 * HW, .073 * HH, .920 * HH


def held(inner, w=HW):
    """The pointing hand holding its card, w px wide; inner sits on the card."""
    h = hgt("hand_sign", w); x0, x1, y0, y1 = .367 * w, .961 * w, .073 * h, .920 * h
    return (f'<div style="position:relative;width:{w}px;height:{h}px">' + a(card(inner, int(x1 - x0) + 12, int(y1 - y0) + 12, 0, pad=16), int(x0) - 6, int(y0) - 6)
            + f'<img src="/assets/real2/hand_sign.png" style="position:absolute;left:0;top:0;width:{w}px;height:{h}px;filter:drop-shadow(9px 11px 0 rgba(0,0,0,.4))"></div>')


BSW = 610; BSH = hgt("bus", BSW)
bubble = (f'<div style="position:relative;background:{WHITE};padding:12px 26px;font:400 70px/1 Bebas;letter-spacing:3px;color:{SL};{SH}">YES.'
          f'<div style="position:absolute;left:30px;bottom:-24px;border:13px solid transparent;border-top-color:{WHITE};border-left-color:{WHITE}"></div></div>')
put("c_test", page(
    A(bebas("TIME.", 340, PAPER), 100, 40, an("slam", "test1", .05, .1), "z-index:10") + A(serif("three words.", 94, AM, True), 112, 372, an("fade", "test1", said("test1", .2), .08), "z-index:10")
    + A(held(f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%">{mono("WAS IT ON MY LIST?", 26, CO, 4)}<div style="height:18px"></div>{serif("YES / NO?", 118)}</div>', 1150),
        680, 250, an("drop", "test1", said("test1", .5), .3), "z-index:20", 'data-dx="1500" data-dy="0"')
    + cut("bus", BSW, 40, 640, an("drop", "test2", said("test2", .52), .5), z=30, data='data-dx="-1100" data-dy="0"', boil=T("test2", said("test2", .8)))
    + A(bubble, 450, 540, an("pop", "test2", said("test2", .88), .2), "z-index:60")
    + bar("later", dark=True, full=True, more=A(stamp("FULL", 60, -6), 1612, 893, an("slam", "test1", .05, .1))), credit("hand_sign", "bus") + " · " + S_TEST, dark=True))
# three words, one hand, one card, one plain style: nothing on screen tips the answer. A projector click, then the word is said.
FIT = int(min((IY1 - IY0) * .56, (IX1 - IX0) * .84 / (5 * .6 + 4 * .09)))
for n_, w_ in enumerate(("DREAM", "DOOR", "SLEEP")):
    put(f"c_t_{w_.lower()}", page(a(label(f"WORD {n_ + 1} OF 3 · WAS IT ON MY LIST?", 30, PAPER, SL), 90, 70, "z-index:40")
                                  + a(held(CENTER(f'<div data-anim="{an("click", f"tw{n_ + 1}", .05)}" style="font:500 {FIT}px/1 Mono;color:{SL};letter-spacing:{FIT * .09:.0f}px;margin-right:-{FIT * .09:.0f}px">{w_}</div>')), 40, 150, "z-index:20")
                                  + a(label("YES OR NO. OUT LOUD.", 30, AM, SL, -2), 96, 930, "z-index:40"), credit("hand_sign") + " · " + S_TEST, dark=True))

# ---- the reveal: three engraved hands hold up the three answers ------------------------------------------------------------------
mk = lambda col: (f'<svg width="150" height="130" viewBox="0 0 150 130"><path d="M14 70 L58 112 L136 16" fill="none" stroke="{col}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/></svg>',
                  f'<svg width="130" height="130" viewBox="0 0 130 130"><path d="M16 16 L114 114 M114 16 L16 114" fill="none" stroke="{col}" stroke-width="24" stroke-linecap="round"/></svg>')
HU = 560; HUH = hgt("hand_up", HU); HX = (70, 680, 1290); HY = (270, 310, 260)


def holder(i, w_, mark="", when="", wanim="", dark=True):
    """One of the three hands, holding up a test word with its verdict on the corner. The middle hand is mirrored."""
    flip = i == 1; cx0 = (1 - .926 if flip else .247) * HU; cw = .679 * HU; cy0 = .037 * HUH; ch = .263 * HUH
    img = (f'<img src="/assets/real2/hand_up.png" style="width:{HU}px;height:{HUH}px;display:block;{"transform:scaleX(-1);" if flip else ""}'
           f'filter:drop-shadow(9px 11px 0 rgba({"0,0,0,.4" if dark else "20,24,36,.2"}))">')
    wd = f'<div {wanim} style="font:500 84px/1 Mono;color:{SL};letter-spacing:8px;margin-right:-8px">{w_}</div>' if w_ else ""
    mk_ = f'<div {when} style="position:absolute;left:{cx0 - 50:.0f}px;top:{cy0 - 64:.0f}px">{mark}</div>' if mark else ""
    return (f'<div style="position:relative;width:{HU}px;height:{HUH}px;transform:rotate({(-3, 2, 4)[i]}deg);transform-origin:50% 25%">{img}'
            + a(CENTER(wd), int(cx0), int(cy0), f"width:{cw:.0f}px;height:{ch:.0f}px") + mk_ + '</div>')


da = lambda s_: f'data-anim="{s_}"'
tick, cross = mk(AM)
k = "cards"
notes = A(marker("on the list.", 58, PAPER, -3), 150, 136, an("wipe", k, said(k, .3), .4), "z-index:22") + A(marker("not on it.", 58, PAPER, 2), 760, 176, an("wipe", k, said(k, .84), .3), "z-index:22")
put("c_cards", page(
    A(holder(0, "DREAM", tick, da(an("pop", k, said(k, .27), .15))), HX[0], HY[0], an("drop", k, 0, .25), "z-index:20", 'data-dx="0" data-dy="760"')
    + A(holder(1, "DOOR", cross, da(an("pop", k, said(k, .8), .15))), HX[1], HY[1], an("drop", k, .07, .25), "z-index:20", 'data-dx="0" data-dy="760"')
    + A(holder(2, "SLEEP"), HX[2], HY[2], an("drop", k, .14, .25), "z-index:20", 'data-dx="0" data-dy="760"') + notes,
    credit("hand_up") + " · " + S_REV, dark=True))
put("c_reveal", page(
    a(holder(0, "DREAM", tick), HX[0], HY[0], "z-index:20") + a(holder(1, "DOOR", cross), HX[1], HY[1], "z-index:20")
    + a(holder(2, "SLEEP", wanim=da(an("flipout", "never", .1, .22))), HX[2], HY[2], "z-index:20")
    + A(ink(stamp("NEVER SAID", 54, -9)), 1420, 366, an("slam", "never", end("never", -.1), .1), "z-index:60"), credit("hand_up") + " · " + S_REV, dark=True))
tick2, cross2 = mk(CO)
put("c_reveal2", page(
    a(block(1860, 330, CO, -1), 30, 320, "z-index:4")
    + a(holder(0, "DREAM", tick2, dark=False), HX[0], HY[0], "z-index:20") + a(holder(1, "DOOR", cross2, dark=False), HX[1], HY[1], "z-index:20") + a(holder(2, "", dark=False), HX[2], HY[2], "z-index:20")
    + a(ink(stamp("NEVER SAID", 54, -9)), 1420, 366, "z-index:60")
    + A(bebas("I NEVER SAID IT.", 230), 84, 26, an("slam", "notonce", .06, .1), "z-index:10")
    + cut("stamp_side", 400, 1470, 36, an("qdrop", "notonce", .3, .3), rot=-12, z=62, data='data-dx="300" data-dy="-400"', boil=T("scroll", .1))
    + A(label(f"REWIND TO {REWIND}", 36, SL, PAPER, -2), 560, 720, an("slam", "scroll", .12, .1), "z-index:60") + A(label("PAUSED", 36, AM, SL, 3), 1090, 806, an("drop", "scroll", said("scroll", .74), .3), "z-index:60")
    + arrow(540, 752, 300, 752, an("draw", "scroll", .45, .5), AM, 10, -22), credit("hand_up", "stamp_side") + " · " + S_REV))

# ---- after the reveal: sources are named from here on ---------------------------------------------------------------------------------
k1, k2, k3 = "maj1", "maj2", "maj3"
studycard = lambda who, where, note="": (f'<div style="width:640px;box-sizing:border-box;background:{WHITE};padding:22px 26px 24px;{SH};transform:rotate(-1.5deg);border-left:14px solid {CO};position:relative">'
                                         f'<div style="font:500 15px Mono;letter-spacing:5px;color:{CO}">STUDY CARD</div><div style="font:900 40px/1.04 Fraunces9;color:{SL};margin-top:8px">{who}</div>'
                                         f'<div style="font:400 30px/1.1 FrauncesI;color:#33405A;margin-top:8px">{where}</div>'
                                         + (f'<div style="display:inline-block;margin-top:12px;background:{SL};color:{PAPER};font:500 14px Mono;letter-spacing:2px;padding:5px 10px">{note}</div>' if note else "") + '</div>')
put("c_majority", page(
    a('<img src="/assets/real2/crowd.jpg" style="width:1920px;height:1080px;object-fit:cover;display:block">', 0, 0, "z-index:3")
    + a(f'<div style="width:1920px;height:1080px;background-image:radial-gradient(rgba(20,24,36,.45) 1.4px,transparent 1.9px);background-size:8px 8px;mix-blend-mode:multiply"></div>', 0, 0, "z-index:4")
    + A(f'<div data-anim="{an("growx", k2, said(k2, .58), .9)}" style="width:1560px;height:1080px;background:{AM};clip-path:polygon(0 0,97% 0,100% 8%,97.5% 17%,100% 27%,98% 38%,100% 49%,97.5% 60%,100% 71%,98% 82%,100% 92%,97.5% 100%,0 100%)"></div>',
        0, 0, "snap 0 0", "z-index:5;mix-blend-mode:multiply")
    + A(f'<div style="width:0;height:1080px;border-left:6px dashed {WHITE}"></div>', 1536, 0, an("fade", k2, said(k2, .58) + .8, .2), "z-index:6")
    + A(label("80% OF THE WAY ACROSS", 18, WHITE, SL, 0), 1380, 40, an("fade", k2, said(k2, .58) + .8, .2), "z-index:7")
    + A(studycard("Stadler, Roediger &amp; McDermott", "Memory &amp; Cognition, 1999", "NORMS FOR THE WORD LISTS"), 70, 60, an("drop", k1, 0, .35), "z-index:40", 'data-dx="-700" data-dy="0"')
    + A(W(torn(1250, 300, WHITE, 3) + a(bebas("THE MAJORITY.", 250), 44, 30), an("slam", k1, said(k1, .5), .1), "", "position:relative"), 70, 420, an("hide", k2, said(k2, .49)), "z-index:40")
    + A(W(torn(1180, 560, WHITE, 5) + a(bebas("MORE THAN", 150), 50, 34) + a(serif("80%", 400, AM), 40, 150), an("slam", k2, said(k2, .5), .12), "", "position:relative"), 70, 380, "hide 0.9005 0.9005", "z-index:41")
    + A(label("SAID YES TO \"SLEEP\"", 34, SL, PAPER, -2), 740, 850, an("slam", k2, said(k2, .86), .1), "z-index:42")
    + A(label("SAID YES", 26, AM, SL, 2), 1160, 300, an("qsnap", k3, 0), "z-index:42")
    + A(label("THE REST SAID NO", 26, WHITE, SL, -2), 1548, 430, an("slam", k3, said(k3, .2), .1), "z-index:42") + arrow(1690, 500, 1750, 600, an("draw", k3, said(k3, .3), .3), WHITE, 7, 16),
    credit("crowd") + " (A CROWD, NOT THE STUDY'S PEOPLE) · STADLER, ROEDIGER & McDERMOTT 1999: FALSE RECOGNITION OF \"SLEEP\" ABOVE 80% · THE TINT ENDS AT THE 80% LINE; THE EXACT VALUE IS NOT SHOWN", gobo=False))

k = "title"
thumb = (f'<div style="position:relative;width:1060px;height:596px;background:{PAPER};overflow:hidden;border-radius:16px;border:6px solid {SL}">'
         + a(disc(520, CO), 560, 40) + f'<img src="/assets/real2/head_brain.png" style="position:absolute;left:520px;top:-10px;width:540px">'
         + a(bebas("GIVE ME", 150), 40, 26) + a(bebas(f'<span style="color:{AM}">60</span> SECONDS', 150), 40, 158)
         + f'<div style="position:absolute;left:0;right:0;bottom:0;height:8px;background:rgba(20,24,36,.25)"><div style="width:86%;height:8px;background:{RED}"></div></div></div>')
put("c_title", page(
    a(block(1180, 700, CO, 2), 370, 40, "z-index:4") + A(thumb, 430, 60, an("drop", k, 0, .3), "z-index:10", 'data-dx="0" data-dy="-500"')
    + A(f'<div style="font:800 54px/1.15 Inter8;color:{SL};white-space:nowrap">Can I Give You a False Memory in 60 Seconds?</div><div style="display:flex;align-items:center;gap:16px;margin-top:16px">'
        f'<div style="width:50px;height:50px;border-radius:50%;background:{CO}"></div><div style="font:400 28px Inter4;color:#33405A">Dragon Psychology</div></div>', 300, 720, an("up", k, .15, .3), "z-index:12")
    + loop(945, 752, 700, 62, an("draw", k, said(k, .56), .5), RED, 10, 5)
    + A(label("IT'S IN THE TITLE", 26, SL, PAPER, -4), 96, 420, an("qpop", k, said(k, .5), .2), "z-index:40") + arrow(230, 490, 290, 700, an("draw", k, said(k, .6), .3), SL, 7, 40)
    + A(ink(stamp("PROBABLY", 96, -8)), 1090, 810, an("slam", k, end(k, .1), .1), "z-index:60"),
    credit("head_brain") + " · A RECREATION OF THIS VIDEO'S OWN PAGE · WARNINGS REDUCE THE EFFECT BUT DO NOT REMOVE IT (GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998)"))

k = "warn"
UW = 500; UH = hgt("hand_up", UW)
put("c_warning", page(
    A(studycard("Gallo, Roberts &amp; Seamon", "Psychonomic Bulletin &amp; Review, 1997"), 80, 70, an("drop", k, 0, .3), "z-index:40", 'data-dx="-700" data-dy="0"')
    + A(bebas("WARNINGS", 230), 86, 330, an("slam", k, .06, .1), "z-index:10") + A(bebas("SHRINK IT.", 230), 86, 528, an("slam", k, .3, .1), "z-index:10")
    + A(serif("They don't remove it.", 86, CO, True), 92, 760, an("wipe", k, said(k, .66), .5), "z-index:10")
    + a(f'<div style="display:flex;gap:64px;align-items:flex-end;border-bottom:8px solid {SL};height:600px;padding:0 36px">'
        f'<div style="width:200px;height:520px;background:#8794A8;clip-path:polygon(0 3%,20% 0,45% 4%,70% 1%,100% 4%,100% 100%,0 100%)"></div>'
        f'<div data-anim="{an("grow", k, .3, .8)}" style="width:200px;height:300px;background:{AM};clip-path:polygon(0 5%,25% 0,50% 6%,78% 1%,100% 6%,100% 100%,0 100%)"></div></div>'
        f'<div style="display:flex;gap:64px;padding:12px 36px 0;font:500 21px Mono;letter-spacing:3px;color:{SL}"><div style="width:200px;text-align:center">NOT WARNED</div><div style="width:200px;text-align:center">WARNED</div></div>', 890, 150, "z-index:12")
    + a(label("BAR SIZES ILLUSTRATIVE · DIRECTION AS REPORTED", 16, WHITE, SL), 906, 850, "z-index:12")
    + A(f'<div style="position:relative;width:{UW}px;height:{UH}px"><img src="/assets/real2/hand_up.png" style="width:{UW}px;height:{UH}px;{HSH}">'
        + a(CENTER(serif("WARNING", 48, RED)), int(UW * .247), int(UH * .037), f"width:{int(UW * .68)}px;height:{int(UH * .263)}px") + '</div>', 1400, 330, an("drop", k, .56, .4), "z-index:30", 'data-dx="0" data-dy="800"'),
    credit("hand_up") + " · GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998 · NO VALUES ARE SHOWN: THE DOSSIER HOLDS THE DIRECTION, NOT THE SIZE"))

k1, k2 = "env1", "env2"
EW = 760; EH = hgt("envelope", EW)
put("c_envelope", page(
    a(disc(900, CO), 510, 90, "z-index:4") + A(W(ring(1030, SL, "18 16", 4), "spin 0 1", 'data-deg="20"'), 445, 25, "snap 0 0", "z-index:5")
    + cut("envelope", EW, 580, 110, an("drop", k1, 0, .35), rot=-4, z=20, boil=T(k1, .6), data='data-dx="0" data-dy="-700"')
    + A(label("A SECOND FALSE MEMORY", 32, AM, SL, -3), 90, 90, an("slam", k1, said(k1, .5), .1), "z-index:60")
    + A(ink(stamp("EXHIBIT B", 110, -7)), 640, 330, an("slam", k1, said(k1, .9), .1), "z-index:60")
    + cut("stamp_side", 420, 1320, 660, an("drop", k1, end(k1, .0), .2), rot=10, z=58, data='data-dx="300" data-dy="-300"')
    + A(label("NOT A WORD", 30, SL, PAPER, -2), 650, 640, an("slam", k2, .1, .1), "z-index:60")
    + A(label("OPEN AT THE END", 36, SL, PAPER, 3), 900, 740, an("slam", k2, said(k2, .7), .1), "z-index:60"),
    credit("envelope", "stamp_side") + " · THE SECOND TEST IS COLLECTED AT THE END OF THE FILM"))

# ---- the trap's rules, checked on what was just written ---------------------------------------------------------------------------------
H = D / "html"
visible = lambda pg: __import__("re").sub(r"<style.*?</style>|<script.*?</script>|<[^>]+>", " ", (H / f"{pg}.html").read_text(), flags=16).upper()   # the text a viewer could read
for pg in dict.fromkeys(s["page"] for s in S[:S.index(K["tw3"])]):
    assert "SLEEP" not in visible(pg), f'"sleep" is on {pg}, before the third test word'
for pg in dict.fromkeys(s["page"] for s in S[:S.index(K["cards"])]):
    for bad in ("ROEDIGER", "MCDERMOTT", "DEESE", "LOFTUS", "MISSING WORD", "ASSOCIATES", "FALSE RECOGNITION", "DRM"):
        assert bad not in visible(pg), f"{bad} is on {pg}, before the reveal"
for pg in dict.fromkeys(s["page"] for s in S):
    for bad in ("STOP SIGN", " STOP ", "GIVE WAY", "GIVE-WAY", "YIELD", "CAR CLIP"):
        assert bad not in visible(pg), f"{bad.strip()} is on {pg}: no sign is named on screen, and nothing points at the clip"
assert not any("sleep" in s["vo"].lower() for s in S[:S.index(K["tw3"])]), '"sleep" is said before the third test word'
assert all(s.get("nocap") for s in S if "stop sign" in s["vo"].lower()), "a line that says \"stop sign\" would be captioned: the plant is never on screen"
print("pages written:", len({s["page"] for s in S}), "· trap rules hold: no \"sleep\" before the third test word, no study named before the reveal, no sign named on any page")
