"""The opening test: act 0 of SCRIPT.md, from 0:00 to "So how did I do that?" (owner's go, 2026-11-20).

Writes video/shots.json and every page the cut uses. The pages are the key frames' layouts, rebuilt here so each thing lands on the word that
names it; the times come from the recorded voice.

Three rules of the trap decide what may be on screen before the reveal (they are checked at the bottom of this file):
  1. "sleep" is never said or shown before the third test word;
  2. nothing names the study, the effect or the missing word before the reveal, not even the source line (it would be an answer key);
  3. nothing names a road sign, and nothing says the second test is the car clip.

Two passes, because the 60-second promise has to be exact:
  1. python3 opening.py                           shots.json and pages, timed from estimates
  2. film_video.py <film> --voice-only            records the voice
  3. python3 opening.py                           pauses set so the test starts 60.0 s after the first word; every animation timed to the voice
  4. python3 preview.py                           the first and last frame of every shot, on check sheets
  5. film_video.py <film> --workers 3             the video
The wording is SCRIPT.md's, unchanged. Two lines are split in two at a full stop, so each half gets its own shot."""
import json
import math
import wave
from pathlib import Path

from kit import (A, a, put, page, big, mono, tag, hand, stamp, sheet, icard, sticky, study, photo, ring, arrow, crowd, hl, SL, PAPER, CO, AM, RED, INK, DIM, SH)
import props as P

D = Path(__file__).resolve().parent
V = D / "video"; V.mkdir(exist_ok=True)
FPS, WORD_FRAMES, MINUTE, CLIP, AFTER = 24, 34, 60 * 24, (53, 24), 45   # 34 frames = 1.42 s a word; the minute is 1,440 frames; the clip: follow 53 frames, push in 24, then 45 silent on the bump
VOICE, SPEED = "af_heart", 1.1
WORDS = ["Bed", "Rest", "Awake", "Tired", "Dream", "Wake", "Snooze", "Blanket", "Doze", "Slumber", "Snore", "Nap", "Peace", "Yawn", "Drowsy"]
CENTER = lambda inner: f'<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%">{inner}</div>'
STILL = [1.0, .5, .5, 1.0, .5, .5]

# ---- the shot plan ---------------------------------------------------------------------------------------------------------
# zone "list" and "gap" make up the minute; w = a gap shot's share of the minute's spare time; fix = a silent shot's length in frames;
# tail = seconds the page keeps building after the line ends (for a stamp that lands in the pause)
S, K = [], {}


def shot(key, vo, pg, t=(0, 1), cam=None, beat=1, zone="", **kw):
    s = {"id": f"0.{len(S) + 1:02d}", "beat": beat, "vo": vo, "page": pg, "t": [round(x, 4) for x in t], "cam": list(cam or [1.0, .5, .5, 1.05, .5, .5]), "zone": zone, **kw}
    S.append(s); K[key] = s


shot("hook1", "Give me sixty seconds. I'm going to put a memory in your head.", "v_01_hook", (0, .29), [1.0, .5, .5, 1.06, .48, .46], post=.15)   # stops short of .3, where the page changes for shot 2
shot("hook2", "Of something that never happened.", "v_01_hook", (.3, .55), [1.5, .531, .542, 1.56, .531, .542], post=.2)
shot("hook3", "If it works, you won't feel a thing. You'll just be sure.", "v_01_hook", (.55, 1), [1.36, .585, .54, 1.4, .59, .545], post=.4)
shot("court", "And this same glitch has helped put innocent people in prison.", "v_02_court", (0, 1), [1.0, .5, .5, 1.06, .56, .5], post=.6, tail=.45)
shot("instr", "Fifteen words. Don't write them down.", "v_03_instr", (0, 1), [1.0, .5, .5, 1.04, .5, .5], post=.5)
for i, w in enumerate(WORDS):
    shot(f"w{i + 1}", f"{w}.", f"m_w{i + 1:02d}", (0, 1), STILL, beat=2, zone="list", pre=.2, mute=True, nocap=True)
