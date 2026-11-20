"""Real rigid-body physics (Rapier, Apache-2.0) rendered with three.js: a Galton board, a domino chain and a block
tower collapse. The browser steps the simulation to a chosen moment, then renders one frame."""
from pathlib import Path
D = Path(__file__).resolve().parent
V = "/vendor/three160"

HEAD = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}}@font-face{{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}}
@font-face{{font-family:ISerif;src:url(/fonts/instrument-serif-latin-400-italic.woff2)}}@font-face{{font-family:Caveat;src:url(/fonts/caveat-latin-700-normal.woff2)}}
@font-face{{font-family:Playfair;src:url(/fonts/playfair-display-latin-900-normal.woff2)}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#EDE7DA}} canvas{{position:absolute;left:0;top:0}} #ov>div{{position:absolute}}
.grain{{position:absolute;inset:0;pointer-events:none;opacity:.28;mix-blend-mode:multiply}}
</style><script type="importmap">{{"imports":{{"three":"{V}/three.module.js","three/addons/":"{V}/addons/"}}}}</script></head><body><div id="ov"></div>
<svg class="grain" width="1920" height="1080"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3"/><feColorMatrix values="0 0 0 0 .4 0 0 0 0 .35 0 0 0 0 .3 0 0 0 .5 0"/></filter><rect width="1920" height="1080" filter="url(#g)"/></svg>
<script type="module">
import * as THREE from 'three';
import RAPIER from '/vendor/rapier3d-compat.mjs';
await RAPIER.init();
const R=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});R.setSize(1920,1080);R.setPixelRatio(1);R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;
R.toneMapping=THREE.ACESFilmicToneMapping;R.toneMappingExposure=1.05;document.body.prepend(R.domElement);
const S=new THREE.Scene();S.background=new THREE.Color('#EDE7DA');
S.add(new THREE.HemisphereLight('#fffaf0','#b8a990',1.1));const L=new THREE.DirectionalLight('#ffffff',2.2);L.position.set(-6,14,10);L.castShadow=true;L.shadow.mapSize.set(2048,2048);
Object.assign(L.shadow.camera,{{left:-20,right:20,top:20,bottom:-20,near:.5,far:60}});L.shadow.bias=-.0004;S.add(L);
const W=new RAPIER.World({{x:0,y:-9.81,z:0}});
const mesh=(g,c,o={{}})=>{{const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial(Object.assign({{color:c,roughness:.7}},o)));m.castShadow=true;m.receiveShadow=true;S.add(m);return m}};
const pairs=[];const sync=()=>{{for(const [b,m] of pairs){{const t=b.translation(),q=b.rotation();m.position.set(t.x,t.y,t.z);m.quaternion.set(q.x,q.y,q.z,q.w)}}}};
const fixedBox=(x,y,z,hx,hy,hz,c,show=true)=>{{W.createCollider(RAPIER.ColliderDesc.cuboid(hx,hy,hz).setTranslation(x,y,z).setFriction(.6));if(show){{const m=mesh(new THREE.BoxGeometry(hx*2,hy*2,hz*2),c);m.position.set(x,y,z);return m}}}};
"""
TAIL = """
sync();R.render(S,cam);
document.getElementById('ov').insertAdjacentHTML('beforeend',OVER);
await document.fonts.ready;window.READY=true;
</script></body></html>"""

GALTON = r"""
// Galton board: pegs in a triangle, balls fall and pile into bins; the heap draws a bell curve.
const rows=15,sp=.46,top=10.5;
fixedBox(0,-.05,0,12,.05,3,'#D9D0BE');
fixedBox(0,6,-.42,30,14,.1,'#ECE5D6');                        // back plate
W.createCollider(RAPIER.ColliderDesc.cuboid(9,9,.1).setTranslation(0,6,.42));  // invisible front glass
for(let r=0;r<rows;r++)for(let i=0;i<=r;i++){const x=(i-r/2)*sp,y=top-r*sp*.86;if(r<1)continue;
  W.createCollider(RAPIER.ColliderDesc.cylinder(.3,.07).setTranslation(x,y,0).setRotation({x:.7071,y:0,z:0,w:.7071}).setRestitution(.3));
  const m=mesh(new THREE.CylinderGeometry(.07,.07,.6,12),'#2A2A2A',{metalness:.6,roughness:.3});m.rotation.x=Math.PI/2;m.position.set(x,y,0)}
