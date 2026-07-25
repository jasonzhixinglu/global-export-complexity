"""Fetch annual AGGREGATE bilateral trade totals (all products) from UN Comtrade.

These feed the two Growth Lab mirroring steps that their paper estimates at the
aggregate importer-exporter level rather than per product (GL WP 251, Steps 2-3):

  Step 2  CIF-to-FOB: the regression is fit on importer reports that carry BOTH
          cifvalue and fobvalue for the same flow -- the only direct observation
          of freight cost. (~23% of import rows have both.)
  Step 3  Reliability scores: pair discrepancies computed on total bilateral
          trade, "to avoid concordance issues ... we use data only at the
          aggregate importer-exporter level".

One call per (year, flow); cmdCode=TOTAL keeps every call far under the row cap.

Output: data/raw/comtrade_totals/<flow>_<year>.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
import fetch_comtrade_monthly as fcm   # reuse the quota-aware puller

YEARS = [str(y) for y in range(2017, 2026)]
OUT_DIR = cfg.RAW_DIR / "comtrade_totals"
KEEP_COLS = ["period", "reporterCode", "reporterISO", "flowCode", "partnerCode",
             "partnerISO", "cifvalue", "fobvalue", "primaryValue"]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    puller = fcm.Puller()
    for flow in ["M", "X"]:
        for year in YEARS:
            out = OUT_DIR / f"{flow}_{year}.parquet"
            if out.exists():
                continue
            df = puller.call(flow, [year], ["TOTAL"], freq="A")
            if df is None or len(df) == 0:
                print(f"  {flow} {year}: EMPTY", flush=True)
                pd.DataFrame(columns=KEEP_COLS).to_parquet(out, index=False)
                continue
            cols = [c for c in KEEP_COLS if c in df.columns]
            df[cols].to_parquet(out, index=False)
            both = ((df.get("cifvalue", pd.Series(dtype=float)).fillna(0) > 0) &
                    (df.get("fobvalue", pd.Series(dtype=float)).fillna(0) > 0)).sum()
            print(f"  {flow} {year}: {len(df)} rows ({both} with cif+fob)", flush=True)


if __name__ == "__main__":
    main()
