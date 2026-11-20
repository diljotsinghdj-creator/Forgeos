"""Four new asset types from the owner's taxonomy, as reusable generators:
[2D-BOX] box plot / range strip, [2D-UNIT] pictogram grid (12 fps pops), [25D-NODE] panning node canvas,
[3D-GLOBE] spinning globe that morphs to a flat map. Each returns one HTML page for a given moment."""
import json, math, random
from pathlib import Path
D = Path(__file__).resolve().parent
SIG = "#FFDD33"
ICONS = json.load(open("/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/tabler_icons.json"))
FONTS = """@font-face{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}@font-face{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}
@font-face{font-family:ISerif;src:url(/fonts/instrument-serif-latin-400-italic.woff2)}@font-face{font-family:Grotesk;src:url(/fonts/space-grotesk-latin-700-normal.woff2)}
@font-face{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}@font-face{font-family:Playfair;src:url(/fonts/playfair-display-latin-900-normal.woff2)}"""
PAPER = ("background:#F2EEE4;background-image:linear-gradient(rgba(60,50,40,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(60,50,40,.07) 1px,transparent 1px);"
         "background-size:48px 48px")
GRAIN = """<svg style="position:absolute;inset:0;pointer-events:none;opacity:.3;mix-blend-mode:multiply;z-index:90" width="1920" height="1080"><filter id="gr"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="3"/><feColorMatrix values="0 0 0 0 .35 0 0 0 0 .3 0 0 0 0 .25 0 0 0 .45 0"/></filter><rect width="1920" height="1080" filter="url(#gr)"/></svg>
<div style="position:absolute;inset:0;pointer-events:none;z-index:91;background-image:radial-gradient(rgba(0,0,0,.05) 1px,transparent 1.3px);background-size:5px 5px"></div>"""


def icon(name, size=40, col="#1C1C1C", sw=1.8, fill="none"):
    o = ICONS[name]["o"]
    inner = "".join(f'<{t} ' + " ".join(f'{k}="{v}"' for k, v in a.items()) + "/>" for t, a in o)
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'


