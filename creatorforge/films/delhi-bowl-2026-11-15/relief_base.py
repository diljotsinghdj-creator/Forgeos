"""Glowing relief map: real terrain heights (Terrarium tiles), a country lit in neon, a black grid floor, a glowing
route tube, bloom (three.js UnrealBloomPass), and paper labels on top. Served over http://localhost (module scripts)."""
import json
from pathlib import Path
from mask import uv
INDIA_UV = json.loads((Path(__file__).resolve().parent / "maps" / "north_india_uv.json").read_text())
D = Path(__file__).resolve().parent
V = "/vendor/three160"
FONTS = "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts"


def page(name, cfg):
    m = json.loads((D / "maps" / f"{name}_h.json").read_text())
    route = [uv(name, lo, la) for lo, la in cfg.get("route", [])]
    pins = [dict(p, uv=uv(name, p["lon"], p["lat"])) for p in cfg.get("pins", [])]
    C = dict(cfg, name=name, aspect=m["h"] / m["w"], route=route, pins=pins, outline=INDIA_UV)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}}@font-face{{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}}
@font-face{{font-family:Serif;src:url(/fonts/dm-serif-display-latin-400-normal.woff2)}}@font-face{{font-family:Marker;src:url(/fonts/permanent-marker-latin-400-normal.woff2)}}
body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#000}} canvas{{position:absolute;left:0;top:0}}
.lab{{position:absolute;transform:translate(-50%,-100%);white-space:nowrap}} .grain{{position:absolute;inset:0;pointer-events:none;opacity:.22;mix-blend-mode:overlay}}
</style><script type="importmap">{{"imports":{{"three":"{V}/three.module.js","three/addons/":"{V}/addons/"}}}}</script></head><body>
<div id="ov"></div><svg class="grain" width="1920" height="1080"><filter id="g"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2"/></filter><rect width="1920" height="1080" filter="url(#g)"/></svg>
<script type="module">
import * as THREE from 'three';
import {{EffectComposer}} from 'three/addons/postprocessing/EffectComposer.js';
import {{RenderPass}} from 'three/addons/postprocessing/RenderPass.js';
import {{UnrealBloomPass}} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {{OutputPass}} from 'three/addons/postprocessing/OutputPass.js';
const C={json.dumps(C)};
const load=src=>new Promise(r=>{{const i=new Image();i.onload=()=>{{const c=document.createElement('canvas');c.width=i.width;c.height=i.height;const x=c.getContext('2d');x.drawImage(i,0,0);r({{w:i.width,h:i.height,d:x.getImageData(0,0,i.width,i.height).data}})}};i.src=src}});
const [H,M]=await Promise.all([load('/maps/'+C.name+'_h8.png'),load('/maps/'+C.name+'_mask.png')]);
const samp=(img,u,v)=>{{const x=Math.min(img.w-1,Math.max(0,Math.round(u*(img.w-1)))),y=Math.min(img.h-1,Math.max(0,Math.round(v*(img.h-1))));return img.d[(y*img.w+x)*4]/255}};
const R=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});R.setSize(1920,1080);R.setPixelRatio(1);document.body.prepend(R.domElement);
R.toneMapping=THREE.ACESFilmicToneMapping;
const S=new THREE.Scene();S.background=new THREE.Color(C.bg||'#030304');S.fog=new THREE.Fog(C.bg||'#030304',C.fog[0],C.fog[1]);
const Wd=100,Hd=100*C.aspect,seg=C.seg||520,ex=C.exag;
const G=new THREE.PlaneGeometry(Wd,Hd,seg,Math.round(seg*C.aspect));G.rotateX(-Math.PI/2);
const P=G.attributes.position,col=[];const base=new THREE.Color(C.base),hot=new THREE.Color(C.hot),hi=new THREE.Color(C.peak||C.hot);
for(let i=0;i<P.count;i++){{const u=P.getX(i)/Wd+.5,v=P.getZ(i)/Hd+.5;const h=samp(H,u,v);P.setY(i,h*ex);
 const m=samp(M,u,v);const c=base.clone().lerp(hot,m).lerp(hi,m*Math.pow(h,1.6)*.8);col.push(c.r,c.g,c.b)}}
