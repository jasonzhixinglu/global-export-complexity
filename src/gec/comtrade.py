"""Pull HS4 export data from UN Comtrade and map it onto the Atlas schema.

Why this exists (see docs/analysis.md and docs/comtrade.md):
  * The Atlas (reconciled, with PCI) lags ~1.5 years. Comtrade is more current but
    (a) RAW / unreconciled, (b) has NO complexity index, and (c) serves recent years
    only in the as-reported HS revision (HS2022-ish), not HS92.
  * Late filers (notably China) may not have filed a given year directly, but their
    exports can be reconstructed by MIRROR: summing partners' reported imports *from*
    that country.

This module therefore offers two pull modes and bolts on an Atlas-2024 PCI proxy:
  - `fetch_country_exports`  : a country's own HS4 exports to World (flow X, FOB).
  - `fetch_mirror_exports`   : sum of all partners' imports FROM a country (flow M, CIF),
                               used when the country itself has not filed.
HS4 codes are matched to the Atlas HS92 4-digit set by identity (most headings are
stable); unmatched value is reported so the loss is explicit rather than hidden.

Auth: set COMTRADE_API_KEY (free registered key from comtradedeveloper.un.org) for full
pulls via getFinalData. The FREE tier allows 100k records/call and 500 calls/day -- enough
for direct (~1.2k rows) and mirror (~60-70k rows) pulls; a full world-denominator pull
(~240k rows) must be chunked under 100k. Without a key it falls back to previewFinalData,
which is capped at 500 rows/call -- fine for smoke tests, NOT for production pulls.
"""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd
import comtradeapicall as ctc

from . import config as cfg

WORLD = "0"
CIF_FOB = 1.10          # rough CIF->FOB deflation for mirror (imports are CIF)
_REF = None


def api_key():
    return os.environ.get("COMTRADE_API_KEY") or None


def reporter_maps():
    """(code->iso3, iso3->code) for real reporters (excludes groups like EU)."""
    global _REF
    if _REF is None:
        ref = ctc.getReference("reporter")
        _REF = ref[ref["isGroup"] == False].copy()  # noqa: E712
    code2iso = {str(c): i for c, i in zip(_REF["reporterCode"], _REF["reporterCodeIsoAlpha3"])
                if isinstance(i, str) and len(i) == 3}
    iso2code = {v: k for k, v in code2iso.items()}
    return code2iso, iso2code


def atlas_pci(year=2024) -> pd.Series:
    """PCI by HS92 4-digit code from the Atlas raw file (proxy for later years)."""
    df = pd.read_csv(cfg.RAW_CSV, usecols=["product_hs92_code", "year", "pci"],
                     dtype={"product_hs92_code": str})
    df = df[df["year"] == year].dropna(subset=["pci"])
    return df.groupby("product_hs92_code")["pci"].first()


# --- low-level pulls -------------------------------------------------------
def _get(key, **kw):
    """One Comtrade call: getFinalData if key present else previewFinalData (<=500)."""
    base = dict(typeCode="C", freqCode="A", clCode="HS", partner2Code="0",
                customsCode="C00", motCode="0")
    base.update(kw)
    if key:
        return ctc.getFinalData(key, **base)
    return ctc.previewFinalData(**base)


def country_code(iso3) -> str:
    """All M49 reporter codes for an ISO3, comma-joined (e.g. USA -> '840,842,841').
    Comtrade accepts the list; only the active code has data, so summing is safe."""
    return str(ctc.convertCountryIso3ToCode(iso3))


def fetch_country_exports(year, iso3, key=None) -> pd.DataFrame:
    """A country's own HS4 exports to World (FOB). Columns: hs4, value."""
    df = _get(key, period=str(year), reporterCode=country_code(iso3), cmdCode="AG4",
              flowCode="X", partnerCode=WORLD)
    return _to_hs4_value(df)


def fetch_mirror_exports(year, iso3, key=None) -> tuple[pd.DataFrame, int]:
    """Reconstruct a country's exports as partners' imports FROM it (CIF->FOB adjusted).
    Returns (DataFrame[hs4, value], n_partners). Needs a key in practice: the all-reporter
    pull far exceeds the 500-row preview cap."""
    if not key:
        print(f"    [warn] mirror for {iso3} without a key uses preview (<=500 rows) "
              f"-> severely truncated; set COMTRADE_API_KEY for a real reconstruction.")
    df = _get(key, period=str(year), reporterCode=None, cmdCode="AG4",
              flowCode="M", partnerCode=country_code(iso3))
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["hs4", "value"]), 0
    n_partners = df["reporterCode"].nunique() if "reporterCode" in df else df.shape[0]
    out = _to_hs4_value(df)
    out["value"] = out["value"] / CIF_FOB
    return out, int(n_partners)


def _to_hs4_value(df) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["hs4", "value"])
    d = df.copy()
    d["hs4"] = d["cmdCode"].astype(str).str.zfill(4)
    d = d[d["hs4"].str.len() == 4]
    return d.groupby("hs4", as_index=False)["primaryValue"].sum().rename(
        columns={"primaryValue": "value"})


# --- assembly into Atlas schema -------------------------------------------
def assemble(records, year, pci_year=2024) -> tuple[pd.DataFrame, dict]:
    """records: list of (iso3, df[hs4,value], provenance). Returns (atlas-schema df, report).
    Joins Atlas `pci_year` PCI by HS4; reports value matched to the HS92 code set."""
    pci = atlas_pci(pci_year)
    valid = set(pci.index)
    rows, rep = [], {"pci_year": pci_year, "countries": {}}
    for iso3, df, prov in records:
        if df is None or df.empty:
            rep["countries"][iso3] = {"provenance": prov, "total": 0.0, "matched_pct": None}
            continue
        df = df.copy()
        df["country_iso3_code"] = iso3
        df["year"] = year
        df["pci"] = df["hs4"].map(pci)
        df["provenance"] = prov
        matched = df.loc[df["pci"].notna(), "value"].sum()
        total = df["value"].sum()
        rep["countries"][iso3] = {
            "provenance": prov, "total": float(total),
            "matched_pct": round(100 * matched / total, 1) if total else None,
        }
        rows.append(df)
    if not rows:
        return pd.DataFrame(), rep
    out = pd.concat(rows, ignore_index=True).rename(columns={"hs4": "product_hs92_code",
                                                             "value": "export_value"})
    out = out[["country_iso3_code", "product_hs92_code", "year",
               "export_value", "pci", "provenance"]]
    return out, rep
