import json, sys
from pathlib import Path
sys.path.insert(0, "/home/user/Forgeos/creatorforge/worker")
from taxonomy import box_plot, unit_grid, node_canvas, globe, ICONS
D = Path(__file__).resolve().parent
H = D / "html"; H.mkdir(exist_ok=True)
for n in ["flag", "temperature", "wind", "mountain", "flame", "cloud-fog", "calendar", "snowflake", "building-skyscraper", "car"]:
    assert n in ICONS, n
# [2D-BOX]: Mauna Loa monthly CO2 by decade (NOAA)
rows = [l.split() for l in (D / "data" / "co2_mm_mlo.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
mm = [(int(r[0]), float(r[3])) for r in rows if float(r[3]) > 0]
groups = []
for dec in range(1960, 2030, 10):
    v = [x for y, x in mm if dec <= y < dec + 10]
    groups.append((f"{dec}s" if dec < 2020 else "2020s*", v))
last = max(y for y, _ in mm)
src = f"SOURCE: NOAA GLOBAL MONITORING LABORATORY, CO2_MM_MLO.TXT (MONTHLY MEAN, MAUNA LOA) · *2020s = JAN 2020 TO {rows[-1][1]}/{rows[-1][0]}"
for t in (.45, 1.0):
    (H / f"box_co2_{int(t*100):03d}.html").write_text(box_plot(groups, "EVERY MONTH, EVERY DECADE", "The air's carbon, month by month", "CO₂, PARTS PER MILLION", src, t=t, lo=310, hi=440))
# [2D-UNIT]: 193 UN member states, 54 of them in Africa
src_u = "SOURCES: UNITED NATIONS (193 MEMBER STATES); AFRICAN UNION MISSION TO THE UN (54 AFRICAN UN MEMBERS) · ONE FLAG = ONE STATE, ORDER ILLUSTRATIVE"
for t in (.45, 1.0):
    (H / f"unit_un_{int(t*100):03d}.html").write_text(unit_grid(193, 54, "193 COUNTRIES", "One flag for every UN member", "flag", src_u, cols=22, t=t, lit_label="OF THEM ARE IN AFRICA"))
# [25D-NODE]: the Delhi bowl chain (NASA Earth Observatory, 3 Nov 2024)
nodes = {"nov": (500, 600, "calendar", "LATE OCT – NOV", "the season it happens"),
         "cold": (1150, 360, "snowflake", "COLDER NIGHTS", "falling temperatures"),
         "wind": (1150, 860, "wind", "SLOW WINDS", "less mixing"),
         "tibet": (1850, 260, "mountain", "COLD AIR", "rolls off the Tibetan Plateau"),
         "lid": (2000, 640, "temperature", "INVERSION", "warm layer on top, a lid"),
         "smoke": (2050, 1150, "flame", "SMOKE & DUST", "from many sources"),
         "trap": (2800, 760, "cloud-fog", "TRAPPED HAZE", "held near the ground"),
         "bowl": (3400, 420, "mountain", "HEMMED IN", "Himalaya north, Vindhya south"),
         "city": (3450, 1150, "building-skyscraper", "DELHI", "breathes what stays")}
edges = [("nov", "cold"), ("nov", "wind"), ("cold", "lid"), ("tibet", "lid"), ("wind", "trap"), ("lid", "trap"), ("smoke", "trap"), ("bowl", "trap"), ("trap", "city")]
src_n = "THE CHAIN: NASA EARTH OBSERVATORY, 'SMOKY SKIES OVER THE INDO-GANGETIC PLAIN', 3 NOV 2024 · DIAGRAM DRAWN IN THE STUDIO"
(H / "node_a.html").write_text(node_canvas(nodes, edges, (1200, 640, .95), "WHY THE AIR STAYS", src_n, t=.45, focus="lid"))
(H / "node_b.html").write_text(node_canvas(nodes, edges, (2900, 820, .95), "WHY THE AIR STAYS", src_n, t=1.0, focus="trap"))
(H / "node_c.html").write_text(node_canvas(nodes, edges, (2000, 760, .42), "WHY THE AIR STAYS", src_n, t=1.0, focus="city"))
# [3D-GLOBE]: Delhi to London great circle, globe -> flat map
from creatorforge_worker.media import maps
india = [[(lo, la) for lo, la in r] for r in maps._find("India")["rings"] if len(r) > 3]
src_g = "IMAGERY: NASA BLUE MARBLE NEXT GENERATION VIA GIBS (PUBLIC DOMAIN) · INDIA: OFFICIAL BOUNDARY · ROUTE: SHORTEST PATH ON THE SPHERE"
for m, spin in ((0.0, 50), (0.5, 40), (1.0, 40)):
    (H / f"globe_{int(m*100):03d}.html").write_text(globe(m, spin, [(77.21, 28.61), (-0.13, 51.51)], india, "THE SHORT WAY", "Delhi to London",
                                                       src_g, labels=[(77.21, 28.61, "DELHI"), (-0.13, 51.51, "LONDON")]))
print(sorted(p.name for p in H.iterdir()))
