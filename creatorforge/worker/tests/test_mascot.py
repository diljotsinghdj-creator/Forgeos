"""The Dragon Psychology mascot: one original drawn dragon, rigged (faces, poses, props), as its own scene and in the
corner of any graphic; never on Print Facts; it reacts and never lip-syncs."""
import json

from creatorforge_worker import vox_director
from creatorforge_worker.media import motion, vox
from creatorforge_worker.studio import writer
from creatorforge_worker.studio.dossier import Dossier


def test_the_mascot_lines_parse_and_are_known_to_the_director():
    p = vox.plan_for("mascot", "curious point magnifier | Wait. Look at this line. | THE CALL")
    assert (p["face"], p["pose"], p["holds"], p["line"], p["title"]) == ("curious", "point", "magnifier", "Wait. Look at this line.", "THE CALL")
    assert vox.plan_for("mascot", "phone")["pose"] == "hold"                      # a prop is held
    assert vox.plan_for("mascot", "banana | x") is None                            # not a look the rig has
    assert vox.plan_for("myth", "a b | c d | mascot: worried shrug")["mascot"] == {"face": "worried", "pose": "shrug", "prop": ""}
    assert vox_director.valid("Mascot: smug explain | It was never about intelligence.") == ""
    assert vox.LAYOUT_SETS["mascot"] == ["base", "mirror"]


def test_print_facts_never_gets_the_mascot():
    d = Dossier(topic="t", claims={})
    sp = {"channel": "print-facts", "engine": "trojan-horse", "concept": {"logline": "x", "central_question": "why?"},
          "scenes": [{"id": "S1", "act": "hook", "narration": "Why does it work?", "graphic": "Mascot: curious point | Why?"},
                     {"id": "S2", "act": "ending", "narration": "That is why.", "graphic": "Statement: *That* | mascot: smug"}]}
    probs = [p for p in writer.check(sp, d) if "no mascot" in p["problem"]]
    assert [p["scene"] for p in probs] == ["S1", "S2"]
    sp["channel"] = "dragon-psychology"
    assert not [p for p in writer.check(sp, d) if "no mascot" in p["problem"]]


def test_the_mascot_renders_in_every_shape_and_in_a_corner(tmp_path):
    if not motion.enabled():
        return
    for w, h in ((480, 270), (270, 480), (360, 360)):
        out = vox.render("mascot", "shocked cover | Two blue ticks. No reply.", "e~0@red/field/", w, h, 2.0, tmp_path / f"m{w}x{h}.mp4",
                         tmp_path / "w", fetch=False, fps=6)
        qa = json.loads(out.with_suffix(".qa.json").read_text())
        assert out.stat().st_size > 3000 and qa["text_cut_off"] == [] and qa["text_below_floor"] == [], (w, h, qa)
    out = vox.render("myth", "Smart people never fall for scams | Intelligence is not armour | mascot: suspicious", "e~0@red/field/",
                     480, 270, 2.0, tmp_path / "corner.mp4", tmp_path / "w", fetch=False, fps=6)
    assert out.stat().st_size > 3000
