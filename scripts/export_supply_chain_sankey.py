"""Supply-chain flow charts: one bilateral 'flow of funds' diagram per chain stage.

One PNG per stage (equipment & inputs -> chips -> parts/modules 847330 ->
baseboards 847180 -> servers 847150), each showing 2024 exports from the top
exporting COUNTRIES (left) to the top importing COUNTRIES (right), ribbon width
proportional to dollars, country colours consistent across all charts. Within a
chart widths share one scale; ACROSS charts scales differ (totals differ 10x) --
each title carries the stage total.

Stage/code definitions per docs/data.md (OECD value chain + Fed
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

# China and Hong Kong are merged into one entity CHK in ALL charts (intra-bloc
# flows excluded); USA and Mexico stay separate.
BLOC = {"CHN": "CHK", "HKG": "CHK"}

# consistent country colours -- one hue family per major country so none collide
# (CHK red, USA blue, TWN green, KOR amber, JPN violet, MEX orange,
#  NLD brown, DEU olive, SGP cyan, MYS crimson, VNM lime, THA blue-gray)
COLOR = {"CHK": "#d7191c", "USA": "#2a78d6", "TWN": "#00a878", "KOR": "#eda100",
         "JPN": "#7b3fbf", "HKG": "#f06ba8", "CHN": "#d7191c", "MEX": "#f4692e",
         "NLD": "#8c510a", "DEU": "#708238", "SGP": "#17becf", "MYS": "#c2185b",
         "VNM": "#84bd00", "THA": "#607d8b", "IRL": "#bdb76b", "Other": "#b5b3ac"}
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


def apply_bloc(flows):
    out = {}
    for (o, t), v in flows.items():
        o2, t2 = BLOC.get(o, o), BLOC.get(t, t)
        if o2 != t2:
            out[(o2, t2)] = out.get((o2, t2), 0.0) + v
    return out


def flows_json(baskets):
    d = json.load(open(cfg.ROOT / "dashboard" / "public" / "data" / "techai_bilateral.json"))
    agg = {}
    for b in baskets:
        for o, dests in d["value"].get(b, {}).items():
            for t, yrs in dests.items():
                v = yrs.get(YEAR)
                if v and o != t:
                    agg[(o, t)] = agg.get((o, t), 0.0) + v
    return apply_bloc(agg)


def flows_panel(code, year=YEAR):
    p = pd.read_parquet(cfg.DATA_DIR / "derived" / "panel_semi_monthly.parquet")
    p = p[(p.code == code) & (p.period.str[:4] == year)]
    g = p.groupby(["exporter", "importer"]).value.sum() / 1e9
    return apply_bloc({k: float(v) for k, v in g.items()})


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
    # thin ribbons get near-full opacity and a minimum visual thickness so small
    # but real flows (e.g. Japan's wafer exports) stay visible
    h_draw = max(h, 0.0022)
    alpha = 0.85 if h < 0.008 else 0.55
    cx = (x1 - x0) * 0.42
    verts = [(x0, y0_top), (x0 + cx, y0_top), (x1 - cx, y1_top), (x1, y1_top),
             (x1, y1_top - h_draw), (x1 - cx, y1_top - h_draw),
             (x0 + cx, y0_top - h_draw), (x0, y0_top - h_draw), (x0, y0_top)]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=color,
                           edgecolor="none", alpha=alpha, zorder=1))


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


def hubs_from_panel(code, year=YEAR):
    """Hub inputs from the era-anchored TV-MFM (China+HKG bloc variant): 2024 means
    of monthly loadings/F."""
    s = json.load(open(cfg.RESULTS_DIR / "mfm" / "tvmfm" / "chn_hkg_bloc" / code / "stats.json"))
    months = [p for p in s["periods"] if p.startswith(year)]
    countries = s["countries"]
    R = np.mean([np.array(s["R_by_period"][m]) for m in months], axis=0).clip(min=0)
    C = np.mean([np.array(s["C_by_period"][m]) for m in months], axis=0).clip(min=0)
    F = np.mean([np.array(s["F_by_period"][m]) for m in months], axis=0)
    return countries, R, C, F, f"era-anchored TV-MFM, {year} monthly means"


def nnf_rotate(L, restarts=6, rng=np.random.default_rng(11)):
    """Rotate to the nonnegativity-identified basis: minimize negative-mass share
    over orthogonal rotations + column signs, warm-started from varimax (shown to
    be ~the optimum; see docs/notes/nonneg-rotation-experiment.md)."""
    from scipy.linalg import expm
    from scipy.optimize import minimize
    k = L.shape[1]
    iu = np.triu_indices(k, 1)

    def sign_fix(B):
        B = B.copy()
        for j in range(B.shape[1]):
            if (np.minimum(B[:, j], 0)**2).sum() > (np.minimum(-B[:, j], 0)**2).sum():
                B[:, j] *= -1
        return B

    def negshare(B):
        B = sign_fix(B)
        return float((np.minimum(B, 0)**2).sum() / (B**2).sum())

    def M(th):
        S = np.zeros((k, k)); S[iu] = th
        return expm(S - S.T)

    L1 = L @ varimax(L)
    best = (negshare(L1), np.eye(k))
    n_par = len(iu[0])
    for th0 in [np.zeros(n_par)] + [rng.uniform(-.6, .6, n_par) for _ in range(restarts - 1)]:
        r = minimize(lambda th: negshare(L1 @ M(th)), th0, method="Nelder-Mead",
                     options={"maxiter": 2500, "fatol": 1e-10})
        if r.fun < best[0]:
            best = (r.fun, M(r.x))
    return sign_fix(L1 @ best[1])


def hubs_from_json(baskets, k=4, rotate=True):
    """Hub inputs for upstream stages: constant-loading MFM (k=r=4, $B levels,
    varimax) on the ANNUAL bilateral matrices 2020-2024 from the dashboard data --
    same estimator as results/mfm/annual, no monthly panel exists upstream."""
    d = json.load(open(cfg.ROOT / "dashboard" / "public" / "data" / "techai_bilateral.json"))
    flows = {}
    for b in baskets:
        for o, dests in d["value"].get(b, {}).items():
            for t, yrs in dests.items():
                for y, v in yrs.items():
                    o2, t2 = BLOC.get(o, o), BLOC.get(t, t)
                    if 2020 <= int(y) <= 2024 and o2 != t2 and v:
                        flows[(int(y), o2, t2)] = flows.get((int(y), o2, t2), 0.0) + v
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
    note = "constant-loading annual MFM 2020-24 (no monthly panel upstream)"
    if rotate == "nnf":
        R, C = nnf_rotate(R), nnf_rotate(C)
        note = "NONNEGATIVITY-IDENTIFIED basis (unique admissible bundle basis); " + note
    elif rotate:
        R, C = R @ varimax(R), C @ varimax(C)
    else:
        note = "UNROTATED spectral basis, hubs in descending eigenvalue order; " + note
    for L in (R, C):                              # dominant member positive
        for j in range(k):
            if L[np.abs(L[:, j]).argmax(), j] < 0:
                L[:, j] *= -1
    F = R.T @ Y[-1] @ C / (p * q)                 # 2024 factor matrix
    return countries, R.clip(min=0), C.clip(min=0), F, note


def hubs_from_panel_pooled(code, year=YEAR, rotate=True, k=4):
    """Constant-loading MFM pooled over the year's monthly matrices (panel codes),
    optionally without varimax -- the unrotated spectral basis."""
    pdf = pd.read_parquet(cfg.DATA_DIR / "derived" / "panel_semi_monthly.parquet")
    pdf = pdf[(pdf.code == code) & (pdf.period.str[:4] == year)]
    flows = {}
    for (per, o, t), v in pdf.groupby(["period", "exporter", "importer"]).value.sum().items():
        o2, t2 = BLOC.get(o, o), BLOC.get(t, t)
        if o2 != t2:
            flows[(per, o2, t2)] = flows.get((per, o2, t2), 0.0) + float(v) / 1e9
    countries = sorted({o for (_, o, _) in flows} | {t for (_, _, t) in flows})
    idx = {c: i for i, c in enumerate(countries)}
    periods = sorted({per for (per, _, _) in flows})
    Y = np.zeros((len(periods), len(countries), len(countries)))
    for (per, o, t), v in flows.items():
        Y[periods.index(per), idx[o], idx[t]] = v
    p_ = q_ = len(countries)
    M_R = np.einsum("sij,skj->ik", Y, Y)
    M_C = np.einsum("sji,sjk->ik", Y, Y)
    _, vr = np.linalg.eigh(M_R)
    _, vc = np.linalg.eigh(M_C)
    R = vr[:, -k:][:, ::-1] * np.sqrt(p_)
    C = vc[:, -k:][:, ::-1] * np.sqrt(q_)
    note = f"pooled {year} monthly MFM"
    if rotate == "nnf":
        R, C = nnf_rotate(R), nnf_rotate(C)
        note = "NONNEGATIVITY-IDENTIFIED basis (unique admissible bundle basis); " + note
    elif rotate:
        R, C = R @ varimax(R), C @ varimax(C)
    else:
        note = "UNROTATED spectral basis, hubs in descending eigenvalue order; " + note
    for L in (R, C):
        for j in range(k):
            if L[np.abs(L[:, j]).argmax(), j] < 0:
                L[:, j] *= -1
    F = np.mean([R.T @ Y[t] @ C / (p_ * q_) for t in range(len(periods))], axis=0)
    return countries, R.clip(min=0), C.clip(min=0), F, note


def draw_hub_chart(fname, title, codes_txt, code_or_baskets, kind, year=YEAR):
    """Four-column chart: exporters -> export hubs -> import hubs -> importers.
    Hub-pair dollars are the model-implied decomposition renormalized to the
    year's actual total -- an interpretation layer, not raw data."""
    if kind == "panel":
        countries, R, C, F, src = hubs_from_panel(code_or_baskets, year)
        total_actual = sum(flows_panel(code_or_baskets, year).values())
        data_src = "Comtrade+TDM monthly panel"
    elif kind == "panel_norot":
        countries, R, C, F, src = hubs_from_panel_pooled(code_or_baskets, year, rotate=False)
        total_actual = sum(flows_panel(code_or_baskets, year).values())
        data_src = "Comtrade+TDM monthly panel"
    elif kind == "panel_nnf":
        countries, R, C, F, src = hubs_from_panel_pooled(code_or_baskets, year, rotate="nnf")
        total_actual = sum(flows_panel(code_or_baskets, year).values())
        data_src = "Comtrade+TDM monthly panel"
    elif kind == "json_nnf":
        countries, R, C, F, src = hubs_from_json(code_or_baskets, rotate="nnf")
        total_actual = sum(flows_json(code_or_baskets).values())
        data_src = "Atlas HS2012 annual bilateral"
    elif kind == "json_norot":
        countries, R, C, F, src = hubs_from_json(code_or_baskets, rotate=False)
        total_actual = sum(flows_json(code_or_baskets).values())
        data_src = "Atlas HS2012 annual bilateral"
    else:
        countries, R, C, F, src = hubs_from_json(code_or_baskets)
        total_actual = sum(flows_json(code_or_baskets).values())
        data_src = "Atlas HS2012 annual bilateral"
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
    # rescale outer columns to ACTUAL country totals (model attribution can misstate
    # e.g. Mexico by 2x); hub columns keep model proportions, nodes absorb the gap
    fl = flows_panel(code_or_baskets, year) if kind.startswith("panel") else flows_json(code_or_baskets)
    act_ex, act_im = {}, {}
    for (o, t), v in fl.items():
        act_ex[o] = act_ex.get(o, 0.0) + v
        act_im[t] = act_im.get(t, 0.0) + v
    for i, c in enumerate(countries):
        rs = E[i].sum()
        if rs > 0:
            E[i] *= act_ex.get(c, 0.0) / rs
        cs = I[i].sum()
        if cs > 0:
            I[i] *= act_im.get(c, 0.0) / cs

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
            if h > 0.0012:
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
    ax.set_title(f"{title}  ({codes_txt})  — {year}\n"
                 f"through the factor model's hubs: country -> hub from loadings; "
                 f"hub-to-hub = F; total ${total_actual:.0f}B",
                 fontsize=11, color=INK, pad=16)
    ax.text(0.5, -0.055, f"Hub decomposition from the factor model ({src}); "
            f"outer columns rescaled to actual totals. CHK = China+HK. Data: {data_src}.",
            ha="center", fontsize=7.5, color=MUTED)
    sub = ("hubs_nnf" if fname.endswith("_nnf") else
           "hubs_spectral" if fname.endswith("_norot") else "hubs_varimax")
    (OUT_DIR / sub).mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / sub / f"supply_chain_{fname}_hubs_{year}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}")


