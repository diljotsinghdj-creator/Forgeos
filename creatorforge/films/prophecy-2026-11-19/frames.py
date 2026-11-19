"""Key frames (16:9) for "The Night the World Didn't End", Dragon Psychology, DJ style (John Oliver script, Vox x Johnny
Harris visuals). Palette: slate #141824, lab-paper #F0F4F8, cobalt #2B6CB0, amber #ED8936 (the only signal colour). No logo.
People are stick figures; documents are reconstructions, labelled. Numbers only from dossier.json."""
import json
import math
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
import studio  # noqa: E402
from studio import A, a, put, wobble  # noqa: E402

SL, PAPER, CO, AM, INKD = "#141824", "#F0F4F8", "#2B6CB0", "#ED8936", "#1F2633"
studio.SIG = AM
GRID = f"background:{PAPER};background-image:linear-gradient(rgba(43,108,176,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(43,108,176,.10) 1px,transparent 1px);background-size:40px 40px"
SLATE = f"background:{SL};background-image:radial-gradient(rgba(240,244,248,.05) 1px,transparent 1.5px);background-size:6px 6px"  # drawn slate (F1 AI desk retired 2026-11-19: "less ai", MASTER_DIRECTIVES 8c: a backdrop is never AI)
hl = lambda t: f'<span style="background:linear-gradient(transparent 52%,{AM} 52%,{AM} 92%,transparent 92%)">{t}</span>'


def page(body, bg=PAPER, src="", dark=False):
    return studio.page(body, bg, src, dark=dark, logo=False)


# ---- real pictures (assets/real, finished by real.py; credits in data/photo_credits.json) -------------------------------
def photo(f, w, h, x, y, anim="up 0 .15", rot=-1.5, extra="", inner="", pos="center", push=None):
    """A real photo as a printed, taped clipping: white border, shadow, a strip of tape. push = slow camera push on the print."""
    im = f'<img src="/assets/real/{f}" style="width:{w}px;height:{h}px;object-fit:cover;object-position:{pos};display:block">'
    if push:
        im = f'<div style="overflow:hidden;width:{w}px;height:{h}px"><div data-anim="push {push}">{im}</div></div>'
    return A(f'<div style="position:relative;background:#fff;padding:12px 12px 16px;box-shadow:0 22px 44px rgba(10,14,24,.42);transform:rotate({rot}deg)">{im}{inner}'
             f'<div style="position:absolute;left:{w / 2 - 70:.0f}px;top:-16px;width:150px;height:36px;background:rgba(236,232,220,.82);transform:rotate({-rot * 1.8:.1f}deg);box-shadow:0 2px 4px rgba(0,0,0,.2)"></div></div>', x, y, anim, extra)


def caption(t, x, y, anim="fade .2 .3", dark=False):
    bg, fg = ("rgba(240,244,248,.92)", SL) if dark else ("rgba(20,24,36,.86)", PAPER)
    return A(f'<div style="background:{bg};color:{fg};font:500 15px Plex;letter-spacing:2px;padding:6px 10px;white-space:nowrap">{t}</div>', x, y, anim, "z-index:60")


def circ(cx, cy, rx, ry, anim="draw .4 .55", seed=3, w=7):
    """The investigator's amber circle, drawn on."""
    return f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62" width="1920" height="1080"><path d="{wobble(cx, cy, rx, ry, seed)}" pathLength="1" fill="none" stroke="{AM}" stroke-width="{w}" stroke-linecap="round"/></svg>'


def arrow(x1, y1, x2, y2, anim="draw .5 .62"):
    return (f'<svg class="a" data-anim="{anim}" style="left:0;top:0;z-index:62" width="1920" height="1080"><path d="M{x1} {y1} Q {(x1 + x2) / 2 + 40} {min(y1, y2) - 60} {x2} {y2}" pathLength="1" fill="none" stroke="{AM}" stroke-width="6" stroke-linecap="round"/>'
            f'<path d="M{x2 - 18} {y2 - 22} L{x2} {y2} L{x2 - 26} {y2 + 6}" pathLength="1" fill="none" stroke="{AM}" stroke-width="6" stroke-linecap="round"/></svg>')


