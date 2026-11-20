"""Key frames, act 0 "The trap" (0:00-2:10). One frame per beat of SCRIPT.md; the five list frames show the five paper treatments.
Numbers and names only from DOSSIER.md. Run through build.py."""
from kit import (A, a, put, page, big, mono, tag, hand, stamp, sheet, icard, sticky, study, photo, ring, arrow, bar60, crowd, hl,
                 SL, PAPER, CO, AM, RED, INK, CARD, DIM, SH)
import props as P

CENTER = lambda inner: f'<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%">{inner}</div>'
S_TRAP = "THE EFFECT: ROEDIGER & McDERMOTT 1995, J. EXP. PSYCHOL.: LMC · THE LIST: THE STUDY'S 15 ASSOCIATES OF ONE MISSING WORD"
# Before the reveal a source line names nothing: the study, the missing word, the sign or the plant on screen would be an answer key.
S_PRE = "THE 15 WORDS COME FROM A PUBLISHED MEMORY STUDY · IT IS NAMED AFTER THE TEST, SO THE TEST STAYS FAIR"
S_TEST = "THE TEST: YES OR NO, OUT LOUD · THE STUDY IS NAMED AFTER THE TEST"

# 01 · the claim. "Give me sixty seconds. I'm going to put a memory in your head. Of something that never happened... You'll just be sure."
put("01_hook", page(
    A(big("GIVE ME", 230), 96, 84, "slam .02 .08")
    + A(big(f'<span style="color:{AM}">60</span> SECONDS', 230), 96, 296, "slam .1 .16")
    + A(icard(mono("FILE: ONE MEMORY", 44, INK, 4) + '<div style="height:36px"></div>' + mono("SUBJECT: NEVER HAPPENED", 50, INK, 3)
              + '<div style="height:14px"></div>' + mono("STATUS:", 50, INK, 3), 1180, 410, 2, pad=48, top=120, line=64), 430, 580, "up .3 .42")
    + A(stamp("CERTAIN", 140, -8), 900, 770, "slam .7 .76", "z-index:60"),
    "THE CLAIM IS TESTED ON THE VIEWER IN THIS VIDEO · THE STUDY IS NAMED AFTER THE TEST, SO THE TEST STAYS FAIR"))

# 02 · the stakes. "And this same glitch has helped put innocent people in prison."
put("02_courthouse", page(
    A(photo("courthouse_front", 1060, 740, -2, "50% 62%", anim="push 0 1"), 70, 96, "drop 0 .08")
    + A(big("INNOCENT<br>PEOPLE.", 104), 1235, 150, "slam .2 .26")
    + A(big("IN PRISON.", 92, AM), 1235, 356, "slam .34 .4")
    + A(tag("HOLD THAT THOUGHT", 34, amber=True, rot=-3), 1235, 560, "slam .6 .66", "z-index:40")
    + A(hand("we come back here.", 70, PAPER, -3), 1250, 700, "wipe .7 .9"),
    "PHOTO: W_LEMAY, CC0 (ALAMANCE COUNTY, NORTH CAROLINA: THE COUNTY OF THE CASE TOLD LATER) · THE FIGURES BEHIND THIS LINE: INNOCENCE PROJECT, DNA EXONERATIONS 1989-2020"))

