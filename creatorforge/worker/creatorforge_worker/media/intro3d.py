"""A 3D channel intro made in Blender (free, GPL): the channel name as bevelled 3D letters that swing in out of the
dark, a light sweep across their faces, a slow camera push, then a hold for the logo moment.

Blender runs in its own process, either as the `bpy` Python module (CF_BLENDER_PYTHON=/path/to/python with bpy) or
the `blender` program (`blender -b --python`). Text is Latin script: Blender's text objects do not shape Devanagari.

    python -m creatorforge_worker.media.intro3d "PRINT FACTS" out.mp4 [--tagline "Sach. Sabooton ke saath."]"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .ff import MediaError

BPY_SCRIPT = r'''
import bpy, json, math, sys
a = json.loads(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = a["w"], a["h"]
sc.render.fps = a["fps"]
sc.frame_start, sc.frame_end = 1, a["frames"]
eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in eng else ("BLENDER_EEVEE" if "BLENDER_EEVEE" in eng else "CYCLES")
if sc.render.engine == "CYCLES":
    sc.cycles.samples = 24
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = a["out"] + "/f_"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.012, 0.016, 1)

def mat(name, rgb, metal, rough, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        key = "Emission Color" if "Emission Color" in b.inputs else "Emission"
        b.inputs[key].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m

def text(body, size, y, depth, material):
    bpy.ops.object.text_add(location=(0, y, 0))
    t = bpy.context.object
    t.data.body = body; t.data.size = size; t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
    t.data.extrude = depth; t.data.bevel_depth = depth * 0.25; t.data.bevel_resolution = 3
    if a.get("font"):
        try: t.data.font = bpy.data.fonts.load(a["font"])
        except Exception: pass
    t.rotation_euler = (math.radians(90), 0, 0)
    t.data.materials.append(material)
    return t

accent = tuple(a["accent"])
title = text(a["title"], 1.0, 0, 0.18, mat("face", (0.92, 0.92, 0.94), 0.85, 0.22))
under = None
if a.get("tagline"):
    under = text(a["tagline"], 0.32, 0, 0.04, mat("tag", (0.95, 0.95, 0.96), 0.3, 0.35, 0.4))
    under.location.z = -0.95
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.05, -0.62))
bar = bpy.context.object; bar.scale = (0.001, 0.035, 1)
bar.data.materials.append(mat("bar", accent, 0.0, 0.5, 0.6))
bar.rotation_euler = (math.radians(90), 0, 0)

F = a["frames"]; fin = int(F * 0.45)
# letters swing up from flat and below, then settle
title.rotation_euler = (math.radians(0), 0, math.radians(-25)); title.location.z = -1.4
title.keyframe_insert("rotation_euler", frame=1); title.keyframe_insert("location", frame=1)
title.rotation_euler = (math.radians(90), 0, 0); title.location.z = 0.15
title.keyframe_insert("rotation_euler", frame=fin); title.keyframe_insert("location", frame=fin)
bar.keyframe_insert("scale", frame=int(F * 0.4))
bar.scale = (title.dimensions.x * 0.9 + 0.3, 0.035, 1)
bar.keyframe_insert("scale", frame=int(F * 0.62))
if under:
    under.scale = (0.001, 0.001, 0.001); under.keyframe_insert("scale", frame=int(F * 0.55))
    under.scale = (1, 1, 1); under.keyframe_insert("scale", frame=int(F * 0.72))

cam_data = bpy.data.cameras.new("cam"); cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_euler = (math.radians(90), 0, 0)
cam.location = (0, -9.5, 0); cam.keyframe_insert("location", frame=1)
cam.location = (0, -7.6, 0.05); cam.keyframe_insert("location", frame=F)
fit = max(title.dimensions.x / 6.2, 1.0)
cam_data.lens = 50 / fit

def light(name, kind, loc, energy, rgb=(1, 1, 1), size=1.0):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = rgb
    if hasattr(d, "size"): d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc; sc.collection.objects.link(o); return o
light("key", "AREA", (-4, -5, 4), 900, size=4).rotation_euler = (math.radians(55), 0, math.radians(-35))
light("rim", "AREA", (4, 3, 2), 600, accent, 3).rotation_euler = (math.radians(-60), 0, math.radians(150))
sweep = light("sweep", "AREA", (-8, -3, 1.5), 1600, size=1.2)
sweep.rotation_euler = (math.radians(90), 0, 0)
sweep.keyframe_insert("location", frame=int(F * 0.45))
sweep.location.x = 8; sweep.keyframe_insert("location", frame=int(F * 0.85))
for ob in (title, bar, cam, sweep) + ((under,) if under else ()):
    if ob.animation_data and ob.animation_data.action:
        try:
            for fc in ob.animation_data.action.fcurves:
                for k in fc.keyframe_points: k.interpolation = "BEZIER"; k.easing = "EASE_OUT"
        except Exception:
            pass
bpy.ops.render.render(animation=True)
'''


def _runner() -> list[str]:
    for py in (os.environ.get("CF_BLENDER_PYTHON", ""), "/workspace/bpy/bin/python"):
        if py and Path(py).is_file():
            return [py, "-"]
    exe = shutil.which("blender")
    if exe:
        return [exe, "-b", "--python-exit-code", "1", "--python"]
    raise MediaError("Blender is not installed (install it, or set CF_BLENDER_PYTHON to a Python that has bpy)")


def render(title: str, out: Path, tagline: str = "", accent=(0.78, 0.06, 0.18), width: int = 1920,
           height: int = 1080, fps: int = 30, seconds: float = 3.0, font: str | None = None,
           timeout: float = 3600) -> Path:
    title = " ".join(title.split())[:28].upper()
    if not title:
        raise MediaError("intro: no channel name")
    frames = max(12, int(round(seconds * fps)))
    with tempfile.TemporaryDirectory(prefix="cf_intro3d_") as tmp:
        args = json.dumps({"title": title, "tagline": " ".join(tagline.split())[:48], "accent": list(accent),
                           "w": width, "h": height, "fps": fps, "frames": frames, "out": tmp,
                           "font": font or next((p for p in ("/usr/share/fonts/truetype/creatorforge/ArchivoBlack-Regular.ttf",
                                                             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
                                                 if Path(p).is_file()), None)})
        run = _runner()
        script = Path(tmp) / "intro.py"
        script.write_text(BPY_SCRIPT, encoding="utf-8")
        if run[-1] == "-":                            # bpy as a module: run the script with that Python
            cmd = [run[0], str(script), "--", args]
        else:
            cmd = run + [str(script), "--", args]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        pngs = sorted(Path(tmp).glob("f_*.png"))
        if r.returncode != 0 or len(pngs) < frames:
            raise MediaError(f"intro: Blender rendered {len(pngs)}/{frames} frames: {(r.stderr or r.stdout)[-400:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                        str(Path(tmp) / "f_%04d.png"), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-movflags", "+faststart", str(out)], check=True)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("out")
    ap.add_argument("--tagline", default="")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--seconds", type=float, default=3.0)
    ns = ap.parse_args()
    w, h = (int(x) for x in ns.size.lower().split("x"))
    print(render(ns.title, Path(ns.out), ns.tagline, width=w, height=h, seconds=ns.seconds))
