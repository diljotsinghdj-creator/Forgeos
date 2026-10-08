"""Brand kits, dubbing, Hook Lab, Shorts Clipper, client review links and hosted accounts."""
import io
import subprocess
import zipfile

import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app
from creatorforge_worker.director import clean_brand

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg


def settled(c, jid, headers=None):
    return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED", "CANCELLED", "REVIEW") else None)(
        c.get(f"/v1/productions/{jid}", headers=headers or {}).json()))


def logo_png(tmp_path):
    p = tmp_path / "logo.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x320", "-frames:v", "1", str(p)], check=True)
    return p.read_bytes()


def test_brand_validation():
    assert clean_brand(None) == {}
    assert clean_brand({"caption_color": "#ffd400", "intro_text": " DARK HISTORY "}) == {"caption_color": "#FFD400", "intro_text": "DARK HISTORY"}
    for bad in ({"caption_color": "yellow"}, {"logo_asset_id": "x", "logo_position": "middle"}, "nope"):
        with pytest.raises(ValueError):
            clean_brand(bad)


def test_brand_dub_hooks_clips_and_review(cfg, tmp_path):
    cfg.voices.append(type(cfg.voices[0])("es_voice", "Spanish", "mock", ""))
    with TestClient(create_app(cfg)) as c:
        logo = c.post("/v1/library/assets?kind=image&name=logo.png", content=logo_png(tmp_path)).json()
        brand = {"logo_asset_id": logo["id"], "logo_position": "bottom-left", "caption_color": "#00E5FF",
                 "highlight_color": "#FF3B30", "intro_text": "DARK HISTORY", "outro_text": "Subscribe for more"}
        jid = c.post("/v1/productions", json={"idea": "Why the Romans built roads", "duration_s": 15, "brand": brand}).json()["id"]
        job = settled(c, jid)
        assert job["status"] == "READY", job
        assert job["providers"]["brand"].startswith("logo logo.png (bottom-left)")
        ass = (cfg.jobs_dir / jid / "work" / "captions.ass").read_text()
        assert "&H00FFE500" in ass and "DARK HISTORY" in ass and "Subscribe for more" in ass and "Style: Brand" in ass

        # Dubbing: one translated line per scene, visuals reused.
        n = len(job["plan"]["scenes"])
        assert c.post(f"/v1/productions/{jid}/dub", json={"language": "Spanish", "voice": "es_voice", "narrations": ["uno"]}).status_code == 422
        d = c.post(f"/v1/productions/{jid}/dub", json={"language": "Spanish", "voice": "es_voice",
                                                       "narrations": [f"Escena {i} en español con varias palabras." for i in range(n)]})
        assert d.status_code == 202
        dub = settled(c, d.json()["id"])
        assert dub["status"] == "READY", dub
        assert dub["spec"]["voice"] == "es_voice" and dub["variant_of"] == jid and dub["plan"]["scenes"][0]["narration"].startswith("Escena 0")
        assert [s["image"] for s in dub["scenes"]] == [s["image"] for s in job["scenes"]]
        assert dub["stages"]["images"]["state"] == "READY"

        # Hook Lab: variants differ only in the opening line.
        v = c.post(f"/v1/productions/{jid}/hook-variants", json={"hooks": ["What if roads built an empire?", "Rome's secret weapon was a road."]})
        assert v.status_code == 202
        ids = [p["id"] for p in v.json()["productions"]]
        variants = [settled(c, i) for i in ids]
        assert all(x["status"] == "READY" for x in variants)
        assert variants[0]["plan"]["scenes"][0]["narration"] == "What if roads built an empire?"
        assert variants[1]["hook_test"]["variant"] == "B" and variants[1]["title"].endswith("hook B")
        assert variants[0]["plan"]["scenes"][1]["narration"] == job["plan"]["scenes"][1]["narration"]
        listed = {p["id"]: p for p in c.get("/v1/productions").json()}
        assert listed[ids[0]]["hook_test"]["group"] == jid

        # Shorts Clipper from a finished production.
        r = c.post("/v1/clips", json={"production_id": jid, "count": 2, "seconds": 20})
        assert r.status_code == 202
        cj = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/clips/{r.json()['id']}").json()))
        assert cj["status"] == "READY", cj["error"]
        assert len(cj["clips"]) == 1 and cj["clips"][0]["title"] == "Best bit"  # the out-of-range pick was dropped
        f = c.get(f"/v1/clips/{cj['id']}/files/1")
        assert f.status_code == 200 and f.content[4:8] == b"ftyp"
        assert c.post("/v1/clips", json={}).status_code == 422

        # Client review link: anyone with the link can watch and decide, without the worker token.
        link = c.post(f"/v1/productions/{jid}/review-link").json()
        page = c.get(link["path"])
        assert page.status_code == 200 and "Approve" in page.text and "<video" in page.text
        assert c.get(link["path"] + "/video").status_code == 200
        c.post(link["path"], content="decision=changes&comment=Make+the+hook+louder",
               headers={"content-type": "application/x-www-form-urlencoded"}, follow_redirects=False)
        rv = c.get("/v1/reviews").json()
        assert rv[0]["status"] == "changes" and rv[0]["comments"][0]["comment"] == "Make the hook louder"
        assert c.get("/review/notarealtoken000000").status_code == 404


