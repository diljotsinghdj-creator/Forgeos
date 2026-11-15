"""The 27 generator frames of the 200: glowing relief (4), real physics (3), blueprint cutaways (2), glow bars (4),
hand drawings (4), box plots (2), unit grids (3), node canvases (2), globe morphs (3). Every number comes from a file
in data/ (World Bank API, NASA GISS) and is written into the source line. Pages are served over http by shoot_http.py."""
import json
import math
import statistics
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
sys.path.insert(0, "/home/user/Forgeos/creatorforge/films/taxonomy-2026-11-15")
sys.path.insert(0, "/home/user/Forgeos/creatorforge/films/vox-tools-2026-11-15")
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
sys.path.insert(0, str(D))                      # this folder first: its terrain/mask/relief write to ./maps
import physics as PH          # noqa: E402  (vox-tools: HEAD / TAIL around a Rapier scene)
import scenes3d as S3         # noqa: E402  (vox-tools: HEAD / TAIL around a bloom scene)
from taxonomy import box_plot, unit_grid, node_canvas, globe, ICONS   # noqa: E402

G = D / "html"
G.mkdir(exist_ok=True)
SIG = "#FFDD33"
OUT = {}


def wb(name, iso="WLD"):
    rows = json.loads((D / "data" / "wb" / f"{name}.json").read_text())[1]
    return sorted((int(r["date"]), float(r["value"])) for r in rows if r["value"] is not None and r["countryiso3code"] == iso)


def put(name, html):
    (G / f"{name}.html").write_text(html, encoding="utf-8")
    OUT[name] = True


# ---------------------------------------------------------------------------------------------------- relief (4)
RELIEF = {
    "relief_andes": dict(box=(-72.0, -34.2, -67.8, -31.4), z=8, country="Argentina", exag=7, base="#2B2622", hot="#D9480F", peak="#FFB070", grid="#4A1E08",
                         cam=[-30, 70, 92], look=[2, 0, -4], pins=[(-70.011, -32.653, "ACONCAGUA", "6,961 M · ARGENTINA")],
                         title="THE ROOF OF THE AMERICAS", sub="ACONCAGUA, THE HIGHEST PEAK OUTSIDE ASIA",
                         src="ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN, AWS OPEN DATA; SRTM) · BORDER: NATURAL EARTH · HEIGHT: INSTITUTO GEOGRÁFICO NACIONAL (ARGENTINA) · RELIEF EXAGGERATED 7×"),
    "relief_rift": dict(box=(34.6, -3.4, 38.6, 1.0), z=8, country="Kenya", exag=10, base="#1E2420", hot="#2FA36B", peak="#B6F0C8", grid="#0D3A24",
                        cam=[0, 92, 74], look=[0, 0, -16], pins=[(36.35, -0.77, "LAKE NAIVASHA", "ON THE RIFT FLOOR"), (37.31, -0.15, "MOUNT KENYA", "5,199 M")],
                        title="WHERE AFRICA IS SPLITTING", sub="KENYA LIT, TANZANIA DARK · THE GREGORY RIFT RUNS NORTH–SOUTH THROUGH IT",
                        src="ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN, AWS OPEN DATA; SRTM) · BORDER: NATURAL EARTH · MOUNT KENYA HEIGHT: KENYA WILDLIFE SERVICE · RELIEF EXAGGERATED 10×"),
    "relief_iceland": dict(box=(-24.6, 63.25, -13.4, 66.6), z=7, country="Iceland", exag=6, base="#1B2230", hot="#3D7BFF", peak="#CFE0FF", grid="#0E2050",
                           cam=[0, 74, 90], look=[0, 0, -3], pins=[(-21.12, 64.26, "ÞINGVELLIR", "THE PLATE BOUNDARY ON LAND")],
                           title="AN ISLAND ON A SEAM", sub="ICELAND SITS ON THE MID-ATLANTIC RIDGE, WHERE TWO PLATES PULL APART",
                           src="ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN, AWS OPEN DATA; SRTM/GMTED) · BORDER: NATURAL EARTH · PLATE BOUNDARY: USGS · RELIEF EXAGGERATED 6×"),
    "relief_atlas": dict(box=(-9.4, 30.4, -5.6, 32.4), z=8, country="Morocco", band=(.42, 1.0), exag=7, base="#2A2018", hot="#E0A21A", peak="#FFE7A3", grid="#4A3008",
                         cam=[10, 66, 90], look=[0, 0, -4], pins=[(-7.915, 31.06, "TOUBKAL", "4,167 M"), (-7.99, 31.63, "MARRAKESH", "THE CITY BELOW")],
                         title="THE WALL BEFORE THE SAHARA", sub="THE HIGH ATLAS, MOROCCO (LIT: THE HIGHEST GROUND IN VIEW) · TOUBKAL IS NORTH AFRICA'S HIGHEST PEAK",
                         src="ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN, AWS OPEN DATA; SRTM) · BORDER: NATURAL EARTH · HEIGHT: TOUBKAL NATIONAL PARK · RELIEF EXAGGERATED 7×"),
}


def relief_pages():
    import terrain
    import mask
    import relief
    card = lambda t, s, rot: (f'<div style="background:#EFE6D2;padding:12px 18px;transform:rotate({rot}deg);box-shadow:0 14px 24px rgba(0,0,0,.6);text-align:center;margin-bottom:26px">'
                              f'<div style="font:400 36px/1 Anton;color:#141414;letter-spacing:1px">{t}</div><div style="font:500 14px Plex;letter-spacing:3px;color:#7A2A20;margin-top:6px">{s}</div></div>')
    for name, r in RELIEF.items():
        if not (D / "maps" / f"{name}_h.json").is_file():
            terrain.heights(name, r["box"], r["z"])
        if "band" in r:                         # light a height band instead of a country (the box is all one country)
            from PIL import Image
            import numpy as np
            h = np.asarray(Image.open(D / "maps" / f"{name}_h8.png")).astype(float) / 255
            lo, hi = r["band"]
            Image.fromarray(((h >= lo) & (h <= hi)).astype(np.uint8) * 255).save(D / "maps" / f"{name}_mask.png")
        elif not (D / "maps" / f"{name}_mask.png").is_file():
            mask.mask(name, r["country"])
        cfg = {"exag": r["exag"], "base": r["base"], "hot": r["hot"], "peak": r["peak"], "grid": r["grid"], "line": "#FFFFFF", "fog": [100, 260],
               "bloom": [0.5, 0.4, 0.62], "glow": 0.8, "cam": r["cam"], "look": r["look"], "fov": 30, "route": [],
               "pins": [{"lon": lo, "lat": la, "html": card(t, s, (-2, 2)[i % 2])} for i, (lo, la, t, s) in enumerate(r["pins"])],
               "overlay": f'<div style="position:absolute;left:80px;top:64px"><div style="font:400 104px/0.92 Anton;color:#F3EFE6;letter-spacing:1px;width:1100px">{r["title"]}</div>'
                          f'<div style="font:500 21px Plex;letter-spacing:4px;color:{r["peak"]};margin-top:16px;width:1100px">{r["sub"]}</div>'
                          f'<div style="display:inline-block;margin-top:18px;background:{SIG};padding:6px 12px;font:500 16px Plex;letter-spacing:3px;color:#141414">REAL TERRAIN · HEIGHTS EXAGGERATED</div></div>'
                          f'<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;letter-spacing:1px;color:rgba(255,255,255,.5)">{r["src"]}</div>'}
        put(name, relief.page(name, cfg))


