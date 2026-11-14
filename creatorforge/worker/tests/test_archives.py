"""The keyless archive sources (Wikimedia Commons, NASA, Library of Congress, Internet Archive): commercial-use
licences only, ledger-ready records, and the studio searching them with no keys set. The services are stood in for."""
import json

import httpx
import pytest

from creatorforge_worker.providers import stock_photo, stock_video
from creatorforge_worker.studio import produce


class Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("x", request=None, response=None)


def fake_get(url, params=None, **kw):
    if "commons.wikimedia.org" in url:
        def page(i, lic, title):
            return {"pageid": i, "index": i, "title": f"File:{title}.jpg", "imageinfo": [{
                "thumburl": f"https://upload.wikimedia.org/{i}.jpg", "thumbwidth": 2400, "thumbheight": 1600,
                "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{i}", "extmetadata": {
                    "LicenseShortName": {"value": lic}, "Artist": {"value": "<a>Jane Doe</a>"},
                    "ImageDescription": {"value": "Aral Sea harbour ships"}, "Categories": {"value": "Aral Sea"}}}]}
        return Resp({"query": {"pages": {"1": page(1, "CC BY-SA 4.0", "Aral Sea ships"), "2": page(2, "CC BY-NC 2.0", "Aral Sea boat"),
                                         "3": page(3, "Public domain", "Aral Sea 1964")}}})
    if "images-api.nasa.gov/search" in url:
        return Resp({"collection": {"items": [
            {"data": [{"nasa_id": "aral1", "title": "Aral Sea shrinking", "description": "Terra view of the Aral Sea", "center": "GSFC"}]},
            {"data": [{"nasa_id": "aral2", "title": "Aral Sea", "description": "© 2010 Someone Else, Aral Sea"}]}]}})
    if "images-api.nasa.gov/asset" in url:
        return Resp({"collection": {"items": [{"href": "http://images-assets.nasa.gov/image/aral1/aral1~orig.jpg"},
                                              {"href": "http://images-assets.nasa.gov/image/aral1/aral1~large.jpg"}]}})
    if "loc.gov" in url:
        return Resp({"results": [
            {"title": "Harbor at Aral Sea", "url": "https://www.loc.gov/item/1/", "id": "1", "image_url": ["//tile.loc.gov/s.jpg", "//tile.loc.gov/l.jpg#h=1"],
             "rights_advisory": "No known restrictions on publication.", "subject": ["aral sea", "harbors"]},
            {"title": "Harbor at Aral Sea, restricted", "url": "https://www.loc.gov/item/2/", "image_url": ["//tile.loc.gov/x.jpg"],
             "rights_advisory": "Rights status not evaluated.", "subject": ["aral sea"]}]})
    return Resp({}, 404)


def test_archive_photos_keep_only_commercial_licences(monkeypatch):
    monkeypatch.setattr(httpx, "get", fake_get)
    w = stock_photo.search("wikimedia", "", "Aral Sea ships", portrait=False)
    assert [x["id"] for x in w] == ["1", "3"]                                    # the non-commercial one is gone
    assert "share alike" in w[0]["attribution"] and w[1]["attribution"] == "not required" and w[0]["creator"] == "Jane Doe"
    n = stock_photo.search("nasa", "", "Aral Sea", portrait=False)
    assert len(n) == 1 and n[0]["url"].endswith("~large.jpg") and n[0]["url"].startswith("https://")   # the © item is skipped
    loc = stock_photo.search("loc", "", "Aral Sea harbor", portrait=False)
    assert len(loc) == 1 and loc[0]["url"] == "https://tile.loc.gov/l.jpg" and "No known restrictions" in loc[0]["licence"]
    for r in w + n + loc:
        assert all(r.get(k) for k in ("page", "creator", "site", "licence", "attribution", "credit")), r
    assert stock_video.search("loc", "", "harbor") == []                          # photo-only sources don't break video search


