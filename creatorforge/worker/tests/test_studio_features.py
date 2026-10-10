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

    spec = ProductionSpec.from_dict({"idea": "the spotlight effect explained", "faces": "faceless"})
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


def test_fast_cuts_give_each_phrase_its_own_picture(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from creatorforge_worker.director import ProductionSpec
    from .conftest import wait_for

    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": "fast cuts test about lying", "duration_s": 15}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        shot = job["plan"]["scenes"][0]
        beats_per_scene = len(shot["beats"])
        assert beats_per_scene >= 2 and all(len(b["text"].split()) <= 7 for b in shot["beats"])   # <= ~2 s each
        assert job["edit"]["shots"] == beats_per_scene * len(job["scenes"])                       # a picture per beat
        assert "shock" in shot["beats"][0]["prompt"] and "fear" in shot["beats"][1]["prompt"]
        assert job["scenes"][0].get("word_starts")              # cuts land on real word timings
    assert ProductionSpec.from_dict({"idea": "a calm ocean story"}).faces == "show"


def test_beats_fall_back_to_phrase_cuts_when_the_ai_cannot_plan_them():
    from creatorforge_worker.director import ProductionPlan, ProductionSpec, ShotPlan, plan_beats

    spec = ProductionSpec.from_dict({"idea": "the spotlight effect explained"})
    plan = ProductionPlan("t", "", "", "", [ShotPlan("Researchers at Cornell had students walk into a room wearing a "
                                                     "Barry Manilow T-shirt. In front of everyone.", "a lecture hall")])

    class Broken:
        def complete_json(self, system, user):
            return "nope"

    plan_beats(Broken(), plan, spec)
    beats = plan.scenes[0].beats
    assert len(beats) >= 3 and all(len(b["text"].split()) <= 6 for b in beats)
    assert " ".join(b["text"] for b in beats).split() == plan.scenes[0].narration.split()
    assert beats[1]["visual"].startswith("walk into a room")


WRITER_SCRIPT = """:00 HOOK Everyone here is lying.
• 0:02 STAKES You just don't know it. Nineteen fifty-one.
• 0:05 SETUP A student thinks he's taking an eye test.
• 0:12 TWIST Every single one picks the wrong line. On purpose. They're actors.
• 1:06 LOOP Because behind every nod, there's someone quietly hiding their doubt. Which means, in that room...
On-screen hook: EVERYONE IS LYING. Visuals: black-and-white 1950s lab footage, cards with lines, row of suited men all pointing.
Post: The Experiment Where Everyone Lied On Purpose. Cover: EVERYONE IS LYING. #psychology #conformity. Source: Asch, 1951."""


def test_writer_script_format_is_understood(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": WRITER_SCRIPT}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        spoken = " ".join(s["narration"] for s in job["plan"]["scenes"])
        for junk in ("HOOK", "0:02", "TWIST", "Post", "Cover", "Source", "#psychology", "Visuals"):
            assert junk not in spoken, junk
        assert spoken.startswith("Everyone here is lying.") and spoken.endswith("in that room...")
        assert job["plan"]["hook"] == "EVERYONE IS LYING"
        assert job["plan"]["title"] == "The Experiment Where Everyone Lied On Purpose"
        assert "black-and-white 1950s lab footage" in job["plan"]["scenes"][0]["prompt"]
        spec = job["spec"]
        assert spec["publish"]["hashtags"] == ["#psychology", "#conformity"] and spec["publish"]["source"] == "Asch, 1951"
        twist = next(s for s in job["plan"]["scenes"] if "picks the wrong line" in s["narration"])
        assert twist["emotion"] == "shock"


def test_script_pasted_into_the_idea_box_is_treated_as_a_script(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"idea": WRITER_SCRIPT, "duration_s": 60}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        assert job["providers"]["llm"].endswith("(script mode)")
        spoken = " ".join(s["narration"] for s in job["plan"]["scenes"])
        assert spoken.startswith("Everyone here is lying.") and "HOOK" not in spoken


def test_editing_upgrades_sound_design_pace_and_pop_captions(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    def make(c, **extra):
        jid = c.post("/v1/productions", json={"idea": "fast cuts test about lying", "duration_s": 15, **extra}).json()["id"]
        return wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))

    with TestClient(create_app(cfg)) as c:
        normal, fast = make(c), make(c, voice_speed=1.1)
        assert normal["status"] == "READY" and fast["status"] == "READY", (normal, fast)
        assert sum(s["narration_s"] for s in fast["scenes"]) < sum(s["narration_s"] for s in normal["scenes"]) * 0.97
        sounds = {s["file"] for s in normal["edit"]["sfx"]}
        assert {"riser_tension.wav"} & sounds and any(f.startswith(("impact_", "whoosh_")) for f in sounds), sounds
        ass = cfg.jobs_dir / normal["id"] / "work" / "captions.ass"
        assert ass.is_file() and "\\t(0,120" in ass.read_text()      # pop-in caption animation


def test_stock_footage_fills_beats_marked_by_the_planner(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    with TestClient(create_app(cfg)) as c:
        body = {"idea": "fast cuts test about lying", "duration_s": 15, "stock": {"provider": "mock", "key": "k"},
                "visual_direction": "black-and-white 1950s lab footage"}
        jid = c.post("/v1/productions", json=body).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        sc = job["scenes"][0]
        assert sc["beat_clips"][1] and not sc["beat_clips"][0]      # beat 2 asked for "city street" footage
        assert (cfg.jobs_dir / jid / sc["beat_clips"][1]).is_file()
        assert sc["beat_images"][0] is None                          # ...so no AI image was generated for it
        assert job["stock_credits"] == ["test"] and "key" not in str(job["spec"])


def test_stock_photo_fills_a_beat_when_no_footage_fits(cfg, monkeypatch):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from creatorforge_worker.providers import stock_video
    from .conftest import wait_for

    monkeypatch.setattr(stock_video, "search_any", lambda *a, **k: [])
    with TestClient(create_app(cfg)) as c:
        body = {"idea": "fast cuts test about lying", "duration_s": 15, "stock": {"provider": "mock", "key": "k"}}
        jid = c.post("/v1/productions", json=body).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        sc = job["scenes"][0]
        assert sc["beat_images"][0].endswith("_photo.jpg") and (cfg.jobs_dir / jid / sc["beat_images"][0]).is_file()
        assert job["stock_credits"] == ["test photo"]


def test_main_character_face_is_locked_across_people_shots(cfg, tmp_path):
    from creatorforge_worker.pipeline import Pipeline
    from creatorforge_worker.store import JobStore

    pipe = Pipeline(cfg, JobStore(cfg.jobs_dir))

    class FaceAwareImage:
        reference, ref_strength = None, 0.0

    img = FaceAwareImage()
    job = {"spec": {"idea": "the spotlight effect explained"}}
    (tmp_path / "scene_01.png").write_bytes(b"png")
    assert pipe._face_lock(img, job, tmp_path, "A student walks into a hall") == ""      # no reference yet
    pipe._remember_face(job, tmp_path / "scene_01.png", "A student walks into a hall")
    assert job["character_ref"] == "scene_01.png"
    assert pipe._face_lock(img, job, tmp_path, "close-up of the student's eyes") == "face:scene_01.png:0.6"
    assert img.reference == tmp_path / "scene_01.png" and img.ref_strength == 0.6
    assert pipe._face_lock(img, job, tmp_path, "an empty lighthouse at night") == "" and img.reference is None
    off = {"spec": {"idea": "the spotlight effect explained", "consistent_character": False}, "character_ref": "scene_01.png"}
    assert pipe._face_lock(img, off, tmp_path, "the student smiles") == ""


def test_visual_match_check_redraws_pictures_that_miss_the_line(cfg, tmp_path, monkeypatch):
    """A picture that doesn't show its line is redrawn with new seeds and the closest kept; off-topic stock is skipped."""
    from creatorforge_worker.media import match
    from creatorforge_worker.pipeline import Pipeline
    from creatorforge_worker.store import JobStore

    pipe = Pipeline(cfg, JobStore(cfg.jobs_dir))

    class Img:
        id, seeds = "fake", []

        def generate(self, prompt, negative, w, h, seed, out):
            self.seeds.append(seed)
            from creatorforge_worker.media import ff
            ff.run(["-f", "lavfi", "-i", f"color=c=0x{seed % 0xFFFFFF:06x}:s=512x512", "-vf", "noise=alls=60:allf=u",
                    "-frames:v", "1", str(out)])

    scores = iter([0.18, 0.31, 0.5])        # first draw misses, second shows the line

    class Checker:
        def score(self, image, text):
            return next(scores) if "map" in text else 0.1

    monkeypatch.setattr(Pipeline, "_matcher", lambda self: Checker())
    img, job = Img(), {"providers": {}}
    src, key = pipe._matched_image(job, img, "p", "n", (64, 64), 7, "", "An old paper map of Britain, close-up")
    assert len(img.seeds) == 2 and src.is_file()
    assert job["match"]["regenerated"] == 1 and job["match"]["low"] == 0
    assert "1 regenerated" in job["providers"]["match"]
    photo = tmp_path / "x.png"
    photo.write_bytes((cfg.cache_dir / "images").glob("*.png").__next__().read_bytes())
    assert pipe._on_topic(job, photo, "eiffel tower 1920s", "The tower at dawn") is False   # 0.1 < POOR
    assert job["match"]["stock_rejected"] == 1
    monkeypatch.setattr(Pipeline, "_matcher", lambda self: None)       # no models on the pod yet: no checks, no delay
    assert pipe._on_topic(job, photo, "anything", "") is True


def test_clip_tokenizer_matches_the_reference_ids(tmp_path):
    from pathlib import Path
    from creatorforge_worker.media import match
    vocab = Path("/tmp/clip_vocab/bpe_simple_vocab_16e6.txt.gz")
    if not vocab.is_file():
        import pytest
        pytest.skip("CLIP vocab not downloaded")
    assert match._Tokenizer(vocab).encode("A photo of a dog") == [49406, 320, 1125, 539, 320, 1929, 49407]


def test_writer_on_screen_text_is_burned_in_while_its_line_is_spoken(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    script = ("Six months of a forgotten plan becomes seventy-two pounds.\nVisual: Calendar pages flipping\n"
              "Text: £12 x 6 = £72\nThat is an illustration, not a claim about any real company.\n"
              "Visual: Blurred phone screen on a dark table\nText: ILLUSTRATION\n"
              "Open your bank statement today and look closely.\nVisual: Hands holding a phone at a kitchen table\n"
              "Find one payment you would not choose again.\nVisual: Finger pausing over a phone\n"
              "Text: Would I buy this again?\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        ass = (cfg.jobs_dir / jid / "work" / "captions.ass").read_text()
        assert "£12 x 6 = £72" in ass and "ILLUSTRATION" in ass and "Would I buy this again?" in ass


def test_editorial_look_highlighter_callouts_paper_grade_and_sliding_cuts(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    script = ("Six months of a forgotten plan becomes seventy-two pounds.\nVisual: Calendar pages flipping\n"
              "Text: £12 x 6 = £72\nThat is an illustration, not a claim about any real company.\n"
              "Visual: Blurred phone screen on a dark table\nText: ILLUSTRATION\n"
              "Open your bank statement today and look closely.\nVisual: Hands holding a phone at a kitchen table\n"
              "Find one payment you would not choose again.\nVisual: Finger pausing over a phone\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20, "style": "editorial"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        ass = (cfg.jobs_dir / jid / "work" / "captions.ass").read_text()
        assert "&H002BD6F7" in ass and "\\fscx15\\t(0,220,\\fscx100)}ILLUSTRATION" in ass   # yellow marker wipes in
        assert "\\fscx75" not in ass                                    # calm explainer captions, no bounce
        assert list((cfg.jobs_dir / jid / "work" / "layout").glob("layout_*.png"))   # pictures laid out on paper
        assert list((cfg.jobs_dir / jid / "work" / "layout").glob("backdrop_paper_*.png"))
        assert "£12 x 6 = £72" not in ass and list((cfg.jobs_dir / jid / "work").glob("chart_*.mp4"))  # sum -> counter
        assert not set(job["edit"]["transitions"]) & {"fade", "dissolve", "dip"}               # paper slides, never dissolves
        prompt = job["plan"]["scenes"][0]["prompt"]
        assert prompt.startswith("vintage halftone press photograph, one clear subject")   # the look leads the prompt


def test_charts_from_script_lines_and_investigative_look(cfg):
    """Chart: lines (and comparison Text: lines in the editorial looks) become animated graphics in the edit;
    the investigative look uses red-pen callouts; the final video carries a quality report and is loudness-levelled."""
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    script = ("Five small subscriptions add up faster than you think.\nVisual: Coins on a desk\n"
              "Chart: £12 → £720 | a year of forgotten subscriptions\n"
              "Heavy users were far more likely to hold costly credit.\nVisual: Stacks of cards\n"
              "Text: 48% vs 22%\n"
              "Open your statement today and look for one you forgot.\nVisual: Hands holding a phone\n"
              "Text: CHECK TODAY\n"
              "Then cancel it before the next payment lands.\nVisual: Finger over a phone\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20, "style": "investigative"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        work = cfg.jobs_dir / jid / "work"
        assert len(list(work.glob("chart_*.mp4"))) == 2                   # Chart: line + "vs" Text: line
        ass = (work / "captions.ass").read_text()
        assert "&H002E10C8" in ass and "CHECK TODAY" in ass and "48% vs 22%" not in ass   # charted text not repeated
        q = job["result"]["quality"]
        assert {c["name"] for c in q["checks"]} >= {"loudness", "no dead air", "first frame visible"}
        lufs = next(c for c in q["checks"] if c["name"] == "loudness")
        assert lufs["ok"], q
