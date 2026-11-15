"""Render the Short: 16 shots, each page animated frame by frame (24 fps camera push, reveals stepped at 12 fps),
word-by-word captions (signature yellow), Kokoro stand-in narration, a synthesised music bed and built-in SFX."""
import http.server
import json
import math
import re
import shutil
import subprocess
import sys
import threading
import wave
from pathlib import Path

import numpy as np

D = Path(__file__).resolve().parent
FPS = 24
ONLY = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), [])
GAP = 0.35
DUR = json.load(open(D / "audio" / "durs.json"))
LINES = json.load(open(D / "lines.json"))
# beat -> shots (page, share of the beat); the long beats are split in two
SHOTS = {1: [("01_rivers", 1)], 2: [("01_statement", .45), ("02_columns", .55)], 3: [("03_glow", 1)], 4: [("04_blocks", 1)],
         5: [("05h_paper", .52), ("05c_cube", .48)], 6: [("06_litres", 1)], 7: [("07a_power", .4), ("07_chain", .6)], 8: [("08_farmers", 1)],
         9: [("09_trend", .52), ("09b_canal", .48)], 10: [("10_warning", 1)], 11: [("11_tubewell", 1)], 12: [("12_end", 1)]}
SFX = {1: "whoosh_air", 2: "impact_punch", 3: "impact_deep", 4: "click_projector", 5: "whoosh_low", 6: "pop_soft", 7: "scribble_pen",
       8: "whoosh_paper", 9: "riser_tension", 10: "whoosh_paper", 11: "impact_deep", 12: "impact_deep"}
CAP_Y = {"02_columns": 1240, "12_end": 185, "06_litres": 835, "07_chain": 1478, "04_blocks": 940, "05c_cube": 1590 - 120, "01_rivers": 1230}

LIB = """<div id="cap" style="position:absolute;left:0;right:0;text-align:center;z-index:999;pointer-events:none"></div><script>
window.setT=function(t,sec,dur,capY,capHTML){
 const q=Math.floor(sec*12)/12/dur;
 const root=document.getElementById('ov')?null:document.body;
 if(root){root.style.transformOrigin='50% 42%';root.style.transform='scale('+(1+0.045*t).toFixed(4)+')';}
 else{const c=document.querySelector('canvas');if(c){c.style.transformOrigin='50% 50%';c.style.transform='scale('+(1+0.06*t).toFixed(4)+')';}}
 if(!window.CUSTOM_ONLY){
  const els=[...document.querySelectorAll(root?'body > .a':'#ov > div')].filter(e=>{const r=e.getBoundingClientRect();
    return !(r.width>=1000&&r.height>=1700)&&!e.dataset.keep&&e.id!=='cap'&&!(parseFloat(e.style.top)>=1570)});
  const n=els.length;els.forEach((e,i)=>{const at=0.02+0.45*i/Math.max(1,n);const vis=q>=at;e.style.opacity=vis?1:0;
    e.style.transform=(vis&&q<at+1/(12*dur)*1.01)?'scale(1.06)':'none'});
 }
 if(window.CUSTOM)window.CUSTOM(q,sec);
 const cap=document.getElementById('cap');cap.style.top=capY+'px';cap.innerHTML=capHTML;
 if(root){cap.style.transform='scale('+(1/(1+0.045*t)).toFixed(4)+')';}
};</script>"""

