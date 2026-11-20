"""Key frames, act 3 "A day that never happened" (5:07-6:36), act 4 "The witness box" (6:36-8:29) and act 5 "Collecting" (8:29-9:52).
Numbers and names only from DOSSIER.md. The 1984 crime is never depicted; the two real people appear once, in a credited photo."""
from kit import (A, a, put, page, big, mono, tag, hand, quote, stamp, sheet, icard, sticky, study, photo, ring, arrow, strike, bust, crowd, bars, hl, clip,
                 SL, PAPER, CO, AM, RED, INK, CARD, FOLD, DIM, SH, SH2)
import props as P

CENTER = lambda inner: f'<div style="display:flex;align-items:center;justify-content:center;height:100%;width:100%">{inner}</div>'
RULE = lambda col=INK, m="18px 0 28px", h=5: f'<div style="height:{h}px;background:{col};margin:{m}"></div>'
GAP = lambda h: f'<div style="height:{h}px"></div>'
S_LP = "LOFTUS & PICKRELL 1995, PSYCHIATRIC ANNALS 25(12)"
S_MU = "MURPHY ET AL. 2023, MEMORY 31(6) (UNIVERSITY COLLEGE CORK AND UNIVERSITY COLLEGE DUBLIN)"
S_IP = "INNOCENCE PROJECT, \"DNA EXONERATIONS IN THE UNITED STATES (1989-2020)\""
S_LMB = "LOFTUS, MILLER & BURNS 1978, J. EXP. PSYCHOL.: HUMAN LEARNING AND MEMORY 4(1)"
frame = lambda inner, rot=-.6: f'<div style="background:#FBFCFE;padding:14px;{SH};transform:rotate({rot}deg)">{inner}</div>'
tickm = lambda s=64: f'<svg width="{s}" height="{s}" viewBox="0 0 150 130"><path d="M14 70 L58 112 L136 16" fill="none" stroke="{CO}" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/></svg>'

# ==== ACT 3 ==================================================================================================================
# 37 · "In a 1995 study, Loftus and Pickrell tried exactly that."
put("37_mall", page(
    A(photo("mall", 1080, 700, -1.5, "50% 50%", anim="push 0 1"), 60, 110, "drop 0 .08")
    + A(study("Loftus &amp; Pickrell", 1995, "Psychiatric Annals", n="N = 24", w=560, rot=2), 1250, 90, "drop .15 .22")
    + A(big("A WHOLE DAY", 82), 1250, 400, "slam .3 .36") + A(big("THAT NEVER<br>HAPPENED?", 82, AM), 1250, 490, "slam .4 .46")
    + A(hand("they tried exactly that.", 70, PAPER, -2), 1256, 720, "wipe .6 .9"),
    "PHOTO: CHRIS.RYCROFT, CC BY 2.0 (ILLUSTRATIVE: NO PARTICULAR MALL) · " + S_LP))

# 38 · "Twenty-four people got a booklet of childhood stories, supplied by a relative. Three true. One invented: you, lost in a shopping mall..."
entry = lambda n, seed: (f'<div style="display:flex;justify-content:space-between;align-items:center">{mono(f"STORY {n} · FROM A RELATIVE", 22, CO, 3)}{tickm(56)}</div>' + GAP(4) + P.squiggles(5, 500, seed, INK, 50, 4) + GAP(26))
put("38_booklet", page(
    A(sheet(mono("YOUR CHILDHOOD", 22, CO, 6) + RULE(CO, "12px 0 26px", 4) + entry(1, 21) + entry(2, 33), 660, 820, -1.5, pad=54), 70, 130, "drop 0 .08")
    + A(sheet(mono("CONTINUED", 22, CO, 6) + RULE(CO, "12px 0 26px", 4) + entry(3, 45)
              + f'<div style="background:{CARD};padding:22px 24px;box-shadow:6px 8px 0 rgba(5,7,12,.3);transform:rotate(-2deg)">{mono("STORY 4", 22, CO, 3)}{GAP(8)}'
                f'<div style="font:500 36px/1.4 Mono;color:{INK}">{hl("LOST IN A SHOPPING MALL, AGED ABOUT FIVE.")}</div></div>', 660, 820, 1, pad=54), 740, 120, "drop .1 .18")
    + a(f'<div style="width:14px;height:820px;background:linear-gradient(90deg,rgba(5,7,12,.3),transparent)"></div>', 742, 126, "z-index:30")
    + clip(1290, 470, 14)
    + A(tag("INVENTED", 40, amber=True, rot=5), 1130, 760, "slam .7 .76", "z-index:60")
    + A(big("3 TRUE.", 76), 1464, 230, "slam .3 .36") + A(big("1 NOT.", 76, AM), 1464, 320, "slam .6 .66")
    + a(tag("RECONSTRUCTION", 20), 1468, 450) + A(hand("stand-in<br>handwriting:<br>no story is<br>invented by us.", 50, DIM, -2), 1470, 530, "fade .2 .4"),
    "A BOOKLET OF CHILDHOOD STORIES SUPPLIED BY A RELATIVE: THREE TRUE, ONE INVENTED (LOST IN A SHOPPING MALL AT ABOUT FIVE) · " + S_LP + " · RECONSTRUCTION"))

