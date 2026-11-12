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

KINDS = ("chart", "timeline", "steps", "pie", "squares", "animate", "clock", "calendar", "sign", "social", "comments",
         "trending", "stamp", "statement", "board")
VENDOR = Path(__file__).parent / "vendor" / "svg.min.js"
# Colour per scene (Vox rhythm): soft paper tints that change as the story moves on; "editorial~2" picks tint 2
PALETTE = ("#F2EBDD", "#E3ECF2", "#F6E1DA", "#E4EDE1", "#F7EFD2")


def split_theme(theme: str) -> tuple[str, str | None]:
    """"editorial~3" -> ("editorial", "#E4EDE1"); a plain theme keeps its own paper."""
    base, _, var = (theme or "editorial").split("@")[0].partition("~")      # "@accent" is for the Vox scenes
    try:
        return base, PALETTE[int(var) % len(PALETTE)] if var != "" else None
    except ValueError:
        return base, None


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
    head, _, tail = spec.partition("|")
    head, tail = head.strip(), tail.strip()
    parts = lambda s: [x.strip() for x in re.split(r"·|•|;", s) if x.strip()]      # noqa: E731
    if kind == "clock":
        m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", head, re.I)
        if not m:
            return None
        h, mi = int(m.group(1)) % 12, int(m.group(2) or 0)
        if (m.group(3) or "").lower() == "pm":
            h += 12
        return {"type": "clock", "h": h, "m": mi, "show": head.upper(), "label": tail}
    if kind == "calendar":
        my = re.fullmatch(r"([A-Za-z]{3,9})\s+(\d{4})", head.strip())
        if my:                                  # "SEP 2018": the month's page shows the year (no invented day)
            return {"type": "calendar", "day": None, "month": my.group(1)[:3].upper(), "year": my.group(2), "label": tail}
        m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})(?:\s+(\d{4}))?", head) or \
            re.search(r"([A-Za-z]{3,9})\s+(\d{1,2})(?:,?\s+(\d{4}))?", head)
        if not m:
            return None
        a, b, y = m.group(1), m.group(2), m.group(3) or ""
        day, mon = (a, b) if a.isdigit() else (b, a)
        return {"type": "calendar", "day": int(day), "month": mon[:3].upper(), "year": y, "label": tail}
    if kind == "sign":
        style = next((w for w in ("banner", "billboard", "board", "placard", "signpost") if w in tail.lower()), "placard")
        return {"type": "sign", "text": head, "style": style, "label": re.sub(r"(?i)\b(banner|billboard|board|placard|signpost)\b", "", tail).strip(" ,·")}
    if kind == "social":
        bits = [x.strip() for x in spec.split("|")]
        stats = parts(bits[2]) if len(bits) > 2 else []
        return {"type": "social", "who": bits[0], "text": bits[1] if len(bits) > 1 else "", "stats": stats[:3]}
    if kind == "comments":
        return {"type": "comments", "who": head if tail else "", "items": parts(tail or head)[:8]}
    if kind == "trending":
        others = parts(tail)[:4]
        return {"type": "trending", "tag": head, "others": others}
    if kind == "stamp":
        return {"type": "stamp", "text": head.upper(), "on": tail}
    if kind == "board":
        items = parts(head)[:7]
        if not items:
            return None
        from .scene_anim import find_icon, icon_nodes
        def ic(t):
            ws = [w for w in re.findall(r"[A-Za-z]+", t.lower()) if len(w) > 2]
            name = next((find_icon(w) for w in ws if find_icon(w)), None)
            return icon_nodes(name) if name else []
        return {"type": "board", "items": [{"t": t, "o": ic(t)} for t in items], "title": tail, "pin": icon_nodes("pin")}
    if kind == "statement":
        # "*ship*." - the stars mark the word; punctuation after the closing star stays, the stars never show
        # a starred phrase ("*$2.8 billion*") stays on one strip; a no-break space also keeps words together
        toks = re.findall(r"\*[^*]+\*[^ \t\n*]*|[^ \t\n]+", spec)
        words = [{"w": w.replace("*", ""), "hi": "*" in w} for w in toks if w.replace("*", "")]
        return {"type": "statement", "words": words[:16]} if words else None
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
text{font-family:'Archivo','CFBold','DejaVu Sans','FreeSans','Noto Sans Devanagari',sans-serif}
.lbl{font-family:'Inter','DejaVu Sans','FreeSans','Noto Sans Devanagari',sans-serif;font-weight:800;letter-spacing:.04em}
body{background-image:url('%PAPERIMG%');background-size:100% 100%}
#grain{position:fixed;left:0;top:0;width:100%;height:100%;mix-blend-mode:multiply;opacity:.5;z-index:10;pointer-events:none}
</style><script>%SVGJS%</script><script>%ILLU%</script></head><body><img id="grain" src="%GRAINIMG%"><script>
(async()=>{try{await Promise.all(Array.from(document.fonts).map(f=>f.load()))}catch(e){}   // measure text in the real fonts
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
    const photo=!!(nodes&&nodes[0]&&(nodes[0][0]==='image'||nodes[0][0]==='illu'||nodes[0][0]==='logo'));   // a photo or drawing, not the line icon
    if(nodes&&nodes[0]&&nodes[0][0]==='logo'){const m=nodes[0][1],sz=size*1.15,k=sz*.6/24;
      g.rect(sz,sz).move(-sz/2,-sz/2).radius(sz*.22).fill(m.hex).stroke({color:'#FFFFFF',width:sz*.04});
      g.path(m.d).fill('#FFFFFF').attr({transform:`translate(${-12*k},${-12*k}) scale(${k})`});
      g.attr({style:'filter:drop-shadow(0 2px 3px rgba(0,0,0,.3))'});return g}
    if(nodes&&nodes[0]&&nodes[0][0]==='illu'&&window.ILLU&&ILLU[nodes[0][1]]){
      const [bw,bh,fn]=ILLU[nodes[0][1]];const k=size*1.5/Math.max(bw,bh);const ig2=g.group();fn(ig2,ACC);
      ig2.attr({transform:`translate(${-bw*k/2},${-bh*k/2}) scale(${k})`,style:'filter:drop-shadow(0 2px 3px rgba(0,0,0,.3))'});return g}
    if(opt.sticker!==false&&!photo){g.circle(size*1.22).center(0,0).fill(opt.bg||'#FFFFFF').stroke({color:INK,width:Math.max(2,size*.04)})}
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

if(['clock','calendar','sign','social','comments','trending','stamp'].includes(T)){
  const TOP=TALL?H*.18:H*.16, BOT=TALL?H*.57:H*.73, MY=(TOP+BOT)/2;
  const card=(x,y,w,h,r,fill)=>{const g=stage.group();g.rect(w,h).move(x+U*.012,y+U*.016).radius(r).fill('#000').opacity(.18);
    g.rect(w,h).move(x,y).radius(r).fill(fill||'#FFFFFF').stroke({color:INK,width:U*.004});return g};
  const lbl=(s,y,st)=>{if(!s)return;const t=wrap(stage,String(s).toUpperCase(),U*.036,W/2,y,W*.8,{cls:'lbl',most:2});t.opacity(0);at(st||.6,.4,p=>t.opacity(p))};
  if(T==='clock'){
    const R=(BOT-TOP)*.36,cx=W/2,cy=MY-R*.12;const f=stage.group();f.circle(R*2).center(cx,cy).fill('#FFFFFF').stroke({color:INK,width:U*.012});
    for(let i=0;i<12;i++){const a=i*Math.PI/6;f.line(cx+Math.sin(a)*R*.82,cy-Math.cos(a)*R*.82,cx+Math.sin(a)*R*(i%3?0.9:0.76),cy-Math.cos(a)*R*(i%3?0.9:0.76)).stroke({color:INK,width:U*(i%3?.005:.01),linecap:'round'})}
    const hh=stage.line(cx,cy,cx,cy-R*.5).stroke({color:INK,width:U*.016,linecap:'round'}),mm=stage.line(cx,cy,cx,cy-R*.75).stroke({color:ACC==='#E8B400'?'#C8102E':ACC,width:U*.01,linecap:'round'});
    stage.circle(U*.03).center(cx,cy).fill(INK);pop(f,cx,cy,.05,.4);
    const tm=P.h*60+P.m,startM=tm-180;
    at(.4,Math.min(2,DUR*.55),p=>{const cur=startM+180*p;const ha=(cur/60%12)*Math.PI/6,ma=(cur%60)*Math.PI/30;
      hh.plot(cx,cy,cx+Math.sin(ha)*R*.5,cy-Math.cos(ha)*R*.5);mm.plot(cx,cy,cx+Math.sin(ma)*R*.75,cy-Math.cos(ma)*R*.75)},ease.inout);
    const d=txt(stage,P.show,U*.06,cx,cy+R*1.22,{});d.opacity(0);at(1.6,.4,p=>d.opacity(p));lbl(P.label,cy+R*1.22+U*.08,1.8);
  }
  if(T==='calendar'){
    const w=Math.min(W*.3,(BOT-TOP)*.75),h=w*1.05,x=W/2-w/2,y=MY-h/2-U*.02;
    const pages=4;for(let i=pages;i>=0;i--){const g=card(x,y,w,h,U*.014);g.rect(w,h*.26).move(x,y).radius(U*.014).fill(ACC==='#E8B400'?'#C8102E':ACC);
      const noDay=P.day==null;txt(g,noDay?P.month:P.month+(P.year?' '+P.year:''),h*.11,W/2,y+h*.13,{fill:'#FFFFFF'});
      const day=noDay?P.year:(i===0?P.day:Math.max(1,P.day-i));
      txt(g,String(day),noDay?h*.3:h*.45,W/2,y+h*.62,{});
      if(i>0){const st=.3+(pages-i)*.32;at(st,.3,p=>g.attr({transform:`translate(0,${-h*1.4*p}) rotate(${-25*p},${x},${y})`}).opacity(1-p),ease.inout)}}
    for(let k=0;k<5;k++)stage.circle(U*.018).center(x+w*(.15+k*.175),y).fill(INK);
    lbl(P.label,y+h+U*.06,1.7);
  }
  if(T==='sign'){
    const tall=P.style==='placard'||P.style==='signpost';const w=P.style==='banner'?W*.7:P.style==='billboard'?W*.6:W*.42,h=P.style==='banner'?U*.18:U*.26;
    const x=W/2-w/2,y=MY-h/2-(tall?U*.08:0);const g=stage.group();
    if(tall)g.rect(U*.02,(BOT-y)*.9).move(W/2-U*.01,y+h-U*.01).fill('#8B5E3C');
    if(P.style==='billboard'){g.rect(U*.02,BOT-y-h).move(x+w*.2,y+h).fill('#555');g.rect(U*.02,BOT-y-h).move(x+w*.8-U*.02,y+h).fill('#555')}
    g.rect(w,h).move(x+U*.01,y+U*.014).fill('#000').opacity(.18);g.rect(w,h).move(x,y).fill(P.style==='banner'?ACC:'#FFFFFF').stroke({color:INK,width:U*.008});
    const t=wrap(g,P.text.toUpperCase(),Math.min(h*.36,U*.075),W/2,y+h/2,w*.9,{most:2});
    g.attr({transform:`translate(0,${H})`});at(.1,.55,p=>g.attr({transform:`translate(0,${H*(1-p)})`}),ease.back);
    tracks.push({start:.8,dur:Math.max(1,DUR-.8),e:q=>q,fn:p=>g.attr({transform:`rotate(${Math.sin(p*10)*1.6},${W/2},${BOT})`})});
    lbl(P.label,BOT+U*.02,1.0);
  }
  if(T==='social'||T==='stamp'){
    const w=Math.min(W*.6,U*1.05),h=(BOT-TOP)*.8,x=W/2-w/2,y=MY-h/2;const g=card(x,y,w,h,U*.02);
    g.circle(U*.07).center(x+U*.07,y+U*.07).fill('#D9D0BE');
    const who=T==='social'?P.who:'Account';txt(g,who,U*.032,x+U*.12,y+U*.07,{anchor:'start'});
    const body=T==='social'?P.text:(P.on||'Viral post');wrap(g,body,U*.04,W/2,y+h*(T==='social'?.45:.32),w*.86,{most:3,cls:'lbl'});
    pop(g,W/2,MY,.1,.45);
    if(T==='social'){const st=P.stats.length?P.stats:['12K likes','3K shares'];st.forEach((s,i)=>{const m=String(s).match(/([\d.,]+)\s*([KkMmLl]?)\s*(.*)/);
      const x0=x+w*(i+.5)/st.length,y0=y+h*.84;const t=txt(stage,'0',U*.03,x0,y0,{});
      if(m){const v=parseFloat(m[1].replace(/,/g,''));at(.7+i*.2,1.2,p=>t.text((v*p).toFixed(v<10&&m[2]?1:0)+m[2].toUpperCase()+' '+m[3]),ease.expo)}else t.text(s)})}
    else{const s=stage.group();const sw=w*.8,sh=U*.12,sy=y+h*.66;s.rect(sw,sh).move(W/2-sw/2,sy-sh/2).fill('#FFFFFF').opacity(.92).stroke({color:'#C8102E',width:U*.012});
      wrap(s,P.text,Math.min(sh*.5,U*.06),W/2,sy,sw*.92,{fill:'#C8102E',most:1});
      s.opacity(0);at(.9,.3,p=>{s.opacity(Math.min(1,p*2));s.attr({transform:`translate(${W/2},${sy}) rotate(-8) scale(${2.2-1.2*p}) translate(${-W/2},${-sy})`})},ease.back)}
  }
  if(T==='comments'){
    const w=Math.min(W*.62,U*1.1),x=W/2-w/2;if(P.who){const t=txt(stage,P.who,U*.036,W/2,TOP,{});}
    const rowH=Math.min(U*.1,(BOT-TOP-U*.05)/Math.max(4,P.items.length));
    P.items.forEach((c,i)=>{const y=TOP+U*.05+i*rowH;const g=card(x,y,w,rowH*.86,U*.012);g.circle(rowH*.5).center(x+rowH*.45,y+rowH*.43).fill('#F3D7D3');
      txt(g,c,Math.min(rowH*.42,U*.04),x+rowH*.85,y+rowH*.43,{anchor:'start',cls:'lbl'});g.opacity(0);
      at(.2+i*.28,.3,p=>{g.opacity(p);g.attr({transform:`translate(${(1-p)*W*.05},0)`})},ease.out)});
  }
  if(T==='trending'){
    const list=[...P.others];const n=list.length+1;const rowH=Math.min(U*.11,(BOT-TOP)/n);const w=Math.min(W*.6,U*1.0),x=W/2-w/2;
    txt(stage,'TRENDING',U*.036,W/2,TOP-U*.02,{fill:SEC});
    const rows=[];list.concat([P.tag]).forEach((t,i)=>{const g=stage.group();const me=i===n-1;g.rect(w,rowH*.84).move(x,0).radius(U*.01).fill(me?ACC:'#FFFFFF').stroke({color:INK,width:U*.004});
      const num=txt(g,String(i+1),rowH*.4,x+rowH*.45,rowH*.42,{});txt(g,t,rowH*.4,x+rowH*.9,rowH*.42,{anchor:'start'});rows.push([g,num])});
    const place=(order)=>order.forEach((ri,k)=>{});
    rows.forEach(([g,num],i)=>{const y0=TOP+U*.03+i*rowH;g.attr({transform:`translate(0,${y0})`});
      if(i===n-1){at(1.0,1.0,p=>{const y=y0+(TOP+U*.03-y0)*p;g.attr({transform:`translate(0,${y})`});num.text(String(Math.max(1,Math.round(n-(n-1)*p))))},ease.inout)}
      else{at(1.0,1.0,p=>{g.attr({transform:`translate(0,${y0+rowH*p})`});num.text(String(i+1+(p>.5?1:0)))},ease.inout)}});
    rows[n-1][0].front();
  }
}

if(T==='statement'){
  // cut-out paper headline: each word on its own paper strip, slightly tilted, popping in as it is said
  const TOP=TALL?H*.16:H*.14, BOT=TALL?H*.57:H*.74, maxw=W*.84;const ws=P.words;const n=ws.length;
  let size=U*(TALL?.1:.092);const pad=()=>size*.28,gap=()=>size*.22,lh=()=>size*1.5;
  const probe=stage.text('').font({size:size,weight:'bold'});
  function layout(){const rows=[[]];let w=0;for(const it of ws){probe.font({size:size});probe.text(it.w.toUpperCase());const tw=probe.length()+pad()*2;
      if(rows[rows.length-1].length&&w+tw>maxw){rows.push([]);w=0}rows[rows.length-1].push([it,tw]);w+=tw+gap()}return rows}
  let rows=layout();while((rows.length*lh()>BOT-TOP||rows.some(r=>r.reduce((a,b)=>a+b[1],0)>maxw))&&size>U*.04){size*=.9;rows=layout()}
  probe.remove();const y0=(TOP+BOT)/2-(rows.length-1)*lh()/2;let k=0;const per=Math.min(.32,Math.max(.12,(DUR*.5)/n));
  rows.forEach((r,ri)=>{const tot=r.reduce((a,b)=>a+b[1],0)+gap()*(r.length-1);let x=W/2-tot/2;const y=y0+ri*lh();
    r.forEach(([it,tw])=>{const g=stage.group();const h=size*1.25,rot=((k*37)%7-3)*.9;
      g.rect(tw,h).move(-tw/2+size*.06,-h/2+size*.09).fill('#000').opacity(.18);
      g.rect(tw,h).move(-tw/2,-h/2).fill(it.hi?ACC:'#FFFFFF').stroke({color:INK,width:Math.max(1.5,size*.02)});
      txt(g,it.w.toUpperCase(),size,0,size*.04,{fill:INK});const cx=x+tw/2;g.opacity(0);
      const st=.15+k*per;at(st,.28,p=>{g.opacity(Math.min(1,p*2));const s=1.25-.25*p;g.attr({transform:`translate(${cx},${y}) rotate(${rot}) scale(${s})`})},ease.back);
      g.attr({transform:`translate(${cx},${y}) rotate(${rot})`});x+=tw+gap();k++})});
}

if(T==='board'){
  // investigation board: cork, pinned paper notes, red string from the centre note to each of the others
  title(P.title);const TOP=TALL?H*.2:H*.2, BOT=TALL?H*.57:H*.74, MY=(TOP+BOT)/2;
  const bw=TALL?W*.92:W*.86,bh=BOT-TOP+U*.04;stage.rect(bw,bh).move(W/2-bw/2,TOP-U*.02).radius(U*.01).fill('#C9A16B').stroke({color:'#8B6A3E',width:U*.012});
  for(let i=0;i<220;i++){const x=W/2-bw/2+((i*97)%1000)/1000*bw,y=TOP-U*.02+((i*61)%1000)/1000*bh;stage.circle(U*.004).center(x,y).fill('#8B6A3E').opacity(.35)}
  const it=P.items,n=it.length;const cx=W/2,cy=MY;const rx=bw*.36,ry=bh*.34;const nw=TALL?W*.3:W*.17,nh=U*.12;
  const pos=it.map((_,i)=>i===0?[cx,cy]:[cx+Math.cos(-Math.PI/2+2*Math.PI*(i-1)/(n-1))*rx,cy+Math.sin(-Math.PI/2+2*Math.PI*(i-1)/(n-1))*ry]);
  const strings=[];const pinY=(i)=>pos[i][1]-(i===0?nh*1.3:nh)/2+U*.012;
  pos.forEach((p,i)=>{if(i===0)return;const l=stage.line(cx,pinY(0),cx,pinY(0)).stroke({color:'#C8102E',width:U*.005,linecap:'round'});strings.push([l,[p[0],pinY(i)],i])});
  let centre=null;it.forEach((t,i)=>{const [x,y]=pos[i];const g=stage.group();if(i===0)centre=g;const w=i===0?nw*1.25:nw,h=i===0?nh*1.3:nh,rot=((i*53)%9-4)*.8;
    g.rect(w,h).move(-w/2+U*.006,-h/2+U*.009).fill('#000').opacity(.2);g.rect(w,h).move(-w/2,-h/2).fill(i===0?ACC:'#FFFDF6').stroke({color:INK,width:U*.003});
    if(t.o&&t.o.length){const ig=g.group();for(const nd of t.o){try{ig.element(nd[0]).attr(nd[1])}catch(e){}};const k=h*.42/24;
      ig.attr({fill:'none',stroke:INK,'stroke-width':1.8,transform:`translate(${-w/2+h*.12},${-12*k}) scale(${k})`});
      wrap(g,t.t.toUpperCase(),Math.min(h*.24,U*.03),h*.24,0,w-h*.62,{cls:'lbl',most:2})}
    else wrap(g,t.t.toUpperCase(),Math.min(h*.24,U*.03),0,0,w*.9,{cls:'lbl',most:2});
    g.circle(U*.022).center(0,-h/2+U*.012).fill('#C8102E').stroke({color:'#7A0A1C',width:2});
    g.opacity(0);const st=i===0?.2:.6+i*.35;at(st,.35,p=>{g.opacity(Math.min(1,p*2));g.attr({transform:`translate(${x},${y}) rotate(${rot}) scale(${1.15-.15*p})`})},ease.back);
    g.attr({transform:`translate(${x},${y}) rotate(${rot})`})});
  const sy=pinY(0);strings.forEach(([l,p,i])=>{const st=.45+i*.35;at(st,.4,q=>l.plot(cx,sy,cx+(p[0]-cx)*q,sy+(p[1]-sy)*q),ease.inout);l.front()});if(centre)centre.front();
  stage.find('g').forEach(g=>{});
}
draw.rect(W,H).fill(grad).attr({'pointer-events':'none'});
window.frame=function(t){
  const z=1+.035*Math.min(1,t/DUR);stage.attr({transform:`translate(${W/2*(1-z)},${H/2*(1-z)}) scale(${z})`});
  for(const k of tracks){const p=Math.max(0,Math.min(1,(t-k.start)/k.dur));k.fn(k.e(p))}
};
window.frame(0);window.READY=true;
})();
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
    if kind == "animate":
        _photos(plan)
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(1.5, float(seconds))
    theme, tint = split_theme(theme)
    th = THEMES.get(theme, THEMES["editorial"])
    if tint and not th[4]:
        th = (tint,) + tuple(th[1:])
    from . import vox
    paper_img, grain_img = vox.paper(th[0], width, height, work)
    page = (_PAGE.replace("%SVGJS%", VENDOR.read_text(encoding="utf-8"))
            .replace("%FONTFACE%", _font_face() + "\n" + vox._font_css())
            .replace("%PAPERIMG%", paper_img.as_uri()).replace("%GRAINIMG%", grain_img.as_uri())
            .replace("%ILLU%", (VENDOR.parent / "illustrations.js").read_text(encoding="utf-8"))
            .replace("%BG%", th[0]).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{seconds:.3f}")
            .replace("%THEME%", json.dumps(list(th))))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"motion_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    return capture(html, width, height, seconds, fps, out)


