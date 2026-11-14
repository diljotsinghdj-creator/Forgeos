"""A kraft-board newspaper-collage ground for the BJP stills, painted procedurally with cloveric/claude-drawing-skill
(MIT, no image model). Only our own words appear; the real source scraps are laid on top later, in the page."""
import sys, time
LIB = "/tmp/claude-0/-home-user-Forgeos/4511f341-cf91-5fed-ac10-e7043335b256/scratchpad/repos/cloveric_claude-drawing-skill/lib"
sys.path.insert(0, LIB)
from newscollage import NewsCollage, RED, INK, PAPER
out = sys.argv[1]; stages = sys.argv[2] if len(sys.argv) > 2 else None
t0 = time.time()
nc = NewsCollage(1920, 1080, seed=23)
nc.board(); nc.stage('board')
s = nc.sheet(940, 520); s.text('EVIDENCE FILE', 40, 90, 64, 'serif_bold'); s.rule(40, 112, 720, 112, 2.0)
for i, t in enumerate(("Subject: the BJP IT cell, 2007-2026", "Every claim carries a status:", "verified · reported · allegation · opinion · response",
                       "Sources: the party's own filings, platforms' own posts,", "court records, peer-reviewed research, named outlets.")):
    s.text(t, 40, 170 + i * 52, 25, 'typewriter')
s.age(0.8); s.tear('rb', 10, 8)
nc.paste(s, 600, 380, rot=-3); nc.stage('file')
nc.disc(1460, 640, 300, RED); nc.stage('disc')
s2 = nc.sheet(560, 260); s2.text('SOURCED', 280, 170, 88, 'slab', anchor='ms', colour=RED); s2.age(0.6); s2.tear('lt', 8, 6)
nc.paste(s2, 1470, 300, rot=4); nc.stage('sourced')
nc.tape(260, 140, 200, rot=-28); nc.tape(880, 130, 190, rot=22); nc.tape(1650, 170, 170, rot=-15)
nc.ransom('WHO CHECKS?', 300, 900, 96, rot=-3)
nc.stamp(1720, 940, ['PRINT FACTS', '2026'], rot=-8)
nc.stage('marks')
nc.composite(vignette=0.22)
nc.save(out, stages)
print(out, f"{time.time() - t0:.1f}s")
