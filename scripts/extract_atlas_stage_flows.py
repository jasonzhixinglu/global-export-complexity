"""Extract Atlas HS6 bilateral flows for the 60 supply-chain codes, all countries.

The 2024 stage charts read this so every stage comes from ONE source (Atlas,
reconciled, annual, full country coverage) instead of mixing Atlas upstream
with our monthly panel downstream. Unlike bilateral_semi_2017_2024.parquet
(built for the panel audit) this keeps EVERY country, not just the panel's 30,
so small exporters are not forced into ROW.

Output: data/derived/atlas_stage_flows.parquet
        columns exporter, importer, code, year, value
"""
from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as O

CODES = {"847150", "847180", "847330"} | {
    c for g, d in O.items() if g != "Photosensitive devices" for c in d}
YEARS = tuple(range(2020, 2025))   # 2024 for the charts; 2020-24 pooled for hubs
SRC = [cfg.RAW_DIR / "hs12_country_country_product_year_6_2020_2024.csv"]
OUT = cfg.DATA_DIR / "derived" / "atlas_stage_flows.parquet"


def main():
    parts = []
    for path in SRC:
        for chunk in pd.read_csv(path, usecols=["country_iso3_code", "partner_iso3_code",
                                                "product_hs12_code", "year", "export_value"],
                                 dtype={"product_hs12_code": str}, chunksize=3_000_000):
            sel = chunk[chunk.product_hs12_code.isin(CODES) & chunk.year.isin(YEARS)]
            sel = sel[(sel.export_value > 0) & sel.country_iso3_code.notna()
                      & sel.partner_iso3_code.notna()]
            if len(sel):
                parts.append(sel.rename(columns={
                    "country_iso3_code": "exporter", "partner_iso3_code": "importer",
                    "product_hs12_code": "code", "export_value": "value"}))
    df = pd.concat(parts, ignore_index=True)
    df = df.groupby(["exporter", "importer", "code", "year"], as_index=False).value.sum()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    t = df[df.year == 2024]
    print(f"-> {OUT}: {len(df):,} rows, {df.code.nunique()} codes, "
          f"{df.exporter.nunique()} exporters")
    print(f"   2024 total ${t.value.sum()/1e12:.2f}T; compute codes "
          + ", ".join(f"{c} ${t[t.code == c].value.sum()/1e9:.0f}B"
                      for c in ("847330", "847180", "847150")))


if __name__ == "__main__":
    main()
