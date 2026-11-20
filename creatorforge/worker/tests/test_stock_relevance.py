"""Pexels / Pixabay / Unsplash results are used only when they show the line - and, for people and places,
the story's own country."""
from creatorforge_worker.pipeline import stock_fits, stock_queries


def test_local_scenes_are_searched_in_the_storys_country():
    assert stock_queries("protest march", "India", "New Delhi") == (
        ["protest march New Delhi", "protest march India"], stock_queries("protest march", "India", "New Delhi")[1])
    assert "delhi" in stock_queries("protest march", "India", "New Delhi")[1]
    assert stock_queries("ocean waves", "India") == (["ocean waves"], ())          # nothing local about waves
    assert stock_queries("police India", "India") == (["police India"], ())        # already placed
    assert stock_queries("protest crowd", "") == (["protest crowd"], ())           # no country known


def test_a_result_must_say_it_shows_the_line():
    place = stock_queries("protest march", "India")[1]
    paris = {"url": "https://x/1.mp4", "about": "protest march paris france crowd"}
    delhi = {"url": "https://x/2.mp4", "about": "protest march india people"}
    blank = {"url": "https://x/3.mp4", "about": ""}
    assert not stock_fits(paris, "protest march", place, checked=True)
    assert stock_fits(delhi, "protest march", place, checked=False)
    assert not stock_fits(blank, "protest march", place, checked=False)      # unknown: only with the picture check
    assert stock_fits(blank, "protest march", place, checked=True)
    sunset = {"url": "https://x/4.jpg", "about": "sunset beach"}
    assert not stock_fits(sunset, "ocean waves", (), checked=False)
    assert stock_fits({"url": "https://x/5.jpg", "about": "big ocean waves crashing"}, "ocean waves", (), checked=False)
