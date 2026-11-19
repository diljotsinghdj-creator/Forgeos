"""AI illustration layer (owner's picks, 2026-11-19: A1, B3, C1, D1, E2). Runs after frames.py and replaces or adds frames.
Every AI plate is labelled AI ILLUSTRATION on screen and logged in data/ai_ledger.json (model, prompt, credits)."""
import math
from frames import (page, A, a, put, chapter, tag, card, stick, clock, hl, wobble, SL, PAPER, CO, AM)  # noqa: F401  (frames.py re-renders first)

AI = lambda f, extra="": f'<img src="/assets/ai/{f}.jpg" style="width:1920px;height:1080px;object-fit:cover;display:block;{extra}">'
LBL = lambda x=1500, y=1000: a(f'<div style="background:rgba(20,24,36,.82);color:{PAPER};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">AI ILLUSTRATION</div>', x, y, "z-index:85")
AISRC = "AI ILLUSTRATION: GPT-IMAGE-2.5 VIA ELEVENLABS, OWNER-APPROVED (MASTER_DIRECTIVES 8b), LOGGED IN DATA/AI_LEDGER.JSON"


def small_clock(cx, cy, r, h, m):
    ha = math.radians((h % 12 + m / 60) * 30); ma = math.radians(m * 6)
    ticks = "".join(f'<line x1="{cx + (r - 12) * math.sin(math.radians(i * 30)):.1f}" y1="{cy - (r - 12) * math.cos(math.radians(i * 30)):.1f}" x2="{cx + r * .95 * math.sin(math.radians(i * 30)):.1f}" y2="{cy - r * .95 * math.cos(math.radians(i * 30)):.1f}" stroke="{SL}" stroke-width="4"/>' for i in range(12))
    return (f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><circle cx="{cx}" cy="{cy}" r="{r + 10}" fill="{SL}"/><circle cx="{cx}" cy="{cy}" r="{r}" fill="{AM}"/>{ticks}'
            f'<line x1="{cx}" y1="{cy}" x2="{cx + r * .5 * math.sin(ha):.1f}" y2="{cy - r * .5 * math.cos(ha):.1f}" stroke="{SL}" stroke-width="9" stroke-linecap="round"/>'
            f'<line x1="{cx}" y1="{cy}" x2="{cx + r * .8 * math.sin(ma):.1f}" y2="{cy - r * .8 * math.cos(ma):.1f}" stroke="{SL}" stroke-width="6" stroke-linecap="round"/><circle cx="{cx}" cy="{cy}" r="7" fill="{SL}"/></svg>')


# A1 · the living room (new establishing frame, after the clock)
people = "".join(stick(x, y, 1.6, SL) for x, y in ((470, 700), (560, 730), (650, 690), (740, 740), (830, 700), (920, 735), (1010, 700)))
observers = "".join(f'<g data-anim="fade {.45 + i * .06:.2f} {.52 + i * .06:.2f}">{stick(x, y, 1.6, AM)}</g>' for i, (x, y) in enumerate(((1110, 720), (1190, 700), (1270, 730))))
put("01b_room", page(
    a(AI("A1"), 0, 0) + small_clock(1545, 225, 84, 11, 59)
    + f'<svg class="a" data-anim="fade .1 .25" style="left:0;top:0;z-index:25" width="1920" height="1080">{people}</svg>'
    + f'<svg class="a" style="left:0;top:0;z-index:26" width="1920" height="1080">{observers}</svg>'
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">THE PREDICTION</div><div style="font:400 40px/1.05 Anton;color:{SL};margin-top:6px">FLOOD ON {hl("21 DEC 1954")}</div>'
           f'<div style="font:400 26px ISerif;color:#3A4456">rescue by flying saucer the night before</div>', 520, 660, 250, "up .3 .42", -1.5, "#FFFFFF", "z-index:40")
    + tag("THREE OF THESE PEOPLE ARE TAKING NOTES", 1180, 900, 1.5, "snap .8 .8") + LBL(110, 1000)
    + chapter(1, "THE WAITING ROOM"),
    PAPER, AISRC + " · PEOPLE: STICK FIGURES (THE THREE UNDERCOVER RESEARCHERS IN AMBER) · CLOCK CORRECTED TO 11:59 IN THE STUDIO"))

