"""River options: the five rivers of the Punjab (Jhelum, Chenab, Ravi, Beas, Sutlej) drawn on, three looks, each
rendered at three moments of the animation (35%, 70%, 100%). Rivers: Natural Earth 10m centerlines (public domain)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
from frames import page, a, put, SIG, RED, NAVY, PAPER, INK, SAFE_TOP, maps, relief, SRC25
import mask as M

R = json.load(open("data/rivers.json"))["rivers"]
FIVE = ["Jhelum", "Chenab", "Ravi", "Beas", "Sutlej"]
STATES = {s["n"]: s["r"] for s in json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/states.json"))["India"]}
WORLD = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/world.json"))
INDIA = [r for r in maps._find("India")["rings"] if len(r) > 3]
BOX = (71.2, 29.0, 77.4, 34.6)
LABEL = {"Jhelum": (73.3, 33.4), "Chenab": (74.3, 32.75), "Ravi": (74.9, 32.2), "Beas": (76.0, 31.85), "Sutlej": (75.4, 30.9)}
SRCR = "RIVERS: NATURAL EARTH 10M CENTERLINES (PUBLIC DOMAIN) · 'PUNJAB' = 'FIVE WATERS' (PERSIAN PANJ + ĀB)"
S2 = "IMAGERY: SENTINEL-2 CLOUDLESS 2016 BY EOX (S2MAPS.EU), CONTAINS MODIFIED COPERNICUS SENTINEL DATA 2016, CC BY 4.0"
STAGES = (0.35, 0.7, 1.0)


def P(x0, y0, w, h):
    return lambda lo, la: (x0 + (lo - BOX[0]) / (BOX[2] - BOX[0]) * w, y0 + (BOX[3] - la) / (BOX[3] - BOX[1]) * h)


def ring_path(rings, p, **st):
    attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in st.items())
    return "".join('<path d="M' + " L".join("%.1f %.1f" % p(lo, la) for lo, la in r) + f'Z" {attrs}/>' for r in rings if len(r) > 3)


def river_paths(p, prog, col, w, glow=True, stagger=.12):
    """Each river draws on in turn; stroke-dashoffset gives the partial line."""
    out, labs = "", ""
    for i, n in enumerate(FIVE):
        t = max(0.0, min(1.0, (prog - i * stagger) / (1 - stagger * (len(FIVE) - 1)) if prog < 1 else 1.0))
        for line in R[n]:
            d = "M" + " L".join("%.1f %.1f" % p(lo, la) for lo, la in line)
            if glow:
                out += f'<path d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1 - t:.3f}" fill="none" stroke="{col}" stroke-width="{w * 3.2}" opacity=".35" filter="url(#bl)"/>'
            out += f'<path d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1 - t:.3f}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
        if t >= .95:
            labs += n
    return out, labs


def labels(p, shown, style):
    return "".join(a(f'<div style="{style}">{n.upper()}</div>', p(*LABEL[n])[0] - 50, p(*LABEL[n])[1] - 18) for n in FIVE if n in shown)


DEFS = '<defs><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter></defs>'

for k, prog in enumerate(STAGES):
    tag = "abc"[k]
    # RA: satellite, the rivers glow on in turn, Punjab (India) outlined, the overdraft punchline lands at the end
    p = P(0, 330, 1080, 1148)
    rv, shown = river_paths(p, prog, "#5EC8FF", 5)
    end = prog >= 1.0
    put(f"ra_{tag}", page(a('<img src="/maps/s2_rivers.jpg" style="width:1080px;height:1148px;filter:brightness(.72) contrast(1.1) saturate(.9)">', 0, 330)
                         + a(f'<svg width="1080" height="1920">{DEFS}<clipPath id="k"><rect x="0" y="330" width="1080" height="1148"/></clipPath><g clip-path="url(#k)">{ring_path(INDIA, p, fill="none", stroke="#FFFFFF", stroke_width=2, opacity=.55)}'
                             f'{ring_path(STATES["Punjab"], p, fill="rgba(200,49,43,.16)" if end else "none", stroke="#FFFFFF", stroke_width=4)}{rv}</g></svg>', 0, 0)
                         + labels(p, shown, "background:rgba(0,0,0,.65);color:#BFE8FF;font:500 20px Plex;letter-spacing:3px;padding:3px 8px")
                         + a(f'<div style="font:400 104px/0.95 Anton;color:#F3EFE6;width:940px">THE LAND OF<br>FIVE RIVERS</div>', 70, SAFE_TOP)
                         + (a(f'<div style="background:{RED};color:#fff;padding:14px 22px;transform:rotate(-2deg)"><div style="font:400 72px/1 Anton">AND STILL IN THE RED</div>'
                              f'<div style="font:500 22px Plex;letter-spacing:3px;color:#FFE3E0;margin-top:6px">PUMPS 156% OF ITS SAFE GROUNDWATER LIMIT</div></div>', 70, 1400) if end else ""),
                         "#000", SRC25 + " · " + SRCR + " · " + S2 + " · INDIA: OFFICIAL BOUNDARY", dark=True))

    # RB: 3D relief, rivers as glowing tubes growing downstream, Punjab (India) lit
    rel = {"exag": 6, "base": "#1C2026", "hot": "#8A2A24", "peak": "#C9A27A", "grid": "#10202C", "line": "#7FD4FF", "fog": [150, 330], "bg": "#03050A",
           "bloom": [0.35, 0.3, 0.7], "glow": 0.6, "cam": [0, 125, 95], "look": [0, 0, 4], "fov": 34, "route": [], "pins": [],
           "overlay": f'<div style="position:absolute;left:0;top:0;width:1080px;height:560px;background:linear-gradient(#03050A 55%,transparent)"></div><div style="position:absolute;left:70px;top:{SAFE_TOP}px;font:400 104px/0.95 Anton;color:#F3EFE6;width:940px">FIVE RIVERS<br>ON THE SURFACE</div>'
                      + (f'<div style="position:absolute;left:70px;top:1380px;background:{SIG};color:#111;padding:12px 20px;font:400 60px/1.05 Anton;width:880px">'
                         f'BUT THE BANK IS<br>UNDERGROUND</div>' if prog >= 1 else "")
                      + f'<div style="position:absolute;left:0;right:0;top:1574px;padding:16px 40px;background:linear-gradient(transparent,rgba(0,0,0,.78) 30%);'
                        f'font:500 17px/1.5 Plex;letter-spacing:1px;color:rgba(255,255,255,.62)">{SRCR} · TERRAIN: TERRARIUM TILES (SRTM), HEIGHTS EXAGGERATED 6× · '
                        f'PUNJAB (INDIA) LIT · STATE: NATURAL EARTH</div>'}
    html = relief.page("rivers5", rel)
    tubes = []
    for i, n in enumerate(FIVE):
        t = max(0.0, min(1.0, (prog - i * .12) / .52 if prog < 1 else 1.0))
        for line in R[n]:
            pts = line[:max(2, int(len(line) * t))] if t > 0 else []
            if len(pts) >= 2:
                tubes.append([M.uv("rivers5", lo, la) for lo, la in pts])
    js = ("for(const L of " + json.dumps(tubes) + "){const pts=L.map(([u,v])=>at(u,v,.5));"
          "if(pts.length<2)continue;const cur=new THREE.CatmullRomCurve3(pts);"
          "S.add(new THREE.Mesh(new THREE.TubeGeometry(cur,Math.max(8,pts.length*3),.16,8),new THREE.MeshBasicMaterial({color:new THREE.Color('#7FD4FF').multiplyScalar(1.5)})))}\n")
    html = html.replace("const cam=new THREE.PerspectiveCamera", js + "const cam=new THREE.PerspectiveCamera", 1)
    put(f"rb_{tag}", html.replace("1920", "__W__").replace("1080", "1920").replace("__W__", "1080"))

    # RC: ink map on paper, rivers inked in, the Indian Punjab shaded, labels handwritten
    p = P(40, 360, 1000, 903)
    pak = next(c for c in WORLD["countries"] if c["n"] == "Pakistan")
    pak_r = pak["r"] if isinstance(pak["r"], list) else json.loads(pak["r"])
    rv, shown = river_paths(p, prog, "#2F6FB5", 4.5, glow=False)
    lines_bg = "".join(f'<div style="position:absolute;left:0;right:0;top:{y}px;border-top:1px solid #D7CDB4"></div>' for y in range(0, 1920, 58))
    put(f"rc_{tag}", page(a(lines_bg, 0, 0, "width:1080px;height:1920px")
                         + a(f'<svg width="1080" height="1920"><clipPath id="c"><rect x="40" y="360" width="1000" height="903"/></clipPath><g clip-path="url(#c)">'
                             f'{ring_path(pak_r, p, fill="#EDE6D3", stroke="#9A8A6A", stroke_width=2)}{ring_path(INDIA, p, fill="#E6DCC4", stroke="#5A4A2A", stroke_width=3)}'
                             f'{ring_path(STATES["Punjab"], p, fill="#E9B8A8", stroke=RED, stroke_width=3)}{rv}</g>'
                             f'<rect x="40" y="360" width="1000" height="903" fill="none" stroke="{INK}" stroke-width="3"/></svg>', 0, 0)
                         + labels(p, shown, "font:700 36px Caveat;color:#1F4E8C")
                         + a(f'<div style="font:400 100px/0.95 Anton;color:{NAVY};width:940px">PANJ + ĀB =<br>FIVE WATERS</div>', 70, SAFE_TOP - 10)
                         + a(f'<div style="font:700 44px Caveat;color:{RED};transform:rotate(-2deg)">Punjab (India)</div>', 620, 1140)
                         + (a(f'<div style="font:700 52px/1.15 Caveat;color:{INK};width:900px">Rivers on top. The real withdrawals happen below, from groundwater.</div>', 70, 1320) if prog >= 1 else ""),
                         PAPER, SRCR + " · MAP: INDIA, OFFICIAL BOUNDARY; OTHER BORDERS AND PUNJAB: NATURAL EARTH"))
print("ok")
