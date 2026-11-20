"""Key frames, act 1 "How I did that" (2:10-3:45) and act 2 "But I'd remember something that mattered" (3:45-5:07).
Numbers and names only from DOSSIER.md. Handwriting is a stand-in (loops, no words), so no answer is invented."""
import random

from kit import (A, a, put, page, big, mono, tag, hand, quote, stamp, sheet, icard, sticky, study, photo, full, ring, arrow, strike, bust, crowd, hl,
                 SL, PAPER, CO, AM, RED, INK, CARD, FOLD, DIM, SH, SH2)
import props as P

CENTER = lambda inner: f'<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%">{inner}</div>'
RULE = lambda col=INK, m="18px 0 28px", h=5: f'<div style="height:{h}px;background:{col};margin:{m}"></div>'
GAP = lambda h: f'<div style="height:{h}px"></div>'
S_DRM = "ROEDIGER & McDERMOTT 1995, J. EXP. PSYCHOL.: LMC"
S_NH = "NEISSER & HARSCH 1992, \"PHANTOM FLASHBULBS\", IN WINOGRAD & NEISSER (EDS.), AFFECT AND ACCURACY IN RECALL"


def xmark(x0, y0, x1, y1, anim="draw .3 .5", col=CO, w=30):
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:58;pointer-events:none;filter:url(#wob)" width="1920" height="1080">'
            f'<path d="M{x0} {y0} L{x1} {y1}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{x1} {y0} L{x0} {y1}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/></svg>')


# ==== ACT 1 ==================================================================================================================
# 17 · "Your memory isn't a camera."
put("17_camera", page(
    A(P.camera(880), 100, 250, "drop 0 .1")
    + xmark(150, 270, 950, 780)
    + A(tag("YOUR MEMORY", 40, amber=True, rot=-3), 1110, 190, "slam .1 .16")
    + A(big("ISN'T A<br>CAMERA.", 136), 1104, 300, "slam .3 .36")
    + A(hand("it never was.", 92, AM, -3), 1120, 620, "wipe .6 .85"),
    "METAPHOR (STUDIO DRAWING) · MEMORY IS REBUILT, NOT REPLAYED: " + S_DRM + "; LOFTUS, TEDGLOBAL 2013"))

# 18 · "It's a middle manager who missed the meeting and is now presenting the minutes, with total confidence."
put("18_manager", page(
    A(P.manager(w=930, h=1100), 20, 40, "up 0 .12")
    + A(P.chair(250, 440), 1560, 540, "up .5 .6") + A(tag("EMPTY SEAT", 22, rot=-3), 1540, 470, "slam .62 .66")
    + A(big("PRESENTING<br>THE MINUTES", 96), 960, 140, "slam .2 .26")
    + A(hand("of a meeting it missed.", 88, AM, -2), 968, 380, "wipe .5 .8")
    + A(tag("WITH TOTAL CONFIDENCE", 32, inv=True, rot=2), 968, 560, "slam .8 .86")
    + a(tag("METAPHOR, NOT ANATOMY", 20), 968, 700),
    "SIGHT GAG (STUDIO DRAWING): THE BRAIN AS A MIDDLE MANAGER · NO FACE, NO REAL PERSON"))

# 19 · "It didn't record fifteen words. It wrote one note: something about bedtime."
rows = ""
for i in range(1, 16):
    note = (f'<div style="position:absolute;left:90px;top:-34px;font:400 70px/1 Hand;color:{CO};white-space:nowrap;transform:rotate(-2deg)">something re: bedtime?</div>' if i == 8 else "")
    rows += (f'<div style="position:relative;height:39px;border-bottom:3px solid rgba(43,108,176,.3);font:500 18px Mono;color:{DIM};padding-top:16px;box-sizing:border-box">{i:02d}{note}</div>')
