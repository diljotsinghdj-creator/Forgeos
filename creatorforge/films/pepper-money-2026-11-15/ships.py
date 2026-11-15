"""Moving-ship maps, each at three moments of the voyage (start / middle / end):
  S1 Roman monsoon voyage, Berenike -> Muziris and back (chapter 2), on the 1596 chart
  S2 the markup voyage, Calicut -> Red Sea -> Alexandria -> on to Venice (chapter 5), price tags ticking
  S3 Vasco da Gama, Lisbon -> round Africa -> Calicut (chapter 6), on the globe with a date counter
Ships are drawn in the studio (simple silhouettes, not to scale); pins and routes placed by hand, approximate."""
import math
from frames import page, a, put, chapter, logo_d, FONTS, SIG, RED, INK, PARCH, DESK

S, OX, OY = 1.25, -40, -312            # chart grid (1600 x 1181) -> screen
G = lambda gx, gy: (gx * S + OX, gy * S + OY)
SRC_MAP = "MAP: LINSCHOTEN, 1596, LIBRARY OF CONGRESS (PUBLIC DOMAIN BY AGE) · ROUTES, PORTS AND SHIP PLACED BY HAND, APPROXIMATE · SHIP DRAWN IN THE STUDIO, NOT TO SCALE"


def ship(scale=1.0, flag=None, cargo=False):
    w = 120 * scale
    cross = f'<path d="M56 22 L56 50 M44 34 L68 34" stroke="{RED}" stroke-width="5"/>' if flag == "cross" else ""
    sacks = '<rect x="30" y="72" width="16" height="12" rx="3" fill="#7A5A2A"/><rect x="50" y="70" width="16" height="14" rx="3" fill="#8C6A35"/><rect x="70" y="72" width="16" height="12" rx="3" fill="#7A5A2A"/>' if cargo else ""
    return (f'<svg width="{w:.0f}" height="{w:.0f}" viewBox="0 0 120 120" style="filter:drop-shadow(0 6px 6px rgba(0,0,0,.5))">'
            f'<line x1="56" y1="10" x2="56" y2="84" stroke="#3A2614" stroke-width="4"/>'
            f'<path d="M30 18 Q 56 12 82 18 L 86 62 Q 56 56 26 62 Z" fill="#F1E6CC" stroke="#3A2614" stroke-width="3"/>{cross}'
            f'{sacks}<path d="M8 82 L112 82 L98 104 L22 104 Z" fill="#6B4423" stroke="#2A1A0C" stroke-width="3"/>'
            f'<path d="M4 110 Q 30 104 60 110 T 116 110" fill="none" stroke="#DDEBFF" stroke-width="3" opacity=".8"/></svg>')


def along(pts, t):
    """Point and heading at fraction t of a polyline."""
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]; L = sum(seg); d = t * L
    for (p, q), s in zip(zip(pts, pts[1:]), seg):
        if d <= s:
            f = d / s if s else 0
            return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f), math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        d -= s
    return pts[-1], 0


def sub(pts, t):
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]; L = sum(seg); d = t * L; out = [pts[0]]
    for (p, q), s in zip(zip(pts, pts[1:]), seg):
        if d <= s:
            f = d / s if s else 0; out.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)); return out
        out.append(q); d -= s
    return out


def path(pts):
    return "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)


def pin(x, y, label, side=1):
    return (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="12" fill="{RED}" stroke="#FFF" stroke-width="2"/>',
            a(f'<div style="background:{PARCH};padding:4px 10px;font:500 18px Plex;letter-spacing:3px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35);white-space:nowrap">{label}</div>',
              x + (18 if side > 0 else -18), y - 16, f"z-index:32;{'' if side > 0 else 'transform:translateX(-100%)'}"))


def chart_base():
    return (a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
            + a('<img src="/assets/chart.jpg" style="width:2000px;height:1476px;display:block;filter:sepia(.2) contrast(1.05) brightness(.92)">', OX, OY))


