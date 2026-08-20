"""One-page schematic of the matrix factor model, in plain terms.

Shows the basic structure: each month's country-to-country trade table is
summarized by three smaller pieces -- which countries export alike, how many
dollars flow between export and import hubs (a small table), and which countries
import alike. Written generically: it applies to the static per-year model of
Section 2 and to the rolling-window version of Section 3 alike.

Output: exports/mfm_schematic.png (+ .pdf, vector) -- used by the chart pack.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
BLUE, GREEN, ORANGE = "#2a78d6", "#008300", "#eb6834"


def grid(ax, x, y, w, h, nx, ny, ec, fc, shade):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.6, zorder=2))
    for i in range(1, nx):
        ax.plot([x + w * i / nx] * 2, [y, y + h], color=ec, lw=0.7, alpha=0.35, zorder=3)
    for j in range(1, ny):
        ax.plot([x, x + w], [y + h * j / ny] * 2, color=ec, lw=0.7, alpha=0.35, zorder=3)
    rng = np.random.default_rng(shade)
    for i in range(nx):
        for j in range(ny):
            if rng.random() < 0.35:
                ax.add_patch(Rectangle((x + w * i / nx, y + h * j / ny),
                                       w / nx, h / ny, fc=ec, alpha=0.18,
                                       ec="none", zorder=2.5))


def block_labels(ax, cx, title, sub, color, title_y, sub_y):
    ax.text(cx, title_y, title, ha="center", va="bottom", fontsize=10.5,
            weight="bold", color=color)
    ax.text(cx, sub_y, sub, ha="center", va="bottom", fontsize=8.2, color=INK2)


def main():
    fig, ax = plt.subplots(figsize=(13.5, 6.4))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 6.4)
    ax.set_aspect("equal")
    ax.axis("off")

    # the full trade table for one period
    grid(ax, 0.5, 1.4, 3.0, 3.0, 10, 10, INK2, "#f1f1ee", shade=7)
    block_labels(ax, 2.0, "one period of trade",
                 "N exporters x N importers", INK, 4.95, 4.55)
    ax.text(2.0, 1.12, "N x N numbers", ha="center", fontsize=8.5, color=MUTED)

    ax.text(4.05, 2.9, "$\\approx$", fontsize=26, ha="center", va="center", color=INK)

    # exporter groups (tall thin)
    grid(ax, 4.6, 1.4, 1.15, 3.0, 4, 10, BLUE, "#eef3fb", shade=3)
    block_labels(ax, 5.17, "who exports alike",
                 "N countries, K export hubs", BLUE, 4.95, 4.55)
    ax.text(5.17, 1.12, "who belongs where", ha="center", fontsize=8.5, color=MUTED)

    ax.text(6.15, 2.9, "$\\times$", fontsize=20, ha="center", va="center", color=INK)

    # group-to-group dollars (small square) -- labels BELOW to avoid collisions
    grid(ax, 6.6, 2.32, 1.15, 1.15, 4, 4, GREEN, "#e8f5ee", shade=5)
    ax.text(7.17, 2.02, "dollars between hubs", ha="center", va="top",
            fontsize=10.5, weight="bold", color=GREEN)
    ax.text(7.17, 1.68, "K x M: export hub to import hub",
            ha="center", va="top", fontsize=8.2, color=INK2)
    ax.text(7.17, 1.34, "the compressed picture", ha="center", va="top",
            fontsize=8.5, color=MUTED)

    ax.text(8.2, 2.9, "$\\times$", fontsize=20, ha="center", va="center", color=INK)

    # importer groups (short wide)
    grid(ax, 8.65, 2.9, 3.0, 1.15, 10, 4, ORANGE, "#fdf1e7", shade=9)
    block_labels(ax, 10.15, "who imports alike",
                 "M import hubs over N countries", ORANGE, 4.95, 4.55)
    ax.text(10.15, 2.6, "who belongs where", ha="center", fontsize=8.5, color=MUTED)

    ax.text(6.75, 5.9, "How the factor model summarizes the trade data",
            ha="center", va="top", fontsize=15, weight="bold", color=INK)
    ax.text(6.75, 0.55,
            "One period of country-to-country flows is compressed into: hubs of exporters that move together,\n"
            "hubs of importers, and a small table of dollars between the hubs. Estimated on a single year the hub\n"
            "memberships are fixed (Section 2); estimated on a rolling window they can move, and a shift in them\n"
            "is what the model reports as a structural break (Section 3).",
            ha="center", va="top", fontsize=9.2, color=MUTED)

    out = cfg.ROOT / "exports" / "mfm_schematic.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.2, facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.2, facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out} (+ .pdf)")


if __name__ == "__main__":
    main()
