"""Run the full pipeline end to end.

  python scripts/run_all.py

Equivalent to: download_data -> compute_surfaces -> make_figures -> run_diagnostics.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["download_data", "compute_surfaces", "make_figures", "run_diagnostics"]


def main():
    for step in STEPS:
        print(f"\n=== {step} ===")
        runpy.run_path(str(HERE / f"{step}.py"), run_name="__main__")


if __name__ == "__main__":
    sys.exit(main())
