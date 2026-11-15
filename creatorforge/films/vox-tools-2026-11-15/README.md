# Vox tools, first samples (2026-11-15)

New studio tools from the owner's reference study, all free and open:
- **Glowing relief map** (`relief.py`): real terrain from the Terrarium elevation tiles (Mapzen/Tilezen, AWS Open Data; SRTM), one country lit, a glowing route, three.js bloom. The Grand Canyon river line is traced as the lowest path through the terrain.
- **Physics** (`physics.py`): Rapier (Apache-2.0) rigid bodies: Galton board, domino chain, tower collapse.
- **Blueprint cutaway** (`scenes3d.py`): simplified wind-turbine nacelle, labelled, generator glowing.
- **Glow on one fact** (`scenes3d.py`): 3D bars of NOAA Mauna Loa CO2 annual means (data/co2_annmean_mlo.txt), bars from zero, 2025 lit.
- **Stroke-by-stroke drawing** (`drawing.py`): ink paths revealed in order with a pen at the tip.

Vendored in the worker: three.js 0.160 modules + addons (MIT), Rapier 3D compat 0.21 (Apache-2.0).
Render: `python3 relief.py; python3 physics.py; python3 scenes3d.py; python3 drawing.py; python3 shoot.py`.