# ---------------------------------------------------------------------------------------------------- physics (3)
FUNNEL = r"""
// A hopper with a narrow neck: balls pour in faster than the neck lets them out, so they queue.
fixedBox(0,-.05,0,14,.05,3,'#D9D0BE');
fixedBox(0,5,-.42,30,14,.1,'#ECE5D6');
W.createCollider(RAPIER.ColliderDesc.cuboid(12,12,.1).setTranslation(0,6,.42));
const slab=(x,y,len,ang,c)=>{const q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),ang);
  W.createCollider(RAPIER.ColliderDesc.cuboid(len/2,.12,.4).setTranslation(x,y,0).setRotation({x:q.x,y:q.y,z:q.z,w:q.w}).setFriction(.2));
  const m=mesh(new THREE.BoxGeometry(len,.24,.8),c);m.position.set(x,y,0);m.quaternion.copy(q)};
const neck=.5, a=.62, L_=7.2;
slab(-neck/2-Math.cos(a)*L_/2,4.2+Math.sin(a)*L_/2,L_,-a,'#2B2D42');
slab( neck/2+Math.cos(a)*L_/2,4.2+Math.sin(a)*L_/2,L_,a,'#2B2D42');
const ballG=new THREE.SphereGeometry(.15,14,10);const balls=[];
for(let s=0;s<STEPS;s++){
  if(s%3===0&&balls.length<NBALLS){const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation((Math.random()-.5)*4,10.5+Math.random(),(Math.random()-.5)*.3).setCcdEnabled(true));
    W.createCollider(RAPIER.ColliderDesc.ball(.15).setRestitution(.1).setFriction(.3),b);
    const through=balls.length%9===0;const m=mesh(ballG,through?'#E63946':'#3A86FF',{roughness:.35});pairs.push([b,m]);balls.push(b)}
  W.step()}
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(3.5,6.2,30);cam.lookAt(3.5,5.0,0);
const OVER=`<div style="left:1260px;top:120px;width:600px"><div style="font:900 118px/0.95 Playfair;color:#141414">The<br>Bottleneck</div>
<div style="font:500 22px/1.5 Plex;letter-spacing:3px;color:#4a4a4a;margin-top:24px">WHEN WORK ARRIVES FASTER THAN THE NARROWEST STEP CAN PASS IT, A QUEUE BUILDS. ADDING MORE ON TOP DOES NOT HELP.</div>
<div style="display:inline-block;margin-top:26px;background:#FFDD33;padding:8px 14px;font:500 20px Plex;letter-spacing:3px">WIDEN THE NECK</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">REAL PHYSICS SIMULATION (RAPIER) · AN ILLUSTRATION OF AN IDEA, NOT DATA</div>`;
"""

SCALE = r"""
// A plank resting on a pivot. The loss block is made twice as dense as the gain block: the plank tips toward loss.
fixedBox(0,-.1,0,40,.1,40,'#E3DACA');
W.createCollider(RAPIER.ColliderDesc.cuboid(.8,.8,1.2).setTranslation(0,1.13,0).setRotation({x:0,y:0,z:.38268,w:.92388}).setFriction(1));
const pm=mesh(new THREE.BoxGeometry(1.6,1.6,2.4),'#2B2D42');pm.position.set(0,1.13,0);pm.rotation.z=Math.PI/4;
const plank=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(0,2.39,0));
W.createCollider(RAPIER.ColliderDesc.cuboid(6,.12,1.2).setFriction(.9).setDensity(.4),plank);
pairs.push([plank,mesh(new THREE.BoxGeometry(12,.24,2.4),'#C9A66B',{roughness:.8})]);
const block=(x,size,dens,col)=>{const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(x,2.52+size,0));
  W.createCollider(RAPIER.ColliderDesc.cuboid(size,size,size).setDensity(dens).setFriction(.9),b);const m=mesh(new THREE.BoxGeometry(size*2,size*2,size*2),col,{roughness:.6});pairs.push([b,m]);return b};
const loss=block(-4.4,.9,2.0,'#E63946');const gain=block(4.4,.9,1.0,'#3A7D44');
for(let s=0;s<STEPS;s++)W.step();
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(0,6,24);cam.lookAt(0,2.6,0);
const lp=loss.translation(),gp=gain.translation();
const pr=(x,y,z)=>{const v=new THREE.Vector3(x,y,z).project(cam);return [(v.x+1)/2*1920,(1-v.y)/2*1080]};
const [lx,ly]=pr(lp.x,lp.y+1.2,0),[gx,gy]=pr(gp.x,gp.y+1.2,0);
const OVER=`<div style="left:${lx-120}px;top:${ly-90}px;width:240px;text-align:center;font:400 54px Anton;color:#E63946">−₹100</div>
<div style="left:${gx-120}px;top:${gy-90}px;width:240px;text-align:center;font:400 54px Anton;color:#3A7D44">+₹100</div>
<div style="left:90px;top:70px;width:900px"><div style="font:900 110px/0.95 Playfair;color:#141414">Losses Weigh More</div>
<div style="font:500 22px/1.5 Plex;letter-spacing:3px;color:#4a4a4a;margin-top:20px;width:820px">IN KAHNEMAN AND TVERSKY'S EXPERIMENTS, A LOSS FELT ROUGHLY TWICE AS STRONG AS A GAIN OF THE SAME SIZE</div>
<div style="display:inline-block;margin-top:22px;background:#FFDD33;padding:8px 14px;font:500 20px Plex;letter-spacing:3px">LOSS AVERSION</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">SOURCE: TVERSKY & KAHNEMAN, "ADVANCES IN PROSPECT THEORY", J. RISK AND UNCERTAINTY, 1992 (LOSS-AVERSION COEFFICIENT ≈ 2.25) · REAL PHYSICS (RAPIER), BLOCK WEIGHTS SET TO 2:1 TO ILLUSTRATE</div>`;
"""

