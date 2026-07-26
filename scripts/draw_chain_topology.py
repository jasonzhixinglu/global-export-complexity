"""Stylized topology of the AI-compute supply chain, with HS6 codes per node.

The simplified narrative shape (docs/data.md §1 "How stages combine"):
two parallel input branches — materials (raw -> wafers/chemicals) and tools
(optics -> equipment) — converge on chip fabrication; chips then run
sequentially through parts/GPU modules, baseboards, and AI servers.
Edge styles carry the combination rule: solid = consumed per unit of output,
dashed = capacity investment (leads output 6-12 months in fab countries).

Output: exports/chain_topology.png (+ .pdf, vector) — referenced from
docs/data.md, docs/supply-chain-narrative.md, and the chart pack.
"""
from __future__ import annotations
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as O

SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
FILL = {"input": "#eef3fb", "fab": "#e8f5ee", "down": "#fdf1e7"}
EDGE = {"input": "#2a78d6", "fab": "#008300", "down": "#eb6834"}


def codes(group):
    return sorted(O[group])


# 2024 world trade per node ($B, CHK basis; stages 1-5 Atlas, 6-8 audited panel).
VAL = {"raw": 13, "wafer": 25, "optic": 38, "equip": 244, "fab": 823,
       "parts": 146, "board": 101, "srv": 127}

# Node heights scale with log10 of the 2024 value (illustrative: keeps chips
# from dwarfing raw materials while preserving the ordering).
import numpy as np
_l = {k: np.log10(v) for k, v in VAL.items()}
_s = {k: 0.66 + 0.34 * _l[k] / max(_l.values()) for k in _l}

NODES = {
    # key: (x, y, w, h, kind, title, subtitle, code list)
    "raw":   (0.010, 0.975 - 0.34 * _s["raw"], 0.155, 0.34 * _s["raw"], "input",
              "Raw materials", "silicon, gases, Ga/Ge, chemicals", codes("Raw materials")),
    "wafer": (0.225, 0.860 - 0.26 * _s["wafer"], 0.145, 0.26 * _s["wafer"], "input",
              "Wafers & chemical inputs", "wafers, photoresists, masks", codes("Wafer inputs")),
    "optic": (0.010, 0.060, 0.155, 0.24 * _s["optic"], "input",
              "Litho & optics inputs", "lenses, e-beam, inspection", codes("Foundry inputs")),
    "equip": (0.215, 0.060, 0.145, 0.30 * _s["equip"], "input",
              "Fab equipment", "litho, dep/etch, metrology", codes("Manufacturing equipment")),
    "fab":   (0.435, 0.300, 0.165, 0.42 * _s["fab"], "fab",
              "CHIP FABRICATION", "logic + memory + discretes", codes("Chips")),
    "parts": (0.675, 0.820 - 0.26 * _s["parts"], 0.135, 0.26 * _s["parts"], "down",
              "Parts & GPU modules", "accelerator cards, components", ["847330"]),
    "board": (0.675, 0.140, 0.135, 0.26 * _s["board"], "down",
              "Baseboards", "HGX trays, subassemblies", ["847180"]),
    "srv":   (0.865, 0.320, 0.125, 0.42 * _s["srv"], "down",
              "AI servers", "assembled systems, racks", ["847150"]),
}

ARROWS = [  # (from, to, style, label)
    ("raw", "wafer", "solid", ""),
    ("wafer", "fab", "solid", "consumed per unit of output"),
    ("optic", "equip", "solid", ""),
    ("equip", "fab", "dashed", "capacity investment;\nleads output 6-12m"),
    ("fab", "parts", "solid", ""),
    ("parts", "board", "solid", ""),
    ("board", "srv", "solid", ""),
    ("parts", "srv", "solid", ""),
]


def centre(k, side):
    x, y, w, h, *_ = NODES[k]
    return {"r": (x + w, y + h / 2), "l": (x, y + h / 2),
            "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


def main():
    fig, ax = plt.subplots(figsize=(13.5, 6.8))
    fig.patch.set_facecolor(SURFACE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    for k, (x, y, w, h, kind, title, sub, cl) in NODES.items():
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008",
                                    fc=FILL[kind], ec=EDGE[kind], lw=1.6, zorder=2))
        ax.text(x + w / 2, y + h - 0.028, f"{title}  (${VAL[k]}B)", ha="center",
                va="top", fontsize=9.8, weight="bold", color=INK, zorder=3)
        ax.text(x + w / 2, y + h - 0.072, sub, ha="center", va="top",
                fontsize=7.6, color=INK2, style="italic", zorder=3)
        ncol = 3 if len(cl) > 8 else (2 if len(cl) >= 4 else 1)
        rows = -(-len(cl) // ncol)
        spacing = max(0.024, min(0.032, (h - 0.125) / max(rows, 1)))
        for i, c in enumerate(cl):
            cx = x + w * (0.5 + (i // rows - (ncol - 1) / 2) * (0.32 if ncol == 3 else 0.42))
            cy = y + h - 0.110 - (i % rows) * spacing
            ax.text(cx, cy, c, ha="center", va="top", fontsize=6.4,
                    family="monospace", color=MUTED, zorder=3)

    for a, b, style, lab in ARROWS:
        # pick sides: rightward flow generally; vertical inside columns
        if a == "raw":
            p1, p2 = centre("raw", "r"), centre("wafer", "l")
        elif a == "optic":
            p1, p2 = centre("optic", "r"), centre("equip", "l")
        elif (a, b) == ("parts", "board"):
            p1, p2 = centre("parts", "b"), centre("board", "t")
        else:
            p1, p2 = centre(a, "r"), centre(b, "l")
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16,
                                     lw=2.0 if style == "solid" else 1.8,
                                     ls="-" if style == "solid" else (0, (5, 3)),
                                     color=INK2, zorder=1,
                                     connectionstyle="arc3,rad=0.08"))
        if lab:
            mx = (p1[0] + p2[0]) / 2 - (0.075 if a == "wafer" else 0.0)
            my = (p1[1] + p2[1]) / 2 + (0.07 if a == "equip" else 0.045)
            ax.text(mx, my, lab, ha="center", fontsize=7.2, color=MUTED, zorder=3)

    ax.text(0.518, 0.24, "memory (KOR) joins logic at advanced packaging,\n"
            "largely inside Taiwan — invisible to customs data",
            ha="center", fontsize=7.2, color=MUTED)
    ax.text(0.5, 0.985, "The AI-compute supply chain — stylized shape, with the HS6 codes in each node",
            ha="center", va="top", fontsize=12.5, weight="bold", color=INK)
    ax.text(0.5, 0.005,
            "Two parallel input branches converge on fabrication; the output side is sequential. "
            "Node heights scale with the log of 2024 world trade (illustrative -- so chips does not dwarf raw materials). "
            "Solid arrows: inputs consumed per unit of output. Dashed: capacity investment. "
            "Design/EDA/IP value enters as services, never as goods trade. Codes: OECD semiconductor "
            "mapping + Fed AI-compute basket (docs/data.md §1).",
            ha="center", va="bottom", fontsize=7.2, color=MUTED)

    out = cfg.ROOT / "exports" / "chain_topology.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", facecolor=SURFACE)
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"-> {out} (+ .pdf)")


if __name__ == "__main__":
    main()