# C1 · the Millerites
put("07_millerites", page(
    a(f'<div style="width:1920px;height:1080px;background:{PAPER};background-image:linear-gradient(rgba(43,108,176,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(43,108,176,.10) 1px,transparent 1px);background-size:40px 40px"></div>', 0, 0)
    + chapter(2, "WHY BRAINS DEFEND BELIEFS")
    + A(f'<div style="background:#fff;padding:14px 14px 18px;box-shadow:0 26px 50px rgba(0,0,0,.4);transform:rotate(-2deg)"><img src="/assets/ai/C1.jpg" style="width:980px;height:551px;object-fit:cover;display:block"></div>', 110, 200, "up 0 .15")
    + a(f'<div style="background:rgba(20,24,36,.82);color:{PAPER};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">AI ILLUSTRATION · SILHOUETTES, NOT REAL PEOPLE</div>', 150, 740, "z-index:40")
    + tag("22 OCT 1844", 830, 230, 3, "snap .25 .25")
    + A(f'<div style="font:400 100px/0.9 Anton;color:{SL}">THE GREAT<br>{hl("DISAPPOINTMENT")}</div>', 1160, 280, "slam .45 .47")
    + A(f'<div style="font:400 34px/1.3 ISerif;color:#3A4456;width:680px">The Millerites expected the end on 22 October 1844. It didn\'t come. Historians gave it the most polite name possible.</div>', 1162, 540, "fade .55 .7")
    + tag("NAMING DEPARTMENT: UNDERSTATED", 1160, 790, 2, "snap .85 .85"),
    PAPER, "HISTORY: THE MILLERITE 'GREAT DISAPPOINTMENT', 22 OCT 1844 (WELL-ESTABLISHED); CITED BY FRS 1956 (KELLY 2025) · " + AISRC))

# E2 · the archive box
sheets = "".join(A(f'<div style="width:300px;height:380px;background:#FFFFFF;box-shadow:0 12px 24px rgba(0,0,0,.3);transform:rotate({r}deg);padding:26px;box-sizing:border-box">'
                   f'<div style="font:500 14px Plex;letter-spacing:2px;color:{CO}">{t}</div>' + "".join(f'<div style="height:8px;background:rgba(31,38,51,.3);margin:14px 0;width:{w}%"></div>' for w in (90, 70, 84, 60, 78, 66, 88))
                   + '</div>', x, y, f"drop {s:.2f} {s + .08:.2f}") for t, x, y, r, s in
                 (("TRANSCRIPT", 1100, 160, -6, .35), ("PHONE LOG", 1330, 140, 4, .43), ("RESEARCH NOTES", 1560, 180, -3, .51), ("\"MESSAGE FROM SPACE\"", 1320, 560, 6, .59)))
put("15_box", page(
    a(f'<div style="width:1920px;height:1080px;background:{PAPER}"></div>', 0, 0) + chapter(4, "THE ARCHIVE")
    + A(f'<div style="position:relative;background:#fff;padding:12px;box-shadow:0 26px 50px rgba(0,0,0,.4);transform:rotate(-1.5deg)"><img src="/assets/ai/E2.jpg" style="width:960px;height:540px;object-fit:cover;display:block">'
        f'<div style="position:absolute;left:470px;top:400px;background:{PAPER};padding:8px 12px;font:500 15px/1.5 Plex;letter-spacing:2px;color:{SL};transform:rotate(4deg)">LEON FESTINGER PAPERS · BOX 4<br>BENTLEY HISTORICAL LIBRARY</div></div>', 100, 260, "up 0 .15")
    + a(f'<div style="background:rgba(20,24,36,.82);color:{PAPER};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">AI ILLUSTRATION · NOT THE REAL BOX</div>', 140, 820, "z-index:40")
    + sheets + tag("PAGES: RECONSTRUCTION · ORIGINALS AT THE BENTLEY", 1100, 960, -1.5, "fade .6 .7")
    + A(f'<div style="font:400 72px/0.95 Anton;color:{SL}">UNSEALED {hl("2025")}</div>', 110, 140, "up .1 .2"),
    PAPER, "BOX 4 CONTENTS: KELLY 2025 · " + AISRC))

# D1 · the antelope gag
put("19_antelope", page(
    a(AI("D1"), 0, 0) + chapter(4, "THE ARCHIVE")
    + A(f'<div style="font:700 60px Caveat;color:{SL};transform:rotate(-3deg)">"Fascinating."</div>', 110, 170, "fade .55 .65", "z-index:40")
    + tag("NATURE DOCUMENTARY · ETHICS SECTION: BLANK", 1060, 120, 2, "snap .85 .85") + LBL(110, 1000),
    PAPER, "SIGHT GAG ILLUSTRATING KELLY 2025'S CLAIM THAT THE OBSERVERS SHAPED EVENTS · " + AISRC))

# B3 · the end card: the saucer arrives late
put("24_end", page(
    a(AI("B3", "filter:brightness(.9)"), 0, 0)
    + A(f'<div style="opacity:.92">{clock(0, 1, 300, "", SL, True)}</div>', 810, 90, "fade 0 .12", "z-index:30")
    + A(f'<div style="font:400 50px/1.3 ISerif;color:{PAPER};text-align:center;width:1920px;text-shadow:0 2px 14px rgba(0,0,0,.8)">The aliens never came.<br>Seventy years later, <span style="color:{AM}">the truth did</span>, a little late.</div>', 0, 440, "fade .45 .65", "z-index:40")
    + LBL(1700, 1000),
    "#141824", "DRAGON PSYCHOLOGY · SOURCES IN THE DESCRIPTION · " + AISRC, dark=True))

