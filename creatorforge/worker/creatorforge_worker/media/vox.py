"""The Vox look: editorial collage scenes drawn as smooth vector animation (SVG in headless Chromium, like motion.py),
with one shared style kit so every scene of every video looks like the same designed magazine:

- printed paper (fine grain, soft mottling) in one paper tone, black ink and ONE accent colour per video
- real cut-out photos (cutouts.py: halftone black-and-white with a white paper edge and a soft shadow), big:
  the subject fills 50-70% of the frame
- type: Anton (big words), Playfair Display (black-box serif headlines), Inter (tags), JetBrains Mono (notes)
- black boxes with white type, small tags, highlighter sweeps, brush strokes, accent discs and bars
- the big word sits BEHIND the subject (depth), blurred accent orb, vertical side text, a mono date/place line,
  crosshair marks, thin leader-line callouts
- motion the Vox way: pieces drop, slide or snap in on a 12 fps "stutter" while the camera pushes in smoothly with
  a little parallax (the background moves less than the subject)

Scenes (one per script line):
    Hero: gavel | THE VERDICT | 2019 · Supreme Court | five judges, one voice
          subject(s) "a + b" or person:Name | headline | tags (·) | a note with a leader line
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .ff import MediaError

FONTS = Path(__file__).parent / "vendor" / "fonts"
ACCENTS = {"yellow": "#F2C200", "red": "#D7262B", "blue": "#2D6BDB", "orange": "#F07A1A", "teal": "#14968A",
           "green": "#2E9B4F"}
PAPERS = {"cream": "#EFE8DA", "grey": "#E5E3DE", "white": "#F4F2EE", "dark": "#1B1B1D"}
INK = "#141414"
LAYOUTS = ("word", "disc", "box", "bars")
KINDS = ("hero",)


def accent_of(theme: str) -> str:
    """'editorial~2@red' -> the red accent; a hex colour is used as given; default yellow."""
    _, _, acc = (theme or "").partition("@")
    acc = acc.strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", acc):
        return acc
    return ACCENTS.get(acc.lower(), ACCENTS["yellow"])


def _seed(*parts) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


# ---- reading a scene line -------------------------------------------------------------------------------------------
def parse_hero(spec: str) -> dict | None:
    """'gavel + crowd | THE VERDICT | 2019 · Supreme Court | note' -> plan (no pictures yet)."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    opts = {}
    keep = []
    for p in parts[1:]:
        m = re.fullmatch(r"(style|layout|word|date|place|side)\s*[:=]\s*(.+)", p, re.I)
        if m:
            opts[m.group(1).lower()] = m.group(2).strip()
        else:
            keep.append(p)
    subjects = [s.strip() for s in re.split(r"\s+\+\s+|\s*&\s*", parts[0]) if s.strip()][:3]
    headline = keep[0] if keep else ""
    tags = [t.strip() for t in re.split(r"·|•|;", keep[1]) if t.strip()][:5] if len(keep) > 1 else []
    note = keep[2] if len(keep) > 2 else ""
    layout = (opts.get("style") or opts.get("layout") or "").lower()
    if layout not in LAYOUTS:
        layout = LAYOUTS[_seed(spec) % len(LAYOUTS)]
    word = opts.get("word") or ""
    if not word and layout == "word":
        # the big word behind the subject: the headline when short, else its strongest word
        hw = re.sub(r"[^\w\s'-]", "", headline).split()
        word = headline if 0 < len(hw) <= 2 else (max(hw, key=len) if hw else subjects[0].split(":")[-1])
    meta = [x for x in (opts.get("date", ""), opts.get("place", "")) if x]
    return {"type": "hero", "subjects": subjects, "headline": headline, "tags": tags, "note": note,
            "layout": layout, "word": word.upper()[:14], "meta": meta, "side": opts.get("side", ""),
            "seed": _seed(spec) % 10000}


PARSERS = {"hero": parse_hero}


def plan_for(kind: str, spec: str) -> dict | None:
    fn = PARSERS.get(kind)
    return fn(spec) if fn else None


