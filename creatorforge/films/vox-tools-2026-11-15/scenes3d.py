"""Blueprint cutaway (wind turbine nacelle, simplified, labelled) and glowing 3D bars (NOAA Mauna Loa CO2) — three.js
with UnrealBloomPass so the one thing being explained glows."""
import json
from pathlib import Path
D = Path(__file__).resolve().parent
V = "/vendor/three160"
HEAD = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}}@font-face{{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}}
@font-face{{font-family:Grotesk;src:url(/fonts/space-grotesk-latin-700-normal.woff2)}}@font-face{{font-family:ISerif;src:url(/fonts/instrument-serif-latin-400-italic.woff2)}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#000}} canvas{{position:absolute;left:0;top:0}} #ov{{position:absolute;inset:0}} #ov>div,#ov>svg{{position:absolute}}
</style><script type="importmap">{{"imports":{{"three":"{V}/three.module.js","three/addons/":"{V}/addons/"}}}}</script></head><body><div id="ov"></div>
<script type="module">
import * as THREE from 'three';
import {{EffectComposer}} from 'three/addons/postprocessing/EffectComposer.js';
import {{RenderPass}} from 'three/addons/postprocessing/RenderPass.js';
import {{UnrealBloomPass}} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {{OutputPass}} from 'three/addons/postprocessing/OutputPass.js';
const R=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});R.setSize(1920,1080);R.setPixelRatio(1);R.toneMapping=THREE.ACESFilmicToneMapping;document.body.prepend(R.domElement);
const S=new THREE.Scene();
const ov=document.getElementById('ov');
const proj=(v,cam)=>{{const p=v.clone().project(cam);return [(p.x+1)/2*1920,(1-p.y)/2*1080]}};
"""
TAIL = """
const comp=new EffectComposer(R);comp.addPass(new RenderPass(S,cam));comp.addPass(new UnrealBloomPass(new THREE.Vector2(1920,1080),BLOOM[0],BLOOM[1],BLOOM[2]));comp.addPass(new OutputPass());comp.render();
LABELS();await document.fonts.ready;window.READY=true;
</script></body></html>"""

CUTAWAY = r"""
S.background=new THREE.Color('#0B3A86');
const grid=new THREE.GridHelper(80,80,'#4F7FD0','#2E62B8');grid.position.y=-6;S.add(grid);
const line='#DCEBFF', fill=new THREE.MeshBasicMaterial({color:'#1E5BC0',transparent:true,opacity:.35,side:THREE.DoubleSide,depthWrite:false});
const part=(g,glow)=>{const grp=new THREE.Group();const m=glow?new THREE.MeshBasicMaterial({color:new THREE.Color('#FF7A1A').multiplyScalar(2.6)}):fill;
  grp.add(new THREE.Mesh(g,m));grp.add(new THREE.LineSegments(new THREE.EdgesGeometry(g,20),new THREE.LineBasicMaterial({color:glow?'#FFE0B0':line})));S.add(grp);return grp};
// tower
const tw=part(new THREE.CylinderGeometry(.55,.9,6,24,1,true));tw.children[0].material=new THREE.MeshBasicMaterial({color:'#1E5BC0',transparent:true,opacity:.18,side:THREE.DoubleSide,depthWrite:false});tw.position.set(0,-3,0);
// nacelle shell: half box (cut away on the near side)
const shell=new THREE.BoxGeometry(7,2.4,2.6);const sh=part(shell);sh.position.set(.6,1.2,0);
sh.children[0].material=new THREE.MeshBasicMaterial({color:'#1E5BC0',transparent:true,opacity:.12,side:THREE.DoubleSide,depthWrite:false});
// hub + blades
const hub=part(new THREE.SphereGeometry(1.0,24,16,0,Math.PI*2,0,Math.PI));hub.rotation.z=Math.PI/2;hub.position.set(-3.6,1.2,0);
for(let k=0;k<3;k++){const b=part(new THREE.BoxGeometry(.12,3.6,.45));const a=k*2*Math.PI/3+.5;b.position.set(-4.0,1.2+2.6*Math.cos(a),2.6*Math.sin(a));b.rotation.x=a}
// main shaft, gearbox, generator, yaw ring
const shaft=part(new THREE.CylinderGeometry(.22,.22,2.6,20));shaft.rotation.z=Math.PI/2;shaft.position.set(-1.9,1.2,0);
const gb=part(new THREE.CylinderGeometry(.75,.75,1.4,28));gb.rotation.z=Math.PI/2;gb.position.set(.1,1.2,0);
const shaft2=part(new THREE.CylinderGeometry(.14,.14,1.1,16));shaft2.rotation.z=Math.PI/2;shaft2.position.set(1.3,1.2,0);
const gen=part(new THREE.CylinderGeometry(.62,.62,1.5,28),true);gen.rotation.z=Math.PI/2;gen.position.set(2.5,1.2,0);
const yaw=part(new THREE.TorusGeometry(.75,.08,10,40));yaw.rotation.x=Math.PI/2;yaw.position.set(0,0,0);
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(10,5.5,19);cam.lookAt(-.8,-.6,0);
const BLOOM=[.55,.25,.92];
const LABELS=()=>{const items=[["ROTOR HUB",new THREE.Vector3(-3.6,1.6,.6),[210,250]],["MAIN SHAFT",new THREE.Vector3(-1.9,1.2,.2),[700,170]],["GEARBOX",new THREE.Vector3(.1,1.95,0),[1080,150]],
  ["GENERATOR",new THREE.Vector3(2.5,1.8,0),[1500,260]],["YAW DRIVE",new THREE.Vector3(0,0,.75),[1380,720]],["TOWER",new THREE.Vector3(0,-3,.8),[1180,880]]];
 let svg='<svg width="1920" height="1080" style="left:0;top:0">';let html='';
 for(const [t,v,[lx,ly]] of items){const [x,y]=proj(v,cam);const hot=t==='GENERATOR';svg+=`<line x1="${x}" y1="${y}" x2="${lx}" y2="${ly+18}" stroke="${hot?'#FFB46A':'#DCEBFF'}" stroke-width="2"/><circle cx="${x}" cy="${y}" r="6" fill="${hot?'#FFB46A':'#DCEBFF'}"/>`;
  html+=`<div style="left:${lx-8}px;top:${ly}px;font:700 30px Grotesk;letter-spacing:2px;color:${hot?'#FFB46A':'#F2F7FF'};border-bottom:2px solid ${hot?'#FFB46A':'#DCEBFF'};padding-bottom:4px">${t}</div>`}
 ov.innerHTML=svg+'</svg>'+html+`<div style="left:90px;bottom:80px"><div style="font:400 120px/0.9 Anton;color:#F2F7FF">INSIDE A<br>WIND TURBINE</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:#FFB46A;margin-top:14px">THE GENERATOR IS WHERE SPIN BECOMES ELECTRICITY</div></div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.55)">SIMPLIFIED CUTAWAY OF A GEARED DESIGN · DRAWN IN THE STUDIO · NOT TO SCALE</div>
 <svg width="1920" height="1080" style="left:0;top:0;opacity:.18"><defs><pattern id="gr" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#9CC0FF" stroke-width="1"/></pattern></defs><rect width="1920" height="1080" fill="url(#gr)"/></svg>`};