def wind(cx, cy, ang, n=5, col="#FFFFFF"):
    out = ""
    for i in range(n):
        x, y = cx + (i % 3) * 120 - 120, cy + (i // 3) * 110 - 40
        r = math.radians(ang); dx, dy = 70 * math.cos(r), 70 * math.sin(r)
        out += (f'<path d="M{x - dx:.0f} {y - dy:.0f} Q {x - dy * .25:.0f} {y + dx * .25:.0f} {x + dx:.0f} {y + dy:.0f}" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round" opacity=".85"/>'
                f'<path d="M{x + dx - 14 * math.cos(r - .5):.0f} {y + dy - 14 * math.sin(r - .5):.0f} L{x + dx:.0f} {y + dy:.0f} L{x + dx - 14 * math.cos(r + .5):.0f} {y + dy - 14 * math.sin(r + .5):.0f}" fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round"/>')
    return out


# ---- S1: the Roman monsoon voyage -----------------------------------------------------------------------------------
berenike, bab, aden, sea1, muziris = G(265, 480), G(410, 808), G(560, 835), G(850, 870), G(1105, 830)
out_route = [berenike, G(330, 640), bab, aden, sea1, muziris]
for tag, t, home in (("a", .12, False), ("b", .6, False), ("c", .45, True)):
    route = out_route[::-1] if home else out_route
    (x, y), hd = along(route, t)
    flip = "scaleX(-1)" if math.cos(math.radians(hd)) < 0 else ""
    p1, l1 = pin(*berenike, "BERENIKE · RED SEA PORT"); p2, l2 = pin(*muziris, "MUZIRIS", -1)
    svg = (f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080">'
           f'<path d="{path(out_route)}" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="10 10" opacity=".55"/>'
           f'<path d="{path(sub(route, t))}" fill="none" stroke="{RED}" stroke-width="6"/>{p1}{p2}'
           + wind(780, 760, -25 if not home else 155) + "</svg>")
    note = ("SUMMER · SOUTH-WEST MONSOON<br>blows ships to India" if not home else "WINTER · THE WIND TURNS<br>north-east monsoon blows them home")
    put(f"s1_{tag}", page(chart_base() + svg + l1 + l2
                          + a(ship(1.1, cargo=home), x - 66, y - 100, f"z-index:40;transform:{flip}")
                          + chapter(2, "ROME PAYS BY THE POUND")
                          + a(f'<div style="background:rgba(20,16,10,.82);padding:16px 22px;font:500 24px/1.5 Plex;letter-spacing:2px;color:#F3EFE6">{note}</div>', 1340, 120, "z-index:41")
                          + a(f'<div style="font:400 64px/1 Anton;color:#F3EFE6;text-shadow:0 4px 18px #000">RIDING THE MONSOON</div>', 70, 120, "z-index:41")
                          + (a(f'<div style="background:{SIG};color:{INK};padding:10px 16px;font:700 38px Caveat;transform:rotate(-3deg)">loaded with pepper</div>', x + 50, y - 150, "z-index:41") if home else ""),
                          "#2A1D12", "WINDS: THE MONSOON PATTERN THE ROMAN TRADE RELIED ON (WELL-ESTABLISHED; SEASONS SHOWN, NOT EXACT DATES) · " + SRC_MAP, dark=True))

# ---- S2: the markup voyage ------------------------------------------------------------------------------------------
calicut, alex, venice_edge = G(1095, 790), G(172, 336), G(60, 250)
red_n = G(300, 400)
m_route = [calicut, sea1, aden, bab, G(330, 640), red_n, alex, venice_edge]
stops = [(calicut, "CALICUT", "~3 ducats / cwt", 0.0), (bab, "RED SEA", "+ tolls, + freight", .42), (alex, "ALEXANDRIA → VENICE", "42 → 56 ducats per cargo (1497)", .86)]
for tag, t in (("a", .05), ("b", .45), ("c", .97)):
    (x, y), hd = along(m_route, t)
    flip = "scaleX(-1)" if math.cos(math.radians(hd)) < 0 else ""
    pins_svg, labels = "", ""
    for (px, py), name, price, at in stops:
        ps, lb = pin(px, py, name, -1 if name == "CALICUT" else 1)
        pins_svg += ps; labels += lb
        if t >= at:
            labels += a(f'<div style="background:{SIG};color:{INK};padding:6px 12px;font:700 34px Caveat;transform:rotate(-3deg);white-space:nowrap;box-shadow:0 6px 10px rgba(0,0,0,.35)">{price}</div>',
                        px + (-260 if name == "CALICUT" else 30), py + 22, "z-index:33")
    end = t > .9
    put(f"s2_{tag}", page(chart_base()
                          + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{path(m_route)}" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="10 10" opacity=".5"/>'
                            f'<path d="{path(sub(m_route, t))}" fill="none" stroke="{RED}" stroke-width="6"/>{pins_svg}</svg>' + labels
                          + a(ship(1.0, cargo=True), x - 60, y - 96, f"z-index:40;transform:{flip}")
                          + chapter(5, "THE MARKUP")
                          + a(f'<div style="font:400 64px/1 Anton;color:#F3EFE6;text-shadow:0 4px 18px #000">FOLLOW THE PRICE</div>', 70, 930, "z-index:41")
                          + (a(f'<div style="background:{RED};color:#fff;padding:14px 22px;transform:rotate(-2deg)"><div style="font:400 60px/1 Anton">EUROPE: ~80 DUCATS / CWT</div>'
                               f'<div style="font:500 18px Plex;letter-spacing:3px">~25× THE PRICE AT CALICUT (UNESCO ESTIMATE, 15TH C.)</div></div>', 1180, 820, "z-index:41") if end else "")
                          + (a(f'<div style="font:700 40px Caveat;color:{SIG};transform:rotate(-8deg)">→ on to Venice</div>', 60, 160, "z-index:41") if end else ""),
                          "#2A1D12", "PRICES: UNESCO SILK ROADS (PER HUNDREDWEIGHT, ESTIMATE); LANE, J. ECON. HISTORY 28 (1968), 1497, PER VENETIAN CARGO: DIFFERENT UNITS, SHOWN SEPARATELY · " + SRC_MAP, dark=True))

# ---- S3: Gama on the globe --------------------------------------------------------------------------------------------
from taxonomy import globe
WP = [(-9.14, 38.72), (-17.0, 14.0), (-5.0, -15.0), (18.47, -36.0), (37.5, -27.0), (42.0, -13.0), (40.1, -3.2), (75.78, 11.25)]
def gc_pts(a_, b_, n=40):
    toV = lambda lo, la: (math.cos(math.radians(la)) * math.cos(math.radians(lo)), math.cos(math.radians(la)) * math.sin(math.radians(lo)), math.sin(math.radians(la)))
    A, B = toV(*a_), toV(*b_); om = math.acos(max(-1, min(1, sum(p * q for p, q in zip(A, B)))))
    out = []
    for i in range(n + 1):
        f = i / n; k1 = math.sin((1 - f) * om) / math.sin(om); k2 = math.sin(f * om) / math.sin(om)
        v = [k1 * p + k2 * q for p, q in zip(A, B)]
        out.append((math.degrees(math.atan2(v[1], v[0])), math.degrees(math.asin(max(-1, min(1, v[2]))))))
    return out
dense = []
for p, q in zip(WP, WP[1:]):
    dense += gc_pts(p, q)[(1 if dense else 0):]
for tag, t, date, spin in (("a", .08, "JULY 1497 · LEAVING LISBON", -5), ("b", .5, "NOV 1497 · ROUNDING THE CAPE", 15), ("c", 1.0, "20 MAY 1498 · CALICUT", 55)):
    n = max(2, int(len(dense) * t)); part = dense[:n]; sx, sy = part[-1]
    shiplab = f'<div style="transform:translate(-60px,-70px)">{ship(.75, flag="cross")}</div>'
    g = globe(0.0, spin, part, [], "THE LONG WAY ROUND", "Vasco da Gama, 1497–98",
              "ROUTE APPROXIMATE, THROUGH WAYPOINTS · DATES: DEPARTURE JULY 1497, CAPE NOV 1497 (WELL-ESTABLISHED), ARRIVAL 20 MAY 1498 (MOST SOURCES) · IMAGERY: NASA BLUE MARBLE NG VIA GIBS · SHIP DRAWN IN THE STUDIO",
              labels=[(sx, sy, shiplab)] + ([(-9.14, 38.72, "LISBON")] if t < .6 else []) + ([(75.78, 11.25, "CALICUT")] if t >= 1 else []))
    g = g.replace("</body>", f'<style>{FONTS}</style><div style="position:absolute;right:56px;top:44px;z-index:90">{logo_d(1.0)}</div>'
                  f'<div style="position:absolute;left:90px;top:860px;z-index:20;background:{SIG};color:{INK};padding:12px 20px;font:400 52px/1 Anton">{date}</div>'
                  f'<div style="position:absolute;left:90px;top:22px;z-index:20;background:{INK};color:{PARCH};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER 6 · THE SHORTCUT</div></body>', 1)
    put(f"s3_{tag}", g)
print("ok")
