# Maps and geography

Maps are the most used explanatory device in the studied work and the most tedious to make well (P8). Read this for
any scene about a place, a route, a border, a spread or a distance, and when geography leads a film.

Labels: [V] source-backed (sources.md, case_studies/) · [I] interpretation · [O] our rule.

---

## 1. What the studied craft shows

- [V] Map-led series (Atlas) use maps with animation on top, combined with news clips, photos and data, at about ten
  minutes (P22).
- [V] The producer works visuals-first and starts from maps cartographers have already made. For one historical piece
  he traced maps from old books rather than using geodata. That piece took about five weeks (P22).
- [V] Some stories are chosen *because* they can only be explained by drawing them on a map: "hard to explain without
  drawing it on a napkin" (P9).
- [V] 3D globe and terrain moves come from Google Earth Studio: slow orbits mimicking drone surveillance over a site,
  and zooms to a specific building. Frames go to After Effects, linked to a master world map and annotated (P23).
- [V] Earth Studio moves were also used to plan real drone flights: map moves as previs for the shoot (P23).
- [V] Experts shape the map's nuance, for example that the money is loans to be repaid, not aid (P9). The best expert
  source also has the data to map: a think tank's database of ports and railways (P9).
- [V] The film toggles between the bird's-eye map and what is happening on the ground, because ten minutes of map
  alone doesn't hold; labels and boxes are animated over aerial or drone footage to sync the two (P22).
- [V] Building a map from a dataset: find the data's geographic unit (e.g. census tracts), download the matching
  shapes, join data to shapes, make one city work, then point the same build at the others (P26).
- [V] Maps are among the most tedious graphics because borders change; other staff help check them (P8).
- [V] Case studies in the history and geography set show maps carrying arguments about borders, capitals and
  settlement (see case_studies/INDEX.md: divided-island, Egypt's capital, Nevada ghost towns, South China Sea).

## 2. The map kit [O]

| Move | Purpose | Spec |
|---|---|---|
| **Globe dive** | Locate an unfamiliar place | Start at the globe with the region centred; dive in 2–3 stages (continent → country → site) with labels appearing at each stage; under 5 s total |
| **Locator inset** | Keep orientation during a close-up | A small globe or country outline in a corner, with a dot, for the whole scene |
| **Border draw-on** | A border, a claim, a line that matters | A mask follows the line at narration speed; the line weight is heavier than other boundaries; disputed lines are dashed and badged |
| **Route animation** | Movement, trade, migration, a journey | A path draws from origin to destination with a moving head; duration matches the narration phrase; distance labelled at the end |
| **Spread / flow** | Diffusion, flows of goods or people | Flow lines with thickness proportional to volume (from the dossier); animate in order of time |
| **Choropleth** | A value by region | A sequential single-hue ramp; per capita; a legend with the range; regions fill on the word |
| **Dot / symbol map** | Locations of many things | One dot per item (or per N items, stated); dots appear in time order if time matters |
| **Satellite before/after** | Physical change | Same framing, a wipe between dates, dates labelled on each side; source (e.g. Sentinel, Landsat, NASA) on screen |
| **Terrain 3D** | Mountains, valleys, rivers that explain a story | Exaggerate relief only with a label saying so; a slow orbit; the key feature is labelled when the camera reaches it |
| **Historical map overlay** | How a place used to be divided | The old map registered over the modern base and cross-faded; the period and source labelled |
| **Scale overlay** | How big is it | Drag a familiar outline (a city, a country the audience knows) over the subject at true scale |

## 3. Cartographic honesty [O]

- **Projection:** say nothing with a projection that it can't support. For world comparisons of size use an
  equal-area projection, or a globe. Mercator inflates high latitudes.
- **Disputed borders:** show the claim lines of each side, labelled by who claims them; never pick a side by default.
  The DISPUTED badge goes on screen.
- **Names:** use the names in common English usage and note local or contested names when they matter to the story.
- **Data:** every choropleth or flow cites its source and year on screen.
- **No flags or emblems as decoration** (CreatorForge). Country colours come from the film palette, not from flags.

## 4. Map style per film [O]

The base map's look is part of each film's DNA, taken from the subject. Some contrasts:
- an investigation into a smuggling route: dark base, satellite texture, thin ink lines, evidence pins;
- a history of a canal: survey-map paper, hand-inked river, period type;
- a story about heat: a clean light base, with temperature as the only colour.

Keep consistent within a film: one base style, one label face, one line weight family, one way to mark "here".

## 5. Workflow [O]

1. List every place, route and border the script names, with claim ids.
2. Find base material: open data (Natural Earth, OpenStreetMap, with attribution), satellite archives (NASA, ESA
   Sentinel, USGS Landsat), historical maps (Library of Congress, David Rumsey collection, national archives), with
   licences in the asset register.
3. Plan the camera path as one continuous journey where possible, so the viewer never loses where they are.
4. Draft the labels: the fewest that let a viewer follow (a place is labelled the first time it matters, then only
   when it returns).
5. Check the mute test: can a viewer with no sound say where we are and what moved?

## 6. Failure modes

| Failure | Fix |
|---|---|
| A flat pin map where terrain or distance is the story | Terrain 3D or the globe dive (BRAIN_LOG 2026-11-11) |
| Too many labels at once | Label on the word, remove when no longer needed |
| Losing the viewer after a cut to a close map | Locator inset, or continuous flight |
| Raw totals on a choropleth | Per capita, or say why the total matters |
| The same map look in every film | Take the base style from the subject |