# ---- Natural Earth geodata (shared by the locator insets and the Great Lakes map) ----------------------------------------
W = {c["n"]: c["r"] for c in json.load(open("/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))["countries"]}
LK = json.load(open(D / "data" / "lakes.json"))["lakes"]


def locator(x, y, w, h, box, pins, anim="up .3 .42", dark=False, title="OAK PARK, ILLINOIS"):
    """A small real-data locator map (Natural Earth): the US, Canada and the Great Lakes, with pins."""
    px = lambda lo, la: ((lo - box[0]) / (box[2] - box[0]) * w, (box[3] - la) / (box[3] - box[1]) * h)
    pth = lambda rings: "".join("M" + " L".join("%.1f %.1f" % px(lo, la) for lo, la in r) + "Z" for r in rings)
    land, edge, water = ("#2A3142", "#4A5468", "#141824") if dark else (PAPER, "#AFC0D3", "#9FB6CF")
    pin = "".join(f'<circle cx="{px(lo, la)[0]:.0f}" cy="{px(lo, la)[1]:.0f}" r="9" fill="{AM}" stroke="{PAPER}" stroke-width="3"/>'
                  f'<text x="{px(lo, la)[0] + 14:.0f}" y="{px(lo, la)[1] + 6:.0f}" font-family="Plex" font-size="16" letter-spacing="2" fill="{PAPER if dark else SL}">{n}</text>' for n, lo, la in pins)
    svg = (f'<svg width="{w}" height="{h}" style="display:block;background:{water}"><path d="{pth(W["United States of America"])}" fill="{land}" stroke="{edge}" stroke-width="1.5"/>'
           f'<path d="{pth(W["Canada"])}" fill="{land}" stroke="{edge}" stroke-width="1.5" opacity=".8"/><path d="{pth([l["r"] for l in LK])}" fill="{water}"/>{pin}</svg>')
    return A(f'<div style="border:3px solid {PAPER if dark else SL};box-shadow:0 14px 28px rgba(0,0,0,.4)">{svg}<div style="background:{PAPER if dark else SL};color:{SL if dark else PAPER};font:500 14px Plex;letter-spacing:3px;padding:5px 10px">{title}</div></div>', x, y, anim, "z-index:45")


def chapter(n, t, dark=False):
    bg, fg = (PAPER, SL) if dark else (SL, PAPER)
    return a(f'<div style="background:{bg};color:{fg};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER {n} · {t}</div>', 70, 60)


def panel_(inner, x, y, w, anim="up .1 .25"):
    return A(f'<div style="width:{w}px;background:#FFFFFF;padding:26px 30px;box-shadow:0 18px 34px rgba(10,14,24,.35);border-top:8px solid {CO}">{inner}</div>', x, y, anim, "z-index:40")


def tag(text, x, y, rot=-1.5, anim="snap .85 .85", light=False):
    bg, fg = (PAPER, SL) if light else (SL, PAPER)
    return A(f'<div style="background:{bg};color:{fg};border:2px solid {fg};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;transform:rotate({rot}deg);'
             f'box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>', x, y, anim, "z-index:70")


def card(inner, w, x, y, anim, rot=-1.2, bg="#FFFFFF", extra=""):
    return A(f'<div style="width:{w}px;background:{bg};padding:26px 30px;box-shadow:0 18px 34px rgba(10,14,24,.35);transform:rotate({rot}deg);border-top:8px solid {CO}">{inner}</div>', x, y, anim, extra)


def study(authors, year, journal, extra="", note=""):
    return (f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">STUDY CARD</div>'
            f'<div style="font:400 40px/1.05 Anton;color:{SL};margin-top:8px">{authors} · {year}</div>'
            f'<div style="font:400 26px ISerif;color:#3A4456;margin-top:4px">{journal}</div>'
            + (f'<div style="font:500 17px Plex;color:#3A4456;margin-top:10px">{extra}</div>' if extra else "")
            + (f'<div style="display:inline-block;margin-top:10px;background:{SL};color:{PAPER};font:500 14px Plex;letter-spacing:2px;padding:4px 8px">{note}</div>' if note else ""))


def stamp(text, x, y, anim, rot=-10, size=52, dark=False):
    return A(f'<div style="border:7px solid {AM};color:{AM};font:400 {size}px/1 Anton;letter-spacing:3px;padding:6px 18px;transform:rotate({rot}deg);background:{"rgba(20,24,36,.85)" if dark else "rgba(240,244,248,.6)"}">{text}</div>', x, y, anim, "z-index:65")


def clock(h, m, size=420, label="", face=SL, crack=False, spin=None):
    c = size / 2; r = c - 14
    ticks = "".join(f'<line x1="{c + (r - (26 if i % 3 == 0 else 14)) * math.sin(math.radians(i * 30)):.1f}" y1="{c - (r - (26 if i % 3 == 0 else 14)) * math.cos(math.radians(i * 30)):.1f}" '
                    f'x2="{c + r * math.sin(math.radians(i * 30)):.1f}" y2="{c - r * math.cos(math.radians(i * 30)):.1f}" stroke="{PAPER}" stroke-width="{6 if i % 3 == 0 else 3}"/>' for i in range(12))
    ha = math.radians((h % 12 + m / 60) * 30); ma = math.radians(m * 6)
    hand = lambda ang, ln, w, col: f'<line x1="{c}" y1="{c}" x2="{c + ln * math.sin(ang):.1f}" y2="{c - ln * math.cos(ang):.1f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
    cr = (f'<path d="M{c - 10} 18 L{c + 8} {c * .55:.0f} L{c - 14} {c * .9:.0f} L{c + 12} {c * 1.3:.0f} L{c - 4} {size - 18}" fill="none" stroke="{AM}" stroke-width="4" pathLength="1"/>' if crack else "")
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block;filter:drop-shadow(0 18px 30px rgba(0,0,0,.45))">'
            f'<circle cx="{c}" cy="{c}" r="{r + 8}" fill="{CO}"/><circle cx="{c}" cy="{c}" r="{r}" fill="{face}"/>{ticks}'
            + (f'<g data-anim="spin {spin}" style="transform-origin:{c}px {c}px">' if spin else "") + f'{hand(ha, r * .5, 12, PAPER)}{hand(ma, r * .78, 8, PAPER)}' + ("</g>" if spin else "") + f'<circle cx="{c}" cy="{c}" r="12" fill="{AM}"/>{cr}</svg>'
            + (f'<div style="font:500 20px Plex;letter-spacing:4px;color:{PAPER};text-align:center;margin-top:16px;width:{size}px">{label}</div>' if label else ""))


def stick(x, y, s=1.0, col=SL, up=False, extra=""):
    arms = f'<path d="M-18 -8 L0 4 L18 -8" fill="none" stroke="{col}" stroke-width="4"/>' if up else f'<path d="M-16 22 L0 4 L16 22" fill="none" stroke="{col}" stroke-width="4"/>'
    return (f'<g transform="translate({x},{y}) scale({s})" {extra}><circle cx="0" cy="-22" r="11" fill="none" stroke="{col}" stroke-width="4"/>'
            f'<line x1="0" y1="-11" x2="0" y2="30" stroke="{col}" stroke-width="4"/>{arms}<path d="M-14 62 L0 30 L14 62" fill="none" stroke="{col}" stroke-width="4"/></g>')


# ---- the house plan (reused) --------------------------------------------------------------------------------------------
def house(figs, observers=True, fade_from=None, halo=False):
    walls = (f'<rect x="420" y="250" width="1080" height="640" fill="none" stroke="{CO}" stroke-width="6"/>'
             f'<line x1="1100" y1="250" x2="1100" y2="600" stroke="{CO}" stroke-width="4"/><line x1="1100" y1="680" x2="1100" y2="890" stroke="{CO}" stroke-width="4"/>'
             f'<line x1="420" y1="620" x2="760" y2="620" stroke="{CO}" stroke-width="4"/><rect x="1420" y="760" width="80" height="12" fill="{PAPER}"/>'
             f'<text x="760" y="300" font-family="Plex" font-size="20" fill="{CO}" letter-spacing="4">LIVING ROOM</text><text x="1180" y="300" font-family="Plex" font-size="20" fill="{CO}" letter-spacing="4">KITCHEN</text>'
             f'<text x="460" y="660" font-family="Plex" font-size="20" fill="{CO}" letter-spacing="4">BATHROOM</text><text x="1520" y="780" font-family="Plex" font-size="18" fill="{CO}" letter-spacing="3">BACK DOOR</text>')
    pts = [(560, 420), (650, 460), (740, 400), (830, 470), (920, 420), (1010, 460), (600, 540), (700, 560), (880, 560), (980, 550)][:figs]
    people = ""
    for i, (x, y) in enumerate(pts):
        an = f'data-anim="fade {1 - (fade_from + i * .07):.2f} {1 - (fade_from + i * .07) + .01:.2f}"' if fade_from is not None else ""
        people += stick(x, y, 1.0, SL, extra=an) if fade_from is None else f'<g data-anim="snap 0 0">{stick(x, y, 1.0, SL)}</g>'
    obs = ""
    if observers:
        for i, (x, y) in enumerate(((500, 740), (590, 760), (1250, 470))):
            obs += f'<g data-anim="fade {.45 + i * .05:.2f} {.52 + i * .05:.2f}">{stick(x, y, .95, AM)}<rect x="{x + 16}" y="{y - 8}" width="20" height="26" fill="{PAPER}" stroke="{AM}" stroke-width="3"/></g>'
        if halo:
            obs += f'<ellipse cx="1250" cy="430" rx="24" ry="7" fill="none" stroke="{AM}" stroke-width="4" data-anim="fade .3 .4"/>'
    return f'<svg class="a" style="left:0;top:0" width="1920" height="1080">{walls}{people}{obs}</svg>'


# ==== 1 HOOK ============================================================================================================
put("01_clock", page(
    a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0)
    + A(clock(11, 59, 640), 640, 150, "slam .05 .08")
    + A(f'<div style="background:{PAPER};color:{SL};padding:10px 18px;font:500 24px Plex;letter-spacing:5px">20 DEC 1954 · OAK PARK, ILLINOIS</div>', 690, 880, "up .25 .35")
    + A(f'<div style="font:700 54px/1.1 Caveat;color:{AM};width:420px;transform:rotate(-3deg)">"Look closely at this minute."</div>', 1380, 300, "fade .5 .65")
    + locator(1380, 560, 440, 260, (-94.0, 39.0, -80.0, 47.5), [("OAK PARK", -87.78, 41.89)], "up .3 .42", True, "20 DEC 1954 · OAK PARK, ILLINOIS"),
    SL, "CLOCK DRAWN IN THE STUDIO · LOCATOR: NATURAL EARTH (PUBLIC DOMAIN) · DATE AND PLACE: KELLY 2025 AND FESTINGER, RIECKEN & SCHACHTER 1956", dark=True))

put("02_house", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + f'<svg class="a" data-anim="draw 0 .3" style="left:0;top:0" width="1920" height="1080"><rect x="420" y="250" width="1080" height="640" pathLength="1" fill="none" stroke="{CO}" stroke-width="6"/></svg>'
    + A(house(10), 0, 0, "fade .25 .35")
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">THE PREDICTION</div><div style="font:400 36px/1.05 Anton;color:{SL};margin-top:6px">FLOOD ON {hl("21 DEC 1954")}</div>'
           f'<div style="font:400 26px ISerif;color:#3A4456">rescue by flying saucer the night before</div>', 320, 1530, 70, "up .55 .68", 1.5)
    + tag("UNDERCOVER RESEARCHERS PRESENT: 3", 1240, 960, -1.5, "snap .8 .8")
    + locator(1540, 330, 330, 200, (-93.5, 40.0, -81.0, 47.0), [("OAK PARK", -87.78, 41.89)], "up .1 .22", False, "A HOUSE IN OAK PARK, IL")
    + chapter(1, "THE WAITING ROOM"),
    PAPER, "LOCATOR: NATURAL EARTH (PUBLIC DOMAIN) · HOUSE PLAN: STUDIO SKETCH, NOT THE REAL LAYOUT · PEOPLE: STICK FIGURES · PREDICTION AND OBSERVERS: KELLY 2025; FRS 1956 · THE THREE OBSERVERS SHOWN IN AMBER"))

