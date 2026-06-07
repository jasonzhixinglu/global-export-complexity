"""Show WHERE the bilateral GMM fit is bad: raw histogram vs fitted mixture.

Loads top-30 x top-30 corridors (2022), fits an adaptive Gaussian mixture to each,
and plots the worst-KS corridors (plus one good one for contrast): value-weighted
histogram of the corridor's export distribution over PCI, with the fitted mixture and
the true KDE overlaid.  Saves results/figures/bilateral_badfit.png.
"""
from __future__ import annotations
import sys, warnings
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
YEAR = 2022; N = 30
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 500)


def fit(pci, w, K):
    p = w / w.sum(); n = min(3000, max(400, 8 * len(pci)))
    d = RNG.choice(pci, n, p=p)
    g = GaussianMixture(K, random_state=0, n_init=1, max_iter=150, reg_covar=1e-4).fit(d.reshape(-1, 1))
    return np.column_stack([g.weights_, g.means_.ravel(), np.sqrt(g.covariances_.ravel())])


def dens(par, x):
    pi = par[:, 0] / par[:, 0].sum()
    return (pi[:, None] * norm.pdf((x[None, :] - par[:, 1][:, None]) / par[:, 2][:, None]) / par[:, 2][:, None]).sum(0)


def kde(pci, w, x, h=0.10):
    w = w / w.sum()
    return (w[None, :] * norm.pdf((x[:, None] - pci[None, :]) / h) / h).sum(1)


def ks(par, pci, w):
    o = np.argsort(pci); c = np.cumsum(w[o]); c = c / c[-1]
    emp = np.interp(XG, pci[o], c, left=0, right=1)
    pi = par[:, 0] / par[:, 0].sum()
    mcdf = (pi[:, None] * norm.cdf((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None])).sum(0)
    return float(np.abs(mcdf - emp).max())


def main():
    print("loading ...", flush=True)
    base = gdata.load_clean(years=[YEAR]); base = base[base.year == YEAR]
    top = base.groupby("country_iso3_code")["export_value"].sum().drop(
        index=[c for c in ("ANS",) if c in base.country_iso3_code.values], errors="ignore").nlargest(N).index.tolist()
    pci_map = base.assign(p4=base.product_hs92_code.str.zfill(4)).groupby("p4")["pci"].first()
    bl = gdata.load_bilateral(year_ranges=("2020_2024",), origins=top, dests=top, years=[YEAR], hs_level=4)
    bl["p4"] = bl.product_hs92_code.str.zfill(4); bl["pci"] = bl.p4.map(pci_map)
    bl = bl.dropna(subset=["pci"]); bl = bl[bl.pci.between(cfg.PCI_LO, cfg.PCI_HI) & (bl.export_value > 0)]

    recs = []
    for (o, d), g in bl.groupby(["country_iso3_code", "partner_iso3_code"]):
        if o == d or len(g) < 8:
            continue
        pci = g.pci.to_numpy(float); w = g.export_value.to_numpy(float)
        best = min(((ks(fit(pci, w, K), pci, w), K) for K in (3, 5, 8)))
        recs.append({"o": o, "d": d, "n": len(g), "ks": best[0], "K": best[1], "pci": pci, "w": w})
    recs.sort(key=lambda r: -r["ks"])

    # 5 worst + 1 good (lowest-KS rich corridor) for contrast
    good = min((r for r in recs if r["n"] > 600), key=lambda r: r["ks"])
    picks = recs[:5] + [good]
    fig, axes = plt.subplots(2, 3, figsize=(16, 8.5))
    for ax, r in zip(axes.ravel(), picks):
        par = fit(r["pci"], r["w"], r["K"])
        ax.hist(r["pci"], bins=50, weights=r["w"] / r["w"].sum(), density=True, color="0.8", label="raw (truth)")
        ax.plot(XG, dens(par, XG), lw=2.2, color="#e4572e", label=f"GMM K={r['K']}")
        ax.plot(XG, kde(r["pci"], r["w"], XG), lw=1.4, ls="--", color="#1f77b4", label="true KDE")
        ax.set_title(f"{r['o']}->{r['d']}  {YEAR}   n={r['n']} products,  KS={100*r['ks']:.0f}%")
        ax.set_xlim(-3, 3); ax.set_xlabel("PCI"); ax.legend(fontsize=8)
    fig.suptitle("Bilateral corridor distributions: worst GMM fits (+ one good, bottom-right)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = cfg.ROOT / "results" / "figures" / "bilateral_badfit.png"
    fig.savefig(out, dpi=110); print("wrote", out)
    print("\nplotted corridors:")
    for r in picks:
        print(f"  {r['o']}->{r['d']}  n={r['n']}  KS={100*r['ks']:.0f}%  K={r['K']}")


if __name__ == "__main__":
    main()