# 39 · "Six of the 24 came to remember the invented one. One in four. Their own childhood, and they accepted fan fiction."
put("39_grid24", page(
    A(crowd(8, 3, 1120, 600, lit=(2, 5, 9, 12, 19, 22), col=DIM, lit_col=AM), 70, 130, "fill 0 .3")
    + A(tag("6 OF THE 24 CAME TO REMEMBER IT", 28, amber=True, rot=-2), 90, 790, "slam .4 .46")
    + A(big("25%", 250, AM), 1270, 110, "slam .3 .36")
    + A(big("ONE IN<br>FOUR", 96), 1276, 380, "slam .45 .5")
    + A(tag("FAN FICTION · AUTHOR: THE LAB", 24, inv=True, rot=-3), 1270, 640, "slam .75 .8")
    + A(hand("their own childhood.", 76, PAPER, -2), 1276, 760, "wipe .8 1"),
    S_LP + ": 6 OF 24 PARTICIPANTS (25%) CAME TO REMEMBER THE INVENTED EVENT"))

# 40 · "But we check the science here. In 2023, a team in Ireland ran it again: 123 people... 35 percent... Eight percent full. Twenty-seven percent partial."
PX = 13.6  # pixels per percentage point on the 0-50% axis
axis = "".join(f'<div style="position:absolute;left:-76px;bottom:{v * PX - 14:.0f}px;font:500 26px Mono;color:{PAPER};width:60px;text-align:right">{v}</div>'
               f'<div style="position:absolute;left:-10px;bottom:{v * PX - 3:.0f}px;width:10px;height:6px;background:{PAPER}"></div>' for v in range(0, 51, 10))
put("40_replication", page(
    A(study("Murphy et al.", 2023, "Memory", n="N = 123 · CORK AND DUBLIN", w=640, rot=-1.5), 90, 80, "drop 0 .08")
    + A(stamp("REPLICATED 2023", 74, -7, sub="N = 123"), 300, 290, "slam .3 .36", "z-index:60")
    + A(f'<div style="width:240px;min-height:190px;box-sizing:border-box;background:#F7CFA5;padding:22px;transform:rotate(6deg);box-shadow:8px 12px 0 rgba(5,7,12,.38);font:400 76px/1 Marker;color:{RED}">CHECK</div>', 800, 60, "slam .05 .1", "z-index:60")
    + A(big("35%", 230, AM), 90, 560, "slam .5 .56") + a(mono("CODED AS REPORTING A FALSE MEMORY OF THE MALL", 26, PAPER, 2, 1.4, 760), 100, 800)
    + a(f'<div style="position:relative;width:300px;height:{50 * PX:.0f}px;border-left:8px solid {PAPER};border-bottom:8px solid {PAPER}">{axis}'
        f'<div data-anim="grow .5 .8" style="position:absolute;left:50px;bottom:0;width:230px;height:{35 * PX:.0f}px;background:repeating-linear-gradient(45deg,{AM} 0 12px,rgba(237,137,54,.35) 12px 24px)"></div>'
        f'<div data-anim="grow .5 .7" style="position:absolute;left:50px;bottom:0;width:230px;height:{8 * PX:.0f}px;background:{AM}"></div></div>', 1280, 150)
    + a(mono("%", 26, PAPER), 1216, 110)
    + A(tag("27% PARTIAL", 28, inv=True, rot=-2), 1610, 440, "slam .8 .86") + A(tag("8% FULL", 28, amber=True, rot=2), 1610, 740, "slam .7 .76")
    + a(tag("PLAN FIXED IN ADVANCE", 20), 1300, 880),
    S_MU + ": A PREREGISTERED REPLICATION, N = 123; 35% CODED AS REPORTING A FALSE MEMORY (8% FULL, 27% PARTIAL)"))

# 41 · "Case closed? Not quite. Critics went back through the same data... some may simply remember really getting lost... 4 percent. That reading is disputed too."
put("41_critics", page(
    A(study("Andrews &amp; Brewin", 2024, "A reanalysis of the same data", w=620, rot=4), 90, 90, "drop 0 .08")
    + A(stamp("DISPUTED", 104, -9), 250, 300, "slam .8 .86", "z-index:60")
    + A(frame(P.floorplan(840, 574), 2), 990, 80, "drop .15 .22") + a(tag("ILLUSTRATION", 18), 1020, 700, "z-index:60")
    + A(hand("some may simply remember<br>really getting lost.", 66, PAPER, -2), 1010, 770, "wipe .3 .6")
    + A(big("4%", 250, AM), 90, 520, "slam .55 .6")
    + a(mono("THE CRITICS' COUNT, FULL FALSE MEMORIES ONLY", 26, PAPER, 2, 1.4, 780), 100, 790)
    + A(tag("CASE CLOSED? NOT QUITE.", 28, inv=True, rot=-2), 520, 560, "slam .05 .1"),
    "ANDREWS & BREWIN 2024 REANALYSED " + S_MU.split(" (")[0] + ": ABOUT HALF THE REPORTS MAY BE REAL MEMORIES; 4% FULL FALSE MEMORIES · THAT READING IS ITSELF DISPUTED"))

