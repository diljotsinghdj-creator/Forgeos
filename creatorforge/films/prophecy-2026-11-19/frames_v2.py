"""Film 3 remake, "The Infiltration" (owner's pick, 2026-11-20): the screens for SCRIPT_TABLE_v2.md. Dragon Psychology palette.
Rules from BRAIN_LOG 2026-11-20: the subject fills the frame, real material first, a page is shot at most three times.
Reuses the helpers in frames.py. Numbers and names only from dossier.json. Run: python3 frames_v2.py"""
import frames as F
from frames import A, a, put, page, SL, PAPER, CO, AM, SLATE, GRID, W, LK, hl

FULL = lambda f, anim="push 0 1", pos="center", dim=.0: (
    f'<div class="a" style="left:0;top:0;width:1920px;height:1080px;overflow:hidden"><div data-anim="{anim}" style="width:1920px;height:1080px">'
    f'<img src="/assets/real/{f}" style="width:1920px;height:1080px;object-fit:cover;object-position:{pos};display:block"></div>'
    f'<div style="position:absolute;inset:0;background:rgba(20,24,36,{dim})"></div></div>')
BIG = lambda t, size, col=PAPER, lh=.92, extra="": f'<div style="font:400 {size}px/{lh} Anton;color:{col};letter-spacing:1px;white-space:nowrap;{extra}">{t}</div>'
MONO = lambda t, size=22, col=PAPER, bg=SL: f'<div style="display:inline-block;background:{bg};color:{col};font:500 {size}px Plex;letter-spacing:4px;padding:8px 14px;white-space:nowrap">{t}</div>'
HAND = lambda t, size=64, col=AM, rot=-3, w=600: f'<div style="font:700 {size}px/1.05 Caveat;color:{col};width:{w}px;transform:rotate({rot}deg)">{t}</div>'
DESK = a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0)
SHEET = lambda inner, w, h, rot=-1.2, bg=PAPER, pad=44: (f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;background:{bg};padding:{pad}px;box-shadow:0 30px 60px rgba(0,0,0,.55);transform:rotate({rot}deg);position:relative">{inner}</div>')

# 1 · NIGHT-HOUSE: the real photo, full frame. Lines: "December 1954…" / "…waiting for a flying saucer."
put("v2_01_house", page(
    FULL("night_house.jpg", "push 0 1", "center", .18)
    + A(BIG("DECEMBER<br>1954", 250, PAPER, .86, "text-shadow:0 10px 40px rgba(0,0,0,.6)"), 110, 120, "slam .02 .06", "z-index:30")
    + A(MONO("A STRANGER'S HOUSE · ILLINOIS", 26, SL, PAPER), 118, 610, "up .1 .16", "z-index:31")
    + A(HAND("someone in here is taking notes.", 78, AM, -3, 760), 1040, 690, "wipe .2 .42", "z-index:32")
    + F.circ(1500, 360, 340, 150, "draw .55 .7", 5, 9)
    + A(HAND("saucer due: tonight", 84, AM, 3, 620), 1240, 310, "wipe .62 .8", "z-index:32")
    + A(MONO("STAND-IN PHOTO · NOT THE ACTUAL HOME", 16, PAPER, "rgba(20,24,36,.85)"), 1330, 990, "fade 0 .02", "z-index:33"),
    SL, "PHOTO: ROBIN MULLIGAN / FLICKR, CC BY 2.0 (A STAND-IN: NOT OAK PARK, NOT 1954) · DATE AND EVENTS: KELLY 2025, JHBS 62:e70043; FESTINGER, RIECKEN & SCHACHTER 1956", dark=True))

# 2 · NOTEBOOK: a real hand, a real pencil. "He's waiting for it not to come."
put("v2_02_notebook", page(
    FULL("notebook.jpg", "push 0 1", "50% 40%", .08)
    + A(MONO("FIELD NOTES · 20 DEC 1954", 26), 90, 80, "snap .02 .02", "z-index:30")
    + A(HAND("21:00 &nbsp; no saucer.", 100, SL, -7, 900), 760, 300, "wipe .1 .3", "z-index:31")
    + A(HAND("22:00 &nbsp; no saucer.", 100, SL, -7, 900), 780, 420, "wipe .32 .5", "z-index:31")
    + A(HAND("good.", 150, AM, -9, 500), 1180, 560, "wipe .6 .75", "z-index:31")
    + F.circ(1330, 650, 250, 120, "draw .78 .92", 8, 9)
    + A(MONO("MODERN PHOTO, ILLUSTRATIVE · THE HANDWRITING IS OURS", 16, PAPER, "rgba(20,24,36,.85)"), 1080, 990, "fade 0 .02", "z-index:33"),
    SL, "PHOTO: RAWPIXEL, CC0 (ILLUSTRATIVE) · THE NOTES ON SCREEN ARE A STUDIO DRAWING, NOT A QUOTE", dark=True))

# 3 · CASE-FILE: a personnel sheet that fills the desk. "He isn't a believer. He's a researcher. Undercover."
row = lambda k, v, an, col=SL: (f'<div style="display:flex;align-items:baseline;gap:28px;border-bottom:3px solid #C9D3DF;padding:22px 0">'
                               f'<div style="font:500 24px Plex;letter-spacing:5px;color:{CO};width:230px">{k}</div>'
                               f'<div data-anim="{an}" style="font:400 150px/1 Anton;color:{col}">{v}</div></div>')
put("v2_03_casefile", page(
    DESK
    + A(SHEET(f'<div style="font:500 22px Plex;letter-spacing:6px;color:{CO}">CASE FILE · STUDIO RECONSTRUCTION</div>'
              + row("BELIEVER?", "NO.", "slam .08 .12") + row("ACTUAL JOB", "RESEARCHER", "slam .34 .38") + row("STATUS", "UNDERCOVER", "slam .62 .66", AM), 1560, 800, -1.4), 180, 140, "drop 0 .06")
    + F.stamp("DO NOT TELL THE ALIENS", 1060, 96, "slam .82 .86", 7, 56, True),
    SL, "SOURCE: FESTINGER, RIECKEN & SCHACHTER AND PAID OBSERVERS JOINED THE GROUP AS BELIEVERS (KELLY 2025; WHEN PROPHECY FAILS, 1956) · THE FILE IS A STUDIO DRAWING", dark=True))

# 4 · SEATING-PLAN: a ring of chairs, some of them flip. No count is claimed. "And he's not the only spy in this group."
import math
seats = ""
for i in range(14):
    ang = math.radians(i * 360 / 14 - 90); x, y = 960 + 620 * math.cos(ang), 560 + 330 * math.sin(ang)
    spy = i in (2, 7, 11)
    seats += f'<rect x="{x - 46:.0f}" y="{y - 46:.0f}" width="92" height="92" rx="10" fill="{PAPER}" stroke="{CO}" stroke-width="6"/>'
    if spy:
        t0 = .25 + (2, 7, 11).index(i) * .18
        seats += (f'<g data-anim="pop {t0:.2f} {t0 + .08:.2f}" style="transform-origin:{x:.0f}px {y:.0f}px"><rect x="{x - 46:.0f}" y="{y - 46:.0f}" width="92" height="92" rx="10" fill="{AM}" stroke="{SL}" stroke-width="6"/>'
                  f'<rect x="{x - 20:.0f}" y="{y - 26:.0f}" width="40" height="52" fill="{PAPER}" stroke="{SL}" stroke-width="4"/><line x1="{x - 12:.0f}" y1="{y - 10:.0f}" x2="{x + 12:.0f}" y2="{y - 10:.0f}" stroke="{SL}" stroke-width="3"/>'
                  f'<line x1="{x - 12:.0f}" y1="{y + 4:.0f}" x2="{x + 12:.0f}" y2="{y + 4:.0f}" stroke="{SL}" stroke-width="3"/></g>')
put("v2_04_plan", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + a(f'<svg width="1920" height="1080"><ellipse cx="960" cy="560" rx="430" ry="190" fill="none" stroke="{CO}" stroke-width="5" stroke-dasharray="14 12"/>{seats}</svg>', 0, 0)
    + A(BIG("THE LIVING ROOM", 96, SL), 660, 500, "fade 0 .05")
    + A(MONO("SEATS: A DIAGRAM, NOT A HEAD COUNT", 20), 720, 620, "fade 0 .05")
    + A(HAND("notebook", 62, AM, -6, 300), 1500, 140, "wipe .32 .42") + A(HAND("notebook", 62, AM, 5, 300), 250, 800, "wipe .7 .8")
    + A(HAND("also a notebook", 62, AM, -4, 420), 1360, 900, "wipe .5 .6")
    + F.tag("HOW MANY? THE RECORD WE HAVE DOESN'T SAY", 560, 60, -1.5, "snap .88 .88"),
    PAPER, "SOURCE: THE THREE AUTHORS AND PAID OBSERVERS INFILTRATED THE GROUP (KELLY 2025) · THE NUMBER AND THE SEATS ARE NOT FROM THE RECORD: DIAGRAM ONLY"))

