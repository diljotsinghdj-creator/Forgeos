"""Five more original Print Facts logo concepts (D-H), board + corner mark on the dark Vox frame."""
from pathlib import Path
from logos import FONTS, SIG, INK, PAPER

H = Path("html")
RED = "#C8312B"
FONTS2 = FONTS + "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Marker", "permanent-marker-latin-400-normal"), ("Caveat", "caveat-latin-700-normal"), ("Grotesk", "space-grotesk-latin-700-normal")))


def logo(kind, s=1.0, dark=True):
    fg = "#F3EFE6" if dark else INK
    bg = "#0E1013" if dark else PAPER
    if kind == "D":   # the highlighter: the name with a marker swipe and a hand tick
        return (f'<div style="display:inline-flex;align-items:center;gap:{10 * s:.0f}px"><div style="white-space:nowrap;font:700 {34 * s:.0f}px/1 Grotesk;letter-spacing:{-.5 * s:.1f}px;color:{fg}">'
                f'PRINT <span style="color:{INK};background:linear-gradient(100deg,transparent 2%,{SIG} 4%,{SIG} 94%,transparent 97%);padding:0 {6 * s:.0f}px">FACTS</span></div>'
                f'<svg width="{34 * s:.0f}" height="{30 * s:.0f}" viewBox="0 0 34 30"><path d="M3 16 L12 25 L31 4" fill="none" stroke="{SIG}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
    if kind == "E":   # the footnote: a citation mark, the promise in the footnote
        return (f'<div style="display:inline-block"><div style="font:900 {36 * s:.0f}px/1 Playfair;color:{fg}">Print Facts<sup style="font:500 {18 * s:.0f}px Plex;color:{SIG};vertical-align:{14 * s:.0f}px;margin-left:{3 * s:.0f}px">[1]</sup></div>'
                f'<div style="border-top:{1.5 * s:.1f}px solid {fg};opacity:.7;width:{120 * s:.0f}px;margin-top:{6 * s:.0f}px"></div>'
                f'<div style="font:500 {10 * s:.0f}px Plex;color:{fg};opacity:.8;margin-top:{3 * s:.0f}px">[1] every fact has a source</div></div>')
    if kind == "F":   # the folded page: a black square sheet with a yellow dog-ear
        sz = 64 * s
        return (f'<div style="display:inline-flex;align-items:center;gap:{12 * s:.0f}px"><div style="position:relative;width:{sz:.0f}px;height:{sz:.0f}px;background:{fg if not dark else "#F3EFE6"};'
                f'clip-path:polygon(0 0,70% 0,100% 30%,100% 100%,0 100%)"><div style="position:absolute;right:0;top:0;width:{sz * .3:.0f}px;height:{sz * .3:.0f}px;background:{SIG};'
                f'clip-path:polygon(0 0,0 100%,100% 100%)"></div><div style="position:absolute;left:{8 * s:.0f}px;bottom:{6 * s:.0f}px;font:400 {30 * s:.0f}px/1 Anton;color:{bg}">PF</div></div>'
                f'<div style="font:500 {20 * s:.0f}px/1.15 Plex;letter-spacing:{3 * s:.1f}px;color:{fg}">PRINT<br>FACTS</div></div>')
    if kind == "G":   # the typewriter key: two round keys, P and F
        key = lambda ch, c, t: (f'<div style="width:{44 * s:.0f}px;height:{44 * s:.0f}px;border-radius:50%;background:{c};border:{3 * s:.0f}px solid {fg};'
                                f'display:flex;align-items:center;justify-content:center;font:500 {22 * s:.0f}px Plex;color:{t};box-shadow:0 {4 * s:.0f}px 0 {fg}"><b>{ch}</b></div>')
        return (f'<div style="display:inline-flex;align-items:center;gap:{8 * s:.0f}px">{key("P", bg, fg)}{key("F", SIG, INK)}'
                f'<div style="font:500 {18 * s:.0f}px/1.2 Plex;letter-spacing:{4 * s:.1f}px;color:{fg};margin-left:{8 * s:.0f}px">PRINT<br>FACTS</div></div>')
    if kind == "H":   # the evidence pin: a pushpin and a string under the name
        return (f'<div style="display:inline-block;position:relative;padding-left:{30 * s:.0f}px">'
                f'<svg style="position:absolute;left:0;top:{2 * s:.0f}px" width="{26 * s:.0f}" height="{40 * s:.0f}" viewBox="0 0 26 40"><circle cx="13" cy="11" r="10" fill="{RED}"/>'
                f'<circle cx="10" cy="8" r="3" fill="#FF8A80"/><line x1="13" y1="20" x2="13" y2="38" stroke="{fg}" stroke-width="2.5"/></svg>'
                f'<div style="font:400 {36 * s:.0f}px/1 Anton;letter-spacing:{1.5 * s:.1f}px;color:{fg}">PRINT FACTS</div>'
                f'<svg width="{190 * s:.0f}" height="{14 * s:.0f}" viewBox="0 0 190 14"><path d="M0 4 Q 60 14 120 6 T 190 8" fill="none" stroke="{SIG}" stroke-width="3.5"/></svg></div>')


NAMES = {"D": "D · THE HIGHLIGHTER", "E": "E · THE FOOTNOTE", "F": "F · THE FOLDED PAGE", "G": "G · THE TYPEWRITER KEYS", "H": "H · THE EVIDENCE PIN"}
cells = ""
for i, k in enumerate("DEFGH"):
    x = 40 + i * 372
    cells += (f'<div style="position:absolute;left:{x}px;top:120px;width:352px;height:360px;background:#0E1013;display:flex;align-items:center;justify-content:center">{logo(k, 1.2 if k == 'D' else 1.55)}</div>'
              f'<div style="position:absolute;left:{x}px;top:500px;width:352px;height:360px;background:{PAPER};display:flex;align-items:center;justify-content:center">{logo(k, 1.2 if k == 'D' else 1.55, False)}</div>'
              f'<div style="position:absolute;left:{x}px;top:880px;font:500 19px Plex;letter-spacing:3px;color:{INK}">{NAMES[k]}</div>')
(H / "logo_board2.html").write_text(
    f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS2}body{{margin:0;width:1920px;height:1080px;background:#DCD6C8;position:relative;overflow:hidden}}</style></head><body>'
    f'<div style="position:absolute;left:40px;top:40px;font:400 54px Anton;color:{INK}">PRINT FACTS · MORE LOGO CONCEPTS (ORIGINAL)</div>{cells}'
    f'<div style="position:absolute;left:40px;top:990px;font:500 18px Plex;color:#555">Drawn in the studio from the channel\'s own fonts and signature yellow. Corner mark only, never an intro.</div>'
    '<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>')
src = (H / "look_dark_vox.html").read_text()
for k in "DEFGH":
    (H / f"look_dark_vox_logo{k}.html").write_text(src.replace("</body>", f'<style>{FONTS2}</style><div style="position:absolute;left:70px;top:92px;z-index:60">{logo(k, 1.45)}</div></body>', 1))
print("ok")
