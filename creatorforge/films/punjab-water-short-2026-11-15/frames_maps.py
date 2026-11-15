"""Map options for beat 1 (the statement) and beat 5 (NASA GRACE, NW India): satellite, 3D relief, paper map."""
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from frames import page, a, put, kick, SIG, RED, NAVY, PAPER, INK, SAFE_TOP, maps, relief, SRC25
import terrain
import mask as M

STATES = {s["n"]: s["r"] for s in json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/states.json"))["India"]}
STUDY = ["Rajasthan", "Punjab", "Haryana", "Delhi", "Chandigarh"]
INDIA = [r for r in maps._find("India")["rings"] if len(r) > 3]
SRC5 = "DATA: RODELL, VELICOGNA &amp; FAMIGLIETTI, NATURE 460, 999–1002 (2009): RAJASTHAN, PUNJAB, HARYANA, DELHI, AUG 2002 – OCT 2008"
S2 = "IMAGERY: SENTINEL-2 CLOUDLESS 2016 BY EOX (S2MAPS.EU), CONTAINS MODIFIED COPERNICUS SENTINEL DATA 2016, CC BY 4.0"


def proj(box, x0, y0, w, h):
    return lambda lo, la: (x0 + (lo - box[0]) / (box[2] - box[0]) * w, y0 + (box[3] - la) / (box[3] - box[1]) * h)


def path(rings, P, **st):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in st.items())
    return "".join('<path d="M' + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + f'Z" {attrs}/>' for r in rings if len(r) > 3)


stamp = (f'<div style="border:8px solid {RED};color:{RED};font:400 92px/1 Anton;letter-spacing:6px;padding:8px 26px;transform:rotate(-12deg);opacity:.92;background:rgba(243,238,223,.6)">OVERDRAWN</div>')
mini = lambda dark=False: (f'<div style="width:620px;background:{PAPER};padding:28px 34px;box-shadow:0 24px 50px rgba(0,0,0,.5);transform:rotate(-2deg)">'
                           f'<div style="font:500 18px Plex;letter-spacing:4px;color:#7A6A4A">STATEMENT OF ACCOUNT · 2025</div>'
                           + "".join(f'<div style="display:flex;justify-content:space-between;border-bottom:2px dashed #B9AE95;padding:12px 0;font:500 26px Plex;color:{INK}">'
                                     f'<span>{k}</span><span style="{st}">{v}</span></div>' for k, v, st in (
                                         ("Safe to draw", "16.80 BCM", ""), ("Drawn", "26.27 BCM", f"color:{RED}"),
                                         ("Share used", "156.36 %", f"background:linear-gradient(transparent 50%,{SIG} 50%,{SIG} 92%,transparent 92%)")))
                           + '<div style="font:500 15px Plex;color:#7A6A4A;margin-top:12px">Figures: 2025 national assessment · layout: studio</div></div>')

# ---- beat 1 options ---------------------------------------------------------------------------------------------------
# 1B: sharp satellite of Punjab's fields, the state outlined, the statement pinned on it
box = (73.6, 29.4, 77.2, 32.7)
P = proj(box, -300, 0, 1680, 1920)
put("01b_sat", page(a('<img src="/maps/s2_punjab.jpg" style="width:1680px;height:1920px;filter:saturate(1.05) contrast(1.08) brightness(.82)">', -300, 0)
                    + a(f'<svg width="1080" height="1920">{path(STATES["Punjab"], P, fill="rgba(200,49,43,.18)", stroke="#FFFFFF", stroke_width=5)}</svg>', 0, 0)
                    + a(f'<div style="font:400 104px/0.95 Anton;color:#F3EFE6;width:940px;text-shadow:0 4px 20px rgba(0,0,0,.6)">PUNJAB\'S WATER<br>BANK STATEMENT</div>', 70, SAFE_TOP)
                    + a(mini(), 120, 980) + a(stamp, 470, 1310)
                    + a(f'<div style="background:#111;color:{SIG};font:500 20px Plex;letter-spacing:3px;padding:6px 12px">PUNJAB · FROM SPACE</div>', 70, 470),
                    "#000", SRC25 + " · " + S2 + " · STATE BOUNDARY: NATURAL EARTH", dark=True))

