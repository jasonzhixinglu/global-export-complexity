"""Concrete size of a GMM density store, and the smoothness-by-quadrature point.

A mixture is an estimator of the RAW distribution, so it is fit once per
country x year x flow -- the Low/Med/High smoothness levels are NOT stored;
smoothing a Gaussian mixture by bandwidth b just maps sigma_k -> sqrt(sigma_k^2 + b^2),
an analytic render-time knob.  So the GMM replaces the entire density payload
(2 flows x 3 levels x 50 x 25 grids) with 2 x 50 x 25 = 2500 mixtures.

Run:  python scripts/prototype_gmm_size.py
"""
from __future__ import annotations
import gzip, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

warnings.filterwarnings("ignore")
RNG = np.random.default_rng(0)


def gz(obj):
    return len(gzip.compress(json.dumps(obj).encode(), 6))


def fit_params(pci, w, K):
    p = w / w.sum()
    draws = RNG.choice(pci, size=8000, p=p)
    g = GaussianMixture(K, random_state=0, n_init=1, max_iter=120).fit(draws.reshape(-1, 1))
    mu = g.means_.ravel(); sd = np.sqrt(g.covariances_.ravel()); pi = g.weights_
    # one component = [weight, mean, sigma]; round modestly
    return [[round(float(pi[k]), 4), round(float(mu[k]), 3), round(float(sd[k]), 3)] for k in range(K)]


def main():
    df = pd.read_csv(cfg.RAW_CSV,
                     usecols=["country_iso3_code", "year", "export_value", "import_value", "pci"],
                     dtype={"country_iso3_code": str}).dropna(subset=["pci"])
    df = df[df["pci"].between(-3, 3)]
    top = df.groupby("country_iso3_code")["export_value"].sum().nlargest(50).index
    df = df[df["country_iso3_code"].isin(top)]
    years = sorted(df["year"].unique())
    print(f"universe: 50 countries x {len(years)} years x 2 flows = {50*len(years)*2} mixtures")

    # sample cells to measure per-cell byte cost, then extrapolate to the full 2500
    cells = [(c, yr, fl) for c in top for yr in years for fl in ("export_value", "import_value")]
    samp = [cells[i] for i in RNG.choice(len(cells), 500, replace=False)]
    n_total = len(cells)

    for K in (4, 5):
        params = []
        for c, yr, fl in samp:
            g = df[(df.country_iso3_code == c) & (df.year == yr)]
            w = g[fl].to_numpy(float); pci = g["pci"].to_numpy(float)
            m = w > 0
            if m.sum() < 10:
                continue
            params.append(fit_params(pci[m], w[m], K))
        arr = {"gmm": params}
        raw = len(json.dumps(arr).encode()); g = gz(arr)
        per_raw, per_gz = raw / len(params), g / len(params)
        full_raw = per_raw * n_total / 1e6
        full_gz = per_gz * n_total / 1e6
        print(f"\nGMM K={K} ({3*K} floats/mixture):")
        print(f"  sample {len(params)} mixtures: raw {raw/1024:.0f} KB  gz {g/1024:.0f} KB")
        print(f"  full {n_total} mixtures (est): raw {full_raw:.2f} MB  gz {full_gz:.2f} MB")

    print("\nbaseline density (current, 2 flows x 3 levels x 150-pt grid): raw 10.70 MB  gz 3.60 MB")
    print("note: GMM has NO level dimension - smoothness is sigma_k -> sqrt(sigma_k^2 + b^2) at render time.")


if __name__ == "__main__":
    main()
