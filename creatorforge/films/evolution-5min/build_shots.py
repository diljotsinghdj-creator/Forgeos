"""Human evolution, 5 min (Dragon Psychology, owner's pick: 'the bush, not the ladder').

Hand-composed shots in the 'museum' kit. Elements enter via data-in/data-at (kit.js). The recurring device is the
bush chart: a log-time chart of hominin branches that grows through the film. The march-of-progress figures are our
own pictograms (the 1965 Zallinger illustration is not reproduced).
"""
import json, math
from pathlib import Path

D = Path(__file__).resolve().parent
AS = D / "assets"
W = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
LAND = [c["r"] for c in W["countries"]]
sc = {s["id"]: s for s in json.load(open(D / "script.json"))}
CRED = json.load(open(AS / "credits.json")) if (AS / "credits.json").exists() else {}
BONE, CARD, COAL, INK, MOSS, OCHRE, OXIDE, SIG = "#EAE2CF", "#F4EEE1", "#1E1D1A", "#2A2620", "#6E8F3E", "#C4882C", "#A4442A", "#FFDD33"


def img(name):
    for e in (".jpg", ".png"):
        if (AS / (name + e)).exists():
            return (AS / (name + e)).as_uri()
    return ""


def credit(name):
    c = CRED.get(name)
    if not c:
        return {"darwin_1837": "CHARLES DARWIN, NOTEBOOK B, 1837 (PUBLIC DOMAIN), VIA WIKIMEDIA COMMONS"}.get(name, "")
    who = c.get("artist") or "unknown"
    return f"PHOTO: {who} · {c.get('license')} · WIKIMEDIA COMMONS"


HEAD = """<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script></head>
<body data-dur="{dur}" data-push="{push}" class="{cls}"><svg width="0" height="0" style="position:absolute">
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" seed="21"/><feColorMatrix values="0 0 0 0 .25  0 0 0 0 .22  0 0 0 0 .18  0 0 0 .32 0"/></filter></svg><div id="cam">"""
TAIL = """</div><svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>{credit}</body></html>"""


def el(html, x, y, at, k="pop", style="", base="", extra=""):
    return f'<div class="el" data-in="{k}" data-at="{at}" data-base="{base}" style="left:{x}px;top:{y}px;{style}" {extra}>{html}</div>'


def svg(body, at=0, k="pop", extra=""):
    return f'<svg class="el" data-in="{k}" data-at="{at}" style="inset:0;overflow:visible" width="1920" height="1080" {extra}>{body}</svg>'


STILL = 'data-d=".01" data-breathe="0" data-jit="0"'


def photo(name, x, y, w, at=.1, rot=0, h=None, pos="center", k="drop", label=None, lab_at=None, bg=CARD):
    hh = f"height:{h}px;object-fit:cover;object-position:{pos};" if h else ""
    out = el(f'<div class="card" style="background:{bg}"><img src="{img(name)}" style="width:{w}px;{hh}display:block"></div>', x, y, at, k, base=f"rotate({rot}deg)")
    if label:
        out += el(f'<div class="label" style="font-size:22px;line-height:1.45">{label}</div>', x + 30, y + (h or w) + 10, lab_at or at + .6, "wipe", base=f"rotate({rot * .5}deg)")
    return out


def big(text, x, y, size, at, col=INK, k="slide", cls="disp", extra="", w=None):
    ww = f"width:{w}px;" if w else ""
    return el(f'<div class="{cls}" style="font-size:{size}px;color:{col};{ww}">{text}</div>', x, y, at, k, extra=extra)


def hand(text, x, y, size, at, col=OXIDE, rot=-4):
    return el(f'<div class="hand" style="font-size:{size}px;color:{col};transform:rotate({rot}deg)">{text}</div>', x, y, at, "wipe")


def tag(text, x, y, size, at, col=INK, bgc=None):
    b = f"background:{bgc};padding:4px 14px;" if bgc else ""
    return el(f'<div class="tag" style="font-size:{size}px;color:{col};{b}">{text}</div>', x, y, at, "wipe")


# ---------------- maps (equirectangular window over Natural Earth land) ----------------
def map_svg(lon0, lon1, lat0, lat1, x, y, w, fill="#3A3833", stroke="#55524A"):
    h = w * (lat1 - lat0) / (lon1 - lon0)
    def P(lon, lat):
        return x + (lon - lon0) / (lon1 - lon0) * w, y + (lat1 - lat) / (lat1 - lat0) * h
    d = ""
    for rings in LAND:
        for r in rings:
            if not any(lon0 - 30 < a < lon1 + 30 and lat0 - 30 < b < lat1 + 30 for a, b in r):
                continue
            d += "M" + " L".join(f"{P(a, b)[0]:.0f} {P(a, b)[1]:.0f}" for a, b in r) + "Z"
    return f'<clipPath id="mclip"><rect x="{x}" y="{y}" width="{w}" height="{h:.0f}"/></clipPath><path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" clip-path="url(#mclip)"/>', P


