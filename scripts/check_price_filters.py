"""Sensitivity of the price results to every filter in the pipeline.

Reruns the whole chain with one filter disabled at a time and reports what moves.
A filter that changes nothing is dead weight and should go; a filter that changes
everything needs a better justification than the author's judgement. Run it after
touching any threshold.

  python scripts/check_price_filters.py            # all variants (slow, ~30 min)
  python scripts/check_price_filters.py compute    # only the ones needing no rebuild

Writes results/tables/price_filter_sensitivity.csv.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gec import config as cfg

MAJORS = cfg.CHAIN_MAJORS
LAST = "202606"
BUILD = [sys.executable, str(ROOT / "scripts" / "build_unit_values.py")]
COMPUTE = [sys.executable, str(ROOT / "scripts" / "compute_prices_net_exports.py")]

# (label, env overrides, needs a rebuild of the unit-value base)
VARIANTS = [
    ("base", {}, True),
    ("no outlier screen", {"GEC_OUTLIER_LOG": "99"}, True),
    ("no degeneracy test", {"GEC_DEGEN": "0"}, True),
    ("weight only (no qty)", {"GEC_QTY": "0"}, True),
    ("no usable-month guard", {"GEC_USABLE": "0"}, False),
    ("no cell floor", {"GEC_MIN_CELL": "0"}, False),
    ("no step trim", {"GEC_MAX_DLN": "99"}, False),
    ("no matched-share rule", {"GEC_MIN_MATCHED": "0"}, False),
]


def run(env, rebuild):
    e = {**os.environ, **env}
    if rebuild:
        subprocess.run(BUILD, cwd=ROOT, env=e, check=True, capture_output=True)
    subprocess.run(COMPUTE, cwd=ROOT, env=e, check=True, capture_output=True)
    t = pd.read_csv(cfg.RESULTS_DIR / "tables" / "terms_of_trade.csv", dtype={"period": str})
    t = t[(t.freq == "roll12") & (t.period == LAST)].set_index("iso")
    return t.tot_2021.reindex(MAJORS).round(0)


def main():
    only = "compute" in sys.argv[1:]
    out = {}
    for label, env, rebuild in VARIANTS:
        if only and rebuild and label != "base":
            continue
        print(f"running: {label} ...", flush=True)
        out[label] = run(env, rebuild)
    df = pd.DataFrame(out)
    base = df["base"]
    for c in df.columns[1:]:
        df[c + " Δ"] = (df[c] - base).round(0)
    df.to_csv(cfg.RESULTS_DIR / "tables" / "price_filter_sensitivity.csv")
    print()
    print(f"Terms of trade at {LAST} (2021 avg = 100), by variant:")
    print(df[[c for c in df.columns if not c.endswith("Δ")]].to_string())
    print()
    print("largest move per variant (index points):")
    for c in df.columns:
        if c.endswith("Δ"):
            d = df[c].abs()
            print(f"  {c[:-2]:<24} max |Δ| {d.max():>5.0f}   median |Δ| {d.median():>4.0f}")


if __name__ == "__main__":
    main()
