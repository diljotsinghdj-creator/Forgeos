"""Re-download the film's real photos from the URLs in data/photo_credits.json into assets/real/raw/ (assets are not kept in git).
Run with `python3 -I fetch_real.py`, then `python3 -I real.py`. Downloads are untrusted files: nothing here executes them."""
import json
import time
import urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent
RAW = D / "assets" / "real" / "raw"; RAW.mkdir(parents=True, exist_ok=True)
for c in json.load(open(D / "data" / "photo_credits.json")):
    dst = RAW / f'{c["slug"]}.jpg'
    if dst.exists() and dst.stat().st_size > 2000:
        continue
    try:
        req = urllib.request.Request(c["image_url"], headers={"User-Agent": "documentary-photo-search/1.0"})
        dst.write_bytes(urllib.request.urlopen(req, timeout=90).read()); print("got", c["slug"]); time.sleep(1)
    except Exception as e:  # a blocked or rate-limited source is reported, never worked around
        print("FAILED", c["slug"], type(e).__name__, e)
