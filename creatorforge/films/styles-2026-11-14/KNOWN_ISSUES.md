# Found while rendering every style (2026-11-14)

- **Fixed:** satellite before/after crashed on relative file paths (media/photo.py).
- **Movement arrows (map 009):** labels collide when two origins are close (LONDON over AMSTERDAM). To fix in the arrows layout.
- **Person lookup:** a vague name ("person:A") fetched a stranger's photo. A person scene must show a real person only
  when the name is exact and the photo record matches; otherwise the empty PHOTO / Name frame. To fix in cutouts.
- **Object search:** "rupee note" returned a US dollar note (picture line chart 037, then-vs-now 039). Object
  searches need a check that the result matches the words that matter (currency, country). To fix in cutouts.
- **Historical borders:** the dated maps folder defaults to a path relative to where the studio starts
  (creatorforge-data/history); set CF_HISTORY to an absolute path on the pod.
