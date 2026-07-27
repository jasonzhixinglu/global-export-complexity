"""Stylized topology of the AI-compute supply chain, with HS6 codes per node.

The simplified narrative shape (docs/data.md §1 "How stages combine"):
two parallel input branches — materials (raw -> wafers/chemicals) and tools
(optics -> equipment) — converge on chip fabrication; chips then run
sequentially through parts/GPU modules, baseboards, and AI servers.
Circle areas follow the log of 2024 world trade (illustrative). Edge styles
carry the combination rule: solid = consumed per unit of output, dashed =
capacity investment (leads output 6-12 months in fab countries).

Output: exports/chain_topology.png (+ .pdf, vector) — referenced from
docs/data.md, docs/supply-chain-narrative.md, and the chart pack.
"""
from __future__ import annotations
import sys
import textwrap
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as O

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
# color coding: materials branch pink, equipment branch orange, fabrication
# green, the three Fed AI-compute codes (the monthly-panel focus) blue
FILL = {"mat": "#fbe9f0", "tool": "#fdf1e7", "fab": "#e8f5ee", "down": "#dce8fb"}
EDGE = {"mat": "#e87ba4", "tool": "#eb6834", "fab": "#008300", "down": "#2a78d6"}

# 2024 world trade per node ($B, CHK basis; stages 1-5 Atlas, 6-8 audited panel)
VAL = {"raw": 13, "wafer": 25, "optic": 38, "equip": 244, "fab": 823,
       "parts": 146, "board": 101, "srv": 127}
_l = {k: np.log10(v) for k, v in VAL.items()}
# circle AREA proportional to log10(2024 value): r = rmax * sqrt(l / lmax)
RAD = {k: 0.165 * np.sqrt(_l[k] / max(_l.values())) for k in _l}

NODES = {
    # key: (cx, cy, kind, title, code list)
    "raw":   (0.150, 0.780, "mat", "Raw materials", sorted(O["Raw materials"])),
    "wafer": (0.600, 0.780, "mat", "Wafers & inputs", sorted(O["Wafer inputs"])),
    "optic": (0.150, 0.235, "tool", "Litho & optics", sorted(O["Foundry inputs"])),
    "equip": (0.615, 0.235, "tool", "Fab equipment", sorted(O["Manufacturing equipment"])),
    "fab":   (1.070, 0.500, "fab", "CHIP FABRICATION", sorted(O["Chips"])),
    "parts": (1.510, 0.760, "down", "Parts & GPU modules", ["847330"]),
    "board": (1.510, 0.255, "down", "Baseboards", ["847180"]),
    "srv":   (1.930, 0.500, "down", "AI servers", ["847150"]),
}

ARROWS = [  # (from, to, style, label[, label xy])
    ("raw", "wafer", "solid", ""),
    ("wafer", "fab", "solid", "consumed per unit\nof output", (0.735, 0.630)),
    ("optic", "equip", "solid", ""),
    ("equip", "fab", "dashed", "capacity investment;\nleads output 6-12m", (0.845, 0.245)),
    ("fab", "parts", "solid", ""),
    ("fab", "board", "solid", ""),
    ("parts", "board", "solid", ""),
    ("parts", "srv", "solid", ""),
    ("board", "srv", "solid", ""),
]


def main():
    fig, ax = plt.subplots(figsize=(17.0, 9.0))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(-0.02, 2.16)
    ax.set_ylim(-0.10, 1.06)
    ax.set_aspect("equal")
    ax.axis("off")

    for k, (cx, cy, kind, title, cl) in NODES.items():
        r = RAD[k]
        ax.add_patch(Circle((cx, cy), r, fc=FILL[kind], ec=EDGE[kind],
                            lw=1.8, zorder=2))
        # title and value sit ABOVE the circle; the code block is centered on
        # the circle and may overflow it (readable fixed-size text; the circle
        # is purely the size glyph)
        ax.text(cx, cy + r + 0.055, title, ha="center", va="center",
                fontsize=11.5, weight="bold", color=INK, zorder=3)
        ax.text(cx, cy + r + 0.018, f"${VAL[k]}B in 2024", ha="center",
                va="center", fontsize=9.0, color=INK2, zorder=3)
        ncol = 3 if len(cl) > 8 else (2 if len(cl) >= 4 else 1)
        rows = -(-len(cl) // ncol)
        fs = 7.2 if len(cl) >= 8 else 7.8
        dy = 0.037 if len(cl) >= 8 else 0.05
        xsp = 0.085 if ncol == 3 else 0.10
        for i, c in enumerate(cl):
            col, row = i // rows, i % rows
            x = cx + (col - (ncol - 1) / 2) * xsp
            y = cy + (rows - 1) / 2 * dy - row * dy
            ax.text(x, y, c, ha="center", va="center", fontsize=fs,
                    family="monospace", color=MUTED, zorder=3)

    for a, b, style, lab, *labxy in ARROWS:
        (x1, y1), (x2, y2) = NODES[a][:2], NODES[b][:2]
        if (a, b) == ("parts", "board"):
            x1 -= 0.10; x2 -= 0.10   # keep the vertical arrow clear of the labels
        v = np.array([x2 - x1, y2 - y1])
        u = v / np.linalg.norm(v)
        p1 = (x1 + u[0] * (RAD[a] + 0.012), y1 + u[1] * (RAD[a] + 0.012))
        p2 = (x2 - u[0] * (RAD[b] + 0.012), y2 - u[1] * (RAD[b] + 0.012))
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=22,
                                     lw=2.6 if style == "solid" else 2.3,
                                     ls="-" if style == "solid" else (0, (5, 3)),
                                     color=INK2, zorder=1,
                                     connectionstyle="arc3,rad=0.06"))
        if lab:
            if labxy:
                mx, my = labxy[0]
            else:
                n = np.array([-u[1], u[0]])
                mx = (p1[0] + p2[0]) / 2 + n[0] * 0.075
                my = (p1[1] + p2[1]) / 2 + n[1] * 0.075
            ax.text(mx, my, lab, ha="center", va="center", fontsize=8.6,
                    color=MUTED, zorder=3)

    ax.text(1.045, 0.055, "memory (KOR) joins logic at advanced packaging,\n"
            "largely inside Taiwan — invisible to customs data",
            ha="center", fontsize=8.6, color=MUTED)
    ax.text(1.04, 1.050, "The AI-compute supply chain — stylized shape, "
            "with the HS6 codes in each node",
            ha="center", va="top", fontsize=16, weight="bold", color=INK)
    foot = ("Two parallel input branches converge on fabrication; the output side is "
            "sequential. Circle areas follow the log of 2024 world trade (illustrative, "
            "so chips does not dwarf raw materials). The materials branch (pink) is "
            "consumed per unit of output; the equipment branch (orange) is capacity "
            "investment (solid vs dashed arrows mark the same distinction). "
            "Design/EDA/IP value enters as "
            "services, never as goods trade. The three AI-compute codes of the Fed basket -- the "
            "monthly panel's focus -- are highlighted blue. Some small niche inputs sit outside the 60 codes "
            "(laser sources, vacuum pumps and valves, ABF substrates -- see "
            "notes/firm-level-supply-chain-data.md). Codes: OECD semiconductor mapping + Fed "
            "AI-compute basket (docs/data.md §1).")
    ax.text(1.04, -0.040, "\n".join(textwrap.wrap(foot, 116)), ha="center",
            va="top", fontsize=8.8, color=MUTED)

    out = cfg.ROOT / "exports" / "chain_topology.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.25, facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out} (+ .pdf)")


if __name__ == "__main__":
    main()
