"""Closing the gap: hand-drawn ink (perfect-freehand + Rough.js), the myth scene, title entrances, reading holds,
Freesound effects, Demucs stems, the ACE-Step composer and BS.1770 loudness. Services and models are stood in for."""
import json
import subprocess
import urllib.parse
from pathlib import Path

import pytest

from creatorforge_worker import vox_director
from creatorforge_worker.media import motion, quality, stems, vox
from creatorforge_worker.providers import freesound
from creatorforge_worker.studio import score, writer
from creatorforge_worker.studio.dossier import Dossier


def _tone(path: Path, secs=3.0, freq=440, vol="0.3"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={secs}", "-af",
                    f"volume={vol}", "-ac", "2", "-ar", "48000", str(path)], check=True)
    return path


def test_hand_drawn_library_is_bundled_and_loaded():
    hand = Path(vox.__file__).parent / "vendor" / "hand.js"
    js = hand.read_text(encoding="utf-8")
    assert "window.rough=rough" in js and "window.PF=exports" in js and "getStroke" in js
    assert (hand.parent / "ROUGHJS_LICENSE.txt").is_file() and (hand.parent / "PERFECT_FREEHAND_LICENSE.txt").is_file()


def test_myth_lines_parse_and_are_valid():
    p = vox.plan_for("myth", "Smart people don't fall for scams | Intelligence is not armour | BUSTED")
    assert p["type"] == "myth" and p["wrong"].startswith("Smart") and p["label"] == "BUSTED"
    assert vox.plan_for("myth", "only one side") is None
    assert vox_director.valid("Myth: Smart people don't fall for scams | Intelligence is not armour") == ""


def test_myth_and_marker_render_with_ink(tmp_path):
    if not motion.enabled():
        return
    out = vox.render("myth", "Smart people don't fall for scams | Intelligence is not armour", "e~0@red/field/", 480, 270, 3.5,
                     tmp_path / "m.mp4", tmp_path / "w", fetch=False, fps=8)
    assert out.stat().st_size > 3000

    def frame(t):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        import numpy as np
        return np.frombuffer(raw, np.uint8).reshape(270, 480, 3).astype(int)
    a, b = frame(0.6), frame(2.6)
    red = lambda f: ((f[..., 0] > 150) & (f[..., 1] < 110) & (f[..., 2] < 110)).sum()
    assert red(b) > red(a) + 200                       # the marker strike and the stamp have been drawn in


def test_reading_hold_warning():
    d = Dossier(topic="t", claims={})
    sp = {"engine": "trojan-horse", "concept": {"logline": "x", "central_question": "y"},
          "scenes": [{"id": "S1", "act": "hook", "narration": "Why?",
                      "graphic": "Myth: smart people never fall for phone scams at all | intelligence is not armour against a calm voice"},
                     {"id": "S2", "act": "ending", "narration": "Hang up and call back on the number you trust.", "graphic": "Statement: Hang *up*"}]}
    warns = [p["problem"] for p in writer.check(sp, d)]
    assert any("on-screen words need" in w for w in warns)


def test_freesound_takes_only_commercial_licences(tmp_path, monkeypatch):
    calls = []

    def fake(url):
        calls.append(url)
        if "apiv2/search" in url:
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            assert 'license:("Creative Commons 0" OR "Attribution")' in q["filter"][0]
            return json.dumps({"results": [
                {"id": 1, "name": "swoosh", "license": "http://creativecommons.org/publicdomain/zero/1.0/", "username": "a",
                 "url": "https://freesound.org/s/1/", "previews": {"preview-hq-mp3": "https://cdn.freesound.org/1.mp3"}},
                {"id": 2, "name": "nc", "license": "http://creativecommons.org/licenses/by-nc/4.0/", "username": "b",
                 "url": "https://freesound.org/s/2/", "previews": {"preview-hq-mp3": "https://cdn.freesound.org/2.mp3"}},
                {"id": 3, "name": "stamp", "license": "https://creativecommons.org/licenses/by/4.0/", "username": "c",
                 "url": "https://freesound.org/s/3/", "previews": {"preview-hq-mp3": "https://cdn.freesound.org/3.mp3"}}]}).encode()
        return b"ID3fake"
    monkeypatch.setattr(freesound, "HTTP", fake)
    res = freesound.fill_bank(tmp_path / "fs", "k", per_role=2)
    files = sorted(p.name for p in (tmp_path / "fs").glob("*.mp3"))
    assert res["added"] == len(files) and not any("fs2" in f for f in files) and "whoosh_fs1.mp3" in files
    cred = (tmp_path / "fs" / "CREDITS.txt").read_text()
    assert "stamp" in cred and "swoosh" not in cred             # CC-BY is credited; CC0 needs no credit
    monkeypatch.delenv("FREESOUND_KEY", raising=False)
    monkeypatch.delenv("CF_FREESOUND_KEY", raising=False)
    assert freesound.fill_bank(tmp_path / "x", "")["added"] == 0


def test_stems_score_and_loudness(tmp_path, monkeypatch):
    song = _tone(tmp_path / "song.wav", 2.0)
    assert stems.instrumental(song, tmp_path)[0] == song or stems.ready()

    def fake_sep(path, out):
        v, nv = out / "v.wav", out / "nv.wav"
        _tone(v, 2.0, 880), _tone(nv, 2.0, 220)
        return {"vocals": v, "no_vocals": nv}
    monkeypatch.setattr(stems, "BACKEND", fake_sep)
    inst, how = stems.instrumental(song, tmp_path / "s")
    assert inst.name == "no_vocals.wav" and "Demucs" in how
    out = score.from_track(song, 5.0, tmp_path / "t")
    assert out.is_file() and "singing removed" in score.LAST_HOW
    made = []

    def fake_ace(prompt, secs, raw):
        made.append(prompt)
        return _tone(raw, secs, 330)
    monkeypatch.setattr(score, "ACE", fake_ace)
    sc = score.compose([("hook", 0.0, 4.0), ("ending", 4.0, 4.0)], "drone", tmp_path / "sc")
    assert sc.is_file() and score.LAST_HOW == "ACE-Step" and len(made) == 2 and "instrumental" in made[0]
    tone = _tone(tmp_path / "l.wav", 3.0)
    lufs = quality.lufs_precise(tone)
    assert lufs is None or abs(lufs - quality.loudness(tone)["lufs"]) < 1.5     # two independent meters agree