# 42 · "Pool eight studies and 423 people, and it's about 30. Depending on who's counting: from 4 percent to about a third. Not most people. But not nobody."
RX = lambda v: 160 + v * 32
def flag(v, label, sub, top, col=AM, size=80, w=420, right=False):
    x = RX(v)
    al = f"right:{1920 - x - 4:.0f}px;text-align:right" if right else f"left:{x - 4:.0f}px"
    return (f'<div class="a" style="left:{x - 4:.0f}px;top:{top + 96}px;width:8px;height:{520 - top - 96}px;background:{col}"></div>'
            f'<div class="a" style="{al};top:{top}px;width:{w}px"><div style="font:400 {size}px/1 Black;color:{col}">{label}</div>'
            f'<div style="font:500 20px/1.3 Mono;letter-spacing:2px;color:{PAPER};margin-top:6px">{sub}</div></div>')
rticks = "".join(f'<div class="a" style="left:{RX(v) - 3}px;top:520px;width:6px;height:{40 if v % 10 == 0 else 20}px;background:{PAPER}"></div>'
                 + (f'<div class="a" style="left:{RX(v) - 24}px;top:566px;font:500 26px Mono;color:{PAPER}">{v}%</div>' if v % 10 == 0 else "") for v in range(0, 51, 5))
small_ = lambda v, t, right=False: (f'<div class="a" style="left:{RX(v) - 3}px;top:520px;width:6px;height:96px;background:{DIM}"></div>'
                       + (f'<div class="a" style="right:{1920 - RX(v) + 12:.0f}px;top:612px;font:500 20px/1.3 Mono;letter-spacing:1.5px;color:{DIM};width:330px;text-align:right">{t}</div>' if right else
                          f'<div class="a" style="left:{RX(v) + 12}px;top:612px;font:500 20px/1.3 Mono;letter-spacing:1.5px;color:{DIM};width:330px">{t}</div>'))
put("42_ruler", page(
    A(big("WHO'S COUNTING?", 104), 96, 60, "slam 0 .06")
    + a(f'<div style="width:1600px;height:10px;background:{PAPER}"></div>', 160, 515) + rticks
    + flag(4, "4%", "FULL ONLY:<br>THE CRITICS' COUNT", 290, AM, 80, 300) + flag(30.4, "30.4%", "POOLED: 8 STUDIES,<br>423 PEOPLE", 290, AM, 80, 330, True) + flag(35, "35%", "THE 2023<br>REPLICATION", 160, AM, 80, 300)
    + small_(15, "15% · FULL MEMORIES,<br>A 2017 REVIEW") + small_(47, "47% · SOME RECOLLECTION,<br>THE SAME REVIEW", True)
    + A(big("FROM 4% TO ABOUT A THIRD.", 80), 96, 730, "wipe .5 .8") + A(big("NOT MOST PEOPLE. BUT NOT NOBODY.", 80, AM), 96, 830, "slam .85 .9"),
    "SCOBORIA ET AL. 2017, MEMORY 25(2): 8 STUDIES, N = 423, 30.4% CLASSED AS FALSE MEMORIES · BREWIN & ANDREWS 2017, APPLIED COGNITIVE PSYCHOLOGY: 15% FULL, 47% SOME RECOLLECTION · ANDREWS & BREWIN 2024: 4% · " + S_MU.split(" (")[0] + ": 35%"))

# 43 · "Researchers doctored photos to put people on a balloon ride they never took. After three interviews, 10 of 20 remembered at least part of it. Half."
dots20 = "".join(f'<circle cx="{(i % 10) * 64 + 30}" cy="{(i // 10) * 70 + 32}" r="25" fill="{AM if i < 10 else DIM}" opacity="{1 if i < 10 else .55}"/>' for i in range(20))
paste = (f'<svg width="250" height="230" viewBox="0 0 250 230" style="overflow:visible;transform:rotate(7deg);filter:drop-shadow(8px 10px 0 rgba(5,7,12,.5))">'
         f'<path d="M6 226 L10 40 L96 4 L236 30 L244 226 Z" fill="#FBFCFE" stroke="{INK}" stroke-width="3" stroke-dasharray="12 8"/>{bust(34, 70, 1.25, INK)}{bust(140, 110, .86, INK)}'
         f'<rect x="80" y="-14" width="96" height="30" fill="rgba(214,224,236,.85)" transform="rotate(-8 128 0)"/></svg>')
put("43_balloon", page(
    A(photo("balloon_big", 1000, 700, -2, "50% 45%", cap="A HOT-AIR BALLOON (ILLUSTRATIVE) · THE PASTED FIGURES ARE OURS"), 50, 100, "drop 0 .08")
    + A(paste, 520, 500, "slam .3 .36", "z-index:40") + ring(650, 610, 190, 170, "draw .4 .6", AM, 9, 6)
    + A(study("Wade, Garry, Read &amp; Lindsay", 2002, "Psychonomic Bulletin &amp; Review", n="N = 20 · THREE INTERVIEWS", w=660, rot=1.5), 1170, 70, "drop .1 .18")
    + A(f'<svg width="640" height="140">{dots20}</svg>', 1180, 420, "fill .5 .8")
    + A(big("HALF.", 170, AM), 1172, 560, "slam .82 .88") + A(hand("from one photo.", 84, PAPER, -3), 1186, 780, "wipe .9 1"),
    "PHOTO: RAWPIXEL, CC0 (ILLUSTRATIVE; NOT THE STUDY'S PHOTO) · WADE, GARRY, READ & LINDSAY 2002: 10 OF 20 CAME TO REMEMBER AT LEAST PART OF A BALLOON RIDE THAT NEVER HAPPENED"))

