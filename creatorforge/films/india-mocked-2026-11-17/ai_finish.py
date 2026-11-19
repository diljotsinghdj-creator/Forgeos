"""Studio finish for AI plates (MASTER_DIRECTIVES §8c): palette pull, paper grain, light halftone.
Usage: python ai_finish.py IN.jpg OUT.jpg [--strength 0.35]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

PAL = np.array([[0xF4, 0xEF, 0xE6], [0x1A, 0x1A, 0x1A], [0xD9, 0x38, 0x29], [0xF7, 0xD0, 0x46], [0x8A, 0x6A, 0x4E]], float)  # cream, charcoal, crimson, yellow, desk walnut


def finish(src, dst, strength=0.35, size=(1920, 1080)):
    im = Image.open(src).convert("RGB")
    w, h = im.size; tw, th = size  # cover-crop to 16:9
    sc = max(tw / w, th / h); im = im.resize((round(w * sc), round(h * sc)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2; im = im.crop((l, t, l + tw, t + th))
    a = np.asarray(im, float)
    gray = a.mean(2, keepdims=True); a = gray + (a - gray) * 0.8                    # tame saturation
    d = ((a[:, :, None, :] - PAL[None, None]) ** 2).sum(-1); near = PAL[d.argmin(-1)]
    a = a * (1 - strength) + near * strength                                         # pull toward the palette
    lum = a.mean(2) / 255
    yy, xx = np.mgrid[0:th, 0:tw]; c = (np.sin(xx * 0.55) * np.sin(yy * 0.55) + 1) / 2   # halftone screen
    a *= (1 - 0.06 * (c > lum)[..., None])
    rng = np.random.default_rng(7); g = rng.normal(0, 1, (th, tw))
    g = np.asarray(Image.fromarray(((g * 40) + 128).clip(0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6)), float) / 128 - 1
    a *= (1 + 0.07 * g)[..., None]                                                   # paper grain
    r = np.hypot((xx - tw / 2) / (tw / 2), (yy - th / 2) / (th / 2)); a *= (1 - 0.12 * np.clip(r - 0.6, 0, 1))[..., None]
    Image.fromarray(a.clip(0, 255).astype("uint8")).save(dst, quality=92)


if __name__ == "__main__":
    s = float(sys.argv[sys.argv.index("--strength") + 1]) if "--strength" in sys.argv else 0.35
    finish(sys.argv[1], sys.argv[2], s)
