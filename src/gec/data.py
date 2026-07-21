"""Loading, cleaning, and reshaping the HS4 country-product-year trade data.

The Atlas data is already harmonized so that, for each (product, year), the sum of country
export (import) values equals world exports (imports) of that product (see docs/pci-analysis.md §2).
Both flows are kept (export_value, import_value); the only cleaning here is type coercion and
dropping rows with missing PCI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg

USECOLS = ["country_iso3_code", "product_hs92_code", "year", "export_value", "import_value", "pci"]


def load_clean(path=None, years=None) -> pd.DataFrame:
    """Read the raw CSV, coerce types, filter years, drop unusable rows.

    Keeps both export_value and import_value (for the export/import flows). Rows need a
    valid PCI and at least one non-zero value; missing values are filled with 0."""
    path = path or cfg.RAW_CSV
    years = years or cfg.YEARS
    df = pd.read_csv(
        path,
        usecols=USECOLS,
        dtype={"country_iso3_code": str, "product_hs92_code": str},
    )
    df["year"] = df["year"].astype(int)
    for col in ("export_value", "import_value"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["pci"] = pd.to_numeric(df["pci"], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df[df["year"].between(min(years), max(years))]
    df = df.dropna(subset=["pci"])
    df[["export_value", "import_value"]] = df[["export_value", "import_value"]].fillna(0.0).clip(lower=0)
    df = df[(df["export_value"] > 0) | (df["import_value"] > 0)]
    return df.reset_index(drop=True)


def ranked_exporters(df: pd.DataFrame) -> list[str]:
    """All reporting economies ranked by cumulative export value (descending).

    Non-country aggregates (e.g. 'ANS' = areas not specified) are kept in the world
    denominator elsewhere but excluded from this *selection* of real economies.
    """
    totals = df.groupby("country_iso3_code")["export_value"].sum()
    totals = totals.drop(index=[c for c in ("ANS",) if c in totals.index], errors="ignore")
    return totals.sort_values(ascending=False).index.tolist()


def top_exporters(df: pd.DataFrame, n=None) -> list[str]:
    """Top-n reporting economies by cumulative export value over the loaded years."""
    n = n or cfg.N_TOP
    return ranked_exporters(df)[:n]


def product_table(df_year: pd.DataFrame, pci_lo=None, pci_hi=None) -> pd.DataFrame:
    """Aggregate one year to product level: pci (constant within product-year) and the
    world export value (W) and world import value (W_imp) = sums over all countries."""
    pci_lo = cfg.PCI_LO if pci_lo is None else pci_lo
    pci_hi = cfg.PCI_HI if pci_hi is None else pci_hi
    prod = (
        df_year.groupby("product_hs92_code")
        .agg(pci=("pci", "first"), W=("export_value", "sum"), W_imp=("import_value", "sum"))
        .reset_index()
    )
    return prod[prod["pci"].between(pci_lo, pci_hi)].reset_index(drop=True)


BILATERAL_USECOLS = ["country_iso3_code", "partner_iso3_code",
                     "product_hs92_code", "year", "export_value"]


def load_bilateral(year_ranges=("2020_2024",), origins=None, dests=None, years=None,
                   hs_level=4, chunksize=2_000_000) -> pd.DataFrame:
    """Load Atlas bilateral (origin x destination x product x year) data, aggregated from
    HS6 to `hs_level` digits, in bounded memory.

    The Atlas only ships bilateral product data at HS6; HS4 bilateral is the first 4 digits
    summed (lossless to HS4). The full files are multi-GB, so we read in chunks, filter, and
    aggregate per chunk before concatenating.

    Parameters
    ----------
    year_ranges : iterable of keys into cfg.BILATERAL_FILE_IDS (e.g. "2020_2024").
    origins, dests : optional iterables of ISO3 to keep (exporter / importer).
    years : optional iterable of ints to keep.
    hs_level : product-code digits to aggregate to (4 = HS4).

    Returns columns: country_iso3_code, partner_iso3_code, product_hs92_code, year, export_value.
    """
    origins = set(origins) if origins else None
    dests = set(dests) if dests else None
    years = set(int(y) for y in years) if years else None
    parts = []
    for yr_range in year_ranges:
        path = cfg.bilateral_path(yr_range)
        if not path.exists():
            raise FileNotFoundError(f"{path} not found - run download_data.py --bilateral {yr_range}")
        for chunk in pd.read_csv(path, usecols=BILATERAL_USECOLS,
                                 dtype={"country_iso3_code": str, "partner_iso3_code": str,
                                        "product_hs92_code": str},
                                 chunksize=chunksize):
            chunk["year"] = chunk["year"].astype(int)
            if years is not None:
                chunk = chunk[chunk["year"].isin(years)]
            if origins is not None:
                chunk = chunk[chunk["country_iso3_code"].isin(origins)]
            if dests is not None:
                chunk = chunk[chunk["partner_iso3_code"].isin(dests)]
            if chunk.empty:
                continue
            chunk["export_value"] = pd.to_numeric(chunk["export_value"], errors="coerce")
            chunk = chunk.dropna(subset=["export_value"])
            chunk["product_hs92_code"] = chunk["product_hs92_code"].str.zfill(6).str[:hs_level]
            g = chunk.groupby(["country_iso3_code", "partner_iso3_code",
                               "product_hs92_code", "year"], as_index=False)["export_value"].sum()
            parts.append(g)
    if not parts:
        return pd.DataFrame(columns=BILATERAL_USECOLS)
    out = pd.concat(parts, ignore_index=True)
    return out.groupby(["country_iso3_code", "partner_iso3_code", "product_hs92_code", "year"],
                       as_index=False)["export_value"].sum()


def country_value_vectors(df_year, products, countries, value_col="export_value") -> dict[str, np.ndarray]:
    """For a year, return {country: array of `value_col` aligned to `products`}.
    value_col is 'export_value' or 'import_value'."""
    idx = pd.Index(products)
    out = {}
    for c in countries:
        cv = (
            df_year[df_year["country_iso3_code"] == c]
            .groupby("product_hs92_code")[value_col]
            .sum()
        )
        out[c] = cv.reindex(idx).fillna(0.0).to_numpy()
    return out
