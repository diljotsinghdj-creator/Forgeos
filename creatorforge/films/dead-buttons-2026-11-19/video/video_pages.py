#!/usr/bin/env python3
"""Video-only copies of the four trap pages (01_press, 02_again, 03_now, 25_last) -> html/<name>_v.html.
The key frames carry storyboard notes for the owner ("[WAIT 3.5 S] LAMP 1 -> +3.5 S", "NO CLICK. NO LAMP."). On screen in the
film they would tell the viewer the trick before the trap has sprung, so the video copies drop them. On 01-03 (before the
reveal) the source line also drops its first clause, which says the lamps run on a timer; the reveal (16) states it in full.
01's PRESS WHEN READY tag moves from under the plate to above it, clear of the burned captions. Nothing else changes.
Run after frames.py:  python3 video/video_pages.py"""
import re
from pathlib import Path

H = Path(__file__).resolve().parent.parent / "html"
NOTE = re.compile(r'<div class="a" data-anim="fade \.3 \.4" style="left:1420px;top:420px;z-index:60"><div style="[^"]*">\[WAIT.*?</div></div>', re.S)
SPOIL = "THE VIEWER TRAP ([SIMULATE]): THE LAMPS RUN ON A TIMER KEYED TO THE NARRATION, NOT TO THE VIEWER · "
for name in ("01_press", "02_again", "03_now", "25_last"):
    s = (H / f"{name}.html").read_text(encoding="utf-8")
    s, n = NOTE.subn("", s)
    assert n == 1, (name, n)
    if name != "25_last":
        assert SPOIL in s, name
        s = s.replace(SPOIL, "")
    if name == "01_press":
        a = 'data-anim="up .2 .3" style="left:640px;top:970px;'
        assert a in s
        s = s.replace(a, 'data-anim="up .2 .3" style="left:704px;top:72px;')
    (H / f"{name}_v.html").write_text(s, encoding="utf-8")
    print("video page", name + "_v")
