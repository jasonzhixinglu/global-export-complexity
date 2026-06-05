"""Build the per-PCI product drill-down DB for the Explorer (NSICX-style detail-on-select).

For each year and PCI bin, list the top-10 HS4 products by world export value whose PCI
falls in that bin: [code, value $B, pci]. Names come from the Atlas HS92 classification.

Usage:  python scripts/export_pci_products.py
Output: dashboard/public/data/pci_products.json
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
NAMES_CSV = cfg.RAW_DIR / "product_hs92.csv"
LO, HI, W = -2.5, 2.5, 0.25
TOPN = 10


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # HS4 code -> name
    cls = pd.read_csv(NAMES_CSV, dtype=str)
    cls = cls[cls["product_level"] == "4"]
    name_of = dict(zip(cls["product_hs92_code"].str.zfill(4), cls["product_name"]))

    df = pd.read_csv(cfg.RAW_CSV,
                     usecols=["product_hs92_code", "year", "export_value", "pci"],
                     dtype={"product_hs92_code": str})
    df["year"] = df["year"].astype(int)
    df = df[df["year"].between(2000, 2024)]
    df["export_value"] = pd.to_numeric(df["export_value"], errors="coerce")
    df["pci"] = pd.to_numeric(df["pci"], errors="coerce")
    df = df.dropna(subset=["pci", "export_value"])

    edges = np.round(np.arange(LO, HI + 1e-9, W), 3)
    centers = [round((edges[i] + edges[i + 1]) / 2, 3) for i in range(len(edges) - 1)]
    years = list(range(2000, 2025))

    top = {}
    used_codes = set()
    for yr in years:
        dy = df[df["year"] == yr]
        prod = dy.groupby("product_hs92_code").agg(pci=("pci", "first"),
                                                   val=("export_value", "sum")).reset_index()
        prod["hs4"] = prod["product_hs92_code"].str.zfill(4)
        prod = prod[(prod["pci"] >= LO) & (prod["pci"] <= HI)]
        bins = pd.cut(prod["pci"], bins=edges, labels=False, include_lowest=True)
        prod = prod.assign(_bin=bins)
        per_bin = []
        for bi in range(len(centers)):
            seg = prod[prod["_bin"] == bi].nlargest(TOPN, "val")
            rows = [[r.hs4, round(r.val / 1e9, 3), round(float(r.pci), 2)] for r in seg.itertuples()]
            used_codes.update(r[0] for r in rows)
            per_bin.append(rows)
        top[str(yr)] = per_bin

    out = {
        "lo": LO, "hi": HI, "binWidth": W, "centers": centers, "years": years,
        "names": {c: (name_of.get(c, c)) for c in sorted(used_codes)},
        "top": top,   # top[year][binIndex] = [[hs4, valueB, pci], ...]
    }
    (OUT / "pci_products.json").write_text(json.dumps(out))
    sz = (OUT / "pci_products.json").stat().st_size / 1024
    print(f"wrote pci_products.json: {sz:.0f} KB | {len(centers)} bins · {len(years)} years · "
          f"{len(used_codes)} distinct products named")


if __name__ == "__main__":
    main()
