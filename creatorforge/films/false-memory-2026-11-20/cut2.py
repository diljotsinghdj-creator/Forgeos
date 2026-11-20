"""Real photos and public-domain engravings -> collage pieces (owner's references: black-and-white halftone cut-outs with a white sticker edge).
Reads the picks below from assets/cand/cand.json (written by find_real2.py), downloads the large file once, and writes
assets/real2/<slug>.png (cut-outs) or .jpg (plates), plus data/photo_credits2.json.   usage: python3 -I cut2.py [slug ...]"""
import io, json, sys, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

D = Path(__file__).resolve().parent
OUT = D / "assets" / "real2"; RAW = OUT / "raw"; RAW.mkdir(parents=True, exist_ok=True)
BOOK = json.loads((D / "assets" / "cand" / "cand.json").read_text())
UA = {"User-Agent": "documentary-photo-search/1.0"}
COBALT, RED, PAPER, SLATE = (43, 108, 176), (197, 48, 48), (240, 244, 248), (20, 24, 36)

# slug: (search, index, mode, options). mode: cut = cut out with the studio's model; ink = line engraving on white; alpha = already transparent;
# plate = whole photo. options: bw (default) | keep (its own colour, the frame's one coloured object) | tint (r,g,b) | edge (sticker edge, share of size)
PICKS = {
    "head_brain": ("antique_brain_illustration", 1, "ink", {"up": 3, "crop": (.0, .0, 1.0, .9)}),
    "head_phren": ("phrenology_chart_engraving", 3, "ink", {"crop": (.0, .0, 1.0, .56)}),
    "eye": ("eye_engraving_vintage", 0, "ink", {}),
    "hand_sign": ("hand_holding_card_vintage", 5, "ink", {}),
    "hand_card": ("hand_holding_card_vintage", 0, "ink", {"up": 1}),
    "hand_small": ("hand_holding_card_vintage", 2, "ink", {}),
    "hand_up": ("hand_holding_card_vintage", 4, "ink", {"up": 1}),
    "hand_sleeve": ("hand_holding_card_vintage", 6, "ink", {"up": 1}),
    "pencil": ("pencil_wooden_single", 3, "cut", {"keep": True}),
    "drawer": ("filing_cabinet_drawer", 2, "plate", {}),
    "drawers": ("filing_cabinet_drawer", 0, "plate", {}),
    "cards_clip": ("index_cards_stack", 6, "plate", {"soft": True}),
    "magnifier": ("magnifying_glass_white_background", 1, "cut", {}),
    "files": ("stack_of_files_folders", 0, "plate", {}),
    "crowd": ("crowd_people_from_behind", 2, "plate", {}),
    "bus": ("city_bus_side", 4, "cut", {}),
    "envelope": ("old_envelope_letter", 3, "cut", {}),
    "stamp_up": ("rubber_stamp_wood", 2, "cut", {}),
    "stamp_side": ("rubber_stamp_wood", 4, "cut", {}),
    "sign": ("yield_sign_road", 7, "cut", {"keep": True}),
    "sign_face": ("yield_sign_road", 5, "sky", {"keep": True}),
    "tag": ("paper_tag_label_blank", 5, "cut", {"keep": True}),
    "tag2": ("paper_tag_label_blank", 6, "cut", {"keep": True}),
    "typewriter": ("typewriter_vintage", 0, "cut", {}),
    "paper": ("paper_texture_old_white", 3, "plate", {"soft": True, "plain": True}),
    "car_blue": ("blue_car_side_view", 6, "cut", {"tint": COBALT, "open": -60, "erase": [(.50, 0, 1, .46), (0, 0, .2, .3), (0, .3, .045, .75), (.955, .3, 1, .75)]}),
    "car_red": ("model_car_isolated_white", 6, "white", {"tint": RED}),
    "street": ("street_row_houses", 4, "plate", {}),
}


def fetch(slug, hit):
    for f in RAW.glob(f"{slug}.*"):
        return f
    for url in (hit["large"], hit["large"].replace("_5a27501db3.jpg", "_5a27501db3_b.jpg")):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
            im = Image.open(io.BytesIO(data)); f = RAW / f"{slug}.{'png' if im.format == 'PNG' else 'jpg'}"; f.write_bytes(data); return f
        except Exception as e:
            err = e
    raise RuntimeError(f"{slug}: {type(err).__name__}")


