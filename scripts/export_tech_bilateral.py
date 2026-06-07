"""Bilateral trade-network data for the Tech & AI tab's Corridors view.

Builds origin -> destination flows for a few clean HS4 tech product groups, reusing the
bloc-aggregated bilateral parquets already produced by export_gmm_bilateral.py (top-50 + ROW,
2000-2024). These are HS4 product groups labeled by code -- distinct from, and coarser than, the
precise HS6 OECD/Fed baskets used in the country "Totals" view (HS 8486 semiconductor equipment
is HS2012-only and absent from the HS92 bilateral, so it is not represented here).

Output: dashboard/public/data/techai_bilateral.json
  { baskets:[{id,label,codes}], blocs (value-ranked, ROW last), years, flow:"export",
    value: { basketId: { origin: { destination: { year: $B } } } } }
Run:  python scripts/export_tech_bilateral.py   (needs the bilateral_blocs_*.parquet caches)
"""
from __future__ import annotations
import glob, gzip, json, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg

DERIVED = cfg.DATA_DIR / "derived"
OUT = cfg.ROOT / "dashboard" / "public" / "data"

BASKETS = [
    {"id": "ic", "label": "Integrated circuits", "codes": ["8542"]},
    {"id": "compute", "label": "Computers & parts", "codes": ["8471", "8473"]},
    {"id": "telecom", "label": "Telecom equipment", "codes": ["8517"]},
    {"id": "semidev", "label": "Diodes/transistors/PV", "codes": ["8541"]},
]


def main():
    files = sorted(glob.glob(str(DERIVED / "bilateral_blocs_top50_*.parquet")))
    if not files:
        raise SystemExit("no bilateral_blocs_*.parquet — run scripts/export_gmm_bilateral.py first")
    df = pd.concat([pd.read_parquet(f, columns=["o", "d", "p4", "year", "export_value"]) for f in files],
                   ignore_index=True)
    years = sorted(int(y) for y in df["year"].unique())
    # bloc order: by total flow (desc), ROW last
    tot = df.groupby("o")["export_value"].sum()
    blocs = [b for b in tot.sort_values(ascending=False).index if b != "ROW"]
    if "ROW" in set(df["o"]) | set(df["d"]):
        blocs.append("ROW")

    value = {}
    for bk in BASKETS:
        sub = df[df["p4"].isin(bk["codes"])]
        g = sub.groupby(["o", "d", "year"])["export_value"].sum()
        d = {}
        for (o, dd, yr), v in g.items():
            if v > 0:
                d.setdefault(o, {}).setdefault(dd, {})[str(int(yr))] = round(float(v) / 1e9, 3)
        value[bk["id"]] = d

    payload = {
        "baskets": [{"id": b["id"], "label": b["label"], "codes": b["codes"]} for b in BASKETS],
        "blocs": blocs, "years": years, "flow": "export", "value": value,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "techai_bilateral.json").write_text(json.dumps(payload))
    raw = (OUT / "techai_bilateral.json").stat().st_size
    gz = len(gzip.compress((OUT / "techai_bilateral.json").read_bytes(), 6))
    print(f"wrote techai_bilateral.json: raw {raw/1e6:.2f} MB  gz {gz/1e6:.2f} MB  "
          f"({len(blocs)} blocs, {len(years)} yr, {len(BASKETS)} baskets)")
    for bk in BASKETS:
        w24 = sum(d.get("2024", 0) for o in value[bk["id"]].values() for d in o.values())
        print(f"  {bk['label']:<24} HS4 {'+'.join(bk['codes'])}: world {w24:.0f} $B (2024)")


if __name__ == "__main__":
    main()