def draw_chain_overview(input_stages, seq_stages, MODE="dollar", fold_min=10.0, draw_min=0.0, suffix=""):
    """Chain overview with correct topology: the four upstream input streams (raw
    materials, wafers, litho/optics, equipment) are PARALLEL, converging on the fab
    checkpoint; chips -> parts -> baseboards -> servers then run sequentially.
    MODE governs vertical scale: 'dollar' (one $ scale), 'log' (heights ~ log10 of
    flow-set total), 'normalized' (equal heights / full column per stage).
    Countries below FOLD_MIN ($B, side total) fold into 'Other' -- an absolute
    threshold, so a small stage (raw materials) may legitimately show no
    individual countries at chain scale."""
    FOLD_MIN = fold_min

    def fold(flows):
        ex = pd.Series(dtype=float)
        im = pd.Series(dtype=float)
        for (o, t), v in flows.items():
            ex[o] = ex.get(o, 0.0) + v
            im[t] = im.get(t, 0.0) + v
        # keep a country if it clears the absolute bar OR ~10% of its stage total,
        # so relatively-large players in small stages (TWN in wafers/equipment)
        # stay visible instead of folding into Other
        rel = 0.10 * sum(flows.values())
        ko = set(ex[(ex >= FOLD_MIN) | (ex >= rel)].index)
        kt = set(im[(im >= FOLD_MIN) | (im >= rel)].index)
        f = {}
        for (o, t), v in flows.items():
            key = (o if o in ko else "Other", t if t in kt else "Other")
            f[key] = f.get(key, 0.0) + v
        return f

    inputs = [(lab, fold(fl)) for lab, fl in input_stages]
    seqs = [(lab, fold(fl)) for lab, fl in seq_stages]
    in_totals = [sum(f.values()) for _, f in inputs]
    seq_totals = [sum(f.values()) for _, f in seqs]

    H = 0.86
    if MODE == "dollar":
        s_common = H / max(seq_totals)
        in_scales = [s_common] * len(inputs)
        seq_scales = [s_common] * len(seqs)
    elif MODE == "log":
        logs = [np.log10(t) for t in in_totals]
        blk = [H * l / sum(logs) * 0.92 for l in logs]
        in_scales = [b / t for b, t in zip(blk, in_totals)]
        seq_scales = [H * np.log10(t) / np.log10(max(seq_totals)) / t for t in seq_totals]
    else:
        in_scales = [H / len(inputs) * 0.92 / t for t in in_totals]
        seq_scales = [H / t for t in seq_totals]

    x_in = 0.045
    xs = np.linspace(0.30, 0.955, len(seqs) + 1)   # fab checkpoint .. final importers
    nw = 0.008
    pad = 0.010

    def order_of(f):
        tot = pd.Series(dtype=float)
        for (o, t), v in f.items():
            tot[o] = tot.get(o, 0.0) + v
        names = list(tot.sort_values(ascending=False).index)
        if "Other" in names:
            names.remove("Other")
            names.append("Other")
        return names

    def build_layout(in_scales, seq_scales):
        """Node layout for all columns; returns positions + tallest column span."""
        y_cursor = 0.5 + (sum(t * s for t, s in zip(in_totals, in_scales))
                          + 0.05 * (len(inputs) - 1)) / 2
        in_top = y_cursor
        in_group_pos = []                  # per group: (label, {exp: (ytop, h)}, scale)
        for (lab, f), sc in zip(inputs, in_scales):
            names = order_of(f)
            pos, y = {}, y_cursor
            for n_ in names:
                h = sum(v for (o, t), v in f.items() if o == n_) * sc
                pos[n_] = (y, h)
                y -= h + pad * 0.6
            in_group_pos.append((lab, pos, sc))
            y_cursor = y - 0.05 + pad * 0.6
        spans = [in_top - (y_cursor + 0.05)]

        fab_in = {}
        for (lab, f), sc in zip(inputs, in_scales):
            for (o, t), v in f.items():
                fab_in[t] = fab_in.get(t, 0.0) + v * sc
        fab_out = {}
        for (o, t), v in seqs[0][1].items():
            fab_out[o] = fab_out.get(o, 0.0) + v * seq_scales[0]
        fab_sz = {n: max(fab_in.get(n, 0.0), fab_out.get(n, 0.0)) for n in
                  set(fab_in) | set(fab_out)}
        fab_names = sorted(fab_sz, key=lambda n: (n == "Other", -fab_sz[n]))
        T = sum(fab_sz.values()) + pad * (len(fab_sz) - 1)
        spans.append(T)
        fab_pos, y = {}, 0.5 + T / 2
        for n_ in fab_names:
            fab_pos[n_] = (y, fab_sz[n_])
            y -= fab_sz[n_] + pad

        col_pos = [fab_pos]
        for g in range(1, len(seqs) + 1):
            out_v, in_v = {}, {}
            if g < len(seqs):
                for (o, t), v in seqs[g][1].items():
                    out_v[o] = out_v.get(o, 0.0) + v * seq_scales[g]
            for (o, t), v in seqs[g - 1][1].items():
                in_v[t] = in_v.get(t, 0.0) + v * seq_scales[g - 1]
            sz = {n: max(out_v.get(n, 0.0), in_v.get(n, 0.0))
                  for n in set(out_v) | set(in_v)}
            names = sorted(sz, key=lambda n: (n == "Other", -sz[n]))
            T = sum(sz.values()) + pad * (len(sz) - 1)
            spans.append(T)
            pos, y = {}, 0.5 + T / 2
            for n_ in names:
                pos[n_] = (y, sz[n_])
                y -= sz[n_] + pad
            col_pos.append(pos)
        return in_group_pos, col_pos, max(spans)

    in_group_pos, col_pos, span = build_layout(in_scales, seq_scales)
    if span > 0.96:                        # tallest column would clip: shrink to fit
        f = 0.96 / span
        in_scales = [s * f for s in in_scales]
        seq_scales = [s * f for s in seq_scales]
        in_group_pos, col_pos, span = build_layout(in_scales, seq_scales)
    fab_pos = col_pos[0]

    fig, ax = plt.subplots(figsize=(22, 10))
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.16, 1.14)
    ax.axis("off")
    fig.patch.set_facecolor(SURFACE)

    # input ribbons -> fab column (shared in-offsets, group by group)
    fab_in_off = {n: 0.0 for n in fab_pos}
    for (lab, f), (lab2, gpos, sc) in zip(inputs, in_group_pos):
        out_off = {n: 0.0 for n in gpos}
        for o in gpos:
            for t in fab_pos:
                v = f.get((o, t), 0.0)
                if v <= 0:
                    continue
                h = v * sc
                if v < draw_min * 0.4:
                    out_off[o] += h
                    fab_in_off[t] += h
                    continue
                y0 = gpos[o][0] - out_off[o]
                y1 = fab_pos[t][0] - fab_in_off[t]
                out_off[o] += h
                fab_in_off[t] += h
                if h > 0.0012:
                    ribbon(ax, x_in + nw, xs[0], y0, y1, h, COLOR.get(o, FALLBACK))

    # sequential ribbons
    for g, (lab, f) in enumerate(seqs):
        src, dst = col_pos[g], col_pos[g + 1]
        out_off = {n: 0.0 for n in src}
        in_off = {n: 0.0 for n in dst}
        for o in src:
            for t in dst:
                v = f.get((o, t), 0.0)
                if v <= 0:
                    continue
                h = v * seq_scales[g]
                if v < draw_min:
                    out_off[o] += h
                    in_off[t] += h
                    continue
                y0 = src[o][0] - out_off[o]
                y1 = dst[t][0] - in_off[t]
                out_off[o] += h
                in_off[t] += h
                if h > 0.0012:
                    ribbon(ax, xs[g] + nw, xs[g + 1], y0, y1, h, COLOR.get(o, FALLBACK))

    # nodes (+ country labels wherever there is room)
    for lab, gpos, sc in in_group_pos:
        for n_, (y, h) in gpos.items():
            ax.add_patch(plt.Rectangle((x_in, y - h), nw, h,
                                       facecolor=COLOR.get(n_, FALLBACK),
                                       edgecolor=SURFACE, lw=0.4, zorder=3))
            if h > 0.012:
                ax.text(x_in - 0.005, y - h / 2, n_, ha="right", va="center",
                        fontsize=7.5, color=INK2, zorder=4)
        top = max(y for y, h in gpos.values())
        ax.text(x_in, top + 0.012, lab, ha="left", fontsize=8.5, color=INK, weight="bold")
    for c, pos in enumerate(col_pos):
        for n_, (y, h) in pos.items():
            ax.add_patch(plt.Rectangle((xs[c], y - h), nw, h,
                                       facecolor=COLOR.get(n_, FALLBACK),
                                       edgecolor=SURFACE, lw=0.4, zorder=3))
            if h > 0.015:
                ax.text(xs[c] + nw / 2, y + 0.006, n_, ha="center", va="bottom",
                        fontsize=7, color=INK2, zorder=4)

    # captions
    ax.text((x_in + xs[0]) / 2, 1.10, "parallel inputs into fabs", ha="center",
            fontsize=10, color=INK, weight="bold")
    ax.text((x_in + xs[0]) / 2, 1.068,   # no '$' here: paired $ triggers mathtext
            "  |  ".join(f"{lab} {t:.0f}B" for (lab, _), t in zip(inputs, in_totals)),
            ha="center", fontsize=7.5, color=INK2)
    for g, ((lab, _), t) in enumerate(zip(seqs, seq_totals)):
        xm = (xs[g] + xs[g + 1] + nw) / 2
        yb = 1.10 if g % 2 == 0 else 1.045
        ax.text(xm, yb, lab, ha="center", fontsize=9.5, color=INK, weight="bold")
        ax.text(xm, yb - 0.032, f"${t:.0f}B", ha="center", fontsize=9, color=INK2)
    ax.text(xs[0] + nw / 2, -0.035, "fab countries", ha="center", fontsize=8.5, color=MUTED)
    ax.text((xs[1] + xs[2]) / 2, -0.035, "assembly countries", ha="center",
            fontsize=8.5, color=MUTED)

    # colour legend (consistent everywhere: CHN red, USA blue, ...)
    lx = 0.045
    for n_ in ["CHK", "USA", "TWN", "KOR", "JPN", "MEX", "NLD", "DEU",
               "SGP", "MYS", "VNM", "Other"]:
        ax.add_patch(plt.Rectangle((lx, -0.135), 0.010, 0.026,
                                   facecolor=COLOR.get(n_, FALLBACK), edgecolor="none"))
        ax.text(lx + 0.014, -0.122, n_, fontsize=8.5, color=INK2, va="center")
        lx += 0.062
    scale_note = {"dollar": "one dollar scale — band widths nominally comparable everywhere",
                  "log": "flow-set heights ~ log10 of totals — a compromise scale",
                  "normalized": "stages equalized — shares only"}[MODE]
    fig.suptitle("The AI-compute supply chain, 2024 — parallel inputs converge on the "
                 f"fabs; chips flow on to servers ({scale_note})",
                 fontsize=13, color=INK, y=0.985)
    ax.text(0.5, -0.155, "Ribbon colour = exporter; CHK = China+Hong Kong merged; "
            f"countries under {FOLD_MIN:.0f}B/side fold into Other. Sources: Atlas annual "
            "(stages 1-5), Comtrade+TDM monthly panel (compute stages).",
            ha="center", fontsize=8, color=MUTED)
    (OUT_DIR / "overviews").mkdir(exist_ok=True)
    out = OUT_DIR / "overviews" / f"supply_chain_overview_{MODE}{suffix}_{YEAR}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}")


