"""The SVG.js motion-graphics engine: what it draws from each script line, and a real render when Chromium is here."""
import subprocess
from pathlib import Path

import pytest

from creatorforge_worker.media import motion


def test_plans_from_script_lines():
    assert motion.plan_for("chart", "₹29.7 करोड़ | 30 दिन")["type"] == "counter"
    bars = motion.plan_for("chart", "28% vs 21% | BJP pages, Congress pages")
    assert bars["type"] == "bars" and bars["values"] == [28.0, 21.0]
    line = motion.plan_for("chart", "2021-22 176 → 2022-23 163 → 2023-24 157 → 2024-25 140 | deaths")
    assert line["type"] == "line" and line["values"] == [176.0, 163.0, 157.0, 140.0]
    assert line["ticks"] == ["2021-22", "2022-23", "2023-24", "2024-25"]
    tl = motion.plan_for("timeline", "JAN 2023 protest | 21 APR complaint | 28 APR FIR")
    assert [i[0] for i in tl["items"]] == ["JAN 2023", "21 APR", "28 APR"]
    assert motion.plan_for("timeline", "2014 BJP at Centre → 2019 Home Minister | Delhi")["title"] == "Delhi"
    st = motion.plan_for("steps", "A → B → C | how")
    assert st["steps"] == ["A", "B", "C"] and st["title"] == "how"
    assert motion.plan_for("pie", "67% | votes")["value"] == 67.0
    assert motion.plan_for("squares", "13.3 vs 12.3 | a, b")["labels"] == ["a", "b"]
    assert motion.plan_for("steps", "only one") is None and motion.plan_for("pie", "no number") is None


@pytest.mark.skipif(not motion.enabled(), reason="no Playwright/Chromium here")
def test_renders_a_smooth_h264_clip(tmp_path: Path):
    out = motion.render("steps", "Group → Forward → Belief | the loop", "investigative", 640, 360, 2.0,
                        tmp_path / "s.mp4", tmp_path / "w")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height,pix_fmt",
                            "-show_entries", "format=duration", "-of", "default=nw=1", str(out)],
                           capture_output=True, text=True).stdout
    assert "codec_name=h264" in probe and "width=640" in probe and "pix_fmt=yuv420p" in probe
    assert abs(float(probe.split("duration=")[1].split()[0]) - 2.0) < 0.15