SAND = r"""
// Grains poured onto one spot build a cone; the slope stops at a critical angle and then slides in avalanches.
fixedBox(0,-.1,0,40,.1,40,'#E8DFC9');
const g=new THREE.SphereGeometry(.16,10,8);let n=0;const grains=[];
for(let s=0;s<STEPS;s++){
  if(s%2===0&&n<NG){const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation((Math.random()-.5)*.2,7,(Math.random()-.5)*.2).setLinearDamping(.3).setAngularDamping(12));
    W.createCollider(RAPIER.ColliderDesc.ball(.16).setFriction(.9).setRestitution(0),b);const last=n===NG-1;
    const m=mesh(g,last?'#E63946':(n%5?'#D9A441':'#C28A2C'),{roughness:.9});pairs.push([b,m]);grains.push(b);n++}
  W.step()}
const cam=new THREE.PerspectiveCamera(28,1920/1080,.1,200);cam.position.set(9,6.5,18);cam.lookAt(-1.2,1.6,0);
const OVER=`<div style="left:1150px;top:110px;width:700px"><div style="font:900 112px/0.95 Playfair;color:#141414">One Grain<br>Too Many</div>
<div style="font:500 22px/1.5 Plex;letter-spacing:3px;color:#4a4a4a;margin-top:22px;width:640px">A PILE GROWS QUIETLY UNTIL ITS SLOPE IS AS STEEP AS IT CAN HOLD. AFTER THAT, ANY GRAIN CAN SET OFF A SLIDE, SMALL OR HUGE.</div>
<div style="display:inline-block;margin-top:24px;background:#FFDD33;padding:8px 14px;font:500 20px Plex;letter-spacing:3px">SELF-ORGANISED CRITICALITY</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">IDEA: BAK, TANG & WIESENFELD, PHYSICAL REVIEW LETTERS 59, 1987 · REAL PHYSICS SIMULATION (RAPIER) OF POURED GRAINS</div>`;
"""


def physics_pages():
    put("physics_bottleneck", PH.HEAD + "const STEPS=2600;const NBALLS=760;\n" + FUNNEL + PH.TAIL)
    put("physics_scale", PH.HEAD + "const STEPS=420;\n" + SCALE + PH.TAIL)
    put("physics_sandpile", PH.HEAD + "const STEPS=3400;const NG=1300;\n" + SAND + PH.TAIL)


