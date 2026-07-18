"""Constant-loading matrix factor models on bilateral AI-compute trade flows, 2020-2024.

Model (Chen, Chen, Bolivar & Chen 2024, docs/references/, without time variation):
    Y_t = R F_t C' + E_t,  Y_t (p x p) = log1p bilateral export matrix, t = 2020..2024.
Estimation: R = sqrt(p) * top-k eigenvectors of M_R = sum_t Y_t Y_t';  C likewise from
sum_t Y_t' Y_t;  F_t = R' Y_t C / (p*q).  Ranks by eigenvalue ratio (Ahn-Horenstein).
Rotation fixed by varimax on each side (one global rotation; loadings are constant here),
signs set so each hub's dominant loading is positive, hubs ordered by loading mass.

Runs one analysis per Fed AI-compute HS6 code (847150 AI servers, 847180 other ADP
units, 847330 parts/GPU cards) plus their sum ("ai_compute"). Outputs one subdirectory
per analysis under results/mfm/ so experiments don't clutter the main results tree.
Run after scripts/extract_ai_compute.py.  Usage: python scripts/prototype_mfm.py [label ...]
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

ANALYSES = {
    "847150": ["847150"],
    "847180": ["847180"],
    "847330": ["847330"],
    "ai_compute": ["847150", "847180", "847330"],
}
TITLES = {
    "847150": "HS 847150 (ADP processing units / AI servers)",
    "847180": "HS 847180 (other ADP units / baseboards)",
    "847330": "HS 847330 (ADP parts / GPU cards)",
    "ai_compute": "AI compute (847150+847180+847330)",
}
YEARS = [2020, 2021, 2022, 2023, 2024]
N_COUNTRIES = 40          # top countries by total (export+import) involvement
KMAX = 8                  # max rank considered by the eigenvalue-ratio estimator
EXCLUDE = {"WLD", "ANS"}  # world / areas-not-specified pseudo-codes
PARQUET = cfg.DATA_DIR / "derived" / "bilateral_ai_compute_2020_2024.parquet"

# dataviz reference palette (light mode)
SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "sans-serif", "font.size": 10,
})


def load_matrices(codes):
    df = pd.read_parquet(PARQUET)
    df = df[df.code.isin(codes)]
    df = df[(df.export_value > 0) & ~df.exporter.isin(EXCLUDE) & ~df.importer.isin(EXCLUDE)]
    df = df.groupby(["exporter", "importer", "year"], as_index=False).export_value.sum()
    world_total = df.export_value.sum()
    involvement = (df.groupby("exporter").export_value.sum()
                   .add(df.groupby("importer").export_value.sum(), fill_value=0.0))
    countries = involvement.sort_values(ascending=False).head(N_COUNTRIES).index.tolist()
    sub = df[df.exporter.isin(countries) & df.importer.isin(countries)]
    coverage = sub.export_value.sum() / world_total
    idx = {c: i for i, c in enumerate(countries)}
    p = len(countries)
    Y = np.zeros((len(YEARS), p, p))
    for t, yr in enumerate(YEARS):
        d = sub[sub.year == yr]
        Y[t, d.exporter.map(idx), d.importer.map(idx)] = np.log1p(d.export_value / 1e6)
    top = {
        "exporters_usd_bn": (df.groupby("exporter").export_value.sum()
                             .nlargest(10) / 1e9).round(2).to_dict(),
        "importers_usd_bn": (df.groupby("importer").export_value.sum()
                             .nlargest(10) / 1e9).round(2).to_dict(),
    }
    return Y, countries, coverage, world_total, top


def eig_ratio(M, kmax=KMAX):
    vals, vecs = np.linalg.eigh(M)
    vals, vecs = vals[::-1], vecs[:, ::-1]
    ratios = vals[:kmax] / vals[1:kmax + 1]
    return vals, vecs, ratios, int(np.argmax(ratios)) + 1


def varimax(L, iters=200, tol=1e-8):
    p, k = L.shape
    O = np.eye(k)
    var = 0.0
    for _ in range(iters):
        B = L @ O
        U, s, Vt = np.linalg.svd(L.T @ (B**3 - B @ np.diag((B**2).sum(0)) / p))
        O = U @ Vt
        if s.sum() < var * (1 + tol):
            break
        var = s.sum()
    return O


def fix_signs_order(L):
    """Sign: dominant loading positive. Order: by column loading mass (descending)."""
    signs = np.sign(L[np.abs(L).argmax(0), np.arange(L.shape[1])])
    L = L * signs
    order = np.argsort(-(L**2).sum(0))
    return L[:, order], signs, order


def run(label):
    codes = ANALYSES[label]
    title = TITLES[label]
    out_dir = cfg.RESULTS_DIR / "mfm" / f"{label}_annual_{YEARS[0]}_{YEARS[-1]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {title} ===")

    Y, countries, coverage, world_total, top = load_matrices(codes)
    T, p, q = Y.shape
    print(f"{T} years {YEARS[0]}-{YEARS[-1]}, {p} countries, "
          f"coverage {coverage:.1%} of ${world_total/1e9:.0f}B world trade")

    M_R = sum(Y[t] @ Y[t].T for t in range(T)) / (T * q)
    M_C = sum(Y[t].T @ Y[t] for t in range(T)) / (T * p)
    vals_R, vecs_R, ratios_R, k_sel = eig_ratio(M_R)
    vals_C, vecs_C, ratios_C, r_sel = eig_ratio(M_C)
    print(f"rank selection (eigenvalue ratio): k={k_sel} (export), r={r_sel} (import)")
    print(f"  row eigenvalue ratios : {np.round(ratios_R, 2)}")
    print(f"  col eigenvalue ratios : {np.round(ratios_C, 2)}")
    # The ratio estimator picks the dominant size/gravity factor alone (k=1), which makes
    # F_t a scalar -- no hub structure. Use the second-best ratio peak as the working rank
    # for hub analysis, reporting both.
    k = int(np.argmax(ratios_R[1:])) + 2
    r = int(np.argmax(ratios_C[1:])) + 2
    print(f"working rank for hub analysis (2nd ratio peak): k={k}, r={r}")

    R = np.sqrt(p) * vecs_R[:, :k]
    C = np.sqrt(q) * vecs_C[:, :r]

    # varimax + sign/order conventions on each side; transform F accordingly
    R, C = R @ varimax(R), C @ varimax(C)
    R, _, _ = fix_signs_order(R)
    C, _, _ = fix_signs_order(C)
    F = np.array([R.T @ Y[t] @ C / (p * q) for t in range(T)])

    S = np.einsum("ik,tkr,jr->tij", R, F, C)
    r2_total = 1 - ((Y - S)**2).sum() / (Y**2).sum()
    r2_year = 1 - ((Y - S)**2).sum((1, 2)) / (Y**2).sum((1, 2))
    R1, C1 = np.sqrt(p) * vecs_R[:, :1], np.sqrt(q) * vecs_C[:, :1]
    S1 = np.einsum("ik,tkr,jr->tij", R1,
                   np.array([R1.T @ Y[t] @ C1 / (p * q) for t in range(T)]), C1)
    r2_rank1 = 1 - ((Y - S1)**2).sum() / (Y**2).sum()
    print(f"fit: uncentered R^2 total {r2_total:.3f} (rank-1 baseline {r2_rank1:.3f}), by year "
          f"{dict(zip(YEARS, np.round(r2_year, 3)))}")

    # Hub sizes. Column norms of R and C are fixed by the R'R = pI normalization, so hub
    # scale lives in F alone; with orthonormal loadings the fitted signal decomposes exactly
    # by hub pair, share of cell (i,j) = mean_t F_t[i,j]^2.
    F2 = (F**2).mean(0)
    hub_pair_share = F2 / F2.sum()
    exp_hub_share, imp_hub_share = hub_pair_share.sum(1), hub_pair_share.sum(0)
    print(f"\ntop exporters 2020-24 ($B): "
          + ", ".join(f"{c} {v:.1f}" for c, v in top["exporters_usd_bn"].items()))
    print(f"top importers 2020-24 ($B): "
          + ", ".join(f"{c} {v:.1f}" for c, v in top["importers_usd_bn"].items()))
    print("hub size (share of fitted signal, log space):")
    print(f"  export hubs: {np.round(exp_hub_share, 3)}")
    print(f"  import hubs: {np.round(imp_hub_share, 3)}")
    print(f"  by hub pair (rows=export hub, cols=import hub):\n{np.round(hub_pair_share, 3)}")

    stats = {
        "label": label, "codes": codes, "years": YEARS, "countries": countries,
        "coverage": float(coverage), "top10": top,
        "hub_size_signal_share": {"export": exp_hub_share.tolist(),
                                  "import": imp_hub_share.tolist(),
                                  "by_pair": hub_pair_share.tolist()},
        "world_total_usd": float(world_total), "k_selected": k_sel, "r_selected": r_sel,
        "k": k, "r": r,
        "eigvals_row": vals_R[:KMAX + 1].tolist(), "eigvals_col": vals_C[:KMAX + 1].tolist(),
        "eig_ratios_row": ratios_R.tolist(), "eig_ratios_col": ratios_C.tolist(),
        "r2_total": float(r2_total), "r2_rank1": float(r2_rank1),
        "r2_by_year": dict(zip(map(str, YEARS), r2_year.tolist())),
        "R": {c: R[i].tolist() for i, c in enumerate(countries)},
        "C": {c: C[i].tolist() for i, c in enumerate(countries)},
        "F_by_year": {str(yr): F[t].tolist() for t, yr in enumerate(YEARS)},
    }
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=1))

    for side, L in (("export", R), ("import", C)):
        print(f"\n{side} hubs (varimax loadings, top 8 per hub):")
        for j in range(L.shape[1]):
            lead = np.argsort(-np.abs(L[:, j]))[:8]
            print(f"  hub {j+1}: " + ", ".join(f"{countries[i]} {L[i, j]:+.2f}" for i in lead))

    fig_summary(top, hub_pair_share, exp_hub_share, imp_hub_share, title, out_dir)
    fig_scree(vals_R, vals_C, ratios_R, ratios_C, k, r, k_sel, title, out_dir)
    fig_loadings(R, countries, k, "export", "R", title, out_dir)
    fig_loadings(C, countries, r, "import", "C", title, out_dir)
    fig_factors(F, k, r, title, out_dir)
    print(f"outputs -> {out_dir}")


def fig_summary(top, pair_share, exp_share, imp_share, title, out_dir):
    fig = plt.figure(figsize=(10, 7))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], hspace=0.45, wspace=0.35)
    for col, (key, panel) in enumerate((("exporters_usd_bn", "Top 10 exporters, 2020-24"),
                                        ("importers_usd_bn", "Top 10 importers, 2020-24"))):
        ax = fig.add_subplot(gs[0, col])
        names, vals = list(top[key])[::-1], list(top[key].values())[::-1]
        ax.barh(names, vals, color=SERIES[0], height=0.62)
        for n, v in zip(names, vals):
            ax.annotate(f"{v:.0f}", (v, n), xytext=(4, -3), textcoords="offset points",
                        fontsize=8, color=INK2)
        ax.set_title(panel, fontsize=10, color=INK)
        ax.set_xlabel("$B")
        ax.tick_params(labelsize=8)
    ax = fig.add_subplot(gs[1, :])
    k, r = pair_share.shape
    im = ax.imshow(pair_share, cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
        "seq", ["#cde2fb", "#0d366b"]), vmin=0, vmax=pair_share.max())
    for i in range(k):
        for j in range(r):
            dark = pair_share[i, j] > 0.55 * pair_share.max()
            ax.text(j, i, f"{pair_share[i, j]:.0%}", ha="center", va="center",
                    fontsize=11, color="#ffffff" if dark else INK)
    ax.set_xticks(range(r), [f"imp hub {j+1}\n({imp_share[j]:.0%} total)" for j in range(r)],
                  fontsize=9)
    ax.set_yticks(range(k), [f"exp hub {i+1}\n({exp_share[i]:.0%})" for i in range(k)],
                  fontsize=9)
    ax.set_title("Hub size: share of fitted signal by hub pair (log space)",
                 fontsize=10, color=INK)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8, label="share of signal")
    fig.suptitle(f"{title} — summary statistics", color=INK)
    fig.savefig(out_dir / "summary.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_scree(vals_R, vals_C, ratios_R, ratios_C, k, r, k_sel, title, out_dir):
    fig, axes = plt.subplots(2, 2, figsize=(9, 5.6), sharex=True)
    n = np.arange(1, KMAX + 1)
    for col, (vals, ratios, kk, side) in enumerate(
            ((vals_R, ratios_R, k, "Row (export) side"),
             (vals_C, ratios_C, r, "Column (import) side"))):
        ax = axes[0, col]
        ax.bar(n, vals[:KMAX] / vals[0], color=SERIES[0], width=0.55)
        ax.set_title(side, fontsize=10, color=INK)
        ax.set_ylabel("eigenvalue (share of λ1)")
        axr = axes[1, col]
        axr.bar(n, ratios, color=SERIES[5], width=0.55)
        axr.axvline(kk + 0.5, color=MUTED, ls="--", lw=1)
        axr.set_ylabel("ratio λi / λi+1")
        axr.set_xlabel("component")
    fig.suptitle(f"{title} — rank selection "
                 f"(ratio estimator picks {k_sel}; working rank {k} for hub analysis)",
                 y=1.0, color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / "scree.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_loadings(L, countries, k, side, mat, title, out_dir):
    show = 12
    fig, axes = plt.subplots(1, k, figsize=(2.9 * k, 4.6), squeeze=False)
    for j in range(k):
        ax = axes[0, j]
        order = np.argsort(-np.abs(L[:, j]))[:show][::-1]
        vals = L[order, j]
        ax.barh([countries[i] for i in order], vals,
                color=[SERIES[j % len(SERIES)] if v >= 0 else MUTED for v in vals], height=0.62)
        ax.axvline(0, color="#c3c2b7", lw=1)
        ax.set_title(f"{side} hub {j+1}", fontsize=10, color=INK)
        ax.tick_params(labelsize=8)
    fig.suptitle(f"{title} — {side}-side loadings ({mat}, varimax, top {show})", color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / f"loadings_{side}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_factors(F, k, r, title, out_dir):
    lo, hi = F.min(), F.max()
    pad = 0.06 * (hi - lo)
    fig, axes = plt.subplots(k, r, figsize=(2.6 * r, 2.0 * k), sharex=True, sharey=True)
    axes = np.atleast_2d(axes)
    for i in range(k):
        for j in range(r):
            ax = axes[i, j]
            ax.plot(YEARS, F[:, i, j], "o-", lw=2, ms=4, color=SERIES[0])
            ax.set_ylim(lo - pad, hi + pad)
            ax.set_title(f"exp hub {i+1} → imp hub {j+1}", fontsize=9, color=INK2)
            ax.set_xticks([YEARS[0], YEARS[2], YEARS[-1]])
            ax.tick_params(labelsize=8)
            if j == 0:
                ax.set_ylabel("F (log units)", fontsize=8)
    fig.suptitle(f"{title} — hub-to-hub factor matrix F_t, {YEARS[0]}-{YEARS[-1]} "
                 "(shared y-scale)", color=INK)
    fig.tight_layout()
    fig.savefig(out_dir / "factors.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    labels = sys.argv[1:] or list(ANALYSES)
    for lab in labels:
        run(lab)