# 5 · DISSONANCE-TYPE: the phrase, wall to wall.
put("v2_05_type", page(
    DESK
    + A(MONO("THE FOUNDING CASE OF A PHRASE YOU KNOW", 28, SL, PAPER), 130, 150, "up 0 .1")
    + A(BIG("COGNITIVE", 330, PAPER), 120, 230, "slam .45 .5") + A(BIG("DISSONANCE", 330, AM), 120, 560, "slam .62 .67")
    + A(HAND("(you've used it this week)", 70, PAPER, -3, 800), 1040, 930, "wipe .8 .95"),
    SL, "WHEN PROPHECY FAILS (1956) IS WIDELY CITED AS THE FOUNDING CASE OF COGNITIVE DISSONANCE (SEE dossier.json)", dark=True))

# 6 · FLOOD-DATE: a tear-off calendar page the size of the screen.
put("v2_06_date", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + A(f'<div style="width:760px;background:#fff;box-shadow:0 30px 60px rgba(10,14,24,.4);transform:rotate(-2deg)"><div style="background:{CO};color:{PAPER};font:400 96px/1.3 Anton;text-align:center;letter-spacing:8px">DECEMBER</div>'
        f'<div style="font:400 560px/.95 Anton;color:{SL};text-align:center">21</div><div style="font:500 40px/2 Plex;letter-spacing:12px;color:{SL};text-align:center;border-top:4px solid {SL}">TUESDAY · 1954</div></div>', 150, 60, "drop 0 .1")
    + A(BIG("PREDICTED:", 110, SL), 1010, 250, "up .2 .3") + A(BIG("A FLOOD.", 250, AM), 1000, 370, "slam .38 .43")
    + A(HAND("says Dorothy Martin", 76, CO, -3, 700), 1020, 660, "wipe .55 .75")
    + F.circ(530, 560, 330, 300, "draw .8 .95", 4, 10),
    PAPER, "SOURCE: IN 1954 DOROTHY MARTIN PREDICTED A FLOOD FOR 21 DEC 1954 (KELLY 2025, SUMMARISING THE 1956 BOOK AND THE ARCHIVE) · CALENDAR DRAWN IN THE STUDIO"))

