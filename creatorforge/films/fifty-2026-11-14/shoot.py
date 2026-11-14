import os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent
exe = "/opt/pw-browsers/chromium/chrome-linux/chrome"
names = sys.argv[1:]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe if os.path.exists(exe) else "/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    for h in sorted((D / "html").glob("*.html")):
        if names and h.stem not in names:
            continue
        pg.goto(h.as_uri() + "?t=99"); pg.wait_for_timeout(700)
        pg.screenshot(path=str(D / "png" / (h.stem + ".jpg")), type="jpeg", quality=90)
    print("errors:", errs)
    b.close()
