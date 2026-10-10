"""Explainer layouts (the editorial / investigative looks): every picture is placed on a textured backdrop the way a
video essay builds its frames - a cut-out subject with a white sticker edge and a soft shadow, or, when the picture is
a whole scene, a tilted print with a white border (taped down on the desk look). Real footage and AI clips play inside
a bordered frame on the same backdrop. Everything is drawn with FFmpeg; cut-outs use the ISNet segmentation model when the pod has it."""
from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path

from . import ff

LAYOUTS = {"editorial": "paper", "investigative": "desk"}
YELLOW = "0xF7D62B"         # the explainer highlighter yellow
TAPE = "0xE9DFC4"
TILTS = (-1.6, 1.1, -0.7, 1.5, -1.2, 0.8)   # degrees, alternating so consecutive prints never sit the same way


def _key(*parts) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def backdrop(kind: str, w: int, h: int, work: Path, cancel: threading.Event | None = None) -> Path:
    """Off-white printed paper (fine grain + soft mottling) or a dark wooden desk (grain lines + mottling)."""
    out = work / f"backdrop_{kind}_{w}x{h}.png"
    if out.is_file():
        return out
    work.mkdir(parents=True, exist_ok=True)
    if kind == "desk":
        base = (f"color=c=0x3B2A1F:s={w}x{h}:d=1,format=rgb24,"
                f"geq=r='r(X,Y)+14*sin(Y/9+4*sin(X/260)+2*sin(Y/57))':g='g(X,Y)+10*sin(Y/9+4*sin(X/260)+2*sin(Y/57))'"
                f":b='b(X,Y)+7*sin(Y/9+4*sin(X/260)+2*sin(Y/57))'")
        mottle_opacity, vignette = 0.45, "vignette=angle=PI/3.2"
    else:
        base = f"color=c=0xF2ECDF:s={w}x{h}:d=1,format=rgb24"
        mottle_opacity, vignette = 0.3, "vignette=angle=PI/9"
    sigma = max(w, h) / 22
    graph = (f"{base}[base];"
             f"color=c=0x808080:s={w}x{h}:d=1,format=rgb24,noise=alls=90:allf=u,gblur=sigma={sigma:.1f}[mottle];"
             f"[base][mottle]blend=all_mode=softlight:all_opacity={mottle_opacity},noise=alls=9:allf=u,{vignette},"
             f"format=rgb24")
    tmp = out.with_name(f"{out.stem}.{threading.get_ident()}.part.png")
    ff.run(["-f", "lavfi", "-i", "nullsrc=s=16x16:d=1", "-filter_complex", graph, "-frames:v", "1", str(tmp)], cancel)
    tmp.replace(out)
    return out


CUTOUT_MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"


