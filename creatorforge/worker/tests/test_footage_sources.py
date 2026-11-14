"""New free footage sources for both channels: NASA SVS, Library of Congress films, Wellcome Collection, Europeana,
and the per-film licence check on Prelinger. Licence filters are the point: nothing non-commercial gets through."""
import httpx

from creatorforge_worker.providers import stock_video


class R:
    def __init__(self, data=None, code=200, text=""):
        self._d, self.status_code, self.text = data, code, text

    def json(self):
        return self._d

    def raise_for_status(self):
        pass


def test_loc_keeps_only_pre_1930_or_no_known_restrictions(monkeypatch):
    res = [{"video": "https://tile.loc.gov/a.mp4", "width": 1440, "height": 1080}]
    monkeypatch.setattr(httpx, "get", lambda url, **kw: R({"results": [
        {"id": "u1", "title": "Flood at Galveston", "date": "1900", "resources": res},
        {"id": "u2", "title": "Flood relief newsreel", "date": "1951", "resources": res},
        {"id": "u3", "title": "Flood survey film", "date": "1960", "rights": ["No known restrictions on publication."], "resources": res}]}))
    found = stock_video._loc("flood", 5)
    assert [c["id"] for c in found] == ["u1", "u3"]
    assert "1900" in found[0]["licence"] and found[0]["archive"]


def test_wellcome_drops_non_commercial_and_home_movies(monkeypatch):
    def work(i, lic, title):
        return {"id": i, "title": title, "items": [{"locations": [{"license": {"id": lic}},
                {"locationType": {"id": "iiif-presentation"}, "url": f"https://iiif/{i}"}]}]}
    def get(url, **kw):
        if "catalogue" in url:
            return R({"results": [work("a", "cc-by-nc", "Brain surgery film"), work("b", "pdm", "Home movies brain"),
                                  work("c", "cc-by", "The brain at work")]})
        return R(text='"id": "https://iiif/av/x/default.mp4"')
    monkeypatch.setattr(httpx, "get", get)
    found = stock_video._wellcome("brain", 5)
    assert [c["id"] for c in found] == ["c"]
    assert found[0]["attribution"].startswith("required")


def test_prelinger_skips_nc_licence(monkeypatch):
    def get(url, **kw):
        if "advancedsearch" in url:
            return R({"response": {"docs": [
                {"identifier": "nc1", "title": "Crowd at a fair", "licenseurl": "http://creativecommons.org/licenses/by-nc/3.0/"},
                {"identifier": "ok1", "title": "Crowd at a fair", "licenseurl": "http://creativecommons.org/publicdomain/mark/1.0/"}]}})
        assert "nc1" not in url
        return R({"files": [{"name": "ok1.mp4", "format": "h.264", "width": "640", "height": "480", "length": "60"}]})
    monkeypatch.setattr(httpx, "get", get)
    found = stock_video._archive("crowd", 5)
    assert all(c["id"] != "nc1" for c in found)


def test_europeana_needs_a_key_and_drops_nc(monkeypatch):
    assert stock_video._europeana("parliament", "", 5) == []
    monkeypatch.setattr(httpx, "get", lambda url, **kw: R({"items": [
        {"id": "x", "title": ["Parliament opening"], "edmIsShownBy": ["https://e/x.mp4"], "rights": ["http://creativecommons.org/licenses/by-nc/4.0/"]},
        {"id": "y", "title": ["Parliament opening"], "edmIsShownBy": ["https://e/y.mp4"], "rights": ["http://creativecommons.org/publicdomain/mark/1.0/"]}]}))
    assert [c["id"] for c in stock_video._europeana("parliament", "k", 5)] == ["y"]


def test_new_sources_registered():
    assert "svs" in stock_video.FREE_SOURCES
    assert {"loc", "wellcome"} <= set(stock_video.ARCHIVE_SOURCES)
