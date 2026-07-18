"""Extract HS 847330 (parts/accessories of 8471 ADP machines) bilateral flows 2020-2024
from the HS2012 bilateral file into a small parquet cache for the matrix-factor prototype."""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

CODE = "847330"
OUT = cfg.DATA_DIR / "derived" / f"bilateral_{CODE}_2020_2024.parquet"

def main():
    if OUT.exists():
        print(f"cached: {OUT}")
        return
    path = cfg.hs12_bilateral_path("2020_2024")
    cols = ["country_iso3_code", "partner_iso3_code", "product_hs12_code", "year", "export_value"]
    head = pd.read_csv(path, nrows=0)
    pcol = next(c for c in head.columns if c.startswith("product_") and c.endswith("_code"))
    cols = ["country_iso3_code", "partner_iso3_code", pcol, "year", "export_value"]
    parts, n = [], 0
    for chunk in pd.read_csv(path, usecols=cols, dtype={pcol: str}, chunksize=3_000_000):
        n += len(chunk)
        sel = chunk[chunk[pcol] == CODE]
        if len(sel):
            parts.append(sel.drop(columns=[pcol]))
        print(f"  scanned {n/1e6:.0f}M rows, kept {sum(len(p) for p in parts)}", flush=True)
    df = pd.concat(parts, ignore_index=True)
    df = df.rename(columns={"country_iso3_code": "exporter", "partner_iso3_code": "importer"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT}: {len(df)} rows, years {sorted(df.year.unique())}, "
          f"total value ${df.export_value.sum()/1e9:.1f}B")

if __name__ == "__main__":
    main()
