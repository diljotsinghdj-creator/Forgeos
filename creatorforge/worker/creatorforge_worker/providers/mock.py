"""TEST-ONLY providers so the full pipeline (including the real FFmpeg render and
verification) can run in CI without models. They are refused unless CF_ALLOW_MOCK=1, and
every production records which providers produced it, so mock output can never be
mistaken for real generation."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .base import ProviderError


def _ffmpeg(args: list[str]) -> None:
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", *args], capture_output=True, timeout=120)
    if p.returncode != 0:
        raise ProviderError(p.stderr.decode(errors="replace")[-300:])


class MockLLM:
    id = "mock-llm"

    def complete_json(self, system: str, user: str) -> str:
        n = int(re.search(r"SCENE_COUNT:\s*(\d+)", user).group(1))
        idea = re.search(r"IDEA:\s*(.+)", user).group(1).strip()
        scenes = [
            {
                "narration": f"Scene {i + 1} narration about {idea[:40]} with enough words to read clearly.",
                "visual": f"Establishing view number {i + 1} illustrating {idea[:40]}",
                "shot": "wide" if i % 2 == 0 else "close-up",
                "camera": "slow push in",
                "mood": "cinematic",
                "overlay": "Key point" if i == 1 else "",
            }
            for i in range(n)
        ]
        return json.dumps({"title": idea[:50], "hook": "Watch this", "cta": "Follow for more",
                           "music_mood": "cinematic", "scenes": scenes})


class MockImage:
    id = "mock-image"

    def generate(self, prompt: str, negative: str, width: int, height: int, seed: int, out: Path) -> None:
        _ffmpeg(["-f", "lavfi", "-i", f"gradients=s={width}x{height}:seed={seed % 100000}",
                 "-frames:v", "1", str(out)])


class MockVoice:
    id = "mock-voice"

    def synthesize(self, text: str, out_wav: Path) -> None:
        seconds = max(1.0, len(text.split()) / 2.6)
        _ffmpeg(["-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=24000:duration={seconds:.2f}",
                 "-ac", "1", str(out_wav)])


class MockVideo:
    id = "mock-video"

    def generate(self, image: Path, prompt: str, seconds: float, width: int, height: int, seed: int, out: Path) -> None:
        frames = max(2, int(seconds * 24))
        _ffmpeg(["-i", str(image), "-vf", f"scale={width}:{height},zoompan=z='1+0.002*on':d={frames}:s={width}x{height}:fps=24",
                 "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
