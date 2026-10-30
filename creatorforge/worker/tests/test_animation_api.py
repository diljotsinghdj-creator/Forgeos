"""The animation editor over HTTP: create a production, edit it with undo/redo and versions, refuse edits that
break it, render a preview in the background and generate assets."""
import pytest
from fastapi.testclient import TestClient

from creatorforge_worker.api import create_app

from .conftest import wait_for

pytestmark = pytest.mark.ffmpeg

DOC = {"title": "API", "scenes": [
    {"id": "s1", "cast": [{"name": "Raj", "x": 0.0}], "props": [{"name": "tree", "asset": "tree", "x": 3.0}],
     "steps": [{"t": 0.2, "who": "Raj", "do": "walk", "to": 1.0}, {"t": "+0.1", "who": "Raj", "do": "gesture",
                                                                  "name": "wave", "dur": 1.0}]}]}


def test_animation_editor_api(cfg):
    with TestClient(create_app(cfg)) as c:
        r = c.post("/v1/animation/docs", json=DOC)
        assert r.status_code == 201, r.text
        did = r.json()["id"]
        assert r.json()["check"]["scenes"][0]["qc"].startswith("clean")
        r = c.post(f"/v1/animation/docs/{did}/ops", json={"op": "update_step", "args": {"sid": "s1", "index": 0,
                                                                                       "to": 2.0}})
        assert r.status_code == 200 and r.json()["doc"]["scenes"][0]["steps"][0]["to"] == 2.0
        v = c.post(f"/v1/animation/docs/{did}/versions", json={"message": "walk further"}).json()["version"]
        bad = c.post(f"/v1/animation/docs/{did}/ops", json={"op": "insert_step", "args": {
            "sid": "s1", "index": 2, "step": {"t": 1.0, "who": "Nobody", "do": "walk", "to": 3}}})
        assert bad.status_code == 422 and "does not stage" in bad.json()["detail"]
        assert c.post(f"/v1/animation/docs/{did}/ops", json={"op": "exec", "args": {}}).status_code == 422
        assert c.get(f"/v1/animation/docs/{did}").json()["doc"]["scenes"][0]["steps"][0]["to"] == 2.0
        assert c.post(f"/v1/animation/docs/{did}/undo").json()["doc"]["scenes"][0]["steps"][0]["to"] == 1.0
        assert c.post(f"/v1/animation/docs/{did}/redo").json()["doc"]["scenes"][0]["steps"][0]["to"] == 2.0
        c.post(f"/v1/animation/docs/{did}/ops", json={"op": "set_layer", "args": {"sid": "s1", "mood": "calm"}})
        assert c.post(f"/v1/animation/docs/{did}/versions/{v}/restore").json()["doc"]["scenes"][0].get("layers") is None
        assert c.post(f"/v1/animation/docs/{did}/render?quality=preview").status_code == 202
        st = wait_for(lambda: (lambda j: j if j["state"] != "running" else None)(
            c.get(f"/v1/animation/docs/{did}/render").json()), timeout=300)
        assert st["state"] == "done", st
        assert st["report"]["video"]["missing"] == 0
        assert c.get(f"/v1/animation/docs/{did}/files/preview.mp4").status_code == 200
        assert c.get(f"/v1/animation/docs/{did}/files/../doc.json").status_code == 404
        g = c.post("/v1/animation/assets", json={"description": "a small green bus"}).json()
        assert g["how"] == "generated" and g["compatible"]["ride"]
        assert c.get(f"/v1/animation/assets/{g['id']}/thumbnail").headers["content-type"] == "image/png"
        assert any(a["kind"] == "dog" for a in c.get("/v1/animation/assets?use=walk").json())
        assert c.get("/v1/animation/docs/zzz").status_code == 404


def test_editor_page_and_director_endpoints(cfg):
    with TestClient(create_app(cfg)) as c:
        page = c.get("/v1/animation/editor")
        assert page.status_code == 200 and "Stickman Editor" in page.text
        v = c.get("/v1/animation/vocab").json()
        assert "set_pose" in v["ops"] and "cheer" in v["gestures"] and "rain" in v["weather"]
        r = c.post("/v1/animation/docs/from-script", json={
            "script": "Maya walks to the bus stop. Suddenly it starts to rain. Maya laughs and waves at her friend Leo.",
            "title": "Rain", "voice": {"lang": "en"}})
        assert r.status_code == 201, r.text
        doc = r.json()["doc"]
        assert [x["name"] for x in doc["scenes"][-1]["cast"]] == ["Maya", "Leo"]          # "Suddenly" is not a person
        assert doc["scenes"][1]["layers"]["weather"][0][2] == "rain"
        assert any(s["do"] == "caption" and s.get("voice") for s in doc["scenes"][0]["steps"])
        assert c.get(f"/v1/animation/docs/{r.json()['id']}").json()["notes"]["domain"] == "story"