def cutout(image: Path, work: Path, model: Path | None = None) -> Path | None:
    """The picture's main subject on a transparent background (ISNet general-use segmentation, run with
    onnxruntime), or None when that wouldn't read as a cut-out: no model/onnxruntime on this machine, or the
    subject fills almost nothing / almost everything (a whole scene rather than an object)."""
    if model is None or not model.is_file():
        return None
    out = work / f"cut_{_key(image, image.stat().st_size, image.stat().st_mtime_ns)}.png"
    if out.is_file():
        return out if out.stat().st_size > 0 else None
    work.mkdir(parents=True, exist_ok=True)
    try:
        import numpy as np
        from PIL import Image
        session = _cutout_session(model)
        with Image.open(image) as im:
            rgb = im.convert("RGB")
        x = np.asarray(rgb.resize((1024, 1024), Image.LANCZOS), dtype=np.float32)
        x = x / max(float(x.max()), 1e-6) - 0.5                       # ISNet: scale to 0..1, mean 0.5, std 1
        pred = session.run(None, {session.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
        pred = (pred - pred.min()) / max(float(pred.max() - pred.min()), 1e-6)
        mask = Image.fromarray((pred * 255).astype("uint8"), "L").resize(rgb.size, Image.LANCZOS)
        m = np.asarray(mask)
        cover = float((m > 128).mean())
        unsure = float(((m > 30) & (m < 225)).mean())     # a soft, hesitant mask means no clear subject
        bbox = mask.point(lambda v: 255 if v > 128 else 0).getbbox()
        if not bbox or not 0.06 <= cover <= 0.62 or unsure > 0.3 * cover:
            out.write_bytes(b"")
            return None
        rgba = rgb.copy()
        rgba.putalpha(mask)
        tmp = out.with_name(f"{out.stem}.{threading.get_ident()}.part.png")   # two shots may share a picture
        rgba.crop(bbox).save(tmp)
        tmp.replace(out)
        return out
    except Exception:  # noqa: BLE001 - no onnxruntime / bad model / odd image: the print layout is used instead
        return None


_sessions: dict = {}
_session_lock = threading.Lock()


def _cutout_session(model: Path):
    with _session_lock:
        if str(model) not in _sessions:
            import onnxruntime as ort
            gpu = [p for p in ("CUDAExecutionProvider",) if p in ort.get_available_providers()]
            _sessions[str(model)] = ort.InferenceSession(str(model), providers=gpu + ["CPUExecutionProvider"])
        return _sessions[str(model)]




SLOTS = {"center": (0.0, 0.0, 1.0), "left": (-0.17, 0.02, 0.86), "right": (0.17, -0.01, 0.86)}


def compose(image: Path, kind: str, index: int, w: int, h: int, work: Path, cut: Path | None = None,
            cancel: threading.Event | None = None, under: Path | None = None, slot: str = "center") -> Path:
    """One finished explainer frame (PNG) for a still: sticker cut-out when `cut` is given, else a tilted print.
    `under` piles it onto the previous frame (photos building up on the desk); `slot` moves it left or right."""
    out = work / f"layout_{_key(image, cut, kind, index, w, h, image.stat().st_mtime_ns, under, slot)}.png"
    if out.is_file():
        return out
    bg = backdrop(kind, w, h, work, cancel)
    if under is not None and under.is_file():
        # the earlier photos stay on the desk, a touch darker, so the new one reads as the top of the pile
        bg = work / f"under_{_key(under, under.stat().st_mtime_ns)}.png"
        if not bg.is_file():
            ff.run(["-i", str(under), "-vf", "eq=brightness=-0.025:saturation=0.92", str(bg)], cancel)
    tilt = TILTS[index % len(TILTS)]
    short = min(w, h)
    fx, fy, size = SLOTS.get(slot, SLOTS["center"])
    if h > w:
        fx, fy = fx * 0.35, fy * 1.5        # tall frames have little room sideways: small shifts only
    ox, oy = int(w * fx), int(h * fy)
    if cut is not None:
        graph, inputs = _sticker(w, h, short, tilt * 0.6, size), [bg, cut]
    else:
        graph, inputs = _print(kind, index, w, h, short, tilt, size), [bg, image]
    # place the layer: every overlay that centres something on the frame shifts by the slot's offset
    graph = graph.replace("(W-w)/2", f"(W-w)/2+{ox}").replace("(H-h)/2", f"(H-h)/2+{oy}")
    graph = re.sub(r"\(W([-+])(\d+)\)/2", lambda m: f"(W{m.group(1)}{m.group(2)})/2+{ox}", graph)
    graph = re.sub(r"\(H([-+])(\d+)\)/2", lambda m: f"(H{m.group(1)}{m.group(2)})/2+{oy}", graph)
    args = []
    for p in inputs:
        args += ["-i", str(p)]
    tmp = out.with_name(f"{out.stem}.{threading.get_ident()}.part.png")
    ff.run([*args, "-filter_complex", graph, "-frames:v", "1", str(tmp)], cancel)
    tmp.replace(out)
    return out


def _shadow(src: str, dst: str, short: int, opacity: float = 0.55) -> str:
    """A soft drop shadow from a layer's alpha."""
    return (f"[{src}]alphaextract,gblur=sigma={short * 0.012:.1f},lut=y='val*{opacity}'[{dst}a];"
            f"[{dst}a]split[{dst}m][{dst}s];[{dst}s]lut=y=0[{dst}k];[{dst}k][{dst}m]alphamerge[{dst}]")


def _sticker(w: int, h: int, short: int, tilt: float, size: float = 1.0) -> str:
    """Cut-out subject with a white outline (its own grown silhouette) and a drop shadow, centred a little high."""
    edge = max(5, int(short * 0.017))
    pad = edge * 3
    bw, bh = int(w * 0.78 * size), int(h * (0.62 if h > w else 0.74) * size)
    dx, dy = int(short * 0.012), int(short * 0.018)
    return (f"[1:v]format=rgba,scale={bw}:{bh}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad=iw+{2 * pad}:ih+{2 * pad}:{pad}:{pad}:color=black@0,split[subj][grow];"
            f"[grow]alphaextract,gblur=sigma={edge * 0.55:.1f},lut=y='if(gt(val,6),255,0)',gblur=sigma=1.2[ea];"
            f"[ea]split[em][es];[es]lut=y=255[ew];[ew][em]alphamerge,format=rgba[edge];"
            f"[edge]format=yuva444p[edgey];[edgey]geq=lum='235':cb='128':cr='128':a='alpha(X,Y)',format=rgba[white];"
            f"[white][subj]overlay=format=auto,format=rgba,"
            f"rotate={tilt}*PI/180:c=none:ow=rotw({tilt}*PI/180):oh=roth({tilt}*PI/180),split[st][stsh];"
            + _shadow("stsh", "sh", short) +
            f";[0:v][sh]overlay=x=(W-w)/2+{dx}:y=(H-h)/2-H*0.03+{dy}[b1];"
            f"[b1][st]overlay=x=(W-w)/2:y=(H-h)/2-H*0.03,format=rgb24")


def _print(kind: str, index: int, w: int, h: int, short: int, tilt: float, size: float = 1.0) -> str:
    """A whole-scene picture as a bordered print: 4:3 on wide frames, 4:5 on tall ones."""
    if h > w:
        pw = int(w * 0.84 * size) // 2 * 2
        ph = int(pw * 5 / 4) // 2 * 2
    else:
        ph = int(h * 0.74 * size) // 2 * 2
        pw = int(ph * 4 / 3) // 2 * 2
    border = max(6, int(short * 0.018)) // 2 * 2
    dx, dy = int(short * 0.012), int(short * 0.018)
    rad = f"{tilt}*PI/180"
    extra = ""
    if kind == "desk":
        # Two strips of masking tape over the top corners.
        tw, th = int(pw * 0.22), max(12, int(short * 0.035))
        extra = (f";color=c={TAPE}@0.82:s={tw}x{th},format=rgba,rotate=-0.45:c=none:ow=rotw(0.45):oh=roth(0.45)[t1];"
                 f"color=c={TAPE}@0.82:s={tw}x{th},format=rgba,rotate=0.45:c=none:ow=rotw(0.45):oh=roth(0.45)[t2];"
                 f"[b2][t1]overlay=x=(W-{pw})/2-w*0.35:y=(H-{ph})/2-H*0.03-h*0.45[b3];"
                 f"[b3][t2]overlay=x=(W+{pw})/2-w*0.65:y=(H-{ph})/2-H*0.03-h*0.45[b4]")
    accent = ""
    base = "0:v"
    if kind == "paper" and index % 2 == 0:
        # The explainer signature: a flat yellow block peeking out behind the print.
        aw, ah = int(pw * 0.55), int(ph * 0.45)
        accent = (f"color=c={YELLOW}:s={aw}x{ah},format=rgb24[acc];"
                  f"[0:v][acc]overlay=x=(W-{pw})/2-w*0.12:y=(H+{ph})/2-H*0.03-h*0.78[b0];")
        base = "b0"
    last = "b4" if kind == "desk" else "b2"
    return (accent +
            f"[1:v]scale={pw}:{ph}:force_original_aspect_ratio=increase:flags=lanczos,crop={pw}:{ph},setsar=1,"
            f"eq=contrast=1.04:saturation=0.92,format=rgba,"
            f"pad=iw+{2 * border}:ih+{2 * border}:{border}:{border}:color=0xFBF8F1,"
            f"rotate={rad}:c=none:ow=rotw({rad}):oh=roth({rad}),split[pr][prsh];"
            + _shadow("prsh", "sh", short) +
            f";[{base}][sh]overlay=x=(W-w)/2+{dx}:y=(H-h)/2-H*0.03+{dy}[b1];"
            f"[b1][pr]overlay=x=(W-w)/2:y=(H-h)/2-H*0.03[b2]" + extra + f";[{last}]format=rgb24")


def video_box(w: int, h: int) -> tuple[int, int]:
    """Size of the picture area when a clip plays framed: 4:5 on tall frames, 16:9 on wide ones."""
    if h > w:
        pw = int(w * 0.88) // 2 * 2
        return pw, int(pw * 5 / 4) // 2 * 2
    ph = int(h * 0.78) // 2 * 2
    pw = int(ph * 16 / 9) // 2 * 2
    if pw > w * 0.9:
        pw = int(w * 0.86) // 2 * 2
        ph = int(pw * 9 / 16) // 2 * 2
    return pw, ph


def video_graph(w: int, h: int, clip: str, bg: str, out: str) -> str:
    """Filter that plays [clip] (already cover-scaled to video_box) inside a white-bordered frame with a soft
    shadow on the backdrop stream [bg]; the result is [out]."""
    short = min(w, h)
    pw, ph = video_box(w, h)
    border = max(6, int(short * 0.016)) // 2 * 2
    dx, dy = int(short * 0.010), int(short * 0.015)
    fw, fh = pw + 2 * border, ph + 2 * border
    return (f"[{bg}]format=rgb24,split[{bg}a][{bg}b];"
            f"color=c=black@0.55:s={fw}x{fh},format=rgba,pad=iw+{border * 8}:ih+{border * 8}:{border * 4}:{border * 4}"
            f":color=black@0,gblur=sigma={short * 0.012:.1f}[{out}s];"
            f"[{bg}a][{out}s]overlay=x=(W-w)/2+{dx}:y=(H-h)/2+{dy}[{out}b];"
            f"[{clip}]pad=iw+{2 * border}:ih+{2 * border}:{border}:{border}:color=0xFBF8F1[{out}p];"
            f"[{out}b][{out}p]overlay=x=(W-w)/2:y=(H-h)/2,format=yuv420p[{out}];[{bg}b]nullsink")
