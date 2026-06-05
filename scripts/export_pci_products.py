"""Build the per-PCI product drill-down DB for the Explorer.

Ships the FULL per-year product list (HS4 code, PCI, world export value) so the client can
dynamically pick the products nearest a clicked PCI and reorder them as the selection moves
(binning made the list static within a bin). Names from the Atlas HS92 classification.

Usage:  python scripts/export_pci_products.py
Output: dashboard/public/data/pci_products.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

OUT = cfg.ROOT / "dashboard" / "public" / "data"
NAMES_CSV = cfg.RAW_DIR / "product_hs92.csv"
LO, HI = -3.0, 3.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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

    years = list(range(2000, 2025))
    by_year, used = {}, set()
    for yr in years:
        dy = df[df["year"] == yr]
        prod = dy.groupby("product_hs92_code").agg(pci=("pci", "first"),
                                                   val=("export_value", "sum")).reset_index()
        prod["hs4"] = prod["product_hs92_code"].str.zfill(4)
        prod = prod[(prod["pci"].between(LO, HI)) & (prod["val"] > 0)].sort_values("pci")
        rows = [[r.hs4, round(float(r.pci), 2), round(r.val / 1e9, 2)] for r in prod.itertuples()]
        used.update(r[0] for r in rows)
        by_year[str(yr)] = rows  # [hs4, pci, valueB], sorted by pci ascending

    out = {
        "lo": LO, "hi": HI, "years": years,
        "names": {c: name_of.get(c, c) for c in sorted(used)},
        "byYear": by_year,
    }
    (OUT / "pci_products.json").write_text(json.dumps(out))
    sz = (OUT / "pci_products.json").stat().st_size / 1024
    npy = sum(len(v) for v in by_year.values()) / len(by_year)
    print(f"wrote pci_products.json: {sz:.0f} KB | {len(years)} years · ~{npy:.0f} products/yr · "
          f"{len(used)} named")


if __name__ == "__main__":
    main()
