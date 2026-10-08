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


def test_writer_shot_list_gives_each_line_its_own_picture():
    """A "Visual:" under every spoken line is a shot list, not the look of the whole video."""
    from creatorforge_worker import director as d
    raw = ("Copy their movements, and they'll trust you.\n"
           "Visual: Dark mirror reflecting a silhouette\n"
           "0:03-0:05 It sounds fake. It's real science.\n"
           "Visual: A hand pressing against cold glass\n"
           "0:05-0:07 And one mistake makes it backfire.\n"
           "Visual: A glowing question mark in the dark\n"
           "0:07-0:09 In 1999, two psychologists tested it.\n"
           "Visual: Dim university corridor\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert spec.visual_direction == "" and len(spec.shots) == 4
    assert "Visual" not in spec.script and "0:03" not in spec.script
    plan = d.direct_script(None, spec)
    d.plan_beats(None, plan, spec)
    beats = [b for s in plan.scenes for b in (s.beats or [{"text": s.narration, "visual": s.visual}])]
    assert [b["visual"] for b in beats] == ["Dark mirror reflecting a silhouette", "A hand pressing against cold glass",
                                            "A glowing question mark in the dark", "Dim university corridor"]
    assert all(b["prompt"].lower().startswith(b["visual"].lower()[:12]) for s in plan.scenes for b in s.beats)


def test_one_visuals_line_is_still_the_look_of_the_video():
    from creatorforge_worker import director as d
    spec = d.ProductionSpec.from_dict({"script": "A man walks in. He sits down. Nobody speaks.\n"
                                                 "Visuals: black-and-white 1950s lab footage", "duration_s": 15})
    assert spec.shots == [] and spec.visual_direction.startswith("black-and-white")
