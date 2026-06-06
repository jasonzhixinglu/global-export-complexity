"""Compare representations against the RAW empirical distribution of exports over PCI
(not against the smoothed KDE curve).

For each country-year (export flow) the truth is the weighted empirical distribution
of product export value over PCI -> empirical CDF (a step function, exact).

We measure each candidate's distance to truth with metrics that don't depend on any
bandwidth choice:
  KS  = max |CDF_cand - CDF_emp|   (share of export value misplaced along PCI)
  W1  = integral|CDF diff| dPCI    (Wasserstein-1, in PCI units)

Candidates:
  KDE-med (bw0.10)   the curve we currently display  -> its KS is the SMOOTHING FLOOR
  KDE-low (bw0.05)   sharper estimate
  coarse M=50        coarse-grid reconstruction of KDE-med (Path C)
  GMM K=3/4/5        K-component mixture fit to the raw data (3K floats)

If a compressor's KS is at or below the KDE-med floor, it's effectively lossless
against the truth.  Run:  python scripts/prototype_truth.py
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

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(0)
XG = np.linspace(-3, 3, 1201)            # fine grid for CDF comparison
YEARS = [2000, 2005, 2010, 2015, 2020, 2024]


def emp_cdf(pci, w):
    o = np.argsort(pci)
    p, ww = pci[o], w[o]
    c = np.cumsum(ww); c /= c[-1]
    return np.interp(XG, p, c, left=0.0, right=1.0)


def kde_cdf(pci, w, h):
    w = w / w.sum()
    # CDF of Gaussian KDE = sum_i w_i * Phi((x-pci_i)/h)
    return (w[:, None] * norm.cdf((XG[None, :] - pci[:, None]) / h)).sum(0)


def coarse_cdf(pci, w, h, M):
    # reconstruct the KDE *density* on a coarse grid + cubic spline, then integrate to a CDF
    from scipy.interpolate import CubicSpline
    xfull = np.linspace(-3, 3, 150)
    dens = (w[None, :] / w.sum() * norm.pdf((xfull[:, None] - pci[None, :]) / h) / h).sum(1)
    idx = np.linspace(0, 149, M).round().astype(int)
    cs = CubicSpline(xfull[idx], dens[idx])
    d = np.clip(cs(XG), 0, None)
    c = np.cumsum(d); c /= c[-1]
    return c


def gmm_cdf(pci, w, K):
    # fit GMM to raw data by resampling proportional to export value
    p = w / w.sum()
    draws = RNG.choice(pci, size=20000, p=p)
    g = GaussianMixture(K, covariance_type="full", random_state=0, n_init=2, max_iter=200)
    g.fit(draws.reshape(-1, 1))
    mu = g.means_.ravel(); sd = np.sqrt(g.covariances_.ravel()); pi = g.weights_
    return (pi[:, None] * norm.cdf((XG[None, :] - mu[:, None]) / sd[:, None])).sum(0)


def ks_w1(cand, emp):
    d = np.abs(cand - emp)
    return d.max(), np.trapezoid(d, XG)


def main():
    df = pd.read_csv(cfg.RAW_CSV, usecols=["country_iso3_code", "year", "export_value", "pci"],
                     dtype={"country_iso3_code": str})
    df = df[df["year"].isin(YEARS)].dropna(subset=["pci", "export_value"])
    df = df[(df["export_value"] > 0) & df["pci"].between(-3, 3)]
    # top-50 exporters overall (match dashboard universe)
    top = df.groupby("country_iso3_code")["export_value"].sum().nlargest(50).index
    df = df[df["country_iso3_code"].isin(top)]

    cands = {"KDE-med(bw.10)": [], "KDE-low(bw.05)": [], "coarse M=50": [],
             "GMM K=3": [], "GMM K=4": [], "GMM K=5": []}
    sizes = {"KDE/coarse 150pt": 150, "coarse M=50": 50, "GMM K=3": 9, "GMM K=4": 12, "GMM K=5": 15}
    n = 0
    for (c, yr), g in df.groupby(["country_iso3_code", "year"]):
        if len(g) < 20:
            continue
        pci = g["pci"].to_numpy(float); w = g["export_value"].to_numpy(float)
        emp = emp_cdf(pci, w)
        cands["KDE-med(bw.10)"].append(ks_w1(kde_cdf(pci, w, 0.10), emp))
        cands["KDE-low(bw.05)"].append(ks_w1(kde_cdf(pci, w, 0.05), emp))
        cands["coarse M=50"].append(ks_w1(coarse_cdf(pci, w, 0.10, 50), emp))
        for K in (3, 4, 5):
            cands[f"GMM K={K}"].append(ks_w1(gmm_cdf(pci, w, K), emp))
        n += 1
    print(f"country-years compared (export flow, top-50, {YEARS}): {n}\n")
    print(f"{'representation':>18} {'floats':>7} {'KS p50':>8} {'KS p95':>8} {'W1 p50':>8} {'W1 p95':>8}")
    floatmap = {"KDE-med(bw.10)": 150, "KDE-low(bw.05)": 150, "coarse M=50": 50,
                "GMM K=3": 9, "GMM K=4": 12, "GMM K=5": 15}
    for k, v in cands.items():
        v = np.array(v)
        print(f"{k:>18} {floatmap[k]:>7} {100*np.median(v[:,0]):7.2f}% {100*np.percentile(v[:,0],95):7.2f}% "
              f"{np.median(v[:,1]):8.4f} {np.percentile(v[:,1],95):8.4f}")
    print("\nKS = max share of export value misplaced along PCI; W1 in PCI units.")
    print("KDE-med is the displayed curve: its KS is the smoothing floor. A compressor")
    print("at or below that floor adds nothing detectable relative to the raw truth.")


if __name__ == "__main__":
    main()
