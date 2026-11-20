"""Clip: lines put the creator's own Asset Library clips on exactly the line they're written under."""
import subprocess

from creatorforge_worker import director
from creatorforge_worker.pipeline import Pipeline, clip_ref, find_asset
from creatorforge_worker.store import STAGES, JobStore


def test_a_clip_line_belongs_to_its_spoken_line():
    spoken, meta = director.parse_script(
        "Title\n\nDelhi's streets filled on the tenth.\nVisual: A wide Delhi avenue\nClip: delhi march @ 0:12\n\n"
        "Then the court stepped in.\nVisual: The Supreme Court of India\n\nSo who answers?\nVisual: Parliament at dusk\n")
    assert "Clip" not in spoken and "delhi march" not in spoken
    shots = {s[0].split()[0]: s for s in meta["shots"]}
    assert shots["Delhi's"][7]["clip"] == "delhi march @ 0:12"
    assert not shots["Then"][7].get("clip")


def test_clip_names_and_start_times():
    assert clip_ref("delhi march @ 1:05") == ("delhi march", 65.0)
    assert clip_ref("delhi march @ 12s") == ("delhi march", 12.0)
    assert clip_ref("Delhi March.mp4") == ("Delhi March.mp4", 0.0)
    assets = [{"id": "a", "name": "Delhi March.mp4"}, {"id": "b", "name": "court steps 2026"},
              {"id": "c", "name": "court steps night"}]
    assert find_asset(assets, "delhi march")["id"] == "a"
    assert find_asset(assets, "DELHI_MARCH.MOV")["id"] == "a"
    assert find_asset(assets, "court steps 2026")["id"] == "b"
    assert find_asset(assets, "court steps") is None          # two match: ambiguous, so not guessed
    assert find_asset(assets, "parliament") is None


def test_own_clips_are_cut_onto_their_lines_and_missing_ones_reported(cfg, tmp_path):
    pipe = Pipeline(cfg, JobStore(cfg.jobs_dir))
    src = tmp_path / "march.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=4",
                    "-f", "lavfi", "-i", "sine=duration=4", "-shortest", str(src)], check=True)
    pipe.library.assets.add("video", "Delhi March.mp4", src, ".mp4", lambda p: {"duration_s": 4.0})
    job = {"id": "own1", "status": "RUNNING", "stages": {k: {"state": "PENDING"} for k in STAGES}, "providers": {}, "spec": {"idea": "t", "aspect": "16:9"},
           "scenes": [{"index": 0}],
           "plan": {"scenes": [{"beats": [{"text": "Streets filled.", "extra": {"clip": "delhi march @ 1"}},
                                          {"text": "Then silence.", "extra": {}},
                                          {"text": "And more.", "extra": {"clip": "no such clip"}}]}]}}
    pipe.store.dir(job["id"]).mkdir(parents=True, exist_ok=True)
    pipe._asset_clips(job, pipe.store.dir(job["id"]))
    clips = job["scenes"][0]["beat_clips"]
    assert clips[0] and clips[1] is None and clips[2] is None
    out = pipe.store.dir(job["id"]) / clips[0]
    streams = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(out)],
                             capture_output=True, text=True, check=True).stdout.split()
    assert streams == ["video"]                                # the clip's own sound is removed
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True, check=True).stdout)
    assert 2.5 < dur < 3.5                                     # started 1 s in
    assert any("no such clip" in w for w in job["warnings"])
    assert job["providers"]["clips_own"] == "1 of your own clip"


def test_a_script_with_a_clip_line_renders_end_to_end(cfg, tmp_path):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    src = tmp_path / "march.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=6",
                    str(src)], check=True)
    script = ("Who Answers\n\nDelhi's streets filled with marchers on the tenth.\nVisual: A wide Delhi avenue at dawn\n"
              "Clip: delhi march @ 0:01\n\nThen the Supreme Court stepped in that weekend.\n"
              "Visual: The Supreme Court of India at dusk\n\nSo who answers when power is questioned?\n"
              "Visual: Parliament House at dusk\n")
    with TestClient(create_app(cfg)) as c:
        r = c.post("/v1/library/assets?kind=video&name=Delhi%20March.mp4", content=src.read_bytes(),
                   headers={"Content-Type": "application/octet-stream"})
        assert r.status_code == 201, r.text
        jid = c.post("/v1/productions", json={"idea": script, "duration_s": 15}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        own = [n for s in job["scenes"] for n in (s.get("beat_clips") or []) if n and "_clip" in n]
        assert len(own) == 1 and (cfg.jobs_dir / jid / own[0]).is_file()
        assert job["providers"]["clips_own"] == "1 of your own clip"
        assert not job.get("warnings")


def test_an_own_image_plays_on_its_clip_line(cfg, tmp_path):
    from PIL import Image
    pipe = Pipeline(cfg, JobStore(cfg.jobs_dir))
    src = tmp_path / "04_mansion.png"
    Image.new("RGB", (1100, 736), (90, 120, 160)).save(src)
    pipe.library.assets.add("image", "04_mansion.png", src, ".png", lambda p: {})
    job = {"id": "own2", "status": "RUNNING", "stages": {k: {"state": "PENDING"} for k in STAGES}, "providers": {},
           "spec": {"idea": "a mansion story", "aspect": "16:9"}, "scenes": [{"index": 0}],
           "plan": {"scenes": [{"beats": [{"text": "A mansion.", "extra": {"clip": "04 mansion"}}]}]}}
    pipe.store.dir(job["id"]).mkdir(parents=True, exist_ok=True)
    pipe._asset_clips(job, pipe.store.dir(job["id"]))
    clip = job["scenes"][0]["beat_clips"][0]
    assert clip and clip.endswith("_img.mp4") and not job.get("warnings")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(pipe.store.dir(job["id"]) / clip)], capture_output=True, text=True, check=True).stdout)
    assert dur > 10
