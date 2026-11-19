"""Motion upgrades for "Why India Is Mocked Online" (owner, 2026-11-17: "add all"). Each is tied to a fact in the film:
  globe_a/b/c   3D globe: the Company's sea route, London round the Cape to Calcutta, India outlined (official boundary)
  ship_a/b/c    a ship sails the 1596 Linschoten chart round Ceylon into the Bay of Bengal (Calcutta, 1690)
  relief_a/b/c  3D relief of India (official boundary lit), the four biodiversity hotspots it overlaps, camera push
  bars_a/b/c    glowing bars: police-reported hate crimes against South Asians in Canada, 2024 and 2025, rising
  z06_smash     1-frame smash-zoom (1 -> 1.32, no easing) on Macaulay's "I have no knowledge" line
  rivers        NASA Blue Marble of the Ganga plain with Natural Earth rivers flowing downstream to the Sundarbans
The globe, ship, relief and bars are baked at three moments (a/b/c); the rivers page uses the ?t= timeline."""
import json
import math
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/forgeos/creatorforge/films/taxonomy-2026-11-15")
sys.path.insert(0, "/home/user/forgeos/creatorforge/films/vox-tools-2026-11-15")
sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
from studio import page, A, a, put, hl, chapter, logo_d, FONTS, DESK, PARCH, RED, SIG, INK, H  # noqa: E402
from creatorforge_worker.media import maps  # noqa: E402

from india_shape import rings as india_rings, CREDIT as INDIA_CREDIT  # noqa: E402
INDIA = india_rings(40)
TAGCSS = f"background:{INK};color:{PARCH};border:2px solid {PARCH};padding:8px 14px;font:500 20px Plex;letter-spacing:4px;box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap"


def ship(scale=1.0, cargo=False):
    w = 120 * scale
    sacks = '<rect x="30" y="72" width="16" height="12" rx="3" fill="#7A5A2A"/><rect x="50" y="70" width="16" height="14" rx="3" fill="#8C6A35"/>' if cargo else ""
    return (f'<svg width="{w:.0f}" height="{w:.0f}" viewBox="0 0 120 120" style="filter:drop-shadow(0 6px 6px rgba(0,0,0,.5))">'
            f'<line x1="56" y1="10" x2="56" y2="84" stroke="#3A2614" stroke-width="4"/>'
            f'<path d="M30 18 Q 56 12 82 18 L 86 62 Q 56 56 26 62 Z" fill="#F1E6CC" stroke="#3A2614" stroke-width="3"/>'
            f'<rect x="58" y="6" width="22" height="12" fill="{RED}"/>{sacks}<path d="M8 82 L112 82 L98 104 L22 104 Z" fill="#6B4423" stroke="#2A1A0C" stroke-width="3"/>'
            f'<path d="M4 110 Q 30 104 60 110 T 116 110" fill="none" stroke="#DDEBFF" stroke-width="3" opacity=".8"/></svg>')


def along(pts, t):
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]; d = t * sum(seg)
    for (p, q), s in zip(zip(pts, pts[1:]), seg):
        if d <= s:
            f = d / s if s else 0
            return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f), math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        d -= s
    return pts[-1], 0


def sub(pts, t):
    seg = [math.dist(p, q) for p, q in zip(pts, pts[1:])]; d = t * sum(seg); out = [pts[0]]
    for (p, q), s in zip(zip(pts, pts[1:]), seg):
        if d <= s:
            f = d / s if s else 0; out.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)); return out
        out.append(q); d -= s
    return out


pathd = lambda pts: "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)


# ---- 1. the globe: London, round the Cape, to Calcutta -------------------------------------------------------------
from taxonomy import globe  # noqa: E402
WP = [(-0.13, 51.5), (-10.0, 45.0), (-17.0, 14.0), (-5.0, -15.0), (18.47, -36.0), (37.5, -27.0), (55.0, -10.0), (80.0, 4.0), (88.0, 15.0), (88.36, 22.57)]


def gc(a_, b_, n=40):
    toV = lambda lo, la: (math.cos(math.radians(la)) * math.cos(math.radians(lo)), math.cos(math.radians(la)) * math.sin(math.radians(lo)), math.sin(math.radians(la)))
    P, Q = toV(*a_), toV(*b_); om = math.acos(max(-1, min(1, sum(p * q for p, q in zip(P, Q)))))
    out = []
    for i in range(n + 1):
        f = i / n; k1 = math.sin((1 - f) * om) / math.sin(om); k2 = math.sin(f * om) / math.sin(om)
        v = [k1 * p + k2 * q for p, q in zip(P, Q)]
        out.append((math.degrees(math.atan2(v[1], v[0])), math.degrees(math.asin(max(-1, min(1, v[2]))))))
    return out