def test_accounts_credits_and_privacy(cfg):
    cfg.token = "owner-secret"
    owner = {"Authorization": "Bearer owner-secret"}
    with TestClient(create_app(cfg, start_runner=False)) as c:
        assert c.get("/v1/me").status_code == 401
        assert c.get("/v1/me", headers=owner).json()["role"] == "owner"
        a = c.post("/v1/accounts", json={"name": "Asha", "role": "creator", "credits": 2}, headers=owner).json()
        cl = c.post("/v1/accounts", json={"name": "Client Co", "role": "client"}, headers=owner).json()
        ah = {"Authorization": f"Bearer {a['key']}"}
        ch = {"Authorization": f"Bearer {cl['key']}"}
        assert c.get("/v1/accounts", headers=ah).status_code == 403  # only the owner manages accounts
        mine = c.post("/v1/productions", json={"idea": "Thirty second fact video", "duration_s": 30}, headers=ah)
        assert mine.status_code == 202
        assert c.get("/v1/me", headers=ah).json()["credits"] == 1
        big = c.post("/v1/productions", json={"idea": "A long documentary", "duration_s": 600}, headers=ah)
        assert big.status_code == 402 and "credits" in big.json()["detail"]
        assert c.post("/v1/productions", json={"idea": "Client tries to make one"}, headers=ch).status_code == 403
        theirs = c.post("/v1/productions", json={"idea": "Owner's own video"}, headers=owner).json()["id"]
        assert [p["id"] for p in c.get("/v1/productions", headers=ah).json()] == [mine.json()["id"]]
        assert c.get(f"/v1/productions/{theirs}", headers=ah).status_code == 404
        assert len(c.get("/v1/productions", headers=owner).json()) == 2
        c.patch(f"/v1/accounts/{a['id']}", json={"add_credits": 40}, headers=owner)
        assert c.get("/v1/me", headers=ah).json()["credits"] == 41
        assert c.delete(f"/v1/accounts/{cl['id']}", headers=owner).status_code == 204
        assert c.get("/v1/me", headers=ch).status_code == 401


def test_clipper_picks_without_ai():
    from creatorforge_worker.clipper import pick, sentences
    from creatorforge_worker.providers.base import Word
    words, t = [], 0.0
    for i in range(30):
        text = f"Why is fact number {i} the biggest secret?" if i in (12, 13) else f"Plain sentence {i} goes here."
        for w in text.split():
            words.append(Word(w, t, t + 0.4)); t += 0.45
    picks = pick(sentences(words), 2, 20)
    assert 1 <= len(picks) <= 2 and all(10 <= p["end"] - p["start"] <= 20.5 for p in picks)
    assert any(p["start"] <= words[12 * 6].start <= p["end"] for p in picks)  # the curious bit is chosen
    assert all(a["end"] <= b["start"] for a, b in zip(picks, picks[1:]))


