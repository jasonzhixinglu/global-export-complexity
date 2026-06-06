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
    RANKED_EXP = gdata.ranked_exporters(df)
    TOP = RANKED_EXP[:cfg.N_TOP]   # tracked per-country set = top exporters (both flows shown)
    imp_tot = df.groupby("country_iso3_code")["import_value"].sum().drop(
        index=[c for c in ("ANS",) if c in df["country_iso3_code"].unique()], errors="ignore")
    RANKED_IMP = imp_tot.sort_values(ascending=False).index.tolist()
    RANKED = {"export": RANKED_EXP, "import": RANKED_IMP}
    thresholds = cfg.COVER_THRESHOLDS
    FLOWS = [("export", "export_value", "W"), ("import", "import_value", "W_imp")]
    print(f"loaded {len(df):,} rows in {time.time()-t0:.0f}s; tracking top {len(TOP)}: {', '.join(TOP)}")

    years = cfg.YEARS
    share_grid = np.linspace(-2.5, 2.5, cfg.SHARE_GRID_N)
    kde_grid = np.linspace(cfg.PCI_LO, cfg.PCI_HI, cfg.KDE_GRID_N)
    edges = np.arange(cfg.PCI_LO, cfg.PCI_HI + 1e-9, cfg.BIN_WIDTH)

    LEVELS = cfg.SMOOTHING
    nL = len(LEVELS)
    nF = len(FLOWS)
    med_idx = next(i for i, lv in enumerate(LEVELS) if lv["id"] == "med")

    nC, nY = len(TOP), len(years)
    # flow x level x country x year x grid  (flow 0 = export, 1 = import)
    density_lvl = np.full((nF, nL, nC, nY, kde_grid.size), np.nan)
    share_lvl = np.full((nF, nL, nC, nY, share_grid.size), np.nan)
    coverage = np.full((nF, len(thresholds), nY, share_grid.size), np.nan)
    addup = np.full((nF, nY, share_grid.size), np.nan)
    totals_cy = np.full((nF, nC, nY), np.nan)

    # distribution conservation diagnostic (export only) for focus countries at snapshot years
    focus = [c for c in cfg.FOCUS_COUNTRIES if c in TOP]
    hist_mass = np.full((len(focus), len(cfg.SNAPSHOT_YEARS), edges.size + 1), np.nan)
    kde_mass = np.full_like(hist_mass, np.nan)
    totals = np.full((len(focus), len(cfg.SNAPSHOT_YEARS), 2), np.nan)  # (actual, kde_total)

    cidx = {c: i for i, c in enumerate(TOP)}
    for yi, yr in enumerate(years):
        dy = df[df["year"] == yr]
        prod = gdata.product_table(dy)
        pci = prod["pci"].to_numpy()
        pcodes = prod["product_hs92_code"].tolist()
        idx = pd.Index(pcodes)

        for fi, (flow, vcol, wcol) in enumerate(FLOWS):
            W = prod[wcol].to_numpy()
            cvecs = gdata.country_value_vectors(dy, pcodes, TOP, value_col=vcol)
            # cumulative coverage value vectors per threshold (flow-specific top-N ranking)
            cov_vecs = {}
            for N in thresholds:
                tv = (dy[dy["country_iso3_code"].isin(RANKED[flow][:N])]
                      .groupby("product_hs92_code")[vcol].sum())
                cov_vecs[f"_cov{N}_"] = tv.reindex(idx).fillna(0.0).to_numpy()
            covres = est.local_linear_shares(pci, W, cov_vecs, share_grid, cfg.BANDWIDTH, clip=False)
            for ti, N in enumerate(thresholds):
                coverage[fi, ti, yi] = np.clip(covres[f"_cov{N}_"], 0, 1)
            addup[fi, yi] = est.adding_up(pci, W, share_grid, cfg.BANDWIDTH)
            for li, lv in enumerate(LEVELS):
                sres = est.local_linear_shares(pci, W, cvecs, share_grid, lv["bw"], clip=False)
                for c in TOP:
                    share_lvl[fi, li, cidx[c], yi] = sres[c]

        # per-country distributions (both flows from one filter per country)
        for c in TOP:
            dc = dy[dy["country_iso3_code"] == c]
            x = dc["pci"].to_numpy()
            for fi, (flow, vcol, wcol) in enumerate(FLOWS):
                w = dc[vcol].to_numpy()
                totals_cy[fi, cidx[c], yi] = w.sum()
                for li, lv in enumerate(LEVELS):
                    density_lvl[fi, li, cidx[c], yi] = est.density_fixed(x, w, kde_grid, lv["bw"])

        # conservation diagnostic (export) at snapshot years
        if yr in cfg.SNAPSHOT_YEARS:
            si = cfg.SNAPSHOT_YEARS.index(yr)
            for fj, c in enumerate(focus):
                dc = dy[dy["country_iso3_code"] == c]
                x, w = dc["pci"].to_numpy(), dc["export_value"].to_numpy()
                hist_mass[fj, si] = est.weighted_histogram(x, w, edges)
                kde_mass[fj, si] = est.kde_bin_mass(x, w, edges, cfg.H_DIST)
                totals[fj, si] = [w.sum(), est.kde_bin_mass(x, w, edges, cfg.H_DIST).sum()]
        print(f"  {yr} done", end="\r")

    EX = 0  # export flow index, for canonical figure arrays
    np.savez_compressed(
        DERIVED / "surfaces.npz",
        # canonical export (Medium) arrays for figures/diagnostics (unchanged shapes)
        density=density_lvl[EX, med_idx], share_raw=share_lvl[EX, med_idx],
        coverage=coverage[EX], addup=addup[EX], totals_cy=totals_cy[EX],
        # flow x level x ... arrays for the dashboard
        density_lvl=density_lvl, share_lvl=share_lvl,
        coverage_flow=coverage, totals_cy_flow=totals_cy,
        flows=np.array([f[0] for f in FLOWS]),
        smoothing_id=np.array([lv["id"] for lv in LEVELS]),
        smoothing_bw=np.array([lv["bw"] for lv in LEVELS]),
        share_grid=share_grid, kde_grid=kde_grid, years=np.array(years),
        countries=np.array(TOP), cover_thresholds=np.array(thresholds),
        ranked_imp=np.array(RANKED_IMP[:cfg.N_TOP]),
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