dense = []
for p, q in zip(WP, WP[1:]):
    dense += gc(p, q)[(1 if dense else 0):]
for tag, t, date, spin in (("a", .08, "1600 · THE EAST INDIA COMPANY IS CHARTERED", 0), ("b", .55, "ROUND THE CAPE OF GOOD HOPE", 25), ("c", 1.0, "1858 · THE CROWN TAKES OVER", 70)):
    part = dense[:max(2, int(len(dense) * t))]; sx, sy = part[-1]
    lab = f'<div style="transform:translate(-50px,-60px)">{ship(.65, cargo=t >= 1)}</div>'
    g = globe(0.0, spin, part, INDIA if t >= .55 else [], "THE LONG WAY ROUND", "Two centuries of Company and Crown",
              "ROUTE: THE SEA ROUTE ROUND THE CAPE, APPROXIMATE, THROUGH WAYPOINTS · DATES: COMPANY CHARTER 31 DEC 1600; GOVERNMENT OF INDIA ACT 1858 · INDIA: OFFICIAL BOUNDARY (DATAMEET, CC BY 4.0) · IMAGERY: NASA BLUE MARBLE NG VIA GIBS · SHIP DRAWN IN THE STUDIO",
              labels=[(sx, sy, lab)] + ([(-0.13, 51.5, "LONDON")] if t < .6 else []) + ([(88.36, 22.57, "CALCUTTA")] if t >= 1 else []))
    g = g.replace("#FFDD33", SIG).replace("#FF6A2A", RED)
    g = re.sub(r'<div class="a" style="left:1480px;top:90px;[^>]*>[^<]*</div>', "", g)
    g = g.replace("</body>", f'<style>{FONTS}</style><div style="position:absolute;right:56px;top:44px;z-index:90">{logo_d(1.0)}</div>'
                  f'<div style="position:absolute;left:90px;top:860px;z-index:20;background:{SIG};color:{INK};padding:12px 20px;font:400 48px/1 Anton">{date}</div>'
                  f'<div style="position:absolute;left:90px;top:22px;z-index:20;background:{INK};color:{PARCH};padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER 1 · THE PAPER TRAIL</div></body>', 1)
    put(f"globe_{tag}", g)

# ---- 2. ships on the old chart: round Ceylon into the Bay of Bengal ---------------------------------------------------
route = [(1050, 640), (1200, 780), (1350, 905), (1500, 955), (1585, 860), (1610, 700), (1645, 540), (1700, 418)]
for tag, t in (("a", .1), ("b", .5), ("c", 1.0)):
    (x, y), hd = along(route, t)
    flip = "scaleX(-1)" if math.cos(math.radians(hd)) < 0 else ""
    put(f"ship_{tag}", page(
        a(f'<div style="width:1920px;height:1080px;{DESK}"></div>', 0, 0)
        + a('<img src="/assets/chart.jpg" style="width:2000px;height:1476px;display:block;filter:sepia(.2) contrast(1.05) brightness(.92)">', -40, -312)
        + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><path d="{pathd(route)}" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="10 10" opacity=".55"/>'
          f'<path d="{pathd(sub(route, t))}" fill="none" stroke="{RED}" stroke-width="6"/><circle cx="1700" cy="418" r="12" fill="{RED}" stroke="#fff" stroke-width="2"/></svg>'
        + a(f'<div style="background:{PARCH};padding:4px 10px;font:500 18px Plex;letter-spacing:3px;color:{INK};box-shadow:0 6px 10px rgba(0,0,0,.35)">CALCUTTA</div>', 1520, 380, "z-index:32")
        + a(ship(1.0, cargo=t >= 1), x - 60, y - 96, f"z-index:40;transform:{flip}")
        + chapter(1, "THE PAPER TRAIL")
        + a(f'<div style="font:400 64px/1 Anton;color:#F3EFE6;text-shadow:0 4px 18px #000">THE COMPANY SAILS IN</div>', 70, 930, "z-index:41")
        + (a(f'<div style="background:{SIG};color:{INK};padding:10px 16px;font:700 40px Caveat;transform:rotate(-3deg);white-space:nowrap">1690: Company traders settle at Calcutta</div>', 1180, 250, "z-index:41") if t >= 1 else "")
        + (a(f'<div style="{TAGCSS};transform:rotate(-1.5deg)">MISSION STATEMENT: "TRADE" (APPROX.)</div>', 110, 860, "z-index:70") if t >= 1 else ""),
        "#2A1D12", "MAP: LINSCHOTEN, 1596, LIBRARY OF CONGRESS (PUBLIC DOMAIN BY AGE) · ROUTE AND PIN PLACED BY HAND, APPROXIMATE · CALCUTTA SETTLEMENT 1690 (JOB CHARNOCK; WELL-ESTABLISHED) · SHIP DRAWN IN THE STUDIO, NOT TO SCALE", dark=True))

