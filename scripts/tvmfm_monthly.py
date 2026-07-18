"""Time-varying matrix factor model on the monthly AI-compute panel.

Spec (per bandwidth experiment, results/mfm/tv_bandwidth_ai_compute_monthly):
  - loadings R_t, C_t: local PCA on a trailing 12-month uniform window (one-sided,
    seasonally balanced, defined through the latest month), rank k=r=4, $B levels
  - factors F_t = R_t' Y_t C_t / (pq): monthly, presented as 3-month moving average
  - rotation handling (Chen et al. 2024 Sec 5, simplified): month-to-month column
    matching + sign fixing against the previous month's loadings, then ONE global
    varimax rotation estimated on the stacked aligned loadings and applied to all t
  - drift diagnostic: chordal distance between consecutive (pre-rotation) subspaces

Outputs -> results/mfm/tv_ai_compute_monthly_12m/
Run after build_monthly_panel.py.
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
WINDOW = 12
PANEL = cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet"
OUT_DIR = cfg.RESULTS_DIR / "mfm" / "tv_ai_compute_monthly_12m"

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


def top_eigvecs(M, k=K):
    _, vec = np.linalg.eigh(M)
    return vec[:, -k:][:, ::-1]           # descending eigenvalue order


def align(L, ref):
    """Match columns of L to ref (greedy by |inner product|), fix signs."""
    k = L.shape[1]
    S = np.abs(ref.T @ L)                 # k x k similarity
    order = np.full(k, -1)
    used = set()
    for _ in range(k):
        i, j = np.unravel_index(np.argmax(S), S.shape)
        order[i] = j
        used.add(j)
        S[i, :] = -1
        S[:, j] = -1
    L = L[:, order]
    signs = np.sign(np.sum(ref * L, axis=0))
    signs[signs == 0] = 1
    return L * signs


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


def main():
    Y, countries, periods = load_Y()
    T, p, q = Y.shape
    est_t = list(range(WINDOW - 1, T))    # first estimate uses months 0..11
    print(f"panel {periods[0]}..{periods[-1]} (T={T}); estimates at {len(est_t)} months, "
          f"window {WINDOW}m, k=r={K}")

    Rs, Cs, drift = [], [], []
    for t in est_t:
        Yw = Y[t - WINDOW + 1: t + 1]
        M_R = np.einsum("sij,skj->ik", Yw, Yw) / (WINDOW * q)
        M_C = np.einsum("sji,sjk->ik", Yw, Yw) / (WINDOW * p)
        R, C = top_eigvecs(M_R), top_eigvecs(M_C)
        if Rs:
            drift.append(np.sqrt(max(0.0, K - ((Rs[-1].T @ R) ** 2).sum())) / np.sqrt(K))
            R, C = align(R, Rs[-1]), align(C, Cs[-1])
        Rs.append(R)
        Cs.append(C)

    # one global varimax on stacked aligned loadings; scale sqrt(p) convention
    Rstack = np.vstack(Rs) * np.sqrt(p)
    Cstack = np.vstack(Cs) * np.sqrt(q)
    O, Q = varimax(Rstack), varimax(Cstack)
    Rs = [R @ O * np.sqrt(p) for R in Rs]
    Cs = [C @ Q * np.sqrt(q) for C in Cs]
    # order hubs by average loading mass; dominant-positive sign convention
    mass = sum((R**2).sum(0) for R in Rs)
    orderR = np.argsort(-mass)
    massC = sum((C**2).sum(0) for C in Cs)
    orderC = np.argsort(-massC)
    Rs = [R[:, orderR] for R in Rs]
    Cs = [C[:, orderC] for C in Cs]
    for j in range(K):
        Rbar = np.mean([R[:, j] for R in Rs], axis=0)
        if Rbar[np.abs(Rbar).argmax()] < 0:
            for R in Rs:
                R[:, j] *= -1
        Cbar = np.mean([C[:, j] for C in Cs], axis=0)
        if Cbar[np.abs(Cbar).argmax()] < 0:
            for C in Cs:
                C[:, j] *= -1

    F = np.array([Rs[i].T @ Y[t] @ Cs[i] / (p * q) for i, t in enumerate(est_t)])
    F_ma = pd.DataFrame(F.reshape(len(F), -1)).rolling(3, min_periods=1).mean().values \
             .reshape(F.shape)

    S = np.array([Rs[i] @ F[i] @ Cs[i].T for i in range(len(est_t))])
    r2 = 1 - ((Y[est_t] - S) ** 2).sum() / (Y[est_t] ** 2).sum()
    print(f"in-sample R^2 (rank {K}, tv loadings): {r2:.3f}")
    print(f"mean drift {np.mean(drift):.4f}; top drift months: "
          + ", ".join(f"{periods[est_t[i+1]]} {d:.3f}"
                      for i, d in sorted(enumerate(drift), key=lambda x: -x[1])[:5]))

    labels = [periods[t] for t in est_t]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = {
        "window": WINDOW, "k": K, "r2": float(r2), "periods": labels,
        "countries": countries, "drift": [float(d) for d in drift],
        "R_by_period": {labels[i]: Rs[i].tolist() for i in range(len(labels))},
        "C_by_period": {labels[i]: Cs[i].tolist() for i in range(len(labels))},
        "F_by_period": {labels[i]: F[i].tolist() for i in range(len(labels))},
    }
    (OUT_DIR / "stats.json").write_text(json.dumps(stats))

    fig_loadings_paths(Rs, countries, labels, "export")
    fig_loadings_paths(Cs, countries, labels, "import")
    fig_factors(F, F_ma, labels)
    fig_drift(drift, labels)
    write_summary(Rs, Cs, F, drift, labels, countries, r2)
    print(f"outputs -> {OUT_DIR}")


def _dates(labels):
    return pd.to_datetime([f"{l[:4]}-{l[4:]}-01" for l in labels])


def fig_loadings_paths(Ls, countries, labels, side):
    d = _dates(labels)
    L = np.stack(Ls)                       # T x p x K
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex=True)
    for j in range(K):
        ax = axes[j // 2, j % 2]
        lead = np.argsort(-np.abs(L[:, :, j]).mean(0))[:6]
        for ci, i in enumerate(lead):
            ax.plot(d, L[:, i, j], lw=2, color=SERIES[ci % len(SERIES)])
            ax.annotate(countries[i], (d[-1], L[-1, i, j]), xytext=(4, 0),
                        textcoords="offset points", fontsize=8,
                        color=SERIES[ci % len(SERIES)])
        ax.set_title(f"{side} hub {j+1}", fontsize=10, color=INK)
        ax.axhline(0, color="#c3c2b7", lw=1)
    fig.suptitle(f"AI compute — time-varying {side} loadings "
                 f"(12m trailing window, varimax, top 6 per hub)", color=INK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"loadings_{side}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_factors(F, F_ma, labels):
    d = _dates(labels)
    lo, hi = F.min(), F.max()
    pad = 0.06 * (hi - lo)
    fig, axes = plt.subplots(K, K, figsize=(2.6 * K, 1.9 * K), sharex=True, sharey=True)
    for i in range(K):
        for j in range(K):
            ax = axes[i, j]
            ax.plot(d, F[:, i, j], lw=1, color="#9ec5f4")
            ax.plot(d, F_ma[:, i, j], lw=2, color=SERIES[0])
            ax.set_ylim(lo - pad, hi + pad)
            ax.set_title(f"exp {i+1} → imp {j+1}", fontsize=8, color=INK2)
            ax.tick_params(labelsize=7)
    fig.suptitle("AI compute — hub-to-hub factors F_t (monthly, thin; 3m MA, thick; "
                 "$B log-free levels)", color=INK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "factors.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_drift(drift, labels):
    d = _dates(labels)[1:]
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(d, drift, lw=2, color=SERIES[0])
    ax.set_title("Loading-space drift: chordal distance between consecutive months "
                 "(pre-rotation subspaces)", fontsize=10, color=INK)
    ax.set_ylabel("subspace change")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "drift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_summary(Rs, Cs, F, drift, labels, countries, r2):
    def hubs(L, n=6):
        out = []
        for j in range(K):
            lead = np.argsort(-np.abs(L[:, j]))[:n]
            out.append(", ".join(f"{countries[i]} {L[i, j]:+.2f}" for i in lead))
        return out

    snaps = [0, len(labels) // 2, len(labels) - 1]
    lines = [
        "# Time-varying MFM — AI compute, monthly panel, 12m trailing window", "",
        f"k=r={K}, $B levels, one global varimax; in-sample R^2 {r2:.3f}; "
        f"mean monthly subspace drift {np.mean(drift):.3f}.", "",
    ]
    for s in snaps:
        lines += [f"## Export hubs at {labels[s][:4]}-{labels[s][4:]}", ""]
        lines += [f"- hub {j+1}: {h}" for j, h in enumerate(hubs(Rs[s]))]
        lines += [""]
    lines += ["## Figures", "", "![export loadings](loadings_export.png)",
              "![import loadings](loadings_import.png)", "![factors](factors.png)",
              "![drift](drift.png)", "",
              "_Generated by `scripts/tvmfm_monthly.py`; full paths in `stats.json`._"]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