def draw_network(stage_groups):
    """Country-node network graph: one node per country (all stages together), so an
    integrated assembler's full mix is visible at one node (Mexico: chips+parts in,
    servers out). Edges = bilateral flows >= EDGE_MIN, coloured by product stage,
    width ~ sqrt(dollars); node area ~ total involvement. Complements the staged
    flow charts, which cannot show in-country transformation."""
    from matplotlib.patches import FancyArrowPatch, Circle
    EDGE_MIN = 5.0
    POS = {"USA": (0.13, 0.56), "MEX": (0.10, 0.28), "DEU": (0.27, 0.86),
           "NLD": (0.41, 0.92), "JPN": (0.88, 0.84), "KOR": (0.79, 0.71),
           "TWN": (0.86, 0.50), "CHK": (0.64, 0.62), "VNM": (0.57, 0.40),
           "MYS": (0.73, 0.30), "SGP": (0.60, 0.20), "THA": (0.76, 0.14),
           "Other": (0.33, 0.12)}
    SCOL = {"fab inputs": "#898781", "chips": "#7b3fbf", "parts": "#2a78d6",
            "baseboards": "#00a878", "servers": "#eb6834"}

    def fold(fl):
        out = {}
        for (o, t), v in fl.items():
            o2 = o if o in POS else "Other"
            t2 = t if t in POS else "Other"
            if o2 != t2:
                out[(o2, t2)] = out.get((o2, t2), 0.0) + v
        return out

    groups = {lab: fold(fl) for lab, fl in stage_groups.items()}
    inv = {n: 0.0 for n in POS}
    for fl in groups.values():
        for (o, t), v in fl.items():
            inv[o] += v
            inv[t] += v

    fig, ax = plt.subplots(figsize=(13, 9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.axis("off")
    fig.patch.set_facecolor(SURFACE)

    # edges: big first so small stay visible on top; slight per-stage curvature so
    # parallel stage-flows between the same pair do not cover each other
    rads = {lab: r for lab, r in zip(groups, (-0.28, -0.14, 0.0, 0.14, 0.28))}
    edges = [(lab, o, t, v) for lab, fl in groups.items() for (o, t), v in fl.items()
             if v >= EDGE_MIN]
    for lab, o, t, v in sorted(edges, key=lambda e: -e[3]):
        (x0, y0), (x1, y1) = POS[o], POS[t]
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                     connectionstyle=f"arc3,rad={rads[lab]}",
                     arrowstyle="-|>", mutation_scale=9 + 1.1 * np.sqrt(v),
                     lw=0.55 * np.sqrt(v), color=SCOL[lab], alpha=0.5,
                     shrinkA=16, shrinkB=17, zorder=2))

    for n, (x, y) in POS.items():
        r = 0.012 + 0.0022 * np.sqrt(inv[n])
        ax.add_patch(Circle((x, y), r, facecolor="#3a3936", edgecolor=SURFACE,
                            lw=1.2, zorder=5))
        ax.text(x, y, n, ha="center", va="center", fontsize=8.5, color="#ffffff",
                zorder=6, weight="bold")
        ax.text(x, y - r - 0.016, f"{inv[n]:.0f}B", ha="center", fontsize=7,
                color=MUTED, zorder=6)

    lx = 0.03
    for lab, c in SCOL.items():
        ax.plot([lx, lx + 0.03], [0.995, 0.995], color=c, lw=4, alpha=0.7)
        ax.text(lx + 0.036, 0.995, lab, fontsize=8.5, color=INK2, va="center")
        lx += 0.045 + 0.0085 * len(lab)
    ax.set_title("The AI-compute supply chain as a country network, 2024 — "
                 "edges by product stage, width ~ $", fontsize=12.5, color=INK,
                 pad=18, loc="left")
    ax.text(0.99, 0.995, f"flows >= {EDGE_MIN:.0f}B; node label = total involvement; "
            "CHK = China+HK", ha="right", fontsize=7.5, color=MUTED)
    (OUT_DIR / "network").mkdir(exist_ok=True)
    out = OUT_DIR / "network" / f"supply_chain_network_{YEAR}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out}")