# ---------------------------------------------------------------------------------------------------- cutaways (2)
BLUEPRINT = r"""
S.background=new THREE.Color('BGCOL');
const grid=new THREE.GridHelper(80,80,'#4F7FD0','#2E62B8');grid.position.y=-4.01;S.add(grid);
const line='#DCEBFF';
const part=(g,glow,op)=>{const grp=new THREE.Group();const m=glow?new THREE.MeshBasicMaterial({color:new THREE.Color(glow).multiplyScalar(2.6)}):
  new THREE.MeshBasicMaterial({color:'#1E5BC0',transparent:true,opacity:op??.3,side:THREE.DoubleSide,depthWrite:false});
  grp.add(new THREE.Mesh(g,m));grp.add(new THREE.LineSegments(new THREE.EdgesGeometry(g,20),new THREE.LineBasicMaterial({color:glow?'#FFF0D0':line})));S.add(grp);return grp};
const prism=(pts,depth)=>{const sh=new THREE.Shape();sh.moveTo(...pts[0]);for(const p of pts.slice(1))sh.lineTo(...p);sh.closePath();
  const g=new THREE.ExtrudeGeometry(sh,{depth,bevelEnabled:false});g.translate(0,0,-depth/2);return g};
"""
DAM = r"""
// reservoir water (left), dam wall (trapezoid), penstock, turbine (glowing), generator, river outlet, power lines
const water=part(new THREE.BoxGeometry(9,5.2,6),null,.22);water.position.set(-6.2,-1.4,0);water.children[0].material.color=new THREE.Color('#2F8BFF');
const wall=part(prism([[-1.6,-4],[1.6,-4],[0.2,4.2],[-0.6,4.2]],6.4),null,.35);wall.position.set(-1.0,0,0);
const pen=part(new THREE.CylinderGeometry(.35,.35,6.4,20),null,.45);pen.position.set(.3,-1.6,0);pen.rotation.z=1.0;
const tur=part(new THREE.CylinderGeometry(.9,.9,.6,28),'#FF7A1A');tur.position.set(3.2,-3.3,0);
const gen=part(new THREE.CylinderGeometry(.75,.75,1.4,28),null,.5);gen.position.set(3.2,-1.9,0);
const shaft=part(new THREE.CylinderGeometry(.12,.12,1.0,12),null,.6);shaft.position.set(3.2,-2.75,0);
const house=part(new THREE.BoxGeometry(3.4,3.6,4.2),null,.10);house.position.set(3.2,-2.2,0);
const river=part(new THREE.BoxGeometry(6,.5,3.2),null,.25);river.position.set(7.4,-3.75,0);river.children[0].material.color=new THREE.Color('#2F8BFF');
for(const x of [6.4,9.4]){const p=part(new THREE.CylinderGeometry(.06,.1,5,8),null,.6);p.position.set(x,0,-2.6)}
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(4,4.5,24);cam.lookAt(.6,-.6,0);
const BLOOM=[.6,.3,.9];
const LABELS=()=>{const items=[["RESERVOIR",new THREE.Vector3(-7,1,1),[150,250]],["DAM WALL",new THREE.Vector3(-.6,3,1),[620,150]],["PENSTOCK",new THREE.Vector3(.6,-1.4,.4),[880,330]],
  ["TURBINE",new THREE.Vector3(3.2,-3.3,.9),[1300,880]],["GENERATOR",new THREE.Vector3(3.2,-1.5,.8),[1350,300]],["TAILRACE",new THREE.Vector3(7.4,-3.6,1.6),[1640,760]]];
 let svg='<svg width="1920" height="1080" style="left:0;top:0">';let html='';
 for(const [t,v,[lx,ly]] of items){const [x,y]=proj(v,cam);const hot=t==='TURBINE';svg+=`<line x1="${x}" y1="${y}" x2="${lx}" y2="${ly+18}" stroke="${hot?'#FFB46A':'#DCEBFF'}" stroke-width="2"/><circle cx="${x}" cy="${y}" r="6" fill="${hot?'#FFB46A':'#DCEBFF'}"/>`;
  html+=`<div style="left:${lx-8}px;top:${ly}px;font:700 30px Grotesk;letter-spacing:2px;color:${hot?'#FFB46A':'#F2F7FF'};border-bottom:2px solid ${hot?'#FFB46A':'#DCEBFF'};padding-bottom:4px">${t}</div>`}
 ov.innerHTML=svg+'</svg>'+html+`<div style="left:90px;bottom:80px"><div style="font:400 112px/0.9 Anton;color:#F2F7FF">HOW A DAM<br>MAKES POWER</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:#FFB46A;margin-top:14px">FALLING WATER SPINS THE TURBINE; THE TURBINE TURNS THE GENERATOR</div>
 <div style="display:inline-block;margin-top:14px;background:#FFDD33;padding:6px 12px;font:500 16px Plex;letter-spacing:3px;color:#141414">HEIGHT × FLOW = POWER</div></div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.55)">SIMPLIFIED CUTAWAY OF A GENERIC GRAVITY DAM AND POWERHOUSE · DRAWN IN THE STUDIO · NOT TO SCALE</div>
 <svg width="1920" height="1080" style="left:0;top:0;opacity:.16"><defs><pattern id="gr" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#9CC0FF" stroke-width="1"/></pattern></defs><rect width="1920" height="1080" fill="url(#gr)"/></svg>`};
"""
SOLAR = r"""
// a solar panel pulled apart into its layers; the cell layer glows
const layers=[["ALUMINIUM FRAME",0,null,.10],["TEMPERED GLASS",1.6,null,.22],["ENCAPSULANT (EVA)",3.0,null,.16],["SILICON CELLS",4.4,'#FF7A1A',0],["ENCAPSULANT (EVA)",5.8,null,.16],["BACKSHEET",7.2,null,.32],["JUNCTION BOX",8.4,null,.5]];
const rot=new THREE.Euler(-.95,0,.18);const pos=[];
layers.forEach(([t,y,glow,op],i)=>{let g;
  if(t==='SILICON CELLS'){const grp=new THREE.Group();for(let r=0;r<6;r++)for(let c=0;c<10;c++){const cell=part(new THREE.BoxGeometry(.9,.04,.9),'#FF7A1A');cell.position.set(-4.6+c*1.02,0,-2.6+r*1.02);S.remove(cell);grp.add(cell)}
    grp.position.set(0,y-4,0);grp.rotation.copy(rot);S.add(grp);pos.push([t,new THREE.Vector3(5.2,y-4,-2.6).applyEuler(rot),true]);return}
  if(t==='ALUMINIUM FRAME'){g=new THREE.BoxGeometry(10.8,.3,6.8);const f=part(g,null,.05);f.position.set(0,y-4,0);f.rotation.copy(rot)}
  else if(t==='JUNCTION BOX'){const f=part(new THREE.BoxGeometry(1.6,.5,1.0),null,op);f.position.set(0,y-4,0);f.rotation.copy(rot)}
  else{const f=part(new THREE.BoxGeometry(10.4,.08,6.4),null,op);f.position.set(0,y-4,0);f.rotation.copy(rot)}
  pos.push([t,new THREE.Vector3(5.2,y-4,-3.2).applyEuler(rot),false])});
const cam=new THREE.PerspectiveCamera(32,1920/1080,.1,200);cam.position.set(-2,4,24);cam.lookAt(-2.4,.2,0);
const BLOOM=[.5,.25,.92];
const LABELS=()=>{let svg='<svg width="1920" height="1080" style="left:0;top:0">';let html='';
 pos.forEach(([t,v,hot],i)=>{const [x,y]=proj(v,cam);const lx=1500,ly=y-16;svg+=`<line x1="${x}" y1="${y}" x2="${lx-14}" y2="${ly+18}" stroke="${hot?'#FFB46A':'#DCEBFF'}" stroke-width="2"/><circle cx="${x}" cy="${y}" r="5" fill="${hot?'#FFB46A':'#DCEBFF'}"/>`;
  html+=`<div style="left:${lx}px;top:${ly}px;font:700 26px Grotesk;letter-spacing:2px;color:${hot?'#FFB46A':'#F2F7FF'}">${t}</div>`});
 ov.innerHTML=svg+'</svg>'+html+`<div style="left:90px;top:70px"><div style="font:400 112px/0.9 Anton;color:#F2F7FF">INSIDE A<br>SOLAR PANEL</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:#FFB46A;margin-top:14px;width:900px">ONLY ONE LAYER MAKES ELECTRICITY. THE REST KEEP IT DRY, COOL AND IN ONE PIECE</div></div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.55)">SIMPLIFIED EXPLODED VIEW OF A TYPICAL CRYSTALLINE-SILICON MODULE · DRAWN IN THE STUDIO · NOT TO SCALE</div>
 <svg width="1920" height="1080" style="left:0;top:0;opacity:.16"><defs><pattern id="gr" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#9CC0FF" stroke-width="1"/></pattern></defs><rect width="1920" height="1080" fill="url(#gr)"/></svg>`};
"""


def cutaway_pages():
    put("cutaway_dam", S3.HEAD + BLUEPRINT.replace("BGCOL", "#0B3A86") + DAM + S3.TAIL)
    put("cutaway_solar", S3.HEAD + BLUEPRINT.replace("BGCOL", "#0A2A5C") + SOLAR + S3.TAIL)


