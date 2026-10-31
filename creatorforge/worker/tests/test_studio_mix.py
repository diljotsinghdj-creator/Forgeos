"""Studio mix: one look that combines investigative desk, documentary, editorial collage, cinematic film,
hyper-realistic and mixed-media collage, choosing per line."""
from creatorforge_worker import director
from creatorforge_worker.templates import EDITORIAL_STYLES, STYLE_PRESETS


def test_each_line_gets_the_look_that_suits_it():
    look = director.mix_look
    assert look({"visual": "A crowd in 1947", "extra": {"archive": "1947"}}) == "collage"
    assert look({"visual": "Narendra Modi", "named": {"name": "Narendra Modi"}}) == "editorial"
    assert look({"visual": "Parliament", "stock": "Parliament House New Delhi"}) == "editorial"
    assert look({"visual": "A stack of government files tied with red string"}) == "investigative"
    assert look({"visual": "A quiet Delhi street at dawn"}, hook=True) == "cinematic"
    assert look({"visual": "An empty chair", "emotion": "shock"}) == "cinematic"
    assert look({"visual": "The dome of the Supreme Court building at dusk"}) == "hyperreal"
    assert look({"visual": "A vegetable seller weighing tomatoes at a market stall"}) == "documentary"
    # a scene without per-line cuts can't be laid out, so it only picks a full-frame photo look
    assert look({"visual": "A stack of files on a desk"}, cutout=False) == "documentary"
    assert "studio_mix" in STYLE_PRESETS and "studio_mix" in EDITORIAL_STYLES
    assert next(iter(STYLE_PRESETS)) == "studio_mix"           # first in the app's look picker


def test_prompts_follow_each_lines_look():
    spec = director.ProductionSpec.from_dict({"idea": "studio mix test", "style": "studio_mix"})
    beats = [{"text": "Thousands marched.", "visual": "A quiet Delhi street at dawn"},
             {"text": "The files tell another story.", "visual": "A stack of government files on a desk"},
             {"text": "In 1975 it happened before.", "visual": "A crowd outside a court", "extra": {"archive": "1975"}},
             {"text": "Today the court is listening.", "visual": "The Supreme Court building at dusk"},
             {"text": "People just want answers.", "visual": "A woman buying vegetables at a market stall"}]
    plan = director.ProductionPlan("t", "", "", "", [director.ShotPlan(" ".join(b["text"] for b in beats),
                                                                       beats[0]["visual"], beats=beats)])
    director.prompt_forge(plan, spec)
    b = plan.scenes[0].beats
    assert [x["look"] for x in b] == ["cinematic", "investigative", "collage", "hyperreal", "documentary"]
    assert "cinematic film still" in b[0]["prompt"]
    assert b[1]["prompt"].startswith("old sepia archival photograph")          # cut out and taped to the desk
    assert "halftone" in b[2]["prompt"] and "archival" in b[2]["prompt"]
    assert "hyper-realistic photograph" in b[3]["prompt"]
    assert "documentary photography" in b[4]["prompt"]
    assert "cinematic film still" in b[0]["video_prompt"] and "documentary photography" in b[4]["video_prompt"]


def test_a_studio_mix_video_renders(cfg):
    from fastapi.testclient import TestClient
    from creatorforge_worker.api import create_app
    from .conftest import wait_for

    script = ("Studio Mix\n\nThousands marched through Delhi that morning.\nVisual: A quiet Delhi street at dawn\n\n"
              "But the files tell a different story.\nVisual: A stack of government files on a desk\n\n"
              "In 1975 the same thing happened.\nVisual: A crowd outside a court\nArchive: 1975\n\n"
              "Today the court is listening again.\nVisual: The Supreme Court building at dusk\n\n"
              "So who answers when power is questioned?\nVisual: A woman buying vegetables at a market stall\n")
    with TestClient(create_app(cfg)) as c:
        styles = [s["id"] for s in c.get("/v1/capabilities").json()["styles"]]
        assert styles[0] == "studio_mix"
        jid = c.post("/v1/productions", json={"idea": script, "duration_s": 20, "style": "studio_mix"}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(c.get(f"/v1/productions/{jid}").json()))
        assert job["status"] == "READY", job
        looks = {b.get("look") for s in job["plan"]["scenes"] for b in s.get("beats") or []}
        assert {"investigative", "collage"} <= looks and looks & {"cinematic", "hyperreal", "documentary"}
