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
FILL = {"input": "#eef3fb", "fab": "#e8f5ee", "down": "#fdf1e7"}
EDGE = {"input": "#2a78d6", "fab": "#008300", "down": "#eb6834"}

# 2024 world trade per node ($B, CHK basis; stages 1-5 Atlas, 6-8 audited panel)
VAL = {"raw": 13, "wafer": 25, "optic": 38, "equip": 244, "fab": 823,
       "parts": 146, "board": 101, "srv": 127}
_l = {k: np.log10(v) for k, v in VAL.items()}
RAD = {k: 0.095 + 0.115 * _l[k] / max(_l.values()) for k in _l}
# dense nodes need room for their code block regardless of dollar size
for _k, _n in {"raw": 15, "optic": 8, "equip": 14}.items():
    RAD[_k] = max(RAD[_k], 0.150 if _n > 10 else 0.138)

NODES = {
    # key: (cx, cy, kind, title, code list)
    "raw":   (0.175, 0.780, "input", "Raw materials", sorted(O["Raw materials"])),
    "wafer": (0.530, 0.780, "input", "Wafers & inputs", sorted(O["Wafer inputs"])),
    "optic": (0.175, 0.235, "input", "Litho & optics", sorted(O["Foundry inputs"])),
    "equip": (0.530, 0.235, "input", "Fab equipment", sorted(O["Manufacturing equipment"])),
    "fab":   (1.000, 0.500, "fab", "CHIP FABRICATION", sorted(O["Chips"])),
    "parts": (1.430, 0.760, "down", "Parts & GPU modules", ["847330"]),
    "board": (1.430, 0.255, "down", "Baseboards", ["847180"]),
    "srv":   (1.830, 0.500, "down", "AI servers", ["847150"]),
}

ARROWS = [  # (from, to, style, label)
    ("raw", "wafer", "solid", ""),
    ("wafer", "fab", "solid", "consumed per unit\nof output"),
    ("optic", "equip", "solid", ""),
    ("equip", "fab", "dashed", "capacity investment;\nleads output 6-12m"),
    ("fab", "parts", "solid", ""),
    ("parts", "board", "solid", ""),
    ("parts", "srv", "solid", ""),
    ("board", "srv", "solid", ""),
]


def main():
    fig, ax = plt.subplots(figsize=(14.5, 7.6))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 2.0)
    ax.set_ylim(-0.10, 1.06)
    ax.set_aspect("equal")
    ax.axis("off")

    for k, (cx, cy, kind, title, cl) in NODES.items():
        r = RAD[k]
        ax.add_patch(Circle((cx, cy), r, fc=FILL[kind], ec=EDGE[kind],
                            lw=1.8, zorder=2))
        dense = len(cl) > 8
        ax.text(cx, cy + r * (0.72 if dense else 0.66), title, ha="center",
                va="center", fontsize=9.6, weight="bold", color=INK, zorder=3)
        ax.text(cx, cy + r * (0.52 if dense else 0.44), f"${VAL[k]}B in 2024",
                ha="center", va="center", fontsize=7.4, color=INK2, zorder=3)
        ncol = 3 if len(cl) > 8 else (2 if len(cl) >= 4 else 1)
        rows = -(-len(cl) // ncol)
        fs = 5.9 if len(cl) > 8 else 6.6
        dy = 0.038 if len(cl) > 8 else 0.05
        block_mid = cy - r * (0.20 if dense else 0.16)
        for i, c in enumerate(cl):
            col, row = i // rows, i % rows
            x = cx + (col - (ncol - 1) / 2) * (r * 0.56)
            y = block_mid + (rows - 1) / 2 * dy - row * dy
            ax.text(x, y, c, ha="center", va="center", fontsize=fs,
                    family="monospace", color=MUTED, zorder=3)

    for a, b, style, lab in ARROWS:
        (x1, y1), (x2, y2) = NODES[a][:2], NODES[b][:2]
        v = np.array([x2 - x1, y2 - y1])
        u = v / np.linalg.norm(v)
        p1 = (x1 + u[0] * (RAD[a] + 0.012), y1 + u[1] * (RAD[a] + 0.012))
        p2 = (x2 - u[0] * (RAD[b] + 0.012), y2 - u[1] * (RAD[b] + 0.012))
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=17,
                                     lw=2.1 if style == "solid" else 1.9,
                                     ls="-" if style == "solid" else (0, (5, 3)),
                                     color=INK2, zorder=1,
                                     connectionstyle="arc3,rad=0.06"))
        if lab:
            n = np.array([-u[1], u[0]])       # normal: offset the label off the arrow
            mx = (p1[0] + p2[0]) / 2 + n[0] * 0.075
            my = (p1[1] + p2[1]) / 2 + n[1] * 0.075
            ax.text(mx, my, lab, ha="center", va="center", fontsize=7.3,
                    color=MUTED, zorder=3)

    ax.text(1.0, 0.055, "memory (KOR) joins logic at advanced packaging,\n"
            "largely inside Taiwan — invisible to customs data",
            ha="center", fontsize=7.3, color=MUTED)
    ax.text(1.0, 1.050, "The AI-compute supply chain — stylized shape, "
            "with the HS6 codes in each node",
            ha="center", va="top", fontsize=13, weight="bold", color=INK)
    foot = ("Two parallel input branches converge on fabrication; the output side is "
            "sequential. Circle areas follow the log of 2024 world trade (illustrative, "
            "so chips does not dwarf raw materials). Solid arrows: inputs consumed per "
            "unit of output. Dashed: capacity investment. Design/EDA/IP value enters as "
            "services, never as goods trade. Codes: OECD semiconductor mapping + Fed "
            "AI-compute basket (docs/data.md §1).")
    ax.text(1.0, -0.040, "\n".join(textwrap.wrap(foot, 116)), ha="center",
            va="top", fontsize=7.4, color=MUTED)

    out = cfg.ROOT / "exports" / "chain_topology.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out} (+ .pdf)")


if __name__ == "__main__":
    main()
