"""Reporter-level unit-value base for price indices / terms of trade.

Streams the Comtrade monthly cache (data/raw/comtrade_monthly) and the TDM
extracts, and aggregates each reporter's own report to
  (iso, flow, code, period) -> value, value_wgt, quantity, basis
where `value_wgt`/`quantity` cover only the lines carrying a usable quantity, so the
unit value value_wgt/quantity is self-consistent (same lines in numerator and
denominator). `value` is the full reported value, used to judge coverage.

Reporters differ in WHICH quantity they actually measure, so both candidates are
carried -- net weight (kg) and the reporter's own unit (qty: number of units, m2,
litres...) -- and `basis` records which one won per series. See choose_basis.

Flows are as reported: exports FOB, imports CIF. A constant CIF margin cancels
in a rebased index, so no CIF->FOB step is applied here (see the caveats in
docs/notes/prices-net-exports.md).

Output: data/derived/unit_values_monthly.parquet (git-ignored).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as _OECD

CODES = set(["847150", "847180", "847330"]) | {
    c for g, d in _OECD.items() if g != "Photosensitive devices" for c in d}
KEEP = ["CHN", "USA", "MEX", "TWN", "KOR", "VNM", "HKG", "MYS", "SGP", "THA",
        "NLD", "DEU", "CZE", "HUN", "JPN", "PHL", "IND", "IDN", "CAN", "GBR",
        "FRA", "ITA", "POL", "IRL", "ESP", "CHE", "BEL", "SWE", "DNK", "ISR"]
# A code whose unit value moves more than this in a median month was screened out as
# churn rather than price. OFF: it was motivated by the 3-month charts, which we do
# not publish, and at a 12-month window the averaging already absorbs that noise --
# while dropping codes leaves the index chaining over a rump basket, which does real
# damage (it was what sent Japan's chips import index to 279).
SCREEN_CHURN = os.environ.get("GEC_CHURN", "0") == "1"
# Single-cell outlier screen: a month whose unit value sits this far (in logs) from its
# series' local median. OFF by default. It did what it claimed -- Malaysia's 12.4bn-unit
# filing of 854231 in 2025-01 is plainly a reporting error -- but every such rule drops
# real observations too, and the ones it drops are the volatile tail, which biases the
# result toward calm. A volatile country is better handled by not plotting it (and
# saying so) than by quietly deleting its awkward months. Set GEC_OUTLIER_LOG to enable.
OUTLIER_LOG = float(os.environ.get("GEC_OUTLIER_LOG", 99.0))
MAX_MEDIAN_STEP = 0.25
# Fall back to the reporter's own quantity unit where net weight is unusable? OFF.
# The column is real and would rescue the US, Singapore, Malaysia and Vietnam (basket
# coverage 57% -> 89%), and the individual series inspected look sound -- Japanese
# memory exports at $1.50 -> $2.20 an IC, US servers at $1.6k -> $7.7k a unit. But
# switching it on moved stage aggregates for reporters whose weights were fine
# (Japan's chips import index to 279, its terms of trade to 22) in ways not yet
# explained, so it stays off until the qty series are validated in their own right:
# per-series unit stability, and the aggregates checked against a known price series.
# See docs/notes/prices-net-exports.md.
USE_QTY_BASIS = os.environ.get("GEC_QTY", "1") == "1"
# China and Hong Kong are one trade bloc throughout this project. The bloc is built
# as its OWN series from EXTRA-bloc lines only -- China's shipments to Hong Kong are
# internal transfers, not bloc exports, and they are not small (388B of chips flowed
# between the two in the year to 2026-04). CHN and HKG keep their own all-partner
# series alongside it.
BLOC = {"CHN": "CHK", "HKG": "CHK"}
# Each member's extra-bloc trade is carried as its own pseudo-reporter ("CHN~x") so the
# Comtrade/TDM precedence still runs per REPORTER; the members are summed into the bloc
# only afterwards. Emitting "CHK" directly put two reporters on one key, and the
# precedence then kept whichever source came first -- which silently dropped China's
# TDM leg from 2025 and cut the bloc's monthly value by three quarters.
EXTRA = "~x"
CT_DIR = cfg.RAW_DIR / "comtrade_monthly"
TDM_DIR = cfg.RAW_DIR / "tdm"
OUT = cfg.DATA_DIR / "derived" / "unit_values_monthly.parquet"
COLS = ["period", "reporterCode", "flowCode", "partnerCode", "cmdCode",
        "primaryValue", "netWgt", "qty"]


def comtrade_base():
    import comtradeapicall as ctc
    ref = ctc.getReference("partner")
    c2i = {int(c): i for c, i in zip(ref["PartnerCode"], ref["PartnerCodeIsoAlpha3"])
           if isinstance(i, str) and len(i) == 3}
    c2i[490] = "TWN"  # "Other Asia, nes"
    keep = set(KEEP)
    out = []
    files = sorted(CT_DIR.glob("*.parquet"))
    for i, f in enumerate(files):
        d = pd.read_parquet(f, columns=COLS)
        if not len(d):
            continue
        d = d[(d.partnerCode != 0)]
        d["iso"] = d.reporterCode.map(c2i)
        d["cmdCode"] = d.cmdCode.astype(str)
        d = d[d.iso.isin(keep) & d.cmdCode.isin(CODES)]
        if not len(d):
            continue
        d["period"] = d.period.astype(str)
        d["value"] = d.primaryValue.astype(float)
        w = d.netWgt.fillna(0) > 0
        d["kg"] = d.netWgt.where(w, 0.0).astype(float)
        d["value_kg"] = d.value.where(w, 0.0)
        # The SECOND quantity: whatever unit the reporter files in (number of units,
        # square metres, litres). Our cached pulls carry no unit label, which is
        # survivable because the index only ever uses the change in a series' own
        # unit value -- the unit cancels as long as it is the same unit next month.
        q = d.qty.fillna(0) > 0
        d["qty"] = d.qty.where(q, 0.0).astype(float)
        d["value_qty"] = d.value.where(q, 0.0)
        cols = ["value", "value_kg", "kg", "value_qty", "qty"]
        out.append(d.groupby(["iso", "flowCode", "cmdCode", "period"], as_index=False)
                   [cols].sum())
        b = d[d.iso.isin(BLOC) & ~d.partnerCode.map(c2i).isin(BLOC)].copy()
        if len(b):
            b["iso"] = b.iso + EXTRA   # keep the member's identity through the merge
            out.append(b.groupby(["iso", "flowCode", "cmdCode", "period"],
                                 as_index=False)[cols].sum())
        if (i + 1) % 200 == 0:
            print(f"  ...{i+1}/{len(files)} files", flush=True)
    df = pd.concat(out, ignore_index=True)
    df = df.groupby(["iso", "flowCode", "cmdCode", "period"], as_index=False).sum()
    df = df.rename(columns={"flowCode": "flow", "cmdCode": "code"})
    df["source"] = "comtrade"
    return df


def tdm_base():
    """TDM extracts: kg comes from QTY2/UNIT2 where TDM carries a secondary weight
    (it does for the PCS/SET-reported codes, e.g. every Taiwanese IC line), else
    from QTY1/UNIT1 when that is itself kg."""
    parts = []
    for f in sorted(TDM_DIR.glob("tdm_*.tsv")):
        d = pd.read_csv(f, sep="\t", encoding="utf-16",
                        dtype={"COMMODITY": str, "MONTH": str, "YEAR": str})
        if not len(d):
            continue
        d = d[d.COMMODITY.isin(CODES)]
        if not len(d):
            continue
        u1 = d.UNIT1.astype(str).str.strip().str.upper()
        u2 = d.UNIT2.astype(str).str.strip().str.upper() if "UNIT2" in d else u1
        q2 = d.QTY2.astype(float) if "QTY2" in d else pd.Series(0.0, index=d.index)
        q1 = d.QTY1.astype(float)
        kg_qty = q2.where(u2.eq("KG") & (q2.fillna(0) > 0),
                          q1.where(u1.eq("KG") & (q1.fillna(0) > 0), 0.0)).fillna(0.0)
        val = d.VALUE.astype(float)
        # QTY1 is the reporter's own unit (PCS, SET, M2...). Keep only the modal
        # unit per series so the second candidate is internally consistent.
        prim = pd.DataFrame({"iso": d.RPT_ISO, "flow": d.FLOW.map({"E": "X", "I": "M"}),
                             "code": d.COMMODITY, "u": u1, "v": val})
        modal = (prim.groupby(["iso", "flow", "code", "u"]).v.sum()
                 .reset_index().sort_values("v")
                 .drop_duplicates(["iso", "flow", "code"], keep="last")
                 .set_index(["iso", "flow", "code"]).u)
        keyed = pd.MultiIndex.from_arrays([prim.iso, prim.flow, prim.code])
        is_modal = u1.to_numpy() == modal.reindex(keyed).to_numpy()
        q_ok = is_modal & (q1.fillna(0) > 0)
        rec = pd.DataFrame({
            "iso": d.RPT_ISO, "flow": d.FLOW.map({"E": "X", "I": "M"}),
            "code": d.COMMODITY, "period": d.YEAR + d.MONTH.str.zfill(2),
            "value": val,
            "value_kg": val.where(kg_qty > 0, 0.0),
            "kg": kg_qty,
            "value_qty": val.where(q_ok, 0.0),
            "qty": q1.where(q_ok, 0.0).fillna(0.0),
        })
        parts.append(rec.groupby(["iso", "flow", "code", "period"], as_index=False).sum())
        rb = rec[rec.iso.isin(BLOC) & ~d.PTN_ISO.isin(BLOC).to_numpy()].copy()
        if len(rb):
            rb["iso"] = rb.iso + EXTRA
            parts.append(rb.groupby(["iso", "flow", "code", "period"], as_index=False).sum())
    df = pd.concat(parts, ignore_index=True)
    df = df.groupby(["iso", "flow", "code", "period"], as_index=False).sum()
    df = df[df.iso.str.replace(EXTRA, "", regex=False).isin(KEEP)]
    df["source"] = "tdm"
    return df


def choose_basis(df):
    """Per (iso, flow, code): pick the quantity that is actually MEASURED.

    Reporters differ in which quantity they collect. US net weight on the compute
    codes is value x a constant -- derived, not weighed -- while its unit counts are
    real; for most European reporters it is the other way round. Both candidates are
    screened by the same degeneracy test, and the one with more usable months wins
    (weight breaks a tie, being the more comparable unit). The choice is made once
    for the whole sample, never mid-series: a chained index tolerates ANY unit, but
    not a change of unit.
    """
    for base in ("kg", "qty"):
        df[f"uv_{base}"] = (df[f"value_{base}"] / df[base]).where(df[base] > 0)
        df[f"bad_{base}"] = _degenerate(df, f"uv_{base}")
        df[f"ok_{base}"] = df[f"uv_{base}"].notna() & ~df[f"bad_{base}"]
    # Weight is the default and only loses its place if it is genuinely unavailable
    # for the series -- switching to units whenever they scored marginally better
    # wrecked reporters whose weights were fine all along (Japan's terms of trade
    # went to 23 on a basket that had been perfectly well measured in kilos).
    n = df.assign(_has=df.value > 0).groupby(["iso", "flow", "code"])._has.transform("sum")
    score = df.groupby(["iso", "flow", "code"])[["ok_kg", "ok_qty"]].transform("sum")
    use_qty = (score.ok_kg < 0.5 * n) & (score.ok_qty > score.ok_kg) & USE_QTY_BASIS
    df["basis"] = np.where(use_qty, "qty", "kg")
    df["quantity"] = np.where(use_qty, df.qty, df.kg)
    df["value_wgt"] = np.where(use_qty, df.value_qty, df.value_kg)
    df["placeholder"] = np.where(use_qty, df.bad_qty, df.bad_kg)
    df.loc[df.placeholder | (df.quantity <= 0), ["value_wgt", "quantity"]] = 0.0
    df["uv"] = (df.value_wgt / df.quantity).where(df.quantity > 0).replace(0.0, np.nan)

    # Single corrupt months: a quantity that is 25x its neighbours with the value
    # unchanged (Malaysia reported 12.4bn units of 854231 in 2025-01 against ~0.5bn
    # either side) survives the index's own trim -- it is one cell, but a 12-month
    # window carries it for a year. Compare each cell with the local median of its own
    # series and drop the cell, not the series.
    lu = np.log(df.uv.where(df.uv > 0))
    med = (lu.groupby([df.iso, df.flow, df.code])
           .transform(lambda x: x.rolling(13, center=True, min_periods=5).median()))
    df["outlier"] = (lu - med).abs() > OUTLIER_LOG
    df.loc[df.outlier, ["value_wgt", "quantity", "uv"]] = [0.0, 0.0, np.nan]
    print(f"  outlier cells dropped: {df.outlier.sum():,} = "
          f"{df.loc[df.outlier, 'value'].sum() / df.value.sum():.2%} of value")

    # Whichever basis won, a series whose unit value typically moves by a quarter in
    # a month is not measuring a price -- it is the covered subset of partner lines
    # churning underneath a fixed code. Drop those outright rather than let the index
    # average them in.
    lv = df[df.uv.gt(0)].sort_values(["iso", "flow", "code", "period"])
    step = (lv.groupby(["iso", "flow", "code"]).uv
            .apply(lambda x: np.median(np.abs(np.diff(np.log(x.to_numpy()))))
                   if len(x) > 3 else np.nan))
    wild = set(step[step > MAX_MEDIAN_STEP].index) if SCREEN_CHURN else set()
    key = list(zip(df.iso, df.flow, df.code))
    df["churny"] = [k in wild for k in key]
    df.loc[df.churny, ["value_wgt", "quantity", "uv"]] = [0.0, 0.0, np.nan]
    print(f"  churny series dropped: {df.churny.sum():,} cells = "
          f"{df.loc[df.churny, 'value'].sum() / df.value.sum():.1%} of value")
    share = df.loc[df.placeholder, "value"].sum() / df.value.sum()
    picked = df.groupby("basis").value.sum() / df.value.sum()
    print(f"  imputed-quantity cells dropped: {share:.1%} of value; "
          f"basis mix {picked.round(3).to_dict()}")
    return df.drop(columns=[c for c in df.columns
                            if c.startswith(("bad_", "ok_", "uv_"))])


def _degenerate(df, col):
    """True where a series' unit value is too repetitive to be a measurement: with at
    least 6 months in a year, genuine unit values are nearly all distinct, an imputed
    one takes a handful of values (see flag_placeholders)."""
    d = df[df[col].notna()].copy()
    d["year"] = d.period.str[:4]
    g = d.groupby(["iso", "flow", "code", "year"])[col]
    stat = pd.DataFrame({"n": g.size(), "nun": g.apply(lambda s: s.round(4).nunique())})
    if os.environ.get("GEC_DEGEN", "1") != "1":
        return pd.Series(False, index=df.index).to_numpy()
    bad = stat[(stat.n >= 6) & (stat.nun <= (stat.n * 0.5).clip(lower=2))].index
    key = pd.MultiIndex.from_arrays(
        [df.iso, df.flow, df.code, df.period.str[:4]],
        names=["iso", "flow", "code", "year"])
    return key.isin(bad)


def main():
    print("comtrade cache ...", flush=True)
    ct = comtrade_base()
    print(f"  {len(ct):,} cells")
    print("tdm extracts ...", flush=True)
    td = tdm_base()
    print(f"  {len(td):,} cells")
    # Comtrade is the backbone; TDM fills (a) cells Comtrade is silent on (TWN
    # always, CHN 2025+, VNM beyond its Comtrade horizon) and (b) cells where the
    # Comtrade report carries NO net weight at all but TDM does. (b) is specific to
    # this base: the panel's value hierarchy is untouched, we are only sourcing the
    # quantity leg of a unit value, and a value with no weight is unusable here.
    key = ["iso", "flow", "code", "period"]
    ct_k = ct.set_index(key)
    td_k = td.set_index(key)
    silent = td_k.index.difference(ct_k.index)
    shared = td_k.index.intersection(ct_k.index)
    swap = shared[((ct_k.loc[shared, ["value_kg", "value_qty"]].to_numpy() <= 0).all(1))
                  & ((td_k.loc[shared, ["value_kg", "value_qty"]].to_numpy() > 0).any(1))]
    fill = td_k.loc[silent.union(swap)]
    df = pd.concat([ct_k.drop(index=swap), fill]).reset_index().sort_values(key)
    extra = df[df.iso.str.endswith(EXTRA)].copy()
    extra["iso"] = extra.iso.str.replace(EXTRA, "", regex=False).map(BLOC)
    extra = extra.groupby(["iso", "flow", "code", "period"], as_index=False).agg(
        {c: "sum" for c in ["value", "value_kg", "kg", "value_qty", "qty"]})
    extra["source"] = "bloc"
    df = pd.concat([df[~df.iso.str.endswith(EXTRA)], extra], ignore_index=True)
    df = choose_basis(df)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    cov = df.value_wgt.sum() / df.value.sum()
    print(f"wrote {OUT} — {len(df):,} cells, {df.period.min()}..{df.period.max()}, "
          f"weight coverage {cov:.1%} of value; TDM filled {len(fill):,} cells")


if __name__ == "__main__":
    main()
