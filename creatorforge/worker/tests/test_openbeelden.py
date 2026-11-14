"""Open Beelden: open-licence films only, English words found in Dutch metadata, local index before Commons."""
import gzip
import json

import httpx

from creatorforge_worker.providers import openbeelden, stock_video

REC = """<record><header><identifier>oai:openimages.eu:{id}</identifier></header><metadata>
<oi:title xml:lang="nl">{title}</oi:title><oi:subject>{subj}</oi:subject><oi:description>{desc}</oi:description>
<oi:date>1953-02-01</oi:date><oi:medium format="hd">https://www.openbeelden.nl/files/{id}.mp4</oi:medium>
<oi:attributionName>Polygoon / Beeld en Geluid</oi:attributionName><oi:license>{lic}</oi:license></metadata></record>"""


def test_harvest_keeps_open_licences_and_follows_the_token(tmp_path, monkeypatch):
    pages = [REC.format(id=1, title="Watersnood in Zeeland", subj="overstromingen", desc="dijken breken",
                        lic="https://creativecommons.org/publicdomain/mark/1.0/")
             + REC.format(id=2, title="Reclame", subj="", desc="", lic="https://creativecommons.org/licenses/by-nc-sa/3.0/")
             + "<resumptionToken>t1</resumptionToken>",
             REC.format(id=3, title="Verkiezingen 1956", subj="verkiezingen", desc="stemmen",
                        lic="https://creativecommons.org/licenses/by-sa/3.0/nl/")]
    calls = []

    class R:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def get(url, params=None, **kw):
        calls.append(dict(params))
        return R(pages[len(calls) - 1])
    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr(openbeelden.time, "sleep", lambda s: None)
    out = tmp_path / "ix.jsonl.gz"
    assert openbeelden.harvest(out, log=lambda m: None) == 2                    # the NC film is dropped
    assert calls[1] == {"verb": "ListRecords", "resumptionToken": "t1"}
    rows = [json.loads(x) for x in gzip.open(out, "rt", encoding="utf-8")]
    assert [r["id"] for r in rows] == ["1", "3"]


def test_english_query_finds_dutch_film(monkeypatch):
    monkeypatch.setattr(openbeelden, "_cache", [
        {"id": "1", "title": "Watersnood in Zeeland", "date": "1953-02-01", "about": "dijken breken", "subjects": ["overstromingen"],
         "places": ["Zeeland"], "licence": "https://creativecommons.org/publicdomain/mark/1.0/", "mp4": "https://x/1.mp4",
         "attribution": "Polygoon / Beeld en Geluid"},
        {"id": "2", "title": "Voetbal", "date": "1960", "about": "", "subjects": [], "places": [],
         "licence": "https://creativecommons.org/licenses/by-sa/3.0/", "mp4": "https://x/2.mp4", "attribution": "B&G"}])
    [c] = openbeelden.search("flood")
    assert c["id"] == "1" and c["credit"].endswith("Open Beelden, 1953") and c["attribution"] == "not required"
    assert openbeelden.search("flood football") == []                           # every word must match


def test_provider_uses_local_index_before_commons(monkeypatch):
    monkeypatch.setattr(openbeelden, "search", lambda q: [{"url": "u", "id": "1"}])
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no Commons call")))
    assert stock_video.search("openbeelden", "", "flood") == [{"url": "u", "id": "1"}]
