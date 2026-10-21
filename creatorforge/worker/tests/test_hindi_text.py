"""Hindi and ₹ on screen: shaping, typing by letter, fonts with the glyphs, amounts parsed to scale, safe paths."""
import subprocess
import shutil

import pytest

from creatorforge_worker.media import captions, cards, charts, ff, globe, marks


def test_graphemes_keep_vowel_signs_and_conjuncts_whole():
    assert captions.graphemes("दिल्ली") == ["दि", "ल्ली"]
    assert captions.graphemes("करोड़") == ["क", "रो", "ड़"]
    assert captions.graphemes("ED raid") == list("ED raid")


def test_norm_keeps_hindi_vowel_signs():
    assert captions._norm("करोड़") != captions._norm("करड")
    assert captions._norm("कटा") != captions._norm("कटे")
    assert captions._norm("Delhi!") == "delhi"


def test_place_stamp_types_whole_letters():
    line = marks.place_events("ओखला, दिल्ली", 0, 3, 1080, 1920)[1]
    assert "ल्ली" in line and "दि" in line


def test_steps_with_pipes_are_all_steps():
    assert cards.steps_lines("मृत | डुप्लीकेट | शिफ़्टेड | हटाओ", "editorial", 1080, 1920, 4)
    assert cards.steps_lines("Raid → Arrest → Bail | how it goes", "editorial", 1080, 1920, 4)


@pytest.mark.parametrize("spec,want", [
    ("₹6,060 crore → ₹12,000 crore", ("₹", " crore", 6060.0, 12000.0)),
    ("Rs 500 → Rs 2,000", ("₹", "", 500.0, 2000.0)),
])
def test_chart_amounts_keep_rupee_and_crore(spec, want):
    p = charts.parse(spec)
    assert (p["prefix"], p["suffix"], p["from"], p["to"]) == want


def test_chart_units_are_whole_words():
    assert charts.parse("4 million vs 2 million")["suffix"] == " million"
    assert charts.parse("3 men vs 5 men")["suffix"] == ""
    assert charts.parse("13 crore vs 9.4 lakh")["values"] == [13.0, 0.094]


def test_squares_scale_crore_and_lakh_and_stay_above_captions():
    out, _ = cards.squares_lines("13 crore vs 9.4 lakh | names cut, a district", "editorial", 1080, 1920, 4)
    assert out
    out, _ = cards.squares_lines("13.3 vs 12.3 | करोड़ नाम कटे, जापान की आबादी (करोड़)", "editorial", 1080, 1920, 4)
    ys = [float(v) for line in out if "\\clip(" in line for v in line.split("\\clip(")[1].split(")")[0].split(",")[1::2]]
    assert max(ys) <= 1920 * 0.61
    label = next(line for line in out if "जापान" in line)
    assert "\\an4" in label or "\\1c&HFFFFFF&" in label          # beside the square, or light on the dark one


def test_label_font_has_the_glyphs():
    assert globe.script_of("दिल्ली") == "deva" and globe.script_of("₹13") == "symbol" and globe.script_of("ED") == "latin"
    path = globe.font_file("symbol")
    if path:
        assert "Archivo" not in path


def test_filter_path_survives_apostrophes_and_colons(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("no ffmpeg")
    d = tmp_path / "it's a:dir, [x]"
    d.mkdir()
    ass = d / "t.ass"
    ass.write_text("[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 180\n\n[V4+ Styles]\n"
                   "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
                   "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                   "MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,30,&H00FFFFFF,&H000000FF,&H00000000,"
                   "&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,10,10,10,1\n\n[Events]\n"
                   "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                   "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,दिल्ली ₹13\n", encoding="utf-8")
    ff.run(["-f", "lavfi", "-i", "color=c=black:s=320x180:d=1", "-vf", ff.ass_filter(ass), "-frames:v", "1",
            str(tmp_path / "o.png")])
    assert (tmp_path / "o.png").is_file()


def test_duration_of_an_empty_file_is_a_media_error(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("no ffmpeg")
    empty = tmp_path / "e.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=s=64x64:d=1", "-ss", "5", "-t", "1",
                    str(empty)], check=False)
    if not empty.is_file():
        empty.write_bytes(b"")
    with pytest.raises(ff.MediaError):
        ff.duration(empty)
