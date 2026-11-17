"""India in its official boundary, islands included: DataMeet India composite (CC BY 4.0), as used by the studio before.
Rings are [(lon, lat)], thinned for drawing (every `step`-th point on long rings)."""
import json
SRC = "/home/user/Forgeos/creatorforge/films/bjp-it-cell-10min/collage/assets/india-composite.geojson"
CREDIT = "INDIA: OFFICIAL BOUNDARY, DATAMEET INDIA COMPOSITE (CC BY 4.0)"


def rings(step=40):
    g = json.load(open(SRC))
    geoms = [f["geometry"] for f in g["features"]] if "features" in g else [g]
    out = []
    for ge in geoms:
        polys = ge["coordinates"] if ge["type"] == "MultiPolygon" else [ge["coordinates"]]
        for p in polys:
            r = p[0]
            k = step if len(r) > 2000 else max(1, step // 10) if len(r) > 200 else 1
            out.append([(round(x, 4), round(y, 4)) for x, y in r[::k]])
    return out
