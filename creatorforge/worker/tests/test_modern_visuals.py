"""Pictures for Indian stories: modern India first, no invented filler pictures, never Hindi text to the image model."""
import re

from creatorforge_worker import director
from creatorforge_worker.director import ProductionSpec


def _plan(script: str, style: str = "cinematic"):
    spec = ProductionSpec.from_dict({"script": script, "aspect": "16:9", "template": "youtube_longform",
                                     "style": style, "faces": "faceless"})
    return director.direct_script(None, spec)


def test_hindi_narration_is_never_the_picture_prompt():
    plan = _plan("व्हाट्सऐप ग्रुप में हर सुबह एक मैसेज आता है।\n\nचुनाव से पहले प्रचार और तेज़ हो जाता है।\n\n"
                 "अदालत ने आदेश रद्द कर दिया।")
    for s in plan.scenes:
        assert not re.search(r"[ऀ-ॿ]", s.prompt), s.prompt
        assert s.prompt.startswith(director.MODERN_INDIA)


def test_modern_india_leads_the_prompt_and_the_negative():
    p, n = director._modernise("cinematic film still, a busy street in Delhi with people", "text, watermark",
                               "a busy street in Delhi with people")
    assert p.startswith(director.MODERN_INDIA) and director.MODERN_PEOPLE in p and director.MODERN_PLACE in p
    assert n.startswith("rust, rusty metal, peeling paint") and n.endswith("text, watermark")
    # a line that asks for a slum keeps it
    assert director._modernise("x", "y", "a slum in 1975") == ("x", "y")


def test_a_card_without_a_visual_gets_no_invented_picture_slot():
    line = "उन्होंने कहा, हम कोई भी मैसेज वायरल कर सकते हैं। खट्टा हो या मीठा। सच्चा हो या झूठा।"
    shots = director._line_shots(line, {"extra": {"quote": "Any message can go viral | Speaker, 2018"}})
    assert len(shots) == 1 and shots[0][7].get("quote")
    with_visual = director._line_shots(line, {"visual": "A modern conference hall",
                                              "extra": {"quote": "Any message can go viral | Speaker, 2018"}})
    assert len(with_visual) == 2 and with_visual[0][1] == "A modern conference hall"


def test_the_writers_visual_is_not_swapped_for_a_stock_concept():
    script = ("पत्रकार और रिपोर्टर हर सुबह यही मैसेज देखते थे, और फिर उसे आगे भेज देते थे।\n"
              "Visual: Extreme close-up of a smartphone lock screen at 8:00 AM, modern apartment\n\n"
              "दूसरी लाइन यहाँ है और यह भी काफ़ी लंबी है।\nVisual: A modern glass office at night\n\n"
              "तीसरी लाइन।\nVisual: Aerial view of a modern city skyline\n")
    plan = _plan(script)
    visuals = [b["visual"] for s in plan.scenes for b in (s.beats or [{"visual": s.visual}])]
    assert any("smartphone lock screen" in v for v in visuals)
    assert not any("newspapers" in v.lower() for v in visuals)
