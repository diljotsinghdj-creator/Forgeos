"""AI plate frames for Pepper Was Money (owner, 2026-11-19; MASTER_DIRECTIVES 8c). Run after comedy.py.
Plates: assets/ai/P1-P6.jpg (raw in assets/ai_raw, finished by channels/design_kits/ai_finish.py), logged in data/ai_ledger.json.
Every word, number and arrow is added by the studio; the plates carry no text. Numbers only from dossier.json."""
from frames import page, A, a, put, hl, RED, SIG, INK, PARCH  # noqa: F401  (frames.py re-renders its own pages first)

AI = lambda n: f'<img src="/assets/ai/P{n}.jpg" style="width:1920px;height:1080px;display:block">'
BAND = a('<div style="width:1920px;height:50px;background:rgba(244,239,230,.88)"></div>', 0, 1030, "z-index:89")
LOGOBACK = a('<div style="width:236px;height:46px;background:rgba(244,239,230,.92);border-radius:4px"></div>', 1640, 34, "z-index:89")
LBL = lambda x=70, y=990, t="AI ILLUSTRATION": a(f'<div style="background:rgba(26,26,26,.85);color:{PARCH};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">{t}</div>', x, y, "z-index:85")
SRC = "AI ILLUSTRATION (GPT-IMAGE-2.5 VIA ELEVENLABS, OWNER-APPROVED, MASTER_DIRECTIVES 8C; LOGGED IN DATA/AI_LEDGER.JSON) · TEXT AND NUMBERS ADDED IN THE STUDIO"


def tag(text, x, y, rot=-1.5, anim="snap .85 .85"):
    return A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;'
             f'transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def head(html, x, y, anim="up .1 .25", size=88):
    return A(f'<div style="font:400 {size}px/0.95 Anton;color:{INK}">{html}</div>', x, y, anim, "z-index:30")


# P2 · Rome surrounded, 408 (1 · 0:13)
put("02a_siege", page(
    a(AI(2), 0, 0) + BAND + LOGOBACK
    + head(f'ROME IS {hl("SURROUNDED")}', 110, 90, "up .05 .2", 96)
    + A(f'<div style="font:400 44px ISerif;color:{INK}">The city is starving.</div>', 114, 200, "fade .3 .45", "z-index:30")
    + tag("ROME · 408 CE", 1380, 120, 2, "snap .2 .2") + LBL(),
    PARCH, "EVENT: ALARIC'S SIEGE OF ROME, 408 CE (ZOSIMUS, NEW HISTORY 5.41; BURY 1923) · SCENE NOT A RECONSTRUCTION FROM EVIDENCE · " + SRC))

# P3 · the monsoon ship (2 · 1:28)
arrow = lambda x, y: f'<svg width="260" height="60" viewBox="0 0 260 60"><path d="M6 30 H230" stroke="{RED}" stroke-width="8" stroke-dasharray="18 10"/><path d="M222 12 L252 30 L222 48" fill="none" stroke="{RED}" stroke-width="8"/></svg>'
put("08a_ship", page(
    a(AI(3), 0, 0) + BAND
    + A(arrow(0, 0), 140, 330, "wipe .2 .35", "z-index:30") + A(arrow(0, 0), 1520, 330, "wipe .25 .4", "z-index:30")
    + A(f'<div style="font:500 22px Plex;letter-spacing:4px;color:{INK}">SUMMER MONSOON</div>', 140, 290, "fade .3 .4", "z-index:30")
    + head(f'BERENIKE {hl("→ MUZIRIS")}', 110, 60, "up .45 .6", 72)
    + tag("FOLLOW THIS SHIP", 1500, 150, 2, "snap .1 .1") + LBL(),
    PARCH, "ROUTE: BERENIKE TO MUZIRIS ON THE MONSOON (SEE DOSSIER, ROME CHAPTER) · SHIP: GENERIC 1ST-CENTURY MERCHANTMAN, NOT A SPECIFIC VESSEL · " + SRC))

# P4 · a fortune on your shoulder (3 · 3:12)
put("10a_sack", page(
    a(AI(4), 0, 0) + BAND
    + head(f'A FORTUNE YOU<br>CAN CARRY ON<br>{hl("YOUR SHOULDER")}', 110, 180, "up .1 .25", 92)
    + A(f'<div style="font:400 54px Anton;color:{RED}">✓ SMALL BUT VALUABLE</div>', 114, 560, "slam .5 .52", "z-index:30")
    + tag("PORTABLE WEALTH (APPROX.)", 110, 700, -1.5, "snap .8 .8") + LBL(),
    PARCH, "RULE TWO OF MONEY: HIGH VALUE FOR ITS SIZE · " + SRC))

# P5 · the relay race (3 · 5:00)
put("13a_relay", page(
    a(AI(5), 0, 0) + BAND
    + head(f'THE WORLD\'S LONGEST {hl("RELAY RACE")}', 110, 90, "up 0 .12", 84)
    + A(f'<div style="background:{SIG};color:{INK};font:400 44px Anton;padding:6px 14px">~3 DUCATS · CALICUT</div>', 90, 860, "slam .3 .32", "z-index:30")
    + A(f'<div style="background:{INK};color:{SIG};font:400 44px Anton;padding:6px 14px">~80 DUCATS · EUROPE</div>', 1420, 860, "slam .7 .72", "z-index:30")
    + "".join(A(f'<div style="font:700 44px Caveat;color:{RED};transform:rotate(-4deg)">+ cut</div>', x, 215, f"pop {s:.2f} {s + .05:.2f}", "z-index:30") for x, s in ((640, .42), (980, .5), (1310, .58)))
    + tag("EVERY RUNNER CHARGES FOR THE BATON", 640, 960, 1, "snap .85 .85") + LBL(),
    PARCH, "PRICES: HUNDREDWEIGHT ~3 DUCATS IN CALICUT, ~80 IN EUROPE, 15TH C. (UNESCO SILK ROADS, 'THE ARAB MONOPOLY') · RUNNERS ILLUSTRATIVE, NOT REAL PEOPLE · " + SRC))

# P6 · the demotion (4 · 6:17)
put("14a_demotion", page(
    a(AI(6), 0, 0) + BAND
    + head(f'THE GREATEST DEMOTION<br>IN {hl("CULINARY HISTORY")}', 650, 110, "up .1 .25", 70)
    + tag("FORMER CURRENCY · NOW SEASONING", 1180, 900, 2, "snap .7 .7") + LBL(),
    PARCH, "17TH-CENTURY PEPPER PRICES FELL (~40% BELOW THE PORTUGUESE LEVEL; SEE DOSSIER) · " + SRC))
print("ai ok")
