"""Smooth motion graphics for explainer lines, drawn with SVG.js (MIT) in headless Chromium and captured frame by frame.

The same script lines as the FFmpeg/ASS cards, rendered as real vector animation with easing curves:

    Chart: ₹12 → ₹720 | a year of subscriptions        a number that counts up, an underline that draws
    Chart: 48% vs 22% | heavy users, everyone else      bars that grow one after another, values counting
    Chart: 76% | of sites used a dark pattern           a bar that fills
    Chart: £1bn → £3bn → £8bn | losses | 2015, 2020, 2025   a line graph that draws itself, dots popping
    Timeline: 2014 BJP at Centre → 2019 Home Minister | ...   a line drawing across, each date dropping in
    Steps: Group → Forward → Belief → Forward | ...      boxes popping in with arrows drawing between them
    Pie: 67% | committee votes                          a donut sweeping round, the share counting up
    Squares: 13.3 vs 12.3 | crore names, Japan          squares to scale, growing from a corner

Every frame is computed from the time alone (frame(t)), so a render is exactly repeatable and resumable. Nothing is
fetched from the network: SVG.js is vendored next to this file. If Chromium is missing, render() raises MediaError
and the pipeline keeps its FFmpeg card for the line. CF_MOTION=0 turns the engine off."""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
from pathlib import Path

from .ff import MediaError

KINDS = ("chart", "timeline", "steps", "pie", "squares", "animate")
VENDOR = Path(__file__).parent / "vendor" / "svg.min.js"
THEMES = {   # background, ink, accent, second, grid
    "investigative": ("#EFE8D8", "#1A1A1A", "#C8102E", "#5A5A5A", True),
    "editorial": ("#F2EBDD", "#111111", "#E8B400", "#111111", False),
}
_BOLD_FONTS = ("/usr/share/fonts/truetype/creatorforge/ArchivoBlack-Regular.ttf",
               str(Path.home() / ".fonts" / "ArchivoBlack-Regular.ttf"))


def enabled() -> bool:
    if os.environ.get("CF_MOTION", "1") == "0" or not VENDOR.is_file():
        return False
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


# ---- what to draw --------------------------------------------------------------------------------------------------
def plan_for(kind: str, spec: str) -> dict | None:
    """The drawing plan for a script line, or None when the line has nothing this engine can draw."""
    spec = (spec or "").strip()
    if not spec:
        return None
    if kind == "animate":
        from .scene_anim import parse as scene_parse
        return scene_parse(spec)
    if kind == "chart":
        from .charts import parse
        head, _, rest = spec.partition("|")
        pairs = [re.match(r"^\s*(\d{4}(?:[-–]\d{2,4})?|[A-Za-z]{3,9}\s+\d{4})\s+(.+?)\s*$", x)
                 for x in re.split(r"→|->", head)]
        if len(pairs) >= 3 and all(pairs):          # "2021-22 176 → 2022-23 163 → ..." : years are the ticks
            ticks = ", ".join(m.group(1) for m in pairs)
            spec = " → ".join(m.group(2) for m in pairs) + f" | {rest.strip()} | {ticks}"
        p = parse(spec)
        return {"type": p["kind"], **p} if p else None
    head, _, tail = spec.partition("|")
    if kind == "timeline":
        items = []
        for part in [x.strip() for x in re.split(r"→|->|;", head) if x.strip()][:6]:
            m = re.match(r"^((?:c\.\s*)?\d{3,4}s?|\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{4}|\d{1,2}\s+[A-Z]{3})\s*[:,-]?\s*(.*)$",
                         part)
            items.append([m.group(1), m.group(2)] if m else ["", part])
        if len(items) < 2 and "|" in head + tail and spec.count("|") >= 2:
            items = []
        if len(items) < 2:
            parts = [x.strip() for x in spec.split("|") if x.strip()]       # "Timeline: 12 MAY x | 21 JUN y"
            for part in parts[:6]:
                m = re.match(r"^(\d{1,2}\s+[A-Za-z]{3,9}(?:\s+\d{4})?|[A-Za-z]{3,9}\s+\d{4}|\d{4}|\?)\s+(.*)$", part)
                items.append([m.group(1), m.group(2)] if m else ["", part])
            tail = ""
        return {"type": "timeline", "items": items, "title": tail.strip()} if len(items) >= 2 else None
    if kind == "steps":
        if "→" not in head and "->" not in head and spec.count("|") >= 2:
            head, tail = spec.replace("|", "→"), ""
        steps = [x.strip() for x in head.replace("->", "→").split("→") if x.strip()][:6]
        return {"type": "steps", "steps": steps, "title": tail.strip()} if len(steps) >= 2 else None
    if kind == "pie":
        m = re.search(r"(\d+(?:\.\d+)?)\s*%?", head)
        if not m:
            return None
        return {"type": "pie", "value": max(0.0, min(100.0, float(m.group(1)))), "label": tail.strip()}
    if kind == "squares":
        from .charts import amounts
        nums = [[shown, v] for shown, v, _, _ in amounts(head) if v > 0][:3]
        if len(nums) < 2:
            return None
        names = [x.strip() for x in tail.split(",")] if tail.strip() else []
        return {"type": "squares", "values": nums, "labels": (names + [""] * len(nums))[:len(nums)]}
    return None


