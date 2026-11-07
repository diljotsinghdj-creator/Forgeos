"""3D camera moves from a depth map, and AI clips interpolated up to 60 fps."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from creatorforge_worker.media import depth3d, interp


def _probe(p: Path, entry: str) -> str:
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry, "-of",
                           "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()


def test_near_things_move_more_than_far_things(tmp_path: Path):
    img = np.zeros((180, 320, 3), np.uint8)
    img[:, :, 2] = 120
    img[70:110, 140:180] = 255                                  # a white square in the middle: the near subject
    Image.fromarray(img).save(tmp_path / "p.png")
    depth = np.zeros((180, 320), np.float32)
    depth[50:130, 120:200] = 1.0
    out = depth3d.render(tmp_path / "p.png", depth, 1.0, tmp_path / "m.mp4", 320, 180, fps=10, move="right")
    assert _probe(out, "stream=width,height") == "320,180"
    for name, at in (("a", ["-ss", "0"]), ("b", ["-sseof", "-0.15"])):
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *at, "-i", str(out), "-frames:v", "1",
                        str(tmp_path / f"{name}.png")], check=True)
    first, last = (np.asarray(Image.open(tmp_path / f"{n}.png")) for n in ("a", "b"))
    white = lambda f: (f.sum(axis=2) > 600).sum()               # noqa: E731
    assert white(last) > white(first) * 1.05                    # the near square grew as the camera moved in


def test_slow_clips_are_interpolated_only_at_60fps(tmp_path: Path):
    clip = tmp_path / "ai.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=160x90:r=16:d=1",
                    "-pix_fmt", "yuv420p", str(clip)], check=True)
    assert interp.smooth(clip, 30, tmp_path) == clip
    out = interp.smooth(clip, 60, tmp_path)
    assert out != clip and abs(interp.fps_of(out) - 60) < 0.5
