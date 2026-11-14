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


def test_topic_routing_picks_libraries_by_subject(monkeypatch):
    monkeypatch.delenv("DVIDS_KEY", raising=False)
    names = lambda t: [n for n, _ in stock_video.topic_sources(t)]
    assert names("A galaxy far away")[:2] == ["esahubble", "eso"]
    assert names("Putin speaks in Moscow")[0] == "kremlin"
    assert names("Modi addresses the Lok Sabha")[0] == "pib"
    assert "wellcome" in names("why fear shapes children")
    assert "dvids" not in names("troops on the border")            # keyed library skipped without its key
    monkeypatch.setenv("DVIDS_KEY", "k")
    assert ("dvids", "k") in stock_video.topic_sources("troops on the border")
    assert names("a kitchen table with receipts") == []
    assert len(names("space war russia")) == len(set(names("space war russia")))


def test_publisher_search_narrows_by_source_link(monkeypatch):
    seen = {}
    def get(url, **kw):
        seen.update(kw["params"])
        return R({"query": {"pages": {}}})
    monkeypatch.setattr(httpx, "get", get)
    assert stock_video.search("kremlin", "", "Putin address") == []
    assert 'insource:"kremlin.ru"' in seen["gsrsearch"]


def test_observatory_reads_1080_file_and_credit(monkeypatch):
    def get(url, **kw):
        if "search=" in url:
            return R(text='<a href="/public/videos/eso2612a/">x</a><a href="/public/videos/eso2612a/">x</a>')
        return R(text='<title>Black hole spins | ESO</title> "https://cdn.eso.org/videos/hd_1080p25_screen/eso2612a.mp4" '
                      '<strong>Credit:</strong><div class="credit"><p>ESO/M. Kornmesser Music: Someone</p></div>')
    monkeypatch.setattr(httpx, "get", get)
    [c] = stock_video._observatory("black hole", 5, "eso")
    assert c["url"].endswith("hd_1080p25_screen/eso2612a.mp4") and c["licence"] == "CC BY 4.0"
    assert c["credit"] == "ESO/M. Kornmesser (CC BY 4.0)"


def test_us_government_films_use_their_own_collection(monkeypatch):
    seen = {}
    def get(url, **kw):
        if "advancedsearch" in url:
            seen["q"] = kw["params"]["q"]
            return R({"response": {"docs": [{"identifier": "f1", "title": "Flood control film"}]}})
        return R({"files": [{"name": "f1.mp4", "format": "h.264", "size": "1000", "width": "640", "height": "480"}]})
    monkeypatch.setattr(httpx, "get", get)
    [c] = stock_video.search("usgov", "", "flood")
    assert "FedFlix" in seen["q"] and c["licence"] == "Public domain (US government work)" and c["site"] == "usgov"


def test_dareful_reads_only_its_own_clips_never_shutterstock_ads(monkeypatch):
    def get(url, **kw):
        if url == "https://dareful.com/":
            return R(text='<a href="https://shutterstock.7eer.net/c/1/2"><video src="https://ak.picdn.net/x.mp4"></video></a>'
                          '<a href="https://dareful.com/sitemap/">s</a><a href="https://dareful.com/crashing-waves-ocean/">c</a>')
        assert url == "https://dareful.com/crashing-waves-ocean/"
        return R(text='<title>Crashing Waves Ocean Royalty Free Stock Video</title><meta itemprop="width" content="1920">'
                      '<meta itemprop="height" content="1080"><a href="https://stream.mux.com/AbC123.m3u8" download class="x">')
    monkeypatch.setattr(httpx, "get", get)
    [c] = stock_video.search("dareful", "", "ocean waves")
    assert c["url"] == "https://stream.mux.com/AbC123/high.mp4" and c["licence"] == "CC BY 4.0"
    assert "picdn" not in c["url"] and c["attribution"].startswith("required")
    assert "dareful" in [n for n, _ in stock_video.topic_sources("calm ocean at sunset")]
