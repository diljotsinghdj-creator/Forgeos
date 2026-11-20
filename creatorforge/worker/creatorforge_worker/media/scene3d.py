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
    Planets: Jupiter, Earth | 1,300 Earths fit inside | move: fill | n: 1300
             - planets drawn in 3D with painted surfaces (Earth from the real coastlines), lit by the Sun:
               compare (side by side at true scale), fill (small bodies pouring into a big one, ILLUSTRATIVE), spin

They carry the video's look (paper, accent, fonts) so they sit in the same film as the 2D scenes.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .ff import MediaError

KINDS = ("bars3d", "prism", "explode", "title3d", "terrain3d", "towers3d", "photo3d", "planets")
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
    # "THE POST: your screen; THE SIGN-OFF: one official..." - with ";" each layer may carry a description after ":"
    sep = ";" if ";" in parts[1] else ","
    layers = [x.strip()[:70] for x in parts[1].split(sep) if x.strip()][:7]
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
    opt = {k: v.strip() for p in parts[2:] for k, _, v in [p.partition(":")] if v}
    opt = {k.strip().lower(): v for k, v in opt.items()}
    # "water: 53.4 -> 26.5": a water surface at those heights (metres above sea level) that fills the real terrain and
    # drains to the second level; "years: 1960 -> 2009" counts with it; "pins: Moynaq, Aralsk" names places
    water = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", opt.get("water", ""))][:2]
    # "-> floor": drain to the lowest surface the elevation data holds (radar maps a lake's water surface as land, so
    # draining below it would show water that is there as gone)
    if water and re.search(r"floor", opt.get("water", ""), re.I):
        water = water[:1] + [-9999.0]
    years = [int(x) for x in re.findall(r"\d{4}", opt.get("years", ""))][:2]
    pins = []
    for nm in [x.strip() for x in opt.get("pins", "").split(",") if x.strip()][:6]:
        f = maps._find(nm)
        if f and f["kind"] == "city":
            pins.append({"name": nm[:22], "lat": f["lat"], "lon": f["lon"]})
    return {"type": "terrain3d", "name": name[:28], "lat": lat, "lon": lon, "km": min(600.0, max(8.0, km)), "height": hm[:16],
            "water": water, "years": years, "pins": pins,
            # "gauge: Sea level" reads the water's height out as it moves; "rise: off" starts on the finished land
            # (a continuation of the shot before, so the land does not grow out of the table again)
            "gauge": opt.get("gauge", "")[:24], "norise": opt.get("rise", "").lower() in ("off", "no", "none"),
            "title": parts[1][:48] if len(parts) > 1 else "", "credit": TERRAIN_CREDIT}


def heights(lat: float, lon: float, km: float, cache: Path, n: int = 150, timeout: float = 30) -> dict:
    """An n x n grid of elevations (metres) for a square `km` wide round a point, from the open terrain tiles
    (downloaded once into `cache`). {"h": [[...]], "min", "max", "peak": (row, col)}"""
    import io
    import math
    import urllib.request
    import numpy as np
    from PIL import Image
    z = int(max(4, min(12, math.floor(math.log2(40075.0 * math.cos(math.radians(lat)) / km * 1.6)))))

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
    dlat_, dlon_ = dlat, dlon
    r, c = np.unravel_index(int(grid.argmax()), grid.shape)
    # the label uses the full-resolution data (the drawn grid is thinned and rounds the summit off)
    return {"h": [[int(v) for v in row] for row in grid], "min": float(grid.min()), "max": float(grid.max()),
            "top": float(crop.max()),
            "peak": [int(r), int(c)], "n": n, "dlat": dlat_, "dlon": dlon_}


def parse_towers3d(spec: str) -> dict | None:
    """'Towers3d: Burj Khalifa 828, Shanghai Tower 632, Eiffel Tower 330, Qutub Minar 73 | How tall? | m' - buildings
    to scale as stepped 3D towers with their floors marked (the massing of a height, not a model of the building)."""
    from . import vox
    parts = [p.strip() for p in (spec or "").split("|")]
    water = 0.0
    keep = []
    for x in parts[1:]:
        m = re.match(r"\s*water\s*[:=]\s*([\d.,]+)", x, re.I)
        if m:
            water = float(m.group(1).replace(",", ""))     # the sea rising to this height around them
        else:
            keep.append(x)
    vals = [v for v in vox._pairs(parts[0]) if v["value"] > 0 and v["label"]][:6]
    if len(vals) < (1 if water else 2):
        return None
    return {"type": "towers3d", "values": vals, "title": keep[0][:60] if keep else "",
            "unit": keep[1][:10] if len(keep) > 1 else "m", "water": water}


