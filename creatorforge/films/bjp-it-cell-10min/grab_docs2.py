"""Clean headline crops of public source pages. Fixed/sticky overlays (ads, cookie banners) are hidden in the
screenshot only; nothing is logged into or bypassed. Pages that refuse automated access are skipped."""
import sys
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
URLS = {
 "print_malviya": "https://theprint.in/politics/why-bjp-has-replaced-amit-malviya-as-partys-it-cell-chief/3017377/",
 "fb_2019": "https://about.fb.com/news/2019/04/cib-and-spam-from-india-pakistan/",
 "arxiv_trend": "https://arxiv.org/abs/2104.13259",
 "adr_1754": "https://adrindia.org/content/bjp-spent-1754-crore-on-election-general-propaganda-in-2023-24-report",
 "scroll_1737": "https://scroll.in/latest/1078621/rs-1737-68-crore-spent-on-2024-lok-sabha-elections-bjp",
 "scroll_wire_retract": "https://scroll.in/latest/1035706/the-wire-retracts-articles-about-meta-amid-dispute-with-social-media-company",
 "livelaw_fcu": "https://www.livelaw.in/top-stories/bombay-high-court-fact-check-unit-it-rules-kunal-kamra-270722",
 "quint_kota": "https://www.thequint.com/news/politics/amit-shah-real-fake-can-make-messages-viral",
 "row_mandi": "https://restofworld.org/2024/bjp-whatsapp-modi/",
 "quint_label": "https://www.thequint.com/news/webqoof/twitter-marks-amit-malviyas-tweet-on-farmer-protest-as-manipulated",
 "print_swamy": "https://theprint.in/politics/subramanian-swamy-attacks-amit-malviya-calls-for-sacking-of-bjp-it-cell-members/497506",
 "scroll_telangana": "https://scroll.in/latest/1067426/delhi-police-arrests-telangana-congress-worker-in-connection-with-doctored-video-of-amit-shah",
 "tribune_7113": "https://www.tribuneindia.com/news/india/bjp-richest-party-with-7113-crore-cong-has-857-cr-shows-ec-data",
 "quint_fb702": "https://www.thequint.com/elections/facebook-removes-702-pages-congress-bjp-linked-it-firm-silver-touch",
}
HIDE = """() => { for (const e of document.querySelectorAll('*')) { const s = getComputedStyle(e);
  if ((s.position === 'fixed' || s.position === 'sticky') && e.tagName !== 'HTML' && e.tagName !== 'BODY') e.style.display = 'none'; }
  for (const f of document.querySelectorAll('iframe, ins, [id*=google_ads], [class*=advert], [class*=-ad-], [class*=adunit]')) f.style.display = 'none';
  document.documentElement.style.overflow = 'auto'; document.body.style.overflow = 'auto'; }"""
def one(item):
    k, u = item
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--headless", "--no-sandbox"])
            pg = b.new_page(viewport={"width": 1300, "height": 1100}, device_scale_factor=2)
            r = pg.goto(u, timeout=60000, wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
            pg.evaluate(HIDE); pg.wait_for_timeout(500)
            h = pg.query_selector("h1.title") if k == "arxiv_trend" else None
            if not h:
                for c in pg.query_selector_all("h1, h2"):
                    t = (c.inner_text() or "").strip()
                    if len(t) > 25 and "ookie" not in t and c.is_visible():
                        h = c; break
            if not h:
                b.close(); return k, r.status if r else 0, "no h1"
            bb = pg.evaluate("e => { e.scrollIntoView({block:'center'}); const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }", h)
            pg.wait_for_timeout(600)
            bb = pg.evaluate("e => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }", h)
            x, y, w, hh = bb
            clip = {"x": max(0, x - 40), "y": max(0, y - 70), "width": min(1300 - max(0, x - 40), max(w, 760) + 80), "height": min(1100 - max(0, y - 70), hh + 330)}
            pg.screenshot(path=f"docs/{k}.png", clip=clip)
            out = (k, r.status if r else 0, h.inner_text()[:90])
            b.close(); return out
    except Exception as e:
        return k, "ERR", str(e)[:90]
ks = sys.argv[1:] or list(URLS)
with ThreadPoolExecutor(4) as ex:
    for res in ex.map(one, [(k, URLS[k]) for k in ks]): print(res)
