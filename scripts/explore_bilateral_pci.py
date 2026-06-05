"""Prototype: bilateral (origin x destination) export distribution by complexity, + sizing.

Method (per design): aggregate Atlas bilateral HS6 -> HS4 (data.load_bilateral), join the
HS4 PCI mapping, then kernel-weight each origin->destination flow over the PCI grid (a full
distribution, or just a value-weighted mean complexity).

Not wired into the dashboard. Run to reproduce the size estimates for the tracking object.

Findings (2020-2024 file): ~68M HS6 rows, ~37k origin-dest pairs, ~31.5k active
(origin,dest,year) cells/yr. Tracking-object size:
  full kernel curve (100 pts/cell), 25y ~ 0.47 GB   (server-side only)
  origin x 6 dest-regions, full curve ~ 18 MB        (embeddable)
  kernel-weighted MEAN complexity / flow ~ 4.7 MB    (embeddable)

Usage:  python scripts/explore_bilateral_pci.py
"""
from __future__ import annotations

import sys, time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg, data as gdata, estimators as est

GRID = np.linspace(-2.5, 2.5, 100)
H = 0.30


def hs4_pci(year):
    df = pd.read_csv(cfg.RAW_CSV, usecols=["product_hs92_code", "year", "pci"],
                     dtype={"product_hs92_code": str})
    return df[df["year"] == year].dropna(subset=["pci"]).groupby("product_hs92_code")["pci"].first()


def demo(origin="CHN", year=2024, n=4):
    pci = hs4_pci(year)
    bil = gdata.load_bilateral(year_ranges=["2020_2024"], origins=[origin], years=[year])
    bil["pci"] = bil["product_hs92_code"].map(pci)
    bil = bil.dropna(subset=["pci"])
    print(f"[demo] {origin} {year}: {bil.partner_iso3_code.nunique()} destinations, rows={len(bil):,}")
    for d in bil.groupby("partner_iso3_code")["export_value"].sum().nlargest(n).index:
        s = bil[bil.partner_iso3_code == d]
        mean_pci = (s.pci * s.export_value).sum() / s.export_value.sum()
        curve = est.density_fixed(s.pci.values, s.export_value.values, GRID, H)
        print(f"   {origin}->{d}: ${s.export_value.sum()/1e9:6.1f}B  mean PCI {mean_pci:+.2f}  "
              f"curve_ok={np.isfinite(curve).all()}")


def size(year_range="2020_2024"):
    cells, pairs, rows = set(), set(), 0
    for ch in pd.read_csv(cfg.bilateral_path(year_range),
                          usecols=["country_iso3_code", "partner_iso3_code", "year"],
                          dtype=str, chunksize=5_000_000):
        rows += len(ch)
        k = ch["country_iso3_code"] + ">" + ch["partner_iso3_code"]
        cells.update((k + "|" + ch["year"]).unique())
        pairs.update(k.unique())
    yrs = len({c.split("|")[1] for c in cells})
    per_yr = len(cells) // max(yrs, 1)
    print(f"[size] HS6 rows={rows:,} | pairs={len(pairs):,} | cells={len(cells):,} | "
          f"years={yrs} | cells/yr={per_yr:,}")
    cells25 = per_yr * 25
    B, G = 6, len(GRID)
    print(f"  full curve 25y (~{cells25:,} cells): ~{cells25*G*B/1e9:.2f} GB json")
    print(f"  mean-PCI scalar 25y:                ~{cells25*B/1e6:.1f} MB json")
    print(f"  origin x 6 regions, full curve:     ~{200*6*25*G*B/1e6:.1f} MB json")


if __name__ == "__main__":
    t = time.time()
    demo()
    size()
    print(f"(done in {time.time()-t:.0f}s)")