# 7 · FLOOD-MAP: North America (Natural Earth), the predicted water rising. Clearly a prediction that did not happen.
BOX = (-135.0, 12.0, -55.0, 62.0)
px = lambda lo, la: ((lo - BOX[0]) / (BOX[2] - BOX[0]) * 1920, (BOX[3] - la) / (BOX[3] - BOX[1]) * 1080)
pth = lambda rings: "".join("M" + " L".join("%.1f %.1f" % px(lo, la) for lo, la in r) + "Z" for r in rings)
land = "".join(f'<path d="{pth(W[n])}" fill="{PAPER}" stroke="{SL}" stroke-width="2.5"/>' for n in ("Canada", "United States of America", "Mexico"))
put("v2_07_floodmap", page(
    a(f'<svg width="1920" height="1080" style="background:#22293A">{land}<path d="{pth([l["r"] for l in LK])}" fill="#22293A"/></svg>', 0, 0)
    + A(f'<div style="width:1920px;height:1080px;background:{CO};opacity:.82;mix-blend-mode:multiply"></div>', 0, 0, "grow .15 .6")
    + A(BIG("NORTH AMERICA:", 120, PAPER), 90, 70, "up 0 .08", "z-index:30") + A(BIG("UNDER WATER", 230, PAPER), 84, 190, "slam .5 .55", "z-index:30")
    + F.stamp("PREDICTED. DID NOT HAPPEN.", 760, 470, "slam .62 .66", -6, 70, True)
    + A(HAND("believers: collected by saucer<br>the day before", 76, AM, -2, 900), 930, 720, "wipe .72 .95", "z-index:31"),
    SL, "MAP: NATURAL EARTH (PUBLIC DOMAIN) · THE FLOOD IS THE 1954 PREDICTION, NOT AN EVENT · SOURCE: KELLY 2025; WHEN PROPHECY FAILS (1956)", dark=True))

