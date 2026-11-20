"""The ten stickman looks: picture styles on the pod, and a prompt pack for AI video models."""
from fastapi.testclient import TestClient

from creatorforge_worker import director, stickman_prompts
from creatorforge_worker.api import create_app
from creatorforge_worker.templates import ANIMATED_STYLES, STICKMAN_LOOKS, STYLE_PRESETS

SCRIPT = ("My Channel\n\nसुबह के आठ बजे। लाखों फ़ोन एक साथ बजते हैं।\nVisual: Phones lighting up on a table\n"
          "Text: ILLUSTRATION\n\nएक ही मैसेज। एक ही वक़्त।\nBig: एक *मैसेज*\n\n"
          "और फिर सब कुछ बदल गया, और कोई नहीं जानता था कि आगे क्या होगा।\nAnimate: the stickman jumps back in shock\n")


def test_ten_looks_are_styles_and_lead_the_picture_prompt():
    assert len(STICKMAN_LOOKS) == 10
    assert all(k in STYLE_PRESETS and k in ANIMATED_STYLES for k in STICKMAN_LOOKS)
    spec = director.ProductionSpec.from_dict({"script": SCRIPT, "style": "stick_cave", "faces": "faceless"})
    plan = director.direct_script(None, spec)
    prompt = (plan.scenes[0].beats[0]["prompt"] if plan.scenes[0].beats else plan.scenes[0].prompt)
    assert prompt.startswith(STYLE_PRESETS["stick_cave"][1])
    assert "faceless framing" not in prompt and not prompt.startswith(director.MODERN_INDIA)


def test_prompt_pack_keeps_the_words_and_drops_heading_and_labels():
    pack = stickman_prompts.build(SCRIPT, "stick_line_art", "9:16")
    said = " ".join(s["voiceover"] for s in pack["shots"])
    assert "My Channel" not in said and "सुबह के आठ बजे" in said and "आगे क्या होगा" in said
    assert all("ILLUSTRATION" not in s["on_screen"] for s in pack["shots"])
    assert any(s["scene"] == "the stickman jumps back in shock" for s in pack["shots"])
    assert "9:16" in pack["text"] and pack["text"].count("===== SHOT") == len(pack["shots"])
    assert all(4.0 <= s["seconds"] <= 10.0 for s in pack["shots"])


def test_prompt_pack_endpoint(cfg):
    with TestClient(create_app(cfg)) as c:
        r = c.post("/v1/library/stickman-prompts", json={"script": SCRIPT, "look": "stick_retro_tv",
                                                         "character": "a small green dragon with big curious eyes"})
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["look"] == "stick_retro_tv" and "green dragon" in j["shots"][0]["prompt"]
        assert c.post("/v1/library/stickman-prompts", json={"script": ""}).status_code == 422
        styles = {s["id"] for s in c.get("/v1/capabilities").json()["styles"]}
        assert set(STICKMAN_LOOKS) <= styles
