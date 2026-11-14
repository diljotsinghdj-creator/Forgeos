"""Build strip: stills of one page at chosen moments (shows the choreography without making a video)."""
import sys
from playwright.sync_api import sync_playwright
src, out = sys.argv[1], sys.argv[2]; ts = [float(x) for x in sys.argv[3].split(",")]
from PIL import Image, ImageDraw, ImageFont
frames = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--headless", "--no-sandbox", "--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.goto("file://" + src); pg.wait_for_timeout(1200)
    for t in ts:
        pg.evaluate(f"setT({t})"); pg.wait_for_timeout(120)
        pg.screenshot(path=f"/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/strip_{t}.png")
        frames.append((t, Image.open(f"/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/strip_{t}.png").convert("RGB").resize((640, 360))))
    b.close()
cols = 3; rows = (len(frames) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 646, rows * 400), "black"); d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("/home/user/Forgeos/creatorforge/worker/creatorforge_worker/media/vendor/fonts/inter-latin-800-normal.woff2", 26) if False else None
for i, (t, im) in enumerate(frames):
    x, y = (i % cols) * 646, (i // cols) * 400
    sheet.paste(im, (x, y)); d.text((x + 12, y + 366), f"t = {t:.1f} s", fill="white")
sheet.save(out); print("strip", out)
