import subprocess

import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app
from creatorforge_worker.media import ff

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg


def client(cfg):
    app = create_app(cfg)
    return TestClient(app), app


def finished(c, job_id):
    def check():
        j = c.get(f"/v1/productions/{job_id}").json()
        return j if j["status"] in ("READY", "FAILED", "CANCELLED") else None
    return wait_for(check)


def test_one_button_production_produces_verified_mp4(cfg):
    c, app = client(cfg)
    with c:
        r = c.post("/v1/productions", json={"idea": "Humanoid robots could change warehouses", "duration_s": 15,
                                            "template": "shorts_cinematic"})
        assert r.status_code == 202
        job = finished(c, r.json()["id"])
        assert job["status"] == "READY", job
        assert all(s["state"] in ("READY", "SKIPPED") for s in job["stages"].values())
        v = job["result"]["verification"]
        assert (v["width"], v["height"]) == (1080, 1920) and v["decode_check"] == "passed"
        assert job["providers"]["music"] == "epic_cinematic_theme.mp3"
        assert job["providers"]["captions"].startswith("estimated")
        video = c.get(job["result"]["video_url"])
        assert video.status_code == 200 and video.content[4:8] == b"ftyp"
        path = app.state.store.dir(job["id"]) / "creatorforge.mp4"
        info = ff.probe(path)
        assert {s["codec_type"] for s in info["streams"]} == {"video", "audio"}
        # audio is not silent: narration + music were mixed in
        vol = subprocess.run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        assert "mean_volume: -91" not in vol


def test_square_output_and_scene_regeneration_reuses_other_assets(cfg):
    c, app = client(cfg)
    with c:
        jid = c.post("/v1/productions", json={"idea": "Three tips for better sleep", "duration_s": 12,
                                              "template": "square_social", "music": False}).json()["id"]
        job = finished(c, jid)
        assert job["status"] == "READY", job
        assert job["result"]["verification"]["width"] == 1080 == job["result"]["verification"]["height"]
        before = [s["image"] for s in job["scenes"]]
        cache_files = len(list((cfg.cache_dir / "images").iterdir()))
        assert c.post(f"/v1/productions/{jid}/scenes/1/regenerate").status_code == 200
        job = finished(c, jid)
        assert job["status"] == "READY", job
        assert [s["image"] for s in job["scenes"]] == before  # same filenames, scene 2 re-rendered
        assert len(list((cfg.cache_dir / "images").iterdir())) == cache_files + 1  # only one new image generated
        assert job["stages"]["narration"]["state"] == "READY"


def test_failure_is_reported_and_retry_resumes(cfg):
    cfg.image_provider = "a1111"
    cfg.image_url = "http://127.0.0.1:9"  # nothing listens here
    c, app = client(cfg)
    with c:
        jid = c.post("/v1/productions", json={"idea": "Why the ocean is salty", "duration_s": 12}).json()["id"]
        job = finished(c, jid)
        assert job["status"] == "FAILED"
        assert job["stages"]["director"]["state"] == "READY"
        assert job["stages"]["images"]["state"] == "FAILED"
        assert all(s["image_state"] == "FAILED" for s in job["scenes"])
        assert job["result"] is None
        assert c.get(f"/v1/productions/{jid}/video").status_code == 409
        plan = job["plan"]
        cfg.image_provider = "mock"
        c.post(f"/v1/productions/{jid}/retry")
        job = finished(c, jid)
        assert job["status"] == "READY", job
        assert job["plan"] == plan  # director was not re-run


def test_cancel_keeps_project_and_auth(cfg):
    cfg.token = "s3cret-token"
    c, app = client(cfg)
    with c:
        assert c.post("/v1/productions", json={"idea": "Unauthorized idea"}).status_code == 401
        h = {"Authorization": "Bearer s3cret-token"}
        jid = c.post("/v1/productions", headers=h, json={"idea": "A long video about bridges",
                                                        "duration_s": 120}).json()["id"]
        wait_for(lambda: c.get(f"/v1/productions/{jid}", headers=h).json()["stages"]["images"]["state"] == "RUNNING")
        c.delete(f"/v1/productions/{jid}", headers=h)
        job = finished_auth(c, jid, h)
        assert job["status"] == "CANCELLED"
        assert job["plan"] is not None


def finished_auth(c, jid, h):
    return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED", "CANCELLED") else None)(
        c.get(f"/v1/productions/{jid}", headers=h).json()))


def test_mock_refused_without_flag(cfg):
    cfg.allow_mock = False
    c, _ = client(cfg)
    with c:
        h = c.get("/health").json()
        assert h["production_ready"] is False
        assert "CF_ALLOW_MOCK" in h["providers"]["llm"]["error"]


def test_legacy_endpoints(cfg):
    c, _ = client(cfg)
    with c:
        assert c.post("/v1/images/generate", json={"prompt": "a cat", "aspect_ratio": "16:9"}).content[:4] == b"\x89PNG"
        assert c.post("/v1/voice/generate", json={"text": "hello there", "format": "wav"}).content[:4] == b"RIFF"
        assert c.post("/v1/video/jobs", json={}).status_code == 501
