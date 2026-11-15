"""Two looks from the owner's references (2026-11-15), on real data:
H: hologram terrain: the Punjab's real heights as a glowing wireframe on a black grid, the five rivers as cyan light.
K: dark satellite: low-key monochrome Sentinel-2 of the five-rivers region, the rivers as thin flowing light.
Each is rendered at two moments of its animation (rivers half drawn, then flowing)."""
import json
from frames import page, a, put, SIG, RED, SAFE_TOP, maps, SRC25
import mask as M
from new_pages import R, FIVE, STATES, INDIA, LABEL, downstream, P, ring, SRCR, S2

V = "/vendor/three160"
FONTS = ("@font-face{font-family:Anton;src:url(/fonts/anton-latin-400-normal.woff2)}"
         "@font-face{font-family:Plex;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}")

for tag, prog in (("a", 0.55), ("b", 1.0)):
    # ---- H: hologram terrain -------------------------------------------------------------------------------------
    lines = []
    for i, n in enumerate(FIVE):
        t = 1.0 if prog >= 1 else max(0.0, min(1.0, (prog - i * .08) / .4))
        for line in R[n]:
            l = downstream(line)
            l = l[:max(2, int(len(l) * t))] if t > 0 else []
            if len(l) >= 2:
                lines.append([M.uv("rivers5", lo, la) for lo, la in l])
    pins = [{"n": n, "uv": M.uv("rivers5", *LABEL[n])} for n in FIVE] if prog >= 1 else []
    m = json.load(open("maps/rivers5_h.json"))
    C = {"aspect": m["h"] / m["w"], "rivers": lines, "pins": pins, "flow": prog >= 1}
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}
body{{margin:0;width:1080px;height:1920px;overflow:hidden;background:#010604}} canvas{{position:absolute;left:0;top:0}} .lab{{position:absolute;transform:translate(-50%,-140%);
font:500 22px Plex;letter-spacing:4px;color:#9FFFF0;background:rgba(0,20,16,.75);border:1px solid #2CE0C0;padding:4px 10px;white-space:nowrap}}</style>
<script type="importmap">{{"imports":{{"three":"{V}/three.module.js","three/addons/":"{V}/addons/"}}}}</script></head><body><div id="ov"></div>
<script type="module">
import * as THREE from 'three';
import {{EffectComposer}} from 'three/addons/postprocessing/EffectComposer.js';
import {{RenderPass}} from 'three/addons/postprocessing/RenderPass.js';
import {{UnrealBloomPass}} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {{OutputPass}} from 'three/addons/postprocessing/OutputPass.js';
const C={json.dumps(C)};
const img=await new Promise(r=>{{const i=new Image();i.onload=()=>{{const c=document.createElement('canvas');c.width=i.width;c.height=i.height;const x=c.getContext('2d');x.drawImage(i,0,0);
  r({{w:i.width,h:i.height,d:x.getImageData(0,0,i.width,i.height).data}})}};i.src='/maps/rivers5_h8.png'}});
const H=(u,v)=>{{const x=Math.min(img.w-1,Math.max(0,Math.round(u*(img.w-1)))),y=Math.min(img.h-1,Math.max(0,Math.round(v*(img.h-1))));return img.d[(y*img.w+x)*4]/255}};
const R=new THREE.WebGLRenderer({{antialias:true,preserveDrawingBuffer:true}});R.setSize(1080,1920);R.setPixelRatio(1);document.body.prepend(R.domElement);
const S=new THREE.Scene();S.background=new THREE.Color('#010604');S.fog=new THREE.Fog('#010604',60,170);
const Wd=100,Hd=100*C.aspect,ex=18;
const G=new THREE.PlaneGeometry(Wd,Hd,240,Math.round(240*C.aspect));G.rotateX(-Math.PI/2);
const P=G.attributes.position,col=[];const lo=new THREE.Color('#0B6B4A'),mid=new THREE.Color('#5BE06A'),hi=new THREE.Color('#F2B233');
for(let i=0;i<P.count;i++){{const u=P.getX(i)/Wd+.5,v=P.getZ(i)/Hd+.5;const h=H(u,v);P.setY(i,Math.pow(h,.8)*ex);
  const c=h<.3?lo.clone().lerp(mid,h/.3):mid.clone().lerp(hi,Math.min(1,(h-.3)/.5));col.push(c.r,c.g,c.b)}}
G.setAttribute('color',new THREE.Float32BufferAttribute(col,3));G.computeVertexNormals();
S.add(new THREE.Mesh(G,new THREE.MeshBasicMaterial({{color:'#02140D',polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1}})));
const wire=new THREE.LineSegments(new THREE.WireframeGeometry(G),new THREE.LineBasicMaterial({{vertexColors:true,transparent:true,opacity:.32}}));
wire.geometry.setAttribute('color',(()=>{{const pos=wire.geometry.attributes.position,c=[];for(let i=0;i<pos.count;i++){{const h=pos.getY(i)/ex;
  const k=h<.3?lo.clone().lerp(mid,h/.3):mid.clone().lerp(hi,Math.min(1,(h-.3)/.5));c.push(k.r*.9,k.g*.9,k.b*.9)}}return new THREE.Float32BufferAttribute(c,3)}})());
S.add(wire);
const grid=new THREE.GridHelper(400,160,'#0C3A2C','#08261D');grid.position.y=-.4;S.add(grid);
const at=(u,v,l)=>new THREE.Vector3((u-.5)*Wd,Math.pow(H(u,v),.8)*ex+(l||0),(v-.5)*Hd);
for(const L of C.rivers){{const pts=L.map(([u,v])=>at(u,v,.35));const cur=new THREE.CatmullRomCurve3(pts);
  S.add(new THREE.Mesh(new THREE.TubeGeometry(cur,Math.max(16,pts.length*4),.26,8),new THREE.MeshBasicMaterial({{color:new THREE.Color('#38F2E0').multiplyScalar(1.15)}})));
  if(C.flow){{for(let k=0;k<pts.length;k+=6){{const s=new THREE.Mesh(new THREE.SphereGeometry(.3,8,8),new THREE.MeshBasicMaterial({{color:new THREE.Color('#FFFFFF').multiplyScalar(1.6)}}));s.position.copy(cur.getPoint(k/pts.length));S.add(s)}}}}}}
const cam=new THREE.PerspectiveCamera(42,1080/1920,.1,500);cam.position.set(-34,26,52);cam.lookAt(6,2,-22);
const comp=new EffectComposer(R);comp.addPass(new RenderPass(S,cam));comp.addPass(new UnrealBloomPass(new THREE.Vector2(1080,1920),.5,.35,.55));comp.addPass(new OutputPass());comp.render();
const ov=document.getElementById('ov');
for(const p of C.pins){{const v=at(p.uv[0],p.uv[1],1).project(cam);const d=document.createElement('div');d.className='lab';d.style.left=((v.x+1)/2*1080)+'px';d.style.top=((1-v.y)/2*1920)+'px';d.textContent=p.n.toUpperCase();ov.appendChild(d)}}
ov.insertAdjacentHTML('beforeend',`<div style="position:absolute;left:0;top:0;width:1080px;height:520px;background:linear-gradient(#010604 50%,transparent)"></div>
<div style="position:absolute;left:70px;top:{SAFE_TOP}px;font:400 104px/0.95 Anton;color:#E9FFF7;width:940px;text-shadow:0 0 24px rgba(56,242,224,.5)">THE LAND OF<br>FIVE RIVERS</div>
<div style="position:absolute;left:74px;top:{SAFE_TOP + 214}px;font:500 22px Plex;letter-spacing:4px;color:#38F2E0">JHELUM · CHENAB · RAVI · BEAS · SUTLEJ</div>
<div style="position:absolute;left:0;right:0;top:1574px;padding:16px 40px;background:linear-gradient(transparent,rgba(0,0,0,.85) 30%);font:500 17px/1.5 Plex;letter-spacing:1px;color:rgba(200,255,240,.6)">
REAL TERRAIN: TERRARIUM TILES (SRTM), HEIGHTS EXAGGERATED · {SRCR} · WIREFRAME LOOK DRAWN IN THE STUDIO</div>`);
await document.fonts.ready;window.READY=true;
</script></body></html>"""
    put(f"look_holo_{tag}", html)

    # ---- K: dark satellite ------------------------------------------------------------------------------------------
    riv = ""
    for i, n in enumerate(FIVE):
        t = 1.0 if prog >= 1 else max(0.0, min(1.0, (prog - i * .08) / .4))
        for line in R[n]:
            d = "M" + " L".join("%.1f %.1f" % P(lo, la) for lo, la in downstream(line))
            riv += (f'<path d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1 - t:.3f}" fill="none" stroke="#DDEBFF" stroke-width="10" opacity=".25" filter="url(#bl)"/>'
                    f'<path d="{d}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="{1 - t:.3f}" fill="none" stroke="#EAF3FF" stroke-width="2.6" stroke-linecap="round"/>')
            if prog >= 1:
                riv += f'<path d="{d}" pathLength="1" stroke-dasharray="0.01 0.05" stroke-dashoffset="-0.02" fill="none" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round"/>'
    labs = "".join(a(f'<div style="font:500 20px Plex;letter-spacing:6px;color:rgba(234,243,255,.85)">{n.upper()}</div>', P(*LABEL[n])[0] - 50, P(*LABEL[n])[1] - 30)
                   for n in FIVE) if prog >= 1 else ""
    put(f"look_dark_{tag}", page(
        a('<img src="/maps/s2_rivers.jpg" style="width:1080px;height:1148px;filter:grayscale(1) contrast(1.45) brightness(.62)">', 0, 330)
        + a('<div style="width:1080px;height:1148px;background:radial-gradient(ellipse at 55% 40%,transparent 35%,rgba(0,0,0,.85) 100%)"></div>', 0, 330)
        + a('<div style="width:1080px;height:330px;background:linear-gradient(#000 40%,transparent)"></div>', 0, 330)
        + '<svg class="a" style="left:0;top:0" width="1080" height="1920"><defs><filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>'
          '<clipPath id="k"><rect x="0" y="330" width="1080" height="1148"/></clipPath></defs><g clip-path="url(#k)">'
        + ring(INDIA, fill="none", stroke="rgba(255,255,255,.35)", stroke_width=1.5)
        + ring(STATES["Punjab"], fill="none", stroke=(SIG if prog >= 1 else "rgba(255,255,255,.5)"), stroke_width=3) + riv + "</g></svg>" + labs
        + a('<div style="font:400 110px/0.95 Anton;color:#F2F2F2;width:940px;letter-spacing:2px">FIVE RIVERS.</div>', 70, SAFE_TOP)
        + (a(f'<div style="font:400 110px/0.95 Anton;color:{SIG};width:940px;letter-spacing:2px">ONE OVERDRAFT.</div>', 70, SAFE_TOP + 110) if prog >= 1 else ""),
        "#000", SRC25 + " · " + SRCR + " · " + S2 + " (SHOWN IN MONOCHROME) · INDIA: OFFICIAL BOUNDARY", dark=True))
print("ok")