# ---- the page ------------------------------------------------------------------------------------------------------
_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTFACE%
html,body{margin:0;padding:0;background:%BG%;overflow:hidden}
svg{display:block}
text{font-family:'CFBold','DejaVu Sans','FreeSans','Noto Sans Devanagari',sans-serif}
.lbl{font-family:'DejaVu Sans','FreeSans','Noto Sans Devanagari',sans-serif;font-weight:700}
</style><script>%SVGJS%</script></head><body><script>
const P=%PLAN%, W=%W%, H=%H%, DUR=%DUR%, TH=%THEME%;
const [BG,INK,ACC,SEC,GRID]=TH; const TALL=H>W; const U=Math.min(W,H);
const draw=SVG().addTo('body').size(W,H);
const tracks=[];
const ease={out:t=>1-Math.pow(1-t,3), expo:t=>t>=1?1:1-Math.pow(2,-10*t), inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
  back:t=>{const c=1.70158,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)}};
function at(start,dur,fn,e){tracks.push({start,dur,fn,e:e||ease.out})}
function fmt(v,dec){const s=Math.abs(v)>=100||dec===0?Math.round(v).toLocaleString('en-IN'):v.toFixed(1);return s}
function decOf(v){return Number.isInteger(v)?0:1}
// paper: grid + vignette
if(GRID){const g=draw.group().opacity(.35);const step=Math.round(H/26);
  for(let x=0;x<W;x+=step)g.line(x,0,x,H).stroke({color:'#7FA3C8',width:1});
  for(let y=0;y<H;y+=step)g.line(0,y,W,y).stroke({color:'#7FA3C8',width:1});}
const grad=draw.gradient('radial',a=>{a.stop(0.62,'#000',0);a.stop(1,'#000',.1)});
const stage=draw.group();
function txt(g,s,size,x,y,opt){opt=opt||{};const t=g.text(String(s)).font({size:size,anchor:opt.anchor||'middle',weight:opt.weight||'bold'})
  .fill(opt.fill||INK).attr({x:x,y:y,'dominant-baseline':'middle'});if(opt.cls)t.addClass(opt.cls);return t}
function wrap(g,s,size,x,y,maxw,opt){opt=opt||{};const words=String(s).split(/\s+/);const lines=[];let cur='';
  const probe=g.text('').font({size:size,weight:'bold'});if(opt.cls)probe.addClass(opt.cls);
  for(const w of words){const tryS=cur?cur+' '+w:w;probe.text(tryS);if(cur&&probe.length()>maxw){lines.push(cur);cur=w}else cur=tryS}
  if(cur)lines.push(cur);probe.remove();const out=g.group();const lh=size*1.18;const n=Math.min(lines.length,opt.most||3);
  for(let i=0;i<n;i++)txt(out,lines[i],size,x,y+(i-(n-1)/2)*lh,opt);return out}
function title(s){if(!s)return;const g=stage.group();const y=TALL?H*.1:H*.11;
  const t=wrap(g,s.toUpperCase(),U*.042,W/2,y,W*.84,{cls:'lbl',most:2});
  const bb=t.bbox();const hl=g.rect(bb.width+U*.04,bb.height+U*.02).move(W/2-(bb.width+U*.04)/2,bb.y-U*.01).fill(ACC).back();
  hl.attr({transform:`scale(0,1)`});g.opacity(0);
  at(0.05,.45,p=>{g.opacity(Math.min(1,p*2));hl.attr({transform:`translate(${(W/2)*(1-p)},0) scale(${p},1)`})});
  if(ACC!=='#E8B400')t.find('text').forEach(e=>e.fill('#FFFFFF'))}
function underline(cx,y,w,start){const l=stage.line(cx-w/2,y,cx-w/2,y).stroke({color:ACC,width:U*.012,linecap:'round'});
  at(start,.5,p=>l.plot(cx-w/2,y,cx-w/2+w*p,y),ease.inout)}
function pop(el,cx,cy,start,d){el.opacity(0);at(start,d||.45,p=>{const s=.6+.4*p;el.opacity(Math.min(1,p*1.6));
  el.attr({transform:`translate(${cx*(1-s)},${cy*(1-s)}) scale(${s})`})},ease.back)}

