"""Supply-chain flow charts: one bilateral 'flow of funds' diagram per chain stage.

One PNG per stage (equipment & inputs -> chips -> parts/modules 847330 ->
baseboards 847180 -> servers 847150), each showing 2024 exports from the top
exporting COUNTRIES (left) to the top importing COUNTRIES (right), ribbon width
proportional to dollars, country colours consistent across all charts. Within a
chart widths share one scale; ACROSS charts scales differ (totals differ 10x) --
each title carries the stage total.

Stage/code definitions per docs/tech-ai-taxonomy.md (OECD value chain + Fed
basket). Data: dashboard techai_bilateral.json (equipment, chips; HS2012
bilateral) and the monthly panel (compute codes). Output: exports/supply_chain_*.png
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
from matplotlib.path import Path as MplPath
from matplotlib.patches import PathPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

YEAR = "2024"
TOP_N = 9               # countries per side; rest folds into "Other"
OUT_DIR = cfg.ROOT / "exports"

# consistent country colours (dataviz palette; colour follows the entity)
COLOR = {"TWN": "#1baf7a", "CHN": "#e34948", "HKG": "#e87ba4", "KOR": "#eda100",
         "JPN": "#4a3aa7", "USA": "#2a78d6", "MEX": "#eb6834", "NLD": "#008300",
         "DEU": "#6da76d", "SGP": "#c98500", "MYS": "#d95926", "VNM": "#199e70",
         "THA": "#d55181", "IRL": "#57c785", "Other": "#b5b3ac"}
FALLBACK = "#898781"
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"

# The OECD 'photo' basket (photosensitive devices, $66B) is excluded: it is
# dominated by solar PV cells -- a fab OUTPUT, not an input to the AI chain.
STAGES = [
    ("1_raw_materials", "Stage 1 — Raw materials", "silicon 280461, rare gases, Ga/Ge, chemicals",
     ("json", ["raw"])),
    ("2_wafers", "Stage 2 — Wafers & wafer inputs", "381800, 3701xx/370790",
     ("json", ["wafer"])),
    ("3_litho_optics", "Stage 3 — Lithography & optics inputs", "9001xx/9002xx, 901210/90, 903141",
     ("json", ["foundry"])),
    ("4_equipment", "Stage 4 — Fab equipment", "8486xx, metrology, fab plant",
     ("json", ["equip"])),
    ("5_chips", "Stage 5 — Chips (logic, memory, discretes)", "8542xx, 8541xx, media",
     ("json", ["chips"])),
    ("6_parts", "Stage 6 — Parts & GPU modules", "HS 847330", ("panel", "847330")),
    ("7_baseboards", "Stage 7 — Baseboards / other units", "HS 847180", ("panel", "847180")),
    ("8_servers", "Stage 8 — Finished AI servers", "HS 847150", ("panel", "847150")),
]


def flows_json(baskets):
    d = json.load(open(cfg.ROOT / "dashboard" / "public" / "data" / "techai_bilateral.json"))
    agg = {}
    for b in baskets:
        for o, dests in d["value"].get(b, {}).items():
            for t, yrs in dests.items():
                v = yrs.get(YEAR)
                if v and o != t:
                    agg[(o, t)] = agg.get((o, t), 0.0) + v
    return agg


def flows_panel(code):
    p = pd.read_parquet(cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet")
    p = p[(p.code == code) & (p.period.str[:4] == YEAR)]
    g = p.groupby(["exporter", "importer"]).value.sum() / 1e9
    return {k: float(v) for k, v in g.items()}


def top_fold(flows):
    """Fold all but the top-N countries per side into 'Other'."""
    ex = pd.Series(dtype=float)
    im = pd.Series(dtype=float)
    for (o, t), v in flows.items():
        ex[o] = ex.get(o, 0.0) + v
        im[t] = im.get(t, 0.0) + v
    keep_o = set(ex.sort_values(ascending=False).head(TOP_N).index)
    keep_t = set(im.sort_values(ascending=False).head(TOP_N).index)
    out = {}
    for (o, t), v in flows.items():
        o2 = o if o in keep_o else "Other"
        t2 = t if t in keep_t else "Other"
        out[(o2, t2)] = out.get((o2, t2), 0.0) + v
    return out


def ribbon(ax, x0, x1, y0_top, y1_top, h, color):
    cx = (x1 - x0) * 0.42
    verts = [(x0, y0_top), (x0 + cx, y0_top), (x1 - cx, y1_top), (x1, y1_top),
             (x1, y1_top - h), (x1 - cx, y1_top - h), (x0 + cx, y0_top - h),
             (x0, y0_top - h), (x0, y0_top)]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=color,
                           edgecolor="none", alpha=0.55, zorder=1))


def draw_stage(fname, title, codes_txt, flows):
    flows = top_fold(flows)
    total = sum(flows.values())
    ex_tot = pd.Series(dtype=float)
    im_tot = pd.Series(dtype=float)
    for (o, t), v in flows.items():
        ex_tot[o] = ex_tot.get(o, 0.0) + v
        im_tot[t] = im_tot.get(t, 0.0) + v
    ex_order = list(ex_tot.sort_values(ascending=False).index)
    im_order = list(im_tot.sort_values(ascending=False).index)
    for lst in (ex_order, im_order):            # Other always last
        if "Other" in lst:
            lst.remove("Other")
            lst.append("Other")

    pad = 0.018
    usable = 1.0 - pad * (max(len(ex_order), len(im_order)) - 1)
    scale = usable / total
    x0n, x1n, nw = 0.16, 0.84, 0.012

    def stack(order, tot):
        pos, y = {}, 1.0
        for c in order:
            h = tot[c] * scale
            pos[c] = (y, h)
            y -= h + pad
        return pos

    ex_pos, im_pos = stack(ex_order, ex_tot), stack(im_order, im_tot)

    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.05, 1.03)
    ax.axis("off")
    fig.patch.set_facecolor(SURFACE)

    out_off = {c: 0.0 for c in ex_order}
    in_off = {c: 0.0 for c in im_order}
    for o in ex_order:                           # draw in stacked order
        for t in im_order:
            v = flows.get((o, t), 0.0)
            if v <= 0:
                continue
            h = v * scale
            y0 = ex_pos[o][0] - out_off[o]
            y1 = im_pos[t][0] - in_off[t]
            out_off[o] += h
            in_off[t] += h
            if h > 0.004:                        # skip invisible slivers (drawn as node mass)
                ribbon(ax, x0n + nw, x1n, y0, y1, h, COLOR.get(o, FALLBACK))

    for c, (y, h) in ex_pos.items():
        ax.add_patch(plt.Rectangle((x0n, y - h), nw, h, facecolor=COLOR.get(c, FALLBACK),
                                   edgecolor=SURFACE, lw=0.5, zorder=3))
        ax.text(x0n - 0.008, y - h / 2, f"{c}  {ex_tot[c]:.1f}", ha="right", va="center",
                fontsize=9, color=INK2)
    for c, (y, h) in im_pos.items():
        ax.add_patch(plt.Rectangle((x1n, y - h), nw, h, facecolor=COLOR.get(c, FALLBACK),
                                   edgecolor=SURFACE, lw=0.5, zorder=3))
        ax.text(x1n + nw + 0.008, y - h / 2, f"{c}  {im_tot[c]:.1f}", ha="left", va="center",
                fontsize=9, color=INK2)

    ax.text(x0n, 1.025, "exporters ($B)", ha="left", fontsize=9, color=MUTED)
    ax.text(x1n + nw, 1.025, "importers ($B)", ha="right", fontsize=9, color=MUTED)
    ax.set_title(f"{title}\n{codes_txt} — world trade ${total:.0f}B ({YEAR})",
                 fontsize=12, color=INK, pad=14)
    ax.text(0.5, -0.045, "Ribbon colour = exporter. Within-chart widths share one scale; "
            "scales differ between stage charts. Sources: docs/tech-ai-taxonomy.md codes; "
            "Atlas HS2012 bilateral / monthly panel.", ha="center", fontsize=7.5, color=MUTED)
    out = OUT_DIR / f"supply_chain_{fname}_{YEAR}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}  (${total:.0f}B)")


def varimax(L, iters=200, tol=1e-8):
    p, k = L.shape
    O = np.eye(k)
    var = 0.0
    for _ in range(iters):
        B = L @ O
        U, sv, Vt = np.linalg.svd(L.T @ (B**3 - B @ np.diag((B**2).sum(0)) / p))
        O = U @ Vt
        if sv.sum() < var * (1 + tol):
            break
        var = sv.sum()
    return O


def hubs_from_panel(code):
    """Hub inputs from the era-anchored TV-MFM: 2024 means of monthly loadings/F."""
    s = json.load(open(cfg.RESULTS_DIR / "mfm" / "tvmfm" / "by_country" / code / "stats.json"))
    months = [p for p in s["periods"] if p.startswith(YEAR)]
    countries = s["countries"]
    R = np.mean([np.array(s["R_by_period"][m]) for m in months], axis=0).clip(min=0)
    C = np.mean([np.array(s["C_by_period"][m]) for m in months], axis=0).clip(min=0)
    F = np.mean([np.array(s["F_by_period"][m]) for m in months], axis=0)
    return countries, R, C, F, "era-anchored TV-MFM, 2024 monthly means"


def hubs_from_json(baskets, k=4):
    """Hub inputs for upstream stages: constant-loading MFM (k=r=4, $B levels,
    varimax) on the ANNUAL bilateral matrices 2020-2024 from the dashboard data --
    same estimator as results/mfm/annual, no monthly panel exists upstream."""
    d = json.load(open(cfg.ROOT / "dashboard" / "public" / "data" / "techai_bilateral.json"))
    flows = {}
    for b in baskets:
        for o, dests in d["value"].get(b, {}).items():
            for t, yrs in dests.items():
                for y, v in yrs.items():
                    if 2020 <= int(y) <= 2024 and o != t and v:
                        flows[(int(y), o, t)] = flows.get((int(y), o, t), 0.0) + v
    countries = sorted({o for (_, o, _) in flows} | {t for (_, _, t) in flows})
    idx = {c: i for i, c in enumerate(countries)}
    years = sorted({y for (y, _, _) in flows})
    Y = np.zeros((len(years), len(countries), len(countries)))
    for (y, o, t), v in flows.items():
        Y[years.index(y), idx[o], idx[t]] = v
    p = q = len(countries)
    M_R = np.einsum("sij,skj->ik", Y, Y)
    M_C = np.einsum("sji,sjk->ik", Y, Y)
    _, vr = np.linalg.eigh(M_R)
    _, vc = np.linalg.eigh(M_C)
    R = vr[:, -k:][:, ::-1] * np.sqrt(p)
    C = vc[:, -k:][:, ::-1] * np.sqrt(q)
    R, C = R @ varimax(R), C @ varimax(C)
    for L in (R, C):                              # dominant member positive
        for j in range(k):
            if L[np.abs(L[:, j]).argmax(), j] < 0:
                L[:, j] *= -1
    F = R.T @ Y[-1] @ C / (p * q)                 # 2024 factor matrix
    return countries, R.clip(min=0), C.clip(min=0), F, \
        "constant-loading annual MFM 2020-24 (no monthly panel upstream)"


def draw_hub_chart(fname, title, code_or_baskets, kind):
    """Four-column chart: exporters -> export hubs -> import hubs -> importers.
    Hub-pair dollars are the model-implied decomposition renormalized to the
    year's actual total -- an interpretation layer, not raw data."""
    if kind == "panel":
        countries, R, C, F, src = hubs_from_panel(code_or_baskets)
        total_actual = sum(flows_panel(code_or_baskets).values())
    else:
        countries, R, C, F, src = hubs_from_json(code_or_baskets)
        total_actual = sum(flows_json(code_or_baskets).values())
    K = R.shape[1]
    hubR = [f"{countries[int(R[:, a].argmax())]}-led" for a in range(K)]
    hubC = [f"{countries[int(C[:, b].argmax())]}-led" for b in range(K)]
    hub_color_R = [COLOR.get(countries[int(R[:, a].argmax())], FALLBACK) for a in range(K)]
    hub_color_C = [COLOR.get(countries[int(C[:, b].argmax())], FALLBACK) for b in range(K)]

    Rsum, Csum = R.sum(0), C.sum(0)
    V = np.outer(Rsum, Csum) * F                 # hub-pair fitted totals
    V = V.clip(min=0)
    V *= total_actual / V.sum()
    E = (R / np.where(Rsum > 0, Rsum, 1)) [:, :] * V.sum(1)   # exporter -> exp hub
    I = (C / np.where(Csum > 0, Csum, 1)) [:, :] * V.sum(0)   # imp hub -> importer

    def fold_side(M):
        tot = pd.Series(M.sum(1), index=countries)
        keep = set(tot.sort_values(ascending=False).head(TOP_N).index)
        rows, names = {}, []
        for i, c in enumerate(countries):
            key = c if c in keep else "Other"
            rows[key] = rows.get(key, np.zeros(M.shape[1])) + M[i]
        names = [c for c in tot.sort_values(ascending=False).index if c in keep] + ["Other"]
        return names, rows

    ex_names, ex_rows = fold_side(E)
    im_names, im_rows = fold_side(I)

    pad = 0.02
    scale = (1.0 - pad * (max(len(ex_names), K) - 1)) / total_actual
    xs = [0.14, 0.42, 0.58, 0.86]
    nw = 0.012

    def stack(names, sizes, x_idx):
        pos, y = {}, 1.0
        for n in names:
            h = sizes[n] * scale
            pos[n] = (y, h)
            y -= h + pad
        return pos

    ex_pos = stack(ex_names, {n: ex_rows[n].sum() for n in ex_names}, 0)
    hubR_pos = stack(range(K), {a: V.sum(1)[a] for a in range(K)}, 1)
    hubC_pos = stack(range(K), {b: V.sum(0)[b] for b in range(K)}, 2)
    im_pos = stack(im_names, {n: im_rows[n].sum() for n in im_names}, 3)

    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.06, 1.06)
    ax.axis("off")
    fig.patch.set_facecolor(SURFACE)

    def band(gap, src_pos, dst_pos, links, color_of):
        out_off = {k: 0.0 for k in src_pos}
        in_off = {k: 0.0 for k in dst_pos}
        for sk, dk, v in links:
            h = v * scale
            if h <= 0:
                continue
            y0 = src_pos[sk][0] - out_off[sk]
            y1 = dst_pos[dk][0] - in_off[dk]
            out_off[sk] += h
            in_off[dk] += h
            if h > 0.004:
                ribbon(ax, xs[gap] + nw, xs[gap + 1], y0, y1, h, color_of(sk, dk))

    band(0, ex_pos, hubR_pos,
         [(n, a, ex_rows[n][a]) for n in ex_names for a in range(K)],
         lambda n, a: COLOR.get(n, FALLBACK))
    band(1, hubR_pos, hubC_pos,
         [(a, b, V[a, b]) for a in range(K) for b in range(K)],
         lambda a, b: hub_color_R[a])
    band(2, hubC_pos, im_pos,
         [(b, n, im_rows[n][b]) for b in range(K) for n in im_names],
         lambda b, n: hub_color_C[b])

    for pos, names, colors, side in ((ex_pos, ex_names, None, "L"),
                                     (im_pos, im_names, None, "R")):
        for n in names:
            y, h = pos[n]
            ax.add_patch(plt.Rectangle((xs[0] if side == "L" else xs[3], y - h), nw, h,
                                       facecolor=COLOR.get(n, FALLBACK),
                                       edgecolor=SURFACE, lw=0.5, zorder=3))
            x = xs[0] - 0.008 if side == "L" else xs[3] + nw + 0.008
            tot = (ex_rows if side == "L" else im_rows)[n].sum()
            ax.text(x, y - h / 2, f"{n}  {tot:.1f}", ha="right" if side == "L" else "left",
                    va="center", fontsize=9, color=INK2)
    for pos, labels, colors, x in ((hubR_pos, hubR, hub_color_R, xs[1]),
                                   (hubC_pos, hubC, hub_color_C, xs[2])):
        for k, (y, h) in pos.items():
            ax.add_patch(plt.Rectangle((x, y - h), nw, h, facecolor=colors[k],
                                       edgecolor=SURFACE, lw=0.5, zorder=3))
            if h > 0.015:
                ax.text(x + nw / 2, y + 0.006, labels[k], ha="center", va="bottom",
                        fontsize=8, color=INK2)

    for x, lab in ((xs[0], "exporters ($B)"), (xs[1] + nw / 2, "export hubs"),
                   (xs[2] + nw / 2, "import hubs"), (xs[3] + nw, "importers ($B)")):
        ax.text(x, 1.045, lab, ha="center", fontsize=9, color=MUTED)
    ax.set_title(f"{title} — through the factor model's hubs ({YEAR})\n"
                 f"country -> hub attribution from loadings; hub-to-hub = F; "
                 f"total ${total_actual:.0f}B", fontsize=11, color=INK, pad=16)
    ax.text(0.5, -0.055, f"Model-implied decomposition ({src}; negative loadings "
            "clipped; renormalized to actual total). Hub named by its dominant member.",
            ha="center", fontsize=7.5, color=MUTED)
    out = OUT_DIR / f"supply_chain_{fname}_hubs_{YEAR}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}")