# 03 · the instruction. "Fifteen words. Don't write them down."
put("03_instructions", page(
    A(sheet(big("PARTICIPANT INSTRUCTIONS", 56, INK) + mono("FORM 15-W · STUDIO RECONSTRUCTION", 20, CO, 4, extra="margin-top:10px")
            + f'<div style="height:5px;background:{INK};margin:26px 0 40px"></div>'
            + mono("1. YOU WILL HEAR FIFTEEN WORDS.", 42, INK, 2) + '<div style="height:38px"></div>'
            + mono("2. " + hl("DO NOT WRITE THEM DOWN."), 42, INK, 2) + '<div style="height:38px"></div>'
            + mono("3. THAT IS THE WHOLE TEST.", 42, INK, 2), 1150, 880, -1.2, pad=60), 80, 90, "drop 0 .08")
    + A(P.pencil(820, snapped=True), 250, 660, "slam .55 .6", "z-index:50;transform-origin:50% 50%")
    + A(big("15", 400, AM), 1300, 130, "slam .1 .16")
    + A(big("WORDS", 128), 1306, 540, "slam .2 .26")
    + A(tag("NO NOTES", 34, inv=True, rot=4), 1320, 740, "slam .6 .66"),
    "THE VIEWER'S INSTRUCTIONS (OUR WORDING) · " + S_PRE))

# 04a-e · the list. One word per card, about 1.4 s each; five paper treatments cycle. The thin amber bar runs for 60 s.
wtag = lambda n: a(tag(f"WORD {n} OF 15", 22), 96, 70)
put("04a_list_card", page(
    wtag(1) + A(icard(CENTER(mono("BED", 330, INK, 26)), 1180, 640, -1, pad=40, top=110, line=66), 370, 190, "slam 0 .06") + bar60(.012), S_PRE))
put("04b_list_tape", page(
    wtag(2) + A(f'<div style="width:1560px;height:360px;background:linear-gradient(#1C2130,#07090E 16%,#07090E 84%,#1C2130);box-shadow:14px 18px 0 rgba(5,7,12,.5);transform:rotate(-2deg);'
                f'clip-path:polygon(0 0,100% 0,98.6% 16%,100% 33%,98.6% 50%,100% 67%,98.6% 84%,100% 100%,0 100%,1.4% 84%,0 67%,1.4% 50%,0 33%,1.4% 16%)">'
                + CENTER(f'<div style="font:400 270px/1 Black;letter-spacing:30px;color:{PAPER};text-shadow:0 5px 0 rgba(255,255,255,.28),0 -4px 0 rgba(0,0,0,.9)">REST</div>') + '</div>', 180, 350, "wipe 0 .1")
    + bar60(.036), S_PRE))
put("04c_list_typed", page(
    wtag(3) + A(f'<div style="width:1500px;height:340px;background:{PAPER};{SH};transform:rotate(1.5deg);'
                f'clip-path:polygon(1% 4%,99% 0,100% 30%,98.8% 52%,100% 78%,99% 100%,2% 97%,0 70%,1.4% 44%,0 20%)">'
                + CENTER(f'<div style="font:500 250px/1 Mono;letter-spacing:18px;color:{INK};text-shadow:6px 4px 0 rgba(43,108,176,.5)">AWAKE</div>') + '</div>', 210, 360, "wipe 0 .1")
    + bar60(.06), S_PRE))
put("04d_list_stencil", page(
    wtag(4) + A(f'<div style="width:1320px;height:580px;background:{CO};{SH};transform:rotate(-1.5deg);border:14px solid {PAPER};box-sizing:border-box">'
                + CENTER(f'<div style="font:400 470px/1 Bebas;letter-spacing:14px;color:{PAPER};-webkit-mask-image:repeating-linear-gradient(90deg,#000 0 58px,transparent 58px 68px);padding-top:30px">TIRED</div>') + '</div>', 300, 220, "slam 0 .06")
    + bar60(.083), S_PRE))
put("04e_list_stamp", page(
    wtag(5) + A(sheet(CENTER(stamp("DREAM", 290, -4)), 1340, 640, -3, pad=30), 290, 190, "slam 0 .06")
    + bar60(.107), S_PRE))

