"""Download raw trade CSVs from Harvard Dataverse if not present.

Usage:
  python scripts/download_data.py [--force]                # the HS4 origin file (default)
  python scripts/download_data.py --hs12                   # HS2012 HS6 file (~463 MB; tech/AI baskets)
  python scripts/download_data.py --bilateral 2020_2024    # one bilateral HS6 file (~2.9 GB)
  python scripts/download_data.py --bilateral all          # all bilateral files (~15 GB)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg


def _fetch(url: str, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        print(f"already present: {dest} ({dest.stat().st_size/1e9:.2f} GB). --force to re-download.")
        return
    print(f"downloading -> {dest}")
    # curl reliably follows the Dataverse 303 -> signed-S3 redirect (urllib gets 403 on it).
    r = subprocess.run(["curl", "-sSL", "-o", str(dest), url])
    if r.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"download failed (curl exit {r.returncode}) for {url}")
    print(f"done: {dest.stat().st_size/1e9:.2f} GB")


def main(argv) -> None:
    cfg.ensure_dirs()
    force = "--force" in argv

    if "--hs12" in argv:
        _fetch(cfg.datafile_url(cfg.HS12_HS6_FILE_ID), cfg.HS12_HS6_CSV, force)
        return

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
