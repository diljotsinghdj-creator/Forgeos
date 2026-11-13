// Every element with data-in enters at data-at seconds: slide (from data-from: l,r,t,b), drop, pop, wipe, sweep (highlighter),
// draw (SVG stroke), count (number). Settled pieces breathe slightly. The camera (#cam) pushes in slowly. setT(t) poses
// the frame at time t; a still is setT(99). Graphics step at 12 fps; the camera stays smooth.
const E={out:t=>1-Math.pow(1-t,3),back:t=>{const c=1.7,c3=c+1;return 1+c3*Math.pow(t-1,3)+c*Math.pow(t-1,2)}};
function clamp(x){return Math.max(0,Math.min(1,x))}
window.setT=function(t){
  const tq=Math.floor(t*12+1e-6)/12;
  const cam=document.getElementById('cam'), push=+(document.body.dataset.push||0.05), dur=+(document.body.dataset.dur||4);
  if(cam)cam.style.transform=`scale(${1+push*clamp(t/dur)})`;
  document.querySelectorAll('[data-in]').forEach((el,i)=>{
    const at=+el.dataset.at||0, d=+(el.dataset.d||.45), p=clamp((tq-at)/d), k=el.dataset.in, base=el.dataset.base||'';
    let tf='',op=p>0?1:0;
    if(k==='slide'){const f=el.dataset.from||'l',e=E.back(p),dist=(1-e)*1.25;const v={l:[-dist*1920,0],r:[dist*1920,0],t:[0,-dist*1080],b:[0,dist*1080]}[f];tf=`translate(${v[0]}px,${v[1]}px)`}
    else if(k==='drop'){tf=`translateY(${-(1-E.back(p))*700}px) rotate(${(1-p)*-8}deg)`}
    else if(k==='pop'){const s=p<1?.6+.4*E.back(p):1;tf=`scale(${s})`}
    else if(k==='wipe'){el.style.clipPath=`inset(0 ${100-100*E.out(p)}% 0 0)`}
    else if(k==='sweep'){el.style.setProperty('--hl',`${100*E.out(p)}%`);op=1}
    else if(k==='draw'){el.querySelectorAll('path').forEach(pa=>{const L=pa.getTotalLength();pa.style.strokeDasharray=L;pa.style.strokeDashoffset=L*(1-E.out(p))});op=1}
    else if(k==='count'){const a=+el.dataset.from0,b=+el.dataset.to;el.textContent=Math.round(a+(b-a)*E.out(p));op=p>0?1:0}
    const life=Math.max(0,tq-at-d), br=(el.dataset.breathe!=='0')?Math.sin(life*1.6+i)*.35*Math.min(1,life*2):0;
    const js=(el.dataset.jit!=='0'&&life>0)?((Math.sin(Math.floor(tq*6)*12.9898+i*78.233)*43758.5453)%1):0;
    el.style.opacity=op; el.style.transform=`${base} ${tf} translate(${js*1.6}px,${-js*1.2}px) rotate(${br}deg)`;
  });
};
window.addEventListener('load',()=>setT(+(new URLSearchParams(location.search).get('t')||99)));
