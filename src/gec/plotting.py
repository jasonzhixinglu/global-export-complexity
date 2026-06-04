"""Shared plotting helpers (matplotlib, headless-safe)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless; scripts save PNGs rather than display
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "figure.dpi": 120,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "font.size": 9,
})


def small_multiples(keys, ncol=4):
    nrow = int(np.ceil(len(keys) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.6 * ncol, 2.5 * nrow), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    return fig, axes


def heatmap_panel(ax, surf, xgrid, years, cmap="viridis", vmin=0, vmax=None):
    return ax.imshow(
        surf, aspect="auto", origin="lower", cmap=cmap, vmin=vmin, vmax=vmax,
        extent=[xgrid[0], xgrid[-1], years[0], years[-1]],
    )


def save(fig, path, **kw):
    fig.savefig(path, bbox_inches="tight", **kw)
    plt.close(fig)
    return path
