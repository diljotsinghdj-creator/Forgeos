"""Delhi, The Bowl: key frames. Facts in data/dossier.json; imagery NASA GIBS + Terrarium; photos Pixabay."""
from pathlib import Path
from relief_base import page as relief_page
D = Path(__file__).resolve().parent
SIG = "#FFDD33"
card = lambda t, s, rot, bg="#EFE6D2", fg="#141414": (f'<div style="background:{bg};padding:12px 18px;transform:rotate({rot}deg);box-shadow:0 12px 22px rgba(0,0,0,.55);text-align:center;margin-bottom:22px">'
                                                     f'<div style="font:400 36px/1 Anton;color:{fg};letter-spacing:1px">{t}</div><div style="font:500 13px Plex;letter-spacing:3px;color:#7A2A20;margin-top:6px">{s}</div></div>')
relief = {"exag": 7, "base": "#5A554E", "hot": "#B5652B", "peak": "#F2EBDD", "grid": "#2A2016", "line": "#FFFFFF", "fog": [110, 260], "bg": "#06060A",
          "bloom": [.35, .3, .9], "glow": 0.0, "cam": [2, 70, 88], "look": [0, 0, -2], "fov": 32, "seg": 600,
          "haze": [0.29, "#E3D3B0", .2], "outlineCol": SIG,
          "pins": [{"lon": 77.21, "lat": 28.61, "html": card("DELHI", "28.6°N 77.2°E", -2, "#141414", "#FFDD33")},
                   {"lon": 84.0, "lat": 29.6, "html": card("HIMALAYA", "TO THE NORTH", 2)},
                   {"lon": 78.5, "lat": 23.4, "html": card("VINDHYA RANGE", "TO THE SOUTH", -2)},
                   {"lon": 83.0, "lat": 26.0, "html": '<div style="font:400 34px ISerif;color:#FFF4DC;font-style:italic;text-shadow:0 2px 12px #000">the Indo-Gangetic Plain</div>'}],
          "overlay": '<div style="position:absolute;left:80px;top:60px"><div style="font:400 64px Serif;font-style:italic;color:#F3E9D2">Hemmed in</div>'
                     '<div style="font:400 120px/0.9 Anton;color:#F3EFE6">THE BOWL</div>'
                     '<div style="font:500 20px Plex;letter-spacing:4px;color:#FFDD33;margin-top:14px;width:760px">HAZE IS TRAPPED BETWEEN THE HIMALAYA AND THE VINDHYA RANGE · NASA EARTH OBSERVATORY</div></div>'
                     '<div style="position:absolute;left:24px;bottom:14px;font:500 12px Plex;color:rgba(255,255,255,.55)">ELEVATION: TERRARIUM TILES (MAPZEN/TILEZEN; SRTM) · HEIGHTS EXAGGERATED (SQUARE-ROOT SCALE) · HAZE LAYER ILLUSTRATIVE · INDIA: OFFICIAL BOUNDARY</div>'}
if __name__ == "__main__":
    (D / "html").mkdir(exist_ok=True)
    (D / "html" / "03_bowl_relief.html").write_text(relief_page("north", relief).replace("@font-face{font-family:Serif;", "@font-face{font-family:ISerif;src:url(/fonts/instrument-serif-latin-400-italic.woff2)}@font-face{font-family:Serif;"))