# ---- Round 2 plates (owner, 2026-11-19: "do the same"): F1 desk (via SLATE in frames.py), F2-F6 below -------------------------
PLATE = lambda f: f'<img src="/assets/ai/{f}.jpg" style="width:1920px;height:1080px;display:block">'
BAND = a(f'<div style="width:1920px;height:50px;background:rgba(240,244,248,.9)"></div>', 0, 1030, "z-index:89")
panel = lambda inner, x, y, w, anim="up .1 .25": A(f'<div style="width:{w}px;background:{PAPER};padding:24px 30px;box-shadow:0 18px 34px rgba(10,14,24,.35);border-top:8px solid {CO}">{inner}</div>', x, y, anim, "z-index:40")
H = lambda h, size=80: f'<div style="font:400 {size}px/0.95 Anton;color:{SL}">{h}</div>'
T = lambda t, c=None: f'<div style="display:inline-block;margin-top:16px;background:{SL};color:{PAPER};font:500 18px Plex;letter-spacing:3px;padding:6px 10px">{t}</div>'
head = lambda h, x, y, anim="up .1 .25", size=84, col=SL: A(f'<div style="font:400 {size}px/0.95 Anton;color:{col}">{h}</div>', x, y, anim, "z-index:40")

# F6 · the membership card (2 · 1:21)
put("06b_card", page(
    a(PLATE("F6"), 0, 0) + BAND + chapter(2, "WHY BRAINS DEFEND BELIEFS")
    + panel(H(f'A BELIEF IS A<br>{hl("MEMBERSHIP CARD")}', 72) + T("CANCELLATION: NOT OFFERED"), 110, 150, 560) + LBL(110, 990),
    PAPER, "THEORY FRAMING: MERCIER & SPERBER (2011), DEBATED · METAPHOR · " + AISRC))

# F2 · the phones (3 · 2:57)
put("11b_phones", page(
    a(PLATE("F2"), 0, 0) + BAND + chapter(3, "THE NIGHT")
    + panel(H(f'SUDDENLY, {hl("PUBLICITY")}', 72) + '<div style="font:400 32px/1.3 ISerif;color:#3A4456;margin-top:12px">The group phoned the newspapers and started recruiting, according to the 1956 book.</div>' + T("THE BOOK'S VERSION · DISPUTED IN CHAPTER 4"), 110, 130, 760) + LBL(110, 990),
    PAPER, "CLAIM: FESTINGER, RIECKEN & SCHACHTER, WHEN PROPHECY FAILS (1956); CONTESTED BY KELLY 2025 · " + AISRC))

# F3 · the peg board (3 · 3:35)
put("13b_pegs", page(
    a(PLATE("F3"), 0, 0) + BAND
    + panel(H(f'TURN EACH PEG<br>A QUARTER TURN.<br>{hl("REPEAT.")}', 64) + T("FESTINGER & CARLSMITH · 1959") + '<br>' + T("FUN LEVEL: STATISTICALLY ZERO"), 1240, 110, 560) + LBL(110, 990),
    PAPER, "TASK: FESTINGER & CARLSMITH (1959), J. ABNORMAL & SOCIAL PSYCHOLOGY 58 · ILLUSTRATION OF THE TASK, NOT THE LAB · " + AISRC))

# F5 · the textbooks (5 · 6:46)
put("22b_textbooks", page(
    a(PLATE("F5"), 0, 0) + BAND + chapter(5, "THE IRONY")
    + head(f'THE STUDY ABOUT<br>DOUBLING DOWN…', 110, 170, "up .05 .2", 80)
    + head(f'…GOT<br>{hl("DOUBLED DOWN ON")}', 110, 560, "slam .6 .62", 70)
    + tag("70 YEARS OF TEXTBOOKS", 110, 400, -1.5, "snap .3 .3") + LBL(110, 990),
    PAPER, "TEXTBOOKS ILLUSTRATIVE, NO REAL TITLES · " + AISRC))

# F4 · the valve in your head (5 · 7:03)
put("23b_head", page(
    a(PLATE("F4"), 0, 0) + BAND
    + head(f'THE SAME VALVE<br>{hl("SITS IN YOUR HEAD")}', 1080, 170, "up .1 .25", 80)
    + "".join(A(f'<div style="background:{PAPER};color:{c};font:500 20px Plex;letter-spacing:3px;padding:6px 10px;box-shadow:4px 4px 0 rgba(0,0,0,.25)">{t}</div>', 1080, y, f"fade {s} {s + .08:.2f}", "z-index:40")
              for t, y, s, c in (("CHANGE THE BELIEF", 470, .4, SL), ("IGNORE IT", 530, .5, SL), ("ADD A NEW STORY", 590, .6, AM)))
    + tag("METAPHOR, NOT ANATOMY", 1080, 700, 1.5, "snap .2 .2") + LBL(110, 990),
    PAPER, "METAPHOR, NOT ANATOMY · THE THREE OUTLETS FOLLOW DISSONANCE THEORY (FESTINGER 1957) · " + AISRC))
print("ok")
