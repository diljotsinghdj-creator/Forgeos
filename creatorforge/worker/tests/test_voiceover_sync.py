import json
import subprocess

from creatorforge_worker import voiceover_sync as V


def _tones(path, spans, total):
    """A 'voice-over': a tone for each spoken span, silence between."""
    expr = "+".join(f"between(t,{a},{b})" for a, b in spans)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=300:d={total}", "-af",
                    f"volume='if({expr},1,0)':eval=frame", str(path)], check=True)


def test_an_outside_voice_over_is_matched_line_for_line(tmp_path):
    lines = ["पहली लाइन थोड़ी लंबी है यहाँ।", "दूसरी छोटी।", "तीसरी लाइन फिर से लंबी होती है।"]
    _tones(tmp_path / "vo.wav", [(0.0, 3.0), (3.6, 4.6), (5.2, 8.6)], 9.0)
    starts, end = V.line_starts_in_audio(tmp_path / "vo.wav", lines)
    assert [round(s, 1) for s in starts] == [0.0, 3.6, 5.2] and abs(end - 9.0) < 0.05
    # CreatorForge's own narration, timed differently: the video is stretched line by line onto the voice-over
    words, t = [], 0.2
    for l in lines:
        for w in l.split():
            words.append({"text": w, "start": t, "end": t + 0.4})
            t += 0.5
        t += 0.6
    assert V.line_starts_in_words(words, lines)[1] == words[len(lines[0].split())]["start"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=s=160x284:r=30:d={t + 0.4:.2f}",
                    "-pix_fmt", "yuv420p", str(tmp_path / "cf.mp4")], check=True)
    info = V.sync(tmp_path / "cf.mp4", words, lines, tmp_path / "vo.wav", tmp_path / "out.mp4", tmp_path / "r.json")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(tmp_path / "out.mp4")], capture_output=True, text=True).stdout)
    assert abs(info["voiceover_seconds"] - 9.0) < 0.1                     # the voice-over sets the length...
    assert abs(dur - info["seconds_after"]) < 0.1 and info["end_card_seconds"] > 0.3   # ...then the end card plays
    assert len(json.loads((tmp_path / "r.json").read_text())["lines"]) == 3
    assert abs(info["lines"][1]["voiceover_start"] - 3.6) < 0.05
