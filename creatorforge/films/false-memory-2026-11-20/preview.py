"""Check sheets for a cut before it is rendered: the first and last frame of every shot (and the middle of long ones), framed by the engine's own camera.
usage: python3 preview.py [out_dir] [shot id ...]      needs video/shots.json and video/timeline.json (film_video.py --voice-only writes it)"""
import functools, http.server, importlib.util, json, math, os, sys, threading
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("film_video", D.parents[1] / "channels" / "design_kits" / "film_video.py")
FV = importlib.util.module_from_spec(spec); spec.loader.exec_module(FV)
args = sys.argv[1:]
OUT = Path(args[0]) if args and not args[0][0].isdigit() else D / "video" / "preview"
only = [x for x in args if x[0].isdigit()]
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((D / "video" / "shots.json").read_text())
tl = {r["id"]: r for r in json.loads((D / "video" / "timeline.json").read_text())}


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/vendor/"):
            return "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media" + p
        if p.startswith("/fonts/"):
            return "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor" + p
        return str(D) + p

    def log_message(self, *a): pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
frames = []
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium/chrome-linux/chrome"
    b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else "/opt/pw-browsers/chromium", args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080}); cur = None
    for s in cfg["shots"]:
        if only and s["id"] not in only:
            continue
        r = tl[s["id"]]; dur, pre = r["dur"], s.get("pre", 0.0)
        build = s.get("build") or max(.4, pre + r["vdur"] if r["vdur"] else dur * .8)
        t0, t1 = s["t"]; z0, x0, y0, z1, x1, y1 = s["cam"]; n = round(dur * FV.FPS)
        picks = [0, n - 1] if dur < 3.2 and not only else [0, (n - 1) // 2, n - 1]
        if only:
            picks = sorted({round(k * (n - 1) / 7) for k in range(8)})
        if cur != s["page"]:
            pg.goto(f"http://127.0.0.1:{PORT}/html/{s['page']}.html?t={t0:.4f}"); pg.wait_for_function("window.READY===true", timeout=120000); pg.wait_for_timeout(250); cur = s["page"]
            pg.evaluate("window.__T = null")
        for i in picks:
            sec = i / FV.FPS
            T = t0 + (t1 - t0) * min(1.0, (math.floor(sec * FV.STEP) / FV.STEP) / build); c = FV.ease(i / max(1, n - 1))
            pg.evaluate(FV.SET_JS, [round(T, 4), z0 + (z1 - z0) * c, x0 + (x1 - x0) * c, y0 + (y1 - y0) * c])
            f = OUT / f"{s['id']}_{i:03d}.jpg"; pg.screenshot(path=str(f), type="jpeg", quality=86)
            frames.append((f, f"{s['id']} {s['page']} @{r['start'] + sec:6.2f}s  {(s['vo'] or '(silent)')[:34]}"))
    b.close()
srv.shutdown()
W, Hh, C, R = 640, 360, 4, 4
for k in range(0, len(frames), C * R):
    sh = Image.new("RGB", (W * C, (Hh + 24) * R), (20, 24, 36)); d = ImageDraw.Draw(sh)
    for j, (f, label) in enumerate(frames[k:k + C * R]):
        x, y = (j % C) * W, (j // C) * (Hh + 24)
        sh.paste(Image.open(f).resize((W, Hh)), (x, y + 24)); d.text((x + 6, y + 6), label, fill=(240, 244, 248))
    out = OUT / f"sheet_{k // (C * R) + 1:02d}.jpg"; sh.save(out, quality=84); print(out)