G.setAttribute('color',new THREE.Float32BufferAttribute(col,3));G.computeVertexNormals();
const mat=new THREE.MeshStandardMaterial({{vertexColors:true,roughness:.85,metalness:.05,flatShading:false}});
mat.onBeforeCompile=s=>{{s.fragmentShader=s.fragmentShader.replace('#include <emissivemap_fragment>','#include <emissivemap_fragment>\\n totalEmissiveRadiance += vColor.rgb*max(vColor.r-vColor.b-.25,0.)*{C.get("glow",0.55)};')}};
S.add(new THREE.Mesh(G,mat));
const grid=new THREE.GridHelper(400,80,C.grid,C.grid);grid.position.y=-.3;grid.material.transparent=true;grid.material.opacity=.35;S.add(grid);
S.add(new THREE.AmbientLight('#ffffff',.25));const L=new THREE.DirectionalLight('#ffffff',1.6);L.position.set(-60,40,-30);S.add(L);
const L2=new THREE.DirectionalLight(C.hot,.5);L2.position.set(50,20,60);S.add(L2);
const at=(u,v,lift)=>new THREE.Vector3((u-.5)*Wd,samp(H,u,v)*ex+(lift||0),(v-.5)*Hd);
if(C.route.length){{const pts=[];for(let i=0;i<C.route.length-1;i++){{for(let t=0;t<1;t+=.05){{const u=C.route[i][0]+(C.route[i+1][0]-C.route[i][0])*t,v=C.route[i][1]+(C.route[i+1][1]-C.route[i][1])*t;pts.push(at(u,v,.6))}}}}
 pts.push(at(...C.route[C.route.length-1],.6));const cur=new THREE.CatmullRomCurve3(pts);
 S.add(new THREE.Mesh(new THREE.TubeGeometry(cur,600,.28,8),new THREE.MeshBasicMaterial({{color:new THREE.Color(C.line).multiplyScalar(2.2)}})));
 for(const p of [pts[0],pts[pts.length-1]]){{const s=new THREE.Mesh(new THREE.SphereGeometry(.7,16,16),new THREE.MeshBasicMaterial({{color:'#ffffff'}}));s.position.copy(p);S.add(s)}}}}
if(C.haze){{const hz=new THREE.Mesh(new THREE.PlaneGeometry(Wd,Hd),new THREE.MeshBasicMaterial({{color:C.haze[1],transparent:true,opacity:C.haze[2],depthWrite:false}}));hz.rotation.x=-Math.PI/2;hz.position.y=C.haze[0]*ex;S.add(hz);
 for(let k=1;k<5;k++){{const l=hz.clone();l.material=hz.material.clone();l.material.opacity=C.haze[2]*.4;l.position.y=C.haze[0]*ex*(1-k*.18);S.add(l)}}}}
for(const ring of C.outline){{const pts=ring.map(([u,v])=>at(u,v,.35));const g=new THREE.BufferGeometry().setFromPoints(pts.concat([pts[0]]));
 const ln=new THREE.Line(g,new THREE.LineBasicMaterial({{color:new THREE.Color(C.outlineCol).multiplyScalar(1.3),depthTest:false,transparent:true,opacity:.95}}));ln.renderOrder=10;S.add(ln)}}
const cam=new THREE.PerspectiveCamera(C.fov||32,1920/1080,.1,1000);cam.position.set(...C.cam);cam.lookAt(...C.look);
const comp=new EffectComposer(R);comp.addPass(new RenderPass(S,cam));comp.addPass(new UnrealBloomPass(new THREE.Vector2(1920,1080),C.bloom[0],C.bloom[1],C.bloom[2]));comp.addPass(new OutputPass());
comp.render();
const ov=document.getElementById('ov');
for(const p of C.pins){{const v=at(p.uv[0],p.uv[1],1).project(cam);const x=(v.x+1)/2*1920,y=(1-v.y)/2*1080;
 const d=document.createElement('div');d.className='lab';d.style.left=x+'px';d.style.top=y+'px';d.innerHTML=p.html;ov.appendChild(d)}}
ov.insertAdjacentHTML('beforeend',C.overlay||'');
await document.fonts.ready;window.READY=true;
</script></body></html>"""


