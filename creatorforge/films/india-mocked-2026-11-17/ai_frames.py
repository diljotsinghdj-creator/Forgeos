"""AI plate frames for draft 3.1 (owner, 2026-11-19; MASTER_DIRECTIVES 8c). Runs after frames.py.
Plates: assets/ai/AI1-6.jpg (raw in assets/ai_raw, finished by channels/design_kits/ai_finish.py), logged in data/ai_ledger.json.
Every word, number, tick and circle here is drawn by the studio; the plates carry no text."""
from frames import tag, page, A, a, put, hl, wobble, RED, SIG, INK, PARCH  # noqa: F401  (frames.py re-renders first)

AI = lambda n: f'<img src="/assets/ai/AI{n}.jpg" style="width:1920px;height:1080px;display:block">'
BAND = a('<div style="width:1920px;height:50px;background:rgba(244,239,230,.88)"></div>', 0, 1030, "z-index:89")  # keeps the source line readable over busy plates
LOGOBACK = a('<div style="width:236px;height:46px;background:rgba(244,239,230,.92);border-radius:4px"></div>', 1640, 34, "z-index:89")
LBL = lambda x=70, y=990, t="AI ILLUSTRATION": a(f'<div style="background:rgba(26,26,26,.85);color:{PARCH};font:500 15px Plex;letter-spacing:3px;padding:6px 10px">{t}</div>', x, y, "z-index:85")
SRC = "AI ILLUSTRATION (GPT-IMAGE-2.5 VIA ELEVENLABS, OWNER-APPROVED, MASTER_DIRECTIVES 8C; LOGGED IN DATA/AI_LEDGER.JSON) · TEXT AND NUMBERS ADDED IN THE STUDIO"
push = lambda html, s=1.06: f'<div data-anim="fade 0 .01" style="position:absolute;inset:0;animation:none">{html}</div>'

# AI·2 · the tiger that lost to a traffic jam (1 · 0:53)
put("03b_tiger", page(
    a(AI(2), 0, 0) + BAND
    + A(f'<div style="width:560px;text-align:center;font:400 96px/1 Anton;color:{INK}">0 VIEWS</div>', 1320, 315, "slam .3 .32", "z-index:30")
    + A(f'<div style="background:{PARCH};padding:20px 28px;box-shadow:0 18px 30px rgba(0,0,0,.35);transform:rotate(-1.5deg)"><div style="font:400 96px/0.95 Anton;color:{INK}">{hl("3,682")}</div><div style="font:400 36px/1.1 Anton;color:{INK}">WILD TIGERS · ABOUT 75% OF THE WORLD\'S</div></div>', 1180, 560, "up .45 .6", "z-index:30")
    + tag("NOT TRENDING · LOST TO A TRAFFIC JAM", 1150, 820, 2, "snap .8 .8") + LBL(),
    PARCH, "TIGER COUNT: NTCA/WII 'STATUS OF TIGERS' 2022 (3,682; RANGE 3,167–3,925) · " + SRC))

# AI·3 · the outrage slot machine (3 · 4:44)
reel = lambda t, s: A(f'<div style="width:150px;text-align:center;font:400 40px/1 Anton;color:{RED}">{t}</div>', 0, 0, f"snap {s} {s}")
put("11b_slot", page(
    a(AI(3), 0, 0) + BAND
    + "".join(A(f'<div style="width:160px;text-align:center;font:400 34px/1 Anton;color:{RED}">OUTRAGE</div>', x, 392, f"slam {s:.2f} {s + .02:.2f}", "z-index:30")
              for x, s in ((650, .3), (852, .42), (1086, .54)))
    + A(f'<div style="background:{INK};color:{SIG};font:400 64px/1 Anton;padding:10px 18px;letter-spacing:4px">4,100,000</div>', 80, 560, "slam .7 .72", "z-index:30")
    + A(f'<div style="font:400 72px/0.95 Anton;color:{INK}">THE INSULT<br>GETS A<br>{hl("SALARY")}</div>', 80, 170, "up .78 .9", "z-index:30")
    + A(f'<div style="font:500 20px/1.5 Plex;color:#444;width:380px">Since Oct 2024, X pays creators by engagement from Premium users.</div>', 82, 680, "fade .8 .9", "z-index:30")
    + tag("ILLUSTRATIVE · DRAWN", 110, 860, -2, "snap .2 .2") + LBL(),
    PARCH, "PAYOUT RULE: TECHCRUNCH, 9 OCT 2024 · CONFIRMED · VIEW COUNT ILLUSTRATIVE · " + SRC))

