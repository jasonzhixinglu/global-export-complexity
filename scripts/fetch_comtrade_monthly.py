"""Fetch monthly bilateral flows for the AI-compute HS6 codes from UN Comtrade.

Backbone of the monthly panel (see docs/tdm.md for the TDM supplement): all reporters,
all partners, HS 847150/847180/847330, monthly 2020-01 onward, both flows. One API call
covers 12 periods x all reporters x 3 codes (well under the 100k row cap), so the whole
pull is ~14 batches - minutes of quota. Requires COMTRADE_API_KEY in .env; uses the
secondary key as fallback if the primary hits its daily cap.

Output: data/raw/comtrade_monthly/<flow>_<firstperiod>_<lastperiod>.parquet (per-batch
caches; re-running skips existing batches).
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import pandas as pd
import comtradeapicall as ctc

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import comtrade as ct
from gec import config as cfg

CODES = "847150,847180,847330"
BEGIN, END = "2020-01", "2026-06"
OUT_DIR = cfg.RAW_DIR / "comtrade_monthly"
KEEP_COLS = ["period", "reporterCode", "reporterISO", "flowCode", "partnerCode",
             "partnerISO", "cmdCode", "primaryValue", "netWgt", "qty", "qtyUnitAbbr"]


def periods():
    return [p.strftime("%Y%m") for p in pd.period_range(BEGIN, END, freq="M")]


def batches(seq, n=4):  # 12-month batches hit the 100k row cap on flow M
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def keys():
    ks = [ct.api_key()]
    envf = cfg.ROOT / ".env"
    for line in envf.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("COMTRADE_API_KEY_SECONDARY="):
            ks.append(line.split("=", 1)[1].strip())
    return [k for k in ks if k]


def fetch_batch(key, flow, period_list):
    return ctc.getFinalData(
        key, typeCode="C", freqCode="M", clCode="HS", period=",".join(period_list),
        reporterCode=None, cmdCode=CODES, flowCode=flow, partnerCode=None,
        partner2Code="0", customsCode="C00", motCode="0", maxRecords=100000,
        format_output="JSON", breakdownMode="classic", includeDesc=False)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ks = keys()
    ki = 0
    for flow in ["M", "X"]:
        for chunk in batches(periods()):
            out = OUT_DIR / f"{flow}_{chunk[0]}_{chunk[-1]}.parquet"
            if out.exists():
                print(f"cached {out.name}")
                continue
            for attempt in range(4):
                try:
                    df = fetch_batch(ks[ki], flow, chunk)
                    break
                except Exception as e:
                    print(f"  attempt {attempt}: {e}; rotating key / retrying")
                    ki = (ki + 1) % len(ks)
                    time.sleep(5)
            else:
                sys.exit(f"failed batch {flow} {chunk[0]}")
            if df is None or len(df) == 0:
                print(f"  {flow} {chunk[0]}-{chunk[-1]}: EMPTY")
                pd.DataFrame(columns=KEEP_COLS).to_parquet(out, index=False)
                continue
            if len(df) >= 100000:
                sys.exit(f"row cap hit on {flow} {chunk[0]} -- split the batch")
            cols = [c for c in KEEP_COLS if c in df.columns]
            df[cols].to_parquet(out, index=False)
            print(f"  {flow} {chunk[0]}-{chunk[-1]}: {len(df)} rows -> {out.name}", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
