"""Assemble: a finished collage poster cut into its pieces, which then land back in place one by one.

The build-on assembly, done locally (no video model, nothing invented, exact every time). Studied from the
vox-director skill's local engine (Alisa0808/vox-director, MIT, 2026): pieces rest at their ORIGINAL positions so the
assembled frame is the poster itself, and each piece's home spot is cleaned first so no copy shows before it lands.

Pieces come from hand-picked boxes when the spec gives them (fractions of the poster), else from an automatic split:
everything that is not the poster's flat ground, plus the salient-object mask, cut at narrow joins. Overlapping
pieces stay together (a headline strip the big "2" overlaps flies in as one piece). When the split finds fewer than
three usable pieces, or one piece is most of the poster, there are no pieces and the shot is a slow push on the
poster: never a broken assembly.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

MIN_AREA = 0.004        # a piece smaller than 0.4% of the poster is a speck, not a piece
MAX_PIECES = 10


def boxes_from(text: str) -> list[tuple[float, float, float, float]]:
    """'0.05 0.02 0.95 0.24; 0.1 0.3 0.4 0.6' -> boxes as fractions (x0, y0, x1, y1), clamped and ordered."""
    out = []
    for part in (text or "").replace(",", " ").split(";"):
        v = [float(x) for x in part.split() if _num(x)]
        if len(v) == 4:
            x0, y0, x1, y1 = (min(1.0, max(0.0, t)) for t in v)
            x0, x1 = sorted((x0, x1))
            y0, y1 = sorted((y0, y1))
            if (x1 - x0) * (y1 - y0) > 0.0005:
                out.append((x0, y0, x1, y1))
    return out[:MAX_PIECES]


def _num(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _ground(a):
    """The poster's flat ground colour: the commonest colour after coarse quantising."""
    import numpy as np
    q = (a // 24).reshape(-1, 3)
    vals, cnt = np.unique(q, axis=0, return_counts=True)
    return vals[cnt.argmax()].astype(np.int16) * 24 + 12


def auto_labels(im, mask_fn=None):
    """Label image of the poster's pieces (0 = ground) and the piece ids, largest first."""
    import cv2
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    m = np.abs(a - _ground(a)).max(axis=2) > 46                      # not the flat ground
    if mask_fn is not None:
        sal = mask_fn(im)
        if sal is not None:
            m |= np.asarray(sal) > 110                               # the salient things
    m = m.astype(np.uint8)
    b = max(4, int(min(w, h) * 0.035))                              # a border round the whole poster joins everything
    band = np.ones_like(m)
    band[b:-b, b:-b] = 0
    if m[band == 1].mean() > 0.6:
        m[band == 1] = 0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    e = max(5, int(min(w, h) * 0.022)) | 1                           # cores, then grown back: splits narrow joins
    core = cv2.erode(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (e, e)), iterations=2)
    ns, seeds, sst, _ = cv2.connectedComponentsWithStats(core, 8)
    mk = np.zeros((h, w), np.int32)
    for i in range(1, ns):
        if sst[i][4] > w * h * 0.0008:
            mk[seeds == i] = i + 1
    mk[m == 0] = 1
    lab = cv2.watershed(np.ascontiguousarray(a.astype(np.uint8)[:, :, ::-1]), mk)
    lab[(m == 0) | (lab < 2)] = 0
    ids, sizes = np.unique(lab[lab > 0], return_counts=True)
    keep = [(int(i), int(s)) for i, s in zip(ids, sizes) if s > w * h * MIN_AREA]
    keep.sort(key=lambda t: -t[1])
    return lab, [i for i, _ in keep[:MAX_PIECES]], [s / (w * h) for _, s in keep[:MAX_PIECES]]


def pieces(src: Path, work: Path, boxes=None, mask_fn=None) -> dict:
    """Cut the poster: {'bd': backdrop file, 'w', 'h', 'pieces': [{'file', 'x', 'y', 'w', 'h'} as fractions],
    'mode': 'boxes'|'auto'|'push'}. The backdrop is the poster with every piece's spot inpainted."""
    import cv2
    import numpy as np
    from PIL import Image
    im = Image.open(src).convert("RGB")
    W, H = im.size
    tag = hashlib.sha1(f"{Path(src).resolve()}|{boxes}".encode()).hexdigest()[:10]
    work.mkdir(parents=True, exist_ok=True)
    masks = []
    mode = "push"
    if boxes:
        mode = "boxes"
        for x0, y0, x1, y1 in boxes:
            bx = (int(x0 * W), int(y0 * H), max(int(x0 * W) + 2, int(x1 * W)), max(int(y0 * H) + 2, int(y1 * H)))
            mk = np.zeros((H, W), np.uint8)
            mk[bx[1]:bx[3], bx[0]:bx[2]] = 1
            sub = mask_fn(im.crop(bx)) if mask_fn is not None else None
            if sub is not None:                                      # a real cut-out inside the box, when it is clean
                s = (np.asarray(sub) > 110).astype(np.uint8)
                if 0.15 < s.mean() < 0.9:
                    mk[bx[1]:bx[3], bx[0]:bx[2]] = s
            masks.append(mk)
    else:
        lab, ids, areas = auto_labels(im, mask_fn)
        if len(ids) >= 3 and areas[0] < 0.55:
            mode = "auto"
            masks = [(lab == i).astype(np.uint8) for i in ids]
    rgb = np.asarray(im)
    out = []
    union = np.zeros((H, W), np.uint8)
    for n, mk in enumerate(masks):
        mk = cv2.dilate(mk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))   # keep the cut edge and its shadow
        ys, xs = np.where(mk > 0)
        if len(xs) == 0:
            continue
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        alpha = cv2.GaussianBlur(mk.astype(np.float32), (0, 0), 1.2)[y0:y1, x0:x1]
        rgba = np.dstack([rgb[y0:y1, x0:x1], (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
        f = work / f"asm_{tag}_{n}.png"
        Image.fromarray(rgba, "RGBA").save(f)
        out.append({"file": f, "x": x0 / W, "y": y0 / H, "w": (x1 - x0) / W, "h": (y1 - y0) / H})
        union |= mk
    bd = work / f"asm_{tag}_bd.jpg"
    if out:
        # each spot becomes bare ground: the median colour of a ring just outside it, with the paper's own grain
        # (inpainting a busy poster smears ghosts of the piece; a flat empty spot reads as the plate before assembly)
        hole = cv2.dilate(union, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        bgr = np.ascontiguousarray(rgb[:, :, ::-1]).astype(np.float32)
        fill = bgr.copy()
        n, lab = cv2.connectedComponents(hole, 8)
        for i in range(1, n):
            spot = (lab == i).astype(np.uint8)
            ring = cv2.dilate(spot, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) & (1 - hole)
            ref = np.median(bgr[ring > 0], axis=0) if ring.any() else np.median(bgr.reshape(-1, 3), axis=0)
            fill[spot > 0] = ref
        rng = np.random.default_rng(7)
        fill = fill + cv2.GaussianBlur(rng.normal(0, 7, (H, W)).astype(np.float32), (0, 0), 0.8)[..., None]   # paper grain
        soft = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 3)[..., None]
        bgr = np.clip(bgr * (1 - soft) + fill * soft, 0, 255).astype(np.uint8)
        cv2.imwrite(str(bd), bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    else:
        im.save(bd, quality=92)
    return {"bd": bd, "w": W, "h": H, "pieces": out, "mode": mode if out else "push"}
