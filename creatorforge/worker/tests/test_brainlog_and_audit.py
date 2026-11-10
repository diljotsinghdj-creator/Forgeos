"""The showrunner's loop: three engines pitched before any script, the retention audit on every draft, and Brain Log
patches and used mechanics that the next film is checked against."""
import json

import pytest

from creatorforge_worker.studio import brainlog, writer
from creatorforge_worker.studio.dossier import Dossier

LOG = """# Brain log

| Channel | Film | Engine | Hook mechanism | Visual metaphors | Status |
|---|---|---|---|---|---|
| Dragon Psychology | Scam v1 | trojan-horse | a counter freezing | two-track brain grid; balance scale | under revision |

---

## Patches
"""


class LLM:
    def complete_json(self, system, user):
        return json.dumps({"pitches": [{"engine": "reverse-autopsy", "opening": "The money left at 9:14. Nobody noticed until noon."},
                                       {"engine": "live-viewer-trap", "opening": "Let's unpack your brain."}]})


def test_three_engines_are_pitched_and_the_last_one_is_never_offered():
    hist = [{"channel": "dragon-psychology", "engine": "trojan-horse"}]
    d = Dossier(topic="phone scams", claims={})
    p = writer.pitch(d, hist, "dragon-psychology")
    assert len(p) == 3 and "trojan-horse" not in [x["engine"] for x in p] and len({x["engine"] for x in p}) == 3
    from creatorforge_worker.studio.dossier import Claim
    d2 = Dossier(topic="phone scams", claims={"C1": Claim(id="C1", claim="Scammers pose as banks", status="verified")})
    p = {x["engine"]: x["opening"] for x in writer.pitch(d2, hist, "dragon-psychology", llm=LLM())}
    assert p["reverse-autopsy"].startswith("The money left") and p["live-viewer-trap"] == ""      # a banned phrase is dropped
    with pytest.raises(ValueError):
        writer.write(LLM(), d, engine="montage")


def test_the_retention_audit_finds_the_weakest_lines_and_the_long_stretches():
    long = " ".join(["word"] * 45) + "."
    sp = {"title": "T", "scenes": [
        {"id": "S1", "act": "hook", "narration": "Why did the call work?", "graphic": "Statement: *Why*"},
        {"id": "S2", "act": "investigation", "narration": long, "graphic": "Photo: a.jpg", "claims": ["C1"]},
        {"id": "S3", "act": "investigation", "narration": long, "graphic": "Photo: b.jpg", "claims": ["C1"]},
        {"id": "S4", "act": "ending", "narration": "Hang up. Call back.", "graphic": "Endcard: x"}]}
    a = writer.retention_audit(sp)
    assert a["weakest"][0]["scene"] == "S3" and a["no_interrupt"] and a["no_interrupt"][0]["scenes"] == ["S2", "S3"]
    md = writer.retention_markdown(sp, a)
    assert "[RETENTION & MISTAKE AUDIT]" in md and "Sharper rewrite" in md and "S2, S3" in md


def test_brain_log_patches_and_used_mechanics_feed_the_anti_clone_check(tmp_path):
    p = tmp_path / "BRAIN_LOG.md"
    p.write_text(LOG, encoding="utf-8")
    block = brainlog.append_patch("Hook too slow", "The hook took 40 s.", "Land the hook in 20 s.", "counter freeze", "Cold open", p, "2026-11-10")
    brainlog.append_patch("Hook too slow", "The hook took 40 s.", "Land the hook in 20 s.", "counter freeze", "Cold open", p, "2026-11-10")
    text = p.read_text()
    assert text.count("### 2026-11-10: Hook too slow") == 1 and "**New Permanent Rule:** Land the hook in 20 s." in block
    brainlog.record_used("Dragon Psychology", "Scam v2", "reverse-autopsy", "the aftermath first", ["evidence desk"], "scripted", p)
    brainlog.record_used("Dragon Psychology", "Scam v2", "reverse-autopsy", "the aftermath first", ["evidence desk"], "rendered", p)
    rows = brainlog.used(p)
    assert [r["id"] for r in rows] == ["Scam v1", "Scam v2"] and rows[1]["status"] == "rendered"
    sp = {"id": "v3", "channel": "dragon-psychology", "engine": "reverse-autopsy", "metaphors": ["evidence desk", "balance scale"]}
    probs = [x["problem"] for x in writer.novelty(sp, rows) if x["level"] == "error"]
    assert any("engine 'reverse-autopsy'" in x for x in probs) and any("evidence desk" in x for x in probs)
    assert any("balance scale" in x["problem"] for x in writer.novelty(sp, rows) if x["level"] == "warning")
