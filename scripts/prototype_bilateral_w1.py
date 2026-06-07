"""Compare CDF-based error (Wasserstein-1) vs sup-norm KS for bilateral corridor GMM fits.

Intuition under test: the PDF of a concentrated corridor is badly off (a spike becomes a
bump), but the CDF is "not far off" -- the disagreement is a thin band around the spike, so
the transport distance W1 = integral|F_fit - F_emp| dPCI stays small even when KS is large.

Caches the bilateral load to parquet so only the first run pays the multi-GB read.
Run:  python scripts/prototype_bilateral_w1.py
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
YEAR = 2022; N = 30
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 600)
CACHE = cfg.DATA_DIR / "derived" / f"bilateral_top{N}_{YEAR}.parquet"


def fit(pci, w, K):
    p = w / w.sum(); n = min(3000, max(400, 8 * len(pci)))
    d = RNG.choice(pci, n, p=p)
    g = GaussianMixture(K, random_state=0, n_init=1, max_iter=150, reg_covar=1e-4).fit(d.reshape(-1, 1))
    return np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])


def cdfs(par, pci, w):
    o = np.argsort(pci); c = np.cumsum(w[o]); c = c / c[-1]
    emp = np.interp(XG, pci[o], c, left=0, right=1)
    pi = par[:, 0] / par[:, 0].sum()
    fit_cdf = (pi[:, None] * norm.cdf((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None])).sum(0)
    d = np.abs(fit_cdf - emp)
    return d.max(), np.trapezoid(d, XG)            # KS, W1


def load():
    if CACHE.exists():
        print("loading cached bilateral ...", flush=True)
        return pd.read_parquet(CACHE)
    print("first run: reading the big bilateral file (chunked) ...", flush=True)
    base = gdata.load_clean(years=[YEAR]); base = base[base.year == YEAR]
    top = base.groupby("country_iso3_code")["export_value"].sum().drop(
        index=[c for c in ("ANS",) if c in base.country_iso3_code.values], errors="ignore").nlargest(N).index.tolist()
    pci_map = base.assign(p4=base.product_hs92_code.str.zfill(4)).groupby("p4")["pci"].first()
    bl = gdata.load_bilateral(year_ranges=("2020_2024",), origins=top, dests=top, years=[YEAR], hs_level=4)
    bl["p4"] = bl.product_hs92_code.str.zfill(4); bl["pci"] = bl.p4.map(pci_map)
    bl = bl.dropna(subset=["pci"]); bl = bl[bl.pci.between(cfg.PCI_LO, cfg.PCI_HI) & (bl.export_value > 0)]
    bl = bl[["country_iso3_code", "partner_iso3_code", "p4", "pci", "export_value"]]
    CACHE.parent.mkdir(parents=True, exist_ok=True); bl.to_parquet(CACHE)
    return bl


def main():
    bl = load()
    rows = []
    for (o, d), g in bl.groupby(["country_iso3_code", "partner_iso3_code"]):
        if o == d or len(g) < 8:
            continue
        pci = g.pci.to_numpy(float); w = g.export_value.to_numpy(float)
        top1 = w.max() / w.sum()                      # concentration: largest single product share
        best = min((cdfs(fit(pci, w, K), pci, w), K) for K in (3, 5, 8))  # by (KS,...) -> lowest KS
        (ks, w1), K = best
        rows.append({"n": len(g), "top1": top1, "ks": ks, "w1": w1})
    r = pd.DataFrame(rows)
    print(f"\ncorridors: {len(r)}\n")
    print(f"{'metric':>10} {'median':>8} {'p75':>8} {'p95':>8} {'max':>8}")
    print(f"{'KS (%)':>10} {100*r.ks.median():8.1f} {100*r.ks.quantile(.75):8.1f} {100*r.ks.quantile(.95):8.1f} {100*r.ks.max():8.1f}")
    print(f"{'W1 (PCI)':>10} {r.w1.median():8.3f} {r.w1.quantile(.75):8.3f} {r.w1.quantile(.95):8.3f} {r.w1.max():8.3f}")
    print("  (country-level totals for reference: KS ~6.7%, W1 ~0.03 PCI)\n")

    print("Split by concentration (top-1 product's share of corridor value):")
    print(f"  {'top-1 share':>14} {'corridors':>10} {'KS med':>8} {'KS p95':>8} {'W1 med':>8} {'W1 p95':>8}")
    for lo, hi in [(0, .15), (.15, .30), (.30, .50), (.50, 1.01)]:
        m = (r.top1 >= lo) & (r.top1 < hi)
        if m.sum():
            print(f"  {f'{int(lo*100)}-{int(hi*100)}%':>14} {int(m.sum()):>10} "
                  f"{100*r.ks[m].median():>7.1f}% {100*r.ks[m].quantile(.95):>7.1f}% "
                  f"{r.w1[m].median():>8.3f} {r.w1[m].quantile(.95):>8.3f}")


if __name__ == "__main__":
    main()
