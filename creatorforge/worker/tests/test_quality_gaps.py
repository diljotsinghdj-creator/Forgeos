"""Gaps found while pushing quality: the studio draws every graphic the director accepts (globe, map, cards), and the
text QA catches words sitting on other words."""
import json

from creatorforge_worker.media import motion, vox
from creatorforge_worker.studio.produce import _render_scene


def test_the_studio_draws_globe_map_and_card_graphics(tmp_path):
    for kind, spec in (("globe", "Los Angeles | where the sign went up"), ("map", "Los Angeles | the sign"),
                       ("chat", "Family group | them: hi · me: hello")):
        out = _render_scene(kind, spec, "editorial~0@red/field/", 320, 180, 1.5, tmp_path / f"{kind}.mp4", tmp_path / "w", 8, "", False, None)
        assert out.stat().st_size > 3000, kind


def test_the_text_qa_catches_overlapping_words(tmp_path):
    if not motion.enabled():
        return
    from playwright.sync_api import sync_playwright
    out = vox.render("myth", "Smart people never fall for scams | Intelligence is not armour", "e~0@red/field/", 480, 270, 1.5,
                     tmp_path / "m.mp4", tmp_path / "w", fetch=False, fps=4)
    assert json.loads(out.with_suffix(".qa.json").read_text())["text_overlap"] == []
    page = next((tmp_path / "w").glob("*.html"))
    with sync_playwright() as p:
        b = motion._launch(p)
        pg = b.new_page(viewport={"width": 480, "height": 270})
        pg.goto(page.as_uri())
        pg.wait_for_function("window.READY === true")
        pg.evaluate("window.frame(1.2)")
        pg.evaluate("""()=>{const s=document.querySelector('svg');for(const [x,y,t] of [[150,135,'WORDS HERE'],[160,137,'MORE WORDS']]){
          const e=document.createElementNS('http://www.w3.org/2000/svg','text');e.setAttribute('x',x);e.setAttribute('y',y);
          e.setAttribute('font-size','24');e.textContent=t;s.appendChild(e)}}""")
        assert pg.evaluate("window.QA()")["text_overlap"] == ["WORDS HERE / MORE WORDS"]
        b.close()