# 44 · "In 2002. On software that would lose a fight with your phone."
put("44_boxing", page(
    A(big("SOFTWARE THAT WOULD LOSE A FIGHT", 62), 96, 60, "wipe 0 .3") + A(big("WITH YOUR PHONE.", 62, AM), 96, 134, "slam .35 .4")
    + a(P.boxing_ring(1560, 700), 180, 270)
    + A(P.monitor(430), 400, 360, "up .1 .2", "z-index:30") + A(f'<div style="transform:rotate(9deg)">{P.phone(200)}</div>', 1240, 400, "slam .45 .5", "z-index:30")
    + A(tag("2002", 50, inv=True, rot=-4), 470, 250, "slam .15 .2", "z-index:40") + A(tag("YOUR PHONE", 30, amber=True, rot=4), 1200, 300, "slam .5 .56", "z-index:40")
    + A(big("VS", 130, PAPER), 920, 520, "slam .6 .66", "z-index:40")
    + a(tag("SIGHT GAG", 18), 1680, 960),
    "SIGHT GAG (STUDIO DRAWING) · THE STUDY BEHIND IT WAS PUBLISHED IN 2002: WADE, GARRY, READ & LINDSAY, PSYCHONOMIC BULLETIN & REVIEW"))

# 45 · "Balloons. Malls. Word lists. Harmless. Unless the memory is the evidence."
put("45_evidence", page(
    A(P.evidence_bag(600, 780), 120, 120, "drop 0 .08")
    + A(stamp("EXHIBIT", 110, -8), 190, 520, "slam .6 .66", "z-index:60")
    + A(f'<div style="position:relative;display:inline-block">{mono("BALLOONS. MALLS. WORD LISTS. HARMLESS.", 30, DIM, 3)}</div>', 870, 170, "fade 0 .2")
    + A(big("UNLESS THE<br>MEMORY IS<br>THE EVIDENCE.", 104), 864, 260, "wipe .3 .7")
    + A(hand("then it matters who touched it.", 70, AM, -2), 872, 640, "wipe .75 1"),
    "BRIDGE TO THE WITNESS BOX · THE BAG IS A STUDIO DRAWING"))

# ==== ACT 4 ==================================================================================================================
# 46 · "375 people were cleared by DNA evidence. On average, they had served 14 years. And 69 percent had been convicted with the help of a mistaken eyewitness."
put("46_dna", page(
    A(crowd(25, 15, 1200, 840, lit=range(259), col=DIM, lit_col=AM), 50, 96, "fill 0 .5")
    + A(big("69%", 250, AM), 1300, 96, "slam .55 .6")
    + a(mono("OF 375 PEOPLE CLEARED BY DNA EVIDENCE HAD BEEN CONVICTED WITH THE HELP OF A MISTAKEN EYEWITNESS", 27, PAPER, 2, 1.45, 560), 1306, 370)
    + A(big("14 YEARS", 92), 1300, 660, "slam .75 .8") + a(mono("SERVED, ON AVERAGE", 27, PAPER, 3), 1306, 770)
    + a(tag("UNITED STATES · 1989-2020", 22, inv=True), 1306, 850),
    S_IP + ": 375 DNA EXONEREES; 69% INVOLVED EYEWITNESS MISIDENTIFICATION; 14 YEARS SERVED ON AVERAGE · EACH FIGURE IS ONE PERSON (259 OF 375 IN AMBER)"))

# 47 · "July 1984. Burlington, North Carolina. Jennifer Thompson, 22, is attacked in her home. She makes a deliberate effort to study the attacker's face."
MAP, (bx, by) = P.nc_map(1340, 660)
put("47_map", page(
    A(frame(MAP, -1), 70, 96, "drop 0 .08")
    + A(tag("BURLINGTON, NC · JULY 1984", 30, amber=True, rot=-2), 84 + bx + 50, 110 + by - 96, "slam .3 .36", "z-index:60")
    + A(icard(CENTER(f'<div style="font:500 60px/1.3 Mono;color:{INK}">She {hl("studied his face.")}</div>'), 900, 250, 3, pad=30, top=74, line=58), 930, 740, "up .6 .7", "z-index:61")
    + A(tag("JENNIFER THOMPSON, 22", 24, inv=True, rot=-2), 1462, 150, "slam .15 .2", "z-index:60")
    + A(hand("on purpose.<br>so she could<br>identify him.", 62, PAPER, -3), 1480, 300, "wipe .75 1"),
    "MAP: NATURAL EARTH STATE BOUNDARIES · THE CASE: INNOCENCE PROJECT CASE PAGE; AP, \"THE PERFECT WITNESS\" · THE ATTACK IS NOT DEPICTED"))

