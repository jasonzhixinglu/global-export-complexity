"""Fetch monthly bilateral AI-compute data from the Trade Data Monitor (TDM) API.

TDM's "Special Report - Download" form exposes a parameterized GET endpoint
(discovered via its "Generate API URL" button). Credentials come from the
git-ignored repo-root .env (TDM_USERNAME / TDM_PASSWORD) -- never commit them,
and never commit the raw extracts either (data/raw/tdm/ is git-ignored):
TDM is subscription-licensed data.

Standing pull set (see docs/data.md): Taiwan full history, China/Vietnam from
2024-01, exports + imports each, HS 847150/847180/847330.

Usage:
  python scripts/fetch_tdm.py            # the standing pull set (compute codes)
  python scripts/fetch_tdm.py semi       # standing reporters x the 57 new
                                         # supply-chain codes, one pull per group
  python scripts/fetch_tdm.py TW E 202001 202606   # one custom pull (compute codes)
"""
from __future__ import annotations
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as OECD

API = "https://www1.tdmlogin.com/tdm/api/api.asp"
CODES = "847150,847180,847330"
OUT_DIR = cfg.RAW_DIR / "tdm"

# Same group split as fetch_comtrade_monthly.py (keeps extract sizes sane and
# lets a failed pull re-run alone).
GROUPS = {
    "chips_core": ["854231", "854232", "854239"],
    "chips_rest": sorted(set(OECD["Chips"]) - {"854231", "854232", "854239"}),
    "equip_semi": sorted(set(OECD["Manufacturing equipment"])
                         - {"841459", "841950", "842129", "842139", "842199"}),
    "equip_generic": ["841459", "841950", "842129", "842139", "842199"],
    "foundry": sorted(OECD["Foundry inputs"]),
    "wafer": sorted(OECD["Wafer inputs"]),
    "raw": sorted(OECD["Raw materials"]),
}

# (reporter code, flow letter E/I, periodBegin, periodEnd). Codes are mostly ISO2;
# VN2 = "Vietnam (preliminary) 2", the only live Vietnam edition (plain VN is dead --
# not in the API spec workbook, which is outdated; VN2 found by probing after the
# edition showed up in the query dashboard).
STANDING = [
    ("TW", "E", "202001", "202606"), ("TW", "I", "202001", "202606"),
    ("CN", "E", "202401", "202606"), ("CN", "I", "202401", "202606"),
    ("VN2", "E", "202001", "202606"), ("VN2", "I", "202001", "202606"),
    # 2017-2019 backfill (sample cutoff 2017 = HS2017 vintage; disjoint period
    # ranges keep filenames distinct from the 2020+ extracts). VN2 is the
    # preliminary edition and may not reach back -- failures fall through to
    # mirror construction in the panel builder.
    ("TW", "E", "201701", "201912"), ("TW", "I", "201701", "201912"),
    ("VN2", "E", "201701", "201912"), ("VN2", "I", "201701", "201912"),
]


def credentials():
    envf = cfg.ROOT / ".env"
    creds = {}
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip().strip('"').strip("'")
    user, pw = creds.get("TDM_USERNAME"), creds.get("TDM_PASSWORD")
    if not user or not pw:
        sys.exit("TDM_USERNAME / TDM_PASSWORD missing from .env -- add them (git-ignored).")
    return user, pw


def fetch(reporter, flow, begin, end, codes=CODES, tag=""):
    user, pw = credentials()
    params = {
        "username": user, "password": pw,
        "reporter": reporter, "periodBegin": begin, "periodEnd": end,
        "flow": flow, "partners": "All", "frequency": "M",
        "hsCode": codes, "productCode": "", "levelDetail": "6",
        "levelDetailGroup": "6", "currency": "USD", "includeUnits": "BOTH",
        "isoCountryCode": "BOTH", "conv": "0", "separator": "T",
        "includeFlow": "Y", "ISO3": "Y",
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{tag}" if tag else ""
    out = OUT_DIR / f"tdm_{reporter}_{flow}_{begin}_{end}{suffix}.tsv"
    if out.exists() and out.stat().st_size > 500:
        print(f"cached {out.name}")
        return out
    print(f"fetching {reporter} {flow} {begin}-{end}{suffix} ...", flush=True)
    with urllib.request.urlopen(url, timeout=600) as r:
        data = r.read()
    head = data[:200].decode("utf-8", errors="replace").lower()
    if len(data) < 500 and ("error" in head or "invalid" in head or "denied" in head):
        raise RuntimeError(f"API error for {reporter} {flow}{suffix}: {data[:300]!r}")
    out.write_bytes(data)
    n_lines = data.count(b"\n")
    print(f"  -> {out} ({len(data)/1e6:.1f} MB, {n_lines} lines)")
    return out


def main():
    args = sys.argv[1:]
    if args == ["semi"]:
        failures = []
        for reporter, flow, begin, end in STANDING:
            for tag, codes in GROUPS.items():
                try:
                    fetch(reporter, flow, begin, end, ",".join(codes), tag)
                except Exception as e:
                    print(f"  FAILED {reporter} {flow} {tag}: {e}", flush=True)
                    failures.append((reporter, flow, tag))
        if failures:
            sys.exit(f"{len(failures)} pulls failed: {failures}")
        return
    pulls = [tuple(args)] if len(args) == 4 else STANDING
    for reporter, flow, begin, end in pulls:
        fetch(reporter, flow, begin, end)


if __name__ == "__main__":
    main()
