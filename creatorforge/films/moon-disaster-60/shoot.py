"""Render each key-frame page at t=99 to a PNG (1920x1080)."""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parent / "stills"
exe = "/opt/pw-browsers/chromium/chrome-linux/chrome"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else "/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    for h in sorted((D / "html").glob(sys.argv[1] if len(sys.argv) > 1 else "*.html")):
        pg.goto(h.as_uri() + "?t=99")
        pg.wait_for_timeout(900)
        pg.screenshot(path=str(D / (h.stem + ".png")))
        print(h.stem)
    b.close()
