#!/usr/bin/env python3
"""Film render engine for the bank films (owner's go, 2026-11-20): shot list -> Kokoro voice -> animated picture -> score, SFX,
captions -> one MP4 at -14 LUFS.

usage: film_video.py <film_dir> [--check] [--voice-only] [--shots A:B] [--workers N] [--port P]

<film_dir>/video/shots.json:
{"slug": "pepper-was-money", "title": "...", "channel": "printfacts" | "dragonpsych", "voice": "am_michael", "speed": 1.0,
 "treatment": "pulse", "guide": {"Muziris": "Moo-ziris"},
 "shots": [{"id": "1.01", "beat": 1, "vo": "spoken line ('' for a silent beat)", "page": "02_receipt", "t": [0.0, 0.35],
            "cam": [z0, cx0, cy0, z1, cx1, cy1],   # zoom and focus centre (0..1 of the frame); default a slow centre push
            "pre": 0.0, "post": 0.3, "hold": 0.0,   # silence before the line, after it, and a still hold for silent beats
            "build": null,                           # seconds the timeline takes to run t0 -> t1 (default: the line's length)
            "cut": false}]}                          # true: 0.2 s music cut before the punchline ([CUT] in the script)

The picture: each shot opens its key-frame page (html/<page>.html) and runs the page's own timeline from t0 to t1, stepped at
12 fps (house style), while the camera (a CSS transform, so type stays crisp) moves at 24 fps. Consecutive shots on one page
continue its timeline, and every shot is a new camera set-up, which is what gate 4 (pacing) counts.
"""
import argparse
import functools
import http.server
import json
import math
import re
import subprocess
import sys
import threading
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORKER = REPO / "creatorforge" / "worker"
MEDIA = WORKER / "creatorforge_worker" / "media"
sys.path.insert(0, str(WORKER))
FPS, STEP = 24, 12
LIMIT_STILL, LIMIT_BUILD, LIMIT_MEAN = 4.5, 7.0, 5.0


def wav_len(p):
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def load(film):
    cfg = json.loads((film / "video" / "shots.json").read_text())
    for i, s in enumerate(cfg["shots"]):
        s.setdefault("id", f"{i + 1:03d}"); s.setdefault("vo", ""); s.setdefault("pre", 0.0); s.setdefault("post", 0.3)
        s.setdefault("hold", 0.0); s.setdefault("cut", False); s.setdefault("t", [0.0, 1.0]); s.setdefault("beat", 1)
        s.setdefault("cam", [1.0, .5, .5, 1.04, .5, .5]); s["n"] = i
    return cfg


def check(film, cfg):
    bad = []
    last = {}
    for s in cfg["shots"]:
        if not (film / "html" / f"{s['page']}.html").is_file():
            bad.append(f"{s['id']}: no page html/{s['page']}.html")
        t0, t1 = s["t"]
        if not (0 <= t0 <= t1 <= 1):
            bad.append(f"{s['id']}: t range {s['t']} must satisfy 0 <= t0 <= t1 <= 1")
        if len(s["cam"]) != 6 or not all(1.0 <= z <= 2.6 for z in (s["cam"][0], s["cam"][3])):
            bad.append(f"{s['id']}: cam must be [z0,cx0,cy0,z1,cx1,cy1] with zoom 1.0-2.6")
        if not s["vo"] and s["hold"] <= 0:
            bad.append(f"{s['id']}: a silent shot needs \"hold\" seconds")
        if re.search(r"[⚠`\[\]]", s["vo"]):
            bad.append(f"{s['id']}: vo contains script markup: {s['vo'][:50]}")
        last[s["page"]] = s
    return bad