put("19_minutes", page(
    A(sheet(f'<div style="display:flex;align-items:baseline;gap:30px">{big("MINUTES", 104, INK)}{mono("MEETING: THE WORD LIST · ATTENDED: NO", 22, CO, 4)}</div>' + RULE(INK, "10px 0 6px") + rows, 1300, 880, -1, pad=54), 100, 70, "drop 0 .08")
    + ring(660, 520, 430, 62, "draw .5 .7", AM, 9, 4)
    + A(stamp("RECEIVED", 104, -8), 900, 690, "slam .8 .86", "z-index:60")
    + A(big("15<br>WORDS", 104), 1470, 150, "slam .1 .16") + A(big("1<br>NOTE.", 104, AM), 1470, 420, "slam .4 .46")
    + a(tag("STUDIO DRAWING", 18), 1470, 880),
    "WHY IT HAPPENS, IN PLAIN TERMS: MEMORY KEEPS THE GIST MORE THAN THE EXACT WORDS (FUZZY-TRACE THEORY, BRAINERD & REYNA) · THE SHEET IS A STUDIO DRAWING"))

# 20 · "Bed, rest, tired, snooze, doze. Every word points at the same spot. And the spot is empty. So your brain fills it..."
small = lambda w_, rot: icard(CENTER(mono(w_, 62, INK, 6)), 330, 170, rot, pad=16, top=52, line=38)
scrib = (f'<svg width="440" height="220" viewBox="0 0 440 220" style="filter:url(#wob)"><path d="M30 120 C80 30 110 200 160 110 S240 40 270 130 S350 190 410 80 M40 160 C120 110 200 200 300 140 S380 120 420 160" fill="none" stroke="{AM}" stroke-width="22" stroke-linecap="round"/></svg>')
put("20_arrows", page(
    A(small("BED", -4), 100, 110, "drop 0 .06") + A(small("REST", 3), 640, 60, "drop .04 .1") + A(small("TIRED", -2), 1190, 90, "drop .08 .14")
    + A(small("SNOOZE", 4), 1500, 380, "drop .12 .18") + A(small("DOZE", 3), 90, 600, "drop .16 .22")
    + a(sheet("", 330, 170, 7, bg=FOLD, pad=0, sh=SH2), 1470, 700) + a(sheet("", 330, 170, -3, bg=FOLD, pad=0, sh=SH2), 1450, 680) + a(sheet(CENTER(mono("+10 MORE", 44, INK, 4)), 330, 170, 2, bg=CARD, pad=0, sh=SH2), 1440, 660)
    + a(f'<div style="width:500px;height:270px;box-sizing:border-box;border:8px dashed {PAPER};background:rgba(20,24,36,.7);display:flex;align-items:center;justify-content:center"><div data-anim="fade .6 .7">{scrib}</div></div>', 710, 390, "z-index:30")
    + arrow(330, 290, 720, 430, "draw .25 .4", CO, 9, 30) + arrow(810, 240, 900, 380, "draw .3 .45", CO, 9, 20) + arrow(1300, 270, 1150, 390, "draw .35 .5", CO, 9, -20)
    + arrow(1490, 480, 1220, 520, "draw .4 .55", CO, 9, 20) + arrow(430, 680, 700, 600, "draw .45 .6", CO, 9, -20) + arrow(1430, 730, 1215, 640, "draw .5 .65", CO, 9, 20)
    + A(stamp("RECEIVED", 78, -8), 800, 610, "slam .8 .86", "z-index:60")
    + A(big("EVERY WORD POINTS AT ONE SPOT.", 62), 250, 850, "wipe .2 .5") + A(big("YOU FILLED IT IN.", 62, AM), 250, 925, "slam .7 .76"),
    "DIAGRAM: THE LIST'S WORDS ARE ALL ASSOCIATES OF ONE WORD THAT IS NEVER PRESENTED (" + S_DRM + ") · THE BOX IS LEFT ILLEGIBLE ON PURPOSE"))

