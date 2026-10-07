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
        if "TREND_IDEAS" in system:
            topic = re.search(r"TOPIC:\s*(.+)", user).group(1).strip()
            n = int(re.search(r"COUNT:\s*(\d+)", user).group(1))
            fmt = "long" if "FORMAT: long" in user else "short"
            return json.dumps({"ideas": [{"title": f"{topic}: angle {i + 1}", "hook": f"Nobody is telling you this about {topic}",
                                          "angle": "Explain what happened and why it matters", "format": fmt,
                                          "why_now": "It is trending this week", "seconds": 45 if fmt == "short" else 600}
                                         for i in range(n)]})
        if "TREND_SCRIPT" in system:
            words = int(re.search(r"about (\d+) words", user).group(1))
            idea = re.search(r"IDEA:\s*(.+)", user).group(1).strip()
            body = " ".join(f"Sentence {i + 1} about {idea} keeps the story moving." for i in range(max(2, words // 9)))
            return json.dumps({"title": idea, "script": f"Here is what happened. {body} Follow for more.",
                               "description": f"All about {idea}.", "hashtags": ["#trending", "news"], "facts_used": [1, 2]})
        if "SCENES (narration, final):" in user:
            n = len(re.findall(r"^\d+\. ", user, flags=re.M))
            return json.dumps({"title": "Script video", "hook": "Listen up", "cta": "Follow for more", "music_mood": "tense",
                               "scenes": [{"visual": f"Scene {i + 1} illustration", "shot": "wide", "camera": "slow push in",
                                           "mood": "tense", "overlay": "", "transition": "dissolve", "emphasis": [],
                                           "hold": 0} for i in range(n)]})
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
                "transition": ["whip", "flash", "dissolve", "zoom"][i % 4],
                "emphasis": ["narration"],
                "hold": 0.5 if i == 0 else 0,
                "motion": f"crowd walks past while drone {i + 1} glides overhead",
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

    def generate(self, image: Path, prompt: str, negative: str, seconds: float, width: int, height: int, seed: int,
                 out: Path) -> None:
        self.last_prompt = prompt
        frames = max(2, int(min(seconds, 5.0) * 24))  # real models top out around 5s; assembly stretches to fit
        _ffmpeg(["-i", str(image), "-vf", f"scale={width}:{height},zoompan=z='1+0.002*on':d={frames}:s={width}x{height}:fps=24",
                 "-frames:v", str(frames), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])


class MockMusic:
    id = "mock-music"
    max_seconds = 30.0

    def generate(self, prompt: str, seconds: float, seed: int, out: Path) -> None:
        _ffmpeg(["-f", "lavfi", "-i", f"sine=frequency=196:sample_rate=44100:duration={min(seconds, self.max_seconds):.2f}",
                 "-ac", "2", str(out)])