# 48 · "She picks Ronald Cotton from a photo lineup. Then from a live one. A detective tells her: same man, both times. She is certain."
lines = "".join(f'<div style="position:absolute;left:0;right:0;top:{60 + i * 74}px;border-top:4px solid rgba(43,108,176,.35)"></div>' for i in range(7))
nums = "".join(f'<div style="position:absolute;left:{64 + i * 240}px;top:14px;font:400 44px Black;color:{CO};width:200px;text-align:center">{i + 1}</div>' for i in range(6))
row6 = "".join(bust(64 + i * 240, 0, 2.0, INK) for i in range(6))
put("48_lineup", page(
    A(f'<div style="width:1560px;height:560px;background:{PAPER};{SH};position:relative;overflow:hidden;transform:rotate(-.6deg)">{lines}{nums}<svg width="1560" height="250" style="position:absolute;left:0;bottom:0">{row6}</svg></div>', 110, 80, "drop 0 .08")
    + ring(110 + 64 + 3 * 240 + 100, 80 + 440, 150, 170, "draw .3 .5", AM, 10, 4)
    + A(sheet(mono("WHAT A DETECTIVE TOLD HER (PARAPHRASE)", 20, CO, 3) + GAP(10) + big("SAME MAN BOTH TIMES", 62, INK), 980, 190, -2, pad=36, sh=SH2), 110, 720, "up .55 .65", "z-index:60")
    + A(stamp("CERTAIN", 112, -7), 1160, 760, "slam .8 .86", "z-index:61")
    + a(tag("ILLUSTRATION · NOT THE REAL LINEUP · NO FACES", 18), 1150, 660, "z-index:60"),
    "INNOCENCE PROJECT CASE PAGE: SHE PICKED RONALD COTTON FROM A PHOTO LINEUP, THEN A LIVE ONE; A DETECTIVE TOLD HER SHE HAD PICKED THE SAME MAN · THE LINE IS A PARAPHRASE"))

# 49 · "Cotton is convicted in January 1985 and sentenced to life... He is exonerated on 30 June 1995, after more than ten years. She wasn't lying. She was remembering."
TX = lambda y: 1010 + (y - 1985) / 10 * 780
tks = "".join(f'<div class="a" style="left:{TX(y) - 3:.0f}px;top:316px;width:6px;height:{40 if y in (1985, 1995) else 20}px;background:{PAPER}"></div>' for y in range(1985, 1996))
put("49_years", page(
    A(photo("courthouse_side", 800, 590, 2, "50% 60%"), 70, 80, "drop 0 .08")
    + A(tag("JAN 1985 · CONVICTED · LIFE", 30, inv=True, rot=-2), 110, 800, "slam .2 .26", "z-index:60")
    + A(big("10+ YEARS", 116, AM), 1004, 90, "slam .5 .56")
    + a(f'<div style="width:780px;height:8px;background:{PAPER}"></div>', 1010, 300) + tks
    + A(f'<div style="width:780px;height:16px;background:{AM}"></div>', 1010, 296, "growx .3 .6")
    + a(mono("1985", 26, PAPER, 2), 1000, 366) + a(mono("30 JUNE 1995", 26, PAPER, 2), 1620, 366)
    + A(tag("DNA CLEARED HIM AND IDENTIFIED ANOTHER MAN", 20, amber=True, rot=1), 1010, 430, "slam .62 .68")
    + A(f'<div style="position:relative;display:inline-block">{big("LYING", 104, DIM)}{strike(430, CO, 18, -3)}</div>', 1006, 560, "slam .75 .8")
    + A(big("REMEMBERING.", 88), 1006, 700, "slam .85 .9") + A(hand("that's the frightening part.", 66, AM, -2), 1014, 820, "wipe .9 1"),
    "PHOTO: W_LEMAY, CC0 (ALAMANCE COUNTY COURTHOUSE) · INNOCENCE PROJECT CASE PAGE: CONVICTED JANUARY 1985, LIFE; EXONERATED 30 JUNE 1995 AFTER MORE THAN TEN YEARS"))

# 50 · "Later, the two wrote a book together: Picking Cotton."  (the real photo, credited, framed neutrally; nothing is drawn on it)
put("50_together", page(
    A(photo("thompson_cotton", 1040, 740, -1.5, "50% 16%", cap="JENNIFER THOMPSON-CANNINO AND RONALD COTTON, 2010", anim="push 0 1"), 70, 80, "drop 0 .08")
    + A(icard(mono("PICKING COTTON", 60, INK, 3) + GAP(26) + mono("A BOOK THEY WROTE TOGETHER · 2009", 24, CO, 2), 680, 250, 3, pad=36, top=110, line=60), 1190, 150, "up .3 .4")
    + A(hand("she wasn't lying.<br>she was remembering.", 74, PAPER, -2), 1200, 500, "wipe .5 .85")
    + A(tag("THEY TELL THIS STORY TOGETHER", 22, inv=True, rot=2), 1200, 760, "slam .88 .92"),
    "PHOTO: POPTECH, CC BY-SA 2.0 (POPTECH 2010, CAMDEN, MAINE) · BLACK AND WHITE, CROPPED; NOTHING ADDED TO THE PEOPLE · \"PICKING COTTON\" (2009)"))