def _photos(plan: dict) -> None:
    """Animated scenes use the real cut-out photo of an object when the library has (or can fetch) one: the
    photo replaces the line icon, drawn bigger, with a soft shadow."""
    from . import cutouts
    model = os.environ.get("CF_CUTOUT_MODEL")
    from .vox import logo_key, logos
    for a in list(plan.get("actors") or []) + ([plan["cargo"]] if isinstance(plan.get("cargo"), dict) else []):
        k = logo_key(str(a.get("name", "")))
        if k:                                  # a platform the line names: its own app tile
            a["o"] = [["logo", logos()[k]]]
            continue
        try:
            c = cutouts.get(str(a.get("name", "")), model=Path(model) if model else None)
        except Exception:  # noqa: BLE001 - no photo: the icon stays
            c = None
        if c is None:
            from .vox import illustration
            drawn = illustration(str(a.get("name", "")))
            if drawn:
                a["o"] = [["illu", drawn]]     # no photo: the drawn illustration, not the thin line icon
            continue
        from PIL import Image
        with Image.open(c.path) as im:
            w, h = im.size
        hh = 50.0                       # in the icon's 24-unit box: about twice the icon's size
        ww = hh * w / h
        if ww > 70:
            ww, hh = 70.0, 70.0 * h / w
        a["o"] = [["image", {"href": c.path.as_uri(), "x": 12 - ww / 2, "y": 12 - hh / 2, "width": ww, "height": hh,
                             "style": "filter:drop-shadow(0 0.6px 0.9px rgba(0,0,0,.35))"}]]
        if c.credit:
            plan.setdefault("credits", []).append(c.credit)


def capture(html: Path, width: int, height: int, seconds: float, fps: int, out: Path) -> Path:
    """Plays an animation page (window.frame(t), window.READY) in headless Chromium and encodes it (H.264)."""
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
                pg.wait_for_function("window.READY === true", timeout=30000)
                if errors:
                    raise MediaError(f"motion page error: {errors[0][:200]}")
                pg.evaluate("document.fonts.ready")
                if pg.evaluate("document.querySelectorAll('image').length"):
                    pg.wait_for_timeout(400)          # cut-out photos: let them decode before the first frame
                qa_at, qa = max(0, frames - int(0.75 * fps) - 1), None
                for i in range(frames):
                    pg.evaluate(f"window.frame({i / fps:.4f})")
                    enc.stdin.write(pg.screenshot(type="jpeg", quality=92))
                    if i == qa_at:      # everything has landed and nothing has left yet: measure what the viewer reads
                        qa = pg.evaluate("window.QA ? window.QA() : null")
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
    if qa:
        import json as _json
        f = out.with_suffix(".qa.json")
        try:
            prev = _json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}
        except ValueError:
            prev = {}
        f.write_text(_json.dumps({**prev, **qa}), encoding="utf-8")
    return out
