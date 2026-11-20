"""Map box and projection for the light table (Web Mercator), and the Natural Earth extract.
Run `python3 -I geo.py` once: it reads the downloaded Natural Earth GeoJSON in maps/ (untrusted data: only numbers and a few
known names are kept) and writes maps/shapes.json (projected map-pixel paths) for frames.py."""
import json
import math
from pathlib import Path

D = Path(__file__).resolve().parent
BOX = (-80.0, -30.0, -54.0, -6.0)          # lon0, lat0, lon1, lat1
MW = 2000


def merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


_KX = MW / math.radians(BOX[2] - BOX[0])
MH = round(_KX * (merc(BOX[3]) - merc(BOX[1])))


def P(lon, lat):
    """lon/lat -> map pixels on the relief image."""
    return (math.radians(lon - BOX[0]) * _KX, (merc(BOX[3]) - merc(lat)) * _KX)


KEEP = ("Bolivia", "Chile", "Peru", "Argentina", "Brazil", "Paraguay", "Ecuador", "Colombia", "Uruguay")
RIVERS = ("Mamoré", "Guaporé", "Madeira", "Madre de Dios", "Pilcomayo", "Paraná")


def _rings(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "Polygon":
        return [c[0]]
    if t == "MultiPolygon":
        return [p[0] for p in c]
    if t == "LineString":
        return [c]
    if t == "MultiLineString":
        return list(c)
    return []


def _path(rings, close=True):
    out = []
    for r in rings:
        pts = [P(float(x), float(y)) for x, y, *_ in r if -95 < float(x) < -40 and -45 < float(y) < 10]
        if len(pts) < 2:
            continue
        out.append("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + ("Z" if close else ""))
    return "".join(out)


if __name__ == "__main__":
    M = D / "maps"
    shapes = {"MW": MW, "MH": MH, "countries": {}, "lakes": {}, "rivers": {}, "coast_litoral": []}
    for f in json.loads((M / "ne_50m_admin_0_countries.geojson").read_text())["features"]:
        n = str(f["properties"].get("NAME"))
        if n in KEEP:
            shapes["countries"][n] = _path(_rings(f["geometry"]))
    for f in json.loads((M / "ne_50m_lakes.geojson").read_text())["features"]:
        if f["properties"].get("name") == "Lago Titicaca":
            shapes["lakes"]["Titicaca"] = _path(_rings(f["geometry"]))
    for f in json.loads((M / "ne_50m_rivers_lake_centerlines.geojson").read_text())["features"]:
        n = str(f["properties"].get("name"))
        if n in RIVERS and f["geometry"]:
            shapes["rivers"][n] = shapes["rivers"].get(n, "") + _path(_rings(f["geometry"]), close=False)
    # the Pacific coast between 20.8 S and 25.2 S (for the schematic Litoral strip), from the coastline layer
    pts = []
    for f in json.loads((M / "ne_50m_coastline.geojson").read_text())["features"]:
        for r in _rings(f["geometry"]):
            for x, y, *_ in r:
                x, y = float(x), float(y)
                if -25.2 <= y <= -20.8 and -71.5 < x < -69.5:
                    pts.append((x, y))
    pts.sort(key=lambda p: -p[1])
    shapes["coast_litoral"] = pts
    (M / "shapes.json").write_text(json.dumps(shapes))
    print({k: (len(v) if not isinstance(v, int) else v) for k, v in shapes.items()}, list(shapes["countries"]), list(shapes["rivers"]))
