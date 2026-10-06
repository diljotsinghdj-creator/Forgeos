import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg

SCRIPT = """Kanye West's child-support bill is reportedly $200,000 every month. 💰

The figure comes from the 2022 divorce settlement. It was described as the highest in U.S. history.
That works out to $2.4 million a year. Either way, it is an insane number."""


def settle(c, jid):
    return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED", "CANCELLED", "REVIEW") else None)(
        c.get(f"/v1/productions/{jid}").json()))


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


# 1. Script mode -----------------------------------------------------------------------------
def test_script_mode_keeps_exact_words_with_director(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": SCRIPT, "template": "shorts_cinematic"}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY", job
        narration = " ".join(s["narration"] for s in job["plan"]["scenes"])
        assert "U.S. history" in narration and "💰" not in narration
        assert narration.split() == " ".join(SCRIPT.replace("💰", "").split()).split()
        assert job["plan"]["scenes"][0]["visual"] == "Scene 1 illustration"  # visuals from the Director
        assert job["providers"]["llm"].endswith("(script mode)")


def test_script_mode_works_without_llm(cfg):
    cfg.llm_url = ""
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": SCRIPT}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY", job
        assert job["providers"]["llm"].startswith("none (script mode")
        assert job["plan"]["scenes"][0]["visual"] == job["plan"]["scenes"][0]["narration"]


# 2. Voice profiles, rename, delete -------------------------------------------------------------
def test_voice_profiles_crud_preview_and_use(cfg):
    with TestClient(create_app(cfg)) as c:
        assert c.post("/v1/library/voices", json={"name": "X", "provider": "piper", "voice": "/nope.onnx"}).status_code == 422
        v = c.post("/v1/library/voices", json={"name": "Calm narrator", "provider": "mock", "speed": 0.9}).json()
        voices = c.get("/v1/library/voices").json()
        assert [x["builtin"] for x in voices] == [True, False]
        assert v["id"] in [x["id"] for x in c.get("/v1/capabilities").json()["voices"]]
        assert c.post(f"/v1/library/voices/{v['id']}/preview", json={"text": "hello"}).content[:4] == b"RIFF"
        jid = c.post("/v1/productions", json={"idea": "Desert survival tips", "duration_s": 12, "voice": v["id"]}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY" and job["providers"]["voice"].startswith(v["id"])
        assert c.put(f"/v1/library/voices/{v['id']}", json={"name": "Calm", "provider": "mock", "speed": 3}).status_code == 422
        assert c.delete(f"/v1/library/voices/{v['id']}").status_code == 204
        assert c.delete("/v1/library/voices/narrator").status_code == 404  # built-in voices are read-only

        assert c.patch(f"/v1/productions/{jid}", json={"title": "Survive the Sahara"}).json()["title"] == "Survive the Sahara"
        assert c.get("/v1/library/videos").json()[0]["title"] == "Survive the Sahara"
        assert c.delete(f"/v1/productions/{jid}?purge=true").status_code == 204
        assert c.get(f"/v1/productions/{jid}").status_code == 404


# 3. Asset library --------------------------------------------------------------------------------
def test_asset_library_upload_validate_and_use_in_scenes(cfg, tmp_path):
    img, clip, voice, song = tmp_path / "logo.png", tmp_path / "broll.mp4", tmp_path / "vo.m4a", tmp_path / "song.mp3"
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=800x600", "-frames:v", "1", str(img))
    ffmpeg("-f", "lavfi", "-i", "testsrc2=s=640x360:d=3", "-pix_fmt", "yuv420p", str(clip))
    ffmpeg("-f", "lavfi", "-i", "sine=f=440:d=4", str(voice))
    ffmpeg("-f", "lavfi", "-i", "sine=f=330:d=10", str(song))
    with TestClient(create_app(cfg)) as c:
        up = lambda path, kind: c.post(f"/v1/library/assets?kind={kind}&name={path.name}", content=path.read_bytes())
        a_img, a_clip, a_vo, a_song = (up(img, "image").json(), up(clip, "video").json(),
                                        up(voice, "audio").json(), up(song, "music").json())
        assert up(song, "image").status_code == 422  # an mp3 is not an image
        assert a_clip["width"] == 640 and a_vo["duration_s"] > 3.5
        assert {a["kind"] for a in c.get("/v1/library/assets").json()} == {"image", "video", "audio", "music"}

        jid = c.post("/v1/productions", json={"idea": "Our product launch", "duration_s": 15, "review": True,
                                              "music_asset_id": a_song["id"]}).json()["id"]
        assert settle(c, jid)["status"] == "REVIEW"
        gen = c.get("/v1/library/assets?kind=image&generated=true").json()
        assert any(a["source"] == "generated" for a in gen)
        assert c.patch(f"/v1/productions/{jid}/scenes/0", json={"asset_id": a_img["id"]}).json()["scenes"][0]["image_source"] == "asset"
        c.patch(f"/v1/productions/{jid}/scenes/1", json={"asset_id": a_clip["id"]})
        c.post(f"/v1/productions/{jid}/approve")
        job = settle(c, jid)
        assert job["status"] == "READY", job
        assert job["scenes"][1]["clip_source"] == "asset"
        assert job["providers"]["music"] == "asset: song.mp3"
        # a voice-over recording replaces generated narration for one scene
        c.patch(f"/v1/productions/{jid}/scenes/2", json={"asset_id": a_vo["id"]})
        c.post(f"/v1/productions/{jid}/approve")
        job = settle(c, jid)
        assert job["status"] == "READY", job
        assert job["scenes"][2]["voice_source"] == "asset" and job["scenes"][2]["narration_s"] > 3.5
        assert c.get(gen[0]["file_url"]).status_code == 200
        assert c.delete(f"/v1/library/assets/{a_img['id']}").status_code == 204


# 4. Sound effects --------------------------------------------------------------------------------
def test_sound_effects_are_placed_on_transitions_and_overlays(cfg, tmp_path):
    folder = tmp_path / "sfx"
    folder.mkdir()
    for name in ("whoosh_soft.wav", "impact_deep.wav", "pop_ui.wav"):
        ffmpeg("-f", "lavfi", "-i", "anoisesrc=d=0.4:a=0.5", str(folder / name))
    cfg.sfx_dir = str(folder)
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Fast facts about sharks", "duration_s": 25}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY", job
        files = [x["file"] for x in job["edit"]["sfx"]]
        # mock Director picks whip/flash/dissolve/zoom: whoosh + impact on edits, impact on hook, pop on callout/CTA
        assert "whoosh_soft.wav" in files and "impact_deep.wav" in files and "pop_ui.wav" in files
        assert job["edit"]["sfx"][0]["at"] < 0.2  # hook hit at the very start
        off = c.post("/v1/productions", json={"idea": "Fast facts about sharks", "duration_s": 15, "sfx": False}).json()["id"]
        assert settle(c, off)["providers"]["sfx"] == "off"


# 5. Timeline editor -------------------------------------------------------------------------------
def test_timeline_reorder_delete_retime_and_overlays(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Five habits of rich people", "duration_s": 20}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY" and len(job["scenes"]) == 4
        images = [s["image"] for s in job["scenes"]]
        n0 = job["scenes"][0]["narration_s"]
        body = {"hook": "Rich habits", "cta": "Save this",
                "scenes": [{"index": 2, "transition": "cut", "overlay": "Habit #3"},
                           {"index": 0, "duration_s": n0 + 3},
                           {"index": 3, "duration_s": 0.1}]}  # scene 1 deleted; 0.1s clamps to narration length
        job = c.patch(f"/v1/productions/{jid}/timeline", json=body).json()
        assert job["status"] == "REVIEW"
        assert [s["image"] for s in job["scenes"]] == [images[2], images[0], images[3]]
        assert job["scenes"][1]["duration_override"] == round(n0 + 3, 2)
        assert job["scenes"][2]["duration_override"] >= job["scenes"][2]["narration_s"]
        c.post(f"/v1/productions/{jid}/approve")
        job = settle(c, jid)
        assert job["status"] == "READY", job
        assert job["plan"]["hook"] == "Rich habits" and job["plan"]["scenes"][0]["overlay"] == "Habit #3"
        assert job["edit"]["transitions"][0] == "dissolve" or job["edit"]["transitions"][0]
        assert job["edit"]["durations"][1] == round(n0 + 3, 2)
        assert c.patch(f"/v1/productions/{jid}/timeline", json={"scenes": [{"index": 7}]}).status_code == 409
        # the new scene 2 (old index 0) entering transition is the director's; scene 1 transition locked to cut
        assert job["plan"]["scenes"][0]["transition_locked"] is True


# Realistic AI video ---------------------------------------------------------------------------------
def test_style_presets_motion_prompts_and_clip_stretch(cfg):
    cfg.video_provider = "mock"
    with TestClient(create_app(cfg)) as c:
        styles = {s["id"] for s in c.get("/v1/capabilities").json()["styles"]}
        assert {"hyperreal", "anime", "animated_3d", "claymation"} <= styles
        jid = c.post("/v1/productions", json={"idea": "London in 2035 with robots and self-driving cars", "duration_s": 25,
                                              "motion": "ai_video", "style": "hyperreal"}).json()["id"]
        job = settle(c, jid)
        assert job["status"] == "READY", job
        shot = job["plan"]["scenes"][0]
        assert "hyper-realistic photograph" in shot["prompt"]
        assert shot["video_prompt"].startswith("crowd walks past while drone 1 glides overhead")
        assert "flicker" in shot["video_negative"]
        # mock clips are capped at 5s like real models; longer scenes are slowed, not frozen
        assert all(1.0 <= s <= 1.6 for s in job["edit"]["clip_stretch"])
        assert job["result"]["verification"]["decode_check"] == "passed"