def halftone(g, cell=5.0, mix=.5):
    """g: 0..1 greyscale (1 = white). A 45-degree dot screen, mixed with the photo so detail survives."""
    h, w = g.shape; y, x = np.mgrid[0:h, 0:w]; k = 2 * np.pi / cell
    spot = (np.cos((x + y) * k * .7071) * np.cos((y - x) * k * .7071) + 1) / 2
    return g * (1 - mix) + (g > spot * .86 + .07) * mix


def grey(im, soft=False, plain=False):
    g = np.asarray(ImageOps.autocontrast(im.convert("L"), cutoff=1), dtype=np.float32) / 255
    g = np.clip((g - .5) * (1.0 if soft else 1.22) + .5, 0, 1)
    return g if plain else halftone(g, max(4.0, im.width / 300), .28 if soft else .5)


def tidy(alpha, keep=.02, opening=0):
    """Drop specks (parts smaller than `keep` of the biggest part) and, with `opening`, thin streaks."""
    from scipy import ndimage as nd
    a = np.asarray(alpha) > 128
    if opening > 0:
        core = nd.binary_opening(a, structure=np.ones((opening, opening)))
        a = a & nd.binary_dilation(core, structure=np.ones((opening + 2, opening + 2)))
    if opening < 0:     # thin horizontal streaks (a stretched image margin): keep only what joins, straight up or down, a part at least -opening px tall
        core = nd.binary_opening(a, structure=np.ones((-opening, 1))); grown = core
        for _ in range(400):
            nxt = nd.binary_dilation(grown, structure=np.ones((3, 1))) & a
            if (nxt == grown).all():
                break
            grown = nxt
        a = grown
    lab, n = nd.label(a)
    if n > 1:
        sizes = nd.sum(a, lab, range(1, n + 1)); big = sizes.max()
        a = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v >= big * keep])
    return Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.7))


