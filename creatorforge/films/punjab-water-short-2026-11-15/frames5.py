"""Four alternatives for beat 5 (NASA GRACE: 109 km3 of groundwater lost from north-west India, Aug 2002 - Oct 2008)."""
import math
from frames import page, a, put, kick, SIG, RED, NAVY, PAPER, INK, SAFE_TOP, maps

SRC = "DATA: RODELL, VELICOGNA &amp; FAMIGLIETTI, NATURE 460, 999–1002 (2009) · STUDY AREA: RAJASTHAN, PUNJAB, HARYANA, DELHI"

# 5B: the twin satellites over the region: an orbit line across a wide satellite view, the study area ringed
box = (40, 0, 110, 50)
P = lambda lo, la: ((lo - box[0]) / (box[2] - box[0]) * 1960 - 440, (box[3] - la) / (box[3] - box[1]) * 1400 + 300)
ind = "".join('<path d="M' + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + 'Z" fill="none" stroke="#fff" stroke-width="2" opacity=".8"/>'
              for r in maps._find("India")["rings"] if len(r) > 3)
cx, cy = P(74.5, 28.5)
orbit = f'<path d="M -40 {cy + 520:.0f} C 300 {cy + 300:.0f}, 700 {cy - 300:.0f}, 1120 {cy - 640:.0f}" fill="none" stroke="{SIG}" stroke-width="3" stroke-dasharray="10 12"/>'
sat = lambda x, y: (f'<g transform="translate({x},{y}) rotate(-38)"><rect x="-26" y="-12" width="52" height="24" fill="#D9DEE6" stroke="#333" stroke-width="2"/>'
                    f'<rect x="-70" y="-8" width="40" height="16" fill="#2F6FB5"/><rect x="30" y="-8" width="40" height="16" fill="#2F6FB5"/></g>')
put("05b_twins", page(a('<img src="/maps/asia.jpg" style="width:1960px;height:1400px;filter:brightness(.8) contrast(1.1)">', -440, 300)
                      + a(f'<svg width="1080" height="1920">{ind}{orbit}{sat(int(cx - 170), int(cy - 70))}{sat(int(cx - 60), int(cy - 170))}'
                          f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="120" fill="rgba(200,49,43,.25)" stroke="{RED}" stroke-width="5"/></svg>', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">TWO SATELLITES<br>WEIGHED THE WATER</div>', 70, SAFE_TOP)
                      + a(f'<div style="font:500 26px/1.5 Plex;color:#DDE6F0;width:900px">NASA\'s GRACE pair felt gravity change as the groundwater under north-west India drained away.</div>', 70, 470)
                      + a(f'<div style="background:{SIG};color:#111;padding:14px 22px"><div style="font:400 120px/1 Anton">−109 km³</div>'
                          f'<div style="font:500 22px Plex;letter-spacing:3px">AUG 2002 – OCT 2008</div></div>', 70, 1300)
                      + a(f'<div style="font:500 18px Plex;letter-spacing:2px;color:#ddd;width:360px">SATELLITES AND ORBIT DRAWN IN THE STUDIO, NOT TO SCALE</div>', 680, 1460),
                      "#02040A", SRC + " · IMAGERY: NASA BLUE MARBLE NG VIA GIBS · INDIA: OFFICIAL BOUNDARY", dark=True))

# 5C: scale: 109 km3 as one cube of water, 4.8 km a side, against Burj Khalifa (828 m), side view, to scale
s = 900 / 4777                     # px per metre: the cube is 900 px tall
cube_h, burj_h = 4777 * s, 828 * s
base = 1500
cube = (f'<rect x="90" y="{base - cube_h:.0f}" width="{cube_h:.0f}" height="{cube_h:.0f}" fill="#2F6FB5" opacity=".85"/>'
        f'<rect x="90" y="{base - cube_h:.0f}" width="{cube_h:.0f}" height="{cube_h:.0f}" fill="none" stroke="#9FD0FF" stroke-width="3"/>')
burj = (f'<path d="M1010 {base} L1016 {base - burj_h * .35:.0f} L1019 {base - burj_h * .7:.0f} L1021 {base - burj_h:.0f} L1023 {base - burj_h * .7:.0f} '
        f'L1026 {base - burj_h * .35:.0f} L1032 {base} Z" fill="#DDD"/>')
