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
TOPN = 50         # significant categories by value
BINW = 0.25       # PCI coverage: a few categories per 0.25-wide bin so no band is empty
BIN_N = 3         # top-by-value kept per interior bin
TAIL_N = 10       # kept in the lowest- and highest-PCI occupied bins (sparse tails)


def pick(g):
    """Union of: top-N by value (significance) + per-0.25-PCI-bin top-few (spread) +
    extra in the two extreme occupied bins (tails). Guarantees PCI coverage so the
    drill-down is never empty within the country's actual export range."""
    keep = set(g.nlargest(TOPN, "val")["hs4"])
    g = g.assign(_b=np.floor((g["pci"] - cfg.PCI_LO) / BINW).astype(int))
    occ = sorted(g["_b"].unique())
    lo, hi = occ[0], occ[-1]
    for bb, gb in g.groupby("_b"):
        keep.update(gb.nlargest(TAIL_N if bb in (lo, hi) else BIN_N, "val")["hs4"])
    return g[g["hs4"].isin(keep)]


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
        for (iso, yr), g in agg.groupby(["country_iso3_code", "year"]):
            sel = pick(g).sort_values("val", ascending=False)
            rows = [[r.hs4, round(float(r.pci), 2), round(float(r.val) / 1e9, 3)] for r in sel.itertuples()]
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