def test_studio_searches_archives_with_no_keys(monkeypatch):
    for k in ("UNSPLASH_KEY", "CF_UNSPLASH_KEY", "PIXABAY_KEY", "CF_PIXABAY_KEY", "PEXELS_KEY", "CF_PEXELS_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("CF_FREE_STOCK", raising=False)
    names = [n for n, _ in produce.asset_sources()]
    assert names[:6] == ["wikimedia", "nasa", "loc", "smithsonian", "europeana", "archive"] and "openverse" in names
    monkeypatch.setenv("CF_FREE_STOCK", "0")
    assert produce.asset_sources() == []


def test_an_archive_record_beats_an_equal_stock_picture_for_a_specific_subject():
    from creatorforge_worker.studio import assets
    n = assets.Need(scene="S1", film="f", subject="Aral Sea harbour", kind="photo", place="Moynaq", specific=True)
    pic = {"about": "Aral Sea harbour, Moynaq", "width": 3000, "height": 2000}
    a = assets.meta_score({**pic, "site": "wikimedia"}, n, (1920, 1080))
    s = assets.meta_score({**pic, "site": "pixabay"}, n, (1920, 1080))
    assert a["archive"] and a["meta"] > s["meta"]
    g = assets.Need(scene="S1", film="f", subject="harbour", kind="photo")
    assert assets.meta_score({**pic, "site": "wikimedia"}, g, (1920, 1080))["meta"] == assets.meta_score({**pic, "site": "pixabay"}, g, (1920, 1080))["meta"]


def test_smithsonian_europeana_and_flickr_commons_return_only_reusable_records(monkeypatch):
    seen = []

    def get(url, params=None, **kw):
        seen.append((url, dict(params or {})))
        if "api.si.edu" in url:
            def row(i, access):
                return {"id": f"si{i}", "title": "Aral Sea fishing boat", "content": {
                    "descriptiveNonRepeating": {"title": {"content": "Aral Sea fishing boat"}, "record_link": f"https://si.edu/{i}",
                                                "data_source": "National Museum of Natural History",
                                                "online_media": {"media": [{"type": "Images", "content": f"https://ids.si.edu/{i}",
                                                                            "usage": {"access": access},
                                                                            "resources": [{"label": "High-resolution JPEG", "url": f"https://ids.si.edu/{i}/hi.jpg"}]}]}},
                    "freetext": {"date": [{"content": "1965"}]}}}
            return Resp({"response": {"rows": [row(1, "CC0"), row(2, "Usage conditions apply")]}})
        if "api.europeana.eu" in url:
            def item(i, rights):
                return {"id": f"/e/{i}", "title": ["Aral Sea harbour"], "rights": [rights], "edmIsShownBy": [f"https://eu/{i}.jpg"],
                        "dataProvider": ["Some Archive"], "dcCreator": ["A Photographer"], "guid": f"https://europeana.eu/{i}", "year": ["1970"]}
            return Resp({"items": [item(1, "http://creativecommons.org/licenses/by-sa/4.0/"),
                                   item(2, "http://creativecommons.org/licenses/by-nc/4.0/"),
                                   item(3, "http://creativecommons.org/publicdomain/mark/1.0/")]})
        if "api.flickr.com" in url:
            return Resp({"photos": {"photo": [
                {"id": "1", "owner": "o@N", "title": "Aral Sea harbour", "license": "7", "url_l": "https://live.staticflickr.com/1.jpg",
                 "width_l": "2048", "height_l": "1536", "ownername": "Some Library", "description": {"_content": ""}},
                {"id": "2", "owner": "o@N", "title": "Aral Sea harbour", "license": "4", "url_l": "https://x/2.jpg", "width_l": "1024", "height_l": "768"}]}})
        raise AssertionError(url)
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.delenv("SMITHSONIAN_KEY", raising=False)
    monkeypatch.delenv("EUROPEANA_KEY", raising=False)
    monkeypatch.delenv("FLICKR_KEY", raising=False)
    si = stock_photo.search("smithsonian", "", "Aral Sea boat", portrait=False)
    assert [x["url"] for x in si] == ["https://ids.si.edu/1/hi.jpg"] and si[0]["licence"] == "CC0" and si[0]["site"] == "smithsonian"
    assert seen[-1][1]["api_key"] == "DEMO_KEY"
    eu = stock_photo.search("europeana", "", "Aral Sea harbour", portrait=False)
    assert [x["licence"] for x in eu] == ["CC BY-SA", "Public Domain Mark"] and eu[0]["sharealike"] and seen[-1][1]["wskey"] == "api2demo"
    assert stock_photo.search("flickr", "", "Aral Sea harbour", portrait=False) == []          # no key, no search
    fl = stock_photo.search("flickr", "k", "Aral Sea harbour", portrait=False)
    assert [x["id"] for x in fl] == ["1"] and "No known copyright restrictions" in fl[0]["licence"]
    assert {"smithsonian", "europeana"} <= set(stock_photo.FREE_SOURCES)
