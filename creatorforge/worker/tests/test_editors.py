"""Shotcut (MLT) and OpenShot (EDL) projects in the export: the cut in order, and a real render through MLT's melt."""
import shutil
import subprocess
from pathlib import Path

import pytest

from creatorforge_worker import editors

CUT = [{"file": "media/01_scene.png", "seconds": 2.5, "image": True},
       {"file": "media/02_scene.mp4", "seconds": 3.0, "image": False},
       {"file": "", "seconds": 1.0},                                  # a scene with no media is left out
       {"file": "media/03_scene.png", "seconds": 2.5, "image": True}]


def test_mlt_and_edl_hold_the_cut():
    x = editors.mlt("Ek <Kursi> & sawal", CUT, "audio/voiceover.wav", "audio/music.mp3", 1080, 1920)
    assert 'width="1080" height="1920"' in x and 'display_aspect_num="9"' in x
    assert x.index("01_scene.png") < x.index("02_scene.mp4") < x.index("03_scene.png")
    assert 'out="239"' in x                                        # 8 s at 30 fps on the tractor
    assert '<property name="level">-18</property>' in x and "&lt;Kursi&gt; &amp;" in x
    e = editors.edl("t", CUT, "audio/voiceover.wav")
    assert e.count("* FROM CLIP NAME: media/") == 3 and "00:00:02:15 00:00:05:15" in e
    assert "* FROM CLIP NAME: audio/voiceover.wav" in e


@pytest.mark.skipif(not shutil.which("melt"), reason="MLT's melt is not installed")
def test_shotcut_project_renders_in_mlt(tmp_path: Path):
    def run(*a):
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *a], check=True)
    (tmp_path / "media").mkdir()
    (tmp_path / "audio").mkdir()
    run("-f", "lavfi", "-i", "color=red:s=320x180", "-frames:v", "1", str(tmp_path / "media/01_scene.png"))
    run("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=3", "-pix_fmt", "yuv420p", str(tmp_path / "media/02_scene.mp4"))
    run("-f", "lavfi", "-i", "color=blue:s=320x180", "-frames:v", "1", str(tmp_path / "media/03_scene.png"))
    run("-f", "lavfi", "-i", "sine=d=8", str(tmp_path / "audio/voiceover.wav"))
    (tmp_path / "p.mlt").write_text(editors.mlt("t", CUT, "audio/voiceover.wav", None, 320, 180))
    out = tmp_path / "o.mp4"
    subprocess.run(["melt", str(tmp_path / "p.mlt"), "-consumer", f"avformat:{out}", "vcodec=libx264", "acodec=aac",
                    "-quiet"], check=True, cwd="/", timeout=300)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(out)], capture_output=True, text=True).stdout)
    assert abs(dur - 8.0) < 0.2
