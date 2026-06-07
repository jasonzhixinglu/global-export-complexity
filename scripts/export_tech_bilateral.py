"""Bilateral tech trade-network data (HS6) for the Tech & AI tab's Corridors view.

Built from the HS2012 BILATERAL files (hs12_country_country_product_year_6_*, 2012-2024),
whose 6-digit codes match the OECD/Fed baskets exactly -- unlike the HS92 bilateral, whose
semiconductor subcodes diverged (e.g. ICs are 8542.31/32/33/39 in HS2012 vs 8542.11/19 in HS92),
which is why this needs the HS2012 vintage rather than the HS4 approximation.

Filters to the OECD value-chain + Fed AI-compute HS6 codes, aggregates to (origin bloc x dest bloc
x basket x year) for the top-N displayed countries + a ROW bloc.  Per-range parquet caches make the
multi-GB read resumable.

Output: dashboard/public/data/techai_bilateral.json
  { baskets:[{id,label,parent}], blocs (value-ranked, ROW last), years, flow:"export",
    value: { basketId: { origin: { destination: { year: $B } } } } }
Run:  python scripts/export_tech_bilateral.py   (needs the hs12 bilateral CSVs downloaded)
"""
from __future__ import annotations
import gzip, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec import classifications as cls

OUT = cfg.ROOT / "dashboard" / "public" / "data"
DERIVED = cfg.DATA_DIR / "derived"
ROW = "ROW"

# OECD value-chain stages + Fed AI compute -> per-code basket id; "all" is their union.
GROUPS = [("chips", "Chips"), ("photo", "Photosensitive devices"), ("raw", "Raw materials"),
          ("equip", "Manufacturing equipment"), ("foundry", "Foundry inputs"), ("wafer", "Wafer inputs")]
CODE_BASKET = {}
for gid, glabel in GROUPS:
    for c in cls.SEMICONDUCTOR_OECD[glabel]:
        CODE_BASKET[c] = gid
for c in cls.AI_COMPUTE_FED:
    CODE_BASKET[c] = "ai"
ALL_CODES = set(CODE_BASKET)
BASKET_META = ([{"id": "all", "label": "All", "parent": None}]
               + [{"id": gid, "label": lbl, "parent": "all"} for gid, lbl in GROUPS]
               + [{"id": "ai", "label": "AI compute", "parent": "all"}])


def read_range(yr_range, top, chunksize=2_000_000):
    cache = DERIVED / f"hs12bil_blocs_top{len(top)}_{yr_range}.parquet"
    if cache.exists():
        print(f"  cached {yr_range}", flush=True)
        return pd.read_parquet(cache)
    path = cfg.hs12_bilateral_path(yr_range)
    if not path.exists():
        raise FileNotFoundError(f"{path} - download datafile {cfg.HS12_BILATERAL_FILE_IDS[yr_range]}")
    head = pd.read_csv(path, nrows=0)
    pcol = next(c for c in head.columns if c.startswith("product_") and c.endswith("_code"))
    topset = set(top)
    parts, n = [], 0
    for chunk in pd.read_csv(path, usecols=["country_iso3_code", "partner_iso3_code", pcol, "year", "export_value"],
                             dtype={"country_iso3_code": str, "partner_iso3_code": str, pcol: str},
                             chunksize=chunksize):
        chunk["hs6"] = chunk[pcol].str.zfill(6)
        chunk = chunk[chunk["hs6"].isin(ALL_CODES)]
        if chunk.empty:
            continue
        chunk["export_value"] = pd.to_numeric(chunk["export_value"], errors="coerce")
        chunk = chunk.dropna(subset=["export_value"])
        chunk = chunk[chunk["export_value"] > 0]
        chunk["o"] = np.where(chunk.country_iso3_code.isin(topset), chunk.country_iso3_code, ROW)
        chunk["d"] = np.where(chunk.partner_iso3_code.isin(topset), chunk.partner_iso3_code, ROW)
        chunk["basket"] = chunk["hs6"].map(CODE_BASKET)
        chunk["year"] = chunk["year"].astype(int)
        parts.append(chunk.groupby(["o", "d", "basket", "year"], as_index=False)["export_value"].sum())
        n += len(chunk)
    out = (pd.concat(parts, ignore_index=True).groupby(["o", "d", "basket", "year"], as_index=False)["export_value"].sum()
           if parts else pd.DataFrame(columns=["o", "d", "basket", "year", "export_value"]))
    DERIVED.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache)
    print(f"  read {yr_range}: {n:,} basket rows -> cached", flush=True)
    return out


def main():
    s = np.load(DERIVED / "surfaces.npz", allow_pickle=True)
    top = [str(c) for c in s["countries"]]
    print(f"HS2012 bilateral tech corridors: top-{len(top)} + ROW", flush=True)
    df = pd.concat([read_range(r, top) for r in cfg.HS12_BILATERAL_FILE_IDS], ignore_index=True)
    df = df.groupby(["o", "d", "basket", "year"], as_index=False)["export_value"].sum()
    years = sorted(int(y) for y in df["year"].unique())
    tot = df.groupby("o")["export_value"].sum()
    blocs = [b for b in tot.sort_values(ascending=False).index if b != ROW]
    if ROW in set(df["o"]) | set(df["d"]):
        blocs.append(ROW)

    # nested value dict per basket; "all" = sum across the sub-baskets
    value = {bm["id"]: {} for bm in BASKET_META}
    for r in df.itertuples():
        v = round(float(r.export_value) / 1e9, 4)
        if v <= 0:
            continue
        for bid in (r.basket, "all"):
            value[bid].setdefault(r.o, {}).setdefault(r.d, {})[str(int(r.year))] = \
                round(value[bid].get(r.o, {}).get(r.d, {}).get(str(int(r.year)), 0) + v, 4)

    payload = {"baskets": BASKET_META, "blocs": blocs, "years": years, "flow": "export", "value": value}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "techai_bilateral.json").write_text(json.dumps(payload))
    raw = (OUT / "techai_bilateral.json").stat().st_size
    gz = len(gzip.compress((OUT / "techai_bilateral.json").read_bytes(), 6))
    print(f"\nwrote techai_bilateral.json: raw {raw/1e6:.2f} MB  gz {gz/1e6:.2f} MB  "
          f"({len(blocs)} blocs, {years[0]}-{years[-1]})")
    for bm in BASKET_META:
        w = sum(d.get(str(years[-1]), 0) for o in value[bm["id"]].values() for d in o.values())
        print(f"  {bm['label']:<24} world {w:.0f} $B ({years[-1]})")


if __name__ == "__main__":
    main()
