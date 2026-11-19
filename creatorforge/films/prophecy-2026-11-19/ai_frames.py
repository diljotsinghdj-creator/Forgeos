"""AI illustration layer. Runs after frames.py and replaces or adds frames.
2026-11-19 (owner: "more real pictures, animation, motion graphics etc and less ai"; MASTER_DIRECTIVES 8c): only three plates
stay, each where nothing real exists: A1 (the 1954 living room nobody photographed, shown as a print on the drawn grid),
D1 (the antelope sight gag) and F4 (the valve-in-your-head metaphor). C1, E2, B3, F1, F2, F3, F5, F6 are retired in
data/ai_ledger.json: replaced by real pictures (real.py, data/photo_credits.json) or the original drawn frames.
Every AI plate is labelled AI ILLUSTRATION on screen and logged in data/ai_ledger.json (model, prompt, credits)."""
import math
from frames import (page, A, a, put, chapter, tag, card, stick, clock, hl, wobble, SL, PAPER, CO, AM, GRID)  # noqa: F401  (frames.py re-renders first)

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
inner = (a(AI("A1"), 0, 0) + small_clock(1545, 225, 84, 11, 59)
         + f'<svg class="a" data-anim="fade .1 .25" style="left:0;top:0;z-index:25" width="1920" height="1080">{people}</svg>'
         + f'<svg class="a" style="left:0;top:0;z-index:26" width="1920" height="1080">{observers}</svg>')
put("01b_room", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + A(f'<div style="background:#fff;padding:14px 14px 18px;box-shadow:0 26px 50px rgba(0,0,0,.4);transform:rotate(-1.2deg)"><div style="position:relative;width:1344px;height:756px;overflow:hidden">'
        f'<div style="position:relative;width:1920px;height:1080px;transform:scale(.7);transform-origin:0 0">{inner}</div></div></div>', 90, 150, "up 0 .14")
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">THE PREDICTION</div><div style="font:400 40px/1.05 Anton;color:{SL};margin-top:6px">FLOOD ON {hl("21 DEC 1954")}</div>'
           f'<div style="font:400 26px ISerif;color:#3A4456">rescue by flying saucer the night before</div>', 400, 1470, 200, "up .3 .42", 2, "#FFFFFF", "z-index:40")
    + tag("THREE OF THESE PEOPLE ARE TAKING NOTES", 1080, 945, 1.5, "snap .8 .8")
    + a(f'<div style="background:rgba(20,24,36,.86);color:{PAPER};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">AI ILLUSTRATION · A RECONSTRUCTION: NO PHOTO OF THE ROOM EXISTS</div>', 120, 930, "z-index:85")
    + chapter(1, "THE WAITING ROOM"),
    PAPER, AISRC + " · PEOPLE: STICK FIGURES (THE THREE UNDERCOVER RESEARCHERS IN AMBER) · CLOCK CORRECTED TO 11:59 IN THE STUDIO"))

# D1 · the antelope gag
put("19_antelope", page(
    a(AI("D1"), 0, 0) + chapter(4, "THE ARCHIVE")
    + A(f'<div style="font:700 60px Caveat;color:{SL};transform:rotate(-3deg)">"Fascinating."</div>', 110, 170, "fade .55 .65", "z-index:40")
    + tag("NATURE DOCUMENTARY · ETHICS SECTION: BLANK", 1060, 120, 2, "snap .85 .85") + LBL(110, 1000),
    PAPER, "SIGHT GAG ILLUSTRATING KELLY 2025'S CLAIM THAT THE OBSERVERS SHAPED EVENTS · " + AISRC))

# ---- Round 2 plate kept: F4 (F1 desk, F2, F3, F5, F6 retired 2026-11-19) ----------------------------------------------
PLATE = lambda f: f'<img src="/assets/ai/{f}.jpg" style="width:1920px;height:1080px;display:block">'
BAND = a(f'<div style="width:1920px;height:50px;background:rgba(240,244,248,.9)"></div>', 0, 1030, "z-index:89")
panel = lambda inner, x, y, w, anim="up .1 .25": A(f'<div style="width:{w}px;background:{PAPER};padding:24px 30px;box-shadow:0 18px 34px rgba(10,14,24,.35);border-top:8px solid {CO}">{inner}</div>', x, y, anim, "z-index:40")
H = lambda h, size=80: f'<div style="font:400 {size}px/0.95 Anton;color:{SL}">{h}</div>'
T = lambda t, c=None: f'<div style="display:inline-block;margin-top:16px;background:{SL};color:{PAPER};font:500 18px Plex;letter-spacing:3px;padding:6px 10px">{t}</div>'
head = lambda h, x, y, anim="up .1 .25", size=84, col=SL: A(f'<div style="font:400 {size}px/0.95 Anton;color:{col}">{h}</div>', x, y, anim, "z-index:40")

# F4 · the valve in your head (5 · 7:03)
put("23b_head", page(
    a(PLATE("F4"), 0, 0) + BAND
    + head(f'THE SAME VALVE<br>{hl("SITS IN YOUR HEAD")}', 1080, 170, "up .1 .25", 80)
    + "".join(A(f'<div style="background:{PAPER};color:{c};font:500 20px Plex;letter-spacing:3px;padding:6px 10px;box-shadow:4px 4px 0 rgba(0,0,0,.25)">{t}</div>', 1080, y, f"fade {s} {s + .08:.2f}", "z-index:40")
              for t, y, s, c in (("CHANGE THE BELIEF", 470, .4, SL), ("IGNORE IT", 530, .5, SL), ("ADD A NEW STORY", 590, .6, AM)))
    + tag("METAPHOR, NOT ANATOMY", 1080, 700, 1.5, "snap .2 .2") + LBL(110, 990),
    PAPER, "METAPHOR, NOT ANATOMY · THE THREE OUTLETS FOLLOW DISSONANCE THEORY (FESTINGER 1957) · " + AISRC))
print("ok")