# 8 · METAL-TRAY: real zips and a real stamped envelope. "Remove all metal. Bring a stamped envelope as a passport."
put("v2_08_metal", page(
    DESK
    + A(BIG("BOARDING RULES", 150, PAPER), 90, 50, "slam 0 .05")
    + F.photo("zip_teeth.jpg", 760, 500, 80, 300, "drop .12 .2", -2.5) + F.photo("zip_snaps.jpg", 520, 360, 560, 620, "drop .2 .28", 3)
    + F.stamp("1 · REMOVE ALL METAL", 150, 250, "slam .3 .34", -5, 64, True)
    + F.photo("envelope.jpg", 800, 490, 1040, 240, "drop .52 .6", 2)
    + F.stamp("2 · PASSPORT", 1250, 760, "slam .7 .74", 5, 76, True)
    + A(HAND("one stamped envelope", 70, AM, -3, 700), 1180, 900, "wipe .78 .95", "z-index:66"),
    SL, "RULES AS DESCRIBED IN WHEN PROPHECY FAILS (1956), VIA KELLY 2025 ⚠ PAGE TO CHECK · PHOTOS: KINCHAN1 AND LEAHLIKESLEMON / FLICKR, CC BY 2.0; SMITHSONIAN NATIONAL POSTAL MUSEUM / RAWPIXEL, CC0 (ALL ILLUSTRATIVE)", dark=True))

# 9 · PASSWORD-TYPE: the password, then the hat-check ticket.
put("v2_09_password", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + A(MONO("PASSWORD", 34), 130, 110, "snap 0 0")
    + A(BIG("&ldquo;I LEFT MY HAT", 230, SL), 110, 200, "wipe .05 .3") + A(BIG("AT HOME.&rdquo;", 230, SL), 110, 430, "wipe .3 .48")
    + A(f'<div style="width:900px;background:{AM};padding:30px 40px;box-shadow:0 26px 50px rgba(10,14,24,.45);transform:rotate(-5deg);border:6px dashed {SL}"><div style="font:500 26px Plex;letter-spacing:8px;color:{SL}">INTERSTELLAR TRANSIT</div>'
        f'<div style="font:400 150px/1 Anton;color:{SL}">HAT CHECK</div><div style="font:500 30px Plex;letter-spacing:6px;color:{SL}">TICKET Nº 001 · KEEP THIS STUB</div></div>', 880, 640, "slam .6 .64", "z-index:40")
    + A(MONO("TICKET: OUR JOKE, NOT A DOCUMENT", 18), 1300, 990, "snap .6 .6", "z-index:41"),
    PAPER, "PASSWORD AS DESCRIBED IN WHEN PROPHECY FAILS (1956), VIA KELLY 2025 ⚠ PAGE TO CHECK · THE TICKET IS A STUDIO JOKE"))

