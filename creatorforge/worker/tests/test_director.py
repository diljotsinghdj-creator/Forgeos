import json

import pytest

from creatorforge_worker import director
from creatorforge_worker.director import Character, ProductionSpec
from creatorforge_worker.providers.base import ProviderError


class FakeLLM:
    id = "fake"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def complete_json(self, system, user):
        self.calls.append(user)
        return self.replies.pop(0)


def plan_json(n):
    return json.dumps({"title": "Robots", "hook": "Robots are coming", "cta": "Follow", "music_mood": "epic",
                       "scenes": [{"narration": f"Line {i}", "visual": f"Ava walking warehouse aisle {i}",
                                   "shot": "wide", "camera": "pan left", "mood": "awe"} for i in range(n)]})


def spec(**kw):
    s = ProductionSpec(idea="Humanoid robots in warehouses", duration_s=45, **kw)
    s.validate()
    return s


def test_scene_count_follows_template_and_pacing():
    assert director.target_scene_count(spec()) == 9
    assert director.target_scene_count(spec(pacing="fast")) == 12
    assert director.target_scene_count(spec(template="youtube_longform")) == 4


def test_director_parses_fenced_json_and_builds_prompts():
    s = spec(characters=[Character("Ava", "a silver humanoid robot with blue eyes")], camera="slow push in")
    llm = FakeLLM(["```json\n" + plan_json(9) + "\n```"])
    plan = director.direct(llm, s)
    assert len(plan.scenes) == 9
    p = plan.scenes[0].prompt
    assert "Ava: a silver humanoid robot" in p
    assert "slow push in" in p  # Director Mode camera override wins
    assert "cinematic" in p  # template style
    assert "watermark" in plan.scenes[0].negative


def test_director_retries_once_then_fails_closed():
    llm = FakeLLM(["not json", plan_json(9)])
    assert len(director.direct(llm, spec()).scenes) == 9
    assert "previous answer was invalid" in llm.calls[1]
    with pytest.raises(ProviderError):
        director.direct(FakeLLM(["{}", '{"scenes": []}']), spec())


def test_spec_validation():
    with pytest.raises(ValueError):
        ProductionSpec.from_dict({"idea": "x"})
    with pytest.raises(ValueError):
        ProductionSpec.from_dict({"idea": "a valid idea", "aspect": "4:3"})
    s = ProductionSpec.from_dict({"idea": "a valid idea", "template": "explainer"})
    assert s.aspect == "16:9"