# 51 · "Tell a witness 'Good, you identified the suspect,' and their confidence goes up. So does their memory of how good a view they had... 7,000 participants..."
meter = lambda lab: (f'<div style="font:500 30px Mono;letter-spacing:3px;color:{PAPER};margin-bottom:12px">{lab}</div><div style="display:flex;align-items:center;gap:20px"><div style="position:relative;width:920px;height:64px;border:6px solid {PAPER};box-sizing:border-box">'
                     f'<div style="position:absolute;left:0;top:0;bottom:0;width:44%;background:{DIM}"></div><div data-anim="growx .4 .7" style="position:absolute;left:44%;top:0;bottom:0;width:38%;background:{AM}"></div></div>'
                     f'<svg width="70" height="50" viewBox="0 0 70 50"><path d="M4 25 H56 M36 6 L58 25 L36 44" fill="none" stroke="{AM}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
put("51_feedback", page(
    A(sheet(mono("SAID TO WITNESSES IN THE LAB, AFTER THEY CHOSE", 20, CO, 4) + RULE(CO, "14px 0 30px", 4) + quote("“Good, you identified the suspect.”", 92, INK, 940), 1060, 400, -1.5, pad=54), 70, 70, "drop 0 .08")
    + A(study("Wells &amp; Bradfield", 1998, "J. Applied Psychology", w=560, rot=2), 1260, 60, "drop .1 .18")
    + a(meter("THEIR CONFIDENCE"), 100, 540) + a(meter("HOW GOOD A VIEW THEY SAY THEY HAD"), 100, 710)
    + a(tag("DIRECTION AS REPORTED · SIZES ILLUSTRATIVE", 18), 100, 900)
    + A(sheet(mono("2014 META-ANALYSIS", 22, CO, 4) + GAP(8) + big("ABOUT 7,000", 76, INK) + GAP(4) + mono("PARTICIPANTS · THE EFFECT HOLDS UP", 22, INK, 2), 640, 240, -2, pad=34, sh=SH2), 1220, 360, "up .6 .7")
    + A(sheet(big("MINUTES", 50, INK) + GAP(12) + "".join(f'<div style="height:8px;background:{DIM};margin-bottom:16px;width:{w_}%"></div>' for w_ in (100, 84, 92, 70)), 400, 300, 5, pad=34, sh=SH2), 1400, 660, "up .75 .82")
    + A(stamp("APPROVED", 74, -9), 1340, 800, "slam .9 .95", "z-index:60"),
    "WELLS & BRADFIELD 1998, J. APPLIED PSYCHOLOGY 83: CONFIRMING FEEDBACK RAISES CONFIDENCE AND REPORTS OF HOW GOOD A VIEW THE WITNESS HAD · 2014 META-ANALYSIS, ABOUT 7,000 PARTICIPANTS · NO VALUES SHOWN"))

# 52 · "Ask a witness once, in a fair lineup, run by someone who doesn't know the suspect, and write down how sure they are. That first confidence does track accuracy..."
bx_ = lambda t, col=CO: (f'<div style="width:340px;height:170px;box-sizing:border-box;background:{col};border:6px solid {PAPER};{SH2};display:flex;align-items:center;justify-content:center;text-align:center;'
                         f'font:400 34px/1.1 Black;color:{PAPER};text-transform:uppercase;padding:14px">{t}</div>')
put("52_clean", page(
    A(P.evidence_bag(500, 660, prints=((250, 420, 120, 12),)), 70, 190, "drop 0 .08")
    + A(big("THE FIRST ANSWER<br>IS THE CLEAN SAMPLE.", 66), 660, 60, "wipe 0 .3")
    + A(bx_("A FAIR LINEUP"), 660, 270, "pop .2 .28") + A(bx_("RUN BY SOMEONE WHO DOESN'T KNOW THE SUSPECT"), 1040, 270, "pop .3 .38") + A(bx_("HOW SURE: WRITTEN DOWN ON THE SPOT"), 1420, 270, "pop .4 .48")
    + a(f'<svg width="1140" height="300" viewBox="0 0 1140 300" style="overflow:visible"><path d="M10 250 L560 60" fill="none" stroke="{AM}" stroke-width="16" stroke-linecap="round" pathLength="1"/>'
        f'<path d="M640 150 H1120" fill="none" stroke="{DIM}" stroke-width="16" stroke-linecap="round" stroke-dasharray="2 34"/>'
        f'<line x1="600" y1="0" x2="600" y2="300" stroke="{PAPER}" stroke-width="4" stroke-dasharray="14 12"/></svg>', 660, 500)
    + A(tag("FIRST TIME: CONFIDENCE TRACKS ACCURACY", 22, amber=True, rot=-2), 664, 790, "slam .6 .66")
    + A(tag("AT TRIAL: IT DOESN'T", 22, inv=True, rot=2), 1330, 740, "slam .8 .86")
    + A(study("Wixted &amp; Wells", 2017, "Psych. Science in the Public Interest", w=600, rot=1.5), 1290, 852, "up .85 .9", "z-index:60"),
    "WIXTED & WELLS 2017, PSYCHOLOGICAL SCIENCE IN THE PUBLIC INTEREST 18: IN A FIRST, CLEAN TEST CONFIDENCE TRACKS ACCURACY; CONFIDENCE STATED LATER, INCLUDING AT TRIAL, DOES NOT · LINES ARE SCHEMATIC"))

# ==== ACT 5 ==================================================================================================================
# 53 · "What sign did the blue car drive past? A stop sign? Or the triangle: give way, yield, whatever your country calls it?"
signcard = lambda inner, lab, rot: sheet(CENTER(f'<div style="text-align:center">{inner}<div style="font:500 36px Mono;letter-spacing:4px;color:{INK};margin-top:26px">{lab}</div></div>'), 640, 600, rot, pad=30)
put("53_whatsign", page(
    A(big("WHAT SIGN?", 190), 96, 50, "slam 0 .06")
    + A(tag("OUT LOUD", 36, amber=True, rot=4), 1520, 130, "slam .2 .26")
    + A(signcard(f'<svg width="360" height="360" viewBox="-10 -10 380 380">{P.stop_sign(360)}</svg>', "STOP", -2), 150, 380, "drop .3 .38")
    + A(signcard(f'<svg width="400" height="360" viewBox="-10 -10 420 370">{P.give_way(400)}</svg>', "GIVE WAY · YIELD", 2), 1130, 380, "drop .4 .48")
    + A(big("OR", 120, DIM), 868, 600, "fade .5 .6"),
    "THE SECOND TEST · THE CLIP AT 0:42 SHOWED ONE OF THESE · AFTER " + S_LMB))

# 54 · "Here's the clip again. Upper right. Red border. Upside-down triangle. Give way. There was no stop sign. Anywhere."
put("54_replay", page(
    A(frame(P.road_scene(car_y=500)), 196, 76, "snap 0 0")
    + ring(1105, 470, 150, 150, "draw .3 .5", AM, 11, 4)
    + a(tag("REPLAY · 0:43", 26, inv=True), 470, 890, "z-index:60")
    + A(tag("RED BORDER. TRIANGLE. GIVE WAY.", 30, amber=True, rot=-2), 1010, 700, "slam .55 .6", "z-index:60")
    + A(f'<svg width="260" height="260" viewBox="-20 -20 240 240" style="overflow:visible;transform:rotate(68deg);filter:drop-shadow(10px 12px 0 rgba(5,7,12,.5))">{P.stop_sign(200)}</svg>', 20, 800, "drop .7 .8", "z-index:62")
    + A(tag("NEVER IN THE CLIP", 22, inv=True, rot=-6), 60, 730, "slam .82 .86", "z-index:63"),
    "THE SAME STUDIO CLIP AS AT 0:42, UNCHANGED · THERE IS NO STOP SIGN IN IT"))

# 55 · "The stop sign came from me. Twice... You saw it once and heard me twice. Your brain went with whoever sounded sure."
strip = lambda txt, tc, rot: (f'<div style="display:flex;align-items:center;gap:26px;transform:rotate({rot}deg)"><div style="background:{PAPER};{SH2};padding:26px 44px;'
                              f'clip-path:polygon(0 6%,99% 0,100% 40%,98.8% 70%,100% 100%,1% 96%,0 60%,1.2% 30%);font:500 50px/1.2 Mono;color:{INK};white-space:nowrap">{txt}</div>{tag(tc, 30, amber=True)}</div>')
put("55_strips", page(
    A(big("YOU SAW IT ONCE.", 104), 96, 56, "slam 0 .06") + A(big("YOU HEARD ME TWICE.", 104, AM), 96, 166, "slam .2 .26")
    + A(strip("…the blue car that ran the " + hl("stop sign") + "…", "0:49", -1.5), 100, 380, "wipe .35 .55")
    + A(strip("…the blue car at the " + hl("stop sign") + "…", "6:36", 1), 160, 560, "wipe .55 .75")
    + A(P.luggage_tag("SURE", "EXHIBIT C", 400, 210, 6), 1330, 760, "drop .8 .88", "z-index:60")
    + A(hand("your brain went with whoever sounded sure.", 66, PAPER, -2), 110, 800, "wipe .85 1"),
    "THE NARRATOR'S OWN TWO LINES, WITH THEIR TIMECODES (SET FROM THE FINAL CUT) · THE SIGN WAS NAMED ONLY IN WORDS, NEVER ON SCREEN"))

# 56 · "In 1978, Loftus, Miller and Burns showed people slides of a car accident, then asked a question that named the wrong road sign... 41 percent... 75."
put("56_lmb", page(
    A(study("Loftus, Miller &amp; Burns", 1978, "J. Exp. Psychol.: Human Learning and Memory", w=780, rot=-1.5), 80, 60, "drop 0 .08")
    + A(P.slide_mount(1, 240), 100, 400, "drop .1 .16") + A(f'<div style="transform:rotate(5deg)">{P.slide_mount(2, 240)}</div>', 370, 420, "drop .15 .21") + A(f'<div style="transform:rotate(-4deg)">{P.slide_mount(3, 240)}</div>', 640, 400, "drop .2 .26")
    + A(tag("THEN A QUESTION NAMED THE WRONG SIGN", 22, inv=True, rot=-2), 100, 700, "slam .35 .4")
    + A(stamp("REPLICATED 2025", 70, -6), 110, 800, "slam .85 .9", "z-index:60")
    + a(mono("PICKED THE RIGHT SLIDE", 28, PAPER, 4), 1100, 70)
    + a(bars([41, 75], ["MISLED", "NOT MISLED"], 100, w=240, h=560, gap=120, cols=[AM, CO], size=110, anims=["grow .45 .65", "grow .55 .75"]), 1100, 130),
    S_LMB + ": MISLED WITNESSES PICKED THE RIGHT SLIDE 41% OF THE TIME, THE OTHERS 75% · REPLICATED BY WIECHERT ET AL. 2025 · SAMPLE SIZE TO CONFIRM, SO NONE IS SHOWN"))

# 57 · "Three things for tonight. One. Confidence is a feeling, not a receipt. Two. Write it down the same day... Three. ...both of them may be wrong."
tcard = lambda n, txt, rot, extra="": icard(big(str(n), 150, AM) + GAP(46) + big(txt, 46, INK, 1.04) + extra, 580, 640, rot, pad=40, top=204, line=58)
put("57_takeaways", page(
    A(tag("THREE THINGS FOR TONIGHT", 36, amber=True, rot=-2), 96, 70, "slam 0 .06")
    + A(tcard(1, "CONFIDENCE<br>IS A FEELING,<br>NOT A RECEIPT.", -2), 60, 240, "drop .1 .18")
    + A(tcard(2, "WRITE IT DOWN<br>THE SAME DAY.", 1.5), 670, 220, "drop .35 .43")
    + A(tcard(3, "REMEMBER IT<br>DIFFERENTLY?<br>YOU MAY BOTH<br>BE WRONG.", -1, f'<svg width="260" height="150" style="position:absolute;right:30px;bottom:26px">{bust(10, 20, 1.05, INK)}{bust(140, 20, 1.05, CO)}</svg>'), 1280, 250, "drop .6 .68")
    + A(f'<div style="transform:rotate(-30deg)">{P.pencil(380, col=CO)}</div>', 800, 720, "up .45 .52", "z-index:60")
    + A(P.luggage_tag("SURE", "", 260, 130, 10), 300, 780, "drop .2 .26", "z-index:60"),
    "THE TAKEAWAYS REST ON: NEISSER & HARSCH 1992 (WRITE IT DOWN; CONFIDENCE IS NOT ACCURACY) · WIXTED & WELLS 2017 · NOT LEGAL OR MEDICAL ADVICE"))

# 58 · "One more, before you go. Was 'pillow' on my list? Go and check. Your middle manager is already very sure."
put("58_pillow", page(
    A(tag("ONE MORE · WAS IT ON MY LIST?", 30), 96, 80, "slam 0 .06")
    + A(icard(CENTER(mono("PILLOW", 250, INK, 22)), 1180, 600, -1, pad=40, top=110, line=66), 80, 200, "slam .1 .16")
    + A(stamp("RECEIVED", 120, -8), 560, 640, "slam .6 .66", "z-index:60")
    + A(P.manager(sheet_text="", w=640, h=760), 1290, 300, "up .4 .5", "z-index:40")
    + A(hand("go and check.", 110, AM, -3), 120, 850, "wipe .8 1"),
    "THE LAST LOOP: THE VIEWER IS SENT BACK TO THE LIST AT 0:18 · THE ANSWER IS NOT GIVEN ON SCREEN"))

# 59 · "Every source is in the description. Check those too."
SRC = ["ROEDIGER & McDERMOTT 1995 · J. EXP. PSYCHOL.: LMC", "STADLER, ROEDIGER & McDERMOTT 1999 · MEMORY & COGNITION", "DEESE 1959 · J. EXP. PSYCHOL.", "GALLO, ROBERTS & SEAMON 1997 · PSYCHON. BULL. & REV.",
       "LOFTUS · TEDGLOBAL 2013", "PATIHIS ET AL. 2013 · PNAS", "NEISSER & HARSCH 1992 · AFFECT AND ACCURACY IN RECALL", "LOFTUS & PICKRELL 1995 · PSYCHIATRIC ANNALS",
       "MURPHY ET AL. 2023 · MEMORY", "ANDREWS & BREWIN 2024; BREWIN & ANDREWS 2017", "SCOBORIA ET AL. 2017 · MEMORY", "WADE, GARRY, READ & LINDSAY 2002 · PSYCHON. BULL. & REV.",
       "INNOCENCE PROJECT · DNA EXONERATIONS 1989-2020", "WELLS & BRADFIELD 1998 · J. APPLIED PSYCHOLOGY", "WIXTED & WELLS 2017 · PSPI", "LOFTUS, MILLER & BURNS 1978 · JEP: HLM", "NASA IMAGE 51L-S-156"]
put("59_sources", page(
    A(sheet(f'<div style="display:flex;align-items:baseline;gap:30px">{big("SOURCES", 96, INK)}{mono("EVERY ONE IS IN THE DESCRIPTION", 24, CO, 4)}</div>' + RULE(INK, "14px 0 22px")
            + f'<div style="columns:2;column-gap:50px">' + "".join(f'<div style="font:500 23px/1.25 Mono;letter-spacing:1px;color:{INK};padding:9px 0;border-bottom:2px solid rgba(43,108,176,.3);break-inside:avoid">{s_}</div>' for s_ in SRC) + '</div>', 1640, 860, -.8, pad=56), 140, 80, "up 0 .2")
    + A(tag("CHECK THOSE TOO", 40, amber=True, rot=4), 1360, 860, "slam .7 .76", "z-index:60"),
    "END CARD · THE FULL REFERENCES, WITH LINKS, GO IN THE VIDEO DESCRIPTION"))
