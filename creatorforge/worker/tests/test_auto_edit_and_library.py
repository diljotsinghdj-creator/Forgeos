import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app
from creatorforge_worker.media import captions

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg


def done(c, jid):
    return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED", "CANCELLED", "REVIEW") else None)(
        c.get(f"/v1/productions/{jid}").json()))


def test_auto_edit_uses_director_transitions_holds_and_emphasis(cfg):
    with TestClient(create_app(cfg)) as c:
        app = c.app
        jid = c.post("/v1/productions", json={"idea": "Why cats purr", "duration_s": 15}).json()["id"]
        job = done(c, jid)
        assert job["status"] == "READY", job
        n = len(job["scenes"])
        assert job["edit"]["transitions"] == ["flash", "dissolve", "zoom", "whip"][: n - 1]
        # scene 1 got the Director's 0.5s hold on top of narration + gap
        assert job["edit"]["durations"][0] == round(job["scenes"][0]["narration_s"] + 0.35 + 0.5, 2)
        ass = (app.state.store.dir(jid) / "work" / "captions.ass").read_text()
        assert "\\c&H0037AFD4&" in ass and "narration" in ass


def test_auto_edit_off_uses_template_rhythm(cfg):
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Why cats purr", "duration_s": 15, "auto_edit": False,
                                              "template": "reels_punchy", "duration_s": 12}).json()["id"]
        job = done(c, jid)
        assert job["status"] == "READY", job
        cycle = ["slide", "cut", "flash", "whip"]
        assert job["edit"]["transitions"] == [cycle[i % 4] for i in range(1, len(job["scenes"]))]


def test_character_library_crud_and_snapshot(cfg):
    with TestClient(create_app(cfg)) as c:
        ava = c.post("/v1/library/characters", json={"name": "Ava", "description": "a silver humanoid robot"}).json()
        assert c.post("/v1/library/characters", json={"name": "ava", "description": "duplicate name"}).status_code == 422
        assert c.post("/v1/library/characters", json={"name": "X", "description": ""}).status_code == 422
        r = c.put(f"/v1/library/characters/{ava['id']}", json={"name": "Ava", "description": "a silver humanoid robot with blue eyes"})
        assert r.status_code == 200
        assert c.post("/v1/productions", json={"idea": "Ava tours a warehouse", "character_ids": ["nope"]}).status_code == 422
        jid = c.post("/v1/productions", json={"idea": "Ava tours a warehouse", "duration_s": 12,
                                              "character_ids": [ava["id"]]}).json()["id"]
        job = done(c, jid)
        assert job["spec"]["characters"] == [{"name": "Ava", "description": "a silver humanoid robot with blue eyes"}]
        c.put(f"/v1/library/characters/{ava['id']}", json={"name": "Ava", "description": "changed later"})
        assert c.get(f"/v1/productions/{jid}").json()["spec"]["characters"][0]["description"].endswith("blue eyes")
        assert c.delete(f"/v1/library/characters/{ava['id']}").status_code == 204
        assert c.get("/v1/library/characters").json() == []

        vids = c.get("/v1/library/videos").json()
        assert [v["id"] for v in vids] == [jid]
        assert c.get(vids[0]["thumbnail_url"]).content[:4] == b"\x89PNG"


def test_caption_emphasis_markup():
    assert captions._highlight("Robots change everything!", {"everything"}) == \
        "Robots change {\\c&H0037AFD4&\\fscx112\\fscy112}everything!{\\r}"


def test_generated_music_is_used_when_configured(cfg):
    cfg.music_provider = "mock"
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "Morning routine tips", "duration_s": 12}).json()["id"]
        job = done(c, jid)
        assert job["status"] == "READY", job
        assert job["providers"]["music"].startswith("mock-music")
        assert len(list((cfg.cache_dir / "music").iterdir())) == 1