const T=P.type;
if(T==='counter'||T==='progress'){
  const cy=TALL?H*.36:H*.44;const big=U*(TALL?.15:.17);
  const val=T==='progress'?P.value:P.to, from=T==='progress'?0:(P.from||0);const dec=decOf(val);
  const pre=T==='progress'?'':(P.prefix||''), suf=T==='progress'?'%':(P.suffix||'');
  const n=txt(stage,pre+fmt(val,dec)+suf,big,W/2,cy,{fill:INK});{const w=n.length();if(w>W*.86)n.font({size:big*W*.86/w})}
  at(.2,Math.min(1.6,DUR*.45),p=>n.text(pre+fmt(from+(val-from)*p,dec)+suf),ease.expo);
  pop(n,W/2,cy,.15,.5);
  if(T==='progress'){const bw=W*(TALL?.78:.6),bh=U*.05,x=W/2-bw/2,y=cy+big*.75;
    stage.rect(bw,bh).move(x,y).radius(bh/2).fill('none').stroke({color:INK,width:U*.005});
    const f=stage.rect(0,bh).move(x,y).radius(bh/2).fill(ACC);at(.2,Math.min(1.6,DUR*.45),p=>f.width(Math.max(.1,bw*val/100*p)),ease.expo)}
  else underline(W/2,cy+big*.62,Math.min(W*.6,big*3.2),.9);
  if(P.label){const l=wrap(stage,P.label,U*.045,W/2,cy+big*(T==='progress'?1.55:1.2),W*.8,{cls:'lbl',fill:SEC});l.opacity(0);
    at(1.0,.5,p=>l.opacity(p))}
}
if(T==='bars'){
  title(P.title);const vals=P.values;const n=vals.length;const top=Math.max(...vals);const dec=vals.some(v=>!Number.isInteger(v))?1:0;
  const base=TALL?H*.62:H*.8, maxh=TALL?H*.38:H*.5, area=W*(TALL?.8:.62), bw=Math.min(area/n*.6,U*.22), gap=area/n;
  vals.forEach((v,i)=>{const cx=W/2-area/2+gap*(i+.5);const h=maxh*v/top;const st=.35+i*.35;
    const isTop=v===top;const b=stage.rect(bw,0).move(cx-bw/2,base).fill(isTop?ACC:SEC);
    const lab=txt(stage,(P.prefix||'')+fmt(0,dec)+(P.suffix||''),U*.06,cx,base-U*.04,{});lab.opacity(0);
    at(st,.9,p=>{b.height(Math.max(.1,h*p)).move(cx-bw/2,base-h*p);lab.attr({y:base-h*p-U*.045}).opacity(Math.min(1,p*3))
      .text((P.prefix||'')+fmt(v*p,dec)+(P.suffix||''))},ease.expo);
    if(P.labels[i]){const l=wrap(stage,P.labels[i],U*.036,cx,base+U*.06,gap*.95,{cls:'lbl',fill:SEC,most:2});l.opacity(0);at(st+.2,.4,p=>l.opacity(p))}});
  stage.line(W/2-area/2,base,W/2+area/2,base).stroke({color:INK,width:U*.005});
}
if(T==='line'){
  const vals=P.values;const n=vals.length;const mx=Math.max(...vals);const lo=Math.min(...vals);const mn=Math.max(0,lo-(mx-lo)*1.2);
  const L=W*(TALL?.12:.16),R=W*(TALL?.88:.84),Tp=TALL?H*.22:H*.2,B=TALL?H*.58:H*.76;
  if(P.label)title(P.label);
  stage.line(L,B,R,B).stroke({color:INK,width:U*.005});
  const pts=vals.map((v,i)=>[L+(R-L)*i/(n-1),B-(B-Tp)*(v-mn)/(mx-mn||1)]);
  const path=stage.polyline(pts.map(p=>p.join(',')).join(' ')).fill('none').stroke({color:ACC,width:U*.012,linecap:'round',linejoin:'round'});
  const len=path.node.getTotalLength();path.attr({'stroke-dasharray':len,'stroke-dashoffset':len});
  const dd=Math.min(2.4,DUR*.6);at(.4,dd,p=>path.attr({'stroke-dashoffset':len*(1-p)}),ease.inout);
  pts.forEach((p,i)=>{const s=.4+dd*i/(n-1);const c=stage.circle(U*.03).center(p[0],p[1]).fill(i===n-1?ACC:INK);pop(c,p[0],p[1],s,.35);
    const v=txt(stage,(P.prefix||'')+fmt(vals[i],decOf(vals[i]))+(P.suffix||''),U*.04,p[0],p[1]-U*.05,{});v.opacity(0);at(s+.1,.3,q=>v.opacity(q));
    if(P.ticks[i]){const t=txt(stage,P.ticks[i],U*.034,p[0],B+U*.045,{cls:'lbl',fill:SEC});t.opacity(0);at(s,.3,q=>t.opacity(q))}});
}
if(T==='timeline'){
  title(P.title);const items=P.items;const n=items.length;const per=Math.min(.75,Math.max(.3,(DUR-1)/n));
  if(!TALL){const y=H*.55,L=W*.1,R=W*.9;const ln=stage.line(L,y,L,y).stroke({color:INK,width:U*.007,linecap:'round'});
    at(.2,per*n,p=>ln.plot(L,y,L+(R-L)*p,y),ease.inout);
    items.forEach((it,i)=>{const x=L+(R-L)*(i+.5)/n;const s=.2+per*(i+.5);const last=i===n-1;
      const c=stage.circle(U*.035).center(x,y).fill(last?ACC:INK);pop(c,x,y,s,.4);
      const up=i%2===0;const d=txt(stage,it[0],U*.05,x,y+(up?-1:1)*U*.09,{fill:last?ACC:INK});
      const l=wrap(stage,it[1],U*.034,x,y+(up?-1:1)*U*.17,(R-L)/n*.95,{cls:'lbl',fill:SEC,most:3});
      [d,l].forEach(e=>{e.opacity(0)});at(s,.45,p=>{d.opacity(p).attr({transform:`translate(0,${(up?-1:1)*U*.03*(1-p)})`});l.opacity(p)})})}
  else{const x=W*.2,T0=H*.2,B0=H*.6;const ln=stage.line(x,T0,x,T0).stroke({color:INK,width:U*.01,linecap:'round'});
    at(.2,per*n,p=>ln.plot(x,T0,x,T0+(B0-T0)*p),ease.inout);
    items.forEach((it,i)=>{const y=T0+(B0-T0)*(i+.5)/n;const s=.2+per*(i+.5);const last=i===n-1;
      const c=stage.circle(U*.05).center(x,y).fill(last?ACC:INK);pop(c,x,y,s,.4);
      const d=txt(stage,it[0],U*.06,x+U*.07,y-U*.035,{anchor:'start',fill:last?ACC:INK});
      const l=wrap(stage,it[1],U*.045,x+U*.07,y+U*.04,W*.68,{cls:'lbl',fill:SEC,anchor:'start',most:2});
      [d,l].forEach(e=>e.opacity(0));at(s,.45,p=>{d.opacity(p);l.opacity(p)})})}
}
if(T==='steps'){
  title(P.title);const st=P.steps;const n=st.length;const per=Math.min(.8,Math.max(.35,(DUR-1)/n));
  const boxes=[];
  if(!TALL){const cols=n<=4?n:Math.ceil(n/2),rows=Math.ceil(n/cols);const gw=W*.86/cols,bw=gw*.78,bh=U*.16;
    st.forEach((s,i)=>{const r=Math.floor(i/cols),c=i%cols;const cx=W*.07+gw*(c+.5);const cy=H*(rows===1?.55:(r===0?.42:.72));boxes.push([cx,cy,bw,bh])})}
  else{const bw=W*.76,bh=U*.17,T0=H*.2,B0=H*.6;st.forEach((s,i)=>{boxes.push([W/2,T0+(B0-T0)*(n===1?.5:i/(n-1)),bw,bh])})}
  st.forEach((s,i)=>{const [cx,cy,bw,bh]=boxes[i];const last=i===n-1;const g=stage.group();const t0=.3+per*i;
    g.rect(bw,bh).center(cx,cy).radius(U*.02).fill(last?ACC:'#FFFFFF').stroke({color:INK,width:U*.006});
    wrap(g,s,U*.042,cx,cy,bw*.88,{cls:'lbl',fill:last&&ACC!=='#E8B400'?'#FFFFFF':INK,most:2});pop(g,cx,cy,t0,.45);
    if(i>0){const [px,py,pw,ph]=boxes[i-1];let x1,y1,x2,y2;
      if(Math.abs(py-cy)<1){x1=px+pw/2+U*.01;y1=py;x2=cx-bw/2-U*.015;y2=cy}else if(TALL){x1=px;y1=py+ph/2+U*.01;x2=cx;y2=cy-bh/2-U*.015}
      else{x1=px;y1=py+ph/2+U*.01;x2=cx;y2=cy-bh/2-U*.015}
      const a=stage.line(x1,y1,x1,y1).stroke({color:ACC,width:U*.009,linecap:'round'});const ang=Math.atan2(y2-y1,x2-x1),hs=U*.025;
      const head=stage.polygon([[0,0],[-hs,-hs*.6],[-hs,hs*.6]].map(q=>q.join(',')).join(' ')).fill(ACC).opacity(0);
      at(t0-per*.45,per*.4,p=>{a.plot(x1,y1,x1+(x2-x1)*p,y1+(y2-y1)*p);head.opacity(p>.9?1:0)
        .attr({transform:`translate(${x1+(x2-x1)*p},${y1+(y2-y1)*p}) rotate(${ang*180/Math.PI})`})},ease.inout)}});
}
if(T==='pie'){
  const cx=W/2,cy=TALL?H*.36:H*.46,r=U*(TALL?.28:.27),w=r*.34;
  stage.circle(r*2).center(cx,cy).fill('none').stroke({color:'#D9D0BE',width:w});
  const arc=stage.path('').fill('none').stroke({color:ACC,width:w,linecap:'butt'});
  const num=txt(stage,'0%',r*.5,cx,cy,{});
  at(.3,Math.min(1.8,DUR*.5),p=>{const f=P.value/100*p;const a=f*2*Math.PI-1e-4;const x=cx+r*Math.sin(a),y=cy-r*Math.cos(a);
    arc.plot(f<=0?'':`M ${cx} ${cy-r} A ${r} ${r} 0 ${a>Math.PI?1:0} 1 ${x} ${y}`);num.text(fmt(P.value*p,decOf(P.value))+'%')},ease.inout);
  if(P.label){const l=wrap(stage,P.label,U*.045,cx,cy+r+U*.11,W*.8,{cls:'lbl',fill:SEC});l.opacity(0);at(1.2,.5,p=>l.opacity(p))}
}
if(T==='squares'){
  const vals=P.values;const top=Math.max(...vals.map(v=>v[1]));const n=vals.length;
  const side=Math.min(W*(TALL?.6:.34),H*(TALL?.34:.56));const sizes=vals.map(v=>Math.max(6,side*Math.sqrt(v[1]/top)));
  let total=sizes.reduce((a,b)=>a+b,0)+U*.08*(n-1);if(total>W*.9){const k=(W*.9-U*.08*(n-1))/(total-U*.08*(n-1));for(let i=0;i<n;i++)sizes[i]*=k;total=W*.9}let x=W/2-total/2;const base=TALL?H*.55:H*.74;
  vals.forEach((v,i)=>{const s=sizes[i];const big=v[1]===top;const r=stage.rect(s,s).move(x,base-s).fill(big?ACC:SEC).opacity(.92);
    const x0=x;r.attr({transform:`translate(${x0},${base}) scale(0) translate(${-x0},${-base})`});
    at(.3+i*.45,.8,p=>r.attr({transform:`translate(${x0},${base}) scale(${p}) translate(${-x0},${-base})`}),ease.back);
    const t=txt(stage,v[0],U*.05,x0+s/2,base-s-U*.045,{});t.opacity(0);at(.6+i*.45,.4,p=>t.opacity(p));
    if(P.labels[i]){const l=wrap(stage,P.labels[i],U*.034,x0+s/2,base+U*.06,Math.max(s,U*.3),{cls:'lbl',fill:SEC,most:2});l.opacity(0);at(.6+i*.45,.4,p=>l.opacity(p))}
    x+=s+U*.08});
}