def page(body, bg=PAPER, extra_head=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;position:relative;{bg}}} .a{{position:absolute}}</style>{extra_head}</head><body>{body}{GRAIN}
<script>document.fonts.ready.then(()=>{{window.READY=window.READY||!window.WAIT}})</script></body></html>"""


def step12(t):
    """12 fps 'posterize time' for reveals."""
    return math.floor(t * 12) / 12


# ---- [2D-BOX] ---------------------------------------------------------------------------------------------------------
def box_plot(groups, title, kicker, unit, source, accent_last=True, t=1.0, lo=None, hi=None):
    """groups: [(label, [values])]. Draws min-max whisker, Q1-Q3 box, median line, dots for every value."""
    def q(v, p):
        v = sorted(v); k = (len(v) - 1) * p; f = math.floor(k); c = min(f + 1, len(v) - 1)
        return v[f] + (v[c] - v[f]) * (k - f)
    allv = [x for _, v in groups for x in v]
    lo = lo if lo is not None else math.floor(min(allv) / 10) * 10
    hi = hi if hi is not None else math.ceil(max(allv) / 10) * 10
    X0, X1, Y0 = 380, 1780, 360
    rowh = (900 - Y0) / len(groups)
    X = lambda v: X0 + (v - lo) / (hi - lo) * (X1 - X0)
    svg = f'<svg class="a" style="left:0;top:0" width="1920" height="1080">'
    for v in range(int(lo), int(hi) + 1, 10):
        svg += f'<line x1="{X(v):.0f}" y1="{Y0 - 20}" x2="{X(v):.0f}" y2="930" stroke="#1C1C1C" stroke-opacity=".12"/><text x="{X(v):.0f}" y="965" font-family="Plex" font-size="20" fill="#555" text-anchor="middle">{v}</text>'
    rnd = random.Random(4)
    for i, (lab, v) in enumerate(groups):
        reveal = max(0.0, min(1.0, (step12(t) * len(groups) * 1.6) - i))       # rows wipe in one after another
        if reveal <= 0:
            continue
        y = Y0 + i * rowh + rowh / 2
        mn, q1, md, q3, mx = min(v), q(v, .25), q(v, .5), q(v, .75), max(v)
        hot = accent_last and i == len(groups) - 1
        col = "#E8B400" if hot else "#3F4A5A"
        fillc = SIG if hot else "#C9D2DE"
        w = lambda a, b: (X(a), X(a) + (X(b) - X(a)) * reveal)
        a_, b_ = w(mn, mx)
        svg += f'<line x1="{a_:.0f}" y1="{y:.0f}" x2="{b_:.0f}" y2="{y:.0f}" stroke="{col}" stroke-width="3"/>'
        if reveal >= 1:
            for xx in (X(mn), X(mx)):
                svg += f'<line x1="{xx:.0f}" y1="{y - 18:.0f}" x2="{xx:.0f}" y2="{y + 18:.0f}" stroke="{col}" stroke-width="3"/>'
            svg += f'<rect x="{X(q1):.0f}" y="{y - 30:.0f}" width="{X(q3) - X(q1):.0f}" height="60" fill="{fillc}" stroke="{col}" stroke-width="3" rx="3"/>'
            svg += f'<line x1="{X(md):.0f}" y1="{y - 34:.0f}" x2="{X(md):.0f}" y2="{y + 34:.0f}" stroke="#1C1C1C" stroke-width="5"/>'
            for val in v:
                svg += f'<circle cx="{X(val):.1f}" cy="{y + rnd.uniform(-22, 22):.1f}" r="3.2" fill="#1C1C1C" fill-opacity=".35"/>'
            svg += f'<text x="{X(md):.0f}" y="{y - 44:.0f}" font-family="Anton" font-size="{30 if hot else 24}" fill="{"#B07A00" if hot else "#333"}" text-anchor="middle">{md:.0f}</text>'
        svg += f'<text x="{X0 - 30}" y="{y + 10:.0f}" font-family="Anton" font-size="34" fill="{"#B07A00" if hot else "#1C1C1C"}" text-anchor="end">{lab}</text>'
    svg += "</svg>"
    key = (f'<div class="a" style="left:900px;top:975px;font:500 16px/1.6 Plex;color:#555;width:520px">'
           f'<svg width="200" height="40" style="vertical-align:middle"><line x1="10" y1="20" x2="190" y2="20" stroke="#3F4A5A" stroke-width="3"/><rect x="60" y="6" width="80" height="28" fill="#C9D2DE" stroke="#3F4A5A" stroke-width="3"/><line x1="95" y1="2" x2="95" y2="38" stroke="#1C1C1C" stroke-width="4"/></svg><br>'
           'WHISKERS: LOWEST TO HIGHEST MONTH · BOX: MIDDLE HALF · BAR: MEDIAN · DOTS: EVERY MONTH</div>').replace('<br>',' ').replace('width:520px','width:1000px;display:flex;align-items:center;gap:14px').replace('height="40"','height="30"')
    body = (f'<div class="a" style="left:110px;top:70px"><div style="font:400 56px ISerif;color:#1C1C1C">{kicker}</div>'
            f'<div style="font:400 120px/0.9 Anton;color:#1C1C1C">{title}</div></div>{key}{svg}'
            f'<div class="a" style="left:{X0}px;top:995px;font:500 18px Plex;letter-spacing:3px;color:#555">{unit}</div>'
            f'<div class="a" style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.5)">{source}</div>')
    return page(body)


# ---- [2D-UNIT] --------------------------------------------------------------------------------------------------------
def unit_grid(n, lit, title, kicker, icon_name, source, cols=20, t=1.0, lit_label=""):
    """n icons pop in at 12 fps in reading order; the first `lit` after the reveal turn accent."""
    shown = int(n * min(1, step12(t) / .7))
    lit_on = t >= .85
    size, gap = 50, 10
    rows = math.ceil(n / cols)
    x0 = 1860 - cols * (size + gap)
    y0 = 1080 - rows * (size + gap) - 90
    cells = ""
    order = list(range(n))
    hot = set(random.Random(9).sample(order, lit)) if lit_on else set()
    for k in range(shown):
        r, c = divmod(k, cols)
        is_hot = k in hot
        pop = "scale(1.15)" if k == shown - 1 and shown < n else "scale(1)"
        cells += (f'<div class="a" style="left:{x0 + c * (size + gap)}px;top:{y0 + r * (size + gap)}px;width:{size}px;height:{size}px;transform:{pop};'
                  f'display:flex;align-items:center;justify-content:center;background:{"#1C1C1C" if is_hot else "transparent"};border-radius:6px">'
                  f'{icon(icon_name, size - 12, SIG if is_hot else "#3A3A3A", 1.7)}</div>')
    counter = (f'<div class="a" style="left:110px;top:{y0}px"><div style="font:400 220px/0.85 Anton;color:#1C1C1C">{shown if not lit_on else lit}</div>'
               f'<div style="font:600 22px/1.4 Plex;letter-spacing:4px;color:{"#B07A00" if lit_on else "#555"};width:300px">{lit_label if lit_on else "COUNTING…"}</div></div>')
    body = (f'<div class="a" style="left:110px;top:70px"><div style="font:400 56px ISerif;color:#1C1C1C">{kicker}</div>'
            f'<div style="font:400 120px/0.9 Anton;color:#1C1C1C">{title}</div></div>{counter}{cells}'
            f'<div class="a" style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.5)">{source}</div>')
    return page(body)


# ---- [25D-NODE] -------------------------------------------------------------------------------------------------------
def node_canvas(nodes, edges, cam, title, source, t=1.0, focus=None):
    """nodes: {id: (x, y, icon, text, sub)} on a 4000x2400 canvas; edges: [(a, b)]; cam: (cx, cy, zoom).
    The canvas pans and zooms; edges draw as dashed curves in order; the focus node is lit."""
    cx, cy, z = cam
    W, H = 4000, 2400
    tx, ty = 960 - cx * z, 540 - cy * z
    svg = f'<svg class="a" style="left:0;top:0;overflow:visible" width="{W}" height="{H}"><defs><marker id="ah" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto"><path d="M0 0 L12 7 L0 14" fill="none" stroke="#C8312B" stroke-width="2.5"/></marker></defs>'
    for k, (a, b) in enumerate(edges):
        if k / len(edges) > step12(t):
            continue
        x1, y1 = nodes[a][:2]; x2, y2 = nodes[b][:2]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 120
        svg += f'<path d="M{x1} {y1} Q {mx} {my} {x2} {y2}" fill="none" stroke="#C8312B" stroke-width="4" stroke-dasharray="14 10" marker-end="url(#ah)" opacity=".85"/>'
    svg += "</svg>"
    cards = ""
    for nid, (x, y, ic, text, sub) in nodes.items():
        hot = nid == focus
        cards += (f'<div class="a" style="left:{x - 190}px;top:{y - 70}px;width:380px;background:{"#1C1C1C" if hot else "#FBF8F0"};border:3px solid #1C1C1C;'
                  f'box-shadow:8px 10px 0 rgba(0,0,0,.18);padding:16px 18px;display:flex;gap:16px;align-items:center;transform:rotate({(hash(nid) % 5) - 2}deg)">'
                  f'{icon(ic, 64, SIG if hot else "#1C1C1C", 1.6)}<div><div style="font:400 34px/1 Anton;color:{SIG if hot else "#1C1C1C"}">{text}</div>'
                  f'<div style="font:500 15px/1.35 Plex;color:{"#ddd" if hot else "#555"};margin-top:6px">{sub}</div></div></div>')
    world = (f'<div class="a" style="left:0;top:0;width:{W}px;height:{H}px;transform-origin:0 0;transform:translate({tx:.0f}px,{ty:.0f}px) scale({z})">'
             f'<div class="a" style="left:0;top:0;width:{W}px;height:{H}px;{PAPER};background-size:60px 60px"></div>{svg}{cards}</div>')
    body = (world + f'<div class="a" style="left:0;top:0;width:1920px;height:230px;background:linear-gradient(#F2EEE4 55%,rgba(242,238,228,0))"></div>'
            f'<div class="a" style="left:90px;top:50px;font:400 96px/0.9 Anton;color:#1C1C1C">{title}</div>'
            f'<div class="a" style="left:1500px;top:70px;font:500 16px Plex;letter-spacing:3px;color:#555">CANVAS {cx:.0f},{cy:.0f} · {z:.2f}×</div>'
            f'<div class="a" style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.5)">{source}</div>')
    return page(body, bg="background:#F2EEE4")


# ---- [3D-GLOBE] -------------------------------------------------------------------------------------------------------
def globe(morph, spin_lon, route, outline, title, kicker, source, labels=()):
    """morph 0 = sphere, 1 = flat equirectangular map; spin_lon = longitude facing the camera.
    route: [(lon, lat)] drawn as a glowing line that morphs with the surface; outline: rings drawn in yellow."""
    V = "/vendor/three160"
    C = {"m": morph, "spin": spin_lon, "route": route, "outline": outline, "labels": list(labels)}
    head = f'<script type="importmap">{{"imports":{{"three":"{V}/three.module.js","three/addons/":"{V}/addons/"}}}}</script>'
    js = r"""