# 05 · "Done. Put those away. Watch this once."
put("05_intray", page(
    a(P.tray(1340, 840), 290, 110)
    + A(sheet(big("WITNESS STATEMENT", 70, INK) + f'<div style="height:5px;background:{INK};margin:20px 0 34px"></div>'
              + mono("NAME: &nbsp;" + hl("YOU"), 40, INK, 3) + '<div style="height:30px"></div>'
              + mono("SAW: &nbsp;ONE ROAD ACCIDENT, 5 SECONDS", 40, INK, 3) + '<div style="height:30px"></div>'
              + mono("HOW SURE: ____________________", 40, INK, 3) + '<div style="height:30px"></div>'
              + mono("SIGNED: ______________________", 40, INK, 3), 1000, 620, 1.5, pad=54), 460, 200, "drop .05 .15")
    + A(tag("EXHIBIT A · 5 S", 40, amber=True, rot=-4), 110, 80, "slam .5 .56", "z-index:60")
    + bar60(.36),
    "STUDIO DRAWING"))

# 06a · the clip: a blue car passes a GIVE WAY triangle and bumps a parked red car. There is no stop sign anywhere.
frame = lambda inner: f'<div style="background:#FBFCFE;padding:14px;{SH};transform:rotate(-.6deg)">{inner}</div>'
put("06a_clip", page(
    A(frame(P.road_scene(car_y=500)), 196, 76, "snap 0 0")
    + a(tag("EXHIBIT A", 30, amber=True, rot=-3), 96, 56, "z-index:60")
    + a(tag("0:43", 26, inv=True), 236, 890, "z-index:60")
    + bar60(.41),
    "STUDIO PAPER CUT-OUT (NOT A REAL ACCIDENT)"))
put("06b_witness", page(
    A(frame(P.road_scene(car_y=236, bump=True)), 196, 76, "snap 0 0")
    + a(tag("EXHIBIT A", 30, amber=True, rot=-3), 96, 56, "z-index:60")
    + a(tag("0:47 · FREEZE", 26, inv=True), 236, 890, "z-index:60")
    + A(stamp("WITNESS NO. 1", 74, -6, sub="YOU"), 1030, 700, "slam .3 .36", "z-index:61")
    + bar60(.48),
    "STUDIO PAPER CUT-OUT (NOT A REAL ACCIDENT)"))

# 07 · plant 1, said in passing: "...the owner of the blue car that ran the stop sign is drafting a defensive email." No sign on screen.
put("07_email", page(
    a(sheet("", 1240, 800, -3.5, bg="#B9C9DE", pad=0), 380, 150)
    + A(sheet(mono("ELECTRONIC MAIL · CARBON COPY · DRAFT", 22, CO, 5)
              + f'<div style="height:4px;background:{CO};margin:16px 0 30px"></div>'
              + mono("FROM: &nbsp;&nbsp;&nbsp;[BLUE CAR]", 40, INK, 2) + '<div style="height:20px"></div>'
              + mono("TO: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;THE INSURER", 40, INK, 2) + '<div style="height:20px"></div>'
              + mono("SUBJECT: RE: RE: RE: THE PARKED CAR", 40, INK, 2)
              + f'<div style="height:3px;background:rgba(43,108,176,.4);margin:34px 0 44px"></div>'
              + f'<div style="font:500 66px/1.3 Mono;color:{INK};letter-spacing:1px">To whom it may concern,<br><span style="position:relative;display:inline-block">it was barely a bump'
                f'<span style="position:absolute;left:-10px;right:-10px;top:52%;height:9px;background:{INK}"></span></span>'
                f'<span style="display:inline-block;width:34px;height:70px;background:{AM};margin-left:20px;vertical-align:-12px"></span></div>', 1240, 800, -1.5, bg="#DDE7F3", pad=56), 330, 110, "up 0 .12")
    + a(f'<svg width="260" height="380" viewBox="-30 -30 220 360" style="overflow:visible;transform:rotate(-24deg);filter:drop-shadow(12px 14px 0 rgba(5,7,12,.42))">{P.car(CO, 150, 290)}</svg>', 60, 560, "z-index:58")
    + A(tag("DRAFT 14 · UNSENT", 30, inv=True, rot=4), 1280, 830, "slam .7 .76", "z-index:60")
    + bar60(.53),
    "SIGHT GAG (STUDIO DRAWING)"))

