"""RETIRED 2026-11-19 (owner: "we need more real pictures, animation, motion graphics etc and less ai"; MASTER_DIRECTIVES 8c).
The AI plates P1-P6 are no longer used; see data/ai_ledger.json ("retired"). This file is kept so the build order in
films/RESTORE.md still works: it builds the replacements instead.
  P1 desk      -> the drawn walnut desk (frames.py DESK)
  P2 02a_siege -> real 19th-century engraving (real_frames.py)
  P3 08a_ship  -> the Portus relief, Torlonia collection (real_frames.py)
  P4 10a_sack  -> a real sack of pepper (real_frames.py)
  P5 13a_relay -> animated map from Natural Earth data (motion_maps.py)
  P6 14a_demotion -> NGA Index of American Design watercolour + photo (real_frames.py)
Run after comedy.py."""
import real_frames  # noqa: F401
import motion_maps  # noqa: F401
