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
        {"id": "ai", "label": "AI compute", "parent": "all", "codes": list(cl.AI_COMPUTE_FED)},
    ]
    for group, codes in cl.SEMICONDUCTOR_OECD.items():  # AI compute leads, then the OECD stages
        slug = "semi_" + group.lower().split()[0]
        baskets.append({"id": slug, "label": group, "parent": "all", "codes": list(codes)})

    union = sorted({c for b in baskets for c in b["codes"]})
    union_set = set(union)
    ship_set = set(ship)

    FLOWS = ["export", "import"]
    VCOL = {"export": "export_value", "import": "import_value"}
    # stream HS12: keep basket rows AND accumulate each shipped country's TOTAL exports+imports/year
    keep, totals = [], []
    for ch in pd.read_csv(cfg.HS12_HS6_CSV,
                          usecols=["country_iso3_code", "product_hs12_code", "year", "export_value", "import_value"],
                          dtype={"country_iso3_code": str, "product_hs12_code": str},
                          chunksize=3_000_000):
        for c in ("export_value", "import_value"):
            ch[c] = pd.to_numeric(ch[c], errors="coerce").fillna(0.0)
        st = ch[ch["country_iso3_code"].isin(ship_set)]
        totals.append(st.groupby(["country_iso3_code", "year"])[["export_value", "import_value"]].sum())
        bk = ch[ch["product_hs12_code"].isin(union_set)]
        if len(bk):
            keep.append(bk)
    df = pd.concat(keep, ignore_index=True)
    df["year"] = df["year"].astype(int)
    ctot = pd.concat(totals).groupby(level=[0, 1]).sum()  # (iso, year) -> total export+import
    years = sorted(int(y) for y in df["year"].unique())
    print(f"basket rows: {len(df):,} | years {years[0]}-{years[-1]} | codes {df.product_hs12_code.nunique()}/{len(union)}")

    value = {fl: {} for fl in FLOWS}
    worldB = {fl: {} for fl in FLOWS}
    for fl in FLOWS:
        vcol = VCOL[fl]
        for b in baskets:
            sub = df[df["product_hs12_code"].isin(set(b["codes"]))]
            wt = sub.groupby("year")[vcol].sum()
            cv = sub[sub["country_iso3_code"].isin(ship)].groupby(["country_iso3_code", "year"])[vcol].sum()
            worldB[fl][b["id"]] = {str(y): r(wt.get(y, 0) / 1e9) for y in years}
            d = {}
            for iso in ship:
                ser = {str(y): r(cv.get((iso, y), 0) / 1e9) for y in years}
                if any(v for v in ser.values()):
                    d[iso] = ser
            value[fl][b["id"]] = d

    country_total = {}
    for fl in FLOWS:
        vcol = VCOL[fl]
        country_total[fl] = {iso: {str(y): r(ctot[vcol].get((iso, y), 0) / 1e9) for y in years} for iso in ship}

    out = {
        "baskets": [{"id": b["id"], "label": b["label"], "parent": b["parent"], "nCodes": len(b["codes"])} for b in baskets],
        "years": years,
        "countries": ship,
        "flows": FLOWS,
        "valueB": value,         # value[flow][basket][iso][year] in $B
        "worldB": worldB,        # world total[flow][basket][year] in $B
        "countryTotalB": country_total,  # each country's TOTAL trade[flow][iso][year] ($B)
        "note": "HS2012; AI compute = Fed FEDS 2026-02; semiconductors = OECD 2025 value chain.",
        "missingCodes": [c for c in union if c not in set(df["product_hs12_code"].unique())],
    }
    (OUT / "techai.json").write_text(json.dumps(out))
    sz = (OUT / "techai.json").stat().st_size / 1024
    print(f"wrote techai.json: {sz:.0f} KB | baskets {len(baskets)} | countries {len(ship)} | flows {FLOWS}")


if __name__ == "__main__":
    main()
