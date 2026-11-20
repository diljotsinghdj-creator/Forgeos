"""World Bank indicators for the charts (api.worldbank.org, CC BY 4.0). Saves raw JSON per request to data/wb/."""
import json, sys, time
from pathlib import Path
import httpx
D = Path(__file__).resolve().parent / "data" / "wb"; D.mkdir(parents=True, exist_ok=True)
Q = {"pop_ind": "country/IND/indicator/SP.POP.TOTL?date=1960:2023",
     "arrivals_mdv": "country/MDV/indicator/ST.INT.ARVL?date=2005:2023",
     "elec_ind": "country/IND/indicator/EG.ELC.ACCS.ZS?date=2000:2023",
     "urban_ind": "country/IND/indicator/SP.URB.TOTL.IN.ZS?date=2023",
     "internet_wld": "country/WLD/indicator/IT.NET.USER.ZS?date=2015:2024",
     "forest_wld": "country/WLD/indicator/AG.LND.FRST.ZS?date=1990:2022",
     "old_jpn": "country/JPN/indicator/SP.POP.65UP.TO.ZS?date=2023",
     "life_all": "country/all/indicator/SP.DYN.LE00.IN?date=2022",
     "countries": "country/all?",
     "renew_wld": "country/WLD/indicator/EG.FEC.RNEW.ZS?date=2000:2022",
     "mobile_wld": "country/WLD/indicator/IT.CEL.SETS.P2?date=2000:2023",
     "pop_wld": "country/WLD/indicator/SP.POP.TOTL?date=2023",
     "lit_ind": "country/IND/indicator/SE.ADT.LITR.ZS?date=2000:2023",
     "fertility_ind": "country/IND/indicator/SP.DYN.TFRT.IN?date=1960:2023",
     "remit_ind": "country/IND/indicator/BX.TRF.PWKR.CD.DT?date=2023"}
for k, q in Q.items():
    if (D / f"{k}.json").is_file():
        continue
    for t in range(4):
        try:
            r = httpx.get(f"https://api.worldbank.org/v2/{q}&format=json&per_page=400", timeout=120)
            d = r.json(); (D / f"{k}.json").write_text(json.dumps(d)); print("ok", k, len(d[1]) if len(d) > 1 and d[1] else 0, flush=True); break
        except Exception as e:
            print("retry", k, type(e).__name__, flush=True); time.sleep(5)
