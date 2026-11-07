"""Talking mascot: Talk: lines are found, LatentSync is called right, and without it the line keeps its picture."""
from pathlib import Path

import pytest

from creatorforge_worker.media import lipsync
from creatorforge_worker.media.ff import MediaError
from creatorforge_worker.pipeline import _talk_of


def test_talk_lines_are_found_on_the_line_or_its_first_beat():
    assert _talk_of({"extra": {"talk": "Dastango"}}) == "Dastango"
    assert _talk_of({"beats": [{"extra": {"talk": " Marcus "}}, {"extra": {}}]}) == "Marcus"
    assert _talk_of({"beats": [{"extra": {}}, {"extra": {"talk": "late"}}]}) == ""


def test_off_by_default_and_a_clean_error(tmp_path, monkeypatch):
    monkeypatch.delenv("CF_LIPSYNC", raising=False)
    assert not lipsync.available()
    with pytest.raises(MediaError, match="lip-sync not installed"):
        lipsync.talk(tmp_path / "a.png", tmp_path / "a.wav", tmp_path / "o.mp4", 640, 360, 2.0)


def test_latentsync_command():
    cmd = lipsync.command(Path("v.mp4"), Path("a.wav"), Path("o.mp4"))
    assert cmd[1:3] == ["-m", "scripts.inference"] and "--video_path" in cmd and "--audio_path" in cmd
    assert cmd[cmd.index("--inference_ckpt_path") + 1] == "checkpoints/latentsync_unet.pt"


def test_a_still_becomes_a_25fps_clip(tmp_path):
    import subprocess
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i", "color=red:s=200x200",
                    "-frames:v", "1", str(tmp_path / "p.png")], check=True)
    out = lipsync.still_video(tmp_path / "p.png", 1.0, tmp_path / "b.mp4", 160, 160)
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate",
                        "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
    assert r == "25/1"
