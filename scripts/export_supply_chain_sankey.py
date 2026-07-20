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

STAGES = [
    ("1_equipment", "Stage 1-3 — Fab equipment & inputs", "8486xx + optics, wafers, materials",
     ("json", ["equip", "raw", "foundry", "wafer", "photo"])),
    ("2_chips", "Stage 4 — Chips (logic, memory, discretes)", "8542xx, 8541xx, media",
     ("json", ["chips"])),
    ("3_parts", "Stage 5 — Parts & GPU modules", "HS 847330", ("panel", "847330")),
    ("4_baseboards", "Stage 6 — Baseboards / other units", "HS 847180", ("panel", "847180")),
    ("5_servers", "Stage 7 — Finished AI servers", "HS 847150", ("panel", "847150")),
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


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for fname, title, codes_txt, (kind, arg) in STAGES:
        flows = flows_json(arg) if kind == "json" else flows_panel(arg)
        draw_stage(fname, title, codes_txt, flows)


if __name__ == "__main__":
    main()