# ---------------------------------------------------------------------------------------------------- glow bars (4)
BARS = r"""
S.background=new THREE.Color(CFG.bg);S.fog=new THREE.Fog(CFG.bg,30,70);
const data=CFG.data;const n=data.length;const k=CFG.k;
S.add(new THREE.AmbientLight('#ffffff',.35));const L=new THREE.DirectionalLight('#ffffff',1.6);L.position.set(-8,14,10);S.add(L);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,40),new THREE.MeshStandardMaterial({color:'#101218',roughness:.9}));floor.rotation.x=-Math.PI/2;S.add(floor);
const grid=new THREE.GridHelper(60,30,'#22252E','#1A1D24');grid.position.y=.01;S.add(grid);
const tops=[];
data.forEach(([yr,v],i)=>{const h=Math.max(.02,v*k),x=(i-(n-1)/2)*CFG.gap;const hot=CFG.hot.includes(i);
  const mat=hot?new THREE.MeshBasicMaterial({color:new THREE.Color(CFG.glow).multiplyScalar(2.4)}):new THREE.MeshStandardMaterial({color:'#3A3F4B',roughness:.5,metalness:.2});
  const m=new THREE.Mesh(new THREE.BoxGeometry(CFG.gap*.66,h,CFG.gap*.66),mat);m.position.set(x,h/2,0);S.add(m);
  const e=new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({color:hot?'#FFF0D8':'#6B7280'}));e.position.copy(m.position);S.add(e);
  tops.push([yr,v,new THREE.Vector3(x,h+.3,.7),new THREE.Vector3(x,-.1,.7),hot])});
const cam=new THREE.PerspectiveCamera(28,1920/1080,.1,200);cam.position.set(...CFG.cam);cam.lookAt(...CFG.look);
const BLOOM=[.45,.22,.95];
const LABELS=()=>{let h='';for(const [yr,v,t,b,hot] of tops){const [x,y]=proj(t,cam),[bx,by]=proj(b,cam);
  h+=`<div style="left:${x-70}px;top:${y-58}px;width:140px;text-align:center;font:${hot?'400 46px':'400 30px'} Anton;color:${hot?CFG.lab:'#C9CDD6'};${hot?'text-shadow:0 0 18px '+CFG.glow:''}">${v.toFixed(CFG.dp)}${CFG.unit}</div>
  <div style="left:${bx-70}px;top:${by+6}px;width:140px;text-align:center;font:500 20px Plex;color:#8B93A3">${yr}</div>`}
 ov.innerHTML=h+`<div style="left:90px;top:60px"><div style="font:400 60px ISerif;color:#E8E4DA">${CFG.kick}</div><div style="font:400 128px/0.9 Anton;color:#F3EFE6">${CFG.title}</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:${CFG.lab};margin-top:16px">${CFG.what}</div></div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.5)">${CFG.src}</div>`};
"""


def bars_pages():
    giss = []
    for line in (D / "data" / "giss_glb.csv").read_text().splitlines()[2:]:
        p = line.split(",")
        if p[13] != "***":
            giss.append((int(p[0]), float(p[13])))
    dec = []
    for d0 in range(1980, 2030, 10):
        v = [x for y, x in giss if d0 <= y < d0 + 10]
        dec.append([f"{d0}s" + ("*" if d0 == 2020 else ""), round(statistics.mean(v), 2)])
    last_full = max(y for y, _ in giss)
    fert = [[y, v] for y, v in wb("fertility_ind", "IND") if y in (1960, 1970, 1980, 1990, 2000, 2010, 2020) or y == max(yy for yy, _ in wb("fertility_ind", "IND"))]
    ren = [[y, v] for y, v in wb("renew_wld") if y in (2000, 2004, 2008, 2012, 2016, 2020)]
    lit = [[y, v] for y, v in wb("lit_ind", "IND") if y in (2001, 2011, 2018, 2023)]
    cfgs = {
        "glow_warming": dict(bg="#07080C", data=dec, k=4.2, gap=3.0, hot=[len(dec) - 1], glow="#FF5A1E", lab="#FF9A66", dp=2, unit="°", cam=[-6, 4.6, 26], look=[-1, 2.2, 0],
                             kick="Every decade warmer", title="THE HEAT ADDS UP", what="GLOBAL SURFACE TEMPERATURE, DECADE AVERAGE, °C ABOVE THE 1951–1980 MEAN",
                             src=f"SOURCE: NASA GISS SURFACE TEMPERATURE ANALYSIS (GISTEMP V4), GLB.TS+DSST.CSV, ANNUAL J-D · *2020s = 2020 TO {last_full} · BARS START AT ZERO (THE 1951–1980 AVERAGE)"),
        "glow_fertility": dict(bg="#0A0710", data=fert, k=1.25, gap=2.4, hot=[len(fert) - 1], glow="#C77DFF", lab="#D9A6FF", dp=2, unit="", cam=[-7, 5.2, 28], look=[-1.5, 3.2, 0],
                               kick="From six children to two", title="INDIA'S FAMILIES SHRANK", what="BIRTHS PER WOMAN (TOTAL FERTILITY RATE), INDIA",
                               src="SOURCE: WORLD BANK, SP.DYN.TFRT.IN (UN POPULATION DIVISION ESTIMATES), WORLD BANK API · BARS START AT ZERO"),
        "glow_renewables": dict(bg="#06100A", data=ren, k=.26, gap=2.6, hot=[len(ren) - 1], glow="#2FD47A", lab="#7CF0B0", dp=1, unit="%", cam=[-6, 4.6, 26], look=[-1.2, 2.2, 0],
                                kick="Two decades, one shrug", title="BARELY MOVED", what="RENEWABLES' SHARE OF ALL ENERGY THE WORLD USES (FINAL ENERGY CONSUMPTION)",
                                src="SOURCE: WORLD BANK, EG.FEC.RNEW.ZS (IEA, IRENA, UN STATISTICS DIVISION, WORLD BANK, WHO), WORLD BANK API · LATEST YEAR IN THE SERIES: 2020 · BARS START AT ZERO"),
        "glow_literacy": dict(bg="#0C0A06", data=lit, k=.075, gap=3.0, hot=[len(lit) - 1], glow="#FFC21A", lab="#FFDD33", dp=1, unit="%", cam=[-5, 4.8, 24], look=[-1, 2.6, 0],
                              kick="Reading, writing, counting", title="MORE INDIANS CAN READ", what="ADULT LITERACY RATE, INDIA, % OF PEOPLE AGED 15 AND ABOVE",
                              src="SOURCE: WORLD BANK, SE.ADT.LITR.ZS (UNESCO INSTITUTE FOR STATISTICS), WORLD BANK API · ONLY YEARS WITH A SURVEY ARE SHOWN, SO THE GAPS ARE UNEVEN · BARS START AT ZERO"),
    }
    for name, cfg in cfgs.items():
        cfg["k"] = 5.0 / max(v for _, v in cfg["data"])
        cfg["cam"] = [-6, 5.2, 30]
        cfg["look"] = [-1.0, 4.6, 0]
        put(name, S3.HEAD + f"const CFG={json.dumps(cfg, ensure_ascii=False)};\n" + BARS + S3.TAIL)
    return cfgs


