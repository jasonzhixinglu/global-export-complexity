"""Compute AI / semiconductor basket export shares from HS12 HS6 data -> compact JSON.

The 463 MB HS12 file stays server-side; the dashboard receives only per-country-year value
and world totals for each basket (share is computed client-side). See classifications.py.

Usage:  python scripts/export_tech_data.py   (after downloading hs12_country_product_year_6.csv)
Output: dashboard/public/data/techai.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg, classifications as cl

OUT = cfg.ROOT / "dashboard" / "public" / "data"


def r(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((OUT / "meta.json").read_text())
    ship = [c["iso3"] for c in meta["countries"]]  # per-country series we expose (tracked set)

    # basket definitions: AI compute, semiconductors total, and the 6 OECD sub-categories
    baskets = [
        {"id": "ai", "label": "AI compute (Fed)", "parent": None, "codes": list(cl.AI_COMPUTE_FED)},
        {"id": "semi", "label": "Semiconductors — all (OECD)", "parent": None,
         "codes": list(cl.semiconductor_hs6())},
    ]
    for group, codes in cl.SEMICONDUCTOR_OECD.items():
        slug = "semi_" + group.lower().split()[0]
        baskets.append({"id": slug, "label": group, "parent": "semi", "codes": list(codes)})

    union = sorted({c for b in baskets for c in b["codes"]})
    union_set = set(union)

    # stream HS12, keep only basket codes
    keep = []
    for ch in pd.read_csv(cfg.HS12_HS6_CSV,
                          usecols=["country_iso3_code", "product_hs12_code", "year", "export_value"],
                          dtype={"country_iso3_code": str, "product_hs12_code": str},
                          chunksize=3_000_000):
        ch = ch[ch["product_hs12_code"].isin(union_set)]
        if len(ch):
            ch["export_value"] = pd.to_numeric(ch["export_value"], errors="coerce")
            keep.append(ch.dropna(subset=["export_value"]))
    df = pd.concat(keep, ignore_index=True)
    df["year"] = df["year"].astype(int)
    years = sorted(int(y) for y in df["year"].unique())
    print(f"basket rows: {len(df):,} | years {years[0]}-{years[-1]} | codes {df.product_hs12_code.nunique()}/{len(union)}")

    value, worldB = {}, {}
    for b in baskets:
        codes = set(b["codes"])
        sub = df[df["product_hs12_code"].isin(codes)]
        # world total per year (all countries), and per-tracked-country value per year
        wt = sub.groupby("year")["export_value"].sum()
        cv = sub[sub["country_iso3_code"].isin(ship)].groupby(["country_iso3_code", "year"])["export_value"].sum()
        worldB[b["id"]] = {str(y): r(wt.get(y, 0) / 1e9) for y in years}
        d = {}
        for iso in ship:
            s = {str(y): r(cv.get((iso, y), 0) / 1e9) for y in years}
            if any(v for v in s.values()):
                d[iso] = s
        value[b["id"]] = d

    out = {
        "baskets": [{"id": b["id"], "label": b["label"], "parent": b["parent"], "nCodes": len(b["codes"])} for b in baskets],
        "years": years,
        "countries": ship,
        "valueB": value,    # value[basket][iso][year] in $B
        "worldB": worldB,   # world total[basket][year] in $B (denominator for share)
        "note": "HS2012; AI compute = Fed FEDS 2026-02; semiconductors = OECD 2025 value chain.",
        "missingCodes": [c for c in union if c not in set(df["product_hs12_code"].unique())],
    }
    (OUT / "techai.json").write_text(json.dumps(out))
    sz = (OUT / "techai.json").stat().st_size / 1024
    print(f"wrote techai.json: {sz:.0f} KB | baskets {len(baskets)} | countries shipped {len(ship)}")


if __name__ == "__main__":
    main()