<div id="ov" class="a" style="inset:0"></div>
<script type="module">
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
const C=CFG;const R=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,alpha:true});R.setSize(1920,1080);R.setPixelRatio(1);
R.domElement.style.position='absolute';document.body.prepend(R.domElement);
const S=new THREE.Scene();S.background=new THREE.Color('#0A1020');const m=C.m, e=m<.5?2*m*m:1-Math.pow(-2*m+2,2)/2;
const RAD=3.0, FW=10.4, FH=FW/2;
// a point on the morphing surface: sphere (spun so spin_lon faces the camera) -> flat map centred on spin_lon
const P=(lon,lat,lift=0)=>{let dl=((lon-C.spin+540)%360)-180;const l=dl*Math.PI/180,p=lat*Math.PI/180;
  const s=new THREE.Vector3((RAD+lift)*Math.cos(p)*Math.sin(l),(RAD+lift)*Math.sin(p),(RAD+lift)*Math.cos(p)*Math.cos(l));
  const f=new THREE.Vector3(dl/360*FW,lat/180*FH,lift);return s.lerp(f,e)};
const seg=180,G=new THREE.BufferGeometry(),pos=[],uv=[],idx=[];
for(let j=0;j<=seg/2;j++)for(let i=0;i<=seg;i++){const lon=C.spin-180+i/seg*360,lat=90-j/(seg/2)*180;const v=P(lon,lat);pos.push(v.x,v.y,v.z);uv.push(((lon+180)%360+360)%360/360,1-j/(seg/2))}
for(let j=0;j<seg/2;j++)for(let i=0;i<seg;i++){const a=j*(seg+1)+i,b=a+1,c=a+seg+1,d=c+1;idx.push(a,c,b,b,c,d)}
G.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));G.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));G.setIndex(idx);G.computeVertexNormals();
const tex=await new THREE.TextureLoader().loadAsync('/maps/bluemarble_world.jpg');tex.colorSpace=THREE.SRGBColorSpace;tex.wrapS=THREE.RepeatWrapping;
// fix the seam: uv u jumps where lon crosses 180; duplicate handling via shader-free approach: set wrap and correct per-vertex
const uvA=G.attributes.uv;for(let j=0;j<=seg/2;j++){let prev=null;for(let i=0;i<=seg;i++){const k=j*(seg+1)+i;let u=uvA.getX(k);if(prev!==null&&u<prev-.5)u+=1;uvA.setX(k,u);prev=u}}
S.add(new THREE.Mesh(G,new THREE.MeshStandardMaterial({map:tex,roughness:1,metalness:0})));
S.add(new THREE.AmbientLight('#ffffff',1.1-e*.2));const L=new THREE.DirectionalLight('#fff7e8',1.6*(1-e)+.6);L.position.set(-6,4,8);S.add(L);
if(e<.02){const atm=new THREE.Mesh(new THREE.SphereGeometry(RAD*1.04,64,48),new THREE.MeshBasicMaterial({color:'#6FA8FF',transparent:true,opacity:.12*(1-e),side:THREE.BackSide}));S.add(atm)}
const line=(pts,col,lift,w)=>{const v=pts.map(([lo,la])=>P(lo,la,lift));const g=new THREE.BufferGeometry().setFromPoints(v);const ln=new THREE.Line(g,new THREE.LineBasicMaterial({color:col,depthTest:e>.6}));S.add(ln);return v};
for(const r of C.outline)line(r.concat([r[0]]),new THREE.Color('#FFDD33').multiplyScalar(1.4),.02,2);
// great-circle route
const gc=(a,b,n=96)=>{const toV=([lo,la])=>new THREE.Vector3(Math.cos(la*Math.PI/180)*Math.cos(lo*Math.PI/180),Math.cos(la*Math.PI/180)*Math.sin(lo*Math.PI/180),Math.sin(la*Math.PI/180));
  const A=toV(a),B=toV(b),om=A.angleTo(B),out=[];for(let i=0;i<=n;i++){const t=i/n;const v=A.clone().multiplyScalar(Math.sin((1-t)*om)/Math.sin(om)).add(B.clone().multiplyScalar(Math.sin(t*om)/Math.sin(om)));
  out.push([Math.atan2(v.y,v.x)*180/Math.PI,Math.asin(v.z)*180/Math.PI])}return out};