def draw_overview(stage_flows, MODE="dollar"):
    """Multi-column chain: checkpoint columns, one stage per gap. ONE common dollar
    scale across all stages, so band widths are nominally comparable everywhere --
    the chain visibly amplifies from $13B of raw materials to $926B of chips."""
    TOPG = 5
    H = 0.82
    folded = []
    for flows in stage_flows:
        ex = pd.Series(dtype=float)
        im = pd.Series(dtype=float)
        for (o, t), v in flows.items():
            ex[o] = ex.get(o, 0.0) + v
            im[t] = im.get(t, 0.0) + v
        ko = set(ex.sort_values(ascending=False).head(TOPG).index)
        kt = set(im.sort_values(ascending=False).head(TOPG).index)
        f = {}
        for (o, t), v in flows.items():
            key = (o if o in ko else "Other", t if t in kt else "Other")
            f[key] = f.get(key, 0.0) + v
        folded.append(f)

    n_cols = len(folded) + 1
    # global stacking order by total involvement, Other last
    inv = pd.Series(dtype=float)
    for f in folded:
        for (o, t), v in f.items():
            inv[o] = inv.get(o, 0.0) + v
            inv[t] = inv.get(t, 0.0) + v
    order = [c for c in inv.sort_values(ascending=False).index if c != "Other"] + ["Other"]

    totals = [sum(f.values()) for f in folded]
    if MODE == "dollar":            # one common $ scale: widths nominal everywhere
        scales = [H / max(totals)] * len(folded)
    elif MODE == "log":             # column height ~ log10($B): compromise
        heights = [H * np.log10(t) / np.log10(max(totals)) for t in totals]
        scales = [h / t for h, t in zip(heights, totals)]
    else:                           # normalized: every stage full height
        scales = [H / t for t in totals]
    pad = 0.008 if MODE == "dollar" else 0.012

    def col_nodes(c):
        out_v, in_v = {}, {}
        if c < len(folded):
            for (o, t), v in folded[c].items():
                out_v[o] = out_v.get(o, 0.0) + v * scales[c]
        if c > 0:
            for (o, t), v in folded[c - 1].items():
                in_v[t] = in_v.get(t, 0.0) + v * scales[c - 1]
        names = [n for n in order if n in out_v or n in in_v]
        return {n: max(out_v.get(n, 0.0), in_v.get(n, 0.0)) for n in names}

    node_pos = []
    for c in range(n_cols):
        sizes = col_nodes(c)
        total_h = sum(sizes.values()) + pad * (len(sizes) - 1)
        y = 0.5 + total_h / 2
        pos = {}
        for n in order:
            if n not in sizes:
                continue
            pos[n] = (y, sizes[n])
            y -= sizes[n] + pad
        node_pos.append(pos)

    xs = np.linspace(0.03, 0.97, n_cols)
    nw = 0.007
    fig, ax = plt.subplots(figsize=(22, 9))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.09, 1.20)
    ax.axis("off")
    fig.patch.set_facecolor(SURFACE)

    for g, f in enumerate(folded):
        out_off = {n: 0.0 for n in node_pos[g]}
        in_off = {n: 0.0 for n in node_pos[g + 1]}
        for o in order:
            for t in order:
                v = f.get((o, t), 0.0)
                if v <= 0:
                    continue
                h = v * scales[g]
                y0 = node_pos[g][o][0] - out_off[o]
                y1 = node_pos[g + 1][t][0] - in_off[t]
                out_off[o] += h
                in_off[t] += h
                if h > 0.0035:
                    ribbon(ax, xs[g] + nw, xs[g + 1], y0, y1, h, COLOR.get(o, FALLBACK))

    for c in range(n_cols):
        for n, (y, h) in node_pos[c].items():
            ax.add_patch(plt.Rectangle((xs[c], y - h), nw, h,
                                       facecolor=COLOR.get(n, FALLBACK),
                                       edgecolor=SURFACE, lw=0.4, zorder=3))
            if h > 0.03:
                ax.text(xs[c] + nw / 2, y + 0.008, n, ha="center", va="bottom",
                        fontsize=7.5, color=INK2, zorder=4)

    for g, ((_, title, codes_txt, _), f) in enumerate(zip(STAGES, folded)):
        xm = (xs[g] + xs[g + 1] + nw) / 2
        short = title.split("— ")[1]
        yb = 1.16 if g % 2 == 0 else 1.075     # stagger captions to avoid collisions
        ax.text(xm, yb, short, ha="center", fontsize=9.5, color=INK, weight="bold")
        ax.text(xm, yb - 0.032, f"${sum(f.values()):.0f}B", ha="center", fontsize=9,
                color=INK2)

    scale_note = {"dollar": "one dollar scale — band width nominally comparable everywhere",
                  "log": "column height ~ log10 of stage total — a compromise scale",
                  "normalized": "each stage normalized to full height — shares only"}[MODE]
    fig.suptitle("The AI-compute supply chain, 2024 — eight stages of bilateral trade "
                 f"({scale_note})", fontsize=13, color=INK, y=0.99)
    ax.text(0.5, -0.08, "Ribbon colour = exporting country; each column is a checkpoint "
            "(country sells the right-hand stage, buys the left-hand stage). Smallest "
            "corridors not drawn (see per-stage charts for detail). No cross-stage "
            "absorption implied. Sources: docs/tech-ai-taxonomy.md codes; Atlas HS2012 "
            "bilateral / monthly panel.", ha="center", fontsize=8, color=MUTED)
    out = OUT_DIR / f"supply_chain_overview_{MODE}_{YEAR}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    all_flows = []
    for fname, title, codes_txt, (kind, arg) in STAGES:
        flows = flows_json(arg) if kind == "json" else flows_panel(arg)
        all_flows.append(flows)
        draw_stage(fname, title, codes_txt, flows)
        draw_hub_chart(fname, title, arg, kind)
    for mode in ("dollar", "log", "normalized"):
        draw_overview(all_flows, mode)


if __name__ == "__main__":
    main()
