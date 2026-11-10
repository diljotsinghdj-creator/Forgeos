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


def test_counter_staircase_scale_parse_validate_and_render(tmp_path):
    c = vox.plan_for("counter", "£0 → £450m | lost to bank-transfer scams | one year")
    assert c["from"] == 0 and c["to"] == 450 and c["pre"] == "£" and c["post"] == "m"
    assert vox.plan_for("counter", "0 → 1,250,000 | people")["comma"] is True
    assert vox.plan_for("staircase", "only one") is None and len(vox.plan_for("staircase", "a; b; c | t")["steps"]) == 3
    assert vox.plan_for("scale", "a, b | c | d")["left"] == ["a", "b"] and vox.plan_for("scale", "a, b") is None
    for g in ("Counter: 0 → 450 | x", "Staircase: a; b; c | t", "Scale: a, b | c | d"):
        assert vox_director.valid(g) == "", g
    if not motion.enabled():
        return
    for k, sp in (("counter", "£0 → £450m | lost | one year"), ("staircase", "One; Two; Three | Steps"),
                  ("scale", "45 minutes, pride | admitting it | too heavy")):
        out = vox.render(k, sp, "e~0@red/field/", 480, 270, 4.0, tmp_path / f"{k}.mp4", tmp_path / "w", fetch=False, fps=8)
        assert out.stat().st_size > 3000
        qa = json.loads(out.with_suffix(".qa.json").read_text())
        assert qa["text_cut_off"] == [] and qa["text_below_floor"] == [], (k, qa)


def test_sound_effects_land_one_frame_after_the_picture_and_rotate(tmp_path):
    from creatorforge_worker.media import sfx
    a, b = tmp_path / "whoosh_a.wav", tmp_path / "whoosh_b.wav"
    for p in (a, b):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono", "-f", "lavfi", "-i",
                        "sine=frequency=500:duration=0.05", "-filter_complex", "[0]atrim=0:0.3[s];[s][1]concat=n=2:v=0:a=1",
                        str(p)], check=True)
    assert 0.25 < sfx.peak(a) < 0.4
    bank = sfx.SfxBank({r: [] for r in sfx.ROLES})
    bank.sounds["whoosh"] = [a, b]
    hits = sfx.place(bank, ["cut", "slide", "slide", "slide"], [2.0, 2.0, 2.0, 2.0], [], "seed")
    assert len(hits) == 3 and all(abs((h[1] + sfx.peak(h[0])) - c) < 0.02 for h, c in zip(hits, (2.0, 4.0, 6.0)))
    assert all(hits[i][0] != hits[i + 1][0] for i in range(len(hits) - 1))       # never the same take twice in a row


def test_selftest_reports_without_failing(tmp_path, monkeypatch, capsys):
    from creatorforge_worker import selftest
    monkeypatch.setenv("CF_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ELEVENLABS_API_KEY", "secret-value-123")
    rows = selftest.local_checks()
    assert {r["status"] for r in rows} <= {"works", "missing", "failed"}
    assert not any("secret-value-123" in json.dumps(r) for r in rows)        # key values are never reported
    assert next(r for r in rows if r["tool"] == "ElevenLabs key")["status"] == "works"


def test_masks_propagate_between_keyframes_and_are_cleaned(tmp_path):
    import numpy as np
    cv2 = pytest.importorskip("cv2")
    from creatorforge_worker.media import track
    frames = []
    for i in range(9):
        im = np.full((120, 160, 3), 40, np.uint8)
        x = 20 + i * 8
        cv2.rectangle(im, (x, 40), (x + 30, 80), (200, 220, 240), -1)
        cv2.circle(im, (x + 10, 50), 4, (10, 10, 10), -1)
        f = tmp_path / f"f_{i:03d}.jpg"
        cv2.imwrite(str(f), im)
        frames.append(f)

    def truth(i):
        z = np.zeros((120, 160), np.uint8)
        z[40:81, 20 + i * 8:51 + i * 8] = 255
        return z
    out = track.propagate(frames, {0: truth(0), 8: truth(8)})
    for i in (2, 4, 6):
        a, b = out[i] > 127, truth(i) > 127
        assert (a & b).sum() / (a | b).sum() > 0.75                 # carried by real optical flow, not guessed
    noisy = truth(4).copy()
    noisy[5:9, 5:9] = 255                                          # a stray speck far from the subject
    c = track.clean(noisy)
    assert c[6, 6] < 40 and c[60, 70] > 200


def test_studio_end_to_end_reel_varies_its_cuts_and_passes_qc(tmp_path):
    """The whole studio on a six-scene test reel (robotic voice, small frame): every step runs, the cuts never repeat
    a plain cut back to back, the text QA is clean and every deliverable is present."""
    if not motion.enabled():
        return
    from creatorforge_worker.studio.produce import PLAIN_CUTS, produce
    data = Path(__file__).parent / "data" / "reel"
    res = produce(data / "screenplay.json", data / "dossier.json", tmp_path / "out", size=(320, 180), fps=12,
                  data_dir=tmp_path / "d", cutdown_size=(180, 320), progress=lambda *a, **k: None)
    assert res["deliverables_missing"] == [] and Path(res["file"]).stat().st_size > 20000
    tl = json.loads((tmp_path / "out" / "timeline" / "timeline.json").read_text())
    cuts = [t["transition_in"] for t in tl]
    assert all(not (a == b and a in PLAIN_CUTS) for a, b in zip(cuts, cuts[1:])), cuts
    assert "every line is at least" in (tmp_path / "out" / "qc" / "report.md").read_text()