items = ["ZIP", "CLASP", "BUCKLE", "COINS"]
put("03_metal", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(1, "THE WAITING ROOM")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{SL}">THE BOARDING<br>REQUIREMENTS</div>', 110, 150, "up 0 .1")
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080">{stick(400, 640, 2.2, SL)}<path d="M720 820 Q 820 900 920 820 Z" fill="{CO}" opacity=".9"/></svg>'
    + "".join(A(f'<div style="background:{SL};color:{PAPER};font:500 20px Plex;letter-spacing:3px;padding:6px 12px;border-radius:6px">{t}</div>', 480 + i * 70, 560 + i * 40, f"drop {.2 + i * .1:.2f} {.27 + i * .1:.2f}") for i, t in enumerate(items))
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">ACCORDING TO THE 1956 BOOK</div>'
           f'<div style="font:400 30px/1.4 ISerif;color:{SL};margin-top:8px">· remove all metal from your body and clothes<br>· password: {hl("\"I left my hat at home\"")}<br>· passport: a stamped envelope</div>', 640, 1120, 260, "up .55 .7", 1.2)
    + tag("AIRLINE: UNKNOWN · BAGGAGE POLICY: STRICT", 1150, 820, -1.5, "snap .88 .88")
    + A(f'<img src="/assets/real/penny.png" style="width:230px;display:block;filter:drop-shadow(0 16px 18px rgba(0,0,0,.45))">', 820, 300, "drop .42 .52", "z-index:30;transform-origin:50% 50%")
    + caption("A REAL ONE-CENT COIN · ALSO NOT ALLOWED", 760, 545, "fade .5 .58")
    + circ(935, 415, 140, 140, "draw .55 .66", 5, 6),
    PAPER, "SOURCE: WHEN PROPHECY FAILS (1956), AS SUMMARISED IN KELLY 2025, JHBS 62:e70043 · PHOTO: MATTHIASXC / FLICKR, CC BY 2.0 (A US CENT, ILLUSTRATIVE) · STICK FIGURE AND ITEMS DRAWN IN THE STUDIO"))

put("04_title", page(
    a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0)
    + A(f'<div style="font:400 64px ISerif;color:#C9D3E0;text-align:center;width:1920px">You\'ve used it: <span style="color:{PAPER}">cognitive dissonance</span>.</div>', 0, 190, "fade 0 .12")
    + A(f'<div style="font:400 190px/0.88 Anton;color:{PAPER};text-align:center;width:1920px">THE NIGHT THE WORLD<br><span style="color:{AM}">DIDN\'T END</span></div>', 0, 380, "slam .3 .33")
    + stamp("REPLICATION?", 1420, 800, "slam .7 .72", -8, 56, True),
    SL, "DRAGON PSYCHOLOGY", dark=True))

# ==== 2 HISTORY ==========================================================================================================
marks = [("~300,000 YEARS AGO", "small groups", 180), ("1844", "the Millerites", 760), ("1954", "the waiting room", 1180), ("TODAY", "you", 1640)]
put("05_timeline", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(2, "WHY BRAINS DEFEND BELIEFS")
    + A(f'<div style="width:1660px;height:6px;background:{SL}"></div>', 130, 560, "wipe 0 .5")
    + "".join(A(f'<div style="width:22px;height:22px;border-radius:50%;background:{AM if i == 0 else CO};margin:-8px 0 14px"></div><div style="font:400 40px Anton;color:{SL}">{d}</div><div style="font:400 28px ISerif;color:#3A4456">{t}</div>', x, 560, f"up {.1 + i * .12:.2f} {.18 + i * .12:.2f}") for i, (d, t, x) in enumerate(marks))
    + f'<svg class="a" data-anim="fade .05 .15" style="left:0;top:0" width="1920" height="1080">{"".join(stick(170 + i * 46, 430, .8, SL) for i in range(5))}</svg>'
    + card(study("MERCIER & SPERBER", "2011", "Behavioral and Brain Sciences 34", "\"Why do humans reason?\" Reasoning evolved to argue and persuade, not for solo truth-seeking.", "THEORY · DEBATED"), 640, 1180, 140, "up .6 .72", 1.5)
    + photo("millerite_chart.jpg", 200, 268, 720, 190, "drop .25 .33", -3)
    + caption("THE REAL CHART · BOSTON, 1843", 700, 495, "fade .3 .36"),
    PAPER, "CHART: J. V. HIMES, BOSTON 1843, PUBLIC DOMAIN (WIKIMEDIA COMMONS) · SOURCE: MERCIER & SPERBER, 'WHY DO HUMANS REASON? ARGUMENTS FOR AN ARGUMENTATIVE THEORY', BBS 34 (2011) 57-111 · A THEORY WITH OPEN PEER COMMENTARY, NOT SETTLED · TIMELINE NOT TO SCALE"))

put("06_membership", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(2, "WHY BRAINS DEFEND BELIEFS")
    + A(f'<div style="width:4px;height:760px;background:{SL}"></div>', 958, 180, "wipe 0 .1")
    + A(f'<div style="font:400 44px Anton;color:{SL};width:700px;text-align:center">ADMITS THE MISTAKE</div>', 160, 190, "fade .05 .12")
    + A(f'<div style="font:400 44px Anton;color:{SL};width:700px;text-align:center">DIGS IN</div>', 1060, 190, "fade .05 .12")
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080">{stick(510, 520, 1.8, SL)}'
      f'<g data-anim="up .2 .35">{stick(330, 560, 1.4, "#8A94A6")}{stick(700, 560, 1.4, "#8A94A6")}</g>'
      f'{stick(1410, 520, 1.8, AM, True)}<g data-anim="pop .3 .45">{"".join(stick(1410 + 240 * math.cos(k), 560 + 120 * math.sin(k), 1.2, CO) for k in (0.3, 1.2, 2.0, 2.9, 3.6, 5.6))}</g></svg>'
    + A(f'<div style="font:700 36px Caveat;color:#5B6576">allies wander off</div>', 330, 760, "fade .38 .45")
    + A(f'<div style="width:380px;background:{CO};color:{PAPER};padding:22px 26px;border-radius:18px;box-shadow:0 16px 28px rgba(0,0,0,.3);transform:rotate(-3deg)">'
        f'<div style="font:500 15px Plex;letter-spacing:3px">MEMBERSHIP CARD</div><div style="font:400 44px/1 Anton;margin-top:8px">MY BELIEF</div><div style="font:400 24px ISerif;margin-top:6px">valid as long as I never update it</div></div>', 1380, 820, "drop .6 .7")
    + photo("padlock.jpg", 170, 200, 1700, 690, "drop .72 .8", 7, "z-index:50", pos="50% 70%")
    + tag("ILLUSTRATION OF THE THEORY, NOT A STUDY", 120, 940, -1.5, "fade .05 .1"),
    PAPER, "ILLUSTRATION OF THE SOCIAL ACCOUNT OF BELIEF (E.G. MERCIER & SPERBER 2011) · PHOTO: ANDYPOWE11 / FLICKR, CC BY 2.0 · STICK FIGURES DRAWN IN THE STUDIO"))