CUSTOM = {
    "01_rivers": "window.CUSTOM_ONLY=true;",
    "02_columns": """window.CUSTOM=function(q){document.querySelectorAll('body > .a').forEach(e=>{const d=e.firstElementChild;
      if(d&&d.style.width==='300px'&&parseFloat(d.style.height)>200){const s=Math.min(1,q/0.45);e.style.transformOrigin='50% 100%';e.style.transform='scaleY('+s.toFixed(3)+')';e.style.opacity=1}})};""",
    "03_glow": """window.CUSTOM=function(q){document.querySelectorAll('body > .a div').forEach(d=>{if(d.style.fontSize==='330px'||/330px/.test(d.style.font)){
      d.textContent=Math.round(156*Math.min(1,q/0.4))+'%'}})};""",
    "04_blocks": """window.CUSTOM=function(q){const g=[...document.querySelectorAll('#ov div div')].filter(d=>d.style.width==='44px');
      const k=Math.round(111*Math.min(1,Math.max(0,(q-0.08)/0.6)));g.forEach((d,i)=>{d.style.background=i<k?'#C8312B':'#3A3F4B';d.style.boxShadow=i<k?'0 0 12px rgba(200,49,43,.7)':'none'})};""",
    "09_trend": """window.CUSTOM=function(q){const p=[...document.querySelectorAll('path')].find(p=>p.getAttribute('stroke-width')==='7');
      if(p){p.setAttribute('pathLength','1');p.setAttribute('stroke-dasharray','1');p.setAttribute('stroke-dashoffset',(1-Math.min(1,q/0.55)).toFixed(3))}};""",
}


def serve():
    class Hd(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            p = path.split("?")[0]
            if p.startswith("/vendor/"):
                return "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media" + p
            if p.startswith("/fonts/"):
                return "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor" + p
            return str(D) + p

        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8781), Hd)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def words_timing(text, dur):
    """Word start/end inside a line, weighted by length plus a pause after punctuation (no forced alignment here)."""
    ws = text.split()
    wt = [len(re.sub(r"[^\w%]", "", w)) + 2 + (3 if w[-1] in ".,?" else 0) for w in ws]
    tot = sum(wt); out, t = [], 0.0
    for w, x in zip(ws, wt):
        d = dur * x / tot; out.append((w, t, t + d)); t += d
    return out


def cap_html(words, now):
    """Shows the 4-word group that holds the current word; the current word in yellow."""
    idx = next((i for i, (_, s, e) in enumerate(words) if s <= now < e), None)
    if idx is None:
        return ""
    g0 = idx - idx % 4
    grp = words[g0:g0 + 4]
    spans = "".join(f'<span style="color:{"#FFDD33" if g0 + j == idx else "#FFFFFF"}">{w} </span>' for j, (w, _, _) in enumerate(grp))
    return (f'<span style="display:inline-block;background:rgba(10,10,12,.82);padding:10px 22px 12px;border-radius:10px;font:400 58px/1.1 Anton;'
            f'letter-spacing:1px;max-width:960px">{spans.strip()}</span>')


def timeline():
    """Absolute times: every beat = its narration + a gap; the end card holds 1 s longer."""
    shots, t = [], 0.0
    for b in range(1, 13):
        span = DUR[b - 1] + GAP + (1.0 if b == 12 else 0)
        start = t
        for name, share in SHOTS[b]:
            shots.append({"beat": b, "page": name, "start": round(t, 3), "dur": round(span * share, 3)})
            t += span * share
        t = start + span
    return shots, t


def render_frames(shots):
    from playwright.sync_api import sync_playwright
    out = D / "frames"
    only = set(ONLY)
    if not only:
        shutil.rmtree(out, ignore_errors=True); out.mkdir()
    srv = serve()
    vo_words = {}
    for b in range(1, 13):
        vo_words[b] = words_timing(LINES[b - 1], DUR[b - 1])
    beat_start = {}
    for s in shots:
        beat_start.setdefault(s["beat"], s["start"])
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        pg = br.new_page(viewport={"width": 1080, "height": 1920})
        k = 0
        for s in shots:
            n = max(1, round(s["dur"] * FPS))
            if only and s["page"] not in only:
                k += n; continue
            src = (D / "html" / f"{s['page']}.html").read_text()
            src = src.replace("</body>", "<script>" + CUSTOM.get(s["page"], "") + "</script>" + LIB + "</body>")
            (D / "html" / f"_anim_{s['page']}.html").write_text(src)
            pg.goto(f"http://127.0.0.1:8781/html/_anim_{s['page']}.html")
            pg.wait_for_function("window.READY===true", timeout=300000); pg.wait_for_timeout(300)
            n = max(1, round(s["dur"] * FPS))
            for f in range(n):
                sec = f / FPS; t = sec / s["dur"]
                now = s["start"] + sec - beat_start[s["beat"]] - 0.1
                html = cap_html(vo_words[s["beat"]], now)
                pg.evaluate("([t,sec,dur,y,h])=>window.setT(t,sec,dur,y,h)", [t, sec, s["dur"], CAP_Y.get(s["page"], 1440), html])
                pg.screenshot(path=str(out / f"{k:05d}.jpg"), type="jpeg", quality=90); k += 1
            print("shot", s["page"], n, flush=True)
        br.close()
    srv.shutdown()
    return k