def voice(film, cfg):
    from creatorforge_worker.studio import voice as V
    import os
    os.environ.setdefault("CF_KOKORO_DIR", str(WORKER / "creatorforge-data" / "models" / "kokoro"))
    assert V.kokoro_ready(), "Kokoro model missing"
    out = film / "video" / "audio"; out.mkdir(parents=True, exist_ok=True)
    stamp = out / "lines.json"
    done = json.loads(stamp.read_text()) if stamp.is_file() else {}
    for s in cfg["shots"]:
        if not s["vo"]:
            s["vdur"] = 0.0; continue
        f = out / f"{s['n']:03d}.wav"
        key = f"{cfg.get('voice', 'am_michael')}|{cfg.get('speed', 1.0)}|{s.get('say') or s['vo']}"
        if not (f.is_file() and done.get(f.name) == key):
            V.synth(s.get("say") or s["vo"], f, voice=cfg.get("voice", "am_michael"), speed=cfg.get("speed", 1.0), guide=cfg.get("guide") or {})
            done[f.name] = key; stamp.write_text(json.dumps(done, indent=0))
        s["vdur"] = wav_len(f)
    t = 0.0
    for s in cfg["shots"]:
        d = s["pre"] + s["vdur"] + s["post"] + s["hold"]
        s["dur"] = math.ceil(d * FPS) / FPS; s["start"] = t; t += s["dur"]
    cfg["total"] = t
    return cfg


def pacing(cfg):
    rows, worst = [], []
    for s in cfg["shots"]:
        building = s["t"][1] > s["t"][0] or s["cam"][:3] != s["cam"][3:]
        lim = LIMIT_BUILD if building else LIMIT_STILL
        if s["dur"] > lim + 1e-6:
            worst.append(f"{s['id']} ({s['page']}): {s['dur']:.1f} s > {lim} s ({'building' if building else 'still'})")
    mean = cfg["total"] / len(cfg["shots"])
    if mean > LIMIT_MEAN:
        worst.append(f"mean hold {mean:.2f} s > {LIMIT_MEAN} s")
    return mean, worst


class Handler(http.server.SimpleHTTPRequestHandler):
    film = None

    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/vendor/"):
            return str(MEDIA) + p
        if p.startswith("/fonts/"):
            return str(MEDIA / "vendor") + p
        return str(self.film) + p

    def log_message(self, *a):
        pass


SET_JS = """([T, z, cx, cy]) => {
  const want = '?t=' + T.toFixed(4);
  if (window.__T !== want) { history.replaceState(null, '', want); window.__T = want; document.dispatchEvent(new Event('DOMContentLoaded')); }
  if (!window.__G) { window.__G = 1; document.querySelectorAll('svg').forEach(e => { if (e.querySelector('feTurbulence') && /multiply/.test(e.getAttribute('style') || '')) e.style.display = 'none'; }); }
  const b = document.body, W = 1920, H = 1080;
  let x = W / 2 - cx * W * z, y = H / 2 - cy * H * z;
  x = Math.min(0, Math.max(W - W * z, x)); y = Math.min(0, Math.max(H - H * z, y));
  b.style.transformOrigin = '0 0'; b.style.transform = `translate(${x}px,${y}px) scale(${z})`;
  document.documentElement.style.overflow = 'hidden';
  document.documentElement.style.background = getComputedStyle(b).backgroundColor;
}"""


def probe(film, cfg, port):
    """Finds pages whose timeline can't be re-run in place (they need a reload per step): prints a "reload_pages" list."""
    from playwright.sync_api import sync_playwright
    from PIL import Image, ImageChops
    import io, os
    Handler.film = film
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler); threading.Thread(target=srv.serve_forever, daemon=True).start()
    exe = "/opt/pw-browsers/chromium/chrome-linux/chrome"; need = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else "/opt/pw-browsers/chromium", args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        for page in sorted({s["page"] for s in cfg["shots"]}):
            worst = 0.0
            for T in (0.35, 0.8):
                pg.goto(f"http://127.0.0.1:{port}/html/{page}.html?t={T}"); pg.wait_for_function("window.READY===true", timeout=120000); pg.wait_for_timeout(300)
                pg.evaluate("window.__T = location.search"); pg.evaluate(SET_JS, [T, 1.0, .5, .5]); ref = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("L")
                pg.goto(f"http://127.0.0.1:{port}/html/{page}.html?t=0.0"); pg.wait_for_function("window.READY===true", timeout=120000); pg.wait_for_timeout(300)
                pg.evaluate(SET_JS, [T, 1.0, .5, .5]); got = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("L")
                d = ImageChops.difference(ref, got).resize((192, 108)); worst = max(worst, sum(d.getdata()) / (192 * 108))
            print(f"  {page}: diff {worst:.2f}{'  -> needs reload' if worst > 1.0 else ''}", flush=True)
            if worst > 1.0:
                need.append(page)
        b.close()
    srv.shutdown()
    print('"reload_pages": ' + json.dumps(need))


