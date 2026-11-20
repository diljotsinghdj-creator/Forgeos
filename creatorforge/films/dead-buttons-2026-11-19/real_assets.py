"""Real, licensed photos for the film (owner, 2026-11-19, MASTER_DIRECTIVES 8c "Real first").
Found through the Openverse API (CC0 / public domain / CC BY only); originals in assets/real/raw (gitignored, untrusted: opened as
images only). This finishes each in the channel look (black and white, or cobalt duotone) into assets/real/<slug>.jpg and writes
data/photo_credits.json from the Openverse metadata. Run: python3 -I real_assets.py"""
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance

D = Path(__file__).resolve().parent
R = D / "assets" / "real"
# slug: (search file, index, look, where it is used, what the frame may say about it)
PICKS = {
    "nyc_wait_sign": ("nyc3", 9, "bw", "02 crosswalk macro", "A NEW YORK 'WAIT FOR WALK SIGNAL' SIGN"),
    "nyc_crosswalk": ("nyc2", 0, "duo", "06 NYC street corner", "A MANHATTAN CROSSWALK AT NIGHT"),
    "push_sign": ("push_sign", 3, "bw", "02 crosswalk macro / 24 recap", "A US WALK BUTTON (CHICAGO, NOT NEW YORK)"),
    "dead_button": ("walk_button", 11, "bw", "08 placebo", "A DEACTIVATED PUSH BUTTON (LOCATION UNVERIFIED)"),
    "lift_buttons": ("lift", 1, "bw", "12 lift", "A LIFT PANEL WITH OPEN / CLOSE BUTTONS"),
    "placebo_thermo": ("thermo", 5, "bw", "14 office", "A WALL BUTTON: 'PRESS FOR COOLER TEMPERATURE'"),
    "thermostat": ("thermo2", 19, "duo", "14 office", "A WALL THERMOSTAT"),
    "london_junction": ("london2", 0, "bw", "10 London", "A LONDON JUNCTION WITH SIGNALLED CROSSINGS"),
    "uk_button_box": ("walk_button", 5, "bw", "10 London", "A UK CROSSING PUSH-BUTTON BOX"),
    "sydney_street": ("syd2", 15, "duo", "11 Sydney", "PARK ST AND ELIZABETH ST, CENTRAL SYDNEY"),
    "london_pelican": ("pelican", 1, "bw", "10 London", "A PELICAN CROSSING, GROSVENOR PLACE, LONDON"),
    # second pass (owner, 2026-11-19: "more real pictures ... less ai")
    "metal_texture": ("brushed", 0, "bw", "the studio control panel: real brushed-steel surface under every frame", "BRUSHED STEEL (PANEL SURFACE)"),
    "lift_panel": ("liftpanel", 2, "bw", "12 lift split / 23 fire / 24 recap", "A LIFT PANEL WITH DOOR CONTROLS"),
    "signal_cabinet": ("controller", 2, "bw", "08 placebo / 16 reveal", "INSIDE A TRAFFIC-SIGNAL CABINET (GREENVILLE, NC)"),
    "office_cubicle": ("office", 0, "duo", "13 office (replaces AI plate K2)", "AN OFFICE CUBICLE, CIRCA 2001 (NOT THE WSJ'S OFFICE)"),
    "windowsill": ("plant2", 0, "bw", "21 plant (replaces AI plate K4)", "A HOUSEPLANT ON A WINDOWSILL (NOT THE 1976 HOME)"),
    "lottery_ticket": ("lottery", 5, "bw", "15 lottery", "A MODERN LOTTERY TICKET (NOT LANGER'S 1975 TICKETS)"),
}
SL, CO, PAPER = (20, 24, 36), (43, 108, 176), (240, 244, 248)


def duotone(g):
    lut = []
    for v in range(256):
        t = v / 255
        a, b, k = (SL, CO, t / .55) if t < .55 else (CO, PAPER, (t - .55) / .45)
        lut.append(tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    return Image.merge("RGB", [g.point([c[i] for c in lut]) for i in range(3)])


def main():
    credits = []
    for slug, (f, i, look, use, caption) in PICKS.items():
        raw = R / "raw" / f"{f}_{i}.jpg"
        if not raw.exists():
            print("missing (not downloaded):", slug); continue
        meta = json.load(open(R / "_search" / f"{f}.json"))[i]
        im = Image.open(raw); im.load()
        g = ImageOps.autocontrast(ImageOps.grayscale(im.convert("RGB")), cutoff=1)
        g = ImageEnhance.Contrast(g).enhance(1.12)
        out = duotone(g) if look == "duo" else g.convert("RGB")
        out.save(R / f"{slug}.jpg", quality=90)
        lic = meta["license"].upper() + (f" {meta['license_version']}" if meta.get("license_version") and meta["license"] != "pdm" else "")
        lic = {"PDM": "PUBLIC DOMAIN MARK", "CC0 1.0": "CC0 1.0"}.get(lic, lic.replace("BY", "CC BY"))
        credits.append({"slug": slug, "file": f"assets/real/{slug}.jpg", "title": meta["title"], "author": meta.get("creator") or meta["source"], "licence": lic,
                        "url": meta["foreign_landing_url"], "image_url": meta["url"], "found_via": "Openverse API", "source": meta["source"],
                        "finish": "black and white" if look == "bw" else "cobalt duotone", "used_in": use, "on_screen_caption": caption,
                        "people": "none identifiable as a 'bad' example; no faces added"})
        print("ok", slug, out.size)
    (D / "data" / "photo_credits.json").write_text(json.dumps(credits, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
