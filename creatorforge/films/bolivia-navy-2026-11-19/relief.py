"""Relief for the light table: real terrain heights from the open Terrarium tiles (AWS Open Data 'elevation-tiles-prod';
SRTM and other public sources, attribution Mapzen / Tilezen), turned into a paper-style hillshade (height x6) in Web Mercator.
Downloads into maps/tiles (gitignored, untrusted data: decoded as images only). Run: python3 -I relief.py
Writes maps/relief.png (MW x MH map pixels for the box in geo.py)."""
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from geo import BOX, MW, MH, merc  # noqa: E402

Z = 7
T = D / "maps" / "tiles"; T.mkdir(parents=True, exist_ok=True)


def txy(lon, lat):
    n = 2 ** Z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


lon0, lat0, lon1, lat1 = BOX
x0, y1 = txy(lon0, lat0); x1, y0 = txy(lon1, lat1)
tx0, tx1, ty0, ty1 = int(x0), int(x1), int(y0), int(y1)
big = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        f = T / f"{Z}_{tx}_{ty}.png"
        if not f.exists():
            urllib.request.urlretrieve(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{tx}/{ty}.png", f)
        im = np.asarray(Image.open(f).convert("RGB"), np.float32)
        big[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = im[..., 0] * 256 + im[..., 1] + im[..., 2] / 256 - 32768
# crop to the box exactly, then resample to MW x MH
px0, px1 = (x0 - tx0) * 256, (x1 - tx0) * 256
py0, py1 = (y0 - ty0) * 256, (y1 - ty0) * 256
crop = big[int(py0):int(py1), int(px0):int(px1)]
h = np.asarray(Image.fromarray(crop).resize((MW, MH), Image.BILINEAR), np.float32)
np.save(D / "maps" / "height.npy", h.astype(np.float16))

# hillshade, sun from the north-west, height x6
ex = 6.0
mpp = 26 * 111320 / MW  # metres per map pixel at the equator scale (approx; latitude ~ -18 shrinks it ~5%)
gy, gx = np.gradient(h * ex / mpp)
az, alt = math.radians(315), math.radians(40)
slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
shade = np.clip(shade, 0, 1)
land = h > 0
cream = np.array([244, 239, 230], np.float32); tan = np.array([222, 208, 182], np.float32); ink = np.array([26, 26, 26], np.float32)
teal = np.array([44, 122, 140], np.float32)
hn = np.clip(h / 5200, 0, 1)[..., None]
base = cream * (1 - hn * .75) + tan * (hn * .75)                       # paper gets a little warmer with height
s = shade[..., None]
flat = math.sin(alt)
dark = np.clip((flat - s) * 1.25, 0, .75)                              # charcoal hillshade on the shadow side only
lit = np.clip((s - flat) * .9, 0, .3)                                  # the lit side goes paler
rgb = base * (1 - dark) + ink * dark
rgb = rgb * (1 - lit) + np.array([252, 249, 242], np.float32) * lit
sea = teal * .82 + cream * .18
rgb = np.where(land[..., None], rgb, sea)
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save(D / "maps" / "relief.png")
print("relief", MW, MH, "elev", float(h.min()), float(h.max()))
