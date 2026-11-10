"""Real photographs and footage as documentary shots: one photo becomes a moving 2.5D composition, footage carries
annotations, and both can hand over to a map or a figure inside the same shot.

    Photo: <src> | <move> | <title> | key: value ...
    Photos: <src>, <src>[, ...] | collage | split | sequence | swipe | fade | <title> | labels: A, B
    Footage: <src> | <title> | in: 2.0 | speed: 0.5 | key: value ...

<src> is a ledger asset ("asset:P0007", see studio/assets.py) or a file path. Options (any of them, any order):
    move:      push | pull | pan-left | pan-right | tilt-up | tilt-down | detail | still      (default push)
    at:        x, y, w, h          the detail to move to and pick out (fractions of the picture)
    depth:     layers | flat       2.5D: the picture is split into depth layers that move at different speeds
    frame:     none | print | taped | polaroid
    annotate:  circle x,y,r Label ; arrow x1,y1 -> x2,y2 Label ; box x,y,w,h Label ; label x,y Text
    then:      pin <place>  |  number <figure> <caption>     the photo hands over to a map or a figure
    grade:     none | mono | warm | cool | archive
    light:     sweep
    illustrative                   a stock picture standing in for the subject: an ILLUSTRATIVE tag is shown

Depth layers (prepare): the depth model (Depth Anything V2, media/depth3d.py) when it is installed, else the subject's
cut-out (ISNet / GrabCut; never a guessed cut of a person) over a ground-plane gradient. The far layer is filled behind
the nearer ones (OpenCV inpainting) only so the small parallax move never opens a hole; the move is kept small enough
that the fill is a few pixels at the edges, and every change is written to the asset's modification history.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from .ff import MediaError

MOVES = ("push", "pull", "pan-left", "pan-right", "tilt-up", "tilt-down", "detail", "still")
GRADES = {"none": "", "mono": "grayscale(1) contrast(1.12)", "warm": "sepia(.22) saturate(1.08) contrast(1.04)",
          "cool": "saturate(.85) hue-rotate(-8deg) contrast(1.05)", "archive": "sepia(.65) contrast(1.18) brightness(.97)"}


NUM = r"-?(?:\d+(?:\.\d+)?|\.\d+)"          # 0.3, .3, 12


def _floats(s: str) -> list[float]:
    return [float(x) for x in re.findall(NUM, s or "")]


def _annotations(text: str) -> list[dict]:
    out = []
    for item in [x.strip() for x in (text or "").split(";") if x.strip()][:6]:
        kind, _, rest = item.partition(" ")
        kind = kind.lower()
        if kind == "arrow" and "->" in rest:
            a, _, b = rest.partition("->")
            pa, pb = _floats(a)[:2], _floats(b)
            label = re.sub(r"^[\s\d.,-]+", "", b).strip()
            if len(pa) == 2 and len(pb) >= 2:
                out.append({"kind": "arrow", "p": pa + pb[:2], "label": label[:40]})
        elif kind in ("circle", "box", "label"):
            n = {"circle": 3, "box": 4, "label": 2}[kind]
            m = re.match(r"\s*((?:%s\s*,\s*){%d}%s)\s*(.*)$" % (NUM, n - 1, NUM), rest)
            if m:
                out.append({"kind": kind, "p": _floats(m.group(1)), "label": m.group(2).strip()[:40]})
    return out


def parse(kind: str, spec: str) -> dict | None:
    """The shot plan from its line (no files touched)."""
    parts = [p.strip() for p in (spec or "").split("|")]
    if not parts or not parts[0]:
        return None
    opts, free = {}, []
    for p in parts[1:]:
        k, sep, v = p.partition(":")
        if sep and re.fullmatch(r"[a-z]+", k.strip().lower()):
            opts[k.strip().lower()] = v.strip()
        elif p:
            free.append(p)
    flags = {f.lower() for f in free}
    move = next((f for f in flags if f in MOVES), opts.get("move", "push")).lower()
    plan = {"type": kind, "move": move if move in MOVES else "push", "depth": opts.get("depth", "layers" if kind == "photo" else "flat"),
            "frame": opts.get("frame", "none"), "annotate": _annotations(opts.get("annotate", "")), "grade": opts.get("grade", "none"),
            "light": opts.get("light", ""), "illustrative": "illustrative" in flags,
            "title": next((f for f in free if f.lower() not in MOVES and f.lower() not in ("illustrative", "collage", "split", "sequence",
                                                                                             "swipe", "fade", "cutout", "follow")), "")[:60]}
    if plan["grade"] not in GRADES:
        plan["grade"] = "none"
    at = _floats(opts.get("at", ""))
    if len(at) == 4:
        plan["at"] = at
    then = opts.get("then", "")
    if then:
        verb, _, rest = then.partition(" ")
        if verb.lower() == "pin" and rest.strip():
            plan["then"] = {"kind": "pin", "place": rest.strip()[:40]}
        elif verb.lower() == "number" and rest.strip():
            fig, _, cap = rest.strip().partition(" ")
            plan["then"] = {"kind": "number", "figure": fig[:14], "caption": cap[:60]}
    if kind == "photos":
        plan["srcs"] = [s.strip() for s in parts[0].split(",") if s.strip()][:6]
        plan["mode"] = next((f for f in flags if f in ("collage", "split", "sequence", "swipe", "fade")), "collage" if len(plan["srcs"]) > 2 else "split")
        plan["labels"] = [x.strip()[:30] for x in opts.get("labels", "").split(",") if x.strip()]
        if len(plan["srcs"]) < 2:
            return None
    else:
        plan["path"] = parts[0]          # (not "src": that key is the on-screen source line)
    if kind == "footage":
        # cutout: the subject is rotoscoped out of the footage onto the paper; follow: a marker stays on the subject
        plan["cutout"] = "cutout" in flags
        plan["follow"] = opts.get("follow", "")[:40] if "follow" in opts else ("" if "follow" not in flags else " ")
        sub = _floats(opts.get("subject", ""))
        plan["subject"] = sub if len(sub) == 4 else None
        plan["in"] = (_floats(opts.get("in", "0")) or [0.0])[0]
        plan["speed"] = min(2.0, max(0.25, (_floats(opts.get("speed", "1")) or [1.0])[0]))
        plan["depth"] = "flat"
    return plan


def resolve(src: str) -> tuple[Path, dict]:
    """A source -> (file, ledger record or {}). 'asset:ID' is looked up in the asset ledger (CF_ASSET_LEDGER)."""
    if src.lower().startswith("asset:"):
        from ..studio import assets
        rec = assets.Ledger(Path(os.environ.get("CF_ASSET_LEDGER") or assets.default_ledger())).get(src.split(":", 1)[1].strip())
        if not rec or not Path(rec.get("file", "")).is_file():
            raise MediaError(f"photo: asset {src} is not in the asset library")
        return Path(rec["file"]), rec
    p = Path(src).expanduser()
    if not p.is_file():
        raise MediaError(f"photo: {src} not found")
    return p, {}


def _depth(rgb, model: Path | None, person_ok: bool):
    """(depth 0..1 far..near, how it was made)."""
    import numpy as np
    from . import cutouts, depth3d
    h, w = rgb.size[1], rgb.size[0]
    try:
        if depth3d.enabled():
            tmp = Path(os.environ.get("TMPDIR", "/tmp")) / f"cf_depth_{hashlib.sha1(rgb.tobytes()[:65536]).hexdigest()[:12]}.png"
            rgb.save(tmp)
            return depth3d.estimate(tmp), "Depth Anything V2 (estimated depth)"
    except Exception:  # noqa: BLE001 - the model is optional; the cut-out below still gives two planes
        pass
    ground = np.linspace(0.0, 0.55, h, dtype=np.float32)[:, None] ** 1.4 * np.ones((1, w), np.float32)
    m = cutouts._mask(rgb, model, person=not person_ok)
    if m is None:
        return ground, "ground-plane gradient (no subject found)"
    mask = np.asarray(m, dtype=np.float32) / 255.0
    if not 0.02 < mask.mean() < 0.7:                   # nothing, or everything, stands out: no subject plane
        return ground, "ground-plane gradient (no clear subject)"
    return np.maximum(ground, mask * 0.95), "subject cut-out over a ground-plane gradient"


def prepare(plan: dict, work: Path, model: Path | None = None, width: int = 1920, height: int = 1080) -> dict:
    """Files for a photo / photos / footage shot; adds plan["img"] (or "imgs" / "frames"), the layers, credits and
    the modification history."""
    from PIL import Image
    work.mkdir(parents=True, exist_ok=True)
    mods: list[str] = []
    credits: list[str] = []
    if plan["type"] == "photos":
        plan["imgs"] = []
        for s in plan["srcs"]:
            path, rec = resolve(s)
            im = Image.open(path).convert("RGB")
            plan["imgs"].append({"img": path.as_uri(), "w": im.size[0], "h": im.size[1]})
            if rec.get("credit"):
                credits.append(rec["credit"])
        plan["credit"] = "; ".join(dict.fromkeys(credits))[:160]
        return plan
    path, rec = resolve(plan["path"])
    if rec.get("credit"):
        credits.append(rec["credit"])
    plan["credit"] = "; ".join(credits)[:160]
    plan["asset"] = rec.get("id", "")
    if plan["type"] == "footage":
        import subprocess
        key = hashlib.sha1(f"{path}|{plan['in']}|{plan['speed']}|{width}x{height}".encode()).hexdigest()[:12]
        fdir = work / f"footage_{key}"
        if not any(fdir.glob("f_*.jpg")):
            fdir.mkdir(parents=True, exist_ok=True)
            fps = int(os.environ.get("CF_MOTION_FPS") or 24)
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{plan['in']:.2f}", "-i", str(path), "-t", "40",
                            "-vf", f"setpts={1 / plan['speed']:.4f}*PTS,fps={fps},scale={width}:{height}:force_original_aspect_ratio=increase,"
                                   f"crop={width}:{height}", "-q:v", "3", str(fdir / "f_%05d.jpg")], check=True, timeout=600)
        frames = sorted(fdir.glob("f_*.jpg"))
        if not frames:
            raise MediaError("footage: no frames could be read")
        plan["frames"] = [f.as_uri() for f in frames]
        if plan.get("cutout") or plan.get("follow"):
            from . import track
            tdir = fdir / "track"
            info = tdir / ("track_cut.json" if plan.get("cutout") else "track.json")
            if info.is_file():
                tr = json.loads(info.read_text())
            else:
                res, how = track.track(frames, plan.get("subject"), tdir)
                tr = {"how": how, "pos": [[round(r["cx"], 4), round(r["cy"], 4)] for r in res],
                      "box": [[round(v, 4) for v in r["box"]] for r in res]}
                if plan.get("cutout"):
                    import numpy as np
                    from PIL import Image, ImageFilter
                    cut = []
                    for f, r in zip(frames, res):
                        m = Image.open(r["mask"]).convert("L").filter(ImageFilter.GaussianBlur(1.2))
                        edge = m.filter(ImageFilter.MaxFilter(9))
                        im = Image.open(f).convert("RGB")
                        rgba = Image.new("RGBA", im.size, (0, 0, 0, 0))
                        rgba.paste(Image.new("RGBA", im.size, (251, 249, 243, 255)), (0, 0), edge)   # the white paper edge
                        rgba.paste(im, (0, 0), m)
                        out = tdir / f"cut_{Path(f).stem}.png"
                        rgba.save(out)
                        cut.append(out.as_uri())
                    tr["cut"] = cut
                info.write_text(json.dumps(tr))
            plan["track"] = tr["pos"]
            plan["trackBox"] = tr["box"]
            if plan.get("cutout"):
                plan["frames"] = tr["cut"]
            mods.append(f"subject {'cut out (rotoscoped)' if plan.get('cutout') else 'tracked'} with {tr['how']}")
        plan["ffps"] = int(os.environ.get("CF_MOTION_FPS") or 24)
        plan["w"], plan["h"] = width, height
        mods.append(f"trimmed from {plan['in']:.1f}s" + (f", played at {plan['speed']}x" if plan["speed"] != 1 else "") + ", cropped to frame")
        plan["mods"] = mods
        return plan
    im = Image.open(path).convert("RGB")
    if max(im.size) > 2400:
        k = 2400 / max(im.size)
        im = im.resize((int(im.size[0] * k), int(im.size[1] * k)), Image.LANCZOS)
        mods.append("downscaled to 2400 px")
    plan["w"], plan["h"] = im.size
    key = hashlib.sha1(f"{path}|{path.stat().st_mtime}|{plan['depth']}".encode()).hexdigest()[:12]
    base = work / f"photo_{key}.jpg"
    if not base.is_file():
        im.save(base, quality=92)
    plan["img"] = base.as_uri()
    plan["layers"] = []
    if plan["depth"] == "layers":
        manifest = work / f"photo_{key}.layers.json"
        if manifest.is_file():
            plan.update(json.loads(manifest.read_text()))
        else:
            import numpy as np
            d, how = _depth(im, model, person_ok=False)
            d = np.asarray(Image.fromarray((np.clip(d, 0, 1) * 255).astype("uint8")).resize(im.size, Image.BILINEAR), np.float32) / 255
            t = [float(np.quantile(d, q)) for q in (0.55, 0.82)]
            t = [x for x in t if x > 0.12] or [0.6]
            a = np.asarray(im)
            layers = []
            for k, th in enumerate(t):
                soft = np.clip((d - th) / 0.015 + 0.5, 0, 1)        # a clean edge: the layer is the real pixels
                if soft.mean() < 0.01:
                    continue
                rgba = np.dstack([a, (soft * 255).astype("uint8")])
                f = work / f"photo_{key}_L{k + 1}.png"
                Image.fromarray(rgba, "RGBA").save(f)
                layers.append({"img": f.as_uri(), "depth": round(0.45 + 0.5 * (k + 1) / len(t), 2)})
            fill = "none"
            if layers:
                try:
                    import cv2
                    from . import inpaint
                    # fill only the inside of the nearer layers: at their edges the far layer keeps the real pixels,
                    # so a small parallax move shows real picture, not fill
                    hole = ((d > t[0]) * 255).astype("uint8")
                    hole = cv2.erode(hole, np.ones((7, 7), np.uint8))
                    painted, how_fill = inpaint.fill(a, hole)
                    far = np.where(hole[..., None] > 0, painted, a)
                    Image.fromarray(far.astype("uint8")).save(base.with_name(f"photo_{key}_far.jpg"), quality=92)
                    fill = f"{how_fill} behind the nearer layers"
                except ImportError:
                    fill = "none (OpenCV missing): parallax kept very small"
            info = {"layers": layers, "far": base.with_name(f"photo_{key}_far.jpg").as_uri() if "inpainting" in fill else base.as_uri(),
                    "depthHow": how, "fill": fill}
            # the subject (the nearest layer): the camera pushes toward it and keeps its head in frame
            near = d > t[-1]
            if 0.02 < near.mean() < 0.6:
                ys, xs = np.nonzero(near)
                h_, w_ = near.shape
                info["subj"] = [round(float(xs.mean() / w_), 3), round(float(ys.mean() / h_), 3), round(float(ys.min() / h_), 3),
                                round(float(ys.max() / h_), 3)]
            manifest.write_text(json.dumps(info))
            plan.update(info)
        if plan["layers"]:
            mods.append(f"split into {len(plan['layers']) + 1} depth layers ({plan.get('depthHow')}); far layer: {plan.get('fill')}")
    plan["mods"] = mods
    return plan
