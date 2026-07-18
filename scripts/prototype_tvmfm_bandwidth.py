"""Bandwidth experiment for the time-varying matrix factor model on the monthly panel.

Question (see docs/references/ Chen et al. 2024): how wide should the (one-sided)
estimation window for the time-varying loadings be? Candidate schemes, all one-sided so
estimates are defined up to the latest publication month:
  - uniform rolling windows of w months (w=3 is the user's simple proposal)
  - EWMA kernels with half-life hl months (smooth one-sided kernel)
  - expanding window (constant-loading limit)

Criterion 1 (out-of-sample fit): estimate loading spaces R_t, C_t from data through t,
project Y_{t+1} onto them; OOS R^2 = ||P_R Y_{t+1} P_C||^2 / ||Y_{t+1}||^2. Fresh-but-
noisy vs stale-but-stable resolves here.
Criterion 2 (stability): mean chordal distance between consecutive row loading spaces.

Data: balanced monthly panel (build_monthly_panel.py), all three codes summed,
$B levels (levels convention per results/mfm), 31x31 incl ROW. Rank fixed at k=r=4
across schemes (paper's rank; comparability).

Outputs: results/mfm/tv_bandwidth_ai_compute_monthly/ (report + figure + json).
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

K = 4
T_MIN_EVAL = 36          # first t whose (t -> t+1) projection enters the evaluation
OUT_DIR = cfg.RESULTS_DIR / "mfm" / "tv_bandwidth_ai_compute_monthly"
PANEL = cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet"

SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})


def load_Y():
    p = pd.read_parquet(PANEL)
    agg = p.groupby(["exporter", "importer", "period"], as_index=False).value.sum()
    countries = sorted(set(agg.exporter) | set(agg.importer))
    periods = sorted(agg.period.unique())
    idx = {c: i for i, c in enumerate(countries)}
    pidx = {q: t for t, q in enumerate(periods)}
    Y = np.zeros((len(periods), len(countries), len(countries)))
    Y[agg.period.map(pidx), agg.exporter.map(idx), agg.importer.map(idx)] = agg.value / 1e9
    return Y, countries, periods


def loading_spaces(M_R, M_C, k=K):
    _, vec_r = np.linalg.eigh(M_R)
    _, vec_c = np.linalg.eigh(M_C)
    return vec_r[:, -k:], vec_c[:, -k:]


def weights(scheme, t):
    """One-sided weights over observations 0..t for the estimate at time t."""
    kind, param = scheme
    idx = np.arange(t + 1)
    if kind == "uniform":
        w = (idx > t - param).astype(float)
    elif kind == "ewma":
        w = 0.5 ** ((t - idx) / param)
    elif kind == "expanding":
        w = np.ones(t + 1)
    return w / w.sum()


def run_scheme(Y, scheme):
    T = Y.shape[0]
    oos, stab = [], []
    prev_R = None
    for t in range(T_MIN_EVAL, T):
        w = weights(scheme, t)
        M_R = np.einsum("s,sij,skj->ik", w, Y[:t + 1], Y[:t + 1])
        M_C = np.einsum("s,sji,sjk->ik", w, Y[:t + 1], Y[:t + 1])
        R, C = loading_spaces(M_R, M_C)
        if prev_R is not None:
            stab.append(np.sqrt(max(0.0, K - np.sum((prev_R.T @ R) ** 2))) / np.sqrt(K))
        prev_R = R
        if t + 1 < T:
            Yn = Y[t + 1]
            fit = R @ (R.T @ Yn @ C) @ C.T
            oos.append((fit ** 2).sum() / (Yn ** 2).sum())
    return float(np.mean(oos)), float(np.mean(stab))


def main():
    Y, countries, periods = load_Y()
    print(f"panel: {Y.shape[0]} months x {Y.shape[1]} countries, "
          f"{periods[0]}..{periods[-1]}, rank k=r={K}")
    schemes = ([("uniform", w) for w in (3, 6, 12, 18, 24, 36)]
               + [("ewma", hl) for hl in (3, 6, 12)]
               + [("expanding", None)])
    rows = []
    for sch in schemes:
        oos, stab = run_scheme(Y, sch)
        name = (f"rolling {sch[1]}m" if sch[0] == "uniform"
                else f"EWMA hl={sch[1]}m" if sch[0] == "ewma" else "expanding (constant)")
        rows.append({"scheme": name, "kind": sch[0], "param": sch[1],
                     "oos_r2": oos, "stability_dist": stab})
        print(f"  {name:22s}  OOS R^2 {oos:.4f}   subspace step-change {stab:.4f}")
    df = pd.DataFrame(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results.json").write_text(json.dumps(
        {"rank": K, "eval_from_month_index": T_MIN_EVAL, "n_months": int(Y.shape[0]),
         "results": rows}, indent=1))
    fig(df)
    report(df, periods)
    print(f"outputs -> {OUT_DIR}")


def fig(df):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    d = df[df.kind == "uniform"]
    axes[0].plot(d.param, d.oos_r2, "o-", color=SERIES[0], lw=2, label="rolling window")
    e = df[df.kind == "ewma"]
    axes[0].plot(e.param * 2, e.oos_r2, "s--", color=SERIES[5], lw=2,
                 label="EWMA (2x half-life)")
    exp_r2 = df[df.kind == "expanding"].oos_r2.iloc[0]
    axes[0].axhline(exp_r2, color=MUTED, ls=":", lw=1.5)
    axes[0].annotate("expanding (constant loadings)", (3, exp_r2), xytext=(0, 5),
                     textcoords="offset points", fontsize=8, color=INK2)
    axes[0].set_xlabel("window length (months)")
    axes[0].set_ylabel("out-of-sample R²  (project next month)")
    axes[0].set_title("Freshness vs noise: OOS fit by bandwidth", fontsize=10, color=INK)
    axes[0].legend(fontsize=8, frameon=False)
    axes[1].plot(d.param, d.stability_dist, "o-", color=SERIES[0], lw=2)
    axes[1].plot(e.param * 2, e.stability_dist, "s--", color=SERIES[5], lw=2)
    axes[1].set_xlabel("window length (months)")
    axes[1].set_ylabel("mean month-to-month subspace change")
    axes[1].set_title("Loading-space stability", fontsize=10, color=INK)
    fig.suptitle("Time-varying MFM bandwidth — AI-compute monthly panel "
                 f"(k=r={K}, one-sided estimation)", color=INK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "bandwidth.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def report(df, periods):
    best = df.loc[df.oos_r2.idxmax()]
    r3 = df[(df.kind == "uniform") & (df.param == 3)].iloc[0]
    r12 = df[(df.kind == "uniform") & (df.param == 12)].iloc[0]
    lines = [
        "# Bandwidth experiment — time-varying MFM on the monthly AI-compute panel", "",
        f"Balanced panel {periods[0]}..{periods[-1]} (T={len(periods)}), 31 entities "
        f"incl ROW, all three codes summed, $B levels, rank k=r={K}. All schemes "
        "one-sided (defined through the latest month). OOS criterion: estimate loading "
        "spaces through t, project month t+1, share of variance captured.",
        "", "| scheme | OOS R² | mean subspace step-change |", "|---|---|---|",
    ]
    for _, r in df.iterrows():
        lines.append(f"| {r.scheme} | {r.oos_r2:.4f} | {r.stability_dist:.4f} |")
    lines += [
        "",
        f"Best OOS: **{best.scheme}** ({best.oos_r2:.4f}). "
        f"Rolling 3m: {r3.oos_r2:.4f} with step-change {r3.stability_dist:.4f} "
        f"({r3.stability_dist / r12.stability_dist:.1f}x the 12m window's).",
        "",
        "_Generated by `scripts/prototype_tvmfm_bandwidth.py`._",
    ]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
