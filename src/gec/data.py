"""Loading, cleaning, and reshaping the HS4 country-product-year trade data.

The Atlas data is already harmonized so that, for each (product, year), the sum of
country export values equals world exports of that product (see docs/analysis.md §2).
We rely on that accounting identity downstream, so the only cleaning here is type
coercion and dropping rows with missing PCI / export value.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as cfg

USECOLS = ["country_iso3_code", "product_hs92_code", "year", "export_value", "pci"]


def load_clean(path=None, years=None) -> pd.DataFrame:
    """Read the raw CSV, coerce types, filter years, drop unusable rows."""
    path = path or cfg.RAW_CSV
    years = years or cfg.YEARS
    df = pd.read_csv(
        path,
        usecols=USECOLS,
        dtype={"country_iso3_code": str, "product_hs92_code": str},
    )
    df["year"] = df["year"].astype(int)
    df["export_value"] = pd.to_numeric(df["export_value"], errors="coerce")
    df["pci"] = pd.to_numeric(df["pci"], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df[df["year"].between(min(years), max(years))]
    df = df.dropna(subset=["pci", "export_value"])
    df = df[df["export_value"] >= 0]
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
    """Aggregate one year to product level: pci (constant within product-year) and
    world export value W = sum over all countries."""
    pci_lo = cfg.PCI_LO if pci_lo is None else pci_lo
    pci_hi = cfg.PCI_HI if pci_hi is None else pci_hi
    prod = (
        df_year.groupby("product_hs92_code")
        .agg(pci=("pci", "first"), W=("export_value", "sum"))
        .reset_index()
    )
    return prod[prod["pci"].between(pci_lo, pci_hi)].reset_index(drop=True)


def country_value_vectors(df_year, products, countries) -> dict[str, np.ndarray]:
    """For a year, return {country: array of its export value aligned to `products`}."""
    idx = pd.Index(products)
    out = {}
    for c in countries:
        cv = (
            df_year[df_year["country_iso3_code"] == c]
            .groupby("product_hs92_code")["export_value"]
            .sum()
        )
        out[c] = cv.reindex(idx).fillna(0.0).to_numpy()
    return out
