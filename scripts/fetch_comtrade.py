"""Pull HS4 export data from UN Comtrade into an Atlas-schema CSV.

For each requested country we pull its own exports (direct); if it has not filed the
requested year, we fall back to a MIRROR reconstruction (partners' imports from it).
HS4 codes are mapped to Atlas HS92 and joined to a PCI proxy (default Atlas 2024).

Usage:
  set COMTRADE_API_KEY=...                 # free registered key (recommended)
  python scripts/fetch_comtrade.py --year 2025 --reporters top30
  python scripts/fetch_comtrade.py --year 2025 --reporters CHN,USA,DEU --mode auto

Output: data/raw/comtrade_hs4_<year>.csv  (git-ignored, Atlas-like schema + provenance)
Without a key it uses the free preview endpoint (capped at 500 rows/call -> truncated;
smoke-test only). 2025 world totals are incomplete (late filers), so shares computed
from a partial year are provisional -- see docs/comtrade.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg, comtrade as ct


def resolve_reporters(spec: str) -> list[str]:
    if spec.lower() in ("top30", "top", "atlas"):
        # reuse the Atlas ranking so the Comtrade pull matches the tracked set
        from gec import data as gdata
        df = gdata.load_clean()
        return gdata.ranked_exporters(df)[:cfg.N_TOP]
    return [s.strip().upper() for s in spec.split(",") if s.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--reporters", default="top30", help="'top30' or comma ISO3 list")
    ap.add_argument("--mode", choices=["auto", "direct", "mirror"], default="auto")
    ap.add_argument("--pci-year", type=int, default=2024, help="Atlas vintage for PCI proxy")
    ap.add_argument("--check", action="store_true",
                    help="only report each reporter's latest filed year (no-key) and exit")
    args = ap.parse_args()

    cfg.ensure_dirs()
    reporters = resolve_reporters(args.reporters)

    if args.check:
        print(f"Filing status (free /getDA, no key) - requested year {args.year}:")
        for iso3 in reporters:
            ys = ct.published_years(iso3)
            latest = ys[-1] if ys else None
            mark = "filed" if args.year in ys else ("MIRROR (not filed)" if ys else "NON-REPORTER")
            print(f"  {iso3:4s} latest={latest}  {args.year}->{mark}")
        return

    key = ct.api_key()
    print(f"Comtrade key: {'present' if key else 'NONE (preview, <=500 rows/call)'}")
    print(f"year={args.year}  mode={args.mode}  reporters={len(reporters)}: {', '.join(reporters)}")

    records = []
    for iso3 in reporters:
        # decide direct vs mirror from no-key availability, not trial-and-error
        filed = args.year in ct.published_years(iso3) if args.mode == "auto" else None
        use_direct = args.mode == "direct" or (args.mode == "auto" and filed)
        prov, df = "direct", None
        if use_direct:
            df = ct.fetch_country_exports(args.year, iso3, key)
        if (df is None or df.empty) and args.mode in ("auto", "mirror"):
            df, n = ct.fetch_mirror_exports(args.year, iso3, key)
            prov = f"mirror(n={n})"
        tot = 0.0 if df is None or df.empty else df["value"].sum()
        print(f"  {iso3:4s} {prov:14s} ${tot/1e9:9.1f}B")
        records.append((iso3, df, prov))

    out, report = ct.assemble(records, args.year, args.pci_year)
    out_path = cfg.RAW_DIR / f"comtrade_hs4_{args.year}.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}  ({len(out):,} rows)")
    print("provenance / HS92 match coverage:")
    for iso3, r in report["countries"].items():
        print(f"  {iso3:4s} {r['provenance']:14s} total=${r['total']/1e9:8.1f}B "
              f"matched_to_HS92={r['matched_pct']}%")
    (cfg.RAW_DIR / f"comtrade_hs4_{args.year}.report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