def test_cancel_stuck_and_review_jobs(cfg):
    """A job left RUNNING by a restart (nothing working on it) and a job in review both cancel at once."""
    app = create_app(cfg, start_runner=False)
    c = TestClient(app)
    jid = c.post("/v1/productions", json={"idea": "The future has arrived", "duration_s": 12}).json()["id"]
    store = app.state.store
    job = store.load(jid)
    job["status"] = "RUNNING"; job["stages"]["images"]["state"] = "RUNNING"
    store.save(job)
    app.state.runner._queue.clear()  # simulate: the worker restarted and lost track of it
    r = c.delete(f"/v1/productions/{jid}").json()
    assert r["status"] == "CANCELLED" and r["stages"]["images"]["state"] == "PENDING"
    assert c.get(f"/v1/productions/{jid}").json()["status"] == "CANCELLED"
    job = store.load(jid); job["status"] = "REVIEW"; store.save(job)
    assert c.delete(f"/v1/productions/{jid}").json()["status"] == "CANCELLED"


def test_cancel_reaches_inside_model_calls():
    import threading
    from creatorforge_worker.providers.base import cancelled, set_cancel, step_callback

    class Pipe:
        def __call__(self, prompt="", callback_on_step_end=None):
            for i in range(5):
                callback_on_step_end(self, i, 0, {})
                if getattr(self, "_interrupt", False):
                    return "stopped"
            return "done"

    ev = threading.Event()
    set_cancel(ev)
    p = Pipe()
    assert p(**step_callback(p)) == "done"
    ev.set()
    p2 = Pipe()
    assert p2(**step_callback(p2)) == "stopped" and cancelled()
    set_cancel(None)
    assert step_callback(object()) == {}


def test_pasted_script_drops_title_labels_and_directions():
    from creatorforge_worker.director import ProductionSpec, clean_script

    raw = ("Nobody Noticed (Brain Glitch)\nVoiceover: Nobody noticed your moment. Here's the proof.\n"
           "[Visual: crowded room]\nVisual: close-up\n**VO:** Researchers at Cornell checked.\n(beat)\nSo relax.")
    assert clean_script(raw) == "Nobody noticed your moment. Here's the proof.\nResearchers at Cornell checked.\nSo relax."
    spec = ProductionSpec.from_dict({"script": raw})
    assert spec.idea == "Nobody Noticed (Brain Glitch)"
    assert "Voiceover" not in spec.script and "Visual" not in spec.script
    assert clean_script("Just a plain script. Two sentences.") == "Just a plain script. Two sentences."


def test_ai_video_speed_presets():
    import pytest
    from creatorforge_worker.director import ProductionSpec
    from creatorforge_worker.providers.video import DiffusersVideoProvider

    v = DiffusersVideoProvider("")
    assert (v.quality, v.steps, v._size(768, 1344)) == ("fast", 20, (448, 832))
    v.set_quality("best")
    assert (v.steps, v.max_frames, v._size(768, 1344)) == (40, 121, (704, 1280))
    assert v.id.endswith(":best")   # clip cache keys differ per preset
    assert ProductionSpec.from_dict({"idea": "a calm ocean story", "video_quality": "balanced"}).video_quality == "balanced"
    with pytest.raises(ValueError):
        ProductionSpec.from_dict({"idea": "a calm ocean story", "video_quality": "ultra"})