def ease(p):
    return p * p * (3 - 2 * p)


def render_shot(pg, state, port, film, s, out, reload_pages):
    """Screenshots the shot frame by frame into ffmpeg (no frames kept on disk)."""
    n = round(s["dur"] * FPS)
    t0, t1 = s["t"]
    build = s.get("build") or max(0.4, s["pre"] + s["vdur"] if s["vdur"] else s["dur"] * .8)
    z0, x0, y0, z1, x1, y1 = s["cam"]
    ff = subprocess.Popen(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-vf", "noise=c0s=3:c0f=t+u", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)], stdin=subprocess.PIPE)  # film grain here: the page's SVG grain is hidden during capture (it made every frame slow)
    hard = s["page"] in reload_pages
    if state.get("page") != s["page"] and not hard:
        pg.goto(f"http://127.0.0.1:{port}/html/{s['page']}.html?t={t0:.4f}"); pg.wait_for_function("window.READY===true", timeout=120000)
        pg.wait_for_timeout(250); state["page"] = s["page"]
    prev, buf = None, None
    for i in range(n):
        sec = i / FPS
        T = t0 + (t1 - t0) * min(1.0, (math.floor(sec * STEP) / STEP) / build)          # the timeline steps at 12 fps
        c = ease(i / max(1, n - 1))
        key = (round(T, 4), round(z0 + (z1 - z0) * c, 4), round(x0 + (x1 - x0) * c, 4), round(y0 + (y1 - y0) * c, 4))
        if key != prev:
            if hard:
                if not prev or key[0] != prev[0]:
                    pg.goto(f"http://127.0.0.1:{port}/html/{s['page']}.html?t={key[0]:.4f}"); pg.wait_for_function("window.READY===true", timeout=120000)
                    pg.wait_for_timeout(120); state["page"] = None
                pg.evaluate("window.__T = location.search")
            pg.evaluate(SET_JS, list(key))
            buf = pg.screenshot(type="jpeg", quality=93, timeout=180000); prev = key
        ff.stdin.write(buf)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"ffmpeg failed on shot {s['id']}")


def picture(film, cfg, workers, port, only):
    from playwright.sync_api import sync_playwright
    import os
    Handler.film = film
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler); threading.Thread(target=srv.serve_forever, daemon=True).start()
    clips = film / "video" / "clips"; clips.mkdir(parents=True, exist_ok=True)
    reload_pages = set(cfg.get("reload_pages") or [])
    stamp = clips / "done.json"
    done = json.loads(stamp.read_text()) if stamp.is_file() else {}
    lock = threading.Lock()
    todo = [s for s in cfg["shots"] if (only is None or only[0] <= s["n"] < only[1])]
    sig = lambda s: json.dumps([s["page"], s["t"], s["cam"], round(s["dur"], 3), s.get("build"), round(s["pre"], 3)])
    todo = [s for s in todo if not ((clips / f"{s['n']:03d}.mp4").is_file() and done.get(str(s["n"])) == sig(s))]
    chunks = [todo[i::workers] for i in range(workers)]
    exe = "/opt/pw-browsers/chromium/chrome-linux/chrome"

    def run(chunk):
        if not chunk:
            return
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else "/opt/pw-browsers/chromium",
                                  args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
            pg = b.new_page(viewport={"width": 1920, "height": 1080}); state = {}
            for s in chunk:
                render_shot(pg, state, port, film, s, clips / f"{s['n']:03d}.mp4", reload_pages)
                with lock:
                    done[str(s["n"])] = sig(s); stamp.write_text(json.dumps(done))
                    print(f"  shot {s['id']} {s['page']} {s['dur']:.2f}s", flush=True)
            b.close()

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, chunks))
    srv.shutdown()


ACTS = {1: "hook", 2: "world", 3: "investigation", 4: "consequences", 5: "ending"}
SFX_FOR = {"slam": ("impact_punch", -15), "drop": ("whoosh_paper", -17), "draw": ("scribble_pen", -21), "pop": ("whoosh_paper", -22), "snap": ("impact_punch", -22)}


