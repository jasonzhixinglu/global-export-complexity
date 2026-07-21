"""Route A of the bundle-identification program: choose the loading basis by
NONNEGATIVITY instead of varimax, within the subspace the MFM already estimated.

For each panel code (pooled 2024 monthly matrices, CHK bloc, k=r=4): estimate the
unrotated eigenbasis, then search orthogonal rotations (with per-column sign
freedom) minimizing the negative-mass share of the loadings. Multi-start
dispersion of the solutions is the uniqueness diagnostic (anchors/sufficient
scattering => solutions cluster). Compares the nonneg basis with varimax.

Output: printed report + docs/notes/nonneg-rotation-experiment.md
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.optimize import minimize, linear_sum_assignment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

K = 4
YEAR = "2024"
BLOC = {"CHN": "CHK", "HKG": "CHK"}
CODES = {"847330": ["847330"], "847180": ["847180"], "847150": ["847150"],
         "ai_compute": ["847330", "847180", "847150"]}
N_STARTS = 60
rng = np.random.default_rng(7)


def estimate(codes):
    p = pd.read_parquet(cfg.DATA_DIR / "derived" / "panel_ai_compute_monthly.parquet")
    p = p[p.code.isin(codes) & (p.period.str[:4] == YEAR)]
    flows = {}
    for (per, o, t), v in p.groupby(["period", "exporter", "importer"]).value.sum().items():
        o2, t2 = BLOC.get(o, o), BLOC.get(t, t)
        if o2 != t2:
            flows[(per, o2, t2)] = flows.get((per, o2, t2), 0.0) + float(v) / 1e9
    countries = sorted({o for (_, o, _) in flows} | {t for (_, _, t) in flows})
    idx = {c: i for i, c in enumerate(countries)}
    periods = sorted({per for (per, _, _) in flows})
    Y = np.zeros((len(periods), len(countries), len(countries)))
    for (per, o, t), v in flows.items():
        Y[periods.index(per), idx[o], idx[t]] = v
    M_R = np.einsum("sij,skj->ik", Y, Y)
    M_C = np.einsum("sji,sjk->ik", Y, Y)
    R = np.linalg.eigh(M_R)[1][:, -K:][:, ::-1] * np.sqrt(len(countries))
    C = np.linalg.eigh(M_C)[1][:, -K:][:, ::-1] * np.sqrt(len(countries))
    return countries, R, C


def varimax(L, iters=500, tol=1e-9):
    p, k = L.shape
    O = np.eye(k)
    var = 0.0
    for _ in range(iters):
        B = L @ O
        U, s, Vt = np.linalg.svd(L.T @ (B**3 - B @ np.diag((B**2).sum(0)) / p))
        O = U @ Vt
        if s.sum() < var * (1 + tol):
            break
        var = s.sum()
    return O


def sign_fix(L):
    """Per-column sign minimizing that column's negative mass."""
    out = L.copy()
    for j in range(L.shape[1]):
        if (np.minimum(out[:, j], 0) ** 2).sum() > (np.minimum(-out[:, j], 0) ** 2).sum():
            out[:, j] *= -1
    return out


def negshare(L):
    L = sign_fix(L)
    return float((np.minimum(L, 0) ** 2).sum() / (L ** 2).sum())


def skew(theta):
    S = np.zeros((K, K))
    iu = np.triu_indices(K, 1)
    S[iu] = theta
    return S - S.T


def optimize_nonneg(L, n_starts=N_STARTS):
    sols = []
    starts = [np.zeros(6)] + [rng.uniform(-np.pi, np.pi, 6) for _ in range(n_starts - 1)]
    for th0 in starts:
        res = minimize(lambda th: negshare(L @ expm(skew(th))), th0,
                       method="Nelder-Mead",
                       options={"maxiter": 4000, "xatol": 1e-6, "fatol": 1e-10})
        sols.append((res.fun, expm(skew(res.x))))
    sols.sort(key=lambda s: s[0])
    return sols


def match_dist(A, B):
    """Column-matching distance: 1 - mean |cos| after optimal permutation."""
    An = A / np.linalg.norm(A, axis=0)
    Bn = B / np.linalg.norm(B, axis=0)
    S = np.abs(An.T @ Bn)
    r, c = linear_sum_assignment(-S)
    return 1 - S[r, c].mean(), S[r, c]


def top(L, countries, j, n=5):
    L = sign_fix(L)
    lead = np.argsort(-np.abs(L[:, j]))[:n]
    return ", ".join(f"{countries[i]} {L[i, j]:+.2f}" for i in lead)


def main():
    lines = ["# Nonnegativity rotation vs varimax (Route A experiment)", "",
             f"Pooled {YEAR} monthly MFM per code (CHK bloc, k=r={K}); basis chosen by",
             "minimizing negative-mass share over orthogonal rotations + column signs,",
             f"{N_STARTS} multi-starts. Dispersion of near-optimal solutions = the",
             "uniqueness diagnostic.", ""]
    for label, codes in CODES.items():
        countries, R, C = estimate(codes)
        out = [f"## {label}", ""]
        for side, L in (("export", R), ("import", C)):
            sols = optimize_nonneg(L)
            best_obj, best_M = sols[0]
            near = [M for f, M in sols if f < best_obj + 1e-4]
            disp = max((match_dist(L @ near[0], L @ M)[0] for M in near[1:]), default=0.0)
            vm = L @ varimax(L)
            d_vm, cos_vm = match_dist(L @ best_M, vm)
            out += [f"**{side}**: neg-share unrotated {negshare(L):.3f} -> varimax "
                    f"{negshare(vm):.3f} -> nonneg-opt {best_obj:.3f}; "
                    f"near-optimal solutions {len(near)}/{len(sols)}, max dispersion "
                    f"{disp:.3f}; nonneg-vs-varimax match |cos| = "
                    + ", ".join(f"{c:.2f}" for c in cos_vm), ""]
            B = sign_fix(L @ best_M)
            for j in np.argsort(-(B ** 2).sum(0)):
                out.append(f"- {side} bundle: {top(B, countries, j)}")
            out.append("")
        print("\n".join(out))
        lines += out
    (cfg.ROOT / "docs" / "notes" / "nonneg-rotation-experiment.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print("-> docs/notes/nonneg-rotation-experiment.md")


if __name__ == "__main__":
    main()