"""

BARS = r"""
S.background=new THREE.Color('#07080C');S.fog=new THREE.Fog('#07080C',30,70);
const data=DATA;const n=data.length;const k=.016;
S.add(new THREE.AmbientLight('#ffffff',.35));const L=new THREE.DirectionalLight('#ffffff',1.6);L.position.set(-8,14,10);S.add(L);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(80,40),new THREE.MeshStandardMaterial({color:'#101218',roughness:.9}));floor.rotation.x=-Math.PI/2;S.add(floor);
const grid=new THREE.GridHelper(60,30,'#22252E','#1A1D24');grid.position.y=.01;S.add(grid);
const tops=[];
data.forEach(([yr,v],i)=>{const h=v*k,x=(i-(n-1)/2)*2.1;const last=i===n-1;
  const mat=last?new THREE.MeshBasicMaterial({color:new THREE.Color('#FF8A1E').multiplyScalar(2.4)}):new THREE.MeshStandardMaterial({color:'#3A3F4B',roughness:.5,metalness:.2});
  const m=new THREE.Mesh(new THREE.BoxGeometry(1.4,h,1.4),mat);m.position.set(x,h/2,0);S.add(m);
  const e=new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry),new THREE.LineBasicMaterial({color:last?'#FFE2BF':'#6B7280'}));e.position.copy(m.position);S.add(e);
  tops.push([yr,v,new THREE.Vector3(x,h+.3,.7),new THREE.Vector3(x,-.1,.7),last])});
const cam=new THREE.PerspectiveCamera(28,1920/1080,.1,200);cam.position.set(-9,6,30);cam.lookAt(-2.2,4.4,0);
const BLOOM=[.45,.22,.95];
const LABELS=()=>{let h='';for(const [yr,v,t,b,last] of tops){const [x,y]=proj(t,cam),[bx,by]=proj(b,cam);
  h+=`<div style="left:${x-60}px;top:${y-58}px;width:120px;text-align:center;font:${last?'400 46px':'400 30px'} Anton;color:${last?'#FFB15A':'#C9CDD6'};${last?'text-shadow:0 0 18px rgba(255,140,30,.8)':''}">${v.toFixed(0)}</div>
  <div style="left:${bx-60}px;top:${by+6}px;width:120px;text-align:center;font:500 20px Plex;color:#8B93A3">${yr}</div>`}
 ov.innerHTML=h+`<div style="left:90px;top:60px"><div style="font:400 64px ISerif;color:#E8E4DA">The air keeps</div><div style="font:400 140px/0.9 Anton;color:#F3EFE6">FILLING UP</div>
 <div style="font:500 22px Plex;letter-spacing:4px;color:#FFB15A;margin-top:16px">CO₂ AT MAUNA LOA, PARTS PER MILLION, ANNUAL MEAN</div></div>
 <div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.5)">SOURCE: NOAA GLOBAL MONITORING LABORATORY, CO2_ANNMEAN_MLO.TXT · BARS START AT ZERO</div>`};
"""

if __name__ == "__main__":
    yrs = {1960, 1970, 1980, 1990, 2000, 2010, 2020, 2025}
    rows = [l.split() for l in (D / "data" / "co2_annmean_mlo.txt").read_text().splitlines() if l and not l.startswith("#")]
    data = [[int(r[0]), float(r[1])] for r in rows if int(r[0]) in yrs]
    (D / "html" / "cutaway_turbine.html").write_text(HEAD + CUTAWAY + TAIL)
    (D / "html" / "glow_co2bars.html").write_text(HEAD + BARS.replace("DATA", json.dumps(data)) + TAIL)
