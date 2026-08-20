"""Stylized topology of the AI-compute supply chain, with HS6 codes per node.

The simplified narrative shape (docs/data.md §1 "How stages combine"):
two parallel input branches — materials (raw -> wafers/chemicals) and tools
(optics -> equipment) — converge on chip fabrication; chips then run
sequentially through parts/GPU modules, baseboards, and AI servers.
Circle diameters follow the log of 2024 world trade (illustrative). Edge styles
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
from gec.palette import STAGE as PAL, FILL as PAL_FILL

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
# one shared stage palette for every chart (src/gec/palette.py): pink =
# consumed per chip, orange = capacity investment, green = fabrication,
# blues = the AI-compute codes, darkening along the chain
FILL = {k: PAL_FILL[v] for k, v in {
    "raw": "materials", "wafer": "materials", "optic": "equipment",
    "equip": "equipment", "fab": "chips", "parts": "parts",
    "board": "baseboards", "srv": "servers"}.items()}
EDGE = {k: PAL[v] for k, v in {
    "raw": "materials", "wafer": "materials", "optic": "equipment",
    "equip": "equipment", "fab": "chips", "parts": "parts",
    "board": "baseboards", "srv": "servers"}.items()}

# 2024 world trade per node ($B, CHK basis, Atlas HS2012 annual for every stage
# -- see scripts/extract_atlas_stage_flows.py)
VAL = {"raw": 13, "wafer": 25, "optic": 38, "equip": 244, "fab": 823,
       "parts": 129, "board": 79, "srv": 115}
_l = {k: np.log10(v) for k, v in VAL.items()}
# circle DIAMETER proportional to log10(2024 value): r = rmax * l / lmax
RAD = {k: 0.190 * _l[k] / max(_l.values()) for k in _l}

NODES = {
    # key: (cx, cy, kind, title, code list)
    "raw":   (0.150, 0.780, "mat", "Raw materials", sorted(O["Raw materials"])),
    "wafer": (0.600, 0.780, "mat", "Wafers & inputs", sorted(O["Wafer inputs"])),
    "optic": (0.150, 0.290, "tool", "Litho & optics", sorted(O["Foundry inputs"])),
    "equip": (0.615, 0.290, "tool", "Fab equipment", sorted(O["Manufacturing equipment"])),
    "fab":   (1.070, 0.500, "fab", "CHIP FABRICATION", sorted(O["Chips"])),
    "parts": (1.510, 0.760, "down", "Parts & GPU modules", ["847330"]),
    "board": (1.510, 0.280, "down", "Baseboards", ["847180"]),
    "srv":   (1.930, 0.500, "down", "AI servers", ["847150"]),
}

ARROWS = [  # (from, to, style, label[, label xy])
    ("raw", "wafer", "solid", ""),
    ("wafer", "fab", "solid", ""),
    ("optic", "equip", "solid", ""),
    ("equip", "fab", "dashed", ""),
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
    ax.set_ylim(-0.22, 1.10)
    ax.set_aspect("equal")
    ax.axis("off")

    for k, (cx, cy, kind, title, cl) in NODES.items():
        r = RAD[k]
        ax.add_patch(Circle((cx, cy), r, fc=FILL[k], ec=EDGE[k],
                            lw=2.6, zorder=2))
        # name and value sit in the CENTER of the circle (may overflow small
        # circles); the HS6 codes list sits just BELOW the circle
        ax.text(cx, cy + 0.020, title, ha="center", va="center",
                fontsize=10.5, weight="bold", color=INK, zorder=3)
        ax.text(cx, cy - 0.024, f"${VAL[k]}B in 2024", ha="center",
                va="center", fontsize=8.6, color=INK2, zorder=3)
        ncol = 3 if len(cl) > 8 else (2 if len(cl) >= 4 else 1)
        rows = -(-len(cl) // ncol)
        fs = 7.0 if len(cl) >= 8 else 7.6
        dy = 0.031 if len(cl) >= 8 else 0.040
        xsp = 0.082 if ncol == 3 else 0.095
        top = cy - r - 0.038
        for i, c in enumerate(cl):
            row, col = i // ncol, i % ncol      # fill row-wise below the circle
            x = cx + (col - (ncol - 1) / 2) * xsp
            y = top - row * dy
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

    ax.text(1.04, 1.050, "The AI-compute supply chain — stylized shape, "
            "with the HS6 codes in each node",
            ha="center", va="top", fontsize=16, weight="bold", color=INK)
    foot = ("Two input branches, one output line. Materials (pink) -- silicon, chemicals, "
            "wafers -- are used up with every chip made (solid arrows). Equipment (orange) -- "
            "lithography and other fab tools -- is investment in capacity: in Taiwan and Korea, "
            "equipment imports rise six to twelve months before chip exports (dashed arrow). "
            "Korean memory and Taiwanese chips are packaged together, usually in Taiwan. "
            "Chip design earns as a service and crosses no border. "
            "Circle diameters grow with the log of 2024 world trade. Blue marks the three "
            "codes of our monthly panel (the Fed AI-compute basket). A few niche inputs "
            "(lasers, vacuum pumps and valves, chip substrates) fall outside the 60 codes. "
            "Codes: OECD semiconductor mapping + Fed basket (docs/data.md, section 1).")
    ax.text(1.04, -0.135, "\n".join(textwrap.wrap(foot, 172)), ha="center",
            va="top", fontsize=8.8, color=MUTED)

    out = cfg.ROOT / "exports" / "chain_topology.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", pad_inches=0.25, facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.25, facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out} (+ .pdf)")


if __name__ == "__main__":
    main()