def parse_photo3d(spec: str) -> dict | None:
    """'Photo3d: asset:P0007 | dolly | The old harbour' - camera projection: the photograph is projected onto its own
    depth (a mesh displaced by the estimated depth) and a real 3D camera moves through it: dolly (in), orbit (a slow
    turn), tilt-left / tilt-right (the picture as a print turning in space, for a perspective reveal)."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    move = next((p.lower() for p in parts[1:] if p.lower() in ("dolly", "orbit", "tilt-left", "tilt-right")), "dolly")
    title = next((p for p in parts[1:] if p.lower() not in ("dolly", "orbit", "tilt-left", "tilt-right", "illustrative") and ":" not in p), "")
    return {"type": "photo3d", "path": parts[0], "move": move, "title": title[:60],
            "illustrative": any(p.lower() == "illustrative" for p in parts[1:])}



# mean radius in km (NASA planetary fact sheets)
BODIES = {"sun": 696340, "mercury": 2440, "venus": 6052, "earth": 6371, "moon": 1737, "mars": 3390, "jupiter": 69911,
          "saturn": 58232, "uranus": 25362, "neptune": 24622, "pluto": 1188}


def parse_planets(spec: str) -> dict | None:
    """'Planets: Jupiter, Earth | 1,300 Earths fit inside | move: fill | n: 1300'."""
    parts = [p.strip() for p in (spec or "").split("|")]
    names = [x.strip().lower() for x in re.split(r",|\+|·| vs ", parts[0]) if x.strip()] if parts else []
    if not names or any(n not in BODIES for n in names) or len(names) > 6:
        return None
    opts, free = {}, []
    for x in parts[1:]:
        k, _, v = x.partition(":")
        if _ and k.strip().lower() in ("move", "n"):      # only these are settings; a colon in a title is part of it
            opts[k.strip().lower()] = v.strip()
        else:
            free.append(x)
    move = opts.get("move", "spin" if len(names) == 1 else "compare").lower()
    if move not in ("spin", "compare", "fill") or (move == "fill" and len(names) != 2):
        return None
    n = int(re.sub(r"\D", "", opts.get("n", "")) or 0)
    plan = {"type": "planets", "bodies": [{"name": x, "r": BODIES[x]} for x in names], "title": (free[0] if free else "")[:60],
            "move": move, "count": n, "illustrative": move == "fill"}
    if "earth" in names:
        from . import maps
        w = json.loads((Path(__file__).with_name("world.json")).read_text(encoding="utf-8"))
        plan["land"] = [ring for c in w["countries"] for ring in c["r"] if len(ring) > 3]
    return plan


PARSERS = {"planets": parse_planets, "photo3d": parse_photo3d, "terrain3d": parse_terrain3d, "towers3d": parse_towers3d, "bars3d": parse_bars3d, "prism": parse_prism, "explode": parse_explode, "title3d": parse_title3d}


def plan_for(kind: str, spec: str) -> dict | None:
    fn = PARSERS.get(kind)
    iso = bool(re.search(r"\|\s*isometric\s*(\||$)", spec or "", re.I))
    plan = fn(re.sub(r"\|\s*isometric\s*(?=\||$)", "", spec or "", flags=re.I)) if fn else None
    if plan is not None and iso:
        plan["iso"] = True            # an isometric (orthographic) camera: the technical-drawing view of the same scene
    return plan


_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
html,body{margin:0;padding:0;overflow:hidden;width:%W%px;height:%H%px;background:%PAPER% url('%BG%') center/cover}
canvas{position:absolute;left:0;top:0}
#ov{position:absolute;left:0;top:0;width:%W%px;height:%H%px;pointer-events:none}
#grain{position:absolute;left:0;top:0;width:%W%px;height:%H%px;background:url('%GRAIN%') center/cover;mix-blend-mode:multiply;opacity:.5}
.t{position:absolute;white-space:nowrap;transform:translate(-50%,-50%)}
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
const scene=new THREE.Scene();let camera=new THREE.PerspectiveCamera(TALL?44:30,W/H,.1,500);
if(P.iso){const f=TALL?11:8;camera=new THREE.OrthographicCamera(-f*W/H,f*W/H,f,-f,.1,600)}   // isometric: no perspective, true proportions
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
  if(P.iso){const a2=Math.PI/4+(o.a1-o.a0)*.15*p,R=60;camera.position.set(o.tx+Math.sin(a2)*R,o.ty+R*.82,o.tz+Math.cos(a2)*R);camera.lookAt(o.tx,o.ty,o.tz);
    camera.zoom=(TALL?11:8)/Math.max(3,o.r0*.3);camera.updateProjectionMatrix();camera.lookAt(o.tx,o.ty,o.tz);return}
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
function phoneSlab(i,n,w,d){ // a phone's layer: a rounded slab; the top one is the lit screen with the signature edge
  const r=Math.min(w,d)*.16,sh=new THREE.Shape();sh.moveTo(-w/2+r,-d/2);sh.lineTo(w/2-r,-d/2);sh.quadraticCurveTo(w/2,-d/2,w/2,-d/2+r);
  sh.lineTo(w/2,d/2-r);sh.quadraticCurveTo(w/2,d/2,w/2-r,d/2);sh.lineTo(-w/2+r,d/2);sh.quadraticCurveTo(-w/2,d/2,-w/2,d/2-r);
  sh.lineTo(-w/2,-d/2+r);sh.quadraticCurveTo(-w/2,-d/2,-w/2+r,-d/2);
  const geo=new THREE.ExtrudeGeometry(sh,{depth:.12,bevelEnabled:true,bevelThickness:.02,bevelSize:.02,bevelSegments:2,curveSegments:10});geo.rotateX(-Math.PI/2);
  const top=i===0,cols=['#2A2A2E','#3A3A40','#4A4A52','#5A5A64','#6A6A74','#7A7A84','#8A8A94'];
  const m=new THREE.Mesh(geo,mat(top?'#16161A':cols[Math.min(i,cols.length-1)],{roughness:top?.15:.55,metalness:top?.3:.1}));m.castShadow=m.receiveShadow=true;
  const g=new THREE.Group();g.add(inked(m,top?(K.sig||'#FFDD33'):'#8A8A94'));
  if(top){const glow=new THREE.Mesh(new THREE.PlaneGeometry(w*.86,d*.9),new THREE.MeshBasicMaterial({color:col(K.sig||'#FFDD33'),transparent:true,opacity:.62}));glow.rotation.x=-Math.PI/2;glow.position.y=.16;g.add(glow)}
  return g}
function explode(){const ls=P.layers,n=ls.length,phone=/phone|mobile/i.test(P.thing),w=phone?(TALL?2.6:2.2):(TALL?3.0:4.4),d=phone?(TALL?5.0:4.2):(TALL?5.2:2.7),gap=TALL?1.25:1.0,tt=title(P.title||P.thing);
  const parts=ls.map((nm,i)=>{const g=phone?phoneSlab(i,n,w,d):partMesh(nm,w,d);scene.add(g);const [head,...rest]=nm.split(':');
    const lb=label(head.trim(),'tag',U*.022,'Inter',800),num=label(String(i+1),'box',U*.022,'Mono',700);
    if(phone&&i===0){lb.style.background=K.sig||'#FFDD33';lb.style.color='#141414'}
    const ds=rest.length?label(rest.join(':').trim(),'src',U*.017,'Inter',600):null;return {g,lb,num,ds}});
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('width',W);svg.setAttribute('height',H);svg.style.position='absolute';OV.insertBefore(svg,OV.firstChild);
  parts.forEach(p=>{p.ln=document.createElementNS('http://www.w3.org/2000/svg','line');p.ln.setAttribute('stroke',K.mark||'#D7262B');p.ln.setAttribute('stroke-width',Math.max(1.5,U*.003));svg.appendChild(p.ln)});
  const side=phone&&TALL;   // a tall frame: the phone stands right, the labels in a column on the left
  const mid=(n-1)*gap/2+.6,o={tx:side?-2.1:TALL?0:.9,ty:mid,tz:0,a0:.95,a1:.45,r0:TALL?17:15,r1:TALL?19:16.5,h0:mid+3.2,h1:mid+5.2};
  update=t=>{orbit(t,o);const e=E.inout(seg(t,.7,1.5));if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);
    parts.forEach((p,i)=>{const k=n-1-i;p.g.position.y=.3+k*(.16+(gap-.16)*e)+Math.sin(t*1.4+i)*.02*e;
      const a=new THREE.Vector3(side?-w*.5:w*.5,p.g.position.y,0).project(camera),ax=(a.x*.5+.5)*W,ay=(-a.y*.5+.5)*H,ly=ay-U*.01;
      const bw=p.lb.getBoundingClientRect().width,lx=side?W*.06+bw/2:TALL?W*.72:W*.76;
      p.lb.style.left=lx+'px';p.lb.style.top=ly+'px';p.num.style.left=(ax+(side?U*.012:-U*.012))+'px';p.num.style.top=ay+'px';
      p.ln.setAttribute('x1',ax);p.ln.setAttribute('y1',ay);p.ln.setAttribute('x2',side?lx+bw/2+U*.008:lx-bw/2-U*.008);p.ln.setAttribute('y2',ly);
      if(p.ds){const dw=p.ds.getBoundingClientRect().width;p.ds.style.left=(side?W*.06+dw/2:lx)+'px';p.ds.style.top=(ly+U*.034)+'px';if(side)p.ds.style.maxWidth=(W*.42)+'px';else p.ds.style.maxWidth=(W-lx)*1.6+'px'}
      const v=seg(t,1.5+i*.14,.25)*leave(t);p.lb.style.opacity=v;p.ln.style.opacity=v;p.num.style.opacity=v;if(p.ds)p.ds.style.opacity=v})}}

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

function terrain3d(){const G=P.grid,n=G.n,size=12,rel=Math.max(1,G.max-G.min);
  // vertical exaggeration: mountains a little, plains a lot (the relief would be invisible otherwise) - always said on screen
  const exf=Math.max(1.6,Math.min(120,(P.water&&P.water.length?.07:.16)*P.km*1000/rel)),ex=exf*size/(P.km*1000);
  const geo=new THREE.PlaneGeometry(size,size,n-1,n-1);geo.rotateX(-Math.PI/2);const pos=geo.attributes.position,cols=new Float32Array(pos.count*3);
  const ramp=[[0,K.land||'#EFE3C2'],[.35,mix(K.land||'#EFE3C2','#8E7E5C',.55)],[.7,mix('#8E7E5C','#5B5346',.6)],[.9,'#E9E6DF'],[1,'#FFFFFF']].map(([t,c])=>[t,col(c)]);
  const shade=f=>{for(let i=1;i<ramp.length;i++)if(f<=ramp[i][0]){const a=ramp[i-1],b=ramp[i];return a[1].clone().lerp(b[1],(f-a[0])/(b[0]-a[0]))}return ramp[ramp.length-1][1]};
  for(let r=0;r<n;r++)for(let c=0;c<n;c++){const i=r*n+c,h=G.h[r][c];pos.setY(i,(h-G.min)*ex);const f=h<=0&&G.min<0?-1:(h-G.min)/rel,cc=f<0?col(K.sea||'#B8CDD1'):shade(f);cols[i*3]=cc.r;cols[i*3+1]=cc.g;cols[i*3+2]=cc.b}
  geo.setAttribute('color',new THREE.BufferAttribute(cols,3));geo.computeVertexNormals();
  const land=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0,flatShading:true}));land.castShadow=land.receiveShadow=true;
  const top=rel*ex,base=new THREE.Mesh(new THREE.BoxGeometry(size,.5,size),mat(mix(K.land||'#EFE3C2','#5B5346',.5)));base.position.y=-.26;base.receiveShadow=true;
  const g=new THREE.Group();g.add(land);g.add(inked(base));g.position.y=.55;scene.add(g);
  sun.position.set(-9,7.5,5);sun.intensity=2.6;
  const xz=(lat,lon)=>[(lon-P.lon)/(2*G.dlon)*size,-(lat-P.lat)/(2*G.dlat)*size];
  const hAt=(x,z)=>{const c=Math.round((x/size+.5)*(n-1)),r=Math.round((z/size+.5)*(n-1));return (G.h[Math.max(0,Math.min(n-1,r))]||[])[Math.max(0,Math.min(n-1,c))]||G.min};
  const exl=label('HEIGHT ×'+(exf>=10?Math.round(exf):exf.toFixed(1)),'src',U*.016,'Mono',700);exl.style.left=(TALL?W/2:W*.86)+'px';exl.style.top=(TALL?H*.93:H*.9)+'px';
  let wat=null,yr=null;if(P.water&&P.water.length){const [a,b]=[P.water[0],P.water.length>1?Math.max(P.water[1],G.min+.8):P.water[0]];
    wat=new THREE.Mesh(new THREE.PlaneGeometry(size*.999,size*.999),new THREE.MeshStandardMaterial({color:col(K.sea||'#7FA7B5'),roughness:.35,metalness:.05,transparent:true,opacity:.86}));
    wat.rotation.x=-Math.PI/2;wat.receiveShadow=true;g.add(wat);wat.userData={a,b};
    if(P.years&&P.years.length){yr=label(String(P.years[0]),'box',U*.06,'Anton',400);yr.style.left=(TALL?W/2:W*.13)+'px';yr.style.top=(TALL?H*.16:H*.2)+'px'}
    if(P.gauge){wat.userData.gauge=label('','box',U*.055,'Anton',400);const gg=wat.userData.gauge;gg.style.left=(TALL?W/2:W*.16)+'px';gg.style.top=(TALL?H*.2:H*.3)+'px'}}
  const pins=(P.pins||[]).map(pn=>{const [x,z]=xz(pn.lat,pn.lon);const y=.55+(Math.max(hAt(x,z),wat?Math.max(...P.water):G.min)-G.min)*ex;
    const st=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,.9,6),mat(INK));st.position.set(x,y+.45,z);scene.add(st);
    return {st,v:new THREE.Vector3(x,y+.95,z),lb:label(pn.name.toUpperCase(),'tag',U*.02,'Inter',800)}});
  const [pr,pc]=G.peak,peak=new THREE.Vector3(-size/2+pc/(n-1)*size,.55+top,-size/2+pr/(n-1)*size);
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(.02,.02,1.1,6),mat(K.mark||'#D7262B'));pole.position.copy(peak).y+=.55;scene.add(pole);
  const tt=title(P.title||P.name),pk=label(P.name.toUpperCase(),'tag',U*.024,'Inter',800),el=label(P.height||('about '+(Math.round((G.top||G.max)/50)*50).toLocaleString('en-US')+' m'),'box',U*.04,'Anton',400);   // the writer's figure, else the data's, said as 'about'
  const cr=label(P.credit,'src',U*.013,'Mono',700);cr.style.left=W/2+'px';cr.style.top=(H-U*.03)+'px';
  const sc=label(Math.round(P.km)+' km across','src',U*.018,'Mono',700);sc.style.left=(TALL?W/2:W*.14)+'px';sc.style.top=(TALL?H*.9:H*.9)+'px';
  const o={tx:0,ty:.55+top*.4,tz:0,a0:-.75,a1:.55,r0:TALL?30:22,r1:TALL?25:17.5,h0:top+9,h1:top+4.5};
  update=t=>{orbit(t,o);const rise=P.norise?1:E.out(seg(t,0,1.4));g.scale.y=.02+.98*rise;pole.scale.y=seg(t,1.3,.4);pole.visible=t>1.3;
    const p2=peak.clone();p2.y=.55+top*rise+1.15*seg(t,1.3,.4);pin(el,p2,0,-U*.05);pin(pk,p2,0,-U*.012);
    const v=seg(t,1.5,.3)*leave(t)*(wat?0:1);el.style.opacity=v;pk.style.opacity=v;pole.visible=pole.visible&&!wat;if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);cr.style.opacity=seg(t,.8,.3)*leave(t)*.9;sc.style.opacity=seg(t,.8,.3)*leave(t);
    exl.style.opacity=seg(t,.8,.3)*leave(t)*(exf>1.5?1:0);
    if(wat){const q=P.norise?E.inout(seg(t,.25,Math.max(1,DUR-1.4))):E.inout(seg(t,1.2,Math.max(1,DUR-2.2))),lev=wat.userData.a+(wat.userData.b-wat.userData.a)*q;wat.position.y=Math.max(.001,(lev-G.min)*ex*rise);wat.visible=rise>.95;
      if(wat.userData.gauge){const gg=wat.userData.gauge;gg.textContent=(P.gauge.toUpperCase()+' '+(Math.abs(lev)<.005?'':lev>0?'+':'−')+Math.abs(lev).toFixed(2)+' M');gg.style.opacity=seg(t,P.norise?.1:1,.3)*leave(t)}
      if(yr){yr.textContent=String(Math.round(P.years[0]+((P.years[1]||P.years[0])-P.years[0])*q));yr.style.opacity=seg(t,1,.3)*leave(t)}}
    pins.forEach((p,i)=>{p.st.visible=t>1.1+i*.15;pin(p.lb,p.v,0,-U*.02);p.lb.style.opacity=seg(t,1.1+i*.15,.3)*leave(t)})}}
function towers3d(){const vs=P.values,n=vs.length,mx=Math.max(...vs.map(v=>v.value)),maxh=TALL?6.6:4.6,gap=2.5,x0=-(n-1)*gap/2,tt=title(P.title);
  const order=vs.map((v,i)=>i);const ts=order.map(i=>{const v=vs[i],h=Math.max(.12,maxh*v.value/mx),g=new THREE.Group(),top=v.value===mx;
    if(/\b(ice|glacier|ice sheet|snow)\b/i.test(v.label)){   // ice is a wide slab with blue depths, not a building
      const ice=new THREE.Mesh(new THREE.BoxGeometry(3.2,h,1.8,1,1,1),new THREE.MeshStandardMaterial({color:col('#E4F3FA'),emissive:col('#5E9CC2'),emissiveIntensity:.22,roughness:.3,metalness:0,transparent:true,opacity:.94}));
      ice.position.y=h/2;ice.castShadow=ice.receiveShadow=true;g.add(inked(ice,'#7FA9C2'));
      for(let k=1;k<6;k++){const l=new THREE.Mesh(new THREE.BoxGeometry(3.212,h*.004,1.812),new THREE.MeshBasicMaterial({color:col('#A9CFE3')}));l.position.y=h*k/6;g.add(l)}   // annual layers
      g.position.set(x0+i*gap,0,0);scene.add(g);const pl=new THREE.Mesh(new THREE.BoxGeometry(3.5,.05,2.1),mat('#6E7B86'));pl.position.set(x0+i*gap,.025,0);scene.add(pl);
      return {g,h,v,val:label(v.shown+(/[a-z]/i.test(v.shown)?'':' '+P.unit),'val',U*.044,'Anton',400),nm:label(v.label,'tag',U*.019,'Inter',800)}}
    if(/\bburj khalifa\b/i.test(v.label)){   // a needle: stacked setbacks that taper into a long spire (base about a fifth of its height)
      const w0=h*.2,glass=k=>mat(top?ACC:(k%2?'#8FA3B1':'#7A8E9C'));let y=0;const steps=7;
      for(let k=0;k<steps;k++){const th=h*.72/steps,w=w0*(1-k*.12);const m=new THREE.Mesh(new THREE.CylinderGeometry(w*.5,w*.55,th,6),glass(k));
        m.position.y=y+th/2;m.castShadow=m.receiveShadow=true;g.add(inked(m,'#4A5A66'));y+=th}
      const sp=new THREE.Mesh(new THREE.CylinderGeometry(h*.004,w0*.1,h*.28,6),mat('#9AAAB6'));sp.position.y=y+h*.14;sp.castShadow=true;g.add(sp);
      g.position.set(x0+i*gap,0,0);scene.add(g);const pl=new THREE.Mesh(new THREE.BoxGeometry(Math.max(.5,w0*1.4),.05,Math.max(.5,w0*1.4)),mat('#FBF8F0'));pl.position.set(x0+i*gap,.025,0);pl.receiveShadow=true;scene.add(inked(pl));
      return {g,h,v,val:label(v.shown+(/[a-z]/i.test(v.shown)?'':' '+P.unit),'val',U*.044,'Anton',400),nm:label(v.label,'tag',U*.019,'Inter',800)}}
    if(/\b(big ben|elizabeth tower|clock tower)\b/i.test(v.label)){   // a clock tower: stone shaft, clock stage with four dials, belfry, spire roof
      const w=Math.max(.42,h*.13),stone=mat('#CBB68C'),dark=mat('#3B4148'),gold=mat('#C9A227');
      const add=(geo,m,y,ry)=>{const o=new THREE.Mesh(geo,m);o.position.y=y;if(ry)o.rotation.y=ry;o.castShadow=o.receiveShadow=true;g.add(o);return o};
      add(new THREE.BoxGeometry(w,h*.58,w,1,Math.max(1,Math.round(h*.58/.18)),1),stone,h*.29);
      inked(g.children[g.children.length-1],'#8C7650');
      add(new THREE.BoxGeometry(w*1.16,h*.15,w*1.16),stone,h*.655);
      for(let k=0;k<4;k++){const a=k*Math.PI/2,f=new THREE.Group(),d=new THREE.Mesh(new THREE.CircleGeometry(w*.42,40),new THREE.MeshBasicMaterial({color:col('#FBF6E4')}));
        const rim=new THREE.Mesh(new THREE.RingGeometry(w*.42,w*.47,40),gold);f.add(d);f.add(rim);
        const hh=new THREE.Mesh(new THREE.PlaneGeometry(w*.035,w*.24),new THREE.MeshBasicMaterial({color:col('#222')}));hh.position.set(w*.07,w*.07,.002);hh.rotation.z=-.8;f.add(hh);
        const mh=new THREE.Mesh(new THREE.PlaneGeometry(w*.025,w*.36),new THREE.MeshBasicMaterial({color:col('#222')}));mh.position.set(0,w*.16,.003);f.add(mh);
        f.position.set(Math.sin(a)*w*.585,h*.655,Math.cos(a)*w*.585);f.rotation.y=a;g.add(f)}
      add(new THREE.BoxGeometry(w*1.02,h*.09,w*1.02),stone,h*.775);
      add(new THREE.BoxGeometry(w*.8,h*.07,w*.8),dark,h*.855);                                      // the open belfry, in shadow
      add(new THREE.ConeGeometry(w*.78,h*.12,4),dark,h*.95,Math.PI/4);                                // the iron spire roof
      add(new THREE.CylinderGeometry(.008,w*.05,h*.03,6),gold,h*.985);
      for(const [sx,sz] of [[1,1],[1,-1],[-1,1],[-1,-1]])add(new THREE.ConeGeometry(w*.07,h*.07,4),dark,h*.765,Math.PI/4).position.set(sx*w*.5,h*.765+h*.035,sz*w*.5);
      g.position.set(x0+i*gap,0,0);scene.add(g);const pl=new THREE.Mesh(new THREE.BoxGeometry(1.7,.05,1.7),mat('#FBF8F0'));pl.position.set(x0+i*gap,.025,0);pl.receiveShadow=true;scene.add(inked(pl));
      return {g,h,v,val:label(v.shown+(/[a-z]/i.test(v.shown)?'':' '+P.unit),'val',U*.044,'Anton',400),nm:label(v.label,'tag',U*.019,'Inter',800)}}
    const tiers=h>1.2?3:h>.5?2:1;let y=0;for(let k=0;k<tiers;k++){const th=h*(k===tiers-1?1-(tiers-1)*.38:.38),w=Math.max(.18,Math.min(1.15,h*.25))*(1-k*.24);
      const floors=Math.max(1,Math.round(th/.16));const m=new THREE.Mesh(new THREE.BoxGeometry(w,th,w,1,floors,1),mat(top?ACC:(k%2?'#5A6670':'#46525C')));
      m.position.y=y+th/2;m.castShadow=m.receiveShadow=true;g.add(m);
      const fl=new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.BoxGeometry(w*1.002,th,w*1.002,1,floors,1)),new THREE.LineBasicMaterial({color:col(top?mix(ACC,'#000000',.35):'#2B343B'),transparent:true,opacity:.55}));fl.position.y=y+th/2;g.add(fl);y+=th}
    if(tiers>1){const sp=new THREE.Mesh(new THREE.CylinderGeometry(.015,.05,h*.06,6),mat('#2B343B'));sp.position.y=h+h*.03;g.add(sp)}
    g.position.set(x0+i*gap,0,0);scene.add(g);const pl=new THREE.Mesh(new THREE.BoxGeometry(1.7,.05,1.7),mat('#FBF8F0'));pl.position.set(x0+i*gap,.025,0);pl.receiveShadow=true;scene.add(inked(pl));
    return {g,h,v,val:label(v.shown+(/[a-z]/i.test(v.shown)?'':' '+P.unit),'val',U*.044,'Anton',400),nm:label(v.label,'tag',U*.019,'Inter',800)}});
  // a person, for scale, when the tallest is under a kilometre: 1.8 m at the same scale
  const ph=maxh*1.8/mx;if(ph>.012){const man=new THREE.Mesh(new THREE.BoxGeometry(ph*.3,ph,ph*.2),mat(K.mark||'#D7262B'));man.position.set(x0-gap*.55,ph/2,1.2);scene.add(man)}
  const span=(n-1)*gap+1.7,o={tx:0,ty:maxh*.48,tz:0,a0:.55,a1:-.35,r0:Math.max(18,span*(TALL?3.3:2.0)),r1:Math.max(16.5,span*(TALL?3.0:1.8)),h0:maxh*.6,h1:maxh*1.1};
  let sea=null,seaLb=null;if(P.water){const wh=maxh*P.water/mx;sea=new THREE.Mesh(new THREE.BoxGeometry(span+6,wh,9),new THREE.MeshStandardMaterial({color:col('#3E8FC7'),transparent:true,opacity:.4,roughness:.1,metalness:.1,depthWrite:false}));
    sea.userData.h=wh;sea.position.set(0,0,0);scene.add(sea);seaLb=label('+'+P.water.toLocaleString('en-US')+' '+P.unit,'box',U*.05,'Anton',400)}
  update=t=>{orbit(t,o);if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);
    if(sea){const q=E.inout(seg(t,1.2,Math.max(1,DUR-2.2))),hh=Math.max(.001,sea.userData.h*q);sea.scale.y=hh/sea.userData.h;sea.position.y=hh/2;
      pin(seaLb,new THREE.Vector3(-(span/2)-2.6,hh,3.2),0,-U*.03);seaLb.style.opacity=seg(t,1.3,.3)*leave(t)}
    ts.forEach((b,i)=>{const p=E.out(seg(t,.3+i*.3,1.0));b.g.scale.y=Math.max(.001,p);
      pin(b.val,new THREE.Vector3(b.g.position.x,b.h*p*1.08,0),0,-U*.036);pin(b.nm,new THREE.Vector3(b.g.position.x,0,1.25),0,U*.03);
      b.val.style.opacity=seg(t,.9+i*.3,.25)*leave(t);b.nm.style.opacity=seg(t,.3+i*.3,.2)*leave(t)})}}

function photo3d(){ // camera projection: the photograph on a mesh shaped by its own depth; a real camera moves through it
  let done;window.WAIT=(window.WAIT||[]).concat(new Promise(r=>done=r));const tex=new THREE.TextureLoader().load(P.data,()=>done(),()=>done());tex.colorSpace=THREE.SRGBColorSpace;   // the first frame waits for the picture
  const ar=P.w/P.h,pw=ar>=1?16:16*ar,ph=pw/ar,n=P.depth.length,m=P.depth[0].length;
  const geo=new THREE.PlaneGeometry(pw,ph,m-1,n-1),pos=geo.attributes.position;
  for(let r=0;r<n;r++)for(let c=0;c<m;c++)pos.setZ(r*m+c,P.depth[r][c]*P.relief);
  geo.computeVertexNormals();ground.visible=false;
  const mesh=new THREE.Mesh(geo,new THREE.MeshBasicMaterial({map:tex}));scene.add(mesh);
  if(P.move.startsWith('tilt')){mesh.geometry=new THREE.PlaneGeometry(pw,ph);const fr=new THREE.Mesh(new THREE.BoxGeometry(pw*1.04,ph*1.04,.05),mat('#FBF9F3'));fr.position.z=-.04;
    const g=new THREE.Group();g.add(fr);g.add(mesh);scene.add(g);g.castShadow=true;fr.castShadow=true;const dir=P.move==='tilt-left'?1:-1;
    update=t=>{const p=E.inout(cl(t/DUR));g.rotation.y=dir*(.55-.45*p);g.rotation.x=-.12+.08*p;camera.position.set(0,0,22-3*p);camera.lookAt(0,0,0)}}
  else if(P.move==='orbit'){update=t=>{const p=E.inout(cl(t/DUR)),a=-.16+.32*p;camera.position.set(Math.sin(a)*19,Math.sin(a*.5)*1.5,Math.cos(a)*19);camera.lookAt(0,0,P.relief*.4)}}
  else{update=t=>{const p=E.inout(cl(t/DUR));camera.position.set(.6*(p-.5),.3*(p-.5),20-4.2*p);camera.lookAt(0,0,P.relief*.3)}}
  camera.fov=TALL?50:36;camera.updateProjectionMatrix();
  if(P.title){const d=label(P.title.toUpperCase(),'box',U*.05,'Playfair',900);d.style.left=W/2+'px';d.style.top=(H*.86)+'px';const u0=update;update=t=>{u0(t);d.style.opacity=seg(t,.4,.4)*leave(t)}}
  if(P.credit){const c=label('PHOTO: '+P.credit.toUpperCase(),'src',U*.013,'Mono',700);c.style.left=(W-U*.04)+'px';c.style.top=(H-U*.03)+'px';c.style.transform='translate(-100%,-50%)'}
  if(P.illustrative){const b=label('ILLUSTRATIVE','src',U*.018,'Mono',700);b.style.left=(U*.12)+'px';b.style.top=(H*.08)+'px';b.style.background='#FBF8F0';b.style.padding='.3em .6em';b.style.border='2px solid #5A5A5A';b.style.opacity=.95}}

// ---- planets: painted spheres lit by the Sun --------------------------------------------------------------------
function noise2(){const p=new Uint8Array(512);for(let i=0;i<256;i++)p[i]=i;let s=7;for(let i=255;i>0;i--){s=(s*16807)%2147483647;const j=s%(i+1);[p[i],p[j]]=[p[j],p[i]]}
  for(let i=0;i<256;i++)p[i+256]=p[i];const f=t=>t*t*(3-2*t),g=(h,x,y)=>((h&1)?x:-x)+((h&2)?y:-y);
  const n=(x,y)=>{const X=Math.floor(x)&255,Y=Math.floor(y)&255;x-=Math.floor(x);y-=Math.floor(y);const u=f(x),v=f(y),a=p[X]+Y,b=p[X+1]+Y;
    return (1-v)*((1-u)*g(p[a],x,y)+u*g(p[b],x-1,y))+v*((1-u)*g(p[a+1],x,y-1)+u*g(p[b+1],x-1,y-1))};
  return (x,y,o)=>{let t=0,a=.5,fq=1;for(let i=0;i<(o||5);i++){t+=a*n(x*fq,y*fq);a*=.5;fq*=2}return t}}
const NZ=noise2();
function hex(c){const v=parseInt(c.slice(1),16);return [v>>16&255,v>>8&255,v&255]}
function lerpc(a,b,t){return a.map((v,i)=>v+(b[i]-v)*t)}
function painted(name){const cw=1024,ch=512,cv=document.createElement('canvas');cv.width=cw;cv.height=ch;const c=cv.getContext('2d');
  const img=c.createImageData(cw,ch),d=img.data;
  const pal={jupiter:['#F1E6D2','#D8B48A','#B07A55','#E9D9BE','#8E5E42'],saturn:['#F2E4BF','#E0C88E','#C9AA72','#EADBB0','#B99A63'],
    uranus:['#BFE7EA','#A6DDE2','#93D2D9','#B2E2E6','#8CCBD3'],neptune:['#4F7EDB','#3D68C4','#5A8AE3','#2F57AE','#6B97E8'],
    venus:['#EBD3A0','#E2C385','#F0DDB3','#D6B274','#F4E6C4'],mars:['#C1643A','#A9502C','#8C3F24','#D07A4C','#6E3220'],
    mercury:['#9A958F','#8A857F','#B0ABA5','#77726D','#A39E98'],moon:['#B8B5B0','#A4A19C','#C9C6C1','#8F8C88','#D3D0CB'],
    pluto:['#D9C2A6','#C2A383','#E8D8C2','#A9876A','#F0E4D4'],sun:['#FFD27A','#FFB547','#FF9E2C','#FFE29B','#FF8A1F'],earth:['#2E5E8C']}[name]||['#888','#999','#777','#aaa','#666'];
  const P5=pal.map(hex),banded={jupiter:1,saturn:1,uranus:1,neptune:1};
  for(let y=0;y<ch;y++){const lat=(.5-y/ch)*Math.PI;for(let x=0;x<cw;x++){const u=x/cw,i=(y*cw+x)*4;let col;
      if(banded[name]){const w=NZ(u*6,y/ch*3,3)*.35,b=Math.sin(lat*(name==='jupiter'?14:9)+w*4),k=(b+1)/2,k2=(NZ(u*20,y/ch*40,3)+1)/2;
        col=lerpc(lerpc(P5[0],P5[2],k),lerpc(P5[1],P5[4],k2),.35)}
      else if(name==='earth'){col=lerpc(hex('#24527E'),hex('#3B74A6'),(NZ(u*8,y/ch*4,3)+1)/2)}
      else if(name==='venus'){const s=NZ(u*3+NZ(u*2,y/ch*2,2),y/ch*6,5);col=lerpc(P5[0],P5[3],(s+1)/2)}
      else if(name==='sun'){const s=NZ(u*30,y/ch*15,4);col=lerpc(P5[0],P5[2],(s+1)/2)}
      else{const s=NZ(u*10,y/ch*5,6);col=lerpc(P5[0],P5[3],(s+1)/2);if(name==='mars'&&Math.abs(lat)>1.3)col=lerpc(col,[245,240,235],.85)}
      d[i]=col[0];d[i+1]=col[1];d[i+2]=col[2];d[i+3]=255}}
  c.putImageData(img,0,0);
  if(name==='jupiter'){c.fillStyle='rgba(196,86,58,.85)';c.beginPath();c.ellipse(cw*.62,ch*.64,cw*.035,ch*.04,0,0,Math.PI*2);c.fill()}   // the Great Red Spot
  if(name==='mercury'||name==='moon'){for(let k=0;k<160;k++){const x=(k*733%cw),y=(k*389%ch),r=2+(k*97%14);c.strokeStyle='rgba(60,58,55,.35)';c.lineWidth=1.5;c.beginPath();c.arc(x,y,r,0,7);c.stroke()}}
  if(name==='earth'&&P.land){c.fillStyle='#6F8E4F';P.land.forEach(ring=>{c.beginPath();ring.forEach(([lo,la],k)=>{const x=(lo+180)/360*cw,y=(90-la)/180*ch;k?c.lineTo(x,y):c.moveTo(x,y)});c.closePath();c.fill()});
    const g=c.createLinearGradient(0,0,0,ch);g.addColorStop(0,'rgba(255,255,255,.95)');g.addColorStop(.08,'rgba(255,255,255,0)');g.addColorStop(.88,'rgba(255,255,255,0)');g.addColorStop(1,'rgba(255,255,255,.95)');
    c.fillStyle=g;c.fillRect(0,0,cw,ch);c.fillStyle='rgba(255,255,255,.55)';
    const cl2=c.getImageData(0,0,cw,ch),dd=cl2.data;for(let y=0;y<ch;y++)for(let x=0;x<cw;x++){const v=NZ(x/cw*14,y/ch*7,6),a=Math.max(0,v-.12)*1.6;   // soft cloud bands
      if(a>0){const i=(y*cw+x)*4,k=Math.min(.75,a);dd[i]+=(255-dd[i])*k;dd[i+1]+=(255-dd[i+1])*k;dd[i+2]+=(255-dd[i+2])*k}}c.putImageData(cl2,0,0)}
  const t=new THREE.CanvasTexture(cv);t.anisotropy=4;return t}
function ringTex(){const s=512,cv=document.createElement('canvas');cv.width=cv.height=s;const c=cv.getContext('2d');
  for(let r=s*.5*.52;r<s*.5;r++){const k=(r/(s*.5)-.52)/.48,a=(.35+.5*Math.abs(Math.sin(k*22)))*(k<.62&&k>.58?.1:1);c.strokeStyle=`rgba(226,205,160,${a})`;c.beginPath();c.arc(s/2,s/2,r,0,7);c.stroke()}
  return new THREE.CanvasTexture(cv)}
function planets(){document.body.style.background='#06080D';document.getElementById('grain').style.opacity=.18;ground.visible=false;
  scene.children.filter(o=>o.isHemisphereLight).forEach(o=>o.intensity=.18);sun.position.set(-30,8,18);sun.intensity=3.2;sun.castShadow=false;
  const sg=new THREE.BufferGeometry(),sp=[];for(let i=0;i<1600;i++){const a=(i*137.5)*Math.PI/180,z=-60-((i*53)%40),r=20+((i*7919)%60);sp.push(Math.cos(a)*r*1.8,Math.sin(a)*r,z)}
  sg.setAttribute('position',new THREE.Float32BufferAttribute(sp,3));scene.add(new THREE.Points(sg,new THREE.PointsMaterial({color:0xffffff,size:.08,transparent:true,opacity:.7})));
  const bs=P.bodies,maxr=Math.max(...bs.map(b=>b.r)),S=(P.move==='spin'?3.4:TALL?2.4:3.2)/maxr;
  const make=b=>{const r=b.r*S,g=new THREE.Group(),m=b.name==='sun'?new THREE.MeshBasicMaterial({map:painted('sun')}):new THREE.MeshStandardMaterial({map:painted(b.name),roughness:.92,metalness:0});
    const me=new THREE.Mesh(new THREE.SphereGeometry(r,96,64),m);me.rotation.z=b.name==='uranus'?1.7:.05;g.add(me);
    if(b.name==='saturn'){const rg=new THREE.Mesh(new THREE.RingGeometry(r*1.25,r*2.3,128),new THREE.MeshStandardMaterial({map:ringTex(),transparent:true,side:THREE.DoubleSide,roughness:1}));rg.rotation.x=-Math.PI/2+.45;g.add(rg)}
    g.userData={r,me};scene.add(g);return g};
  const tt=P.title?title(P.title):null,lbs=[];
  if(P.move==='fill'){const big=make(bs[0]),small=bs[1],r=big.userData.r;big.userData.me.material.transparent=true;big.userData.me.material.opacity=.5;big.userData.me.material.depthWrite=false;
    const sr=small.r*S,n=Math.min(P.count||300,1400),geo=new THREE.SphereGeometry(sr,16,12),mt=new THREE.MeshStandardMaterial({map:painted(small.name),roughness:.9});
    const inst=new THREE.InstancedMesh(geo,mt,n),M=new THREE.Matrix4(),pts=[];for(let i=0;i<n;i++){let v;do{v=new THREE.Vector3((Math.random()*2-1),(Math.random()*2-1),(Math.random()*2-1))}while(v.length()>1);
      v.multiplyScalar(r-sr);pts.push(v.clone().add(new THREE.Vector3(0,r*2.2,0)).toArray().concat(v.toArray()))}
    pts.sort((a,b)=>a[4]-b[4]);inst.count=0;scene.add(inst);
    const cnt=label('0','box',U*.06,'Anton',400),nm=label(small.name.toUpperCase()+'S','tag',U*.024,'Inter',800),il=label('ILLUSTRATIVE · BY VOLUME','src',U*.016,'Mono',700);
    il.style.left=U*.04+'px';il.style.top=(H-U*.06)+'px';il.style.transform='translate(0,-50%)';il.style.background='#FBF8F0';il.style.padding='.3em .6em';il.style.fontSize=(U*.022)+'px';
    update=t=>{const p=E.inout(cl(t/DUR)),D=r*(TALL?6.2:4.6);camera.position.set(Math.sin(.25-.5*p)*D,r*.3,Math.cos(.25-.5*p)*D);camera.lookAt(0,r*.12,0);big.rotation.y=t*.15;big.userData.me.material.opacity=1-.55*seg(t,.3,.8);   // solid first, see-through as the small bodies pour in
      const k=Math.floor(n*E.out(seg(t,.4,Math.max(1,DUR-1.4))));inst.count=k;for(let i=0;i<k;i++){const q=pts[i],f=E.out(cl((t-.4-i/n*(DUR-1.4))/.5));
        M.makeTranslation(q[0]+(q[3]-q[0])*f,q[1]+(q[4]-q[1])*f,q[2]+(q[5]-q[2])*f);inst.setMatrixAt(i,M)}inst.instanceMatrix.needsUpdate=true;
      cnt.textContent=Math.round((P.count||n)*k/n).toLocaleString('en-US');cnt.style.left=W/2+'px';cnt.style.top=(H*.86)+'px';nm.style.left=W/2+'px';nm.style.top=(H*.93)+'px';
      cnt.style.opacity=nm.style.opacity=seg(t,.3,.3)*leave(t);il.style.opacity=.95*leave(t);if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t)}}
  else{const gs=bs.map(make),half=g=>g.userData.r*(bs[gs.indexOf(g)].name==='saturn'?2.3:1),tot=gs.reduce((a,g)=>a+half(g)*2,0)+(gs.length-1)*.5;let x=-tot/2;   // Saturn takes the room its rings need
    gs.forEach(g=>{const r=half(g);g.position.set(x+r,0,0);x+=r*2+.5;const lb=label(P.bodies[gs.indexOf(g)].name.toUpperCase(),'tag',U*.022,'Inter',800);lbs.push([g,lb])});
    const span=Math.max(tot,4.2);update=t=>{const p=E.inout(cl(t/DUR));const dist=(P.move==='spin'?(TALL?19:14.5):span*(TALL?2.6:1.45))*(1-.08*p);
      camera.position.set(Math.sin(-.1+.2*p)*dist,dist*.08,Math.cos(-.1+.2*p)*dist);camera.lookAt(0,0,0);gs.forEach(g=>g.children[0].rotation.y=t*.35);
      let lastR=-1e9,flip=false;lbs.forEach(([g,lb],i)=>{pin(lb,g.position.clone().add(new THREE.Vector3(0,-g.userData.r-.35,0)),0,U*.02);
        const w=lb.getBoundingClientRect().width,x=parseFloat(lb.style.left);flip=x-w/2<lastR+U*.012?!flip:false;   // crowded small bodies: alternate above / below
        if(flip)pin(lb,g.position.clone().add(new THREE.Vector3(0,g.userData.r+.35,0)),0,-U*.02);lastR=x+w/2;
        const rb=lb.getBoundingClientRect(),off=rb.bottom>H-U*.02||rb.top<U*.13;   // no room in frame (a close-up): the title names it
        lb.style.opacity=off?0:seg(t,.4+i*.12,.3)*leave(t)});
      if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t)}}}

({bars3d,prism,explode,title3d,terrain3d,towers3d,photo3d,planets})[P.type]();
window.QA=function(){const els=[...document.querySelectorAll('#ov .t')].filter(e=>parseFloat(e.style.opacity||1)>.5&&e.textContent.trim()),cut=[],over=[],small=[];
  const rs=els.map(e=>[e.textContent.trim().slice(0,30),e.getBoundingClientRect()]);
  rs.forEach(([s2,r])=>{if(r.left<-2||r.top<-2||r.right>W+2||r.bottom>H+2)cut.push(s2)});
  for(let i=0;i<rs.length;i++)for(let j=i+1;j<rs.length;j++){const a=rs[i][1],b=rs[j][1],w=Math.min(a.right,b.right)-Math.max(a.left,b.left),h=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
    if(w>0&&h>0&&w*h>.25*Math.min(a.width*a.height,b.width*b.height))over.push(rs[i][0]+' / '+rs[j][0])}
  return {text_below_floor:small,text_cut_off:cut.slice(0,8),text_overlap:over.slice(0,8)}};
Promise.all([document.fonts.ready].concat(window.WAIT||[])).then(()=>{window.frame=t=>{update(t);renderer.render(scene,camera)};window.frame(0);window.READY=true});
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
    if kind == "photo3d":
        import base64
        import io

        import numpy as np
        from PIL import Image

        from . import photo as _photo
        path, rec = _photo.resolve(plan["path"])
        im = Image.open(path).convert("RGB")
        if max(im.size) > 2048:
            k = 2048 / max(im.size)
            im = im.resize((int(im.size[0] * k), int(im.size[1] * k)), Image.LANCZOS)
        d, how = _photo._depth(im, None, person_ok=False)
        n = 96
        m = max(16, int(n * im.size[0] / im.size[1]))
        dd = np.asarray(Image.fromarray((np.clip(d, 0, 1) * 255).astype("uint8")).resize((m, n), Image.BILINEAR), np.float32) / 255
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90)
        plan.update({"data": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), "w": im.size[0], "h": im.size[1],
                     "depth": [[round(float(v), 3) for v in row] for row in dd], "relief": 1.6, "depthHow": how,
                     "credit": rec.get("credit", "")})
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