def test_human_like_voice_profiles(tmp_path):
    import pytest
    from creatorforge_worker.library import Library
    from creatorforge_worker.providers.base import NotConfigured
    from creatorforge_worker.providers.tts import ChatterboxVoice

    lib = Library(tmp_path / "library")
    v = lib.voices.create({"name": "My voice", "provider": "chatterbox", "voice": "asset:abc123", "style": "documentary"}, set())
    assert (v["provider"], v["style"]) == ("chatterbox", "documentary")
    with pytest.raises(ValueError):
        lib.voices.create({"name": "Bad", "provider": "chatterbox", "voice": "/etc/passwd"}, set())
    with pytest.raises(ValueError):
        lib.voices.create({"name": "Bad", "provider": "chatterbox", "voice": "default", "style": "shouty"}, set())

    files = tmp_path / "library" / "assets" / "files"
    files.mkdir(parents=True, exist_ok=True)
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=d=2", "-y", str(files / "abc123.m4a")], check=True)
    voice = ChatterboxVoice("asset:abc123", "documentary", tmp_path, url="http://127.0.0.1:9")
    assert voice.reference().endswith("asset_abc123.wav")   # phone m4a converted to WAV for Chatterbox
    with pytest.raises(NotConfigured):   # engine not running -> clear message, not a crash
        voice.synthesize("Hello there.", tmp_path / "x.wav")


def test_faceless_framing_only_for_people_shots():
    from creatorforge_worker.director import ProductionPlan, ProductionSpec, ShotPlan, prompt_forge

    spec = ProductionSpec.from_dict({"idea": "the spotlight effect explained"})
    assert spec.faces == "faceless"
    plan = ProductionPlan("t", "", "", "", [ShotPlan("n1", "A student walks into a crowded lecture hall"),
                                           ShotPlan("n2", "A lighthouse on a stormy cliff at night")])
    prompt_forge(plan, spec)
    people, scenery = plan.scenes
    assert "faceless framing" in people.prompt and "visible face" in people.negative
    assert "faceless framing" not in scenery.prompt and "visible face" not in scenery.negative
    shown = ProductionSpec.from_dict({"idea": "the spotlight effect explained", "faces": "show"})
    prompt_forge(plan, shown)
    assert "faceless framing" not in plan.scenes[0].prompt


def test_script_mode_survives_llm_miscounting_scenes():
    import json
    from creatorforge_worker.director import ProductionSpec, direct_script, split_script

    script = " ".join(f"Sentence number {i} tells part of the story about people lying every day." for i in range(1, 40))
    spec = ProductionSpec.from_dict({"script": script})
    n = len(split_script(spec))

    class Miscounting:
        def complete_json(self, system, user):
            return json.dumps({"title": "Everyone Is Lying", "scenes": [{"visual": f"shot {i}"} for i in range(n - 3)]})

    plan = direct_script(Miscounting(), spec)
    assert len(plan.scenes) == n
    assert plan.scenes[0].visual.startswith("shot 0")
    assert plan.scenes[-1].visual == plan.scenes[-1].narration   # gap filled from its own words

    class Garbage:
        def complete_json(self, system, user):
            return "not json at all"

    assert len(direct_script(Garbage(), spec).scenes) == n


def test_app_lends_its_ai_for_planning_with_local_fallback(tmp_path):
    from creatorforge_worker import providers
    from creatorforge_worker.config import Config

    cfg = Config(data_dir=tmp_path, llm_url="http://127.0.0.1:9/v1", llm_model="local-7b")
    providers.set_director_llm("job1", {"url": "http://insecure.example/v1", "model": "m", "key": "k"})
    assert providers.director_llm(cfg, "job1").id == "llm:local-7b"          # only https is accepted
    providers.set_director_llm("job2", {"url": "https://127.0.0.1:9/v1", "model": "gemini-x", "key": "k"})
    llm = providers.director_llm(cfg, "job2")
    assert llm.id.startswith("llm:gemini-x (from app)")

    class Local:
        id = "llm:local-7b"
        def complete_json(self, system, user):
            return '{"ok": true}'

    llm.backup = Local()
    assert llm.complete_json("s", "u") == '{"ok": true}'                       # app AI unreachable -> local model
    assert "app AI failed" in llm.id