def pin(P, lon, lat, label, at, col=SIG, sub=""):
    px, py = P(lon, lat)
    s = svg(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="16" fill="{col}" stroke="{COAL}" stroke-width="5"/><circle cx="{px:.0f}" cy="{py:.0f}" r="36" fill="none" stroke="{col}" stroke-width="3"/>', at)
    s += el(f'<div class="tag" style="font-size:28px;color:{BONE}">{label}</div>' + (f'<div class="hand" style="font-size:40px;color:{SIG}">{sub}</div>' if sub else ""), px + 48, py - 22, at + .2, "wipe")
    return s


def mapshot(lon0, lon1, lat0, lat1, pins, title=None, x=None, w=None, push=.06):
    w = w or 1500
    h = w * (lat1 - lat0) / (lon1 - lon0)
    if h > 960:
        w = w * 960 / h
        h = 960
    x = x if x is not None else (1920 - w) / 2
    y = (1080 - h) / 2
    land, P = map_svg(lon0, lon1, lat0, lat1, x, y, w)
    body = svg(land, 0, "pop", STILL)
    for p in pins:
        body += pin(P, *p)
    if title:
        body += big(title, 80, 70, 84, .1, BONE)
    return dict(cls="coal", push=push, credit="MAP: NATURAL EARTH (PUBLIC DOMAIN) · LOCATIONS APPROXIMATE", body=body)


# ---------------- the bush chart (log time) ----------------
SP = {  # name: (oldest Ma, youngest Ma, x, parent, label)
    "sahel": (7.0, 6.0, 960, None, "Sahelanthropus"),
    "ardi": (5.8, 4.4, 900, "sahel", "Ardipithecus"),
    "afar": (3.85, 2.95, 960, "ardi", "Au. afarensis (Lucy)"),
    "boisei": (2.3, 1.2, 1260, "afar", "P. boisei"),
    "habilis": (2.4, 1.4, 820, "afar", "H. habilis"),
    "erectus": (1.89, .108, 640, "habilis", "H. erectus"),
    "naledi": (.335, .236, 1520, "erectus", "H. naledi"),
    "neander": (.43, .04, 1120, "erectus", "Neanderthals"),
    "deni": (.3, .05, 1340, "neander", "Denisovans"),
    "flores": (.19, .05, 340, "erectus", "H. floresiensis"),
    "luzon": (.067, .05, 560, "erectus", "H. luzonensis"),
    "sapiens": (.315, 0, 960, "erectus", "H. sapiens"),
}


def Y(ma):
    yrs = max(ma * 1e6, 1.2e4)
    return 990 - (7 - math.log10(yrs)) / (7 - math.log10(1.2e4)) * 860 if ma > 0 else 92


def bush(show, new=(), hi=(), ended=(), line_at=None, dim=False, at0=.2, labels=True, extra=""):
    """show: species drawn settled; new: species that draw on in this shot; hi: highlighted (yellow); ended: X marks."""
    b = ""
    ax = "".join(f'<line x1="150" x2="1770" y1="{Y(m):.0f}" y2="{Y(m):.0f}" stroke="#3A3833" stroke-width="2"/>'
                 f'<text x="140" y="{Y(m) + 8:.0f}" font-family="Plex" font-size="22" fill="#8C8577" text-anchor="end">{t}</text>'
                 for m, t in ((7, "7 Ma"), (3, "3 Ma"), (1, "1 Ma"), (.3, "300 ka"), (.1, "100 ka"), (.04, "40 ka")))
    ax += f'<text x="140" y="{Y(0) + 8:.0f}" font-family="Plex" font-size="22" fill="{SIG}" text-anchor="end">today</text>'
    b += svg(ax, 0, "pop", STILL)
    allk = list(show) + list(new)
    for i, k in enumerate(allk):
        o, yng, x, par, lab = SP[k]
        col = SIG if k in hi else (MOSS if not dim else "#4A5A33")
        dash = ' stroke-dasharray="4 14"' if k == "luzon" else ""
        conn = ""
        if par and par in allk:
            px = SP[par][2]
            y0 = Y(o)
            conn = f'<path d="M{px} {y0 + 60:.0f} C {px} {y0:.0f}, {x} {y0 + 40:.0f}, {x} {y0:.0f}" fill="none" stroke="{col}" stroke-width="5" stroke-dasharray="6 10" opacity=".7"/>'
        seg = f'<path d="M{x} {Y(o):.0f} L{x} {Y(yng):.0f}" stroke="{col}" stroke-width="18" stroke-linecap="round"/>'
        if k == "luzon":
            seg = f'<path d="M{x} {Y(.2):.0f} L{x} {Y(o):.0f}" stroke="{col}" stroke-width="10" stroke-linecap="round"{dash}/>' + seg
        if k in new:
            at = at0 + list(new).index(k) * .35
            b += f'<svg class="el" data-in="draw" data-at="{at:.2f}" data-d=".9" data-breathe="0" data-jit="0" style="inset:0" width="1920" height="1080">{conn}{seg}</svg>'
            la = at + .5
        else:
            b += svg(conn + seg, 0, "pop", STILL)
            la = 0
        if labels:
            lx = x - 322 if k == "flores" else x + 22
            al = "text-align:right;width:300px;" if k == "flores" else ""
            b += el(f'<div class="sp" style="font-size:26px;{al}color:{SIG if k in hi else BONE}">{lab}</div>', lx, Y(yng) - 18, la, "wipe", extra=STILL if not la else "")
        if k in ended:
            ex, ey = x, Y(yng) - 6
            b += svg(f'<path d="M{ex - 20} {ey - 20:.0f} L{ex + 20} {ey + 20:.0f} M{ex + 20} {ey - 20:.0f} L{ex - 20} {ey + 20:.0f}" stroke="{OXIDE}" stroke-width="8" stroke-linecap="round"/>', at0 + .4 + list(ended).index(k) * .3, "pop")
    if line_at is not None:
        yy = Y(line_at)
        b += f'<svg class="el" data-in="draw" data-at="{at0 + .6:.2f}" data-d=".8" style="inset:0" width="1920" height="1080"><path d="M160 {yy:.0f} H1780" stroke="{SIG}" stroke-width="5" stroke-dasharray="18 10"/></svg>'
    return b + extra


BUSHCRED = "ILLUSTRATIVE · LOG TIME SCALE · DATE RANGES APPROXIMATE (SMITHSONIAN HUMAN ORIGINS; PAPERS IN DOSSIER) · RELATIONSHIPS UNCERTAIN (DASHED)"


# ---------------- pictogram figures (our own drawing) ----------------
def figure(x, lean, col=BONE, ground=900):
    a = math.radians(lean)
    hip = (x, ground - 190)
    sh = (hip[0] + 230 * math.sin(a), hip[1] - 230 * math.cos(a))
    hd = (sh[0] + 62 * math.sin(a + .25), sh[1] - 62 * math.cos(a + .25))
    if lean > 40:
        hand1, hand2 = (sh[0] + 40, ground), (sh[0] - 10, ground)
    else:
        hand1 = (sh[0] + 170 * math.sin(a * .6) + 18, sh[1] + 170 * math.cos(a * .6))
        hand2 = (sh[0] + 170 * math.sin(a * .6) - 22, sh[1] + 170 * math.cos(a * .6))
    knee = 25 * (lean / 70)
    st = f'stroke="{col}" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    return (f'<path d="M{hip[0]} {hip[1]} L{hip[0] + 30 + knee} {hip[1] + 95} L{hip[0] + 34} {ground}" {st} stroke-width="30"/>'
            f'<path d="M{hip[0]} {hip[1]} L{hip[0] - 20 + knee} {hip[1] + 95} L{hip[0] - 40} {ground}" {st} stroke-width="30"/>'
            f'<path d="M{hip[0]} {hip[1]} L{sh[0]:.0f} {sh[1]:.0f}" {st} stroke-width="56"/>'
            f'<path d="M{sh[0]:.0f} {sh[1]:.0f} L{hand1[0]:.0f} {hand1[1]:.0f}" {st} stroke-width="24"/>'
            f'<path d="M{sh[0]:.0f} {sh[1]:.0f} L{hand2[0]:.0f} {hand2[1]:.0f}" {st} stroke-width="24"/>'
            f'<circle cx="{hd[0]:.0f}" cy="{hd[1]:.0f}" r="40" fill="{col}"/>')


def march(at0=.2, step=.35, col=BONE, scale=1.0, x0=260, gap=340):
    return "".join(f'<g class="el" data-in="slide" data-from="l" data-at="{at0 + i * step:.2f}"><g transform="translate({x0 + i * gap},0)">{figure(0, lean, col)}</g></g>'
                   for i, lean in enumerate((68, 50, 32, 14, 0)))


def ladder(x, y, h, rungs=7, col=BONE, w=200):
    s = f'<path d="M{x} {y} V{y + h} M{x + w} {y} V{y + h}" stroke="{col}" stroke-width="14" stroke-linecap="round"/>'
    s += "".join(f'<path d="M{x} {y + 30 + i * (h - 60) / (rungs - 1):.0f} H{x + w}" stroke="{col}" stroke-width="10" stroke-linecap="round"/>' for i in range(rungs))
    return s


def brains(items, at0=.2, y=560, x0=260, gapx=480, unit=1350, rmax=230):
    """items: (label, cc text, cc value, colour). Circle AREA proportional to volume."""
    b = ""
    for i, (lab, cct, cc, col) in enumerate(items):
        r = rmax * math.sqrt(cc / unit)
        cx = x0 + i * gapx
        b += svg(f'<circle cx="{cx}" cy="{y}" r="{r:.0f}" fill="{col}" opacity=".9"/>', at0 + i * .35, "pop")
        b += el(f'<div class="tag" style="font-size:28px;text-align:center;width:420px;color:{BONE}">{lab}</div><div class="dispb" style="font-size:52px;text-align:center;width:420px;color:{BONE}">{cct}</div>', cx - 210, y + rmax + 40, at0 + i * .35 + .3, "wipe")
    return b


def dna_strip(n_on, total=100, col=SIG, at0=.3, y=470):
    b = ""
    for i in range(total):
        c = col if i < n_on else "#4A463E"
        b += f'<rect class="el" data-in="pop" data-at="{at0 + i * .012:.3f}" data-d=".12" x="{160 + i * 16}" y="{y}" width="12" height="140" fill="{c}"/>'
    return svg(b, 0, "pop", STILL)


# ======================= the shots =======================
B = {}   # builder per shot id -> dict(cls, push, credit, body)

# --- hook: the picture
B["L01a"] = dict(cls="coal", push=.05, credit="ILLUSTRATION OF THE POPULAR 'MARCH OF PROGRESS' IDEA (OUR OWN DRAWING)",
                 body=svg(march(), 0, "pop", STILL) + svg(f'<path d="M140 905 H1780" stroke="#4A463E" stroke-width="6"/>', 0, "pop", STILL))
