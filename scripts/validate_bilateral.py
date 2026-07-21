"""Validate the bilateral GMM corridors against the (already-validated) country-level GMMs.

Checks (all from the small JSON outputs, no big-file reads):
  1. COVERAGE / adding-up: encoded outbound corridors of A sum to ~A's total exports;
     inbound corridors of B sum to ~B's total imports (inclusive of ROW).  Gap = skipped
     thin corridors + reconciliation slack.
  2. DISTRIBUTION RECOMPOSITION: a value-weighted sum of corridor mixtures is itself a
     mixture; the outbound sum for A should reproduce A's country-level EXPORT distribution
     (gmm.json), and the inbound sum for B its country-level IMPORT distribution.  Compared
     with KS (sup-norm) and W1 (transport) -- the bilateral fits are anchored to the country
     curves, which are themselves validated against raw data (docs/pci-analysis.md s3.3).

Run:  python scripts/validate_bilateral.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

DATA = cfg.ROOT / "dashboard" / "public" / "data"
XG = np.linspace(cfg.PCI_LO, cfg.PCI_HI, 600)
DX = XG[1] - XG[0]


def density(params):
    par = np.array(params, float); pi = par[:, 0] / par[:, 0].sum()
    return (pi[:, None] * np.exp(-0.5 * ((XG[None, :] - par[:, 1][:, None]) / par[:, 2][:, None]) ** 2)
            / (par[:, 2][:, None] * np.sqrt(2 * np.pi))).sum(0)


def cdf(d):
    c = np.cumsum(d) * DX
    return c / c[-1]


def ks_w1(a, b):
    ca, cb = cdf(a), cdf(b)
    diff = np.abs(ca - cb)
    return diff.max(), np.trapezoid(diff, XG)


def main():
    gmm = json.loads((DATA / "gmm.json").read_text())            # country distributions
    series = json.loads((DATA / "series.json").read_text())       # country totals
    bil = json.loads((DATA / "gmm_bilateral.json").read_text())   # corridors
    mixC = gmm["mix"]; totB = series["totalB"]
    mixB = bil["mix"]; corrB = bil["corridorB"]
    top = [b for b in bil["blocs"] if b != "ROW"]
    years = [str(y) for y in bil["years"]]

    def recompose(country, get_corr, flow):
        """get_corr(country, y) -> dict {counterparty: (params, weight)}; compare aggregate to country GMM."""
        ks_l, w1_l, cov_l = [], [], []
        for c in top:
            cmix = mixC.get(flow, {}).get(c, {})
            tser = totB.get(flow, {}).get(c, {})
            for y in years:
                pieces = get_corr(c, y)
                if not pieces or y not in cmix or tser.get(y) in (None, 0):
                    continue
                num = np.zeros_like(XG); wsum = 0.0
                for params, w in pieces:
                    num += w * density(params); wsum += w
                if wsum <= 0:
                    continue
                agg = num / wsum
                ks, w1 = ks_w1(agg, density(cmix[y]))
                ks_l.append(ks); w1_l.append(w1)
                cov_l.append(wsum / tser[y])          # encoded corridor value / country total
        return np.array(ks_l), np.array(w1_l), np.array(cov_l)

    # EXPORT: outbound corridors of A (over all destinations incl ROW)
    def outbound(c, y):
        return [(mixB[c][d][y], corrB[c][d][y]) for d in mixB.get(c, {})
                if y in mixB[c][d] and y in corrB.get(c, {}).get(d, {})]
    # IMPORT: inbound corridors of B (over all origins incl ROW)
    def inbound(c, y):
        return [(mixB[o][c][y], corrB[o][c][y]) for o in mixB
                if c in mixB[o] and y in mixB[o][c] and y in corrB.get(o, {}).get(c, {})]

    print(f"bilateral: {bil['blocs'].__len__()} blocs (incl ROW), years {bil['years'][0]}-{bil['years'][-1]}\n")

    # 0. EXACT marginal adding-up (all corridors incl ROW, incl thin/skipped): bilateral origin
    #    marginal should equal the country's total exports; destination marginal its total imports.
    margE, margI = bil.get("margExpB"), bil.get("margImpB")
    if margE and margI:
        for flow, marg in [("export", margE), ("import", margI)]:
            res = []
            for c in top:
                for y in years:
                    tot = totB.get(flow, {}).get(c, {}).get(y)
                    m = marg.get(c, {}).get(y)
                    if tot and m is not None:
                        res.append(abs(m - tot) / tot)
            res = np.array(res)
            print(f"MARGINAL adding-up, {flow}: |bilateral marginal - country total| / total  "
                  f"p50 {100*np.median(res):.2f}%  p95 {100*np.percentile(res,95):.2f}%  max {100*res.max():.2f}%")
        print()
    for label, getter, flow in [("EXPORT (outbound -> country export dist)", outbound, "export"),
                                ("IMPORT (inbound  -> country import dist)", inbound, "import")]:
        ks, w1, cov = recompose(label, getter, flow)
        print(f"{label}  ({len(ks)} country-years)")
        print(f"  recomposition vs country GMM:  KS  p50 {100*np.median(ks):.1f}%  p95 {100*np.percentile(ks,95):.1f}%"
              f"   |  W1 p50 {np.median(w1):.3f}  p95 {np.percentile(w1,95):.3f} PCI")
        print(f"  coverage (encoded corridor value / country total): p50 {100*np.median(cov):.1f}%  "
              f"p10 {100*np.percentile(cov,10):.1f}%\n")


if __name__ == "__main__":
    main()