# 08a · "That amber bar is your minute. Don't rehearse. I can't see you, but I'll know."
ticks = "".join(f'<div class="a" style="left:{i * 32}px;top:{650 if i % 10 else 636}px;width:{3 if i % 10 else 6}px;height:{26 if i % 10 else 54}px;background:rgba(240,244,248,.55)"></div>' for i in range(1, 60))
nums = "".join(f'<div class="a" style="left:{i * 32 - 22}px;top:700px;font:500 26px Mono;color:rgba(240,244,248,.75)">{i}</div>' for i in range(10, 60, 10))
put("08a_bar", page(
    a(f'<div style="width:1920px;height:230px;background:rgba(240,244,248,.08);border-top:5px solid rgba(240,244,248,.45);border-bottom:5px solid rgba(240,244,248,.45);box-sizing:border-box"></div>', 0, 410)
    + A(f'<div style="width:1184px;height:220px;background:{AM}"></div>', 0, 415, "growx 0 1")
    + ticks + nums
    + a(P.magnifier(190), 994, 335, "z-index:50")
    + A(tag("YOUR MINUTE", 44, amber=True, rot=-3), 96, 220, "slam .05 .1", "z-index:60")
    + A(hand("don't rehearse.", 130, PAPER, -3), 110, 780, "wipe .3 .6", "z-index:60")
    + A(tag("I CAN'T SEE YOU. I'LL KNOW.", 26, inv=True, rot=2), 1130, 880, "slam .75 .8", "z-index:60"),
    "THE 60 SECONDS RUN FROM THE FIRST WORD TO THE TEST", ticks=False))

# 08b · "Some of you are already sure you'll pass. Hold on to that feeling. We'll need it later."
put("08b_sure", page(
    A(big("SURE.", 500), 110, 200, "slam .05 .11")
    + A(P.luggage_tag("EXHIBIT C", "KEEP", 500, 220, 7), 1150, 700, "drop .45 .55", "z-index:60")
    + A(hand("hold on to that feeling.", 84, AM, -2), 130, 760, "wipe .6 .9")
    + bar60(.72),
    "THE FEELING OF BEING SURE IS KEPT AS AN EXHIBIT · IT RETURNS LATER IN THE FILM"))

# 09 · "This trick has a lab behind it, and nearly seventy years of paperwork. You'll get all of it after you've fallen for it."
put("09_folders", page(
    A(P.folders(10, 880, 80), 930, 170, "up 0 .2")
    + A(sticky("LATER.", 300, 5, 104), 1300, 60, "slam .7 .76", "z-index:60")
    + A(tag("PAPERWORK SINCE 1959", 32, amber=True, rot=-3), 100, 150, "slam .1 .16")
    + A(big("YOU'LL GET<br>ALL OF IT", 128), 100, 290, "wipe .2 .45")
    + A(hand("after you've<br>fallen for it.", 96, AM, -2), 106, 590, "wipe .6 .9")
    + bar60(.88),
    "THE STUDIES ARE NAMED AFTER THE TEST · THE FOLDERS ARE A STUDIO DRAWING"))

# 10 · the test. "Time. Three words. Was each one on my list? Yes or no, out loud. If you're on a bus, commit."
put("10_test", page(
    A(P.bus(1460, 230, 9), 96, 50, "up .2 .4")
    + A(P.bubble("YES.", 300, 150, 76), 1570, 70, "pop .6 .7", "z-index:60")
    + A(icard(CENTER(big("YES / NO?", 210, INK)), 1320, 580, -1, pad=40, top=110, line=66), 300, 350, "slam 0 .06")
    + bar60(1.0) + A(stamp("FULL", 60, -6), 1560, 890, "slam .05 .1", "z-index:88"),
    S_TEST))

