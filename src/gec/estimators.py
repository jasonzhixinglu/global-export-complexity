"""Non-parametric estimators with explicit accounting properties.

Two estimands, two different conservation guarantees (see docs/pci-analysis.md §3):

* `local_linear_shares` — a country's share of world exports as a function of PCI.
  It is a *linear smoother that reproduces constants*, applied to a response
  (C_p / W_p) whose sum over all countries is identically 1. Therefore the shares
  add up to exactly 1 at every PCI, for any bandwidth -- a self-calibrating /
  self-benchmarking property. We return UNCLIPPED estimates so that holds; clip
  only for display.

* `kde_bin_mass` / `weighted_histogram` — the distribution of export dollars over
  PCI. The histogram conserves dollar mass exactly per bin (it is the ground truth
  for any range). The KDE is the smooth approximation; its TOTAL is conserved exactly
  (kernels each integrate to 1) but sub-ranges carry mean-zero O(h^2) redistribution
  error. `calibrate_total` benchmarks any estimate to a known accounting total.
"""
from __future__ import annotations

import numpy as np
from scipy.special import ndtr  # standard normal CDF, vectorized
from scipy.stats import gaussian_kde


# ---------------------------------------------------------------------------
# Market share by complexity: value-weighted local-linear regression
# ---------------------------------------------------------------------------
def local_linear_shares(pci, W, C_by_country, grid, h, clip=False):
    """Value-weighted local-linear estimate of share(PCI) for many countries.

    Parameters
    ----------
    pci, W : (P,) arrays
        Product-level complexity and world export value.
    C_by_country : dict[str, (P,) array]
        Each country's export value aligned to the same products.
    grid : (G,) array
        PCI values at which to evaluate.
    h : float
        Gaussian kernel bandwidth.
    clip : bool
        If True, clip each curve to [0, 1] (display only -- breaks exact adding-up).

    Returns
    -------
    dict[str, (G,) array]
        Estimated shares. The local-linear intercept solves a weighted least-squares
        fit of C_p/W_p on (pci_p - x) with weights K_h(pci_p - x) * W_p, giving
        s = (S2*T0 - S1*T1) / (S2*S0 - S1^2).
    """
    pci = np.asarray(pci, float)
    W = np.asarray(W, float)
    U = pci[None, :] - grid[:, None]              # (G, P)
    Km = np.exp(-0.5 * (U / h) ** 2)              # raw Gaussian kernel
    Kk = Km * W[None, :]                           # value-weighted kernel
    S0 = Kk.sum(1)
    S1 = (Kk * U).sum(1)
    S2 = (Kk * U * U).sum(1)
    denom = S2 * S0 - S1 * S1
    denom = np.where(np.abs(denom) < 1e-12, np.nan, denom)
    KmU = Km * U
    out = {}
    for name, C in C_by_country.items():
        C = np.asarray(C, float)
        T0 = Km @ C                                # sum_p K * C_p   (W cancels in T = Kk*y)
        T1 = KmU @ C                               # sum_p K * U * C_p
        s = (S2 * T0 - S1 * T1) / denom
        out[name] = np.clip(s, 0.0, 1.0) if clip else s
    return out


def adding_up(pci, W, grid, h):
    """Sum of all-country shares at each grid point. Feeding C = W reproduces
    sum_c s_c exactly (linearity), which should be 1.0 to machine precision."""
    return local_linear_shares(pci, W, {"_all_": W}, grid, h, clip=False)["_all_"]


# ---------------------------------------------------------------------------
# Distribution of export dollars across complexity
# ---------------------------------------------------------------------------
def kde_density(x, w, grid, bw_method=None):
    """Value-weighted Gaussian KDE, normalized to integrate to 1 over `grid`.
    Bandwidth defaults to Scott's rule on the weighted sample (data-driven)."""
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[m], w[m]
    if x.size < 5 or np.unique(x).size < 2:
        return np.full(grid.shape, np.nan)
    kde = gaussian_kde(x, weights=w, bw_method=bw_method)
    y = kde(grid)
    area = np.trapezoid(y, grid)
    return y / area if area > 0 else y


def density_fixed(x, w, grid, h):
    """Value-weighted Gaussian density with an explicit bandwidth `h` (PCI units),
    normalized to integrate to 1 over the real line. Uses the SAME kernel as
    `kde_bin_mass`, so integrating this curve over any bin equals that bin's mass
    fraction -- the curve and the conservation diagnostic are mutually consistent."""
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[m], w[m]
    if x.size < 2:
        return np.full(grid.shape, np.nan)
    wn = w / w.sum()
    z = (grid[:, None] - x[None, :]) / h
    phi = np.exp(-0.5 * z * z) / (h * np.sqrt(2 * np.pi))
    return phi @ wn


def kde_bin_mass(x, w, edges, h):
    """Dollar mass per bin via closed-form Gaussian-kernel CDF allocation.

    Each observation's weight w_i is spread by a Gaussian of width h centered at x_i;
    the mass it contributes to bin [a, b] is w_i * (Phi((b-x_i)/h) - Phi((a-x_i)/h)).
    Summed over all (-inf, inf) bins this returns exactly sum(w) -- total dollar mass
    is conserved regardless of h. Sub-bin values approximate the true binned dollars
    with mean-zero O(h^2) redistribution error.

    `edges` are the K+1 interior bin edges; two implicit tail bins (-inf, edges[0]) and
    (edges[-1], inf) are included so the returned masses sum to sum(w).
    Returns (mass, edges_full) with len(mass) == len(edges)+1.
    """
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    m = np.isfinite(x) & np.isfinite(w)
    x, w = x[m], w[m]
    z = (edges[None, :] - x[:, None]) / h          # (N, K)
    cdf = ndtr(z)                                   # P(X <= edge)
    full = np.concatenate([np.zeros((x.size, 1)), cdf, np.ones((x.size, 1))], axis=1)
    per_bin = np.diff(full, axis=1)                 # (N, K+1) incl. both tails
    return per_bin.T @ w                            # (K+1,) dollar mass per bin


def weighted_histogram(x, w, edges):
    """Exact dollar mass per bin (the conservation ground truth). Returns K+1 bins to
    match `kde_bin_mass`: [(-inf,e0), (e0,e1), ..., (e_{K-1}, inf)]."""
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    inner, _ = np.histogram(x, bins=edges, weights=w)
    below = w[x < edges[0]].sum()
    above = w[x >= edges[-1]].sum()
    return np.concatenate([[below], inner, [above]])


def calibrate_total(values, target_total):
    """Raking / ratio benchmarking: scale `values` so they sum to a known accounting
    total. This is the standard official-statistics fix for aligning a smooth estimate
    with an aggregate (see docs/pci-analysis.md §3)."""
    s = np.nansum(values)
    return values * (target_total / s) if s > 0 else values
