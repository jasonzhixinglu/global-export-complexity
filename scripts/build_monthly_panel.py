"""Assemble the balanced monthly bilateral panel for the supply-chain HS6 codes.

Covers all 60 codes (Fed AI-compute 3 + OECD semiconductor 57, stages 1-8;
see src/gec/classifications.py) from 2017-01. The legacy 3-code panel
(panel_ai_compute_monthly.parquet, 2020+) is left untouched on disk so existing
estimations keep their sample; new work should read panel_semi_monthly.parquet
and filter codes/periods as needed.

Sources and hierarchy (per user direction + Atlas methodology, docs/data.md):
  1. UN Comtrade monthly (validated national submissions) is the backbone.
  2. TDM fills where Comtrade is silent: Taiwan (always), China 2025+, Vietnam 2024+
     (edition VN2, preliminary), and recent-month top-ups (KR/SG/FR/TR/TH).
  3. Reconciliation follows the Growth Lab mirroring pipeline (Bustos, Yildirim et
     al., "Tackling Discrepancies in Trade Data", GL WP 251 / Scientific Data 2026),
     implemented faithfully at annual country-pair level and applied to code-months:
       Step 2  CIF->FOB: gravity regression ln(M/X) ~ ln(dist) + contiguity +
               exporter FE + importer FE (CEPII GeoDist), per year, on both-sides
               pairs; predicted ratios clipped to [1.00, 1.20] (their 20% cap).
       Step 3  Reliability: pair discrepancy D = |X - M_fob|/(X + M_fob) (D = 1 for
               single-sided pairs); OLS D = a_j + a_k over the trade network;
               negative a clipped to 0; base country chosen by R^2 search;
               reliability = 1 - a, re-estimated per year.
       Step 4  Pair weights: softmax over (rel_exp, rel_imp); reporters in the
               bottom decile of reliability are disregarded in favor of the
               reliable side; single-sided flows taken at full weight.
       Step 5  Weights applied per code-month within the pair-year.
     Data-forced adaptations (documented, not method changes): reliability and the
     CIF regression run on our 60-code basket totals rather than all-product
     totals; the CIF regression uses both-sides corridors (monthly pulls carry no
     dual-basis values); ROW pairs are excluded from estimation (ROW never
     reports) and use the importer's predicted CIF ratio; the product-level
     consistency rescale/XXXX residual code is inapplicable without all-product
     pair totals.

Panel: top-30 countries + ROW, per HS6 code, monthly from 2020-01. The balanced
endpoint is the last month at which every kept country has reported (or is covered by
TDM) on at least one side; within the balanced window, absent corridors are true zeros.
Cells between two non-reporting parties do not exist by construction (ROW-ROW is the
one structural hole; it is set to 0 and flagged).

Outputs:
  data/derived/panel_ai_compute_monthly.parquet   (long; git-ignored)
  results/panel_monthly/build_report.md           (committed summary + validation)
Run after fetch_comtrade_monthly.py and fetch_tdm.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gec import config as cfg
from gec.comtrade import CIF_FOB

from gec.classifications import SEMICONDUCTOR_OECD as _OECD
CODES = ["847150", "847180", "847330"] + sorted(
    {c for g, d in _OECD.items() if g != "Photosensitive devices" for c in d})
START = "2017-01"
# Top 30 by 2020-24 AI-compute involvement (see results/mfm), AUT excluded (reporting
# stopped 2022); everything else folds into ROW.
KEEP = ["CHN", "USA", "MEX", "TWN", "KOR", "VNM", "HKG", "MYS", "SGP", "THA",
        "NLD", "DEU", "CZE", "HUN", "JPN", "PHL", "IND", "IDN", "CAN", "GBR",
        "FRA", "ITA", "POL", "IRL", "ESP", "CHE", "BEL", "SWE", "DNK", "ISR"]
ROW = "ROW"
# Countries whose own reporting ends before the panel endpoint but whose kept-partner
# corridors are covered by mirror (partners' reports). Their ROW cells go dark beyond
# their horizon (0 + provenance flag). FRA: Comtrade ends 2025-12, TDM edition
# inaccessible on this account (probed empty even for 2024). PHL/IND/ITA/ESP/SWE:
# ~1-month slower than the rest; mirroring them moves the balanced endpoint from
# 2026-03 to 2026-04 at ~0.06% of monthly value going dark (see build report).
MIRROR_FALLBACK = {"FRA", "PHL", "IND", "ITA", "ESP", "SWE"}
CT_DIR = cfg.RAW_DIR / "comtrade_monthly"
TDM_DIR = cfg.RAW_DIR / "tdm"
OUT_PARQUET = cfg.DATA_DIR / "derived" / "panel_semi_monthly.parquet"
ATLAS_CACHE = cfg.DATA_DIR / "derived" / "bilateral_semi_2017_2024.parquet"
REPORT_DIR = cfg.RESULTS_DIR / "panel_monthly"


def load_comtrade():
    """Comtrade monthly -> report records: one row per (reporter's view of a flow).
    The pulls carry only numeric M49 codes (includeDesc=False leaves ISO blank), so
    map code -> ISO3 via the Comtrade reference tables."""
    import comtradeapicall as ctc
    parts = []
    for f in sorted(CT_DIR.glob("*.parquet")):
        d = pd.read_parquet(f)
        if len(d):
            parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df["period"] = df["period"].astype(str)
    df["cmdCode"] = df["cmdCode"].astype(str)
    df = df[df.cmdCode.isin(CODES) & (df.partnerCode != 0)]
    ref = ctc.getReference("partner")  # superset of reporters; has ISO3 per M49 code
    code2iso = {int(c): i for c, i in zip(ref["PartnerCode"], ref["PartnerCodeIsoAlpha3"])
                if isinstance(i, str) and len(i) == 3}
    code2iso[490] = "TWN"  # "Other Asia, nes" is Taiwan
    rec = pd.DataFrame({
        "reporter": df.reporterCode.map(code2iso), "partner": df.partnerCode.map(code2iso),
        "code": df.cmdCode, "period": df.period, "value": df.primaryValue.astype(float),
        "flow": df.flowCode, "source": "comtrade",
    })
    rec = rec[rec.reporter.notna()]
    rec["partner"] = rec.partner.fillna(ROW)
    return rec


def load_tdm():
    parts = []
    for f in sorted(TDM_DIR.glob("tdm_*.tsv")):
        d = pd.read_csv(f, sep="\t", encoding="utf-16",
                        dtype={"COMMODITY": str, "MONTH": str, "YEAR": str})
        if not len(d):
            continue
        parts.append(pd.DataFrame({
            "reporter": d.RPT_ISO, "partner": d.PTN_ISO, "code": d.COMMODITY,
            "period": d.YEAR + d.MONTH.str.zfill(2), "value": d.VALUE.astype(float),
            "flow": d.FLOW.map({"E": "X", "I": "M"}), "source": "tdm",
        }))
    return pd.concat(parts, ignore_index=True)


def normalize(rec):
    """Map to (exporter, importer, basis); bucket non-kept and non-country to ROW."""
    rec = rec[rec.value > 0].copy()
    valid = rec.partner.astype(str).str.fullmatch(r"[A-Z]{3}")
    rec.loc[~valid.fillna(False), "partner"] = ROW
    rec.loc[~rec.partner.isin(KEEP), "partner"] = ROW
    rec = rec[rec.reporter.isin(KEEP)]  # only kept countries' reports are usable
    exp = np.where(rec.flow == "X", rec.reporter, rec.partner)
    imp = np.where(rec.flow == "X", rec.partner, rec.reporter)
    out = pd.DataFrame({"exporter": exp, "importer": imp, "code": rec.code,
                        "period": rec.period, "value": rec.value,
                        "side": np.where(rec.flow == "X", "x", "m"),
                        "source": rec.source})
    out = out[out.exporter != out.importer]
    # duplicate reports of the same side of the same cell: comtrade beats tdm
    out = (out.sort_values("source")  # 'comtrade' < 'tdm'
              .groupby(["exporter", "importer", "code", "period", "side"], as_index=False)
              .first())
    # aggregate ROW buckets (many partners collapsed into one)
    return out


def load_cepii():
    """CEPII GeoDist: (iso_o, iso_d) -> ln(dist), contiguity."""
    d = pd.read_excel(cfg.RAW_DIR / "dist_cepii.xls",
                      usecols=["iso_o", "iso_d", "dist", "contig"])
    d = d[d.iso_o.isin(KEEP) & d.iso_d.isin(KEEP) & (d.iso_o != d.iso_d)]
    return d.set_index(["iso_o", "iso_d"])[["dist", "contig"]]


def pair_year_totals(piv):
    """Aggregate the cell table to annual country-pair totals (kept-kept only)."""
    py = piv.assign(year=piv.period.str[:4])
    py = py[(py.exporter != ROW) & (py.importer != ROW)]
    return py.groupby(["exporter", "importer", "year"], as_index=False)[["x", "m"]] \
             .sum(min_count=1)


def cif_fob_ratios(py, geo):
    """BY Step 2: per-year gravity regression of ln(M/X) on ln(dist), contiguity,
    exporter FE, importer FE; predicted CIF/FOB ratio per pair, clipped [1, 1.2].
    Returns dict (exporter, importer, year) -> ratio, plus per-importer fallback."""
    py = py.merge(geo, left_on=["exporter", "importer"], right_index=True, how="left")
    out, imp_fallback = {}, {}
    for year, g in py.groupby("year"):
        est = g[(g.x > 0) & (g.m > 0) & g.dist.notna()].copy()
        if len(est) < 50:
            continue
        y = np.log(est.m / est.x)
        Xe = pd.get_dummies(est.exporter, prefix="e", dtype=float)
        Xi = pd.get_dummies(est.importer, prefix="i", dtype=float)
        X = pd.concat([pd.Series(np.log(est.dist.values), index=est.index, name="lndist"),
                       est.contig.astype(float), Xe, Xi], axis=1)
        X.insert(0, "const", 1.0)
        beta, *_ = np.linalg.lstsq(X.values, y.values, rcond=None)
        coef = pd.Series(beta, index=X.columns)
        # predict for every kept pair with distance data
        allp = py[(py.year == year) & py.dist.notna()]
        Pe = pd.get_dummies(allp.exporter, prefix="e", dtype=float).reindex(
            columns=Xe.columns, fill_value=0.0)
        Pi = pd.get_dummies(allp.importer, prefix="i", dtype=float).reindex(
            columns=Xi.columns, fill_value=0.0)
        P = pd.concat([pd.Series(np.log(allp.dist.values), index=allp.index, name="lndist"),
                       allp.contig.astype(float), Pe, Pi], axis=1)
        P.insert(0, "const", 1.0)
        pred = np.clip(np.exp(P.values @ coef.values), 1.0, 1.2)
        for (e, i), r in zip(zip(allp.exporter, allp.importer), pred):
            out[(e, i, year)] = float(r)
        # importer-average ratio for ROW-exporter cells (exporter FE at sample mean)
        for i in KEEP:
            rs = [v for (e2, i2, y2), v in out.items() if i2 == i and y2 == year]
            if rs:
                imp_fallback[(i, year)] = float(np.mean(rs))
    return out, imp_fallback


def reliability_scores(py, ratios):
    """BY Step 3 per year: discrepancy regression over the trade network with
    base-country R^2 search; returns dict (country, year) -> reliability in [0,1]."""
    rel = {}
    for year, g in py.groupby("year"):
        g = g.copy()
        r = np.array([ratios.get((e, i, year), 1.1)
                      for e, i in zip(g.exporter, g.importer)])
        g["m_fob"] = g.m / r
        both = g.x.notna() & g.m_fob.notna()
        D = np.where(both,
                     (g.x - g.m_fob).abs() / (g.x + g.m_fob),
                     1.0)                       # single-sided pairs: D = 1
        countries = sorted(set(g.exporter) | set(g.importer))
        cidx = {c: n for n, c in enumerate(countries)}
        B = np.zeros((len(g), len(countries)))
        B[np.arange(len(g)), [cidx[c] for c in g.exporter]] = 1.0
        B[np.arange(len(g)), [cidx[c] for c in g.importer]] = 1.0
        best = None
        for base in range(len(countries)):        # base-country search (alpha_base = 0)
            cols = [c for c in range(len(countries)) if c != base]
            a, *_ = np.linalg.lstsq(B[:, cols], D, rcond=None)
            alpha = np.zeros(len(countries))
            alpha[cols] = np.maximum(a, 0.0)      # clip negatives to 0 (their rule)
            resid = D - B @ alpha
            r2 = 1 - (resid ** 2).sum() / ((D - D.mean()) ** 2).sum()
            if best is None or r2 > best[0]:
                best = (r2, alpha)
        for c, n in cidx.items():
            rel[(c, year)] = float(np.clip(1.0 - best[1][n], 0.0, 1.0))
    return rel


def pair_weights(py, rel):
    """BY Step 4: softmax of (rel_exp, rel_imp) -> weight on the importer report;
    bottom-decile reporters disregarded in favor of the reliable side.
    Returns dict (exporter, importer, year) -> w_importer in [0, 1]."""
    w = {}
    for year in py.year.unique():
        rs = {c: r for (c, y), r in rel.items() if y == year}
        if not rs:
            continue
        thr = np.percentile(list(rs.values()), 10)
        for e, i in {(e, i) for e, i, y in zip(py.exporter, py.importer, py.year)
                     if y == year}:
            re_, ri = rs.get(e, np.nan), rs.get(i, np.nan)
            if np.isnan(re_) or np.isnan(ri):
                continue
            lo_e, lo_i = re_ < thr, ri < thr
            if lo_e and not lo_i:
                w[(e, i, year)] = 1.0             # disregard unreliable exporter
            elif lo_i and not lo_e:
                w[(e, i, year)] = 0.0             # disregard unreliable importer
            else:
                w[(e, i, year)] = float(np.exp(ri) / (np.exp(re_) + np.exp(ri)))
    return w


def reporter_horizons(records):
    """Last period each kept country has any report of its own (either side/source)."""
    isrep = ((records.side == "x") & records.exporter.isin(KEEP) |
             (records.side == "m") & records.importer.isin(KEEP))
    rep = np.where(records.side == "x", records.exporter, records.importer)
    h = (records[isrep].assign(rep=rep[isrep.values] if isinstance(isrep, pd.Series) else rep)
         .groupby("rep").period.max())
    return h


def main():
    ct = load_comtrade()
    tdm = load_tdm()
    print(f"comtrade records: {len(ct)}, tdm records: {len(tdm)}")
    rec = normalize(pd.concat([ct, tdm], ignore_index=True))
    # ROW partner rows were exploded per original partner -> sum them per cell/side
    rec = (rec.groupby(["exporter", "importer", "code", "period", "side"], as_index=False)
              .agg(value=("value", "sum"), source=("source", "first")))

    # reconcile x vs m per cell (Growth Lab mirroring, faithful implementation)
    piv = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="value", aggfunc="sum").reset_index()
    src = rec.pivot_table(index=["exporter", "importer", "code", "period"],
                          columns="side", values="source", aggfunc="first").reset_index()
    piv = piv.merge(src, on=["exporter", "importer", "code", "period"],
                    suffixes=("", "_src"))
    for c in ["x", "m", "x_src", "m_src"]:
        if c not in piv:
            piv[c] = np.nan

    geo = load_cepii()
    py = pair_year_totals(piv)
    ratios, imp_fallback = cif_fob_ratios(py, geo)          # BY Step 2
    rel = reliability_scores(py, ratios)                    # BY Step 3
    w = pair_weights(py, rel)                               # BY Step 4
    yr = piv.period.str[:4]
    keys = list(zip(piv.exporter, piv.importer, yr))
    r_pair = np.array([ratios.get(k, imp_fallback.get((k[1], k[2]), CIF_FOB))
                       for k in keys])
    w_pair = np.array([w.get(k, np.nan) for k in keys])
    fob_m = piv["m"] / r_pair
    both = piv["x"].notna() & piv["m"].notna()
    # softmax weight where both sides + weights exist; single side at full weight;
    # both-sides pairs outside the estimation set (ROW) fall back to equal weights
    w_eff = np.where(np.isnan(w_pair), 0.5, w_pair)
    piv["value"] = np.where(both, (1 - w_eff) * piv["x"] + w_eff * fob_m,
                            piv["x"].fillna(fob_m))
    piv["provenance"] = np.select(
        [both, piv["x"].notna()],
        ["both:" + piv["x_src"].fillna("") + "+" + piv["m_src"].fillna(""),
         "x_only:" + piv["x_src"].fillna("")],
        default="m_only:" + piv["m_src"].fillna(""))
    piv["mirror_gap"] = np.where(both, np.log(piv["x"] / fob_m), np.nan)
    rel_summary = pd.Series(rel).rename_axis(["country", "year"]).unstack()
    print("reliability scores (last estimated year):")
    print(rel_summary.iloc[:, -2].sort_values(ascending=False).round(3).to_string())

    # balanced endpoint: every kept country reporting (either side, any source),
    # except designated mirror-fallback countries
    horizons = reporter_horizons(rec)
    horizons = horizons.reindex(KEEP)
    endpoint = horizons.drop(list(MIRROR_FALLBACK)).min()
    print("reporter horizons (last reported period):")
    print(horizons.sort_values().to_string())
    print(f"balanced endpoint: {endpoint} (mirror-fallback: {sorted(MIRROR_FALLBACK)})")

    panel = piv[(piv.period >= START.replace("-", "")) & (piv.period <= endpoint)]
    panel = panel[["exporter", "importer", "code", "period", "value", "x", "m",
                   "provenance", "mirror_gap"]].rename(columns={"x": "value_x_fob",
                                                                "m": "value_m_cif"})
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT_PARQUET, index=False)

    write_report(panel, horizons, endpoint)
    print(f"panel -> {OUT_PARQUET}: {len(panel)} rows through {endpoint}")


def lag_analysis(panel, horizons, endpoint):
    """Document publication lags and the endpoint choice: what each laggard tier costs.

    A country whose reporting stops before the endpoint is 'mirror-fallback': its
    corridors with reporting partners survive via the partner's report; corridors
    where NEITHER party reports (laggard x laggard, laggard x ROW) go dark (0).
    Dark shares are measured against 2025+ value weights.
    """
    w = panel[panel.period >= "202501"]
    tot = w.value.sum()
    inv = lambda g: w.exporter.isin(g) | w.importer.isin(g)
    dark = lambda fb: w[(w.exporter.isin(fb) & w.importer.isin(fb)) |
                        (inv(fb) & ((w.exporter == ROW) | (w.importer == ROW)))
                        ].value.sum() / tot
    tiers = horizons.groupby(horizons).groups
    lines = ["", "## Publication lags and the endpoint choice", "",
             "National monthly submissions arrive with heterogeneous lags (~2-4 months; "
             "France has stopped monthly reporting since 2025-12 and its TDM edition is "
             "inaccessible). The balanced endpoint is the last month at which every "
             "kept country outside the mirror-fallback set has reported. Fallback "
             "countries stay covered on corridors where the partner reports; only "
             "laggard-laggard and laggard-ROW corridors go dark (set to 0, weighted "
             "share of 2025+ value shown below).", "",
             f"- Mirror-fallback set: {', '.join(sorted(MIRROR_FALLBACK))} -> "
             f"balanced endpoint {endpoint[:4]}-{endpoint[4:]}; dark-cell share "
             f"{dark(MIRROR_FALLBACK):.2%} of monthly value.",
             "- Cost of pushing further (dark share if all countries reporting before "
             "that month were mirrored):"]
    for h in sorted(set(horizons) - {horizons.max()}):
        fb = set(horizons[horizons <= h].index)
        nxt = min(x for x in set(horizons) if x > h)
        lines.append(f"  - endpoint {nxt[:4]}-{nxt[4:]}: fallback {len(fb)} countries "
                     f"({', '.join(sorted(fb)[:8])}{'...' if len(fb) > 8 else ''}), "
                     f"dark {dark(fb):.2%}")
    lines.append("- Re-running the fetch scripts + assembler rolls the endpoint forward "
                 "as laggards file; the fallback set should be revisited then.")
    return lines


def atlas_bilateral():
    """Kept-kept Atlas corridors for all 60 codes, 2017-2024 (cached extract from
    the HS12 bulk CSVs)."""
    if ATLAS_CACHE.exists():
        return pd.read_parquet(ATLAS_CACHE)
    parts = []
    for path in [cfg.RAW_DIR / "hs12_country_country_product_year_6_2012_2019.csv",
                 cfg.RAW_DIR / "hs12_country_country_product_year_6_2020_2024.csv"]:
        for chunk in pd.read_csv(path, usecols=["country_iso3_code", "partner_iso3_code",
                                                "product_hs12_code", "year", "export_value"],
                                 dtype={"product_hs12_code": str}, chunksize=3_000_000):
            sel = chunk[chunk.product_hs12_code.isin(CODES) & (chunk.year >= 2017)
                        & chunk.country_iso3_code.isin(KEEP)
                        & chunk.partner_iso3_code.isin(KEEP)]
            if len(sel):
                parts.append(sel.rename(columns={
                    "country_iso3_code": "exporter", "partner_iso3_code": "importer",
                    "product_hs12_code": "code"}))
    atlas = pd.concat(parts, ignore_index=True)
    ATLAS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    atlas.to_parquet(ATLAS_CACHE, index=False)
    return atlas


def validate_vs_atlas(panel):
    """Aggregate kept-kept cells to annual and compare with the Atlas bilateral file."""
    atlas = atlas_bilateral()
    atlas = atlas.groupby(["exporter", "importer", "code", "year"], as_index=False
                          ).export_value.sum()
    p = panel[(panel.exporter != ROW) & (panel.importer != ROW)].copy()
    p["year"] = p.period.str[:4].astype(int)
    p = p[p.year <= 2024].groupby(["exporter", "importer", "code", "year"],
                                  as_index=False).value.sum()
    m = atlas.merge(p, on=["exporter", "importer", "code", "year"], how="inner")
    m = m[(m.export_value > 1e5) & (m.value > 1e5)]
    out = {}
    for code, g in m.groupby("code"):
        lr = np.log(g.value / g.export_value)
        out[code] = {"n_corridor_years": len(g),
                     "log_corr": float(np.corrcoef(np.log(g.value),
                                                   np.log(g.export_value))[0, 1]),
                     "median_ratio": float(np.exp(lr.median())),
                     "iqr_log_ratio": float(lr.quantile(0.75) - lr.quantile(0.25))}
    return out


def write_report(panel, horizons, endpoint):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    prov = panel.provenance.value_counts(normalize=True)
    val = validate_vs_atlas(panel)
    total_by_year = panel.assign(year=panel.period.str[:4]).groupby("year").value.sum() / 1e9
    gaps = panel.mirror_gap.dropna()
    lines = [
        "# Monthly bilateral supply-chain panel — build report", "",
        f"{len(CODES)} HS6 codes (stages 1-8, docs/data.md); {len(KEEP)} countries + ROW; {START} .. "
        f"{endpoint[:4]}-{endpoint[4:]} (balanced endpoint = slowest reporter).",
        "Sources: UN Comtrade monthly (backbone) + TDM (TWN always; CHN/VNM beyond "
        "Comtrade). Reconciliation: Growth Lab mirroring (Bustos-Yildirim et al., GL "
        "WP 251) — gravity-estimated CIF/FOB ratios (capped 1.20), network-estimated "
        "annual reliability scores, softmax pair weights with bottom-decile "
        "disregard; see script docstring for the faithful-implementation notes.",
        "",
        f"- Rows: {len(panel):,}; total value {total_by_year.sum():.0f}B "
        f"(by year, $B: {', '.join(f'{y} {v:.0f}' for y, v in total_by_year.items())})",
        f"- Provenance shares: "
        + ", ".join(f"{k} {v:.1%}" for k, v in prov.items()),
        f"- Mirror gap log(x/m_fob), cells with both sides: median "
        f"{gaps.median():+.3f}, IQR {gaps.quantile(0.75)-gaps.quantile(0.25):.3f} "
        f"({len(gaps):,} cells)",
        "",
        "## Reporter horizons (last reported month)", "",
        "| country | last period |", "|---|---|",
    ]
    lines += [f"| {c} | {p[:4]}-{p[4:]} |" for c, p in horizons.sort_values().items()]
    lines += lag_analysis(panel, horizons, endpoint)
    lines += ["", "## Validation vs Atlas annual bilateral (2017–2024, kept-kept "
              "corridors > $0.1M)", "",
              "| code | corridor-years | log-corr | median panel/Atlas | IQR(log ratio) |",
              "|---|---|---|---|---|"]
    for code, v in val.items():
        lines.append(f"| {code} | {v['n_corridor_years']} | {v['log_corr']:.3f} | "
                     f"{v['median_ratio']:.2f} | {v['iqr_log_ratio']:.2f} |")
    lines += ["", "_Generated by `scripts/build_monthly_panel.py`; panel parquet in "
              "`data/derived/` (git-ignored)._"]
    (REPORT_DIR / "build_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"report -> {REPORT_DIR / 'build_report.md'}")


if __name__ == "__main__":
    main()
