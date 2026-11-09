"""Motivated transitions, freeze frame, speed ramp and slow motion."""
import subprocess
import threading

from creatorforge_worker import pipeline
from creatorforge_worker.media import ff, render


def _clip(path, colour, seconds=3):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=270x480:rate=30,hue=h={colour}", "-t", str(seconds),
                    "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def test_the_cut_comes_from_what_the_two_shots_are():
    m = pipeline.motivated_transition
    assert m("pinmap", "bignumber") == "dive"          # out of a map: dive into the place
    assert m("globe", "") == "dive"                    # map to footage
    assert m("route", "heatmap") == "blur"             # map to map: a blur pan
    assert m("hero", "courtdoc") == "page" and m("", "newscard") == "page"
    assert m("stack", "trend") == "push" and m("compare", "hero") == "squeeze"
    assert m("hero", "table") == "drop" and m("", "") == ""
    assert pipeline.beat_kind({"extra": {"heatmap": "x"}}) == "heatmap" and pipeline.beat_kind({"chart": "1 vs 2"}) == "chart"
    assert all(render.TRANSITIONS[k][0] for k in ("dive", "page", "push", "drop", "squeeze"))


def test_freeze_ramp_and_slow_motion_render(tmp_path):
    a, b = _clip(tmp_path / "a.mp4", 0, 4), _clip(tmp_path / "b.mp4", 120, 4)
    still = tmp_path / "s.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=270x480", "-frames:v", "1", str(still)], check=True)
    audio = tmp_path / "a.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=9", "-ar", "48000", str(audio)], check=True)
    clips = [render.Clip(still, 2.0, "static", "cut", a, 4.0, playback="freeze"),
             render.Clip(still, 2.0, "static", "dive", b, 4.0, playback="ramp"),
             render.Clip(still, 2.0, "static", "page", a, 4.0, playback="slow"),
             render.Clip(still, 1.5, "static", "squeeze", b, 4.0)]
    out = tmp_path / "o.mp4"
    total = render.render_video(clips, audio, None, 270, 480, out, tmp_path / "work", threading.Event(), grade="")
    assert out.is_file() and abs(ff.duration(out) - total) < 0.4

    def frame(t):
        return subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", str(out), "-frames:v", "1", "-vf", "scale=32:32",
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    # the freeze: two frames late in the first shot are the same picture; two early ones are not
    diff = lambda x, y: sum(abs(p - q) for p, q in zip(x, y)) / len(x)     # noqa: E731
    assert diff(frame(1.5), frame(1.8)) < 2.0 < diff(frame(0.3), frame(0.6))


def test_ambient_beds_follow_the_shot(tmp_path):
    from creatorforge_worker.media import ambience
    assert ambience.bed_for("route", "Shanghai → Rotterdam | x | ship") == "sea"
    assert ambience.bed_for("pinmap", "Kota") == "wind" and ambience.bed_for("courtdoc") == "paper"
    assert ambience.bed_for("hero", "", archive=True) == "projector" and ambience.bed_for("stack") == ""
    beds = ambience.place(tmp_path, [(0.0, 3.0, "route", "A → B | t | ship", False), (3.0, 2.0, "route", "B → C | t | ship", False),
                                     (5.0, 2.5, "stack", "", False), (7.5, 3.0, "courtdoc", "", False)])
    assert len(beds) == 2                                   # the two sea shots share one bed; the chart has none
    assert beds[0][0].name.startswith("sea_") and abs(ff.duration(beds[0][0]) - 5.0) < 0.3 and beds[0][2] < 0.2
    assert beds[1][0].name.startswith("paper_") and 7.3 < beds[1][1] < 7.6
