"""Temporal stability of a per-year GMM fit (the gating risk for the animation).

For each country x flow we fit a K-component mixture every year, two ways:
  COLD  independent fit each year (n_init=3, random)
  WARM  fit year 1, then init each year from the PREVIOUS year's parameters

Jitter metric: mean adjacent-year L2 change of the reconstructed density, divided
by the same change for the displayed KDE-med curve (the intended smooth motion).
  ~1.0 => tracks the true motion;  >>1.0 => adds shimmer not in the data.

Also: how far sorted component means jump year-to-year (mode hopping), and KS-to-
truth (warm must not hurt accuracy).  Run: python scripts/prototype_gmm_stability.py
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
XG = np.linspace(-3, 3, 200)
K = 5


def dens(par):
    pi, mu, sd = par[:, 0], par[:, 1], par[:, 2]
    return (pi[:, None] * norm.pdf((XG[None, :] - mu[:, None]) / sd[:, None]) / sd[:, None]).sum(0)


def cdf(par):
    pi, mu, sd = par[:, 0], par[:, 1], par[:, 2]
    return (pi[:, None] * norm.cdf((XG[None, :] - mu[:, None]) / sd[:, None])).sum(0)


def emp_cdf(pci, w):
    o = np.argsort(pci); p, ww = pci[o], w[o]
    c = np.cumsum(ww); c /= c[-1]
    return np.interp(XG, p, c, left=0, right=1)


def kde_dens(pci, w, h=0.10):
    w = w / w.sum()
    return (w[None, :] * norm.pdf((XG[:, None] - pci[None, :]) / h) / h).sum(1)


def fit(draws, warm=None):
    kw = dict(n_components=K, random_state=0, max_iter=200)
    if warm is not None:
        g = GaussianMixture(n_init=1, means_init=warm[:, 1:2],
                            weights_init=warm[:, 0] / warm[:, 0].sum(),
                            precisions_init=(1 / warm[:, 2] ** 2).reshape(K, 1, 1), **kw)
    else:
        g = GaussianMixture(n_init=3, **kw)
    g.fit(draws.reshape(-1, 1))
    return np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])


def main():
    df = pd.read_csv(cfg.RAW_CSV,
                     usecols=["country_iso3_code", "year", "export_value", "import_value", "pci"],
                     dtype={"country_iso3_code": str}).dropna(subset=["pci"])
    df = df[df["pci"].between(-3, 3)]
    top = list(df.groupby("country_iso3_code")["export_value"].sum().nlargest(40).index)
    years = sorted(y for y in df["year"].unique() if 2000 <= y <= 2024)

    res = {"cold": {"jit": [], "hop": [], "ks": []}, "warm": {"jit": [], "hop": [], "ks": []}}
    for c in top:
        for fl in ("export_value", "import_value"):
            sub = df[df.country_iso3_code == c]
            # build per-year draws + reference
            draws_y, kref, ecdf = {}, {}, {}
            for yr in years:
                g = sub[sub.year == yr]
                w = g[fl].to_numpy(float); pci = g["pci"].to_numpy(float)
                m = w > 0
                if m.sum() < 10:
                    draws_y[yr] = None; continue
                p = w[m] / w[m].sum()
                draws_y[yr] = RNG.choice(pci[m], 6000, p=p)
                kref[yr] = kde_dens(pci[m], w[m]); ecdf[yr] = emp_cdf(pci[m], w[m])
            ys = [y for y in years if draws_y[y] is not None]
            if len(ys) < 10:
                continue
            for mode in ("cold", "warm"):
                params, prev = {}, None
                for yr in ys:
                    params[yr] = fit(draws_y[yr], warm=prev if mode == "warm" else None)
                    prev = params[yr]
                # metrics
                dgrid = XG[1] - XG[0]
                gjit = [np.linalg.norm(dens(params[ys[i+1]]) - dens(params[ys[i]])) for i in range(len(ys)-1)]
                kjit = [np.linalg.norm(kref[ys[i+1]] - kref[ys[i]]) for i in range(len(ys)-1)]
                hop = [np.abs(np.sort(params[ys[i+1]][:,1]) - np.sort(params[ys[i]][:,1])).max()
                       for i in range(len(ys)-1)]
                ks = [np.abs(cdf(params[y]) - ecdf[y]).max() for y in ys]
                res[mode]["jit"].append(np.mean(gjit) / max(np.mean(kjit), 1e-9))
                res[mode]["hop"].append(np.mean(hop))
                res[mode]["ks"].append(np.mean(ks))

    print(f"series compared: {len(res['cold']['jit'])} (country x flow), K={K}\n")
    print(f"{'':>6} {'jitter/ref p50':>15} {'jitter/ref p95':>15} {'mean-hop p95':>13} {'KS-truth p50':>13}")
    for mode in ("cold", "warm"):
        j = np.array(res[mode]["jit"]); h = np.array(res[mode]["hop"]); k = np.array(res[mode]["ks"])
        print(f"{mode:>6} {np.median(j):15.2f} {np.percentile(j,95):15.2f} "
              f"{np.percentile(h,95):13.3f} {100*np.median(k):12.2f}%")
    print("\njitter/ref ~1 = tracks true motion; >>1 = shimmer. hop in PCI units (mode jumps).")


if __name__ == "__main__":
    main()
