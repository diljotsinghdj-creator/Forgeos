"""Shot 5: the Senate flips on a tilted paper map of the US (CSS 3D), Natural Earth admin-1 (public domain)."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parent
st = json.load(open("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/states.json"))["United States of America"]
p1, p2, p0, l0 = map(math.radians, (29.5, 45.5, 37.5, -96))
n = (math.sin(p1) + math.sin(p2)) / 2; C = math.cos(p1) ** 2 + 2 * n * math.sin(p1); r0 = math.sqrt(C - 2 * n * math.sin(p0)) / n
def proj(lon, lat):
    t = n * (math.radians(lon) - l0); r = math.sqrt(C - 2 * n * math.sin(math.radians(lat))) / n
    return r * math.sin(t), -(r0 - r * math.cos(t))
def rings(g):
    g = json.loads(g) if isinstance(g, str) else g
    d = 0
    while isinstance(g, list) and g and isinstance(g[0], list) and isinstance(g[0][0], list) and isinstance(g[0][0][0], list):
        g = [r for poly in g for r in poly]; d += 1
    return g
shapes = {s["n"]: rings(s["r"]) for s in st if s["n"] not in ("Alaska", "Hawaii")}
pts = [proj(*p) for rs in shapes.values() for r in rs for p in r]
xs, ys = [p[0] for p in pts], [p[1] for p in pts]
W, H, M = 1500, 920, 40
k = min((W - 2 * M) / (max(xs) - min(xs)), (H - 2 * M) / (max(ys) - min(ys)))
def xy(lon, lat):
    x, y = proj(lon, lat); return M + (x - min(xs)) * k, M + (max(ys) - (-y) if False else (y - min(ys))) * k
def path(rs):
    out = []
    for r in rs:
        q = [xy(*p) for p in r]
        out.append("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in q) + "Z")
    return " ".join(out)
# y axis: proj returns -y up; flip so north is up
def path2(rs):
    out = []
    for r in rs:
        q = []
        for lon, lat in r:
            x, y = proj(lon, lat); q.append((M + (x - min(xs)) * k, M + (y - min(ys)) * k))
        out.append("M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in q) + "Z")
    return " ".join(out)
flips = ["Texas", "Kansas", "Iowa", "South Carolina", "Maine"]
base = "".join(f'<path d="{path2(rs)}" fill="#E9DCBC" stroke="#8E7E5C" stroke-width="1.6"/>' for nm, rs in shapes.items())
NEWS = ('<pattern id="np" width="96" height="14" patternUnits="userSpaceOnUse"><rect x="0" y="5" width="40" height="3" fill="#000" opacity=".16"/>'
        '<rect x="46" y="5" width="44" height="3" fill="#000" opacity=".12"/></pattern>')
lift = ""
for i, nm in enumerate(flips):
    d = path2(shapes[nm])
    lift += (f'<svg class="el lift" data-in="pop" data-at="{0.9 + i * 0.25:.2f}" data-base="translateZ(46px)" data-jit="0" data-name="{nm}" style="position:absolute;left:0;top:0" width="{W}" height="{H}">'
             f'<defs>{NEWS}</defs><path d="{d}" fill="#2B57A8" stroke="#EEE7D8" stroke-width="3" style="filter:drop-shadow(0 0 14px rgba(80,140,255,.85))"/>'
             f'<path d="{d}" fill="url(#np)" style="mix-blend-mode:multiply"/></svg>')
# Kansas centre for the dashed ring (in map coordinates)
kx = sum(p[0] for r in shapes["Kansas"] for p in r) / sum(len(r) for r in shapes["Kansas"])
ky = sum(p[1] for r in shapes["Kansas"] for p in r) / sum(len(r) for r in shapes["Kansas"])
x0, y0 = proj(kx, ky); cx, cy = M + (x0 - min(xs)) * k, M + (y0 - min(ys)) * k
grat = "".join(f'<path d="M{x} 0 V{H}" stroke="#8E7E5C" stroke-width=".8" opacity=".35"/>' for x in range(0, W, 120)) + \
       "".join(f'<path d="M0 {y} H{W}" stroke="#8E7E5C" stroke-width=".8" opacity=".35"/>' for y in range(0, H, 120))
html = f"""<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="../kit.css"><script src="../kit.js"></script>
<style>
#table{{position:absolute;left:210px;top:170px;width:{W}px;height:{H}px;transform-style:preserve-3d}}
#stage{{position:absolute;inset:0;perspective:1700px;perspective-origin:50% 30%}}
.paper{{position:absolute;inset:-60px;background:#E6D6B0;box-shadow:0 60px 80px rgba(0,0,0,.35);border:1px solid #c9b48a}}
.lbl{{position:absolute;font:800 22px Inter;letter-spacing:3px;color:#EEE7D8;background:#111;padding:8px 14px;text-transform:uppercase;white-space:nowrap}}
</style></head>
<body data-dur="4.4" data-push=".05"><svg width="0" height="0" style="position:absolute"><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="21"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .3  0 0 0 0 .25  0 0 0 .35 0"/></filter></svg>
<div id="cam"><div id="stage">
 <div class="el" data-in="slide" data-from="b" data-at="0" data-jit="0" data-breathe="0" style="position:absolute;inset:0;transform-style:preserve-3d">
  <div id="table" style="transform:rotateX(46deg) rotateZ(-5deg)">
   <div class="paper"></div>
   <svg style="position:absolute;left:0;top:0" width="{W}" height="{H}">{grat}{base}</svg>
   {lift}
   <svg class="el" data-in="draw" data-at="2.2" data-base="translateZ(48px)" data-jit="0" style="position:absolute;left:0;top:0;overflow:visible" width="{W}" height="{H}">
     <path d="M{cx - 150:.0f} {cy:.0f} a150 150 0 1 0 300 0 a150 150 0 1 0 -300 0" fill="none" stroke="#E8551E" stroke-width="7" stroke-dasharray="20 14"/></svg>
  </div>
 </div>
</div>
<div id="labels"></div>
<div class="el" data-in="slide" data-at=".2" style="left:70px;top:60px"><div class="serif" style="font-size:120px;color:#111">Red to blue</div></div>
<div class="el" data-in="wipe" data-at=".5" style="left:76px;top:190px"><div class="tag">Some of the Senate seats Democrats flipped · 2026</div></div>
<div class="el" data-in="wipe" data-at="2.6" style="left:1180px;top:930px"><div class="marker" style="font-size:44px;transform:rotate(-4deg);white-space:nowrap">Kansas: first since 1932</div></div>
</div>
<svg class="grain" width="1920" height="1080"><rect width="1920" height="1080" filter="url(#grain)"/></svg>
<div class="credit">MAP: NATURAL EARTH (PUBLIC DOMAIN)</div>
<script>
// leader-line labels in screen space, from each lifted state's projected centre (computed after the 3D layout)
window.addEventListener('load',()=>{{
  const L=document.getElementById('labels'); const spots={{'Texas':[-160,40],'Kansas':[-40,-150],'Iowa':[60,-170],'South Carolina':[150,40],'Maine':[60,-120]}};
  document.querySelectorAll('.lift').forEach((s,i)=>{{
    const keep=s.style.opacity; s.style.opacity=1; const r=s.querySelector('path').getBoundingClientRect(); s.style.opacity=keep;
    const cx=r.left+r.width/2, cy=r.top+r.height/2, [dx,dy]=spots[s.dataset.name], at=(+s.dataset.at+.35).toFixed(2);
    L.insertAdjacentHTML('beforeend',`<svg class="el" data-in="draw" data-at="${{at}}" data-jit="0" style="left:0;top:0;position:absolute" width="1920" height="1080"><path d="M${{cx}} ${{cy}} L${{cx+dx}} ${{cy+dy}}" stroke="#111" stroke-width="3" fill="none"/><circle cx="${{cx}}" cy="${{cy}}" r="7" fill="#111"/></svg>`+
      `<div class="el lbl" data-in="pop" data-at="${{at}}" style="left:${{cx+dx-(dx<0?190:0)}}px;top:${{cy+dy-24}}px">${{s.dataset.name}}</div>`);
  }});
  setT(+(new URLSearchParams(location.search).get('t')||99));
}});
</script></body></html>"""
(D / "shots" / "s05_kansas.html").write_text(html, encoding="utf-8")
print("ok", round(cx), round(cy))
