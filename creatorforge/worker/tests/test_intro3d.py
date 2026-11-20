"""The Blender 3D intro: refuses cleanly without Blender, renders a real clip when bpy is available."""
import os
import subprocess
from pathlib import Path

import pytest

from creatorforge_worker.media import intro3d
from creatorforge_worker.media.ff import MediaError


def test_no_name_or_no_blender_is_a_clean_error(tmp_path, monkeypatch):
    with pytest.raises(MediaError):
        intro3d.render("   ", tmp_path / "x.mp4")
    monkeypatch.setenv("CF_BLENDER_PYTHON", "/nope/python")
    monkeypatch.setattr(intro3d.shutil, "which", lambda _: None)
    monkeypatch.setattr(intro3d.Path, "is_file", lambda self: False)
    with pytest.raises(MediaError, match="Blender is not installed"):
        intro3d._runner()


@pytest.mark.skipif(not os.environ.get("CF_BLENDER_PYTHON"), reason="no Blender Python (CF_BLENDER_PYTHON) here")
def test_renders_an_intro_clip(tmp_path: Path):
    out = intro3d.render("Print Facts", tmp_path / "i.mp4", "Sach", width=320, height=180, fps=8, seconds=1.0)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                       capture_output=True, text=True).stdout
    assert abs(float(d) - 1.0) < 0.15
