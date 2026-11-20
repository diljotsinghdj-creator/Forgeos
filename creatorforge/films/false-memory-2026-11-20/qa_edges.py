"""Edge check: lists every positioned piece whose box leaves the 1920x1080 frame (a cut-off word or stamp). Run after the builders.
Pieces meant to bleed (full-frame photos, the mat, the water, the minute bar) are skipped by size."""
import functools, http.server, os, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent
class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/fonts/"):
            return "/home/user/forgeos/creatorforge/worker/creatorforge_worker/media/vendor" + p
        return str(D) + p
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = """() => [...document.querySelectorAll('body > .a')].map(e => {const r = e.getBoundingClientRect();
  return {x0: Math.round(r.left), y0: Math.round(r.top), x1: Math.round(r.right), y1: Math.round(r.bottom), t: (e.innerText || e.tagName).trim().slice(0, 40).replace(/\\n/g, ' ')}})
  .filter(b => (b.x1 - b.x0) < 1900 && (b.x1 - b.x0) > 4 && (b.x1 > 1924 || b.x0 < -4 || b.y1 > 1084 || b.y0 < -4))"""
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium/chrome-linux/chrome" if os.path.exists("/opt/pw-browsers/chromium/chrome-linux/chrome") else "/opt/pw-browsers/chromium", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    for f in sorted((D / "html").glob("*.html")):
        pg.goto(f"http://127.0.0.1:{PORT}/html/{f.name}"); pg.wait_for_function("window.READY===true", timeout=120000)
        for o in pg.evaluate(JS):
            bad += 1; print(f"{f.stem:20s} x {o['x0']}..{o['x1']}  y {o['y0']}..{o['y1']}  {o['t']!r}")
    b.close()
srv.shutdown(); print("pieces off the frame:", bad)