# 07 · the real 1843 Millerite chart (public domain), full sheet + the sums that "end" in 1843
put("07_millerites", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(2, "WHY BRAINS DEFEND BELIEFS")
    + photo("millerite_chart.jpg", 500, 671, 110, 150, "up 0 .14", -2.5, push=".0 1")
    + photo("millerite_detail.jpg", 560, 507, 560, 330, "up .14 .26", 2, "z-index:20", push=".14 1")
    + circ(790, 680, 115, 42, "draw .32 .44", 4)
    + arrow(960, 895, 880, 725, "draw .38 .46")
    + A(f'<div style="font:700 40px Caveat;color:{AM};transform:rotate(-3deg);background:rgba(240,244,248,.85);padding:0 10px">the maths "ends" here</div>', 830, 890, "fade .4 .48", "z-index:63")
    + caption("A CHRONOLOGICAL CHART OF THE VISIONS OF DANIEL & JOHN · J. V. HIMES, BOSTON, 1843", 110, 862, "fade .2 .3")
    + tag("THEN: 22 OCT 1844", 1180, 230, 3, "snap .5 .5")
    + A(f'<div style="font:400 100px/0.9 Anton;color:{SL}">THE GREAT<br>{hl("DISAPPOINTMENT")}</div>', 1180, 300, "slam .55 .57")
    + A(f'<div style="font:400 34px/1.3 ISerif;color:#3A4456;width:660px">The Millerites printed the end of the world on a chart. 1843 passed; the date moved to 22 October 1844. It didn\'t come either. Historians gave it the most polite name possible.</div>', 1182, 560, "fade .62 .74")
    + tag("NAMING DEPARTMENT: UNDERSTATED", 1180, 860, 2, "snap .88 .88"),
    PAPER, "CHART: 'A CHRONOLOGICAL CHART OF THE VISIONS OF DANIEL & JOHN', J. V. HIMES / B. W. THAYER, BOSTON 1843, PUBLIC DOMAIN (WIKIMEDIA COMMONS, SCAN: GEOGRAPHICUS) · THE 'GREAT DISAPPOINTMENT', 22 OCT 1844: WELL-ESTABLISHED HISTORY; CITED BY FRS 1956 (KELLY 2025)"))

# ---- the map: where it happened (Natural Earth) ---------------------------------------------------------------------------
BOX = (-97.0, 39.5, -79.0, 49.5)
PX = lambda lo, la: ((lo - BOX[0]) / (BOX[2] - BOX[0]) * 1920, (BOX[3] - la) / (BOX[3] - BOX[1]) * 1080)
path = lambda rings: "".join("M" + " L".join("%.0f %.0f" % PX(lo, la) for lo, la in r) + "Z" for r in rings)
pins = [("MINNEAPOLIS", "the researchers' university", -93.27, 44.98, .1), ("OAK PARK", "the waiting room, Dec 1954", -87.78, 41.89, .35),
        ("EAST LANSING", "the believers' second base", -84.48, 42.74, .5), ("ANN ARBOR", "the archive, unsealed 2025", -83.74, 42.28, .75)]
pinsvg = "".join(f'<g data-anim="pop {s:.2f} {s + .06:.2f}"><circle cx="{PX(lo, la)[0]:.0f}" cy="{PX(lo, la)[1]:.0f}" r="13" fill="{AM if n == "ANN ARBOR" else CO}" stroke="{PAPER}" stroke-width="3"/></g>' for n, _, lo, la, s in pins)
labels = "".join(A(f'<div style="background:{PAPER};padding:6px 12px;box-shadow:0 6px 12px rgba(0,0,0,.25)"><div style="font:500 18px Plex;letter-spacing:3px;color:{SL}">{n}</div><div style="font:400 22px ISerif;color:#3A4456">{t}</div></div>',
                   PX(lo, la)[0] + (22 if n not in ("ANN ARBOR",) else 24), PX(lo, la)[1] + (-70 if n == "EAST LANSING" else 14), f"fade {s + .03:.2f} {s + .1:.2f}", "z-index:31") for n, t, lo, la, s in pins)
route = lambda p, q: f'<path d="M{PX(*p)[0]:.0f} {PX(*p)[1]:.0f} Q {(PX(*p)[0] + PX(*q)[0]) / 2:.0f} {min(PX(*p)[1], PX(*q)[1]) - 120:.0f} {PX(*q)[0]:.0f} {PX(*q)[1]:.0f}" pathLength="1" fill="none" stroke="{CO}" stroke-width="5" stroke-dasharray="0.02 0.015"/>'
put("08_map", page(
    a(f'<div style="width:1920px;height:1080px;background:#DCE5EF"></div>', 0, 0)
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080"><path d="{path(W["United States of America"])}" fill="{PAPER}" stroke="#AFC0D3" stroke-width="2"/>'
      f'<path d="{path(W["Canada"])}" fill="#E7EDF4" stroke="#AFC0D3" stroke-width="2"/><path d="{path([l["r"] for l in LK])}" fill="#9FB6CF"/>{pinsvg}</svg>'
    + "".join(f'<svg class="a" data-anim="draw {s0} {s1}" style="left:0;top:0;z-index:30" width="1920" height="1080">{route(p0, q0)}</svg>' for p0, q0, s0, s1 in
              (((-93.27, 44.98), (-87.78, 41.89), .14, .33), ((-87.78, 41.89), (-84.48, 42.74), .38, .49), ((-84.48, 42.74), (-83.74, 42.28), .53, .74)))
    + labels + chapter(2, "WHERE IT HAPPENED")
    + A(f'<div style="font:400 72px/0.95 Anton;color:{SL};text-shadow:0 2px 0 {PAPER}">THREE PSYCHOLOGISTS<br>GO UNDERCOVER</div>', 90, 820, "up .6 .7")
    + tag("DISGUISE: TWEED", 1500, 940, 2, "snap .9 .9"),
    "#DCE5EF", "MAP: NATURAL EARTH (COUNTRIES 110M, LAKES 50M; PUBLIC DOMAIN) · PLACES: KELLY 2025 (OAK PARK, EAST LANSING, BENTLEY HISTORICAL LIBRARY, UNIVERSITY OF MINNESOTA) · ROUTE DRAWN IN STORY ORDER (MINNEAPOLIS → OAK PARK → EAST LANSING → ANN ARBOR), NOT A TRAVEL RECORD"))

# ==== 3 MECHANICS =========================================================================================================
put("09_midnight", page(
    a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0)
    + A(clock(0, 0, 560), 680, 140, "slam 0 .03")
    + A(f'<div style="font:400 120px Anton;color:{PAPER};text-align:center;width:1920px">MIDNIGHT.</div>', 0, 760, "snap .3 .3")
    + A(f'<div style="font:400 60px ISerif;color:{AM};text-align:center;width:1920px">Nothing.</div>', 0, 900, "snap .65 .65"),
    SL, "THE GROUP WAITED THROUGH THE NIGHT OF 20-21 DEC 1954 (KELLY 2025) · CLOCK DRAWN IN THE STUDIO", dark=True))

put("10_christmas", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(3, "THE CHRISTMAS MESSAGE")
    + A(f'<div style="opacity:.55">{clock(4, 40, 300, "", SL)}</div>', 120, 180, "fade 0 .1")
    + A(f'<div style="font:500 18px Plex;letter-spacing:4px;color:{CO}">BEFORE DAWN · 21 DEC 1954</div>', 120, 500, "fade .05 .12")
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">A NEW MESSAGE (PARAPHRASE)</div>'
           f'<div style="font:400 48px/1.25 ISerif;color:{SL};margin-top:12px">The group has spread so much light that {hl("the flood has been called off")}.</div>', 940, 600, 220, "up .2 .35", -1.5)
    + tag("OUTCOME: SAVED THE WORLD (UNVERIFIED)", 640, 640, -2, "snap .7 .7")
    + A(f'<div style="font:700 50px/1.1 Caveat;color:{AM};width:900px;transform:rotate(-2deg)">"You didn\'t miss the deadline. You were so good the deadline cancelled itself."</div>', 640, 760, "fade .8 .92"),
    PAPER, "THE 'CHRISTMAS MESSAGE', EARLY 21 DEC 1954: KELLY 2025 AND FRS 1956 · WORDING PARAPHRASED, NOT QUOTED · CLOCK TIME ILLUSTRATIVE"))

