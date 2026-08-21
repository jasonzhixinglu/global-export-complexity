"""Export/import price indices (country x stage), terms of trade and net exports
(country, aggregate) for the semiconductor / AI-compute basket.

Prices. Unit values come from data/derived/unit_values_monthly.parquet (each
reporter's own report; USD per kg on the lines that carry a net weight). Levels of
$/kg are not comparable across products, so the index is a CHAINED TORNQVIST over
HS6 codes within a stage:

    dln P_t = sum_i wbar_it * (ln uv_it - ln uv_i,t-1),
    wbar_it = 0.5 * (s_i,t-1 + s_it), renormalised over the codes present in both
    months, where s_i is code i's share of the stage's weight-covered value.

Two frequencies:
  * monthly  -- unit values from the month's own cells (noisy; thin cells filtered)
  * roll12   -- unit values from trailing 12-month sums of value and kg, chained
                monthly. This is the series to read: it removes seasonality and
                thin-cell noise. Each series starts at 100 in its first month.

Terms of trade = aggregate export price index / aggregate import price index, both
built the same way over ALL codes at once (not an average of stage indices), so ToT
is a country-level number, = 100 at the series start.

Net exports come from the RECONCILED panel (panel_semi_monthly.parquet), not from
the reporter files: X_c = flows with exporter c, M_c = flows with importer c,
summed over all partners incl. ROW. Monthly and 12-month rolling sums.

Outputs (results/tables/):
  price_index_stage_monthly.csv    iso, flow, stage, period, index, n_codes, matched
  price_index_stage_roll12.csv     same, 12m-rolling unit values
  terms_of_trade.csv               iso, freq, period, px, pm, tot
  net_exports.csv                  iso, period, exports, imports, net, *_12m
  price_coverage.csv               iso, flow, stage: share of value carrying a weight
  price_index_broad_roll12.csv     iso, flow, broad stage (upstream/chips/downstream)
  terms_of_trade_broad.csv         within-stage ToT, one row per iso x broad x month
  terms_of_trade_net_position.csv  sell-side over buy-side ToT (see broad_tot)

Every index carries a second base as well (*_2021, 2021-01 = 100) so "since the AI
cycle began" needs no re-chaining.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.classifications import SEMICONDUCTOR_OECD as _OECD

UV = cfg.DATA_DIR / "derived" / "unit_values_monthly.parquet"
PANEL = cfg.DATA_DIR / "derived" / "panel_semi_monthly.parquet"
OUT = cfg.RESULTS_DIR / "tables"

# stage labels: the chain order used everywhere else (export_supply_chain_sankey)
STAGES = [
    ("1_raw_materials", sorted(_OECD["Raw materials"])),
    ("2_wafers", sorted(_OECD["Wafer inputs"])),
    ("3_litho_optics", sorted(_OECD["Foundry inputs"])),
    ("4_equipment", sorted(_OECD["Manufacturing equipment"])),
    ("5_chips", sorted(_OECD["Chips"])),
    ("6_parts", ["847330"]),
    ("7_baseboards", ["847180"]),
    ("8_servers", ["847150"]),
]
CODE2STAGE = {c: s for s, codes in STAGES for c in codes}
# Three broad stages: what you need to make chips, the chips, and the hardware
# built out of them. Coarse enough that most countries are clearly a net buyer of
# one and a net seller of another.
BROAD = {"1_raw_materials": "upstream", "2_wafers": "upstream",
         "3_litho_optics": "upstream", "4_equipment": "upstream",
         "5_chips": "chips",
         "6_parts": "downstream", "7_baseboards": "downstream",
         "8_servers": "downstream"}
REBASE_YEAR = "2021"   # second base: the 2021 AVERAGE = 100 ("since the AI cycle began")
# A code-month cell must clear this to enter an index: below it a unit value is
# mostly rounding, and one odd shipment moves the ratio by an order of magnitude.
MIN_CELL = float(os.environ.get("GEC_MIN_CELL", 50_000.0))          # USD per month (the rolling series sees 12x this)
MAX_DLN = float(os.environ.get("GEC_MAX_DLN", np.log(3.0)))        # drop |dln uv| bigger than this as a reporting glitch
MIN_MATCHED = float(os.environ.get("GEC_MIN_MATCHED", 0.30))           # need 30% of the stage's covered value matched t-1,t
SEASON = 12                  # months per cycle, for the STL seasonal adjustment
BLOC = {"CHN", "HKG"}        # counted as one throughout the project
BLOC_LABEL = "CHK"


def _usable_periods(cells, gcols):
    """Drop months where the series' weight coverage collapses relative to its own
    norm. A country whose reporters impute weight (or simply do not report it) in
    some months would otherwise have those months' surviving rump of codes stand in
    for the whole basket -- China's 2017 is entirely imputed, which left its 2017
    windows resting on a single $30m code."""
    cov = (cells.groupby(gcols + ["period"], sort=False)[["value_wgt", "value"]].sum()
           .assign(r=lambda x: x.value_wgt / x.value)["r"].rename("period_cov")
           .reset_index())
    norm = cov.groupby(gcols, sort=False).period_cov.transform("median")
    # ...and months that are simply incomplete. The most recent month or two often
    # carry only the fastest reporters, which is a different basket, not a price move.
    lvl = cells.groupby(gcols + ["period"], sort=False).value_wgt.sum().rename("lvl")
    cov = cov.join(lvl, on=gcols + ["period"])
    lnorm = cov.groupby(gcols, sort=False).lvl.transform("median")
    if os.environ.get("GEC_USABLE", "1") != "1":
        return cells
    ok = cov[(cov.period_cov >= 0.5 * norm) & (cov.lvl >= 0.4 * lnorm)][gcols + ["period"]]
    return cells.merge(ok, on=gcols + ["period"], how="inner")


def _tornqvist(cells, gcols, min_cell=MIN_CELL):
    """cells: gcols + code, period, value, value_wgt, kg. Chained-index log steps per
    (gcols, period), with the diagnostics needed to judge them."""
    cells = _usable_periods(cells, gcols)
    d = cells[(cells.quantity > 0) & (cells.value_wgt >= min_cell)].copy()
    d["luv"] = np.log(d.value_wgt / d.quantity)
    d = d.sort_values(gcols + ["code", "period"])
    g = d.groupby(gcols + ["code"], sort=False)
    d["luv_lag"] = g.luv.shift()
    d["val_lag"] = g.value_wgt.shift()
    d["per_lag"] = g.period.shift()
    per = pd.PeriodIndex(d.period, freq="M")
    lag = pd.PeriodIndex(d.per_lag.fillna(d.period), freq="M")
    consecutive = d.per_lag.notna() & (lag == per - 1)
    d["dln"] = (d.luv - d.luv_lag).where(consecutive)
    d.loc[d.dln.abs() > MAX_DLN, "dln"] = np.nan

    covered = d.groupby(gcols + ["period"], sort=False).value_wgt.sum().rename("stage_val")
    m = d[d.dln.notna()].copy()
    # average of the two months' SHARES (Tornqvist proper), not of the two dollar
    # values -- the latter would tilt the weight toward whichever month traded more.
    gm0 = m.groupby(gcols + ["period"], sort=False)
    m["wbar"] = 0.5 * (m.value_wgt / gm0.value_wgt.transform("sum")
                       + m.val_lag / gm0.val_lag.transform("sum"))
    gm = m.groupby(gcols + ["period"], sort=False)
    step = gm.apply(lambda x: np.average(x.dln, weights=x.wbar),
                    include_groups=False).rename("dln_p").to_frame()
    step["n_codes"] = gm.size()
    step["matched_val"] = gm.value_wgt.sum()
    step = step.join(covered, how="left")
    step["matched"] = step.matched_val / step.stage_val
    step.loc[step.matched < MIN_MATCHED, "dln_p"] = np.nan
    return step.reset_index()


def _direct(cells, gcols, min_cell=MIN_CELL):
    """Drift-free companion to the chained index: a single Tornqvist comparison of
    each month against the base month (the series' first), over the codes present in
    both. A chained index can drift when weights and unit values move together; if
    the two series tell different stories, the chained one is not to be trusted.
    """
    cells = _usable_periods(cells, gcols)
    d = cells[(cells.quantity > 0) & (cells.value_wgt >= min_cell)].copy()
    d["luv"] = np.log(d.value_wgt / d.quantity)
    base_per = d.groupby(gcols, sort=False).period.transform("min")
    b = d[d.period == base_per][gcols + ["code", "luv", "value_wgt"]].rename(
        columns={"luv": "luv_b", "value_wgt": "val_b"})
    m = d.merge(b, on=gcols + ["code"], how="inner")
    m["wbar"] = 0.5 * (m.value_wgt / m.groupby(gcols + ["period"], sort=False)
                       .value_wgt.transform("sum")
                       + m.val_b / m.groupby(gcols + ["period"], sort=False)
                       .val_b.transform("sum"))
    gm = m.groupby(gcols + ["period"], sort=False)
    out = gm.apply(lambda x: 100 * np.exp(np.average(x.luv - x.luv_b, weights=x.wbar)),
                   include_groups=False).rename("index_direct").reset_index()
    return out


def _chain(step, gcols):
    """Cumulate the log steps into an index = 100 at each series' first month. A
    month whose step could not be computed is carried as a gap (flat) and flagged,
    so a thin month never silently becomes a price move."""
    out = []
    for _, x in step.groupby(gcols, sort=False):
        x = x.sort_values("period").copy()
        x["index"] = 100 * np.exp(x.dln_p.fillna(0.0).cumsum())
        x["gap"] = x.dln_p.isna()
        out.append(x)
    return pd.concat(out, ignore_index=True)


def _sa(y):
    """Seasonally adjust one monthly series: STL on logs (multiplicative seasonality
    is the right model for trade), robust to the outliers this data has plenty of.
    Returns the series with the seasonal component divided out.

    The monthly panel elsewhere in this project is deliberately NOT seasonally
    adjusted (docs/modeling-brainstorm.md); this is local to the fast-moving charts,
    where a 3-month average would otherwise mostly show Lunar New Year.
    """
    y = y.astype(float)
    ok = y.notna() & (y > 0)
    if ok.sum() < 3 * SEASON:
        return y
    ly = np.log(y[ok])
    try:
        res = STL(ly.to_numpy(), period=SEASON, robust=True).fit()
    except Exception:
        return y
    out = y.copy()
    out.loc[ok] = np.exp(ly.to_numpy() - res.seasonal)
    return out


def _sa_3m(df, gcols, col):
    """Seasonally adjusted, then a trailing 3-month mean -- the fast companion to the
    12-month series. Two months of noise still show; that is the trade for speed."""
    g = df.groupby(gcols, sort=False)[col]
    sa = g.transform(_sa)
    return sa, sa.groupby([df[c] for c in gcols], sort=False).transform(
        lambda x: x.rolling(3, min_periods=3).mean())


def _rebase(df, gcols, cols, year=REBASE_YEAR, suffix="_2021"):
    """Restate an index on the average of a base YEAR = 100, so a reader can ask
    "since 2021" without re-chaining. The average of twelve months, not one month,
    so the base is not itself a seasonal or one-month accident. Series with no data
    in that year are left blank rather than rebased on a neighbouring period."""
    base = (df[df.period.str[:4] == year].groupby(gcols)[cols].mean()
            .rename(columns={c: c + "_b" for c in cols}))
    j = df.join(base, on=gcols)
    for c in cols:
        df[c + suffix] = 100 * j[c] / j[c + "_b"]
    return df


def _rollsum(cells, gcols, n=12):
    """Trailing n-month sums of value and kg per code on a complete month grid.
    Absent months are true zeros (no trade in that cell), so the grid is filled with
    zeros and the first n-1 months of the sample -- whose windows reach outside it --
    are dropped."""
    keys = gcols + ["code"]
    grid = pd.period_range(pd.Period(cells.period.min(), "M"),
                           pd.Period(cells.period.max(), "M"), freq="M", name="p")
    d = cells.copy()
    d["p"] = pd.PeriodIndex(d.period, freq="M")
    out = {}
    for col in ("value_wgt", "quantity", "value"):
        w = (d.pivot_table(index=keys, columns="p", values=col, aggfunc="sum")
             .reindex(columns=grid).fillna(0.0))
        out[col] = w.T.rolling(n, min_periods=n).sum().T.iloc[:, n - 1:]
    stacked = pd.concat({c: v.stack() for c, v in out.items()}, axis=1).reset_index()
    stacked["period"] = stacked["p"].dt.strftime("%Y%m")
    return stacked.drop(columns="p")


def ne_by_stage():
    """Net trade per country x broad stage over the whole sample, from the panel.
    Used only to decide which side of the ratio a stage sits on, so it is measured
    once over the full window rather than month by month -- a basket that flips with
    the data would make the index meaningless."""
    p = pd.read_parquet(PANEL)
    p["broad"] = p.code.map(CODE2STAGE).map(BROAD)
    x = p.groupby(["exporter", "broad"]).value.sum().rename("x")
    m = p.groupby(["importer", "broad"]).value.sum().rename("m")
    ne = pd.concat([x, m], axis=1).fillna(0.0)
    ne.index.names = ["iso", "broad"]
    ne = ne.reset_index()
    ne = ne[ne.iso != "ROW"]
    ne["net"] = ne.x - ne.m
    return ne


def broad_tot(uv, ne):
    """Two cuts, both on the three broad stages:

    within-stage  price of a country's exports of that stage over the price of its
                  imports of the same stage -- the ordinary terms of trade, asked
                  one stage at a time.
    net-position  the country's SELL side (broad stages it is a net exporter of)
                  against its BUY side, each an index over that side's codes,
                  weighted within the index by the codes' own trade. This is the
                  ratio that says whether what a country sells is getting dearer
                  relative to what it must buy -- for a processing economy the
                  within-stage cut mostly cancels, and this one does not.
    """
    d = uv.copy()
    d["broad"] = d.stage.map(BROAD)
    gcols = ["iso", "flow", "broad"]
    cells = _rollsum(d, gcols)
    idx = _chain(_tornqvist(cells, gcols, 12 * MIN_CELL), gcols).merge(
        _direct(cells, gcols, 12 * MIN_CELL), on=gcols + ["period"], how="left")
    idx["base_period"] = idx.groupby(gcols, sort=False).period.transform("min")
    idx = _rebase(idx, gcols, ["index", "index_direct"])
    cov = (d.groupby(gcols).apply(lambda x: x.value_wgt.sum() / x.value.sum(),
                                  include_groups=False).rename("coverage").reset_index())
    idx = idx.merge(cov, on=gcols, how="left")
    idx.to_csv(OUT / "price_index_broad_roll12.csv", index=False)

    # within-stage terms of trade
    w = idx.pivot_table(index=["iso", "broad", "period"],
                        columns="flow", values=["index", "index_2021"])
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.dropna(subset=["index_X", "index_M"]).reset_index()
    w["tot"] = 100 * w.index_X / w.index_M
    w["tot_2021"] = 100 * w.index_2021_X / w.index_2021_M   # legs rebased, then divided
    w = w.merge(ne.rename(columns={"broad": "broad", "net": "net_usd"})[
        ["iso", "broad", "net_usd"]], on=["iso", "broad"], how="left")
    w.rename(columns={"index_X": "px", "index_M": "pm",
                      "index_2021_X": "px_2021", "index_2021_M": "pm_2021"}
             ).to_csv(OUT / "terms_of_trade_broad.csv", index=False)

    # net-position terms of trade: sell side over buy side
    side = ne.assign(side=lambda x: np.where(x.net > 0, "sell", "buy"))[
        ["iso", "broad", "side"]]
    c = d.merge(side, on=["iso", "broad"], how="inner")
    # a country's sell side is priced by its EXPORTS of those stages, its buy side by
    # its IMPORTS of the others; the other two flow-side combinations are dropped.
    c = c[((c.side == "sell") & (c.flow == "X")) | ((c.side == "buy") & (c.flow == "M"))]
    g2 = ["iso", "side"]
    cells2 = _rollsum(c, g2)
    idx2 = _chain(_tornqvist(cells2, g2, 12 * MIN_CELL), g2).merge(
        _direct(cells2, g2, 12 * MIN_CELL), on=g2 + ["period"], how="left")
    idx2["base_period"] = idx2.groupby(g2, sort=False).period.transform("min")
    idx2 = _rebase(idx2, g2, ["index", "index_direct"])
    n = idx2.pivot_table(index=["iso", "period"], columns="side",
                         values=["index", "index_direct", "index_2021"])
    n.columns = [f"{a}_{b}" for a, b in n.columns]
    n = n.dropna(subset=["index_sell", "index_buy"]).reset_index()
    n["tot_net"] = 100 * n.index_sell / n.index_buy
    n["tot_net_direct"] = 100 * n.index_direct_sell / n.index_direct_buy
    n["tot_net_2021"] = 100 * n.index_2021_sell / n.index_2021_buy
    sides = (side.groupby(["iso", "side"]).broad
             .apply(lambda x: "+".join(sorted(x))).unstack())
    n = n.merge(sides.rename(columns={"sell": "sell_stages", "buy": "buy_stages"}
                             ).reset_index(), on="iso", how="left")
    n.to_csv(OUT / "terms_of_trade_net_position.csv", index=False)
    print(f"terms_of_trade_broad.csv          {len(w):,} rows")
    print(f"terms_of_trade_net_position.csv   {len(n):,} rows, {n.iso.nunique()} countries")


def main():
    uv = pd.read_parquet(UV)
    if "quantity" not in uv:            # bases written before the qty basis existed
        uv["quantity"] = uv["kg"]
    uv["stage"] = uv.code.map(CODE2STAGE)
    uv = uv[uv.stage.notna()].copy()
    OUT.mkdir(parents=True, exist_ok=True)

    # --- coverage: what share of reported value carries a net weight ---
    def _cov(x):
        return pd.Series({"value_usd": x.value.sum(),
                          "coverage": x.value_wgt.sum() / x.value.sum()})

    cov = uv.groupby(["iso", "flow", "stage"]).apply(_cov, include_groups=False).reset_index()
    cov_all = uv.groupby(["iso", "flow"]).apply(_cov, include_groups=False).reset_index()
    cov_all["stage"] = "ALL"
    pd.concat([cov, cov_all], ignore_index=True).to_csv(
        OUT / "price_coverage.csv", index=False)

    # --- price indices: per stage, plus an all-code aggregate for ToT ---
    uv_all = uv.copy()
    uv_all["stage"] = "ALL"
    both = pd.concat([uv, uv_all], ignore_index=True)
    gcols = ["iso", "flow", "stage"]

    r12_cells = _rollsum(both, gcols)
    monthly = _chain(_tornqvist(both, gcols), gcols).merge(
        _direct(both, gcols), on=gcols + ["period"], how="left")
    roll12 = _chain(_tornqvist(r12_cells, gcols, 12 * MIN_CELL), gcols).merge(
        _direct(r12_cells, gcols, 12 * MIN_CELL), on=gcols + ["period"], how="left")

    covmap = pd.concat([cov, cov_all], ignore_index=True)[
        ["iso", "flow", "stage", "coverage"]]
    keep = gcols + ["period", "index", "index_direct", "base_period", "coverage",
                    "dln_p", "n_codes", "matched", "gap"]
    for name, src in (("monthly", monthly), ("roll12", roll12)):
        src["base_period"] = src.groupby(gcols, sort=False).period.transform("min")
        out = src.merge(covmap, on=gcols, how="left")
        out.loc[out.stage != "ALL", keep].to_csv(
            OUT / f"price_index_stage_{name}.csv", index=False)

    # --- terms of trade (country aggregate) ---
    tots = []
    for lab, src in (("monthly", monthly), ("roll12", roll12)):
        w = src[src.stage == "ALL"]
        a = (w.pivot_table(index=["iso", "period"], columns="flow", values="index")
             .dropna(subset=["X", "M"]).reset_index())
        a["tot"] = 100 * a.X / a.M
        dd = (w.pivot_table(index=["iso", "period"], columns="flow",
                            values="index_direct").reset_index()
              .rename(columns={"X": "px_direct", "M": "pm_direct"}))
        a = a.merge(dd, on=["iso", "period"], how="left")
        a["tot_direct"] = 100 * a.px_direct / a.pm_direct
        a["freq"] = lab
        tots.append(a.rename(columns={"X": "px", "M": "pm"}))
    # Fast variant: the same estimator on a THREE-month unit-value window, then
    # seasonally adjusted. A 3-month window is the "3m average" itself, and it drifts
    # far less than chaining raw monthly unit values (whose basket churns every month).
    for n in (3, 6):
        rn = _rollsum(both, gcols, n)
        m = _chain(_tornqvist(rn, gcols, n * MIN_CELL), gcols)
        m = m[m.stage == "ALL"].sort_values(["iso", "flow", "period"]).copy()
        m["index"] = m.groupby(["iso", "flow"], sort=False)["index"].transform(_sa)
        a = (m.pivot_table(index=["iso", "period"], columns="flow", values="index")
             .dropna(subset=["X", "M"]).reset_index())
        a["tot"] = 100 * a.X / a.M
        a["freq"] = f"m{n}_sa"
        tots.append(a.rename(columns={"X": "px", "M": "pm"}))

    tot = pd.concat(tots, ignore_index=True)
    tot = _rebase(tot, ["iso", "freq"], ["px", "pm"])
    tot["tot_2021"] = 100 * tot.px_2021 / tot.pm_2021
    cw = cov_all.pivot_table(index="iso", columns="flow", values="coverage")
    tot = tot.merge(cw.rename(columns={"X": "cov_x", "M": "cov_m"}).reset_index(),
                    on="iso", how="left")
    tot["base_period"] = tot.groupby(["iso", "freq"], sort=False).period.transform("min")
    tot = tot[["iso", "freq", "period", "px", "pm", "tot", "px_2021", "pm_2021",
               "tot_2021", "px_direct", "pm_direct", "tot_direct", "base_period",
               "cov_x", "cov_m"]]
    tot.to_csv(OUT / "terms_of_trade.csv", index=False)

    # --- broad-stage prices, and the two terms-of-trade cuts they support ---
    broad_tot(uv, ne_by_stage())

    # --- net exports from the reconciled panel (country aggregate) ---
    p = pd.read_parquet(PANEL)
    x = p.groupby(["exporter", "period"]).value.sum().rename("exports")
    m = p.groupby(["importer", "period"]).value.sum().rename("imports")
    ne = pd.concat([x, m], axis=1).fillna(0.0)
    ne.index.names = ["iso", "period"]
    ne = ne.reset_index()
    ne = ne[ne.iso != "ROW"]
    # ...plus the China-Hong Kong bloc as its own row, from EXTRA-bloc flows only.
    # Summing the two countries would count China's shipments to Hong Kong as both a
    # bloc export and a bloc import; the net is right either way, but the gross
    # columns would be inflated by an entrepot leg that doubled since 2022.
    b = p[~(p.exporter.isin(BLOC) & p.importer.isin(BLOC))]
    bx = b[b.exporter.isin(BLOC)].groupby("period").value.sum().rename("exports")
    bm = b[b.importer.isin(BLOC)].groupby("period").value.sum().rename("imports")
    bloc = pd.concat([bx, bm], axis=1).fillna(0.0).reset_index()
    bloc["iso"] = BLOC_LABEL
    ne = pd.concat([ne, bloc], ignore_index=True).sort_values(["iso", "period"])
    ne["net"] = ne.exports - ne.imports
    for c in ("exports", "imports"):
        sa, sa3 = _sa_3m(ne, ["iso"], c)
        ne[c + "_sa"], ne[c + "_sa3m"] = sa, sa3
    # net is the difference of the two adjusted legs, not an adjustment of the
    # difference: net exports change sign, and logs cannot.
    ne["net_sa"] = ne.exports_sa - ne.imports_sa
    ne["net_sa3m"] = ne.exports_sa3m - ne.imports_sa3m
    g = ne.groupby("iso", sort=False)
    for c in ("exports", "imports", "net"):
        # transform, not groupby().rolling(): the latter returns rows keyed by group
        # and re-attaching them positionally silently mixes countries up.
        ne[c + "_12m"] = g[c].transform(lambda s: s.rolling(12, min_periods=12).sum())
    ne.to_csv(OUT / "net_exports.csv", index=False)

    print(f"price_index_stage_monthly.csv  {(monthly.stage != 'ALL').sum():,} rows")
    print(f"price_index_stage_roll12.csv   {(roll12.stage != 'ALL').sum():,} rows")
    print(f"terms_of_trade.csv             {len(tot):,} rows, {tot.iso.nunique()} countries")
    print(f"net_exports.csv                {len(ne):,} rows, {ne.iso.nunique()} countries, "
          f"{ne.period.min()}..{ne.period.max()}")


if __name__ == "__main__":
    main()
