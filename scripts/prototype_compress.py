"""Prototype Path C compression for the dashboard density curves.

Compares the current representation (150-point grid, 6-dp JSON) against:
  (C1) DCT  - keep K low-frequency cosine coefficients, reconstruct via iDCT
  (C2) Coarse grid - subsample to M points, reconstruct via cubic spline

Reports reconstruction error (relative L2, max-abs as % of peak, mass error)
and the serialized JSON byte size of each scheme across ALL curves.

Run:  python scripts/prototype_compress.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from scipy.fft import dct, idct
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

DERIVED = cfg.DATA_DIR / "derived"
KSTEP = 2  # current shipping subsample -> 150 points


import gzip


def json_bytes(obj) -> int:
    return len(json.dumps(obj).encode("utf-8"))


def gz_bytes(obj) -> int:
    return len(gzip.compress(json.dumps(obj).encode("utf-8"), 6))


def rnd(a, n):
    """Round like the exporter does (JSON-realistic sizes), return python list."""
    return [None if not np.isfinite(v) else round(float(v), n) for v in a]


def dct_encode(curve, K):
    c = dct(curve, norm="ortho")
    c[K:] = 0.0
    return c[:K]


def dct_decode(coefs, n):
    full = np.zeros(n)
    full[: len(coefs)] = coefs
    return idct(full, norm="ortho")


def coarse_encode(curve, x, M):
    idx = np.linspace(0, len(curve) - 1, M).round().astype(int)
    return idx, curve[idx]


def coarse_decode(x, idx, vals, xfull):
    cs = CubicSpline(x[idx], vals)
    return np.clip(cs(xfull), 0, None)


def errors_subset(recon, curves, x):
    diff = recon - curves
    rel = np.linalg.norm(diff, axis=1) / np.maximum(np.linalg.norm(curves, axis=1), 1e-12)
    peak = curves.max(axis=1); peak[peak == 0] = 1.0
    mx = np.abs(diff).max(axis=1) / peak
    m0 = np.trapezoid(curves, x, axis=1); m1 = np.trapezoid(recon, x, axis=1)
    ms = np.abs(m1 - m0) / np.maximum(np.abs(m0), 1e-12)
    return rel, mx, ms


def main():
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    dens = s["density_lvl"]  # (flow, level, country, year, 300)
    grid_full = s["kde_grid"]
    idx150 = list(range(0, len(grid_full), KSTEP))
    x = grid_full[idx150]                       # the 150-pt grid actually shipped
    n = len(x)                                  # 150
    nf, nl, nc, ny, _ = dens.shape

    levels = [lv["id"] for lv in cfg.SMOOTHING]
    # flatten every shipped curve (subsampled to 150 pts) into one big list; track level
    curves, lvl_of = [], []
    for fi in range(nf):
        for li in range(nl):
            for ci in range(nc):
                for yi in range(ny):
                    curves.append(dens[fi, li, ci, yi][idx150])
                    lvl_of.append(li)
    curves = np.array(curves)                   # (N, 150)
    lvl_of = np.array(lvl_of)
    N = len(curves)
    peak = curves.max(axis=1)
    peak[peak == 0] = 1.0

    def errors(recon):
        diff = recon - curves
        rel_l2 = np.linalg.norm(diff, axis=1) / np.maximum(np.linalg.norm(curves, axis=1), 1e-12)
        max_pct = np.abs(diff).max(axis=1) / peak
        m0 = np.trapezoid(curves, x, axis=1)
        m1 = np.trapezoid(recon, x, axis=1)
        mass_pct = np.abs(m1 - m0) / np.maximum(np.abs(m0), 1e-12)
        return rel_l2, max_pct, mass_pct

    print(f"curves: {N}  grid points each: {n}  (flows={nf} levels={nl} countries={nc} years={ny})")

    # ---- baseline: current 150-pt grid at 6 dp ----
    base = {"density": [rnd(c, 6) for c in curves]}
    base_bytes = json_bytes(base)
    base_gz = gz_bytes(base)
    print(f"\nBASELINE  150-pt grid @6dp : raw {base_bytes/1e6:6.2f} MB  gz {base_gz/1e6:5.2f} MB  ({base_bytes/N:6.1f} B/curve)")

    # ---- C1: DCT, several K and rounding ----
    print("\n(C1) DCT  keep K coefficients")
    print(f"  {'K':>3} {'dp':>3} {'relL2%':>8} {'maxErr%peak':>12} {'mass%':>7} {'MB':>7} {'B/curve':>8} {'vs base':>8}")
    for K in (8, 12, 16, 20, 24):
        for dp in (3, 4):
            coefs = np.array([dct_encode(c, K) for c in curves])
            recon = np.array([dct_decode(np.round(co, dp), n) for co in coefs])
            recon = np.clip(recon, 0, None)
            rel, mx, ms = errors(recon)
            payload = {"dct": [rnd(co, dp) for co in coefs]}
            b = json_bytes(payload)
            print(f"  {K:>3} {dp:>3} {100*np.median(rel):8.3f} {100*np.median(mx):12.3f} "
                  f"{100*np.median(ms):7.3f} {b/1e6:7.2f} {b/N:8.1f} {base_bytes/b:7.1f}x")

    # ---- C2: coarse grid + cubic spline ----
    print("\n(C2) Coarse grid + cubic spline (reconstruct to 150 pts)")
    print(f"  {'M':>3} {'dp':>3} {'relL2%':>8} {'maxErr%peak':>12} {'mass%':>7} {'MB':>7} {'B/curve':>8} {'vs base':>8}")
    for M in (30, 40, 50, 60, 75):
        for dp in (5, 6):
            idx, _ = coarse_encode(curves[0], x, M)
            vals = curves[:, idx]
            recon = np.array([coarse_decode(x, idx, v, x) for v in vals])
            rel, mx, ms = errors(recon)
            payload = {"grid": [rnd(v, dp) for v in vals]}  # grid x stored once in meta
            b = json_bytes(payload)
            print(f"  {M:>3} {dp:>3} {100*np.median(rel):8.3f} {100*np.median(mx):12.3f} "
                  f"{100*np.median(ms):7.3f} {b/1e6:7.2f} {b/N:8.1f} {base_bytes/b:7.1f}x")

    # ---- per-level breakdown: coarse grid is the winner; show where the cost lives ----
    print("\nPer-level coarse-grid error (relL2 % p50 / p95):  low=bw0.05  med=bw0.10  high=bw0.20")
    print(f"  {'M':>3} " + "".join(f"{lv+' p50':>11}{lv+' p95':>11}" for lv in levels))
    for M in (40, 50, 60, 75, 100):
        idx, _ = coarse_encode(curves[0], x, M)
        recon = np.array([coarse_decode(x, idx, v, x) for v in curves[:, idx]])
        rel, _, _ = errors(recon)
        row = f"  {M:>3} "
        for li in range(nl):
            m = lvl_of == li
            row += f"{100*np.median(rel[m]):11.3f}{100*np.percentile(rel[m],95):11.3f}"
        print(row)

    # ---- adaptive: per-level resolution + 5dp; total size & worst error ----
    print("\nADAPTIVE coarse grid (per-level M) + cubic spline, 5dp:")
    for plan in ({"low": 150, "med": 75, "high": 50},
                 {"low": 120, "med": 60, "high": 40},
                 {"low": 100, "med": 50, "high": 40}):
        total_b, worst95 = 0, 0.0
        detail = []
        for li, lid in enumerate(levels):
            M = plan[lid]
            idx = np.linspace(0, n - 1, M).round().astype(int)
            mask = lvl_of == li
            sub = curves[mask]
            recon = np.array([coarse_decode(x, idx, v, x) for v in sub[:, idx]])
            rel, _, _ = errors_subset(recon, sub, x)
            payload = {"grid": [rnd(v, 5) for v in sub[:, idx]]}
            b = json_bytes(payload)
            total_b += b
            worst95 = max(worst95, 100 * np.percentile(rel, 95))
            detail.append(f"{lid}:M={M}(p95={100*np.percentile(rel,95):.1f}%)")
        print(f"  plan {plan} -> density {total_b/1e6:.2f} MB "
              f"(vs {base_bytes/1e6:.2f} MB base, {base_bytes/total_b:.1f}x), worst p95 relL2={worst95:.1f}%")
        print("     " + "  ".join(detail))

    # ---- gzip transfer sizes (what the browser actually downloads) ----
    print("\nGZIP transfer size (GitHub Pages serves gzipped):")
    cfgs = {
        "baseline 150 @6dp": [rnd(c, 6) for c in curves],
        "DCT K=16 @4dp": [rnd(dct_encode(c, 16), 4) for c in curves],
        "coarse M=50 @5dp": [rnd(v, 5) for v in curves[:, np.linspace(0, n-1, 50).round().astype(int)]],
        "coarse M=60 @5dp": [rnd(v, 5) for v in curves[:, np.linspace(0, n-1, 60).round().astype(int)]],
    }
    for label, payload in cfgs.items():
        raw, gz = json_bytes(payload), gz_bytes(payload)
        print(f"  {label:>20}: raw {raw/1e6:5.2f} MB  gz {gz/1e6:5.2f} MB  ({base_gz/gz:.1f}x vs base gz)")


if __name__ == "__main__":
    main()