# ---- 3. 3D relief of India and its biodiversity hotspots -------------------------------------------------------------
import relief  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from mask import uv  # noqa: E402
_m = json.loads((D / "maps" / "india_h.json").read_text())
_im = Image.new("L", (_m["w"], _m["h"]), 0); _d = ImageDraw.Draw(_im)
for _r in india_rings(4):
    _d.polygon([(u * _m["w"], v * _m["h"]) for u, v in (uv("india", lo, la) for lo, la in _r)], fill=255)
_im.save(D / "maps" / "india_mask.png")
card = lambda t, s, rot: (f'<div style="background:{PARCH};padding:12px 18px;transform:rotate({rot}deg);box-shadow:0 14px 24px rgba(0,0,0,.6);text-align:center;margin-bottom:26px">'
                          f'<div style="font:400 34px/1 Anton;color:{INK};letter-spacing:1px">{t}</div><div style="font:500 14px Plex;letter-spacing:3px;color:#7A2A20;margin-top:6px">{s}</div></div>')
hot = [(80.0, 30.6, "HIMALAYA", "HOTSPOT"), (75.6, 12.2, "WESTERN GHATS", "HOTSPOT, SHARED WITH SRI LANKA"), (93.6, 25.6, "INDO-BURMA", "HOTSPOT · THE NORTHEAST"),
       (93.8, 7.6, "SUNDALAND", "HOTSPOT · NICOBAR ISLANDS")]
for tag, cam, look in (("a", [4, 150, 160], [6, 0, 4]), ("b", [2, 134, 140], [6, 0, 4]), ("c", [0, 122, 126], [6, 0, 4])):
    cfg = {"exag": 6, "base": "#2A2622", "hot": RED, "peak": SIG, "grid": "#3A1410", "line": "#FFFFFF", "fog": [140, 320],
           "bloom": [0.45, 0.4, 0.62], "glow": 0.7, "cam": cam, "look": look, "fov": 30, "route": [], "seg": 600, "bg": "#08070A",
           "pins": [{"lon": lo, "lat": la, "html": card(t, s, (-2, 2)[i % 2])} for i, (lo, la, t, s) in enumerate(hot)] if tag != "a" else [],
           "overlay": f'<div style="position:absolute;left:80px;top:64px"><div style="font:400 72px/0.92 Anton;color:#F3EFE6;width:520px">4 OF THE WORLD\'S 36 BIODIVERSITY HOTSPOTS</div>'
                      f'<div style="display:inline-block;margin-top:18px;background:{SIG};padding:6px 12px;font:500 16px Plex;letter-spacing:3px;color:#141414">REAL TERRAIN · HEIGHTS EXAGGERATED 6×</div></div>'
                      f'<div style="position:absolute;right:56px;top:44px">{logo_d(1.0)}</div>'
                      f'<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;letter-spacing:1px;color:rgba(255,255,255,.55)">ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN, AWS OPEN DATA; SRTM) · INDIA LIT: OFFICIAL BOUNDARY (DATAMEET COMPOSITE, CC BY 4.0) · HOTSPOTS: CRITICAL ECOSYSTEM PARTNERSHIP FUND (CEPF); ALL FOUR ARE SHARED WITH NEIGHBOURS · PIN POSITIONS APPROXIMATE</div>'}
    html = relief.page("india", cfg).replace("<style>", f"<style>{FONTS}", 1)
    put(f"relief_{tag}", html)