const binY=top-rows*sp*.86-.3, nb=rows+1;
// side rails along the triangle so no ball escapes the pegs
for(const sgn of [-1,1]){const k=(sp/2)/(sp*.86),x0=sgn*.27,y0=top+.3,y1=binY+.1,x1=sgn*(.27+(top-y1)*k);const cx=(x0+x1)/2,cy=(y0+y1)/2,len=Math.hypot(x1-x0,y1-y0),ang=Math.atan2(y1-y0,x1-x0);
  const q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),ang);
  W.createCollider(RAPIER.ColliderDesc.cuboid(len/2,.04,.4).setTranslation(cx,cy,0).setRotation({x:q.x,y:q.y,z:q.z,w:q.w}));
  const m=mesh(new THREE.BoxGeometry(len,.08,.7),'#2A2A2A');m.position.set(cx,cy,0);m.quaternion.copy(q)}
for(let i=0;i<=nb;i++){const x=(i-nb/2)*sp;fixedBox(x,binY/2,0,.03,binY/2,.35,'#2A2A2A')}

const balls=[];const g=new THREE.SphereGeometry(.1,16,12);
for(let k=0;k<NBALLS;k++){balls.push(null)}
let made=0;
for(let step=0;step<STEPS;step++){
  if(made<NBALLS && step%4===0){const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation((Math.random()-.5)*.04,top+.9,0).setCcdEnabled(true));
    W.createCollider(RAPIER.ColliderDesc.ball(.1).setRestitution(.15).setFriction(.1).setDensity(2),b);
    const m=mesh(g,made%9===0?'#E63946':'#E07A1F',{roughness:.35});pairs.push([b,m]);made++}
  W.step()}
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(6.4,5.6,24.5);cam.lookAt(3.4,5.4,0);
const OVER=`<div style="left:1180px;top:170px;width:640px"><div style="font:400 64px ISerif;color:#141414">Chance has a</div><div style="font:400 170px/0.9 Anton;color:#141414">SHAPE</div>
<div style="font:500 22px/1.5 Plex;color:#4a4a4a;letter-spacing:2px;margin-top:20px;width:560px">EVERY BALL GOES LEFT OR RIGHT AT RANDOM, PEG AFTER PEG. TOGETHER THEY PILE INTO A BELL CURVE.</div>
<div style="font:700 44px Caveat;color:#C0262D;margin-top:30px">no ball is aimed</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">REAL PHYSICS SIMULATION (RAPIER) · ${NBALLS} BALLS</div>`;
"""

DOMINO = r"""
// A domino chain on a curve: one push, every tile falls in turn. Captured mid-wave.
fixedBox(0,-.1,0,40,.1,40,'#E3DACA');
const n=46,pts=[];for(let i=0;i<n;i++){const t=i/(n-1);const x=-11+t*22,z=3.2*Math.sin(t*Math.PI*1.4);pts.push([x,z])}
const dg=new THREE.BoxGeometry(.18,1.2,.6);
pts.forEach(([x,z],i)=>{const nx=pts[Math.min(i+1,n-1)],pv=pts[Math.max(i-1,0)];const ang=Math.atan2(-(nx[1]-pv[1]),nx[0]-pv[0]);
  const q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,1,0),ang);
  const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(x,.6,z).setRotation({x:q.x,y:q.y,z:q.z,w:q.w}));
  W.createCollider(RAPIER.ColliderDesc.cuboid(.09,.6,.3).setFriction(.5).setDensity(1),b);
  const c=i===0?'#E63946':(i===n-1?'#FFDD33':'#1F1F1F');const m=mesh(dg,c,{roughness:.4});
  if(i>0&&i<n-1){const f=mesh(new THREE.PlaneGeometry(.12,.12),'#F4EFE6');}
  pairs.push([b,m]);if(i===0)b.applyImpulseAtPoint({x:.5*Math.cos(ang),y:0,z:-.5*Math.sin(ang)},{x,y:1.1,z},true)});