# ---- pictures -------------------------------------------------------------------------------------------------------
def _pictures(plan: dict, lib: Path | None, model: Path | None, fetch: bool) -> None:
    """Each subject: a cut-out photo {img, w, h, credit} or the vector icon {o} when there's no photo."""
    from . import cutouts
    from .scene_anim import find_icon, icon_nodes
    out = []
    for s in plan.get("subjects", []):
        name = s if s.lower().startswith("person:") else s.lower()
        c = cutouts.get(name, lib, model=model, fetch=fetch)
        if c is not None:
            from PIL import Image
            with Image.open(c.path) as im:
                w, h = im.size
            out.append({"name": s, "img": c.path.as_uri(), "w": w, "h": h, "credit": c.credit})
        elif not name.startswith("person:"):
            icon = find_icon(name.split()[-1]) or find_icon(name) or "circle"
            out.append({"name": s, "o": icon_nodes(icon)})
    plan["pics"] = out
    credits = sorted({p["credit"] for p in out if p.get("credit")})
    plan["credit"] = ("Photo: " + "; ".join(credits))[:120] if credits else ""


# ---- paper and grain (baked once per size/tone) ---------------------------------------------------------------------
def paper(tone: str, w: int, h: int, work: Path) -> tuple[Path, Path]:
    """(paper background PNG, transparent fine-grain overlay PNG)."""
    import numpy as np
    from PIL import Image, ImageFilter
    work.mkdir(parents=True, exist_ok=True)
    bg, gr = work / f"vox_paper_{tone[1:]}_{w}x{h}.png", work / f"vox_grain_{w}x{h}.png"
    if not bg.is_file():
        rng = np.random.default_rng(7)
        base = np.array([int(tone[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
        small = Image.fromarray((rng.random((max(2, h // 40), max(2, w // 40))) * 255).astype("uint8"), "L")
        mottle = np.asarray(small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(w / 60)),
                            np.float32) / 255 - 0.5
        fine = rng.normal(0, 1, (h, w)).astype(np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        vig = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
        dark = base.mean() < 90
        img = base[None, None, :] + (mottle * 10)[..., None] + (fine * 3.2)[..., None] - (vig * (18 if not dark else 10))[..., None]
        Image.fromarray(np.clip(img, 0, 255).astype("uint8"), "RGB").save(bg)
    if not gr.is_file():
        rng = np.random.default_rng(11)
        n = rng.normal(0, 1, (h, w)).astype(np.float32)
        a = np.clip(np.abs(n) * 26, 0, 70).astype("uint8")
        v = np.where(n > 0, 255, 0).astype("uint8")
        Image.fromarray(np.dstack([v, v, v, a]), "RGBA").save(gr)
    return bg, gr


def _font_css() -> str:
    faces = [("Anton", "anton-latin-400-normal", 400, "normal"), ("Bebas", "bebas-neue-latin-400-normal", 400, "normal"),
             ("Playfair", "playfair-display-latin-400-normal", 400, "normal"),
             ("Playfair", "playfair-display-latin-700-normal", 700, "normal"),
             ("Playfair", "playfair-display-latin-900-normal", 900, "normal"),
             ("Playfair", "playfair-display-latin-700-italic", 700, "italic"),
             ("DMSerif", "dm-serif-display-latin-400-normal", 400, "normal"),
             ("Inter", "inter-latin-400-normal", 400, "normal"), ("Inter", "inter-latin-600-normal", 600, "normal"),
             ("Inter", "inter-latin-800-normal", 800, "normal"),
             ("Mono", "jetbrains-mono-latin-400-normal", 400, "normal"),
             ("Mono", "jetbrains-mono-latin-700-normal", 700, "normal"),
             ("Oswald", "oswald-latin-600-normal", 600, "normal"), ("Archivo", "archivo-black-latin-400-normal", 400, "normal")]
    out = []
    for fam, f, wt, st in faces:
        p = FONTS / f"{f}.woff2"
        if p.is_file():
            out.append(f"@font-face{{font-family:'{fam}';src:url('{p.as_uri()}') format('woff2');"
                       f"font-weight:{wt};font-style:{st}}}")
    return "\n".join(out)


# ---- the page -------------------------------------------------------------------------------------------------------
_PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
%FONTS%
html,body{margin:0;padding:0;background:%PAPER%;overflow:hidden}
svg{display:block}
</style><script>%SVGJS%</script></head><body><script>
const P=%PLAN%, W=%W%, H=%H%, DUR=%DUR%, K=%KIT%;
const TALL=H>W, U=Math.min(W,H), ACC=K.acc, INK=K.ink, PAPER=K.paper, DARK=K.dark;
const FG=DARK?'#F3EFE6':INK;
const draw=SVG().addTo('body').size(W,H);
const tracks=[], cam=[];
const E={out:t=>1-Math.pow(1-t,3), back:t=>{const c=1.6,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)},
  inout:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2, snap:t=>1-Math.pow(1-t,5), lin:t=>t};
function at(start,dur,fn,e){tracks.push({start,dur,fn,e:e||E.out})}
let seed=P.seed||1;function rnd(){seed=(seed*16807)%2147483647;return (seed-1)/2147483646}
// ---- layers (back to front) and the camera ----
const L={};['paper','back','mid','hero','front','grain'].forEach(k=>L[k]=draw.group());
draw.defs().svg(`<filter id="shadow" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="${U*.004}" dy="${U*.012}" stdDeviation="${U*.011}" flood-color="#000" flood-opacity=".32"/></filter>
<filter id="softshadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="${U*.006}" stdDeviation="${U*.006}" flood-color="#000" flood-opacity=".22"/></filter>
<filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="${U*.035}"/></filter>`);
L.paper.image(K.bg).size(W,H);
L.grain.image(K.grain).size(W,H).attr({style:'mix-blend-mode:multiply'}).opacity(DARK?.25:.55);
const DEPTH={paper:.012,back:.03,mid:.045,hero:.07,front:.055};
function camera(t){const p=E.inout(Math.min(1,t/Math.max(DUR,.1)));
  for(const k in DEPTH){const z=1+DEPTH[k]*p;L[k].attr({transform:`translate(${W/2*(1-z)},${H*.46*(1-z)}) scale(${z})`})}}
// ---- the style kit ----
function T(g,s,size,x,y,o){o=o||{};const t=g.text(String(s)).font({family:o.family||'Inter',size:size,weight:o.weight||600,
  anchor:o.anchor||'middle',style:o.italic?'italic':'normal'}).fill(o.fill||FG).attr({x:x,y:y,'dominant-baseline':'central'});
  if(o.ls)t.attr({'letter-spacing':o.ls});return t}
function fit(t,maxw){const w=t.bbox().width;if(w>maxw)t.font({size:t.font('size')*maxw/w});return t}
function lines(s,size,maxw,family,weight,most){const words=String(s).split(/\s+/).filter(Boolean),out=[];let cur='';
  const pr=draw.text('').font({family:family,size:size,weight:weight});
  for(const w of words){const tr=cur?cur+' '+w:w;pr.text(tr);if(cur&&pr.bbox().width>maxw){out.push(cur);cur=w}else cur=tr}
  if(cur)out.push(cur);pr.remove();return out.slice(0,most||3)}
function boxText(g,s,size,x,y,o){ // black box(es), white serif type - one box per line, like a cut label
  o=o||{};const ls=lines(String(s).toUpperCase(),size,o.maxw||W*.4,o.family||'Playfair',900,o.most||3);const grp=g.group();const pad=size*.28;
  let yy=y;const anchor=o.anchor||'start';
  ls.forEach((ln,i)=>{const row=grp.group();const t=T(row,ln,size,0,0,{family:o.family||'Playfair',weight:900,anchor:'start',fill:o.ink||'#FFFFFF',ls:'0.02em'});
    const bb=t.bbox();const r=row.rect(bb.width+pad*2,bb.height+pad*1.1).move(bb.x-pad,bb.y-pad*.55).fill(o.bg||'#111111').back();
    const w=bb.width+pad*2;const x0=anchor==='middle'?x-w/2+pad:anchor==='end'?x-w+pad:x+pad;
    row.attr({transform:`translate(${x0+(o.stagger?(i%2)*size*.9:0)},${yy})`});row.data('x',x0+(o.stagger?(i%2)*size*.9:0)).data('y',yy);yy+=bb.height+pad*1.5});
  return grp}
function tag(g,s,x,y,o){o=o||{};const grp=g.group();const size=o.size||U*.021;
  const t=T(grp,String(s).toUpperCase(),size,0,0,{family:'Inter',weight:800,anchor:'start',fill:o.ink||INK,ls:'0.14em'});
  const bb=t.bbox(),pad=size*.55;grp.rect(bb.width+pad*2,bb.height+pad*1.2).move(bb.x-pad,bb.y-pad*.6).fill(o.bg||'#FFFFFF')
    .stroke({color:o.ink||INK,width:Math.max(1,size*.07)}).back();
  grp.attr({transform:`translate(${x},${y})`});grp.data('w',bb.width+pad*2);return grp}
function highlight(g,bb,start,color){const r=g.rect(0,bb.height*.9).move(bb.x-bb.height*.12,bb.y+bb.height*.08).fill(color||ACC).back();
  at(start,.45,p=>r.width(Math.max(.1,(bb.width+bb.height*.24)*p)),E.inout);return r}
function brush(g,x,y,w,h,color,angle){ // a dry-brush stroke: ragged ends, streaky body
  const grp=g.group();const n=26;
  for(let k=0;k<7;k++){const yy=y+h*(k/7)+rnd()*h*.06;const th=h/7*(1.25+rnd()*.5);const x0=x+rnd()*w*.05;const x1=x+w*(.9+rnd()*.1);
    grp.rect(x1-x0,th).move(x0,yy).radius(th/2).fill(color||ACC).opacity(.86+rnd()*.14)}
  for(let k=0;k<n;k++){grp.circle(h*(.05+rnd()*.07)).center(x+w*(rnd()<.5?rnd()*.06:.94+rnd()*.06),y+rnd()*h).fill(color||ACC)}
  grp.attr({transform:`rotate(${angle||-6},${x+w/2},${y+h/2})`});return grp}
function disc(g,cx,cy,r,color){return g.circle(r*2).center(cx,cy).fill(color||ACC)}
function orb(g,cx,cy,r){return g.circle(r*2).center(cx,cy).fill(ACC).opacity(.85).attr({filter:'url(#blur)'})}
function cross(g,x,y,s){const c=g.group();c.line(x-s,y,x+s,y).stroke({color:FG,width:Math.max(1,U*.0016)});
  c.line(x,y-s,x,y+s).stroke({color:FG,width:Math.max(1,U*.0016)});c.circle(s*.9).center(x,y).fill('none').stroke({color:FG,width:Math.max(1,U*.0016)});return c}
function side(g,s){if(!s)return;const t=T(g,String(s),U*.019,0,0,{family:'Inter',weight:600,anchor:'middle',ls:'0.18em'});
  t.attr({transform:`translate(${W-U*.035},${H*.42}) rotate(90)`});return t}
function mono(g,s,x,y,o){o=o||{};return T(g,s,o.size||U*.019,x,y,{family:'Mono',weight:o.weight||400,anchor:o.anchor||'start',fill:o.fill||FG})}
function callout(g,x1,y1,x2,y2,s,start){ // dot on the subject, an elbow line, a mono note
  const dot=g.circle(U*.012).center(x1,y1).fill(ACC).stroke({color:INK,width:Math.max(1,U*.002)});
  const ln=g.polyline([[x1,y1],[x1,y1]]).fill('none').stroke({color:FG,width:Math.max(1,U*.0018)});
  const ls=lines(s,U*.027,W*.24,'Mono',400,3);const tg=g.group();const right=x2>x1;
  ls.forEach((l,i)=>mono(tg,l,x2+(right?U*.012:-U*.012),y2+i*U*.036,{size:U*.027,anchor:right?'start':'end'}));
  [dot,tg].forEach(e=>e.opacity(0));
  at(start,.6,p=>{dot.opacity(Math.min(1,p*3));const mx=x1+(x2-x1)*.35;
    const pts=[[x1,y1],[mx,y2],[x2,y2]];const seg=p<.5?[[x1,y1],[x1+(mx-x1)*p*2,y1+(y2-y1)*p*2]]:[pts[0],pts[1],[mx+(x2-mx)*(p-.5)*2,y2]];
    ln.plot(seg);tg.opacity(p>.8?(p-.8)*5:0)},E.inout)}
function picture(g,pic,x,y,h,o){ // a cut-out photo (or its icon) with its height h, centred at x, bottom at y
  o=o||{};const grp=g.group();
  if(pic&&pic.img){const w=h*pic.w/pic.h;grp.image(pic.img).size(w,h).move(x-w/2,y-h).attr({filter:'url(#shadow)'});grp.data('w',w)}
  else{const r=h*.42;grp.circle(r*2).center(x,y-h/2).fill(o.iconBg||'#FFFFFF').stroke({color:INK,width:U*.005}).attr({filter:'url(#softshadow)'});
    const ig=grp.group();for(const nd of ((pic&&pic.o)||[])){try{ig.element(nd[0]).attr(nd[1])}catch(e){}}
    const k=r*1.15/24;ig.attr({fill:'none',stroke:INK,'stroke-width':1.6,'stroke-linecap':'round','stroke-linejoin':'round',
      transform:`translate(${x-12*k},${y-h/2-12*k}) scale(${k})`});grp.data('w',r*2)}
  return grp}
// ---- motion kit (the stutter: these run on 12 fps steps) ----
function drop(el,start,dist,rot){el.opacity(0);const base=el.attr('transform')||'';
  at(start,.55,p=>{el.opacity(p>0?1:0);el.attr({transform:`translate(0,${-(dist||H*.25)*(1-p)}) rotate(${(rot||0)*(1-p)},${W/2},${H/2}) ${base}`})},E.back)}
function slide(el,start,dx,dy){el.opacity(0);const base=el.attr('transform')||'';
  at(start,.45,p=>{el.opacity(Math.min(1,p*2));el.attr({transform:`translate(${(dx||0)*(1-p)},${(dy||0)*(1-p)}) ${base}`})},E.snap)}
function popIn(el,cx,cy,start,d){el.opacity(0);const base=el.attr('transform')||'';
  at(start,d||.42,p=>{const s=.4+.6*p;el.opacity(Math.min(1,p*2.5));el.attr({transform:`translate(${cx*(1-s)},${cy*(1-s)}) scale(${s}) ${base}`})},E.back)}
function wipe(el,start){el.opacity(0);at(start,.35,p=>el.opacity(p),E.lin)}

// ---- scenes ----
function hit(a,b){return a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h}
function free(r,taken){return r.x>=U*.03&&r.x+r.w<=W-U*.03&&r.y>=U*.03&&r.y+r.h<=(TALL?H*.6:H*.77)&&!taken.some(t=>hit(r,t))}
function hero(){
  const pics=P.pics||[], lay=P.layout, taken=[];
  const BOT=TALL?H*.62:H*.78;                       // above the captions
  let HH=TALL?H*.40:H*.66;                          // the subject fills most of the frame height
  const main=pics[0]||{};const ar=main.img?main.w/main.h:.84;
  const maxW=W*(TALL?(lay==='word'?.7:.86):(lay==='box'?.46:lay==='word'?.36:.6));   // 'word': the word must show both sides
  if(HH*ar>maxW)HH=maxW/ar;                         // a wide subject: as big as the width allows
  const MW=HH*ar;
  let cx=(lay==='box'&&!TALL)?W*.31:W/2;
  cx=Math.max(U*.05+MW/2,Math.min(W-U*.05-MW/2,cx));
  const heroBox={x:cx-MW/2,y:BOT-HH,w:MW,h:HH};
  const core={x:cx-MW*.3,y:BOT-HH*.85,w:MW*.6,h:HH*.7};taken.push(core);
  // back: the accent shape and the big word sit behind the subject
  if(lay==='disc'){const r=Math.max(HH*.46,MW*.48);const dx=cx+MW*.1,dy=BOT-HH*.62;const d=disc(L.back,dx,dy,r);popIn(d,dx,dy,.05,.5)}
  if(lay==='bars'){const bw=Math.max(MW*.22,W*(TALL?.12:.06));[[-.52,0,ACC],[.42,.12,INK]].forEach(([k,dy,c],i)=>{
      const x=cx+k*MW;const bh=HH*(1.04-dy);
      const b=L.back.rect(bw,bh).move(x-bw/2,BOT-bh).fill(c).opacity(i?0.92:1).attr({transform:`rotate(${i?4:-5},${x},${BOT})`});
      slide(b,.05+i*.12,0,H*.4)})}
  if(lay==='box'&&!TALL){const b=brush(L.back,cx-MW*.62,BOT-HH*.45,MW*1.24,HH*.22,ACC,-8);wipe(b,.1)}
  if(lay==='word'){
    const word=P.word||(P.headline||'').toUpperCase();
    // widescreen: behind the subject's upper half (the subject cuts through it); Shorts: across the top, the
    // subject rising into its lower edge
    const t=TALL?T(L.back,word,W*.3,W/2,BOT-HH-W*.06,{family:'Anton',weight:400,fill:FG})
                :T(L.back,word,H*.5,W/2,BOT-HH*.66,{family:'Anton',weight:400,fill:FG,ls:'0.01em'});
    fit(t,W*.92);slide(t,.15,0,H*.06);const bb=t.bbox();taken.push({x:bb.x,y:bb.y,w:bb.width,h:bb.height})}
  orb(L.back,cx+(rnd()<.5?-1:1)*MW*.45,BOT-HH*.22,U*.075);
  // the subject(s): main one big, the others smaller at its sides
  pics.forEach((pic,i)=>{const isMain=i===0;const h=isMain?HH:HH*.46;
    const side=i===1?1:-1;const x=isMain?cx:Math.max(U*.12,Math.min(W-U*.12,cx+side*(MW*.5+HH*.22)));const y=isMain?BOT:BOT-HH*.02;
    const g=picture(isMain?L.hero:L.mid,pic,x,y,h);
    if(!isMain)taken.push({x:x-h*.4,y:y-h,w:h*.8,h:h});
    drop(g,isMain?.35:.6+i*.15,H*.3,isMain?-3:4)});
  // headline: black boxes, serif
  if(P.headline&&!(lay==='word'&&P.word&&P.word===P.headline.toUpperCase())){
    let g;
    if(lay==='box'&&!TALL){g=boxText(L.front,P.headline,U*.075,Math.min(W*.6,cx+MW/2+U*.04),H*.28,{maxw:W*.34,stagger:true});
      g.children().forEach((row,i)=>slide(row,.75+i*.18,W*.06,0))}
    else{g=boxText(L.front,P.headline,U*(TALL?.055:.052),W/2,TALL?H*.11:H*.085,{anchor:'middle',maxw:W*.8,most:2});
      g.children().forEach((row,i)=>slide(row,.7+i*.15,0,-H*.05))}
    const bb=g.rbox(draw);taken.push({x:bb.x-U*.02,y:bb.y-U*.02,w:bb.width+U*.04,h:bb.height+U*.04})}
  // tags: around the subject's edges, never on the headline, the subject's middle or each other
  const cand=[];const ys=[.18,.42,.66,.3,.54,.06];
  for(const fy of ys){cand.push([heroBox.x-U*.02,BOT-HH*(1-fy),'end']);cand.push([heroBox.x+MW+U*.02,BOT-HH*(1-fy),'start'])}
  (P.tags||[]).forEach((s,i)=>{const g=tag(L.front,s,0,0);const bb=g.bbox();const tw=bb.width,th=bb.height;
    let spot=null;for(let k=0;k<cand.length&&!spot;k++){const [x,y,an]=cand[(k+i)%cand.length];
      const r={x:an==='end'?x-tw:x,y:y-th/2,w:tw,h:th};if(free(r,taken))spot=r}
    if(!spot){g.remove();return}
    taken.push({x:spot.x-U*.01,y:spot.y-U*.01,w:spot.w+U*.02,h:spot.h+U*.02});
    g.attr({transform:`translate(${spot.x-bb.x},${spot.y-bb.y})`});slide(g,1.0+i*.22,(spot.x<cx?-1:1)*W*.05,0)});
  // note with a leader line from the subject
  if(P.note){const right=cx<W*.55;const x1=cx+(right?MW*.12:-MW*.12),y1=BOT-HH*.6;
    const x2=right?Math.min(W*.72,heroBox.x+MW+U*.08):Math.max(W*.28,heroBox.x-U*.08),y2=TALL?H*.68:H*.62;
    callout(L.front,x1,y1,x2,y2,P.note,1.3)}
  // the small print: crosshairs, the mono date/place line, side text, the photo credit
  const c=U*.016;[[U*.05,U*.05],[W-U*.05,U*.05]].forEach(([x,y])=>cross(L.front,x,y,c));
  if(P.meta&&P.meta.length){const m=mono(L.front,P.meta.join('  ·  ').toUpperCase(),U*.05,TALL?H*.66:H*.75,{weight:700});wipe(m,.9)}
  if(P.side)side(L.front,P.side.toUpperCase());
  if(P.credit){mono(L.front,P.credit,W-U*.03,H-U*.025,{size:U*.014,anchor:'end',fill:DARK?'#BBBBBB':'#555555'})}
}

const SCENES={hero};
async function boot(){
  try{await Promise.all(Array.from(document.fonts).map(f=>f.load()))}catch(e){}
  const imgs=[];(P.pics||[]).forEach(p=>{if(p.img)imgs.push(new Promise(r=>{const i=new Image();i.onload=i.onerror=r;i.src=p.img}))});
  await Promise.all(imgs);
  (SCENES[P.type]||hero)();
  window.frame=function(t){camera(t);const tq=Math.floor(t*12+1e-6)/12;   // the hand-made 12 fps stutter
    for(const k of tracks){const p=Math.max(0,Math.min(1,(tq-k.start)/k.dur));k.fn(k.e(p))}};
  window.frame(0);window.READY=true}
boot();
</script></body></html>"""


def render(kind: str, spec: str, theme: str, width: int, height: int, seconds: float, out: Path, work: Path,
           lib: Path | None = None, model: Path | None = None, fetch: bool = True, fps: int | None = None,
           tone: str = "cream") -> Path:
    """Draws one Vox scene into `out` (H.264)."""
    from . import motion
    if not motion.enabled():
        raise MediaError("vox scenes need the animation engine (Chromium + Playwright)")
    plan = plan_for(kind, spec)
    if plan is None:
        raise MediaError(f"vox: nothing to draw from {spec!r}")
    _pictures(plan, lib, model, fetch)
    if not plan["pics"]:
        raise MediaError("vox: no picture or icon for the subject")
    fps = int(fps or os.environ.get("CF_MOTION_FPS") or (60 if os.environ.get("CF_FPS") == "60" else 30))
    seconds = max(1.5, float(seconds))
    paper_hex = PAPERS.get(tone, PAPERS["cream"])
    bg, grain = paper(paper_hex, width, height, work)
    kit = {"acc": accent_of(theme), "ink": INK, "paper": paper_hex, "dark": tone == "dark",
           "bg": bg.as_uri(), "grain": grain.as_uri()}
    page = (_PAGE.replace("%SVGJS%", motion.VENDOR.read_text(encoding="utf-8")).replace("%FONTS%", _font_css())
            .replace("%PAPER%", paper_hex).replace("%PLAN%", json.dumps(plan, ensure_ascii=False))
            .replace("%W%", str(width)).replace("%H%", str(height)).replace("%DUR%", f"{seconds:.3f}")
            .replace("%KIT%", json.dumps(kit)))
    work.mkdir(parents=True, exist_ok=True)
    html = work / f"vox_{out.stem}.html"
    html.write_text(page, encoding="utf-8")
    return motion.capture(html, width, height, seconds, fps, out)