# ---------------------------------------------------------------------------------------------------- drawings (4)
def wob(pts, amp=2.0, step=10, seed=1):
    import random
    r = random.Random(seed)
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t + r.uniform(-amp, amp), a[1] + (b[1] - a[1]) * t + r.uniform(-amp, amp)))
    out.append(pts[-1])
    return out


def circ(cx, cy, rx, ry=None, a0=0, a1=360, n=48):
    ry = ry or rx
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def stick(x, y, s=1.0, look=0):
    """A plain stick figure (no face details): head circle, body, arms, legs."""
    return [circ(x, y - 150 * s, 26 * s), [(x, y - 124 * s), (x, y - 40 * s)], [(x - 46 * s, y - 100 * s + look), (x, y - 96 * s), (x + 46 * s, y - 100 * s - look)],
            [(x - 34 * s, y + 30 * s), (x, y - 40 * s), (x + 34 * s, y + 30 * s)]]


INK, RED, BLUE = "#1C1C1C", "#C8312B", "#2457C5"


def drawing(title, sub, strokes, notes, page_no, src):
    svg = ""
    for i, (pts, col, w) in enumerate(strokes):
        pts = wob(pts, 1.6, 10, seed=i + page_no * 31)
        svg += f'<path d="M{" L".join(f"{x:.1f} {y:.1f}" for x, y in pts)}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    paper = ("background:#FBF8F0;background-image:linear-gradient(90deg,transparent 118px,#E7A9A3 118px,#E7A9A3 121px,transparent 121px),"
             "repeating-linear-gradient(0deg,transparent 0 47px,#D9E3F2 47px 48px)")
    nt = "".join(f'<div style="position:absolute;left:{x}px;top:{y}px;white-space:nowrap;font:700 {s}px Caveat;color:{c}">{t}</div>' for x, y, t, c, s in notes)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}}@font-face{{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}}
