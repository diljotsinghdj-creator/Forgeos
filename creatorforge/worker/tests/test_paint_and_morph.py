"""p5.brush painted maps (vox Wash) and the shape-morph cut (render 'morph')."""
import json
import threading
import wave
from pathlib import Path

from PIL import Image, ImageDraw

from creatorforge_worker.media import motion, render, vox


def test_wash_parses_states_and_countries():
    p = vox.parse_wash("Bihar, Jharkhand | hi: Bihar | East India")
    assert [s["name"] for s in p["shapes"]] == ["Bihar", "Jharkhand"] and p["hi"] == "Bihar" and p["context"]
    c = vox.parse_wash("India, Nepal | hi: Nepal | South Asia")
    assert {s["name"] for s in c["shapes"]} == {"India", "Nepal"} and not c["context"]
    assert vox.parse_wash("Nowhere-land | x") is None


def test_wash_paints_with_p5brush(tmp_path):
    if not motion.enabled():
        return
    out = vox.render("wash", "Bihar, Jharkhand, West Bengal | hi: Bihar | East India", "editorial~0@#2D6BDB/field/",
                     960, 540, 2.5, tmp_path / "w.mp4", tmp_path / "work", fps=6)
    page = (tmp_path / "work" / "vox_w.html").read_text()
    assert "window.PB=window.brush" in page                      # the library is on the page, under its own name
    qa = json.loads(Path(str(out).replace(".mp4", ".qa.json")).read_text())
    assert not qa["text_overlap"] and not qa["text_cut_off"]
    import subprocess
    png = tmp_path / "f.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.0", "-i", str(out), "-frames:v", "1", str(png)], check=True)
    im = Image.open(png).convert("RGB").resize((96, 54))
    yellowish = sum(1 for r, g, b in im.getdata() if r > 170 and g > 150 and b < 120)
    assert yellowish > 20                                        # the highlighted state is painted in the signature yellow


def test_morph_cut_draws_a_yellow_shape_between_two_shots(tmp_path):
    a = Image.new("RGB", (320, 180), "#ECE8DF"); ImageDraw.Draw(a).ellipse([110, 40, 210, 140], fill="#1F4FB8"); a.save(tmp_path / "a.png")
    b = Image.new("RGB", (320, 180), "#ECE8DF"); ImageDraw.Draw(b).rectangle([60, 70, 260, 120], fill="#D7262B"); b.save(tmp_path / "b.png")
    with wave.open(str(tmp_path / "s.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(b"\0\0" * 48000 * 4)
    clips = [render.Clip(tmp_path / "a.png", 1.5, "static", "cut"), render.Clip(tmp_path / "b.png", 1.5, "static", "morph")]
    render.render_video(clips, tmp_path / "s.wav", None, 320, 180, tmp_path / "o.mp4", tmp_path / "w", threading.Event(), grade="")
    assert clips[1].morph is not None and len(list(clips[1].morph.glob("m_*.png"))) >= 10
    import subprocess
    png = tmp_path / "mid.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.75", "-i", str(tmp_path / "o.mp4"), "-frames:v", "1", str(png)], check=True)
    px = Image.open(png).convert("RGB").getpixel((160, 95))
    assert px[0] > 200 and px[1] > 180 and px[2] < 120, px       # the middle of the cut is the yellow morphing shape
