"""Three original Print Facts logo concepts (not Vox's mark), shown on a board and as a small corner bug on the two
Vox-layer frames. Signature yellow #FFDD33 is the channel's own colour."""
from pathlib import Path

H = Path("html")
SIG, INK, PAPER = "#FFDD33", "#141414", "#F3EEDF"
FONTS = "".join(f"@font-face{{font-family:{n};src:url(/fonts/{f}.woff2)}}" for n, f in (
    ("Anton", "anton-latin-400-normal"), ("Plex", "ibm-plex-mono-latin-500-normal"), ("Playfair", "playfair-display-latin-900-normal")))


def logo(kind, s=1.0, dark=True):
    fg = "#F3EFE6" if dark else INK
    if kind == "A":   # the stamp: a rubber-stamp box, typewriter caps, a ruled line like a printed form
        return (f'<div style="display:inline-block;border:{3 * s:.0f}px solid {fg};padding:{6 * s:.0f}px {12 * s:.0f}px {7 * s:.0f}px;transform:rotate(-2deg)">'
                f'<div style="font:500 {11 * s:.0f}px Plex;letter-spacing:{4 * s:.1f}px;color:{fg};border-bottom:{2 * s:.0f}px solid {SIG};padding-bottom:{3 * s:.0f}px">FACT FILE</div>'
                f'<div style="font:400 {34 * s:.0f}px/1 Anton;letter-spacing:{2 * s:.1f}px;color:{fg};margin-top:{4 * s:.0f}px">PRINT FACTS</div></div>')
    if kind == "B":   # the registration mark: a printer's crosshair with PF, the name beside it
        r = 26 * s
        return (f'<div style="display:inline-flex;align-items:center;gap:{12 * s:.0f}px"><svg width="{2 * r + 8:.0f}" height="{2 * r + 8:.0f}" viewBox="0 0 {2 * r + 8:.0f} {2 * r + 8:.0f}">'
                f'<circle cx="{r + 4:.0f}" cy="{r + 4:.0f}" r="{r * .78:.0f}" fill="{SIG}"/><line x1="0" y1="{r + 4:.0f}" x2="{2 * r + 8:.0f}" y2="{r + 4:.0f}" stroke="{fg}" stroke-width="{2 * s:.1f}"/>'
                f'<line x1="{r + 4:.0f}" y1="0" x2="{r + 4:.0f}" y2="{2 * r + 8:.0f}" stroke="{fg}" stroke-width="{2 * s:.1f}"/>'
                f'<text x="{r + 4:.0f}" y="{r + 4 + 9 * s:.0f}" text-anchor="middle" font-family="Anton" font-size="{25 * s:.0f}" fill="{INK}">PF</text></svg>'
                f'<div style="font:400 {30 * s:.0f}px/0.9 Anton;letter-spacing:{1.5 * s:.1f}px;color:{fg}">PRINT<br>FACTS</div></div>')
    if kind == "C":   # the press slug: a serif word set like a newspaper nameplate, with a yellow ink bar
        return (f'<div style="display:inline-block;text-align:left"><div style="font:900 {34 * s:.0f}px/1 Playfair;color:{fg};letter-spacing:{.5 * s:.1f}px">Print Facts</div>'
                f'<div style="height:{6 * s:.0f}px;background:{SIG};margin-top:{4 * s:.0f}px;width:78%"></div>'
                f'<div style="font:500 {10 * s:.0f}px Plex;letter-spacing:{3.5 * s:.1f}px;color:{fg};margin-top:{4 * s:.0f}px;opacity:.8">SOURCED · CHECKED · SHOWN</div></div>')


# the board: three concepts large, on dark and on paper
cells = ""
for i, k in enumerate("ABC"):
    name = {"A": "A · THE STAMP", "B": "B · THE REGISTRATION MARK", "C": "C · THE NAMEPLATE"}[k]
    cells += (f'<div style="position:absolute;left:{60 + i * 610}px;top:120px;width:570px;height:380px;background:#0E1013;display:flex;align-items:center;justify-content:center">{logo(k, 2.2)}</div>'
              f'<div style="position:absolute;left:{60 + i * 610}px;top:520px;width:570px;height:380px;background:{PAPER};display:flex;align-items:center;justify-content:center">{logo(k, 2.2, dark=False)}</div>'
              f'<div style="position:absolute;left:{60 + i * 610}px;top:920px;font:500 22px Plex;letter-spacing:4px;color:{INK}">{name}</div>')
board = (f'<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}body{{margin:0;width:1920px;height:1080px;background:#DCD6C8;position:relative;overflow:hidden}}</style></head><body>'
         f'<div style="position:absolute;left:60px;top:40px;font:400 54px Anton;color:{INK}">PRINT FACTS · LOGO CONCEPTS (ORIGINAL, FOR THE OWNER TO PICK)</div>{cells}'
         f'<div style="position:absolute;left:60px;top:990px;font:500 18px Plex;color:#555">Drawn in the studio from the channel\'s own fonts and signature yellow. Used as a small corner mark, never as an intro.</div>'
         '<script>document.fonts.ready.then(()=>window.READY=true)</script></body></html>')
(H / "logo_board.html").write_text(board)

# the corner bug on the two Vox frames (top left, above the title, inside the Shorts safe area)
for page in ("look_dark_vox", "look_holo_vox"):
    src = (H / f"{page}.html").read_text()
    for k in "ABC":
        bug = f'<style>{FONTS}</style><div style="position:absolute;left:70px;top:88px;z-index:60;opacity:.95">{logo(k, 1.45)}</div>'
        (H / f"{page}_logo{k}.html").write_text(src.replace("</body>", bug + "</body>", 1))
print("ok")
