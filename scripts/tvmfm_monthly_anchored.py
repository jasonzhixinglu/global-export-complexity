"""Era-anchored time-varying MFM on the monthly AI-compute panel.

Resolves hub-label instability (see tvmfm_monthly.py, whose chained month-to-month
matching accumulates ambiguity through high-drift bursts):
  1. Segment the sample into ERAS: burst months are where the 12m-window loading
     subspace jumps (chordal drift > THR); eras are the calm stretches between bursts
     (eras shorter than MIN_ERA months merge into their successor).
  2. Estimate a CONSTANT-loading anchor MFM per era (pooled covariances, varimax);
     each era's anchor is permutation/sign-matched to the previous era's, so hub
     labels carry across eras as faithfully as the data allows.
  3. Align every month's local (12m trailing) loadings to its era anchor by orthogonal
     Procrustes -- no chaining, so no drift accumulation; within an era, labels are
     fixed by construction.
  4. Cross-era CROSSWALK: cosine-similarity tables between adjacent era anchors --
     the quantified statement of how hub composition reorganized at each break.
  5. Functional labels: import hubs are stable (USA / entrepot / Europe / Asia), so
     each export hub is labeled by its dominant destination import hub in the era-
     average F, plus its top member for display.

Outputs -> results/mfm/tv_ai_compute_monthly_12m_anchored/
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
THR = 0.20               # drift threshold marking a structural burst
MIN_ERA = 6              # months; shorter calm stretches merge into the next era
PANEL = cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet"

ALL_CODES = ["847150", "847180", "847330"]
# China+HKG bloc: CHN and HKG merged into one entity CHK; intra-bloc flows (the
# CHN<->HKG entrepot churn) cancel, and HKG re-exports are attributed to the bloc.
# Taiwan is deliberately NOT part of this bloc -- it is a separate economy in the
# supply chain; its substitution vs China is a finding to measure, not to merge away.
CHNHKG_BLOC = {"CHN": "CHK", "HKG": "CHK"}
ANALYSES = {
    "847150": (["847150"], {}),
    "847180": (["847180"], {}),
    "847330": (["847330"], {}),
    "ai_compute": (ALL_CODES, {}),
    "ai_compute_chnhkg": (ALL_CODES, CHNHKG_BLOC),
}
TITLES = {
    "847150": "HS 847150 (AI servers)",
    "847180": "HS 847180 (other units / baseboards)",
    "847330": "HS 847330 (parts / GPU cards)",
    "ai_compute": "AI compute (sum of 3 codes)",
    "ai_compute_chnhkg": "AI compute, China+HKG bloc (TWN separate)",
}

SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})


def load_Y(codes, bloc=None):
    p = pd.read_parquet(PANEL)
    p = p[p.code.isin(codes)]
    if bloc:
        p = p.assign(exporter=p.exporter.replace(bloc), importer=p.importer.replace(bloc))
        p = p[p.exporter != p.importer]     # intra-bloc flows cancel
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
    return vec[:, -k:][:, ::-1]


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


def perm_sign_match(A, ref):
    """Permute/sign columns of orthonormal-ish A to best match ref (greedy)."""
    S = np.abs(ref.T @ A)
    order = np.full(K, -1)
    for _ in range(K):
        i, j = np.unravel_index(np.argmax(S), S.shape)
        order[i] = j
        S[i, :], S[:, j] = -1, -1
    A = A[:, order]
    signs = np.sign(np.sum(ref * A, axis=0))
    signs[signs == 0] = 1
    return A * signs


def procrustes_to(L, anchor):
    """Rotate orthonormal L onto orthonormal anchor (orthogonal Procrustes)."""
    U, _, Vt = np.linalg.svd(L.T @ anchor)
    return L @ (U @ Vt)


def local_spaces(Y):
    """12m trailing eigvec spaces + drift series (pre-alignment, label-free)."""
    T = Y.shape[0]
    est_t = list(range(WINDOW - 1, T))
    Rraw, Craw, drift = [], [], []
    for t in est_t:
        Yw = Y[t - WINDOW + 1: t + 1]
        R = top_eigvecs(np.einsum("sij,skj->ik", Yw, Yw))
        C = top_eigvecs(np.einsum("sji,sjk->ik", Yw, Yw))
        if Rraw:
            drift.append(np.sqrt(max(0.0, K - ((Rraw[-1].T @ R) ** 2).sum())) / np.sqrt(K))
        Rraw.append(R)
        Craw.append(C)
    return est_t, Rraw, Craw, drift


def segment_eras(est_t, drift):
    """Burst months split eras; short eras merge into their successor."""
    bursts = [i + 1 for i, d in enumerate(drift) if d > THR]   # index into est_t
    bounds = [0] + bursts + [len(est_t)]
    eras = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)
            if bounds[i + 1] > bounds[i]]
    merged = []
    for a, b in eras:
        if merged and (b - a) < MIN_ERA:
            merged[-1] = (merged[-1][0], b)      # absorb short stretch backwards
        elif merged and (merged[-1][1] - merged[-1][0]) < MIN_ERA:
            merged[-1] = (merged[-1][0], b)      # previous was short: extend it
        else:
            merged.append((a, b))
    if len(merged) > 1 and merged[-1][1] - merged[-1][0] < MIN_ERA:
        a, b = merged.pop()
        merged[-1] = (merged[-1][0], b)
    return merged


def main(label="ai_compute"):
    global OUT_DIR, TITLE
    codes_, bloc_ = ANALYSES[label]
    group = "chn_hkg_bloc" if bloc_ else "by_country"
    OUT_DIR = cfg.RESULTS_DIR / "mfm" / "tvmfm" / group / label.replace("_chnhkg", "")
    TITLE = TITLES[label]
    print(f"\n=== {TITLE} ===")
    codes, bloc = ANALYSES[label]
    Y, countries, periods = load_Y(codes, bloc)
    p = q = Y.shape[1]
    est_t, Rraw, Craw, drift = local_spaces(Y)
    labels = [periods[t] for t in est_t]
    eras = segment_eras(est_t, drift)
    print("eras (estimate-month ranges):")
    for e, (a, b) in enumerate(eras):
        print(f"  era {e}: {labels[a]} .. {labels[b - 1]} ({b - a} months)")

    # era anchors: pooled covariance over the era's raw months, varimax, chained match
    anchorsR, anchorsC = [], []
    for e, (a, b) in enumerate(eras):
        months = range(est_t[a] - 0, est_t[b - 1] + 1)   # raw months covered
        Ye = Y[list(months)]
        A_R = top_eigvecs(np.einsum("sij,skj->ik", Ye, Ye))
        A_C = top_eigvecs(np.einsum("sji,sjk->ik", Ye, Ye))
        A_R, A_C = A_R @ varimax(A_R * np.sqrt(p)), A_C @ varimax(A_C * np.sqrt(q))
        if anchorsR:
            A_R = perm_sign_match(A_R, anchorsR[-1])
            A_C = perm_sign_match(A_C, anchorsC[-1])
        else:
            for A in (A_R, A_C):                          # dominant member positive
                for j in range(K):
                    if A[np.abs(A[:, j]).argmax(), j] < 0:
                        A[:, j] *= -1
        anchorsR.append(A_R)
        anchorsC.append(A_C)

    # monthly loadings: Procrustes to the era anchor (no chaining)
    era_of = np.zeros(len(est_t), int)
    for e, (a, b) in enumerate(eras):
        era_of[a:b] = e
    Rs = [np.sqrt(p) * procrustes_to(Rraw[i], anchorsR[era_of[i]])
          for i in range(len(est_t))]
    Cs = [np.sqrt(q) * procrustes_to(Craw[i], anchorsC[era_of[i]])
          for i in range(len(est_t))]
    F = np.array([Rs[i].T @ Y[t] @ Cs[i] / (p * q) for i, t in enumerate(est_t)])
    F_ma = pd.DataFrame(F.reshape(len(F), -1)).rolling(3, min_periods=1).mean() \
             .values.reshape(F.shape)

    S = np.array([Rs[i] @ F[i] @ Cs[i].T for i in range(len(est_t))])
    r2 = 1 - ((Y[est_t] - S) ** 2).sum() / (Y[est_t] ** 2).sum()

    # label-stability metric: mean loading change within eras (excl. era transitions)
    steps = [np.linalg.norm(Rs[i] - Rs[i - 1]) / np.linalg.norm(Rs[i - 1])
             for i in range(1, len(Rs)) if era_of[i] == era_of[i - 1]]
    print(f"in-sample R^2: {r2:.3f}; mean within-era loading step {np.mean(steps):.3f}")

    # crosswalk between adjacent era anchors (columns are orthonormal -> |cos| in [0,1])
    crosswalk = [np.abs(anchorsR[e].T @ anchorsR[e + 1])
                 for e in range(len(eras) - 1)]

    # functional labels from era-average F: export hub j serves import hub argmax
    era_F = [F[a:b].mean(0) for a, b in eras]
    func = []
    for e in range(len(eras)):
        impname = [countries[int(np.abs(anchorsC[e][:, j]).argmax())] for j in range(K)]
        expname = [countries[int(np.abs(anchorsR[e][:, j]).argmax())] for j in range(K)]
        func.append({"export": [f"{expname[j]}-led, serves {impname[int(np.argmax(np.abs(era_F[e][j])))]}-hub"
                                for j in range(K)],
                     "import": [f"{impname[j]}-led" for j in range(K)]})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stats.json").write_text(json.dumps({
        "window": WINDOW, "k": K, "thr": THR, "r2": float(r2),
        "periods": labels, "countries": countries,
        "eras": [{"start": labels[a], "end": labels[b - 1]} for a, b in eras],
        "drift": [float(d) for d in drift],
        "crosswalk_R": [cw.tolist() for cw in crosswalk],
        "functional_labels": func,
        "anchors_R": [A.tolist() for A in anchorsR],
        "anchors_C": [A.tolist() for A in anchorsC],
        "R_by_period": {labels[i]: Rs[i].tolist() for i in range(len(labels))},
        "C_by_period": {labels[i]: Cs[i].tolist() for i in range(len(labels))},
        "F_by_period": {labels[i]: F[i].tolist() for i in range(len(labels))}}))

    fig_paths(Rs, countries, labels, eras, "export")
    fig_paths(Cs, countries, labels, eras, "import")
    fig_factors(F, F_ma, labels, eras)
    fig_drift(drift, labels, eras)
    write_summary(anchorsR, anchorsC, crosswalk, func, eras, labels, countries,
                  r2, np.mean(steps))
    print(f"outputs -> {OUT_DIR}")


def _dates(labels):
    return pd.to_datetime([f"{l[:4]}-{l[4:]}-01" for l in labels])


def _shade(ax, labels, eras):
    d = _dates(labels)
    for e, (a, b) in enumerate(eras):
        if e % 2 == 1:
            ax.axvspan(d[a], d[b - 1], color="#f0efec", zorder=0)


def fig_paths(Ls, countries, labels, eras, side):
    d = _dates(labels)
    L = np.stack(Ls)
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex=True)
    for j in range(K):
        ax = axes[j // 2, j % 2]
        _shade(ax, labels, eras)
        lead = np.argsort(-np.abs(L[:, :, j]).mean(0))[:6]
        for ci, i in enumerate(lead):
            ax.plot(d, L[:, i, j], lw=2, color=SERIES[ci % len(SERIES)])
            ax.annotate(countries[i], (d[-1], L[-1, i, j]), xytext=(4, 0),
                        textcoords="offset points", fontsize=8,
                        color=SERIES[ci % len(SERIES)])
        ax.set_title(f"{side} hub {j+1}", fontsize=10, color=INK)
        ax.axhline(0, color="#c3c2b7", lw=1)
    fig.suptitle(f"{TITLE} — {side} loadings, era-anchored "
                 "(12m window; shaded bands = eras)", color=INK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"loadings_{side}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_factors(F, F_ma, labels, eras):
    d = _dates(labels)
    lo, hi = F.min(), F.max()
    pad = 0.06 * (hi - lo)
    fig, axes = plt.subplots(K, K, figsize=(2.6 * K, 1.9 * K), sharex=True, sharey=True)
    for i in range(K):
        for j in range(K):
            ax = axes[i, j]
            _shade(ax, labels, eras)
            ax.plot(d, F[:, i, j], lw=1, color="#9ec5f4")
            ax.plot(d, F_ma[:, i, j], lw=2, color=SERIES[0])
            ax.set_ylim(lo - pad, hi + pad)
            ax.set_title(f"exp {i+1} → imp {j+1}", fontsize=8, color=INK2)
            ax.tick_params(labelsize=7)
    fig.suptitle(f"{TITLE} — hub-to-hub F_t, era-anchored (3m MA thick)", color=INK)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "factors.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_drift(drift, labels, eras):
    d = _dates(labels)[1:]
    fig, ax = plt.subplots(figsize=(9, 3))
    _shade(ax, labels, eras)
    ax.plot(d, drift, lw=2, color=SERIES[0])
    ax.axhline(THR, color=SERIES[5], ls="--", lw=1.5)
    ax.annotate(f"burst threshold {THR}", (d[0], THR), xytext=(0, 4),
                textcoords="offset points", fontsize=8, color=SERIES[5])
    ax.set_title("Loading-space drift with era segmentation", fontsize=10, color=INK)
    ax.set_ylabel("subspace change")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "drift.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_summary(aR, aC, crosswalk, func, eras, labels, countries, r2, step):
    def comp(A, j, n=6):
        lead = np.argsort(-np.abs(A[:, j]))[:n]
        return ", ".join(f"{countries[i]} {A[i, j]:+.2f}" for i in lead)

    lines = [f"# Era-anchored time-varying MFM — {TITLE}, monthly panel", "",
             f"12m trailing loadings, k=r={K}, $B levels; months aligned to per-era "
             f"constant anchors (Procrustes), no chained matching. In-sample R^2 "
             f"{r2:.3f}; mean within-era loading step {step:.3f} "
             f"(superseded chained version: ../../archive/ai_compute_chained).", ""]
    for e, (a, b) in enumerate(eras):
        lines += [f"## Era {e}: {labels[a][:4]}-{labels[a][4:]} .. "
                  f"{labels[b-1][:4]}-{labels[b-1][4:]}", ""]
        for j in range(K):
            lines.append(f"- export hub {j+1} ({func[e]['export'][j]}): "
                         f"{comp(np.array(aR[e]) * np.sqrt(len(countries)), j)}")
        lines.append("")
    lines += ["## Cross-era hub crosswalk (|cosine| between anchor loadings, "
              "rows = earlier era hub, cols = later era hub)", ""]
    for e, cw in enumerate(crosswalk):
        lines += [f"### era {e} -> era {e+1}", "",
                  "| | " + " | ".join(f"hub {j+1}'" for j in range(K)) + " |",
                  "|---|" + "---|" * K]
        for i in range(K):
            lines.append(f"| hub {i+1} | " + " | ".join(f"{cw[i, j]:.2f}"
                                                        for j in range(K)) + " |")
        lines.append("")
    lines += ["## Figures", "", "![drift](drift.png)", "![export loadings](loadings_export.png)",
              "![import loadings](loadings_import.png)", "![factors](factors.png)", "",
              "_Generated by `scripts/tvmfm_monthly_anchored.py`._"]
    (OUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    for lab in (sys.argv[1:] or list(ANALYSES)):
        main(lab)
