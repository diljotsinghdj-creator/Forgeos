"""Genuine 3D scenes: real meshes, lights, shadows and a moving perspective camera, rendered with three.js (MIT,
bundled) in the same headless Chromium that draws the Vox scenes. No Blender, no GPU needed (WebGL runs on the
software rasteriser when there is no graphics card).

    Bars3d:  UP 80, Maharashtra 48, Bihar 40, Tamil Nadu 39 | Lok Sabha seats | seats
             - bars that rise out of the paper, lit from one side, the camera orbiting them
    Prism:   India 1.9, China 8.0, USA 14.9, Germany 8.1 | CO2 per person | tonnes, 2022
             - a prism map: each country is extruded to its number, the camera tilts down across the map
    Explode: Smartphone | Glass, Display, Battery, Logic board, Camera, Back cover | What is inside
             - an exploded view: the layers of a thing lift apart, each one named
    Title3d: THE CANAL | 1914 · Panama
             - extruded letters that swing up one by one, a light sweeping across them, a slow push in

They carry the video's look (paper, accent, fonts) so they sit in the same film as the 2D scenes.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .ff import MediaError

KINDS = ("bars3d", "prism", "explode", "title3d", "terrain3d", "towers3d")
TERRAIN_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
TERRAIN_CREDIT = "Elevation: Mapzen terrain tiles (AWS Open Data; SRTM, GMTED, ETOPO1 and others)"
# places explainers go to that the place list doesn't hold: (lat, lon)
PEAKS = {"mount everest": (27.988, 86.925), "everest": (27.988, 86.925), "k2": (35.881, 76.513),
         "kangchenjunga": (27.703, 88.147), "mont blanc": (45.833, 6.865), "matterhorn": (45.976, 7.658),
         "kilimanjaro": (-3.067, 37.355), "mount fuji": (35.361, 138.727), "denali": (63.069, -151.007),
         "grand canyon": (36.1, -112.1), "siachen": (35.42, 77.1), "kailash": (31.067, 81.312),
         "nanda devi": (30.376, 79.971), "khyber pass": (34.09, 71.15), "strait of hormuz": (26.57, 56.25)}
VENDOR = Path(__file__).parent / "vendor"


def parse_bars3d(spec: str) -> dict | None:
    from . import vox
    parts = [p.strip() for p in (spec or "").split("|")]
    vals = [v for v in vox._pairs(parts[0]) if v["value"] >= 0][:8]
    if len(vals) < 2:
        return None
    return {"type": "bars3d", "values": vals, "title": parts[1][:48] if len(parts) > 1 else "",
            "unit": parts[2][:20] if len(parts) > 2 else ""}


def parse_prism(spec: str) -> dict | None:
    from . import maps, vox
    parts = [p.strip() for p in (spec or "").split("|")]
    pairs = vox._pairs(parts[0])
    vals = [(c, v) for v in pairs for c in [vox._country(v["label"])] if c]
    world = maps._world()["countries"]
    st = vox._state_heat(pairs) if len(vals) < 2 or len(vals) < len(pairs) / 2 else None
    if st:
        vals = st[1]
        world = [x for x in vox._states()[st[0]] if x["n"] not in {c["n"] for c, _ in vals}]
    if len(vals) < 2:
        return None
    pts = [(x, y) for c, _ in vals for x, y in max(c["r"], key=len)]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    box = [min(xs), max(-56.0, min(ys)), max(xs), min(78.0, max(ys))]
    named = {c["n"] for c, _ in vals}

    def thin(r, n):
        return [[round(x, 2), round(y, 2)] for x, y in r[:: max(1, len(r) // n)]]
    items = []
    for c, v in vals[:12]:
        big = max(c["r"], key=len)
        items.append({"name": c["n"], "label": v["label"], "value": v["value"], "shown": v["shown"],
                      "rings": [thin(r, 110) for r in c["r"] if len(r) >= 10 or r is big][:6],
                      "at": [round(sum(q[0] for q in big) / len(big), 2), round(sum(q[1] for q in big) / len(big), 2)]})
    others = []
    for c in world:
        if c["n"] in named:
            continue
        for r in c["r"]:
            if len(r) >= 12 and any(box[0] - 25 <= x <= box[2] + 25 and box[1] - 18 <= y <= box[3] + 18
                                    for x, y in r[:: max(1, len(r) // 20)]):
                others.append(thin(r, 60))
    return {"type": "prism", "items": items, "others": others[:260], "box": box,
            "title": parts[1][:48] if len(parts) > 1 else "", "unit": parts[2][:26] if len(parts) > 2 else ""}


def parse_explode(spec: str) -> dict | None:
    parts = [p.strip() for p in (spec or "").split("|")]
    if len(parts) < 2 or not parts[0]:
        return None
    layers = [x.strip()[:24] for x in parts[1].split(",") if x.strip()][:7]
    if len(layers) < 2:
        return None
    return {"type": "explode", "thing": parts[0][:30], "layers": layers, "title": parts[2][:48] if len(parts) > 2 else ""}


def parse_title3d(spec: str) -> dict | None:
    parts = [p.strip() for p in (spec or "").split("|")]
    text = re.sub(r"\s+", " ", parts[0]).upper()[:22]
    # the 3D face is Latin; a Hindi title stays in the 2D type scenes, which shape Devanagari properly
    if not text or not re.fullmatch(r"[A-Z0-9 .,:;!?&'\-]+", text):
        return None
    return {"type": "title3d", "text": text, "sub": parts[1][:60] if len(parts) > 1 else ""}


def parse_terrain3d(spec: str) -> dict | None:
    """'Terrain3d: Mount Everest | The roof of the world | 40 km' or 'Terrain3d: Siachen @ 35.42, 77.1 | ...' - the
    real shape of the land (elevation tiles), lit from the side, the camera circling; the highest point is named."""
    from . import maps
    parts = [p.strip() for p in (spec or "").split("|")]
    name, _, at = parts[0].partition("@")
    name = name.strip()
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", at)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
    elif name.lower() in PEAKS:
        lat, lon = PEAKS[name.lower()]
    else:
        f = maps._find(name)
        if not f or f["kind"] != "city":
            return None                                   # a whole country is a map, not a landform
        lat, lon = f["lat"], f["lon"]
    if not name or not (-80 <= lat <= 80):
        return None
    km = next((float(x.group(1)) for p in parts[2:] for x in [re.search(r"([\d.]+)\s*km", p, re.I)] if x), 40.0)
    hm = next((x.group(1).strip() for p in parts[2:] for x in [re.search(r"height\s*[:=]\s*(.+)", p, re.I)] if x), "")
    return {"type": "terrain3d", "name": name[:28], "lat": lat, "lon": lon, "km": min(300.0, max(8.0, km)), "height": hm[:16],
            "title": parts[1][:48] if len(parts) > 1 else "", "credit": TERRAIN_CREDIT}


def heights(lat: float, lon: float, km: float, cache: Path, n: int = 150, timeout: float = 30) -> dict:
    """An n x n grid of elevations (metres) for a square `km` wide round a point, from the open terrain tiles
    (downloaded once into `cache`). {"h": [[...]], "min", "max", "peak": (row, col)}"""
    import io
    import math
    import urllib.request
    import numpy as np
    from PIL import Image
    z = int(max(5, min(12, math.floor(math.log2(40075.0 * math.cos(math.radians(lat)) / km * 1.6)))))

    def tile_xy(la, lo):
        x = (lo + 180) / 360 * 2 ** z
        y = (1 - math.asinh(math.tan(math.radians(la))) / math.pi) / 2 * 2 ** z
        return x, y
    dlat = km / 2 / 110.57
    dlon = km / 2 / (111.32 * math.cos(math.radians(lat)))
    x0, y0 = tile_xy(lat + dlat, lon - dlon)
    x1, y1 = tile_xy(lat - dlat, lon + dlon)
    tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
    if (tx1 - tx0 + 1) * (ty1 - ty0 + 1) > 36:
        raise MediaError("terrain: the area is too wide for its zoom")
    cache.mkdir(parents=True, exist_ok=True)
    mosaic = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            f = cache / f"{z}_{tx % 2 ** z}_{ty}.png"
            if not (f.is_file() and f.stat().st_size > 100):
                try:
                    req = urllib.request.Request(TERRAIN_URL.format(z=z, x=tx % 2 ** z, y=ty), headers={"User-Agent": "CreatorForge"})
                    with urllib.request.urlopen(req, timeout=timeout) as r:
                        f.write_bytes(r.read())
                except Exception as e:  # noqa: BLE001
                    raise MediaError(f"terrain: elevation tiles not reachable ({str(e)[:80]})") from e
            a = np.asarray(Image.open(io.BytesIO(f.read_bytes())).convert("RGB"), np.float32)
            mosaic[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = \
                a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    px0, py0 = int((x0 - tx0) * 256), int((y0 - ty0) * 256)
    px1, py1 = max(px0 + 8, int((x1 - tx0) * 256)), max(py0 + 8, int((y1 - ty0) * 256))
    crop = mosaic[py0:py1, px0:px1]
    grid = np.asarray(Image.fromarray(crop).resize((n, n), Image.BILINEAR), np.float32)
    grid = np.maximum(grid, -50.0)                         # the sea floor is not the story
    r, c = np.unravel_index(int(grid.argmax()), grid.shape)
    # the label uses the full-resolution data (the drawn grid is thinned and rounds the summit off)
    return {"h": [[int(v) for v in row] for row in grid], "min": float(grid.min()), "max": float(grid.max()),
            "top": float(crop.max()),
            "peak": [int(r), int(c)], "n": n}


def parse_towers3d(spec: str) -> dict | None:
    """'Towers3d: Burj Khalifa 828, Shanghai Tower 632, Eiffel Tower 330, Qutub Minar 73 | How tall? | m' - buildings
    to scale as stepped 3D towers with their floors marked (the massing of a height, not a model of the building)."""
    from . import vox
    parts = [p.strip() for p in (spec or "").split("|")]
    vals = [v for v in vox._pairs(parts[0]) if v["value"] > 0 and v["label"]][:6]
    if len(vals) < 2:
        return None
    return {"type": "towers3d", "values": vals, "title": parts[1][:48] if len(parts) > 1 else "",
            "unit": parts[2][:10] if len(parts) > 2 else "m"}


PARSERS = {"terrain3d": parse_terrain3d, "towers3d": parse_towers3d, "bars3d": parse_bars3d, "prism": parse_prism, "explode": parse_explode, "title3d": parse_title3d}


def plan_for(kind: str, spec: str) -> dict | None:
    fn = PARSERS.get(kind)
    return fn(spec) if fn else None


_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
html,body{margin:0;padding:0;overflow:hidden;width:%W%px;height:%H%px;background:%PAPER% url('%BG%') center/cover}
canvas{position:absolute;left:0;top:0}
#ov{position:absolute;left:0;top:0;width:%W%px;height:%H%px;pointer-events:none}
#grain{position:absolute;left:0;top:0;width:%W%px;height:%H%px;background:url('%GRAIN%') center/cover;mix-blend-mode:multiply;opacity:.5}
.t{position:absolute;white-space:nowrap;transform:translate(-50%,-50%);will-change:transform,opacity}
.box{background:#141414;color:#fff;padding:.12em .32em;font-weight:900}
.val{color:#141414}
.tag{background:#141414;color:#fff;padding:.18em .5em;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.src{color:#3a3a3a;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
</style><script>%THREE%</script></head><body><div id="ov"></div><div id="grain"></div><script>
const P=%PLAN%, W=%W%, H=%H%, DUR=%DUR%, K=%KIT%, FONT=%FONT%;
const TALL=H>W, U=Math.min(W,H), ACC=K.acc, INK='#141414';
const E={out:t=>1-Math.pow(1-t,3), inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2, back:t=>{const c=1.5,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)}};
const cl=(v,a,b)=>Math.max(a===undefined?0:a,Math.min(b===undefined?1:b,v)), seg=(t,s,d)=>cl((t-s)/d);
const col=c=>new THREE.Color(c);
function mix(a,b,t){return '#'+col(a).lerp(col(b),t).getHexString()}
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});renderer.setPixelRatio(1);renderer.setSize(W,H);
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;document.body.insertBefore(renderer.domElement,document.getElementById('ov'));
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(TALL?44:30,W/H,.1,500);
scene.add(new THREE.HemisphereLight(0xffffff,0xb9ad94,1.15));
const sun=new THREE.DirectionalLight(0xfff1d8,2.1);sun.position.set(-7,13,9);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-16,right:16,top:16,bottom:-16,near:.5,far:60});sun.shadow.bias=-.0006;sun.shadow.radius=5;scene.add(sun);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(400,400),new THREE.ShadowMaterial({opacity:.3}));ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
const mat=(c,o)=>new THREE.MeshStandardMaterial(Object.assign({color:col(c),roughness:.82,metalness:.02},o||{}));
function inked(mesh,c){const e=new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry,28),new THREE.LineBasicMaterial({color:col(c||INK)}));mesh.add(e);return mesh}  // the drawn outline
const OV=document.getElementById('ov'),labels=[];
function label(text,cls,size,family,weight){const d=document.createElement('div');d.className='t '+(cls||'');d.textContent=text;
  d.style.fontFamily="'"+((K.fam||{})[family]||family||'Inter')+"'";d.style.fontSize=size+'px';d.style.fontWeight=weight||800;d.style.opacity=0;OV.appendChild(d);return d}
function pin(d,v,dx,dy){const q=v.clone().project(camera);d.style.left=((q.x*.5+.5)*W+(dx||0))+'px';d.style.top=((-q.y*.5+.5)*H+(dy||0))+'px'}
function title(s){if(!s)return null;const d=label(s.toUpperCase(),'box',U*.05,'Playfair',900);d.style.left=W/2+'px';d.style.top=(TALL?H*.075:H*.085)+'px';return d}
function orbit(t,o){const p=E.inout(cl(t/DUR)),a=o.a0+(o.a1-o.a0)*p,r=o.r0+(o.r1-o.r0)*p,h=o.h0+(o.h1-o.h0)*p;
  camera.position.set(o.tx+Math.sin(a)*r,h,o.tz+Math.cos(a)*r);camera.lookAt(o.tx,o.ty,o.tz)}
const leave=t=>1-seg(t,DUR-.55,.35);   // labels clear before the cut
let update=()=>{};

function bars3d(){const vs=P.values,n=vs.length,mx=Math.max(...vs.map(v=>v.value)),gap=1.7,w=1.05,maxh=TALL?5.6:4.0,x0=-(n-1)*gap/2;
  const tt=title(P.title),bars=vs.map((v,i)=>{const h=Math.max(.08,maxh*v.value/mx),top=v.value===mx;
    const m=inked(new THREE.Mesh(new THREE.BoxGeometry(w,1,w),mat(top?ACC:'#46525C')));m.castShadow=m.receiveShadow=true;m.position.set(x0+i*gap,0,0);scene.add(m);
    const plinth=new THREE.Mesh(new THREE.BoxGeometry(w*1.3,.06,w*1.3),mat('#FBF8F0'));plinth.position.set(x0+i*gap,.03,0);plinth.receiveShadow=true;scene.add(inked(plinth));
    return {m,h,v,val:label('0','val',U*.052,'Anton',400),nm:label(v.label||'','tag',U*.021,'Inter',800)}});
  const dec=s=>((String(s).match(/\.(\d+)/)||[])[1]||'').length,pre=s=>(String(s).match(/^[^\d-]*/)||[''])[0],suf=s=>(String(s).match(/[^\d.,]*$/)||[''])[0];
  const span=(n-1)*gap+w,o={tx:0,ty:maxh*.5,tz:0,a0:-.62,a1:.42,r0:Math.max(17,span*(TALL?3.3:2.0)),r1:Math.max(15,span*(TALL?2.9:1.75)),h0:maxh*1.5,h1:maxh*1.05};
  const unit=P.unit?label(P.unit,'src',U*.018,'Mono',700):null;if(unit){unit.style.left=W/2+'px';unit.style.top=(H-U*.05)+'px'}
  update=t=>{orbit(t,o);if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);if(unit)unit.style.opacity=seg(t,.6,.3)*leave(t);
    bars.forEach((b,i)=>{const p=E.back(seg(t,.35+i*.22,.75)),h=Math.max(.001,b.h*p);b.m.scale.y=h;b.m.position.y=h/2;
      pin(b.val,new THREE.Vector3(b.m.position.x,h+.02,0),0,-U*.04);pin(b.nm,new THREE.Vector3(b.m.position.x,0,w*.9),0,U*.03);
      const q=seg(t,.35+i*.22,.75);b.val.textContent=pre(b.v.shown)+(b.v.value*q).toFixed(dec(b.v.shown))+suf(b.v.shown);
      b.val.style.opacity=seg(t,.45+i*.22,.2)*leave(t);b.nm.style.opacity=seg(t,.3+i*.22,.2)*leave(t)})}}

function prism(){const [x0,y0,x1,y1]=P.box,kx=Math.cos((y0+y1)/2*Math.PI/180),span=Math.max((x1-x0)*kx,(y1-y0)*1.2),s=(TALL?9:13)/span,cx=(x0+x1)/2,cy=(y0+y1)/2;
  const shape=r=>{const sh=new THREE.Shape();r.forEach((q,i)=>{const x=(q[0]-cx)*kx*s,y=(q[1]-cy)*s;i?sh.lineTo(x,y):sh.moveTo(x,y)});return sh};
  const flat=new THREE.Group();P.others.forEach(r=>{const m=new THREE.Mesh(new THREE.ExtrudeGeometry(shape(r),{depth:.05,bevelEnabled:false}),mat(K.land||'#EFE3C2'));m.receiveShadow=true;flat.add(inked(m,K.edge||'#8E7E5C'))});
  flat.rotation.x=-Math.PI/2;scene.add(flat);
  const vs=P.items.map(i=>i.value),mn=Math.min(...vs),mx=Math.max(...vs),lo=mix(K.land||'#EFE3C2',ACC,.25),maxh=TALL?2.4:2.0,tt=title(P.title);
  const order=P.items.slice().sort((a,b)=>a.value-b.value);
  const ps=order.map((it,i)=>{const f=mx>mn?(it.value-mn)/(mx-mn):1,g=new THREE.Group();
    it.rings.forEach(r=>{const m=new THREE.Mesh(new THREE.ExtrudeGeometry(shape(r),{depth:1,bevelEnabled:false}),mat(mix(lo,ACC,f)));m.castShadow=m.receiveShadow=true;g.add(inked(m))});
    g.rotation.x=-Math.PI/2;scene.add(g);const h=.35+maxh*(it.value/mx);
    return {g,h,it,pos:new THREE.Vector3((it.at[0]-cx)*kx*s,0,-(it.at[1]-cy)*s),val:label(it.shown,'box',U*.036,'Anton',400),nm:label(it.label,'tag',U*.016,'Inter',800)}});
  const o={tx:0,ty:.4,tz:0,a0:-.14,a1:.3,r0:TALL?30:24,r1:TALL?26:20,h0:TALL?34:26,h1:TALL?20:14};
  const unit=P.unit?label(P.unit,'src',U*.018,'Mono',700):null;if(unit){unit.style.left=W/2+'px';unit.style.top=(H-U*.05)+'px'}
  update=t=>{orbit(t,o);if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);if(unit)unit.style.opacity=seg(t,.6,.3)*leave(t);
    ps.forEach((p,i)=>{const q=E.out(seg(t,.7+i*.28,.9)),h=Math.max(.05,p.h*q);p.g.scale.z=h;
      const top=p.pos.clone();top.y=h;pin(p.val,top,0,-U*.045);pin(p.nm,top,0,-U*.008);
      p.val.style.opacity=seg(t,1.0+i*.28,.25)*leave(t);p.nm.style.opacity=seg(t,1.0+i*.28,.25)*leave(t)})}}

function partMesh(name,w,d){const n=name.toLowerCase(),g=new THREE.Group();const add=(geo,m,x,y,z)=>{const me=inked(new THREE.Mesh(geo,m));me.position.set(x||0,y||0,z||0);me.castShadow=me.receiveShadow=true;g.add(me);return me};
  if(/glass|screen|display|lens|window|panel/.test(n)){add(new THREE.BoxGeometry(w,.07,d),mat(/glass|lens|window/.test(n)?'#9FC4D6':'#1F2A33',{roughness:.2,metalness:.3,transparent:true,opacity:/glass|lens|window/.test(n)?.55:1}))}
  else if(/batter|cell|tank|fuel/.test(n)){add(new THREE.BoxGeometry(w*.62,.3,d*.78),mat(ACC));add(new THREE.BoxGeometry(w*.1,.12,d*.3),mat('#46525C'),w*.36,0,0)}
  else if(/board|chip|logic|circuit|processor|motherboard|engine|motor/.test(n)){add(new THREE.BoxGeometry(w*.9,.06,d*.9),mat('#2F6B4F'));
    [[-.25,.2,.22,.2],[.15,-.1,.3,.26],[.28,.28,.14,.14],[-.2,-.25,.18,.12]].forEach(([x,z,a,b])=>add(new THREE.BoxGeometry(w*a,.1,d*b),mat('#22272B',{roughness:.5}),w*x,.08,d*z))}
  else if(/camera|sensor|speaker|fan|wheel|gear/.test(n)){add(new THREE.BoxGeometry(w*.9,.05,d*.9),mat('#D9D4C7'));[-.28,0,.28].forEach(x=>add(new THREE.CylinderGeometry(d*.13,d*.13,.16,28),mat('#22272B',{roughness:.35,metalness:.4}),w*x,.1,-d*.2))}
  else if(/case|cover|back|frame|shell|body|hull|chassis|housing/.test(n)){add(new THREE.BoxGeometry(w,.14,d),mat('#46525C'));add(new THREE.BoxGeometry(w*.9,.06,d*.9),mat('#5A6670'),0,.1,0)}
  else{add(new THREE.BoxGeometry(w*.94,.12,d*.94),mat('#D9D4C7'))}
  return g}
function explode(){const ls=P.layers,n=ls.length,w=TALL?3.0:4.4,d=TALL?5.2:2.7,gap=TALL?1.25:1.0,tt=title(P.title||P.thing);
  const parts=ls.map((nm,i)=>{const g=partMesh(nm,w,d);scene.add(g);const lb=label(nm,'tag',U*.022,'Inter',800),num=label(String(i+1),'box',U*.022,'Mono',700);return {g,lb,num}});
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('width',W);svg.setAttribute('height',H);svg.style.position='absolute';OV.insertBefore(svg,OV.firstChild);
  parts.forEach(p=>{p.ln=document.createElementNS('http://www.w3.org/2000/svg','line');p.ln.setAttribute('stroke',K.mark||'#D7262B');p.ln.setAttribute('stroke-width',Math.max(1.5,U*.003));svg.appendChild(p.ln)});
  const mid=(n-1)*gap/2+.6,o={tx:TALL?0:.9,ty:mid,tz:0,a0:.95,a1:.45,r0:TALL?17:15,r1:TALL?19:16.5,h0:mid+3.2,h1:mid+5.2};
  update=t=>{orbit(t,o);const e=E.inout(seg(t,.7,1.5));if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);
    parts.forEach((p,i)=>{const k=n-1-i;p.g.position.y=.3+k*(.16+(gap-.16)*e)+Math.sin(t*1.4+i)*.02*e;
      const a=new THREE.Vector3(w*.5,p.g.position.y,0).project(camera),ax=(a.x*.5+.5)*W,ay=(-a.y*.5+.5)*H,lx=TALL?W*.72:W*.76,ly=ay-U*.01;
      p.lb.style.left=lx+'px';p.lb.style.top=ly+'px';p.num.style.left=(ax-U*.012)+'px';p.num.style.top=ay+'px';
      const bw=p.lb.getBoundingClientRect().width;p.ln.setAttribute('x1',ax);p.ln.setAttribute('y1',ay);p.ln.setAttribute('x2',lx-bw/2-U*.008);p.ln.setAttribute('y2',ly);
      const v=seg(t,1.5+i*.14,.25)*leave(t);p.lb.style.opacity=v;p.ln.style.opacity=v;p.num.style.opacity=v})}}

function glyphs(text,size){const sc=size/FONT.resolution,out=[];let ox=0;
  for(const ch of text){const g=FONT.glyphs[ch]||FONT.glyphs['?'];if(!g)continue;
    if(g.o){const path=new THREE.ShapePath(),o=g.o.split(' ');for(let i=0;i<o.length;){const a=o[i++];
        if(a==='m')path.moveTo(o[i++]*sc,o[i++]*sc);else if(a==='l')path.lineTo(o[i++]*sc,o[i++]*sc);
        else if(a==='q'){const x=o[i++]*sc,y=o[i++]*sc,x1=o[i++]*sc,y1=o[i++]*sc;path.quadraticCurveTo(x1,y1,x,y)}
        else if(a==='b'){const x=o[i++]*sc,y=o[i++]*sc,x1=o[i++]*sc,y1=o[i++]*sc,x2=o[i++]*sc,y2=o[i++]*sc;path.bezierCurveTo(x1,y1,x2,y2,x,y)}}
      out.push({shapes:path.toShapes(),x:ox,w:g.ha*sc})}
    ox+=g.ha*sc}
  return {letters:out,width:ox}}
function title3d(){const words=P.text.split(' '),rows=TALL&&words.length>1?words:[P.text];const size=1.6,all=[];
  const widest=Math.max(...rows.map(r=>glyphs(r,size).width));
  rows.forEach((r,ri)=>{const g=glyphs(r,size),y=(rows.length-1-ri)*size*1.25;g.letters.forEach(l=>{
      const geo=new THREE.ExtrudeGeometry(l.shapes,{depth:.42,bevelEnabled:true,bevelThickness:.045,bevelSize:.035,bevelSegments:3,curveSegments:8});geo.translate(-l.w/2,0,-.21);
      const m=new THREE.Mesh(geo,[mat(ACC,{roughness:.45,metalness:.15}),mat(mix(ACC,'#000000',.45))]);m.castShadow=m.receiveShadow=true;
      const piv=new THREE.Group();piv.position.set(l.x+l.w/2-g.width/2,y,0);piv.add(m);scene.add(piv);all.push(piv)})});
  const sweep=new THREE.PointLight(0xffffff,60,14);scene.add(sweep);
  const sub=P.sub?label(P.sub,'tag',U*.026,'Inter',800):null;if(sub){sub.style.left=W/2+'px';sub.style.top=(TALL?H*.74:H*.82)+'px'}
  const hh=rows.length*size*1.25,fit=Math.max(widest*(TALL?2.5:1.25),hh*2.2),o={tx:0,ty:hh*.42,tz:0,a0:-.34,a1:.16,r0:fit*1.3,r1:fit*1.12,h0:hh*.9+1.2,h1:hh*.5+.5};
  update=t=>{orbit(t,o);all.forEach((p,i)=>{const q=E.back(seg(t,.15+i*.07,.7));p.rotation.x=-Math.PI/2*(1-q);p.scale.setScalar(.001+q)});
    const s=seg(t,1.2,1.4);sweep.position.set(-widest*.7+widest*1.4*s,hh*.6,2.6);sweep.intensity=60*Math.sin(Math.PI*s);
    if(sub)sub.style.opacity=seg(t,1.3,.3)*leave(t)}}

function terrain3d(){const G=P.grid,n=G.n,size=12,rel=Math.max(1,G.max-G.min),ex=Math.min(4.2,Math.max(1.6,P.km*1000/rel*.085))*size/(P.km*1000);   // vertical exaggeration, capped
  const geo=new THREE.PlaneGeometry(size,size,n-1,n-1);geo.rotateX(-Math.PI/2);const pos=geo.attributes.position,cols=new Float32Array(pos.count*3);
  const ramp=[[0,K.land||'#EFE3C2'],[.35,mix(K.land||'#EFE3C2','#8E7E5C',.55)],[.7,mix('#8E7E5C','#5B5346',.6)],[.9,'#E9E6DF'],[1,'#FFFFFF']].map(([t,c])=>[t,col(c)]);
  const shade=f=>{for(let i=1;i<ramp.length;i++)if(f<=ramp[i][0]){const a=ramp[i-1],b=ramp[i];return a[1].clone().lerp(b[1],(f-a[0])/(b[0]-a[0]))}return ramp[ramp.length-1][1]};
  for(let r=0;r<n;r++)for(let c=0;c<n;c++){const i=r*n+c,h=G.h[r][c];pos.setY(i,(h-G.min)*ex);const f=h<=0&&G.min<0?-1:(h-G.min)/rel,cc=f<0?col(K.sea||'#B8CDD1'):shade(f);cols[i*3]=cc.r;cols[i*3+1]=cc.g;cols[i*3+2]=cc.b}
  geo.setAttribute('color',new THREE.BufferAttribute(cols,3));geo.computeVertexNormals();
  const land=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0,flatShading:true}));land.castShadow=land.receiveShadow=true;
  const top=rel*ex,base=new THREE.Mesh(new THREE.BoxGeometry(size,.5,size),mat(mix(K.land||'#EFE3C2','#5B5346',.5)));base.position.y=-.26;base.receiveShadow=true;
  const g=new THREE.Group();g.add(land);g.add(inked(base));g.position.y=.55;scene.add(g);
  sun.position.set(-9,7.5,5);sun.intensity=2.6;
  const [pr,pc]=G.peak,peak=new THREE.Vector3(-size/2+pc/(n-1)*size,.55+top,-size/2+pr/(n-1)*size);
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(.02,.02,1.1,6),mat(K.mark||'#D7262B'));pole.position.copy(peak).y+=.55;scene.add(pole);
  const tt=title(P.title||P.name),pk=label(P.name.toUpperCase(),'tag',U*.024,'Inter',800),el=label(P.height||('about '+(Math.round((G.top||G.max)/50)*50).toLocaleString('en-US')+' m'),'box',U*.04,'Anton',400);   // the writer's figure, else the data's, said as 'about'
  const cr=label(P.credit,'src',U*.013,'Mono',700);cr.style.left=W/2+'px';cr.style.top=(H-U*.03)+'px';
  const sc=label(Math.round(P.km)+' km across','src',U*.018,'Mono',700);sc.style.left=(TALL?W/2:W*.14)+'px';sc.style.top=(TALL?H*.9:H*.9)+'px';
  const o={tx:0,ty:.55+top*.4,tz:0,a0:-.75,a1:.55,r0:TALL?30:22,r1:TALL?25:17.5,h0:top+9,h1:top+4.5};
  update=t=>{orbit(t,o);const rise=E.out(seg(t,0,1.4));g.scale.y=.02+.98*rise;pole.scale.y=seg(t,1.3,.4);pole.visible=t>1.3;
    const p2=peak.clone();p2.y=.55+top*rise+1.15*seg(t,1.3,.4);pin(el,p2,0,-U*.05);pin(pk,p2,0,-U*.012);
    const v=seg(t,1.5,.3)*leave(t);el.style.opacity=v;pk.style.opacity=v;if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);cr.style.opacity=seg(t,.8,.3)*leave(t)*.9;sc.style.opacity=seg(t,.8,.3)*leave(t)}}
function towers3d(){const vs=P.values,n=vs.length,mx=Math.max(...vs.map(v=>v.value)),maxh=TALL?6.6:4.6,gap=2.5,x0=-(n-1)*gap/2,tt=title(P.title);
  const order=vs.map((v,i)=>i);const ts=order.map(i=>{const v=vs[i],h=Math.max(.12,maxh*v.value/mx),g=new THREE.Group(),top=v.value===mx;
    const tiers=h>1.2?3:h>.5?2:1;let y=0;for(let k=0;k<tiers;k++){const th=h*(k===tiers-1?1-(tiers-1)*.38:.38),w=1.15*(1-k*.24);
      const floors=Math.max(1,Math.round(th/.16));const m=new THREE.Mesh(new THREE.BoxGeometry(w,th,w,1,floors,1),mat(top?ACC:(k%2?'#5A6670':'#46525C')));
      m.position.y=y+th/2;m.castShadow=m.receiveShadow=true;g.add(m);
      const fl=new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.BoxGeometry(w*1.002,th,w*1.002,1,floors,1)),new THREE.LineBasicMaterial({color:col(top?mix(ACC,'#000000',.35):'#2B343B'),transparent:true,opacity:.55}));fl.position.y=y+th/2;g.add(fl);y+=th}
    if(tiers>1){const sp=new THREE.Mesh(new THREE.CylinderGeometry(.015,.05,h*.06,6),mat('#2B343B'));sp.position.y=h+h*.03;g.add(sp)}
    g.position.set(x0+i*gap,0,0);scene.add(g);const pl=new THREE.Mesh(new THREE.BoxGeometry(1.7,.05,1.7),mat('#FBF8F0'));pl.position.set(x0+i*gap,.025,0);pl.receiveShadow=true;scene.add(inked(pl));
    return {g,h,v,val:label(v.shown+(/[a-z]/i.test(v.shown)?'':' '+P.unit),'val',U*.044,'Anton',400),nm:label(v.label,'tag',U*.019,'Inter',800)}});
  // a person, for scale, when the tallest is under a kilometre: 1.8 m at the same scale
  const ph=maxh*1.8/mx;if(ph>.012){const man=new THREE.Mesh(new THREE.BoxGeometry(ph*.3,ph,ph*.2),mat(K.mark||'#D7262B'));man.position.set(x0-gap*.55,ph/2,1.2);scene.add(man)}
  const span=(n-1)*gap+1.7,o={tx:0,ty:maxh*.48,tz:0,a0:.55,a1:-.35,r0:Math.max(18,span*(TALL?3.3:2.0)),r1:Math.max(16.5,span*(TALL?3.0:1.8)),h0:maxh*.6,h1:maxh*1.1};
  update=t=>{orbit(t,o);if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);
    ts.forEach((b,i)=>{const p=E.out(seg(t,.3+i*.3,1.0));b.g.scale.y=Math.max(.001,p);
      pin(b.val,new THREE.Vector3(b.g.position.x,b.h*p*1.08,0),0,-U*.036);pin(b.nm,new THREE.Vector3(b.g.position.x,0,1.25),0,U*.03);
      b.val.style.opacity=seg(t,.9+i*.3,.25)*leave(t);b.nm.style.opacity=seg(t,.3+i*.3,.2)*leave(t)})}}

({bars3d,prism,explode,title3d,terrain3d,towers3d})[P.type]();
document.fonts.ready.then(()=>{window.frame=t=>{update(t);renderer.render(scene,camera)};window.frame(0);window.READY=true});
</script></body></html>"""


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           fps: int | None = None) -> Path:
    """Renders one 3D scene into `out` (H.264)."""
    from . import motion, vox
    if not motion.enabled():
        raise MediaError("3D scenes need the animation engine (Chromium + Playwright)")
    plan = plan_for(kind, spec)
    if plan is None:
        raise MediaError(f"3d: nothing to draw from {spec!r}")
    if kind == "terrain3d":
        cache = Path(os.environ.get("CF_TERRAIN") or Path(os.environ.get("CF_DATA_DIR", "./creatorforge-data")) / "terrain")
        plan["grid"] = heights(plan["lat"], plan["lon"], plan["km"], cache)
        if plan["grid"]["max"] - plan["grid"]["min"] < 30:
            raise MediaError("terrain: this place is flat; a map shows it better")
    look = vox.look_of(theme)
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(2.0, float(seconds))
    bg, grain = vox.paper(look["paper"], width, height, work)
    kit = {"acc": vox.accent_of(theme), "mark": look["mark"], "land": look["land"], "edge": look["edge"], "sea": look["sea"],
           "fam": {"Playfair": look["head"], "Anton": look["big"], "Caveat": look["hand"]}}
    page = (_PAGE.replace("%THREE%", (VENDOR / "three.min.js").read_text(encoding="utf-8"))
            .replace("%FONT%", (VENDOR / "helvetiker_bold.typeface.json").read_text(encoding="utf-8") if kind == "title3d" else "null")
            .replace("%FONTS%", vox._font_css()).replace("%PAPER%", look["paper"]).replace("%BG%", bg.as_uri())
            .replace("%GRAIN%", grain.as_uri()).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{seconds:.3f}")
            .replace("%KIT%", json.dumps(kit)))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"s3d_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    return motion.capture(html, width, height, seconds, fps, out)