put("11_book", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(3, "THE CHRISTMAS MESSAGE")
    + A(f'<div style="width:470px;height:680px;background:linear-gradient(160deg,#2B6CB0,#1C4A7C);box-shadow:0 30px 50px rgba(0,0,0,.45);transform:rotate(-3deg);padding:60px 44px;box-sizing:border-box">'
        f'<div style="font:400 84px/0.92 Anton;color:{PAPER}">WHEN<br>PROPHECY<br>FAILS</div><div style="font:500 20px Plex;letter-spacing:3px;color:#CFE0F2;margin-top:26px">FESTINGER · RIECKEN · SCHACHTER · 1956</div>'
        f'<div style="font:500 13px Plex;color:#9DB8D6;margin-top:250px">COVER DRAWN IN THE STUDIO</div></div>', 170, 200, "up 0 .14")
    + "".join(A(f'<div style="background:{SL};color:{PAPER};font:500 22px Plex;letter-spacing:2px;padding:10px 16px;border-radius:10px">☎ {t}</div>'.replace("☎ ", "● "), 760 + (i % 2) * 380, 300 + i * 120, f"pop {.25 + i * .1:.2f} {.32 + i * .1:.2f}") for i, t in enumerate(("CALLS THE NEWSPAPERS", "INVITES REPORTERS", "STARTS RECRUITING", "SINGS CAROLS, CHRISTMAS EVE")))
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">THE BOOK\'S CLAIM</div><div style="font:400 40px/1.15 Anton;color:{SL};margin-top:6px">THE FAILURE MADE THEM {hl("DOUBLE DOWN")}</div>', 620, 1160, 780, "up .7 .82", 1.5),
    PAPER, "SOURCE: WHEN PROPHECY FAILS (1956) AS SUMMARISED BY KELLY 2025; CHRISTMAS EVE CAROLS: KELLY 2025 · BOOK COVER IS A STUDIO DRAWING"))

rings = "".join(f'<path d="M{cx - r} {cy} A {r} {r} 0 0 1 {cx + r * .2:.0f} {cy - r}" fill="none" stroke="{AM}" stroke-width="6" stroke-linecap="round" data-anim="fade {s} {s + .04:.2f}"/>' for cx, cy, r, s in ((640, 360, 60, .3), (640, 360, 95, .36), (640, 360, 130, .42)))
put("11b_phones", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(3, "THE NIGHT")
    + photo("phone_model500.jpg", 760, 506, 100, 250, "up 0 .14", -2, push="0 1")
    + photo("phone_bakelite.jpg", 400, 291, 640, 610, "drop .2 .3", 4, "z-index:20")
    + f'<svg class="a" style="left:0;top:0;z-index:40" width="1920" height="1080">{rings}</svg>'
    + caption("REAL 1950s DESK PHONES · NOT THE GROUP'S OWN", 110, 790, "fade .15 .25")
    + panel_(f'<div style="font:400 80px/0.95 Anton;color:{SL}">SUDDENLY,<br>{hl("PUBLICITY")}</div><div style="font:400 32px/1.3 ISerif;color:#3A4456;margin-top:14px">After the failed night, the group phoned the newspapers and started recruiting, according to the 1956 book.</div>', 1180, 170, 640, "up .4 .52")
    + tag("THE BOOK'S VERSION · DISPUTED IN CHAPTER 4", 1180, 640, -1.5, "snap .7 .7")
    + A(f'<div style="font:700 46px/1.1 Caveat;color:{AM};width:600px;transform:rotate(-2deg)">"Hello, newspaper? The world didn\'t end. Please don\'t print that part."</div>', 1180, 740, "fade .8 .9"),
    PAPER, "CLAIM: FESTINGER, RIECKEN & SCHACHTER, WHEN PROPHECY FAILS (1956); CONTESTED BY KELLY 2025 · PHOTOS: PHILLIP PESSAR / FLICKR (WESTERN UNION MODEL 500) AND NREIJMERSDAL / FLICKR, BOTH CC BY 2.0"))

valve = (f'<svg class="a" style="left:0;top:0" width="1920" height="1080">'
         f'<g data-anim="draw 0 .25"><path d="M120 420 L760 420" pathLength="1" stroke="{CO}" stroke-width="44" fill="none"/><path d="M120 660 L760 660" pathLength="1" stroke="{SL}" stroke-width="44" fill="none"/></g>'
         f'<text x="140" y="380" font-family="Anton" font-size="44" fill="{CO}">BELIEF</text><text x="140" y="740" font-family="Anton" font-size="44" fill="{SL}">REALITY</text>'
         f'<circle cx="900" cy="540" r="150" fill="{PAPER}" stroke="{SL}" stroke-width="10"/><text x="900" y="550" text-anchor="middle" font-family="Anton" font-size="40" fill="{SL}">DISSONANCE</text>'
         f'<path d="M760 420 Q 820 420 850 470 M760 660 Q 820 660 850 610" stroke="{SL}" stroke-width="30" fill="none"/>'
         f'<g data-anim="fade .3 .4"><path d="M980 470 A 110 110 0 0 1 1010 540" stroke="{AM}" stroke-width="10" fill="none"/><line x1="900" y1="540" x2="985" y2="470" stroke="{AM}" stroke-width="8"/></g>'
         + "".join(f'<g data-anim="draw {.45 + i * .1:.2f} {.55 + i * .1:.2f}"><path d="M1050 540 Q 1200 {380 + i * 160} 1400 {380 + i * 160}" pathLength="1" stroke="{AM if i == 2 else "#8A94A6"}" stroke-width="{34 if i == 2 else 22}" fill="none"/></g>'
                   f'<text x="1430" y="{392 + i * 160}" font-family="Anton" font-size="40" fill="{AM if i == 2 else "#5B6576"}" data-anim="fade {.5 + i * .1:.2f} {.56 + i * .1:.2f}">{t}</text>' for i, t in enumerate(("CHANGE THE BELIEF", "IGNORE THE FACT", "ADD A NEW STORY")))
         + "</svg>")
put("12_valve", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(3, "THE THEORY") + valve
    + A(f'<img src="/assets/real/gauge.jpg" style="width:300px;height:300px;object-fit:cover;border-radius:50%;border:10px solid {SL};display:block;box-shadow:0 18px 30px rgba(0,0,0,.35)">', 740, 380, "pop .22 .34", "z-index:20")
    + A(f'<div style="background:{SL};color:{PAPER};font:400 36px Anton;letter-spacing:2px;padding:4px 16px">DISSONANCE</div>', 800, 712, "fade .3 .38", "z-index:21")
    + circ(895, 470, 60, 50, "draw .36 .46", 6, 6)
    + A(f'<div style="font:500 20px Plex;letter-spacing:3px;color:#5B6576">EXPENSIVE ↑ · CHEAP ↓</div>', 1430, 900, "fade .8 .9")
    + tag("METAPHOR, NOT ANATOMY", 120, 940, -1.5, "fade 0 .1"),
    PAPER, "COGNITIVE DISSONANCE AS DESCRIBED BY FESTINGER (1957, A THEORY OF COGNITIVE DISSONANCE) · DIAGRAM IS A STUDIO METAPHOR · GAUGE PHOTO: WWARBY / FLICKR, CC BY 2.0"))

