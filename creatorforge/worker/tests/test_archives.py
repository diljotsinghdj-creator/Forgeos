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
    assert names[:4] == ["wikimedia", "nasa", "loc", "archive"] and "openverse" in names
    monkeypatch.setenv("CF_FREE_STOCK", "0")
    assert produce.asset_sources() == []
