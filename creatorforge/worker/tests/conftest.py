import shutil
import subprocess
import time
from pathlib import Path

import pytest

from creatorforge_worker.config import Config, VoiceProfile


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    music = tmp_path / "music"
    music.mkdir()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=330:sample_rate=44100:duration=6", "-ac", "2", str(music / "epic_cinematic_theme.mp3")],
                   check=True)
    return Config(data_dir=tmp_path / "data", llm_url="mock", image_provider="mock", music_dir=str(music),
                  voices=[VoiceProfile("narrator", "Test narrator", "mock", "")], allow_mock=True)


def wait_for(fn, timeout=240):
    end = time.time() + timeout
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(0.25)
    raise AssertionError("timed out")


def pytest_collection_modifyitems(items):
    if not shutil.which("ffmpeg"):
        skip = pytest.mark.skip(reason="ffmpeg not installed")
        for item in items:
            if "ffmpeg" in item.keywords:
                item.add_marker(skip)
