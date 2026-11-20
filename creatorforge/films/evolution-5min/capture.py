"""Animate each shot: setT(i/24) per frame in headless Chromium, frames piped to ffmpeg."""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent; FPS = 24
T = json.load(open(D / "timeline.json"))["shots"]; durs = {s["shot"]: s["dur"] for s in T}; out = D / "render"; out.mkdir(exist_ok=True)
def one(k):
    n = round(durs[k] * FPS)
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", str(out / f"{k}.mp4")], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--headless", "--no-sandbox", "--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto((D / "shots" / f"{k}.html").as_uri()); pg.wait_for_timeout(800)
        for i in range(n):
            pg.evaluate(f"setT({i / FPS})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=93))
        b.close()
    ff.stdin.close(); ff.wait(); return k, n
ks = sys.argv[1:] or list(durs)
with ThreadPoolExecutor(4) as ex:
    for k, n in ex.map(one, ks): print(k, n, flush=True)
