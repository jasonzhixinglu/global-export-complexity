"""Fetch monthly bilateral flows for the supply-chain HS6 codes from UN Comtrade.

Backbone of the monthly panel (see docs/data.md for the TDM supplement): all
reporters, all partners, monthly 2020-01 onward, both flows.

Code groups (docs/data.md taxonomy; OECD lists in src/gec/classifications.py):
  compute        847150/847180/847330 (Fed AI-compute codes -- the original panel)
  chips_core     854231/32/39 (the big three IC codes, ~83% of stage-5 value)
  chips_rest     remaining 13 OECD "Chips" codes
  equip_semi     8486xx + semiconductor metrology (the semi-specific equipment)
  equip_generic  fans / heat exchangers / filtration (dual-use fab-plant codes)
  foundry        litho & optics inputs      wafer  wafer inputs      raw  raw materials

Batch length per group is set by row density (dense IC codes need 1-month
batches); any batch that still hits the 100k row cap is split recursively --
first by period, then by code -- so no pull dies on the cap. Requires
COMTRADE_API_KEY in .env; rotates to the secondary key on failure.

Output: data/raw/comtrade_monthly/<group>_<flow>_<first>_<last>.parquet
(per-batch caches; re-running skips existing batches; the compute group keeps
its legacy unprefixed filenames).

Usage:
  python scripts/fetch_comtrade_monthly.py                  # compute (legacy)
  python scripts/fetch_comtrade_monthly.py semi             # all 57 new codes
  python scripts/fetch_comtrade_monthly.py chips_core raw   # specific groups
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
from gec.classifications import SEMICONDUCTOR_OECD as OECD

BEGIN, END = "2020-01", "2026-06"
OUT_DIR = cfg.RAW_DIR / "comtrade_monthly"
KEEP_COLS = ["period", "reporterCode", "reporterISO", "flowCode", "partnerCode",
             "partnerISO", "cmdCode", "primaryValue", "netWgt", "qty", "qtyUnitAbbr"]

CHIPS_CORE = ["854231", "854232", "854239"]
EQUIP_GENERIC = ["841459", "841950", "842129", "842139", "842199"]
# group -> (codes, months per batch)
GROUPS = {
    "compute": (["847150", "847180", "847330"], 4),
    "chips_core": (CHIPS_CORE, 1),
    "chips_rest": (sorted(set(OECD["Chips"]) - set(CHIPS_CORE)), 1),
    "equip_semi": (sorted(set(OECD["Manufacturing equipment"]) - set(EQUIP_GENERIC)), 2),
    "equip_generic": (EQUIP_GENERIC, 1),
    "foundry": (sorted(OECD["Foundry inputs"]), 2),
    "wafer": (sorted(OECD["Wafer inputs"]), 4),
    "raw": (sorted(OECD["Raw materials"]), 3),
}
SEMI_GROUPS = [g for g in GROUPS if g != "compute"]


def periods():
    return [p.strftime("%Y%m") for p in pd.period_range(BEGIN, END, freq="M")]


def batches(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def keys():
    ks = [ct.api_key()]
    envf = cfg.ROOT / ".env"
    for line in envf.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("COMTRADE_API_KEY_SECONDARY="):
            ks.append(line.split("=", 1)[1].strip())
    return [k for k in ks if k]


class Puller:
    def __init__(self):
        self.ks = keys()
        self.ki = 0

    def call(self, flow, period_list, codes):
        for attempt in range(4):
            try:
                df = ctc.getFinalData(
                    self.ks[self.ki], typeCode="C", freqCode="M", clCode="HS",
                    period=",".join(period_list), reporterCode=None,
                    cmdCode=",".join(codes), flowCode=flow, partnerCode=None,
                    partner2Code="0", customsCode="C00", motCode="0",
                    maxRecords=100000, format_output="JSON",
                    breakdownMode="classic", includeDesc=False)
                time.sleep(1)
                return df
            except Exception as e:
                print(f"  attempt {attempt}: {e}; rotating key / retrying", flush=True)
                self.ki = (self.ki + 1) % len(self.ks)
                time.sleep(5)
        raise RuntimeError(f"failed batch {flow} {period_list[0]}")

    def fetch(self, flow, period_list, codes):
        """Fetch, splitting recursively (periods first, then codes) on the row cap."""
        df = self.call(flow, period_list, codes)
        if df is None or len(df) < 100000:
            return df if df is not None else pd.DataFrame(columns=KEEP_COLS)
        if len(period_list) > 1:
            mid = len(period_list) // 2
            print(f"  cap hit ({flow} {period_list[0]}..{period_list[-1]}): "
                  "splitting by period", flush=True)
            return pd.concat([self.fetch(flow, period_list[:mid], codes),
                              self.fetch(flow, period_list[mid:], codes)])
        if len(codes) > 1:
            mid = len(codes) // 2
            print(f"  cap hit ({flow} {period_list[0]}, {len(codes)} codes): "
                  "splitting by code", flush=True)
            return pd.concat([self.fetch(flow, period_list, codes[:mid]),
                              self.fetch(flow, period_list, codes[mid:])])
        raise RuntimeError(f"single code {codes[0]} {period_list[0]} exceeds row cap")


def run_group(puller, group):
    codes, span = GROUPS[group]
    prefix = "" if group == "compute" else f"{group}_"
    print(f"=== {group}: {len(codes)} codes, {span}-month batches ===", flush=True)
    for flow in ["M", "X"]:
        for chunk in batches(periods(), span):
            out = OUT_DIR / f"{prefix}{flow}_{chunk[0]}_{chunk[-1]}.parquet"
            if out.exists():
                continue
            df = puller.fetch(flow, chunk, codes)
            if len(df) == 0:
                print(f"  {flow} {chunk[0]}-{chunk[-1]}: EMPTY", flush=True)
                pd.DataFrame(columns=KEEP_COLS).to_parquet(out, index=False)
                continue
            cols = [c for c in KEEP_COLS if c in df.columns]
            df[cols].to_parquet(out, index=False)
            print(f"  {flow} {chunk[0]}-{chunk[-1]}: {len(df)} rows", flush=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:] or ["compute"]
    if args == ["semi"]:
        args = SEMI_GROUPS
    unknown = [a for a in args if a not in GROUPS]
    if unknown:
        sys.exit(f"unknown group(s) {unknown}; choose from {list(GROUPS)} or 'semi'")
    puller = Puller()
    for group in args:
        run_group(puller, group)


if __name__ == "__main__":
    main()
