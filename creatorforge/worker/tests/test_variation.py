"""The variation ledger: lead technique measured from the scenes, palette hue from the subject and a third of the
wheel away from the last film, opening shot and transition family rotated, effects capped, more than one music cue,
and key frames compared with the last films."""
from pathlib import Path

from creatorforge_worker.studio import variation as v


def _sp(**kw):
    sp = {"channel": "print-facts", "genre": "politics", "native_material": "documents",
          "concept": {"central_question": "Who runs the machine?", "claim": "One party built the biggest online machine."},
          "scenes": [{"id": "S1", "act": "hook", "graphic": "Courtdoc: A | B | \"x\" | para 1"},
                     {"id": "S2", "act": "investigation", "graphic": "Clipping: a | b | c | 1"},
                     {"id": "S3", "act": "investigation", "graphic": "Counter: 0 → 5 | x"},
                     {"id": "S4", "act": "ending", "graphic": "Statement: *Why*?"}]}
    sp.update(kw)
    return sp


def test_the_lead_is_measured_and_the_hue_comes_from_the_subject_away_from_the_last_film():
    p = v.plan(_sp(), [])
    assert p["lead"] == "documents" and p["subject"] == "politics" and p["opening"] == "courtdoc"
    assert p["hue"] in v.SUBJECTS["politics"]["hues"] and p["accent"].startswith("#")
    prev = [{"film": "a", "accent": v.hex_of(p["hue"]), "lead": "data", "opening": "hero", "family": "wipes"}]
    p2 = v.plan(_sp(), prev)
    assert v.hue_gap(p2["hue"], p["hue"]) >= 120
    assert not [i for i in v.check(_sp(), p2, prev) if i["level"] == "error"]


def test_repeats_are_errors():
    prev = [{"film": "a", "lead": "documents", "accent": "#D7262B", "opening": "courtdoc", "family": "hard cuts"}]
    p = v.plan(_sp(), prev)
    p["family"] = "hard cuts"
    probs = " ".join(i["problem"] for i in v.check(_sp(), p, prev) if i["level"] == "error")
    assert "lead technique 'documents'" in probs and "opening shot type 'courtdoc'" in probs and "transition family" in probs
    sp = _sp()
    sp["scenes"] = [dict(s, graphic=s["graphic"] + " | fx: dust", act="hook") for s in sp["scenes"]]
    probs = " ".join(i["problem"] for i in v.check(sp, v.plan(sp, []), []) if i["level"] == "error")
    assert "'dust' effect is used 4 times" in probs and "one music cue" in probs
    sp = _sp()
    sp["concept"] = {"central_question": "Why?"}
    assert any("one-sentence claim" in i["problem"] for i in v.check(sp, v.plan(sp, []), []))


def test_the_ledger_keeps_one_row_per_film_and_key_frames_are_compared(tmp_path):
    import subprocess
    from PIL import Image
    led = v.Ledger(tmp_path / "ledger.json")
    p = v.plan(_sp(), [])
    led.add(v.row("film-a", _sp(), p))
    led.add(v.row("film-a", _sp(), p))
    assert len(led.rows()) == 1 and "film-a" in led.markdown()
    a = [tmp_path / f"a{i}.png" for i in range(3)]
    b = [tmp_path / f"b{i}.png" for i in range(3)]
    for f in a:
        Image.new("RGB", (160, 90), (255, 0, 0)).save(f)
    for f in b:
        Image.new("RGB", (160, 90), (20, 60, 200)).save(f)
    assert v.swappable(a, a) > .95 and v.swappable(a, b) < .5
    vid = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=320x180:d=3", str(vid)], check=True)
    kf, probs = v.keyframes(vid, [0.5, 1.5, 2.5], tmp_path / "k", [{"film": "old", "keyframes": [str(x) for x in a]}], tmp_path / "sheet.png")
    assert len(kf) == 3 and Path(kf[0]).is_file() and (tmp_path / "sheet.png").is_file()
    assert probs and "look like old" in probs[0]["problem"]


def test_signature_yellow_is_fixed_and_never_a_film_accent():
    """The owner's pick (2026-11-11): yellow #FFDD33 is the channel signature; a film's accent keeps clear of it."""
    from creatorforge_worker.media import cards, vox
    from creatorforge_worker.studio import variation
    assert vox.SIGNATURE == "#FFDD33" and cards.MARK["editorial"] == "&H0033DDFF"
    for subject in ("money", "evolution", "culture"):
        p = variation.plan({"id": "x", "subject": subject, "scenes": [{"graphic": "Counter: 1 → 2"}]}, [])
        assert variation.hue_gap(p["hue"], variation.SIGNATURE_HUE) >= 25
