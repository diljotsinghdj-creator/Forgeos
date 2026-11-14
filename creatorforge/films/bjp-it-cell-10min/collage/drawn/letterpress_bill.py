"""The film's timeline as a letterpress bill (red, then black, a hair out of register), painted procedurally with
cloveric/claude-drawing-skill (MIT, numpy + Pillow, no image model). Content is the film's own sourced timeline."""
import os, sys, time
LIB = "/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/repos/cloveric_claude-drawing-skill/lib"
sys.path.insert(0, LIB)
from letterpress import Letterpress, RED, BLACK
out = sys.argv[1]; stages = sys.argv[2] if len(sys.argv) > 2 else None
t0 = time.time()
lp = Letterpress(1920, 1080, seed=7, misreg=3.2)
lp.register(BLACK, 0, 0, 0)
lp.register(RED, 3.2, -2.0, 0.05)
lp.paper(tone=0.55)
X0, X1 = 110, 1810
# red forme: the title and the stars
lp.type_line('THE MACHINE', X0, X1, 368, 200, face='clarendon', ink=RED, shade=(10, 9, BLACK, 3))
rows = [("2007", "THE IT CELL IS SET UP"), ("2015", "A NEW NATIONAL HEAD"), ("2018", "KOTA: 'TRUE OR FALSE', AS REPORTED"),
        ("2020", "'GONE ROGUE', FROM ITS OWN MP"), ("2026", "A NEW HEAD. NO REASON GIVEN")]
for i in range(len(rows)):
    lp.star(X0 + 16, 470 + i * 92 - 14, 16, RED)
lp.type_line('EVERY DATE SOURCED  ·  PRINT FACTS', X0, X1, 1000, 46, face='gothic', ink=RED)
lp.press(RED)
lp.stage('red')
# black forme: the bill
lp.type_line('THE BJP IT CELL  ·  NINETEEN YEARS  ·  2007 TO 2026', X0, X1, 112, 52, face='gothic', ink=BLACK)
lp.rule(X0, X1, 136, 'double', BLACK, 3)
lp.rule(X0, X1, 398, 'single', BLACK, 3)
for i, (yr, what) in enumerate(rows):
    y = 470 + i * 92
    lp.text(yr, X0 + 52, y, 54, 'roman_bold', anchor='ls')
    w = lp.text_width(what, 46, 'roman_bold')
    lp.leaders(X0 + 210, X1 - w - 30, y - 12, 4.5, 16)
    lp.text(what, X1, y, 46, 'roman_bold', anchor='rs')
lp.rule(X0, X1, 940, 'single', BLACK, 3)
lp.border(60, 40, 1860, 1040, BLACK, 5)
lp.press(BLACK)
lp.stage('black')
lp.save(out, stages)
print(out, f"{time.time() - t0:.1f}s")
