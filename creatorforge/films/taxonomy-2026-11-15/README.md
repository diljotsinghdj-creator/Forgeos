# Taxonomy: the four missing asset types (2026-11-15)

`taxonomy.py` holds reusable generators; `samples.py` renders the samples; `shoot.py` screenshots them.

| Code | Generator | Sample | Data |
|---|---|---|---|
| `[2D-BOX]` | `box_plot(groups, ...)`: whiskers, box, median, every value as a dot; rows wipe in at 12 fps | Mauna Loa CO2 by decade | NOAA GML co2_mm_mlo.txt (monthly mean) |
| `[2D-UNIT]` | `unit_grid(n, lit, ...)`: icons pop in at 12 fps, a counter ticks, then the subset lights | 193 UN members, 54 in Africa | UN; African Union mission to the UN |
| `[25D-NODE]` | `node_canvas(nodes, edges, cam, ...)`: 4000x2400 canvas, the camera pans and zooms, edges draw in order, one node lit | why the air stays (Delhi) | NASA Earth Observatory, 3 Nov 2024 |
| `[3D-GLOBE]` | `globe(morph, spin_lon, route, outline, ...)`: textured globe morphing to a flat map, great-circle route, India official outline | Delhi to London | NASA Blue Marble NG via GIBS |
