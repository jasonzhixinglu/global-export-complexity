"""Central configuration: paths and analysis constants.

Importing this module is side-effect free except for resolving paths relative
to the repository root, so scripts can `from gec import config as cfg`.
"""
from __future__ import annotations

from pathlib import Path

# --- paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_CSV = RAW_DIR / "hs92_country_product_year_4.csv"
RESULTS_DIR = ROOT / "results"
FIG_DIR = RESULTS_DIR / "figures"
TABLE_DIR = RESULTS_DIR / "tables"

# --- data provenance -------------------------------------------------------
# Harvard Growth Lab, Atlas of Economic Complexity, HS92 HS4 country-product-year.
DATAVERSE_DOI = "doi:10.7910/DVN/T4CHWJ"
DATAVERSE_FILE_ID = 13685110  # hs92_country_product_year_4.csv, dataset version 18


def datafile_url(file_id) -> str:
    return f"https://dataverse.harvard.edu/api/access/datafile/{file_id}?format=original"


DOWNLOAD_URL = datafile_url(DATAVERSE_FILE_ID)

# Bilateral origin x destination x HS6 x year files (one per year range). HS4 bilateral is
# obtained by truncating product_hs92_code to 4 digits and summing -- see data.load_bilateral.
BILATERAL_FILE_IDS = {
    "1995_1999": 13685106,
    "2000_2009": 13685108,
    "2010_2019": 13685120,
    "2020_2024": 13685118,
}


def bilateral_path(year_range: str):
    return RAW_DIR / f"hs92_country_country_product_year_6_{year_range}.csv"


# HS2012 vintage (needed for AI/semiconductor HS6 codes that don't exist in HS92).
HS12_DOI = "doi:10.7910/DVN/YAVJDF"
HS12_HS6_FILE_ID = 13685185  # hs12_country_product_year_6.csv (~463 MB, 2012-2023)
HS12_HS6_CSV = RAW_DIR / "hs12_country_product_year_6.csv"

# HS2012 BILATERAL origin x destination x HS6 x year (HS2012 codes match the OECD/Fed tech baskets,
# unlike the HS92 bilateral whose 6-digit semiconductor codes diverged). Covers 2012-2024 only.
HS12_BILATERAL_FILE_IDS = {
    "2012_2019": 13685181,  # ~4.45 GB
    "2020_2024": 13685183,  # ~2.80 GB
}


def hs12_bilateral_path(year_range: str):
    return RAW_DIR / f"hs12_country_country_product_year_6_{year_range}.csv"

# --- analysis constants ----------------------------------------------------
YEARS = list(range(2000, 2025))   # 2000-2024 inclusive
N_TOP = 50                        # number of top exporters to track (per-country panels)
COVER_THRESHOLDS = [20, 30, 50]   # cumulative-coverage thresholds to report
SNAPSHOT_YEARS = [2000, 2008, 2012, 2018, 2024]
FOCUS_COUNTRIES = ["CHN", "USA", "DEU", "JPN", "KOR", "MEX"]  # for readable line plots
LEGACY_COUNTRIES = ["CHN", "DEU", "JPN", "KOR"]  # the four from legacy/ notebook
REPRO_YEARS = [2000, 2012, 2024]                 # snapshot years for line-chart reproductions
STACK_COUNTRIES = ["CHN", "JPN", "DEU"]          # stacked cumulative-share chart (bottom->top)

# Supply-chain workstream: the countries carried on every time-series chart, so a
# reader sees the same cast (and the same colours) from page to page. Chosen by
# 2026 net position on the 60-code basket plus the two upstream sellers.
# CHN and Hong Kong are the CHK bloc (built from extra-bloc flows, not by summing
# the two countries). Price-based charts
# can only show the subset whose customs data carry usable net weights -- filter on
# results/tables/price_coverage.csv rather than editing this list.
CHAIN_MAJORS = ["TWN", "KOR", "CHK", "JPN", "USA", "DEU", "NLD", "MYS", "SGP", "VNM"]

# Estimator settings
BANDWIDTH = 0.10                  # canonical bandwidth for figures / coverage / diagnostics
H_DIST = 0.10                     # canonical bandwidth for the dollar-distribution density
# Dashboard smoothness levels: bw = kernel bandwidth (PCI units); win = starting half-width
# of the product drill-down window (widened adaptively until it holds ~10 products).
SMOOTHING = [
    {"id": "low", "label": "Low", "bw": 0.05, "win": 0.02},
    {"id": "med", "label": "Medium", "bw": 0.10, "win": 0.05},
    {"id": "high", "label": "High", "bw": 0.20, "win": 0.10},
]
PCI_LO, PCI_HI = -3.0, 3.0        # plotting/aggregation window for PCI
SHARE_GRID_N = 120                # grid points for the share curves over [-2.5, 2.5]
KDE_GRID_N = 300                  # grid points for density curves over [PCI_LO, PCI_HI]
BIN_WIDTH = 0.25                  # PCI bin width for the mass-conservation diagnostic


def ensure_dirs() -> None:
    for d in (RAW_DIR, FIG_DIR, TABLE_DIR):
        d.mkdir(parents=True, exist_ok=True)
