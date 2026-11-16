"""John Oliver layer on the pepper frames (draft 4): archive-tag sarcastic captions, a smash-zoom receipt, and a
cut-out sight gag. Injected into the rendered pages; every caption sits on a sourced fact."""
from pathlib import Path
H = Path("html")
SIG, RED, INK = "#F7D046", "#D93829", "#1A1A1A"
FONT = "<style>@font-face{font-family:PlexC;src:url(/fonts/ibm-plex-mono-latin-500-normal.woff2)}@font-face{font-family:CaveatC;src:url(/fonts/caveat-latin-700-normal.woff2)}</style>"


def tag(text, x, y, rot=-1.5, dark=False):
    bg, fg = ("#1A1A1A", "#F4EFE6") if not dark else ("#F4EFE6", "#1A1A1A")
    return (f'<div style="position:absolute;left:{x}px;top:{y}px;z-index:70;background:{bg};color:{fg};border:2px solid {fg};padding:8px 14px;'
            f'font:500 20px PlexC;letter-spacing:4px;transform:rotate({rot}deg);box-shadow:6px 6px 0 rgba(0,0,0,.35);white-space:nowrap">{text}</div>')


def inject(src, dst, overlay, extra_body_css=""):
    s = (H / f"{src}.html").read_text()
    if extra_body_css:
        s = s.replace("<body>", f'<body><div id="zoomwrap" style="{extra_body_css}">', 1).replace("</body>", "</div></body>", 1) if False else s
    s = s.replace("</body>", FONT + overlay + "</body>", 1)
    (H / f"{dst}.html").write_text(s)


inject("02_ransom", "c02_ransom", tag("ITEM 5 · FILED UNDER: SEASONING", 250, 790))
# smash-zoom receipt: the same page scaled 1.32 around the pepper line, red ink circle
s = (H / "02_ransom.html").read_text()
s = s.replace("</style>", "</style><style>body>*:not(script){}</style>", 1)
s = s.replace("<body>", '<body><div style="position:absolute;inset:0;transform:scale(1.32);transform-origin:560px 640px">', 1)
s = s.replace("</body>", "</div>" + FONT + tag("RECEIPT · ZOSIMUS 5.41", 1260, 120) + "</body>", 1)
(H / "c02b_receipt.html").write_text(s)
trousers = ('<svg style="position:absolute;left:1240px;top:110px;z-index:68;filter:drop-shadow(10px 12px 0 rgba(0,0,0,.8))" width="260" height="330" viewBox="0 0 120 150">'
            '<path d="M20 6 L100 6 L104 146 L70 146 L60 56 L50 146 L16 146 Z" fill="#C0392B" stroke="#FFFFFF" stroke-width="4" stroke-linejoin="round"/>'
            '<rect x="20" y="6" width="80" height="12" fill="#8E2A20" stroke="#FFFFFF" stroke-width="3"/></svg>')
inject("11_rents", "c11_rents", trousers + tag("LINE ITEM 4 · NO FURTHER DETAILS", 1060, 470, 2)
       + f'<div style="position:absolute;left:1090px;top:522px;z-index:70;font:700 38px CaveatC;color:{RED};transform:rotate(-3deg)">"Nobody explains the trousers. I checked."</div>'
       + '<div style="position:absolute;left:1250px;top:86px;z-index:69;font:500 13px PlexC;color:#555">ILLUSTRATION</div>')
inject("r3v", "c_r3v", tag("DEPARTMENT OF PEPPER (APPROX.)", 120, 1000 - 70, -2))
inject("s3_c", "c_s3_c", tag("“60× THE COST” · STATUS: UNVERIFIED BRAG", 90, 760, -2, True))
inject("13_markup", "c13_markup", tag("MARKUP · EVERY RUNNER CHARGES FOR THE BATON", 110, 960, -1.5))
inject("14_fall", "c14_fall", tag("MOST BRITISH SENTENCE EVER SPOKEN IN COURT", 1040, 760, 1.5))
print("ok")