put("05c_cube", page(a(f'<svg width="1080" height="1920"><line x1="40" y1="{base}" x2="1060" y2="{base}" stroke="#888" stroke-width="3"/>{cube}{burj}</svg>', 0, 0)
                     + kick("109 km³ OF WATER, PILED UP", 70, SAFE_TOP, "#9AA0AA")
                     + a(f'<div style="font:400 92px/0.95 Anton;color:#F3EFE6;width:940px">A CUBE OF WATER<br>4.8 KM ON EACH SIDE</div>', 70, 260)
                     + a(f'<div style="font:400 64px/1 Anton;color:{SIG};text-align:center;width:{cube_h:.0f}px">4.8 km</div>', 90, base - cube_h / 2 - 40)
                     + a(f'<div style="font:500 20px/1.4 Plex;color:#ddd;width:120px;text-align:right">BURJ KHALIFA<br>828 m</div>', 900, base - burj_h - 70)
                     + a(f'<div style="font:500 24px/1.5 Plex;color:#C9CDD6;width:940px">That is how much groundwater north-west India lost in six years (Aug 2002 – Oct 2008), measured by NASA\'s GRACE satellites.</div>', 70, 1520 - 0, "display:none")
                     + a(f'<div style="font:700 44px Caveat;color:{SIG}">lost in six years</div>', 640, base + 14),
                     "#07080C", SRC + " · CUBE AND TOWER DRAWN TO THE SAME SCALE (CUBE EDGE = ∛109 km³ ≈ 4.78 km)", dark=True))

# 5D: the paper itself, as a citation card with the abstract's numbers highlighted
hl = lambda t: f'<span style="background:linear-gradient(transparent 52%,{SIG} 52%,{SIG} 92%,transparent 92%)">{t}</span>'
cite = (f'<div style="width:900px;background:#FBF9F3;padding:46px 50px;box-shadow:0 30px 60px rgba(0,0,0,.45);transform:rotate(-1.5deg)">'
        f'<div style="font:500 20px Plex;letter-spacing:4px;color:#8A7A5A">NATURE · VOL 460 · AUGUST 2009</div>'
        f'<div style="font:400 50px/1.15 Playfair;color:{INK};margin-top:16px">Satellite-based estimates of groundwater depletion in India</div>'
        f'<div style="font:500 22px Plex;color:#555;margin-top:14px">Rodell, Velicogna &amp; Famiglietti</div>'
        f'<div style="font:400 38px/1.45 Playfair;color:#333;margin-top:30px">Groundwater in Rajasthan, Punjab and Haryana, including Delhi, was being depleted at {hl("about 4 cm of water a year")}. '
        f'Between August 2002 and October 2008 the region lost {hl("109 km³")}.</div>'
        f'<div style="font:500 18px/1.5 Plex;color:#8A7A5A;margin-top:26px">Summary of the paper\'s abstract in our words; card laid out in the studio.</div></div>')
put("05d_paper", page(a('<img src="/maps/nw_india.jpg" style="width:1080px;height:1920px;object-fit:cover;filter:brightness(.45) saturate(.8) blur(2px)">', 0, 0)
                      + a(f'<div style="font:400 100px/0.95 Anton;color:#F3EFE6;width:940px">THE SCIENCE<br>SAYS IT TOO</div>', 70, SAFE_TOP)
                      + a(cite, 90, 560), "#000", SRC + " · BACKGROUND: NASA BLUE MARBLE NG VIA GIBS", dark=True))

# 5E: a layer of water peeling off the map: six 4 cm layers stacked = ~24 cm over four states
layers = "".join(f'<rect x="140" y="{1240 - i * 64}" width="800" height="52" rx="6" fill="#2F6FB5" opacity="{.35 + i * .1:.2f}"/>'
                 f'<text x="960" y="{1276 - i * 64}" font-family="Plex" font-size="22" fill="#333">YEAR {i + 1}</text>' for i in range(6))
put("05e_layers", page(kick("NASA GRACE · NORTH-WEST INDIA", 70, SAFE_TOP)
                       + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">4 CM OF WATER<br>GONE EVERY YEAR</div>', 70, 270)
                       + a('<img src="/maps/nw_india.jpg" style="width:800px;height:240px;object-fit:cover;border:6px solid #fff;box-shadow:0 20px 30px rgba(0,0,0,.3)">', 140, 1310)
                       + a(f'<svg width="1080" height="1920">{layers}</svg>', 0, 0)
                       + a(f'<div style="font:700 46px Caveat;color:{RED};width:820px">spread over four states, six years of it adds up to 109 km³</div>', 150, 650)
                       + a(f'<div style="font:500 18px Plex;color:#666;width:800px">Layers are a diagram: one layer = one year of loss (~4 cm water-equivalent, study average).</div>', 140, 1250 - 64 * 6 - 50),
                       PAPER, SRC + " · MAP: NASA BLUE MARBLE NG VIA GIBS"))
print("ok")