if(T==='scene'){
  title(P.title);
  const TOP=TALL?H*.2:H*.22, BOT=TALL?H*.56:H*.72, MY=(TOP+BOT)/2, SZ=U*(TALL?.21:.18);
  const A=P.actors, act=P.action, n=A.length, END=Math.max(1.2,DUR-.3);
  function ico(nodes,size,opt){opt=opt||{};const g=stage.group();
    if(opt.sticker!==false){g.circle(size*1.22).center(0,0).fill(opt.bg||'#FFFFFF').stroke({color:INK,width:Math.max(2,size*.04)})}
    const ig=g.group();for(const nd of (nodes||[])){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    const k=size*.66/24;ig.attr({fill:'none',stroke:opt.ink||INK,'stroke-width':opt.sw||1.7,'stroke-linecap':'round',
      'stroke-linejoin':'round',transform:`translate(${-12*k},${-12*k}) scale(${k})`});return g}
  function put(g,x,y,s,r){g.attr({transform:`translate(${x},${y}) rotate(${r||0}) scale(${s===undefined?1:s})`})}
  function appear(g,x,y,start,s){s=s||1;put(g,x,y,s*.5);g.opacity(0);
    at(start,.45,p=>{g.opacity(Math.min(1,p*1.8));put(g,x,y,s*(.5+.5*p))},ease.back)}
  function label(s,x,y,start,size,maxw){if(!s)return null;const t=wrap(stage,String(s).toUpperCase(),size||U*.032,x,y,maxw||W*.26,{cls:'lbl',most:2});
    t.opacity(0);at(start||.4,.35,p=>t.opacity(p));return t}
  function arrow(x1,y1,x2,y2,start,dur){const a=stage.line(x1,y1,x1,y1).stroke({color:ACC==='#E8B400'?INK:ACC,width:U*.008,linecap:'round'});
    const ang=Math.atan2(y2-y1,x2-x1),hs=U*.022;const h=stage.polygon([[0,0],[-hs,-hs*.6],[-hs,hs*.6]].map(q=>q.join(',')).join(' ')).fill(ACC==='#E8B400'?INK:ACC).opacity(0);
    at(start,dur||.4,p=>{a.plot(x1,y1,x1+(x2-x1)*p,y1+(y2-y1)*p);h.opacity(p>.9?1:0).attr({transform:`translate(${x1+(x2-x1)*p},${y1+(y2-y1)*p}) rotate(${ang*180/Math.PI})`})},ease.inout)}
  function row(items,start,gapArrows){ // icons in a row (widescreen) or a column (Shorts), labels under/beside
    const m=items.length;const pos=[];
    for(let i=0;i<m;i++){if(TALL&&m>2){pos.push([W*.3,TOP+(BOT-TOP)*(m===1?.5:i/(m-1))])}else{pos.push([W*.5+(i-(m-1)/2)*Math.min(W*.24,W*.76/m),MY])}}
    items.forEach((a,i)=>{const [x,y]=pos[i];const g=ico(a.o,m===1?SZ*1.25:SZ,{bg:i===m-1&&m>1?ACC:'#FFFFFF'});appear(g,x,y,start+i*.45);
      if(TALL&&m>2)label(a.label,x+SZ*1.35,y,start+i*.45+.2,U*.034,W*.4);else label(a.label,x,y+SZ*(m===1?1.05:.95),start+i*.45+.2,U*.032,Math.min(W*.24,W*.76/m)*.95);
      if(gapArrows&&i>0){const [px,py]=pos[i-1];const r=SZ*.72;const d=Math.hypot(x-px,y-py)||1;
        arrow(px+(x-px)/d*r,py+(y-py)/d*r,x-(x-px)/d*r,y-(y-py)/d*r,start+i*.45-.25,.3)}});return pos}
  if(act==='move'){
    const x0=W*.2,x1=W*.8,y=MY+U*.03,pins=!!(P.from||P.to);
    if(pins){[[x0,P.from],[x1,P.to]].forEach(([x,l],i)=>{const pin=ico(P.pin,SZ*.6,{bg:i?ACC:'#FFFFFF'});appear(pin,x,y+SZ*.35,.15+i*.15);label(l,x,y+SZ*.95,.3+i*.15)})}
    else if(n>=2){const tg=ico(A[n-1].o,SZ,{bg:'#FFFFFF'});appear(tg,x1,y,.2);label(A[n-1].label,x1,y+SZ*.95,.35);label(A[0].label,x0,y+SZ*.95,.35)}
    const cyc=y-U*(TALL?.12:.17);const endX=pins?x1:x1-SZ*.9;
    const path=stage.path(`M ${x0} ${y} Q ${W/2} ${cyc} ${endX} ${y}`).fill('none').stroke({color:SEC,width:U*.005});
    const len=path.node.getTotalLength();path.attr({'stroke-dasharray':`${U*.018},${U*.014}`});
    const trail=stage.path(`M ${x0} ${y} Q ${W/2} ${cyc} ${endX} ${y}`).fill('none').stroke({color:'#00000000',width:0});
    const mask=stage.rect(0,H).move(0,0).fill('#fff');const clipped=stage.clip().add(mask);path.clipWith(clipped);
    const mover=ico(A[0].o,SZ*(pins?1:.8),{bg:ACC});let cargo=P.cargo?ico(P.cargo.o,SZ*.42):null;
    const t0=.55,t1=Math.min(END,t0+Math.max(1.4,DUR*.62));const turn=/plane|rocket|helicopter|send|paper/.test(A[0].icon);
    const at0=path.node.getPointAtLength(0);put(mover,at0.x,at0.y-SZ*.12,1);mover.opacity(0);at(.35,.25,p=>mover.opacity(p));
    if(cargo){put(cargo,at0.x+SZ*.48,at0.y+SZ*.25,1);cargo.opacity(0);at(.4,.25,p=>cargo.opacity(p))}
    tracks.push({start:t0,dur:t1-t0,e:ease.inout,fn:p=>{const L=len*p;const pt=path.node.getPointAtLength(L),q=path.node.getPointAtLength(Math.min(len,L+2));
      const ang=Math.atan2(q.y-pt.y,q.x-pt.x)*180/Math.PI;put(mover,pt.x,pt.y-SZ*.12,1,turn?ang:Math.sin(p*40)*2);
      if(cargo)put(cargo,pt.x+SZ*.48,pt.y+SZ*.25,1);mask.width(pt.x)}});
  }
  else if(act==='grow'||act==='shrink'){
    const x=W/2,y=MY,up=act==='grow',s0=up?.55:1.3,s1=up?1.3:.55;const g=ico(A[0].o,SZ,{bg:ACC});put(g,x,y,s0);g.opacity(0);
    at(.15,.3,p=>g.opacity(p));at(.5,Math.min(1.8,END-.6),p=>put(g,x,y,s0+(s1-s0)*p),ease.back);
    const col=up?'#2E7D32':'#C62828',ax=x+SZ*1.45,tip=y+(up?-1:1)*SZ*.75,tail=y-(up?-1:1)*SZ*.75;
    const ln=stage.line(ax,tail,ax,tail).stroke({color:col,width:U*.014,linecap:'round'});const hd=stage.polygon(`${ax-U*.03},${tip-(up?-1:1)*U*.035} ${ax+U*.03},${tip-(up?-1:1)*U*.035} ${ax},${tip+(up?-1:1)*U*.005}`).fill(col).opacity(0);
    at(.6,.6,p=>{ln.plot(ax,tail,ax,tail+(tip-tail)*p);hd.opacity(p>.9?1:0)},ease.inout);
    if(n>1){const g2=ico(A[1].o,SZ*.6);appear(g2,x-SZ*1.5,y,.3)}
    label(A[0].label,x,BOT-U*.01,.6);
  }
  else if(act==='multiply'){
    const cx=W/2,cy=MY,rx=TALL?W*.34:W*.3,ry=(BOT-TOP)*.42;const src=ico(A[0].o,SZ*.9,{bg:ACC});
    const kids=(n>1?A[1]:A[0]).o;const N=TALL?10:14;
    for(let i=0;i<N;i++){const a=2*Math.PI*i/N-Math.PI/2;const x=cx+Math.cos(a)*rx,y=cy+Math.sin(a)*ry;const st=.7+i*.07;
      const ln=stage.line(cx,cy,cx,cy).stroke({color:SEC,width:U*.0035}).opacity(.6);const c=ico(kids,SZ*.4);put(c,cx,cy,.3);c.opacity(0);
      at(st,.55,p=>{c.opacity(Math.min(1,p*2));put(c,cx+(x-cx)*p,cy+(y-cy)*p,.35+.65*p);ln.plot(cx,cy,cx+(x-cx)*p,cy+(y-cy)*p)})}
    src.front();appear(src,cx,cy,.15);
    if(n>1)label(A[1].label,cx,BOT+U*.005,1.6,U*.03,W*.5);
  }
  else if(act==='converge'){
    const tg=A[n-1],att=n>1?A[0].o:P.mob;const cx=W/2,cy=MY,rx=TALL?W*.4:W*.36,ry=(BOT-TOP)*.5;
    const t=ico(tg.o,SZ,{bg:'#FFFFFF'});appear(t,cx,cy,.15);label(tg.label,cx,BOT+U*.02,.45);
    const N=TALL?8:12;for(let i=0;i<N;i++){const a=2*Math.PI*i/N;const sx=cx+Math.cos(a)*rx*1.6,sy=cy+Math.sin(a)*ry*1.6,
      ex=cx+Math.cos(a)*rx*.6,ey=cy+Math.sin(a)*ry*.7;const c=ico(att,SZ*.42,{bg:'#F3D7D3'});put(c,sx,sy,1);c.opacity(0);
      at(.6+i*.08,.6,p=>{c.opacity(Math.min(1,p*2));put(c,sx+(ex-sx)*p,sy+(ey-sy)*p,1)},ease.out)}
    t.front();tracks.push({start:1.5,dur:Math.max(.6,END-1.5),e:x=>x,fn:p=>put(t,cx+Math.sin(p*80)*U*.006,cy,1)});
  }
  else if(act==='stack'){
    const x=W/2,N=6,base=BOT-SZ*.35;for(let i=0;i<N;i++){const c=ico(A[0].o,SZ*.7,{bg:i%2?'#FFFFFF':ACC});const y=base-i*SZ*.52;
      put(c,x,TOP-SZ,1);c.opacity(0);at(.3+i*.22,.4,p=>{c.opacity(Math.min(1,p*3));put(c,x,(TOP-SZ)+(y-(TOP-SZ))*p,1)},ease.back)}
    label(A[0].label,x+SZ*1.5,MY,.8,U*.034,W*.3);
  }
  else if(act==='split'){
    const cx=W/2,cy=MY;const g1=ico(A[0].o,SZ,{bg:ACC}),g2=ico(A[0].o,SZ,{bg:'#FFFFFF'});[g1,g2].forEach(g=>{put(g,cx,cy,1);g.opacity(0);at(.15,.3,p=>g.opacity(p))});
    at(.7,.8,p=>{put(g1,cx-W*.2*p,cy,1-.15*p);put(g2,cx+W*.2*p,cy,1-.15*p)},ease.inout);
    if(n>2){label(A[1].label,cx-W*.2,cy+SZ*.95,1.3);label(A[2].label,cx+W*.2,cy+SZ*.95,1.3)}else label(A[0].label,cx,BOT,1.3);
  }
  else if(act==='shake'){
    const cx=W/2,cy=MY;const g=ico(A[0].o,SZ*1.2,{bg:ACC});appear(g,cx,cy,.15);
    for(let k=0;k<3;k++){const c=stage.circle(SZ*1.2).center(cx,cy).fill('none').stroke({color:INK,width:U*.006}).opacity(0);
      at(.6+k*.4,.9,p=>{c.radius(SZ*.62*(1+1.2*p)).center(cx,cy);c.opacity(.8*(1-p))})}
    g.front();tracks.push({start:.6,dur:Math.max(.8,END-.6),e:x=>x,fn:p=>put(g,cx+Math.sin(p*120)*U*.007,cy,1,Math.sin(p*90)*5)});
    label(A[0].label,cx,BOT,.5);
  }
  else if(act==='block'){
    const pos=row(A,.15,n>1);const [bx,by]=pos[pos.length-1];const b=ico(P.ban,SZ*(n===1?1.9:1.5),{sticker:false,ink:'#C62828',sw:2.6});
    put(b,bx,by,2.2);b.opacity(0);at(1.1,.35,p=>{b.opacity(Math.min(1,p*2));put(b,bx,by,2.2-1.2*p)},ease.back);
  }
  else if(act==='compare'){
    const a=A[0],b=A[1]||A[0];const xs=[W*.3,W*.7];[a,b].forEach((it,i)=>{const g=ico(it.o,SZ*1.1,{bg:i?ACC:'#FFFFFF'});appear(g,xs[i],MY,.2+i*.3);label(it.label,xs[i],MY+SZ*1.0,.4+i*.3)});
    const v=txt(stage,'VS',U*.08,W/2,MY,{fill:INK});v.opacity(0);at(.7,.3,p=>v.opacity(p));
  }
  else if(act==='cycle'){
    const items=n>=2?A:[A[0],A[0],A[0]];const m=items.length;const cx=W/2,cy=MY,rx=TALL?W*.3:W*.2,ry=(BOT-TOP)*.38;const pts=[];
    items.forEach((it,i)=>{const a=-Math.PI/2+2*Math.PI*i/m;const x=cx+Math.cos(a)*rx,y=cy+Math.sin(a)*ry;pts.push([x,y]);
      const g=ico(it.o,SZ*.8,{bg:i===0?ACC:'#FFFFFF'});appear(g,x,y,.2+i*.35);label(it.label,x,y+SZ*.78,.35+i*.35,U*.028,W*.2)});
    pts.forEach((p0,i)=>{const p1=pts[(i+1)%m];const d=Math.hypot(p1[0]-p0[0],p1[1]-p0[1])||1,r=SZ*.6;
      arrow(p0[0]+(p1[0]-p0[0])/d*r,p0[1]+(p1[1]-p0[1])/d*r,p1[0]-(p1[0]-p0[0])/d*r,p1[1]-(p1[1]-p0[1])/d*r,.5+i*.35+.3,.35)});
  }
  else{ // connect / show
    const pos=row(A,.15,act==='connect');
    if(n===1){const g=stage.find('g').last();}
  }
}
draw.rect(W,H).fill(grad).attr({'pointer-events':'none'});
window.frame=function(t){
  const z=1+.035*Math.min(1,t/DUR);stage.attr({transform:`translate(${W/2*(1-z)},${H/2*(1-z)}) scale(${z})`});
  for(const k of tracks){const p=Math.max(0,Math.min(1,(t-k.start)/k.dur));k.fn(k.e(p))}
};
window.frame(0);window.READY=true;
</script></body></html>"""


def _font_face() -> str:
    for p in _BOLD_FONTS:
        if Path(p).is_file():
            return f"@font-face{{font-family:'CFBold';src:url('file://{p}')}}"
    return ""


def _launch(p):
    args = ["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"]
    try:
        return p.chromium.launch(args=args)
    except Exception:  # noqa: BLE001 - the bundled browser is missing: try a known one
        for exe in [os.environ.get("CF_CHROMIUM", "")] + sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")):
            if exe and Path(exe).is_file():
                return p.chromium.launch(executable_path=exe, args=args)
        raise


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           fps: int | None = None) -> Path:
    """Draws the line as a smooth vector animation into `out` (H.264, yuv420p)."""
    if not enabled():
        raise MediaError("motion engine off (no Chromium/Playwright)")
    plan = plan_for(kind, spec)
    if plan is None:
        raise MediaError(f"motion: nothing to draw from {spec!r}")
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(1.5, float(seconds))
    th = THEMES.get(theme, THEMES["editorial"])
    page = (_PAGE.replace("%SVGJS%", VENDOR.read_text(encoding="utf-8")).replace("%FONTFACE%", _font_face())
            .replace("%BG%", th[0]).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{seconds:.3f}")
            .replace("%THEME%", json.dumps(list(th))))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"motion_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    frames = max(1, int(round(seconds * fps)))
    from playwright.sync_api import sync_playwright
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps),
                            "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                            "-pix_fmt", "yuv420p", "-r", str(fps), "-movflags", "+faststart", str(out)],
                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        with sync_playwright() as p:
            browser = _launch(p)
            try:
                pg = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                errors: list[str] = []
                pg.on("pageerror", lambda e: errors.append(str(e)))
                pg.goto(html.as_uri())
                pg.wait_for_function("window.READY === true", timeout=15000)
                if errors:
                    raise MediaError(f"motion page error: {errors[0][:200]}")
                pg.evaluate("document.fonts.ready")
                for i in range(frames):
                    pg.evaluate(f"window.frame({i / fps:.4f})")
                    enc.stdin.write(pg.screenshot(type="jpeg", quality=92))
            finally:
                browser.close()
        enc.stdin.close()
        if enc.wait(timeout=600) != 0:
            raise MediaError(f"motion encode failed: {enc.stderr.read().decode()[-300:]}")
    except MediaError:
        enc.kill()
        raise
    except Exception as e:  # noqa: BLE001 - any browser trouble: the pipeline falls back to the FFmpeg card
        enc.kill()
        raise MediaError(f"motion render failed: {e}") from None
    if not out.is_file() or out.stat().st_size < 1000:
        raise MediaError("motion: empty output")
    return out