shot("done", "Done. Put those away.", "m_21_done", (0, 1), [1.0, .5, .5, 1.05, .5, .5], beat=2, zone="gap", w=.8)
shot("watch", "Watch this once.", "m_22_watch", (0, 1), [1.05, .5, .5, 1.1, .48, .5], beat=2, zone="gap", w=.5)
shot("clipa", "", "m_23_clip", (0, CLIP[0] / sum(CLIP)), [1.8, .47, .722, 1.8, .47, .4], beat=2, zone="gap", fix=CLIP[0])          # the camera follows the car and stops as it hits
shot("clipb", "", "m_23_clip", (CLIP[0] / sum(CLIP), 1), [1.8, .47, .4, 2.6, .335, .292], beat=2, zone="gap", fix=CLIP[1])          # then pushes in on the bump; the triangle leaves the frame
shot("witness", "Congratulations. You are now a witness.", "m_24_witness", (0, 1), [2.6, .335, .292, 2.45, .323, .292], beat=2, zone="gap", w=1.0, pre=AFTER / FPS)   # the clip's last 1.9 s are this shot's silent start
shot("email", "Somewhere, the owner of the blue car that ran the stop sign is drafting a defensive email.", "m_25_email", (0, 1), [1.0, .5, .5, 1.1, .56, .6], beat=2, zone="gap", w=1.1)
shot("bar", "That amber bar is your minute.", "m_26_bar", (0, 1), [1.0, .5, .5, 1.03, .53, .5], beat=2, zone="gap", w=.5)
shot("rehearse", "Don't rehearse. I can't see you, but I'll know.", "m_27_rehearse", (0, 1), [1.03, .53, .5, 1.06, .5, .54], beat=2, zone="gap", w=.9)
shot("sure", "Some of you are already sure you'll pass.", "m_28_sure", (0, 1), [1.0, .5, .5, 1.06, .44, .44], beat=2, zone="gap", w=.8)
shot("hold", "Hold on to that feeling. We'll need it later.", "m_29_hold", (0, 1), [1.06, .44, .44, 1.08, .5, .54], beat=2, zone="gap", w=1.0)
shot("folders", "This trick has a lab behind it, and nearly seventy years of paperwork.", "m_30_folders", (0, 1), [1.0, .5, .5, 1.05, .53, .5], beat=2, zone="gap", w=.8)
shot("later", "You'll get all of it after you've fallen for it.", "m_31_later", (0, 1), [1.05, .53, .5, 1.0, .5, .5], beat=2, zone="gap", w=1.5, pre=.2, mute=True)
shot("test1", "Time. Three words. Was each one on my list?", "m_32_test", (0, .5), [1.0, .5, .5, 1.04, .5, .52], beat=3, post=.2, mute=True)
shot("test2", "Yes or no, out loud. If you're on a bus, commit.", "m_32_test", (.5, 1), [1.04, .5, .52, 1.04, .5, .46], beat=3, post=.45, mute=True)
for n_, (w, post) in enumerate((("Dream", 1.2), ("Door", 1.2), ("Sleep", 1.5))):
    shot(f"tw{n_ + 1}", f"{w}.", f"t_{w.lower()}", (0, 1), STILL, beat=3, pre=.3, post=post, mute=True, nocap=True)
