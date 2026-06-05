"""Export computed surfaces to compact static JSON for the dashboard (dashboard/public/data/).

Reads data/derived/surfaces.npz (run compute_surfaces.py first) and the raw HS4 file
(for PCI 'anchor' products). Writes:
  meta.json      countries (name/region), years, grids, thresholds, settings
  series.json    per-country share / density / total, all years (client stacks/scales)
  coverage.json  cumulative top-N coverage by PCI, per threshold and year
  anchors.json   representative high-value HS4 products per PCI bin (axis legend)

Usage:  python scripts/export_dashboard_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

OUT = cfg.ROOT / "dashboard" / "public" / "data"
DERIVED = cfg.DATA_DIR / "derived"

# ISO3 -> (display name, region) for the tracked economies
COUNTRY_META = {
    "CHN": ("China", "Asia-Pacific"), "USA": ("United States", "Americas"),
    "DEU": ("Germany", "Europe"), "JPN": ("Japan", "Asia-Pacific"),
    "FRA": ("France", "Europe"), "KOR": ("South Korea", "Asia-Pacific"),
    "ITA": ("Italy", "Europe"), "NLD": ("Netherlands", "Europe"),
    "CAN": ("Canada", "Americas"), "GBR": ("United Kingdom", "Europe"),
    "MEX": ("Mexico", "Americas"), "RUS": ("Russia", "Other"),
    "TWN": ("Taiwan", "Asia-Pacific"), "BEL": ("Belgium", "Europe"),
    "ESP": ("Spain", "Europe"), "CHE": ("Switzerland", "Europe"),
    "SGP": ("Singapore", "Asia-Pacific"), "IND": ("India", "Asia-Pacific"),
    "MYS": ("Malaysia", "Asia-Pacific"), "THA": ("Thailand", "Asia-Pacific"),
    "BRA": ("Brazil", "Americas"), "SAU": ("Saudi Arabia", "Middle East"),
    "AUS": ("Australia", "Other"), "POL": ("Poland", "Europe"),
    "ARE": ("UAE", "Middle East"), "VNM": ("Vietnam", "Asia-Pacific"),
    "IDN": ("Indonesia", "Asia-Pacific"), "SWE": ("Sweden", "Europe"),
    "IRL": ("Ireland", "Europe"), "AUT": ("Austria", "Europe"),
    # ranks ~31-50
    "TUR": ("Turkey", "Middle East"), "HKG": ("Hong Kong", "Asia-Pacific"),
    "CZE": ("Czechia", "Europe"), "NOR": ("Norway", "Europe"),
    "HUN": ("Hungary", "Europe"), "ZAF": ("South Africa", "Other"),
    "DNK": ("Denmark", "Europe"), "FIN": ("Finland", "Europe"),
    "QAT": ("Qatar", "Middle East"), "PHL": ("Philippines", "Asia-Pacific"),
    "SVK": ("Slovakia", "Europe"), "CHL": ("Chile", "Americas"),
    "ARG": ("Argentina", "Americas"), "ROU": ("Romania", "Europe"),
    "NGA": ("Nigeria", "Other"), "PRT": ("Portugal", "Europe"),
    "ISR": ("Israel", "Middle East"), "IRN": ("Iran", "Middle East"),
    "IRQ": ("Iraq", "Middle East"), "KWT": ("Kuwait", "Middle East"),
}

# HS2 chapter -> short label, for anchor product readability
CHAPTERS = {
    "01": "Live animals", "02": "Meat", "03": "Fish", "04": "Dairy/eggs",
    "05": "Animal products", "06": "Plants/flowers", "07": "Vegetables",
    "08": "Fruit/nuts", "09": "Coffee/tea/spices", "10": "Cereals",
    "11": "Milling products", "12": "Oilseeds", "13": "Gums/resins",
    "14": "Vegetable plaiting", "15": "Fats/oils", "16": "Prepared meat/fish",
    "17": "Sugars", "18": "Cocoa", "19": "Cereal preparations",
    "20": "Prepared vegetables/fruit", "21": "Misc edible preps", "22": "Beverages/spirits",
    "23": "Animal feed", "24": "Tobacco", "25": "Salt/stone/cement",
    "26": "Ores/slag/ash", "27": "Mineral fuels/oil", "28": "Inorganic chemicals",
    "29": "Organic chemicals", "30": "Pharmaceuticals", "31": "Fertilizers",
    "32": "Dyes/pigments", "33": "Perfumery/cosmetics", "34": "Soaps/waxes",
    "35": "Albuminoids/glues", "36": "Explosives", "37": "Photographic goods",
    "38": "Misc chemicals", "39": "Plastics", "40": "Rubber",
    "41": "Raw hides/leather", "42": "Leather articles", "43": "Furskins",
    "44": "Wood", "45": "Cork", "46": "Straw/basketware", "47": "Wood pulp",
    "48": "Paper", "49": "Printed books", "50": "Silk", "51": "Wool",
    "52": "Cotton", "53": "Vegetable fibres", "54": "Man-made filaments",
    "55": "Man-made staple fibres", "56": "Wadding/nonwovens", "57": "Carpets",
    "58": "Special woven fabrics", "59": "Coated textiles", "60": "Knitted fabrics",
    "61": "Apparel (knit)", "62": "Apparel (woven)", "63": "Made-up textiles",
    "64": "Footwear", "65": "Headgear", "66": "Umbrellas", "67": "Feathers/artificial flowers",
    "68": "Stone/cement articles", "69": "Ceramics", "70": "Glass",
    "71": "Pearls/precious metals", "72": "Iron/steel", "73": "Iron/steel articles",
    "74": "Copper", "75": "Nickel", "76": "Aluminium", "78": "Lead", "79": "Zinc",
    "80": "Tin", "81": "Other base metals", "82": "Tools/cutlery", "83": "Misc metal articles",
    "84": "Machinery", "85": "Electrical machinery", "86": "Railway",
    "87": "Vehicles", "88": "Aircraft", "89": "Ships", "90": "Optical/medical instruments",
    "91": "Clocks/watches", "92": "Musical instruments", "93": "Arms/ammunition",
    "94": "Furniture/lighting", "95": "Toys/games/sports", "96": "Misc manufactures",
    "97": "Art/antiques", "99": "Unclassified",
}


def r(x, n):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    countries = list(s["countries"])
    years = [int(y) for y in s["years"]]
    share_grid = [r(x, 4) for x in s["share_grid"]]
    thresholds = [int(t) for t in s["cover_thresholds"]]
    # subsample the density grid (every 2nd point) to keep the 3-level payload small
    KSTEP = 2
    kde_idx = list(range(0, len(s["kde_grid"]), KSTEP))
    kde_grid = [r(s["kde_grid"][i], 4) for i in kde_idx]
    levels = [lv["id"] for lv in cfg.SMOOTHING]

    # --- meta ---
    regions_order = ["Asia-Pacific", "Europe", "Americas", "Middle East", "Other"]
    cmeta = []
    for c in countries:
        name, region = COUNTRY_META.get(c, (c, "Other"))
        cmeta.append({"iso3": c, "name": name, "region": region})
    meta = {
        "countries": cmeta,
        "regionsOrder": regions_order,
        "years": years,
        "shareGrid": share_grid,
        "kdeGrid": kde_grid,
        "coverThresholds": thresholds,
        "bandwidth": cfg.BANDWIDTH,
        "smoothing": [{"id": lv["id"], "label": lv["label"], "win": lv["win"]} for lv in cfg.SMOOTHING],
        "defaultLevel": "med",
        "source": "Harvard Growth Lab, Atlas of Economic Complexity (HS92 HS4), 2000-2024",
    }
    (OUT / "meta.json").write_text(json.dumps(meta))

    # --- per-country series at each smoothness level: share, density (+ shared total) ---
    share_lvl, dens_lvl, totals = s["share_lvl"], s["density_lvl"], s["totals_cy"]
    ser_share = {lid: {} for lid in levels}
    ser_dens = {lid: {} for lid in levels}
    ser_tot = {}
    for ci, c in enumerate(countries):
        for li, lid in enumerate(levels):
            ser_share[lid][c] = {str(years[yi]): [r(max(0.0, v), 4) for v in np.clip(share_lvl[li, ci, yi], 0, 1)]
                                 for yi in range(len(years))}
            ser_dens[lid][c] = {str(years[yi]): [r(dens_lvl[li, ci, yi][k], 6) for k in kde_idx]
                                for yi in range(len(years))}
        ser_tot[c] = {str(years[yi]): r(totals[ci, yi] / 1e9, 2) for yi in range(len(years))}  # $B
    (OUT / "series.json").write_text(json.dumps(
        {"levels": levels, "share": ser_share, "density": ser_dens, "totalB": ser_tot}))

    # --- coverage ---
    cov = s["coverage"]  # (nThresh, nY, grid)
    coverage = {"thresholds": thresholds, "grid": share_grid, "years": years,
                "coverage": [[[r(v, 4) for v in cov[ti, yi]] for yi in range(len(years))]
                             for ti in range(len(thresholds))]}
    (OUT / "coverage.json").write_text(json.dumps(coverage))

    # --- anchors: top-value HS4 per PCI bin (latest year) ---
    df = pd.read_csv(cfg.RAW_CSV, usecols=["product_hs92_code", "year", "export_value", "pci"],
                     dtype={"product_hs92_code": str})
    yr = max(years)
    df = df[df["year"] == yr].dropna(subset=["pci", "export_value"])
    prod = df.groupby("product_hs92_code").agg(pci=("pci", "first"),
                                               val=("export_value", "sum")).reset_index()
    prod = prod[prod["pci"].between(-2.5, 2.5)]
    edges = np.linspace(-2.5, 2.5, 15)
    anchors = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        seg = prod[(prod["pci"] >= lo) & (prod["pci"] < hi)].nlargest(2, "val")
        prods = [{"hs4": row.product_hs92_code,
                  "chapter": CHAPTERS.get(row.product_hs92_code[:2], "HS " + row.product_hs92_code[:2]),
                  "valueB": r(row.val / 1e9, 1)} for row in seg.itertuples()]
        anchors.append({"pci": r((lo + hi) / 2, 2), "products": prods})
    (OUT / "anchors.json").write_text(json.dumps({"year": yr, "bins": anchors}))

    print(f"wrote dashboard data to {OUT}")
    for f in OUT.glob("*.json"):
        print(f"  {f.name}: {f.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
