// Collage kit v2: motion rules adopted from LottieFiles' motion-design skill (MIT), applied to paper.
//  - Paper material: duration 1.0x, overshoot 3-5% (never rubbery). Entrances ease-out, exits ease-in at 70% of the
//    entrance duration, on-screen moves ease-in-out, loops sine.
//  - Duration scales with distance travelled (100px = 1.0x ... full screen = 1.8x) unless data-d is given.
//  - Counter-motion: a piece lifted in the air casts a larger, softer shadow that tightens as it lands.
//  - Depth through speed: data-depth (0 = background, 1 = foreground) sets how much a layer drifts with the camera.
//  - Paper pieces step at 12 fps (stop-motion); camera, light and drifting layers stay smooth.
// Elements: .el with data-in (slide drop pop wipe sweep draw count scan dissolve) data-at data-d data-from data-base
//   data-out (exit time) data-depth. Layers: .gobo (window-blind light), .fall (falling pieces), .dissolve (pixel reveal).
(function () {
  const clamp = x => Math.max(0, Math.min(1, x));
  const E = {
    out: p => 1 - Math.pow(1 - p, 3),
    in: p => p * p * p,
    io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
    paper: p => { const s = .55; p = p - 1; return 1 + p * p * ((s + 1) * p + s); },   // ~4% overshoot
  };
  const distScale = px => px <= 50 ? .8 : px <= 100 ? 1 : px <= 200 ? 1.3 : px <= 300 ? 1.5 : px <= 400 ? 1.6 : 1.85;
  window.KIT_EASE = E;
  window.setT = function (t) {
    const tq = Math.floor(t * 12 + 1e-6) / 12;                       // stop-motion clock for paper
    const cam = document.getElementById('cam');
    const push = +(document.body.dataset.push || .04), dur = +(document.body.dataset.dur || 4);
    const k = E.io(clamp(t / dur));
    if (cam) cam.style.transform = `scale(${1 + push * k})`;
    document.querySelectorAll('[data-in]').forEach((el, i) => {
      const kind = el.dataset.in, at = +el.dataset.at || 0, from = el.dataset.from || 'l';
      const travel = kind === 'slide' ? (from === 'l' || from === 'r' ? 1920 : 1080) * .6 : kind === 'drop' ? 420 : 80;
      const d = el.dataset.d ? +el.dataset.d : .42 * distScale(travel);
      const p = d <= .05 ? (tq >= at ? 1 : 0) : clamp((tq - at) / d);
      const base = el.dataset.base || '';
      let tf = '', op = p > 0 ? 1 : 0;
      if (kind === 'slide') {
        const e = E.paper(p), dist = (1 - e) * travel / .6 * .62;
        const v = { l: [-dist, 0], r: [dist, 0], t: [0, -dist], b: [0, dist] }[from];
        tf = `translate(${v[0]}px,${v[1]}px)`;
      } else if (kind === 'drop') {
        const e = E.paper(p);
        tf = `translateY(${-(1 - e) * travel}px) rotate(${(1 - p) * -6}deg) scale(${1 + (1 - p) * .06})`;
      } else if (kind === 'pop') {
        tf = `scale(${p < 1 ? .86 + .14 * E.paper(p) : 1})`;
      } else if (kind === 'wipe') { el.style.clipPath = `inset(0 ${100 - 100 * E.out(p)}% 0 0)`; }
      else if (kind === 'sweep') { el.style.setProperty('--hl', `${100 * E.out(p)}%`); op = 1; }
      else if (kind === 'scan') { el.style.clipPath = `inset(0 0 ${100 - 100 * E.out(p)}% 0)`; }
      else if (kind === 'draw') {
        (el.tagName === 'path' ? [el] : [...el.querySelectorAll('path')]).forEach(pa => { const L = pa.getTotalLength(); pa.style.strokeDasharray = L; pa.style.strokeDashoffset = L * (1 - E.out(p)); });
        op = 1;
      } else if (kind === 'count') {
        const a = +el.dataset.from0, b = +el.dataset.to, n = Math.round(a + (b - a) * E.out(p));
        el.textContent = el.dataset.comma ? n.toLocaleString('en-US') : n;
      } else if (kind === 'dissolve') {                                // pixel-dissolve reveal (cells hide in random order)
        el.querySelectorAll('.cell').forEach(c => { c.style.opacity = (+c.dataset.o) < E.io(p) ? 0 : 1; });
        op = 1;
      }
      // counter-motion: lifted pieces cast a bigger, softer shadow that tightens on landing
      if ((kind === 'drop' || kind === 'pop' || kind === 'slide') && el.dataset.shadow !== '0') {
        const lift = 1 - E.out(p), o = 8 + lift * 26, b = lift * 18;
        el.style.filter = `drop-shadow(${o * .7}px ${o}px ${b}px rgba(0,0,0,${.24 - lift * .1}))` + (el.dataset.filter ? ' ' + el.dataset.filter : '');
      }
      // exit: ease-in at 70% of the entrance duration
      if (el.dataset.out) {
        const pe = clamp((tq - +el.dataset.out) / (d * .7));
        if (pe > 0) { op = 1 - E.in(pe); tf += ` translateY(${E.in(pe) * -40}px)`; }
      }
      // depth: layers drift with the camera at their own speed; settled paper breathes a little (12 fps)
      const depth = el.dataset.depth !== undefined ? +el.dataset.depth : .5;
      const drift = (depth - .5) * 40 * k;
      const life = Math.max(0, tq - at - d);
      const br = el.dataset.breathe === '0' ? 0 : Math.sin(life * 1.4 + i) * .3 * Math.min(1, life * 2);
      const jit = (el.dataset.jit !== '0' && life > 0) ? ((Math.sin(Math.floor(tq * 6) * 12.9898 + i * 78.233) * 43758.5453) % 1) : 0;
      el.style.opacity = op;
      el.style.transform = `${base} ${tf} translate(${drift + jit * 1.4}px,${-jit}px) rotate(${br}deg)`;
    });
    // window-blind light drifting across the paper (smooth, not stepped)
    document.querySelectorAll('.gobo').forEach(g => { g.style.transform = `translateX(${-120 + t * 22}px) skewX(-18deg)`; });
    // falling pieces (banknote-like scraps, icons): constant fall with a slow sway
    document.querySelectorAll('.fall > *').forEach((c, i) => {
      const v = +(c.dataset.v || 160), y0 = +(c.dataset.y0 || -200), sw = Math.sin(t * 1.3 + i) * 24;
      c.style.transform = `translate(${sw}px,${y0 + v * t}px) rotate(${(+(c.dataset.r || 0)) + t * (+(c.dataset.spin || 30))}deg)`;
    });
  };
  window.addEventListener('load', () => setT(+(new URLSearchParams(location.search).get('t') || 99)));
})();