@font-face{{font-family:Marker;src:url(/fonts/permanent-marker-latin-400-normal.woff2)}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;{paper}}}</style></head><body>
<div style="position:absolute;left:160px;top:70px;font:500 18px Plex;letter-spacing:5px;color:#8A8A8A">DRAGON PSYCHOLOGY · SKETCHBOOK · PAGE {page_no:02d}</div>
<div style="position:absolute;left:160px;top:110px;font:400 92px Marker;color:#1C1C1C;white-space:nowrap"><span style="background:linear-gradient(transparent 60%,{SIG} 60%,{SIG} 92%,transparent 92%)">{title}</span></div>
<div style="position:absolute;left:166px;top:240px;font:700 44px Caveat;color:#555;white-space:nowrap">{sub}</div>
<svg width="1920" height="1080" style="position:absolute;left:0;top:0">{svg}</svg>{nt}
<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">{src} · DRAWN STROKE BY STROKE IN THE STUDIO</div>
<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>"""


def drawing_pages():
    # anchoring: a price tag with a big crossed-out number, an arrow pulling the guess toward it
    s = [(circ(560, 560, 210, 130), INK, 5), ([(350, 560), (300, 520)], INK, 4)]
    s += [([(440, 520), (690, 600)], RED, 7), ([(440, 600), (690, 520)], RED, 7)]
    s += [([(800, 560), (1080, 560)], INK, 4), ([(1050, 535), (1080, 560), (1050, 585)], INK, 4)]
    s += [(circ(1240, 560, 120, 90), BLUE, 4)]
    s += [([(1500, 380), (1500, 760)], INK, 3)] + [([(1490, y), (1510, y)], INK, 3) for y in range(400, 760, 60)]
    s += [([(1440, 470), (1480, 470)], RED, 6), ([(1440, 650), (1480, 650)], BLUE, 6)]
    notes = [(470, 520, "₹9,999", INK, 70), (1170, 520, "₹6,000?", BLUE, 56), (1380, 440, "first number", RED, 38), (1380, 660, "your guess", BLUE, 38),
             (300, 760, "the first number you see drags every guess after it", RED, 48), (300, 840, "even when it is random", INK, 42)]
    put("draw_anchoring", drawing("Anchoring", "why the first number wins", s, notes, 7,
                                  "IDEA: TVERSKY & KAHNEMAN, 'JUDGMENT UNDER UNCERTAINTY: HEURISTICS AND BIASES', SCIENCE 185, 1974 · PRICES ILLUSTRATIVE"))
    # confirmation bias: a figure with a magnifier, ticks on agreeing notes, crossed-out disagreeing notes ignored
    s = stick(420, 760, 1.2)
    s = [(p, INK, 5) for p in s] + [(circ(560, 560, 70), INK, 5), ([(510, 610), (470, 660)], INK, 7)]
    for i, (x, y) in enumerate(((800, 420), (1000, 470), (840, 640), (1060, 680))):
        s.append(([(x, y), (x + 150, y), (x + 150, y + 100), (x, y + 100), (x, y)], INK, 3))
        s.append(([(x + 40, y + 50), (x + 65, y + 75), (x + 110, y + 25)], BLUE, 5))
    for i, (x, y) in enumerate(((1350, 380), (1480, 560), (1340, 740))):
        s.append(([(x, y), (x + 150, y), (x + 150, y + 100), (x, y + 100), (x, y)], "#9A9A9A", 3))
        s.append(([(x + 45, y + 25), (x + 105, y + 75)], "#9A9A9A", 4)); s.append(([(x + 105, y + 25), (x + 45, y + 75)], "#9A9A9A", 4))
    notes = [(820, 330, "what we look for", BLUE, 44), (1330, 300, "what we skip", "#7A7A7A", 44),
             (300, 880, "we test ideas by hunting for proof they are right, not for proof they are wrong", RED, 44)]
    put("draw_confirmation", drawing("Confirmation Bias", "we see what we came to see", s, notes, 8,
                                     "IDEA: P. C. WASON, 'ON THE FAILURE TO ELIMINATE HYPOTHESES IN A CONCEPTUAL TASK', Q. J. EXP. PSYCHOLOGY 12, 1960"))
    # spotlight effect: one figure under a big cone of light, the crowd looking elsewhere
    s = [([(960, 300), (760, 820)], "#E0B000", 4), ([(960, 300), (1160, 820)], "#E0B000", 4), (circ(960, 820, 200, 40), "#E0B000", 4)]
    s += [(p, INK, 5) for p in stick(960, 800, 1.1)]
    for k, x in enumerate((360, 500, 1420, 1560, 1700)):
        s += [(p, "#8A8A8A", 4) for p in stick(x, 830, .8, look=(-14 if x < 960 else 14))]
    notes = [(1040, 360, "everyone is looking at me", INK, 46), (1300, 600, "...they are not", RED, 52),
             (300, 920, "we think others notice us far more than they do", RED, 46)]
    put("draw_spotlight", drawing("The Spotlight Effect", "the audience is smaller than it feels", s, notes, 9,
                                  "IDEA: GILOVICH, MEDVEC & SAVITSKY, 'THE SPOTLIGHT EFFECT IN SOCIAL JUDGMENT', J. PERSONALITY AND SOCIAL PSYCHOLOGY 78, 2000"))
    # planning fallacy: a calendar with a planned span and a much longer real span
    s = []
    for r in range(4):
        for c in range(7):
            x, y = 340 + c * 150, 400 + r * 110
            s.append(([(x, y), (x + 140, y), (x + 140, y + 100), (x, y + 100), (x, y)], "#9AA6B8", 2))
    s += [([(350, 450), (920, 450)], BLUE, 9), ([(350, 670), (1370, 670), (1370, 780), (500, 780)], RED, 9)]
    s += [(circ(1470, 560, 110), INK, 5), ([(1470, 560), (1470, 480)], INK, 5), ([(1470, 560), (1530, 590)], INK, 5)]
    notes = [(350, 350, "the plan", BLUE, 48), (940, 420, "← what we expected", BLUE, 40), (520, 800, "what it took", RED, 48),
             (300, 900, "we plan for the best case and forget how long things took last time", RED, 46)]
    put("draw_planning", drawing("The Planning Fallacy", "why everything takes longer", s, notes, 10,
                                 "IDEA: KAHNEMAN & TVERSKY 1979; BUEHLER, GRIFFIN & ROSS, J. PERSONALITY AND SOCIAL PSYCHOLOGY 67, 1994 · CALENDAR ILLUSTRATIVE"))


# ---------------------------------------------------------------------------------------------------- box plots, unit grids, nodes, globes
def taxonomy_pages():
    giss = {}
    for line in (D / "data" / "giss_glb.csv").read_text().splitlines()[2:]:
        p = line.split(",")
        giss[int(p[0])] = [float(x) for x in p[1:13] if x != "***"]
    groups = []
    for d0 in range(1880, 2030, 20):
        v = [x for y, xs in giss.items() if d0 <= y < d0 + 20 for x in xs]
        groups.append((f"{d0}–{str(min(d0 + 19, max(giss)))[2:]}", [x * 100 for x in v]))
    last_m = max(giss)
    put("box_giss", box_plot(groups, "THE WHOLE CURVE MOVED", "Every month since 1880, in twenty-year groups", "HUNDREDTHS OF °C VS 1951–1980",
                             f"SOURCE: NASA GISS SURFACE TEMPERATURE ANALYSIS (GISTEMP V4), GLB.TS+DSST.CSV, MONTHLY GLOBAL MEANS, JAN 1880 TO {len(giss[last_m])}/{last_m} · VALUES ×100 FOR READABILITY",
                             t=1.0, lo=-80, hi=160))
    cs = json.loads((D / "data" / "wb" / "countries.json").read_text())[1]
    reg = {c["id"]: c["region"]["value"].strip() for c in cs if c["region"]["value"].strip() and c["region"]["value"].strip() != "Aggregates"}
    life = json.loads((D / "data" / "wb" / "life_all.json").read_text())[1]
    by = {}
    for r in life:
        if r["value"] is not None and r["countryiso3code"] in reg:
            by.setdefault(reg[r["countryiso3code"]], []).append(r["value"])
    short = {"Sub-Saharan Africa": "SUB-SAHARAN AFRICA", "South Asia": "SOUTH ASIA", "Middle East, North Africa, Afghanistan & Pakistan": "MIDDLE EAST & N. AFRICA",
             "Middle East & North Africa": "MIDDLE EAST & N. AFRICA", "Latin America & Caribbean": "LATIN AMERICA", "East Asia & Pacific": "EAST ASIA & PACIFIC",
             "Europe & Central Asia": "EUROPE & C. ASIA", "North America": "NORTH AMERICA"}
    groups = sorted(((short.get(k, k.upper()), v) for k, v in by.items() if len(v) >= 2), key=lambda g: statistics.median(g[1]))
    put("box_life", box_plot(groups, "WHERE YOU ARE BORN", "Life expectancy at birth, every country, by region", "YEARS",
                             "SOURCE: WORLD BANK, SP.DYN.LE00.IN, 2022, ALL COUNTRIES WITH DATA, GROUPED BY WORLD BANK REGION · WORLD BANK API", accent_last=False, t=1.0, lo=50, hi=90))
    pick = lambda *names: next(n for n in names if n in ICONS)
    inet = [v for y, v in wb("internet_wld")][-1]
    forest = [v for y, v in wb("forest_wld")][-1]
    urb = [v for y, v in wb("urban_ind", "IND")][-1]
    lit = [v for y, v in wb("lit_ind", "IND")][-1]
    put("unit_internet", unit_grid(100, round(inet), "SEVEN IN TEN", "People in the world who use the internet", pick("world-www", "world", "wifi"),
                                   f"SOURCE: WORLD BANK, IT.NET.USER.ZS (ITU), WORLD, {wb('internet_wld')[-1][0]}: {inet:.1f}% · ONE ICON = 1% OF THE WORLD'S PEOPLE", cols=10, t=1.0, lit_label="ARE ONLINE"))
    put("unit_forest", unit_grid(100, round(forest), "ALMOST A THIRD", "Squares of the world's land that are forest", pick("tree", "trees", "plant"),
                                 f"SOURCE: WORLD BANK, AG.LND.FRST.ZS (FAO), WORLD, {wb('forest_wld')[-1][0]}: {forest:.2f}% · ONE ICON = 1% OF LAND AREA", cols=10, t=1.0, lit_label="ARE FOREST"))
    put("unit_urban", unit_grid(100, round(urb), "ABOUT ONE IN THREE", "Indians who live in a town or city", pick("building-skyscraper", "building"),
                                f"SOURCE: WORLD BANK, SP.URB.TOTL.IN.ZS (UN WORLD URBANIZATION PROSPECTS), INDIA, {wb('urban_ind', 'IND')[-1][0]}: {urb:.1f}% · NATIONAL DEFINITIONS OF 'URBAN' DIFFER · ONE ICON = 1%",
                                cols=10, t=1.0, lit_label="LIVE IN CITIES"))
    # nodes: how a UPI payment travels; why vegetable prices jump after a bad monsoon (simplified chain)
    nodes = {"you": (500, 640, pick("user", "user-circle"), "YOU", "tap pay in any UPI app"),
             "app": (1200, 380, pick("device-mobile", "phone"), "PAYMENT APP", "sends the request"),
             "npci": (1950, 640, pick("building-bank", "building"), "NPCI", "runs the UPI switch"),
             "bank1": (2700, 380, pick("building-bank", "building"), "YOUR BANK", "debits your account"),
             "bank2": (2700, 900, pick("building-bank", "building"), "THEIR BANK", "credits the shop"),
             "shop": (3400, 640, pick("building-store", "shopping-cart"), "THE SHOP", "sees the money arrive")}
    edges = [("you", "app"), ("app", "npci"), ("npci", "bank1"), ("bank1", "npci"), ("npci", "bank2"), ("bank2", "shop")]
    squeeze = lambda N: {k: (round(420 + (v[0] - 500) * .72), round(700 + (v[1] - 640) * .85)) + tuple(v[2:]) for k, v in N.items()}
    nodes = squeeze(nodes)
    put("node_upi", node_canvas(nodes, edges, (1480, 700, .74), "WHERE A UPI TAP GOES",
                                "SOURCE: NATIONAL PAYMENTS CORPORATION OF INDIA (NPCI), 'UNIFIED PAYMENTS INTERFACE' PRODUCT OVERVIEW · SIMPLIFIED; REAL FLOWS ADD CHECKS AND MESSAGES · DIAGRAM DRAWN IN THE STUDIO", t=1.0, focus="npci"))
    nodes = {"rain": (500, 500, pick("cloud-rain", "cloud"), "MONSOON", "too little, too late, or too much"),
             "crop": (1250, 380, pick("plant", "leaf"), "CROPS", "sown late or damaged"),
             "store": (1250, 900, pick("building-warehouse", "building"), "STORAGE", "little of it is cold storage"),
             "supply": (2000, 640, pick("truck", "truck-delivery"), "LESS REACHES MANDIS", "arrivals fall"),
             "price": (2750, 640, pick("currency-rupee", "coin"), "PRICES JUMP", "same demand, less supply"),
             "plate": (3450, 640, pick("bowl", "tools-kitchen-2", "chef-hat"), "YOUR PLATE", "onions, tomatoes, pulses")}
    edges = [("rain", "crop"), ("crop", "supply"), ("store", "supply"), ("supply", "price"), ("price", "plate")]
    nodes = squeeze(nodes)
    put("node_monsoon", node_canvas(nodes, edges, (1480, 700, .74), "WHY PRICES FOLLOW THE RAIN",
                                    "CHAIN: RESERVE BANK OF INDIA MONETARY POLICY REPORTS ON FOOD INFLATION AND WEATHER SHOCKS · SIMPLIFIED, ONE OF SEVERAL CAUSES · DIAGRAM DRAWN IN THE STUDIO", t=1.0, focus="price"))
    from creatorforge_worker.media import maps
    india = [[(lo, la) for lo, la in r] for r in maps._find("India")["rings"] if len(r) > 3]
    srcg = "IMAGERY: NASA BLUE MARBLE NEXT GENERATION VIA GIBS (PUBLIC DOMAIN) · ROUTE: SHORTEST PATH ON THE SPHERE, NOT THE ROUTE SHIPS OR PLANES TAKE"
    put("globe_shanghai", globe(0.0, 70, [(121.47, 31.23), (4.48, 51.92)], [], "THE SHORT WAY ROUND", "Shanghai to Rotterdam, as the crow flies", srcg,
                                labels=[(121.47, 31.23, "SHANGHAI"), (4.48, 51.92, "ROTTERDAM")]))
    put("globe_mumbai", globe(0.5, 10, [(72.88, 19.08), (-74.01, 40.71)], india, "OVER THE TOP", "Mumbai to New York on a sphere, then flattened",
                              srcg + " · INDIA: OFFICIAL BOUNDARY", labels=[(72.88, 19.08, "MUMBAI"), (-74.01, 40.71, "NEW YORK")]))
    put("globe_sydney", globe(1.0, 110, [(77.21, 28.61), (151.21, -33.87)], india, "THE FLAT MAP LIES", "Delhi to Sydney: the curve is the shortest line",
                              srcg + " · INDIA: OFFICIAL BOUNDARY", labels=[(77.21, 28.61, "DELHI"), (151.21, -33.87, "SYDNEY")]))


if __name__ == "__main__":
    which = set(sys.argv[1:])
    for nm, f in (("relief", relief_pages), ("physics", physics_pages), ("cutaway", cutaway_pages), ("bars", bars_pages), ("draw", drawing_pages), ("tax", taxonomy_pages)):
        if not which or nm in which:
            f()
    print(len(OUT), sorted(OUT))