pegs = "".join(f'<circle cx="{560 + (i % 6) * 50}" cy="{520 + (i // 6) * 50}" r="14" fill="{CO}" data-anim="pop {.1 + i * .01:.2f} {.13 + i * .01:.2f}"/>' for i in range(24))
put("13_carlsmith", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(3, "THE THEORY")
    + card(study("FESTINGER & CARLSMITH", "1959", "J. of Abnormal and Social Psychology", "A dull task (turning pegs), then paid to tell the next person it was fun."), 660, 110, 150, "up 0 .12", -1.5)
    + photo("pegboard.jpg", 400, 266, 470, 450, "up .02 .12", -1)
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080">{pegs}{stick(390, 600, 1.4, SL)}</svg>'
    + caption("A REAL PEG BOARD · NOT THE 1959 APPARATUS", 470, 760, "fade .1 .2")
    + A(f'<div style="width:560px;height:5px;background:{SL}"></div><div style="font:500 16px Plex;letter-spacing:3px;color:#5B6576;margin-top:6px">ZERO</div>', 1060, 720, "wipe .3 .4")
    + A(f'<div style="width:220px;height:120px;background:#8A94A6"></div><div style="font:400 48px Anton;color:{SL};text-align:center;width:220px;margin-top:10px">PAID $20</div>', 1100, 600, "grow .4 .52")
    + A(f'<div style="width:220px;height:300px;background:{AM}"></div><div style="font:400 48px Anton;color:{SL};text-align:center;width:220px;margin-top:10px">PAID $1</div>', 1400, 420, "grow .55 .68")
    + A(f'<div style="font:500 18px Plex;letter-spacing:3px;color:#5B6576;width:560px">LATER SAID THE TASK WAS ENJOYABLE (DIRECTION OF THE EFFECT)</div>', 1100, 340, "fade .4 .5")
    + tag("ILLUSTRATIVE BARS · EXACT SCORES TO CHECK", 1100, 900, -1.5, "fade .6 .7")
    + tag("PROJECT STATUS: ALWAYS WAS A SUCCESS", 120, 900, 2, "snap .88 .88", True),
    PAPER, "SOURCE: FESTINGER & CARLSMITH, 'COGNITIVE CONSEQUENCES OF FORCED COMPLIANCE', J ABNORM SOC PSYCHOL 58 (1959) · BARS SHOW THE DIRECTION OF THE RESULT, NOT THE MEASURED SCORES · PEG BOARD PHOTO: ERIC M MARTIN / FLICKR, CC BY 2.0"))

put("14_twoclocks", page(
    a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0)
    + A(clock(0, 0, 440, "1954 · THE NIGHT", spin="0 .3"), 340, 220, "fade 0 .1")
    + A(f'<div>{clock(10, 10, 440, "2025 · THE ARCHIVE", spin=".38 .8")}</div>', 1140, 220, "slam .35 .38")
    + A(f'<div style="font:400 50px ISerif;color:#C9D3E0;text-align:center;width:1920px">And that\'s when the second clock starts.</div>', 0, 860, "fade .55 .7"),
    SL, "CLOCKS DRAWN IN THE STUDIO · 1954: THE NIGHT OF 20-21 DEC (KELLY 2025) · 2025: BOX 4 UNSEALED, KELLY'S PAPER ONLINE 4 NOV 2025", dark=True))

# ==== 4 STAKES ===========================================================================================================
sheets = "".join(A(f'<div style="width:250px;height:320px;background:#FFFFFF;box-shadow:0 12px 24px rgba(0,0,0,.3);transform:rotate({r}deg);padding:24px;box-sizing:border-box">'
                   f'<div style="font:500 13px Plex;letter-spacing:2px;color:{CO}">{t}</div>' + "".join(f'<div style="height:7px;background:rgba(31,38,51,.3);margin:13px 0;width:{w}%"></div>' for w in (90, 70, 84, 60, 78, 66, 88))
                   + '</div>', x, y, f"drop {s:.2f} {s + .08:.2f}", "z-index:30") for t, x, y, r, s in
                 (("TRANSCRIPT", 1330, 560, -6, .42), ("PHONE LOG", 1530, 540, 4, .5), ("RESEARCH NOTES", 1360, 690, -3, .58), ("\"MESSAGE FROM SPACE\"", 1590, 700, 6, .66)))
put("15_box", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(4, "THE ARCHIVE")
    + A(f'<div style="font:400 72px/0.95 Anton;color:{SL}">UNSEALED {hl("2025")}</div>', 110, 130, "up .05 .15")
    + photo("bentley.jpg", 700, 620, 110, 250, "up 0 .14", -1.5, push="0 1", pos="50% 60%")
    + circ(245, 690, 95, 52, "draw .25 .36", 8, 6)
    + caption("THE BENTLEY HISTORICAL LIBRARY, ANN ARBOR (PHOTO 2010)", 130, 895, "fade .15 .25")
    + photo("archive_boxes.jpg", 420, 420, 860, 170, "drop .18 .28", 3, "z-index:20")
    + caption("A REAL ARCHIVE · NOT THE BENTLEY, NOT THE FESTINGER BOX", 830, 620, "fade .3 .38")
    + A(f'<div style="background:{PAPER};padding:10px 14px;font:500 17px/1.5 Plex;letter-spacing:2px;color:{SL};border:3px solid {SL};box-shadow:6px 6px 0 rgba(0,0,0,.25)">LEON FESTINGER PAPERS · BOX 4<br>HELD AT THE BENTLEY</div>', 1330, 200, "snap .34 .34", "z-index:40")
    + arrow(1320, 250, 720, 560, "draw .36 .48")
    + sheets + tag("PAGES: STUDIO RECONSTRUCTION · ORIGINALS AT THE BENTLEY", 950, 960, -1.5, "fade .7 .78"),
    PAPER, "BOX 4 CONTENTS (TRANSCRIPTS, TELEPHONE LOGS, RESEARCH NOTES, CHANNELLED MESSAGES): KELLY 2025 · PHOTOS: DWIGHT BURDETTE / WIKIMEDIA COMMONS, CC BY 3.0 (BENTLEY); SILLYGWAILO / FLICKR, CC BY 2.0 (TORONTO ARCHIVES) · PAGES: RECONSTRUCTIONS"))

put("16_kelly", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(4, "THE ARCHIVE")
    + card(study("THOMAS KELLY", "2025", "Journal of the History of the Behavioral Sciences", "\"Debunking 'When Prophecy Fails'\" · drawn from the unsealed papers", "ONE SCHOLAR'S READING · ATTRIBUTED"), 760, 110, 150, "up 0 .12", -1.5)
    + A(f'<div style="width:4px;height:520px;background:{SL}"></div>', 958, 470, "wipe .2 .3")
    + A(f'<div style="font:400 40px Anton;color:#5B6576;width:760px">THE BOOK SAYS</div><div style="font:400 34px/1.4 ISerif;color:{SL};margin-top:10px">· little recruiting before the failure<br>· after it: the group doubled down</div>', 140, 520, "up .25 .35")
    + A(f'<div style="font:400 40px Anton;color:{AM};width:760px">THE PAPERS SAY (KELLY)</div><div style="font:400 34px/1.4 ISerif;color:{SL};margin-top:10px">· a book planned, magazines, letters, visitors: before<br>· after it: the leader recanted, the group dissolved</div>', 1010, 520, "up .4 .52")
    + f'<svg class="a" data-anim="draw .62 .74" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{wobble(1410, 640, 420, 150, 4)}" pathLength="1" fill="none" stroke="{AM}" stroke-width="6"/></svg>'
    + photo("bentley.jpg", 380, 250, 1440, 110, "up .08 .2", 2.5, pos="40% 70%")
    + caption("WHERE THE PAPERS ARE: THE BENTLEY", 1440, 400, "fade .15 .25")
    + stamp("STORY REVERSED?", 1000, 360, "slam .85 .87", 6, 48),
    PAPER, "SOURCE: T. KELLY, 'DEBUNKING WHEN PROPHECY FAILS', JHBS 62 (2026 VOL.; ONLINE 4 NOV 2025), doi 10.1002/jhbs.70043 · KELLY'S CLAIMS, ATTRIBUTED; SEE ACT 4 FOR THE OTHER SIDE · PHOTO: DWIGHT BURDETTE / WIKIMEDIA COMMONS, CC BY 3.0"))

put("17_empty", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0)
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080"><rect x="420" y="250" width="1080" height="640" fill="none" stroke="{CO}" stroke-width="6"/></svg>'
    + "".join(A(f'<svg width="60" height="110" viewBox="-30 -40 60 110" style="display:block">{stick(0, 0, 1, SL)}</svg>', x - 30, y - 40, f"fade 0 .01", f"z-index:20") for x, y in ())
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080">' + "".join(f'<g data-anim="fade {.05 + i * .06:.2f} {.0 + .01:.2f}"></g>' for i in range(0)) + "</svg>"
    + "".join(A(f'<svg width="60" height="110" viewBox="-30 -40 60 110" style="display:block">{stick(0, 0, 1, SL)}</svg>', x - 30, y - 40, "fade 0 0", "z-index:20;opacity:1") for x, y in ())
    + chapter(4, "THE ARCHIVE")
    + A(f'<div style="font:400 60px Anton;color:{SL}">AN EMPTY ROOM</div><div style="font:400 30px ISerif;color:#3A4456">the group broke up, according to Kelly</div>', 520, 330, "fade .1 .2")
    + A(f'<div style="display:flex;gap:120px"><div>{clock(0, 0, 240)}<div style="font:400 30px Anton;color:{SL};text-align:center;margin-top:14px;width:240px">BOOK: DOUBLED DOWN</div></div>'
        f'<div>{clock(10, 10, 240)}<div style="font:400 30px Anton;color:{AM};text-align:center;margin-top:14px;width:240px">PAPERS: GAVE UP</div></div></div>', 600, 470, "up .4 .55"),
    PAPER, "KELLY 2025: THE LEADER RECANTED AND THE GROUP DISSOLVED (ATTRIBUTED) · HOUSE PLAN IS A STUDIO SKETCH"))

