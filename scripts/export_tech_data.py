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
    # "All" = OECD semiconductor value chain + Fed AI compute (disjoint, no double-count).
    # Sub-categories = the 6 OECD stages + AI compute.
    all_codes = list(cl.semiconductor_hs6()) + list(cl.AI_COMPUTE_FED)
    baskets = [
        {"id": "all", "label": "All (semiconductors + AI)", "parent": None, "codes": all_codes},
    ]
    for group, codes in cl.SEMICONDUCTOR_OECD.items():
        slug = "semi_" + group.lower().split()[0]
        baskets.append({"id": slug, "label": group, "parent": "all", "codes": list(codes)})
    baskets.append({"id": "ai", "label": "AI compute", "parent": "all", "codes": list(cl.AI_COMPUTE_FED)})

    union = sorted({c for b in baskets for c in b["codes"]})
    union_set = set(union)
    ship_set = set(ship)

    # stream HS12: keep basket rows AND accumulate each shipped country's TOTAL exports/year
    keep, totals = [], []
    for ch in pd.read_csv(cfg.HS12_HS6_CSV,
                          usecols=["country_iso3_code", "product_hs12_code", "year", "export_value"],
                          dtype={"country_iso3_code": str, "product_hs12_code": str},
                          chunksize=3_000_000):
        ch["export_value"] = pd.to_numeric(ch["export_value"], errors="coerce")
        ch = ch.dropna(subset=["export_value"])
        st = ch[ch["country_iso3_code"].isin(ship_set)]
        totals.append(st.groupby(["country_iso3_code", "year"])["export_value"].sum())
        bk = ch[ch["product_hs12_code"].isin(union_set)]
        if len(bk):
            keep.append(bk)
    df = pd.concat(keep, ignore_index=True)
    df["year"] = df["year"].astype(int)
    ctot = pd.concat(totals).groupby(level=[0, 1]).sum()  # (iso, year) -> total exports
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

    country_total = {iso: {str(y): r(ctot.get((iso, y), 0) / 1e9) for y in years} for iso in ship}

    out = {
        "baskets": [{"id": b["id"], "label": b["label"], "parent": b["parent"], "nCodes": len(b["codes"])} for b in baskets],
        "years": years,
        "countries": ship,
        "valueB": value,    # value[basket][iso][year] in $B
        "worldB": worldB,   # world total[basket][year] in $B (denominator for world share)
        "countryTotalB": country_total,  # each country's TOTAL exports/year (for 'share of own exports')
        "note": "HS2012; AI compute = Fed FEDS 2026-02; semiconductors = OECD 2025 value chain.",
        "missingCodes": [c for c in union if c not in set(df["product_hs12_code"].unique())],
    }
    (OUT / "techai.json").write_text(json.dumps(out))
    sz = (OUT / "techai.json").stat().st_size / 1024
    print(f"wrote techai.json: {sz:.0f} KB | baskets {len(baskets)} | countries shipped {len(ship)}")


if __name__ == "__main__":
    main()