def main():
    OUT_DIR.mkdir(exist_ok=True)
    all_flows = []
    # Plain (2-column) per-stage charts retired: the rank-4 hub decomposition fits
    # at R^2 0.95-0.99, so the hub-routed versions carry the flows faithfully.
    for fname, title, codes_txt, (kind, arg) in STAGES:
        flows = flows_json(arg) if kind == "json" else flows_panel(arg)
        all_flows.append(flows)
        draw_hub_chart(fname, title, codes_txt, arg, kind)
        draw_hub_chart(fname + "_norot", title + " [unrotated]", codes_txt, arg,
                       "panel_norot" if kind == "panel" else "json_norot")
        draw_hub_chart(fname + "_nnf", title, codes_txt, arg,
                       "panel_nnf" if kind == "panel" else "json_nnf")
    input_stages = [("raw materials", all_flows[0]), ("wafers", all_flows[1]),
                    ("litho & optics", all_flows[2]), ("fab equipment", all_flows[3])]
    inter = {}
    for f in (all_flows[5], all_flows[6]):
        for k, v in f.items():
            inter[k] = inter.get(k, 0.0) + v
    seq_stages = [("chips", all_flows[4]),
                  ("intra-assembly trade (parts+baseboards)", inter),
                  ("AI servers", all_flows[7])]
    for mode in ("dollar", "normalized"):   # log retired: inflates small (Other-heavy) stages
        draw_chain_overview(input_stages, seq_stages, mode)
        draw_chain_overview(input_stages, seq_stages, mode,
                            fold_min=30.0, draw_min=8.0, suffix="_coarse")
    fab_inputs = {}
    for f in all_flows[:4]:
        for k, v in f.items():
            fab_inputs[k] = fab_inputs.get(k, 0.0) + v
    draw_network({"fab inputs": fab_inputs, "chips": all_flows[4],
                  "parts": all_flows[5], "baseboards": all_flows[6],
                  "servers": all_flows[7]})


if __name__ == "__main__":
    main()