# 21 · "Then failure number two. Did I hear that, or did I just think it? You thought it. The manager filed it as heard."
box_ = lambda lab, ticked: (f'<div style="display:flex;align-items:center;gap:28px"><div style="width:150px;height:150px;border:12px solid {INK};box-sizing:border-box;position:relative">'
                            + (f'<svg width="270" height="230" viewBox="0 0 270 230" style="position:absolute;left:-30px;top:-80px"><path d="M30 130 L100 200 L250 20" fill="none" stroke="{AM}" stroke-width="46" stroke-linecap="round" stroke-linejoin="round"/></svg>' if ticked else "")
                            + f'</div>{big(lab, 88, INK)}</div>')
put("21_form", page(
    a(sheet("", 1500, 860, -3, bg="#B9C9DE", pad=0), 250, 120)
    + A(sheet(mono("INTAKE FORM 2 · WHERE DID THIS MEMORY COME FROM? · STUDIO DRAWING", 22, CO, 4) + RULE(CO, "16px 0 34px", 4)
              + big("DID I HEAR IT,<br>OR JUST THINK IT?", 100, INK) + GAP(70)
              + f'<div style="display:flex;gap:80px">{box_("HEARD", True)}{box_("THOUGHT", False)}</div>', 1500, 860, -1, bg="#DDE7F3", pad=60), 200, 90, "up 0 .1")
    + A(tag("FAILURE NUMBER TWO", 32, amber=True, rot=-3), 100, 56, "slam .05 .1", "z-index:60")
    + A(stamp("FILED", 150, -10), 1240, 660, "slam .8 .86", "z-index:60"),
    "THE SECOND FAILURE, IN PLAIN TERMS: MEMORY IS POOR AT TELLING \"I HEARD IT\" FROM \"I THOUGHT IT\" (SOURCE MONITORING: JOHNSON, HASHTROUDI & LINDSAY 1993)"))

# 22 · "James Deese found this back in 1959... largely overlooked, until Roediger and McDermott revived it in 1995. Thirty-six years."
X = lambda y: 150 + (y - 1959) / 36 * 1620
yrs = "".join(f'<div class="a" style="left:{X(y) - 3:.0f}px;top:{622 if y in (1959, 1995) else 632}px;width:6px;height:{44 if y in (1959, 1995) else 24}px;background:{PAPER}"></div>'
              f'<div class="a" style="left:{X(y) - 34:.0f}px;top:672px;font:500 22px Mono;color:{PAPER if y in (1959, 1995) else DIM}">{y}</div>' for y in range(1959, 1996, 4))
put("22_timeline", page(
    a(f'<div style="width:1620px;height:8px;background:{PAPER}"></div>', 150, 640) + yrs
    + A(study("James Deese", 1959, "J. Exp. Psychol.", n="36 LISTS OF 12 WORDS", w=540, rot=-2), 80, 150, "drop 0 .08")
    + A(study("Roediger &amp; McDermott", 1995, "J. Exp. Psychol.: LMC", n="THE REVIVAL", w=600, rot=2), 1240, 130, "drop .5 .58")
    + A(f'<div style="width:1620px;height:14px;background:{AM}"></div>', 150, 730, "growx .1 .5")
    + a(f'<div style="width:14px;height:50px;background:{AM}"></div>', 150, 712) + A(f'<div style="width:14px;height:50px;background:{AM}"></div>', 1756, 712, "snap .5 .5")
    + A(big("36 YEARS", 150, AM), 470, 770, "slam .6 .66")
    + A(sticky("re: memory.<br>misplaced.", 320, -5, 62), 720, 300, "slam .7 .76", "z-index:60")
    + A(big("55%", 130), 1420, 780, "slam .85 .9") + a(tag("WROTE DOWN THE MISSING WORD", 18), 1410, 930),
    "DEESE 1959 (36 LISTS OF 12 WORDS; LARGELY OVERLOOKED FOR 36 YEARS) · " + S_DRM + ": MISSING WORD RECALLED 55% OF THE TIME IN EXPERIMENT 2"))