def sound(film, cfg):
    from creatorforge_worker.media import sfx_builtin
    from creatorforge_worker.studio import score
    v = film / "video"; work = v / "work"; work.mkdir(exist_ok=True)
    total = cfg["total"]
    bank = {p.stem: p for p in sfx_builtin.ensure(work / "sfx")}
    cues = []
    for s in cfg["shots"]:
        html = (film / "html" / f"{s['page']}.html").read_text(errors="ignore")
        t0, t1 = s["t"]
        build = s.get("build") or max(0.4, s["pre"] + s["vdur"] if s["vdur"] else s["dur"] * .8)
        mine = []
        for k, a0 in re.findall(r'data-anim="(\w+) ([\d.]+) [\d.]+"', html):
            a0 = float(a0)
            if k in SFX_FOR and t0 < a0 <= t1 and t1 > t0 and SFX_FOR[k][0] in bank:
                at = (a0 - t0) / (t1 - t0) * build
                if at < s["dur"] - .15 and all(abs(at - m[0]) > .45 for m in mine) and len(mine) < 2:
                    mine.append((at, *SFX_FOR[k]))
        cues += [(s["start"] + at, nm, db, s["id"]) for at, nm, db in mine]
    (film / "SFX_LOG.md").write_text(f"# SFX_LOG: {cfg['title']}\n\nAll sounds are the studio's built-in synthesised effects (ffmpeg, nothing licensed). "
                                     "Each cue comes from the shot's own animation event.\n\n| Time (s) | Shot | Sound | Level |\n|---|---|---|---|\n"
                                     + "".join(f"| {t:.2f} | {sh} | {nm} | {db} dB |\n" for t, nm, db, sh in cues))
    sfx = work / "sfx.wav"
    if cues:
        args, mix = [], []
        for i, (t, nm, db, _) in enumerate(cues):
            args += ["-i", str(bank[nm])]; ms = int(t * 1000); mix.append(f"[{i}:a]volume={db}dB,adelay={ms}|{ms}[s{i}]")
        # amix in groups so the filter graph stays small
        parts = []
        for g in range(0, len(cues), 40):
            sub = list(range(g, min(g + 40, len(cues)))); part = work / f"sfx_{g:04d}.wav"
            a2, m2 = [], []
            for j, i in enumerate(sub):
                t, nm, db, _ = cues[i]; a2 += ["-i", str(bank[nm])]; ms = int(t * 1000); m2.append(f"[{j}:a]volume={db}dB,adelay={ms}|{ms}[s{j}]")
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *a2, "-filter_complex", ";".join(m2) + ";" + "".join(f"[s{j}]" for j in range(len(sub)))
                            + f"amix=inputs={len(sub)}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo[a]", "-map", "[a]", "-ar", "48000", str(part)], check=True)
            parts.append(part)
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *sum((["-i", str(p)] for p in parts), []), "-filter_complex",
                        "".join(f"[{i}:a]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0[a]", "-map", "[a]", "-ar", "48000", str(sfx)], check=True)
    else:
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", str(sfx)], check=True)
    # narration bus
    lines = [s for s in cfg["shots"] if s["vo"]]
    vparts = []
    for g in range(0, len(lines), 40):
        sub = lines[g:g + 40]; part = work / f"vo_{g:04d}.wav"; a2, m2 = [], []
        for j, s in enumerate(sub):
            a2 += ["-i", str(v / "audio" / f"{s['n']:03d}.wav")]; ms = int((s["start"] + s["pre"]) * 1000); m2.append(f"[{j}:a]adelay={ms}|{ms}[v{j}]")
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *a2, "-filter_complex", ";".join(m2) + ";" + "".join(f"[v{j}]" for j in range(len(sub)))
                        + f"amix=inputs={len(sub)}:normalize=0,apad,atrim=0:{total:.3f},aformat=channel_layouts=stereo[a]", "-map", "[a]", "-ar", "48000", str(part)], check=True)
        vparts.append(part)
    vo = work / "vo.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *sum((["-i", str(p)] for p in vparts), []), "-filter_complex",
                    "".join(f"[{i}:a]" for i in range(len(vparts))) + f"amix=inputs={len(vparts)}:normalize=0[a]", "-map", "[a]", "-ar", "48000", str(vo)], check=True)
    # score, by act; a 0.2 s music cut before each [CUT] punchline
    acts, cur = [], None
    for s in cfg["shots"]:
        if s["beat"] != cur:
            acts.append([ACTS.get(s["beat"], "investigation"), s["start"], 0.0]); cur = s["beat"]
        acts[-1][2] += s["dur"]
    sc = score.compose([tuple(a) for a in acts], cfg.get("treatment", "pulse"), work / "score")
    cuts = [(max(0, s["start"] + s["pre"] - 0.2), s["start"] + s["pre"]) for s in cfg["shots"] if s["cut"]]
    mute = ",".join(f"volume=enable='between(t,{a:.3f},{b:.3f})':volume=0" for a, b in cuts)
    g = (f"[1:a]volume=2.0{',' + mute if mute else ''}[m];[0:a]asplit[vo][key];[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
         f"[vo][md][2:a]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]")
    mixed = work / "mix.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(vo), "-i", str(sc), "-i", str(sfx), "-filter_complex", g, "-map", "[a]", "-ar", "48000", str(mixed)], check=True)
    return mixed, len(cues), score.LAST_HOW, len(cuts)


