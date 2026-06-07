"""Can we derive market-share-by-PCI as a ratio of value densities, instead of
storing the local-linear share curves?

Compares, at the share-grid points (export flow, latest year):
  LL       stored local-linear share (what we ship)            -- baseline
  NW_KDE   ratio of TRUE value KDEs  num_c(x)/den_all(x)        -- estimator change only
  NW_GMM   T_c f_c^GMM / (T_world g_world^GMM)                  -- the proposed method

Δ tells us (a) how much deviation is NW-vs-local-linear boundary bias [NW_KDE-LL]
and (b) how much the stored-mixture approximation adds [NW_GMM-NW_KDE].

Run:  python scripts/prototype_share_ratio.py
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(0)
DATA = cfg.ROOT / "dashboard" / "public" / "data"
H = 0.10                       # med bandwidth / blur
SHOW = ["CHN", "DEU", "USA", "JPN"]


def kern_num(x, pci, v):
    """Unnormalised value-KDE: sum_i v_i * phi((x-pci_i)/h)."""
    return (v[None, :] * norm.pdf((x[:, None] - pci[None, :]) / H)).sum(1)


def mix_shape(par, x, b=H):
    par = np.array(par); pi = par[:, 0] / par[:, 0].sum()
    sd = np.sqrt(par[:, 2] ** 2 + b ** 2)
    return (pi[:, None] * norm.pdf((x[None, :] - par[:, 1][:, None]) / sd[:, None]) / sd[:, None]).sum(0)


def fit_world(pci, v, K=8):
    p = v / v.sum()
    d = RNG.choice(pci, 12000, p=p)
    g = GaussianMixture(K, random_state=0, n_init=2, max_iter=300, reg_covar=1e-4).fit(d.reshape(-1, 1))
    return np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])


def main():
    meta = json.loads((DATA / "meta.json").read_text())
    series = json.loads((DATA / "series.json").read_text())
    gmm = json.loads((DATA / "gmm.json").read_text())
    grid = np.array(meta["shareGrid"])
    yr = max(meta["years"]); y = str(yr)
    tracked = gmm["countries"]

    df = gdata.load_clean(years=[yr])
    df = df[(df.year == yr) & (df.export_value > 0) & df.pci.between(cfg.PCI_LO, cfg.PCI_HI)]
    pci_all = df.pci.to_numpy(float); v_all = df.export_value.to_numpy(float)
    T_world = v_all.sum()

    den_kde = kern_num(grid, pci_all, v_all)                  # world value KDE (unnormalised)
    world_par = fit_world(pci_all, v_all)
    g_world = mix_shape(world_par, grid)                      # world shape (integrates to 1)
    in_band = den_kde > 0.02 * den_kde.max()                  # ignore the empty tails

    shareLL = series["share"]["export"]["med"]
    totB = series["totalB"]["export"]
    mixE = gmm["mix"]["export"]

    # consistent denominator: sum of the SAME stored mixtures (+ a rest-of-world term),
    # so every share is component/sum-of-components, bounded in [0,1] and stable in the tails.
    Tc = {c: (totB.get(c, {}).get(y) or 0.0) * 1e9 for c in tracked}
    fC = {c: (mix_shape(mixE[c][y], grid) if c in mixE and y in mixE[c] else np.zeros_like(grid)) for c in tracked}
    rest = df[~df.country_iso3_code.isin(tracked)]
    T_rest = rest.export_value.sum()
    f_rest = mix_shape(fit_world(rest.pci.to_numpy(float), rest.export_value.to_numpy(float)), grid)
    den_cons = sum(Tc[c] * fC[c] for c in tracked) + T_rest * f_rest

    dev_kde, dev_gmm, dev_cons = [], [], []
    sumLL = np.zeros_like(grid); sumNW = np.zeros_like(grid)
    curves = {}
    for c in tracked:
        ll = np.array(shareLL.get(c, {}).get(y, [np.nan] * len(grid)), float)
        cd = df[df.country_iso3_code == c]
        nw_kde = kern_num(grid, cd.pci.to_numpy(float), cd.export_value.to_numpy(float)) / np.maximum(den_kde, 1e-12)
        nw_gmm = (Tc[c] * fC[c]) / np.maximum(T_world * g_world, 1e-12)          # independent world fit
        nw_cons = (Tc[c] * fC[c]) / np.maximum(den_cons, 1e-12)                  # sum-of-mixtures denom
        sumLL += np.nan_to_num(ll); sumNW += nw_kde
        m = in_band & np.isfinite(ll)
        dev_kde.append(np.abs(nw_kde[m] - ll[m]))
        dev_gmm.append(np.abs(nw_gmm[m] - ll[m]))
        dev_cons.append(np.abs(nw_cons[m] - ll[m]))
        if c in SHOW:
            curves[c] = (ll, nw_kde, nw_cons)

    dk = np.concatenate(dev_kde); dg = np.concatenate(dev_gmm); dc = np.concatenate(dev_cons)
    print(f"export {yr}, {len(tracked)} tracked countries, in-band share-grid points\n")
    print(f"{'comparison':>26} {'median |d|':>11} {'p95 |d|':>9} {'max |d|':>9}   (d in share percentage points)")
    print(f"{'NW_KDE       vs local-linear':>26} {100*np.median(dk):10.2f}% {100*np.percentile(dk,95):8.2f}% {100*dk.max():8.2f}%")
    print(f"{'NW_GMM indep vs local-linear':>26} {100*np.median(dg):10.2f}% {100*np.percentile(dg,95):8.2f}% {100*dg.max():8.2f}%")
    print(f"{'NW_GMM sum   vs local-linear':>26} {100*np.median(dc):10.2f}% {100*np.percentile(dc,95):8.2f}% {100*dc.max():8.2f}%")

    # boundary vs centre for the full method
    centre = in_band & (np.abs(grid) <= 1.5)
    edge = in_band & (np.abs(grid) > 1.5)
    def band_dev(mask):
        d = []
        for c in tracked:
            ll = np.array(shareLL.get(c, {}).get(y, [np.nan]*len(grid)), float)
            cd = df[df.country_iso3_code == c]
            nw = kern_num(grid, cd.pci.to_numpy(float), cd.export_value.to_numpy(float))/np.maximum(den_kde,1e-12)
            mm = mask & np.isfinite(ll); d.append(np.abs(nw[mm]-ll[mm]))
        return np.concatenate(d)
    print(f"\nNW_KDE-LL by region:  centre |PCI|<=1.5 median {100*np.median(band_dev(centre)):.2f}%   "
          f"edge |PCI|>1.5 median {100*np.median(band_dev(edge)):.2f}%")
    print(f"adding-up over the 50 tracked (should match): "
          f"LL sum @PCI~0 {sumLL[np.argmin(np.abs(grid))]:.3f}  NW sum @PCI~0 {sumNW[np.argmin(np.abs(grid))]:.3f}")

    fig, axes = plt.subplots(1, 4, figsize=(20, 4.2))
    for ax, c in zip(axes, SHOW):
        ll, nk, ng = curves[c]
        ax.plot(grid, 100*ll, lw=2, label="local-linear (stored)")
        ax.plot(grid, 100*nk, lw=1.5, ls="--", label="NW ratio (KDE)")
        ax.plot(grid, 100*ng, lw=1.5, ls=":", label="NW ratio (GMM, sum-denom)")
        ax.set_title(f"{c} export share {yr}"); ax.set_xlim(-2.5, 2.5)
        ax.set_xlabel("PCI"); ax.set_ylabel("% of world"); ax.legend(fontsize=7)
    fig.tight_layout()
    out = cfg.ROOT / "results" / "figures" / "share_ratio_check.png"
    fig.savefig(out, dpi=110); print("\nwrote", out)


if __name__ == "__main__":
    main()
