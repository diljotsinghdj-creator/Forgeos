"""Data maps with deck.gl (MIT, bundled): figures that stand on the map itself, in the film's paper look, with a
tilted camera that moves.

    Flowmap: China → Netherlands 120, China → USA 90, India → UAE 40 | Container trade | million tonnes | src: UNCTAD
        arcs that lift off the map and draw themselves, as wide as their number, with light travelling along them
    Columns: India 1.43, China 1.41, USA 0.34 | Population | billion | src: UN
        3D columns that rise from each place to its number
    Dots: Tokyo 37, Delhi 32, Shanghai 29, Dhaka 23 | The biggest cities | million people | src: UN
        circles whose area is the number, pulsing gently

Places are countries or cities the map knows (media/maps.py); a name it does not know refuses the line instead of
guessing a position. Labels are set in the film's typefaces over the map, at the projected position of each place.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

from .ff import MediaError

KINDS = ("flowmap", "columns", "dots")
VENDOR = Path(__file__).parent / "vendor"


def _parts(spec: str) -> tuple[str, str, str, str]:
    parts = [p.strip() for p in (spec or "").split("|")]
    src = next((p.split(":", 1)[1].strip() for p in parts[1:] if p.lower().startswith("src:")), "")
    rest = [p for p in parts[1:] if not p.lower().startswith("src:")]
    return parts[0], (rest[0] if rest else "")[:48], (rest[1] if len(rest) > 1 else "")[:24], src[:60]


def _arc(a: dict, b: dict, n: int = 64) -> list[list[float]]:
    """An arc from a to b drawn straight across the flat map, lifting off it (height in metres). A great circle would
    bend towards the pole on a flat map and leave the frame; the lift is capped so a long route stays in the picture."""
    lo1, la1, lo2, la2 = a["lon"], a["lat"], b["lon"], b["lat"]
    km = math.hypot((lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2)), la2 - la1) * 111.0
    top = min(km * 0.12, 900.0) * 1000
    return [[round(lo1 + (lo2 - lo1) * f, 4), round(la1 + (la2 - la1) * f, 4), round(math.sin(math.pi * f) * top, 1)]
            for f in (i / n for i in range(n + 1))]


def parse(kind: str, spec: str) -> dict | None:
    from . import vox
    head, title, unit, src = _parts(spec)
    items = []
    if kind == "flowmap":
        for chunk in re.split(r",(?!\d{3}\b)|;", head):
            m = re.match(r"\s*(.+?)\s*(?:→|->)\s*(.+?)\s+(-?\d[\d,]*(?:\.\d+)?)\s*$", chunk)
            if not m:
                continue
            g = vox._geo([m.group(1), m.group(2)])
            if len(g) != 2:
                return None                          # an unknown place: never a guessed position
            items.append({"a": g[0], "b": g[1], "value": float(m.group(3).replace(",", "")), "shown": m.group(3), "path": _arc(g[0], g[1])})
        pts = [(e["lon"], e["lat"]) for it in items for e in (it["a"], it["b"])]
    else:
        for v in vox._pairs(head):
            g = vox._geo([v["label"]])
            if not g:
                return None
            items.append({"at": g[0], "value": v["value"], "shown": v["shown"], "label": v["label"]})
        pts = [(it["at"]["lon"], it["at"]["lat"]) for it in items]
    if len(items) < (1 if kind == "flowmap" else 2):
        return None
    box, shapes = vox._map_frame(pts, 0.35)
    return {"type": kind, "items": items[:12], "box": box, "shapes": shapes, "title": title, "unit": unit, "src": src}


_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
html,body{margin:0;padding:0;overflow:hidden;width:%W%px;height:%H%px;background:%SEA%}
#deck{position:absolute;left:0;top:0;width:%W%px;height:%H%px}
#ov{position:absolute;left:0;top:0;width:%W%px;height:%H%px;pointer-events:none}
#grain{position:absolute;left:0;top:0;width:%W%px;height:%H%px;background:url('%GRAIN%') center/cover;mix-blend-mode:multiply;opacity:.45}
.t{position:absolute;white-space:nowrap;transform:translate(-50%,-50%)}
.box{background:#141414;color:#fff;padding:.12em .32em;font-weight:900}
.tag{background:#141414;color:#fff;padding:.18em .5em;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.val{color:#141414;text-shadow:0 0 6px #fff,0 0 2px #fff}
.src{color:#3a3a3a;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
</style><script>%DECK%</script></head><body><div id="deck"></div><div id="ov"></div><div id="grain"></div><script>
const P=%PLAN%, W=%W%, H=%H%, DUR=%DUR%, K=%KIT%;
const TALL=H>W, U=Math.min(W,H);
const E={out:t=>1-Math.pow(1-t,3), inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2};
const cl=(v)=>Math.max(0,Math.min(1,v)), seg=(t,s,d)=>cl((t-s)/d), leave=t=>1-seg(t,DUR-.55,.35);
const rgb=(h,a)=>[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16),a===undefined?255:a];
const OV=document.getElementById('ov');
function label(text,cls,size,fam,weight){const d=document.createElement('div');d.className='t '+cls;d.textContent=text;
  d.style.fontFamily="'"+((K.fam||{})[fam]||fam)+"'";d.style.fontSize=size+'px';d.style.fontWeight=weight||800;d.style.opacity=0;OV.appendChild(d);return d}
const [x0,y0,x1,y1]=P.box,clon=(x0+x1)/2,clat=(y0+y1)/2;
const span=Math.max((x1-x0)*Math.cos(clat*Math.PI/180),(y1-y0)*1.25);
const zoom0=Math.log2(360/span*Math.min(W,H*1.6)/512)-.15;
const land={type:'FeatureCollection',features:P.shapes.map(r=>({type:'Feature',geometry:{type:'Polygon',coordinates:[r]}}))};
const tt=P.title?label(P.title.toUpperCase(),'box',U*.05,'Playfair',900):null;if(tt){tt.style.left=W/2+'px';tt.style.top=(H*.08)+'px'}
const un=P.unit?label(P.unit,'src',U*.02,'Mono',700):null;if(un){un.style.left=W/2+'px';un.style.top=(H*.14)+'px'}
const sr=P.src?label('SOURCE: '+P.src,'src',U*.015,'Mono',700):null;if(sr){sr.style.left=(W-U*.04)+'px';sr.style.top=(H-U*.03)+'px';sr.style.transform='translate(-100%,-50%)'}
const COLH=.16;const mx=Math.max(...P.items.map(i=>i.value)),acc=rgb(K.acc);
let labs=[];
if(P.type==='flowmap'){P.items.forEach(it=>{it.la=label(it.a.name,'tag',U*.019,'Inter',800);it.lb=label(it.b.name,'tag',U*.019,'Inter',800);it.lv=label(it.shown,'val',U*.04,'Anton',400)})}
else P.items.forEach(it=>{it.ln=label(it.label,'tag',U*.019,'Inter',800);it.lv=label(it.shown,'val',U*.042,'Anton',400)});
function layers(t){const out=[new deck.GeoJsonLayer({id:'land',data:land,filled:true,stroked:true,getFillColor:rgb(K.land),getLineColor:rgb(K.edge),lineWidthUnits:'pixels',getLineWidth:1})];
  if(P.type==='flowmap'){const n=P.items.length;
    const paths=P.items.map((it,i)=>{const p=E.inout(seg(t,.5+i*.45,1.2));const k=Math.max(2,Math.round(p*(it.path.length-1))+1);return {path:it.path.slice(0,k),w:4+18*it.value/mx,i}});
    out.push(new deck.PathLayer({id:'arcs',data:paths,getPath:d=>d.path,getWidth:d=>d.w,widthUnits:'pixels',getColor:[...acc.slice(0,3),230],capRounded:true,jointRounded:true,updateTriggers:{getPath:t}}));
    const heads=[];P.items.forEach((it,i)=>{const p=seg(t,.5+i*.45,1.2);if(p>=1){for(let q=0;q<3;q++){const f=((t*.35+q/3+i*.17)%1),j=Math.floor(f*(it.path.length-1));heads.push({p:it.path[j],r:3+5*it.value/mx})}}});
    out.push(new deck.ScatterplotLayer({id:'heads',data:heads,getPosition:d=>d.p,getRadius:d=>d.r,radiusUnits:'pixels',getFillColor:[255,250,235,235],updateTriggers:{getPosition:t}}));
    const ends=P.items.flatMap(it=>[it.a,it.b]);out.push(new deck.ScatterplotLayer({id:'ends',data:ends,getPosition:d=>[d.lon,d.lat],getRadius:6,radiusUnits:'pixels',getFillColor:[20,20,20,255],getLineColor:[255,255,255,255],stroked:true,lineWidthUnits:'pixels',getLineWidth:2}))}
  else if(P.type==='columns'){const km=Math.max(20,span*111*.022);
    out.push(new deck.ColumnLayer({id:'cols',data:P.items,getPosition:d=>[d.at.lon,d.at.lat],diskResolution:24,radius:km*1000,extruded:true,
      getElevation:d=>{const i=P.items.indexOf(d);return E.out(seg(t,.4+i*.25,1.1))*d.value/mx*span*111000*COLH},getFillColor:d=>d.value===mx?acc:[70,82,92,255],
      material:{ambient:.55,diffuse:.6,shininess:20},updateTriggers:{getElevation:t}}))}
  else{out.push(new deck.ScatterplotLayer({id:'dots',data:P.items,getPosition:d=>[d.at.lon,d.at.lat],stroked:true,lineWidthUnits:'pixels',getLineWidth:2,
      getRadius:d=>{const i=P.items.indexOf(d);return E.out(seg(t,.4+i*.22,.8))*Math.sqrt(d.value/mx)*span*111000*.06*(1+.04*Math.sin(t*3+i))},
      getFillColor:[...acc.slice(0,3),170],getLineColor:[20,20,20,255],updateTriggers:{getRadius:t}}))}
  return out}
const pitch=P.type==='columns'?45:P.type==='flowmap'?30:18;
function view(t){const p=E.inout(cl(t/DUR));return {longitude:clon+(x1-x0)*.04*(p-.5),latitude:clat-(y1-y0)*.06*p,zoom:zoom0+.25*p,pitch:pitch*(.55+.45*p),bearing:-8+16*p}}
let done=null;
const dk=new deck.Deck({parent:document.getElementById('deck'),width:W,height:H,controller:false,views:new deck.MapView({repeat:true}),
  initialViewState:view(0),layers:layers(0),_animate:false,useDevicePixels:1,deviceProps:{webgl:{preserveDrawingBuffer:true}},
  onAfterRender:()=>{if(done){const d=done;done=null;d()}}});
function place(el,lon,lat,alt,dy){const vp=dk.getViewports()[0];if(!vp)return;const [x,y]=vp.project([lon,lat,alt||0]);el.style.left=x+'px';el.style.top=(y+(dy||0))+'px'}
window.frame=t=>new Promise(res=>{done=res;dk.setProps({viewState:view(t),layers:layers(t)});setTimeout(()=>{if(done===res){done=null;res()}},400);
  requestAnimationFrame(()=>{if(tt)tt.style.opacity=seg(t,.1,.3)*leave(t);if(un)un.style.opacity=seg(t,.3,.3)*leave(t);if(sr)sr.style.opacity=seg(t,.6,.3)*leave(t)*.9;
    P.items.forEach((it,i)=>{if(P.type==='flowmap'){const s0=.5+i*.45;place(it.la,it.a.lon,it.a.lat,0,-U*.035);place(it.lb,it.b.lon,it.b.lat,0,-U*.035);
        const m=it.path[Math.floor(it.path.length/2)];place(it.lv,m[0],m[1],m[2],-U*.04);it.la.style.opacity=seg(t,s0,.3)*leave(t);it.lb.style.opacity=seg(t,s0+1,.3)*leave(t);it.lv.style.opacity=seg(t,s0+1.1,.3)*leave(t)}
      else{const s0=.4+i*.25;place(it.ln,it.at.lon,it.at.lat,0,U*.035);const h=P.type==='columns'?E.out(seg(t,s0,1.1))*it.value/mx*span*111000*COLH:0;
        place(it.lv,it.at.lon,it.at.lat,h,P.type==='columns'?-U*.035:-U*.01);it.ln.style.opacity=seg(t,s0,.3)*leave(t);it.lv.style.opacity=seg(t,s0+.6,.3)*leave(t)}})})});
document.fonts.ready.then(()=>window.frame(0)).then(()=>{window.READY=true});
</script></body></html>"""


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path, fps: int | None = None) -> Path:
    from . import motion, vox
    if not motion.enabled():
        raise MediaError("data maps need the animation engine (Chromium + Playwright)")
    plan = parse(kind, spec)
    if plan is None:
        raise MediaError(f"{kind}: a place in the line is not on the map, or the line has too few figures")
    look = vox.look_of(theme)
    _, grain = vox.paper(look["paper"], width, height, work)
    kit = {"acc": vox.accent_of(theme), "land": look["land"], "edge": look["edge"],
           "fam": {"Playfair": look["head"], "Anton": look["big"], "Caveat": look["hand"]}}
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or 30)
    page = (_PAGE.replace("%DECK%", (VENDOR / "deckgl.min.js").read_text(encoding="utf-8")).replace("%FONTS%", vox._font_css())
            .replace("%SEA%", look["sea"]).replace("%GRAIN%", grain.as_uri()).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{max(2.0, seconds):.3f}").replace("%KIT%", json.dumps(kit)))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"datamap_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    return motion.capture(html, width, height, max(2.0, seconds), fps, out)