# ---- 4. glowing bars: Canada, police-reported hate crimes against South Asians ----------------------------------------
import scenes3d as S3  # noqa: E402
BARS = r"""
S.background=new THREE.Color(CFG.bg);S.fog=new THREE.Fog(CFG.bg,30,70);
const data=CFG.data;const n=data.length;const k=CFG.k;
S.add(new THREE.AmbientLight('#ffffff',.35));const L=new THREE.DirectionalLight('#ffffff',1.6);L.position.set(-8,14,10);S.add(L);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,40),new THREE.MeshStandardMaterial({color:'#121014',roughness:.9}));floor.rotation.x=-Math.PI/2;S.add(floor);
const grid=new THREE.GridHelper(60,30,'#2A2226','#1C181B');grid.position.y=.01;S.add(grid);
const tops=[];
data.forEach(([yr,v],i)=>{const h=Math.max(.02,v*k*CFG.grow),x=(i-(n-1)/2)*CFG.gap;const hot=CFG.hot.includes(i);
  const mat=hot?new THREE.MeshBasicMaterial({color:new THREE.Color(CFG.glow).multiplyScalar(1.25)}):new THREE.MeshStandardMaterial({color:'#6B7280',roughness:.5,metalness:.2});
  const m=new THREE.Mesh(new THREE.BoxGeometry(CFG.gap*.6,h,CFG.gap*.6),mat);m.position.set(x,h/2,0);S.add(m);
  const e=new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({color:hot?'#FFE3DF':'#6B7280'}));e.position.copy(m.position);S.add(e);
  tops.push([yr,Math.round(v*CFG.grow),new THREE.Vector3(x,h+.3,.7),new THREE.Vector3(x,-.1,.7),hot])});
const cam=new THREE.PerspectiveCamera(28,1920/1080,.1,200);cam.position.set(...CFG.cam);cam.lookAt(...CFG.look);
const BLOOM=[.42,.22,.95];
const LABELS=()=>{let h='';for(const [yr,v,t,b,hot] of tops){const [x,y]=proj(t,cam),[bx,by]=proj(b,cam);
  h+=`<div style="left:${x-90}px;top:${y-70}px;width:180px;text-align:center;font:${hot?'400 64px':'400 46px'} Anton;color:${hot?CFG.lab:'#C9CDD6'};${hot?'text-shadow:0 0 18px '+CFG.glow:''}">${v}</div>
  <div style="left:${bx-90}px;top:${by+6}px;width:180px;text-align:center;font:500 24px Plex;color:#A0A6B2">${yr}</div>`}
 ov.innerHTML=h+`<div style="left:90px;top:120px"><div style="font:400 56px ISerif;color:#E8E4DA">${CFG.kick}</div><div style="font:400 112px/0.9 Anton;color:#F3EFE6">${CFG.title}</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:${CFG.lab};margin-top:16px;width:900px">${CFG.what}</div></div>
 <div style="left:90px;top:22px;background:#1A1A1A;color:#F4EFE6;padding:8px 16px;font:500 20px Plex;letter-spacing:5px">CHAPTER 4 · WHERE IT LANDS</div>
 <div style="left:90px;top:640px;${CFG.tag}">${CFG.tagtext}</div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.55)">${CFG.src}</div>`};
"""
for tag, grow in (("a", .3), ("b", .7), ("c", 1.0)):
    cfg = dict(bg="#0B0A0D", data=[["2021", 167], ["2022", 196], ["2023", 279], ["2024", 324], ["2025", 483]], gap=3.0, hot=[4], glow=RED, lab=SIG, grow=grow, k=5.0 / 483,
               cam=[-4, 5.4, 27], look=[0.4, 3.0, 0], kick="Not online. On paper, at the police station.", title="CANADA: +49% IN A YEAR",
               what="POLICE-REPORTED HATE CRIMES AGAINST SOUTH ASIANS, CANADA (INCLUDES SUSPECTED INCIDENTS)",
               tag=TAGCSS + ";position:absolute;transform:rotate(-1.5deg)" + (";opacity:0" if grow < 1 else ""), tagtext="TIMING, NOT CAUSE",
               src="SOURCE: STATISTICS CANADA, THE DAILY, TABLE 6 (22 JUL 2026), 2024 REVISED · CONFIRMED · INCLUDES SUSPECTED INCIDENTS · BARS START AT ZERO")
    html = S3.HEAD + f"const CFG={json.dumps(cfg, ensure_ascii=False)};\n" + BARS + S3.TAIL
    html = html.replace("</body>", f'<div style="position:absolute;right:56px;top:44px;z-index:90">{logo_d(1.0)}</div><style>{FONTS}</style></body>', 1)
    put(f"bars_{tag}", html)

# ---- 5. smash-zoom on the Macaulay receipt (1 frame, scale 1 -> 1.32, no easing) ------------------------------------
s = (H / "06_macaulay.html").read_text()
s = s.replace("<body>", '<body><div style="position:absolute;inset:0;transform:scale(1.32);transform-origin:490px 390px">', 1)
s = s.replace("</body>", "</div>" + A(f'<div style="{TAGCSS};transform:rotate(-2deg)">RECEIPT · MINUTE, 2 FEB 1835, LINE 2</div>', 1180, 120, "snap 0 0", "z-index:70") + "</body>", 1)
(H / "z06_smash.html").write_text(s)