put("18_riecken", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + house(10, True, None, True) + chapter(4, "THE ARCHIVE")
    + card(f'<div style="font:500 15px Plex;letter-spacing:3px;color:{CO}">FROM H. RIECKEN\'S NOTES, 20-21 DEC 1954, AS QUOTED BY KELLY 2025</div>'
           f'<div style="font:400 40px/1.3 ISerif;color:{SL};margin-top:10px">"…{hl("precipitated")} what seems to have been quite a scene inside of the house."</div>', 900, 960, 120, "up .45 .6", 1.5)
    + A(f'<div style="background:{CO};color:{PAPER};font:500 18px Plex;letter-spacing:2px;padding:8px 14px;border-radius:10px">"MESSAGE FROM SPACE"?</div>', 1080, 520, "drop .3 .4", "z-index:40")
    + tag("OBSERVER EFFECT: PERSONALLY DELIVERED", 160, 940, -2, "snap .85 .85"),
    PAPER, "KELLY 2025: RIECKEN WAS TREATED AS A SPIRITUAL FIGURE AND FABRICATED MESSAGES (KELLY'S CLAIM, ATTRIBUTED); QUOTE FROM RIECKEN'S 1954 NOTES AS QUOTED BY KELLY · STICK FIGURES, NO REAL LIKENESS"))

put("19_antelope", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(4, "THE ARCHIVE")
    + f'<svg class="a" style="left:0;top:0" width="1920" height="1080">{stick(360, 640, 2.0, SL, True)}<rect x="300" y="520" width="20" height="60" fill="{SL}"/>'
      f'<g stroke="#fff" stroke-width="5"><ellipse cx="1500" cy="760" rx="170" ry="70" fill="#C8A060"/><circle cx="1330" cy="700" r="78" fill="#9A6A2E"/><circle cx="1330" cy="705" r="48" fill="#C8A060"/>'
      f'<rect x="1380" y="800" width="26" height="90" fill="#C8A060"/><rect x="1440" y="800" width="26" height="90" fill="#C8A060"/><rect x="1560" y="800" width="26" height="90" fill="#C8A060"/><rect x="1620" y="800" width="26" height="90" fill="#C8A060"/>'
      f'<path d="M1668 740 q 70 -10 60 -80" fill="none" stroke="#C8A060" stroke-width="10"/></g><text x="1470" y="660" font-family="Plex" font-size="20" fill="#5B6576" letter-spacing="3">LION (CUT-OUT)</text></svg>'
    + A(f'<svg width="240" height="200" viewBox="0 0 240 200"><g stroke="#fff" stroke-width="5"><ellipse cx="110" cy="100" rx="70" ry="32" fill="#D9B27A"/><circle cx="196" cy="70" r="22" fill="#D9B27A"/>'
        f'<path d="M190 50 q 0 -40 -16 -48 M204 50 q 8 -40 24 -46" fill="none" stroke="#3A2A1A" stroke-width="6"/><path d="M180 82 L150 96" stroke="#D9B27A" stroke-width="16"/>'
        f'<path d="M70 128 L60 190 M95 130 L92 190 M140 128 L150 190 M160 124 L176 186" stroke="#D9B27A" stroke-width="10" fill="none"/></g></svg><div style="font:500 16px Plex;letter-spacing:3px;color:#5B6576;text-align:center">ANTELOPE (CUT-OUT)</div>', 700, 330, "up .2 .5", "transform:rotate(-14deg)")
    + A(f'<div style="font:700 56px Caveat;color:{SL}">"Fascinating."</div>', 140, 360, "fade .6 .7")
    + tag("NATURE DOCUMENTARY · ETHICS SECTION: BLANK", 1100, 940, 2, "snap .85 .85")
    + tag("ILLUSTRATION", 120, 940, -1.5, "fade 0 .1", True),
    PAPER, "SIGHT GAG DRAWN IN THE STUDIO · ILLUSTRATES KELLY 2025'S CLAIM THAT THE OBSERVERS SHAPED EVENTS"))

reps = [("HARDYCK & BRADEN", "1962", "a Pentecostal group"), ("ZYGMUNT", "1970", "Jehovah's Witnesses"), ("BALCH ET AL.", "1983", "a Baha'i group")]
put("20_replications", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(4, "THE WARNINGS")
    + "".join(card(f'<div style="font:400 38px/1 Anton;color:{SL}">{n}</div><div style="font:500 18px Plex;color:{CO};margin-top:6px">{y}</div><div style="font:400 26px ISerif;color:#3A4456;margin-top:6px">{t}</div>'
                   f'<div style="display:inline-block;margin-top:12px;background:{SL};color:{PAPER};font:500 15px Plex;letter-spacing:2px;padding:4px 8px">DIDN\'T DOUBLE DOWN</div>', 420, 110 + i * 470, 150, f"up {.05 + i * .12:.2f} {.15 + i * .12:.2f}", (-1.5, 1.5, -1)[i]) for i, (n, y, t) in enumerate(reps))
    + card(study("VAIDIS ET AL.", "2024", "Advances in Methods and Practices in Psychological Science 7(1)", "the induced-compliance paradigm, run again")
           + '<div style="display:flex;gap:44px;margin-top:18px">' + "".join(f'<div><div data-anim="count {s0} {s0 + .14:.2f}" data-to="{n}" style="font:400 92px/1 Anton;color:{AM if k == 2 else SL}">{n:,}</div><div style="font:500 17px Plex;letter-spacing:3px;color:#3A4456">{t}</div></div>'
                                                                            for k, (n, t, s0) in enumerate(((39, "LABS", .5), (19, "COUNTRIES", .56), (4898, "PEOPLE", .62)))) + '</div>', 900, 520, 520, "up .45 .58", 1.2)
    + stamp("EFFECT NOT FOUND", 1180, 900, "slam .8 .82", -6, 56),
    PAPER, "FAILED-PROPHECY FOLLOW-UPS: AS REVIEWED BY KELLY 2025 · VAIDIS ET AL. 2024, AMPPS 7(1), doi 10.1177/25152459231213375: NO EFFECT OF CHOICE ON ATTITUDE (A CONSTRUCTIVE REPLICATION)"))

