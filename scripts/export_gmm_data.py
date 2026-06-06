"""Encode each country's export/import distribution over PCI as a Gaussian mixture.

One mixture per (flow, country, year), fit to the RAW weighted distribution of
product value over PCI -- replacing the high-dimensional density grid in series.json.

Design (see the analysis discussion):
  * K is chosen per (flow, country) by BIC, then held FIXED across years so the
    component count never changes mid-animation.
  * Years are fit sequentially, warm-started from the previous year, so components
    track smoothly instead of swapping (cold fitting jitters ~3.8x the true motion;
    warm ~0.95x).
  * Smoothness is NOT stored per level: a render-time blur b maps sigma_k ->
    sqrt(sigma_k^2 + b^2), so one mixture yields the whole Low/Med/High continuum.

Stored shape integrates to 1 (weights sum to 1); multiply by series.totalB for $.
Writes dashboard/public/data/gmm.json.  Run: python scripts/export_gmm_data.py
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
import numpy as np
from scipy.stats import norm
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

warnings.filterwarnings("ignore")
OUT = cfg.ROOT / "dashboard" / "public" / "data"
DERIVED = cfg.DATA_DIR / "derived"
RNG = np.random.default_rng(0)
KMAX = 8
NDRAW = 3000           # resample size for fitting
MIN_PROD = 12          # need at least this many products in a year to fit


XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 600)


def draws_of(pci, w):
    p = w / w.sum()
    return RNG.choice(pci, NDRAW, p=p)


def ks_to_truth(par, pci, w):
    """Max gap between the stored mixture CDF and the raw empirical CDF (bandwidth-free)."""
    o = np.argsort(pci); c = np.cumsum(w[o]); c = c / c[-1]
    emp = np.interp(XG, pci[o], c, left=0, right=1)
    pi = par[:, 0] / par[:, 0].sum()
    mcdf = (pi[:, None] * norm.cdf((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None])).sum(0)
    return float(np.abs(mcdf - emp).max())


def fit_k(draws, K, warm=None):
    kw = dict(n_components=K, random_state=0, max_iter=200, reg_covar=1e-4)
    if warm is not None and len(warm) == K:
        g = GaussianMixture(n_init=1, means_init=warm[:, 1:2],
                            weights_init=warm[:, 0] / warm[:, 0].sum(),
                            precisions_init=(1 / warm[:, 2] ** 2).reshape(K, 1, 1), **kw)
    else:
        g = GaussianMixture(n_init=2, **kw)
    g.fit(draws.reshape(-1, 1))
    par = np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])
    score = g.score(draws.reshape(-1, 1))          # mean log-likelihood per sample
    return par[np.argsort(par[:, 1])], score        # sort components by mean


def choose_k(pci, w, tol=0.005):
    """Pick K (2..KMAX) by fidelity to the raw truth: take the smallest K whose
    KS-to-truth is within `tol` (0.5 pp) of the best achievable. Adding humps that
    don't measurably improve the fit is skipped, so commodity exporters land low and
    broad/bimodal economies land high -- adaptive on real distributional complexity."""
    ks = {}
    for K in range(2, KMAX + 1):
        par, _ = fit_k(draws_of(pci, w), K)
        ks[K] = ks_to_truth(par, pci, w)
    best = min(ks.values())
    for K in range(2, KMAX + 1):
        if ks[K] <= best + tol:
            return K
    return min(ks, key=ks.get)


def main():
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    countries = [str(c) for c in s["countries"]]
    years = [int(y) for y in s["years"]]
    df = gdata.load_clean(years=years)
    df = df[df["pci"].between(cfg.PCI_LO, cfg.PCI_HI)]

    flows = [("export", "export_value"), ("import", "import_value")]
    mix = {fl: {} for fl, _ in flows}
    kmap = {fl: {} for fl, _ in flows}
    kcount, ncell, ncomp, ks_list = [], 0, 0, []

    for fl, col in flows:
        sub = df[df[col] > 0]
        for c in countries:
            cd = sub[sub.country_iso3_code == c]
            by_year = {}
            for yr in years:
                g = cd[cd.year == yr]
                if len(g) >= MIN_PROD:
                    by_year[yr] = (g["pci"].to_numpy(float), g[col].to_numpy(float))
            if len(by_year) < 5:
                continue
            # choose K on the most recent well-populated year, by fidelity to truth
            ref_yr = max(by_year)
            rp, rw = by_year[ref_yr]
            K = choose_k(rp, rw)
            kmap[fl][c] = K
            kcount.append(K)
            # sequential warm-started fits, ascending years
            cell, prev = {}, None
            for yr in sorted(by_year):
                pci, w = by_year[yr]
                par, _ = fit_k(draws_of(pci, w), K, warm=prev)
                prev = par
                rounded = [[round(float(par[k, 0]), 4), round(float(par[k, 1]), 3),
                            round(float(par[k, 2]), 3)] for k in range(K)]
                cell[str(yr)] = rounded
                ncomp += K
                ks_list.append(ks_to_truth(np.array(rounded), pci, w))   # verify stored params
            mix[fl][c] = cell
            ncell += 1

    payload = {
        "flows": [fl for fl, _ in flows],
        "countries": countries,
        "years": years,
        "blur": {"low": 0.05, "med": 0.10, "high": 0.18},  # render-time sigma quadrature (mirrors KDE bws)
        "K": kmap,
        "mix": mix,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gmm.json").write_text(json.dumps(payload))

    import gzip
    raw = (OUT / "gmm.json").stat().st_size
    gz = len(gzip.compress((OUT / "gmm.json").read_bytes(), 6))
    kc = np.array(kcount)
    print(f"cells: {ncell} (flow x country), components total: {ncomp}")
    print(f"K per country-flow: min {kc.min()} median {int(np.median(kc))} max {kc.max()}  "
          f"mean {kc.mean():.1f}")
    hist = {k: int((kc == k).sum()) for k in range(2, KMAX + 1)}
    print(f"K histogram: {hist}")
    ks = np.array(ks_list)
    print(f"KS of stored mixtures vs raw truth: p50 {100*np.median(ks):.2f}%  p95 {100*np.percentile(ks,95):.2f}%"
          f"   (displayed KDE floor ~6.7%)")
    print(f"gmm.json: raw {raw/1e6:.2f} MB   gz {gz/1e6:.2f} MB   (vs density today gz 3.60 MB)")


if __name__ == "__main__":
    main()
