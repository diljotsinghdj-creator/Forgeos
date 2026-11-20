"""Fixes from auditing a real exported Short: captions never join two sentences, Wikipedia seat charts and diagrams
are never shown as a subject's picture, and the final check catches frozen pictures and black frames."""
import subprocess

import pytest

from creatorforge_worker.media import quality
from creatorforge_worker.media.captions import group
from creatorforge_worker.providers import wiki_image
from creatorforge_worker.providers.base import Word


def _words(text):
    return [Word(t, i * 0.4, i * 0.4 + 0.35) for i, t in enumerate(text.split())]


def test_captions_end_at_sentence_ends_without_lone_words():
    cues = [c.text for c in group(_words("तीन लोग चुनेंगे। फिर कुछ ही महीनों में क्या हुआ? नया क़ानून। मुख्य न्यायाधीश बाहर।"), 3)]
    assert cues == ["तीन लोग चुनेंगे।", "फिर कुछ ही", "महीनों में", "क्या हुआ?", "नया क़ानून।", "मुख्य न्यायाधीश बाहर।"]
    assert all(c.count("।") + c.count("?") <= 1 for c in cues)


def test_seat_charts_and_diagrams_are_not_pictures(monkeypatch):
    def fake_get(params, timeout=20):
        name = params["titles"].split(":", 1)[1]
        mime = "image/svg+xml" if name.endswith(".svg") else "image/jpeg"
        return {"query": {"pages": {"1": {"imageinfo": [{"url": "https://x/" + name, "mime": mime, "extmetadata": {
            "LicenseShortName": {"value": "CC BY-SA 4.0"}, "Artist": {"value": "Someone"}}}]}}}}
    monkeypatch.setattr(wiki_image, "_get", fake_get)
    assert wiki_image.file_info("Rajya_Sabha_composition_2024.svg") is None
    assert wiki_image.file_info("Lok_Sabha_seats_2024.png") is None
    assert wiki_image.file_info("India_election_results_map.png") is None
    assert wiki_image.file_info("Parliament_House_New_Delhi.jpg") is not None
    assert wiki_image.file_info("Emblem_of_the_Supreme_Court_of_India.svg")["logo"] is True


@pytest.mark.ffmpeg
def test_final_check_catches_a_frozen_picture_and_black_frames(tmp_path):
    v = tmp_path / "v.mp4"
    # 2 s moving, 4 s frozen, 1 s black, 2 s moving
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=30:d=2",
                    "-f", "lavfi", "-i", "color=c=gray:s=320x568:r=30:d=4", "-f", "lavfi", "-i", "color=c=black:s=320x568:r=30:d=1",
                    "-f", "lavfi", "-i", "testsrc2=s=320x568:r=30:d=2",
                    "-filter_complex", "[0][1][2][3]concat=n=4:v=1:a=0", "-pix_fmt", "yuv420p", str(v)], check=True)
    frozen = quality.freezes(v)
    assert frozen and 1.5 < frozen[0][0] < 2.5 and frozen[0][1] >= 3.0
    black = quality.blacks(v, 9.0)
    assert black and 5.5 < black[0][0] < 6.5
