"""Animated maps from real geodata (2026-11-19, owner: "more real pictures, animation, motion graphics, less AI").
Land and borders: Natural Earth 1:50m admin-0 (public domain); India in its official boundary (DataMeet India composite,
CC BY 4.0), drawn on top. Each map is a paper sheet on the walnut map table, with pins, red string and handwritten tags,
and every piece carries a timeline entry (render any moment with ?t=0..1). Numbers only from dossier.json.
  13a_relay   the relay race: Calicut -> Aden -> Cairo/Alexandria -> Venice -> Bruges, a "+ cut" at every hand-off
  13b_shift   the shortcut: the old relay fades, Lisbon's sea road round Africa draws (Casa da India, c. 1500)
  15a_world   who grows it now: producer circles grow from zero on the world map (FAO 2023, area ~ tonnes)
Run after frames.py (it imports the page kit)."""
import json
import math
from pathlib import Path
from frames import page, A, a, put, chapter, hl, blk, wobble, DESK, SIG, RED, INK, PARCH

FILMS = Path(__file__).resolve().parent.parent
NE = FILMS / "bolivia-navy-2026-11-19" / "maps" / "ne_50m_admin_0_countries.geojson"
INDIA = FILMS / "india-mocked-2026-11-17" / "data" / "india-composite.geojson"
GEO_SRC = "LAND AND BORDERS: NATURAL EARTH 1:50M (PUBLIC DOMAIN) · INDIA: OFFICIAL BOUNDARY, DATAMEET INDIA COMPOSITE (CC BY 4.0)"
LAND, LINE, SEA = "#E4D9C3", "#5A4A36", "#F4EFE6"


def _rings(geom, step):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for p in polys:
        r = p[0]
        k = step if len(r) > 400 else 1
        yield r[::k] + [r[0]]


def _load():
    ne = json.load(open(NE))
    other = [f["geometry"] for f in ne["features"] if f["properties"].get("ADM0_A3") != "IND"]
    ind = json.load(open(INDIA)); ind = [f["geometry"] for f in ind["features"]] if "features" in ind else [ind]
    return other, ind


OTHER, IND = _load()


class Proj:
    """Equirectangular projection of a lon/lat box onto a sheet of w x h pixels."""
    def __init__(self, lon0, lon1, lat0, lat1, w, h):
        self.lon0, self.lat1 = lon0, lat1
        self.k = min(w / (lon1 - lon0), h / (lat1 - lat0)); self.w, self.h = w, h

    def __call__(self, lon, lat):
        return (lon - self.lon0) * self.k, (self.lat1 - lat) * self.k


def land_svg(P, w, h, step=3, india_step=60):
    def path(ring):
        pts = [P(x, y) for x, y in ring]
        if all(px < -50 or px > w + 50 for px, _ in pts) or all(py < -50 or py > h + 50 for _, py in pts):
            return ""
        return "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts) + "Z"
    other = "".join(path(r) for g in OTHER for r in _rings(g, step))
    ind = "".join(path(r) for g in IND for r in _rings(g, india_step))
    grid = "".join(f'<line x1="{P(lo, 0)[0]:.0f}" y1="0" x2="{P(lo, 0)[0]:.0f}" y2="{h}" stroke="rgba(90,74,54,.12)" stroke-width="1.5"/>' for lo in range(-180, 181, 15))
    grid += "".join(f'<line x1="0" y1="{P(0, la)[1]:.0f}" x2="{w}" y2="{P(0, la)[1]:.0f}" stroke="rgba(90,74,54,.12)" stroke-width="1.5"/>' for la in range(-90, 91, 15))
    return (f'<rect width="{w}" height="{h}" fill="{SEA}"/>{grid}'
            f'<path d="{other}" fill="{LAND}" stroke="{LINE}" stroke-width="1.2" stroke-linejoin="round"/>'
            f'<path d="{ind}" fill="{LAND}" stroke="{LINE}" stroke-width="1.2" stroke-linejoin="round"/>')


SX, SY, SW, SH = 70, 112, 1780, 918     # the paper sheet on the desk


def sheet(P, inner_svg, extra=""):
    """The map as a paper sheet on the walnut map table, taped at two corners."""
    tape = lambda x, y, r: a(f'<div style="width:150px;height:40px;background:rgba(236,226,200,.85);transform:rotate({r}deg);box-shadow:0 2px 4px rgba(0,0,0,.25)"></div>', x, y, "z-index:20")
    return (a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
            + a(f'<svg width="{SW}" height="{SH}" style="display:block">{land_svg(P, SW, SH)}{inner_svg}</svg>', SX, SY,
                "box-shadow:0 30px 60px rgba(0,0,0,.6);overflow:hidden")
            + tape(SX - 50, SY + SH - 60, 32) + tape(SX + SW - 110, SY + SH - 30, -28) + extra)


