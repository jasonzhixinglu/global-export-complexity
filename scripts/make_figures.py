"""Render the analysis figures from cached surfaces into results/figures/.

Usage:  python scripts/make_figures.py   (run compute_surfaces.py first)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import plotting as P
import matplotlib.pyplot as plt

DERIVED = cfg.DATA_DIR / "derived"


def load():
    return np.load(DERIVED / "surfaces.npz", allow_pickle=True)


def fig_density_lines(d):
    """Reproduction of the legacy notebook's 'export complexity density' chart:
    per-country normalized density, snapshot years overlaid (line plot)."""
    countries = list(d["countries"]); years = list(d["years"]); g = d["kde_grid"]
    focus = [c for c in cfg.LEGACY_COUNTRIES if c in countries]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, c in zip(axes.ravel(), focus):
        for yr in cfg.REPRO_YEARS:
            ax.plot(g, d["density"][countries.index(c), years.index(yr)], lw=2, label=str(yr))
        ax.set_title(c); ax.set_xlabel("PCI"); ax.set_ylabel("density (share of export value)")
        ax.legend(fontsize=8)
    fig.suptitle("Density of export value across complexity (normalized) — reproduction", y=1.01)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "repro_density_lines.png")


def fig_value_lines(d):
    """Reproduction of the legacy notebook's 'export value by complexity' chart:
    normalized density scaled to nominal dollars (area under curve = total exports)."""
    countries = list(d["countries"]); years = list(d["years"]); g = d["kde_grid"]
    focus = [c for c in cfg.LEGACY_COUNTRIES if c in countries]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, c in zip(axes.ravel(), focus):
        for yr in cfg.REPRO_YEARS:
            ci, yidx = countries.index(c), years.index(yr)
            curve = d["density"][ci, yidx] * d["totals_cy"][ci, yidx] / 1e9  # $B
            ax.plot(g, curve, lw=2, label=str(yr))
        ax.set_title(c); ax.set_xlabel("PCI"); ax.set_ylabel("export value density ($B per PCI)")
        ax.legend(fontsize=8)
    fig.suptitle("Distribution of export value by complexity (nominal $) — reproduction\n"
                 "area under each curve = that year's total exports", y=1.02)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "repro_value_lines.png")


def fig_density(d):
    countries = list(d["countries"]); years = d["years"]; g = d["kde_grid"]
    fig, axes = P.small_multiples(countries, ncol=5)
    for ax, c in zip(axes, countries):
        surf = d["density"][countries.index(c)]
        vmax = np.nanmax(surf) if np.isfinite(surf).any() else 1.0
        P.heatmap_panel(ax, surf, g, years, cmap="magma", vmax=vmax)
        ax.set_title(c); ax.grid(False)
    for ax in axes[len(countries):]:
        ax.axis("off")
    fig.suptitle("Distribution of export value across complexity (per-country, normalized)\n"
                 "x = PCI · y = year (2000-2024) · brighter = more export $ at that complexity",
                 y=1.02)
    fig.supxlabel("PCI")
    return P.save(fig, cfg.FIG_DIR / "density_heatmap.png")


def fig_market_share(d):
    countries = list(d["countries"]); years = d["years"]; g = d["share_grid"]
    surf_all = np.clip(d["share_raw"], 0, 1)  # clip for display only
    vmax = np.nanpercentile(surf_all, 99)
    fig, axes = P.small_multiples(countries, ncol=5)
    im = None
    for ax, c in zip(axes, countries):
        im = P.heatmap_panel(ax, surf_all[countries.index(c)], g, years, cmap="viridis", vmax=vmax)
        ax.set_title(c); ax.grid(False)
    for ax in axes[len(countries):]:
        ax.axis("off")
    fig.suptitle(f"Global market share by product complexity, 2000-2024 "
                 f"(shared scale, 99th pct = {vmax:.2f})\n"
                 "x = PCI · y = year · color = share of world exports at that complexity", y=1.02)
    fig.supxlabel("PCI")
    fig.colorbar(im, ax=axes.tolist(), shrink=0.5, label="global market share")
    return P.save(fig, cfg.FIG_DIR / "market_share_heatmap.png")


def fig_snapshots(d):
    countries = list(d["countries"]); years = list(d["years"]); g = d["share_grid"]
    focus = [c for c in cfg.FOCUS_COUNTRIES if c in countries]
    surf = np.clip(d["share_raw"], 0, 1)
    fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=True)
    for ax, c in zip(axes.ravel(), focus):
        for yr in [2000, 2012, 2024]:
            ax.plot(g, surf[countries.index(c), years.index(yr)], lw=2, label=str(yr))
        ax.set_title(c); ax.set_xlabel("PCI"); ax.set_ylabel("global market share")
        ax.legend(fontsize=8)
    fig.suptitle("Global market share vs. complexity — snapshot years (local-linear)", y=1.02)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "market_share_snapshots.png")


def fig_stacked_share(d):
    """Cumulative (stacked) global market share of CHN/JPN/DEU by complexity, one
    panel per snapshot year. Top of the stack = the three countries' combined share."""
    countries = list(d["countries"]); years = list(d["years"]); g = d["share_grid"]
    stack = [c for c in cfg.STACK_COUNTRIES if c in countries]
    surf = np.clip(d["share_raw"], 0, 1)  # display clip
    colors = {"CHN": "#d62728", "JPN": "#1f77b4", "DEU": "#2ca02c",
              "KOR": "#9467bd", "USA": "#ff7f0e"}
    yrs = cfg.REPRO_YEARS
    ymax = max(np.nansum([surf[countries.index(c), years.index(yr)] for c in stack], axis=0).max()
               for yr in yrs)
    fig, axes = plt.subplots(1, len(yrs), figsize=(5 * len(yrs), 4.6), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, yr in zip(axes, yrs):
        bands = [surf[countries.index(c), years.index(yr)] for c in stack]
        ax.stackplot(g, *bands, labels=stack, colors=[colors.get(c) for c in stack], alpha=0.85)
        ax.plot(g, np.sum(bands, axis=0), color="k", lw=1.2)  # cumulative total outline
        ax.set_title(str(yr)); ax.set_xlabel("PCI"); ax.set_ylim(0, ymax * 1.05)
    axes[0].set_ylabel("cumulative global market share")
    axes[-1].legend(loc="upper left", fontsize=9, title="stacked")
    fig.suptitle(f"Cumulative global market share by complexity: {' + '.join(stack)}\n"
                 "stacked bands = each country's share · black line = combined total", y=1.03)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "stacked_share_by_complexity.png")