# 11 · the third test word. It has never been said or shown until now.
put("11_sleep", page(
    a(tag("WORD 3 OF 3 · WAS IT ON MY LIST?", 30), 100, 110)
    + f'<div class="a" data-anim="slam 0 .05" style="left:0;top:270px;width:1920px;text-align:center">{big("SLEEP", 420)}</div>'   # plain white and centred, like the two words before it: amber would tip the answer
    + A(tag("YES OR NO. OUT LOUD.", 34, inv=True, rot=-2), 104, 800, "slam .5 .56"),
    S_TEST))

# 12 · the reveal. "Dream was on the list. Door wasn't. And sleep? I never said it. Not once. Scroll back and check."
tick = f'<svg width="150" height="130" viewBox="0 0 150 130"><path d="M14 70 L58 112 L136 16" fill="none" stroke="{CO}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/></svg>'
cross = f'<svg width="130" height="130" viewBox="0 0 130 130"><path d="M16 16 L114 114 M114 16 L16 114" fill="none" stroke="{CO}" stroke-width="24" stroke-linecap="round"/></svg>'
wcard = lambda w, mark, rot: icard(CENTER(mono(w, 118, INK, 8)) + f'<div style="position:absolute;right:20px;top:14px">{mark}</div>', 540, 380, rot, pad=30, top=96, line=58)
put("12_reveal", page(
    A(big("I NEVER SAID IT.", 136), 90, 64, "slam .5 .56")
    + A(wcard("DREAM", tick, -2), 80, 330, "up 0 .08") + A(wcard("DOOR", cross, 1.5), 690, 360, "up .1 .18")
    + A(sheet("", 540, 380, 4, pad=0), 1290, 320, "up .2 .28")
    + A(stamp("NEVER SAID", 62, -9), 1340, 450, "slam .6 .66", "z-index:60")
    + A(tag("REWIND TO 0:14", 36, inv=True, rot=-2), 1290, 850, "slam .8 .86", "z-index:60")
    + arrow(1260, 890, 720, 905, "draw .86 .98", AM, 10, -24)
    + A(hand("on the list.", 64, PAPER, -3), 190, 740, "wipe .12 .2") + A(hand("not on it.", 64, PAPER, 2), 830, 765, "wipe .2 .3"),
    "\"SLEEP\" WAS NEVER SAID OR SHOWN BEFORE THE TEST · " + S_TRAP))

# 13 · "Said yes? You're the majority. When researchers tested this exact list, more than 80 percent of people said yes to 'sleep'."
put("13_majority", page(
    a(f'<div style="opacity:.34">{crowd(16, 5, 1920, 760, col=DIM)}</div>', 0, 260)
    + A(study("Stadler, Roediger &amp; McDermott", 1999, "Memory &amp; Cognition", note="NORMS FOR THE WORD LISTS", w=700), 90, 90, "up 0 .1", "z-index:40")
    + A(big("MORE THAN", 110), 96, 420, "slam .2 .26", "z-index:40") + A(big("80%", 330, AM), 90, 520, "slam .3 .36", "z-index:40")
    + A(tag("SAID YES TO \"SLEEP\"", 34, inv=True, rot=-2), 760, 780, "slam .5 .56", "z-index:41")
    + a(f'<div style="width:300px;height:720px;box-sizing:border-box;border:6px solid {PAPER};border-bottom-width:10px;background:rgba(20,24,36,.86);position:relative">'
        f'<div data-anim="grow .3 .7" style="position:absolute;left:0;right:0;bottom:0;height:80%;background:{AM}"></div>'
        f'<div style="position:absolute;left:0;right:0;bottom:80%;height:9%;background:repeating-linear-gradient(135deg,{AM} 0 12px,transparent 12px 24px)"></div>'
        f'<div style="position:absolute;left:-40px;right:-40px;bottom:80%;border-top:6px dashed {PAPER}"></div>'
        f'<div style="position:absolute;left:-150px;bottom:calc(80% - 22px);font:500 34px Mono;color:{PAPER}">80%</div>'
        f'<div style="position:absolute;left:-90px;bottom:-14px;font:500 34px Mono;color:{PAPER}">0</div>'
        f'<div style="position:absolute;left:-150px;top:-18px;font:500 34px Mono;color:{PAPER}">100%</div></div>', 1440, 150, "z-index:40"),
    "STADLER, ROEDIGER & McDERMOTT 1999: FALSE RECOGNITION OF \"SLEEP\" ABOVE 80% · THE BAR IS SOLID TO 80%; THE HATCHED PART MEANS \"MORE THAN\" (EXACT VALUE NOT SHOWN)"))

