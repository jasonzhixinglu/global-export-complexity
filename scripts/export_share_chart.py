"""Static export: global market share by PCI for CHN/DEU/JPN, comparing 2000/2012/2024.

Reproduces the dashboard's Explorer "Market share" stacked view — reads the same precomputed
curves the site plots (series.share[flow][level][iso][year] over meta.shareGrid, level = High) —
and renders three vertically stacked subpanels (one per year) on a shared axis so the years are
directly comparable.

The PCI axis is clipped to [-2, +2]: the extreme high-complexity tail (PCI > 2) is sparse and the
share estimate there is unstable, and its spike would otherwise inflate the shared y-scale. Sized
with large type / thick strokes so it stays legible when displayed small.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

DATA = os.path.join(os.path.dirname(__file__), "..", "dashboard", "public", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "exports")
os.makedirs(OUT, exist_ok=True)

COUNTRIES = ["CHN", "DEU", "JPN"]            # stacking order: bottom -> top
YEARS = [2000, 2012, 2024]                   # one subpanel each (top -> bottom)
FLOW, LEVEL = "export", "high"               # global EXPORT share, High smoothness (dashboard default)
XLIM = (-2.0, 2.0)                           # clip the sparse high-complexity tail
YSTEP = 0.20                                 # uniform 20% y-tick interval

# Dashboard palette (selection order CHN/DEU/JPN -> PALETTE[0..2]): blue / orange / green
COLOR = {"CHN": "#3b82f6", "DEU": "#f97316", "JPN": "#22c55e"}
NAME = {"CHN": "China", "DEU": "Germany", "JPN": "Japan"}

meta = json.load(open(os.path.join(DATA, "meta.json")))
series = json.load(open(os.path.join(DATA, "series.json")))
pci_full = np.array(meta["shareGrid"])
mask = (pci_full >= XLIM[0] - 1e-9) & (pci_full <= XLIM[1] + 1e-9)
pci = pci_full[mask]
share = series["share"][FLOW][LEVEL]

def curve(iso, year):
    return np.array(share[iso][str(year)], dtype=float)[mask]

# shared y-ceiling with breathing room (mirrors the dashboard's niceShareMax: smallest round
# step where the stacked peak fills <= 80% of the axis), computed over the clipped range.
STEPS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
peak = max(sum(curve(c, y) for c in COUNTRIES).max() for y in YEARS)
ceil = next((s for s in STEPS if peak <= 0.8 * s + 1e-9), 1.0)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 14,
    "axes.edgecolor": "#cbd5e1", "axes.linewidth": 1.0,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
fig, axes = plt.subplots(len(YEARS), 1, figsize=(6.4, 8.2), sharex=True, sharey=True)

for ax, year in zip(axes, YEARS):
    ys = [curve(c, year) for c in COUNTRIES]
    ax.stackplot(pci, *ys, colors=[COLOR[c] for c in COUNTRIES],
                 alpha=0.9, edgecolor="white", linewidth=0.8)
    ax.plot(pci, sum(ys), color="#334155", linewidth=1.0, alpha=0.5)   # crisp top edge
    ax.axvline(0, color="#94a3b8", linewidth=1.0, linestyle=(0, (4, 3)), zorder=0)

    ax.set_xlim(*XLIM)
    ax.set_ylim(0, ceil)
    ax.set_yticks(np.arange(0, ceil + 1e-9, YSTEP))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}" if v else "0"))
    ax.tick_params(labelsize=13)
    ax.grid(True, axis="y", color="#e2e8f0", linewidth=0.9)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.02, 0.9, str(year), transform=ax.transAxes,
            fontsize=20, fontweight="bold", color="#0f172a", va="top")

axes[-1].set_xlabel("Product Complexity Index (PCI)", fontsize=14, labelpad=4)
fig.text(0.015, 0.5, "Share of world exports at each PCI", va="center",
         rotation="vertical", fontsize=13, color="#334155")

handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[c], alpha=0.9) for c in COUNTRIES]
fig.legend(handles, [NAME[c] for c in COUNTRIES], loc="upper center",
           ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.975), fontsize=14)
fig.suptitle("Global market share by product complexity", x=0.5, y=0.998,
             fontsize=16, fontweight="bold", color="#0f172a")
fig.text(0.5, 0.012,
         "Source: Harvard Atlas of Economic Complexity (HS 1992). Stacked export share by PCI.",
         ha="center", fontsize=9, color="#64748b")

fig.subplots_adjust(left=0.135, right=0.965, top=0.925, bottom=0.105, hspace=0.14)
png = os.path.join(OUT, "market_share_pci_chn_deu_jpn.png")
pdf = os.path.join(OUT, "market_share_pci_chn_deu_jpn.pdf")
fig.savefig(png, dpi=200)
fig.savefig(pdf)
print(f"clipped PCI {XLIM} | peak stacked share {peak:.3f} -> y-ceiling {ceil:.0%}")
print("wrote", os.path.relpath(png), "and", os.path.relpath(pdf))
