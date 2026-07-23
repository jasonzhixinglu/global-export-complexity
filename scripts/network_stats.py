"""Concentration & fragmentation statistics from the TV-MFM hub decomposition.

Implements the measure system of docs/concentration-fragmentation-nnf-mfm-trade.md
on the stored per-month loadings/factors of the era-anchored TV-MFM
(results/mfm/tvmfm/chn_hkg_bloc/*/stats.json), per month:

  Level 0   a_k, b_k'          within-hub country HHIs (export / import side)
  Level 1   HHI_exp, HHI_imp   volume-weighted one-sided aggregates
  core      HHI_F              hub-pair linkage concentration
            HHI_row_k          per-hub linkage concentration (one program or many?)
  Level 2   HHI_flat           channel-level joint concentration
            = HHI_F * (mu_a*mu_b + aligncov)   exact decomposition (doc Part V)
            HHI_bilat          bilateral HHI of the reconstructed flows (>= HHI_flat)
  overlap   frag_exp/imp       1 - volume-weighted cosine overlap across hubs
            effrank_exp/imp    IPR of the Gram spectrum
  blocs     s_{B->B'}          smooth bloc-channel shares (doc IV.4):
            crossbloc_cnus     CN-bloc <-> US-bloc channel share (both directions)
            within_cn/within_us

Loadings are the nonnegativity-identified basis but only approximately nonnegative:
negatives are clipped to zero and columns renormalized; the clipped mass share is
tracked per month as a basis-quality diagnostic (doc Part VI).

Outputs -> results/network_stats/<label>/ (series.csv, figures, summary.md)
plus results/network_stats/README.md with the cross-code comparison and the
concentration-vs-power first pass (destination/origin HHIs from the raw panel).
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

LABELS = ["ai_compute", "847150", "847180", "847330"]
SRC = cfg.RESULTS_DIR / "mfm" / "tvmfm" / "chn_hkg_bloc"
OUT = cfg.RESULTS_DIR / "network_stats"
PANEL = cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet"
TITLES = {"ai_compute": "AI compute (3 codes)", "847150": "HS 847150 (AI servers)",
          "847180": "HS 847180 (baseboards)", "847330": "HS 847330 (parts/GPU cards)"}
BREAKS = {"202307": "2023-07 (H100 ramp)", "202504": "2025-04 (tariffs)"}

CN_BLOC = {"CHK", "CHN", "HKG"}
US_BLOC = {"USA", "USM", "MEX", "CAN"}

SERIES = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a", "#eb6834", "#4a3aa7", "#e34948"]
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
})


def shares(L):
    """Clip negatives, renormalize columns to the simplex; return (P, colsums, clipped)."""
    clipped = float((np.minimum(L, 0) ** 2).sum() / (L ** 2).sum())
    Lc = np.clip(L, 0, None)
    s = Lc.sum(0)
    s[s == 0] = 1.0
    return Lc / s, s, clipped


def month_stats(R, C, F, countries):
    P, sig, clipR = shares(R)
    Q, tau, clipC = shares(C)
    Fs = sig[:, None] * F * tau[None, :]                     # scale into F (doc Part II)
    clipF = float((np.minimum(Fs, 0) ** 2).sum() / max((Fs ** 2).sum(), 1e-300))
    Ft = np.clip(Fs, 0, None)
    g = Ft / Ft.sum()
    w, v = g.sum(1), g.sum(0)
    a, b = (P ** 2).sum(0), (Q ** 2).sum(0)

    hhi_exp, hhi_imp = float(w @ a), float(v @ b)
    hhi_F = float((g ** 2).sum())
    hhi_flat = float((g ** 2 * np.outer(a, b)).sum())
    tg = g ** 2 / hhi_F
    mu_a, mu_b = float(tg.sum(1) @ a), float(tg.sum(0) @ b)
    aligncov = float((tg * np.outer(a, b)).sum() - mu_a * mu_b)
    h = g / np.where(w[:, None] > 0, w[:, None], 1.0)
    hhi_row = (h ** 2).sum(1)
    X = P @ g @ Q.T                                  # reconstructed bilateral shares
    hhi_bilat = float((X ** 2).sum())

    def side(Pm, wt):
        S = Pm.T @ Pm
        d = np.sqrt(np.diag(S))
        cos = S / np.outer(d, d)
        K = len(wt)
        om = np.outer(wt, wt) * (1 - np.eye(K))
        om = om / om.sum() if om.sum() > 0 else om
        frag = float(1 - (om * cos).sum())
        eff = float(np.trace(S) ** 2 / (S ** 2).sum())
        return frag, eff

    frag_exp, eff_exp = side(P, w)
    frag_imp, eff_imp = side(Q, v)

    cn = np.array([c in CN_BLOC for c in countries])
    us = np.array([c in US_BLOC for c in countries])
    Pcn, Pus = P[cn].sum(0), P[us].sum(0)
    Qcn, Qus = Q[cn].sum(0), Q[us].sum(0)
    s = lambda x, y: float((g * np.outer(x, y)).sum())
    row = {
        "hhi_exp": hhi_exp, "hhi_imp": hhi_imp, "hhi_F": hhi_F,
        "hhi_flat": hhi_flat, "hhi_bilat": hhi_bilat,
        "mu_a": mu_a, "mu_b": mu_b, "aligncov": aligncov,
        "frag_exp": frag_exp, "frag_imp": frag_imp,
        "effrank_exp": eff_exp, "effrank_imp": eff_imp,
        "crossbloc_cnus": s(Pcn, Qus) + s(Pus, Qcn),
        "within_cn": s(Pcn, Qcn), "within_us": s(Pus, Qus),
        "clip_R": clipR, "clip_C": clipC, "clip_F": clipF,
    }
    for k in range(len(hhi_row)):
        row[f"a_{k+1}"], row[f"b_{k+1}"] = float(a[k]), float(b[k])
        row[f"hhi_row_{k+1}"], row[f"w_{k+1}"] = float(hhi_row[k]), float(w[k])
    return row


def run(label):
    st = json.loads((SRC / label / "stats.json").read_text())
    countries, periods = st["countries"], st["periods"]
    rows = []
    for t in periods:
        R = np.array(st["R_by_period"][t])
        C = np.array(st["C_by_period"][t])
        F = np.array(st["F_by_period"][t])
        rows.append(month_stats(R, C, F, countries))
    df = pd.DataFrame(rows, index=pd.to_datetime([f"{t[:4]}-{t[4:]}-01" for t in periods]))
    df.index.name = "period"
    out = OUT / label
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "series.csv")
    figs(df, label, out)
    summary(df, label, out, periods)
    print(f"{label}: {len(df)} months -> {out}")
    return df


def _ma(x):
    return x.rolling(3, min_periods=1).mean()


def _mark(ax, df):
    for t, name in BREAKS.items():
        d = pd.Timestamp(f"{t[:4]}-{t[4:]}-01")
        if df.index[0] <= d <= df.index[-1]:
            ax.axvline(d, color="#e34948", ls=":", lw=1.2)


def figs(df, label, out):
    title = TITLES[label]
    # 1. joint-concentration decomposition
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex=True)
    panels = [("hhi_F", "linkage concentration HHI_F"),
              (None, "linkage-weighted means mu_a * mu_b"),
              ("aligncov", "alignment covariance Cov(a,b)"),
              (None, "joint: HHI_flat (blue) vs bilateral (green)")]
    for ax, (col, name) in zip(axes.flat, panels):
        _mark(ax, df)
        if name.startswith("linkage-weighted"):
            ax.plot(df.index, _ma(df.mu_a * df.mu_b), lw=2, color=SERIES[0])
        elif name.startswith("joint"):
            ax.plot(df.index, _ma(df.hhi_flat), lw=2, color=SERIES[0])
            ax.plot(df.index, _ma(df.hhi_bilat), lw=2, color=SERIES[1])
        else:
            ax.plot(df.index, _ma(df[col]), lw=2, color=SERIES[0])
            if col == "aligncov":
                ax.axhline(0, color="#c3c2b7", lw=1)
        ax.set_title(name, fontsize=10, color=INK)
    fig.suptitle(f"{title} — joint concentration decomposition "
                 "(3m MA; dotted = 2023-07, 2025-04)", color=INK)
    fig.tight_layout()
    fig.savefig(out / "decomposition.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 2. fragmentation: agnostic (hub overlap) vs bloc (channel shares)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharex=True)
    ax = axes[0]
    _mark(ax, df)
    ax.plot(df.index, _ma(df.frag_exp), lw=2, color=SERIES[0], label="export side")
    ax.plot(df.index, _ma(df.frag_imp), lw=2, color=SERIES[1], label="import side")
    ax.set_title("hub-overlap fragmentation (agnostic)", fontsize=10, color=INK)
    ax.legend(fontsize=8, frameon=False)
    ax = axes[1]
    _mark(ax, df)
    ax.plot(df.index, _ma(df.crossbloc_cnus), lw=2, color=SERIES[7], label="cross-bloc CN<->US")
    ax.plot(df.index, _ma(df.within_us), lw=2, color=SERIES[0], label="within US-bloc")
    ax.plot(df.index, _ma(df.within_cn), lw=2, color=SERIES[3], label="within CN-bloc")
    ax.set_title("bloc channel shares of g (geopolitical)", fontsize=10, color=INK)
    ax.legend(fontsize=8, frameon=False)
    fig.suptitle(f"{title} — two notions of fragmentation (3m MA)", color=INK)
    fig.tight_layout()
    fig.savefig(out / "fragmentation.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    # 3. per-hub linkage concentration + basis diagnostic
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharex=True)
    ax = axes[0]
    _mark(ax, df)
    for k in range(4):
        ax.plot(df.index, _ma(df[f"hhi_row_{k+1}"]), lw=2, color=SERIES[k],
                label=f"export hub {k+1}")
    ax.set_title("per-hub linkage HHI (1 = sells to a single import hub)",
                 fontsize=10, color=INK)
    ax.legend(fontsize=8, frameon=False)
    ax = axes[1]
    _mark(ax, df)
    ax.plot(df.index, df.clip_R, lw=2, color=SERIES[0], label="R clipped mass")
    ax.plot(df.index, df.clip_C, lw=2, color=SERIES[1], label="C clipped mass")
    ax.set_title("negative mass clipped (basis-quality diagnostic)", fontsize=10, color=INK)
    ax.legend(fontsize=8, frameon=False)
    fig.suptitle(f"{title} — linkage structure and basis diagnostics", color=INK)
    fig.tight_layout()
    fig.savefig(out / "linkage.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def window_delta(df, t, pre=3, post=3):
    d = pd.Timestamp(f"{t[:4]}-{t[4:]}-01")
    before = df[(df.index < d) & (df.index >= d - pd.DateOffset(months=pre))]
    after = df[(df.index >= d) & (df.index < d + pd.DateOffset(months=post))]
    if before.empty or after.empty:
        return None
    return before.mean(), after.mean()


def summary(df, label, out, periods):
    title = TITLES[label]
    cols = ["hhi_F", "aligncov", "hhi_flat", "hhi_bilat", "frag_exp",
            "crossbloc_cnus", "within_us", "within_cn"]
    lines = [f"# Network concentration & fragmentation — {title}", "",
             "Measures per docs/concentration-fragmentation-nnf-mfm-trade.md, computed "
             "monthly from the era-anchored TV-MFM (CHN+HKG bloc, NNF basis, clipped "
             "shares). Full series in `series.csv`.", "",
             f"Coverage {df.index[0]:%Y-%m} .. {df.index[-1]:%Y-%m} ({len(df)} months). "
             f"Mean clipped negative mass: R {df.clip_R.mean():.3f}, C {df.clip_C.mean():.3f} "
             f"(max {max(df.clip_R.max(), df.clip_C.max()):.3f}).", "",
             "## Readings around the structural breaks (3m before vs 3m from the break)", ""]
    for t, name in BREAKS.items():
        wd = window_delta(df, t)
        if wd is None:
            lines += [f"### {name}: outside sample", ""]
            continue
        before, after = wd
        lines += [f"### {name}", "",
                  "| measure | before | after | change |", "|---|---|---|---|"]
        for c in cols:
            lines.append(f"| {c} | {before[c]:.4f} | {after[c]:.4f} | "
                         f"{after[c] - before[c]:+.4f} |")
        lines.append("")
    lines += ["## Figures", "", "![decomposition](decomposition.png)",
              "![fragmentation](fragmentation.png)", "![linkage](linkage.png)", "",
              "_Generated by `scripts/network_stats.py`._"]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def power_table():
    """Concentration-vs-power first pass: destination/origin HHIs from the raw panel."""
    p = pd.read_parquet(PANEL)
    p = p.assign(exporter=p.exporter.replace({"CHN": "CHK", "HKG": "CHK"}),
                 importer=p.importer.replace({"CHN": "CHK", "HKG": "CHK"}))
    p = p[p.exporter != p.importer]
    p["year"] = p.period.str[:4].astype(int)

    def hhi(g):
        s = g / g.sum()
        return float((s ** 2).sum())

    rows = []
    for (exp, code), grp in p.groupby(["exporter", "code"]):
        if exp not in {"TWN", "MEX", "CHK", "KOR", "USA", "VNM"}:
            continue
        for yr in (2023, 2025):
            gy = grp[grp.year == yr]
            if gy.value.sum() <= 0:
                continue
            rows.append({"exporter": exp, "code": code, "year": yr,
                         "dest_hhi": hhi(gy.groupby("importer").value.sum()),
                         "exports_bn": gy.value.sum() / 1e9})
    dest = pd.DataFrame(rows)
    rows = []
    for (imp, code), grp in p.groupby(["importer", "code"]):
        if imp not in {"USA", "CHK", "TWN", "MEX", "VNM"}:
            continue
        for yr in (2023, 2025):
            gy = grp[grp.year == yr]
            if gy.value.sum() <= 0:
                continue
            rows.append({"importer": imp, "code": code, "year": yr,
                         "orig_hhi": hhi(gy.groupby("exporter").value.sum()),
                         "imports_bn": gy.value.sum() / 1e9})
    orig = pd.DataFrame(rows)
    return dest, orig


def readme(dfs):
    dest, orig = power_table()

    def piv(d, key, val):
        t = d.pivot_table(index=[key, "code"], columns="year", values=val)
        return t

    dp = piv(dest, "exporter", "dest_hhi")
    op = piv(orig, "importer", "orig_hhi")
    lines = ["# Network concentration & fragmentation statistics", "",
             "Monthly implementation of docs/concentration-fragmentation-nnf-mfm-trade.md "
             "on the era-anchored TV-MFM (CHN+HKG bloc, nonnegativity-identified basis). "
             "One folder per basket; each has `series.csv`, three figures, and a "
             "`summary.md` with break-window readings. Interpretation of the "
             "results: see `findings.md` (hand-written, not regenerated).", "",
             "| basket | HHI_F (mean) | aligncov (mean) | frag_exp (mean) | "
             "crossbloc CN<->US: first yr -> last yr |", "|---|---|---|---|---|"]
    for label, df in dfs.items():
        y0 = df.loc[df.index < df.index[0] + pd.DateOffset(months=12), "crossbloc_cnus"].mean()
        y1 = df.loc[df.index > df.index[-1] - pd.DateOffset(months=12), "crossbloc_cnus"].mean()
        lines.append(f"| {label} | {df.hhi_F.mean():.3f} | {df.aligncov.mean():+.4f} | "
                     f"{df.frag_exp.mean():.3f} | {y0:.3f} -> {y1:.3f} |")
    lines += ["", "## Concentration vs market power — first pass", "",
              "Destination HHI (downstream concentration) per key exporter x code, "
              "2023 vs 2025, from the raw panel (CHK = CHN+HKG). The test: does "
              "concentration predict where pricing power appeared? Prior evidence — "
              "Taiwan repriced 20x under stress (power), Mexico's corridor was "
              "contested within a quarter (no power).", "",
              "| exporter | code | dest HHI 2023 | dest HHI 2025 |", "|---|---|---|---|"]
    for (exp, code), r in dp.iterrows():
        v23 = f"{r.get(2023, float('nan')):.3f}" if pd.notna(r.get(2023)) else "-"
        v25 = f"{r.get(2025, float('nan')):.3f}" if pd.notna(r.get(2025)) else "-"
        lines.append(f"| {exp} | {code} | {v23} | {v25} |")
    lines += ["", "Origin HHI (upstream supplier concentration) per key importer x code:",
              "", "| importer | code | orig HHI 2023 | orig HHI 2025 |", "|---|---|---|---|"]
    for (imp, code), r in op.iterrows():
        v23 = f"{r.get(2023, float('nan')):.3f}" if pd.notna(r.get(2023)) else "-"
        v25 = f"{r.get(2025, float('nan')):.3f}" if pd.notna(r.get(2025)) else "-"
        lines.append(f"| {imp} | {code} | {v23} | {v25} |")
    lines += ["", "_Generated by `scripts/network_stats.py`. Upstream raw-material "
              "stages await the chips-stage monthly panel extension._"]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    dfs = {lab: run(lab) for lab in (sys.argv[1:] or LABELS)}
    readme(dfs)
    print(f"index -> {OUT / 'README.md'}")
