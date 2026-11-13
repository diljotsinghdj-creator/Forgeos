"""The BJP IT cell, rewound (Print Facts, 10 min, reverse autopsy). Hand-composed shots in the 'light table' kit.

Every claim on screen carries its dossier status as a chip (VERIFIED / REPORTED / ALLEGATION / OPINION / RESPONSE).
Source pages appear under a scanner light ('scan'), always with the outlet and date. No party colours, no India
outline maps (Natural Earth does not follow India's official boundary), no ordinary account holders.
"""
import json, math
from pathlib import Path

D = Path(__file__).resolve().parent
sc = {s["id"]: s for s in json.load(open(D / "script.json"))}
NAVY, INK, TABLE, VER, REP, ALG, OPI, RES, SIG = "#0F1D2B", "#13202D", "#EDEFF1", "#1F8A70", "#2F6DB5", "#D2553C", "#7A5BBF", "#5E6B78", "#FFDD33"
HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script></head>
<body data-dur="{dur}" data-push="{push}" class="{cls}"><svg width="0" height="0" style="position:absolute"><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="31"/><feColorMatrix values="0 0 0 0 .1  0 0 0 0 .15  0 0 0 0 .2  0 0 0 .25 0"/></filter></svg><div id="cam">"""
TAIL = """</div><svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>{credit}</body></html>"""
STILL = 'data-d=".01" data-breathe="0" data-jit="0"'
DOCS = {  # name: (outlet line for the credit, crop fraction of height to keep)
    "print_malviya": ("THEPRINT, 17 AUG 2026", .62), "fb_2019": ("META NEWSROOM, 1 APR 2019", .72), "arxiv_trend": ("ARXIV / CSCW 2021 (JAKESCH, GARIMELLA, ECKLES, NAAMAN)", 1),
    "scroll_1737": ("SCROLL, 31 JAN 2025 (PTI DATA FROM THE BJP'S EXPENDITURE REPORT)", .82), "scroll_wire_retract": ("SCROLL, 23 OCT 2022", .82),
    "livelaw_fcu": ("LIVELAW, SEPT 2024", .48), "quint_kota": ("THE QUINT, 27 SEPT 2018", .7), "row_mandi": ("REST OF WORLD, 15 MAY 2024 (WITH PRINCETON'S DIGITAL WITNESS LAB)", .8),
    "quint_label": ("THE QUINT, 2 DEC 2020", .7), "print_swamy": ("THEPRINT, 7 SEPT 2020", .62), "scroll_telangana": ("SCROLL, 4 MAY 2024", .74),
    "tribune_7113": ("THE TRIBUNE, 29 JAN 2025 (ELECTION COMMISSION DATA)", .62), "quint_fb702": ("THE QUINT, 4 APR 2019", .7),
}
CHIP = {"ver": ("VERIFIED", "c-ver"), "rep": ("REPORTED", "c-rep"), "alg": ("ALLEGATION", "c-alg"), "opi": ("OPINION", "c-opi"), "res": ("RESPONSE", "c-res"), "com": ("COMPUTED", "c-com")}


def el(html, x, y, at, k="pop", style="", base="", extra=""):
    return f'<div class="el" data-in="{k}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;{style}" {extra}>{html}</div>'


def svg(body, at=0, k="pop", extra=""):
    return f'<svg class="el" data-in="{k}" data-at="{at}" style="inset:0;overflow:visible" width="1920" height="1080" {extra}>{body}</svg>'


def chip(kind, x, y, at, extra_text=""):
    t, c = CHIP[kind]
    return el(f'<div class="chip {c}">{t}{(" · " + extra_text) if extra_text else ""}</div>', x, y, at, "pop")


def g(text, x, y, size, at, col=INK, k="slide", w=None, extra=""):
    return el(f'<div class="g" style="font-size:{size}px;color:{col};{f"width:{w}px;" if w else ""}">{text}</div>', x, y, at, k, extra=extra)


def q(text, x, y, size, at, col=INK, w=1500, k="slide"):
    return el(f'<div class="q" style="font-size:{size}px;color:{col};width:{w}px">{text}</div>', x, y, at, k)


def m(text, x, y, size, at, col=INK, bg=None, k="wipe"):
    b = f"background:{bg};padding:6px 14px;" if bg else ""
    return el(f'<div class="m" style="font-size:{size}px;color:{col};{b}">{text}</div>', x, y, at, k)


def doc(name, x=110, y=150, w=1120, at=.1, rot=0, callout=None, chip_kind=None, cx=1300, cy=260, cw=520):
    """A source page revealed under the scanner light, with an optional callout quoting the key line."""
    crop = DOCS[name][1]
    w = int(w * 1.22); x = max(70, x - 60); y = max(150, y - 10)
    cx = min(cx + 120, 1920 - cw - 120); cy = cy + 120
    from PIL import Image
    iw, ih = Image.open(D / "docs" / f"{name}.png").size
    h = int(w * ih / iw * crop)
    b = el(f'<div class="doc" style="width:{w}px;height:{h}px"><img src="{(D / "docs" / (name + ".png")).as_uri()}" style="width:{w}px;display:block"></div>', x, y, at, "scan", base=f"rotate({rot}deg)", extra='data-d="1.1" data-jit="0"')
    b += el(f'<div style="width:{w + 60}px;height:6px;background:{SIG};box-shadow:0 0 30px 10px rgba(255,221,51,.55)"></div>', x - 30, y, at, "scanbar", extra=f'data-h="{h}" data-d="1.1" data-breathe="0" data-jit="0"')
    if callout:
        b += el(f'<div style="width:{cw}px;background:{NAVY};color:#fff;padding:26px 30px;box-shadow:0 18px 40px rgba(15,29,43,.35)"><div class="q" style="font-size:44px">{callout}</div></div>', cx, cy, at + 1.2, "slide", extra='data-from="r"')
    if chip_kind:
        b += chip(chip_kind, x, y - 50, at + .9)
    return b, "SOURCE PAGE: " + DOCS[name][0]


def dshot(name, **kw):
    b, cr = doc(name, **kw)
    return dict(cls="table", push=.05, credit=cr, body=b)


def card(cls, push, credit, body):
    return dict(cls=cls, push=push, credit=credit, body=body)


def counter(to, x, y, size, at, col=INK, comma=True, prefix="", suffix="", frm=0, d=1.3):
    return el(f'<div class="g" style="font-size:{size}px;color:{col}">{prefix}<span class="el" data-in="count" {"data-comma=1" if comma else ""} data-from0="{frm}" data-to="{to}" data-at="{at + .1}" data-d="{d}" style="position:static">{to:,}</span>{suffix}</div>', x, y, at, "pop")


def ribbon(year, at=0, dark=False):
    """The rewind ribbon: 2007..2026 along the top, a marker on the current year."""
    col = "#9FB0C1" if dark else "#8A97A4"
    b = "".join(f'<text x="{140 + (y - 2007) * 86}" y="70" font-family="DMono" font-size="18" fill="{SIG if y == year else col}" text-anchor="middle">{y}</text>' for y in range(2007, 2027))
    b += f'<path d="M110 84 H1790" stroke="{col}" stroke-width="2"/><circle cx="{140 + (year - 2007) * 86}" cy="84" r="9" fill="{SIG}" stroke="{NAVY}" stroke-width="3"/>'
    return svg(b, at, "pop", STILL)


def bubbles(n, x0, y0, cols, size, gap, col, at0=.2, step=.006):
    b = ""
    for i in range(n):
        x, y = x0 + (i % cols) * gap, y0 + (i // cols) * gap
        b += f'<path class="el" data-in="pop" data-at="{at0 + i * step:.3f}" data-d=".15" d="M{x} {y} h{size} v{size * .7:.1f} h{-size * .55:.1f} l{-size * .25:.1f} {size * .25:.1f} v{-size * .25:.1f} h{-size * .2:.1f} Z" fill="{col}"/>'
    return svg(b, 0, "pop", 'data-breathe="0" data-jit="0"')


def dots(n, x0, y0, cols, r, gap, col, at0=.2, step=.003):
    return svg("".join(f'<circle class="el" data-in="pop" data-at="{at0 + i * step:.3f}" data-d=".12" cx="{x0 + (i % cols) * gap}" cy="{y0 + (i // cols) * gap}" r="{r}" fill="{col}"/>' for i in range(n)), 0, "pop", 'data-breathe="0" data-jit="0"')


def versus(left_kind, left_title, left_body, right_kind, right_title, right_body, at2=1.2):
    b = ""
    for i, (kd, tt, bd, at) in enumerate(((left_kind, left_title, left_body, .1), (right_kind, right_title, right_body, at2))):
        x = 110 + i * 870
        t, c = CHIP[kd]
        border = {"alg": ALG, "res": INK, "opi": OPI, "rep": REP, "ver": VER}[kd]
        b += el(f'<div style="width:780px;height:640px;background:#fff;border-top:14px solid {border};box-shadow:0 20px 44px rgba(15,29,43,.2);padding:40px 44px;box-sizing:border-box">'
                f'<div class="chip {c}" style="display:inline-block">{t}</div><div class="g" style="font-size:52px;margin-top:30px;letter-spacing:-1px">{tt}</div>'
                f'<div class="s" style="font-size:40px;margin-top:26px;color:#33424F">{bd}</div></div>', x, 230, at, "slide", extra='data-from="b"')
    return b


def bars(items, x0=200, y0=300, maxw=1300, h=110, gap=170, at0=.3, unit=""):
    vmax = max(v for _, v, _ in items)
    b = ""
    for i, (lab, v, col) in enumerate(items):
        y = y0 + i * gap
        b += m(lab, x0, y - 44, 28, at0 + i * .3)
        b += el(f'<div style="width:{max(8, int(v / vmax * maxw))}px;height:{h}px;background:{col}"></div>', x0, y, at0 + i * .3, "wipe", extra='data-d=".9"')
        b += el(f'<div class="g" style="font-size:64px;color:{INK}">{unit}{v:,}{"%" if isinstance(v, float) or v < 100 else ""}</div>', x0 + max(8, int(v / vmax * maxw)) + 30, y + 14, at0 + i * .3 + .7, "pop")
    return b


def tiles(states, hi, at0=.2):
    """State name tiles instead of an outline map (no boundary is drawn)."""
    b = ""
    for i, s in enumerate(states):
        on = s in hi
        b += el(f'<div style="width:300px;height:96px;background:{SIG if on else "#fff"};border:2px solid {INK if on else "#C9D1D9"};display:flex;align-items:center;justify-content:center" class="m"><span style="font-size:26px">{s}</span></div>',
                1180 + (i % 2) * 330, 200 + (i // 2) * 120, at0 + i * .08, "pop")
    return b


# ======================= shots =======================
B = {}
# cold open: the handover
B["B01"] = card("night", .06, "", g("17", 140, 260, 380, .05, "#fff", "drop") + g("August", 600, 330, 170, .35, "#fff") + g("2026", 610, 520, 170, .6, SIG)
                + m("the BJP's IT cell gets a new head", 620, 760, 30, 1.0, "#9FB0C1"))
B["B02"] = dshot("print_malviya", chip_kind="ver", callout="Mhaskey in, Malviya out, after 11 years", cx=1260, cy=640, cw=560)
B["B03"] = card("table", .04, "SOURCE: OUTLOOK, AUG 2026", g("Deepak Mhaskey", 140, 220, 112, .1) + chip("rep", 145, 150, .3, "OUTLOOK")
                + m("former chemistry professor", 145, 430, 36, .6) + m("Chhattisgarh", 145, 500, 36, .9) + m("party IT work there since 2009", 145, 570, 36, 1.2)
                + tiles(["Bihar", "Karnataka", "Uttar Pradesh", "Rajasthan", "Himachal Pradesh", "Chhattisgarh"], ["Chhattisgarh"], .8))
B["B04"] = card("table", .04, "SOURCE: THEPRINT; OUTLOOK", g("Amit Malviya", 140, 260, 130, .1) + m("national head of the IT cell", 145, 440, 36, .5)
                + el(f'<div class="g" style="font-size:300px;color:{INK}"><span class="el" data-in="count" data-from0="0" data-to="11" data-at=".6" data-d="1.0" style="position:static">11</span></div>', 1150, 280, .5, "pop")
                + m("years · 2015 to 2026", 1170, 600, 34, 1.3) + chip("ver", 145, 190, .4))
B["B05"] = card("night", .05, "", g("Reason given:", 140, 330, 120, .1, "#fff") + el(f'<div class="g" style="font-size:220px;color:{SIG}">none.</div>', 140, 470, .8, "pop"))
B["B06a"] = dshot("print_malviya", chip_kind="rep", x=140, y=200, w=1000, callout="insiders: Gen Z protests exposed gaps in social media outreach", cx=1220, cy=320, cw=600)
B["B06b"] = card("table", .04, "SOURCE: THEPRINT, 17 AUG 2026 (PARTY INSIDERS, NOT AN OFFICIAL REASON)", chip("rep", 140, 240, .1, "THEPRINT, CITING INSIDERS")
                 + q("“Gen Z protests that exposed gaps in its social media outreach”", 140, 320, 96, .3, INK, 1600))
B["B07"] = card("night", .05, "", g("What changed hands?", 140, 400, 150, .1, "#fff", w=1700))
B["B08"] = card("night", .05, "", ribbon(2026, 0, True) + el(f'<div class="g" style="font-size:360px;color:#fff"><span class="el" data-in="count" data-from0="2026" data-to="2007" data-at=".3" data-d="2.4" style="position:static">2007</span></div>', 400, 280, .1, "pop")
                + m("rewind · 19 years", 420, 700, 40, .6, SIG) + svg("".join(f'<path class="el" data-in="wipe" data-at="{.3 + i * .15:.2f}" d="M120 {200 + i * 120} H1800" stroke="rgba(255,255,255,.08)" stroke-width="40"/>' for i in range(7)), 0, "pop", STILL))
# act 1: birth
B["B09"] = card("table", .05, "SOURCES: THE QUINT; HUFFPOST INDIA (2018); WIKIPEDIA: BJP IT CELL", ribbon(2007) + g("2007", 140, 220, 260, .1) + m("BJP IT cell set up", 150, 500, 40, .6) + m("party president: Rajnath Singh", 150, 570, 36, .9) + chip("ver", 150, 650, 1.1))
B["B10"] = card("table", .04, "SOURCE: THE QUINT; HUFFPOST INDIA", ribbon(2007) + m("first head", 140, 300, 40, .1) + g("Prodyut Bora", 140, 360, 170, .3))
B["B11"] = card("table", .04, "SOURCE: ONE PUBLISHED ACCOUNT (DOSSIER C02); DATE NOT INDEPENDENTLY CONFIRMED", ribbon(2010) + g("~2010", 140, 220, 200, .1) + g("Arvind Gupta", 140, 460, 130, .4) + chip("rep", 145, 640, .8, "ONE ACCOUNT"))
B["B12a"] = card("table", .04, "SOURCES: DOSSIER C03", ribbon(2015) + g("2015", 140, 220, 260, .1) + m("party president: Amit Shah", 150, 500, 36, .5))
B["B12b"] = card("table", .04, "SOURCES: DOSSIER C03", ribbon(2015) + m("national head, IT cell", 140, 300, 40, .1) + g("Amit Malviya", 140, 360, 170, .3) + chip("ver", 145, 600, .7))
B["B13"] = card("table", .04, "", ribbon(2018) + g("Prodyut Bora", 140, 320, 120, .1) + el(f'<div class="m" style="font-size:44px;color:{ALG}">later left the BJP</div>', 145, 480, .6, "wipe"))
B["B14a"] = card("night", .05, "SOURCES: THE QUINT; HUFFPOST INDIA, 22 JUNE 2018", chip("opi", 140, 200, .1, "PRODYUT BORA, 2018") + q("“a Frankenstein's monster”", 140, 300, 170, .3, "#fff", 1700))
B["B14b"] = card("night", .05, "SOURCES: THE QUINT; HUFFPOST INDIA, 22 JUNE 2018", chip("opi", 140, 200, .1, "PRODYUT BORA, 2018") + q("“the rot started with Team Modi”", 140, 300, 140, .3, "#fff", 1700))
B["B15"] = card("table", .04, "", chip("opi", 140, 260, .1) + g("= one man's view,", 140, 340, 110, .3) + g("after he left.", 140, 480, 110, .8, RES) + m("now: the scale →", 145, 720, 40, 1.6))
# act 2: the machine
B["B16a"] = card("table", .05, "", ribbon(2018) + g("Kota, Rajasthan", 140, 250, 130, .1) + m("22 September 2018", 150, 420, 40, .5) + m("Amit Shah, then BJP president · to social media volunteers", 150, 490, 30, .9))
B["B16b"] = dshot("quint_kota", chip_kind="rep", x=120, y=170, w=1160, callout="The Quint, 27 Sept 2018", cx=1340, cy=640, cw=460)
B["B17"] = card("table", .04, "AS REPORTED: TWO GROUPS, ABOUT 15 LAKH AND 17 LAKH MEMBERS · ONE BUBBLE = 50,000 MEMBERS", bubbles(64, 160, 300, 8, 54, 80, REP) + chip("rep", 160, 220, .1)
                + el(f'<div class="g" style="font-size:180px">32 lakh</div>', 900, 340, .9, "pop") + m("WhatsApp group members, Uttar Pradesh", 910, 560, 30, 1.2))
B["B18a"] = card("night", .05, "SOURCE: THE QUINT, 27 SEPT 2018 (REPORTED QUOTE, TRANSLATED)", chip("rep", 140, 200, .1, "AMIT SHAH, AS QUOTED BY THE QUINT") + q("“We can spread any message we want…”", 140, 300, 120, .3, "#fff", 1640))
B["B18b"] = card("night", .06, "SOURCE: THE QUINT, 27 SEPT 2018 (REPORTED QUOTE, TRANSLATED)", chip("rep", 140, 200, .1, "AMIT SHAH, AS QUOTED BY THE QUINT") + q('“…whether it is <span class="hl" data-in="sweep" data-at=".7" data-d=".8">true or false</span>.”', 140, 300, 140, .2, "#fff", 1640))
B["B19"] = card("table", .04, "SOURCE: THE QUINT; THE WIRE; BLOOMBERG (SEPT 2018)", chip("rep", 140, 200, .1) + g("His example:", 140, 280, 90, .2) + m("a story about Akhilesh Yadav", 145, 420, 40, .6)
                 + el(f'<div class="m" style="font-size:40px;color:#fff;background:{ALG};padding:8px 16px">“untrue”, by his own account</div>', 145, 500, 1.0, "wipe")
                 + el(f'<div class="m" style="font-size:40px;color:{INK};background:{SIG};padding:8px 16px">went viral anyway, he said</div>', 145, 580, 1.5, "wipe"))
B["B20a"] = versus("rep", "Kota, Sept 2018", "Reports differ on whether he added a caveat, and how strong it was.", "rep", "Delhi, months earlier", "He reportedly told volunteers not to post fake news: it could hurt the party's credibility.")
B["B20b"] = card("table", .04, "SOURCES: THE QUINT; BLOOMBERG; THE WIRE; TIMES OF INDIA VIA BLOOMBERG", ribbon(2018) + g("Both are on the record.", 140, 400, 120, .1, w=1700))
B["B21"] = card("night", .05, "", g("The scale,", 140, 340, 150, .1, "#fff") + g("in the party's own numbers.", 140, 520, 110, .6, SIG, w=1700))
B["B22a"] = card("table", .04, "SOURCES: DOSSIER C08 (THREE REPORTS)", ribbon(2019) + g("2019", 140, 200, 200, .1) + m("one “cell phone pramukh” per polling booth", 150, 440, 36, .5) + chip("rep", 150, 520, .9))
B["B22b"] = card("table", .04, "AS REPORTED, ABOUT 900,000 VOLUNTEERS · ONE DOT = 1,000", dots(900, 140, 210, 36, 5, 30, REP, .1, .0018) + counter(900000, 1300, 420, 120, .6, INK) + m("planned volunteers", 1310, 580, 30, 1.0))
B["B23a"] = card("table", .04, "SOURCE: THEPRINT, 2020 (PARTY LEADERS)", ribbon(2020) + tiles(["Bihar", "Karnataka", "Uttar Pradesh", "Rajasthan", "Himachal Pradesh", "Chhattisgarh"], ["Bihar"]) + g("Bihar, 2020", 140, 220, 120, .1) + chip("rep", 145, 380, .5, "THEPRINT"))
B["B23b"] = card("table", .04, "SOURCE: THEPRINT, 2020; THE BIHAR CONVENOR TOLD CARAVAN OVER 1 LAKH GROUPS", counter(9500, 140, 240, 170, .1) + m("IT cell heads", 150, 430, 34, .5) + counter(72000, 140, 560, 170, .8) + m("planned WhatsApp groups", 150, 750, 34, 1.2) + chip("rep", 150, 160, .2))
B["B24a"] = card("table", .04, "SOURCE: THE WASHINGTON POST, 2023", ribbon(2023) + tiles(["Bihar", "Karnataka", "Uttar Pradesh", "Rajasthan", "Himachal Pradesh", "Chhattisgarh"], ["Karnataka"]) + g("Karnataka, 2023", 140, 220, 110, .1) + chip("rep", 145, 360, .5, "WASHINGTON POST"))
B["B24b"] = card("table", .04, "SOURCE: THE WASHINGTON POST, 2023 (A FORMER STATE SOCIAL MEDIA HEAD) · PULITZER FINALIST SERIES", counter(150000, 140, 300, 200, .1) + m("workers on WhatsApp", 150, 520, 36, .7) + chip("rep", 150, 220, .2))
B["B25a"] = dshot("row_mandi", chip_kind="rep", x=140, y=170, w=1040, callout="400+ BJP-run WhatsApp groups, one hill town", cx=1260, cy=420, cw=560)
B["B25b"] = card("table", .04, "SOURCE: REST OF WORLD / DIGITAL WITNESS LAB, 2024", tiles(["Bihar", "Karnataka", "Uttar Pradesh", "Rajasthan", "Himachal Pradesh", "Chhattisgarh"], ["Himachal Pradesh"]) + g("Mandi", 140, 240, 180, .1) + m("Himachal Pradesh · 2024", 150, 460, 36, .5))
B["B26"] = card("table", .03, "TOWN: CENSUS 2011, ~26,000 · GROUPS: REST OF WORLD 2024 · ONE DOT = 100 PEOPLE · ONE BUBBLE = 1 GROUP (FIRST 400)", dots(260, 140, 240, 20, 8, 30, "#9FB0C1", .1, .004) + bubbles(400, 900, 240, 25, 22, 34, REP, .6, .003)
                + m("26,000 people", 140, 180, 30, .1) + m("400+ groups", 900, 180, 30, .6, REP))
B["B27"] = card("table", .04, "SOURCE: META (ESTIMATE)", chip("rep", 140, 260, .1, "META'S ESTIMATE") + g("~500 million", 140, 340, 200, .3) + m("WhatsApp users in India", 150, 560, 38, .8))
B["B28a"] = card("table", .04, "SOURCES: DOSSIER C13", ribbon(2018) + g("July 2018", 140, 220, 160, .1) + m("after lynchings linked to rumours", 150, 420, 36, .5) + chip("ver", 150, 500, .8))
B["B28b"] = card("table", .04, "SOURCE: WHATSAPP (2018)", m("forward limit in India", 140, 220, 36, .1) + "".join(el(f'<div style="width:220px;height:300px;background:{"#fff" if i < 5 else "#D9DFE5"};border:3px solid {INK if i < 5 else "#C9D1D9"};"></div>', 140 + i * 250, 330, .2 + i * .15, "pop") for i in range(7))
                 + svg(f'<path d="M1395 300 L1590 660 M1590 300 L1395 660" stroke="{ALG}" stroke-width="14"/><path d="M1645 300 L1840 660 M1840 300 L1645 660" stroke="{ALG}" stroke-width="14"/>', 1.4, "draw") + g("5", 560, 700, 200, 1.6, SIG))
B["B29a"] = card("table", .04, "SOURCE: NEWSLAUNDRY (DOSSIER C44)", chip("rep", 140, 200, .1, "NEWSLAUNDRY") + g("Who makes it?", 140, 280, 130, .2) + m("Uttar Pradesh unit alone", 150, 450, 36, .6))
B["B29b"] = card("table", .03, "SOURCE: NEWSLAUNDRY · ONE FIGURE = ONE PERSON", svg("".join(f'<g class="el" data-in="pop" data-at="{.1 + i * .03:.2f}" data-d=".15"><circle cx="{180 + (i % 15) * 70}" cy="{300 + (i // 15) * 150}" r="18" fill="{INK if i < 25 else RES}"/><rect x="{163 + (i % 15) * 70}" y="{322 + (i // 15) * 150}" width="34" height="56" rx="12" fill="{INK if i < 25 else RES}"/></g>' for i in range(45)), 0, "pop", 'data-breathe="0"')
                 + m("25 core team", 180, 220, 30, .4) + m("+ ~20 designers, technicians, cartoonists", 180, 760, 30, 1.3, RES))
B["B30"] = card("night", .05, "SOURCE: DOSSIER C43", g("Total size?", 140, 300, 150, .1, "#fff") + el(f'<div class="m" style="font-size:44px;color:{SIG}">never independently measured</div>', 150, 520, .7, "wipe"))
# act 3: money
B["B31"] = card("night", .05, "", g("The money.", 140, 330, 180, .1, "#fff") + m("the paper trail is the party's own", 150, 560, 40, .7, SIG))
B["B32a"] = dshot("scroll_1737", chip_kind="ver", x=140, y=170, w=1040, callout="from the BJP's own expenditure report to the Election Commission", cx=1260, cy=360, cw=560)
B["B32b"] = card("table", .04, "SOURCE: BJP EXPENDITURE REPORT TO THE ELECTION COMMISSION, VIA PTI / SCROLL", counter(1737, 140, 280, 260, .1, prefix="₹") + m("crore · 2024 Lok Sabha election · declared by the BJP", 150, 560, 32, .8) + chip("ver", 150, 200, .2))
waterfall = [("total declared", 1737.68, INK), ("media advertising", 611.50, REP), ("Google India", 156.95, REP), ("Facebook", 24.63, REP)]
B["B33"] = card("table", .03, "SOURCE: BJP EXPENDITURE REPORT (₹ CRORE)", "".join(
    el(f'<div style="width:{int(v / 1737.68 * 1400)}px;height:90px;background:{c}"></div>', 200, 260 + i * 160, .2 + i * .25, "wipe", extra='data-d=".7"')
    + m(f"{lab} · ₹{v:,.2f} cr", 200, 220 + i * 160, 28, .2 + i * .25) for i, (lab, v, c) in enumerate(waterfall[:2])))
B["B34"] = card("table", .03, "SOURCE: BJP EXPENDITURE REPORT (₹ CRORE)", "".join(
    el(f'<div style="width:{max(10, int(v / 1737.68 * 1400))}px;height:90px;background:{c if i < 2 else SIG}"></div>', 200, 260 + i * 160, 0 if i < 2 else .2 + (i - 2) * .4, "pop" if i < 2 else "wipe", extra=STILL if i < 2 else 'data-d=".7"')
    + m(f"{lab} · ₹{v:,.2f} cr", 200, 220 + i * 160, 28, 0 if i < 2 else .2 + (i - 2) * .4) for i, (lab, v, c) in enumerate(waterfall)))
B["B35"] = card("table", .04, "SOURCE: GOOGLE ADS TRANSPARENCY DATA AS REPORTED (DOSSIER C30), 1 JAN-31 MAY 2024", chip("rep", 140, 200, .1)
                + svg("".join(f'<rect class="el" data-in="pop" data-at="{.2 + i * .01:.2f}" data-d=".12" x="{160 + (i % 20) * 60}" y="{300 + (i // 20) * 60}" width="50" height="50" fill="{REP if i < 90 else "#C9D1D9"}"/>' for i in range(200)), 0, "pop", 'data-breathe="0"')
                + m("200,000+ Google ads", 1420, 320, 30, .4) + el(f'<div class="m" style="font-size:30px;color:#fff;background:{REP};padding:6px 14px">~180,000 by the BJP</div>', 1420, 380, 1.4, "wipe"))
B["B36"] = dshot("tribune_7113", chip_kind="rep", x=140, y=170, w=1040, callout="Election Commission data on party funds", cx=1260, cy=420, cw=560)
B["B37"] = card("table", .03, "SOURCE: ELECTION COMMISSION DATA, AS REPORTED BY THE TRIBUNE (₹ CRORE, FUND BALANCE)", bars([("BJP", 7113, INK), ("Congress", 857, RES)], 200, 360, 1250, 140, 280, .2, "₹"))
# act 4: the questions
B["B38"] = card("table", .04, "", g("Scale ≠ wrongdoing.", 140, 320, 150, .1) + m("every party campaigns · every party wants reach", 150, 520, 34, .8, RES))
B["B39"] = card("night", .05, "", g("What travels through it?", 140, 400, 140, .1, "#fff", w=1700))
B["B40"] = card("table", .04, "SOURCES: THE QUINT; THEPRINT (DEC 2020)", ribbon(2020) + g("December 2020", 140, 220, 140, .1) + m("farmers' protests", 150, 400, 36, .5) + m("Amit Malviya posts a clip: a policeman, an elderly farmer", 150, 470, 30, .9))
B["B41"] = dshot("quint_label", chip_kind="ver", x=140, y=170, w=1040, callout="“manipulated media”: reported as Twitter's first such label in India", cx=1260, cy=360, cw=560)
B["B42"] = card("table", .04, "SOURCE: FACT-CHECKS BY ALT NEWS, BOOM, THE QUINT (DEC 2020) · ILLUSTRATION OF THE TRIM, NOT THE FOOTAGE",
                el('<div style="width:1500px;height:120px;background:#C9D1D9"></div>', 200, 420, .1, "wipe") + el(f'<div style="width:420px;height:120px;background:{INK}"></div>', 1100, 420, .7, "wipe")
                + m("the longer video", 200, 370, 28, .2) + m("the clip posted", 1100, 570, 28, .9) + chip("rep", 200, 240, .3, "FACT-CHECKERS") + m("batons swinging, earlier in the video →", 200, 580, 26, 1.4, ALG))
B["B43"] = card("table", .04, "SOURCE: TWITTER SPOKESPERSON, AS REPORTED", chip("res", 140, 300, .1, "TWITTER") + g("“declined to give details”", 140, 380, 110, .3, w=1700))
B["B44a"] = card("table", .04, "SOURCE: DOSSIER C20 (MAY 2021)", ribbon(2021) + g("May 2021", 140, 220, 150, .1) + m("same label · BJP spokesperson Sambit Patra", 150, 420, 34, .5) + chip("ver", 150, 500, .8))
B["B44b"] = card("table", .04, "", m("Sambit Patra", 140, 330, 40, .1) + el(f'<div class="g" style="font-size:90px;color:{RES}">spokesperson ≠ IT cell</div>', 140, 400, .4, "pop") + m("same party", 145, 560, 40, 1.0, ALG))
B["B45"] = card("night", .05, "", g("The trend machine.", 140, 400, 160, .1, "#fff", w=1700))
B["B46"] = dshot("arxiv_trend", chip_kind="rep", x=120, y=180, w=1100, callout="600+ public pro-BJP WhatsApp groups, 2019", cx=1290, cy=600, cw=520)
B["B47"] = card("table", .04, "SOURCE: JAKESCH ET AL., CSCW 2021", chip("rep", 140, 200, .1, "PEER-REVIEWED")
                + svg("".join(f'<path class="el" data-in="draw" data-at="{.2 + i * .025:.3f}" data-d=".3" d="M{160 + (i % 12) * 100} {330 + (i // 12) * 100} l36 -46 l36 46" stroke="{REP}" stroke-width="10" fill="none"/>' for i in range(75)), 0, "pop", 'data-breathe="0"')
                + g("75", 1360, 300, 260, 1.4, INK) + m("coordinated", 1370, 580, 30, 1.6) + m("hashtag campaigns", 1370, 630, 30, 1.8))
B["B48a"] = card("night", .05, "SOURCE: JAKESCH ET AL., CSCW 2021", chip("rep", 140, 200, .1, "THE RESEARCHERS") + g("organiser:", 140, 300, 100, .2, "#9FB0C1") + q("“most likely” the party's social media arm", 140, 420, 110, .5, "#fff", 1640))
B["B48b"] = card("night", .05, "SOURCE: JAKESCH ET AL., CSCW 2021", el(f'<div class="m" style="font-size:60px;color:{SIG}">not confirmed</div>', 140, 420, .1, "pop") + m("whatsapp's anonymity hid who ran it", 150, 540, 34, .6, "#9FB0C1"))
B["B49"] = versus("rep", "Smaller than reported", "The campaigns were smaller than media reports and claims had suggested.", "rep", "No sign of pay", "The authors found no evidence that participants were paid.", .9)
B["B50a"] = card("table", .04, "SOURCE: DECODE (BOOM), 2024 · ALLEGATION", ribbon(2024) + chip("alg", 140, 200, .1, "DECODE, 2024") + g("Paid reels?", 140, 280, 150, .2) + m("a consultancy working for the BJP", 150, 480, 34, .6) + m("young influencers · unlabelled", 150, 550, 34, 1.0))
B["B50b"] = versus("alg", "Decode's report", "A consultancy working for the BJP paid influencers for reels on proxy pages, without labelling them as paid.", "res", "The BJP's answer", "Declined to say what it pays, and pointed to rival parties doing the same.", 1.0)
B["B51"] = card("table", .04, "SOURCE: DECODE (BOOM), 2024", chip("res", 140, 300, .1, "BJP") + g("“other parties do it too”", 140, 380, 110, .3, w=1700) + m("paraphrase of the party's reply", 150, 560, 28, .9, RES))
B["B52"] = card("night", .05, "", g("The sharpest words", 140, 330, 140, .1, "#fff") + g("came from inside.", 140, 490, 140, .6, SIG))
B["B53a"] = dshot("print_swamy", chip_kind="opi", x=140, y=170, w=1040, callout="BJP MP Subramanian Swamy, 7 Sept 2020", cx=1260, cy=420, cw=520)
B["B53b"] = card("night", .05, "SOURCE: SUBRAMANIAN SWAMY ON TWITTER, 7 SEPT 2020 (REPORTED BY THEPRINT, THE QUINT)", chip("opi", 140, 200, .1, "SUBRAMANIAN SWAMY, BJP MP") + q('“The BJP IT cell has <span class="hl" data-in="sweep" data-at=".9" data-d=".7">gone rogue</span>.”', 140, 300, 150, .3, "#fff", 1640))
B["B54"] = card("table", .04, "SOURCE: THEPRINT; THE QUINT (SEPT 2020)", chip("opi", 140, 200, .1) + m("“fake ID tweets”, he said", 150, 300, 40, .3) + g("Remove Malviya", 140, 380, 130, .7) + m("his demand", 150, 540, 34, 1.1))
B["B55"] = card("night", .05, "SOURCE: REPUBLIC WORLD; THE WEEK (SEPT 2020)", g("The party kept", 140, 330, 140, .1, "#fff") + g("Malviya.", 140, 490, 180, .6, SIG) + chip("ver", 145, 720, 1.0))
B["B56a"] = card("table", .04, "SOURCE: THE WALL STREET JOURNAL, AUG 2020", ribbon(2020) + chip("rep", 140, 200, .1, "WALL STREET JOURNAL") + g("Platforms too.", 140, 280, 150, .2))
B["B56b"] = card("table", .04, "SOURCE: THE WALL STREET JOURNAL, AUG 2020", m("Facebook's top policy executive in India", 150, 300, 34, .1) + g("opposed applying", 140, 370, 110, .4) + g("hate-speech rules", 140, 480, 110, .7, ALG) + m("to a BJP politician, the WSJ reported", 150, 620, 34, 1.1))
B["B57"] = versus("rep", "The report", "Her view, the WSJ said, cited the company's business interests in India.", "res", "Facebook's answer", "Her view was not the only factor. It later banned the politician.", .9)
B["B58"] = card("table", .04, "SOURCE: SWATI CHATURVEDI, 'I AM A TROLL' (2016) · ALLEGATION", ribbon(2016) + chip("alg", 140, 200, .1, "SWATI CHATURVEDI, 2016")
                + el(f'<div style="width:440px;height:620px;background:{INK};box-shadow:16px 20px 0 rgba(15,29,43,.25);padding:50px 36px;box-sizing:border-box"><div class="g" style="font-size:70px;color:#fff">I Am a Troll</div><div class="m" style="font-size:22px;color:{SIG};margin-top:30px">2016</div></div>', 1300, 220, .3, "drop", base="rotate(3deg)")
                + g("a “hit list”", 140, 300, 130, .6) + m("of journalists, a former volunteer told her", 150, 460, 30, 1.0))
B["B59"] = card("table", .04, "SOURCE: ARVIND GUPTA, THEN BJP IT HEAD, AS REPORTED", chip("res", 140, 260, .1, "BJP IT HEAD, 2016") + g("“never part of the cell”", 140, 340, 110, .3, w=1700) + g("“false”", 140, 500, 140, 1.0, ALG))
# act 5: the other side
B["B60"] = card("night", .05, "", g("The other side.", 140, 330, 170, .1, "#fff") + m("this is not a one-party story", 150, 560, 40, .7, SIG))
B["B61a"] = dshot("fb_2019", chip_kind="ver", x=140, y=170, w=1000, callout="687 pages and accounts linked to the Congress IT cell", cx=1230, cy=380, cw=580)
B["B61b"] = card("table", .04, "SOURCE: META NEWSROOM, 1 APR 2019 · 'COORDINATED INAUTHENTIC BEHAVIOUR'", counter(687, 140, 280, 260, .1) + m("pages and accounts · Congress IT cell", 150, 560, 34, .7) + chip("ver", 150, 200, .2))
B["B62"] = card("table", .04, "SOURCES: META NEWSROOM; THE QUINT (SILVER TOUCH RAN THE PRO-BJP PAGE 'THE INDIA EYE', AS REPORTED)", counter(15, 140, 280, 260, .1) + m("pages, groups and accounts · IT firm Silver Touch", 150, 560, 34, .7) + chip("rep", 150, 200, .2))
B["B63"] = card("table", .03, "SOURCE: OXFORD INTERNET INSTITUTE, 2019 ELECTION STUDY · SHARE OF NEWS LINKS CLASSED AS 'JUNK NEWS'", bars([("pro-BJP Facebook pages", 28, INK), ("pro-Congress Facebook pages", 21, RES)], 200, 360, 1100, 140, 280, .2) + chip("rep", 200, 200, .1, "OXFORD"))
B["B64"] = dshot("scroll_telangana", chip_kind="ver", x=140, y=170, w=1040, callout="arrests over a doctored video of Amit Shah", cx=1260, cy=380, cw=560)
B["B65"] = card("table", .04, "SOURCE: MALLIKARJUN KHARGE, CONGRESS PRESIDENT (MAY 2024), AS REPORTED", chip("res", 140, 260, .1, "CONGRESS PRESIDENT") + g("“the BJP is the expert", 140, 340, 110, .3) + g("in fake videos”", 140, 460, 110, .7, ALG) + m("paraphrase of his response", 150, 620, 28, 1.1, RES))
B["B66"] = card("night", .05, "", g("And one story", 140, 330, 150, .1, "#fff") + g("collapsed.", 140, 500, 190, .6, ALG))
B["B67"] = card("table", .04, "SOURCE: THE WIRE (JAN 2022), RETRACTED · SHOWN ONLY AS A RETRACTED STORY", ribbon(2022) + g("“Tek Fog”", 140, 260, 200, .1) + m("The Wire, January 2022 · an app said to hijack trends", 150, 500, 32, .6))
B["B68"] = dshot("scroll_wire_retract", chip_kind="ver", x=140, y=170, w=1040, callout="taken down; The Wire said it was deceived", cx=1260, cy=380, cw=560)
B["B69a"] = card("table", .04, "SOURCE: THE NEWS MINUTE (OCT 2022)", chip("res", 140, 260, .1, "AMIT MALVIYA") + g("said he would sue", 140, 340, 130, .3))
B["B69b"] = card("night", .05, "", el(f'<div class="g" style="font-size:160px;color:#fff;text-decoration:line-through;text-decoration-color:{ALG};text-decoration-thickness:14px">Tek Fog</div>', 140, 300, .1, "pop") + m("not evidence · not used in this film", 150, 520, 40, .7, SIG))
B["B70a"] = card("table", .04, "SOURCES: DOSSIER C36 (ASIAN AGE; PTI; THEPRINT)", chip("res", 140, 200, .1, "THE BJP'S CASE") + g("organised political communication", 140, 280, 110, .3, w=1700))
B["B70b"] = card("table", .04, "SOURCES: DOSSIER C36", chip("res", 140, 200, .1, "THE BJP'S CASE") + g("by volunteers.", 140, 280, 150, .1) + g("the kind every party runs.", 140, 450, 110, .7, RES, w=1700))
B["B71"] = versus("res", "Abuse?", "The party has denied directing abuse.", "res", "Following = endorsing?", "No, it says. A leader following an account is not an endorsement.", 1.0)
# ending
B["B72"] = card("night", .05, "", g("Who checks", 140, 330, 180, .1, "#fff") + g("any of this?", 140, 520, 180, .6, SIG))
B["B73"] = card("table", .04, "SOURCES: IT RULES AMENDMENT 2023; LIVELAW", ribbon(2023) + g("2023", 140, 220, 200, .1) + m("the government's own fact-check unit", 150, 440, 36, .5) + m("could flag content about its business as false", 150, 510, 32, .9) + chip("ver", 150, 590, 1.2))
B["B74a"] = dshot("livelaw_fcu", chip_kind="ver", x=140, y=200, w=1100, callout="struck down as unconstitutional", cx=1300, cy=520, cw=500)
B["B74b"] = card("night", .05, "SOURCE: BOMBAY HIGH COURT, KUNAL KAMRA V. UNION OF INDIA (SEPT 2024)", ribbon(2024, 0, True) + el(f'<div class="g" style="font-size:150px;color:#fff;text-decoration:line-through;text-decoration-color:{SIG};text-decoration-thickness:12px">fact-check unit</div>', 140, 360, .2, "pop") + m("Bombay High Court · September 2024", 150, 580, 36, .9, SIG))
B["B75"] = card("table", .04, "", "".join(el(f'<div class="g" style="font-size:96px;color:{c}">{t}</div>', 140, 160 + i * 150, .1 + i * .35, "slide") for i, (t, c) in enumerate((("platforms", INK), ("fact-checkers", INK), ("courts", INK), ("rival parties", INK), ("everyone checks someone.", REP)))))
B["B76"] = card("night", .05, "", ribbon(2026, 0, True) + el(f'<div class="g" style="font-size:300px;color:#fff"><span class="el" data-in="count" data-from0="2007" data-to="2026" data-at=".1" data-d="1.4" style="position:static">2026</span></div>', 140, 300, .1, "pop") + m("back to 17 August", 150, 700, 40, .8, SIG))
B["B77"] = card("table", .04, "", el(f'<div class="g" style="font-size:110px;text-decoration:line-through;text-decoration-color:{ALG};text-decoration-thickness:10px;color:{RES}">Amit Malviya</div>', 140, 160, .1, "pop")
                + g("Deepak Mhaskey", 140, 300, 110, .5) + m("still there: the groups · the volunteers · the budget", 150, 520, 34, 1.2)
                + bubbles(60, 160, 640, 30, 30, 52, REP, 1.3, .01))
B["B78"] = card("night", .06, "", g("It didn't change hands.", 140, 300, 130, .1, "#fff", w=1700) + g("It changed drivers.", 140, 480, 150, 1.4, SIG, w=1700) + m("our reading", 150, 720, 28, 2.0, "#9FB0C1"))
B["B79a"] = card("night", .05, "", g("Not who runs it.", 140, 380, 150, .1, "#9FB0C1", w=1700))
B["B79b"] = card("table", .05, "", g('Who <span class="hl" data-in="sweep" data-at=".6" data-d=".8">checks</span> what it sends.', 140, 380, 150, .1, INK, w=1700))

B["B29ca"] = card("table", .04, "SOURCE: NEWSLAUNDRY (DOSSIER C44)", chip("rep", 140, 200, .1, "NEWSLAUNDRY") + g("“Toolkits”", 140, 280, 180, .2) + m("leaked lists for supporters", 150, 500, 36, .7))
toolkit = "".join(el(f'<div style="width:1100px;height:84px;background:#fff;border-left:10px solid {REP};display:flex;align-items:center;padding-left:24px;box-sizing:border-box;box-shadow:0 6px 16px rgba(15,29,43,.1)"><span class="m" style="font-size:26px">{t} · #hashtag · ready-made post</span></div>', 140 + (i % 2) * 40, 200 + i * 110, .1 + i * .3, "slide") for i, t in enumerate(("09:00", "11:00", "13:00", "16:00", "19:00", "21:00")))
B["B29cb"] = card("table", .03, "ILLUSTRATION OF THE FORMAT DESCRIBED BY NEWSLAUNDRY (NOT A REAL TOOLKIT)", toolkit + m("set times", 1400, 300, 40, 1.6, REP))
B["B30ba"] = card("table", .04, "SOURCE: MALVIYA, AS REPORTED (DOSSIER C43)", chip("rep", 140, 200, .1, "THE PARTY'S OWN CLAIM") + counter(12, 140, 280, 300, .2, comma=False, suffix=" lakh") + m("social media volunteers", 150, 620, 36, .9))
B["B30bb"] = card("night", .05, "SOURCE: DOSSIER C43", g("a claim,", 140, 330, 170, .1, "#fff") + g("not a measurement.", 140, 520, 150, .7, SIG, w=1700))
B["B34ba"] = dshot("tribune_7113", chip_kind="rep", x=140, y=170, w=1040, callout="audited accounts, 2023-24", cx=1260, cy=420, cw=520)
B["B34bb"] = card("table", .04, "SOURCE: BJP AUDITED ACCOUNTS 2023-24, VIA ADR AND THE TRIBUNE", counter(1754, 140, 280, 260, .1, prefix="₹") + m("crore · election and general propaganda · 2023-24", 150, 560, 32, .8) + chip("rep", 150, 200, .2, "AUDITED ACCOUNTS"))
B["B63ba"] = card("table", .04, "SOURCE: OXFORD INTERNET INSTITUTE, 2019", chip("rep", 140, 200, .1, "OXFORD · WHATSAPP") + g("On WhatsApp", 140, 280, 150, .2) + m("visual content classed as divisive or conspiratorial", 150, 480, 32, .7))
B["B63bb"] = card("table", .03, "SOURCE: OXFORD INTERNET INSTITUTE, 2019 ELECTION STUDY (WHATSAPP VISUAL CONTENT)", bars([("BJP", 34.5, INK), ("Congress", 28.5, RES)], 200, 360, 1100, 140, 280, .2))
VCRED = {"B20a": "SOURCES: THE QUINT; BLOOMBERG; THE WIRE; TIMES OF INDIA VIA BLOOMBERG", "B49": "SOURCE: JAKESCH ET AL., CSCW 2021", "B50b": "SOURCE: DECODE (BOOM), 2024",
         "B57": "SOURCE: THE WALL STREET JOURNAL, AUG 2020; FACEBOOK'S RESPONSE AS REPORTED", "B71": "SOURCES: DOSSIER C36 (ASIAN AGE; PTI)"}
for _k, _cr in VCRED.items():
    if isinstance(B[_k], str):
        B[_k] = card("table", .03, _cr, B[_k])
CH = {"K1": ("the handover", "17 August 2026"), "K2": ("chapter one", "Birth"), "K3": ("chapter two", "The machine"), "K4": ("chapter three", "The money"),
      "K5": ("chapter four", "The questions"), "K6": ("chapter five", "The other side"), "K7": ("chapter six", "Who checks?")}
for k, (a, b) in CH.items():
    B[k] = card("night", .05, "", m(a, 140, 380, 32, .1, "#9FB0C1") + g(b, 130, 430, 210, .3, "#fff", w=1700))
B["T0"] = card("night", .04, "PRINT FACTS · EVERY CLAIM CARRIES ITS STATUS", g("The Machine", 140, 300, 230, .1, "#fff") + m("the BJP IT cell, rewound", 150, 560, 44, .7, SIG)
               + "".join(chip(k, 150 + i * 260, 680, 1.2 + i * .15) for i, k in enumerate(("ver", "rep", "alg", "opi", "res"))))

PLAN = [("B01", ["B01"]), ("B02", ["B02"]), ("B03", ["B03"]), ("B04", ["B04"]), ("B05", ["B05"]), ("B06", ["B06a", "B06b"]), ("B07", ["B07"]), ("B08", ["B08"]), ("T0", ["T0"]),
        ("K2", ["K2"]), ("B09", ["B09"]), ("B10", ["B10"]), ("B11", ["B11"]), ("B12", ["B12a", "B12b"]), ("B13", ["B13"]), ("B14", ["B14a", "B14b"]), ("B15", ["B15"]),
        ("K3", ["K3"]), ("B16", ["B16a", "B16b"]), ("B17", ["B17"]), ("B18", ["B18a", "B18b"]), ("B19", ["B19"]), ("B20", ["B20a", "B20b"]), ("B21", ["B21"]),
        ("B22", ["B22a", "B22b"]), ("B23", ["B23a", "B23b"]), ("B24", ["B24a", "B24b"]), ("B25", ["B25a", "B25b"]), ("B26", ["B26"]), ("B27", ["B27"]),
        ("B28", ["B28a", "B28b"]), ("B29", ["B29a", "B29b"]), ("B29c", ["B29ca", "B29cb"]), ("B30", ["B30"]), ("B30b", ["B30ba", "B30bb"]),
        ("K4", ["K4"]), ("B31", ["B31"]), ("B32", ["B32a", "B32b"]), ("B33", ["B33"]), ("B34", ["B34"]), ("B34b", ["B34ba", "B34bb"]), ("B35", ["B35"]), ("B36", ["B36"]), ("B37", ["B37"]),
        ("K5", ["K5"]), ("B38", ["B38"]), ("B39", ["B39"]), ("B40", ["B40"]), ("B41", ["B41"]), ("B42", ["B42"]), ("B43", ["B43"]), ("B44", ["B44a", "B44b"]),
        ("B45", ["B45"]), ("B46", ["B46"]), ("B47", ["B47"]), ("B48", ["B48a", "B48b"]), ("B49", ["B49"]), ("B50", ["B50a", "B50b"]), ("B51", ["B51"]),
        ("B52", ["B52"]), ("B53", ["B53a", "B53b"]), ("B54", ["B54"]), ("B55", ["B55"]), ("B56", ["B56a", "B56b"]), ("B57", ["B57"]), ("B58", ["B58"]), ("B59", ["B59"]),
        ("K6", ["K6"]), ("B60", ["B60"]), ("B61", ["B61a", "B61b"]), ("B62", ["B62"]), ("B63", ["B63"]), ("B63b", ["B63ba", "B63bb"]), ("B64", ["B64"]), ("B65", ["B65"]), ("B66", ["B66"]),
        ("B67", ["B67"]), ("B68", ["B68"]), ("B69", ["B69a", "B69b"]), ("B70", ["B70a", "B70b"]), ("B71", ["B71"]),
        ("K7", ["K7"]), ("B72", ["B72"]), ("B73", ["B73"]), ("B74", ["B74a", "B74b"]), ("B75", ["B75"]), ("B76", ["B76"]), ("B77", ["B77"]), ("B78", ["B78"]), ("B79", ["B79a", "B79b"])]
PAUSE = {"B05": .7, "B07": .5, "B08": .8, "B15": .4, "B30": .5, "B37": .5, "B55": .6, "B66": .4, "B69": .5, "B78": .8, "B79": 2.6}
GAP = .65
import re
FOCUS = [(1.32, 18, 38), (1.28, 70, 45), (1.36, 30, 60)]
def reframe(b, n):
    """A closer framing of the same shot, everything settled: a real cut to the detail."""
    z, ox, oy = FOCUS[n % len(FOCUS)]
    body = re.sub(r'data-at="[-\d.]+"', 'data-at="-5"', b["body"])
    return card(b["cls"], b["push"] * .6, b["credit"], f'<div class="el" data-in="pop" data-at="0" data-d=".01" data-breathe="0" data-jit="0" data-base="scale({z})" style="inset:0;transform-origin:{ox}% {oy}%">{body}</div>')
timeline, t = [], 0.0
for line, shots in PLAN:
    total = (3.2 if line in ("T0",) else 2.8) if line[0] in "KT" else sc[line]["sec"] + GAP + PAUSE.get(line, 0)
    base = [round(total / len(shots), 3)] * len(shots)
    seq = []
    for sid, d in zip(shots, base):
        k = max(1, math.ceil(d / 4.4)) if d > 5.4 else 1
        for j in range(k):
            name = sid if j == 0 else f"{sid}_r{j}"
            if j:
                B[name] = reframe(B[sid], j + len(seq))
            seq.append((name, round(d / k, 3)))
    for i, (sid, d) in enumerate(seq):
        timeline.append({"shot": sid, "start": round(t, 3), "dur": d, "line": line if (i == 0 and line[0] == "B") else None})
        t += round(d * 24) / 24
for s in timeline:
    b = B[s["shot"]]
    (D / "shots" / f"{s['shot']}.html").write_text(HEAD.format(dur=s["dur"], push=b["push"], cls=b["cls"]) + b["body"]
                                                    + TAIL.format(credit=f'<div class="credit">{b["credit"]}</div>' if b["credit"] else ""), encoding="utf-8")
json.dump({"shots": timeline, "total": round(t, 2)}, open(D / "timeline.json", "w"), indent=1)
ds = [s["dur"] for s in timeline]
print(len(timeline), "shots", round(t, 1), "s  max", max(ds), "mean", round(sum(ds) / len(ds), 2), "over5.5:", [(s["shot"], s["dur"]) for s in timeline if s["dur"] > 5.5])
