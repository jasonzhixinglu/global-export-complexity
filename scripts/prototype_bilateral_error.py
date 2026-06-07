"""Sense of GMM estimation error for BILATERAL (origin->destination) PCI distributions.

Bilateral corridors are far thinner than country totals (fewer products per cell), so the
mixture fit is noisier. We measure it on the top-30 x top-30 corridors for one year -- these
include the thinnest small-country pairs (worst case); topN<->ROW and ROW<->ROW corridors
aggregate many countries and are thicker (lower error), so this is a conservative read.

For each corridor we fit a Gaussian mixture (fixed K=5, and an adaptive best-of {3,5,8})
and report KS vs the raw empirical CDF, stratified by how many HS4 products the corridor has.

Run:  python scripts/prototype_bilateral_error.py
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(0)
YEAR = 2022
N = 30
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 600)
MIN_PROD = 8


def ks(par, pci, w):
    o = np.argsort(pci); c = np.cumsum(w[o]); c = c / c[-1]
    emp = np.interp(XG, pci[o], c, left=0, right=1)
    pi = par[:, 0] / par[:, 0].sum()
    mcdf = (pi[:, None] * norm.cdf((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None])).sum(0)
    return float(np.abs(mcdf - emp).max())


def fit(pci, w, K):
    p = w / w.sum()
    n = min(3000, max(400, 8 * len(pci)))
    d = RNG.choice(pci, n, p=p)
    g = GaussianMixture(K, random_state=0, n_init=1, max_iter=150, reg_covar=1e-4).fit(d.reshape(-1, 1))
    return np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])


def main():
    print(f"Loading HS4 PCI map + top-{N} for {YEAR} ...", flush=True)
    base = gdata.load_clean(years=[YEAR])
    base = base[base.year == YEAR]
    top = base.groupby("country_iso3_code")["export_value"].sum()
    top = top.drop(index=[c for c in ("ANS",) if c in top.index], errors="ignore")
    top = list(top.nlargest(N).index)
    pci_map = (base.assign(p4=base.product_hs92_code.str.zfill(4))
               .groupby("p4")["pci"].first())

    print("Loading bilateral (top-N x top-N, chunked read of the big file) ...", flush=True)
    bl = gdata.load_bilateral(year_ranges=("2020_2024",), origins=top, dests=top,
                              years=[YEAR], hs_level=4)
    bl["p4"] = bl.product_hs92_code.str.zfill(4)
    bl["pci"] = bl.p4.map(pci_map)
    bl = bl.dropna(subset=["pci"])
    bl = bl[bl.pci.between(cfg.PCI_LO, cfg.PCI_HI) & (bl.export_value > 0)]

    rows = []
    for (o, d), g in bl.groupby(["country_iso3_code", "partner_iso3_code"]):
        if o == d or len(g) < MIN_PROD:
            continue
        pci = g.pci.to_numpy(float); w = g.export_value.to_numpy(float)
        ess = w.sum() ** 2 / (w ** 2).sum()
        rec = {"o": o, "d": d, "nprod": len(g), "ess": ess}
        ksk = {K: ks(fit(pci, w, K), pci, w) for K in (3, 5, 8)}
        rec["ks5"] = ksk[5]
        rec["ks_adapt"] = min(ksk.values())   # best of {3,5,8} ~ adaptive
        rows.append(rec)
    r = pd.DataFrame(rows)
    print(f"\ncorridors fitted: {len(r)} (of {N}x{N-1} possible, with >= {MIN_PROD} products)\n")

    def line(name, v):
        print(f"  {name:>22} median {100*np.median(v):5.1f}%  p75 {100*np.percentile(v,75):5.1f}%  "
              f"p95 {100*np.percentile(v,95):5.1f}%  max {100*np.max(v):5.1f}%")
    print("KS vs raw truth (share of bilateral value misplaced along PCI):")
    line("fixed K=5", r.ks5); line("adaptive K (best 3/5/8)", r.ks_adapt)
    print("\n  for reference: country-level totals were median ~6.1%, p95 ~24%\n")

    print("How thin are corridors? distribution of #HS4 products per corridor:")
    for q in (10, 25, 50, 75, 90):
        print(f"    p{q:>2}: {int(np.percentile(r.nprod, q)):>4} products")

    print("\nError vs corridor richness (adaptive K), bucketed by #products:")
    bins = [(0, 50), (50, 150), (150, 400), (400, 10000)]
    print(f"  {'#products':>14} {'corridors':>10} {'KS median':>10} {'KS p95':>8}")
    for lo, hi in bins:
        m = (r.nprod >= lo) & (r.nprod < hi)
        if m.sum():
            label = f"{lo}-{hi}" if hi < 10000 else f"{lo}+"
            print(f"  {label:>14} {int(m.sum()):>10} "
                  f"{100*np.median(r.ks_adapt[m]):>9.1f}% {100*np.percentile(r.ks_adapt[m],95):>7.1f}%")


if __name__ == "__main__":
    main()
