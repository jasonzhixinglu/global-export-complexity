"""Extract the Fed AI-compute HS6 codes (847150 AI servers, 847180 other ADP units,
847330 parts/GPU cards) bilateral flows 2020-2024 from the HS2012 bilateral file into
one parquet (with a `code` column) for the matrix-factor prototypes."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

CODES = ["847150", "847180", "847330"]
OUT = cfg.DATA_DIR / "derived" / "bilateral_ai_compute_2020_2024.parquet"

def main():
    if OUT.exists():
        print(f"cached: {OUT}")
        return
    path = cfg.hs12_bilateral_path("2020_2024")
    head = pd.read_csv(path, nrows=0)
    pcol = next(c for c in head.columns if c.startswith("product_") and c.endswith("_code"))
    cols = ["country_iso3_code", "partner_iso3_code", pcol, "year", "export_value"]
    parts, n = [], 0
    for chunk in pd.read_csv(path, usecols=cols, dtype={pcol: str}, chunksize=3_000_000):
        n += len(chunk)
        sel = chunk[chunk[pcol].isin(CODES)]
        if len(sel):
            parts.append(sel)
        print(f"  scanned {n/1e6:.0f}M rows, kept {sum(len(p) for p in parts)}", flush=True)
    df = pd.concat(parts, ignore_index=True)
    df = df.rename(columns={"country_iso3_code": "exporter", "partner_iso3_code": "importer",
                            pcol: "code"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT}: {len(df)} rows")
    print(df.groupby("code").export_value.sum().div(1e9).round(1).rename("$B"))

if __name__ == "__main__":
    main()