# 10 · BOOK-COVER: the 1956 book, big, on the real stack.
put("v2_10_book", page(
    FULL("books_stack.jpg", "push 0 1", "center", .45)
    + A(f'<div style="width:620px;height:860px;box-sizing:border-box;background:{CO};padding:60px 50px;box-shadow:0 40px 80px rgba(0,0,0,.7);transform:rotate(-3deg);border-left:22px solid #1F4F86">'
        f'<div style="font:400 130px/.92 Anton;color:{PAPER}">WHEN<br>PROPHECY<br>FAILS</div><div style="font:500 22px/1.6 Plex;letter-spacing:4px;color:#CFE0F2;margin-top:40px">FESTINGER<br>RIECKEN<br>SCHACHTER</div>'
        f'<div style="font:400 90px Anton;color:{AM};margin-top:50px">1956</div></div>', 160, 110, "drop 0 .1", "z-index:30")
    + A(BIG("THAT'S HOW", 150, PAPER), 900, 300, "up .2 .3", "z-index:31") + A(BIG("THE BOOK", 220, PAPER), 896, 450, "up .28 .38", "z-index:31") + A(BIG("TELLS IT.", 220, AM), 896, 660, "slam .5 .55", "z-index:31")
    + A(MONO("COVER: STUDIO RECONSTRUCTION", 18, PAPER, "rgba(20,24,36,.85)"), 180, 1000, "fade 0 .02", "z-index:33"),
    SL, "BOOK: FESTINGER, RIECKEN & SCHACHTER, WHEN PROPHECY FAILS (1956); COVER REDRAWN · PHOTO: WONDERLANE / FLICKR, CC BY 2.0", dark=True))

# 11 · KELLY-PAPER: the 2025 paper's first page (reconstruction), one line highlighted.
ln = lambda w: f'<div style="height:14px;width:{w}%;background:#C9D3DF;margin:16px 0"></div>'
put("v2_11_kelly", page(
    DESK
    + A(SHEET(f'<div style="font:500 20px Plex;letter-spacing:4px;color:{CO}">JOURNAL OF THE HISTORY OF THE BEHAVIORAL SCIENCES · VOL. 62 · e70043</div>'
              f'<div style="font:400 92px/1 Anton;color:{SL};margin-top:26px">DEBUNKING<br>&ldquo;WHEN PROPHECY FAILS&rdquo;</div>'
              f'<div style="font:400 44px ISerif;color:#3A4456;margin-top:16px">Thomas Kelly · online 2025</div>' + ln(96) + ln(90) + ln(94)
              + f'<div data-anim="wipe .5 .75" style="font:400 62px/1.25 ISerif;color:{SL};margin:26px 0">{hl("one of them did more than take notes")}</div>' + ln(88) + ln(60), 1320, 900, -1.2, "#FFFFFF", 56), 120, 80, "drop 0 .08")
    + A(BIG("2025", 330, AM, .9, "text-shadow:0 12px 30px rgba(0,0,0,.5)"), 1300, 110, "slam .2 .25", "z-index:40")
    + F.tag("FIRST PAGE: RECONSTRUCTION · THE HIGHLIGHT IS OUR SUMMARY", 560, 960, 1.5, "snap .5 .5")
    + F.tag("ONE SCHOLAR'S READING · THE OTHER SIDE IS IN ACT 4", 1010, 560, -2, "snap .85 .85"),
    SL, "SOURCE: T. KELLY, 'DEBUNKING WHEN PROPHECY FAILS', JHBS 62, e70043 (ONLINE 2025), doi 10.1002/jhbs.70043 · KELLY'S CLAIMS, ATTRIBUTED", dark=True))
print("v2 pages ok")