B["L01b"] = dict(cls="coal", push=.08, credit="ILLUSTRATION (OUR OWN DRAWING)",
                 body=svg(march(0, 0, BONE), 0, "pop", STILL).replace('data-at="0.00"', 'data-at="0" data-d=".01"')
                 + f'<svg class="el" data-in="draw" data-at=".2" data-d="1.2" style="inset:0" width="1920" height="1080"><path d="M200 300 C 700 260, 1200 240, 1700 200" stroke="{SIG}" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M1660 170 L1715 198 L1668 238" stroke="{SIG}" stroke-width="12" fill="none" stroke-linecap="round"/></svg>'
                 + hand("progress?", 1300, 90, 90, 1.0, SIG))
copies = "".join(el(f'<div style="width:330px;height:200px;background:{["#2E2C28", "#C4882C", "#6E8F3E", "#A4442A", "#EAE2CF", "#2E2C28", "#FFDD33", "#6E8F3E", "#C4882C"][i]};overflow:hidden;box-shadow:0 10px 24px rgba(0,0,0,.5)">'
                    f'<svg width="330" height="200" viewBox="140 380 1700 560"><g>{march(0, 0, "#1E1D1A" if i in (4, 6) else BONE).replace(chr(100)+'ata-at="0.00"', chr(100)+'ata-at="0" data-d=".01"')}</g></svg></div>',
                    170 + (i % 3) * 560, 110 + (i // 3) * 300, .1 + i * .18, "drop", base=f"rotate({[-4, 3, -2, 5, -3, 2, -5, 4, -1][i]}deg)") for i in range(9))
B["L02"] = dict(cls="coal", push=.04, credit="ILLUSTRATION: THE SAME IDEA, COPIED (OUR OWN DRAWINGS, NOT REAL PRODUCTS)",
                body=copies.replace('data-at="0"', 'data-at="0" data-d=".01"'))
B["L03"] = dict(cls="coal", push=.06, credit="ILLUSTRATION (OUR OWN DRAWING)",
                body=svg(march(0, 0, "#6B665C"), 0, "pop", STILL).replace('data-at="0.00"', 'data-at="0" data-d=".01"')
                + f'<svg class="el" data-in="draw" data-at=".5" data-d=".5" style="inset:0" width="1920" height="1080"><path d="M300 250 L1650 950 M1650 250 L300 950" stroke="{OXIDE}" stroke-width="40" stroke-linecap="round"/></svg>'
                + el('<div class="stamp" style="font-size:140px;background:rgba(30,29,26,.85)">Wrong</div>', 700, 400, 1.1, "pop", base="rotate(-8deg)"))
B["L04"] = dict(cls="paper", push=.04, credit="",
                body=big("The idea is older<br>than the picture.", 120, 300, 140, .1)
                + el('<div class="disp" style="font-size:220px;color:#A4442A"><span class="el" data-in="count" data-from0="1965" data-to="1874" data-at=".9" data-d="1.4" style="position:static">1874</span></div>', 1300, 620, .8, "pop"))
# --- Haeckel
HCRED = "ERNST HAECKEL, 'PEDIGREE OF MAN', THE EVOLUTION OF MAN, 1874 (PUBLIC DOMAIN), VIA WIKIMEDIA COMMONS"
B["L05a"] = dict(cls="coal", push=.05, credit=HCRED,
                 body=photo("haeckel_1874", 1000, 40, 520, .1, -2, h=900, pos="center top")
                 + tag("Ernst Haeckel · 1874", 120, 120, 34, .8, BONE) + hand("the human story, as a tree", 110, 190, 64, 1.3, SIG))
B["L05b"] = dict(cls="coal", push=.1, credit=HCRED,
                 body=photo("haeckel_1874", 260, 60, 1400, 0, 0, h=900, pos="center 85%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"')
                 + tag("Pedigree of Man", 300, 980, 34, .6, BONE, "#1E1D1A"))
B["L06"] = dict(cls="coal", push=.06, credit=HCRED,
                body=photo("haeckel_1874", 560, 40, 800, 0, 1, h=960, pos="center 70%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"')
                + hand("roots: simple life", 80, 860, 64, .4, SIG) + el('<div class="hand" style="font-size:64px;color:#FFDD33;background:rgba(30,29,26,.9);padding:0 20px">trunk: fish, apes</div>', 1380, 380, 1.4, "wipe")
                + svg(f'<path d="M520 880 L640 820" stroke="{SIG}" stroke-width="8"/><path d="M1410 420 L1300 470" stroke="{SIG}" stroke-width="8"/>', 1.0, "draw"))
B["L07"] = dict(cls="coal", push=.12, credit=HCRED,
                body=photo("haeckel_1874", 360, 30, 1200, 0, 0, h=1000, pos="center 2%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"')
                + svg(f'<ellipse cx="960" cy="200" rx="260" ry="120" fill="none" stroke="{SIG}" stroke-width="12"/>', .8, "draw")
                + el('<div class="hand" style="font-size:80px;color:#FFDD33;background:rgba(30,29,26,.9);padding:0 24px">Man, at the top</div>', 1200, 330, 1.4, "wipe"))
# --- title
B["L08"] = dict(cls="paper", push=.04, credit="",
                body=svg(ladder(240, 200, 620, col="#9A917F"), .1, "pop")
                + f'<svg class="el" data-in="draw" data-at=".9" data-d=".5" style="inset:0" width="1920" height="1080"><path d="M190 180 L500 860" stroke="{OXIDE}" stroke-width="26" stroke-linecap="round"/></svg>'
                + f'<svg class="el" data-in="draw" data-at="1.4" data-d="1.4" style="inset:0" width="1920" height="1080"><g transform="translate(0,130)"><path d="M1460 900 C1460 700 1460 600 1460 560 M1460 700 C1400 640 1330 600 1300 470 M1460 640 C1540 580 1600 520 1620 400 M1300 560 C1260 520 1230 480 1220 420 M1460 560 C1440 460 1480 380 1470 300 M1620 480 C1680 450 1700 400 1720 360" stroke="{MOSS}" stroke-width="22" fill="none" stroke-linecap="round"/></g></svg>'
                + big("The bush,", 600, 110, 150, .4) + big("not the ladder.", 600, 270, 150, .8, OXIDE))
# --- Darwin
DCRED = "CHARLES DARWIN, NOTEBOOK B, 1837, P. 36 (PUBLIC DOMAIN; CAMBRIDGE UNIVERSITY LIBRARY), VIA WIKIMEDIA COMMONS"
B["L09a"] = dict(cls="coal", push=.05, credit=DCRED,
                 body=photo("darwin_1837", 680, 20, 560, .1, -2, h=910, pos="center top")
                 + tag("Charles Darwin · 1837", 1330, 300, 34, .8, BONE) + hand("a private notebook", 1330, 360, 64, 1.2, SIG))
B["L09b"] = dict(cls="coal", push=.1, credit=DCRED,
                 body=photo("darwin_1837", 360, 40, 1200, 0, 0, h=960, pos="center 22%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"'))
B["L10"] = dict(cls="coal", push=.12, credit=DCRED,
                body=photo("darwin_1837", 260, 60, 1400, 0, 0, h=900, pos="left 3%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"')
                + svg(f'<ellipse cx="560" cy="250" rx="330" ry="150" fill="none" stroke="{SIG}" stroke-width="12"/>', .6, "draw")
                + big('<span class="hl" data-in="sweep" data-at="1.4" data-d=".8">"I think"</span>', 1100, 200, 150, 1.0, INK, cls="disp", k="pop"))
twig = ""
for i, (x1, y1, x2, y2, end) in enumerate([(960, 1000, 960, 760, 0), (960, 760, 700, 560, 1), (960, 760, 1200, 600, 0), (700, 560, 560, 380, 1), (700, 560, 780, 340, 1),
                                         (1200, 600, 1100, 400, 1), (1200, 600, 1380, 420, 0), (1380, 420, 1320, 220, 1), (1380, 420, 1520, 250, 1), (1100, 400, 1040, 230, 1), (1380, 420, 1450, 150, 2)]):
    twig += f'<svg class="el" data-in="draw" data-at="{.1 + i * .22:.2f}" data-d=".5" style="inset:0" width="1920" height="1080"><path d="M{x1} {y1} Q {(x1 + x2) / 2 + 30} {(y1 + y2) / 2} {x2} {y2}" stroke="{INK}" stroke-width="12" fill="none" stroke-linecap="round"/></svg>'
    if end == 1:
        twig += svg(f'<path d="M{x2 - 16} {y2 - 16} L{x2 + 16} {y2 + 16} M{x2 + 16} {y2 - 16} L{x2 - 16} {y2 + 16}" stroke="{OXIDE}" stroke-width="7" stroke-linecap="round"/>', .5 + i * .22, "pop")
    if end == 2:
        twig += svg(f'<circle cx="{x2}" cy="{y2}" r="22" fill="{MOSS}"/>', .6 + i * .22, "pop")
B["L11"] = dict(cls="paper", push=.04, credit="ILLUSTRATION AFTER DARWIN'S SKETCH (OUR OWN DRAWING)",
                body=twig + hand("most branches end", 120, 260, 80, 1.6))
B["L12"] = dict(cls="paper", push=.04, credit="",
                body=big("No top.", 140, 180, 150, .1) + big("No finish line.", 140, 380, 150, 1.0) + big("Just what's still growing.", 140, 600, 120, 2.0, MOSS))
# --- chapter 2
B["K2"] = dict(cls="coal", push=.05, credit="",
               body=tag("Chapter one", 140, 300, 34, .1, "#8C8577") + el('<div class="disp" style="font-size:200px;color:#EAE2CF"><span class="el" data-in="count" data-comma="1" data-from0="0" data-to="7000000" data-at=".3" data-d="1.4" style="position:static">7,000,000</span></div>', 130, 380, .2, "pop")
               + big("years ago", 140, 620, 90, .9, SIG))
AFR = (-20, 55, -36, 38)
B["L13"] = mapshot(*AFR, [(18.9, 16.0, "Chad", .5, SIG, "~7 million years ago")], None, x=None, w=1000)
B["L14a"] = dict(cls="coal", push=.05, credit=credit("toumai") + " · CAST",
                 body=photo("toumai", 560, 110, 800, .1, -2, h=600, label='<i class="sp" style="font-size:30px">Sahelanthropus tchadensis</i><br>nicknamed Toumaï · ~7 Ma · Chad · found 2001', lab_at=.9))
B["L14b"] = dict(cls="paper", push=.04, credit=BUSHCRED,
                 body=svg(f'<path d="M760 980 C 760 700, 700 600, 600 420" stroke="{INK}" stroke-width="16" fill="none" stroke-linecap="round"/><path d="M760 980 C 760 700, 830 600, 960 400" stroke="{MOSS}" stroke-width="16" fill="none" stroke-linecap="round"/>', .1, "draw")
                 + tag("chimpanzees", 470, 360, 34, .6) + tag("our line", 900, 340, 34, .8, MOSS)
                 + svg(f'<circle cx="760" cy="760" r="34" fill="{SIG}" stroke="{INK}" stroke-width="5"/>', 1.2, "pop") + hand("Toumaï: near the split?", 820, 760, 72, 1.5))
B["L15"] = dict(cls="paper", push=.03, credit="THE DEBATE: E.G. DAVER ET AL. 2022 (NATURE) FOR UPRIGHT WALKING; MACCHIARELLI ET AL. 2020 (JHE) AGAINST",
                body=big("Walked upright?", 120, 90, 120, .1)
                + el(f'<div class="card" style="width:640px;height:420px;background:#DCE5CC"><div class="disp" style="font-size:90px;color:{MOSS}">Yes</div><div class="tag" style="font-size:28px;margin-top:20px;white-space:normal;line-height:1.5">some researchers, from the thigh and arm bones</div></div>', 140, 360, .6, "slide")
                + el(f'<div class="card" style="width:640px;height:420px;background:#EED9CF"><div class="disp" style="font-size:90px;color:{OXIDE}">Not convinced</div><div class="tag" style="font-size:28px;margin-top:20px;white-space:normal;line-height:1.5">others, reading the same bones</div></div>', 1060, 360, 1.4, "slide", extra='data-from="r"'))
B["L16a"] = mapshot(*AFR, [(35.2, -3.2, "Laetoli, Tanzania", .4, SIG, "3.66 million years ago")], None, w=1000)
ash = "".join(f'<rect x="0" y="{600 + i * 70}" width="1920" height="70" fill="{c}"/>' for i, c in enumerate(("#8C8577", "#6F6A5F", "#575249", "#46423B", "#36332D", "#2B2925")))
prints = "".join(f'<ellipse class="el" data-in="pop" data-at="{.6 + i * .2:.1f}" cx="{300 + i * 220}" cy="{640 + (i % 2) * 50}" rx="34" ry="70" fill="#3A3833" transform="rotate(80 {300 + i * 220} {640 + (i % 2) * 50})"/>' for i, c in enumerate(range(7)))
B["L16b"] = dict(cls="coal", push=.05, credit="ILLUSTRATION: A TRAIL IN WET VOLCANIC ASH (NOT TO SCALE)",
                 body=svg(ash, 0, "pop", STILL) + svg(prints, 0, "pop", 'data-breathe="0" data-jit="0"') + hand("wet volcanic ash", 1250, 420, 80, .3, SIG))
B["L17"] = dict(cls="coal", push=.06, credit="3D SCAN, PANEL C OF A FIGURE BY " + credit("laetoli").replace("PHOTO: ", "") + " (RAICHLEN ET AL. 2010, PLOS ONE)",
                body=photo("laetoli_scan", 460, 80, 1000, .1, 1, h=720, bg="#000", label="3D scan of a real Laetoli footprint (G1-37) · Tanzania · ~3.66 Ma · upright, two-footed", lab_at=1.0)
                + hand("heel", 560, 700, 64, 1.6, SIG) + hand("toes", 1250, 690, 64, 1.9, SIG))
B["L18a"] = dict(cls="coal", push=.05, credit=credit("lucy") + " · RECONSTRUCTED CAST",
                 body=photo("lucy", 760, 20, 380, .1, -1, h=900, pos="center top")
                 + big('"Lucy"', 1250, 260, 130, .6, BONE) + el('<div class="sp" style="font-size:44px;color:#EAE2CF">Australopithecus afarensis</div>', 1260, 420, .9, "wipe"))
B["L18b"] = mapshot(*AFR, [(40.5, 11.1, "Hadar, Ethiopia", .2, SIG, "found 1974")], None, w=1000)
B["L19a"] = dict(cls="coal", push=.1, credit=credit("lucy") + " · RECONSTRUCTED CAST",
                 body=photo("lucy", 460, 40, 1000, 0, 0, h=900, pos="center 72%", k="pop").replace('data-at="0"', 'data-at="0" data-d=".01"')
                 + el('<div class="disp" style="font-size:150px;color:#FFDD33;text-shadow:0 8px 30px #000">3.2 Ma</div>', 1180, 120, .4, "pop")
                 + hand("legs built for walking", 1100, 860, 72, 1.0, SIG))
B["L19b"] = dict(cls="coal", push=.04, credit="BRAIN VOLUMES APPROX.: AU. AFARENSIS ~380–550 CC, MODERN HUMANS ~1,350 CC (SMITHSONIAN HUMAN ORIGINS) · CIRCLE AREA ∝ VOLUME",
                 body=brains([("Lucy's species", "~450 cc", 450, OCHRE), ("us", "~1,350 cc", 1350, MOSS)], x0=560, gapx=800) + tag("brain size", 120, 90, 40, .1, BONE))
B["L20"] = dict(cls="paper", push=.04, credit="ILLUSTRATION",
                body=svg(ladder(840, 120, 820, col="#9A917F"), 0, "pop", STILL)
                + svg(f'<circle cx="940" cy="640" r="40" fill="{OCHRE}"/>', .2) + tag("Lucy, a rung?", 1100, 620, 40, .4)
                + f'<svg class="el" data-in="draw" data-at="1.4" data-d="1.2" style="inset:0" width="1920" height="1080"><path d="M940 980 C 940 760, 760 640, 520 380 M940 760 C 1100 600, 1280 520, 1420 300 M760 600 C 700 500, 690 420, 700 300" stroke="{MOSS}" stroke-width="20" fill="none" stroke-linecap="round"/></svg>'
                + hand("messier", 1450, 200, 90, 2.0))
B["L21"] = mapshot(*AFR, [(36.3, 3.9, "Koobi Fora, Kenya", .2, SIG, "~1.5 million years ago")], None, w=1000)
trail = "".join(f'<ellipse class="el" data-in="pop" data-at="{.3 + i * .12:.2f}" cx="{200 + i * 130}" cy="{560 + (i % 2) * 70}" rx="30" ry="62" fill="{OCHRE}" transform="rotate(90 {200 + i * 130} {560 + (i % 2) * 70})"/>' for i in range(12))
trail += "".join(f'<ellipse class="el" data-in="pop" data-at="{1.9 + i * .2:.2f}" cx="{1080 + (i % 2) * 50}" cy="{250 + i * 150}" rx="24" ry="52" fill="{SIG}"/>' for i in range(3))
B["L22"] = dict(cls="coal", push=.04, credit="ILLUSTRATION AFTER HATALA ET AL., SCIENCE 2024 (12-PRINT TRAIL AND THREE ISOLATED PRINTS; LAYOUT SIMPLIFIED)",
                body=svg('<rect x="0" y="0" width="1920" height="1080" fill="#3B3730"/>', 0, "pop", STILL) + svg(trail, 0, "pop", 'data-breathe="0" data-jit="0"') + hand("one muddy lakeshore", 120, 100, 80, .2, BONE))
B["L23a"] = dict(cls="coal", push=.05, credit=credit("boisei") + " · CAST",
                 body=photo("boisei", 300, 120, 700, .1, -2, h=640, label='<i class="sp" style="font-size:30px">Paranthropus boisei</i><br>huge jaws and teeth for tough food', lab_at=.9)
                 + tag("Homo erectus", 1200, 300, 40, 1.3, "#1E1D1A", SIG) + tag("Paranthropus boisei", 1200, 400, 40, 1.6, "#1E1D1A", OCHRE))
B["L23b"] = dict(cls="coal", push=.06, credit="ILLUSTRATION AFTER HATALA ET AL., SCIENCE 2024",
                 body=svg('<rect x="0" y="0" width="1920" height="1080" fill="#3B3730"/>', 0, "pop", STILL)
                 + svg(trail.replace('class="el" data-in="pop"', 'class="el" data-in="pop" data-d=".01"').replace('data-at="', 'data-at="0" data-x="'), 0, "pop", STILL)
                 + tag("P. boisei", 260, 440, 44, .3, "#1E1D1A", OCHRE) + tag("H. erectus", 1170, 300, 44, .6, "#1E1D1A", SIG))
B["L24"] = dict(cls="coal", push=.04, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis"], ["erectus", "boisei"], hi=("erectus", "boisei"))
                + hand("side by side", 1400, 380, 72, 1.6, SIG))
# --- erectus
B["L25"] = dict(cls="coal", push=.05, credit=credit("turkana") + " · TURKANA BOY, ~1.5 MA",
                body=photo("turkana", 720, 20, 480, .1, 1, h=930, pos="center top")
                + el('<div class="sp" style="font-size:80px;color:#EAE2CF">Homo erectus</div>', 1280, 300, .6, "wipe") + hand("went further", 1290, 420, 72, 1.1, SIG))
WRLD = (-20, 150, -15, 55)
B["L26"] = mapshot(*WRLD, [(36.3, 3.9, "Africa", .2, SIG), (44.4, 41.3, "Georgia", .7, SIG), (116, 39.7, "China", 1.2, SIG), (111.4, -7.4, "Java", 1.7, SIG)], None, w=1800)
B["L27a"] = mapshot(95, 130, -12, 10, [(111.4, -7.4, "Ngandong, Java", .3, SIG, "last known H. erectus")], None, w=1400)
B["L27b"] = dict(cls="coal", push=.05, credit="SOURCE: RIZAL ET AL., NATURE 2020: 117,000–108,000 YEARS AGO",
                 body=el('<div class="disp" style="font-size:240px;color:#EAE2CF">≈<span class="el" data-in="count" data-comma="1" data-from0="1900000" data-to="110000" data-at=".2" data-d="1.4" style="position:static">110,000</span></div>', 120, 300, .1, "pop")
                 + tag("years ago · last known Homo erectus", 140, 620, 40, .8, SIG))
B["L28"] = dict(cls="coal", push=.04, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei"], [], hi=()) + bush([], ["erectus"], hi=("erectus",), labels=False)
                + svg(f'<path d="M560 {Y(1.89):.0f} L540 {Y(1.89):.0f} L540 {Y(.108):.0f} L560 {Y(.108):.0f}" stroke="{SIG}" stroke-width="6" fill="none"/>', 1.2, "draw")
                + big("1.5+ million years", 160, 600, 70, 1.4, SIG, w=380))
# --- chapter 3: the crowd
B["K3"] = dict(cls="coal", push=.05, credit="", body=tag("Chapter two", 140, 360, 34, .1, "#8C8577") + big("The crowd", 130, 420, 220, .3, BONE))
B["L29"] = dict(cls="coal", push=.05, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus"], ["sapiens", "neander", "naledi", "deni", "flores", "luzon"], at0=.1, dim=False))
B["L30a"] = mapshot(*AFR, [(-8.9, 31.9, "Jebel Irhoud, Morocco", .3, SIG, "~300,000 years ago")], None, w=1000)
B["L30b"] = dict(cls="coal", push=.06, credit=credit("irhoud") + " · RECONSTRUCTION FROM SCANS · SITE DATED ~315,000 YEARS (HUBLIN ET AL., NATURE 2017)",
                 body=photo("irhoud", 600, 80, 720, .05, -1, h=760, pos="center 40%"))
B["L31"] = dict(cls="paper", push=.03, credit="HUBLIN ET AL. 2017 (NATURE) CALL THEM EARLY H. SAPIENS; OTHERS (E.G. J. HAWKS) SEE A FORM ON THE WAY",
                body=el(f'<div class="card" style="width:700px;height:380px;background:#DCE5CC"><div class="disp" style="font-size:80px;color:{MOSS}">Early<br><i class="sp">Homo sapiens</i></div><div class="tag" style="font-size:28px;margin-top:24px">some experts</div></div>', 140, 300, .1, "slide")
                + el(f'<div class="card" style="width:700px;height:380px;background:#EED9CF"><div class="disp" style="font-size:80px;color:{OXIDE}">A step<br>on the way</div><div class="tag" style="font-size:28px;margin-top:24px">others</div></div>', 1060, 300, 1.4, "slide", extra='data-from="r"'))
B["L32"] = dict(cls="coal", push=.05, credit=credit("naledi") + " · BERGER ET AL., ELIFE 2015",
                body=photo("naledi", 420, 30, 760, .05, 0, h=980, pos="center 30%")
                + el('<div class="sp" style="font-size:80px;color:#EAE2CF">Homo naledi</div>', 1260, 260, .5, "wipe") + tag("Rising Star cave · South Africa", 1240, 380, 26, .9, SIG))
B["L33"] = dict(cls="coal", push=.04, credit="BRAIN VOLUMES: H. NALEDI ~465–610 CC (BERGER ET AL. 2015/2017), MODERN HUMANS ~1,350 CC · CIRCLE AREA ∝ VOLUME",
                body=brains([("Homo naledi", "~550 cc", 550, OCHRE), ("us", "~1,350 cc", 1350, MOSS)], x0=560, gapx=800) + hand("less than half", 120, 100, 80, 1.2, SIG))
B["L34"] = dict(cls="coal", push=.04, credit="SOURCE: DIRKS ET AL., ELIFE 2017: 335,000–236,000 YEARS AGO · " + BUSHCRED,
                body=bush(["afar", "habilis", "erectus", "sapiens", "neander"], ["naledi"], hi=("naledi", "sapiens")) + hand("not millions", 1500, 700, 72, 1.5, SIG))
B["L35"] = dict(cls="coal", push=.05, credit=credit("neander") + " · LA CHAPELLE-AUX-SAINTS (CAST)",
                body=photo("neander", 300, 100, 640, .05, -2, h=760) + el('<div class="disp" style="font-size:112px;color:#EAE2CF">Neanderthals</div>', 990, 320, .5, "slide", extra='data-from="r"')
                + tag("Europe · western Asia", 1010, 470, 34, .9, SIG))
B["L36"] = dict(cls="coal", push=.06, credit=credit("skulls") + " · REPLICA SKULLS: NEANDERTHAL (LEFT), MODERN HUMAN (RIGHT)",
                body=photo("skulls", 640, 20, 640, .05, 0, h=960, pos="center 45%") + hand("as large as ours", 1320, 450, 80, .9, SIG))
B["L37a"] = dict(cls="coal", push=.06, credit=credit("denisova") + " · REPLICA",
                 body=photo("denisova", 160, 140, 900, .05, -1, h=600) + big("Denisovans", 1180, 300, 104, .6, BONE, k="slide", extra='data-from="r"'))
dna = "".join(el(f'<div class="tag" style="font-size:44px;color:{["#6E8F3E", "#C4882C", "#A4442A", "#EAE2CF"][j % 4]}">{"ACGTTGCA"[j % 8]}</div>', 200 + j * 70, 300 + (j % 5) * 90, .05 + j * .04, "pop") for j in range(22))
B["L37b"] = dict(cls="coal", push=.05, credit="FIRST DENISOVAN GENOME FROM A FINGER BONE, DENISOVA CAVE, SIBERIA (KRAUSE ET AL. 2010; REICH ET AL. 2010)",
                 body=dna + el('<div class="stamp" style="font-size:110px;background:#1E1D1A">2010</div>', 1300, 720, 1.0, "pop", base="rotate(-6deg)") + hand("known mostly from DNA", 160, 120, 72, .5, SIG))
B["L38"] = dict(cls="coal", push=.05, credit=credit("flores") + " · LB1 (CAST) · HEIGHT ~1.06 M (BROWN ET AL. 2004)",
                body=photo("flores", 260, 140, 860, .05, -1, h=640)
                + svg(f'<rect x="1400" y="{940 - 425}" width="90" height="425" fill="{OCHRE}"/><rect x="1560" y="{940 - 700}" width="90" height="700" fill="#5B574E"/><path d="M1360 940 H1700" stroke="#EAE2CF" stroke-width="4"/>', .6, "pop")
                + tag("~1 m", 1395, 470, 30, 1.0, BONE) + tag("1.65 m", 1555, 190, 30, 1.0, BONE)
                + el('<div class="sp" style="font-size:60px;color:#EAE2CF">Homo floresiensis</div>', 1220, 90, .4, "wipe"))
B["L39"] = mapshot(100, 135, -12, 22, [(121.6, 17.6, "Callao Cave, Luzon", .3, SIG, "Homo luzonensis · named 2019"), (120.4, -8.5, "Flores", .9, OCHRE)], None, w=1300)
B["L40"] = dict(cls="coal", push=.04, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus", "sapiens", "neander", "naledi", "deni", "flores", "luzon"], [])
                + svg(ladder(1600, 300, 600, col="#9A917F", w=140), .3)
                + f'<svg class="el" data-in="draw" data-at="1.0" data-d=".4" style="inset:0" width="1920" height="1080"><path d="M1560 280 L1790 920" stroke="{OXIDE}" stroke-width="22" stroke-linecap="round"/></svg>')
six = ("sapiens", "neander", "deni", "flores", "luzon", "erectus")
B["L41a"] = dict(cls="coal", push=.05, credit=BUSHCRED + " · H. LUZONENSIS DATES ARE MINIMUM AGES (DASHED: MAY BE OLDER)",
                 body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "naledi"], [], dim=True)
                 + bush(list(six), [], hi=six, line_at=.11, at0=.2, labels=True)
                 + tag("~110,000 years ago", 1380, Y(.11) - 60, 30, 1.2, "#1E1D1A", SIG))
cards6 = [("irhoud", "H. sapiens"), ("neander", "Neanderthals"), ("denisova", "Denisovans"), ("flores", "H. floresiensis"), (None, "H. luzonensis"), ("turkana", "H. erectus")]
row = ""
for i, (nm, lab) in enumerate(cards6):
    x = 70 + i * 305
    inner = f'<img src="{img(nm)}" style="width:250px;height:330px;object-fit:cover;display:block">' if nm else '<div style="width:250px;height:330px;background:#3A3833;color:#EAE2CF;font:900 160px Fraunces;text-align:center;line-height:330px">?</div>'
    row += el(f'<div class="card" style="padding:12px">{inner}<div class="sp" style="font-size:26px;margin-top:10px;width:250px">{lab}</div></div>', x, 300, .1 + i * .25, "drop", base=f"rotate({[-3, 2, -1, 3, -2, 1][i]}deg)")
B["L41b"] = dict(cls="coal", push=.04, credit="PHOTOS: WIKIMEDIA COMMONS (SEE PRESHOW FOR EACH CREDIT) · 'AS MANY AS SIX': SOME DATES ARE MINIMUM AGES",
                 body=row + el('<div class="disp" style="font-size:140px;color:#FFDD33"><span class="el" data-in="count" data-from0="1" data-to="6" data-at=".2" data-d="1.4" style="position:static">6</span></div>', 1700, 60, .1, "pop"))
crowd = "".join(f'<circle class="el" data-in="pop" data-at="{.8 + (i % 30) * .02:.2f}" cx="{140 + (i * 137) % 1640}" cy="{560 + (i * 61) % 420}" r="{14 + (i % 4) * 4}" fill="{[MOSS, OCHRE, OXIDE, BONE, SIG][i % 5]}"/>' for i in range(120))
B["L42"] = dict(cls="coal", push=.05, credit="", body=big("Not a line.", 140, 120, 150, .1, BONE) + big("A crowd.", 1000, 120, 150, .7, SIG) + svg(crowd, 0, "pop", 'data-breathe="0"'))
B["L43"] = dict(cls="paper", push=.05, credit="ILLUSTRATION",
                body=f'<svg class="el" data-in="draw" data-at=".1" data-d="1.4" style="inset:0" width="1920" height="1080"><path d="M500 1000 C 520 700, 820 560, 900 300" stroke="{MOSS}" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M1400 1000 C 1380 700, 1060 560, 1000 300" stroke="{OCHRE}" stroke-width="22" fill="none" stroke-linecap="round"/><path d="M790 560 C 900 520, 1000 520, 1110 560" stroke="{SIG}" stroke-width="12" fill="none" stroke-dasharray="14 10"/></svg>'
                + svg(f'<circle cx="950" cy="525" r="40" fill="{SIG}"/>', 1.4) + hand("the branches touched", 640, 160, 90, 1.6))
B["L44a"] = dict(cls="coal", push=.04, credit="ESTIMATES: ~2% (E.G. PRÜFER ET AL. 2014); RANGE ~1.5–4% BY POPULATION AND METHOD (VERNOT ET AL. 2016)",
                 body=tag("your genome, if your ancestors lived outside Africa", 160, 340, 34, .1, BONE) + dna_strip(2) + tag("≈ 2% Neanderthal", 160, 660, 44, 1.6, "#1E1D1A", SIG))
B["L44b"] = dict(cls="coal", push=.04, credit="ESTIMATES VARY BY STUDY, POPULATION AND METHOD",
                 body=el('<div class="disp" style="font-size:300px;color:#FFDD33">~2%</div>', 160, 260, .1, "pop") + hand("from Neanderthals", 900, 420, 100, .6, BONE) + tag("estimates ~1.5–4%", 900, 600, 40, 1.0, BONE))
B["L45"] = mapshot(125, 160, -15, 5, [(143.5, -6.0, "Papua New Guinea", .3, SIG, "several % Denisovan DNA (up to ~5%)")], None, w=1400)
B["L45"]["credit"] = "MAP: NATURAL EARTH · DENISOVAN ANCESTRY ESTIMATES VARY WIDELY BY METHOD (REICH ET AL. 2010; VERNOT ET AL. 2016)"
braid = f'<path d="M300 1000 C 600 800, 300 600, 700 400 S 900 200, 1000 120" stroke="{MOSS}" stroke-width="20" fill="none"/><path d="M1600 1000 C 1300 800, 1500 600, 1100 420 S 950 220, 1000 120" stroke="{OCHRE}" stroke-width="20" fill="none"/><path d="M900 1000 C 950 800, 1000 600, 1000 120" stroke="{SIG}" stroke-width="16" fill="none"/>'
B["L46a"] = dict(cls="coal", push=.05, credit="ILLUSTRATION", body=f'<svg class="el" data-in="draw" data-at=".1" data-d="1.8" style="inset:0" width="1920" height="1080">{braid}</svg>' + hand("not only replaced", 120, 120, 80, 1.2, BONE))
B["L46b"] = dict(cls="paper", push=.04, credit="", body=big("They met them.", 140, 300, 170, .1) + big("And had children with them.", 140, 560, 110, .8, MOSS))
B["L47"] = dict(cls="coal", push=.04, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus", "naledi", "neander", "deni", "flores", "luzon", "sapiens"], [], ended=("erectus", "naledi", "neander", "deni", "flores", "luzon"), at0=.1))
B["L48"] = dict(cls="coal", push=.05, credit=credit("neander") + " · DATES: HIGHAM ET AL., NATURE 2014 (41,000–39,000 YEARS AGO)",
                body=el(f'<div class="card"><img src="{img("neander")}" style="width:600px;height:740px;object-fit:cover;display:block;filter:grayscale(1) brightness(.75)"></div>', 200, 120, 0, "pop", extra=STILL)
                + el('<div class="disp" style="font-size:200px;color:#EAE2CF">≈<span class="el" data-in="count" data-comma="1" data-from0="400000" data-to="40000" data-at=".3" data-d="1.4" style="position:static">40,000</span></div>', 900, 320, .2, "pop")
                + tag("years ago · Neanderthals vanish", 920, 560, 32, 1.2, SIG))
B["L49a"] = dict(cls="coal", push=.06, credit=credit("flores") + " · LB1 (CAST)",
                 body=el(f'<div class="card"><img src="{img("flores")}" style="width:900px;height:640px;object-fit:cover;display:block;filter:grayscale(1) brightness(.75)"></div>', 500, 160, 0, "pop", extra=STILL))
B["L49b"] = dict(cls="coal", push=.05, credit="SOURCE: SUTIKNA ET AL., NATURE 2016: SKELETAL REMAINS ~100,000–60,000 YEARS OLD",
                 body=el('<div class="disp" style="font-size:240px;color:#EAE2CF">≈<span class="el" data-in="count" data-comma="1" data-from0="100000" data-to="60000" data-at=".2" data-d="1.2" style="position:static">60,000</span></div>', 160, 300, .1, "pop")
                 + tag("years · the youngest Homo floresiensis bones", 170, 620, 36, .9, SIG))
B["L50"] = dict(cls="coal", push=.06, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus", "naledi", "neander", "deni", "flores", "luzon"], [], dim=True, labels=False)
                + bush([], ["sapiens"], hi=("sapiens",), at0=.2) + big("Us.", 1180, 60, 200, 1.4, SIG, k="pop"))
# --- chapter 4: the mind
B["K4"] = dict(cls="coal", push=.05, credit="", body=tag("Chapter three", 140, 360, 34, .1, "#8C8577") + big("Why the ladder sticks", 130, 420, 160, .3, BONE, w=1700))
B["L51"] = dict(cls="paper", push=.05, credit="ILLUSTRATION", body=svg(ladder(860, 140, 800, col=INK), .1, "pop") + big("?", 1200, 200, 400, .8, OXIDE, k="pop"))
B["L52a"] = dict(cls="paper", push=.04, credit="STEPHEN JAY GOULD, WONDERFUL LIFE (1989), CHAPTER 1: 'THE ICONOGRAPHY OF AN EXPECTATION' (PARAPHRASED)",
                 body=el('<div class="card" style="width:1300px;padding:60px 70px"><div class="tag" style="font-size:30px;color:#A4442A">Stephen Jay Gould · palaeontologist</div><div class="dispb" style="font-size:72px;margin-top:30px;line-height:1.15">The picture shows what we <span class="hl" data-in="sweep" data-at="1.4" data-d="1.0">expect to see.</span></div></div>', 300, 260, .1, "drop", base="rotate(-1deg)"))
B["L52b"] = dict(cls="coal", push=.05, credit="STEPHEN JAY GOULD, WONDERFUL LIFE, 1989",
                 body=el('<div style="width:520px;height:720px;background:#5B3A2A;box-shadow:16px 20px 0 rgba(0,0,0,.5);padding:60px 40px;box-sizing:border-box"><div class="disp" style="font-size:72px;color:#EAE2CF">Wonderful Life</div><div class="tag" style="font-size:26px;color:#C4882C;margin-top:30px">Stephen Jay Gould · 1989</div></div>', 700, 160, .1, "drop", base="rotate(3deg)")
                 + hand('"the iconography of an expectation"', 160, 940, 64, .9, SIG))
B["L53"] = dict(cls="paper", push=.05, credit="ILLUSTRATION",
                body=svg(ladder(860, 520, 500, col=INK), 0, "pop", STILL)
                + svg(f'<g transform="translate(960,-110) scale(.7)">{figure(0, 0, OXIDE)}</g>', .6, "drop") + hand("the top: us", 1240, 200, 90, 1.4))
B["L54a"] = dict(cls="coal", push=.04, credit="BRAIN VOLUMES APPROX.: LB1 ~426 CC (KUBO ET AL. 2013), CHIMPANZEE ~400 CC, MODERN HUMANS ~1,350 CC · CIRCLE AREA ∝ VOLUME",
                 body=brains([("chimpanzee", "~400 cc", 400, "#8C8577"), ("H. floresiensis", "~426 cc", 426, OCHRE), ("us", "~1,350 cc", 1350, MOSS)], x0=330, gapx=620) + tag("brain size", 120, 80, 40, .1, BONE))
tools = "".join(f'<path class="el" data-in="pop" data-at="{.3 + i * .25:.2f}" d="M{500 + i * 330} 700 l60 -170 l70 30 l40 150 l-80 60 Z" fill="{["#8C8577", "#A39C8C", "#6F6A5F", "#8C8577"][i]}" stroke="#EAE2CF" stroke-width="4"/>' for i in range(4))
B["L54b"] = dict(cls="coal", push=.05, credit="ILLUSTRATION · STONE TOOLS FOUND WITH H. FLORESIENSIS AT LIANG BUA (SUTIKNA ET AL. 2016)",
                 body=svg(tools, 0, "pop", 'data-breathe="0"') + hand("and still made stone tools", 400, 200, 90, 1.2, SIG))
B["L55"] = dict(cls="coal", push=.05, credit=BUSHCRED,
                body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus", "naledi", "neander", "deni", "flores", "luzon"], [], ended=("sahel", "ardi", "afar", "habilis", "boisei", "erectus", "naledi", "neander", "deni", "flores", "luzon"), at0=0, labels=False, dim=True)
                + bush([], ["sapiens"], hi=("sapiens",), at0=.3, labels=False) + hand("no top. just survivors", 1250, 150, 72, 1.4, SIG))
B["L56a"] = dict(cls="coal", push=.12, credit=BUSHCRED,
                 body=bush(["sahel", "ardi", "afar", "habilis", "boisei", "erectus", "naledi", "neander", "deni", "flores", "luzon"], [], at0=0, labels=False)
                 + bush([], ["sapiens"], hi=("sapiens",), at0=.2))
B["L56b"] = dict(cls="paper", push=.05, credit="",
                 body=big("The last twig left", 140, 220, 140, .1) + big("on a crowded bush.", 140, 400, 140, .8, MOSS)
                 + svg(f'<path d="M1500 1000 C1500 860 1500 800 1500 700" stroke="{MOSS}" stroke-width="20" stroke-linecap="round"/><circle cx="1500" cy="690" r="30" fill="{SIG}"/>', 1.6, "draw"))

# ---------------- upgrades: cut-out specimens, photo-filled type, tilted paper map ----------------
def specimen(name, x, y, w, at=.1, label=None, cr=""):
    """A BiRefNet cut-out of the real fossil (colour kept, nothing redrawn) on a lit plinth."""
    cut = (AS / f"{name}_cut.png")
    if not cut.exists():
        return None
    b = el('<div style="width:1920px;height:1080px;background:radial-gradient(ellipse 34% 60% at 50% 0%,rgba(255,236,190,.22),transparent 70%)"></div>', 0, 0, 0, "pop", extra=STILL)
    from PIL import Image as _I
    iw, ih = _I.open(cut).size
    b += el(f'<div style="width:{w + 160}px;height:70px;background:linear-gradient(#3A3731,#262420);border-top:3px solid #57524A"></div>', x - 80, y + int(w * ih / iw) - 10, 0, "pop", extra=STILL)
    b += el(f'<img src="{cut.as_uri()}" style="width:{w}px;filter:drop-shadow(0 30px 30px rgba(0,0,0,.7))">', x, y, at, "drop", extra='data-jit="0"')
    if label:
        b += el(f'<div class="label" style="font-size:24px;line-height:1.5">{label}</div>', x + w + 40, y + 120, at + .7, "wipe")
    return b
def filled(text, imgname, size, x, y, at, pos="center", extra_style=""):
    return el(f'<div class="disp" style="font-size:{size}px;background:url({img(imgname)}) {pos}/cover;-webkit-background-clip:text;background-clip:text;color:transparent;filter:contrast(1.2) brightness(1.15);{extra_style}">{text}</div>', x, y, at, "pop")
sp = specimen("toumai", 470, 150, 760, .1, '<i class="sp" style="font-size:30px">Sahelanthropus tchadensis</i><br>nicknamed Toumaï · ~7 Ma<br>Chad · found 2001')
if sp:
    B["L14a"] = dict(cls="coal", push=.06, credit=credit("toumai") + " · CAST · BACKGROUND REMOVED (BIREFNET), FOSSIL UNALTERED", body=sp.replace('left:1270px', 'left:1250px'))
if img("laetoli"):
    B["K2"]["body"] = tag("Chapter one", 140, 300, 34, .1, "#8C8577") + filled('<span class="el" data-in="count" data-comma="1" data-from0="0" data-to="7000000" data-at=".3" data-d="1.4" style="position:static">7,000,000</span>', "toumai", 250, 120, 350, .2, "center 45%") + big("years ago", 140, 640, 90, .9, SIG)
    B["K2"]["credit"] = "TYPE FILLED WITH THE TOUMAÏ FOSSIL PHOTO · " + credit("toumai")
if img("haeckel_1874"):
    B["K3"]["body"] = tag("Chapter two", 140, 330, 34, .1, "#8C8577") + filled("The crowd", "haeckel_1874", 300, 110, 380, .3, "center 40%", "filter:sepia(.35) contrast(1.1)")
    B["K3"]["credit"] = "TYPE FILLED WITH HAECKEL'S 1874 ENGRAVING (PUBLIC DOMAIN)"
B["L26"]["body"] = f'<div class="el" data-in="pop" data-at="0" data-d=".01" data-breathe="0" data-jit="0" data-base="perspective(1500px) rotateX(36deg) scale(1.12) translateY(-40px)" style="inset:0;transform-origin:50% 70%">{B["L26"]["body"]}</div>' + big("Further than anyone before", 80, 60, 70, .2, BONE)

sp = specimen("boisei", 300, 170, 640, .1, '<i class="sp" style="font-size:30px">Paranthropus boisei</i><br>huge jaws and teeth<br>for tough food')
if sp:
    B["L23a"] = dict(cls="coal", push=.05, credit=credit("boisei") + " · CAST · BACKGROUND REMOVED (BIREFNET)", body=sp
                     + tag("Homo erectus", 1240, 700, 40, 1.3, "#1E1D1A", SIG) + tag("Paranthropus boisei", 1240, 790, 40, 1.6, "#1E1D1A", OCHRE))
sp = specimen("neander", 280, 90, 600, .05)
if sp:
    B["L35"] = dict(cls="coal", push=.05, credit=credit("neander") + " · LA CHAPELLE-AUX-SAINTS (CAST) · BACKGROUND REMOVED (BIREFNET)", body=sp
                    + el('<div class="disp" style="font-size:112px;color:#EAE2CF">Neanderthals</div>', 990, 320, .5, "slide", extra='data-from="r"') + tag("Europe · western Asia", 1000, 470, 34, .9, SIG))

# ---------------- timing ----------------
PLAN = [("L01", ["L01a", "L01b"]), ("L02", ["L02"]), ("L03", ["L03"]), ("L04", ["L04"]), ("L05", ["L05a", "L05b"]), ("L06", ["L06"]), ("L07", ["L07"]),
        ("L08", ["L08"]), ("L09", ["L09a", "L09b"]), ("L10", ["L10"]), ("L11", ["L11"]), ("L12", ["L12"]), ("K2", ["K2"]), ("L13", ["L13"]),
        ("L14", ["L14a", "L14b"]), ("L15", ["L15"]), ("L16", ["L16a", "L16b"]), ("L17", ["L17"]), ("L18", ["L18a", "L18b"]), ("L19", ["L19a", "L19b"]),
        ("L20", ["L20"]), ("L21", ["L21"]), ("L22", ["L22"]), ("L23", ["L23a", "L23b"]), ("L24", ["L24"]), ("L25", ["L25"]), ("L26", ["L26"]),
        ("L27", ["L27a", "L27b"]), ("L28", ["L28"]), ("K3", ["K3"]), ("L29", ["L29"]), ("L30", ["L30a", "L30b"]), ("L31", ["L31"]), ("L32", ["L32"]),
        ("L33", ["L33"]), ("L34", ["L34"]), ("L35", ["L35"]), ("L36", ["L36"]), ("L37", ["L37a", "L37b"]), ("L38", ["L38"]), ("L39", ["L39"]),
        ("L40", ["L40"]), ("L41", ["L41a", "L41b"]), ("L42", ["L42"]), ("L43", ["L43"]), ("L44", ["L44a", "L44b"]), ("L45", ["L45"]),
        ("L46", ["L46a", "L46b"]), ("L47", ["L47"]), ("L48", ["L48"]), ("L49", ["L49a", "L49b"]), ("L50", ["L50"]), ("K4", ["K4"]), ("L51", ["L51"]),
        ("L52", ["L52a", "L52b"]), ("L53", ["L53"]), ("L54", ["L54a", "L54b"]), ("L55", ["L55"]), ("L56", ["L56a", "L56b"])]
PAUSE = {"L03": 0.9, "L07": 0.6, "L08": 0.5, "L12": 0.5, "L42": 0.8, "L50": 1.0, "L56": 2.2}
GAP = 0.5
timeline, t = [], 0.0
for line, shots in PLAN:
    total = 3.0 if line.startswith("K") else sc[line]["sec"] + GAP + PAUSE.get(line, 0)
    parts = [total] if len(shots) == 1 else [round(total * .5, 2), round(total - round(total * .5, 2), 2)]
    for i, (sid, d) in enumerate(zip(shots, parts)):
        timeline.append({"shot": sid, "start": round(t, 3), "dur": d, "line": line if (i == 0 and not line.startswith("K")) else None})
        t += round(d * 24) / 24
for s in timeline:
    b = B[s["shot"]]
    cr = b["credit"]
    (D / "shots" / f"{s['shot']}.html").write_text(HEAD.format(dur=s["dur"], push=b["push"], cls=b["cls"]) + b["body"]
                                                    + TAIL.format(credit=f'<div class="credit" style="color:{"#8C8577" if b["cls"] == "coal" else "#6d675c"}">{cr}</div>' if cr else ""), encoding="utf-8")
json.dump({"shots": timeline, "total": round(t, 2)}, open(D / "timeline.json", "w"), indent=1)
ds = [s["dur"] for s in timeline]
print(len(timeline), "shots", round(t, 1), "s  max", max(ds), "mean", round(sum(ds) / len(ds), 2), "over5:", [(s["shot"], s["dur"]) for s in timeline if s["dur"] > 5])
