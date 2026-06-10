"""Static export: global market share by PCI for CHN/DEU/JPN, comparing 2000/2012/2024.

Reproduces the dashboard's Explorer "Market share" stacked view exactly — it reads the same
precomputed curves the site plots (series.share[flow][level][iso][year] over meta.shareGrid,
level = High, matching the dashboard's fixed smoothness) — and renders three vertically stacked
subpanels (one per year) sharing a common y-axis so the years are directly comparable.
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

# Dashboard palette (selection order CHN/DEU/JPN -> PALETTE[0..2]): blue / orange / green
COLOR = {"CHN": "#3b82f6", "DEU": "#f97316", "JPN": "#22c55e"}
NAME = {"CHN": "China", "DEU": "Germany", "JPN": "Japan"}

meta = json.load(open(os.path.join(DATA, "meta.json")))
series = json.load(open(os.path.join(DATA, "series.json")))
pci = np.array(meta["shareGrid"])
share = series["share"][FLOW][LEVEL]

def curve(iso, year):
    return np.array(share[iso][str(year)], dtype=float)

# common y-ceiling with breathing room (mirrors the dashboard's niceShareMax: smallest round
# step where the stacked peak fills <= 80% of the axis), so all three panels share one scale.
STEPS = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0]
peak = max(sum(curve(c, y) for c in COUNTRIES).max() for y in YEARS)
ceil = next((s for s in STEPS if peak <= 0.8 * s + 1e-9), 1.0)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#cbd5e1", "axes.linewidth": 0.8,
    "figure.facecolor": "white", "axes.facecolor": "white",
})
fig, axes = plt.subplots(len(YEARS), 1, figsize=(8.2, 10.5), sharex=True, sharey=True)

for ax, year in zip(axes, YEARS):
    ys = [curve(c, year) for c in COUNTRIES]
    ax.stackplot(pci, *ys, colors=[COLOR[c] for c in COUNTRIES],
                 alpha=0.88, edgecolor="white", linewidth=0.6)
    total = sum(ys)
    ax.plot(pci, total, color="#334155", linewidth=0.8, alpha=0.5)  # crisp top edge
    ax.axvline(0, color="#94a3b8", linewidth=0.8, linestyle=(0, (4, 3)), zorder=0)

    ax.set_xlim(pci[0], pci[-1])
    ax.set_ylim(0, ceil)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v*100:.0f}%"))
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}" if v else "0"))
    ax.grid(True, axis="y", color="#e2e8f0", linewidth=0.7)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.012, 0.93, str(year), transform=ax.transAxes,
            fontsize=15, fontweight="bold", color="#0f172a", va="top")

axes[-1].set_xlabel("Product Complexity Index (PCI)", fontsize=11, labelpad=8)
fig.text(0.022, 0.5, "Share of world exports at each PCI", va="center",
         rotation="vertical", fontsize=11, color="#334155")

# single legend up top
handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[c], alpha=0.88) for c in COUNTRIES]
fig.legend(handles, [NAME[c] for c in COUNTRIES], loc="upper center",
           ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.975), fontsize=11)
fig.suptitle("Global market share by product complexity", x=0.5, y=0.995,
             fontsize=15, fontweight="bold", color="#0f172a")
fig.text(0.5, 0.018,
         "Source: Harvard Atlas of Economic Complexity (HS 1992). Stacked export share by PCI, High smoothing.",
         ha="center", fontsize=8, color="#64748b")

fig.subplots_adjust(left=0.10, right=0.97, top=0.93, bottom=0.075, hspace=0.13)
png = os.path.join(OUT, "market_share_pci_chn_deu_jpn.png")
pdf = os.path.join(OUT, "market_share_pci_chn_deu_jpn.pdf")
fig.savefig(png, dpi=200)
fig.savefig(pdf)
print("peak stacked share:", round(peak, 4), "-> y-ceiling:", ceil)
print("wrote", os.path.relpath(png), "and", os.path.relpath(pdf))