# AI·4 · the drain inspector, gone digital (4 · 5:36)
put("13b_inspector", page(
    a(AI(4), 0, 0) + BAND
    + A('<svg width="56" height="56" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#1D9BF0" stroke="#fff" stroke-width="1.6"/><path d="M7 12.5 L10.4 15.8 L17.2 8.6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>', 1730, 180, "pop .45 .52", "z-index:30")
    + A(f'<div style="font:400 92px/0.95 Anton;color:{INK}">THE DRAIN<br>INSPECTOR HAS<br>{hl("GONE DIGITAL")}</div>', 110, 180, "up .1 .25", "z-index:30")
    + A(f'<div style="font:700 56px/1.1 Caveat;color:{RED};transform:rotate(-2deg)">"With a blue tick."</div>', 116, 560, "fade .55 .65", "z-index:30")
    + tag("CALLBACK · GANDHI ON 'MOTHER INDIA', 1927", 110, 760, -1.5, "snap .8 .8")
    + tag("THE INTERNET, KEEPING RECEIPTS ON ITSELF", 110, 850, 1, "snap .9 .9") + LBL(),
    PARCH, "QUOTE: M. K. GANDHI, 'DRAIN INSPECTOR'S REPORT', YOUNG INDIA, 15 SEP 1927 · FIGURE SEEN FROM BEHIND, NO REAL PERSON · " + SRC))

# AI·6 · the 'not interested' button (5 · 8:30)
put("19b_button", page(
    a(AI(6), 0, 0) + BAND + LOGOBACK
    + A(f'<div style="background:#fff;padding:12px 22px;font:400 46px/1 Anton;color:{INK};letter-spacing:2px;box-shadow:6px 6px 0 rgba(0,0,0,.3);transform:rotate(-3deg)">NOT INTERESTED</div>', 760, 900, "slam .4 .42", "z-index:30")
    + A(f'<div style="font:400 80px/0.95 Anton;color:{INK}">THE CHEAPEST<br>GOOD MANNERS<br>{hl("ON THE INTERNET")}</div>', 110, 130, "up .55 .7", "z-index:30")
    + tag("SOUND: ONE HEAVY THUNK", 1380, 980, 1.5, "snap .42 .42") + LBL(),
    PARCH, "BUTTON, HAND AND PHONE: " + SRC))

# AI·5 · the editing table (5 · 8:33)
put("20b_edit", page(
    a(AI(5), 0, 0) + BAND + LOGOBACK
    + f'<svg class="a" data-anim="draw .45 .6" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(950, 505, 215, 150, 5)}" pathLength="1" fill="none" stroke="{RED}" stroke-width="7"/></svg>'
    + A(f'<div style="background:{PARCH};padding:18px 26px;box-shadow:0 18px 30px rgba(0,0,0,.35);transform:rotate(-1.5deg)"><div style="font:400 64px/1 Anton;color:{INK}">1.4 BILLION PEOPLE</div>'
        f'<div style="font:400 64px/1 Anton;color:{RED}">→ ONE FRAME</div></div>', 1180, 470, "up .65 .8", "z-index:40")
    + tag("FINAL CUT: ONE DRAIN", 760, 690, -2, "snap .85 .85") + LBL(),
    PARCH, "POPULATION: UN WORLD POPULATION PROSPECTS (ABOUT 1.4 BILLION; CHECK LATEST) · " + SRC))
print("ai ok")