def sticker(rgb, alpha, edge=.012):
    """A white paper edge around the piece, like a cut-out stuck on the page."""
    r = max(4, int(max(rgb.size) * edge)) | 1
    pad = r * 2; W, H = rgb.width + 2 * pad, rgb.height + 2 * pad
    A = Image.new("L", (W, H), 0); A.paste(alpha, (pad, pad))
    wide = A.filter(ImageFilter.MaxFilter(r * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: 255 if v > 110 else 0).filter(ImageFilter.GaussianBlur(.8))
    out = Image.new("RGBA", (W, H), (251, 252, 254, 0)); out.putalpha(wide)
    piece = Image.new("RGBA", (W, H), (0, 0, 0, 0)); piece.paste(rgb, (pad, pad)); piece.putalpha(A)
    return Image.alpha_composite(out, piece)


def finish(rgb, alpha, o):
    if o.get("keep"):
        col = Image.blend(rgb.convert("RGB"), ImageOps.grayscale(rgb).convert("RGB"), .18)
    else:
        g = grey(rgb)
        if o.get("tint"):
            t = np.array(o["tint"], dtype=np.float32) / 255; sl = np.array(SLATE, dtype=np.float32) / 255      # a duotone: slate shadows, the colour in the mid-tones, paper highlights
            g2 = (g ** o.get("gamma", .62))[..., None]
            arr = np.where(g2 < .5, sl + (t - sl) * (g2 / .5), t + (1 - t) * ((g2 - .5) / .5))
        else:
            arr = np.repeat(g[..., None], 3, 2)
        col = Image.fromarray((arr * 255).astype(np.uint8))
    return sticker(col, alpha, o.get("edge", .012))


def ink(im, o):
    """A line engraving: the paper inside the outline becomes a solid cut-out, the white around it goes."""
    if o.get("crop"):
        a, b, c, d = o["crop"]; im = im.crop((int(a * im.width), int(b * im.height), int(c * im.width), int(d * im.height)))
    up = o.get("up", 2 if max(im.size) < 1400 else 1)
    if up > 1:
        im = im.resize((im.width * up, im.height * up), Image.LANCZOS)
    L = ImageOps.autocontrast(im.convert("L"), cutoff=2)
    line = L.point(lambda v: 0 if v < 150 else 255)
    barrier = line.filter(ImageFilter.MinFilter(5))                                    # thicken the ink so small gaps in the outline are sealed
    pad = ImageOps.expand(barrier, 6, 255); ImageDraw.floodfill(pad, (0, 0), 128, thresh=20)
    back = pad.crop((6, 6, pad.width - 6, pad.height - 6)).point(lambda v: 255 if v == 128 else 0)
    alpha = tidy(ImageChops.invert(back).filter(ImageFilter.MaxFilter(3)), .03)
    g = np.asarray(L, dtype=np.float32) / 255; g = np.clip((g - .42) * 2.4 + .5, 0, 1)
    arr = g[..., None] * (np.array(PAPER) - np.array(SLATE)) + np.array(SLATE)
    rgb = Image.fromarray(arr.astype(np.uint8))
    box = alpha.getbbox(); return sticker(rgb.crop(box), alpha.crop(box), o.get("edge", .01))


def build(slug):
    key, idx, mode, o = PICKS[slug]; hit = next(h for h in BOOK[key]["hits"] if h["i"] == idx)
    f = fetch(slug, hit); im = Image.open(f)
    if mode == "plate":
        rgb = im.convert("RGB"); rgb.thumbnail((2200, 2200)); g = grey(rgb, o.get("soft"), o.get("plain"))
        Image.fromarray((g * 255).astype(np.uint8)).save(OUT / f"{slug}.jpg", quality=92); kind = "plate"
    elif mode == "ink":
        ink(im.convert("RGB"), o).save(OUT / f"{slug}.png"); kind = "engraving"
    elif mode == "alpha":
        im = im.convert("RGBA"); im.thumbnail((1500, 1500)); a = im.getchannel("A")
        white = Image.new("RGB", im.size, (255, 255, 255)); white.paste(im.convert("RGB"), mask=a)
        g = np.asarray(ImageOps.grayscale(white), dtype=np.float32) / 255; g = np.clip((g - .45) * 1.8 + .5, 0, 1)
        arr = g[..., None] * (np.array(PAPER) - np.array(SLATE)) + np.array(SLATE)
        box = a.getbbox(); sticker(Image.fromarray(arr.astype(np.uint8)).crop(box), a.crop(box), o.get("edge", .01)).save(OUT / f"{slug}.png"); kind = "engraving"
    elif mode in ("sky", "white"):      # a plain backdrop: blue sky, or a white studio sweep
        rgb = im.convert("RGB"); rgb.thumbnail((1500, 1500)); a = np.asarray(rgb, dtype=np.int16)
        back = (a[..., 2] > a[..., 0] + 18) & (a[..., 2] > 110) if mode == "sky" else (a.min(2) > 226)
        if mode == "white":             # only the white that touches the border is backdrop (the car has white parts too)
            from scipy import ndimage as nd
            lab, n = nd.label(back); edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
            back = np.isin(lab, list(edge))
        m = tidy(Image.fromarray((~back * 255).astype(np.uint8)), .2, 5); box = m.getbbox()
        finish(rgb.crop(box), m.crop(box), o).save(OUT / f"{slug}.png"); kind = "cut-out"
    else:
        sys.path.insert(0, "/home/user/forgeos/creatorforge/worker")
        from creatorforge_worker.media import cutouts
        rgb = im.convert("RGB"); rgb.thumbnail((1500, 1500)); m = cutouts._mask(rgb, None, False)
        assert m is not None, f"{slug}: no cut-out"
        m = tidy(m, .05, o.get("open", 0))
        for x0, y0, x1, y1 in o.get("erase", ()):        # parts of the mask that are the picture's stretched margin, not the object
            ImageDraw.Draw(m).rectangle((int(x0 * m.width), int(y0 * m.height), int(x1 * m.width), int(y1 * m.height)), fill=0)
        box = m.getbbox()
        finish(rgb.crop(box), m.crop(box), o).save(OUT / f"{slug}.png"); kind = "cut-out"
    lic = hit.get("licence") or "Pixabay Content License"
    return {"slug": slug, "kind": kind, "author": hit.get("author") or "", "source": hit.get("source") or "pixabay", "page": hit.get("page", ""), "licence": lic.upper() if len(lic) < 12 else lic,
            "title": hit.get("tags", "")[:90]}


if __name__ == "__main__":
    cred = {c["slug"]: c for c in (json.loads((D / "data" / "photo_credits2.json").read_text()) if (D / "data" / "photo_credits2.json").is_file() else [])}
    for slug in (sys.argv[1:] or list(PICKS)):
        try:
            cred[slug] = build(slug); print("ok  ", slug)
        except Exception as e:
            print("FAIL", slug, type(e).__name__, str(e)[:100])
    (D / "data" / "photo_credits2.json").write_text(json.dumps(list(cred.values()), indent=1))