def assemble(film, cfg, mixed):
    v = film / "video"; work = v / "work"
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{(v / 'clips' / (str(s['n']).zfill(3) + '.mp4')).as_posix()}'\n" for s in cfg["shots"]))
    raw = work / "picture.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(raw)], check=True)
    pre = work / "premix.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(raw), "-i", str(mixed), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(pre)], check=True)
    script = work / "script.txt"; script.write_text(" ".join(s["vo"] for s in cfg["shots"] if s["vo"]))
    out = v / f"{cfg['slug']}.mp4"
    chan = cfg.get("channel", "printfacts")
    subprocess.run([sys.executable, str(REPO / ".claude/skills/printfacts-style/captions.py"), str(pre), str(out), "youtube", str(script), chan], check=True)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("film"); ap.add_argument("--check", action="store_true"); ap.add_argument("--voice-only", action="store_true")
    ap.add_argument("--shots"); ap.add_argument("--workers", type=int, default=3); ap.add_argument("--port", type=int, default=8791)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    film = Path(a.film).resolve(); cfg = load(film)
    bad = check(film, cfg)
    if bad:
        print("SHOT LIST ERRORS:\n  " + "\n  ".join(bad)); sys.exit(2)
    if a.probe:
        probe(film, cfg, a.port); return
    if a.check and not a.voice_only:
        print(f"ok: {len(cfg['shots'])} shots, {len({s['page'] for s in cfg['shots']})} pages used"); return
    cfg = voice(film, cfg)
    mean, worst = pacing(cfg)
    print(f"voice: {sum(1 for s in cfg['shots'] if s['vo'])} lines, total {cfg['total'] / 60:.2f} min, mean hold {mean:.2f} s")
    if worst:
        print("GATE 4 (pacing) FAILS:\n  " + "\n  ".join(worst)); sys.exit(3)
    (film / "video" / "timeline.json").write_text(json.dumps([{k: s[k] for k in ("id", "page", "start", "dur", "vdur", "beat")} for s in cfg["shots"]], indent=0))
    if a.voice_only or a.check:
        return
    only = tuple(int(x) for x in a.shots.split(":")) if a.shots else None
    picture(film, cfg, a.workers, a.port, only)
    if only:
        return
    mixed, ncue, how, ncut = sound(film, cfg)
    out = assemble(film, cfg, mixed)
    rep = {"file": out.name, "minutes": round(cfg["total"] / 60, 2), "shots": len(cfg["shots"]), "mean_hold": round(mean, 2), "sfx_cues": ncue, "score": how, "music_cuts": ncut,
           "voice": f"kokoro:{cfg.get('voice', 'am_michael')}"}
    (film / "video" / "report.json").write_text(json.dumps(rep, indent=1)); print(json.dumps(rep))


if __name__ == "__main__":
    main()