let rpts=[];for(let i=0;i<C.route.length-1;i++)rpts=rpts.concat(gc(C.route[i],C.route[i+1]));
const arc=rpts.map(([lo,la],i)=>P(lo,la,.04+.35*Math.sin(Math.PI*i/(rpts.length-1))*(1-e)));
const tube=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(arc),300,.025,8),new THREE.MeshBasicMaterial({color:new THREE.Color('#FF6A2A').multiplyScalar(2.2)}));S.add(tube);
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,100);const cz=17*(1-e)+15*e;cam.position.set(-2.6*(1-e),.8*(1-e)+1.15*e,cz);cam.lookAt(-2.6*(1-e),.4*(1-e)+1.15*e,0);
const comp=new EffectComposer(R);comp.addPass(new RenderPass(S,cam));comp.addPass(new UnrealBloomPass(new THREE.Vector2(1920,1080),.5,.3,.85));comp.addPass(new OutputPass());comp.render();
const ov=document.getElementById('ov');
for(const [lo,la,txt] of C.labels){const p=P(lo,la,.05).project(cam);const x=(p.x+1)/2*1920,y=(1-p.y)/2*1080;
  ov.insertAdjacentHTML('beforeend',`<div class="a" style="left:${x+12}px;top:${y-18}px;font:400 30px Anton;color:#FFDD33;text-shadow:0 2px 8px #000">${txt}</div><div class="a" style="left:${x-7}px;top:${y-7}px;width:14px;height:14px;border-radius:50%;background:#FFDD33;box-shadow:0 0 12px #FFDD33"></div>`)}
window.READY=true;
</script>""".replace("CFG", json.dumps(C))
    body = (js + f'<div class="a" style="left:90px;top:70px;z-index:5"><div style="font:400 54px ISerif;color:#E8E4DA">{kicker}</div><div style="font:400 120px/0.9 Anton;color:#F3EFE6">{title}</div></div>'
            f'<div class="a" style="left:1480px;top:90px;z-index:5;font:500 18px Plex;letter-spacing:3px;color:#9AA3B2">{"GLOBE" if morph < .2 else "MORPHING" if morph < .9 else "FLAT MAP"} · {int(morph * 100)}%</div>'
            f'<div class="a" style="left:24px;bottom:14px;z-index:5;font:500 12px Plex;color:rgba(255,255,255,.55)">{source}</div>')
    return page(body, bg="background:radial-gradient(ellipse at 60% 50%,#14213D 0%,#05070D 70%)", extra_head=head).replace("window.READY=window.READY||!window.WAIT", "window.READY=window.READY")
