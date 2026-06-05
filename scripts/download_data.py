"""Download raw trade CSVs from Harvard Dataverse if not present.

Usage:
  python scripts/download_data.py [--force]                # the HS4 origin file (default)
  python scripts/download_data.py --bilateral 2020_2024    # one bilateral HS6 file (~2.9 GB)
  python scripts/download_data.py --bilateral all          # all bilateral files (~15 GB)
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg


def _fetch(url: str, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        print(f"already present: {dest} ({dest.stat().st_size/1e9:.2f} GB). --force to re-download.")
        return
    print(f"downloading -> {dest}")
    urllib.request.urlretrieve(url, dest)
    print(f"done: {dest.stat().st_size/1e9:.2f} GB")


def main(argv) -> None:
    cfg.ensure_dirs()
    force = "--force" in argv

    if "--bilateral" in argv:
        i = argv.index("--bilateral")
        spec = argv[i + 1] if i + 1 < len(argv) else "2020_2024"
        ranges = list(cfg.BILATERAL_FILE_IDS) if spec == "all" else [spec]
        for yr in ranges:
            if yr not in cfg.BILATERAL_FILE_IDS:
                print(f"unknown range '{yr}'. options: {', '.join(cfg.BILATERAL_FILE_IDS)} | all")
                continue
            _fetch(cfg.datafile_url(cfg.BILATERAL_FILE_IDS[yr]), cfg.bilateral_path(yr), force)
        return

    _fetch(cfg.DOWNLOAD_URL, cfg.RAW_CSV, force)


if __name__ == "__main__":
    main(sys.argv[1:])
