# Infographics and data visualisation

How numbers become pictures the viewer understands at speaking pace. Read this for any scene with a figure, a
comparison, a trend or a share, and before designing a chart. Pair it with vox_motion_graphics.md for how charts
move. If the repo's `dataviz` skill is available, use its palette validator for categorical colours.

Labels: [V] source-backed (sources.md, case_studies/) · [I] interpretation · [O] our rule.

---

## 1. What the studied craft shows

- [V] Economic claims are tested against a baseline or a counter-signal rather than asserted: an employment rate that
  stays flat outside recessions, productivity growth that undercuts an automation story, input costs that don't
  explain a price rise (case studies future-of-work-debate-2017, why-everything-so-expensive-2023).
- [V] One ordinary object carries a macro number. The cost of diapers stands in for inflation; a cartoon character's
  career stands in for the median worker (why-everything-so-expensive-2023, homer-simpson-economic-analysis-2016).
- [V] A whole case can rest on one published table (100 jobs, priced), and that table is shared in a companion
  article (homer-simpson-economic-analysis-2016).
- [V] Unit conversions such as "households' worth of electricity" vary between sources. One case study found
  conflicting figures (clean-energy-ai-boom-2024). [O] Verify every conversion and show its basis.
- [V] Atlas pieces combine maps, news clips, photos and data visualisations in one layout (P22).
- [V] Data can be made physical: one producer printed a series of charts on paper and walked through them on camera
  (P19).

## 2. Choosing the chart [O]

| The line says | Use | Don't use |
|---|---|---|
| "X is bigger than Y" | bars, side by side, same baseline | two big numbers far apart |
| "X rose / fell" | a line drawn over time | a before/after pair of numbers with no path |
| "X is N% of Y" | a unit chart or one stacked bar | a pie with more than 3 slices |
| "X is enormous" | a scale comparison with a familiar object | a count-up |
| "X varies by place" | a choropleth or dot map, normalised | a table of countries |
| "X happened after Y" | an annotated timeline | a chart with a legend for events |
| "X causes Y" | a diagram with verb arrows, then the data | a correlation chart alone |
| "Experts disagree" | the two series or estimates side by side, labelled by source | one averaged number |

## 3. Design rules [O]

1. **Label directly, not with legends.** The label sits on the line or bar it names.
2. **One message per chart,** written as the chart's title in plain words ("Prices rose faster than costs"), not the
   variable name.
3. **The key number in the signal colour** (CreatorForge: #FFDD33). Everything else in the base and accent roles.
4. **Honest axes.** Bars start at zero. Line charts may zoom, but the axis is labelled so the zoom is visible. Use the
   same scale for anything compared.
5. **Units with bodies.** Every big number names its unit and, where possible, something the viewer has held, seen or
   walked ("enough to fill 40 stadiums" only if the conversion is verified and in the dossier).
6. **Show uncertainty** when it exists: a range band, "estimate" badge or "up to" phrasing on screen.
7. **Per-capita by default** for comparisons across places of different size, unless the raw total is the point.
8. **Source line on every chart:** organisation, dataset and year, bottom-left.
9. **Phone legibility:** label text at least ~3.5% of frame height; at most about 5 bars or 3 lines.
10. **Count-ups only when the counting is the point** (a timer, money racking up live). Otherwise land the number
    whole and let a comparison give it weight. (BRAIN_LOG 2026-11-11: no counter where the subject should be drawn.)

## 4. The data-to-screen workflow [O]

1. From the dossier, list every number the script uses, with claim id, source, year and status.
2. For each, write the comparison that makes it mean something (its baseline, a counter-signal, a familiar unit).
3. Choose the chart from §2. Sketch it as a frame description in the scene card.
4. Write the build order against the narration (vox_motion_graphics.md §2).
5. Check: the mute test, honest axes, source line, units, badge (ESTIMATE / REPORTED / DISPUTED).
6. Keep the data file next to the blueprint (`data/<claim-id>.csv`) so the graphic can be rebuilt and checked.

## 5. Failure modes

| Failure | Fix |
|---|---|
| Number soup: several figures in one line | One figure per shot; others move to the next shot or are cut |
| A spurious precision such as "4.20 s" or "138 IQ" | Only figures from the dossier; round as the source allows; ILLUSTRATIVE badge for invented examples (BRAIN_LOG 2026-11-10) |
| Chart junk (3D bars, gradients, icons in bars) | Flat marks, direct labels |
| A dual-axis chart | Two charts, or index both to 100 |
| A truncated bar axis | Start at zero |