shot("cards", "Dream was on the list. Door wasn't.", "r_cards", (0, 1), [1.0, .5, .5, 1.04, .5, .5], beat=3, post=.25, mute=True)
shot("sleepq", "And sleep?", "r_cards", (1, 1), [1.6, .755, .47, 2.0, .755, .47], beat=3, post=.45, mute=True)
shot("never", "I never said it.", "r_reveal", (0, .5), [2.0, .755, .47, 2.1, .755, .47], beat=3, post=.3, mute=True)
shot("notonce", "Not once.", "r_reveal", (.5, .7), [1.0, .5, .5, 1.04, .5, .5], beat=3, post=.6, mute=True)
shot("scroll", "Scroll back and check. I'm a video. I can wait.", "r_reveal", (.7, 1), [1.04, .5, .5, 1.08, .5, .5], beat=3, post=.5)
shot("maj1", "Said yes? You're the majority.", "v_13_majority", (0, .2), [1.0, .5, .5, 1.05, .42, .5], beat=3, post=.15)
shot("maj2", "When researchers tested this exact list, more than 80 percent of people said yes to \"sleep\".", "v_13_majority", (.2, .9), [1.05, .42, .5, 1.08, .5, .5], beat=3, post=.35)
shot("title", "And I warned you. It's in the title.", "v_14_title", (0, 1), [1.0, .5, .5, 1.07, .52, .54], beat=3, post=.6, tail=.3)
shot("warn", "Warnings shrink the effect. They don't remove it.", "v_15_warning", (0, 1), [1.0, .5, .5, 1.04, .5, .5], beat=3, post=.3)
shot("maj3", "If you said no, well done. It doesn't work on everyone.", "v_13_majority", (.9, 1), [1.9, .83, .24, 2.0, .83, .2], beat=3, post=.35)
shot("env1", "But I've already planted a second false memory in this video.", "v_16_envelope", (0, .5), [1.0, .5, .5, 1.08, .5, .5], beat=3, post=.2)
shot("env2", "It isn't a word. I'll collect it at the end.", "v_16_envelope", (.5, 1), [1.3, .6, .66, 1.34, .6, .68], beat=3, post=.35)
shot("env3", "So how did I do that?", "v_16_envelope", (1, 1), [1.34, .6, .68, 1.0, .5, .5], beat=3, post=.9)

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
W = sum(s["w"] for s in talk)
for s, b in zip(talk, need):
    s["frames"] = math.ceil((b + max(.08, spare * s["w"] / W)) * FPS)
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
(V / "shots.json").write_text(json.dumps({"slug": "false-memory-opening-test", "title": "Can I Give You a False Memory in 60 Seconds? (opening test)", "channel": "dragonpsych",
                                          "voice": VOICE, "speed": SPEED, "treatment": "pulse", "guide": {}, "reload_pages": [],
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


def typed(t, size, ls, anim, col=INK):
    """A mono line typed on, key by key."""
    return (f'<div style="font:500 {size}px/1.35 Mono;color:{col};letter-spacing:{ls}px;white-space:nowrap;height:{size * 1.35:.0f}px">'
            f'<span data-anim="{anim}" data-n="{len(t)}" data-ls="{ls}" style="display:inline-block;overflow:hidden;white-space:nowrap;vertical-align:top">{t}</span></div>')


# ---- the 60-second bar: fixed to the screen, not to the page, so it holds still while the camera moves -------------------------------
def hud(inner):
    return f'<div class="a" data-hud style="left:0;top:0;width:1920px;height:1080px;z-index:95;pointer-events:none">{inner}</div>'


BAND = '<div style="width:1920px;height:64px;background:linear-gradient(transparent,rgba(6,8,14,.62) 42%,rgba(6,8,14,.62) 62%,transparent)"></div>'   # keeps the bar readable over pale paper


def bar(key, key2=None, y=1012):
    """The thin amber bar, moving evenly through this shot's share of the minute (key2: the page is shot twice in a row)."""
    p0, p1 = K[key]["p0"], K[key2 or key]["p1"]
    return hud(a(BAND, 0, y - 26)
               + a('<div style="width:1760px;height:14px;background:rgba(240,244,248,.14);border:2px solid rgba(240,244,248,.4);box-sizing:border-box"></div>', 80, y)
               + f'<div class="a" data-anim="bar 0 1" data-p0="{p0:.5f}" data-p1="{p1:.5f}" data-w="1756" style="left:82px;top:{y + 2}px;height:10px;background:{AM}"></div>'
               + a(f'<div style="font:500 15px Mono;letter-spacing:3px;color:{AM}">60 S</div>', 1850, y - 4))


# ---- source lines. Before the reveal they name nothing (see the rules above) ----------------------------------------------------------
S_PRE = "THE 15 WORDS COME FROM A PUBLISHED MEMORY STUDY · IT IS NAMED AFTER THE TEST, SO THE TEST STAYS FAIR"
S_REV = "\"SLEEP\" WAS NEVER SAID OR SHOWN BEFORE THE TEST · THE EFFECT: ROEDIGER & McDERMOTT 1995, J. EXP. PSYCHOL.: LMC · THE LIST: THE STUDY'S 15 ASSOCIATES OF ONE MISSING WORD"

# ---- 0:00 the hook ------------------------------------------------------------------------------------------------------------
t2 = T("hook2", 0)   # at the cut to shot 2 the headline leaves and the card takes the middle of the frame
put("v_01_hook", page(
    f'<div data-anim="hide {t2:.4f} {t2:.4f}">' + A(big("GIVE ME", 230), 96, 84, an("slam", "hook1", .04, .12))
    + A(big(f'<span style="color:{AM}">60</span> SECONDS', 230), 96, 296, an("slam", "hook1", .52, .12)) + '</div>'
    + f'<div class="a" data-anim="move {t2:.4f} {t2:.4f}" data-dy="200" style="left:430px;top:380px"><div data-anim="{an("up", "hook1", said("hook1", .52), .9)}">'
    + icard(mono("FILE: ONE MEMORY", 44, INK, 4) + '<div style="height:36px"></div>' + typed("SUBJECT: NEVER HAPPENED", 50, 3, an("type", "hook2", .08, 1.0))
            + '<div style="height:14px"></div>' + f'<div data-anim="{an("snap", "hook3", .12)}">{mono("STATUS:", 50, INK, 3)}</div>', 1180, 410, 2, pad=48, top=120, line=64) + '</div></div>'
    + A(stamp("CERTAIN", 140, -8), 860, 570, an("slam", "hook3", said("hook3", .84), .1), "z-index:60"),
    "THE CLAIM IS TESTED ON THE VIEWER IN THIS VIDEO · THE STUDY IS NAMED AFTER THE TEST, SO THE TEST STAYS FAIR"))

k = "court"   # the words slam on as they are said; the tag lands in the pause after the line
put("v_02_court", page(
    A(big("INNOCENT<br>PEOPLE.", 104), 1235, 150, an("slam", k, said(k, .54), .1))
    + A(big("IN PRISON.", 92, AM), 1235, 356, an("slam", k, said(k, .8), .1))
    + A(tag("HOLD THAT THOUGHT", 34, amber=True, rot=-3), 1235, 560, an("slam", k, end(k, .1), .1), "z-index:40")
    + A(hand("we come back here.", 70, PAPER, -3), 1250, 700, an("wipe", k, end(k, .15), .28))
    + a(photo("courthouse_front", 1060, 740, -2, "50% 62%", anim="push 0 1"), 70, 96),
    "PHOTO: W_LEMAY, CC0 (ALAMANCE COUNTY, NORTH CAROLINA: THE COUNTY OF A CASE TOLD LATER) · THE FIGURES BEHIND THIS LINE: INNOCENCE PROJECT, DNA EXONERATIONS 1989-2020"))

k = "instr"
put("v_03_instr", page(
    A(big("15", 400, AM), 1300, 130, an("slam", k, .04, .1))
    + A(P.pencil(820, snapped=True), 250, 660, an("slam", k, said(k, .72), .08), "z-index:50;transform-origin:50% 50%")
    + a(sheet(big("PARTICIPANT INSTRUCTIONS", 56, INK) + mono("FORM 15-W · STUDIO RECONSTRUCTION", 20, CO, 4, extra="margin-top:10px")
              + f'<div style="height:5px;background:{INK};margin:26px 0 40px"></div>' + mono("1. YOU WILL HEAR FIFTEEN WORDS.", 42, INK, 2) + '<div style="height:38px"></div>'
              + mono("2. " + hl("DO NOT WRITE THEM DOWN."), 42, INK, 2) + '<div style="height:38px"></div>' + mono("3. THAT IS THE WHOLE TEST.", 42, INK, 2), 1150, 880, -1.2, pad=60), 80, 90)
    + A(big("WORDS", 128), 1306, 540, an("slam", k, .5, .1))
    + A(tag("NO NOTES", 34, inv=True, rot=4), 1320, 740, an("slam", k, said(k, .95), .1)),
    "THE VIEWER'S INSTRUCTIONS (OUR WORDING) · " + S_PRE))

# ---- the list: one word per card, five paper treatments in turn -------------------------------------------------------------------
for i, w in enumerate(WORDS):
    U, n, kind, key = w.upper(), len(w), i % 5, f"w{i + 1}"
    pop = an("pop", key, .03, .14)
    if kind == 0:
        sz = min(330, int((1060 - 26 * n) / (.6 * n)))
        body = A(icard(CENTER(mono(U, sz, INK, 26)), 1180, 640, -1, pad=40, top=110, line=66), 370, 190, pop)
    elif kind == 1:
        sz = min(270, int((1400 - 30 * n) / (.8 * n)))
        body = A(f'<div style="width:1560px;height:360px;background:linear-gradient(#1C2130,#07090E 16%,#07090E 84%,#1C2130);box-shadow:14px 18px 0 rgba(5,7,12,.5);transform:rotate(-2deg);'
                 f'clip-path:polygon(0 0,100% 0,98.6% 16%,100% 33%,98.6% 50%,100% 67%,98.6% 84%,100% 100%,0 100%,1.4% 84%,0 67%,1.4% 50%,0 33%,1.4% 16%)">'
                 + CENTER(f'<div style="font:400 {sz}px/1 Black;letter-spacing:30px;color:{PAPER};text-shadow:0 5px 0 rgba(255,255,255,.28),0 -4px 0 rgba(0,0,0,.9)">{U}</div>') + '</div>', 180, 350, pop)
    elif kind == 2:
        sz = min(250, int((1380 - 18 * n) / (.6 * n)))
        body = A(f'<div style="width:1500px;height:340px;background:{PAPER};{SH};transform:rotate(1.5deg);clip-path:polygon(1% 4%,99% 0,100% 30%,98.8% 52%,100% 78%,99% 100%,2% 97%,0 70%,1.4% 44%,0 20%)">'
                 + CENTER(f'<div style="font:500 {sz}px/1 Mono;letter-spacing:18px;color:{INK};text-shadow:6px 4px 0 rgba(43,108,176,.5)">{U}</div>') + '</div>', 210, 360, pop)
    elif kind == 3:  # a stencil with few bridges, so the word still reads at a glance
        sz = min(470, int((1180 - 14 * n) / (.44 * n))); per, gap = round(sz * .62), max(8, round(sz * .02))
        body = A(f'<div style="width:1320px;height:580px;background:{CO};{SH};transform:rotate(-1.5deg);border:14px solid {PAPER};box-sizing:border-box">'
                 + CENTER(f'<div style="font:400 {sz}px/1 Bebas;letter-spacing:14px;color:{PAPER};-webkit-mask-image:repeating-linear-gradient(90deg,#000 0 {per - gap}px,transparent {per - gap}px {per}px);padding-top:30px">{U}</div>') + '</div>', 300, 220, pop)
    else:
        sz = min(290, int(1120 / (.8 * n)))
        body = A(sheet(CENTER(stamp(U, sz, -4)), 1340, 640, -3, pad=30), 290, 190, pop)
    put(f"m_w{i + 1:02d}", page(a(tag(f"WORD {i + 1} OF 15", 22), 96, 70) + body + bar(key), S_PRE))

# ---- the minute between the list and the test -------------------------------------------------------------------------------------
frame = lambda inner: f'<div style="background:#FBFCFE;padding:14px;{SH};transform:rotate(-.6deg)">{inner}</div>'
STMT = (big("WITNESS STATEMENT", 70, INK) + f'<div style="height:5px;background:{INK};margin:20px 0 34px"></div>'
        + mono("NAME: &nbsp;" + hl("YOU"), 40, INK, 3) + '<div style="height:30px"></div>' + mono("SAW: &nbsp;ONE ROAD ACCIDENT, 5 SECONDS", 40, INK, 3) + '<div style="height:30px"></div>'
        + mono("HOW SURE: ____________________", 40, INK, 3) + '<div style="height:30px"></div>' + mono("SIGNED: ______________________", 40, INK, 3))
put("m_21_done", page(a(P.tray(1340, 840), 290, 110) + A(sheet(STMT, 1000, 620, 1.5, pad=54), 460, 200, an("drop", "done", .38, .45)) + bar("done"), "STUDIO DRAWING"))
put("m_22_watch", page(a(P.tray(1340, 840), 290, 110) + a(sheet(STMT, 1000, 620, 1.5, pad=54), 460, 200)
                       + A(tag("EXHIBIT A · 5 S", 40, amber=True, rot=-4), 110, 80, an("slam", "watch", .06, .1), "z-index:60")
                       + bar("watch"), "STUDIO DRAWING"))

# the clip: the blue car runs up the side road past the junction's red triangle and bumps the parked red car. No other sign exists in it.
# One continuous clip in three parts: the camera follows the car, stops on the bump, pushes in (the triangle leaves the frame) and holds. The triangle is in view for about two seconds.
TC = sum(CLIP) / FPS
ct = lambda sec: round(sec / TC, 4)
put("m_23_clip", page(a(frame(P.road_scene(car_y=236, bump=True, drive=(700, ct(.15), ct(2.1), ct(2.12)))), 196, 76) + bar("clipa", "clipb"), "STUDIO PAPER CUT-OUT (NOT A REAL ACCIDENT)"))
put("m_24_witness", page(a(frame(P.road_scene(car_y=236, bump=True)), 196, 76)
                         + A(tag("WITNESS NO. 1 · YOU", 22, amber=True, rot=-4), 326, 206, an("slam", "witness", said("witness", .8), .1), "z-index:61") + bar("witness"), "STUDIO PAPER CUT-OUT (NOT A REAL ACCIDENT)"))

k = "email"   # plant 1 is in the narration only; the line is read flat and nothing lands on screen while it is said
put("m_25_email", page(
    a(sheet("", 1240, 800, -3.5, bg="#B9C9DE", pad=0), 380, 150)
    + A(sheet(mono("ELECTRONIC MAIL · CARBON COPY · DRAFT", 22, CO, 5) + f'<div style="height:4px;background:{CO};margin:16px 0 30px"></div>'
              + mono("FROM: &nbsp;&nbsp;&nbsp;[BLUE CAR]", 40, INK, 2) + '<div style="height:20px"></div>' + mono("TO: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;THE INSURER", 40, INK, 2) + '<div style="height:20px"></div>'
              + mono("SUBJECT: RE: RE: RE: THE PARKED CAR", 40, INK, 2) + f'<div style="height:3px;background:rgba(43,108,176,.4);margin:34px 0 44px"></div>'
              + f'<div style="font:500 66px/1.3 Mono;color:{INK};letter-spacing:1px;white-space:nowrap">To whom it may concern,<br><span style="position:relative;display:inline-block;vertical-align:bottom;height:86px">'
                f'<span data-anim="{an("type", k, said(k, .66), 1.2)}" data-n="20" data-ls="1" style="display:inline-block;overflow:hidden;white-space:nowrap;vertical-align:bottom;height:86px">it was barely a bump</span>'
                f'<span data-anim="{an("growx", k, end(k, .12), .3)}" style="position:absolute;left:-10px;right:-10px;top:52%;height:9px;background:{INK}"></span></span>'
                f'<span style="display:inline-block;width:34px;height:70px;background:{AM};margin-left:20px;vertical-align:bottom;margin-bottom:8px"></span></div>', 1240, 800, -1.5, bg="#DDE7F3", pad=56),
        330, 110, an("up", k, 0, .6))
    + a(f'<svg width="260" height="380" viewBox="-30 -30 220 360" style="overflow:visible;transform:rotate(-24deg);filter:drop-shadow(12px 14px 0 rgba(5,7,12,.42))">{P.car(CO, 150, 290)}</svg>', 60, 560, "z-index:58")
    + A(tag("DRAFT 14 · UNSENT", 30, inv=True, rot=4), 1280, 830, an("slam", k, end(k, .62), .1), "z-index:60") + bar(k),
    "SIGHT GAG (STUDIO DRAWING)"))

ticks = "".join(f'<div class="a" style="left:{i * 32}px;top:{650 if i % 10 else 636}px;width:{3 if i % 10 else 6}px;height:{26 if i % 10 else 54}px;background:rgba(240,244,248,.55)"></div>' for i in range(1, 60))
nums = "".join(f'<div class="a" style="left:{i * 32 - 22}px;top:700px;font:500 26px Mono;color:rgba(240,244,248,.75)">{i}</div>' for i in range(10, 60, 10))


def bigbar(key, extra):
    """The bar itself, huge: the same minute, the same place on it (so the thin bar is left off these two pages)."""
    p0, p1 = K[key]["p0"], K[key]["p1"]
    return page(a('<div style="width:1920px;height:230px;background:rgba(240,244,248,.08);border-top:5px solid rgba(240,244,248,.45);border-bottom:5px solid rgba(240,244,248,.45);box-sizing:border-box"></div>', 0, 410)
                + f'<div class="a" data-anim="bar 0 1" data-p0="{p0:.5f}" data-p1="{p1:.5f}" data-w="1920" style="left:0;top:415px;height:220px;background:{AM}"></div>' + ticks + nums
                + f'<div class="a" data-anim="move 0 1" data-dx="{-(p1 - p0) * 1920:.1f}" style="left:{p1 * 1920 - 190:.0f}px;top:335px;z-index:50">{P.magnifier(190)}</div>' + extra,
                "THE 60 SECONDS RUN FROM THE FIRST WORD TO THE TEST", ticks=False)


put("m_26_bar", bigbar("bar", A(tag("YOUR MINUTE", 44, amber=True, rot=-3), 96, 220, an("slam", "bar", .25, .1), "z-index:60")))
put("m_27_rehearse", bigbar("rehearse", a(tag("YOUR MINUTE", 44, amber=True, rot=-3), 96, 220, "z-index:60") + A(hand("don't rehearse.", 130, PAPER, -3), 110, 735, an("wipe", "rehearse", .05, .55), "z-index:60")
                                        + A(tag("I CAN'T SEE YOU. I'LL KNOW.", 26, inv=True, rot=2), 1130, 812, an("slam", "rehearse", said("rehearse", .74), .1), "z-index:60")))
S_SURE = "THE FEELING OF BEING SURE IS KEPT AS AN EXHIBIT · IT RETURNS LATER IN THE FILM"
put("m_28_sure", page(A(big("SOME OF YOU ARE ALREADY", 84), 118, 96, an("wipe", "sure", .05, .8)) + A(big("SURE.", 500), 110, 200, an("slam", "sure", said("sure", .55), .12)) + bar("sure"), S_SURE))
put("m_29_hold", page(a(big("SOME OF YOU ARE ALREADY", 84), 118, 96) + a(big("SURE.", 500), 110, 200) + A(P.luggage_tag("EXHIBIT C", "KEEP", 500, 220, 7), 1150, 700, an("drop", "hold", .1, .4), "z-index:60")
                      + A(hand("hold on to that feeling.", 84, AM, -2), 130, 760, an("wipe", "hold", .2, .8)) + bar("hold"), S_SURE))
S_FOLD = "THE STUDIES ARE NAMED AFTER THE TEST · 1959 TO 2026 IS 67 YEARS · THE FOLDERS ARE A STUDIO DRAWING"
stack = lambda when="": P.folders(10, 880, 80).replace("<svg ", f'<svg data-anim="{when}" ' if when else "<svg ", 1)
put("m_30_folders", page(A("", 0, 0, an("drop", "folders", .05)) + a(stack(an("fill", "folders", .05, 2.1)), 930, 170) + a(tag("PAPERWORK SINCE 1959", 32, amber=True, rot=-3), 100, 150, "z-index:40")
                         + A(big(f'<span style="color:{AM}">67</span>', 380), 96, 236, an("slam", "folders", said("folders", .64), .1)) + A(big("YEARS", 150), 104, 590, an("slam", "folders", said("folders", .64) + .12, .1))
                         + bar("folders"), S_FOLD))
put("m_31_later", page(a(P.folders(10, 880, 80), 930, 170) + a(tag("PAPERWORK SINCE 1959", 32, amber=True, rot=-3), 100, 150, "z-index:40")
                       + A(big("YOU'LL GET<br>ALL OF IT", 128), 100, 290, an("wipe", "later", .2, .6)) + A(hand("after you've<br>fallen for it.", 96, AM, -2), 106, 590, an("wipe", "later", said("later", .44), .8))
                       + A(sticky("LATER.", 300, 5, 104), 1300, 60, an("slam", "later", end("later", .1), .1), "z-index:60") + bar("later"), S_FOLD))

# ---- the test ------------------------------------------------------------------------------------------------------------------
S_TEST = "THE TEST: YES OR NO, OUT LOUD · THE STUDY IS NAMED AFTER THE TEST"
FULL = (a(BAND, 0, 986) + a(f'<div style="width:1760px;height:14px;background:{AM};border:2px solid rgba(240,244,248,.4);box-sizing:border-box"></div>', 80, 1012)
        + a(f'<div style="font:500 15px Mono;letter-spacing:3px;color:{AM}">60 S</div>', 1850, 1008))
put("m_32_test", page(
    A(big("TIME.", 330), 380, 380, an("slam", "test1", .05, .1)) + A(big("THREE WORDS.", 100, AM), 386, 712, an("fade", "test1", said("test1", .2), .08))
    + A(icard(CENTER(big("YES / NO?", 190, INK)), 1240, 520, -1, pad=40, top=104, line=62), 340, 330, an("slam", "test1", said("test1", .53), .1), "z-index:20")
    + A(P.bus(1460, 230, 9), 96, 50, an("up", "test2", said("test2", .56), .5), "z-index:30")
    + A(P.bubble("YES.", 300, 150, 76), 1570, 70, an("pop", "test2", said("test2", .88), .2), "z-index:60")
    + hud(FULL + A(stamp("FULL", 60, -6), 1612, 893, an("slam", "test1", .05, .1))), S_TEST))
# three words in one plain style, so nothing on screen tips the answer; a projector click, then the word is said
for n_, w in enumerate(("DREAM", "DOOR", "SLEEP")):
    put(f"t_{w.lower()}", page(a(tag(f"WORD {n_ + 1} OF 3 · WAS IT ON MY LIST?", 30), 100, 110)
                               + f'<div class="a" data-anim="{an("click", f"tw{n_ + 1}", .05)}" style="left:0;top:270px;width:1920px;text-align:center">{big(w, 420)}</div>'
                               + a(tag("YES OR NO. OUT LOUD.", 34, inv=True, rot=-2), 104, 800), S_TEST))

# ---- the reveal ----------------------------------------------------------------------------------------------------------------
tick = f'<svg width="150" height="130" viewBox="0 0 150 130"><path d="M14 70 L58 112 L136 16" fill="none" stroke="{CO}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/></svg>'
cross = f'<svg width="130" height="130" viewBox="0 0 130 130"><path d="M16 16 L114 114 M114 16 L16 114" fill="none" stroke="{CO}" stroke-width="24" stroke-linecap="round"/></svg>'


def wcard(w, rot, mark="", when=""):
    """A test word on an index card, with its verdict in the corner."""
    da = f' data-anim="{when}"' if when else ""
    return icard(CENTER(mono(w, 118, INK, 8)) + (f'<div{da} style="position:absolute;left:16px;top:10px;transform:scale(.8);transform-origin:0 0">{mark}</div>' if mark else ""), 540, 380, rot, pad=30, top=96, line=58)


k = "cards"
put("r_cards", page(A(wcard("DREAM", -2, tick, an("pop", k, said(k, .27), .15)), 60, 330, an("drop", k, 0, .2)) + A(wcard("DOOR", 1.5, cross, an("pop", k, said(k, .8), .15)), 620, 360, an("drop", k, 0, .26))
                    + A(wcard("SLEEP", 4), 1180, 320, an("drop", k, 0, .32)) + A(hand("on the list.", 64, PAPER, -3), 170, 740, an("wipe", k, said(k, .3), .4))
                    + A(hand("not on it.", 64, PAPER, 2), 760, 765, an("wipe", k, said(k, .84), .3)), S_REV))
paused = (f'<div style="display:inline-flex;align-items:center;background:{AM};color:{SL};border:2px solid {SL};padding:12px 24px;transform:rotate(3deg);box-shadow:6px 7px 0 rgba(5,7,12,.45);'
          f'font:500 40px Mono;letter-spacing:6px"><span style="display:inline-block;width:12px;height:40px;background:{SL};margin-right:10px"></span>'
          f'<span style="display:inline-block;width:12px;height:40px;background:{SL};margin-right:22px"></span>PAUSED</div>')
put("r_reveal", page(
    a(wcard("DREAM", -2, tick), 60, 330) + a(wcard("DOOR", 1.5, cross), 620, 360) + a(hand("on the list.", 64, PAPER, -3), 170, 740) + a(hand("not on it.", 64, PAPER, 2), 760, 765)
    + A(wcard("SLEEP", 4), 1180, 320, an("flipout", "never", .1, .22)) + A(sheet("", 540, 380, 4, pad=0), 1180, 320, an("flipin", "never", .32, .22))
    + A(stamp("NEVER SAID", 62, -9), 1200, 450, an("slam", "never", end("never", -.1), .1), "z-index:60") + A(big("I NEVER SAID IT.", 136), 90, 64, an("slam", "notonce", .06, .1))
    + A(tag(f"REWIND TO {REWIND}", 36, inv=True, rot=-2), 1290, 850, an("slam", "scroll", .12, .1), "z-index:60") + A(paused, 330, 850, an("drop", "scroll", said("scroll", .74), .3), "z-index:60")
    + arrow(1260, 890, 720, 905, an("draw", "scroll", .45, .5), AM, 10, -24), S_REV))

# ---- after the reveal: sources are named from here on ---------------------------------------------------------------------------------
k1, k2, k3 = "maj1", "maj2", "maj3"
put("v_13_majority", page(
    a(f'<div style="opacity:.34">{crowd(16, 5, 1920, 760, col=DIM)}</div>', 0, 260)
    + A(study("Stadler, Roediger &amp; McDermott", 1999, "Memory &amp; Cognition", note="NORMS FOR THE WORD LISTS", w=700), 90, 90, an("up", k1, 0, .35), "z-index:40")
    + A(f'<div data-anim="{an("slam", k1, said(k1, .5), .1)}">{big("THE<br>MAJORITY.", 170)}</div>', 96, 440, an("hide", k2, said(k2, .49)), "z-index:40")
    + A(big("80%", 330, AM), 90, 520, an("slam", k2, said(k2, .58), .1), "z-index:40") + A(big("MORE THAN", 110), 96, 420, an("slam", k2, said(k2, .5), .1), "z-index:40")
    + A(tag("SAID YES TO \"SLEEP\"", 34, inv=True, rot=-2), 760, 780, an("slam", k2, said(k2, .86), .1), "z-index:41")
    + A(f'<div style="width:300px;height:720px;box-sizing:border-box;border:6px solid {PAPER};border-bottom-width:10px;background:rgba(20,24,36,.86);position:relative">'
        f'<div data-anim="{an("grow", k2, said(k2, .58), .8)}" style="position:absolute;left:0;right:0;bottom:0;height:80%;background:{AM}"></div>'
        f'<div data-anim="{an("fade", k2, said(k2, .58) + .8, .3)}" style="position:absolute;left:0;right:0;bottom:80%;height:9%;background:repeating-linear-gradient(135deg,{AM} 0 12px,transparent 12px 24px)"></div>'
        f'<div style="position:absolute;left:-40px;right:-40px;bottom:80%;border-top:6px dashed {PAPER}"></div>'
        f'<div style="position:absolute;left:-150px;bottom:calc(80% - 22px);font:500 34px Mono;color:{PAPER}">80%</div>'
        f'<div style="position:absolute;left:-90px;bottom:-14px;font:500 34px Mono;color:{PAPER}">0</div>'
        f'<div style="position:absolute;left:-150px;top:-18px;font:500 34px Mono;color:{PAPER}">100%</div></div>', 1440, 150, an("up", k2, said(k2, .3), .4), "z-index:40")
    + A(tag("THE REST SAID NO", 20, inv=True, rot=-2), 980, 222, an("slam", k3, said(k3, .2), .1), "z-index:42") + arrow(1262, 238, 1480, 196, an("draw", k3, said(k3, .3), .3), PAPER, 6, 14),
    "STADLER, ROEDIGER & McDERMOTT 1999: FALSE RECOGNITION OF \"SLEEP\" ABOVE 80% · THE BAR IS SOLID TO 80%; THE HATCHED PART MEANS \"MORE THAN\" (EXACT VALUE NOT SHOWN)"))

k = "title"
put("v_14_title", page(
    a(tag("IT'S IN THE TITLE", 30, inv=True, rot=-2), 100, 90)
    + A(icard(CENTER(f'<div style="font:500 70px/1.5 Mono;color:{INK};letter-spacing:2px;text-align:center">CAN I GIVE YOU A FALSE MEMORY<br>IN 60 SECONDS?</div>'), 1560, 600, -1.2, pad=40, top=110, line=66), 180, 220, an("up", k, 0, .3))
    + ring(960, 512, 700, 205, an("draw", k, said(k, .56), .5), RED, 11, 5)
    + A(stamp("PROBABLY", 126, -8), 880, 680, an("slam", k, end(k, .1), .1), "z-index:60"),
    "THE WARNING IS THE TITLE · WARNINGS REDUCE THE EFFECT BUT DO NOT REMOVE IT (GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998)"))

k = "warn"
put("v_15_warning", page(
    A(study("Gallo, Roberts &amp; Seamon", 1997, "Psychonomic Bulletin &amp; Review", w=700), 90, 100, an("up", k, 0, .3))
    + A(big("WARNINGS<br>SHRINK IT.", 150), 96, 420, an("slam", k, .06, .1)) + A(big("THEY DON'T REMOVE IT.", 62, AM), 100, 740, an("slam", k, said(k, .66), .1))
    + a(f'<div style="display:flex;gap:90px;align-items:flex-end;border-bottom:8px solid {PAPER};height:640px;padding:0 50px">'
        f'<div style="width:240px;height:560px;background:{DIM}"></div><div data-anim="{an("grow", k, .3, .8)}" style="width:240px;height:330px;background:{AM}"></div></div>'
        f'<div style="display:flex;gap:90px;padding:14px 50px 0;font:500 26px Mono;letter-spacing:3px;color:{PAPER}"><div style="width:240px;text-align:center">NOT WARNED</div><div style="width:240px;text-align:center">WARNED</div></div>', 1130, 130)
    + a(tag("BAR SIZES ILLUSTRATIVE · DIRECTION AS REPORTED", 18), 1170, 880),
    "GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998 · NO VALUES ARE SHOWN: THE DOSSIER HOLDS THE DIRECTION, NOT THE SIZE"))

k1, k2 = "env1", "env2"
put("v_16_envelope", page(
    a(P.tray(1340, 840), 290, 110) + A(P.envelope(920, 580, -3), 500, 240, an("drop", k1, 0, .35))
    + A(tag("A SECOND FALSE MEMORY", 30, amber=True, rot=-3), 96, 70, an("slam", k1, said(k1, .5), .1), "z-index:60")
    + A(stamp("EXHIBIT B", 110, -7), 560, 300, an("slam", k1, said(k1, .9), .1), "z-index:60")
    + A(tag("NOT A WORD", 30, inv=True, rot=-2), 610, 640, an("slam", k2, .1, .1), "z-index:60")
    + A(tag("OPEN AT THE END", 36, inv=True, rot=3), 980, 730, an("slam", k2, said(k2, .7), .1), "z-index:60"),
    "THE SECOND TEST IS COLLECTED AT THE END OF THE FILM"))

# ---- the trap's rules, checked on what was just written ---------------------------------------------------------------------------------
H = D / "html"
visible = lambda pg: __import__("re").sub(r"<style.*?</style>|<script.*?</script>|<[^>]+>", " ", (H / f"{pg}.html").read_text(), flags=16).upper()   # the text a viewer could read
for pg in dict.fromkeys(s["page"] for s in S[:S.index(K["tw3"])]):
    assert "SLEEP" not in visible(pg), f'"sleep" is on {pg}, before the third test word'
for pg in dict.fromkeys(s["page"] for s in S[:S.index(K["cards"])]):
    for word in ("ROEDIGER", "MCDERMOTT", "DEESE", "LOFTUS", "MISSING WORD", "ASSOCIATES", "FALSE RECOGNITION", "DRM"):
        assert word not in visible(pg), f"{word} is on {pg}, before the reveal"
for pg in dict.fromkeys(s["page"] for s in S):
    for word in ("STOP SIGN", " STOP ", "GIVE WAY", "GIVE-WAY", "YIELD", "CAR CLIP"):
        assert word not in visible(pg), f"{word.strip()} is on {pg}: no sign is named on screen, and nothing points at the clip"
assert not any("sleep" in s["vo"].lower() for s in S[:S.index(K["tw3"])]), '"sleep" is said before the third test word'
print("pages written:", len({s["page"] for s in S}), "· trap rules hold: no \"sleep\" before the third test word, no study named before the reveal, no sign named on any page")