# 23 · "Memory works a little bit more like a Wikipedia page: you can go in there and change it, but so can other people." Including me. Just now.
put("23_loftus", page(
    A(sheet(mono("TEDGLOBAL 2013 · ELIZABETH LOFTUS · \"HOW RELIABLE IS YOUR MEMORY?\" · TRANSCRIPT, TYPESET", 21, CO, 3) + RULE(CO, "16px 0 44px", 4)
            + quote("“Memory works a little bit more like a Wikipedia page: you can go in there and change it, " + hl("but so can other people.") + "”", 104, INK, 1420), 1580, 800, -1, pad=76), 170, 120, "drop 0 .08")
    + A(tag("THE RECEIPT", 30, amber=True, rot=-3), 100, 70, "slam .05 .1", "z-index:60")
    + A(tag("EDIT BY: NARRATOR, 0:18", 32, inv=True, rot=3), 1180, 880, "slam .8 .86", "z-index:60"),
    "ELIZABETH LOFTUS, TEDGLOBAL 2013, \"HOW RELIABLE IS YOUR MEMORY?\" (TRANSCRIPT) · QUOTED WORD FOR WORD; TYPESET, NOT A SCREENSHOT"))

# 24 · "So researchers tested 20 people who remember their own lives extraordinarily well. Against 38 controls... They fell for it just as easily."
def group(n, cols, w, col):
    cw = w / cols; s = cw / 112; rows_ = (n + cols - 1) // cols
    return f'<svg width="{w}" height="{rows_ * cw * 1.2:.0f}">' + "".join(bust((i % cols) * cw + 6 * s, (i // cols) * cw * 1.2, s, col) for i in range(n)) + "</svg>"
put("24_hsam", page(
    A(study("Patihis et al.", 2013, "PNAS", n="N = 20, AGAINST 38 MATCHED CONTROLS", w=700, rot=-1.5), 90, 50, "drop 0 .08", "z-index:40")
    + A(big("JUST AS EASILY.", 104), 900, 96, "slam .85 .9", "z-index:60")
    + A(group(20, 5, 480, AM), 110, 330, "fill .1 .3") + A(group(38, 8, 760, CO), 900, 330, "fill .3 .55")
    + a(tag("20 · EXTRAORDINARY MEMORIES", 24, amber=True), 110, 930) + a(tag("38 · CONTROLS", 24, inv=True), 900, 930)
    + A(sheet(stamp("SUSCEPTIBLE", 58, 0), 520, 132, -7, pad=20, sh=SH2), 100, 520, "slam .7 .76", "z-index:60")
    + A(sheet(stamp("SUSCEPTIBLE", 58, 0), 520, 132, -5, pad=20, sh=SH2), 1030, 560, "slam .76 .82", "z-index:60"),
    "PATIHIS ET AL. 2013, PNAS: 20 PEOPLE WITH HIGHLY SUPERIOR AUTOBIOGRAPHICAL MEMORY WERE AS SUSCEPTIBLE TO FALSE MEMORIES AS 38 CONTROLS, WORD LISTS INCLUDED"))

# 25 · "Peer review's gentlest way of saying: same manager, nicer office."
put("25_office", page(
    A(P.manager(sheet_text="", desk=True, w=900, h=1065), 520, 60, "up 0 .12")
    + A(tag("SAME MANAGER, NICER OFFICE", 40, inv=True, rot=-2), 100, 90, "slam .3 .36", "z-index:60")
    + A(sheet(mono("CERTIFICATE", 20, CO, 6) + GAP(10) + big("MOST<br>CONFIDENT", 54, INK) + GAP(12) + mono("AWARDED BY: ITSELF", 20, INK, 3), 400, 320, -4, pad=30, sh=SH2, extra=f"border:8px solid {CO}"), 110, 330, "drop .5 .58")
    + a(tag("METAPHOR", 20), 110, 720)
    + A(hand("extraordinary<br>memories get<br>rebuilt too.", 74, AM, -2), 1470, 230, "wipe .6 .9"),
    "SIGHT GAG (STUDIO DRAWING) · THE POINT BEHIND IT: PATIHIS ET AL. 2013, PNAS (PARAPHRASED, NOT QUOTED)"))

# 26 · "Objection: those are words. Something that mattered, you'd remember."
put("26_objection", page(
    A(tag("OBJECTION", 40, amber=True, rot=-3), 100, 70, "slam 0 .06")
    + A(big("“IF IT<br>MATTERED,<br>I'D REMEMBER.”", 168), 96, 200, "wipe .1 .5")
    + A(hand("okay. something that mattered.", 96, AM, -2), 110, 790, "wipe .65 .95"),
    "THE VIEWER'S OBJECTION (OUR WORDING) · ANSWERED BY " + S_NH))

# ==== ACT 2 ==================================================================================================================
# 27 · "You have one of these: the day of some enormous news. You can still see the room. Psychologists call them flashbulb memories."
put("27_flashbulb", page(
    A(P.flashbulb(400), 60, 30, "pop 0 .06")
    + A(big("FLASHBULB<br>MEMORY", 132), 96, 440, "slam .4 .46")
    + A(hand("you can still see the room.", 78, PAPER, -2), 104, 730, "wipe .2 .4")
    + A(f'<div style="background:#FBFCFE;padding:18px 18px 70px;{SH};transform:rotate(2.5deg);position:relative">{P.room(800, 520)}'
        f'<div style="position:absolute;left:22px;bottom:18px;font:500 22px Mono;letter-spacing:4px;color:{INK}">THE DAY OF THE NEWS</div></div>', 1010, 90, "draw .08 .4")
    + A(P.banknote(520, 240, -7), 1180, 760, "slam .7 .76", "z-index:60")
    + A(tag("YOU'D BET MONEY ON YOURS", 26, inv=True, rot=3), 1330, 700, "slam .8 .86", "z-index:61"),
    "\"FLASHBULB MEMORIES\": VIVID MEMORIES OF HOW YOU HEARD SHOCKING NEWS (TERM: BROWN & KULIK 1977) · THE ROOM AND THE NOTE ARE STUDIO DRAWINGS"))

# 28 · "28 January 1986. The space shuttle Challenger launches with seven crew aboard."  (real photo; no gag, no stamp)
put("28_challenger", page(
    full("challenger_launch", "50% 38%", .06)
    + A(tag("28 JAN 1986 · KENNEDY SPACE CENTER", 36, inv=True), 96, 84, "snap .05 .05", "z-index:40")
    + A(tag("CHALLENGER LIFTS OFF, SEVEN CREW ABOARD", 24), 96, 170, "snap .2 .2", "z-index:40"),
    "PHOTO: NASA 51L-S-156, PUBLIC DOMAIN · LIFTOFF FROM PAD 39B AT 11:38 A.M. EST, 28 JAN 1986 (NASA IMAGE RECORD)", ticks=False))

# 29 · "Seventy-three seconds later, it breaks apart."  (slate, silence)
put("29_seconds", page(
    A(big("73", 540), 110, 150, "fade 0 .1")
    + A(big("SECONDS", 150), 1000, 330, "fade .1 .2")
    + A(mono("AFTER LIFTOFF, AN ACCIDENT CLAIMED THE CREW AND THE VEHICLE.", 34, PAPER, 3, 1.5, 820), 1006, 520, "fade .3 .5")
    + a(tag("NASA IMAGE RECORD 51L-S-156", 20), 1006, 760),
    "NASA: \"AN ACCIDENT 73 SECONDS AFTER LIFTOFF CLAIMED BOTH CREW AND VEHICLE\" (IMAGE RECORD 51L-S-156) · NO FOOTAGE OF THE BREAK-UP IS SHOWN"))

# 30 · "The next morning, 106 psychology students at Emory University were asked to write down how they heard."
put("30_class", page(
    A(photo("lecture_hall", 1080, 720, -1.5, "50% 55%", anim="push 0 1"), 60, 100, "drop 0 .08")
    + A(big("106", 270, AM), 1250, 130, "slam .2 .26") + A(big("STUDENTS", 96), 1256, 400, "slam .3 .36")
    + A(tag("THE NEXT MORNING", 34, amber=True, rot=-3), 1256, 560, "slam .5 .56")
    + A(hand("asked to write down<br>how they heard.", 70, PAPER, -2), 1262, 670, "wipe .6 .9"),
    "PHOTO: COGDOGBLOG, CC0 (ILLUSTRATIVE: NOT EMORY, NOT 1986) · 106 EMORY PSYCHOLOGY STUDENTS, THE MORNING AFTER: " + S_NH))

# 31 · "In their own handwriting. While it was fresh."
field = lambda lab, seed, n=2: mono(lab, 30, INK, 3) + GAP(6) + P.squiggles(n, 980, seed, CO) + GAP(22)
put("31_questionnaire", page(
    A(sheet(mono("QUESTIONNAIRE · 29 JAN 1986 · RECONSTRUCTION, WORDING OURS", 20, CO, 3) + GAP(10) + big("HOW DID YOU HEAR THE NEWS?", 50, INK) + RULE(INK, "16px 0 26px")
            + field("WHERE WERE YOU?", 3) + field("WHO TOLD YOU?", 7) + field("WHAT WERE YOU DOING?", 11) + field("HOW SURE ARE YOU?", 19, 1), 1140, 900, -1.2, pad=60), 90, 70, "drop 0 .08")
    + A(tag("IN THEIR OWN HANDWRITING", 28, amber=True, rot=3), 1320, 170, "slam .3 .36", "z-index:60")
    + A(f'<div style="transform:rotate(-38deg)">{P.pencil(520, col=CO)}</div>', 1330, 420, "up .2 .3")
    + A(hand("while it<br>was fresh.", 96, PAPER, -3), 1340, 640, "wipe .6 .9"),
    "THE FORM IS A RECONSTRUCTION AND THE HANDWRITING IS A STAND-IN: NO STUDENT'S ANSWER IS INVENTED · " + S_NH))

# 32 · "Then the researchers, Neisser and Harsch, put the answers away. For about two and a half years. Psychology is patient like that."
put("32_box", page(
    A(P.box(840, 560), 100, 240, "up 0 .1")
    + A(sticky("DO NOT OPEN<br>UNTIL 1988", 340, 5, 60), 650, 120, "slam .3 .36", "z-index:60")
    + a(tag("ABOUT", 28), 1070, 250) + A(big("2&#189; YEARS", 128, AM), 1064, 310, "slam .5 .56")
    + a(f'<div style="width:760px;height:8px;background:{PAPER}"></div>', 1070, 560) + a(f'<div style="width:8px;height:44px;background:{PAPER}"></div>', 1070, 542) + a(f'<div style="width:8px;height:44px;background:{PAPER}"></div>', 1822, 542)
    + A(f'<div style="width:760px;height:14px;background:{AM}"></div>', 1070, 557, "growx .4 .8")
    + a(mono("JAN 1986", 26, PAPER, 3), 1070, 610) + a(mono("THE RETEST", 26, PAPER, 3), 1660, 610)
    + A(tag("PSYCHOLOGY IS PATIENT LIKE THAT", 24, inv=True, rot=2), 1080, 740, "slam .85 .9"),
    "THE ANSWERS WERE KEPT FOR ABOUT TWO AND A HALF YEARS, THEN 44 OF THE STUDENTS ANSWERED AGAIN: " + S_NH + " · THE BOX IS A STUDIO DRAWING"))

# 33 · "Scored against their own first answers, out of seven, the average was 2.95. Eleven scored zero... Twenty-two scored two or less. Half the room."
dots = ""
for i in range(44):
    x, y = (i % 11) * 76 + 38, (i // 11) * 84 + 40
    if i < 11:
        dots += f'<circle cx="{x}" cy="{y}" r="29" fill="{AM}"/>'
    elif i < 22:
        dots += f'<circle cx="{x}" cy="{y}" r="25" fill="none" stroke="{AM}" stroke-width="8"/>'
    else:
        dots += f'<circle cx="{x}" cy="{y}" r="29" fill="{DIM}" opacity=".55"/>'
scale = "".join(f'<div style="position:absolute;left:{i * 110 - 3}px;top:-16px;width:6px;height:40px;background:{PAPER}"></div><div style="position:absolute;left:{i * 110 - 9}px;top:34px;font:500 26px Mono;color:{PAPER}">{i}</div>' for i in range(8))
put("33_scores", page(
    A(study("Neisser &amp; Harsch", 1992, "“Phantom flashbulbs”", n="N = 106, THEN 44 RETESTED", w=720, rot=-1.5), 80, 70, "drop 0 .08")
    + A(big("2.95", 290, AM), 84, 380, "slam .2 .26") + a(mono("AVERAGE SCORE, OUT OF 7", 32, PAPER, 3), 96, 690)
    + a(f'<div style="position:relative;width:770px;height:8px;background:{PAPER}">{scale}<div style="position:absolute;left:{2.95 * 110 - 14:.0f}px;top:-46px;width:28px;height:28px;background:{AM};transform:rotate(45deg)"></div></div>', 100, 810)
    + A(f'<svg width="836" height="336">{dots}</svg>', 1000, 190, "fill .3 .7")
    + A(tag("11 SCORED ZERO", 28, amber=True, rot=-2), 1000, 110, "slam .5 .56")
    + A(tag("22 SCORED 2 OR LESS: HALF THE ROOM", 24, inv=True, rot=1), 1000, 560, "slam .75 .8")
    + a(mono("THE OTHER 22 SCORED 3 TO 7 (NOT BROKEN OUT)", 20, DIM, 2), 1004, 640)
    + A(hand("on their own lives.", 86, PAPER, -3), 1080, 730, "wipe .85 1"),
    S_NH + " · EACH DOT IS ONE OF THE 44 RETESTED STUDENTS, SCORED AGAINST THEIR OWN FIRST ANSWERS"))

# 34 · "Surely they knew they were fuzzy. They did not. Average confidence: 4.17 out of 5. And confidence had nothing to do with accuracy."
rnd = random.Random(8)
cloud = "".join(f'<circle cx="{60 + rnd.random() * 560:.0f}" cy="{70 + rnd.random() * 130:.0f}" r="13" fill="{AM}" opacity=".85"/>' for _ in range(44))
ruler5 = "".join(f'<div style="position:absolute;left:{i * 190 - 3}px;top:-18px;width:6px;height:44px;background:{PAPER}"></div><div style="position:absolute;left:{i * 190 - 9}px;top:36px;font:500 26px Mono;color:{PAPER}">{i + 1}</div>' for i in range(5))
put("34_confidence", page(
    A(f'<div style="position:relative;display:inline-block">{big("“THEY KNEW.”", 120)}{strike(900, CO, 18, -3)}</div>', 90, 70, "slam 0 .06")
    + A(big("4.17", 300, AM), 84, 300, "slam .25 .31") + a(mono("AVERAGE CONFIDENCE, OUT OF 5", 32, PAPER, 3), 96, 620)
    + a(f'<div style="position:relative;width:760px;height:8px;background:{PAPER}">{ruler5}<div data-anim="growx .3 .6" style="position:absolute;left:0;top:-5px;width:{(4.17 - 1) / 4 * 760:.0f}px;height:18px;background:{AM}"></div></div>', 100, 760)
    + a(f'<div style="width:700px;height:560px;box-sizing:border-box;border-left:8px solid {PAPER};border-bottom:8px solid {PAPER};position:relative"><svg width="680" height="540">{cloud}</svg>'
        f'<div style="position:absolute;left:-58px;top:210px;font:500 24px Mono;letter-spacing:5px;color:{PAPER};transform:rotate(-90deg);transform-origin:0 0;white-space:nowrap;margin-top:160px">CONFIDENCE</div>'
        f'<div style="position:absolute;left:250px;bottom:-50px;font:500 24px Mono;letter-spacing:5px;color:{PAPER}">ACCURACY</div></div>', 1120, 130)
    + A(tag("UNRELATED", 40, amber=True, rot=-3), 1300, 430, "slam .8 .86", "z-index:60")
    + a(tag("AS REPORTED · DOT POSITIONS ILLUSTRATIVE", 18), 1130, 790),
    S_NH + ": MEAN CONFIDENCE 4.17 OF 5; CONFIDENCE UNRELATED TO ACCURACY · THE CLOUD SHOWS THE FINDING'S SHAPE, NOT THE STUDY'S DATA POINTS"))

# 35 · "It's a sat-nav announcing 'You have arrived' from the middle of a lake."
wave = "M0 60 " + " ".join(f"Q {x + 60} {20 if (x // 120) % 2 else 100} {x + 120} 60" for x in range(0, 1920, 120)) + " V700 H0 Z"
put("35_satnav", page(
    a(f'<svg width="1920" height="700" viewBox="0 0 1920 700"><path d="{wave}" fill="{CO}"/><path d="M0 200 Q 480 150 960 200 T1920 200" fill="none" stroke="rgba(240,244,248,.25)" stroke-width="8"/>'
      f'<path d="M0 380 Q 480 330 960 380 T1920 380" fill="none" stroke="rgba(240,244,248,.18)" stroke-width="8"/><path d="M0 540 Q 480 500 960 540 T1920 540" fill="none" stroke="rgba(240,244,248,.12)" stroke-width="8"/></svg>', 0, 440, "z-index:20")
    + a(f'<svg width="460" height="200" viewBox="0 0 460 200" style="overflow:visible;filter:drop-shadow(10px 12px 0 rgba(5,7,12,.35))"><path d="M40 200 C40 90 110 30 230 30 C350 30 420 90 420 200 Z" fill="{CARD}" stroke="#FBFCFE" stroke-width="8"/>'
        f'<path d="M96 200 C100 130 150 86 230 86 C310 86 360 130 364 200 Z" fill="{INK}"/><rect x="224" y="86" width="12" height="114" fill="{CARD}"/></svg>', 700, 300, "z-index:10")
    + A(sheet(mono("SAT NAV", 22, CO, 6) + GAP(8) + big("YOU HAVE<br>ARRIVED.", 84, INK), 560, 300, -4, pad=36, sh=SH2), 1130, 70, "slam .3 .36", "z-index:40")
    + arrow(1150, 330, 960, 390, "draw .4 .55", AM, 9, -20)
    + A(tag("AVERAGE CONFIDENCE: 4.17 / 5", 32, amber=True, rot=-3), 96, 90, "slam .05 .1", "z-index:40")
    + a(tag("SIGHT GAG", 18), 96, 190, "z-index:40"),
    "SIGHT GAG (STUDIO DRAWING) · THE FINDING BEHIND IT: " + S_NH))

# 36 · "Then they saw their first answers, in their own handwriting. Most were surprised. And most kept the new version."
pg = lambda head, sub, seed, col: (mono(sub, 26, col, 5) + GAP(6) + big(head, 60, INK) + RULE(INK, "16px 0 30px") + P.squiggles(11, 620, seed, CO, 56, 4))
put("36_split", page(
    A(sheet(pg("FIRST ANSWERS", "JANUARY 1986", 3, CO), 760, 880, -3, pad=56), 110, 80, "drop 0 .08")
    + A(sheet(pg("NEW ANSWERS", "ABOUT 2.5 YEARS LATER", 14, AM), 760, 880, 3, pad=56), 600, 90, "up .4 .6")
    + A(tag("MOST WERE SURPRISED", 28, inv=True, rot=-2), 1440, 200, "slam .65 .7", "z-index:60")
    + A(tag("MOST KEPT THE NEW VERSION", 24, amber=True, rot=3), 1420, 320, "slam .8 .86", "z-index:60")
    + A(hand("same people.<br>same news.<br>new story.", 76, PAPER, -3), 1450, 470, "wipe .86 1")
    + a(tag("RECONSTRUCTION · STAND-IN HANDWRITING", 16), 1440, 800),
    "SHOWN THEIR FIRST ANSWERS IN THEIR OWN HANDWRITING, MOST WERE SURPRISED AND MOST KEPT THE NEW VERSION: " + S_NH + " (VIA SUMMARIES; THE CHAPTER ITSELF TO BE CHECKED)"))
