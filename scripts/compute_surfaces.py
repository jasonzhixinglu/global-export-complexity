"""Compute all derived surfaces once and cache them under data/derived/.

Outputs (git-ignored):
  data/derived/surfaces.npz   density / share / coverage / adding-up surfaces
  data/derived/dist_diag.npz  per-country bin-mass: actual histogram vs smooth KDE
  data/derived/meta.json      grids, country order, settings

Downstream scripts (figures, diagnostics) read these so the 431 MB CSV is parsed once.

Usage:  python scripts/compute_surfaces.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg, data as gdata, estimators as est

DERIVED = cfg.DATA_DIR / "derived"


def main() -> None:
    cfg.ensure_dirs()
    DERIVED.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    df = gdata.load_clean()
    RANKED = gdata.ranked_exporters(df)
    TOP = RANKED[:cfg.N_TOP]
    thresholds = cfg.COVER_THRESHOLDS
    print(f"loaded {len(df):,} rows in {time.time()-t0:.0f}s; tracking top {len(TOP)}: {', '.join(TOP)}")

    years = cfg.YEARS
    share_grid = np.linspace(-2.5, 2.5, cfg.SHARE_GRID_N)
    kde_grid = np.linspace(cfg.PCI_LO, cfg.PCI_HI, cfg.KDE_GRID_N)
    edges = np.arange(cfg.PCI_LO, cfg.PCI_HI + 1e-9, cfg.BIN_WIDTH)

    nC, nY = len(TOP), len(years)
    density = np.full((nC, nY, kde_grid.size), np.nan)        # per-country export $ shape
    share_raw = np.full((nC, nY, share_grid.size), np.nan)    # UNCLIPPED shares
    coverage = np.full((len(thresholds), nY, share_grid.size), np.nan)  # cum share per threshold
    addup = np.full((nY, share_grid.size), np.nan)            # all-country share sum (~1)
    totals_cy = np.full((nC, nY), np.nan)                     # total export value per country-year

    # distribution conservation diagnostic for the focus countries at snapshot years
    focus = [c for c in cfg.FOCUS_COUNTRIES if c in TOP]
    diag = {"edges": edges, "focus": np.array(focus), "snap": np.array(cfg.SNAPSHOT_YEARS)}
    hist_mass = np.full((len(focus), len(cfg.SNAPSHOT_YEARS), edges.size + 1), np.nan)
    kde_mass = np.full_like(hist_mass, np.nan)
    totals = np.full((len(focus), len(cfg.SNAPSHOT_YEARS), 2), np.nan)  # (actual, kde_total)

    cidx = {c: i for i, c in enumerate(TOP)}
    for yi, yr in enumerate(years):
        dy = df[df["year"] == yr]
        prod = gdata.product_table(dy)
        pci, W = prod["pci"].to_numpy(), prod["W"].to_numpy()
        cvecs = gdata.country_value_vectors(dy, prod["product_hs92_code"].tolist(), TOP)

        # cumulative coverage value vectors per threshold (single ratio -> bounded)
        pcodes = prod["product_hs92_code"].tolist()
        cov_vecs = {}
        for N in thresholds:
            tv = (dy[dy["country_iso3_code"].isin(RANKED[:N])]
                  .groupby("product_hs92_code")["export_value"].sum())
            cov_vecs[f"_cov{N}_"] = tv.reindex(pd.Index(pcodes)).fillna(0.0).to_numpy()

        # shares (unclipped) + coverage (single ratio) in one local-linear call
        res = est.local_linear_shares(pci, W, {**cvecs, **cov_vecs},
                                      share_grid, cfg.BANDWIDTH, clip=False)
        for c in TOP:
            share_raw[cidx[c], yi] = res[c]
        for ti, N in enumerate(thresholds):
            coverage[ti, yi] = np.clip(res[f"_cov{N}_"], 0, 1)
        addup[yi] = est.adding_up(pci, W, share_grid, cfg.BANDWIDTH)  # C = W -> exactly 1

        # per-country dollar distribution (each country's own products & values)
        for c in TOP:
            dc = dy[dy["country_iso3_code"] == c]
            x, w = dc["pci"].to_numpy(), dc["export_value"].to_numpy()
            density[cidx[c], yi] = est.density_fixed(x, w, kde_grid, cfg.H_DIST)
            totals_cy[cidx[c], yi] = w[np.isfinite(x)].sum()

        # conservation diagnostic at snapshot years
        if yr in cfg.SNAPSHOT_YEARS:
            si = cfg.SNAPSHOT_YEARS.index(yr)
            for fi, c in enumerate(focus):
                dc = dy[dy["country_iso3_code"] == c]
                x, w = dc["pci"].to_numpy(), dc["export_value"].to_numpy()
                tot = w[np.isfinite(x)].sum()
                hist_mass[fi, si] = est.weighted_histogram(x, w, edges)
                kde_mass[fi, si] = est.kde_bin_mass(x, w, edges, cfg.H_DIST)
                totals[fi, si] = [tot, est.kde_bin_mass(x, w, edges, cfg.H_DIST).sum()]
        print(f"  {yr} done", end="\r")

    np.savez_compressed(
        DERIVED / "surfaces.npz",
        density=density, share_raw=share_raw, coverage=coverage, addup=addup,
        totals_cy=totals_cy, share_grid=share_grid, kde_grid=kde_grid,
        years=np.array(years),
        countries=np.array(TOP), cover_thresholds=np.array(thresholds),
    )
    np.savez_compressed(
        DERIVED / "dist_diag.npz",
        hist_mass=hist_mass, kde_mass=kde_mass, totals=totals,
        edges=edges, focus=np.array(focus), snap=np.array(cfg.SNAPSHOT_YEARS),
    )
    meta = {
        "n_top": cfg.N_TOP, "cover_thresholds": thresholds,
        "bandwidth": cfg.BANDWIDTH, "h_dist": cfg.H_DIST,
        "bin_width": cfg.BIN_WIDTH, "years": [years[0], years[-1]],
        "countries": TOP, "focus": focus, "snapshot_years": cfg.SNAPSHOT_YEARS,
        "ranked_21_50": RANKED[20:50],
    }
    (DERIVED / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nwrote surfaces to {DERIVED} in {time.time()-t0:.0f}s total")


if __name__ == "__main__":
    main()
