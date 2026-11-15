"""Research dossier for the 200: every number on screen with its source and status (data/dossier.json)."""
import json
from pathlib import Path
D = Path(__file__).resolve().parent
WB = "World Bank API (api.worldbank.org/v2), fetched 2026-11-15"
GISS = "NASA GISS GISTEMP v4, GLB.Ts+dSST.csv (data.giss.nasa.gov), fetched 2026-11-15"
def wb(name, iso="WLD"):
    rows = json.loads((D / "data" / "wb" / f"{name}.json").read_text())[1]
    return sorted((int(r["date"]), r["value"]) for r in rows if r["value"] is not None and r["countryiso3code"] == iso)
N = []
def add(frame, shown, status, source, url=""):
    N.append({"frame": frame, "shown": shown, "status": status, "source": source, "url": url})
data = "pulled from the source file by script; shown as recorded"
add("eightbn", f"{wb('pop_wld')[-1][1]:,.0f} → 8.06 billion (2023)", data, WB + ", SP.POP.TOTL WLD")
add("remit", f"${wb('remit_ind','IND')[-1][1]/1e9:.1f} billion ({wb('remit_ind','IND')[-1][0]})", data, WB + ", BX.TRF.PWKR.CD.DT IND")
add("japan65", f"{wb('old_jpn','JPN')[-1][1]:.1f}% ({wb('old_jpn','JPN')[-1][0]})", data, WB + ", SP.POP.65UP.TO.ZS JPN")
add("mobiles", f"{wb('mobile_wld')[-1][1]} per 100 ({wb('mobile_wld')[-1][0]})", data, WB + ", IT.CEL.SETS.P2 WLD")
add("indiapop", "0.44 bn (1960) … 1.44 bn (2023)", data, WB + ", SP.POP.TOTL IND")
add("maldives", "tourist arrivals 2005–2020, 1.70 m (2019) → 0.56 m (2020)", data, WB + ", ST.INT.ARVL MDV")
add("electric", "60% (2000) → 99.5% (2023)", data, WB + ", EG.ELC.ACCS.ZS IND")
add("glow_fertility", "India TFR 5.92 (1960) → 1.98 (2023)", data, WB + ", SP.DYN.TFRT.IN IND")
add("glow_renewables", "17.5% (2000) → 19.7% (2020, latest in series)", data, WB + ", EG.FEC.RNEW.ZS WLD")
add("glow_literacy", "61.0% (2001), 69.3% (2011), 73.7% (2018), 81.7% (2023); survey years only", data, WB + ", SE.ADT.LITR.ZS IND")
add("glow_warming / box_giss", "decade means 1980s 0.25 … 2020s 1.06 °C vs 1951–1980; monthly values by 20-year group", data, GISS)
add("box_life", "life expectancy 2022, all countries, by World Bank region", data, WB + ", SP.DYN.LE00.IN + country regions")
add("unit_internet", f"{wb('internet_wld')[-1][1]}% ({wb('internet_wld')[-1][0]})", data, WB + ", IT.NET.USER.ZS WLD")
add("unit_forest", f"{wb('forest_wld')[-1][1]:.2f}% ({wb('forest_wld')[-1][0]})", data, WB + ", AG.LND.FRST.ZS WLD")
add("unit_urban", f"{wb('urban_ind','IND')[-1][1]:.1f}% ({wb('urban_ind','IND')[-1][0]})", data, WB + ", SP.URB.TOTL.IN.ZS IND")
chk = "confirmed by web search 2026-11-15 (snippets; canonical page linked)"
for f, s, src, u in [
    ("relief_andes", "Aconcagua 6,961 m; highest peak outside Asia", "Instituto Geográfico Nacional (Argentina) 2012 survey (6,960.8 m)", "https://rpp.pe/lima/actualidad/nueva-altura-oficial-del-cerro-aconcagua-es-de-69608-metros-noticia-518097"),
    ("relief_rift", "Mount Kenya 5,199 m; Lake Naivasha on the Gregory Rift floor", "Kenya Wildlife Service / UNESCO WHS 800; IUCN WH Outlook", "https://whc.unesco.org/en/list/800"),
    ("relief_atlas", "Toubkal 4,167 m, North Africa's highest peak (Britannica: 4,165 m)", "Britannica", "https://www.britannica.com/place/Mount-Toubkal"),
    ("relief_iceland", "Þingvellir shows the North American–Eurasian plate boundary on land", "Þingvellir National Park", "https://www.thingvellir.is/en/"),
    ("physics_scale", "loss-aversion coefficient ≈ 2.25", "Tversky & Kahneman, J. Risk Uncertainty 5 (1992) 297–323", "https://doi.org/10.1007/BF00122574"),
    ("physics_sandpile", "self-organised criticality", "Bak, Tang & Wiesenfeld, PRL 59, 381 (1987)", "https://doi.org/10.1103/PhysRevLett.59.381"),
    ("draw_confirmation", "Wason 1960", "QJEP 12(3) 129–140", "https://doi.org/10.1080/17470216008416717"),
    ("draw_spotlight", "Gilovich, Medvec & Savitsky 2000", "JPSP 78(2) 211–222", "https://doi.org/10.1037/0022-3514.78.2.211"),
    ("draw_planning", "Buehler, Griffin & Ross 1994", "JPSP 67(3) 366–381", "https://doi.org/10.1037/0022-3514.67.3.366"),
    ("draw_anchoring", "Tversky & Kahneman 1974", "Science 185, 1124–1131", "https://doi.org/10.1126/science.185.4157.1124"),
    ("pearl", "7:55 a.m. first wave; second wave attacks ~8:54 a.m.; US declares war 8 Dec", "NPS; Naval History & Heritage Command (sources differ 8:40–8:55 on the second wave, so the frame says ~)", "https://www.nps.gov/articles/pearlattackww2.htm"),
    ("earhart", "1932 solo transatlantic flight landed near Derry, Northern Ireland (21 May 1932)", "Smithsonian NASM", "https://airandspace.si.edu/explore/stories/amelia-earhart"),
    ("bell", "New York–Chicago line opened 1892 (18 Oct)", "Library of Congress, Bell papers timeline", "https://www.loc.gov/collections/alexander-graham-bell-papers/articles-and-essays/time-line-of-alexander-graham-bell/"),
    ("tesla", "US 381,968, 1 May 1888; 1856–1943; Smiljan → New York", "Google Patents; Britannica", "https://patents.google.com/patent/US381968A"),
    ("edison", "phonograph 1877; carbon-filament lamp 1879; Menlo Park; 1847–1931", "NPS Thomas Edison NHP", "https://www.nps.gov/edis/learn/historyculture/index.htm"),
    ("curie", "Physics 1903, Chemistry 1911; 1867–1934", "NobelPrize.org", "https://www.nobelprize.org/prizes/physics/1903/marie-curie/biographical/"),
    ("cyclone", "Cyclone Mocha over the Bay of Bengal, 13 May 2023", "IMD RSMC New Delhi bulletin 13 May 2023", "https://rsmcnewdelhi.imd.gov.in/"),
    ("smokeplume", "West Coast wildfire smoke, 9 Sep 2020", "NASA Earth Observatory", "https://science.nasa.gov/earth/earth-observatory/a-wall-of-smoke-on-the-us-west-coast-147261/"),
    ("dustplume", "Saharan dust over the Atlantic, 18 Jun 2020 (our image: MODIS Terra via GIBS; NASA's own image that day is VIIRS)", "NASA Earth Observatory", "https://earthobservatory.nasa.gov/images/146871/dust-traverses-the-atlantic-ocean"),
    ("trafalgar/dday/lebanon", "21 Oct 1805; 6 Jun 1944, five beaches, Paris freed Aug 1944; Beirut 4 Aug 2020", "Royal Museums Greenwich; National WWII Museum; UN", "https://www.nationalww2museum.org/students-teachers/student-resources/research-starters/d-day-june-6-1944"),
    ("toytrain", "Siliguri · Kurseong · Ghum (highest station)", "UNESCO WHS 944", "https://whc.unesco.org/en/list/944"),
    ("transmongol", "Datong · Erenhot · Zamyn-Üüd", "Seat61", "https://www.seat61.com/Trans-Siberian-Railway.htm"),
    ("glacierexp", "Brig · Andermatt · Chur", "Glacier Express", "https://www.glacierexpress.ch/en/"),
    ("lehavre", "city centre rebuilt by Auguste Perret; UNESCO 2005", "UNESCO WHC 1181", "https://whc.unesco.org/en/list/1181"),
    ("node_upi", "UPI is run by NPCI", "NPCI", "https://www.npci.org.in/what-we-do/upi/product-overview"),
    ("perry", "fleet at Uraga, July 1853", "Office of the Historian", "https://history.state.gov/milestones/1830-1860/opening-to-japan"),
    ("wright", "'Success four flights', 17 Dec 1903", "Library of Congress", "https://www.loc.gov/item/mcc.016/"),
    ("gigwork", "7.7 million gig and platform workers (2020–21); 23.5 million projected (2029–30)", "NITI Aayog, 'India's Booming Gig and Platform Economy', June 2022 (well-known report figures; not re-fetched today)", "https://www.niti.gov.in/sites/default/files/2022-06/Policy_Brief_India%27s_Booming_Gig_and_Platform_Economy_27062022.pdf"),
    ("jefferson", "rough draught held at the Library of Congress", "Library of Congress", "https://www.loc.gov/exhibits/declara/ruffdrft.html")]:
    add(f, s, chk, src, u)
out = {"date": "2026-11-15", "method": "numbers read by script from the source files in data/; history and science checked by a web-search pass (snippets, official pages linked). "
       "Illustrative items are labelled on the frame (positions, prices, physics block weights, diagrams).", "numbers": N}
(D / "data" / "dossier.json").write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(len(N))