def read_wav(p):
    with wave.open(str(p)) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    if ch == 2:
        a = a.reshape(-1, 2).mean(1)
    if sr != 48000:
        x = np.arange(0, len(a), sr / 48000); a = np.interp(x, np.arange(len(a)), a)
    return a


def music(total):
    """A quiet minor-key pad with a slow low pulse (synthesised here, no licence needed)."""
    sr = 48000; t = np.arange(int(total * sr)) / sr
    chord = [110.0, 130.81, 164.81, 220.0]
    pad = sum(np.sin(2 * np.pi * f * t + i) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + i)) for i, f in enumerate(chord)) / len(chord)
    pad += 0.4 * np.sin(2 * np.pi * 55 * t)
    beat = 60 / 76
    ph = (t % beat)
    pulse = np.sin(2 * np.pi * 50 * ph) * np.exp(-ph * 9) * 0.9
    env = np.minimum(1, t / 2.0) * np.minimum(1, (total - t) / 2.5)
    return (0.10 * pad + 0.16 * pulse) * env


def mix(shots, total):
    sr = 48000
    L = int((total + 0.5) * sr)
    vo = np.zeros(L); fx = np.zeros(L)
    beat_start = {}
    for s in shots:
        beat_start.setdefault(s["beat"], s["start"])
    for b in range(1, 13):
        a = read_wav(D / "audio" / f"vo_{b:02d}.wav"); i = int((beat_start[b] + 0.1) * sr)
        vo[i:i + len(a)] += a[:L - i]
    for s in shots:
        name = SFX[s["beat"]] if s["start"] == beat_start[s["beat"]] else "whoosh_paper"
        a = read_wav(D / "audio" / "sfx" / f"{name}.wav") * 0.35; i = int(s["start"] * sr)
        fx[i:i + len(a)] += a[:L - i]
    m = music(L / sr)
    # duck the music under the voice
    envv = np.convolve(np.abs(vo), np.ones(4800) / 4800, mode="same")
    duck = 1 - 0.55 * np.clip(envv / (envv.max() * 0.25 + 1e-9), 0, 1)
    out = vo * 1.0 + fx + m * duck
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    out = pyln.normalize.loudness(out, meter.integrated_loudness(out), -14.0)
    out = np.tanh(out * 1.1) / np.tanh(1.1)          # soft limiter instead of hard clipping
    out = pyln.normalize.loudness(out, meter.integrated_loudness(out), -14.0)
    out = np.clip(out, -0.98, 0.98)
    with wave.open(str(D / "audio" / "mix.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    shots, total = timeline()
    json.dump({"shots": shots, "total": total}, open(D / "data" / "timeline.json", "w"), indent=1)
    holds = [s["dur"] for s in shots]
    print(f"{len(shots)} shots, total {total:.1f}s, longest {max(holds):.2f}s, mean {sum(holds) / len(holds):.2f}s")
    if "--audio-only" not in sys.argv:
        render_frames(shots)
    mix(shots, total)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(D / "frames" / "%05d.jpg"), "-i", str(D / "audio" / "mix.wav"),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", str(D / "punjab_water_overdraft.mp4")], check=True)
    print("done")