for(let s=0;s<STEPS;s++)W.step();
const cam=new THREE.PerspectiveCamera(28,1920/1080,.1,200);cam.position.set(-2,10,21);cam.lookAt(1,-.5,0);
const OVER=`<div style="left:100px;top:80px"><div style="font:400 150px/0.9 Anton;color:#141414">ONE PUSH</div>
<div style="font:400 56px ISerif;color:#141414;margin-top:8px">and everything after it moves</div>
<div style="font:500 20px Plex;letter-spacing:4px;color:#7A2A20;margin-top:18px">THE CHAIN REACTION</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">REAL PHYSICS SIMULATION (RAPIER) · ${46} TILES</div>`;
"""

JENGA = r"""
// A block tower: one block near the bottom is pulled out, the rest comes down. Captured mid-collapse.
fixedBox(0,-.1,0,40,.1,40,'#E3DACA');
const L_=3,Hh=.3,Wd=1,levels=17;const bg=new THREE.BoxGeometry(L_,Hh*2*.98,Wd*.98);let pulled=[];
for(let lv=0;lv<levels;lv++)for(let k=0;k<3;k++){const y=Hh+lv*Hh*2,off=(k-1)*Wd;const rot=lv%2===1;
  const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(rot?off:0,y,rot?0:off).setRotation(rot?{x:0,y:.7071,z:0,w:.7071}:{x:0,y:0,z:0,w:1}));
  W.createCollider(RAPIER.ColliderDesc.cuboid(L_/2,Hh*.98,Wd/2*.98).setFriction(.55).setDensity(.6),b);
  const hot=(lv===2&&k!==2);const m=mesh(bg,hot?'#E63946':(lv%3===0?'#D8B07A':'#E8C99A'),{roughness:.8});pairs.push([b,m]);if(hot)pulled.push(b)}
for(let s=0;s<60;s++)W.step();
pulled.forEach((b,i)=>{const c=b.collider(0);W.removeCollider(c,true);b.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased,true);
  const t=b.translation();b.setNextKinematicTranslation({x:t.x+(i?-3.4:3.2),y:t.y+.2,z:t.z},true)});
for(let s=0;s<STEPS;s++)W.step();
const cam=new THREE.PerspectiveCamera(30,1920/1080,.1,200);cam.position.set(12,9,22);cam.lookAt(2.4,4.6,0);
const OVER=`<div style="left:1140px;top:120px;width:700px"><div style="font:900 120px/0.95 Playfair;color:#141414">Too Big<br>to Fail</div>
<div style="font:500 22px/1.5 Plex;letter-spacing:3px;color:#4a4a4a;margin-top:24px;width:600px">WHEN ONE PIECE HOLDS UP EVERYTHING ABOVE IT</div>
<div style="display:inline-block;margin-top:26px;background:#FFDD33;padding:8px 14px;font:500 20px Plex;letter-spacing:3px">SYSTEMIC RISK</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">REAL PHYSICS SIMULATION (RAPIER)</div>`;
"""

if __name__ == "__main__":
    for name, body, steps, extra in (("physics_galton", GALTON, 7200, "const NBALLS=900;"), ("physics_dominoes", DOMINO, 210, ""), ("physics_jenga", JENGA, 95, "")):
        (D / "html" / f"{name}.html").write_text(HEAD + f"const STEPS={steps};{extra}\n" + body + TAIL)
