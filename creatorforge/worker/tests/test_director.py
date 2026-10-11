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


def test_header_lines_are_not_read_aloud():
    from creatorforge_worker import director as d
    spec = d.ProductionSpec.from_dict({"script": "Post title: The Silent Trick\nRuntime: about 100 seconds\n"
                                                 "Say nothing. It wins negotiations. Then wait.", "duration_s": 30})
    assert spec.script == "Say nothing. It wins negotiations. Then wait."
    assert spec.publish["title"] == "The Silent Trick"


def test_a_wrapped_source_link_is_never_read_aloud():
    from creatorforge_worker import director as d
    # A phone wrapped the long Source: line inside a link; the second half must stay in the source.
    raw = ("The Subscription Trap\nOn-screen hook: STOPPED. STILL PAYING?\n"
           "Source: UK estimate (https://techradar.com/tech/a-b); (https://www\n"
           ".scmp.com/news/world/europe/article/3363469/uk-subscription-traps)\n\n"
           "You quit in January. It still charged you.\nVisual: A phone face down\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert "scmp" not in spec.script and "http" not in spec.script
    assert spec.script.endswith("You quit in January. It still charged you.")
    assert spec.publish["source"].endswith("uk-subscription-traps)")


def test_lines_wrapped_by_a_phone_stay_with_their_direction():
    from creatorforge_worker import director as d
    # Pasted on a phone, long Visual:/Chart: lines broke in two; the second halves must not be narrated.
    raw = ("Short\nTitle: A Test\n\nYou quit in January.\nVisual: Coins crawling out from under a phone on\n"
           "a kitchen table\n\nTwelve pounds a month.\nVisual: A calendar\nChart: £1.6bn | unwanted\n"
           "subscriptions a year · UK est.\n\nFind payments that repeat.\nVisual: A bank statement\n"
           "Text: CHECK\nTONIGHT\n")
    spoken, meta = d.parse_script(raw)
    assert spoken.split("\n")[1:] == ["You quit in January.", "Twelve pounds a month.", "Find payments that repeat."]
    shots = meta["shots"]
    assert shots[1][1] == "Coins crawling out from under a phone on a kitchen table"
    assert shots[2][4] == "£1.6bn | unwanted subscriptions a year · UK est."
    assert shots[3][2] == "CHECK TONIGHT"


def test_several_visual_lines_cut_one_spoken_line_into_several_pictures():
    from creatorforge_worker import director as d
    raw = ("The Subscription Trap\nTitle: The trap test\n\nYou quit in January. It still charged you.\n"
           "Visual: A calendar page for January\nVisual: A phone face down on a kitchen table\nText: JAN\n\n"
           "Twelve pounds a month, every month, for six long months in a row.\nVisual: A one pound coin\n"
           "Visual: A stack of coins\nVisual: A torn calendar\n\nCheck your statement tonight.\nVisual: A bank statement\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert spec.script.split("\n")[0] == "You quit in January. It still charged you."   # narration untouched
    beats = [b for s in d.direct_script(None, spec).scenes for b in (s.beats or [{"text": s.narration, "visual": s.visual}])]
    assert [b["text"] for b in beats][:3] == ["You quit in January.", "It still charged you.", "Twelve pounds a month,"]
    assert [b["visual"] for b in beats][:5] == ["A calendar page for January", "A phone face down on a kitchen table",
                                               "A one pound coin", "A stack of coins", "A torn calendar"]
    assert beats[0]["overlay"] == "JAN" and beats[1]["overlay"] == ""          # text stays with the first picture


def test_pen_marks_and_bubbles_belong_to_the_last_picture_of_their_line():
    from creatorforge_worker import director as d
    raw = ("The Subscription Trap\nTitle: The trap test\n\nYou quit in January. It still charged you.\n"
           "Visual: A calendar page for January\nVisual: A phone face down on a kitchen table\nDraw: circle\n"
           "Bubble: Is this really free?\n\nTwelve pounds a month, every month.\nVisual: A one pound coin\n"
           "Thought: I will cancel it later\n\nCheck your statement tonight.\nVisual: A bank statement\nPen: arrow\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert "circle" not in spec.script and "free?" not in spec.script and "cancel it" not in spec.script
    beats = [b for s in d.direct_script(None, spec).scenes for b in s.beats]
    assert beats[0]["draw"] == "" and beats[1]["draw"] == "circle" and beats[1]["bubble"] == "say:Is this really free?"
    assert beats[2]["bubble"] == "think:I will cancel it later" and beats[3]["draw"] == "arrow"


def test_map_chapter_quote_place_and_cite_lines_are_directions_not_narration():
    from creatorforge_worker import director as d
    raw = ("The Trap Test Video\nTitle: The trap test\n\nYou quit in January. It still charged you.\nVisual: A calendar\n"
           "Visual: A phone\nPlace: Paris · 1925\nCite: FTC, 2025\n\nTwelve pounds a month, every single month.\n"
           "Visual: A coin\nMap: London → Paris\n\nCheck your statement tonight please.\nVisual: A statement\n"
           "Chapter: Part 1 | The trap\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20, "fast_cuts": False})
    assert "Paris" not in spec.script and "FTC" not in spec.script and "trap" not in spec.script.lower()
    assert spec.fast_cuts                                     # a shot list always cuts on its lines
    beats = [b for s in d.direct_script(None, spec).scenes for b in s.beats]
    assert beats[0]["extra"] == {"place": "Paris · 1925", "cite": "FTC, 2025"} and beats[1]["extra"] == {}
    assert beats[2]["extra"] == {"map": "London → Paris"} and beats[3]["extra"] == {"chapter": "Part 1 | The trap"}


def test_writer_text_and_stock_lines_belong_to_their_spoken_line():
    from creatorforge_worker import director as d
    raw = ("Six months becomes seventy-two pounds.\nVisual: Calendar pages flipping\nText: £12 × 6 = £72\n"
           "Stock: calendar pages\nThat is an illustration, not a real company.\nVisual: Blurred phone screen\n"
           "Text: ILLUSTRATION\nOpen your bank statement today.\n"
           "Find one payment you would not choose again.\nVisual: Finger pausing over a phone\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert "Text" not in spec.script and "Stock" not in spec.script and "£" not in spec.script
    plan = d.direct_script(None, spec)
    beats = [b for s in plan.scenes for b in s.beats]
    assert beats[0]["overlay"] == "£12 × 6 = £72" and beats[0]["stock"] == "calendar pages"
    assert beats[1]["overlay"] == "ILLUSTRATION" and beats[1]["stock"] == ""
    assert beats[2]["overlay"] == "" and beats[2]["visual"]            # no visual given: the scene's picture


def test_animated_styles_keep_faces_in_ai_video_and_use_the_illustration_model(cfg, monkeypatch):
    from creatorforge_worker import director as d, providers
    from creatorforge_worker.templates import ANIMATED_STYLES, STYLE_PRESETS
    assert ANIMATED_STYLES <= set(STYLE_PRESETS) and {"explainer_2d", "doodle", "neon"} <= ANIMATED_STYLES
    raw = "A man counts coins at a kitchen table. He looks worried. Then he smiles at the window."
    real = d.ProductionSpec.from_dict({"script": raw, "motion": "ai_video", "style": "cinematic", "fast_cuts": False})
    cartoon = d.ProductionSpec.from_dict({"script": raw, "motion": "ai_video", "style": "animated_3d", "fast_cuts": False})
    assert "faceless framing" in d.direct_script(None, real).scenes[0].prompt
    assert "faceless framing" not in d.direct_script(None, cartoon).scenes[0].prompt
    # illustration model only when configured AND downloaded; otherwise the main model
    cfg.image_provider, cfg.image_model, cfg.image_model_stylized = "diffusers", "main/model", "toon/model"
    monkeypatch.setattr(providers, "_downloaded", lambda repo: False)
    assert providers.build_image(cfg, "anime").model == "main/model"
    monkeypatch.setattr(providers, "_downloaded", lambda repo: True)
    assert providers.build_image(cfg, "anime").model == "toon/model"
    assert providers.build_image(cfg, "cinematic").model == "main/model"


def test_a_chart_on_a_long_line_gets_its_own_slot_so_the_picture_still_shows():
    from creatorforge_worker import director as d
    raw = ("Cancel Test\nTitle: Cancel test\n\n"
           "In twenty twenty-four, regulators reviewed six hundred and forty-two subscription sites and apps.\n"
           "Visual: A government office building with flags outside\nChart: 642 | sites reviewed\nText: 642 SITES\n\n"
           "Hiding the exit is not fair at all, not even a little.\nVisual: A hand holding a phone\n"
           "Visual: An emergency exit door blocked by boxes\nStock: emergency exit door\n\n"
           "Three in four used one.\nVisual: Four phones on a desk\nChart: 76% vs 67% | one, several\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    beats = [b for s in d.direct_script(None, spec).scenes for b in (s.beats or [])]
    assert beats[0]["chart"] and not beats[0]["overlay"]                       # the chart opens the line ...
    assert beats[1]["visual"].startswith("A government") and not beats[1]["chart"]   # ... then the picture shows
    assert beats[1]["overlay"] == "642 SITES"
    assert beats[2]["stock"] == "" and beats[3]["stock"] == "emergency exit door"    # stock goes to the exit door
    assert beats[-1]["chart"] and beats[-1]["visual"] == "Four phones on a desk"     # short line: chart replaces it


def test_globe_timeline_and_icons_lines_are_full_frame_graphics():
    from creatorforge_worker import director as d
    raw = ("Eiffel Test\nTitle: Eiffel test\n\nIn nineteen twenty-five, a con man arrived in Paris.\nVisual: A Paris street\n"
           "Globe: France | where it began\n\nHis life ran from Austria to Alcatraz.\nVisual: An old suitcase\n"
           "Timeline: 1890 Born → 1947 Dies | His life\n\nThree in four sites did it.\nVisual: A laptop\n"
           "Icons: 3 of 4 | sites\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert "Globe" not in spec.script and "1890" not in spec.script
    beats = [b for s in d.direct_script(None, spec).scenes for b in (s.beats or [])]
    extras = [b["extra"] for b in beats if b.get("extra")]
    assert {"globe", "timeline", "icons"} <= {k for e in extras for k in e}


def test_screen_document_statement_split_and_archive_keys():
    from creatorforge_worker import director as d
    raw = ("Keys Test\nTitle: Keys test\n\nIn nineteen twenty, crowds queued outside his office in Boston.\n"
           "Visual: A crowd outside an office\nVisual: Banknotes on a desk\nArchive: 1920s\n\n"
           "The page looks simple until you try to leave it.\nVisual: A laptop\n"
           "Screen: Your plan | Keep my plan · *small:Cancel\n\nWhat you see and what you pay are different things.\n"
           "Visual: A price tag\nVisual: A receipt\nSplit: What you see | What you pay\n\nHe never owned it.\n"
           "Visual: The tower\nStatement: He never *owned* it.\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 30})
    assert "Archive" not in spec.script and "Cancel" not in spec.script
    plan = d.direct_script(None, spec)
    d.prompt_forge(plan, spec)
    beats = [b for s in plan.scenes for b in (s.beats or [])]
    assert all("archival photograph from the 1920s" in b["prompt"] for b in beats[:2])     # both pictures of the line
    keys = {k for b in beats for k in (b.get("extra") or {})}
    assert {"archive", "screen", "split", "statement"} <= keys


def test_big_transition_object_and_article_keys():
    from creatorforge_worker import director as d
    raw = ("Keys Two\nTitle: Keys two\n\nIt was free, they said, for the first seven days.\nVisual: A phone\nBig: FREE\n"
           "Transition: match\n\nTwelve coins later, the trial was not free at all.\nVisual: Coins\nObject: stack | 12 | twelve months\n\n"
           "Regulators wrote it down in a report that year.\nVisual: A report\n"
           "Article: A real headline | Publisher, July 2024\n")
    spec = d.ProductionSpec.from_dict({"script": raw, "duration_s": 20})
    assert "FREE" not in spec.script and "headline" not in spec.script
    beats = [b for s in d.direct_script(None, spec).scenes for b in (s.beats or [])]
    keys = {k for b in beats for k in (b.get("extra") or {})}
    assert {"big", "transition", "object", "article"} <= keys


def test_whisper_falls_back_to_cpu_when_the_gpu_is_full(monkeypatch):
    import sys
    import types
    from pathlib import Path
    from creatorforge_worker.providers import asr_whisper as a
    devices = []

    class FakeModel:
        def __init__(self, name, device="auto", compute_type="default"):
            devices.append(device)
            self.device = device

        def transcribe(self, audio, **kw):
            if self.device != "cpu":
                raise RuntimeError("CUDA failed with error out of memory")
            return [types.SimpleNamespace(words=[types.SimpleNamespace(word=" hi", start=0.0, end=0.4)])], None
    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=FakeModel))
    monkeypatch.setattr(a, "_load_audio", lambda p: "audio")
    assert [w.text for w in a.WhisperASR().words(Path("x.wav"))] == ["hi"] and devices == ["auto", "cpu"]


def test_a_full_gpu_frees_its_own_models_then_script_mode_carries_on(monkeypatch):
    from creatorforge_worker import pipeline, providers
    from creatorforge_worker.providers.base import ProviderError
    freed = []
    monkeypatch.setattr(providers, "release_gpu", lambda: freed.append(1))
    calls = []

    def step(m):
        calls.append(m)
        if m is not None:
            raise ProviderError("LLM HTTP 500: llama-server reported out-of-memory during startup")
        return "plan"
    result, used = pipeline.Pipeline._with_gpu_room(None, step, "llm", optional=True)
    assert result == "plan" and used is None and freed == [1] and calls == ["llm", "llm", None]
    import pytest
    with pytest.raises(ProviderError):           # idea mode needs the script model: the error is reported
        pipeline.Pipeline._with_gpu_room(None, step, "llm", optional=False)


def test_a_script_model_that_times_out_does_not_stop_a_pasted_script(monkeypatch):
    from creatorforge_worker import pipeline, providers
    from creatorforge_worker.providers.base import ProviderError
    import pytest
    monkeypatch.setattr(providers, "release_gpu", lambda: None)

    def step(m):
        if m is not None:
            raise ProviderError("LLM unreachable at http://127.0.0.1:11434/v1: timed out")
        return "plan"
    assert pipeline.Pipeline._with_gpu_room(None, step, "llm", optional=True) == ("plan", None)
    with pytest.raises(ProviderError):
        pipeline.Pipeline._with_gpu_room(None, step, "llm", optional=False)
    assert providers.is_local_url("http://127.0.0.1:11434/v1") and not providers.is_local_url("https://api.example.com/v1")