def fig_coverage(d):
    years = list(d["years"]); g = d["share_grid"]
    cov = d["coverage"]; thr = list(d["cover_thresholds"])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    # Left: does adding countries help? thresholds in the latest year.
    yi = years.index(2024)
    for ti, N in enumerate(thr):
        ax1.plot(g, cov[ti, yi], lw=2, label=f"top {N}")
    ax1.axhline(0.90, ls="--", color="k", alpha=0.6, label="90% reference")
    ax1.set_title("Coverage by number of countries (2024)")
    ax1.set_xlabel("PCI"); ax1.set_ylabel("cumulative share of world exports")
    ax1.set_ylim(0, 1.05); ax1.legend(fontsize=9)

    # Right: largest threshold over time.
    Nmax = thr[-1]; ti = len(thr) - 1
    for yr in cfg.SNAPSHOT_YEARS:
        ax2.plot(g, cov[ti, years.index(yr)], lw=2, label=str(yr))
    ax2.axhline(0.90, ls="--", color="k", alpha=0.6)
    ax2.set_title(f"Top {Nmax} coverage over time")
    ax2.set_xlabel("PCI"); ax2.legend(title="year", fontsize=8)
    fig.suptitle("World-export coverage of the top exporters, by complexity", y=1.02)
    fig.tight_layout()
    return P.save(fig, cfg.FIG_DIR / "coverage_by_complexity.png")


def main():
    cfg.ensure_dirs()
    d = load()
    for f in (fig_density_lines, fig_value_lines, fig_density,
              fig_market_share, fig_snapshots, fig_stacked_share, fig_coverage):
        print("wrote", f(d))


if __name__ == "__main__":
    main()