put("21_otherside", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(4, "THE OTHER SIDE")
    + A(f'<div style="font:400 84px/0.95 Anton;color:{SL}">BEFORE WE<br>{hl("PILE ON")}</div>', 110, 150, "up 0 .1")
    + "".join(card(f'<div style="font:400 40px/1.05 Anton;color:{SL}">{h}</div><div style="font:400 28px/1.25 ISerif;color:#3A4456;margin-top:8px">{t}</div>', 500, 700 + (i % 2) * 570, 150 + (i // 2) * 420, f"up {.15 + i * .15:.2f} {.25 + i * .15:.2f}", (-1.2, 1.2)[i % 2])
              for i, (h, t) in enumerate((("ONE SCHOLAR'S READING", "Kelly's paper is a single re-examination of the archive."), ("THEY CAN'T REPLY", "All three authors have died, so they can't answer."),
                                          ("NO REBUTTAL YET", "None found as of 19 Nov 2026. His sources are open: osf.io/4jevm"), ("DISSONANCE ISN'T DEAD", "Other studies still find people justify what they've already done."))))
    + tag("WE CHECK THE SCIENCE · INCLUDING THE DEBUNKING", 110, 420, -1.5, "snap .85 .85")
    + photo("archive_shelf.jpg", 330, 400, 150, 530, "up .05 .18", -2.5)
    + caption("ARCHIVES CAN BE RE-READ · BY ANYONE", 150, 965, "fade .2 .3"),
    PAPER, "PHOTO: DIGITAL GAME MUSEUM / FLICKR, CC BY 2.0 (ARCHIVAL BOXES, ILLUSTRATIVE) · KELLY 2025 DATA STATEMENT (OSF.IO/4JEVM) · REBUTTAL SEARCH 19 NOV 2026 · DISSONANCE IN OTHER PARADIGMS: MIXED EVIDENCE"))

# ==== 5 SYNTHESIS ========================================================================================================
spines = "".join(A(f'<div style="width:46px;height:{260 + (i * 37) % 90}px;background:{(CO, SL, "#5B6576")[i % 3]};border-radius:4px"></div>', 300 + i * 56, 640 - (260 + (i * 37) % 90), f"grow {.1 + i * .025:.2f} {.14 + i * .025:.2f}") for i, _ in enumerate(range(22)))
put("22_irony", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(5, "THE IRONY")
    + spines + A(f'<div style="width:1320px;height:6px;background:{SL}"></div>', 280, 640, "wipe 0 .1")
    + A(f'<div style="font:500 20px Plex;letter-spacing:3px;color:#5B6576">1956 ················ SEVENTY YEARS OF TEXTBOOKS ················ 2025</div>', 300, 660, "fade .05 .15")
    + A(f'<div style="font:400 110px/0.9 Anton;color:{SL};text-align:center;width:1920px">THE STUDY ABOUT DOUBLING DOWN<br><span style="color:{AM}">GOT DOUBLED DOWN ON</span></div>', 0, 760, "slam .75 .77"),
    PAPER, "BOOK SPINES DRAWN IN THE STUDIO · 'SEVENTY YEARS' = 1956-2025"))

kin = lambda word, x, y, s0, size=132, col=SL, tail="": a(f'<div style="font:400 {size}px/1 Anton;color:{col};white-space:nowrap">' + "".join(f'<span data-anim="drop {s0 + k * .035:.3f} {s0 + k * .035 + .06:.3f}" style="display:inline-block">{ch}</span>' for k, ch in enumerate(word)) + tail + '</div>', x, y, "z-index:40")
put("22b_textbooks", page(
    a(f'<div style="width:1920px;height:1080px;{GRID}"></div>', 0, 0) + chapter(5, "THE IRONY")
    + photo("books_stack.jpg", 860, 572, 90, 200, "up 0 .14", -1.5, push="0 1")
    + caption("REAL BOOKS · STAND-INS FOR SEVENTY YEARS OF TEXTBOOKS, NO TITLES SHOWN", 110, 815, "fade .1 .2")
    + A(f'<div style="font:400 64px/1 Anton;color:#5B6576">THE STUDY ABOUT<br>DOUBLING DOWN…</div>', 1080, 170, "up .08 .2", "z-index:40")
    + A(f'<div style="font:400 64px/1 Anton;color:#5B6576">…GOT</div>', 1080, 360, "fade .3 .36", "z-index:40")
    + kin("DOUBLED", 1080, 450, .38) + kin("DOWN", 1080, 600, .62, 132, AM, f' <span data-anim="slam .84 .86" style="display:inline-block;color:{SL}">ON.</span>')
    + tag("1956 → 2025: STILL IN THE SYLLABUS", 1080, 830, -1.5, "snap .9 .9"),
    PAPER, "PHOTO: WONDERLANE / FLICKR, CC BY 2.0 (STACKS OF BOOKS, SEATTLE; ILLUSTRATIVE) · 'SEVENTY YEARS' = 1956-2025 · WHEN PROPHECY FAILS STILL CITED AS THE FOUNDING CASE (KELLY 2025)"))

put("23_you", page(
    a(f'<div style="width:1920px;height:1080px;{SLATE}"></div>', 0, 0) + chapter(5, "THE VALVE IN YOUR HEAD", True)
    + f'<svg class="a" data-anim="draw 0 .3" style="left:0;top:0" width="1920" height="1080"><path d="M560 640 C 480 420 640 230 860 240 C 980 140 1200 170 1260 300 C 1420 320 1460 520 1360 620 C 1380 760 1220 820 1120 760 L 1080 880 L 960 880 L 960 760 C 820 800 600 780 560 640 Z" pathLength="1" fill="none" stroke="{CO}" stroke-width="8"/></svg>'
    + A(f'<svg width="260" height="260" viewBox="0 0 260 260"><circle cx="130" cy="130" r="100" fill="{SL}" stroke="{PAPER}" stroke-width="8"/><text x="130" y="140" text-anchor="middle" font-family="Anton" font-size="30" fill="{PAPER}">DISSONANCE</text><path d="M170 70 A 70 70 0 0 1 200 120" stroke="{AM}" stroke-width="8" fill="none"/></svg>', 830, 380, "pop .3 .4")
    + "".join(A(f'<div style="background:{PAPER};color:{SL};font:400 30px Anton;padding:10px 16px;transform:rotate({r}deg);box-shadow:0 10px 20px rgba(0,0,0,.4)">{t}</div>', x, y, f"drop {s:.2f} {s + .07:.2f}") for t, x, y, r, s in
              (("THE STOCK YOU WON'T SELL", 120, 300, -3, .45), ("THE TEAM YOU DEFEND", 1440, 260, 3, .55), ("THE PREDICTION YOU MADE AT DINNER", 1380, 760, -2, .65)))
    + A(f'<div style="background:{AM};color:{SL};font:400 44px Anton;padding:10px 22px">UPDATE ↗</div>', 1000, 640, "slam .82 .84", "z-index:40")
    + tag("METAPHOR, NOT ANATOMY", 120, 940, -1.5, "fade 0 .1", True),
    SL, "BRAIN OUTLINE AND VALVE: STUDIO METAPHOR, NOT ANATOMY · EVERYDAY EXAMPLES ARE ILLUSTRATIONS", dark=True))

put("24_end", page(
    a(f'<div style="width:1920px;height:1080px;overflow:hidden"><div data-anim="push 0 1" style="transform-origin:60% 70%"><img src="/assets/real/night_house.jpg" style="width:1920px;height:1080px;object-fit:cover;display:block"></div></div>', 0, 0)
    + a(f'<div style="width:1920px;height:1080px;background:linear-gradient(rgba(20,24,36,.55),rgba(20,24,36,.25) 50%,rgba(20,24,36,.7))"></div>', 0, 0)
    + A(clock(0, 1, 380, "", SL, True), 770, 90, "fade 0 .1", "z-index:30")
    + A(f'<svg width="120" height="50" viewBox="0 0 120 50"><ellipse cx="60" cy="30" rx="58" ry="14" fill="{AM}"/><ellipse cx="60" cy="20" rx="24" ry="14" fill="{AM}" opacity=".8"/></svg>', 180, 160, "up .4 .95", "z-index:40")
    + A(f'<div style="font:700 40px Caveat;color:{AM};transform:rotate(-4deg)">running seventy years late</div>', 150, 230, "fade .7 .8", "z-index:40")
    + A(f'<div style="font:400 50px/1.3 ISerif;color:{PAPER};text-align:center;width:1920px;text-shadow:0 2px 14px rgba(0,0,0,.8)">The aliens never came.<br>Seventy years later, <span style="color:{AM}">the truth did</span>, a little late.</div>', 0, 560, "fade .45 .65", "z-index:40")
    + caption("A REAL NIGHT SKY · NOT OAK PARK, NOT 1954", 1340, 975, "fade .1 .2", True),
    SL, "DRAGON PSYCHOLOGY · SOURCES IN THE DESCRIPTION · PHOTO: ROBIN MULLIGAN / FLICKR, CC BY 2.0 · CLOCK AND SAUCER DRAWN IN THE STUDIO", dark=True))
print("ok")
