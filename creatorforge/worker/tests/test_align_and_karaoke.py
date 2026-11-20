"""Word-by-word captions: WhisperX refinement merges safely, and each cue lights up the word being spoken."""
from creatorforge_worker.media import captions as cap
from creatorforge_worker.providers import align
from creatorforge_worker.providers.base import Word


def test_merge_takes_whisperx_times_only_when_words_line_up():
    orig = [Word("सच्चा", 0.2, 0.8), Word("हो", 0.8, 1.0), Word("या", 1.0, 1.3)]
    al = [{"text": "सच्चा", "start": 0.25, "end": 0.7}, {"text": "हो", "start": None, "end": None},
          {"text": "या", "start": 1.05, "end": 1.25}]
    m = align.merge(orig, al)
    assert (m[0].start, m[1].start, m[2].start) == (0.25, 0.8, 1.05) and m[0].text == "सच्चा"
    assert align.merge(orig, al[:2]) is orig                         # a different word count: keep Whisper's
    assert align.merge(orig, [{"start": 2, "end": 3}, {"start": 1, "end": 1.1}, {"start": 3, "end": 4}]) is orig
    assert align.lang_of("नमस्ते दुनिया") == "hi" and align.lang_of("hello") == "en"


def test_refine_without_whisperx_keeps_whisper_timings(monkeypatch):
    monkeypatch.setattr(align, "python", lambda: None)
    ws = [Word("a", 0, 1)]
    out, note = align.refine([("x.wav", ws)])
    assert out == [ws] and note == "whisper"


def test_each_cue_lights_up_word_by_word(tmp_path):
    ws = [Word("सच्चा", 0.2, 0.7), Word("हो", 0.7, 1.0), Word("या", 1.0, 1.3), Word("झूठा।", 1.3, 1.9)]
    cues, parts = cap.group_parts(ws, 3)
    assert [len(p) for p in parts] == [2, 2] and cues[0].text == "सच्चा हो"
    cap.write_ass(tmp_path / "c.ass", 1080, 1920, 0.045, 0.72, cues, [], None, "", "", "", parts)
    ev = [ln for ln in (tmp_path / "c.ass").read_text(encoding="utf-8").splitlines() if ln.startswith("Dialogue: 0,")]
    assert len(ev) == 4                                              # one event per spoken word
    assert "\\1c&H0037AFD4&\\fscx108\\fscy108}सच्चा" in ev[0] and "\\1c&H0037AFD4&\\fscx108\\fscy108}हो" in ev[1]
    assert ev[0].split(",")[1] == "0:00:00.20" and ev[1].split(",")[1] == "0:00:00.70"
