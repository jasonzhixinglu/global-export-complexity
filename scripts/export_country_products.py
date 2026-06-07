"""Per-country top-HS4 export/import categories by year, for the corridor drill-down.

The corridor tab's right panel shows the largest product categories of the *anchor* country
near a selected PCI (not global products). Storing every country's full product vector is large,
so we keep only the top-N categories per country x year x flow (they carry the vast majority of
value); the client shows the 10 nearest to the selected PCI among those, sorted by value -- so a
sparsely-populated PCI may surface categories somewhat further away, which is acceptable.

Output: dashboard/public/data/country_products.json
  { years, flows, topN, products: { export|import: { iso3: { year: [[hs4, pci, valueB], ...] } } } }
Run:  python scripts/export_country_products.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

OUT = cfg.ROOT / "dashboard" / "public" / "data"
DERIVED = cfg.DATA_DIR / "derived"
TOPN = 50


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    countries = [str(c) for c in s["countries"]]
    years = [int(y) for y in s["years"]]

    df = gdata.load_clean(years=years)
    df = df[df["pci"].between(cfg.PCI_LO, cfg.PCI_HI) & df["country_iso3_code"].isin(countries)]
    df["hs4"] = df["product_hs92_code"].str.zfill(4)

    flows = [("export", "export_value"), ("import", "import_value")]
    products = {fl: {} for fl, _ in flows}
    nrows = 0
    for fl, col in flows:
        sub = df[df[col] > 0]
        # one product row per (country, year, hs4); pci is constant within (hs4, year)
        agg = (sub.groupby(["country_iso3_code", "year", "hs4"])
               .agg(val=(col, "sum"), pci=("pci", "first")).reset_index())
        agg["rank"] = agg.groupby(["country_iso3_code", "year"])["val"].rank(ascending=False, method="first")
        agg = agg[agg["rank"] <= TOPN]
        for (iso, yr), g in agg.groupby(["country_iso3_code", "year"]):
            g = g.sort_values("val", ascending=False)
            rows = [[r.hs4, round(float(r.pci), 2), round(float(r.val) / 1e9, 3)] for r in g.itertuples()]
            products[fl].setdefault(iso, {})[str(int(yr))] = rows
            nrows += len(rows)

    payload = {"years": years, "flows": [fl for fl, _ in flows], "topN": TOPN, "products": products}
    (OUT / "country_products.json").write_text(json.dumps(payload))

    import gzip
    raw = (OUT / "country_products.json").stat().st_size
    gz = len(gzip.compress((OUT / "country_products.json").read_bytes(), 6))
    print(f"wrote country_products.json: raw {raw/1e6:.2f} MB  gz {gz/1e6:.2f} MB  "
          f"({nrows:,} product rows, top-{TOPN} x {len(countries)} countries x {len(years)} yr x 2 flows)")


if __name__ == "__main__":
    main()
