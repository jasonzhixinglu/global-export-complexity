"""Download the raw HS4 trade CSV from Harvard Dataverse if it is not present.

Usage:  python scripts/download_data.py [--force]
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg


def main(force: bool = False) -> None:
    cfg.ensure_dirs()
    if cfg.RAW_CSV.exists() and not force:
        mb = cfg.RAW_CSV.stat().st_size / 1e6
        print(f"already present: {cfg.RAW_CSV} ({mb:.0f} MB). Use --force to re-download.")
        return
    print(f"downloading {cfg.DOWNLOAD_URL}\n      -> {cfg.RAW_CSV}")
    urllib.request.urlretrieve(cfg.DOWNLOAD_URL, cfg.RAW_CSV)
    mb = cfg.RAW_CSV.stat().st_size / 1e6
    print(f"done: {mb:.0f} MB")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
