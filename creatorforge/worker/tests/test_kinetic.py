"""Editorial type: every line becomes a typographic card - a red dated kicker, a bold headline with a crimson
serif-italic accent, a portrait on a red circle, a calendar for a date, navy for dramatic lines."""
from pathlib import Path

import pytest

from creatorforge_worker.media import kinetic as K
from creatorforge_worker.templates import EDITORIAL_STYLES, STYLE_PRESETS


def test_headline_kicker_and_accent_from_the_line():
    k, h = K.headline({"text": "17 फ़रवरी 2025. राहुल गांधी ने लिखित असहमति दी।",
                       "extra": {"place": "17 FEB 2025 · चयन समिति"}})
    assert k == "17 FEB 2025 · चयन समिति" and h.endswith("*असहमति दी।*")          # the last words are the accent
    k, h = K.headline({"text": "Fourteen days before the hearing, the judge was moved.", "extra": {}})
    assert h == "fourteen days before the hearing, the judge was *moved.*" and k == ""   # Latin set in lower case
    assert K.headline({"text": "x", "extra": {"big": "कुछ ही *घंटे*"}})[1] == "कुछ ही *घंटे*"   # writer's accent kept
    assert K.find_date("31 जनवरी 2024. एक अफ़सर रिटायर हुआ।") == (31, 0, 2024)
    assert K.find_date("on June 25, 2014 he was moved") == (25, 5, 2014)
    assert all(" " not in r or "*" not in r or r.count("*") % 2 == 0 for r in K._wrap("a b c *d e f* g", 4))
    assert "kinetic" in STYLE_PRESETS and "kinetic" in EDITORIAL_STYLES


@pytest.mark.ffmpeg
def test_a_short_renders_every_line_as_a_card(cfg):
    from fastapi.testclient import TestClient

    from creatorforge_worker.api import create_app

    from .conftest import wait_for
    script = ("Ek Kursi\nTitle: Ek Kursi #Shorts\nSource: Tribune, 2025\n\n"
              "31 जनवरी 2024. एक अफ़सर रिटायर हुआ।\nPlace: NEW DELHI · 31 JAN 2024\nBig: रिटायर।\n"
              "Visual: A calendar on a desk\n\n"
              "छह हफ़्ते बाद, वही अफ़सर चुनाव आयुक्त।\nTone: strong\nVisual: A ballot box on a table\n\n"
              "कुछ ही घंटों में, नियुक्ति हो गई।\nTone: dramatic\nVisual: An empty office at night\n\n"
              "एक कुर्सी। 13 करोड़ सवाल।\nStatement: एक कुर्सी। *13 करोड़* सवाल।\nVisual: An empty chair\n")
    with TestClient(create_app(cfg)) as c:
        jid = c.post("/v1/productions", json={"script": script, "duration_s": 20, "style": "kinetic",
                                              "aspect": "9:16", "fast_cuts": True}).json()["id"]
        job = wait_for(lambda: (lambda j: j if j["status"] in ("READY", "FAILED") else None)(
            c.get(f"/v1/productions/{jid}").json()))
    assert job["status"] == "READY", job.get("error")
    work = cfg.jobs_dir / jid / "work"
    cards = list(work.glob("kinetic_*.mp4"))
    assert len(cards) >= 3                                            # the lines are typographic cards
    assert list(work.glob("kbg_*.png"))                               # each over its composed background
    ass = "\n".join(p.read_text() for p in work.glob("kin_*.ass"))
    assert "&H00301EB2" in ass or "&H0048C4F0" in ass                 # crimson (paper) or yellow (navy) accent
    assert "NEW DELHI" in ass                                         # the dated kicker


def test_an_editorial_short_without_visual_lines_keeps_its_per_line_directions():
    from creatorforge_worker.director import parse_script
    from creatorforge_worker.pipeline import _EVENT
    raw = ("Ek Maidan\nTitle: x\nSource: The Quint https://www.thequint.com/a\n\n"
           "1 नवंबर। दिल्ली का रामलीला मैदान।\nPlace: RAMLILA MAIDAN · 1 NOV 2026\nCite: The Quint, Nov 2026\n\n"
           "विपक्ष की एक माँग।\nBig: एक *माँग*\n\n"
           "रिपोर्टों के मुताबिक़, दस हज़ार सुरक्षाकर्मी तैनात।\nBig: 10,000\nCite: The Quint, Nov 2026\n")
    _, meta = parse_script(raw)
    shots = meta.get("shots") or []
    assert any(s[-1].get("place") == "RAMLILA MAIDAN · 1 NOV 2026" for s in shots)   # Place:/Big:/Cite: kept
    assert _EVENT.search("रामलीला मैदान में विपक्ष की रैली")        # a Hindi rally line pulls the news photo
