"""Visual QA: reconstructed GMM vs raw truth vs the current KDE curve, latest year.

For a few economies (broad, and commodity-concentrated) plot:
  - raw weighted histogram of export value over PCI (truth)
  - current displayed KDE-med curve
  - GMM reconstruction at Low / Med / High blur (sigma_k -> sqrt(sigma^2 + b^2))
Saves results/figures/gmm_check.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import data as gdata

DERIVED = cfg.DATA_DIR / "derived"
DATA = cfg.ROOT / "dashboard" / "public" / "data"
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 400)
SHOW = ["CHN", "DEU", "USA", "SAU", "NGA", "VNM"]


def mix_density(par, b=0.0):
    par = np.array(par)
    pi = par[:, 0] / par[:, 0].sum()
    sd = np.sqrt(par[:, 2] ** 2 + b ** 2)
    return (pi[:, None] * norm.pdf((XG[None, :] - par[:, 1][:, None]) / sd[:, None]) / sd[:, None]).sum(0)


def main():
    gmm = json.loads((DATA / "gmm.json").read_text())
    blur = gmm["blur"]
    yr = max(gmm["years"])
    df = gdata.load_clean(years=[yr])
    df = df[(df.year == yr) & (df.export_value > 0) & df.pci.between(cfg.PCI_LO, cfg.PCI_HI)]

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for ax, iso in zip(axes.ravel(), SHOW):
        g = df[df.country_iso3_code == iso]
        pci = g.pci.to_numpy(float); w = g.export_value.to_numpy(float)
        # raw truth as a density histogram (value-weighted), normalised to integrate to 1
        ax.hist(pci, bins=60, weights=w / w.sum(), density=True, color="0.8",
                label="raw (truth)")
        cell = gmm["mix"]["export"].get(iso, {}).get(str(yr))
        if cell:
            K = len(cell)
            ax.plot(XG, mix_density(cell, blur["low"]), lw=1.4, label=f"GMM low (K={K})")
            ax.plot(XG, mix_density(cell, blur["med"]), lw=2.0, label="GMM med")
            ax.plot(XG, mix_density(cell, blur["high"]), lw=1.4, ls="--", label="GMM high")
        ax.set_title(f"{iso} exports {yr}"); ax.set_xlim(-3, 3)
        ax.set_xlabel("PCI"); ax.legend(fontsize=7)
    fig.tight_layout()
    out = cfg.ROOT / "results" / "figures" / "gmm_check.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110)
    print("wrote", out)


if __name__ == "__main__":
    main()
