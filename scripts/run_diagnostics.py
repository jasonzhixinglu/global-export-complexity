"""Conservation & adding-up diagnostics: figures + a summary table.

Verifies the two accounting properties from docs/pci-analysis.md §3:
  1. Shares add up to exactly 1 across all countries (self-calibration).
  2. Dollar mass is conserved exactly in total; sub-range error is mean-zero
     redistribution, quantified against the exact weighted histogram.

Usage:  python scripts/run_diagnostics.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import plotting as P
import matplotlib.pyplot as plt

DERIVED = cfg.DATA_DIR / "derived"


def fig_adding_up(s):
    years = list(s["years"]); g = s["share_grid"]; addup = s["addup"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for yr in cfg.SNAPSHOT_YEARS:
        ax.plot(g, addup[years.index(yr)], lw=1.5, label=str(yr))
    ax.axhline(1.0, ls="--", color="k", alpha=0.5)
    ax.set_ylim(0.9, 1.1)
    ax.set_xlabel("PCI"); ax.set_ylabel("sum of all-country shares")
    md = np.nanmax(np.abs(addup - 1.0))
    ax.set_title(f"Adding-up: sum of estimated shares over ALL countries "
                 f"(max deviation from 1 = {md:.1e})")
    ax.legend(title="year", fontsize=8)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "adding_up.png")


def fig_conservation(dg):
    edges = dg["edges"]; focus = list(dg["focus"]); snap = list(dg["snap"])
    centers = 0.5 * (edges[:-1] + edges[1:])
    c, yr = "CHN", 2024
    fi, si = focus.index(c), snap.index(yr)
    hist = dg["hist_mass"][fi, si][1:-1] / 1e9      # drop tail bins for the plot
    kde = dg["kde_mass"][fi, si][1:-1] / 1e9
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 1]})
    ax1.bar(centers, hist, width=cfg.BIN_WIDTH * 0.9, alpha=0.45,
            label="exact histogram (ground truth)")
    ax1.plot(centers, kde, "o-", color="crimson", ms=3, lw=1.5,
             label=f"smooth KDE bin mass (h={cfg.H_DIST})")
    ax1.set_ylabel("export value ($B)")
    ax1.set_title(f"{c} {yr}: dollar mass per PCI bin — smooth estimate vs exact histogram")
    ax1.legend()
    ax2.bar(centers, kde - hist, width=cfg.BIN_WIDTH * 0.9, color="gray")
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_ylabel("resid ($B)"); ax2.set_xlabel("PCI")
    ax2.set_title("KDE − histogram  (mean-zero redistribution, not net bias)")
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "mass_conservation_CHN.png")


def table_summary(dg):
    focus = list(dg["focus"]); snap = list(dg["snap"])
    rows = []
    for fi, c in enumerate(focus):
        for si, yr in enumerate(snap):
            actual, kdetot = dg["totals"][fi, si]
            resid = dg["kde_mass"][fi, si] - dg["hist_mass"][fi, si]
            rows.append({
                "country": c, "year": int(yr),
                "total_exports_$B": round(actual / 1e9, 1),
                "total_rel_err": f"{(kdetot - actual) / actual:+.1e}" if actual else "nan",
                "net_bias_$": f"{np.nansum(resid):+.2e}",
                "mean_abs_bin_resid_$B": round(np.nanmean(np.abs(resid)) / 1e9, 2),
                "mean_abs_resid_pct_of_total": round(
                    100 * np.nanmean(np.abs(resid)) / actual, 2) if actual else np.nan,
            })
    df = pd.DataFrame(rows)
    out = cfg.TABLE_DIR / "conservation_summary.csv"
    df.to_csv(out, index=False)
    return out, df


def table_coverage(s):
    g = s["share_grid"]; cov = s["coverage"]; thr = list(s["cover_thresholds"])
    df = pd.DataFrame({"pci": g})
    for ti, N in enumerate(thr):
        df[f"coverage_top{N}_mean"] = np.nanmean(cov[ti], 0)  # mean across years
    out = cfg.TABLE_DIR / "coverage_by_pci.csv"
    df.round(4).to_csv(out, index=False)
    return out


def main():
    cfg.ensure_dirs()
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    dg = np.load(DERIVED / "dist_diag.npz", allow_pickle=True)
    print("wrote", fig_adding_up(s))
    print("wrote", fig_conservation(dg))
    out, df = table_summary(dg)
    print("wrote", out)
    print(df.to_string(index=False))
    print("wrote", table_coverage(s))


if __name__ == "__main__":
    main()
