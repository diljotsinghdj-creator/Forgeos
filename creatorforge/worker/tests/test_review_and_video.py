import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg


def settled(c, jid):
    return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED", "CANCELLED", "REVIEW") else None)(
        c.get(f"/v1/productions/{jid}").json()))


def test_ai_video_clips_are_generated_and_used(cfg):
    cfg.video_provider = "mock"
    with TestClient(create_app(cfg)) as c:
        assert "ai_video" in c.get("/v1/capabilities").json()["motion"]
        jid = c.post("/v1/productions", json={"idea": "Volcanoes explained simply", "duration_s": 12,
                                              "template": "explainer", "motion": "ai_video"}).json()["id"]
        job = settled(c, jid)
        assert job["status"] == "READY", job
        assert job["stages"]["clips"]["state"] == "READY"
        assert all(s["clip_state"] == "READY" and s["clip"].endswith(".mp4") for s in job["scenes"])
        assert job["providers"]["clips"] == "mock-video (3/3 scenes)"
        v = job["result"]["verification"]
        assert (v["width"], v["height"]) == (1920, 1080) and v["decode_check"] == "passed"


def test_ai_video_without_provider_fails_closed(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Volcanoes explained simply", "duration_s": 12,
                                              "motion": "ai_video"}).json()["id"]
        job = settled(c, jid)
        assert job["status"] == "FAILED" and job["stages"]["clips"]["state"] == "FAILED"
        assert "No video model configured" in job["error"]
        assert job["result"] is None


def test_storyboard_review_edit_and_approve(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "How bees make honey", "duration_s": 12, "fast_cuts": False,
                                              "review": True}).json()["id"]
        job = settled(c, jid)
        assert job["status"] == "REVIEW", job
        assert job["stages"]["review"]["state"] == "WAITING"
        assert job["stages"]["narration"]["state"] == "PENDING"  # nothing past the gate ran yet
        assert all(s["image_state"] == "READY" for s in job["scenes"])
        images = [s["image"] for s in job["scenes"]]
        prompts = [s["prompt"] for s in job["plan"]["scenes"]]

        r = c.patch(f"/v1/productions/{jid}/scenes/1", json={"visual": "A honeybee on a sunflower, macro",
                                                             "narration": "Bees visit thousands of flowers."})
        assert r.status_code == 200
        job = r.json()
        assert job["status"] == "REVIEW"
        assert job["scenes"][1]["image_state"] == "QUEUED"
        assert job["plan"]["scenes"][1]["prompt"].startswith("A honeybee on a sunflower")
        assert [s["prompt"] for i, s in enumerate(job["plan"]["scenes"]) if i != 1] == \
            [p for i, p in enumerate(prompts) if i != 1]  # other scenes untouched

        c.post(f"/v1/productions/{jid}/approve")
        job = settled(c, jid)
        assert job["status"] == "READY", job
        assert job["plan"]["scenes"][1]["narration"] == "Bees visit thousands of flowers."
        assert [s["image"] for i, s in enumerate(job["scenes"]) if i != 1] == [im for i, im in enumerate(images) if i != 1]
        assert len(list((cfg.cache_dir / "images").iterdir())) == len(images) + 1  # only the edited scene re-ran

        # Editing a finished video returns it to review; approve re-renders.
        c.patch(f"/v1/productions/{jid}/scenes/0", json={"narration": "Honey starts with nectar."})
        assert c.get(f"/v1/productions/{jid}").json()["status"] == "REVIEW"
        assert c.get(f"/v1/productions/{jid}/video").status_code == 409
        c.post(f"/v1/productions/{jid}/approve")
        assert settled(c, jid)["status"] == "READY"


def test_cancel_during_review(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "How bees make honey", "duration_s": 12,
                                              "review": True}).json()["id"]
        assert settled(c, jid)["status"] == "REVIEW"
        assert c.delete(f"/v1/productions/{jid}").json()["status"] == "CANCELLED"


def test_swipe_redraw_pauses_for_review_again(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Why octopuses are smart", "duration_s": 12,
                                              "review": True}).json()["id"]
        job = settled(c, jid)
        assert job["status"] == "REVIEW"
        before = [s["image"] for s in job["scenes"]]
        assert c.post(f"/v1/productions/{jid}/redraw", json={"scenes": []}).status_code == 422
        assert c.post(f"/v1/productions/{jid}/redraw", json={"scenes": [99]}).status_code == 422
        r = c.post(f"/v1/productions/{jid}/redraw", json={"scenes": [0, 2]})
        assert r.status_code == 200 and r.json()["status"] == "QUEUED"
        job = settled(c, jid)
        assert job["status"] == "REVIEW" and job["stages"]["narration"]["state"] == "PENDING"
        after = [s["image"] for s in job["scenes"]]
        assert after[0] != before[0] and after[2] != before[2] and after[1] == before[1]
        c.post(f"/v1/productions/{jid}/approve")
        assert settled(c, jid)["status"] == "READY"


def test_publish_kit_and_capcut_export(cfg):
    import io
    import zipfile
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Why cats purr", "duration_s": 12}).json()["id"]
        assert c.get(f"/v1/productions/{jid}/export").status_code in (409, 200)
        job = settled(c, jid)
        assert job["status"] == "READY", job
        kit = c.post(f"/v1/productions/{jid}/publish-kit").json()
        assert len(kit["titles"]) == 3 and kit["hashtags"] == ["#shorts", "#facts", "#learn"] and kit["pinned_comment"]
        assert c.get(f"/v1/productions/{jid}").json()["publish_kit"]["titles"] == kit["titles"]
        r = c.get(f"/v1/productions/{jid}/export")
        assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = set(z.namelist())
        n = len(job["scenes"])
        assert {f"media/{i + 1:02d}_scene.png" for i in range(n)} <= names
        assert {"audio/voiceover.wav", "captions.srt", "timeline.csv", "creatorforge.mp4", "publish.txt", "README.txt"} <= names
        assert any(x.startswith("audio/music") for x in names)
        srt = z.read("captions.srt").decode()
        assert srt.startswith("1\n00:00:0") and " --> " in srt
        assert "The truth about" in z.read("publish.txt").decode()
        assert len(z.read("timeline.csv").decode().strip().splitlines()) == n + 1