# ---- 6. satellite: the Ganga plain, rivers flowing to the Sundarbans -------------------------------------------------
BOX = (76.5, 21.0, 93.5, 31.2)
IMW, IMH = 1920, 1920 * 1440 / 2400
OY = (1080 - IMH) / 2
P = lambda lo, la: ((lo - BOX[0]) / (BOX[2] - BOX[0]) * IMW, OY + (BOX[3] - la) / (BOX[3] - BOX[1]) * IMH)
R = json.load(open(D / "data" / "rivers.json"))["rivers"]
DELTA = (89.5, 21.8)
riv = ""
for i, (n, lines) in enumerate(R.items()):
    s0 = .1 + i * .08
    for line in lines:
        if math.dist(line[0], DELTA) < math.dist(line[-1], DELTA):
            line = line[::-1]           # run every line downstream, toward the delta
        d = "M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in line)
        riv += (f'<g data-anim="draw {s0:.2f} {s0 + .35:.2f}"><path d="{d}" pathLength="1" fill="none" stroke="#2E86DE" stroke-width="12" opacity=".35"/>'
                f'<path d="{d}" pathLength="1" fill="none" stroke="#2E86DE" stroke-width="4" stroke-linecap="round"/></g>'
                f'<g data-anim="fade {s0 + .3:.2f} {s0 + .4:.2f}"><g data-anim="flow 3 0"><path d="{d}" pathLength="1" fill="none" stroke="#DCEBFA" stroke-width="2.2" stroke-dasharray="0.012 0.04" stroke-linecap="round" opacity=".9"/></g></g>')
border = "".join('<path d="M' + " L".join("%.1f %.1f" % P(lo, la) for lo, la in r) + f'Z" fill="none" stroke="{SIG}" stroke-width="2.5" stroke-dasharray="8 6" opacity=".85"/>' for r in INDIA)
lab = lambda t, lo, la, an, c="#DCEBFA": A(f'<div style="background:rgba(10,12,16,.72);color:{c};font:500 20px Plex;letter-spacing:3px;padding:4px 10px;white-space:nowrap">{t}</div>', P(lo, la)[0], P(lo, la)[1], an, "z-index:40")
put("rivers", page(
    a(f'<img src="/maps/ganga_bm.jpg" style="width:{IMW}px;height:{IMH:.0f}px;display:block;filter:brightness(.82) contrast(1.08) saturate(.9)">', 0, OY)
    + f'<svg class="a" style="left:0;top:0;z-index:30" width="1920" height="1080"><g data-anim="fade 0 .1">{border}</g>{riv}</svg>'
    + lab("YAMUNA", 77.6, 28.2, "fade .2 .3") + lab("GANGA", 82.4, 25.9, "fade .25 .35") + lab("BRAHMAPUTRA", 91.0, 26.6, "fade .4 .5") + lab("GANDAK", 84.4, 27.3, "fade .35 .45")
    + A(f'<div style="width:520px;background:{PARCH};padding:20px 24px;box-shadow:0 14px 26px rgba(0,0,0,.45);transform:rotate(-1.5deg)">'
        f'<div style="font:500 16px Plex;letter-spacing:3px;color:#7A6A4A">UNESCO WORLD HERITAGE · SUNDARBANS</div>'
        f'<div style="font:400 44px/1.05 Anton;color:{INK};margin-top:6px">THE LARGEST MANGROVE FOREST ON EARTH</div>'
        f'<div style="font:400 26px ISerif;color:#444;margin-top:4px">where the rivers meet the Bay of Bengal</div></div>', 1300, 760, "up .7 .82", "z-index:41")
    + A(f'<div style="font:400 84px/0.95 Anton;color:#F3EFE6;text-shadow:0 4px 18px #000">ALSO OFF THE FEED</div><div style="font:400 40px ISerif;color:#E8E4DA;text-shadow:0 2px 10px #000">from the Himalaya to the Sundarbans</div>', 90, 140, "fade 0 .1", "z-index:41")
    + chapter(6, "FIXING THE FEED"),
    "#000", "IMAGERY: NASA BLUE MARBLE NEXT GENERATION VIA GIBS (PUBLIC DOMAIN) · RIVERS: NATURAL EARTH 10M CENTRELINES (PUBLIC DOMAIN), DRAWN FLOWING DOWNSTREAM · INDIA: OFFICIAL BOUNDARY, DATAMEET (CC BY 4.0), DASHED · SUNDARBANS: UNESCO WHC (INDIA, 1987; BANGLADESH, 1997)", dark=True))
print("ok")