# 1C: a paper map of India (official boundary), Punjab in red with the stamp on it
box = (67, 6, 98, 37.5)
P = proj(box, 40, 380, 1000, 1016)
lines = "".join(f'<div style="position:absolute;left:0;right:0;top:{y}px;border-top:1px solid #D7CDB4"></div>' for y in range(0, 1920, 58))
put("01c_paper", page(a(lines, 0, 0, "width:1080px;height:1920px")
                      + a(f'<svg width="1080" height="1920">{path(INDIA, P, fill="#E6DCC4", stroke="#5A4A2A", stroke_width=2.5)}'
                          f'{path(STATES["Punjab"], P, fill=RED, stroke="#7A1A15", stroke_width=2)}'
                          f'<path d="M{P(75.4, 31.0)[0]:.0f} {P(75.4, 31.0)[1]:.0f} L 760 520" stroke="{RED}" stroke-width="4"/></svg>', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">PUNJAB\'S WATER<br>BANK STATEMENT</div>', 70, SAFE_TOP)
                      + a(f'<div style="font:700 50px Caveat;color:{RED}">Punjab</div>', 770, 480)
                      + a(mini(), 400, 1080) + a(stamp, 140, 1360),
                      PAPER, SRC25 + " · MAP: INDIA, OFFICIAL BOUNDARY; STATE: NATURAL EARTH"))

# 1D: Punjab glowing red on real terrain, the statement over it
card = lambda t, s: (f'<div style="background:#EFE6D2;padding:8px 14px;box-shadow:0 12px 20px rgba(0,0,0,.6);text-align:center">'
                     f'<div style="font:400 30px/1 Anton;color:#141414">{t}</div><div style="font:500 13px Plex;letter-spacing:3px;color:#7A2A20;margin-top:4px">{s}</div></div>')
cfg = {"exag": 5, "base": "#24282E", "hot": "#C8312B", "peak": "#FF8A7A", "grid": "#3A1010", "line": "#FFFFFF", "fog": [140, 320], "bg": "#05060A",
       "bloom": [0.55, 0.4, 0.6], "glow": 0.9, "cam": [0, 130, 110], "look": [0, 0, 6], "fov": 34, "route": [],
       "pins": [{"lon": 75.85, "lat": 30.9, "html": card("LUDHIANA", "PUNJAB")}, {"lon": 74.87, "lat": 31.63, "html": card("AMRITSAR", "PUNJAB")}],
       "overlay": f'<div style="position:absolute;left:70px;top:{SAFE_TOP}px;font:400 104px/0.95 Anton;color:#F3EFE6;width:940px">PUNJAB\'S WATER<br>BANK STATEMENT</div>'
                  f'<div style="position:absolute;left:120px;top:1060px">{mini()}</div><div style="position:absolute;left:470px;top:1380px">{stamp}</div>'
                  f'<div style="position:absolute;left:40px;right:40px;top:1590px;font:500 17px/1.5 Plex;letter-spacing:1px;color:rgba(255,255,255,.6)">{SRC25} · '
                  f'TERRAIN: TERRARIUM TILES (SRTM), HEIGHTS EXAGGERATED 5× · STATE BOUNDARY: NATURAL EARTH</div>'}
put("01d_relief", relief.page("punjab", cfg).replace("1920", "__W__").replace("1080", "1920").replace("__W__", "1080"))

# ---- beat 5 options ---------------------------------------------------------------------------------------------------
# 5F: sharp satellite of NW India, the four states of the study outlined
box = (68.0, 22.5, 80.0, 33.5)
P = proj(box, -160, 260, 1400, 1440)
study = "".join(path(STATES[n], P, fill="rgba(47,111,181,.28)", stroke="#9FD0FF", stroke_width=4) for n in STUDY)
labs = "".join(a(f'<div style="background:rgba(0,0,0,.65);color:#DDEEFF;font:500 20px Plex;letter-spacing:3px;padding:4px 10px">{n.upper()}</div>', P(lo, la)[0] - 60, P(lo, la)[1])
               for n, lo, la in (("Rajasthan", 73.6, 26.6), ("Punjab", 75.2, 30.9), ("Haryana", 76.2, 29.3)))
put("05f_sat", page(a('<img src="/maps/s2_nwindia.jpg" style="width:1400px;height:1440px;filter:contrast(1.08) brightness(.8)">', -160, 260)
                    + a(f'<svg width="1080" height="1920">{path(INDIA, P, fill="none", stroke="#FFFFFF", stroke_width=2.5, opacity=.8)}{study}</svg>', 0, 0) + labs
                    + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px;text-shadow:0 4px 20px #000">WHERE THE<br>WATER WENT</div>', 70, SAFE_TOP)
                    + a(f'<div style="background:{SIG};color:#111;padding:12px 20px"><div style="font:400 110px/1 Anton">−109 km³</div>'
                        f'<div style="font:500 20px Plex;letter-spacing:3px">NASA GRACE · AUG 2002 – OCT 2008</div></div>', 70, 1360),
                    "#000", SRC5 + " · " + S2 + " · INDIA: OFFICIAL BOUNDARY; STATES: NATURAL EARTH", dark=True))

# 5G: the study area glowing blue on real terrain
if not (Path("maps") / "nwindia_h.json").is_file():
    terrain.heights("nwindia", (68.5, 22.8, 79.8, 33.2), 7)
m = json.loads(Path("maps/nwindia_h.json").read_text())
im = Image.new("L", (m["w"], m["h"]), 0); d = ImageDraw.Draw(im)
for n in STUDY:
    for r in STATES[n]:
        d.polygon([(u * m["w"], v * m["h"]) for u, v in (M.uv("nwindia", lo, la) for lo, la in r)], fill=255)
im.save("maps/nwindia_mask.png")
cfg = {"exag": 4, "base": "#202530", "hot": "#2F8BFF", "peak": "#BFE3FF", "grid": "#0E2050", "line": "#FFFFFF", "fog": [140, 340], "bg": "#04060C",
       "bloom": [0.55, 0.4, 0.6], "glow": 0.9, "cam": [0, 175, 120], "look": [0, 0, 14], "fov": 34, "route": [],
       "pins": [{"lon": 73.5, "lat": 26.8, "html": card("RAJASTHAN", "STUDY AREA")},
                {"lon": 77.2, "lat": 28.6, "html": card("DELHI", "STUDY AREA")}],
       "overlay": f'<div style="position:absolute;left:70px;top:{SAFE_TOP}px;font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">109 km³<br>GONE IN SIX YEARS</div>'
                  f'<div style="position:absolute;left:70px;top:1400px;background:rgba(5,15,30,.85);border:2px solid #2F6FB5;padding:14px 22px;font:500 24px/1.5 Plex;color:#CFE6FF">'
                  f'NASA GRACE · AUG 2002 – OCT 2008<br>study area lit in blue: Rajasthan, Punjab,<br>Haryana and Delhi</div>'
                  f'<div style="position:absolute;left:40px;right:40px;top:1590px;font:500 17px/1.5 Plex;letter-spacing:1px;color:rgba(255,255,255,.6)">{SRC5} · '
                  f'TERRAIN: TERRARIUM TILES (SRTM), HEIGHTS EXAGGERATED 4× · STATES: NATURAL EARTH</div>'}
put("05g_relief", relief.page("nwindia", cfg).replace("1920", "__W__").replace("1080", "1920").replace("__W__", "1080"))

# 5H: paper India map, the study area hatched in water blue
box = (67, 6, 98, 37.5)
P = proj(box, 40, 380, 1000, 1016)
hatch = '<defs><pattern id="h" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="14" fill="#BFD9F2"/><line x1="0" y1="0" x2="0" y2="14" stroke="#2F6FB5" stroke-width="6"/></pattern></defs>'
put("05h_paper", page(a(lines, 0, 0, "width:1080px;height:1920px")
                      + a(f'<svg width="1080" height="1920">{hatch}{path(INDIA, P, fill="#E6DCC4", stroke="#5A4A2A", stroke_width=2.5)}'
                          + "".join(path(STATES[n], P, fill="url(#h)", stroke=NAVY, stroke_width=2) for n in STUDY) + '</svg>', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">NASA WEIGHED<br>THE WATER</div>', 70, SAFE_TOP)
                      + a(f'<div style="font:700 48px Caveat;color:#2F6FB5;width:420px">−4 cm of water a year, across these four states</div>', 600, 700)
                      + a(f'<div style="background:{NAVY};color:{SIG};padding:12px 20px"><div style="font:400 100px/1 Anton">−109 km³</div>'
                          f'<div style="font:500 20px Plex;letter-spacing:3px;color:#fff">AUG 2002 – OCT 2008</div></div>', 520, 1250),
                      PAPER, SRC5 + " · MAP: INDIA, OFFICIAL BOUNDARY; STATES: NATURAL EARTH"))
print("ok")