def pinsvg(x, y, r=13):
    return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{RED}" stroke="#FFF" stroke-width="2.5"/><circle cx="{x - 4:.0f}" cy="{y - 4:.0f}" r="4" fill="#FF9A90"/>'


def onpage(P, lon, lat):
    x, y = P(lon, lat); return x + SX, y + SY


def label(P, lon, lat, text, dx=18, dy=-16, anim="fade 0 .05", left=False):
    x, y = onpage(P, lon, lat)
    return A(f'<div style="background:{PARCH};padding:4px 10px;font:500 18px Plex;letter-spacing:3px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35);white-space:nowrap;'
             f'{"transform:translateX(-100%)" if left else ""}">{text}</div>', x + (-dx if left else dx), y + dy, anim, "z-index:32")


def handtag(x, y, text, rot, anim, bg=SIG, col=INK, size=36):
    return A(f'<div style="background:{bg};color:{col};padding:6px 14px;font:700 {size}px Caveat;transform:rotate({rot}deg);white-space:nowrap;box-shadow:0 8px 14px rgba(0,0,0,.4)">{text}</div>', x, y, anim, "z-index:34")


def string(P, pts, anim, col=RED, w=6, dash=""):
    d = "M" + " L".join(f"{P(lo, la)[0]:.0f} {P(lo, la)[1]:.0f}" for lo, la in pts)
    return (f'<svg class="a" data-anim="{anim}" style="left:{SX}px;top:{SY}px;z-index:30" width="{SW}" height="{SH}">'
            f'<path d="{d}" pathLength="1" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def pins(P, pts, start, gap):
    out = ""
    for i, (lo, la) in enumerate(pts):
        x, y = P(lo, la)
        out += (f'<svg class="a" data-anim="pop {start + i * gap:.2f} {start + i * gap + .05:.2f}" style="left:{SX + x - 16:.0f}px;top:{SY + y - 16:.0f}px;z-index:31" width="32" height="32" viewBox="{x - 16:.0f} {y - 16:.0f} 32 32">{pinsvg(x, y)}</svg>')
    return out


# ---- 13a: the world's longest relay race (3 · 5:00) -----------------------------------------------------------------
P = Proj(-12, 84, 2, 58, SW, SH)
calicut, aden, cairo, venice, bruges = (75.78, 11.25), (45.03, 12.8), (31.24, 30.05), (12.33, 45.44), (3.22, 51.21)
route = [calicut, (65.0, 12.5), (52.0, 12.0), aden, (43.3, 12.6), (39.0, 20.0), (34.0, 27.5), (32.6, 29.9), cairo, (29.9, 31.2),
         (26.0, 33.5), (20.0, 36.8), (18.9, 40.0), (14.5, 43.5), venice, (11.0, 47.5), (8.5, 49.5), (6.0, 50.5), bruges]
stops = [calicut, aden, cairo, venice, bruges]
legs = [("CALICUT", calicut, True), ("ADEN · RED SEA", aden, False), ("CAIRO · ALEXANDRIA", cairo, False), ("VENICE", venice, False), ("BRUGES · NORTHERN EUROPE", bruges, False)]
cuts = ""
for i, (lo, la) in enumerate(stops[1:-1]):
    x, y = onpage(P, lo, la); s = .3 + i * .14
    cuts += handtag(x + 26, y + 18, "+ cut", -4 + i * 3, f"pop {s:.2f} {s + .04:.2f}", RED, "#FFF", 34)
x0, y0 = onpage(P, *calicut); x4, y4 = onpage(P, *bruges)
put("13a_relay", page(
    sheet(P, "")
    + string(P, route, "draw .05 .72")
    + pins(P, stops, .04, .15)
    + "".join(label(P, lo, la, n, left=lf, anim=f"fade {.06 + i * .15:.2f} {.1 + i * .15:.2f}") for i, (n, (lo, la), lf) in enumerate(legs))
    + cuts
    + A(f'<div style="background:{SIG};color:{INK};font:400 46px Anton;padding:6px 16px;box-shadow:6px 6px 0 rgba(0,0,0,.35)">~3 DUCATS</div>', x0 - 250, y0 - 100, "slam .1 .13", "z-index:35")
    + A(f'<div style="background:{INK};color:{SIG};font:400 46px Anton;padding:6px 16px;box-shadow:6px 6px 0 rgba(0,0,0,.35)">~80 DUCATS</div>', x4 + 10, y4 - 100, "slam .76 .79", "z-index:35")
    + A(f'<div style="background:{INK};color:{PARCH};padding:16px 24px;box-shadow:8px 8px 0 rgba(0,0,0,.35)"><div style="font:400 66px/1.15 Anton">THE WORLD\'S LONGEST {blk("RELAY RACE")}</div>'
        f'<div style="font:500 18px Plex;letter-spacing:3px;margin-top:14px;color:#CFC6B4">ONE HUNDREDWEIGHT OF PEPPER · 15TH CENTURY · UNESCO ESTIMATE</div></div>', 110, 760, "up 0 .1", "z-index:36")
    + A(f'<div style="background:{PARCH};color:{INK};border:2px solid {INK};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;transform:rotate(1.5deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">EVERY RUNNER CHARGES FOR THE BATON</div>', 1240, 200, "snap .86 .86", "z-index:70")
    + chapter(5, "THE MARKUP"),
    "#2A1D12", "PRICES: ~3 DUCATS (CALICUT) AND ~80 (EUROPE) PER HUNDREDWEIGHT, 15TH C. (UNESCO SILK ROADS, 'THE ARAB MONOPOLY', ESTIMATE) · NO MIDDLE PRICES SHOWN: '+ CUT' MARKS EACH HAND-OFF · ROUTE AND PORTS PLACED BY HAND, APPROXIMATE · " + GEO_SRC, dark=True))

# ---- 13b: the shortcut: the relay is bypassed (4 · 5:06–5:10) --------------------------------------------------------
P2 = Proj(-28, 96, -42, 56, SW, SH)
lisbon, cape = (-9.14, 38.72), (18.47, -34.36)
sea = [lisbon, (-17.0, 28.0), (-19.0, 14.0), (-10.0, 2.0), (-2.0, -12.0), (6.0, -24.0), (14.5, -33.5), (19.5, -36.2), (27.0, -35.0),
       (35.0, -28.0), (41.0, -17.0), (42.5, -5.0), (40.1, -3.2), (52.0, 4.0), (64.0, 9.0), calicut]
x_l, y_l = onpage(P2, *lisbon); x_v, y_v = onpage(P2, *venice); x_c, y_c = onpage(P2, *cape)
put("13b_shift", page(
    sheet(P2, "")
    + string(P2, route, "draw 0 .25", "#3A3F4B", 6)
    + f'<div class="a" data-anim="fade .3 .42" style="left:0;top:0;width:1920px;height:1080px;z-index:30"><svg width="1920" height="1080" style="display:block"><path d="{wobble(x_v + 10, y_v + 20, 170, 62, 3)}" fill="none" stroke="{RED}" stroke-width="5"/></svg></div>'
    + A(f'<div style="border:6px solid {RED};color:{RED};font:400 54px/1 Anton;letter-spacing:5px;padding:4px 18px;transform:rotate(-8deg);background:rgba(244,239,230,.85)">BYPASSED</div>', x_v + 170, y_v + 10, "slam .4 .43", "z-index:36")
    + string(P2, sea, "draw .45 .9", RED, 7)
    + pins(P2, [lisbon, cape, calicut, venice], .02, .03)
    + label(P2, *lisbon, "LISBON", left=True) + label(P2, *calicut, "CALICUT") + label(P2, *cape, "CAPE OF GOOD HOPE", dy=14) + label(P2, *venice, "VENICE", dy=-48)
    + handtag(max(30, x_l - 260), y_l + 100, "Casa da Índia,<br>Lisbon, c. 1500", -3, "drop .9 .96", PARCH, INK, 36).replace("white-space:nowrap", "line-height:1.05")
    + A(f'<div style="background:{INK};color:{PARCH};padding:16px 24px;box-shadow:8px 8px 0 rgba(0,0,0,.35)"><div style="font:400 62px/1.15 Anton">WHAT IF YOU {blk("SKIPPED THE RELAY?")}</div>'
        f'<div style="font:500 18px Plex;letter-spacing:3px;margin-top:14px;color:#CFC6B4">BY SEA, ROUND AFRICA · GAMA REACHES CALICUT, 20 MAY 1498</div></div>', 980, 820, "up .02 .12", "z-index:36")
    + a(f'<div style="background:{INK};color:{PARCH};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER 6 · THE SHORTCUT</div>', 70, 60, "z-index:40"),
    "#2A1D12", "OLD ROUTE: AS IN CHAPTER 5 (UNESCO; LANE 1968) · NEW ROUTE: GAMA 1497–98, THROUGH WAYPOINTS, APPROXIMATE (FORDHAM MODERN SOURCEBOOK) · CASA DA ÍNDIA c. 1500 (INFOPÉDIA) · " + GEO_SRC, dark=True))

# ---- 15a: who grows it now, on the world map (5 · 6:46) --------------------------------------------------------------
P3 = Proj(-120, 160, -62, 82, SW, SH)
# (name, thousand tonnes, growing region (pin), circle centre (offset into open sea where circles would overlap))
prod = [("VIETNAM", 257, (107.8, 14.5), (118.0, 24.0)), ("BRAZIL", 126.5, (-47.0, -10.0), (-28.0, -12.0)),
        ("INDONESIA", 70.2, (105.0, -5.0), (98.0, -14.0)), ("INDIA (FAO)", 65.7, (75.8, 13.0), (64.0, 6.0))]
bubbles = ""
for i, (n, v, (plo, pla), (lo, la)) in enumerate(prod):
    x, y = onpage(P3, lo, la); px, py = onpage(P3, plo, pla); r = math.sqrt(v) * 6.5; s = .1 + i * .16
    if (lo, la) != (plo, pla):
        bubbles += (f'<svg class="a" data-anim="draw {s:.2f} {s + .05:.2f}" style="left:0;top:0;z-index:32" width="1920" height="1080">'
                    f'<path d="M{px:.0f} {py:.0f} L{x:.0f} {y:.0f}" pathLength="1" fill="none" stroke="{INK}" stroke-width="3"/></svg>')
    bubbles += f'<svg class="a" data-anim="pop {s - .04:.2f} {s:.2f}" style="left:{px - 16:.0f}px;top:{py - 16:.0f}px;z-index:34" width="32" height="32" viewBox="{px - 16:.0f} {py - 16:.0f} 32 32">{pinsvg(px, py, 11)}</svg>'
    bubbles += A(f'<div style="width:{2 * r:.0f}px;height:{2 * r:.0f}px;border-radius:50%;background:{SIG if i == 0 else "rgba(58,63,75,.9)"};border:3px solid {INK};box-sizing:border-box;'
                 f'display:flex;align-items:center;justify-content:center;font:400 {40 if i == 0 else 26}px Anton;color:{INK if i == 0 else "#F3EFE6"}">{v:.0f}k t</div>',
                 x - r, y - r, f"pop {s:.2f} {s + .1:.2f}", "z-index:33")
    left = n == "INDIA (FAO)"
    bubbles += A(f'<div style="background:{PARCH};padding:4px 10px;font:500 18px Plex;letter-spacing:3px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35);white-space:nowrap;{"transform:translateX(-100%)" if left else ""}">{n}</div>',
                 (x - r - 12) if left else (x + r + 12), y - 14, f"fade {s + .06:.2f} {s + .1:.2f}", "z-index:34")
xi, yi = onpage(P3, 76.0, 15.5)
put("15a_world", page(
    sheet(P3, "") + bubbles
    + A(f'<div style="background:{INK};color:{PARCH};padding:16px 24px;box-shadow:8px 8px 0 rgba(0,0,0,.35)"><div style="font:400 66px/1.15 Anton">WHO GROWS IT {blk("NOW")}</div>'
        f'<div style="font:500 18px Plex;letter-spacing:3px;margin-top:14px;color:#CFC6B4">BLACK PEPPER · TONNES, 2023 · CIRCLE AREA ∝ TONNES</div></div>', 110, 130, "up 0 .1", "z-index:36")
    + A(f'<div style="width:500px;background:{PARCH};padding:20px 24px;box-shadow:0 18px 30px rgba(0,0,0,.5);transform:rotate(-2deg)">'
        f'<div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">INSIDE INDIA · SPICES BOARD, 2023-24</div>'
        f'<div style="font:400 48px/1.05 Anton;color:{INK};margin-top:8px">KARNATAKA ~71%<br>KERALA ~22%</div>'
        f'<div style="font:700 30px Caveat;color:#7A2A20">pepper began in Kerala. Karnataka grows most now.</div></div>', 690, 770, "up .78 .88", "z-index:37")
    + A(f'<div style="background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;transform:rotate(1.5deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">FAO vs SPICES BOARD · THE SOURCES DIFFER</div>', 1240, 960, "snap .9 .9", "z-index:70")
    + chapter(8, "PEPPER TODAY"),
    "#2A1D12", "WORLD: FAO (ITEM 0687) VIA TRIDGE, 2023 · INDIA: SPICES BOARD (125,000 t, 2023-24); FAO GIVES ~66,000 t: THE SOURCES DIFFER · CIRCLES PLACED ON GROWING REGIONS, APPROXIMATE · " + GEO_SRC, dark=True))
print("maps ok")
