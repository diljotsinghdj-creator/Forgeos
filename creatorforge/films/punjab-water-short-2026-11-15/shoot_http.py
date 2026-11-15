"""Serve the studio over localhost (module scripts need http) and screenshot pages once window.READY is set."""
import functools, http.server, os, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent
ROOT = D
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/vendor/"):
            return "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media" + p
        if p.startswith("/fonts/"):
            return "/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor" + p
        return str(D) + p
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
names = sys.argv[1:] or [p.stem for p in sorted((D / "html").glob("*.html"))]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium/chrome-linux/chrome" if os.path.exists("/opt/pw-browsers/chromium/chrome-linux/chrome") else "/opt/pw-browsers/chromium", args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    for n in names:
        pg.goto(f"http://127.0.0.1:8765/html/{n}.html"); pg.wait_for_function("window.READY===true", timeout=300000); pg.wait_for_timeout(400)
        pg.screenshot(path=str(D / "png" / f"{n}.jpg"), type="jpeg", quality=92); print("shot", n, flush=True)
    print("errors:", errs[:5]); b.close()
srv.shutdown()
