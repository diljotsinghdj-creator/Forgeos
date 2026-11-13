"""Screenshot public source pages as evidence (headline region). Sites that block automated access are skipped."""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
URLS = {
 "print_malviya": "https://theprint.in/politics/why-bjp-has-replaced-amit-malviya-as-partys-it-cell-chief/3017377/",
 "fb_2019": "https://about.fb.com/news/2019/04/cib-from-india-and-pakistan/",
 "arxiv_trend": "https://arxiv.org/abs/2104.13259",
 "adr_1754": "https://adrindia.org/content/bjp-spent-1754-crore-on-election-general-propaganda-in-2023-24",
 "scroll_1737": "https://scroll.in/latest/1078621/rs-1737-68-crore-spent-on-2024-lok-sabha-elections-bjp",
 "scroll_wire_retract": "https://scroll.in/latest/1035706/the-wire-retracts-articles-about-meta-amid-dispute-with-social-media-company",
 "livelaw_fcu": "https://www.livelaw.in/top-stories/bombay-high-court-fact-check-unit-it-rules-kunal-kamra-270722",
 "quint_kota": "https://www.thequint.com/news/politics/amit-shah-real-fake-can-make-messages-viral",
 "row_mandi": "https://restofworld.org/2024/bjp-whatsapp-modi/",
 "quint_label": "https://www.thequint.com/news/webqoof/twitter-marks-amit-malviyas-tweet-on-farmer-protest-as-manipulated",
 "print_swamy": "https://theprint.in/politics/subramanian-swamy-attacks-amit-malviya-calls-for-sacking-of-bjp-it-cell-members/497506",
 "bt_telangana": "https://www.businesstoday.in/india/story/amit-shahs-doctored-video-5-members-of-congress-it-cell-arrested-428349-2024-05-03",
}
def one(item):
    k, u = item
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--headless", "--no-sandbox"])
            pg = b.new_page(viewport={"width": 1400, "height": 1000}, device_scale_factor=2)
            r = pg.goto(u, timeout=45000, wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
            title = pg.title(); st = r.status if r else 0
            h1 = pg.query_selector("h1")
            if h1:
                h1.scroll_into_view_if_needed(); pg.wait_for_timeout(800)
            pg.screenshot(path=f"docs/{k}.png")
            txt = (h1.inner_text()[:160] if h1 else "")
            b.close()
            return k, st, title[:80], txt
    except Exception as e:
        return k, "ERR", str(e)[:80], ""
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, URLS.items()))
for r in res: print(r)
json.dump({k: u for k, u in URLS.items()}, open("docs/urls.json", "w"), indent=1)