# 14 · "And I warned you. It's in the title."
put("14_title", page(
    a(tag("IT'S IN THE TITLE", 30, inv=True, rot=-2), 100, 90)
    + A(icard(CENTER(f'<div style="font:500 70px/1.5 Mono;color:{INK};letter-spacing:2px;text-align:center">CAN I GIVE YOU A FALSE MEMORY<br>IN 60 SECONDS?</div>'), 1560, 600, -1.2, pad=40, top=110, line=66), 180, 220, "up 0 .1")
    + ring(960, 512, 700, 205, "draw .3 .55", RED, 11, 5)
    + A(stamp("PROBABLY", 126, -8), 880, 680, "slam .7 .76", "z-index:60"),
    "THE WARNING IS THE TITLE · WARNINGS REDUCE THE EFFECT BUT DO NOT REMOVE IT (GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998)"))

# 15 · "Warnings shrink the effect. They don't remove it. If you said no, well done. It doesn't work on everyone."
put("15_warning", page(
    A(study("Gallo, Roberts &amp; Seamon", 1997, "Psychonomic Bulletin &amp; Review", w=700), 90, 100, "up 0 .1")
    + A(big("WARNINGS<br>SHRINK IT.", 150), 96, 420, "slam .15 .21") + A(big("THEY DON'T REMOVE IT.", 62, AM), 100, 740, "slam .5 .56")
    + a(f'<div style="display:flex;gap:90px;align-items:flex-end;border-bottom:8px solid {PAPER};height:640px;padding:0 50px">'
        f'<div style="width:240px;height:560px;background:{DIM}"></div><div data-anim="grow .3 .6" style="width:240px;height:330px;background:{AM}"></div></div>'
        f'<div style="display:flex;gap:90px;padding:14px 50px 0;font:500 26px Mono;letter-spacing:3px;color:{PAPER}"><div style="width:240px;text-align:center">NOT WARNED</div><div style="width:240px;text-align:center">WARNED</div></div>', 1130, 130)
    + a(tag("BAR SIZES ILLUSTRATIVE · DIRECTION AS REPORTED", 18), 1170, 880),
    "GALLO, ROBERTS & SEAMON 1997; McDERMOTT & ROEDIGER 1998 · NO VALUES ARE SHOWN: THE DOSSIER HOLDS THE DIRECTION, NOT THE SIZE"))

# 16 · "But I've already planted a second false memory in this video. It isn't a word. I'll collect it at the end."
put("16_envelope", page(
    a(P.tray(1340, 840), 290, 110)
    + A(P.envelope(920, 580, -3), 500, 240, "drop 0 .1")
    + A(stamp("EXHIBIT B", 110, -7), 560, 300, "slam .35 .41", "z-index:60")
    + A(tag("OPEN AT THE END", 36, inv=True, rot=3), 980, 730, "slam .6 .66", "z-index:60")
    + A(tag("A SECOND FALSE MEMORY · NOT A WORD", 28, amber=True, rot=-3), 96, 70, "slam .1 .16", "z-index:60"),
    "THE SECOND TEST IS COLLECTED AT THE END OF THE FILM"))
