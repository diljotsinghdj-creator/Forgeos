"""Real news on screen: article screenshots for Article: lines, the article's own photo for event lines, and no
garbled AI text or blown-up thumbnails."""
from pathlib import Path

from creatorforge_worker import director
from creatorforge_worker.providers import news_media, wiki_image

SOURCE = ("Al Jazeera, India's 'Cockroach' leaders released, 10 Oct 2026, "
          "https://www.aljazeera.com/news/2026/10/10/indias-cockroach-leaders-detained-new-delhi-in-lockdown; "
          "CPJ, At least 37 journalists detained, 12 Oct 2026, "
          "https://cpj.org/2026/10/at-least-37-journalists-detained-several-assaulted-while-covering-protests-against-indias-election-chief/; "
          "Scroll, ED chargesheet, Apr 2025, https://scroll.in/latest/1081384/ed-files-chargesheet-against-sonia-gandhi-rahul-gandhi-in-national-herald-case")


def test_a_line_is_matched_to_the_article_it_cites():
    links = news_media.source_links(SOURCE)
    assert len(links) == 3 and links[0]["host"] == "aljazeera.com"
    got = news_media.find_link("Police detained the Cockroach leaders in New Delhi", links, "Al Jazeera")
    assert got["host"] == "aljazeera.com"
    got = news_media.find_link("At least 37 journalists detained, several assaulted", links, "CPJ")
    assert got["host"] == "cpj.org"
    assert news_media.find_link("Prices of onions went up", links) is None       # nothing matches: no guess


def test_og_image_is_read_and_tiny_or_logo_images_are_refused(tmp_path, monkeypatch):
    import httpx
    from PIL import Image
    big = tmp_path / "big.jpg"
    Image.new("RGB", (1200, 675), (40, 90, 160)).save(big)

    class R:
        def __init__(self, text="", content=b""):
            self.text, self.content = text, content

        def raise_for_status(self):
            pass
    pages = {"https://news.example/a": '<meta property="og:image" content="https://img.example/protest.jpg">',
             "https://news.example/b": '<meta property="og:image" content="https://img.example/site-logo.png">'}

    def fake_get(url, **kw):
        if url in pages:
            return R(text=pages[url])
        return R(content=big.read_bytes())
    monkeypatch.setattr(httpx, "get", fake_get)
    photo = news_media.lead_photo("https://news.example/a", tmp_path / "news")
    assert photo is not None and photo.is_file()
    assert news_media.lead_photo("https://news.example/b", tmp_path / "news") is None


def test_signs_and_papers_are_drawn_blank_not_with_fake_words():
    v, writing = director._no_text("A barricade with a plain sign reading SECURITY, street empty behind it")
    assert writing and "SECURITY" not in v
    spec = director.ProductionSpec.from_dict({"idea": "protest signs story", "style": "cinematic"})
    shot = director.ShotPlan("A placard.", "Protesters holding placards, text unreadable")
    prompt, negative = director._image_prompt(shot.visual, "", shot, spec, "cinematic")
    assert "unreadable" not in prompt and director.NO_WRITING in prompt
    assert "garbled letters" in negative and "poster text" in negative


def test_a_thumbnail_is_never_blown_up_full_screen(tmp_path, monkeypatch):
    import httpx
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (220, 160), (120, 120, 120)).save(buf, "JPEG")

    class R:
        content = buf.getvalue()

        def raise_for_status(self):
            pass
    monkeypatch.setattr(httpx, "get", lambda url, **kw: R())
    import pytest
    from creatorforge_worker.providers.base import ProviderError
    with pytest.raises(ProviderError):
        wiki_image.fetch_framed({"url": "https://x/thumb.jpg", "logo": False}, tmp_path, (1080, 1920))


def test_a_screenshot_is_framed_with_its_source(tmp_path):
    from PIL import Image
    shot = tmp_path / "shot.png"
    Image.new("RGB", (1280, 1500), (250, 250, 250)).save(shot)
    out = news_media.framed(shot, tmp_path / "f.png", 1080, 1920, "Al Jazeera")
    clip = news_media.still_clip(out, tmp_path / "f.mp4", 1080, 1920, 2.0)
    assert Path(clip).is_file() and Path(clip).stat().st_size > 1000


def test_a_flag_march_photo_is_not_a_logo_and_symbols_are_logos():
    assert not wiki_image._LOGO.search("Flag_march_in_Delhi_2026.jpg")
    assert not wiki_image._LOGO.search("Sealed_ballot_box.jpg")
    assert wiki_image._LOGO.search("BJP_election_symbol.png") and wiki_image._LOGO.search("Flag_of_India.svg")


def test_video_clips_of_collage_looks_ask_for_plain_footage_not_documents():
    assert "documentary footage" in director._video_look("investigative", "x")
    assert director._video_look("cinematic", "x").startswith("cinematic film still")


def test_political_idioms_are_shown_as_what_they_mean():
    v, _ = director._no_text("The minister got a clean chit from the agency")
    assert "shirt" not in v and "clearance stamp" in v
    assert "cabinet" in director.literal_idioms("They whitewashed the report")
    assert director.literal_idioms("A crowd at a rally") == "A crowd at a rally"


def test_the_pen_goes_on_the_text_box_or_not_at_all():
    from creatorforge_worker.media import captions as cap, marks
    from pathlib import Path
    import tempfile
    d = Path(tempfile.mkdtemp())
    with_box = d / "a.ass"
    cap.write_ass(with_box, 1080, 1920, 0.05, 0.8, [], [cap.Overlay(0, 3, "CLEAN CHIT · 2023", "Callout"),
                                                        cap.Overlay(0.3, 3, "circle", "Draw")], set(), "", "", "redpen")
    drawn = [ln for ln in with_box.read_text().splitlines() if ",Mark," in ln]
    assert drawn                                                    # circled: the Text: box
    nums = [[int(v) for v in ln.split("}")[-1].split() if v.lstrip("-").isdigit()] for ln in drawn]
    ys = [y for n in nums for y in n[1::2]]
    assert max(ys) < 1920 * 0.3                                     # up where the Text: box is, not mid-picture
    bare = d / "b.ass"
    cap.write_ass(bare, 1080, 1920, 0.05, 0.8, [], [cap.Overlay(0.3, 3, "circle, cross", "Draw")], set(), "", "", "redpen")
    marks_left = [ln for ln in bare.read_text().splitlines() if ",Mark," in ln]
    assert marks_left and len(marks_left) == len(marks.mark_events("cross", 0.3, 3, 1080, 1920))   # cross kept, circle dropped


def test_the_pen_mark_sits_on_the_picture_with_the_text_box():
    shots = director._line_shots("Then the agency gave him a clean chit in the end, quietly",
                                 {"visual": "A file", "more": ["A desk"], "text": "CLEAN CHIT", "draw": "circle"})
    with_text = [s for s in shots if s[2]]
    assert with_text and with_text[0][5] == "circle"
