"""Long films are assembled a batch of shots at a time (memory and time stay bounded), then joined."""
import threading

import pytest
from PIL import Image

from creatorforge_worker.media import ff, render

pytestmark = pytest.mark.ffmpeg


def test_long_film_is_assembled_in_pieces_with_captions_on_film_time(tmp_path, monkeypatch):
    for k, colour in enumerate(["red", "green", "blue"]):
        Image.new("RGB", (320, 240), colour).save(tmp_path / f"{k}.png")
    ff.run(["-f", "lavfi", "-i", "sine=f=220:d=9", "-ar", "48000", str(tmp_path / "a.wav")])
    # a caption late in the film: it must land in the third piece, at its film time
    work = tmp_path / "w"
    work.mkdir()
    (work / "c.ass").write_text(  # the pipeline keeps captions in the work folder
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 270\nPlayResY: 480\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,60,&H0000FFFF,&H0000FFFF,&H00000000,&H00000000,1,0,0,0,"
        "100,100,0,0,3,40,0,5,10,10,10,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\nDialogue: 0,0:00:07.00,0:00:08.00,Default,,0,0,0,,XXXXXXXX\n")
    transitions = ["cut", "fade", "tear", "fade", "cut", "fade", "match", "fade"]
    clips = [render.Clip(tmp_path / f"{i % 3}.png", 1.0, "slow push in", t) for i, t in enumerate(transitions)]
    monkeypatch.setattr(render, "CHUNK_SHOTS", 3)
    out = tmp_path / "long.mp4"
    total = render.render_video(clips, tmp_path / "a.wav", work / "c.ass", 270, 480, out, work, threading.Event())
    assert total == pytest.approx(8.5)
    assert sorted(p.name for p in work.glob("part_*.mp4")) == ["part_000.mp4", "part_001.mp4", "part_002.mp4"]
    assert ff.duration(out) == pytest.approx(8.5, abs=0.15)
    info = ff.probe(out)
    assert {s["codec_type"] for s in info["streams"]} == {"video", "audio"}
    # the caption (a big yellow box) shows at 7.5 s and not at 2.5 s
    def yellow(t):
        ff.run(["-ss", str(t), "-i", str(out), "-frames:v", "1", str(tmp_path / f"f{t}.png")])
        im = Image.open(tmp_path / f"f{t}.png").convert("RGB")
        return sum(1 for p in im.getdata() if p[0] > 200 and p[1] > 200 and p[2] < 80)
    assert yellow(7.5) > 500 and yellow(2.5) < 50
